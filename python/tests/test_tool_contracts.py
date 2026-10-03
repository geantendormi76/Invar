# -*- coding: utf-8 -*-
"""
Phase 9.7 第一单步: Tool Gateway 核心数据契约测试
验证强类型 Spec、凭据脱敏、原始字节物证、安全默认策略与异常防污染
"""

import unittest
from harness.tools.tool_contracts import (
    ToolType,
    ToolExecutionStatus,
    HttpSendSpec,
    ToolExecutionPolicy,
    ToolRequest,
    ToolResult,
)

class ToolContractsTests(unittest.TestCase):

    def test_01_http_send_spec_immutability_and_method_normalization(self) -> None:
        """【契约 1】HttpSendSpec 规范化动词并保持不可变性"""
        spec = HttpSendSpec(method="post ", url="https://api.example.com/orders")
        self.assertEqual(spec.method, "POST")
        self.assertEqual(spec.url, "https://api.example.com/orders")
        with self.assertRaises(AttributeError):
            spec.method = "GET"  # type: ignore

    def test_02_policy_defaults_to_secure_settings(self) -> None:
        """【契约 2】策略默认安全: 默认强制校验 TLS 证书，具备 10MB 物理上限"""
        policy = ToolExecutionPolicy()
        self.assertTrue(policy.verify_tls, "TLS 校验必须默认开启")
        self.assertEqual(policy.timeout_seconds, 10)
        self.assertEqual(policy.max_response_bytes, 10 * 1024 * 1024)

    def test_03_credential_redaction_and_fingerprint_stability(self) -> None:
        """【契约 3】敏感请求头被 100% 安全脱敏，且指纹生成全局确定唯一"""
        spec = HttpSendSpec(
            method="GET",
            url="https://api.example.com/user",
            headers={
                "Authorization": "Bearer super_secret_token_12345",
                "Cookie": "session=sensitive_cookie_abc",
                "Accept": "application/json"
            }
        )
        req = ToolRequest(tool_type=ToolType.CURL, spec=spec)
        redacted = req.get_redacted_headers()
        
        # 断言明文绝不泄露
        self.assertEqual(redacted["Authorization"], "<REDACTED>")
        self.assertEqual(redacted["Cookie"], "<REDACTED>")
        self.assertEqual(redacted["Accept"], "application/json")
        
        # 断言指纹稳定生成 (16位)
        fp1 = req.compute_request_fingerprint()
        fp2 = req.compute_request_fingerprint()
        self.assertEqual(fp1, fp2)
        self.assertEqual(len(fp1), 16)

    def test_04_tool_result_preserves_raw_bytes_and_exact_hash(self) -> None:
        """【契约 4】物证真实性: 原始字节零损耗存留，哈希直接由原始字节派生"""
        payload = b"\x00\x01\x02\x03\xff\xfe RAW_BINARY_DATA"
        res = ToolResult.create(
            status=ToolExecutionStatus.SUCCESS,
            raw_bytes=payload,
            status_code=200
        )
        self.assertEqual(res.raw_bytes, payload)
        self.assertTrue(res.is_binary)
        self.assertIsNone(res.response_body_text)
        # 断言 hash 严密对齐
        import hashlib
        self.assertEqual(res.content_hash, hashlib.sha256(payload).hexdigest())

    def test_05_parse_failure_strictly_forbids_200_status_code(self) -> None:
        """【契约 5】解析异常防污染: 状态为 PARSE_FAILURE 时状态码强制置为 None，严禁伪造 200"""
        res = ToolResult.create(
            status=ToolExecutionStatus.PARSE_FAILURE,
            raw_bytes=b"CORRUPTED_STREAM",
            status_code=200  # 外部尝试传入 200 污染
        )
        self.assertIsNone(res.status_code, "解析失败时状态码绝不可为 200")
        self.assertEqual(res.status, ToolExecutionStatus.PARSE_FAILURE)
