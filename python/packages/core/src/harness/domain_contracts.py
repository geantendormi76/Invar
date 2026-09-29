# -*- coding: utf-8 -*-
"""
Invar 权威领域数据契约统一中枢 (Canonical Domain Contracts)
对标顶级安全工程标准，集中管理端点契约、运行周期、候选指纹、安全发现、微观事实、变异算子与证据门禁
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import difflib
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunsplit



# ==========================================================================
# 1. 基础端点表示与契约注册表 (Original models.py)
# ==========================================================================
class EndpointNotFoundError(KeyError):
    """当引用的 endpoint_id 在权威注册表中不存在时显式抛出"""
    pass

@dataclass
class EndpointIR:
    """
    Invar 标准 API 契约中间表示模型 (Intermediate Representation)
    具备防御性解构与权威身份标识能力
    """
    method: str
    path: str
    endpoint_id: str = ""
    source_file: str = ""
    line: int = 0
    is_dynamic: bool = False
    extracted_params: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    confidence: float = 1.0
    call_signature: str = ""

    def __post_init__(self):
        normalized_method = self.method.upper()
        if not self.endpoint_id:
            self.endpoint_id = f"{normalized_method}:{self.path}"
        self.method = normalized_method

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> "EndpointIR":
        if not isinstance(data, dict):
            return cls(method="GET", path="")
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def __repr__(self) -> str:
        params_preview = f", params={self.extracted_params}" if self.extracted_params else ""
        return f"<EndpointIR [{self.endpoint_id}] (line={self.line}{params_preview})>"

class EndpointRegistry:
    """
    Invar 权威端点契约注册表 (Canonical Endpoint Registry)
    保证全局生命周期内端点元数据唯一、零损耗且可被确定性引用解析。
    """
    def __init__(self):
        self._endpoints: Dict[str, EndpointIR] = {}

    def register(self, endpoint: EndpointIR) -> str:
        if not endpoint.endpoint_id:
            endpoint.endpoint_id = f"{endpoint.method.upper()}:{endpoint.path}"
        self._endpoints[endpoint.endpoint_id] = endpoint
        return endpoint.endpoint_id

    def register_all(self, endpoints: List[EndpointIR]) -> List[str]:
        return [self.register(ep) for ep in endpoints]

    def get(self, endpoint_id: str) -> EndpointIR:
        if endpoint_id not in self._endpoints:
            raise EndpointNotFoundError(
                f"Endpoint '{endpoint_id}' not found in canonical EndpointRegistry"
            )
        return self._endpoints[endpoint_id]

    def contains(self, endpoint_id: str) -> bool:
        return endpoint_id in self._endpoints

    def __len__(self) -> int:
        return len(self._endpoints)

    def to_list(self) -> List[EndpointIR]:
        return list(self._endpoints.values())

# ==========================================================================
# 2. 运行周期状态机与授权边界 (Original run_models.py)
# ==========================================================================
class IllegalStateTransitionError(ValueError):
    """当尝试非法跃迁 ResearchRun 状态机时抛出"""
    pass


class RunTrack(str, Enum):
    """Invar 运行轨道契约；与 RunStatus 正交。"""
    PRODUCTION = "PRODUCTION"
    RESEARCH = "RESEARCH"
    INTELLIGENCE = "INTELLIGENCE"
    BENCHMARK = "BENCHMARK"

class RunStatus(str, Enum):
    INIT = "INIT"
    SCOPE_VERIFIED = "SCOPE_VERIFIED"
    CONTEXT_READY = "CONTEXT_READY"
    PLAN_READY = "PLAN_READY"
    EXECUTING = "EXECUTING"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    EVALUATED = "EVALUATED"
    REPORT_READY = "REPORT_READY"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


# 合法状态转移拓扑定义
VALID_TRANSITIONS: Dict[RunStatus, Set[RunStatus]] = {
    RunStatus.INIT: {RunStatus.SCOPE_VERIFIED, RunStatus.BLOCKED},
    RunStatus.SCOPE_VERIFIED: {RunStatus.CONTEXT_READY, RunStatus.BLOCKED},
    RunStatus.CONTEXT_READY: {RunStatus.PLAN_READY, RunStatus.BLOCKED},
    RunStatus.PLAN_READY: {RunStatus.EXECUTING, RunStatus.BLOCKED},
    RunStatus.EXECUTING: {RunStatus.EVIDENCE_COLLECTED, RunStatus.BLOCKED},
    RunStatus.EVIDENCE_COLLECTED: {RunStatus.EVALUATED, RunStatus.BLOCKED},
    RunStatus.EVALUATED: {RunStatus.REPORT_READY, RunStatus.BLOCKED},
    RunStatus.REPORT_READY: {RunStatus.COMPLETED, RunStatus.BLOCKED},
    RunStatus.BLOCKED: {
        RunStatus.INIT,
        RunStatus.SCOPE_VERIFIED,
        RunStatus.CONTEXT_READY,
        RunStatus.PLAN_READY,
        RunStatus.EXECUTING,
        RunStatus.EVIDENCE_COLLECTED,
        RunStatus.EVALUATED,
    },
    RunStatus.COMPLETED: set(),
}


@dataclass
class SourceRef:
    """源码上下文精确溯源事实"""
    vcs: Optional[str] = "git"
    commit: Optional[str] = None
    worktree_dirty: bool = False
    raw_input_hash: Optional[str] = None

    @staticmethod
    def compute_sha256(content: str | bytes) -> str:
        data = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.sha256(data).hexdigest()


@dataclass
class ResearchScope:
    """法定科研与测试授权边界"""
    target_domain: str
    included_subdomains: List[str] = field(default_factory=list)
    excluded_paths: List[str] = field(default_factory=list)
    allowed_methods: List[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    )
    authorization_boundary: str = "AUTHORIZED_ENGAGEMENT_ONLY"

    def is_method_allowed(self, method: str) -> bool:
        return method.upper() in [m.upper() for m in self.allowed_methods]

    def is_path_excluded(self, path: str) -> bool:
        return any(ex in path for ex in self.excluded_paths)


@dataclass
class RunProfile:
    """执行轮廓与沙箱参数"""
    name: str = "default"
    max_mutation_rounds: int = 4
    timeout: int = 5
    workers: int = 10


@dataclass
class ExecutionPolicy:
    """安全与执行权限铁律"""
    allow_dynamic_testing: bool = False
    require_independent_verification: bool = True
    enforce_dual_token_for_idor: bool = True
    max_requests_per_task: int = 10


@dataclass
class RunBudget:
    """实验资源与熔断预算"""
    max_tasks: int = 100
    max_requests: int = 1000
    max_duration_seconds: int = 3600
    tasks_executed: int = 0
    requests_made: int = 0

    def is_exhausted(self) -> bool:
        return (
            self.tasks_executed >= self.max_tasks
            or self.requests_made >= self.max_requests
        )


@dataclass
class ResearchRun:
    """
    Invar 权威科研运行周期实体 (Canonical Research Run)
    """
    run_id: str
    target_root: str
    scope: ResearchScope
    source_ref: SourceRef = field(default_factory=SourceRef)
    repository: str = ""
    raw_js_hash: Optional[str] = None
    profile: RunProfile = field(default_factory=RunProfile)
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    budget: Optional[RunBudget] = None
    status: RunStatus = RunStatus.INIT
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    coverage_ledger_ref: str = ""
    findings_ref: str = ""
    prior_run_refs: List[str] = field(default_factory=list)
    block_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    track: RunTrack = RunTrack.PRODUCTION

    def transition_to(self, new_status: RunStatus, reason: Optional[str] = None) -> None:
        """
        强类型状态机跃迁卫语句，严禁非法跳步与未裁决直接宣称完成
        """
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise IllegalStateTransitionError(
                f"Invalid transition from [{self.status.value}] to [{new_status.value}]. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )

        if new_status == RunStatus.BLOCKED:
            self.block_reason = reason or "Execution blocked by prerequisite failure"
        elif self.status == RunStatus.BLOCKED:
            self.block_reason = None

        if new_status == RunStatus.COMPLETED:
            self.completed_at = datetime.now(timezone.utc).isoformat()

        self.status = new_status

    def inspect(self) -> Dict[str, Any]:
        """
        对齐 Tool Contract: run.inspect 输出规范
        """
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "target_root": self.target_root,
            "source_ref": asdict(self.source_ref),
            "scope": asdict(self.scope),
            "profile": self.profile.name,
            "track": self.track.value,
            "execution_policy": asdict(self.execution_policy),
            "budget": asdict(self.budget) if self.budget else None,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "coverage_ledger_ref": self.coverage_ledger_ref,
            "findings_ref": self.findings_ref,
            "block_reason": self.block_reason,
            "prior_run_refs": list(self.prior_run_refs),
        }

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchRun":
        data_copy = dict(data)
        data_copy["status"] = RunStatus(data_copy["status"])
        data_copy["source_ref"] = SourceRef(**data_copy["source_ref"])
        data_copy["scope"] = ResearchScope(**data_copy["scope"])
        data_copy["profile"] = RunProfile(**data_copy["profile"])
        # Legacy payloads predate the Track Contract.
        # Preserve historical Research semantics instead of silently relabelling them.
        if "track" in data_copy:
            data_copy["track"] = RunTrack(data_copy["track"])
        else:
            data_copy["track"] = RunTrack.RESEARCH
        data_copy["execution_policy"] = ExecutionPolicy(**data_copy["execution_policy"])
        if data_copy.get("budget"):
            data_copy["budget"] = RunBudget(**data_copy["budget"])
        return cls(**data_copy)

    def save(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "ResearchRun":
        p = Path(path)
        content = p.read_text(encoding="utf-8")
        return cls.from_dict(json.loads(content))

# ==========================================================================
# 3. 候选漏洞根因指纹 (Original candidate_models.py)
# ==========================================================================
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

# ==========================================================================
# 4. 权威安全发现与治理记录 (Original finding_models.py)
# ==========================================================================
class FindingSchemaError(ValueError):
    """当 FindingRecord 结构或语义违背严格 Schema 契约时抛出"""
    pass


class Verdict(str, Enum):
    CONFIRMED = "confirmed"
    NEEDS_VALIDATION = "needs_validation"
    REJECTED = "rejected"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Confidence(str, Enum):
    CONFIRMED = "confirmed"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExecutionRecord:
    """微观物理发包与响应事实摘要"""
    status_code: int
    method: str
    url: str
    observed_payload: Dict[str, Any] = field(default_factory=dict)
    response_summary: str = ""
    evidence_ref: str = ""


@dataclass
class Remediation:
    """安全治理指引与修复建议"""
    summary: str
    guidance: str


@dataclass
class VerificationSummary:
    """独立第三方复核状态与摘要事实"""
    independent_verified: bool = False
    verifier_id: Optional[str] = None
    verified_at: Optional[str] = None
    verdict: Optional[str] = None
    rationale: str = ""


@dataclass
class FindingProvenance:
    """发现事实的生成与源环境血统"""
    run_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_hash: Optional[str] = None


@dataclass
class FindingRecord:
    """
    Invar 结构化安全发现记录 (Authoritative Finding Record)
    严格契约化表达，经由独立第三方验证与 PromotionGate 后可晋级为 KnowledgeCard
    """
    finding_id: str
    verdict: Verdict
    fingerprint: str
    title: str
    description: str

    root_cause: Optional[str] = None
    claimed_root_cause: Optional[str] = None
    intended_behavior: Optional[str] = None
    rejection_reason: Optional[str] = None
    unresolved_blocker: Optional[str] = None

    trace: List[TraceStep] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    execution: Optional[ExecutionRecord] = None

    endpoint_refs: List[str] = field(default_factory=list)
    coverage_refs: List[str] = field(default_factory=list)
    hypothesis_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)

    severity: Optional[Severity] = None
    confidence: Confidence = Confidence.MEDIUM
    remediation: Optional[Remediation] = None

    verification: VerificationSummary = field(default_factory=VerificationSummary)
    provenance: FindingProvenance = field(default_factory=lambda: FindingProvenance(run_id="unknown"))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["verdict"] = self.verdict.value
        data["severity"] = self.severity.value if self.severity else None
        data["confidence"] = self.confidence.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FindingRecord":
        data_copy = dict(data)
        data_copy["verdict"] = Verdict(data_copy["verdict"])
        data_copy["severity"] = Severity(data_copy["severity"]) if data_copy.get("severity") else None
        data_copy["confidence"] = Confidence(data_copy["confidence"])
        data_copy["trace"] = [TraceStep(**s) if isinstance(s, dict) else s for s in data_copy.get("trace", [])]
        data_copy["conditions"] = [Condition(**c) if isinstance(c, dict) else c for c in data_copy.get("conditions", [])]
        if data_copy.get("execution"):
            data_copy["execution"] = ExecutionRecord(**data_copy["execution"])
        if data_copy.get("remediation"):
            data_copy["remediation"] = Remediation(**data_copy["remediation"])
        if data_copy.get("verification"):
            data_copy["verification"] = VerificationSummary(**data_copy["verification"])
        if data_copy.get("provenance"):
            data_copy["provenance"] = FindingProvenance(**data_copy["provenance"])
        return cls(**data_copy)

    @classmethod
    def from_candidate(
        cls,
        candidate: Candidate,
        run_id: str,
        verdict: Verdict,
        severity: Optional[Severity] = None,
        root_cause: Optional[str] = None,
        intended_behavior: Optional[str] = None,
        execution: Optional[ExecutionRecord] = None,
        remediation: Optional[Remediation] = None,
        rejection_reason: Optional[str] = None,
        unresolved_blocker: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
    ) -> "FindingRecord":
        """
        从科研 Candidate 实体验证升级为正式 FindingRecord
        """
        # 修正：空值守卫，严禁空列表被回退短路
        eff_evidence = candidate.evidence_refs if evidence_refs is None else evidence_refs
        eff_severity = severity if verdict == Verdict.CONFIRMED else None
        eff_root_cause = (
            (candidate.claimed_root_cause if root_cause is None else root_cause)
            if verdict == Verdict.CONFIRMED
            else root_cause
        )

        finding = cls(
            finding_id=f"FINDING-{candidate.fingerprint.value}",
            verdict=verdict,
            fingerprint=candidate.fingerprint.value,
            title=candidate.title,
            description=candidate.description,
            claimed_root_cause=candidate.claimed_root_cause,
            root_cause=eff_root_cause,
            intended_behavior=intended_behavior,
            rejection_reason=rejection_reason,
            unresolved_blocker=unresolved_blocker,
            trace=list(candidate.trace),
            conditions=list(candidate.conditions),
            execution=execution,
            endpoint_refs=list(candidate.endpoint_refs),
            coverage_refs=list(candidate.coverage_refs),
            hypothesis_refs=list(candidate.hypothesis_refs),
            evidence_refs=list(eff_evidence),
            severity=eff_severity,
            confidence=Confidence.CONFIRMED if verdict == Verdict.CONFIRMED else Confidence.LOW,
            remediation=remediation,
            provenance=FindingProvenance(run_id=run_id),
        )
        return finding


class FindingSchemaValidator:
    """
    Invar 结构化发现记录权威 Schema 验证门禁
    严格校验结构合法性与三权分立语义
    """
    @staticmethod
    def validate(record_dict: Dict[str, Any]) -> List[str]:
        errors: List[str] = []

        # 1. 核心必须键校验
        required_keys = ["finding_id", "verdict", "fingerprint", "title", "description"]
        for k in required_keys:
            if not record_dict.get(k):
                errors.append(f"Missing required field: [{k}]")

        # 2. Verdict 枚举校验
        v_str = record_dict.get("verdict")
        if v_str not in {v.value for v in Verdict}:
            errors.append(f"Invalid verdict [{v_str}]. Allowed: {[v.value for v in Verdict]}")
            return errors

        verdict = Verdict(v_str)

        # 3. 语义约束：needs_validation 严禁存在 Severity
        if verdict == Verdict.NEEDS_VALIDATION:
            if record_dict.get("severity") is not None:
                errors.append("Schema violation: [needs_validation] records must NOT have severity")
            if not record_dict.get("unresolved_blocker"):
                errors.append("Schema violation: [needs_validation] records must specify unresolved_blocker")

        # 4. 语义约束：confirmed 必须有 severity、root_cause、非空 trace 与 evidence_refs
        elif verdict == Verdict.CONFIRMED:
            if not record_dict.get("severity"):
                errors.append("Schema violation: [confirmed] records MUST specify severity")
            if not record_dict.get("root_cause"):
                errors.append("Schema violation: [confirmed] records MUST specify root_cause")
            if not record_dict.get("trace"):
                errors.append("Schema violation: [confirmed] records MUST provide non-empty trace")
            if not record_dict.get("evidence_refs"):
                errors.append("Schema violation: [confirmed] records MUST reference at least one evidence")

        # 5. 语义约束：rejected 必须记录明确排除原因
        elif verdict == Verdict.REJECTED:
            if not record_dict.get("rejection_reason"):
                errors.append("Schema violation: [rejected] records MUST specify rejection_reason")

        # 6. Trace 规范：严禁绝对路径
        for idx, step in enumerate(record_dict.get("trace", [])):
            fp = step.get("file_path", "") if isinstance(step, dict) else getattr(step, "file_path", "")
            if fp.startswith("/") or fp.startswith("\\") or re.match(r"^[a-zA-Z]:", fp):
                errors.append(f"Schema violation: trace[{idx}] file_path '{fp}' must be repository-relative, not absolute")

        return errors

    @classmethod
    def assert_valid(cls, record_dict: Dict[str, Any]) -> None:
        errors = cls.validate(record_dict)
        if errors:
            raise FindingSchemaError("FindingRecord failed strict schema validation:\n" + "\n".join(errors))

# ==========================================================================
# 5. 微观发包事实日志 (Original evidence.py)
# ==========================================================================
@dataclass
class HTTPRequestLog:
    """
    HTTP 发包原始请求快照
    """
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None

@dataclass
class HTTPResponseLog:
    """
    HTTP 响应快照
    """
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body_preview: str = ""

@dataclass
class EvidenceRecord:
    """
    Invar 标准可追溯证据链记录对象 (Evidence Object)
    """
    endpoint: EndpointIR
    request: HTTPRequestLog
    response: HTTPResponseLog
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    finding_type: str = "ENDPOINT_PROBE"
    is_anomaly: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceRecord":
        endpoint_data = data.get("endpoint", {})
        request_data = data.get("request", {})
        response_data = data.get("response", {})

        return cls(
            endpoint=EndpointIR.from_dict(endpoint_data),
            request=HTTPRequestLog(**request_data),
            response=HTTPResponseLog(**response_data),
            timestamp=data.get("timestamp", ""),
            finding_type=data.get("finding_type", "ENDPOINT_PROBE"),
            is_anomaly=data.get("is_anomaly", False),
            notes=data.get("notes", "")
        )

# ==========================================================================
# 6. 安全假说与研究用例 (Original research_models.py)
# ==========================================================================
@dataclass(frozen=True)
class SecurityInvariant:
    invariant_type: str
    statement: str


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str
    rationale: str = ""
    status: str = "PROPOSED"
    evidence_notes: str = ""


@dataclass(frozen=True)
class ProbeAttempt:
    attempt_number: int
    payload: Dict[str, Any]
    status_code: int
    response_preview: str
    interpretation: str = ""
    mutation_reason: str = ""


@dataclass(frozen=True)
class ResearchDecision:
    status: str
    rationale: str


@dataclass
class ResearchCase:
    case_id: str
    endpoint: EndpointIR
    invariants: List[SecurityInvariant] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    attempts: List[ProbeAttempt] = field(default_factory=list)
    decision: Optional[ResearchDecision] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_invariant(self, invariant: SecurityInvariant) -> None:
        self.invariants.append(invariant)

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        self.hypotheses.append(hypothesis)

    def add_attempt(self, attempt: ProbeAttempt) -> None:
        expected_number = len(self.attempts) + 1
        if attempt.attempt_number != expected_number:
            raise ValueError(
                f"attempt_number must be contiguous: expected {expected_number}, "
                f"got {attempt.attempt_number}"
            )
        self.attempts.append(attempt)

    def record_attempt(
        self,
        payload: Dict[str, Any],
        status_code: int,
        response_preview: str,
        interpretation: str = "",
        mutation_reason: str = "",
    ) -> ProbeAttempt:
        attempt = ProbeAttempt(
            attempt_number=len(self.attempts) + 1,
            payload=dict(payload),
            status_code=status_code,
            response_preview=response_preview,
            interpretation=interpretation,
            mutation_reason=mutation_reason,
        )
        self.add_attempt(attempt)
        return attempt

    def set_decision(self, decision: ResearchDecision) -> None:
        self.decision = decision

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "endpoint": self.endpoint.to_dict(),
            "invariants": [
                {
                    "invariant_type": item.invariant_type,
                    "statement": item.statement,
                }
                for item in self.invariants
            ],
            "hypotheses": [
                {
                    "hypothesis_id": item.hypothesis_id,
                    "statement": item.statement,
                    "rationale": item.rationale,
                    "status": item.status,
                    "evidence_notes": item.evidence_notes,
                }
                for item in self.hypotheses
            ],
            "attempts": [
                {
                    "attempt_number": item.attempt_number,
                    "payload": dict(item.payload),
                    "status_code": item.status_code,
                    "response_preview": item.response_preview,
                    "interpretation": item.interpretation,
                    "mutation_reason": item.mutation_reason,
                }
                for item in self.attempts
            ],
            "decision": (
                None
                if self.decision is None
                else {
                    "status": self.decision.status,
                    "rationale": self.decision.rationale,
                }
            ),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ResearchExecutionResult:
    evidence: Any
    research_case: ResearchCase
    evidence_history: List[Any] = field(default_factory=list)

# ==========================================================================
# 7. 拒绝分类与网络拓扑推演 (Original denial_models.py)
# ==========================================================================
class DenialLayer(str, Enum):
    """请求被拒绝的网络/架构层级"""
    EDGE = "EDGE"
    PROXY = "PROXY"
    ROUTER = "ROUTER"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    APPLICATION = "APPLICATION"
    UNKNOWN = "UNKNOWN"


class DenialCategory(str, Enum):
    """拒绝发生的原因类别（与执行组件正交）"""
    ACCESS_POLICY_DENIAL = "ACCESS_POLICY_DENIAL"
    METHOD_POLICY_DENIAL = "METHOD_POLICY_DENIAL"
    ROUTING_MISMATCH = "ROUTING_MISMATCH"
    PARSER_MISMATCH = "PARSER_MISMATCH"
    IDENTITY_OR_TRUST_CONTEXT = "IDENTITY_OR_TRUST_CONTEXT"
    RATE_LIMIT = "RATE_LIMIT"
    DEFAULT_ERROR_HANDLER = "DEFAULT_ERROR_HANDLER"
    APPLICATION_POLICY = "APPLICATION_POLICY"
    UNKNOWN = "UNKNOWN"


class FrontendComponent(str, Enum):
    """前端网络拓扑组件指纹（解决 WAF 不是 Category 的核心解耦）"""
    WAF = "WAF"
    CDN = "CDN"
    REVERSE_PROXY = "REVERSE_PROXY"
    UNKNOWN = "UNKNOWN"


class EvidenceGrade(str, Enum):
    """证据可信度等级"""
    GRADE_A = "GRADE_A"  # 确定性 RFC 规范头部、已知指纹或受控单变量差分
    GRADE_B = "GRADE_B"  # 响应体特征、状态码模式、长度/哈希差异
    GRADE_C = "GRADE_C"  # 模型推断、路径命名猜测、单次无对照响应


@dataclass
class DenialObservation:
    """
    底层客观网络观测快照（仅记录物理事实，不含主观判定）
    """
    status_code: int
    response_headers: Dict[str, str] = field(default_factory=dict)
    body_preview: str = ""
    body_hash: str = ""
    content_type: str = ""
    redirect_url: Optional[str] = None
    latency_ms: Optional[float] = None
    transport_error: Optional[str] = None

    is_soft_denial: bool = False
    business_code: Optional[int] = None
    business_message: Optional[str] = None

    def __post_init__(self):
        self.response_headers = {k.lower(): str(v) for k, v in self.response_headers.items()}
        if not self.body_hash and self.body_preview:
            self.body_hash = hashlib.sha256(self.body_preview.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SoftDenial:
    """
    软拒绝（Soft Denial）业务错误信息载体
    """
    business_code: Optional[int]
    business_message: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _json_loads(text: str) -> Any:
    return json.loads(text)


@dataclass
class DenialHypothesis:
    """
    针对拒绝原因的单项科学假设
    """
    hypothesis_id: str
    layer: DenialLayer
    category: DenialCategory
    confidence: float
    evidence_grade: EvidenceGrade
    supporting_evidence_refs: List[str] = field(default_factory=list)
    contradicting_evidence_refs: List[str] = field(default_factory=list)
    status: str = "PROPOSED"
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["layer"] = self.layer.value
        data["category"] = self.category.value
        data["evidence_grade"] = self.evidence_grade.value
        return data


@dataclass
class DenialClassificationResult:
    """
    拒绝响应综合分类结果
    """
    primary_hypothesis: DenialHypothesis
    alternative_hypotheses: List[DenialHypothesis] = field(default_factory=list)
    frontend_component: FrontendComponent = FrontendComponent.UNKNOWN
    raw_observation: Optional[DenialObservation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_hypothesis": self.primary_hypothesis.to_dict(),
            "alternative_hypotheses": [h.to_dict() for h in self.alternative_hypotheses],
            "frontend_component": self.frontend_component.value,
            "raw_observation": self.raw_observation.to_dict() if self.raw_observation else None,
        }


class DeterministicDenialClassifier:
    """
    Invar 确定性拒绝原因分类器
    """
    KNOWN_WAF_HEADERS: Set[str] = {
        "x-waf-event", "x-waf-rule", "x-sucuri-id", "x-firewall",
    }
    KNOWN_WAF_SERVER_TOKENS: Set[str] = {
        "waf", "guard", "shield", "aliyun", "tengine", "cloudflare", "imperva",
    }

    @classmethod
    def identify_frontend(cls, obs: DenialObservation) -> FrontendComponent:
        headers = obs.response_headers
        server = headers.get("server", "").lower()
        if any(h in headers for h in cls.KNOWN_WAF_HEADERS):
            return FrontendComponent.WAF
        if any(token in server for token in cls.KNOWN_WAF_SERVER_TOKENS):
            return FrontendComponent.WAF
        if "cf-ray" in headers or "x-amz-cf-id" in headers:
            return FrontendComponent.CDN
        if server in {"nginx", "apache", "caddy", "envoy", "traefik"}:
            return FrontendComponent.REVERSE_PROXY
        return FrontendComponent.UNKNOWN

    @classmethod
    def _parse_soft_denial(cls, obs: DenialObservation):
        if obs.status_code != 200 or not obs.body_preview:
            return None
        try:
            payload = _json_loads(obs.body_preview)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None

        code = payload.get("code")
        message = payload.get("message") or payload.get("msg")
        is_forbidden_code = isinstance(code, int) and (code in {401, 403, 4001, 4003, 4008} or 4000 <= code <= 4999)
        is_forbidden_msg = isinstance(message, str) and any(
            w in message.lower()
            for w in [
                "forbidden", "unauthorized", "invalid reset password token",
                "invalid token", "not logged in", "未登录", "无权限"
            ]
        )
        if is_forbidden_code or is_forbidden_msg:
            return SoftDenial(
                business_code=code if isinstance(code, int) else None,
                business_message=message,
            )
        return None

    @classmethod
    def classify(cls, obs: DenialObservation) -> DenialClassificationResult:
        frontend = cls.identify_frontend(obs)
        sc = obs.status_code
        headers = obs.response_headers

        if sc == 405:
            allow_header = headers.get("allow")
            has_allow = allow_header is not None and bool(allow_header.strip())
            return DenialClassificationResult(
                primary_hypothesis=DenialHypothesis(
                    hypothesis_id="DH-405-METHOD-POLICY",
                    layer=DenialLayer.ROUTER,
                    category=DenialCategory.METHOD_POLICY_DENIAL,
                    confidence=0.95 if has_allow else 0.75,
                    evidence_grade=EvidenceGrade.GRADE_A if has_allow else EvidenceGrade.GRADE_B,
                    supporting_evidence_refs=[f"HTTP {sc}"] + ([f"Allow: {allow_header}"] if has_allow else []),
                    rationale=f"服务端明确声明当前动词不被路由层允许 (Allow: {allow_header or 'N/A'})",
                ),
                frontend_component=frontend,
                raw_observation=obs,
            )

        if sc == 429:
            retry_after = headers.get("retry-after", "")
            return DenialClassificationResult(
                primary_hypothesis=DenialHypothesis(
                    hypothesis_id="DH-429-RATE-LIMIT",
                    layer=DenialLayer.EDGE,
                    category=DenialCategory.RATE_LIMIT,
                    confidence=0.95,
                    evidence_grade=EvidenceGrade.GRADE_A,
                    supporting_evidence_refs=[f"HTTP {sc}"] + ([f"Retry-After: {retry_after}"] if retry_after else []),
                    rationale="请求触发了速率或并发限制",
                ),
                frontend_component=frontend,
                raw_observation=obs,
            )

        if sc == 403:
            if frontend == FrontendComponent.WAF:
                primary = DenialHypothesis(
                    hypothesis_id="DH-403-EDGE-POLICY",
                    layer=DenialLayer.EDGE,
                    category=DenialCategory.ACCESS_POLICY_DENIAL,
                    confidence=0.85,
                    evidence_grade=EvidenceGrade.GRADE_A,
                    supporting_evidence_refs=[f"HTTP 403", f"WAF Server/Header: {headers.get('server', 'Header Token')}"],
                    rationale="请求被明确的前端防火墙安全策略阻断",
                )
                alt = DenialHypothesis(
                    hypothesis_id="DH-403-ROUTING-ALT",
                    layer=DenialLayer.ROUTER,
                    category=DenialCategory.ROUTING_MISMATCH,
                    confidence=0.40,
                    evidence_grade=EvidenceGrade.GRADE_B,
                    rationale="可能是反向代理针对内部特权路径的前缀黑名单拦截",
                )
                return DenialClassificationResult(
                    primary_hypothesis=primary,
                    alternative_hypotheses=[alt],
                    frontend_component=frontend,
                    raw_observation=obs,
                )

            primary = DenialHypothesis(
                hypothesis_id="DH-403-AUTH-OR-POLICY",
                layer=DenialLayer.AUTHORIZATION,
                category=DenialCategory.ACCESS_POLICY_DENIAL,
                confidence=0.60,
                evidence_grade=EvidenceGrade.GRADE_B,
                supporting_evidence_refs=["HTTP 403"],
                rationale="服务端业务层或网关因权限不足或策略校验拒绝放行",
            )
            alt1 = DenialHypothesis(
                hypothesis_id="DH-403-ROUTER-ALT",
                layer=DenialLayer.PROXY,
                category=DenialCategory.ROUTING_MISMATCH,
                confidence=0.45,
                evidence_grade=EvidenceGrade.GRADE_C,
                rationale="可能是反向代理/中间件的访问控制列表 (ACL) 拦截",
            )
            return DenialClassificationResult(
                primary_hypothesis=primary,
                alternative_hypotheses=[alt1],
                frontend_component=frontend,
                raw_observation=obs,
            )

        soft = cls._parse_soft_denial(obs)
        if soft is not None:
            return DenialClassificationResult(
                primary_hypothesis=DenialHypothesis(
                    hypothesis_id="DH-200-SOFT-ACCESS-POLICY",
                    layer=DenialLayer.APPLICATION,
                    category=DenialCategory.ACCESS_POLICY_DENIAL,
                    confidence=0.80,
                    evidence_grade=EvidenceGrade.GRADE_B,
                    supporting_evidence_refs=[
                        f"HTTP 200",
                        f"JSON code={soft.business_code}",
                        f"message={soft.business_message!r}",
                    ],
                    rationale=(
                        f"状态码为 200 但响应体 JSON 携带业务级拒绝码 {soft.business_code}，"
                        "判定为应用层/业务层的访问策略拒绝（软 403）"
                    ),
                ),
                frontend_component=frontend,
                raw_observation=obs,
            )

        return DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id=f"DH-{sc}-UNKNOWN",
                layer=DenialLayer.UNKNOWN,
                category=DenialCategory.UNKNOWN,
                confidence=0.30,
                evidence_grade=EvidenceGrade.GRADE_C,
                supporting_evidence_refs=[f"HTTP {sc}"],
                rationale=f"状态码 [{sc}] 当前未匹配到确定性拒绝规则，作为通用待决事实保留",
            ),
            frontend_component=frontend,
            raw_observation=obs,
        )

# ==========================================================================
# 8. 9大变换族变异算子库 (Original transformation_models.py)
# ==========================================================================
class TransformationFamily(str, Enum):
    """
    Invar 9 大核心变换族（对齐规格书与 RFC 3986/9110 规范）
    """
    F1_PATH_NORMALIZATION = "F1_PATH_NORMALIZATION"
    F2_METHOD_SEMANTICS = "F2_METHOD_SEMANTICS"
    F3_HEADER_TRUST_CONTEXT = "F3_HEADER_TRUST_CONTEXT"
    F4_HOST_AUTHORITY_SCHEME = "F4_HOST_AUTHORITY_SCHEME"
    F5_ENCODING_DECODING = "F5_ENCODING_DECODING"
    F6_QUERY_BODY_PARSER = "F6_QUERY_BODY_PARSER"
    F7_PROTOCOL_WIRE = "F7_PROTOCOL_WIRE"
    F8_CACHE_ROUTING = "F8_CACHE_ROUTING"
    F9_SESSION_AUTH = "F9_SESSION_AUTH"


@dataclass(frozen=True)
class TransformationVariant:
    """
    独立且不可变的物理变异请求实体
    """
    variant_id: str
    family: TransformationFamily
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    expected_effect: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["family"] = self.family.value
        return data


class TransformationFamilyRegistry:
    """
    Invar 变换族算子库注册与生成中枢
    融合业界前沿实战词表（nomore403 / NoMoreForbidden / HackTricks 2025-2026）
    """
    TRUST_IP_PAYLOADS: List[str] = [
        "127.0.0.1",
        "127.0.0.1:80",
        "http://127.0.0.1",
    ]

    VERB_TUNNEL_HEADERS: List[str] = [
        "X-HTTP-Method-Override",
        "X-Method-Override",
        "X-HTTP-Method",
        "X-Original-Method",
    ]

    @classmethod
    def _rebuild_url(cls, parsed_url, new_path: str, new_query: Optional[str] = None) -> str:
        q = new_query if new_query is not None else parsed_url.query
        return urlunsplit((
            parsed_url.scheme,
            parsed_url.netloc,
            new_path,
            q,
            parsed_url.fragment,
        ))

    @classmethod
    def generate_f1_path_variants(
        cls,
        url: str,
        method: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
    ) -> List[TransformationVariant]:
        """
        【F1 路径规范化差异族】
        收录: %2e, %2e%2e, /., //, /./, %20, %09, ?, #, /*, 后缀混淆, Tomcat 分号 ..;/ 等
        """
        parsed = urlparse(url)
        path = parsed.path or "/"
        clean_p = path.lstrip('/')
        variants: List[TransformationVariant] = []

        # 1. 点斜杠与多斜杠解析差异 (Dot-Segment & Slash Normalization)
        dot_mutations = [
            (f"/%2e/{clean_p}", "PATH_PERCENT_DOT", "利用前后端对 URL 编码点号 %2e 解码阶段的差异"),
            (f"/%2e%2e/{clean_p}", "PATH_PERCENT_DOUBLE_DOT", "利用前后端对双点号 %2e%2e 规范化解码的差异"),
            (f"{path}/.", "PATH_TRAILING_DOT_SLASH", "利用路径末端目录标记 /. 扰动路由前缀匹配"),
            (f"//{clean_p}//", "PATH_DUAL_SLASH", "连续双斜杠 // 探查反向代理与容器的斜杠合并策略"),
            (f"/./{clean_p}/./", "PATH_DOT_SLASH_WRAPPED", "用 /./ 环绕真实路径绕过精确黑名单"),
            (f"{path}..;/", "PATH_TOMCAT_SEMICOLON_TRAVERSAL", "Tomcat 经典 ..;/ 分号参数截断与目录跨越"),
            (f"{path};/", "PATH_SEMICOLON_ROOT", "分号矩阵参数后置，测试中间件是否忽略后续字符"),
        ]
        if not path.endswith("/"):
            dot_mutations.append((f"{path}/", "PATH_TRAILING_SLASH", "尾部追加斜杠探测反代目录匹配分流差异"))

        for mutated_path, vid, rat in dot_mutations:
            variants.append(TransformationVariant(
                variant_id=f"F1_{vid}",
                family=TransformationFamily.F1_PATH_NORMALIZATION,
                method=method,
                url=cls._rebuild_url(parsed, mutated_path),
                headers=dict(headers),
                payload=dict(payload),
                rationale=rat,
                expected_effect="绕过反向代理基于字符串字面的路径阻断",
            ))

        # 2. 空白字符与控制符截断
        whitespace_mutations = [
            (f"{path}%20", "PATH_TRAILING_SPACE", "尾部追加 URL 编码空格 %20"),
            (f"{path}%09", "PATH_TRAILING_TAB", "尾部追加 URL 编码水平制表符 %09"),
        ]
        for mutated_path, vid, rat in whitespace_mutations:
            variants.append(TransformationVariant(
                variant_id=f"F1_{vid}",
                family=TransformationFamily.F1_PATH_NORMALIZATION,
                method=method,
                url=cls._rebuild_url(parsed, mutated_path),
                headers=dict(headers),
                payload=dict(payload),
                rationale=rat,
                expected_effect="依赖容器对文件名或路径尾部空白的自动裁剪机制",
            ))

        # 3. 查询分隔符与伪参数 (Query / Fragment Injection)
        query_mutations = [
            (f"{path}?", "PATH_EMPTY_QUERY", "尾部注入问号形成空 Query 改变 URI 解析树"),
            (f"{path}/?anything", "PATH_DUMMY_QUERY", "注入假查询参数绕过静态黑名单匹配"),
            (f"{path}#", "PATH_FRAGMENT_ANCHOR", "注入客户端锚点符号 # 截断服务端路径感知"),
            (f"{path}/*", "PATH_WILDCARD", "尾部追加通配符 /* 探测模糊路由分派"),
        ]
        for mutated_path, vid, rat in query_mutations:
            variants.append(TransformationVariant(
                variant_id=f"F1_{vid}",
                family=TransformationFamily.F1_PATH_NORMALIZATION,
                method=method,
                url=cls._rebuild_url(parsed, mutated_path),
                headers=dict(headers),
                payload=dict(payload),
                rationale=rat,
                expected_effect="改变 URI 结构分类，混淆 WAF 的正则表达式",
            ))

        # 4. 后缀与表征扩展名混淆 (Extension / Representation Confusion)
        ext_mutations = [
            (f"{path}.json", "EXT_JSON", "请求伪静态 .json 拓展名，探测内容协商与路由解耦"),
            (f"{path}.html", "EXT_HTML", "请求伪静态 .html 拓展名，绕过针对 API 路径的阻断"),
            (f"{path}.php", "EXT_PHP", "探测旧式 FastCGI 或伪静态后缀透传"),
            (f"{path}.action", "EXT_ACTION", "探测 Struts/Java 框架动作后缀透传"),
        ]
        for mutated_path, vid, rat in ext_mutations:
            variants.append(TransformationVariant(
                variant_id=f"F1_{vid}",
                family=TransformationFamily.F1_PATH_NORMALIZATION,
                method=method,
                url=cls._rebuild_url(parsed, mutated_path),
                headers=dict(headers),
                payload=dict(payload),
                rationale=rat,
                expected_effect="匹配网关静态资源放行白名单，但由后端框架完整处理",
            ))

        return variants

    @classmethod
    def generate_f2_method_variants(
        cls,
        url: str,
        method: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        target_verb: Optional[str] = None,
    ) -> List[TransformationVariant]:
        """
        【F2 动词语义与隧道穿透族】
        收录: POST 空载荷降级、TRACE 动词、HEAD 探测、X-HTTP-Method-Override 头隧道与 Query 动词
        """
        effective_target = (target_verb or method).upper()
        variants: List[TransformationVariant] = []

        # 1. POST 协议降级变体 (Content-Length: 0)
        post_headers = dict(headers)
        post_headers["Content-Length"] = "0"
        variants.append(TransformationVariant(
            variant_id="F2_POST_EMPTY_BODY",
            family=TransformationFamily.F2_METHOD_SEMANTICS,
            method="POST",
            url=url,
            headers=post_headers,
            payload={},
            rationale="使用 POST 伴随 Content-Length: 0 发起探测，绕过仅针对 GET 的拦截策略",
            expected_effect="以非缓存、状态变更语义迫使后端放行",
        ))

        # 2. 诊断动词探测变体 (TRACE / HEAD)
        variants.append(TransformationVariant(
            variant_id="F2_VERB_TRACE",
            family=TransformationFamily.F2_METHOD_SEMANTICS,
            method="TRACE",
            url=url,
            headers=dict(headers),
            payload=dict(payload),
            rationale="发送 RFC 标准 TRACE 动词探查边缘代理是否回显或未设防",
            expected_effect="利用代理对诊断动词的盲区实现透传",
        ))
        variants.append(TransformationVariant(
            variant_id="F2_VERB_HEAD",
            family=TransformationFamily.F2_METHOD_SEMANTICS,
            method="HEAD",
            url=url,
            headers=dict(headers),
            payload=dict(payload),
            rationale="发送 HEAD 动词探查应用是否仅拦截正文返回但放行元数据",
            expected_effect="探查不敏感动词放行状态",
        ))

        # 3. HTTP 动词隧道头 (Header Verb Tunneling - 吸收社区主流标准)
        for h_name in cls.VERB_TUNNEL_HEADERS:
            h_tunnel = dict(headers)
            h_tunnel[h_name] = effective_target
            variants.append(TransformationVariant(
                variant_id=f"F2_HEADER_TUNNEL_{h_name.upper().replace('-', '_')}",
                family=TransformationFamily.F2_METHOD_SEMANTICS,
                method="POST" if effective_target != "POST" else "GET",
                url=url,
                headers=h_tunnel,
                payload=dict(payload),
                rationale=f"载荷动词置于载体请求中，通过隧道头 [{h_name}] 穿透 WAF",
                expected_effect="前端看到的是普通动词，后端中间件将其还原为目标动词",
            ))

        # 4. URL 查询参数动词隧道 (Query Verb Tunneling)
        parsed = urlparse(url)
        delimiter = "&" if parsed.query else "?"
        for q_param in ["_method", "method"]:
            tampered_url = f"{url}{delimiter}{q_param}={effective_target}"
            variants.append(TransformationVariant(
                variant_id=f"F2_QUERY_TUNNEL_{q_param.upper()}",
                family=TransformationFamily.F2_METHOD_SEMANTICS,
                method="POST",
                url=tampered_url,
                headers=dict(headers),
                payload=dict(payload),
                rationale=f"通过 URL 查询参数 [{q_param}] 声明目标动词",
                expected_effect="触发 Web 框架内置的 MethodFilter 动词重写",
            ))

        return variants

    @classmethod
    def generate_f3_header_trust_variants(
        cls,
        url: str,
        method: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
    ) -> List[TransformationVariant]:
        """
        【F3 代理头与信任上下文族】
        收录: X-Original-URL, X-Rewrite-URL, X-Forwarded-Prefix, Cloudflare/Akamai 真实 IP 头, RFC 7239 Forwarded 等
        """
        parsed = urlparse(url)
        target_path = parsed.path or "/"
        root_url = cls._rebuild_url(parsed, "/")
        variants: List[TransformationVariant] = []

        # 1. 代理路径重写头 (X-Original-URL / X-Rewrite-URL / X-Forwarded-Prefix)
        rewrite_headers = [
            ("X-Original-URL", "X_ORIGINAL_URL", target_path),
            ("X-Rewrite-URL", "X_REWRITE_URL", target_path),
            ("X-rewrite-url", "X_REWRITE_URL_LOWER", target_path),
            ("X-Forwarded-Prefix", "X_FORWARDED_PREFIX", target_path),
        ]
        for h_rewrite, vid_suffix, h_val in rewrite_headers:
            rw_headers = dict(headers)
            rw_headers[h_rewrite] = h_val
            variants.append(TransformationVariant(
                variant_id=f"F3_REWRITE_{vid_suffix}",
                family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
                method=method,
                url=root_url,
                headers=rw_headers,
                payload=dict(payload),
                rationale=f"请求根路由 '/'，通过 [{h_rewrite}: {h_val}] 探查后端内部路由重写与前缀剥离",
                expected_effect="前端放行根路由，后端内部转发到目标保护端点",
            ))

        # 2. 现代云原生中间件穿透头 (Next.js / Nginx Accel)
        mw_headers = dict(headers)
        mw_headers["X-Middleware-Subrequest"] = "1"
        variants.append(TransformationVariant(
            variant_id="F3_NEXTJS_MIDDLEWARE_SUBREQUEST",
            family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
            method=method,
            url=url,
            headers=mw_headers,
            payload=dict(payload),
            rationale="注入 Next.js / Edge 网关内部子请求标记头 X-Middleware-Subrequest: 1",
            expected_effect="欺骗边缘中间件跳过外部路由鉴权守卫",
        ))

        # 3. 全量主流 CDN & 反代客户端真实 IP 伪装头 (nomore403 / NoMoreForbidden 规则汇集)
        ip_headers = [
            ("X-Custom-IP-Authorization", "X_CUSTOM_IP_AUTH"),
            ("X-Forwarded-For", "X_FORWARDED_FOR"),
            ("X-Host", "X_HOST"),
            ("X-Forwarded-Host", "X_FORWARDED_HOST"),
            ("X-Forwarded-Server", "X_FORWARDED_SERVER"),
            ("X-Remote-IP", "X_REMOTE_IP"),
            ("X-Client-IP", "X_CLIENT_IP"),
            ("X-Real-IP", "X_REAL_IP"),
            ("X-Original-Remote-Addr", "X_ORIGINAL_REMOTE_ADDR"),
            ("CF-Connecting-IP", "CF_CONNECTING_IP"),
            ("True-Client-IP", "TRUE_CLIENT_IP"),
        ]

        for h_name, vid_prefix in ip_headers:
            for ip_val in cls.TRUST_IP_PAYLOADS:
                h_spoof = dict(headers)
                h_spoof[h_name] = ip_val
                if ip_val.startswith("http://"):
                    clean_val_id = "HTTP_" + ip_val.replace("http://", "").replace(":", "_").replace(".", "_")
                elif ":" in ip_val:
                    clean_val_id = ip_val.replace(":", "_PORT_").replace(".", "_")
                else:
                    clean_val_id = ip_val.replace(".", "_")

                variants.append(TransformationVariant(
                    variant_id=f"F3_{vid_prefix}_{clean_val_id}",
                    family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
                    method=method,
                    url=url,
                    headers=h_spoof,
                    payload=dict(payload),
                    rationale=f"向请求头注入内网信任凭证 [{h_name}: {ip_val}]",
                    expected_effect="欺骗应用层的客户端 IP 校验，命中内部管理白名单",
                ))

        # 4. RFC 7239 标准 Forwarded 标头
        h_rfc_forwarded = dict(headers)
        h_rfc_forwarded["Forwarded"] = "for=127.0.0.1;proto=https;by=127.0.0.1"
        variants.append(TransformationVariant(
            variant_id="F3_RFC7239_FORWARDED",
            family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
            method=method,
            url=url,
            headers=h_rfc_forwarded,
            payload=dict(payload),
            rationale="注入 RFC 7239 标准多字段代理头 Forwarded: for=127.0.0.1;proto=https;by=127.0.0.1",
            expected_effect="命中遵循 RFC 标准的反向代理内部来源放行规则",
        ))

        return variants

    @classmethod
    def generate_all(
        cls,
        url: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        target_verb: Optional[str] = None,
        families: Optional[Set[TransformationFamily]] = None,
    ) -> List[TransformationVariant]:
        """
        组合生成器：一键生成各家族变异体并执行去重对账
        """
        h = dict(headers or {})
        p = dict(payload or {})
        active_families = families or {
            TransformationFamily.F1_PATH_NORMALIZATION,
            TransformationFamily.F2_METHOD_SEMANTICS,
            TransformationFamily.F3_HEADER_TRUST_CONTEXT,
        }

        variants: List[TransformationVariant] = []
        if TransformationFamily.F1_PATH_NORMALIZATION in active_families:
            variants.extend(cls.generate_f1_path_variants(url, method, h, p))
        if TransformationFamily.F2_METHOD_SEMANTICS in active_families:
            variants.extend(cls.generate_f2_method_variants(url, method, h, p, target_verb=target_verb))
        if TransformationFamily.F3_HEADER_TRUST_CONTEXT in active_families:
            variants.extend(cls.generate_f3_header_trust_variants(url, method, h, p))

        # 确定性去重：依据 (method, url, headers_fingerprint) 保持纯净
        seen: Set[str] = set()
        deduped: List[TransformationVariant] = []
        for v in variants:
            h_str = "|".join(f"{k}:{v.headers[k]}" for k in sorted(v.headers.keys()))
            fp = f"{v.method}:{v.url}:{h_str}"
            if fp not in seen:
                seen.add(fp)
                deduped.append(v)

        return deduped

# ==========================================================================
# 9. 语义等价性与微观物理差分 (Original semantic_models.py)
# ==========================================================================
class ThreeValuedLogic(str, Enum):
    """三值逻辑维度断言"""
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class EquivalenceVerdict(str, Enum):
    """
    语义等价最终判决（对齐规格书第 12.2 节：严禁强制二元 True/False）
    """
    SAME_RESOURCE = "SAME_RESOURCE"            # 实锤触达同一受保护目标业务资源
    DIFFERENT_RESOURCE = "DIFFERENT_RESOURCE"  # 偏移至公开首页、登录页、软404或其他非目标资源
    UNKNOWN = "UNKNOWN"                        # 证据不充分（如裸 200 且无业务特征），拒绝假定放行


@dataclass
class SemanticDimensions:
    """
    六维资源正交等价性评估（规格书第 12.3 节）
    """
    route_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    method_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    parameter_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    identity_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    action_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    business_effect_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN

    def to_dict(self) -> Dict[str, str]:
        return {k: v.value for k, v in asdict(self).items()}


@dataclass
class DifferentialObservation:
    """
    基线拒绝响应与变异探测响应之间的微观物理差分（规格书第 13 节）
    """
    status_delta: int
    body_length_delta: int
    body_hash_changed: bool
    content_type_changed: bool
    location_delta: Optional[str] = None
    redirect_to_auth_barrier: bool = False
    body_similarity_to_baseline: float = 0.0
    body_similarity_to_public_root: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticEquivalenceResult:
    """
    语义等价综合判定报告实体
    """
    verdict: EquivalenceVerdict
    dimensions: SemanticDimensions
    differential: DifferentialObservation
    rationale: str
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "dimensions": self.dimensions.to_dict(),
            "differential": self.differential.to_dict(),
            "rationale": self.rationale,
            "confidence": self.confidence,
        }


class SemanticEquivalenceEvaluator:
    """
    Invar 语义等价判决器
    负责断言探测变异体是否真正触达了保护目标本身，彻底消除 200 虚假绕过
    """

    LOGIN_LOCATION_KEYWORDS: Set[str] = {
        "/login", "/auth", "/signin", "/sso", "/oauth", "login.html", "cas/login"
    }

    LOGIN_BODY_PATTERNS: List[re.Pattern] = [
        re.compile(r'<form[^>]+(?:login|auth|signin)', re.IGNORECASE),
        re.compile(r'type=["\']password["\']', re.IGNORECASE),
        re.compile(r'(?:统一身份认证|登录系统|Sign In|User Login)', re.IGNORECASE),
    ]

    GENERIC_404_PATTERNS: List[re.Pattern] = [
        re.compile(r'(?:Page Not Found|404 Not Found|页面未找到|资源不存在)', re.IGNORECASE),
    ]

    PUBLIC_ROOT_SIMILARITY_THRESHOLD: float = 0.85

    @classmethod
    def evaluate(
        cls,
        baseline: DenialObservation,
        candidate: DenialObservation,
        variant: TransformationVariant,
        expected_resource_markers: Optional[List[str]] = None,
        public_root_preview: Optional[str] = None,
    ) -> SemanticEquivalenceResult:
        # 1. 计算微观物理差分
        status_delta = candidate.status_code - baseline.status_code
        len_base = len(baseline.body_preview)
        len_cand = len(candidate.body_preview)
        body_length_delta = len_cand - len_base
        body_hash_changed = candidate.body_hash != baseline.body_hash
        content_type_changed = candidate.content_type != baseline.content_type
        location = candidate.redirect_url or candidate.response_headers.get("location")

        # 差分相似度比对
        sim_to_baseline = difflib.SequenceMatcher(
            None, baseline.body_preview, candidate.body_preview
        ).ratio()

        sim_to_root = 0.0
        if public_root_preview is not None:
            sim_to_root = difflib.SequenceMatcher(
                None, candidate.body_preview, public_root_preview
            ).ratio()

        # 2. 检查是否重定向/阻断在身份认证关卡 (Auth Barrier)
        redirect_to_auth = False
        if location:
            loc_lower = location.lower()
            if any(k in loc_lower for k in cls.LOGIN_LOCATION_KEYWORDS):
                redirect_to_auth = True

        if not redirect_to_auth and candidate.status_code in {200, 401}:
            for pat in cls.LOGIN_BODY_PATTERNS:
                if pat.search(candidate.body_preview):
                    redirect_to_auth = True
                    break

        differential = DifferentialObservation(
            status_delta=status_delta,
            body_length_delta=body_length_delta,
            body_hash_changed=body_hash_changed,
            content_type_changed=content_type_changed,
            location_delta=location,
            redirect_to_auth_barrier=redirect_to_auth,
            body_similarity_to_baseline=round(sim_to_baseline, 4),
            body_similarity_to_public_root=round(sim_to_root, 4),
        )

        dims = SemanticDimensions()

        # 3. 门禁分支 A：命中登录关卡，判定为 DIFFERENT_RESOURCE
        if redirect_to_auth:
            dims.route_equivalent = ThreeValuedLogic.NO
            dims.identity_equivalent = ThreeValuedLogic.NO
            return SemanticEquivalenceResult(
                verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                dimensions=dims,
                differential=differential,
                rationale="变异请求被引导至身份认证关卡（登录网关/表单），并未穿透至受保护目标资源",
                confidence=0.98,
            )

        # 4. 门禁分支 B：命中公共首页回退（解决 X-Rewrite-URL 引起的 200 误报）
        if (
            public_root_preview is not None
            and sim_to_root >= cls.PUBLIC_ROOT_SIMILARITY_THRESHOLD
            and 200 <= candidate.status_code < 300
        ):
            dims.route_equivalent = ThreeValuedLogic.NO
            dims.identity_equivalent = ThreeValuedLogic.NO
            return SemanticEquivalenceResult(
                verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                dimensions=dims,
                differential=differential,
                rationale=f"候选响应与站点公共根路由 (/) 页面高度重合 (相似度 {sim_to_root:.2f})，系网关重写失效后的公共页面回退",
                confidence=0.95,
            )

        # 5. 门禁分支 C：软 404 或未授权页面
        if candidate.status_code in {404, 400}:
            dims.route_equivalent = ThreeValuedLogic.NO
            return SemanticEquivalenceResult(
                verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                dimensions=dims,
                differential=differential,
                rationale=f"候选探测返回状态码 HTTP {candidate.status_code}，资源路径在应用层未被识别或未分派路由",
                confidence=0.90,
            )

        for pat in cls.GENERIC_404_PATTERNS:
            if pat.search(candidate.body_preview):
                dims.route_equivalent = ThreeValuedLogic.NO
                return SemanticEquivalenceResult(
                    verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                    dimensions=dims,
                    differential=differential,
                    rationale="响应正文包含明显的软 404 / 页面未找到标识",
                    confidence=0.92,
                )

        # 6. 门禁分支 D：业务资源标识精准核验
        if expected_resource_markers:
            matched_markers = [m for m in expected_resource_markers if m in candidate.body_preview]
            if matched_markers:
                dims.route_equivalent = ThreeValuedLogic.YES
                dims.identity_equivalent = ThreeValuedLogic.YES
                dims.action_equivalent = ThreeValuedLogic.YES
                return SemanticEquivalenceResult(
                    verdict=EquivalenceVerdict.SAME_RESOURCE,
                    dimensions=dims,
                    differential=differential,
                    rationale=f"成功匹配受保护目标的特征业务标识 [{', '.join(matched_markers)}]，证实已准确触达受控业务实体",
                    confidence=0.99,
                )
            else:
                dims.identity_equivalent = ThreeValuedLogic.NO
                return SemanticEquivalenceResult(
                    verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                    dimensions=dims,
                    differential=differential,
                    rationale="候选响应虽返回 2xx，但缺失目标端点声明的所有预期业务特征标识，判定为非目标资源响应",
                    confidence=0.88,
                )

        # 7. 门禁分支 E：无任何业务特征参考时的裸 200（严格三值逻辑，拒绝假定成功）
        if 200 <= candidate.status_code < 300:
            dims.route_equivalent = ThreeValuedLogic.UNKNOWN
            dims.identity_equivalent = ThreeValuedLogic.UNKNOWN
            return SemanticEquivalenceResult(
                verdict=EquivalenceVerdict.UNKNOWN,
                dimensions=dims,
                differential=differential,
                rationale="候选响应返回 2xx，但调用方未提供业务实体特征参考且正文无明显标识，依据三值逻辑置为 UNKNOWN 待核验",
                confidence=0.50,
            )

        # 兜底
        return SemanticEquivalenceResult(
            verdict=EquivalenceVerdict.UNKNOWN,
            dimensions=dims,
            differential=differential,
            rationale=f"无法依据当前差分确证等价性（状态码 {candidate.status_code}）",
            confidence=0.30,
        )

# ==========================================================================
# 10. 科学证据链与终审门禁 (Original evidence_models.py)
# ==========================================================================
class EvidenceVerdict(str, Enum):
    """
    证据链最终科学裁决状态（对齐规格书第 14.1 节与状态机第 15 节）
    """
    CONFIRMED = "CONFIRMED"                    # 经过重放与独立复核实锤的漏洞
    CANDIDATE = "CANDIDATE"                    # 具备充分实证但尚未完成独立复核的候选事实
    INCONCLUSIVE = "INCONCLUSIVE"              # 重放不稳定、语义存疑或证据不闭环
    REJECTED = "REJECTED"                      # 确认未突破安全底线或语义不等价（误报消除）
    RATE_LIMITED = "RATE_LIMITED"              # 遭遇频控熔断，保留待测状态
    TRANSPORT_FAILED = "TRANSPORT_FAILED"      # 网络/传输异常，严禁归为无漏洞
    OUT_OF_SCOPE = "OUT_OF_SCOPE"              # 越界拦截，严禁未授权测试


class EvidenceGateError(ValueError):
    """当尝试在不满足科学前置谓词的情况下强行确权为 CONFIRMED 时抛出"""
    pass


@dataclass
class ReplayRecord:
    """
    同态物理发包重放检验事实（证明漏洞可稳定复现）
    """
    total_replays: int
    successful_replays: int
    is_stable: bool
    reproduced_status_codes: List[int] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceChain:
    """
    六层全景证据链实体（对齐规格书第 14 节 Layer 0 ~ Layer 6）
    """
    chain_id: str
    target_domain: str
    is_scope_verified: bool

    # Layer 1: 基线拒绝事实
    baseline_observation: DenialObservation

    # Layer 2: 实施的物理变换变体
    applied_variant: TransformationVariant

    # Layer 3: 候选物理发包观测
    candidate_observation: DenialObservation

    # Layer 4: 微观物理差分与语义等价判定
    semantic_result: SemanticEquivalenceResult

    # Layer 5: 安全不变量与重放验真事实
    security_invariant_violated: bool
    invariant_rationale: str
    replay_record: Optional[ReplayRecord] = None
    independent_verified: bool = False
    verifier_id: Optional[str] = None

    # Layer 6: 最终判定与推论
    verdict: EvidenceVerdict = EvidenceVerdict.CANDIDATE
    verdict_rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "target_domain": self.target_domain,
            "is_scope_verified": self.is_scope_verified,
            "baseline_observation": self.baseline_observation.to_dict(),
            "applied_variant": self.applied_variant.to_dict(),
            "candidate_observation": self.candidate_observation.to_dict(),
            "semantic_result": self.semantic_result.to_dict(),
            "security_invariant_violated": self.security_invariant_violated,
            "invariant_rationale": self.invariant_rationale,
            "replay_record": self.replay_record.to_dict() if self.replay_record else None,
            "independent_verified": self.independent_verified,
            "verifier_id": self.verifier_id,
            "verdict": self.verdict.value,
            "verdict_rationale": self.verdict_rationale,
        }


class EvidenceGate:
    """
    Invar 科学证据准入与晋级终审门禁 (Evidence Gate)
    对标顶级同行评审标准，执行绝对客观、确定性的谓词裁决
    """

    @classmethod
    def evaluate_verdict(cls, chain: EvidenceChain) -> EvidenceVerdict:
        # 1. 前置谓词：授权范围检验 (Scope Verification)
        if not chain.is_scope_verified:
            return EvidenceVerdict.OUT_OF_SCOPE

        # 2. 前置谓词：异常与频控检测 (Rate Limit & Transport Failure)
        if chain.candidate_observation.transport_error or chain.baseline_observation.transport_error:
            return EvidenceVerdict.TRANSPORT_FAILED
        if chain.candidate_observation.status_code == 429:
            return EvidenceVerdict.RATE_LIMITED

        # 3. 前置谓词：语义等价性检验 (Semantic Equivalence)
        sem_verdict = chain.semantic_result.verdict
        if sem_verdict == EquivalenceVerdict.DIFFERENT_RESOURCE:
            return EvidenceVerdict.REJECTED
        if sem_verdict == EquivalenceVerdict.UNKNOWN:
            return EvidenceVerdict.INCONCLUSIVE

        # 4. 前置谓词：安全底线击穿检验 (Security Invariant)
        if not chain.security_invariant_violated:
            return EvidenceVerdict.REJECTED

        # 5. 前置谓词：重放稳定性检验 (Replay Stability)
        if chain.replay_record is None or not chain.replay_record.is_stable:
            return EvidenceVerdict.INCONCLUSIVE

        # 6. 前置谓词：无偏独立第三方复核 (Independent Verification)
        if not chain.independent_verified:
            # 事实完备但尚缺独立复核签名，收敛为高置信度 CANDIDATE
            return EvidenceVerdict.CANDIDATE

        # 7. 全量通过 8 大谓词断言，正式确权为 CONFIRMED 实锤发现
        return EvidenceVerdict.CONFIRMED

    @classmethod
    def assert_confirmed(cls, chain: EvidenceChain) -> None:
        actual_verdict = cls.evaluate_verdict(chain)
        if actual_verdict != EvidenceVerdict.CONFIRMED:
            raise EvidenceGateError(
                f"EvidenceChain failed confirmation predicates! Current verdict: [{actual_verdict.value}]. "
                "Reasons may include unverified scope, unstable replay, unviolated invariant, or missing independent review."
            )

# ==========================================================================
# 11. 可观测性科研事件与汇点协议 (Observability Events & Sink Protocol)
# ==========================================================================
class ResearchEventType(str, Enum):
    """
    强类型科研事件类型枚举 (对齐 pi-agent-core AgentEvent)
    """
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    DENIAL_CLASSIFIED = "denial_classified"
    VARIANT_SELECTED = "variant_selected"
    PROBE_DISPATCHED = "probe_dispatched"
    PROBE_RESPONDED = "probe_responded"
    DIFFERENTIAL_COMPUTED = "differential_computed"
    SEMANTIC_EVALUATED = "semantic_evaluated"
    REPLAY_STARTED = "replay_started"
    REPLAY_COMPLETED = "replay_completed"
    STEERING_INJECTED = "steering_injected"
    LLM_REASONING_STARTED = "llm_reasoning_started"
    LLM_REASONING_COMPLETED = "llm_reasoning_completed"
    LLM_REASONING_FAILED = "llm_reasoning_failed"
    ABORTED = "aborted"


@dataclass(frozen=True)
class ResearchEvent:
    """
    可观测性事件实体 (Push-based Event)
    支持直接序列化并通过 IPC 流式推送到终端或上层调度器
    """
    event_type: ResearchEventType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


# 事件汇点接口定义
from typing import Callable
ResearchEventSink = Callable[[ResearchEvent], None]

# ==========================================================================
# 12. 静态分析领域常量 (Static Analysis Domain Constants)
# ==========================================================================
IDOR_KEYWORDS: Set[str] = {
    "id", "user_id", "uid", "account_id", "order_id",
    "member_id", "customer_id", "tenant_id", "doc_id"
}

# ==========================================================================
# 13. 威胁模型一级契约 (First-Class Threat Model Contract)
# ==========================================================================
@dataclass(frozen=True)
class AttackerProfile:
    """
    攻击者身份与主体画像 (Attacker Profile)
    明确威胁发起者的身份凭据状态、主体权限等级与能力范围 (不可变不可篡改)
    """
    role: str  # 例如: "anonymous_external", "authenticated_tenant", "internal_unprivileged"
    token_ref: Optional[str] = None
    description: str = ""
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttackerProfile":
        return cls(**data)


@dataclass
class ThreatModel:
    """
    Invar 权威威胁模型一级契约 (Canonical Threat Model)
    对标 Anthropic Reference Harness 与 Strix 黄金标准，
    在任何 Agent 扫描与假说推演之前，确立目标系统攻击面、主体凭据、信任边界与安全不变量底线。
    """
    model_id: str
    title: str
    attacker: AttackerProfile
    assets: List[str] = field(default_factory=list)
    trust_boundaries: List[str] = field(default_factory=list)
    entrypoints: List[str] = field(default_factory=list)
    expected_controls: List[str] = field(default_factory=list)
    invariants: List[SecurityInvariant] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "title": self.title,
            "attacker": self.attacker.to_dict(),
            "assets": list(self.assets),
            "trust_boundaries": list(self.trust_boundaries),
            "entrypoints": list(self.entrypoints),
            "expected_controls": list(self.expected_controls),
            "invariants": [
                {
                    "invariant_type": inv.invariant_type,
                    "statement": inv.statement,
                }
                for inv in self.invariants
            ],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreatModel":
        data_copy = dict(data)
        raw_attacker = data_copy.get("attacker", {})
        data_copy["attacker"] = (
            AttackerProfile.from_dict(raw_attacker)
            if isinstance(raw_attacker, dict)
            else raw_attacker
        )
        data_copy["invariants"] = [
            SecurityInvariant(**inv) if isinstance(inv, dict) else inv
            for inv in data_copy.get("invariants", [])
        ]
        return cls(**data_copy)

    def validate(self) -> List[str]:
        """
        断言威胁模型核心结构合法性与完备性
        """
        errors = []
        if not self.model_id or not str(self.model_id).strip():
            errors.append("ThreatModel model_id cannot be empty")
        if not self.title or not str(self.title).strip():
            errors.append("ThreatModel title cannot be empty")
        if not self.attacker or not self.attacker.role:
            errors.append("ThreatModel attacker role must be specified")
        if not self.assets:
            errors.append("ThreatModel must specify at least one protected asset")
        if not self.trust_boundaries:
            errors.append("ThreatModel must define at least one trust boundary")
        return errors

    def derive_hypothesis(
        self,
        hypothesis_id: str,
        statement: str,
        rationale: str = "",
    ) -> Hypothesis:
        """
        从当前威胁模型受控派生出标准的科研假说 (Research Hypothesis)，建立明确溯源依据
        """
        prefix = f"[ThreatModel: {self.model_id}] (Attacker: {self.attacker.role})"
        full_rationale = f"{prefix} {rationale}".strip()
        return Hypothesis(
            hypothesis_id=hypothesis_id,
            statement=statement,
            rationale=full_rationale,
            status="PROPOSED",
        )

