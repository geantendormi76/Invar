import unittest

from harness.evidence import EvidenceRecord
from harness.models import EndpointIR
from harness.research_evidence import ProbeAttemptEvidenceMapper
from harness.research_models import (
    Hypothesis,
    ProbeAttempt,
    ResearchCase,
    ResearchDecision,
    SecurityInvariant,
)


class TestResearchEvidence(unittest.TestCase):
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

    def test_attempt_maps_to_existing_evidence_contract(self):
        attempt = ProbeAttempt(
            attempt_number=1,
            payload={
                "out_trade_no": "TEST",
                "user_id": 1,
            },
            status_code=400,
            response_preview="validation failed",
            interpretation="required field missing",
            mutation_reason="add user_id",
        )

        evidence = ProbeAttemptEvidenceMapper.to_evidence(
            endpoint=self.case.endpoint,
            attempt=attempt,
            url="https://fixture.invalid/api/v1/test/verify",
            headers={
                "Accept": "application/json",
            },
        )

        self.assertIsInstance(
            evidence,
            EvidenceRecord,
        )

        self.assertEqual(
            evidence.endpoint.path,
            "/test/verify",
        )

        self.assertEqual(
            evidence.request.method,
            "POST",
        )

        self.assertEqual(
            evidence.request.url,
            "https://fixture.invalid/api/v1/test/verify",
        )

        self.assertEqual(
            evidence.request.body,
            {
                "out_trade_no": "TEST",
                "user_id": 1,
            },
        )

        self.assertEqual(
            evidence.response.status_code,
            400,
        )

        self.assertEqual(
            evidence.response.body_preview,
            "validation failed",
        )

        self.assertIn(
            "research_attempt=1",
            evidence.notes,
        )

        self.assertIn(
            "required field missing",
            evidence.notes,
        )

        self.assertIn(
            "add user_id",
            evidence.notes,
        )

    def test_each_attempt_produces_independent_evidence(self):
        attempt_one = ProbeAttempt(
            attempt_number=1,
            payload={
                "out_trade_no": "TEST",
            },
            status_code=400,
            response_preview="missing user_id",
            interpretation="required field missing",
            mutation_reason="add user_id",
        )

        attempt_two = ProbeAttempt(
            attempt_number=2,
            payload={
                "out_trade_no": "TEST",
                "user_id": 1,
            },
            status_code=200,
            response_preview='{"ok":true}',
            interpretation="request accepted",
        )

        evidence_one = ProbeAttemptEvidenceMapper.to_evidence(
            self.case.endpoint,
            attempt_one,
            "https://fixture.invalid/api/v1/test/verify",
        )

        evidence_two = ProbeAttemptEvidenceMapper.to_evidence(
            self.case.endpoint,
            attempt_two,
            "https://fixture.invalid/api/v1/test/verify",
        )

        self.assertEqual(
            evidence_one.request.body,
            {
                "out_trade_no": "TEST",
            },
        )

        self.assertEqual(
            evidence_two.request.body,
            {
                "out_trade_no": "TEST",
                "user_id": 1,
            },
        )

        self.assertEqual(
            evidence_one.response.status_code,
            400,
        )

        self.assertEqual(
            evidence_two.response.status_code,
            200,
        )

        self.assertIn(
            "research_attempt=1",
            evidence_one.notes,
        )

        self.assertIn(
            "research_attempt=2",
            evidence_two.notes,
        )

    def test_research_case_accepts_complete_research_sequence(self):
        self.case.add_invariant(
            SecurityInvariant(
                invariant_type="authorization-boundary",
                statement="caller must remain within authorized object scope",
            )
        )

        self.case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H1",
                statement="object identifier may cross authorization boundary",
            )
        )

        self.case.add_attempt(
            ProbeAttempt(
                attempt_number=1,
                payload={"object_id": 1},
                status_code=400,
                response_preview="validation failed",
            )
        )

        self.case.add_attempt(
            ProbeAttempt(
                attempt_number=2,
                payload={"object_id": 2},
                status_code=200,
                response_preview='{"ok":true}',
            )
        )

        self.case.set_decision(
            ResearchDecision(
                status="INCONCLUSIVE",
                rationale="The response does not establish an authorization boundary violation.",
            )
        )

        self.assertEqual(
            len(self.case.invariants),
            1,
        )

        self.assertEqual(
            len(self.case.hypotheses),
            1,
        )

        self.assertEqual(
            len(self.case.attempts),
            2,
        )

        self.assertEqual(
            self.case.attempts[1].attempt_number,
            2,
        )

        self.assertEqual(
            self.case.decision.status,
            "INCONCLUSIVE",
        )


if __name__ == "__main__":
    unittest.main()
