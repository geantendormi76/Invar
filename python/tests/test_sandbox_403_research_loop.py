import unittest
from unittest.mock import patch
from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class Sandbox403ResearchLoopIntegrationTests(unittest.TestCase):
    """
    Invar 403 自适应研究闭环端到端集成测试
    """

    def setUp(self):
        # target_api_base 设为站点根域名，与 endpoint.path ("/api/v1/...") 保持正交规范
        self.config = InvarConfig(
            target_api_base="https://target.corp.local",
            request_timeout=1,
            max_mutation_rounds=1,
        )
        self.executor = AdaptiveSandboxExecutor(cfg=self.config)

    def test_403_bypass_with_x_rewrite_url_penetration(self):
        """
        【实战闭环 1】真正的 403 突破实证：
        基线常规请求被 WAF 拦截 (403)，通过 X-Rewrite-URL 成功穿透，
        获得内部真实机密数据 (200)，同态重放一致，实锤确认漏洞！
        """
        endpoint = EndpointIR(
            method="GET",
            path="/api/v1/admin/secrets",
            tags=["sensitive-route", "admin"],
        )

        call_log = []

        class RealBypassTransport:
            def request(self, method, url, payload, headers, timeout):
                call_log.append({"url": url, "headers": dict(headers)})
                class Resp:
                    pass
                r = Resp()
                # 检查是否携带了目标重写头
                rewrite_val = headers.get("X-Rewrite-URL", "")
                if rewrite_val and "admin/secrets" in rewrite_val:
                    r.status_code = 200
                    r.text = '{"admin_tokens": ["SEC-9988", "SEC-7766"], "vault_status": "unlocked"}'
                    r.headers = {"Content-Type": "application/json"}
                else:
                    r.status_code = 403
                    r.text = "403 Forbidden: WAF blocked admin route"
                    r.headers = {"Content-Type": "text/html"}
                return r

        with patch.object(self.executor, "transport", RealBypassTransport()):
            result = self.executor.probe_endpoint_with_research(endpoint)

        case = result.research_case
        evidence = result.evidence

        # 1. 断言至少经历了基线(403)与变异突破(200)两次记录
        self.assertTrue(len(case.attempts) >= 2)
        # 2. 断言元数据记录了分类与完备证据链
        self.assertIn("denial_classification", case.metadata)
        self.assertIn("evidence_chain", case.metadata)
        # 3. 断言安全底线被击穿：sensitive-route 无凭证放行 -> vulnerable
        self.assertIsNotNone(case.decision)
        self.assertEqual(case.decision.status, "vulnerable")
        self.assertTrue(evidence.is_anomaly)
        self.assertEqual(evidence.finding_type, "VULNERABILITY_FOUND")
        self.assertIn("403拒绝突破成功", case.attempts[-1].interpretation)

    def test_403_fake_200_homepage_fallback_is_eliminated(self):
        """
        【实战闭环 2】防误报铁壁：
        虽然携带 X-Rewrite-URL 返回了 200，但响应内容是公开首页 (index.html)。
        语义等价门禁彻底识破，坚决拒绝记录为突破，守住零误报底线！
        """
        endpoint = EndpointIR(
            method="GET",
            path="/api/v1/admin/secrets",
            tags=["sensitive-route"],
        )

        homepage_html = "<html><title>Example Cloud Public Home</title><body>Banner</body></html>"

        class FakeHomepageTransport:
            def request(self, method, url, payload, headers, timeout):
                class Resp:
                    pass
                r = Resp()
                # 无论是请求根路由还是伪造头，后端一律返回公共首页 200
                if "X-Rewrite-URL" in headers or url.rstrip("/") == "https://target.corp.local":
                    r.status_code = 200
                    r.text = homepage_html
                    r.headers = {"Content-Type": "text/html"}
                else:
                    r.status_code = 403
                    r.text = "403 Forbidden"
                    r.headers = {"Content-Type": "text/html"}
                return r

        with patch.object(self.executor, "transport", FakeHomepageTransport()):
            result = self.executor.probe_endpoint_with_research(endpoint)

        case = result.research_case

        # 核心断言：首页回退被坚决剔除，决断绝对不能被误判为 vulnerable！
        self.assertNotEqual(case.decision.status, "vulnerable")
        # 证据不应标记为发现漏洞
        self.assertFalse(result.evidence.is_anomaly)

    def test_403_login_redirect_is_rejected_as_bypass(self):
        """
        【实战闭环 3】重定向登录防误报：
        变异发包被 302 重定向至 SSO 登录页，语义等价判定为 DIFFERENT_RESOURCE，不误报。
        """
        endpoint = EndpointIR(
            method="GET",
            path="/api/v1/internal/config",
            tags=["sensitive-route"],
        )

        class LoginRedirectTransport:
            def request(self, method, url, payload, headers, timeout):
                class Resp:
                    pass
                r = Resp()
                if "X-Rewrite-URL" in headers:
                    r.status_code = 302
                    r.text = "Redirecting to login"
                    r.headers = {"Location": "https://target.corp.local/sso/login"}
                else:
                    r.status_code = 403
                    r.text = "403 Forbidden"
                    r.headers = {}
                return r

        with patch.object(self.executor, "transport", LoginRedirectTransport()):
            result = self.executor.probe_endpoint_with_research(endpoint)

        case = result.research_case
        self.assertNotEqual(case.decision.status, "vulnerable")
        self.assertFalse(result.evidence.is_anomaly)


if __name__ == "__main__":
    unittest.main()
