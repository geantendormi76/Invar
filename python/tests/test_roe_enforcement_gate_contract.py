# -*- coding: utf-8 -*-
"""
Phase 9.7-A Scope & Rules of Engagement (RoE) 前置安全门禁契约测试
对齐顶级 Bug Bounty / SRC 法定授权规范：
断言在任何沙箱网络物理发包前，必须经过强类型 RoE 门禁强制校验。
凡越界域名、排除黑名单路径或非授权动词，必须在物理接触网络前绝对阻断！
"""
import unittest

from harness.domain_contracts import (
    OutOfScopeError,
    ResearchScope,
    RoEBoundaryViolationError,
    RoEEnforcementGate,
)


class RoEEnforcementGateContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.scope = ResearchScope(
            target_domain="ikuai8.com",
            included_subdomains=["api.ikuai8.com", "cloud.ikuai8.com"],
            excluded_paths=["/api/v1/auth/logout", "/danger/*", "/admin/wipe_database"],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
            authorization_boundary="AUTHORIZED_SRC_ENGAGEMENT_V1",
        )

    def test_01_target_within_scope_passes_roe_gate(self) -> None:
        """【契约 1】完全合规的目标域名、路径与动词顺利通过前置门禁"""
        RoEEnforcementGate.assert_allowed(
            url="https://api.ikuai8.com/api/v1/user/profile",
            method="GET",
            scope=self.scope,
        )

    def test_02_unauthorized_host_strictly_blocked_before_physical_network(self) -> None:
        """【契约 2】越界未授权域名在物理发包前必须被一票否决，抛出 OutOfScopeError"""
        out_of_scope_url = "https://internal.evil.corp/api/secrets"
        with self.assertRaises(OutOfScopeError) as ctx:
            RoEEnforcementGate.assert_allowed(
                url=out_of_scope_url,
                method="GET",
                scope=self.scope,
            )
        self.assertIn("Host 'internal.evil.corp' is outside authorized engagement scope", str(ctx.exception))

    def test_03_excluded_path_strictly_blocked_before_physical_network(self) -> None:
        """【契约 3】法定排除路径（如注销、破坏性清库）必须被绝对拦截，抛出 RoEBoundaryViolationError"""
        # 1. 精确匹配排除路径
        with self.assertRaises(RoEBoundaryViolationError) as ctx1:
            RoEEnforcementGate.assert_allowed(
                url="https://api.ikuai8.com/api/v1/auth/logout",
                method="POST",
                scope=self.scope,
            )
        self.assertIn("violates excluded paths constraint", str(ctx1.exception))

        # 2. 通配符模式匹配排除路径 (/danger/*)
        with self.assertRaises(RoEBoundaryViolationError) as ctx2:
            RoEEnforcementGate.assert_allowed(
                url="https://api.ikuai8.com/danger/destroy_all",
                method="POST",
                scope=self.scope,
            )
        self.assertIn("violates excluded paths constraint", str(ctx2.exception))

    def test_04_disallowed_method_strictly_blocked(self) -> None:
        """【契约 4】非授权危险动词（如未经允许的 CONNECT / TRACE）必须被前置拦截"""
        with self.assertRaises(RoEBoundaryViolationError) as ctx:
            RoEEnforcementGate.assert_allowed(
                url="https://api.ikuai8.com/api/v1/user/profile",
                method="TRACE",
                scope=self.scope,
            )
        self.assertIn("HTTP Method 'TRACE' is disallowed by program rules", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
