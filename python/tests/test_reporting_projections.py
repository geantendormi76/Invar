import json
import tempfile
import unittest
from pathlib import Path

from harness.candidate_models import Candidate, CandidateFingerprint, CanonicalFactors, TraceStep
from harness.coverage_ledger import CoverageLedger, CoverageStatus, CoverageUnit
from harness.finding_models import (
    ExecutionRecord,
    FindingRecord,
    FindingSchemaValidator,
    Remediation,
    Severity,
    Verdict,
)
from harness.reporting import ReportProjector
from harness.run_models import ResearchRun, ResearchScope, RunStatus, SourceRef
from harness.verification_gate import IndependentVerifier


class ReportingProjectionsTests(unittest.TestCase):
    def setUp(self):
        self.scope = ResearchScope(target_domain="target.corp.local")
        self.source_ref = SourceRef(commit="feat-sec-audit-99", raw_input_hash="hash-abcdef")
        self.run = ResearchRun(
            run_id="RUN-PROJ-001",
            target_root="data/targets/local",
            scope=self.scope,
            source_ref=self.source_ref,
            status=RunStatus.EVALUATED,
        )

        self.ledger = CoverageLedger(run_id="RUN-PROJ-001")
        self.ledger.add_unit(
            CoverageUnit(
                coverage_id="api-auth-check",
                surface="api",
                boundary="tenant",
                subsystem="auth",
                attack_class="authorization",
                starting_paths=["/api/auth/verify"],
                status=CoverageStatus.COVERED,
                reviewed_paths=["/api/auth/verify"],
                check_refs=["CHK-01"],
            )
        )

        # 构造一个实锤漏洞 Finding
        fp_confirmed = CandidateFingerprint.from_factors(
            CanonicalFactors("authorization", "tenant", "order_service", "missing_owner_check")
        )
        cand_conf = Candidate(
            fingerprint=fp_confirmed,
            title="BOLA in Order Service",
            description="Tenant isolation broken",
            claimed_root_cause="Missing owner check",
            endpoint_refs=["POST:/api/orders/cancel"],
            evidence_refs=["EV-1001"],
            trace=[TraceStep("sink", "src/orders.js", 88, "cancel", "sink exec")],
        )
        self.finding_confirmed = FindingRecord.from_candidate(
            candidate=cand_conf,
            run_id="RUN-PROJ-001",
            verdict=Verdict.CONFIRMED,
            severity=Severity.HIGH,
            root_cause="Missing ownership verification in cancel API",
            remediation=Remediation("Verify owner", "Check user_id matches"),
            execution=ExecutionRecord(200, "POST", "http://target/api/orders/cancel", {"id": 1}, "ok", "EV-1001"),
        )
        # 实施独立第三方复核签署
        verifier = IndependentVerifier(verifier_id="verifier-audit-team")
        verifier.verify(self.finding_confirmed, originator_id="hunter-wave-1")

        # 构造一个存疑待验 Finding (绝无 Severity)
        fp_nv = CandidateFingerprint.from_factors(
            CanonicalFactors("auth", "admin", "admin_service", "missing_token")
        )
        cand_nv = Candidate(
            fingerprint=fp_nv,
            title="Suspicious Admin Route",
            description="May lack auth",
            claimed_root_cause="Missing token",
            endpoint_refs=["GET:/api/admin/metrics"],
        )
        self.finding_nv = FindingRecord.from_candidate(
            candidate=cand_nv,
            run_id="RUN-PROJ-001",
            verdict=Verdict.NEEDS_VALIDATION,
            unresolved_blocker="Awaiting internal token to verify access",
        )

        self.findings = [self.finding_confirmed, self.finding_nv]
        self.projector = ReportProjector(self.run, self.ledger, self.findings)

    def test_project_all_generates_all_five_deliverables(self):
        """核心断言：必须一键原子化输出全量 5 大投影交付物"""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_files = self.projector.project_all(tmpdir)

            self.assertEqual(len(out_files), 5)
            self.assertTrue(out_files["findings_json"].exists())
            self.assertTrue(out_files["report_md"].exists())
            self.assertTrue(out_files["findings_detail_md"].exists())
            self.assertTrue(out_files["needs_validation_md"].exists())
            self.assertTrue(out_files["coverage_summary_md"].exists())

    def test_projected_findings_json_satisfies_schema(self):
        """投影断言：产出的 findings.json 必须 100% 通过严格 Schema 门禁校验"""
        json_str = self.projector.render_findings_json()
        data = json.loads(json_str)

        self.assertEqual(data["run_id"], "RUN-PROJ-001")
        self.assertEqual(len(data["findings"]), 2)
        for f_dict in data["findings"]:
            FindingSchemaValidator.assert_valid(f_dict)

    def test_report_md_contains_authoritative_run_and_coverage_facts(self):
        """投影断言：REPORT.md 必须准确呈现 Run 身份血统与客观覆盖率百分比"""
        report_md = self.projector.render_report_md()

        self.assertIn("RUN-PROJ-001", report_md)
        self.assertIn("target.corp.local", report_md)
        self.assertIn("feat-sec-audit-99", report_md)
        self.assertIn("100.0%", report_md)  # 账本唯一的单元处于 COVERED，覆盖率应为 100.0%
        self.assertIn("BOLA in Order Service", report_md)
        self.assertIn("verifier-audit-team", report_md)

    def test_findings_detail_md_contains_trace_and_excludes_unconfirmed(self):
        """投影断言：FINDINGS-DETAIL.md 必须包含调用链与证据，且绝不混入未实锤记录"""
        detail_md = self.projector.render_findings_detail_md()

        self.assertIn("BOLA in Order Service", detail_md)
        self.assertIn("src/orders.js:88", detail_md)
        self.assertIn("EV-1001", detail_md)
        # 铁律：存疑的 Suspicious Admin Route 绝不允许出现在实锤报告中
        self.assertNotIn("Suspicious Admin Route", detail_md)

    def test_needs_validation_md_discloses_blocker_and_strictly_excludes_severity(self):
        """投影断言：NEEDS-VALIDATION.md 披露阻塞原因，严禁标注任何 Severity"""
        nv_md = self.projector.render_needs_validation_md()

        self.assertIn("Suspicious Admin Route", nv_md)
        self.assertIn("Awaiting internal token", nv_md)
        # 铁律：绝无 CRITICAL/HIGH 等假定严重度
        self.assertNotIn("CRITICAL", nv_md)
        self.assertNotIn("Severity:", nv_md)

    def test_blocked_run_explicitly_discloses_block_reason_in_report(self):
        """投影断言：处于 BLOCKED 状态的 Run，报告头部必须显式披露阻断告警"""
        self.run.status = RunStatus.BLOCKED
        self.run.block_reason = "Gateway token revoked by security policy"

        report_md = self.projector.render_report_md()
        self.assertIn("运行受阻警报 (Run Blocked)", report_md)
        self.assertIn("Gateway token revoked", report_md)


if __name__ == "__main__":
    unittest.main()
