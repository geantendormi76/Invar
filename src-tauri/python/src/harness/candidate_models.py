from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Set


class CandidateStatus(str, Enum):
    PROPOSED = "proposed"
    VALIDATING = "validating"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class CanonicalFactors:
    """
    决定漏洞根本原因的正交规范因子
    绝对禁止渗入代码行号、Agent ID、Severity 或扫描轮次！
    """
    attack_class: str       # 例如: "authorization", "broken_authentication", "destructive_guard"
    boundary: str           # 例如: "tenant_isolation", "privileged_route", "confirmation_check"
    sink_component: str     # 例如: "orders_mutation_service", "user_profile_api"
    missing_control: str    # 例如: "missing_owner_check", "missing_confirm_param", "missing_token_verification"

    def to_canonical_string(self) -> str:
        def _clean(val: str) -> str:
            v = val.strip().lower()
            return re.sub(r"[^a-z0-9_-]+", "_", v)
        return (
            f"{_clean(self.attack_class)}:"
            f"{_clean(self.boundary)}:"
            f"{_clean(self.sink_component)}:"
            f"{_clean(self.missing_control)}"
        )


@dataclass(frozen=True)
class CandidateFingerprint:
    """
    Invar 确定性候选漏洞根因指纹 (Candidate Fingerprint)
    跨 Hunter、跨端点、跨轮次永久稳定唯一
    """
    value: str
    algorithm: str = "v1-canonical-factors"
    canonical_factors: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_factors(cls, factors: CanonicalFactors) -> "CandidateFingerprint":
        canonical_str = factors.to_canonical_string()
        digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()[:16]
        # 结构: fp:<attack_class>:<sink_component>:<16位确定性摘要>
        ac_clean = re.sub(r"[^a-z0-9_-]+", "_", factors.attack_class.lower())
        sink_clean = re.sub(r"[^a-z0-9_-]+", "_", factors.sink_component.lower())
        fp_val = f"fp:{ac_clean}:{sink_clean}:{digest}"
        return cls(
            value=fp_val,
            algorithm="v1-canonical-factors",
            canonical_factors=asdict(factors),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateFingerprint":
        return cls(**data)


@dataclass
class TraceStep:
    """
    程序切片调用与数据流追溯步 (Trace Step)
    严禁包含宿主机绝对路径
    """
    step_type: str  # "entrypoint", "propagation", "sink"
    file_path: str  # 仓库相对路径
    line: int
    scope: str      # 函数或方法名
    description: str


@dataclass
class Condition:
    """触发漏洞的必要前置条件与约束"""
    condition_id: str
    description: str
    satisfied: bool = False


@dataclass
class Candidate:
    """
    Invar 候选安全漏洞实体 (Security Candidate)
    尚处于假说与证据验证期，未被实锤前绝非正式 Finding
    """
    fingerprint: CandidateFingerprint
    title: str
    description: str
    claimed_root_cause: str
    endpoint_refs: List[str] = field(default_factory=list)
    hypothesis_refs: List[str] = field(default_factory=list)
    coverage_refs: List[str] = field(default_factory=list)
    trace: List[TraceStep] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    status: CandidateStatus = CandidateStatus.PROPOSED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Candidate":
        data_copy = dict(data)
        data_copy["status"] = CandidateStatus(data_copy["status"])
        data_copy["fingerprint"] = CandidateFingerprint.from_dict(data_copy["fingerprint"])
        data_copy["trace"] = [TraceStep(**s) if isinstance(s, dict) else s for s in data_copy.get("trace", [])]
        data_copy["conditions"] = [Condition(**c) if isinstance(c, dict) else c for c in data_copy.get("conditions", [])]
        return cls(**data_copy)


class CandidateConsolidator:
    """
    多 Hunter / 多端点候选指纹去重聚类合并器
    """
    @staticmethod
    def consolidate(candidates: List[Candidate]) -> List[Candidate]:
        if not candidates:
            return []

        grouped: Dict[str, List[Candidate]] = {}
        for c in candidates:
            grouped.setdefault(c.fingerprint.value, []).append(c)

        consolidated: List[Candidate] = []
        for fp_val, group in grouped.items():
            primary = group[0]

            # 聚合多 Hunter 发现的所有关联端点、证据链与覆盖单元
            merged_endpoints = sorted(list({ep for c in group for ep in c.endpoint_refs}))
            merged_hypotheses = sorted(list({h for c in group for h in c.hypothesis_refs}))
            merged_coverage = sorted(list({cov for c in group for cov in c.coverage_refs}))
            merged_evidence = sorted(list({ev for c in group for ev in c.evidence_refs}))

            # 去重合并调用追溯步
            seen_steps: Set[tuple] = set()
            merged_trace: List[TraceStep] = []
            for c in group:
                for s in c.trace:
                    key = (s.step_type, s.file_path, s.line, s.scope)
                    if key not in seen_steps:
                        seen_steps.add(key)
                        merged_trace.append(s)

            # 去重合并前置条件
            seen_conds: Set[str] = set()
            merged_conditions: List[Condition] = []
            for c in group:
                for cond in c.conditions:
                    if cond.condition_id not in seen_conds:
                        seen_conds.add(cond.condition_id)
                        merged_conditions.append(cond)

            # 状态聚合策略：若有任一推进至 SUPPORTED，整体升级
            resolved_status = primary.status
            if any(c.status == CandidateStatus.SUPPORTED for c in group):
                resolved_status = CandidateStatus.SUPPORTED
            elif any(c.status == CandidateStatus.VALIDATING for c in group):
                resolved_status = CandidateStatus.VALIDATING

            consolidated.append(
                Candidate(
                    fingerprint=primary.fingerprint,
                    title=primary.title,
                    description=primary.description,
                    claimed_root_cause=primary.claimed_root_cause,
                    endpoint_refs=merged_endpoints,
                    hypothesis_refs=merged_hypotheses,
                    coverage_refs=merged_coverage,
                    trace=merged_trace,
                    evidence_refs=merged_evidence,
                    conditions=merged_conditions,
                    status=resolved_status,
                    metadata=dict(primary.metadata),
                )
            )

        return consolidated
