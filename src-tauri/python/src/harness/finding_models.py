from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from harness.candidate_models import Candidate, Condition, TraceStep


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
