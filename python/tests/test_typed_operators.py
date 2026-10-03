# -*- coding: utf-8 -*-
"""
Phase 9.8 第三单步: 强类型算子库 (Typed Operators) 契约测试
验证 F1~F3 算子纯函数生成规格、URL 与 Header 变换正确性、不可变性与 HttpSendSpec 兼容性
"""

import unittest
from harness.skills.typed_operators import (
    PathNormalizationOperator,
    MethodTunnelOperator,
    HeaderTrustOperator
)
from harness.tools.tool_contracts import HttpSendSpec

class TypedOperatorsTests(unittest.TestCase):

    def test_01_path_normalization_operator_generates_essential_variants(self) -> None:
        """【契约 1】PathNormalizationOperator 确定性生成 Tomcat 分号、点号与多斜杠规格"""
        specs = PathNormalizationOperator.generate_specs(
            method="GET",
            url="https://api.example.com/api/v1/users"
        )
        self.assertGreater(len(specs), 5)
        urls = [s.url for s in specs]

        # 必须覆盖核心畸变技巧
        self.assertTrue(any("/..;/" in u for u in urls), "必须包含 Tomcat 分号跳跃")
        self.assertTrue(any("/;/" in u for u in urls), "必须包含 Tomcat 分号截断")
        self.assertTrue(any("//" in u for u in urls), "必须包含多斜杠")
        self.assertTrue(any(".json" in u for u in urls), "必须包含扩展名伪装")
        
        # 每一个元素均为强类型的 HttpSendSpec
        for s in specs:
            self.assertIsInstance(s, HttpSendSpec)
            self.assertEqual(s.method, "GET")

    def test_02_method_tunnel_operator_generates_headers_and_verbs(self) -> None:
        """【契约 2】MethodTunnelOperator 确定性生成 X-HTTP-Method-Override 隧道头与替代动词"""
        specs = MethodTunnelOperator.generate_specs(
            method="DELETE",
            url="https://api.example.com/api/orders/purge",
            headers={"Accept": "application/json"},
            target_verb="DELETE"
        )
        self.assertGreater(len(specs), 3)

        # 验证隧道请求头
        override_specs = [s for s in specs if "X-HTTP-Method-Override" in s.headers]
        self.assertEqual(len(override_specs), 1)
        self.assertEqual(override_specs[0].method, "POST")
        self.assertEqual(override_specs[0].headers["X-HTTP-Method-Override"], "DELETE")
        self.assertEqual(override_specs[0].headers["Accept"], "application/json")

    def test_03_header_trust_operator_generates_rewrite_and_ip_spoofing(self) -> None:
        """【契约 3】HeaderTrustOperator 确定性生成 X-Rewrite-URL 与内网 IP 伪装头"""
        target_url = "https://api.example.com/admin/secrets"
        specs = HeaderTrustOperator.generate_specs(
            method="GET",
            url=target_url
        )
        self.assertGreater(len(specs), 5)

        # 1. 验证代理重写头 (目标指向根路由 /，头部指定内部路径)
        rewrite_specs = [s for s in specs if "X-Rewrite-URL" in s.headers]
        self.assertEqual(len(rewrite_specs), 1)
        self.assertEqual(rewrite_specs[0].url, "https://api.example.com/")
        self.assertEqual(rewrite_specs[0].headers["X-Rewrite-URL"], "/admin/secrets")

        # 2. 验证内网 IP 伪装头
        ip_specs = [s for s in specs if s.headers.get("X-Forwarded-For") == "127.0.0.1"]
        self.assertEqual(len(ip_specs), 1)
        self.assertEqual(ip_specs[0].url, target_url)
