import unittest
from unittest.mock import Mock, patch

from harness.feedback import FeedbackInterpreter
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor
from harness.transport import HttpTransport


class TestAdaptiveSandboxIntegration(unittest.TestCase):
    def test_executor_uses_transport_and_feedback_boundaries(self):
        endpoint = EndpointIR(
            method="POST",
            path="/test/verify",
            extracted_params=["out_trade_no"],
            source_file="fixture.js",
            line=1,
            call_signature="request",
        )

        first_response = Mock()
        first_response.status_code = 400
        first_response.text = (
            "Key: 'VerifyOrderRequest.UserId' "
            "failed on the 'required' tag"
        )
        first_response.headers = {
            "Content-Type": "application/json"
        }

        second_response = Mock()
        second_response.status_code = 200
        second_response.text = '{"ok":true}'
        second_response.headers = {
            "Content-Type": "application/json"
        }

        executor = AdaptiveSandboxExecutor()

        with patch.object(
            HttpTransport,
            "request",
            side_effect=[
                type(
                    "TransportResult",
                    (),
                    {
                        "status_code": 400,
                        "text": first_response.text,
                        "headers": dict(first_response.headers),
                    },
                )(),
                type(
                    "TransportResult",
                    (),
                    {
                        "status_code": 200,
                        "text": second_response.text,
                        "headers": dict(second_response.headers),
                    },
                )(),
            ],
        ) as transport_mock, patch.object(
            FeedbackInterpreter,
            "interpret",
            wraps=executor.feedback_interpreter.interpret,
        ) as feedback_mock:
            evidence = executor.probe_endpoint(
                endpoint,
                base_url="https://fixture.invalid/api/v1",
            )

        self.assertEqual(transport_mock.call_count, 2)
        self.assertEqual(feedback_mock.call_count, 2)

        self.assertIsNotNone(
            feedback_mock.call_args_list[0]
        )
        self.assertEqual(
            feedback_mock.call_args_list[0].kwargs["status_code"],
            400,
        )
        self.assertIn(
            "VerifyOrderRequest.UserId",
            feedback_mock.call_args_list[0].kwargs["response_text"],
        )

        self.assertEqual(
            transport_mock.call_args_list[0].kwargs["method"],
            "POST",
        )
        self.assertEqual(
            transport_mock.call_args_list[0].kwargs["payload"],
            {"out_trade_no": "TEST_PROBE_VALUE"},
        )

        self.assertEqual(
            transport_mock.call_args_list[1].kwargs["payload"],
            {
                "out_trade_no": "TEST_PROBE_VALUE",
                "user_id": 1,
            },
        )

        self.assertEqual(
            evidence.response.status_code,
            200,
        )
        self.assertIn(
            "自愈变异成功击穿契约",
            evidence.notes,
        )


if __name__ == "__main__":
    unittest.main()
