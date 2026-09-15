import unittest
from unittest.mock import patch
from harness.config import InvarConfig
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor

class SandboxIdorIntegrationTests(unittest.TestCase):
    def test_executor_triggers_dual_token_idor_detection_when_idor_hypothesis_present(self) -> None:
        # 1. 构造带有 ID 参数的越权敏感端点 (触发 H-IDOR 假说)
        endpoint = EndpointIR(
            method="GET",
            path="/api/orders/detail",
            extracted_params=["order_id"],
            tags=["sensitive-params"],
        )

        # 2. 配置具备双主体凭证 (Victim Token A 与 Attacker Token B) 的沙箱环境
        config = InvarConfig(
            target_api_base="http://fixture.invalid/api/v1",
            auth_token="token_victim_a",
            auth_token_b="token_attacker_b",
            request_timeout=1,
            max_mutation_rounds=1,
        )

        executor = AdaptiveSandboxExecutor(cfg=config)

        # 3. 模拟底层 Transport:
        #    第一次发包 (主体 A 基线): 返回真实受害者订单数据
        #    第二次发包 (主体 B 越权): 后端鉴权缺失，同样返回了受害者订单数据 (200 OK 且高度相似)
        victim_resp_text = '{"order_id": 999, "owner": "alice", "amount": 10000}'
        attacker_resp_text = '{"order_id": 999, "owner": "alice", "amount": 10000}'

        call_records = []

        class FakeTransport:
            def request(self, method, url, payload, headers, timeout):
                call_records.append({"headers": dict(headers), "url": url})
                class Resp:
                    pass
                r = Resp()
                r.status_code = 200
                # 依据当前携带的 Authorization 头返回对应报文
                auth = headers.get("Authorization", "")
                if "token_victim_a" in auth:
                    r.text = victim_resp_text
                else:
                    r.text = attacker_resp_text
                r.headers = {"Content-Type": "application/json"}
                return r

        with patch.object(executor, "transport", FakeTransport()):
            result = executor.probe_endpoint_with_research(endpoint)

        case = result.research_case
        evidence = result.evidence

        # 4. 契约断言:
        # 4.1 发包次数应为 2 次 (主体 A 基线探针 + 主体 B 越权探针)
        self.assertEqual(len(call_records), 2)
        self.assertIn("token_victim_a", call_records[0]["headers"].get("Authorization", ""))
        self.assertIn("token_attacker_b", call_records[1]["headers"].get("Authorization", ""))

        # 4.2 假设流转: H-IDOR-1 应被正式证实 (VERIFIED)
        idor_hypotheses = [h for h in case.hypotheses if h.hypothesis_id.startswith("H-IDOR")]
        self.assertTrue(len(idor_hypotheses) >= 1)
        self.assertEqual(idor_hypotheses[0].status, "VERIFIED")

        # 4.3 决断判定: 综合决策判定为 vulnerable
        self.assertIsNotNone(case.decision)
        self.assertEqual(case.decision.status, "vulnerable")
        self.assertIn("水平越权", case.decision.rationale)

        # 4.4 证据留痕: 证据被升级为漏洞证据
        self.assertTrue(evidence.is_anomaly)
        self.assertEqual(evidence.finding_type, "VULNERABILITY_FOUND")

if __name__ == "__main__":
    unittest.main()
