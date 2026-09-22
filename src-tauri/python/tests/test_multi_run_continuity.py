import unittest

from harness.candidate_models import Candidate, CandidateFingerprint, CanonicalFactors, TraceStep
from harness.coverage_ledger import CoverageLedger, CoverageStatus, CoverageUnit, UnresolvedFact
from harness.finding_models import FindingRecord, Severity, Verdict
from harness.models import EndpointIR
from harness.multi_run import MultiRunReconciler
from harness.run_models import ResearchRun, ResearchScope, SourceRef


class MultiRunContinuityTests(unittest.TestCase):
    def setUp(self):
        self.scope = ResearchScope(target_domain="example.com")
        self.fp = CandidateFingerprint.from_factors(
            CanonicalFactors("authorization", "tenant", "orders", "missing_check")
        )

        # 构造历史运行实例 (Run 1)
        self.prior_run = ResearchRun(
            run_id="RUN-001",
            target_root="data/targets/example",
            scope=self.scope,
            source_ref=SourceRef(commit="commit-v1", raw_input_hash="hash-11111"),
        )
        self.prior_ledger = CoverageLedger(run_id="RUN-001")
        self.prior_ledger.add_unit(
            CoverageUnit(
                coverage_id="api-orders-authorization",
                surface="api",
                boundary="tenant",
                subsystem="orders",
                attack_class="authorization",
                starting_paths=["/api/orders/list"],
                status=CoverageStatus.COVERED,
                reviewed_paths=["/api/orders/list"],
                check_refs=["CHK-01"],
            )
        )
        # 历史中有一个受阻的盲区单元
        self.prior_ledger.add_unit(
            CoverageUnit(
                coverage_id="api-orders-blocked_unit",
                surface="api",
                boundary="tenant",
                subsystem="orders",
                attack_class="authorization",
                starting_paths=["/api/orders/secret"],
                status=CoverageStatus.BLOCKED,
                unresolved=[UnresolvedFact("FACT-01", "WAF 403 blocks probing", "Need tunnel")],
            )
        )

        # 历史实锤漏洞与存疑记录
        self.prior_confirmed = FindingRecord.from_candidate(
            candidate=Candidate(
                fingerprint=self.fp,
                title="BOLA in orders",
                description="Desc",
                claimed_root_cause="Missing check",
                endpoint_refs=["POST:/api/orders/cancel"],
                evidence_refs=["EV-01"],
                trace=[TraceStep("sink", "orders.js", 10, "cancel", "sink")],
            ),
            run_id="RUN-001",
            verdict=Verdict.CONFIRMED,
            severity=Severity.HIGH,
            root_cause="Missing check",
        )
        self.prior_needs_validation = FindingRecord.from_candidate(
            candidate=Candidate(
                fingerprint=CandidateFingerprint.from_factors(
                    CanonicalFactors("auth", "admin", "admin_service", "missing_token")
                ),
                title="Potential Admin Bypass",
                description="Desc",
                claimed_root_cause="Missing token",
                endpoint_refs=["GET:/api/admin/config"],
            ),
            run_id="RUN-001",
            verdict=Verdict.NEEDS_VALIDATION,
            unresolved_blocker="Need admin cookie",
        )
        self.prior_findings = [self.prior_confirmed, self.prior_needs_validation]

        self.endpoints = [
            EndpointIR(method="GET", path="/api/orders/list"),
            EndpointIR(method="POST", path="/api/orders/cancel"),
            EndpointIR(method="GET", path="/api/orders/secret"),
            EndpointIR(method="GET", path="/api/admin/config"),
            EndpointIR(method="POST", path="/api/users/register"),  # 新增的端点
        ]

    def test_same_source_carries_forward_confirmed_findings(self):
        """场景 1：源码完全一致 -> 历史实锤平移继承，不重复立项靶向复测"""
        current_run = ResearchRun(
            run_id="RUN-002",
            target_root="data/targets/example",
            scope=self.scope,
            source_ref=SourceRef(commit="commit-v1", raw_input_hash="hash-11111"),  # 哈希完全相同
        )

        result = MultiRunReconciler.reconcile(
            current_run=current_run,
            prior_run=self.prior_run,
            prior_ledger=self.prior_ledger,
            prior_findings=self.prior_findings,
            current_endpoints=self.endpoints,
        )

        self.assertFalse(result.diff_summary.source_changed)
        self.assertEqual(result.diff_summary.carried_confirmed_count, 1)
        self.assertEqual(result.diff_summary.confirmed_revalidation_count, 0)
        self.assertEqual(len(result.carried_findings), 1)
        self.assertEqual(result.carried_findings[0].fingerprint, self.fp.value)

    def test_changed_source_forces_revalidation_targets_for_confirmed_findings(self):
        """场景 2：源码发生变化 -> 历史实锤拒绝盲目信任，强制立项为高权重靶向复测单元"""
        current_run = ResearchRun(
            run_id="RUN-002",
            target_root="data/targets/example",
            scope=self.scope,
            source_ref=SourceRef(commit="commit-v2", raw_input_hash="hash-99999_CHANGED"),  # 源码变动
        )

        result = MultiRunReconciler.reconcile(
            current_run=current_run,
            prior_run=self.prior_run,
            prior_ledger=self.prior_ledger,
            prior_findings=self.prior_findings,
            current_endpoints=self.endpoints,
        )

        self.assertTrue(result.diff_summary.source_changed)
        self.assertEqual(result.diff_summary.confirmed_revalidation_count, 1)
        self.assertEqual(result.diff_summary.carried_confirmed_count, 0)
        self.assertEqual(len(result.revalidation_units), 1)

        reval_unit = result.revalidation_units[0]
        self.assertEqual(reval_unit.attack_class, "regression_verification")
        self.assertEqual(reval_unit.weight, 3.0)  # 高权重
        self.assertIn(self.fp.value, reval_unit.candidate_fingerprints)

    def test_unresolved_gaps_always_resurface_regardless_of_source_state(self):
        """铁律验证：历史 blocked 和 needs_validation 盲区 100% 显式浮现为新轮次待审计划"""
        current_run = ResearchRun(
            run_id="RUN-002",
            target_root="data/targets/example",
            scope=self.scope,
            source_ref=SourceRef(commit="commit-v2", raw_input_hash="hash-99999_CHANGED"),
        )

        result = MultiRunReconciler.reconcile(
            current_run=current_run,
            prior_run=self.prior_run,
            prior_ledger=self.prior_ledger,
            prior_findings=self.prior_findings,
            current_endpoints=self.endpoints,
        )

        # 必须显式捕获到 2 个遗留盲区：1 个 blocked 单元 + 1 个 needs_validation 发现
        self.assertEqual(result.diff_summary.unresolved_resurfaced_count, 2)
        self.assertTrue(result.reconciled_ledger.contains("api-orders-blocked_unit"))
        self.assertEqual(
            result.reconciled_ledger.get_unit("api-orders-blocked_unit").status,
            CoverageStatus.PLANNED,
        )
        self.assertTrue(any("reval-gap-" in cid for cid in result.reconciled_ledger.units))

    def test_newly_introduced_endpoints_are_planned(self):
        """验证新代码中引入的新端点 (users/register) 自动被规划入新账本"""
        current_run = ResearchRun(
            run_id="RUN-002",
            target_root="data/targets/example",
            scope=self.scope,
            source_ref=SourceRef(commit="commit-v2", raw_input_hash="hash-99999_CHANGED"),
        )

        result = MultiRunReconciler.reconcile(
            current_run=current_run,
            prior_run=self.prior_run,
            prior_ledger=self.prior_ledger,
            prior_findings=self.prior_findings,
            current_endpoints=self.endpoints,
        )

        self.assertTrue(result.reconciled_ledger.contains("api-users-authorization"))


if __name__ == "__main__":
    unittest.main()
