import unittest

from harness.invariant_evaluator import InvariantEvaluation
from harness.models import EndpointIR
from harness.research_models import Hypothesis, ResearchCase


class HypothesisEngineTests(unittest.TestCase):
    def test_generates_idor_hypothesis_when_identifier_params_present(self) -> None:
        from agent.hypothesis_engine import HypothesisEngine

        endpoint = EndpointIR(
            method="GET",
            path="/api/orders/detail",
            extracted_params=["order_id", "user_id"],
        )

        hypotheses = HypothesisEngine.generate_hypotheses(endpoint)

        idor_hypotheses = [h for h in hypotheses if h.hypothesis_id.startswith("H-IDOR")]
        self.assertTrue(len(idor_hypotheses) >= 1)
        self.assertIn("order_id", idor_hypotheses[0].rationale)
        self.assertIn("越权", idor_hypotheses[0].statement)
        self.assertEqual(idor_hypotheses[0].status, "PROPOSED")

    def test_generates_auth_hypothesis_when_sensitive_route_detected(self) -> None:
        from agent.hypothesis_engine import HypothesisEngine

        endpoint = EndpointIR(
            method="GET",
            path="/api/admin/config",
            tags=["sensitive-route", "admin"],
        )

        hypotheses = HypothesisEngine.generate_hypotheses(endpoint)

        auth_hypotheses = [h for h in hypotheses if h.hypothesis_id.startswith("H-AUTH")]
        self.assertTrue(len(auth_hypotheses) >= 1)
        self.assertIn("认证", auth_hypotheses[0].statement)
        self.assertIn("敏感特权路由", auth_hypotheses[0].rationale)
        self.assertEqual(auth_hypotheses[0].status, "PROPOSED")

    def test_generates_destructive_hypothesis_when_delete_action_detected(self) -> None:
        from agent.hypothesis_engine import HypothesisEngine

        endpoint = EndpointIR(
            method="DELETE",
            path="/api/users/clear",
            tags=["destructive"],
        )

        hypotheses = HypothesisEngine.generate_hypotheses(endpoint)

        destruct_hypotheses = [h for h in hypotheses if h.hypothesis_id.startswith("H-DESTRUCT")]
        self.assertTrue(len(destruct_hypotheses) >= 1)
        self.assertIn("破坏性", destruct_hypotheses[0].statement)
        self.assertEqual(destruct_hypotheses[0].status, "PROPOSED")

    def test_attach_to_case_populates_research_case_hypotheses(self) -> None:
        from agent.hypothesis_engine import HypothesisEngine

        endpoint = EndpointIR(
            method="DELETE",
            path="/api/orders/batch",
            extracted_params=["order_id"],
            tags=["destructive"],
        )
        case = ResearchCase(case_id="DELETE:/api/orders/batch", endpoint=endpoint)

        HypothesisEngine.attach_to_case(case)

        self.assertTrue(len(case.hypotheses) >= 2)
        hypothesis_ids = [h.hypothesis_id for h in case.hypotheses]
        self.assertTrue(any(hid.startswith("H-IDOR") for hid in hypothesis_ids))
        self.assertTrue(any(hid.startswith("H-DESTRUCT") for hid in hypothesis_ids))

    def test_resolve_hypotheses_verifies_destruct_when_invariant_vulnerable(self) -> None:
        from agent.hypothesis_engine import HypothesisEngine

        endpoint = EndpointIR(method="DELETE", path="/api/danger/clear", tags=["destructive"])
        case = ResearchCase(case_id="DELETE:/api/danger/clear", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-DESTRUCT-1",
                statement="破坏性操作可能缺失二次确认",
                rationale="DELETE method detected",
            )
        )

        evaluations = [
            InvariantEvaluation(
                invariant_type="destructive_confirmation",
                status="vulnerable",
                rationale="破坏性操作在缺失确认参数的情况下被成功执行",
            )
        ]

        resolved = HypothesisEngine.resolve_hypotheses(case=case, evaluations=evaluations)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].status, "VERIFIED")
        self.assertIn("破坏性操作在缺失确认参数的情况下被成功执行", resolved[0].evidence_notes)

    def test_resolve_hypotheses_refutes_auth_when_invariant_confirmed(self) -> None:
        from agent.hypothesis_engine import HypothesisEngine

        endpoint = EndpointIR(method="GET", path="/api/admin/users", tags=["admin"])
        case = ResearchCase(case_id="GET:/api/admin/users", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-AUTH-1",
                statement="特权管理路由可能缺失认证",
                rationale="admin route detected",
            )
        )

        evaluations = [
            InvariantEvaluation(
                invariant_type="auth_boundary",
                status="confirmed",
                rationale="服务端返回了严格的未授权拒绝响应 (401/403)",
            )
        ]

        resolved = HypothesisEngine.resolve_hypotheses(case=case, evaluations=evaluations)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].status, "REFUTED")
        self.assertIn("未授权拒绝响应", resolved[0].evidence_notes)

    def test_case_serialization_preserves_hypothesis_verification_state(self) -> None:
        endpoint = EndpointIR(method="GET", path="/api/admin/users")
        case = ResearchCase(case_id="GET:/api/admin/users", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-AUTH-1",
                statement="特权管理路由可能缺失认证",
                status="REFUTED",
                evidence_notes="服务端返回401拦截",
            )
        )

        case_dict = case.to_dict()
        h_dict = case_dict["hypotheses"][0]

        self.assertEqual(h_dict["status"], "REFUTED")
        self.assertEqual(h_dict["evidence_notes"], "服务端返回401拦截")
