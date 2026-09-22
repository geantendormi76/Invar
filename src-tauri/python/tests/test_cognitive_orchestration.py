import unittest
from unittest.mock import Mock

from agent.coverage_critic import CoverageCritic
from agent.hunter import Hunter
from agent.wave_orchestrator import HunterWaveOrchestrator
from harness.candidate_models import CandidateStatus
from harness.coverage_ledger import CoverageLedger, CoverageStatus, CoverageUnit
from harness.models import EndpointIR
from harness.research_models import ResearchCase, ResearchDecision, ResearchExecutionResult
from harness.run_models import ResearchScope


class CognitiveOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.endpoints = [
            EndpointIR(method="GET", path="/api/orders/list"),
            EndpointIR(method="DELETE", path="/api/orders/batch", tags=["destructive"]),
            EndpointIR(
                method="GET",
                path="/api/users/profile",
                extracted_params=["user_id"],
            ),
        ]
        self.scope = ResearchScope(target_domain="example.com")
        # 初始仅规划 orders 授权单元
        self.ledger = CoverageLedger(run_id="RUN-WAVE-001")
        self.ledger.add_unit(
            CoverageUnit(
                coverage_id="api-orders-authorization",
                surface="api",
                boundary="user-boundary",
                subsystem="orders",
                attack_class="authorization",
                starting_paths=["/api/orders/list"],
                status=CoverageStatus.PLANNED,
            )
        )

    def test_hunter_investigates_unit_and_returns_clean_coverage(self):
        """验证 Hunter 审查无违背端点后产出 COVERED 提案，且不直接篡改账本"""
        hunter = Hunter(agent_id="hunter-01")
        unit = self.ledger.get_unit("api-orders-authorization")

        result = hunter.hunt(unit, self.endpoints, self.scope)

        self.assertEqual(result.status, CoverageStatus.COVERED)
        self.assertEqual(result.reviewed_paths, ["/api/orders/list"])
        self.assertIn("CHK-AUTHORIZATION-GET", result.check_refs)
        self.assertEqual(len(result.candidate_proposals), 0)
        # 铁律：账本本身状态未受直接修改（仍为 PLANNED），等待主进程提交
        self.assertEqual(unit.status, CoverageStatus.PLANNED)

    def test_hunter_detects_vulnerability_and_proposes_candidate(self):
        """验证 Hunter 遭遇沙箱漏洞事实时，返回 CANDIDATE 提案与关联指纹"""
        hunter = Hunter(agent_id="hunter-02")
        destruct_unit = CoverageUnit(
            coverage_id="api-orders-destructive_guard",
            surface="api",
            boundary="state-mutation-safety",
            subsystem="orders",
            attack_class="destructive_action",
            starting_paths=["/api/orders/batch"],
            status=CoverageStatus.PLANNED,
        )

        # Mock 沙箱执行器触发破坏性操作无确认漏洞
        fake_case = ResearchCase(case_id="DELETE:/api/orders/batch", endpoint=self.endpoints[1])
        fake_case.set_decision(ResearchDecision(status="vulnerable", rationale="Missing confirmation guard"))
        fake_exec_result = ResearchExecutionResult(
            evidence=Mock(notes="Physical evidence snapshot"),
            research_case=fake_case,
            evidence_history=[Mock()],
        )

        mock_executor = Mock()
        mock_executor.probe_endpoint_with_research.return_value = fake_exec_result

        result = hunter.hunt(
            destruct_unit,
            self.endpoints,
            self.scope,
            executor=mock_executor,
        )

        self.assertEqual(result.status, CoverageStatus.CANDIDATE)
        self.assertEqual(len(result.candidate_proposals), 1)
        candidate = result.candidate_proposals[0]
        self.assertIn("fp:destructive_action:orders_service", candidate.fingerprint.value)
        self.assertEqual(candidate.status, CandidateStatus.SUPPORTED)

    def test_coverage_critic_identifies_gaps_in_subsystems_and_attack_classes(self):
        """验证 CoverageCritic 精准发现未规划的 users 子系统及 IDOR、破坏性盲区"""
        critic = CoverageCritic()
        proposals = critic.critique(self.ledger, self.endpoints, self.scope)

        proposal_cids = [f"{p.surface}-{p.subsystem}-{p.attack_class}" for p in proposals]

        # 1. 必须发现未规划的 users 子系统
        self.assertIn("api-users-authorization", proposal_cids)
        # 2. 必须发现 orders 中未被覆盖的破坏性动作
        self.assertIn("api-orders-destructive_action", proposal_cids)
        # 3. 必须发现 users 中携带 user_id 参数的 IDOR 盲区
        self.assertIn("api-users-idor_boundary", proposal_cids)

    def test_wave_orchestrator_executes_full_closed_loop(self):
        """端到端编排闭环：Planned -> Hunter -> Parent Commit -> Critic Gap Discovery -> Ledger Evolution"""
        orchestrator = HunterWaveOrchestrator(
            ledger=self.ledger,
            endpoints=self.endpoints,
            scope=self.scope,
        )

        # 执行第一波次
        wave_res = orchestrator.run_wave()

        self.assertEqual(wave_res.wave_number, 1)
        self.assertEqual(wave_res.units_assigned, 1)
        self.assertEqual(wave_res.units_covered, 1)

        # 账本状态必须在主控协调下正式演进为 COVERED
        unit = self.ledger.get_unit("api-orders-authorization")
        self.assertEqual(unit.status, CoverageStatus.COVERED)
        self.assertEqual(unit.owner_agent_id, "hunter-wave-1")

        # Critic 发现的盲区必须自动以 PLANNED 状态补入账本
        self.assertTrue(wave_res.gap_units_added >= 2)
        self.assertTrue(self.ledger.contains("api-users-authorization"))
        self.assertEqual(
            self.ledger.get_unit("api-users-authorization").status,
            CoverageStatus.PLANNED,
        )


if __name__ == "__main__":
    unittest.main()
