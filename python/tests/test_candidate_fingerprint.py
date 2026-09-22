import unittest

from harness.candidate_models import (
    Candidate,
    CandidateConsolidator,
    CandidateFingerprint,
    CandidateStatus,
    CanonicalFactors,
    Condition,
    TraceStep,
)


class CandidateFingerprintTests(unittest.TestCase):
    def setUp(self):
        self.factors_a = CanonicalFactors(
            attack_class="authorization",
            boundary="tenant_isolation",
            sink_component="orders_mutation_service",
            missing_control="missing_owner_check",
        )
        self.factors_b = CanonicalFactors(
            attack_class="authorization",
            boundary="tenant_isolation",
            sink_component="orders_mutation_service",
            missing_control="missing_owner_check",
        )
        self.factors_different = CanonicalFactors(
            attack_class="destructive_guard",
            boundary="confirmation_check",
            sink_component="orders_mutation_service",
            missing_control="missing_confirm_param",
        )

    def test_deterministic_fingerprint_generation(self):
        """不变性：相同规范因子在任何环境/多次调用下生成的指纹绝对一致"""
        fp1 = CandidateFingerprint.from_factors(self.factors_a)
        fp2 = CandidateFingerprint.from_factors(self.factors_b)

        self.assertEqual(fp1.value, fp2.value)
        self.assertEqual(fp1.algorithm, "v1-canonical-factors")
        self.assertEqual(fp1.canonical_factors["missing_control"], "missing_owner_check")

    def test_different_root_causes_produce_different_fingerprints(self):
        """不变性：不同攻防类型或缺失校验产生正交的唯一指纹"""
        fp_idor = CandidateFingerprint.from_factors(self.factors_a)
        fp_destruct = CandidateFingerprint.from_factors(self.factors_different)

        self.assertNotEqual(fp_idor.value, fp_destruct.value)
        self.assertIn("authorization", fp_idor.value)
        self.assertIn("destructive_guard", fp_destruct.value)

    def test_fingerprint_ignores_line_and_agent_and_severity(self):
        """铁律验证：指纹严禁受 Agent ID、行号或严重性影响"""
        # 两名不同的 Hunter 在不同的代码行号与严重度下提议同一根因
        cand_hunter_1 = Candidate(
            fingerprint=CandidateFingerprint.from_factors(self.factors_a),
            title="Hunter 1 Candidate",
            description="Found at line 100",
            claimed_root_cause="Missing owner check",
            endpoint_refs=["GET:/api/orders/detail"],
            trace=[TraceStep("entrypoint", "api/orders.js", 100, "getDetail", "call")],
            metadata={"agent_id": "hunter-alpha", "severity": "HIGH"},
        )
        cand_hunter_2 = Candidate(
            fingerprint=CandidateFingerprint.from_factors(self.factors_a),
            title="Hunter 2 Candidate",
            description="Found at line 250",
            claimed_root_cause="Missing owner check",
            endpoint_refs=["PUT:/api/orders/update"],
            trace=[TraceStep("entrypoint", "api/orders.js", 250, "updateOrder", "call")],
            metadata={"agent_id": "hunter-beta", "severity": "CRITICAL"},
        )

        self.assertEqual(cand_hunter_1.fingerprint.value, cand_hunter_2.fingerprint.value)

    def test_candidate_consolidator_merges_duplicates_across_endpoints(self):
        """验证多 Hunter 候选去重合并器：相同指纹候选合并端点与追踪链"""
        fp = CandidateFingerprint.from_factors(self.factors_a)
        c1 = Candidate(
            fingerprint=fp,
            title="BOLA in Orders",
            description="Found by agent 1",
            claimed_root_cause="Missing owner check",
            endpoint_refs=["GET:/api/orders/detail"],
            coverage_refs=["COV-01"],
            evidence_refs=["EV-001"],
            status=CandidateStatus.PROPOSED,
        )
        c2 = Candidate(
            fingerprint=fp,
            title="BOLA in Orders",
            description="Found by agent 2",
            claimed_root_cause="Missing owner check",
            endpoint_refs=["POST:/api/orders/cancel"],
            coverage_refs=["COV-02"],
            evidence_refs=["EV-002"],
            status=CandidateStatus.SUPPORTED,
        )

        consolidated = CandidateConsolidator.consolidate([c1, c2])

        self.assertEqual(len(consolidated), 1)
        merged = consolidated[0]
        self.assertEqual(merged.fingerprint.value, fp.value)
        self.assertEqual(merged.endpoint_refs, ["GET:/api/orders/detail", "POST:/api/orders/cancel"])
        self.assertEqual(merged.coverage_refs, ["COV-01", "COV-02"])
        self.assertEqual(merged.evidence_refs, ["EV-001", "EV-002"])
        self.assertEqual(merged.status, CandidateStatus.SUPPORTED)

    def test_serialization_and_roundtrip(self):
        """验证候选模型无损序列化与还原"""
        fp = CandidateFingerprint.from_factors(self.factors_a)
        candidate = Candidate(
            fingerprint=fp,
            title="Test Candidate",
            description="Desc",
            claimed_root_cause="Root cause",
            endpoint_refs=["GET:/api/test"],
            trace=[TraceStep("sink", "service.js", 42, "mutate", "sink execution")],
            conditions=[Condition("COND-01", "Auth bypass")],
        )

        d = candidate.to_dict()
        restored = Candidate.from_dict(d)

        self.assertEqual(restored.fingerprint.value, fp.value)
        self.assertEqual(len(restored.trace), 1)
        self.assertEqual(restored.trace[0].file_path, "service.js")
        self.assertEqual(restored.conditions[0].condition_id, "COND-01")


if __name__ == "__main__":
    unittest.main()
