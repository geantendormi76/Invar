from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

IDOR_KEYWORDS: Set[str] = {
    "id", "user_id", "uid", "account_id", "order_id",
    "member_id", "customer_id", "tenant_id", "doc_id",
}

VALID_HTTP_METHODS: Set[str] = {
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"
}

DESTRUCTIVE_KEYWORDS: Set[str] = {"delete", "drop", "batch", "purge", "clear", "remove"}


@dataclass
class TriageTask:
    """
    Invar System-2 靶向科研验证任务 (Targeted Research Task)
    100% 契合 Rust crates/core::ResearchTask 序列化要求，并携带轻量语义元数据
    """
    task_id: str
    endpoint_id: str
    coverage_id: str
    hypothesis_id: Optional[str]
    profile: str
    method: str
    path: str
    surface_id: str
    pool_origin: str
    priority: str
    attack_class: str
    extracted_params: List[str] = field(default_factory=list)
    impact_score: float = 1.0
    sensitivity_score: float = 1.0
    code_slice: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_rust_task_dict(self) -> Dict[str, Any]:
        """严格收敛为 Rust ResearchTask 跨进程交互所需的数据结构，剔除长文本以维持极速 IPC"""
        return {
            "task_id": self.task_id,
            "endpoint_id": self.endpoint_id,
            "coverage_id": self.coverage_id,
            "hypothesis_id": self.hypothesis_id,
            "profile": self.profile,
            "method": self.method,
            "path": self.path,
        }


