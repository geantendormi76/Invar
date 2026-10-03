import unittest
from unittest.mock import Mock

from agent.loop_types import (
    AbortSignal,
    QueueMode,
    ResearchEvent,
    ResearchEventType,
    SteeringMessage,
)
from agent.research_loop import (
    ResearchLoopConfig,
    ResearchLoopContext,
    ResearchLoopResult,
    run_research_loop,
)
from harness.denial_models import (
    DenialCategory,
    DenialClassificationResult,
    DenialHypothesis,
    DenialLayer,
    DenialObservation,
    EvidenceGrade,
    FrontendComponent,
)
from harness.evidence_models import EvidenceVerdict
from harness.models import EndpointIR


class ResearchLoopContractTests(unittest.TestCase):
    """
    对齐 pi-agent-core 纯函数算法、推模式事件流与双队列机制的核心测试
    """

    def setUp(self):
        self.endpoint = EndpointIR(method="GET", path="/api/v1/admin/secrets", tags=["admin"])
        self.target_url = "https://target.corp.local/api/v1/admin/secrets"
        self.baseline_obs = DenialObservation(
            status_code=403,
            response_headers={"server": "nginx"},
            body_preview="403 Forbidden",
        )
        self.classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-403",
                layer=DenialLayer.EDGE,
                category=DenialCategory.ACCESS_POLICY_DENIAL,
                confidence=0.9,
                evidence_grade=EvidenceGrade.GRADE_A,
            ),
            frontend_component=FrontendComponent.WAF,
        )

    def test_pure_loop_dispatches_events_and_achieves_breakthrough(self):
        """【契约 1】推模式事件流与突破全过程：事件严格按顺序抛出，实证突破并装配证据链"""
        context = ResearchLoopContext(
            endpoint=self.endpoint,
            target_url=self.target_url,
            baseline_observation=self.baseline_obs,
            denial_classification=self.classification,
        )
        config = ResearchLoopConfig(max_turns=6, max_budget=6)

        event_log = []
        def mock_sink(evt: ResearchEvent):
            event_log.append(evt.event_type)

        class MockBypassTransport:
            def request(self, method, url, payload, headers, timeout):
                class Resp:
                    pass
                r = Resp()
                # 模拟当命中 X-Rewrite-URL 时返回内部机密
                if headers.get("X-Rewrite-URL"):
                    r.status_code = 200
                    r.text = '{"secrets": ["KEY_001", "KEY_002"]}'
                    r.headers = {"Content-Type": "application/json"}
                else:
                    r.status_code = 403
                    r.text = "403 Forbidden"
                    r.headers = {}
                return r

        result = run_research_loop(
            context=context,
            config=config,
            transport=MockBypassTransport(),
            emit=mock_sink,
        )

        # 1. 验证突破达成与证据链装配
        self.assertTrue(result.breakthrough_achieved)
        self.assertEqual(result.final_verdict, EvidenceVerdict.CANDIDATE)
        self.assertIsNotNone(result.evidence_chain)
        self.assertEqual(result.evidence_chain.applied_variant.headers.get("X-Rewrite-URL"), "/api/v1/admin/secrets")

        # 2. 验证推模式事件流序列完整性 (对齐 pi-agent-core 规范)
        self.assertIn(ResearchEventType.LOOP_START, event_log)
        self.assertIn(ResearchEventType.DENIAL_CLASSIFIED, event_log)
        self.assertIn(ResearchEventType.TURN_START, event_log)
        self.assertIn(ResearchEventType.PROBE_DISPATCHED, event_log)
        self.assertIn(ResearchEventType.PROBE_RESPONDED, event_log)
        self.assertIn(ResearchEventType.REPLAY_COMPLETED, event_log)
        self.assertIn(ResearchEventType.LOOP_END, event_log)

    def test_steering_queue_injects_critic_instruction_before_turn(self):
        """【契约 2】Steering 动态插队：在 Turn 开始前优先消费 Critic 干预指令并记录内轨消息"""
        context = ResearchLoopContext(
            endpoint=self.endpoint,
            target_url=self.target_url,
            baseline_observation=self.baseline_obs,
            denial_classification=self.classification,
        )
        steering_msg = SteeringMessage(
            content="Critic Notice: Target backend is Spring, skip dot-segment mutations.",
            source="CoverageCritic",
        )
        config = ResearchLoopConfig(
            max_turns=2,
            steering_queue=[steering_msg],
        )

        event_log = []
        def mock_sink(evt: ResearchEvent):
            event_log.append(evt)

        class AlwaysBlockTransport:
            def request(self, method, url, payload, headers, timeout):
                class Resp:
                    pass
                r = Resp()
                r.status_code = 403
                r.text = "Forbidden"
                r.headers = {}
                return r

        result = run_research_loop(
            context=context,
            config=config,
            transport=AlwaysBlockTransport(),
            emit=mock_sink,
        )

        # 验证 Steering 队列被成功轮询并抛出强类型事件
        steering_events = [e for e in event_log if e.event_type == ResearchEventType.STEERING_INJECTED]
        self.assertEqual(len(steering_events), 1)
        self.assertIn("Spring", steering_events[0].payload["instruction"])

        # 验证内轨消息历史中留痕
        steer_msgs = [m for m in result.context.messages if m.role.value == "critic_steer"]
        self.assertEqual(len(steer_msgs), 1)
        self.assertIn("Spring", steer_msgs[0].content)

    def test_abort_signal_halts_loop_immediately(self):
        """【契约 3】取消信号熔断：收到 AbortSignal 时立即中止循环，抛出 ABORTED 事件"""
        context = ResearchLoopContext(
            endpoint=self.endpoint,
            target_url=self.target_url,
            baseline_observation=self.baseline_obs,
            denial_classification=self.classification,
        )
        signal = AbortSignal()
        signal.abort("Manual operator stop")
        config = ResearchLoopConfig(max_turns=10)

        event_log = []
        def mock_sink(evt: ResearchEvent):
            event_log.append(evt.event_type)

        result = run_research_loop(
            context=context,
            config=config,
            transport=None,  # 瞬间熔断，无需执行发包
            emit=mock_sink,
            signal=signal,
        )

        self.assertTrue(result.aborted)
        self.assertEqual(result.abort_reason, "Manual operator stop")
        self.assertEqual(result.turns_executed, 0)
        self.assertIn(ResearchEventType.ABORTED, event_log)
        self.assertIn(ResearchEventType.LOOP_END, event_log)

    def test_fake_200_homepage_is_skipped_and_loop_continues(self):
        """【契约 4】防误报闭环：首页回退被拒后，循环自动不中断，继续测试后续真实变体"""
        context = ResearchLoopContext(
            endpoint=self.endpoint,
            target_url=self.target_url,
            baseline_observation=self.baseline_obs,
            denial_classification=self.classification,
        )
        homepage_html = "<html><title>Public Portal</title><body>Public Content</body></html>"
        config = ResearchLoopConfig(
            max_turns=3,
            public_root_preview=homepage_html,
        )

        class FakeHomepageTransport:
            def request(self, method, url, payload, headers, timeout):
                class Resp:
                    pass
                r = Resp()
                # 模拟变异体返回公共首页
                r.status_code = 200
                r.text = homepage_html
                r.headers = {"Content-Type": "text/html"}
                return r

        result = run_research_loop(
            context=context,
            config=config,
            transport=FakeHomepageTransport(),
        )

        # 核心断言：虽然返回了 200，但被语义等价全部打回，未能达成突破
        self.assertFalse(result.breakthrough_achieved)
        self.assertEqual(result.final_verdict, EvidenceVerdict.REJECTED)
        self.assertIsNone(result.evidence_chain)

    def test_actionable_steer_triggers_turn2_verb_substitution_and_poc(self):
        """【契约 5 (路线 B 核心)】首轮 405 动词拒绝后，大模型反思推断建议改用 GET 动词，
        研究循环必须自主调度第 2 轮物理变异发包 (GET)，实证突破并导出可复现 PoC 代码。"""
        # 1. 模拟遭受 405 Method Not Allowed 的 POST 密码重置接口
        post_endpoint = EndpointIR(method="POST", path="/users/${H}/reset-password", tags=["sensitive-route"])
        target_url = "https://target.corp.local/users/admin_user/reset-password"
        obs_405 = DenialObservation(
            status_code=405,
            response_headers={"Allow": "GET, HEAD, OPTIONS"},
            body_preview='{"code": 405, "message": "Method Not Allowed"}',
        )
        classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-405",
                layer=DenialLayer.APPLICATION,
                category=DenialCategory.METHOD_POLICY_DENIAL,
                confidence=0.95,
                evidence_grade=EvidenceGrade.GRADE_A,
            ),
            frontend_component=FrontendComponent.UNKNOWN,
        )
        context = ResearchLoopContext(
            endpoint=post_endpoint,
            target_url=target_url,
            baseline_observation=obs_405,
            denial_classification=classification,
        )

        # 2. 模拟大模型 CoT 认知反思：给出动词改换建议 (method="GET")
        mock_llm = Mock()
        mock_llm.model = "Ornith-35B-Mock"
        mock_llm.generate_structured_json.return_value = {
            "action": "RUN_EXPERIMENT",
            "method": "GET",  # 核心建议：将破坏性 POST 转换为只读 GET 探测
            "headers": {"Accept": "application/json"},
            "payload": {},
            "rationale": "Server returned 405 with Allow header indicating GET is supported. Testing method substitution.",
        }

        # 3. 记录多轮发包序列的测试 Transport
        dispatched_probes = []
        class MultiTurnTransport:
            def request(self, method, url, payload, headers, timeout):
                dispatched_probes.append({"method": method, "url": url, "headers": headers})
                class Resp:
                    pass
                r = Resp()
                # 凡是发送 POST 的一律按基线拦截 405
                if method.upper() == "POST":
                    r.status_code = 405
                    r.text = '{"code": 405, "message": "Method Not Allowed"}'
                    r.headers = {"Allow": "GET, HEAD, OPTIONS"}
                elif method.upper() == "GET":
                    # 大模型改换 GET 后成功放行 200 并泄露重置敏感上下文
                    r.status_code = 200
                    r.text = '{"status": "ok", "user": "admin_user", "reset_token": "TOK-998811"}'
                    r.headers = {"Content-Type": "application/json"}
                return r

        config = ResearchLoopConfig(
            max_turns=1,  # 启发式阶段只执行 1 轮
            max_budget=1,
            llm_provider=mock_llm,
        )

        result = run_research_loop(
            context=context,
            config=config,
            transport=MultiTurnTransport(),
        )

        # 核心断言 1：必须自主发起了大模型建议的第 2 轮 GET 物理发包追击
        dispatched_methods = [p["method"].upper() for p in dispatched_probes]
        self.assertIn("GET", dispatched_methods, "研究循环未能执行大模型给出的 GET 动词变换建议！")

        # 核心断言 2：实证突破达成并确权为 CANDIDATE
        self.assertTrue(result.breakthrough_achieved, "切换 GET 后服务端已放行 200，但循环未记录突破！")
        self.assertEqual(result.final_verdict, EvidenceVerdict.CANDIDATE)

        # 核心断言 3：变异体与证据链记录的生效动词必须是 GET，而非被锁死的 POST
        applied_variant = result.evidence_chain.applied_variant
        self.assertEqual(applied_variant.method.upper(), "GET", "生效变异体的 HTTP 动词依然被硬编码为 POST！")

        # 核心断言 4：自动导出可独立复现的 PoC 实体 (curl / python 代码)
        self.assertIsNotNone(result.evidence_chain.poc_code, "突破达成后必须自动组装可执行的 PoC 代码！")
        self.assertIn("curl", result.evidence_chain.poc_code.lower())
        self.assertIn("-X GET", result.evidence_chain.poc_code)


if __name__ == "__main__":
    unittest.main()
