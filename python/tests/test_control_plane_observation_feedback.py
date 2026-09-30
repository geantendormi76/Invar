import unittest

from agent.research_agent import ResearchAgent
from agent.research_controller import (
    ControlPlaneConfig,
    ControlPlaneDecision,
    ResearchAction,
    ResearchController,
    ResearchControlState,
)
from agent.research_loop import (
    ResearchLoopConfig,
    ResearchLoopContext,
    run_research_loop,
)
from harness.adaptive_selector import PrioritizedExperiment
from harness.denial_models import (
    DenialCategory,
    DenialClassificationResult,
    DenialHypothesis,
    DenialLayer,
    DenialObservation,
    EvidenceGrade,
    FrontendComponent,
)
from harness.models import EndpointIR
from harness.transformation_models import TransformationFamily, TransformationVariant


class _FakeTransport:
    """固定返回 403 / permission denied 的 fake transport，不访问真实网络。"""

    def request(self, method, url, payload, headers, timeout):
        class Resp:
            pass

        r = Resp()
        r.status_code = 403
        r.text = "permission denied"
        r.headers = {"Content-Type": "text/plain"}
        return r


class RecordingFakeController(ResearchController):
    """
    记录每一轮收到的 ResearchControlState，并据此做决策：
    优先选择“尚未尝试过”的候选 -> 天然体现“基于上一轮结果改变下一次决策”。
    """

    def __init__(self):
        super().__init__()
        self.seen_states: list[ResearchControlState] = []
        self.seen_candidate_ids: list[list[str]] = []

    def decide(self, candidates, state, llm_provider=None, emit=None):
        # 决策时刻的快照 (state 是 loop 内复用的同一可变对象，需拷贝值)
        self.seen_states.append(ResearchControlState(
            current_status=state.current_status,
            tried_variants=set(state.tried_variants),
            last_observation_summary=state.last_observation_summary,
        ))
        self.seen_candidate_ids.append([c.variant_id for c in candidates])
        untried = [c for c in candidates if c.variant_id not in state.tried_variants]
        if untried:
            return ControlPlaneDecision(
                action=ResearchAction.RUN_EXPERIMENT,
                target_id=untried[0].variant_id,
                reason="feedback-driven: pick untried candidate",
                confidence=1.0,
            )
        if candidates:
            return ControlPlaneDecision(
                action=ResearchAction.RUN_EXPERIMENT,
                target_id=candidates[0].variant_id,
                reason="fallback",
                confidence=0.0,
            )
        return ControlPlaneDecision(
            action=ResearchAction.STOP, target_id=None, reason="no untried", confidence=0.0
        )


def _variant(vid):
    return TransformationVariant(
        variant_id=vid,
        family=TransformationFamily.F1_PATH_NORMALIZATION,
        method="GET",
        url="https://target.corp.local/api/v1/admin/secrets",
        headers={},
        payload={},
        rationale=vid,
        expected_effect="bypass",
    )


def _exp(vid):
    return PrioritizedExperiment(
        variant=_variant(vid),
        priority_score=9.0 if vid == "FA" else 8.0,
        selection_rationale=vid,
        expected_information_gain=1.0,
    )


class ObservationAwareProvider:
    """
    Fake LLM provider：其返回的 JSON 依赖传入 prompt 中是否包含上一轮 Observation。
    用于证明真实 ResearchController 把 Observation 写进了 prompt，
    且 provider 据此返回不同的 target_id（数据依赖，而非“两次调用”）。
    """

    def __init__(self):
        self.prompts: list[str] = []

    def generate_structured_json(self, prompt):
        blob = "\n".join(m.get("content", "") for m in prompt)
        self.prompts.append(blob)
        if "status=403" in blob and "permission denied" in blob:
            return {
                "action": "RUN_EXPERIMENT",
                "target_id": "FB",
                "reason": "respond to previous 403 observation",
                "confidence": 0.9,
            }
        return {
            "action": "RUN_EXPERIMENT",
            "target_id": "FA",
            "reason": "first pick",
            "confidence": 0.9,
        }


class _FakeSelector:
    """忽略 registry，直接返回预设的 prioritized experiments。"""

    def __init__(self, experiments):
        self._experiments = experiments

    def select(self, variants, classification, max_budget):
        return self._experiments


