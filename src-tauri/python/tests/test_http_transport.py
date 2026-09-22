import unittest
from unittest.mock import Mock, patch

from harness.transport import HttpTransport, TransportResponse


class TestHttpTransport(unittest.TestCase):
    def setUp(self):
        self.transport = HttpTransport()

    def test_post_uses_json_payload(self):
        response = Mock()
        response.status_code = 200
        response.text = '{"ok":true}'
        response.headers = {"Content-Type": "application/json"}

        payload = {"name": "alice"}
        headers = {"Accept": "application/json"}

        with patch("harness.transport.requests.request", return_value=response) as request_mock:
            result = self.transport.request(
                method="post",
                url="https://fixture.invalid/api/test",
                payload=payload,
                headers=headers,
                timeout=5,
            )

        self.assertIsInstance(result, TransportResponse)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.text, '{"ok":true}')
        self.assertEqual(result.headers, {"Content-Type": "application/json"})

        request_mock.assert_called_once_with(
            "POST",
            "https://fixture.invalid/api/test",
            headers=headers,
            timeout=5,
            json=payload,
        )

    def test_get_uses_query_params(self):
        response = Mock()
        response.status_code = 404
        response.text = "not found"
        response.headers = {"Content-Type": "text/plain"}

        payload = {"user_id": 1}
        headers = {"Accept": "application/json"}

        with patch("harness.transport.requests.request", return_value=response) as request_mock:
            result = self.transport.request(
                method="get",
                url="https://fixture.invalid/api/test",
                payload=payload,
                headers=headers,
                timeout=5,
            )

        self.assertIsInstance(result, TransportResponse)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.text, "not found")
        self.assertEqual(result.headers, {"Content-Type": "text/plain"})

        request_mock.assert_called_once_with(
            "GET",
            "https://fixture.invalid/api/test",
            headers=headers,
            timeout=5,
            params=payload,
        )


if __name__ == "__main__":
    unittest.main()
