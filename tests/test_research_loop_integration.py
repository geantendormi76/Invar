import unittest
from unittest.mock import patch

from harness.evidence import EvidenceRecord
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor
from harness.transport import HttpTransport
from harness.feedback import FeedbackInterpreter


class TransportResult:
    def __init__(
        self,
        status_code,
        text,
        headers,
    ):
        self.status_code = status_code
        self.text = text
        self.headers = headers


class TestResearchLoopIntegration(unittest.TestCase):
    def test_each_loop_round_is_recorded_as_probe_attempt(self):
        endpoint = EndpointIR(
            method="POST",
            path="/test/verify",
            extracted_params=["out_trade_no"],
            source_file="fixture.js",
            line=1,
            call_signature="request",
        )

        first_result = TransportResult(
            400,
            (
                "Key: 'VerifyOrderRequest.UserId' "
                "failed on the 'required' tag"
            ),
            {"Content-Type": "application/json"},
        )

        second_result = TransportResult(
            200,
            '{"ok":true}',
            {"Content-Type": "application/json"},
        )

        executor = AdaptiveSandboxExecutor()

        with patch.object(
            HttpTransport,
            "request",
            side_effect=[
                first_result,
                second_result,
            ],
        ):
            evidence = executor.probe_endpoint(
                endpoint,
                base_url="https://fixture.invalid/api/v1",
            )

        self.assertIsInstance(
            evidence,
            EvidenceRecord,
        )

        self.assertEqual(
            evidence.response.status_code,
            200,
        )

        self.assertIn(
            "自愈变异成功击穿契约",
            evidence.notes,
        )

        first_payload = {
            "out_trade_no": "TEST_PROBE_VALUE",
        }

        second_payload = {
            "out_trade_no": "TEST_PROBE_VALUE",
            "user_id": 1,
        }

        expected_attempts = [
            (1, first_payload, 400),
            (2, second_payload, 200),
        ]

        research_case = executor._create_research_case(
            endpoint
        )

        for attempt_number, payload, status_code in expected_attempts:
            research_case.record_attempt(
                payload=payload,
                status_code=status_code,
                response_preview="fixture",
            )

        self.assertEqual(
            len(research_case.attempts),
            2,
        )

        self.assertEqual(
            research_case.attempts[0].attempt_number,
            1,
        )

        self.assertEqual(
            research_case.attempts[0].payload,
            first_payload,
        )

        self.assertEqual(
            research_case.attempts[0].status_code,
            400,
        )

        self.assertEqual(
            research_case.attempts[1].attempt_number,
            2,
        )

        self.assertEqual(
            research_case.attempts[1].payload,
            second_payload,
        )

        self.assertEqual(
            research_case.attempts[1].status_code,
            200,
        )

    def test_research_case_attempt_sequence_remains_contiguous(self):
        endpoint = EndpointIR(
            method="GET",
            path="/fixture",
        )

        executor = AdaptiveSandboxExecutor()
        case = executor._create_research_case(endpoint)

        case.record_attempt(
            payload={},
            status_code=404,
            response_preview="not found",
        )

        case.record_attempt(
            payload={"id": 1},
            status_code=200,
            response_preview="ok",
        )

        self.assertEqual(
            [a.attempt_number for a in case.attempts],
            [1, 2],
        )


if __name__ == "__main__":
    unittest.main()
