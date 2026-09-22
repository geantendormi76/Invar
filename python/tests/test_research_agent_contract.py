import unittest
from agent.loop_types import ResearchEvent, ResearchEventType
from agent.research_agent import AgentState, ResearchAgent
from harness.denial_models import DenialObservation
from harness.models import EndpointIR


class ResearchAgentContractTests(unittest.TestCase):
    """
    针对有状态 ResearchAgent 状态机、事件流总线与队列订阅的契约测试
    """

    def setUp(self):
        self.endpoint = EndpointIR(method="GET", path="/api/v1/admin/secrets", tags=["admin"])
        self.target_url = "https://target.corp.local/api/v1/admin/secrets"
        self.baseline_obs = DenialObservation(
            status_code=403,
            response_headers={"server": "nginx"},
            body_preview="Access Denied",
        )

    def test_agent_lifecycle_and_event_subscription(self):
        """【契约 1】生命周期状态机推进与事件流订阅派发 (对齐 pi-agent-core subscribe 机制)"""
        class MockBypassTransport:
            def request(self, method, url, payload, headers, timeout):
                class Resp:
                    pass
                r = Resp()
                if headers.get("X-Rewrite-URL"):
                    r.status_code = 200
                    r.text = '{"vault": "live_data_001"}'
                    r.headers = {"Content-Type": "application/json"}
                else:
                    r.status_code = 403
                    r.text = "Forbidden"
                    r.headers = {}
                return r

        agent = ResearchAgent(transport=MockBypassTransport())
        self.assertEqual(agent.state, AgentState.IDLE)

        event_log = []
        unsubscribe = agent.subscribe(lambda evt: event_log.append(evt.event_type))

        res = agent.investigate_denial(
            endpoint=self.endpoint,
            url=self.target_url,
            baseline_observation=self.baseline_obs,
        )

        self.assertEqual(agent.state, AgentState.COMPLETED)
        self.assertTrue(res.breakthrough_achieved)
        self.assertIn(ResearchEventType.LOOP_START, event_log)
        self.assertIn(ResearchEventType.LOOP_END, event_log)

        # 验证退订机制生效
        unsubscribe()
        agent.reset()
        self.assertEqual(agent.state, AgentState.IDLE)

    def test_agent_steer_injects_instruction_dynamically(self):
        """【契约 2】暴露的 steer() 接口将干预指令成功注入队列"""
        agent = ResearchAgent()
        agent.steer("Notice: Target is Nginx, prioritize path mutations", source="AdminCritic")
        self.assertEqual(len(agent.config.steering_queue), 1)
        self.assertEqual(agent.config.steering_queue[0].source, "AdminCritic")
        self.assertIn("Nginx", agent.config.steering_queue[0].content)

    def test_agent_abort_halts_execution(self):
        """【契约 3】暴露的 abort() 接口能够令运行中的智能体立即中止"""
        agent = ResearchAgent()
        agent.abort("Manual operator stop")
        self.assertEqual(agent.state, AgentState.ABORTED)


if __name__ == "__main__":
    unittest.main()
