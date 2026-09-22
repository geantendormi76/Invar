import unittest
from unittest.mock import patch

from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class ResearchEvidenceBridgeTests(unittest.TestCase):
    def test_production_probe_path_uses_research_evidence_mapper(self) -> None:
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
            result = executor._probe_endpoint_with_research_case(endpoint)

        evidence = result.evidence
        research_case = result.research_case

        self.assertEqual(len(research_case.attempts), 2)
        self.assertEqual(evidence.endpoint, endpoint)
        self.assertEqual(evidence.finding_type, "ENDPOINT_PROBE")
        self.assertFalse(evidence.is_anomaly)

        self.assertEqual(
            evidence.request.body,
            research_case.attempts[-1].payload,
        )
        self.assertEqual(
            evidence.response.status_code,
            research_case.attempts[-1].status_code,
        )
        self.assertEqual(
            evidence.response.body_preview,
            research_case.attempts[-1].response_preview,
        )
        self.assertEqual(
            evidence.response.headers,
            {"X-Fixture": "research"},
        )

        self.assertIn("research_attempt=2", evidence.notes)
        self.assertIn("契约结果达到收敛条件", evidence.notes)


if __name__ == "__main__":
    unittest.main()
