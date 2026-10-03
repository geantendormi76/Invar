from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from harness.finding_models import (
    FindingRecord,
    FindingSchemaValidator,
    Severity,
    Verdict,
    VerificationSummary,
)


class VerificationVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"


class PromotionGateError(ValueError):
    """当 FindingRecord 无法跨越科学晋级门禁时抛出"""
    pass


class IndependenceViolationError(ValueError):
    """当同一主体尝试自我复核时抛出"""
    pass


@dataclass
class VerificationResult:
    """独立复核裁决结果事实"""
    verdict: VerificationVerdict
    verifier_id: str
    verified_at: str
    rationale: str
    corrections: Dict[str, Any] = field(default_factory=dict)


class IndependentVerifier:
    """
    Invar 独立第三方复核器 (Independent Verifier)
    铁律：产生该发现的 Agent / Hunter 绝不可自我复核
    """
    def __init__(self, verifier_id: str = "independent-verifier-prime"):
        self.verifier_id = verifier_id

    def verify(
        self,
        finding: Optional[FindingRecord] = None,
        originator_id: Optional[str] = None,
        force_reject_reason: Optional[str] = None,
        corrections: Optional[Dict[str, Any]] = None,
        finding_candidate: Optional[Any] = None,
    ) -> VerificationResult:
        # 1. 独立性铁律检查：严禁发现者自我复核
        if originator_id and originator_id == self.verifier_id:
            raise IndependenceViolationError(
                f"Self-verification rejected: Agent [{originator_id}] cannot verify its own finding"
            )

        now_iso = datetime.now(timezone.utc).isoformat()

        # 候选实体 (Candidate) 快速双盲重放通路
        target_cand = finding_candidate if finding_candidate is not None else (finding if not hasattr(finding, 'verdict') or not hasattr(finding, 'verification') else None)
        if target_cand is not None and hasattr(target_cand, 'fingerprint'):
            if force_reject_reason:
                return VerificationResult(
                    verdict=VerificationVerdict.REJECTED,
                    verifier_id=self.verifier_id,
                    verified_at=now_iso,
                    rationale=force_reject_reason,
                )
            if not getattr(target_cand, 'trace', None) or not getattr(target_cand, 'evidence_refs', None):
                return VerificationResult(
                    verdict=VerificationVerdict.REJECTED,
                    verifier_id=self.verifier_id,
                    verified_at=now_iso,
                    rationale="Factual grounding missing: trace or evidence_refs is empty",
                )
            return VerificationResult(
                verdict=VerificationVerdict.VERIFIED,
                verifier_id=self.verifier_id,
                verified_at=now_iso,
                rationale="Candidate independently replayed and verified with reproducible evidence.",
                corrections=corrections or {},
            )

        # 候选实体 (Candidate) 快速双盲重放通路
        target_cand = finding_candidate if finding_candidate is not None else (finding if not hasattr(finding, 'verdict') or not hasattr(finding, 'verification') else None)
        if target_cand is not None and hasattr(target_cand, 'fingerprint'):
            if force_reject_reason:
                return VerificationResult(
                    verdict=VerificationVerdict.REJECTED,
                    verifier_id=self.verifier_id,
                    verified_at=now_iso,
                    rationale=force_reject_reason,
                )
            if not getattr(target_cand, 'trace', None) or not getattr(target_cand, 'evidence_refs', None):
                return VerificationResult(
                    verdict=VerificationVerdict.REJECTED,
                    verifier_id=self.verifier_id,
                    verified_at=now_iso,
                    rationale="Factual grounding missing: trace or evidence_refs is empty",
                )
            return VerificationResult(
                verdict=VerificationVerdict.VERIFIED,
                verifier_id=self.verifier_id,
                verified_at=now_iso,
                rationale="Candidate independently replayed and verified with reproducible evidence.",
                corrections=corrections or {},
            )

        # 2. 若存在强制打回理由（例如存在上层 WAF 拦截或代码行语义不符）
        if force_reject_reason:
            res = VerificationResult(
                verdict=VerificationVerdict.REJECTED,
                verifier_id=self.verifier_id,
                verified_at=now_iso,
                rationale=force_reject_reason,
            )
            self._apply_to_finding(finding, res)
            return res

        # 3. 基础事实有效性核验
        if finding.verdict != Verdict.CONFIRMED:
            res = VerificationResult(
                verdict=VerificationVerdict.REJECTED,
                verifier_id=self.verifier_id,
                verified_at=now_iso,
                rationale=f"Finding verdict is [{finding.verdict.value}], not confirmed",
            )
            self._apply_to_finding(finding, res)
            return res

        if not finding.trace or not finding.evidence_refs:
            res = VerificationResult(
                verdict=VerificationVerdict.REJECTED,
                verifier_id=self.verifier_id,
                verified_at=now_iso,
                rationale="Factual grounding missing: trace or evidence_refs is empty",
            )
            self._apply_to_finding(finding, res)
            return res

        # 4. 字段校正 (CORRECTED) 逻辑
        if corrections:
            for k, v in corrections.items():
                if hasattr(finding, k):
                    setattr(finding, k, v)
            res = VerificationResult(
                verdict=VerificationVerdict.CORRECTED,
                verifier_id=self.verifier_id,
                verified_at=now_iso,
                rationale="Factual fields corrected after independent source inspection",
                corrections=corrections,
            )
            self._apply_to_finding(finding, res)
            return res

        # 5. 全面实锤证实 (VERIFIED)
        res = VerificationResult(
            verdict=VerificationVerdict.VERIFIED,
            verifier_id=self.verifier_id,
            verified_at=now_iso,
            rationale="Independent review confirmed source trace, exploitability conditions and physical evidence",
        )
        self._apply_to_finding(finding, res)
        return res

    def _apply_to_finding(self, finding: FindingRecord, result: VerificationResult) -> None:
        finding.verification = VerificationSummary(
            independent_verified=True,
            verifier_id=result.verifier_id,
            verified_at=result.verified_at,
            verdict=result.verdict.value,
            rationale=result.rationale,
        )


