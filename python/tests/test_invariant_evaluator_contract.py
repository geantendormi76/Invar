# -*- coding: utf-8 -*-
"""
Security Invariant Evaluator 核心科学裁决契约测试
对齐 RFC 9110 动词拒绝语义与 Anthropic Reference Harness 黄金标准：
断言 405 策略拒绝属于底线守住 (confirmed)，并断言不变量击穿判定不受 URL 'admin' 字符猜忌限制。
"""
import unittest
from harness.domain_contracts import EndpointIR, SecurityInvariant
from harness.invariant_evaluator import InvariantEvaluator


class InvariantEvaluatorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.auth_inv = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="Sensitive administration routes must enforce authentication",
        )

    def test_01_http_405_method_policy_denial_is_confirmed(self) -> None:
        """【契约 1】无凭据请求收到 HTTP 405 (Method Not Allowed) 时，判定安全底线未被击穿 (confirmed)"""
        endpoint = EndpointIR(method="POST", path="/users/${H}/reset-password")
        
        evaluation = InvariantEvaluator.evaluate(
            invariant=self.auth_inv,
            endpoint=endpoint,
            status_code=405,
            payload={},
            headers={},
            response_text="405 Method Not Allowed",
        )

        self.assertEqual(
            evaluation.status,
            "confirmed",
            "根据 RFC 9110，未认证发包收到 405 动词拒绝策略时，请求被服务端拒绝，安全底线守住，绝不可落入 inconclusive",
        )

    def test_02_unauthenticated_200_flags_vulnerable_without_admin_keyword(self) -> None:
        """【契约 2】挂载 auth_boundary 的非 admin 路径若在无凭据下被真实 200 放行，必须确权击穿 (vulnerable)"""
        endpoint = EndpointIR(method="POST", path="/fs/recursive_move", tags=[])

        evaluation = InvariantEvaluator.evaluate(
            invariant=self.auth_inv,
            endpoint=endpoint,
            status_code=200,
            payload={"src_dir": "a", "dst_dir": "b"},
            headers={},  # 无鉴权凭证
            response_text='{"status": "ok", "moved": true}',  # 真实 API 放行，非 SPA 首页
        )

        self.assertEqual(
            evaluation.status,
            "vulnerable",
            "只要挂载了 auth_boundary 不变量，无凭据真实 200 放行必须确权为 vulnerable，严禁因路径不含 'admin' 而漏报",
        )


if __name__ == "__main__":
    unittest.main()
