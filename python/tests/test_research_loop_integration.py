import unittest
from unittest.mock import patch

from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class ResearchLoopIntegrationTests(unittest.TestCase):
    def test_real_probe_loop_records_every_attempt_in_research_case(self) -> None:
        endpoint = EndpointIR(
            method="POST",
            path="/api/orders",
            source_file="fixture.js",
            line=10,
            is_dynamic=False,
            extracted_params=["orderId"],
            tags=[],
            risk_score=5.0,
            confidence=0.95,
            call_signature="client.post('/api/orders')",
        )

        config = InvarConfig(
            target_api_base="http://fixture.invalid",
            request_timeout=1,
            max_concurrent_workers=1,
            max_mutation_rounds=3,
        )

        executor = AdaptiveSandboxExecutor(config)

        responses = [
            (400, "Key: 'Order.OrderId' failed on the 'required' tag"),
            (201, '{"ok":true}'),
        ]

        def fake_request(method, url, payload, headers, timeout):
            status_code, text = responses.pop(0)

            class FakeResponse:
                pass

            result = FakeResponse()
            result.status_code = status_code
            result.text = text
            result.headers = {}
            return result

        with patch.object(executor.transport, "request", side_effect=fake_request):
            result = executor._probe_endpoint_with_research_case(endpoint)

        evidence = result.evidence
        research_case = result.research_case

        self.assertEqual(evidence.finding_type, "ENDPOINT_PROBE")
        self.assertEqual(len(research_case.attempts), 2)

        first_attempt = research_case.attempts[0]
        second_attempt = research_case.attempts[1]

        self.assertEqual(first_attempt.attempt_number, 1)
        self.assertEqual(first_attempt.status_code, 400)
        self.assertIn("OrderId", first_attempt.response_preview)
        self.assertEqual(first_attempt.payload, {"orderId": 1})
        self.assertNotEqual(first_attempt.mutation_reason, "")

        self.assertEqual(second_attempt.attempt_number, 2)
        self.assertEqual(second_attempt.status_code, 201)
        self.assertEqual(
            second_attempt.payload,
            {
                "orderId": 1,
                "order_id": 1,
            },
        )
        self.assertEqual(
            second_attempt.interpretation,
            "契约结果达到收敛条件",
        )

        self.assertEqual(
            evidence.request.body,
            second_attempt.payload,
        )

    def test_research_case_attempt_sequence_remains_contiguous(self) -> None:
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
