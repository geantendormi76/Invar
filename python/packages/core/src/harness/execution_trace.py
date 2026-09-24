from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from agent.loop_types import ResearchEvent, ResearchEventType
from harness.coverage_ledger import CoverageUnit
from harness.denial_models import DenialObservation, DeterministicDenialClassifier
from harness.finding_models import FindingRecord
from harness.models import EndpointIR
from harness.research_models import ResearchExecutionResult


TRACE_SCHEMA_VERSION = "1.0.0"

_SENSITIVE_KEY_RE = re.compile(
    r"(authorization|cookie|token|secret|password|passwd|api[_-]?key|"
    r"access[_-]?key|refresh[_-]?token|session|signature|credential|csrf)",
    re.IGNORECASE,
)

_JWT_RE = re.compile(
    r"\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"
)

_BEARER_RE = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"
)

_LONG_SECRET_RE = re.compile(
    r"(?<![A-Za-z0-9])(?=[A-Za-z0-9._~+/=-]{32,}(?![A-Za-z0-9]))"
    r"[A-Za-z0-9._~+/=-]{32,}"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_sensitive_key(key: Any) -> bool:
    return bool(_SENSITIVE_KEY_RE.search(str(key)))


def _redact_text(value: str) -> str:
    if not value:
        return value

    text = str(value)
    text = _BEARER_RE.sub("Bearer <REDACTED>", text)
    text = _JWT_RE.sub("<JWT-REDACTED>", text)

    def replace_long_token(match: re.Match[str]) -> str:
        token = match.group(0)
        if any(ch in token for ch in ["/", "\\", ":"]):
            return token
        return "<TOKEN-REDACTED>"

    text = _LONG_SECRET_RE.sub(replace_long_token, text)
    return text


def sanitize(value: Any, *, key: Optional[str] = None) -> Any:
    """
    对执行审计数据做安全脱敏。

    规则：
    1. 敏感字段直接替换。
    2. 普通字符串进一步处理 JWT / Bearer / 长 token。
    3. 保持 JSON 可序列化。
    """
    if key is not None and _is_sensitive_key(key):
        return "<REDACTED>"

    if isinstance(value, dict):
        return {
            str(k): sanitize(v, key=str(k))
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]

    if isinstance(value, str):
        return _redact_text(value)

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if hasattr(value, "value"):
        try:
            return sanitize(value.value)
        except Exception:
            pass

    return sanitize(str(value))


def classify_response(
    status_code: int,
    body_preview: str = "",
) -> str:
    """
    将一次响应归入稳定的分析类别。

    注意：
    这是观测分类，不是漏洞裁决。
    """
    if status_code == 0:
        return "transport_error"

    body = (body_preview or "").strip()

    if body.lower().startswith("<!doctype html") or body.lower().startswith("<html"):
        return "html_fallback"

    try:
        obs = DenialObservation(
            status_code=status_code,
            response_headers={},
            body_preview=body,
        )
        classified = DeterministicDenialClassifier.classify(obs)
        category = classified.primary_hypothesis.category.value
    except Exception:
        category = "UNKNOWN"

    if status_code == 429:
        return "rate_limit"

    if status_code == 405:
        return "method_policy_denial"

    if status_code in {401, 403}:
        return "access_policy_denial"

    if category == "ACCESS_POLICY_DENIAL":
        return "soft_access_policy_denial"

    if status_code == 404:
        return "not_found"

    if 200 <= status_code <= 299:
        return "success_2xx"

    if 400 <= status_code <= 499:
        return "client_error"

    if 500 <= status_code <= 599:
        return "server_error"

    return "unknown"


@dataclass
class _ActiveTask:
    index: int
    total: int
    task: Dict[str, Any]
    endpoint: EndpointIR
    started_at: str
    events: List[Dict[str, Any]] = field(default_factory=list)


class ExecutionTraceRecorder:
    """
    Invar 逐任务执行事实记录器。

    设计目标：
    - 不修改执行行为；
    - 接收 ResearchAgent 的事件流；
    - 在任务结束后将 ResearchCase + Event + Coverage 合并为一条 JSONL；
    - 每条记录带 run_id；
    - 每个任务完成后立即 flush，避免整批丢失；
    - 不保存认证凭据和明显 secret。
    """

    def __init__(
        self,
        run_id: str,
        output_path: Path,
        total_tasks: int,
        *,
        llm_enabled: bool,
        llm_model: Optional[str] = None,
        append: bool = False,
    ) -> None:
        self.run_id = run_id
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.total_tasks = total_tasks
        self.llm_enabled = bool(llm_enabled)
        self.llm_model = llm_model

        self._active: Optional[_ActiveTask] = None
        self._lock = Lock()
        self._closed = False

        if append and self.output_path.exists() and self.output_path.stat().st_size:
            with self.output_path.open("rb") as existing:
                existing.seek(-1, 2)
                if existing.read(1) != b"\n":
                    raise RuntimeError(
                        "Cannot append to execution trace without a trailing newline"
                    )

        self._stream = self.output_path.open(
            "a" if append else "w",
            encoding="utf-8",
            newline="\n",
        )

    def begin_task(
        self,
        *,
        index: int,
        task: Dict[str, Any],
        endpoint: EndpointIR,
    ) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("ExecutionTraceRecorder is already closed")

            if self._active is not None:
                raise RuntimeError(
                    f"Previous task was not finalized: "
                    f"{self._active.task.get('task_id')}"
                )

            self._active = _ActiveTask(
                index=index,
                total=self.total_tasks,
                task=dict(task),
                endpoint=endpoint,
                started_at=_utc_now(),
            )

    def on_event(self, event: ResearchEvent) -> None:
        """
        ResearchAgent.subscribe(...) 的事件接收器。
        """
        with self._lock:
            if self._closed or self._active is None:
                return

            self._active.events.append(
                {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type.value,
                    "payload": sanitize(event.payload),
                }
            )

    def _event_counts(
        self,
        events: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        return dict(
            Counter(
                str(event.get("event_type", "unknown"))
                for event in events
            )
        )

    def _extract_variant_ids(
        self,
        events: List[Dict[str, Any]],
    ) -> List[str]:
        values: List[str] = []

        for event in events:
            event_type = event.get("event_type")
            payload = event.get("payload") or {}

            if event_type in {
                ResearchEventType.VARIANT_SELECTED.value,
                ResearchEventType.TURN_START.value,
            }:
                variant_id = payload.get("variant_id")
                if variant_id:
                    values.append(str(variant_id))

        return sorted(set(values))

    def _extract_families(
        self,
        events: List[Dict[str, Any]],
    ) -> List[str]:
        values: List[str] = []

        for event in events:
            payload = event.get("payload") or {}
            family = payload.get("family")
            if family:
                values.append(str(family))

        return sorted(set(values))

    def _extract_llm_info(
        self,
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        started = [
            e for e in events
            if e.get("event_type")
            == ResearchEventType.LLM_REASONING_STARTED.value
        ]

        completed = [
            e for e in events
            if e.get("event_type")
            == ResearchEventType.LLM_REASONING_COMPLETED.value
        ]

        failed = [
            e for e in events
            if e.get("event_type")
            == ResearchEventType.LLM_REASONING_FAILED.value
        ]

        rationales: List[str] = []
        turns_prior: List[int] = []

        for event in started:
            payload = event.get("payload") or {}
            turns = payload.get("turns_prior")
            if isinstance(turns, int):
                turns_prior.append(turns)

        for event in completed:
            payload = event.get("payload") or {}
            rationale = payload.get("rationale")
            if rationale:
                rationales.append(str(rationale))

        if failed:
            terminal_status = "failed"
        elif completed:
            terminal_status = "completed"
        elif started:
            terminal_status = "started"
        else:
            terminal_status = "not_invoked"

        return {
            "enabled": self.llm_enabled,
            "invoked": bool(started or completed or failed),
            "started_count": len(started),
            "completed_count": len(completed),
            "failed_count": len(failed),
            "terminal_status": terminal_status,
            "model": self.llm_model,
            "turns_prior": sorted(set(turns_prior)),
            "rationales": rationales,
        }

    def _extract_response_observations(
        self,
        case: Any,
    ) -> Dict[str, Any]:
        attempts = list(getattr(case, "attempts", []) or [])

        status_codes: List[int] = []
        categories: List[str] = []
        attempt_rows: List[Dict[str, Any]] = []

        for attempt in attempts:
            status_code = int(getattr(attempt, "status_code", 0) or 0)
            preview = str(getattr(attempt, "response_preview", "") or "")
            category = classify_response(status_code, preview)

            status_codes.append(status_code)
            categories.append(category)

            attempt_rows.append(
                {
                    "attempt_number": getattr(attempt, "attempt_number", 0),
                    "status_code": status_code,
                    "response_category": category,
                    "payload": sanitize(
                        getattr(attempt, "payload", {}) or {}
                    ),
                    "response_preview": sanitize(preview),
                    "interpretation": sanitize(
                        getattr(attempt, "interpretation", "") or ""
                    ),
                    "mutation_reason": sanitize(
                        getattr(attempt, "mutation_reason", "") or ""
                    ),
                }
            )

        final_status = (
            int(status_codes[-1])
            if status_codes
            else 0
        )

        final_category = (
            categories[-1]
            if categories
            else "no_response"
        )

        return {
            "attempts_count": len(attempts),
            "status_codes": status_codes,
            "response_categories": dict(Counter(categories)),
            "final_status_code": final_status,
            "final_response_category": final_category,
            "attempts": attempt_rows,
        }

    def finalize_task(
        self,
        *,
        task: Dict[str, Any],
        endpoint: EndpointIR,
        execution_result: ResearchExecutionResult,
        coverage_unit: Optional[CoverageUnit],
        elapsed_ms: float,
        finding: Optional[FindingRecord] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            if self._closed:
                raise RuntimeError("ExecutionTraceRecorder is already closed")

            if self._active is None:
                raise RuntimeError(
                    "finalize_task() called without begin_task()"
                )

            case = execution_result.research_case
            decision = getattr(case, "decision", None)

            decision_status = (
                getattr(decision, "status", None)
                if decision is not None
                else None
            )

            decision_rationale = (
                getattr(decision, "rationale", "")
                if decision is not None
                else ""
            )

            events = list(self._active.events)
            responses = self._extract_response_observations(case)
            llm_info = self._extract_llm_info(events)

            metadata = dict(getattr(case, "metadata", {}) or {})
            denial = metadata.get("denial_classification")

            record: Dict[str, Any] = {
                "schema_version": TRACE_SCHEMA_VERSION,
                "run_id": self.run_id,
                "recorded_at": _utc_now(),

                "task": {
                    "index": self._active.index,
                    "total": self._active.total,
                    "task_id": task.get("task_id"),
                    "endpoint_id": task.get("endpoint_id"),
                    "coverage_id": task.get("coverage_id"),
                    "hypothesis_id": task.get("hypothesis_id"),
                    "profile": task.get("profile"),
                    "method": task.get("method"),
                    "path": task.get("path"),
                    "surface_id": task.get("surface_id"),
                    "pool_origin": task.get("pool_origin"),
                    "priority": task.get("priority"),
                    "attack_class": task.get("attack_class"),
                    "extracted_params": task.get("extracted_params"),
                    "impact_score": task.get("impact_score"),
                    "sensitivity_score": task.get("sensitivity_score"),
                    "source_file": task.get("source_file"),
                    "source_line": task.get("source_line"),
                },

                "endpoint": sanitize(endpoint.to_dict()),

                "execution": {
                    "elapsed_ms": round(float(elapsed_ms), 3),
                    "runner_status": (
                        "completed"
                        if decision is not None
                        else "inconclusive"
                    ),
                    "decision_status": decision_status,
                    "decision_rationale": sanitize(decision_rationale),
                    "attempts_count": responses["attempts_count"],
                    "agent_turns_executed": metadata.get(
                        "agent_turns_executed"
                    ),
                    "agent_breakthrough": metadata.get(
                        "agent_breakthrough"
                    ),
                    "evidence_history_count": len(
                        getattr(execution_result, "evidence_history", [])
                        or []
                    ),
                },

                "responses": responses,

                "denial": sanitize(denial),

                "hypotheses": sanitize(
                    getattr(case, "hypotheses", []) or []
                ),

                "coverage": (
                    sanitize(coverage_unit.to_dict())
                    if coverage_unit is not None
                    else None
                ),

                "finding": (
                    sanitize(finding.to_dict())
                    if finding is not None
                    else None
                ),

                "llm": sanitize(llm_info),

                "mutation": {
                    "variant_ids": self._extract_variant_ids(events),
                    "variant_count": len(
                        self._extract_variant_ids(events)
                    ),
                    "families": self._extract_families(events),
                },

                "events": events,

                "case_metadata": sanitize(metadata),
            }

            # 绝对保证 run_id 存在。
            record["run_id"] = self.run_id

            self._stream.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
            self._stream.flush()
            os.fsync(self._stream.fileno())

            self._active = None

            return record

    def finalize_exception(
        self,
        *,
        task: Dict[str, Any],
        endpoint: EndpointIR,
        error: BaseException,
        elapsed_ms: float,
        coverage_unit: Optional[CoverageUnit] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            if self._closed:
                raise RuntimeError("ExecutionTraceRecorder is already closed")

            if self._active is None:
                raise RuntimeError(
                    "finalize_exception() called without begin_task()"
                )

            record = {
                "schema_version": TRACE_SCHEMA_VERSION,
                "run_id": self.run_id,
                "recorded_at": _utc_now(),
                "task": sanitize(task),
                "endpoint": sanitize(endpoint.to_dict()),
                "execution": {
                    "elapsed_ms": round(float(elapsed_ms), 3),
                    "runner_status": "error",
                    "decision_status": None,
                    "decision_rationale": "",
                    "attempts_count": 0,
                    "agent_turns_executed": None,
                    "agent_breakthrough": False,
                    "evidence_history_count": 0,
                },
                "responses": {
                    "attempts_count": 0,
                    "status_codes": [0],
                    "response_categories": {
                        "runner_exception": 1,
                    },
                    "final_status_code": 0,
                    "final_response_category": "runner_exception",
                    "attempts": [],
                },
                "coverage": (
                    sanitize(coverage_unit.to_dict())
                    if coverage_unit is not None
                    else None
                ),
                "llm": {
                    "enabled": self.llm_enabled,
                    "invoked": False,
                    "started_count": 0,
                    "completed_count": 0,
                    "failed_count": 0,
                    "terminal_status": "not_invoked",
                    "model": self.llm_model,
                    "turns_prior": [],
                    "rationales": [],
                },
                "error": {
                    "type": type(error).__name__,
                    "message": sanitize(str(error)),
                },
                "events": list(self._active.events),
            }

            self._stream.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
            self._stream.flush()
            os.fsync(self._stream.fileno())

            self._active = None
            return record

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return

            if self._active is not None:
                raise RuntimeError(
                    f"Cannot close recorder with unfinished task "
                    f"{self._active.task.get('task_id')}"
                )

            self._stream.flush()
            self._stream.close()
            self._closed = True

    def __enter__(self) -> "ExecutionTraceRecorder":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
