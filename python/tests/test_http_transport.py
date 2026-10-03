# -*- coding: utf-8 -*-
"""
HttpTransport 物理契约测试 (已升级为基于 LocalFixtureServer 的确定性测试)
验证 HttpTransport 在重构为 Tool Gateway 门面后：
1. POST 载荷以 application/json 物理发包并被接收；
2. GET 载荷以 urlencode query params 物理发包并被接收；
3. 状态码与响应头符合 TransportResponse 契约。
"""

import unittest
import json
from fixtures.local_server_fixture import LocalFixtureServer
from harness.transport import HttpTransport, TransportResponse


class TestHttpTransport(unittest.TestCase):
    def setUp(self):
        self.transport = HttpTransport()

    def test_post_uses_json_payload(self):
        """【契约 1】POST 动词下 payload 自动序列化为 JSON 物理发包"""
        with LocalFixtureServer() as fixture:
            payload = {"name": "alice", "role": "admin"}
            headers = {"Accept": "application/json"}

            result = self.transport.request(
                method="post",
                url=f"{fixture.base_url}/echo_body",
                payload=payload,
                headers=headers,
                timeout=5,
            )

            self.assertIsInstance(result, TransportResponse)
            self.assertEqual(result.status_code, 200)
            received_body = json.loads(result.text)
            self.assertEqual(received_body, payload)
            self.assertEqual(result.headers.get("x-body-length"), str(len(result.text.encode("utf-8"))))

    def test_get_uses_query_params(self):
        """【契约 2】GET 动词下 payload 自动转换为 URL Query 参数物理发包"""
        with LocalFixtureServer() as fixture:
            payload = {"delay": 0.05}
            headers = {"Accept": "application/json"}

            result = self.transport.request(
                method="get",
                url=f"{fixture.base_url}/slow",
                payload=payload,
                headers=headers,
                timeout=5,
            )

            self.assertIsInstance(result, TransportResponse)
            self.assertEqual(result.status_code, 200)
            self.assertIn("slow_completed", result.text)

    def test_forbidden_and_not_found_contracts(self):
        """【契约 3】403 与 404 真实状态码与响应体零损耗映射"""
        with LocalFixtureServer() as fixture:
            res_403 = self.transport.request("get", f"{fixture.base_url}/forbidden", headers={}, timeout=5)
            self.assertEqual(res_403.status_code, 403)
            self.assertIn("forbidden", res_403.text)

            res_404 = self.transport.request("get", f"{fixture.base_url}/not_found", headers={}, timeout=5)
            self.assertEqual(res_404.status_code, 404)
            self.assertIn("route_not_found", res_404.text)


if __name__ == "__main__":
    unittest.main()
