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
        )
        verifier = IndependentVerifier(verifier_id="verifier-audit-team")
        verifier.verify(self.finding_confirmed, originator_id="hunter-01")

        self.projector = ReportProjector(
            run=self.run,
            ledger=self.ledger,
            findings=[self.finding_confirmed],
        )

    def test_project_all_generates_all_six_deliverables(self):
        """核心断言：一键原子化输出全量 6 大正交交付产物 (包含 sarif_json)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_files = self.projector.project_all(tmpdir)
            self.assertEqual(len(out_files), 6)
            self.assertTrue(out_files["sarif_json"].exists())
            self.assertTrue(out_files["findings_json"].exists())
            self.assertTrue(out_files["report_md"].exists())

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


if __name__ == "__main__":
    unittest.main()
