import unittest
from unittest.mock import patch

from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class SandboxBaseUrlCompatibilityTests(unittest.TestCase):
    def test_probe_all_accepts_cli_base_url_override(self) -> None:
        endpoint = EndpointIR(
            method="GET",
            path="/api/orders",
            source_file="fixture.js",
            line=10,
            is_dynamic=False,
            extracted_params=[],
            tags=[],
            risk_score=1.0,
            confidence=0.95,
            call_signature="client.get('/api/orders')",
        )

        config = InvarConfig(
            target_api_base="http://default.invalid/api/v1",
            request_timeout=1,
            max_concurrent_workers=1,
            max_mutation_rounds=1,
        )

        executor = AdaptiveSandboxExecutor(config)

        with patch.object(
            executor.transport,
            "request",
        ) as request_mock:
            class FakeResponse:
                status_code = 404
                text = ""
                headers = {}

            request_mock.return_value = FakeResponse()

            executor.probe_all(
                [endpoint],
                base_url="http://override.invalid/api/v2",
            )

        request_mock.assert_called_once()

        call_kwargs = request_mock.call_args.kwargs

        self.assertEqual(
            call_kwargs["url"],
            "http://override.invalid/api/v2/api/orders",
        )


if __name__ == "__main__":
    unittest.main()
