from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional
from harness.denial_models import DenialObservation
from harness.semantic_models import EquivalenceVerdict, SemanticEquivalenceResult
from harness.transformation_models import TransformationVariant


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
