import tempfile
import unittest
from pathlib import Path

from harness.coverage_ledger import (
    CoverageLedger,
    CoverageStatus,
    CoverageUnit,
    CoverageValidationError,
    IllegalCoverageStateTransitionError,
    UnresolvedFact,
)
from harness.models import EndpointIR
from harness.run_models import ResearchScope


class CoverageLedgerTests(unittest.TestCase):
    def setUp(self):
        self.unit = CoverageUnit(
            coverage_id="api-authconf-authorization",
            surface="api",
            boundary="user-to-privileged-config",
            subsystem="authConf",
            attack_class="authorization",
            starting_paths=["/api/v3/authConf/saveAuth"],
            status=CoverageStatus.PLANNED,
        )
        self.ledger = CoverageLedger(run_id="RUN-TEST-001")
        self.ledger.add_unit(self.unit)

    def test_duplicate_coverage_id_rejected(self):
        """不变性：同一账本内 coverage_id 必须全局唯一"""
        dup = CoverageUnit(
            coverage_id="api-authconf-authorization",
            surface="api",
            boundary="other",
            subsystem="authConf",
            attack_class="authorization",
        )
        with self.assertRaises(ValueError):
            self.ledger.add_unit(dup)

    def test_coverage_unit_state_machine(self):
        """验证覆盖单元合法状态跃迁流"""
        self.unit.transition_to(CoverageStatus.IN_PROGRESS)
        self.assertEqual(self.unit.status, CoverageStatus.IN_PROGRESS)

        self.unit.transition_to(CoverageStatus.COVERED)
        self.assertEqual(self.unit.status, CoverageStatus.COVERED)

    def test_illegal_coverage_state_transition(self):
        """验证非法跳步（如 PLANNED 直接到 COVERED）被拦截"""
        with self.assertRaises(IllegalCoverageStateTransitionError):
            self.unit.transition_to(CoverageStatus.COVERED)

    def test_validator_detects_unjustified_covered_status(self):
        """不变性校验：标记为 COVERED 时若无审查路径与检查项，拒绝通过"""
        self.unit.status = CoverageStatus.COVERED
        self.unit.reviewed_paths = []
        self.unit.check_refs = []

        with self.assertRaises(CoverageValidationError) as ctx:
            self.ledger.validate()
        self.assertIn("empty reviewed_paths", str(ctx.exception))

    def test_validator_detects_candidate_without_fingerprint(self):
        """不变性校验：标记为 CANDIDATE 时若无候选指纹，拒绝通过"""
        self.unit.status = CoverageStatus.CANDIDATE
        self.unit.candidate_fingerprints = []

        with self.assertRaises(CoverageValidationError) as ctx:
            self.ledger.validate()
        self.assertIn("no candidate_fingerprints", str(ctx.exception))

    def test_validator_detects_blocked_without_unresolved_fact(self):
        """不变性校验：标记为 BLOCKED 时必须记录未决事实"""
        self.unit.status = CoverageStatus.BLOCKED
        self.unit.unresolved = []

        with self.assertRaises(CoverageValidationError) as ctx:
            self.ledger.validate()
        self.assertIn("no unresolved facts", str(ctx.exception))

    def test_coverage_metrics_computation(self):
        """验证客观覆盖率测算（过滤 out_of_scope，计算加权百分比）"""
        # 补充一个完成单元
        unit_done = CoverageUnit(
            coverage_id="api-users-authorization",
            surface="api",
            boundary="user-boundary",
            subsystem="users",
            attack_class="authorization",
            status=CoverageStatus.COVERED,
            reviewed_paths=["/api/users"],
            check_refs=["CHK-01"],
            weight=1.0,
        )
        # 补充一个排除单元
        unit_excluded = CoverageUnit(
            coverage_id="api-logout-authorization",
            surface="api",
            boundary="public",
            subsystem="auth",
            attack_class="authorization",
            status=CoverageStatus.OUT_OF_SCOPE,
            weight=1.0,
        )
        self.ledger.add_unit(unit_done)
        self.ledger.add_unit(unit_excluded)

        metrics = self.ledger.compute_metrics()
        self.assertEqual(metrics["total_units"], 3)
        self.assertEqual(metrics["in_scope_units"], 2)
        self.assertEqual(metrics["covered_units"], 1)
        self.assertEqual(metrics["out_of_scope_units"], 1)
        self.assertEqual(metrics["coverage_percentage"], 50.0)

    def test_plan_from_endpoints_generates_correct_units(self):
        """验证 Stage 1 AST 端点列表直接生成规划账本"""
        endpoints = [
            EndpointIR(method="GET", path="/api/orders/list"),
            EndpointIR(method="DELETE", path="/api/orders/batch", tags=["destructive"]),
            EndpointIR(method="POST", path="/api/users/create"),
        ]
        scope = ResearchScope(target_domain="example.com")
        ledger = CoverageLedger.plan_from_endpoints("RUN-AST-01", endpoints, scope=scope)

        self.assertTrue(ledger.contains("api-orders-authorization"))
        self.assertTrue(ledger.contains("api-orders-destructive_guard"))
        self.assertTrue(ledger.contains("api-users-authorization"))

    def test_serialization_and_disk_roundtrip(self):
        """验证 CoverageLedger JSON 持久化与还原"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "coverage_ledger.json"
            self.ledger.save(file_path)

            restored = CoverageLedger.load(file_path)
            self.assertEqual(restored.run_id, "RUN-TEST-001")
            self.assertTrue(restored.contains("api-authconf-authorization"))
            self.assertEqual(
                restored.get_unit("api-authconf-authorization").boundary,
                "user-to-privileged-config",
            )


if __name__ == "__main__":
    unittest.main()
