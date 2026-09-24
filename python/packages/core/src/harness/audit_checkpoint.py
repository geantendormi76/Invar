from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from harness.coverage_ledger import CoverageLedger, CoverageUnit
from harness.finding_models import FindingRecord
from harness.run_models import ResearchRun


CHECKPOINT_SCHEMA_VERSION = "1.0.0"


class CheckpointError(RuntimeError):
    """断点状态与当前任务计划不一致或无法安全恢复。"""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def task_key(task: Dict[str, Any], index: int) -> str:
    explicit = str(task.get("task_id") or "").strip()
    if explicit:
        return explicit
    digest = hashlib.sha256(_canonical_json(task).encode("utf-8")).hexdigest()
    return f"TASK-SHA256-{digest}"


def compute_plan_digest(
    tasks: List[Dict[str, Any]],
    options: Dict[str, Any],
) -> str:
    material = {"tasks": tasks, "options": options}
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def repair_trace_tail(trace_path: Path | str) -> bool:
    """Repair only a torn final JSONL record left by an abrupt process exit."""
    path = Path(trace_path)
    if not path.exists() or path.stat().st_size == 0:
        return False

    with path.open("r+b") as stream:
        stream.seek(-1, os.SEEK_END)
        if stream.read(1) == b"\n":
            return False

        stream.seek(0)
        data = stream.read()
        tail_start = data.rfind(b"\n") + 1
        tail = data[tail_start:]

        try:
            json.loads(tail.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            stream.seek(tail_start)
            stream.truncate()
        else:
            stream.seek(0, os.SEEK_END)
            stream.write(b"\n")

        stream.flush()
        os.fsync(stream.fileno())
        return True


@dataclass
class AuditCheckpoint:
    run: ResearchRun
    ledger: CoverageLedger
    findings: List[FindingRecord]
    plan_digest: str
    total_tasks: int
    completed_task_keys: List[str] = field(default_factory=list)
    last_completed_index: int = 0
    status: str = "executing"
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema_version: str = CHECKPOINT_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "updated_at": self.updated_at,
            "plan_digest": self.plan_digest,
            "total_tasks": self.total_tasks,
            "completed_task_keys": list(self.completed_task_keys),
            "last_completed_index": self.last_completed_index,
            "run": self.run.to_dict(),
            "ledger": self.ledger.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditCheckpoint":
        schema_version = data.get("schema_version")
        if schema_version != CHECKPOINT_SCHEMA_VERSION:
            raise CheckpointError(
                f"Unsupported checkpoint schema: {schema_version!r}"
            )
        return cls(
            schema_version=schema_version,
            status=str(data.get("status") or "executing"),
            updated_at=str(data.get("updated_at") or ""),
            plan_digest=str(data.get("plan_digest") or ""),
            total_tasks=int(data.get("total_tasks") or 0),
            completed_task_keys=[
                str(value) for value in data.get("completed_task_keys", [])
            ],
            last_completed_index=int(data.get("last_completed_index") or 0),
            run=ResearchRun.from_dict(data["run"]),
            ledger=CoverageLedger.from_dict(data["ledger"]),
            findings=[
                FindingRecord.from_dict(value)
                for value in data.get("findings", [])
            ],
        )

    @classmethod
    def load(cls, path: Path | str) -> "AuditCheckpoint":
        checkpoint_path = Path(path)
        try:
            data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CheckpointError(
                f"Failed to load checkpoint [{checkpoint_path}]: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise CheckpointError("Checkpoint root must be a JSON object")
        return cls.from_dict(data)

    def save_atomic(self, path: Path | str) -> None:
        checkpoint_path = Path(path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = checkpoint_path.with_suffix(checkpoint_path.suffix + ".tmp")
        self.updated_at = datetime.now(timezone.utc).isoformat()
        serialized = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        with temp_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temp_path.replace(checkpoint_path)


@dataclass(frozen=True)
class TraceProgress:
    run_id: str
    completed_task_keys: List[str]
    coverage_units: Dict[str, CoverageUnit]
    findings: List[FindingRecord]
    last_completed_index: int


def recover_trace_progress(
    trace_path: Path | str,
    tasks: List[Dict[str, Any]],
    *,
    expected_total: int,
) -> Optional[TraceProgress]:
    path = Path(trace_path)
    if not path.exists() or path.stat().st_size == 0:
        return None

    planned_keys = {
        task_key(task, index)
        for index, task in enumerate(tasks, 1)
    }
    run_ids = set()
    completed: List[str] = []
    completed_set = set()
    coverage_units: Dict[str, CoverageUnit] = {}
    findings: Dict[str, FindingRecord] = {}
    last_completed_index = 0

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise CheckpointError(
                f"Execution trace line {line_number} is not valid JSON: {exc}"
            ) from exc

        run_id = str(record.get("run_id") or "")
        if not run_id:
            raise CheckpointError(
                f"Execution trace line {line_number} has no run_id"
            )
        run_ids.add(run_id)

        task_data = record.get("task") or {}
        record_total = task_data.get("total")
        if record_total is not None and int(record_total) != expected_total:
            raise CheckpointError(
                "Execution trace task total does not match the current plan: "
                f"{record_total} != {expected_total}"
            )

        execution = record.get("execution") or {}
        if record.get("error") or execution.get("runner_status") == "error":
            continue

        key = task_key(task_data, int(task_data.get("index") or 0))
        if key not in planned_keys:
            raise CheckpointError(
                f"Execution trace contains a task outside the current plan: {key}"
            )
        finding_data = record.get("finding")
        if execution.get("decision_status") == "vulnerable" and not isinstance(
            finding_data, dict
        ):
            raise CheckpointError(
                "Cannot safely reconstruct an uncheckpointed vulnerable finding "
                f"from execution trace task [{key}]"
            )
        if key in completed_set:
            raise CheckpointError(
                f"Execution trace contains duplicate completed task [{key}]"
            )

        completed.append(key)
        completed_set.add(key)
        last_completed_index = max(
            last_completed_index,
            int(task_data.get("index") or 0),
        )
        coverage_data = record.get("coverage")
        if isinstance(coverage_data, dict):
            unit = CoverageUnit.from_dict(coverage_data)
            coverage_units[unit.coverage_id] = unit
        if isinstance(finding_data, dict):
            finding = FindingRecord.from_dict(finding_data)
            findings[finding.finding_id] = finding

    if len(run_ids) != 1:
        raise CheckpointError(
            f"Execution trace must contain exactly one run_id, found {sorted(run_ids)}"
        )

    return TraceProgress(
        run_id=next(iter(run_ids)),
        completed_task_keys=completed,
        coverage_units=coverage_units,
        findings=list(findings.values()),
        last_completed_index=last_completed_index,
    )
