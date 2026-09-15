import unittest
from unittest.mock import patch

from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class SandboxInvariantIntegrationTests(unittest.TestCase):
    def test_executor_evaluates_vulnerable_decision_for_unprotected_destructive_action(self) -> None:
        endpoint = EndpointIR(
            method="DELETE",
            path="/api/orders/batch",
            extracted_params=["order_ids"],
            tags=["destructive", "state-changing"],
        )

        config = InvarConfig(
            target_api_base="http://fixture.invalid",
            request_timeout=1,
            max_concurrent_workers=1,
            max_mutation_rounds=2,
        )

        executor = AdaptiveSandboxExecutor(cfg=config)

        class FakeResponse:
            status_code = 200
            text = '{"deleted_count": 3}'
            headers = {}

        with patch.object(executor.transport, "request", return_value=FakeResponse()):
            result = executor.probe_endpoint_with_research(endpoint)

        case = result.research_case
        evidence = result.evidence

        # 1. 断言自动挂载了破坏性确认不变量
        self.assertTrue(any(inv.invariant_type == "destructive_confirmation" for inv in case.invariants))

        # 2. 断言决断状态被精确升级为 vulnerable (底线被击穿)
        self.assertIsNotNone(case.decision)
        self.assertEqual(case.decision.status, "vulnerable")
        self.assertIn("破坏性操作在缺失确认参数的情况下被成功执行", case.decision.rationale)

        # 3. 断言证据记录被打上高危漏洞标志
        self.assertTrue(evidence.is_anomaly)
        self.assertEqual(evidence.finding_type, "VULNERABILITY_FOUND")

        # 4. 断言假设状态机流转：H-DESTRUCT-1 被正式证实为 VERIFIED
        destruct_hypotheses = [h for h in case.hypotheses if h.hypothesis_id.startswith("H-DESTRUCT")]
        self.assertTrue(len(destruct_hypotheses) >= 1)
        self.assertEqual(destruct_hypotheses[0].status, "VERIFIED")
        self.assertIn("破坏性操作在缺失确认参数的情况下被成功执行", destruct_hypotheses[0].evidence_notes)

    def test_executor_evaluates_confirmed_decision_when_confirmation_provided(self) -> None:
        endpoint = EndpointIR(
            method="DELETE",
            path="/api/orders/batch",
            extracted_params=["order_ids", "confirm"],
            tags=["destructive"],
        )

        config = InvarConfig(
            target_api_base="http://fixture.invalid",
            request_timeout=1,
            max_concurrent_workers=1,
            max_mutation_rounds=2,
        )

        executor = AdaptiveSandboxExecutor(cfg=config)

        class FakeResponse:
            status_code = 200
            text = '{"deleted_count": 3}'
            headers = {}

        with patch.object(executor.transport, "request", return_value=FakeResponse()):
            result = executor.probe_endpoint_with_research(endpoint)

        case = result.research_case
        evidence = result.evidence

        self.assertIsNotNone(case.decision)
        self.assertEqual(case.decision.status, "confirmed")
        self.assertFalse(evidence.is_anomaly)

        # 断言假设状态机流转：H-DESTRUCT-1 正确被证伪 (REFUTED)，确认防御坚固
        destruct_hypotheses = [h for h in case.hypotheses if h.hypothesis_id.startswith("H-DESTRUCT")]
        self.assertTrue(len(destruct_hypotheses) >= 1)
        self.assertEqual(destruct_hypotheses[0].status, "REFUTED")
