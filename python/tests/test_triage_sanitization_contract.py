# -*- coding: utf-8 -*-
"""
Triage Dispatcher 候选端点合法性清洗门禁契约测试 (Endpoint Sanitization Contract)
对齐彭峙酿博士《Hacking with LLMs》与 Tencent A.I.G 黄金标准：
断言所有包含换行符、大段中文法律条款以及类前端调用表达式的脏样本在上游被严密过滤，
确保任务库存与覆盖账本绝不受非 API 噪声污染。
"""
import unittest
from harness.triage_dispatcher import TriageDispatcher


class TriageSanitizationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dispatcher = TriageDispatcher()

    def test_01_rejects_paths_with_newlines_or_chinese_clauses(self) -> None:
        """【契约 1】包含换行符或非 ASCII 法律免责声明的文本必须被清洗拦截"""
        dirty_chinese_clause = (
            "/\n                对于用户通过爱快服务后台上传到认证相关页面上可公开获取区域的任何内容，"
            "用户同意授予爱快在全世界范围内享有完全的、免费的、永久性的权利..."
        )
        self.assertFalse(
            self.dispatcher._is_valid_api_path(dirty_chinese_clause),
            "包含换行符和大段中文免责声明的文本绝不可判定为合法 API 路径",
        )

    def test_02_rejects_client_method_call_expressions(self) -> None:
        """【契约 2】前端 SDK 内部调用表达式 (如 this._instance.requestRouter...) 必须被拦截"""
        client_expr = (
            '/this._instance.requestRouter.endpointFor("api","/api/product_tours/?token="+this._instance.config.token)'
        )
        self.assertFalse(
            self.dispatcher._is_valid_api_path(client_expr),
            "前端类方法调用表达式绝不可判定为合法静态 API 路由",
        )

    def test_03_accepts_clean_standard_api_paths(self) -> None:
        """【契约 3】标准纯净的业务 API 路由必须正常通过"""
        clean_paths = [
            "/fs/recursive_move",
            "/api/v1/users/login",
            "/users/reset-password",
            "/api/v1/audit-logs/export",
        ]
        for p in clean_paths:
            self.assertTrue(
                self.dispatcher._is_valid_api_path(p),
                f"合法业务接口 {p} 必须通过清洗门禁",
            )


if __name__ == "__main__":
    unittest.main()
