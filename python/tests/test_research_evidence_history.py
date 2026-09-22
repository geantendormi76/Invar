import unittest
from unittest.mock import patch

from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.research_evidence import ProbeAttemptEvidenceMapper
from harness.sandbox_executor import AdaptiveSandboxExecutor


class ResearchEvidenceHistoryTests(unittest.TestCase):
    def test_research_case_maps_all_attempts_to_evidence_records(self) -> None:
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

        history = ProbeAttemptEvidenceMapper.to_evidence_records(
            research_case=research_case,
            url="http://fixture.invalid/api/orders",
            headers=config.custom_headers,
        )

        self.assertEqual(len(history), 2)

        self.assertEqual(
            history[0].request.body,
            {"orderId": 1},
        )
        self.assertEqual(history[0].response.status_code, 400)
        self.assertIn("research_attempt=1", history[0].notes)
        self.assertIn("反馈包含可识别变异线索", history[0].notes)

        self.assertEqual(
            history[1].request.body,
            {
                "orderId": 1,
                "order_id": 1,
            },
        )
        self.assertEqual(history[1].response.status_code, 201)
        self.assertIn("research_attempt=2", history[1].notes)
        self.assertIn("契约结果达到收敛条件", history[1].notes)

        self.assertEqual(
            evidence.request.body,
            history[-1].request.body,
        )


if __name__ == "__main__":
    unittest.main()