class ControlPlaneObservationFeedbackTests(unittest.TestCase):
    """
    闭环验收：第 2 轮 Controller 决策的输入必须真正包含第 1 轮 Experiment 的真实结果。
    """

    def test_control_plane_receives_previous_observation(self):
        endpoint = EndpointIR(method="GET", path="/api/v1/admin/secrets")
        target_url = "https://target.corp.local/api/v1/admin/secrets"
        baseline_obs = DenialObservation(
            status_code=403,
            response_headers={},
            body_preview="403 Forbidden",
        )
        classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-403",
                layer=DenialLayer.EDGE,
                category=DenialCategory.ACCESS_POLICY_DENIAL,
                confidence=0.9,
                evidence_grade=EvidenceGrade.GRADE_A,
            ),
            frontend_component=FrontendComponent.WAF,
        )
        context = ResearchLoopContext(
            endpoint=endpoint,
            target_url=target_url,
            baseline_observation=baseline_obs,
            denial_classification=classification,
        )

        controller = RecordingFakeController()
        config = ResearchLoopConfig(
            max_turns=2,
            max_budget=2,
            control_plane_enabled=True,
            controller=controller,
            selector=_FakeSelector([_exp("FA"), _exp("FB")]),
        )

        run_research_loop(
            context=context,
            config=config,
            transport=_FakeTransport(),
        )

        # 至少进行了两轮 controller 决策
        self.assertGreaterEqual(len(controller.seen_states), 2)

        # 第 1 轮决策时，尚未产生任何 Observation，摘要为空。
        self.assertEqual(controller.seen_states[0].last_observation_summary, "")

        # 第 1 轮选中 FA，第 2 轮选中 FB（因为 FA 已尝试）—— 证明决策因上一轮结果而改变。
        first_decision = controller.seen_states[0]
        self.assertNotIn("FA", first_decision.tried_variants)

        # 核心断言：第 2 轮 Controller 收到的摘要必须包含第 1 轮的真实 Observation。
        second_state = controller.seen_states[1]
        summary = second_state.last_observation_summary
        self.assertIn("403", summary)
        self.assertIn("permission denied", summary)

        # 第 2 轮候选集合中 FA 已被标记为已尝试。
        self.assertIn("FA", second_state.tried_variants)


class RealControllerObservationFeedbackTests(unittest.TestCase):
    """
    核心证明：真实 ResearchController.decide() + _build_prompt() + ControlPlaneDecision.validate()
    完整路径下，第二轮决策真正读取了第一轮真实 Observation，并据此改选候选。
    不使用 RecordingFakeController。
    """

    def test_real_controller_uses_previous_observation(self):
        endpoint = EndpointIR(method="GET", path="/api/v1/admin/secrets")
        target_url = "https://target.corp.local/api/v1/admin/secrets"
        baseline_obs = DenialObservation(
            status_code=403,
            response_headers={},
            body_preview="403 Forbidden",
        )
        classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-403",
                layer=DenialLayer.EDGE,
                category=DenialCategory.ACCESS_POLICY_DENIAL,
                confidence=0.9,
                evidence_grade=EvidenceGrade.GRADE_A,
            ),
            frontend_component=FrontendComponent.WAF,
        )
        context = ResearchLoopContext(
            endpoint=endpoint,
            target_url=target_url,
            baseline_observation=baseline_obs,
            denial_classification=classification,
        )

        provider = ObservationAwareProvider()
        config = ResearchLoopConfig(
            max_turns=2,
            max_budget=2,
            control_plane_enabled=True,
            llm_provider=provider,
            selector=_FakeSelector([_exp("FA"), _exp("FB")]),
        )

        dispatched_urls = []

        class RecordingTransport:
            def request(self, method, url, payload, headers, timeout):
                dispatched_urls.append(url)
                class Resp:
                    pass

                r = Resp()
                r.status_code = 403
                r.text = "permission denied"
                r.headers = {"Content-Type": "text/plain"}
                return r

        run_research_loop(
            context=context,
            config=config,
            transport=RecordingTransport(),
        )

        # 真实 Controller 被调用了两次（两轮各一次）。
        self.assertEqual(len(provider.prompts), 2)

        # 第 1 轮 prompt 不含第一轮 Observation。
        self.assertNotIn("permission denied", provider.prompts[0])

        # 第 2 轮 prompt 必须真正包含第一轮真实 Observation。
        self.assertIn("status=403", provider.prompts[1])
        self.assertIn("permission denied", provider.prompts[1])

        # 真实 Controller 最终选择：第一轮 FA，第二轮 FB（因 Observation 而改变）。
        self.assertEqual(dispatched_urls[0], _variant("FA").url)
        self.assertEqual(dispatched_urls[1], _variant("FB").url)


class ResearchAgentControlPlaneWiringTests(unittest.TestCase):
    """验证 ResearchAgent 的显式 Control Plane 启用入口正确写入 ResearchLoopConfig。"""

    def test_default_agent_keeps_control_plane_disabled(self):
        agent = ResearchAgent()
        self.assertFalse(agent.config.control_plane_enabled)
        self.assertIsNone(agent.config.controller)
        self.assertIsNone(agent.config.control_plane_config)

    def test_explicit_control_plane_entry_wires_config(self):
        controller = ResearchController()
        cp_config = ControlPlaneConfig(max_reason_length=123, max_llm_attempts=2)
        agent = ResearchAgent(
            control_plane_enabled=True,
            controller=controller,
            control_plane_config=cp_config,
        )
        self.assertTrue(agent.config.control_plane_enabled)
        self.assertIs(agent.config.controller, controller)
        self.assertIs(agent.config.control_plane_config, cp_config)

    def test_explicit_false_keeps_config_untouched_when_no_config_given(self):
        # 显式传 False 时，config 被置为 False（与默认一致），行为不变。
        agent = ResearchAgent(control_plane_enabled=False)
        self.assertFalse(agent.config.control_plane_enabled)


if __name__ == "__main__":
    unittest.main()
