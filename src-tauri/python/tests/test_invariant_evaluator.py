import unittest

from harness.models import EndpointIR
from harness.research_models import ResearchCase, SecurityInvariant


class InvariantEvaluatorTests(unittest.TestCase):
    def test_destructive_confirmation_flagged_vulnerable_when_unprotected(self) -> None:
        from harness.invariant_evaluator import InvariantEvaluator

        endpoint = EndpointIR(
            method="DELETE",
            path="/api/orders/batch",
            tags=["destructive", "state-changing"],
        )
        invariant = SecurityInvariant(
            invariant_type="destructive_confirmation",
            statement="Destructive actions must require explicit confirmation",
        )

        evaluation = InvariantEvaluator.evaluate(
            invariant=invariant,
            endpoint=endpoint,
            status_code=200,
            payload={"ids": [1, 2, 3]},
        )

        self.assertEqual(evaluation.status, "vulnerable")
        self.assertIn("破坏性操作在缺失确认参数的情况下被成功执行", evaluation.rationale)

    def test_destructive_confirmation_confirmed_when_protection_present(self) -> None:
        from harness.invariant_evaluator import InvariantEvaluator

        endpoint = EndpointIR(
            method="DELETE",
            path="/api/orders/batch",
            tags=["destructive"],
        )
        invariant = SecurityInvariant(
            invariant_type="destructive_confirmation",
            statement="Destructive actions must require explicit confirmation",
        )

        evaluation = InvariantEvaluator.evaluate(
            invariant=invariant,
            endpoint=endpoint,
            status_code=200,
            payload={"ids": [1, 2, 3], "confirm": True},
        )

        self.assertEqual(evaluation.status, "confirmed")
        self.assertIn("携带了合法的确认字段", evaluation.rationale)

    def test_auth_boundary_flagged_vulnerable_when_sensitive_route_returns_200(self) -> None:
        from harness.invariant_evaluator import InvariantEvaluator

        endpoint = EndpointIR(
            method="GET",
            path="/api/admin/users",
            tags=["sensitive-route", "admin"],
        )
        invariant = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="Sensitive administration routes must enforce authentication",
        )

        evaluation = InvariantEvaluator.evaluate(
            invariant=invariant,
            endpoint=endpoint,
            status_code=200,
            payload={},
            headers={},
        )

        self.assertEqual(evaluation.status, "vulnerable")
        self.assertIn("敏感特权路由在未携带有效凭证时被异常放行", evaluation.rationale)

    def test_auth_boundary_confirmed_when_rejected_with_401_or_403(self) -> None:
        from harness.invariant_evaluator import InvariantEvaluator

        endpoint = EndpointIR(
            method="GET",
            path="/api/admin/users",
            tags=["sensitive-route"],
        )
        invariant = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="Sensitive administration routes must enforce authentication",
        )

        evaluation = InvariantEvaluator.evaluate(
            invariant=invariant,
            endpoint=endpoint,
            status_code=401,
            payload={},
        )

        self.assertEqual(evaluation.status, "confirmed")
        self.assertIn("返回了严格的未授权拒绝响应", evaluation.rationale)

    def test_evaluator_synthesizes_research_decision_for_case(self) -> None:
        from harness.invariant_evaluator import InvariantEvaluator

        endpoint = EndpointIR(
            method="DELETE",
            path="/api/danger/clear",
            tags=["destructive"],
        )
        case = ResearchCase(case_id="DELETE:/api/danger/clear", endpoint=endpoint)
        case.add_invariant(
            SecurityInvariant(
                invariant_type="destructive_confirmation",
                statement="Must have confirm",
            )
        )

        decision = InvariantEvaluator.evaluate_case(
            case=case,
            status_code=200,
            payload={"all": True},
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.status, "vulnerable")
