import unittest

from agent.knowledge_promoter import KnowledgeCard, KnowledgePromoter
from harness.candidate_models import (
    Candidate,
    CandidateFingerprint,
    CanonicalFactors,
    Condition,
    TraceStep,
)
from harness.finding_models import (
    FindingRecord,
    Remediation,
    Severity,
    Verdict,
)
from harness.verification_gate import (
    IndependenceViolationError,
    IndependentVerifier,
    PromotionGate,
    PromotionGateError,
    VerificationVerdict,
)


class VerificationAndPromotionGateTests(unittest.TestCase):
    def setUp(self):
        self.factors = CanonicalFactors(
            attack_class="authorization",
            boundary="tenant_isolation",
            sink_component="orders_mutation_service",
            missing_control="missing_owner_check",
        )
        self.fp = CandidateFingerprint.from_factors(self.factors)
        self.candidate = Candidate(
            fingerprint=self.fp,
            title="BOLA in Orders Mutation",
            description="Tenant isolation broken",
            claimed_root_cause="Missing owner check",
            endpoint_refs=["POST:/api/orders/cancel"],
            coverage_refs=["COV-ORDERS-01"],
            evidence_refs=["EV-001"],
            trace=[TraceStep("sink", "src/controllers/order.js", 45, "cancel", "sink call")],
            conditions=[Condition("COND-01", "Cross-tenant ID passed")],
        )
        self.finding = FindingRecord.from_candidate(
            candidate=self.candidate,
            run_id="RUN-TEST-001",
            verdict=Verdict.CONFIRMED,
            severity=Severity.HIGH,
            root_cause="Missing owner check before cancellation mutation",
            remediation=Remediation("Verify ownership", "Check current user ID matches order.user_id"),
        )
        self.verifier = IndependentVerifier(verifier_id="verifier-fresh-context-01")

    def test_self_verification_rejected_by_independence_rule(self):
        """铁律验证：发现候选的原 Agent 绝不允许自我复核"""
        with self.assertRaises(IndependenceViolationError) as ctx:
            self.verifier.verify(self.finding, originator_id="verifier-fresh-context-01")
        self.assertIn("Self-verification rejected", str(ctx.exception))

    def test_independent_verifier_confirms_valid_finding(self):
        """验证无偏独立复核者成功实锤并签署复核意见"""
        res = self.verifier.verify(self.finding, originator_id="agent-hunter-alpha")
        self.assertEqual(res.verdict, VerificationVerdict.VERIFIED)
        self.assertTrue(self.finding.verification.independent_verified)
        self.assertEqual(self.finding.verification.verifier_id, "verifier-fresh-context-01")
        self.assertEqual(self.finding.verification.verdict, "VERIFIED")

    def test_independent_verifier_can_correct_fields(self):
        """验证独立复核者具有 field-level 修正权"""
        corrections = {"severity": Severity.CRITICAL}
        res = self.verifier.verify(self.finding, originator_id="agent-hunter-alpha", corrections=corrections)

        self.assertEqual(res.verdict, VerificationVerdict.CORRECTED)
        self.assertEqual(self.finding.severity, Severity.CRITICAL)

    def test_promotion_gate_blocks_unverified_finding(self):
        """门禁铁律：未获得第三方独立复核的记录，绝对禁止晋升为知识卡片"""
        self.assertFalse(self.finding.verification.independent_verified)
        with self.assertRaises(PromotionGateError) as ctx:
            KnowledgePromoter.promote_finding(self.finding)
        self.assertIn("Independent verification not performed", str(ctx.exception))

    def test_promotion_gate_blocks_needs_validation_finding(self):
        """门禁铁律：处于 needs_validation 存疑状态的记录绝对禁止晋升"""
        nv_finding = FindingRecord.from_candidate(
            candidate=self.candidate,
            run_id="RUN-TEST-001",
            verdict=Verdict.NEEDS_VALIDATION,
            unresolved_blocker="Awaiting dual tokens",
        )
        with self.assertRaises(PromotionGateError) as ctx:
            PromotionGate.assert_promotable(nv_finding)
        self.assertIn("Verdict must be 'confirmed'", str(ctx.exception))

    def test_promotion_gate_blocks_rejected_verification(self):
        """门禁铁律：被独立复核者打回 (REJECTED) 的记录绝对禁止晋升"""
        self.verifier.verify(
            self.finding,
            originator_id="agent-hunter-alpha",
            force_reject_reason="Mitigated by gateway WAF",
        )
        self.assertEqual(self.finding.verification.verdict, "REJECTED")

        with self.assertRaises(PromotionGateError) as ctx:
            KnowledgePromoter.promote_finding(self.finding)
        self.assertIn("was not approved", str(ctx.exception))

    def test_full_chain_from_finding_to_promoted_knowledge_card(self):
        """端到端科学闭环：Finding -> Independent Verification -> PromotionGate -> KnowledgeCard"""
        # 1. 独立第三方严格复核
        res = self.verifier.verify(self.finding, originator_id="agent-hunter-alpha")
        self.assertEqual(res.verdict, VerificationVerdict.VERIFIED)

        # 2. 晋级门禁检验通过
        self.assertTrue(PromotionGate.is_promotable(self.finding))

        # 3. 升华结晶为不可变 KnowledgeCard
        card = KnowledgePromoter.promote_finding(self.finding)
        self.assertIsInstance(card, KnowledgeCard)
        self.assertEqual(card.card_id, f"KC-{self.fp.value}")
        self.assertEqual(card.verification_state, "VERIFIED")
        self.assertEqual(card.confidence, 1.0)
        self.assertEqual(card.severity, "HIGH")
        self.assertIn("verifier-fresh-context-01", card.evidence_summary)
        self.assertIn("POST:/api/orders/cancel", card.provenance_task)


if __name__ == "__main__":
    unittest.main()
