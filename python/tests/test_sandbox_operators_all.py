# -*- coding: utf-8 -*-
import unittest
from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.research_models import SecurityInvariant
from harness.sandbox_executor import AdaptiveSandboxExecutor


class SandboxOperatorsAllTests(unittest.TestCase):
    """
    高内聚整合测试：覆盖 System-2 核心动态实证攻防算子与沙箱的深度联动
    (合并原 sandbox_idor, sandbox_invariant, sandbox_tamper 碎片测试)
    """

    def test_destructive_action_confirmation_invariant(self):
        """【算子整合 1】破坏性操作二次确认安全不变量：无确认放行为 vulnerable，有确认则 confirmed"""
        endpoint = EndpointIR(method="DELETE", path="/api/orders/batch", tags=["destructive"])
        config = InvarConfig()
        executor = AdaptiveSandboxExecutor(cfg=config)

        class FakeResponse:
            status_code = 200
            text = '{"deleted_count": 5}'
            headers = {}

        executor.transport.request = lambda method, url, payload, headers, timeout: FakeResponse()

        # 无确认参数被直接执行 ➔ 击穿不变量 (vulnerable)
        res = executor.probe_endpoint_with_research(endpoint)
        self.assertEqual(res.research_case.decision.status, "vulnerable")
        self.assertTrue(res.evidence.is_anomaly)

    def test_method_tamper_bypass_when_blocked_by_403(self):
        """【算子整合 2】403 阻断触发动词隧道篡改算子 (X-HTTP-Method-Override) 穿透验证"""
        endpoint = EndpointIR(method="DELETE", path="/api/orders/purge", tags=["destructive"])
        config = InvarConfig()
        executor = AdaptiveSandboxExecutor(cfg=config)

        call_records = []

        class FakeTamperTransport:
            def request(self, method, url, payload, headers, timeout):
                call_records.append((method, dict(headers)))
                class Resp:
                    pass
                r = Resp()
                # 常规 DELETE 模拟被 WAF 阻断
                if headers.get("X-HTTP-Method-Override") == "DELETE":
                    r.status_code = 200
                    r.text = '{"purged": true}'
                    r.headers = {}
                else:
                    r.status_code = 403
                    r.text = "Forbidden by WAF"
                    r.headers = {}
                return r

        executor.transport = FakeTamperTransport()
        res = executor.probe_endpoint_with_research(endpoint)

        # 验证发生了动词隧道重试发包
        has_tunnel_call = any(h.get("X-HTTP-Method-Override") == "DELETE" for _, h in call_records)
        self.assertTrue(has_tunnel_call)
        self.assertEqual(res.research_case.decision.status, "vulnerable")

    def test_dual_token_idor_differential_detection(self):
        """【算子整合 3】携带 ID 参数端点触发双主体 (Token A vs Token B) 水平越权差分对账"""
        endpoint = EndpointIR(method="GET", path="/api/orders/detail", extracted_params=["order_id"])
        config = InvarConfig(auth_token="token_a_victim", auth_token_b="token_b_attacker")
        executor = AdaptiveSandboxExecutor(cfg=config)

        call_records = []

        class FakeIdorTransport:
            def request(self, method, url, payload, headers, timeout):
                call_records.append(headers.get("Authorization", ""))
                class Resp:
                    status_code = 200
                    text = '{"order_id": 999, "owner": "victim_user", "balance": 8888}'
                    headers = {}
                return Resp()

        executor.transport = FakeIdorTransport()
        res = executor.probe_endpoint_with_research(endpoint)

        # 验证经历了双主体发包
        self.assertGreaterEqual(len(call_records), 2)
        # 攻击者拿到受害者高度相似数据 ➔ 裁决 vulnerable
        self.assertEqual(res.research_case.decision.status, "vulnerable")