class TriageDispatcher:
    """
    双轨比对产物分流与动态任务装配器
    利用 Impact / Sensitivity 双正交因果打分精准装配安全测试 Profile 与假说，
    并内置切片紧凑截断与非标动词纠偏安全防线。
    """
    def __init__(
        self,
        impact_threshold: float = 3.5,
        sensitivity_threshold: float = 3.5,
        max_slice_chars: int = 800,
    ):
        self.impact_threshold = impact_threshold
        self.sensitivity_threshold = sensitivity_threshold
        self.max_slice_chars = max_slice_chars

    def _normalize_method(self, raw_method: Any, path: str, call_sig: Optional[str] = None) -> str:
        """
        纠偏 AST 提取过程中产生的单字母残片 (如 E, T, R) 与非标 HTTP 动词
        """
        m = str(raw_method or "").strip().upper()
        if m in VALID_HTTP_METHODS:
            return m
        
        # 启发式纠偏：从调用签名中提取真实动词
        sig = str(call_sig or "").upper()
        for valid in ["DELETE", "POST", "PUT", "PATCH", "GET"]:
            if f".{valid.lower()}(" in sig or f"['{valid}']" in sig or f'["{valid}"]' in sig:
                return valid

        # 启发式纠偏：从路径语义推断
        p_lower = path.lower()
        if any(k in p_lower for k in ["delete", "remove", "clear", "purge", "drop"]):
            return "DELETE"
        if any(k in p_lower for k in ["save", "create", "update", "set", "grant", "add", "post"]):
            return "POST"
        if any(k in p_lower for k in ["put", "upload"]):
            return "PUT"

        # 安全兜底为 POST (通常状态操作端点居多) 或 GET
        return "POST" if (m in {"E", "T", "P"}) else "GET"

    def _normalize_path(self, raw_path: Any) -> str:
        """确保路径必须以前导 / 开始"""
        p = str(raw_path or "").strip()
        if not p.startswith("/"):
            p = "/" + p
        return p

    def _compact_slice(self, raw_slice: Optional[str]) -> Optional[str]:
        """将长单行前端混淆切片压缩至安全字符上限，杜绝 IPC 膨胀"""
        if not raw_slice:
            return None
        text = str(raw_slice).strip()
        if len(text) > self.max_slice_chars:
            return text[:self.max_slice_chars] + "...[TRUNCATED]"
        return text

    def _extract_subsystem(self, path: str) -> str:
        parts = [p for p in path.strip("/").split("/") if p and not p.startswith("v")]
        if len(parts) > 1 and parts[0] == "api":
            return parts[1]
        return parts[0] if parts else "root"

    def classify_and_assemble(
        self,
        record: Dict[str, Any],
        pool_origin: str = "UNKNOWN",
    ) -> TriageTask:
        raw_path = str(record.get("path", "")).strip()
        path = self._normalize_path(raw_path)
        method = self._normalize_method(
            record.get("method"),
            path=path,
            call_sig=record.get("call_signature")
        )
        surface_id = str(record.get("surface_id", "")).strip()
        endpoint_id = f"{method}:{path}"
        params = [str(p).strip() for p in record.get("extracted_params", []) if str(p).strip()]
        
        neural = record.get("neural", {})
        rule = record.get("rule", {})
        impact = float(neural.get("impact_score") or rule.get("native_risk_score") or 1.0)
        sensitivity = float(neural.get("sensitivity_score") or 1.0)

        subsystem = self._extract_subsystem(path)
        is_high_impact = impact >= self.impact_threshold
        is_high_sens = sensitivity >= self.sensitivity_threshold
        has_id_param = any(any(k in p.lower() for k in IDOR_KEYWORDS) for p in params)
        is_destructive = (
            method == "DELETE"
            or bool(rule.get("destructive", False))
            or any(k in path.lower() for k in DESTRUCTIVE_KEYWORDS)
        )

        # 策略 1: P0 级双高复合靶点
        if is_high_impact and is_high_sens:
            priority = "P0"
            profile = "p0_dual_high_state_and_confidentiality"
            hypothesis_id = "H-DESTRUCT-1" if is_destructive else "H-AUTH-1"
            attack_class = "unauthorized_state_and_idor"
        # 策略 2: P1 级高破坏性状态变更
        elif is_high_impact:
            priority = "P1"
            profile = "p1_state_mutation_safety"
            hypothesis_id = "H-DESTRUCT-1" if is_destructive else "H-AUTH-1"
            attack_class = "destructive_action" if is_destructive else "authorization"
        # 策略 3: P1 级敏感资产泄露与 IDOR
        elif is_high_sens:
            priority = "P1"
            profile = "p1_differential_idor_leak"
            hypothesis_id = "H-IDOR-1" if has_id_param else "H-AUTH-1"
            attack_class = "idor_boundary" if has_id_param else "information_disclosure"
        # 策略 4: P2 级规则硬保底
        elif bool(rule.get("high_risk_candidate", False)):
            priority = "P2"
            profile = "p2_rule_defense_verification"
            hypothesis_id = "H-AUTH-1"
            attack_class = "rule_high_risk"
        # 策略 5: P3 级普通探索覆盖
        else:
            priority = "P3"
            profile = "p3_surface_exploration"
            hypothesis_id = None
            attack_class = "exploration"

        coverage_id = f"api-{subsystem}-{attack_class}"
        task_id = f"{surface_id}:{endpoint_id}"

        return TriageTask(
            task_id=task_id,
            endpoint_id=endpoint_id,
            coverage_id=coverage_id,
            hypothesis_id=hypothesis_id,
            profile=profile,
            method=method,
            path=path,
            surface_id=surface_id,
            pool_origin=pool_origin,
            priority=priority,
            attack_class=attack_class,
            extracted_params=params,
            impact_score=round(impact, 2),
            sensitivity_score=round(sensitivity, 2),
            code_slice=self._compact_slice(record.get("code_slice")),
            source_file=record.get("source_file"),
            source_line=record.get("source_line"),
        )

    def assemble_from_files(
        self,
        pools_path: Path,
        dual_track_path: Path,
        target_pools: Optional[List[str]] = None,
    ) -> List[TriageTask]:
        pools_data = json.loads(pools_path.read_text(encoding="utf-8"))
        active_pools = target_pools or ["pool_a_rule_must_keep", "pool_b_discrepancy"]

        wanted_surfaces: Dict[str, str] = {}
        for pool_key in active_pools:
            surfaces = pools_data.get(pool_key, [])
            label = pool_key.upper()
            for sid in surfaces:
                wanted_surfaces[sid] = label

        surface_records: Dict[str, Dict[str, Any]] = {}
        with dual_track_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                sid = row.get("surface_id")
                if sid in wanted_surfaces:
                    if sid not in surface_records:
                        surface_records[sid] = row
                    else:
                        existing = surface_records[sid]
                        cur_params_len = len(row.get("extracted_params", []))
                        old_params_len = len(existing.get("extracted_params", []))
                        if cur_params_len > old_params_len:
                            surface_records[sid] = row

        assembled_tasks: List[TriageTask] = []
        for sid, origin_pool in wanted_surfaces.items():
            if sid in surface_records:
                record = surface_records[sid]
                task = self.classify_and_assemble(record, pool_origin=origin_pool)
                assembled_tasks.append(task)

        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        assembled_tasks.sort(key=lambda t: (priority_order.get(t.priority, 9), -t.impact_score, t.task_id))
        return assembled_tasks
