import unittest
from unittest.mock import patch

from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class ResearchExecutionResultTests(unittest.TestCase):
    def test_research_execution_result_exposes_full_history(self) -> None:
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
            result.headers = {"X-Fixture": "research"}
            return result

        with patch.object(executor.transport, "request", side_effect=fake_request):
            result = executor.probe_endpoint_with_research(endpoint)

        self.assertEqual(len(result.research_case.attempts), 2)
        self.assertEqual(len(result.evidence_history), 2)

        self.assertEqual(
            result.evidence_history[0].response.status_code,
            400,
        )
        self.assertEqual(
            result.evidence_history[1].response.status_code,
            201,
        )

        self.assertEqual(
            result.evidence_history[0].request.body,
            {"orderId": 1},
        )
        self.assertEqual(
            result.evidence_history[1].request.body,
            {
                "orderId": 1,
                "order_id": 1,
            },
        )

        self.assertEqual(
            result.evidence,
            result.evidence_history[-1],
        )
        self.assertEqual(
            result.evidence.response.headers,
            {"X-Fixture": "research"},
        )

    def test_legacy_probe_endpoint_still_returns_evidence_record(self) -> None:
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

        class FakeResponse:
            status_code = 201
            text = '{"ok":true}'
            headers = {}

        with patch.object(
            executor.transport,
            "request",
            return_value=FakeResponse(),
        ):
            evidence = executor.probe_endpoint(endpoint)

        self.assertEqual(evidence.finding_type, "ENDPOINT_PROBE")
        self.assertEqual(evidence.response.status_code, 201)


if __name__ == "__main__":
    unittest.main()
