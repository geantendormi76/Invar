import unittest
from unittest.mock import patch, Mock

from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class TestAdaptiveSandboxTransportBaseline(unittest.TestCase):
    def test_post_payload_is_sent_as_json(self):
        endpoint = EndpointIR(
            method="POST",
            path="/fixture/post",
            extracted_params=["name"],
            source_file="fixture.js",
            line=1,
            call_signature="request",
        )

        response = Mock()
        response.status_code = 422
        response.text = "validation failed"
        response.headers = {"Content-Type": "application/json"}

        with patch("harness.transport.requests.request") as request_mock:
            request_mock.return_value = response

            executor = AdaptiveSandboxExecutor()
            executor.probe_endpoint(
                endpoint,
                base_url="https://fixture.invalid/api/v1",
            )

        self.assertEqual(request_mock.call_count, 1)
        call = request_mock.call_args

        self.assertEqual(call.args[0], "POST")
        self.assertEqual(
            call.kwargs["json"],
            {"name": "TEST_PROBE_VALUE"},
        )
        self.assertNotIn("params", call.kwargs)

    def test_get_payload_is_sent_as_query_params(self):
        endpoint = EndpointIR(
            method="GET",
            path="/fixture/get",
            extracted_params=["user_id"],
            source_file="fixture.js",
            line=1,
            call_signature="request",
        )

        response = Mock()
        response.status_code = 404
        response.text = "not found"
        response.headers = {"Content-Type": "application/json"}

        with patch("harness.transport.requests.request") as request_mock:
            request_mock.return_value = response

            executor = AdaptiveSandboxExecutor()
            executor.probe_endpoint(
                endpoint,
                base_url="https://fixture.invalid/api/v1",
            )

        self.assertEqual(request_mock.call_count, 1)
        call = request_mock.call_args

        self.assertEqual(call.args[0], "GET")
        self.assertEqual(
            call.kwargs["params"],
            {"user_id": 1},
        )
        self.assertNotIn("json", call.kwargs)


if __name__ == "__main__":
    unittest.main()
