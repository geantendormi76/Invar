import unittest
from unittest.mock import patch
from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor

class SandboxTamperIntegrationTests(unittest.TestCase):
    def test_executor_triggers_method_tamper_bypass_when_destructive_action_blocked_by_403(self) -> None:
        # 1. 构造一个高危破坏性端点 (DELETE 动作)
        endpoint = EndpointIR(
            method="DELETE",
            path="/api/orders/batch",
            extracted_params=["order_ids"],
            tags=["destructive", "state-changing"],
        )

        config = InvarConfig(
            target_api_base="http://fixture.invalid/api/v1",
            request_timeout=1,
            max_mutation_rounds=1,
        )

        executor = AdaptiveSandboxExecutor(cfg=config)

        # 2. 模拟底层 Transport 行为:
        #    第一次发包 (常规 DELETE): 被反向代理/WAF 拦截，返回 403 Forbidden
        #    后续发包 (动词隧道变体): 携带 X-HTTP-Method-Override 头，穿透 WAF，后端直接执行并返回 200 OK!
        call_records = []

        class FakeTamperTransport:
            def request(self, method, url, payload, headers, timeout):
                call_records.append({
                    "method": method,
                    "headers": dict(headers),
                    "url": url,
                    "payload": payload,
                })
                class Resp:
                    pass
                r = Resp()
                # 若使用了 X-HTTP-Method-Override 隧道技术，模拟后端放行返回 200
                if headers.get("X-HTTP-Method-Override") == "DELETE":
                    r.status_code = 200
                    r.text = '{"deleted": true, "count": 10}'
                    r.headers = {"Content-Type": "application/json"}
                else:
                    r.status_code = 403
                    r.text = "403 Forbidden: WAF blocked dangerous HTTP verb DELETE"
                    r.headers = {"Content-Type": "text/html"}
                return r

        with patch.object(executor, "transport", FakeTamperTransport()):
            result = executor.probe_endpoint_with_research(endpoint)

        case = result.research_case
        evidence = result.evidence

        # 3. 契约断言:
        # 3.1 必须发生穿透重试發包，且包含 X-HTTP-Method-Override 变体
        tunnel_calls = [
            c for c in call_records
            if c["headers"].get("X-HTTP-Method-Override") == "DELETE"
        ]
        self.assertTrue(len(tunnel_calls) >= 1, "沙箱在遭遇 403 拦截时未触发 HTTP 动词隧道穿透重试")

        # 3.2 假设流转: 破坏性假设 H-DESTRUCT-1 应被成功证实 (VERIFIED)
        destruct_hypotheses = [h for h in case.hypotheses if h.hypothesis_id.startswith("H-DESTRUCT")]
        self.assertTrue(len(destruct_hypotheses) >= 1)
        self.assertEqual(destruct_hypotheses[0].status, "VERIFIED")

        # 3.3 决断判定: 综合决断被定性为 vulnerable (底线被穿透击穿)
        self.assertIsNotNone(case.decision)
        self.assertEqual(case.decision.status, "vulnerable")

        # 3.4 证据留痕: 标记为真实有效漏洞
        self.assertTrue(evidence.is_anomaly)
        self.assertEqual(evidence.finding_type, "VULNERABILITY_FOUND")

if __name__ == "__main__":
    unittest.main()
