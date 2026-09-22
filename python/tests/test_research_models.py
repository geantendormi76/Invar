import unittest

from harness.models import EndpointIR
from harness.research_models import (
    Hypothesis,
    ProbeAttempt,
    ResearchCase,
    ResearchDecision,
    SecurityInvariant,
)


class TestResearchModels(unittest.TestCase):
    def setUp(self):
        endpoint = EndpointIR(
            method="POST",
            path="/test/verify",
            extracted_params=["out_trade_no"],
            source_file="fixture.js",
            line=10,
            call_signature="request",
        )

        self.case = ResearchCase(
            case_id="case-001",
            endpoint=endpoint,
        )

    def test_case_separates_endpoint_fact_from_research_state(self):
        self.assertEqual(
            self.case.endpoint.path,
            "/test/verify",
        )

        self.case.add_invariant(
            SecurityInvariant(
                invariant_type="authorization-boundary",
                statement="caller must only access authorized order",
            )
        )

        self.case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H1",
                statement="order identifier may cross authorization boundary",
                rationale="identifier is supplied by caller",
            )
        )

        self.assertEqual(len(self.case.invariants), 1)
        self.assertEqual(len(self.case.hypotheses), 1)

    def test_attempts_are_ordered(self):
        self.case.add_attempt(
            ProbeAttempt(
                attempt_number=1,
                payload={"out_trade_no": "TEST"},
                status_code=400,
                response_preview="validation failed",
                interpretation="required field missing",
                mutation_reason="add missing field",
            )
        )

        self.case.add_attempt(
            ProbeAttempt(
                attempt_number=2,
                payload={
                    "out_trade_no": "TEST",
                    "user_id": 1,
                },
                status_code=200,
                response_preview='{"ok":true}',
                interpretation="request accepted",
            )
        )

        self.assertEqual(len(self.case.attempts), 2)
        self.assertEqual(self.case.attempts[0].attempt_number, 1)
        self.assertEqual(self.case.attempts[1].attempt_number, 2)

    def test_attempt_sequence_must_be_contiguous(self):
        with self.assertRaises(ValueError):
            self.case.add_attempt(
                ProbeAttempt(
                    attempt_number=2,
                    payload={},
                    status_code=400,
                    response_preview="invalid",
                )
            )

    def test_decision_can_be_persisted(self):
        self.case.set_decision(
            ResearchDecision(
                status="INCONCLUSIVE",
                rationale="no reliable authorization boundary evidence",
            )
        )

        self.assertIsNotNone(self.case.decision)
        self.assertEqual(
            self.case.decision.status,
            "INCONCLUSIVE",
        )

    def test_case_serialization_is_structured(self):
        self.case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H1",
                statement="test hypothesis",
            )
        )

        data = self.case.to_dict()

        self.assertEqual(data["case_id"], "case-001")
        self.assertEqual(
            data["endpoint"]["path"],
            "/test/verify",
        )
        self.assertEqual(
            data["hypotheses"][0]["hypothesis_id"],
            "H1",
        )
        self.assertEqual(data["attempts"], [])
        self.assertIsNone(data["decision"])


if __name__ == "__main__":
    unittest.main()
