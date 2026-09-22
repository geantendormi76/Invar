import unittest

from harness.candidate_models import (
    Candidate,
    CandidateFingerprint,
    CanonicalFactors,
    Condition,
    TraceStep,
)
from harness.finding_models import (
    Confidence,
    ExecutionRecord,
    FindingRecord,
    FindingSchemaError,
    FindingSchemaValidator,
    Remediation,
    Severity,
    Verdict,
)


class FindingRecordContractTests(unittest.TestCase):
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

    def test_confirmed_finding_satisfies_schema(self):
        """验证合规的 confirmed 发现记录顺利通过 Schema 检验"""
        finding = FindingRecord.from_candidate(
            candidate=self.candidate,
            run_id="RUN-TEST-001",
            verdict=Verdict.CONFIRMED,
            severity=Severity.HIGH,
            root_cause="Missing owner verification before database mutation",
            remediation=Remediation("Add auth guard", "Verify token sub matches order owner"),
        )
        finding_dict = finding.to_dict()

        errors = FindingSchemaValidator.validate(finding_dict)
        self.assertEqual(errors, [])
        self.assertEqual(finding.severity, Severity.HIGH)
        self.assertEqual(finding.verdict, Verdict.CONFIRMED)

    def test_needs_validation_strictly_rejects_severity(self):
        """铁律：needs_validation 状态绝对禁止携带 Severity 评级"""
        finding = FindingRecord.from_candidate(
            candidate=self.candidate,
            run_id="RUN-TEST-001",
            verdict=Verdict.NEEDS_VALIDATION,
            unresolved_blocker="Awaiting dual-token credential to verify tenant boundary",
        )
        finding_dict = finding.to_dict()
        # 正常状态：severity 应为 None，Schema 校验通过
        self.assertIsNone(finding_dict["severity"])
        self.assertEqual(FindingSchemaValidator.validate(finding_dict), [])

        # 恶意/误操作注入 severity，必须被 Schema 校验器拦截
        finding_dict["severity"] = "HIGH"
        with self.assertRaises(FindingSchemaError) as ctx:
            FindingSchemaValidator.assert_valid(finding_dict)
        self.assertIn("must NOT have severity", str(ctx.exception))

    def test_confirmed_finding_requires_evidence_and_trace(self):
        """铁律：confirmed 状态若无 evidence_refs 或无 trace，拒绝通过"""
        finding = FindingRecord.from_candidate(
            candidate=self.candidate,
            run_id="RUN-TEST-001",
            verdict=Verdict.CONFIRMED,
            severity=Severity.HIGH,
            root_cause="Missing check",
            evidence_refs=[],  # 篡改为空证据
        )
        finding_dict = finding.to_dict()

        with self.assertRaises(FindingSchemaError) as ctx:
            FindingSchemaValidator.assert_valid(finding_dict)
        self.assertIn("MUST reference at least one evidence", str(ctx.exception))

    def test_rejected_finding_requires_rationale(self):
        """铁律：rejected 状态必须具备明确的排除解释"""
        finding = FindingRecord.from_candidate(
            candidate=self.candidate,
            run_id="RUN-TEST-001",
            verdict=Verdict.REJECTED,
            rejection_reason="WAF and middleware intercept this route with 403",
        )
        finding_dict = finding.to_dict()
        self.assertEqual(FindingSchemaValidator.validate(finding_dict), [])

        # 缺失排除理由时必须被拦截
        finding_dict["rejection_reason"] = None
        with self.assertRaises(FindingSchemaError):
            FindingSchemaValidator.assert_valid(finding_dict)

    def test_trace_step_rejects_absolute_path(self):
        """铁律：Trace 文件路径严禁包含宿主机绝对路径"""
        bad_candidate = Candidate(
            fingerprint=self.fp,
            title="Bad Path Test",
            description="Absolute path injection",
            claimed_root_cause="Root cause",
            evidence_refs=["EV-01"],
            trace=[TraceStep("sink", "C:\\dev\\Invar\\src\\order.js", 10, "call", "step")],
        )
        finding = FindingRecord.from_candidate(
            candidate=bad_candidate,
            run_id="RUN-TEST-001",
            verdict=Verdict.CONFIRMED,
            severity=Severity.HIGH,
            root_cause="Root cause",
        )
        with self.assertRaises(FindingSchemaError) as ctx:
            FindingSchemaValidator.assert_valid(finding.to_dict())
        self.assertIn("must be repository-relative", str(ctx.exception))

    def test_serialization_and_roundtrip(self):
        """验证 FindingRecord 的无损字典与对象往返还原"""
        finding = FindingRecord.from_candidate(
            candidate=self.candidate,
            run_id="RUN-TEST-001",
            verdict=Verdict.CONFIRMED,
            severity=Severity.CRITICAL,
            root_cause="Flaw",
            execution=ExecutionRecord(200, "POST", "http://target/api", {"id": 1}, "ok", "EV-01"),
        )
        d = finding.to_dict()
        restored = FindingRecord.from_dict(d)

        self.assertEqual(restored.finding_id, finding.finding_id)
        self.assertEqual(restored.verdict, Verdict.CONFIRMED)
        self.assertEqual(restored.severity, Severity.CRITICAL)
        self.assertEqual(restored.execution.status_code, 200)


if __name__ == "__main__":
    unittest.main()
