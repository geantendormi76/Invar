# -*- coding: utf-8 -*-
"""
确定性本地测试桩本身的行为与生命周期测试
使用 Python 标准库 urllib 验证各场景在本地回环上的纯净表现
"""

import unittest
import urllib.request
import urllib.error
import json
from fixtures.local_server_fixture import LocalFixtureServer

class LocalServerFixtureTests(unittest.TestCase):

    def test_01_fixture_lifecycle_and_port_binding(self) -> None:
        """【契约 1】测试桩在上下文管理器内正确动态绑定未占用端口并在退出后释放"""
        with LocalFixtureServer() as fixture:
            base_url = fixture.base_url
            self.assertTrue(base_url.startswith("http://127.0.0.1:"))
            self.assertGreater(fixture.port, 1024)
            
            # 物理验证服务在线
            with urllib.request.urlopen(f"{base_url}/ok", timeout=2) as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(body["status"], "ok")
                self.assertEqual(resp.headers.get("X-Invar-Echo"), "fixture-ok")

    def test_02_fixture_echo_headers_and_body(self) -> None:
        """【契约 2】测试桩精准回显标头与请求体，验证物理网络真实发包"""
        with LocalFixtureServer() as fixture:
            # 1. 标头回显
            req = urllib.request.Request(
                f"{fixture.base_url}/echo_headers",
                headers={"X-Test-Auth": "token-12345"}
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                headers_echo = json.loads(resp.read().decode("utf-8"))
                # urllib 会将 header key 规范化首字母大写，检查存在性
                self.assertEqual(headers_echo.get("X-Test-Auth"), "token-12345")

            # 2. Body 回显
            test_payload = b"PHYSICAL_PAYLOAD_BYTES_XYZ"
            post_req = urllib.request.Request(
                f"{fixture.base_url}/echo_body",
                data=test_payload,
                method="POST"
            )
            with urllib.request.urlopen(post_req, timeout=2) as resp:
                body_echo = resp.read()
                self.assertEqual(body_echo, test_payload)

    def test_03_fixture_handles_status_codes_and_binary(self) -> None:
        """【契约 3】测试桩支持 403、404 与真实物理二进制流"""
        with LocalFixtureServer() as fixture:
            # 1. 403 响应
            with self.assertRaises(urllib.error.HTTPError) as ctx_403:
                urllib.request.urlopen(f"{fixture.base_url}/forbidden", timeout=2)
            self.assertEqual(ctx_403.exception.code, 403)

            # 2. 404 响应
            with self.assertRaises(urllib.error.HTTPError) as ctx_404:
                urllib.request.urlopen(f"{fixture.base_url}/not_found", timeout=2)
            self.assertEqual(ctx_404.exception.code, 404)

            # 3. 二进制响应
            with urllib.request.urlopen(f"{fixture.base_url}/binary", timeout=2) as resp:
                bin_data = resp.read()
                self.assertIn(b"\x00\x01\x02\x03\xff\xfe", bin_data)