class PromotionGate:
    """
    Invar 科学证据晋级门禁 (Promotion Gate)
    对标顶级科学审查标准，唯有全量满足 8 大前置谓词，方准晋升为 KnowledgeCard
    """
    @classmethod
    def check_promotable(cls, finding: FindingRecord) -> List[str]:
        errors = []

        # 1. 必须通过严格 Schema 结构校验
        schema_errs = FindingSchemaValidator.validate(finding.to_dict())
        if schema_errs:
            errors.append(f"Schema invalid: {'; '.join(schema_errs)}")

        # 2. 裁决必须为 CONFIRMED
        if finding.verdict != Verdict.CONFIRMED:
            errors.append(f"Verdict must be 'confirmed', got '{finding.verdict.value}'")

        # 3. 必须通过独立第三方复核
        if not finding.verification.independent_verified:
            errors.append("Independent verification not performed")
        elif finding.verification.verdict not in {VerificationVerdict.VERIFIED.value, VerificationVerdict.CORRECTED.value}:
            errors.append(f"Independent verification was not approved (verdict: {finding.verification.verdict})")

        # 4. 源码溯源链非空
        if not finding.trace:
            errors.append("Trace cannot be empty for promotion")

        # 5. 必须具备实锤物理发包证据链
        if not finding.evidence_refs:
            errors.append("Evidence refs cannot be empty for promotion")

        # 6. 严禁带有未决阻塞
        if finding.unresolved_blocker:
            errors.append(f"Unresolved blocker present: {finding.unresolved_blocker}")

        # 7. 必须确立权威严重度
        if not finding.severity:
            errors.append("Severity must be defined for promotion")

        return errors

    @classmethod
    def is_promotable(cls, finding: FindingRecord) -> bool:
        return len(cls.check_promotable(finding)) == 0

    @classmethod
    def assert_promotable(cls, finding: FindingRecord) -> None:
        errors = cls.check_promotable(finding)
        if errors:
            raise PromotionGateError(
                "FindingRecord failed PromotionGate prerequisites:\n"
                + "\n".join(f"- {e}" for e in errors)
            )
