# -*- coding: utf-8 -*-
"""
Phase 9.7 第三单步: CurlToolAdapter 确定性物理网络契约测试
基于 LocalFixtureServer 实施 100% 离线、物理发包验真，杜绝任何外部网络依赖与二义性断言
"""

import unittest
from fixtures.local_server_fixture import LocalFixtureServer
from harness.tools.tool_contracts import (
    ToolType,
    ToolExecutionStatus,
    HttpSendSpec,
    ToolExecutionPolicy,
    ToolRequest,
)
from harness.tools.curl_adapter import CurlToolAdapter
from harness.domain_contracts import (
    ResearchScope,
    RoEBoundaryViolationError,
    OutOfScopeError,
)

class CurlToolAdapterTests(unittest.TestCase):

    def test_01_curl_adapter_ok_response_and_raw_bytes(self) -> None:
        """【契约 1】访问本地测试桩 /ok，捕获真实 200、原生标头与物理原始字节"""
        with LocalFixtureServer() as fixture:
            spec = HttpSendSpec(method="GET", url=f"{fixture.base_url}/ok")
            req = ToolRequest(tool_type=ToolType.CURL, spec=spec)
            
            res = CurlToolAdapter.execute(req)
            self.assertEqual(res.status, ToolExecutionStatus.SUCCESS)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"fixture_ready", res.raw_bytes)
            self.assertEqual(res.response_headers.get("x-invar-echo"), "fixture-ok")
            self.assertFalse(res.is_binary)
            self.assertGreater(res.latency_ms, 0.0)

    def test_02_curl_adapter_forbidden_and_not_found(self) -> None:
        """【契约 2】准确单射 403 与 404 状态码，不发生任何语义伪造"""
        with LocalFixtureServer() as fixture:
            # 1. 403
            spec_403 = HttpSendSpec(method="GET", url=f"{fixture.base_url}/forbidden")
            res_403 = CurlToolAdapter.execute(ToolRequest(tool_type=ToolType.CURL, spec=spec_403))
            self.assertEqual(res_403.status_code, 403)
            self.assertEqual(res_403.status, ToolExecutionStatus.SUCCESS)

            # 2. 404
            spec_404 = HttpSendSpec(method="GET", url=f"{fixture.base_url}/not_found")
            res_404 = CurlToolAdapter.execute(ToolRequest(tool_type=ToolType.CURL, spec=spec_404))
            self.assertEqual(res_404.status_code, 404)
            self.assertEqual(res_404.status, ToolExecutionStatus.SUCCESS)

    def test_03_curl_adapter_binary_response_preserves_raw_bytes(self) -> None:
        """【契约 3】遇到二进制响应体，保持原始字节零转译损耗，标记 is_binary=True"""
        with LocalFixtureServer() as fixture:
            spec = HttpSendSpec(method="GET", url=f"{fixture.base_url}/binary")
            res = CurlToolAdapter.execute(ToolRequest(tool_type=ToolType.CURL, spec=spec))
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.is_binary)
            self.assertIn(b"\x00\x01\x02\x03\xff\xfe", res.raw_bytes)
            self.assertIsNone(res.response_body_text)

    def test_04_curl_adapter_deterministic_timeout(self) -> None:
        """【契约 4】确定性物理超时: 目标延迟 2.0s，策略超时设为 1s -> 确定性熔断 TIMEOUT"""
        with LocalFixtureServer() as fixture:
            spec = HttpSendSpec(method="GET", url=f"{fixture.base_url}/slow?delay=2.0")
            policy = ToolExecutionPolicy(timeout_seconds=1)
            req = ToolRequest(tool_type=ToolType.CURL, spec=spec, policy=policy)
            
            res = CurlToolAdapter.execute(req)
            self.assertEqual(res.status, ToolExecutionStatus.TIMEOUT)
            self.assertIsNone(res.status_code, "超时状态下状态码必须为 None，严禁伪造")
            self.assertIn("timed out", res.error_message.lower())

    def test_05_credential_physical_delivery_and_audit_redaction(self) -> None:
        """【契约 5】凭据物理送达与审计脱敏物理隔离:
           服务端收到明文 Token，但 ToolResult 记录的命令中 100% 安全脱敏"""
        with LocalFixtureServer() as fixture:
            secret_token = "Bearer secret_jwt_token_99999"
            spec = HttpSendSpec(
                method="GET",
                url=f"{fixture.base_url}/echo_headers",
                headers={"Authorization": secret_token, "Cookie": "session=sensitive_abc"}
            )
            req = ToolRequest(tool_type=ToolType.CURL, spec=spec)
            res = CurlToolAdapter.execute(req)

            # 1. 断言服务端物理收到了真实的凭据
            import json
            server_received = json.loads(res.raw_bytes.decode("utf-8"))
            self.assertEqual(server_received.get("Authorization"), secret_token)

            # 2. 断言审计命令字符串中绝不包含明文凭证
            self.assertNotIn("secret_jwt_token_99999", res.redacted_command)
            self.assertNotIn("sensitive_abc", res.redacted_command)
            self.assertIn("<REDACTED>", res.redacted_command)

    def test_06_roe_boundary_enforcement_blocks_before_curl_process(self) -> None:
        """【契约 6】RoE 门禁在前置完成物理拦截，违规发包时绝对禁止启动 curl"""
        scope = ResearchScope(
            target_domain="127.0.0.1",
            allowed_methods=["GET"],
            excluded_paths=["/api/v1/forbidden"]
        )

        # 场景 A: 越界主机
        out_req = ToolRequest(
            tool_type=ToolType.CURL,
            spec=HttpSendSpec(method="GET", url="http://internal.evil.corp/secret")
        )
        with self.assertRaises(OutOfScopeError):
            CurlToolAdapter.execute(out_req, scope=scope)

        # 场景 B: 排除黑名单路径
        blocked_req = ToolRequest(
            tool_type=ToolType.CURL,
            spec=HttpSendSpec(method="GET", url="http://127.0.0.1:8080/api/v1/forbidden")
        )
        with self.assertRaises(RoEBoundaryViolationError):
            CurlToolAdapter.execute(blocked_req, scope=scope)
