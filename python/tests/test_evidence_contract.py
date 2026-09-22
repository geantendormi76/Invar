import unittest
from harness.denial_models import DenialObservation
from harness.evidence_models import (
    EvidenceChain,
    EvidenceGate,
    EvidenceGateError,
    EvidenceVerdict,
    ReplayRecord,
)
from harness.semantic_models import (
    DifferentialObservation,
    EquivalenceVerdict,
    SemanticDimensions,
    SemanticEquivalenceResult,
    ThreeValuedLogic,
)
from harness.transformation_models import TransformationFamily, TransformationVariant


class EvidenceContractTests(unittest.TestCase):
    """
    对齐《规格书 v1.0.0》第 14 节、15 节与 22.2 节的证据门禁契约测试
    """

    def setUp(self):
        self.baseline_403 = DenialObservation(
            status_code=403,
            response_headers={"server": "nginx"},
            body_preview="Access Denied",
        )
        self.variant = TransformationVariant(
            variant_id="F3_REWRITE_X_ORIGINAL_URL",
            family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
            method="GET",
            url="https://example.com/",
            headers={"X-Original-URL": "/api/v1/vault"},
        )
        self.candidate_200 = DenialObservation(
            status_code=200,
            response_headers={"content-type": "application/json"},
            body_preview='{"vault_key": "CONFIDENTIAL_DATA"}',
        )
        self.valid_semantic_result = SemanticEquivalenceResult(
            verdict=EquivalenceVerdict.SAME_RESOURCE,
            dimensions=SemanticDimensions(
                route_equivalent=ThreeValuedLogic.YES,
                identity_equivalent=ThreeValuedLogic.YES,
            ),
            differential=DifferentialObservation(
                status_delta=-203,
                body_length_delta=30,
                body_hash_changed=True,
                content_type_changed=True,
            ),
            rationale="Matched vault_key",
        )
        self.stable_replay = ReplayRecord(
            total_replays=3,
            successful_replays=3,
            is_stable=True,
            reproduced_status_codes=[200, 200, 200],
            rationale="100% reproducible",
        )

    def test_confirmed_only_when_all_prerequisites_met(self):
        """【契约 1】唯有全量满足 8 大科学前置谓词，方准确权为 CONFIRMED"""
        chain = EvidenceChain(
            chain_id="CHAIN-001",
            target_domain="example.com",
            is_scope_verified=True,
            baseline_observation=self.baseline_403,
            applied_variant=self.variant,
            candidate_observation=self.candidate_200,
            semantic_result=self.valid_semantic_result,
            security_invariant_violated=True,
            invariant_rationale="Confidential vault key disclosed without authentication",
            replay_record=self.stable_replay,
            independent_verified=True,
            verifier_id="independent-verifier-gamma",
        )
        verdict = EvidenceGate.evaluate_verdict(chain)
        self.assertEqual(verdict, EvidenceVerdict.CONFIRMED)
        # assert_confirmed 必须顺利通过无异常
        EvidenceGate.assert_confirmed(chain)

    def test_cannot_confirm_without_replay_stability(self):
        """【契约 2】偶发抖动或重放失败时，绝不误标实锤，必须降级为 INCONCLUSIVE"""
        unstable_replay = ReplayRecord(
            total_replays=3,
            successful_replays=1,
            is_stable=False,
            reproduced_status_codes=[200, 403, 500],
            rationale="Flaky response across identical requests",
        )
        chain = EvidenceChain(
            chain_id="CHAIN-002",
            target_domain="example.com",
            is_scope_verified=True,
            baseline_observation=self.baseline_403,
            applied_variant=self.variant,
            candidate_observation=self.candidate_200,
            semantic_result=self.valid_semantic_result,
            security_invariant_violated=True,
            invariant_rationale="Data disclosed",
            replay_record=unstable_replay,  # 重放不稳定
            independent_verified=True,
        )
        verdict = EvidenceGate.evaluate_verdict(chain)
        self.assertEqual(verdict, EvidenceVerdict.INCONCLUSIVE)
        with self.assertRaises(EvidenceGateError):
            EvidenceGate.assert_confirmed(chain)

    def test_cannot_confirm_without_semantic_equivalence(self):
        """【契约 3】语义不等价（命中登录页或公开首页）时，直接判决为 REJECTED"""
        diff_semantic = SemanticEquivalenceResult(
            verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
            dimensions=SemanticDimensions(),
            differential=DifferentialObservation(0, 0, False, False),
            rationale="Fallback to public home page",
        )
        chain = EvidenceChain(
            chain_id="CHAIN-003",
            target_domain="example.com",
            is_scope_verified=True,
            baseline_observation=self.baseline_403,
            applied_variant=self.variant,
            candidate_observation=self.candidate_200,
            semantic_result=diff_semantic,  # 语义不等价
            security_invariant_violated=True,
            invariant_rationale="",
            replay_record=self.stable_replay,
            independent_verified=True,
        )
        verdict = EvidenceGate.evaluate_verdict(chain)
        self.assertEqual(verdict, EvidenceVerdict.REJECTED)

    def test_cannot_confirm_without_scope_verification(self):
        """【契约 4】授权范围未核准时，强制输出 OUT_OF_SCOPE"""
        chain = EvidenceChain(
            chain_id="CHAIN-004",
            target_domain="unauthorized-target.org",
            is_scope_verified=False,  # 越界未授权
            baseline_observation=self.baseline_403,
            applied_variant=self.variant,
            candidate_observation=self.candidate_200,
            semantic_result=self.valid_semantic_result,
            security_invariant_violated=True,
            invariant_rationale="",
            replay_record=self.stable_replay,
            independent_verified=True,
        )
        verdict = EvidenceGate.evaluate_verdict(chain)
        self.assertEqual(verdict, EvidenceVerdict.OUT_OF_SCOPE)

    def test_rate_limit_and_transport_failure_states(self):
        """【契约 5】频控与断流必须映射为专属状态，严禁归纳为无漏洞"""
        obs_429 = DenialObservation(status_code=429)
        chain_rate = EvidenceChain(
            chain_id="CHAIN-005A",
            target_domain="example.com",
            is_scope_verified=True,
            baseline_observation=self.baseline_403,
            applied_variant=self.variant,
            candidate_observation=obs_429,
            semantic_result=self.valid_semantic_result,
            security_invariant_violated=True,
            invariant_rationale="",
        )
        self.assertEqual(EvidenceGate.evaluate_verdict(chain_rate), EvidenceVerdict.RATE_LIMITED)

        obs_transport_err = DenialObservation(status_code=0, transport_error="Connection timed out")
        chain_trans = EvidenceChain(
            chain_id="CHAIN-005B",
            target_domain="example.com",
            is_scope_verified=True,
            baseline_observation=self.baseline_403,
            applied_variant=self.variant,
            candidate_observation=obs_transport_err,
            semantic_result=self.valid_semantic_result,
            security_invariant_violated=True,
            invariant_rationale="",
        )
        self.assertEqual(EvidenceGate.evaluate_verdict(chain_trans), EvidenceVerdict.TRANSPORT_FAILED)

    def test_cannot_confirm_without_independent_verification(self):
        """【契约 6】未获独立复核签署前，只能止步于 CANDIDATE，绝不可擅自 CONFIRMED"""
        chain = EvidenceChain(
            chain_id="CHAIN-006",
            target_domain="example.com",
            is_scope_verified=True,
            baseline_observation=self.baseline_403,
            applied_variant=self.variant,
            candidate_observation=self.candidate_200,
            semantic_result=self.valid_semantic_result,
            security_invariant_violated=True,
            invariant_rationale="Vault key leaked",
            replay_record=self.stable_replay,
            independent_verified=False,  # 缺失独立复核
        )
        verdict = EvidenceGate.evaluate_verdict(chain)
        self.assertEqual(verdict, EvidenceVerdict.CANDIDATE)
        with self.assertRaises(EvidenceGateError):
            EvidenceGate.assert_confirmed(chain)


if __name__ == "__main__":
    unittest.main()
