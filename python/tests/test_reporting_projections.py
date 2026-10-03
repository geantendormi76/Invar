import json
from pathlib import Path
import tempfile
import unittest

from harness.candidate_models import (
    Candidate,
    CandidateFingerprint,
    CanonicalFactors,
    TraceStep,
)
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
from harness.run_models import ExecutionPolicy, ResearchRun, ResearchScope, RunProfile, RunStatus
from harness.verification_gate import IndependentVerifier


class ReportingProjectionsTests(unittest.TestCase):
    def setUp(self):
        self.run = ResearchRun(
            run_id="RUN-TEST-001",
            target_root="example.com",
            scope=ResearchScope(target_domain="example.com"),
            status=RunStatus.COMPLETED,
        )

        self.ledger = CoverageLedger(run_id="RUN-TEST-001")
        self.unit = CoverageUnit(
            coverage_id="api-users-authorization",
            surface="api",
            boundary="user-to-admin",
            subsystem="users",
            attack_class="authorization",
            starting_paths=["/api/users"],
            status=CoverageStatus.COVERED,
            reviewed_paths=["/api/users"],
            check_refs=["CHK-AUTH-GET"],
        )
        self.ledger.add_unit(self.unit)

        # 构造实锤漏洞
        fp_confirmed = CandidateFingerprint.from_factors(
            CanonicalFactors(
                attack_class="authorization",
                boundary="tenant_isolation",
                sink_component="user_service",
                missing_control="missing_owner_check",
            )
        )
        cand_conf = Candidate(
            fingerprint=fp_confirmed,
            title="BOLA in User Service",
            description="Tenant isolation broken",
            claimed_root_cause="Missing owner verification",
            endpoint_refs=["GET:/api/users/123"],
            coverage_refs=["api-users-authorization"],
            trace=[
                TraceStep(
                    step_type="sink",
                    file_path="routes/users.js",
                    line=42,
                    scope="getUser",
                    description="Returns user object",
                )
            ],
            evidence_refs=["evidence-uuid-01"],
        )
        self.sample_poc = "curl -s -i -X GET 'https://example.com/api/users/123' \\\n  -H 'Authorization: Bearer test_token'"
        self.finding_confirmed = FindingRecord.from_candidate(
            candidate=cand_conf,
            run_id="RUN-TEST-001",
            verdict=Verdict.CONFIRMED,
            severity=Severity.HIGH,
            root_cause="Missing owner verification",
            execution=ExecutionRecord(
                status_code=200,
                method="GET",
                url="https://example.com/api/users/123",
                response_summary='{"user_id": 123}',
            ),
            remediation=Remediation(
                summary="Add ownership check",
                guidance="Verify session.user_id == requested_id",
            ),
            poc_code=self.sample_poc,
        )
        verifier = IndependentVerifier(verifier_id="verifier-audit-team")
        verifier.verify(self.finding_confirmed, originator_id="hunter-01")

        self.projector = ReportProjector(
            run=self.run,
            ledger=self.ledger,
            findings=[self.finding_confirmed],
        )

    def test_project_all_generates_all_seven_deliverables(self):
        """核心断言：一键原子化输出全量 7 大正交交付产物 (包含 sarif_json 与 BOUNTY-SUBMISSION.md)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_files = self.projector.project_all(tmpdir)
            self.assertEqual(len(out_files), 7)
            self.assertTrue(out_files["sarif_json"].exists())
            self.assertTrue(out_files["findings_json"].exists())
            self.assertTrue(out_files["report_md"].exists())
            self.assertTrue(out_files["bounty_submission_md"].exists())
            bounty_content = out_files["bounty_submission_md"].read_text(encoding="utf-8")
            self.assertIn("Bug Bounty", bounty_content)
            self.assertIn("## Step-by-Step Proof of Concept (PoC)", bounty_content)
            self.assertIn(self.sample_poc, bounty_content)

    def test_projected_sarif_json_satisfies_oasis_standard(self):
        """断言: 导出的 sarif.json 100% 符合 OASIS SARIF 2.1.0 核心 Schema"""
        sarif_str = self.projector.render_sarif_json()
        doc = json.loads(sarif_str)
        self.assertEqual(doc["version"], "2.1.0")
        self.assertIn("sarif-schema-2.1.0.json", doc["$schema"])
        runs = doc.get("runs", [])
        self.assertEqual(len(runs), 1)
        results = runs[0].get("results", [])
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res["level"], "error")
        self.assertEqual(res["ruleId"], self.finding_confirmed.fingerprint)
        self.assertEqual(res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"], "routes/users.js")
        self.assertEqual(res["locations"][0]["physicalLocation"]["region"]["startLine"], 42)

    def test_projected_findings_detail_and_json_renders_reproducible_poc(self):
        """断言: 深度战报 FINDINGS-DETAIL.md 必须渲染独立 PoC 代码块，且 findings.json 完整沉淀 poc_code 契约"""
        # 1. 验证 findings.json
        findings_json_str = self.projector.render_findings_json()
        doc = json.loads(findings_json_str)
        f_entry = doc["findings"][0]
        self.assertIn("poc_code", f_entry, "findings.json 中缺少 poc_code 序列化字段！")
        self.assertEqual(f_entry["poc_code"], self.sample_poc)

        # 2. 验证 FINDINGS-DETAIL.md
        detail_md = self.projector.render_findings_detail_md()
        self.assertIn("### 4. 独立漏洞复现 PoC (Reproducible PoC)", detail_md, "FINDINGS-DETAIL.md 缺少独立的 PoC 章节标题！")
        self.assertIn("```bash\n" + self.sample_poc + "\n```", detail_md, "FINDINGS-DETAIL.md 中 PoC bash 代码块渲染不匹配！")
        self.assertIn("### 5. 架构修复与治理建议", detail_md, "存在 PoC 时，治理建议章节编号必须自然顺延至第 5 节！")


if __name__ == "__main__":
    unittest.main()
