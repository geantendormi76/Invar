import unittest
from unittest.mock import patch, Mock

from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class TestAdaptiveSandboxExecutorBaseline(unittest.TestCase):
    def test_feedback_mutation_loop_is_preserved(self):
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
            "Key: 'VerifyOrderRequest.UserId' failed on the 'required' tag"
        )
        first_response.headers = {"Content-Type": "application/json"}

        second_response = Mock()
        second_response.status_code = 200
        second_response.text = '{"ok":true}'
        second_response.headers = {"Content-Type": "application/json"}

        with patch("harness.transport.requests.request") as request_mock:
            request_mock.side_effect = [first_response, second_response]

            executor = AdaptiveSandboxExecutor()
            evidence = executor.probe_endpoint(
                endpoint,
                base_url="https://fixture.invalid/api/v1",
            )

        self.assertEqual(request_mock.call_count, 2)

        first_call = request_mock.call_args_list[0]
        second_call = request_mock.call_args_list[1]

        self.assertEqual(first_call.kwargs["json"], {"out_trade_no": "TEST_PROBE_VALUE"})
        self.assertEqual(
            second_call.kwargs["json"],
            {
                "out_trade_no": "TEST_PROBE_VALUE",
                "user_id": 1,
            },
        )

        self.assertEqual(evidence.response.status_code, 200)
        self.assertIn("契约结果达到收敛条件", evidence.notes)


if __name__ == "__main__":
    unittest.main()
