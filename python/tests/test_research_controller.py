import unittest
from unittest.mock import Mock

from agent.loop_types import ResearchEvent, ResearchEventType
from agent.research_controller import (
    CandidateAction,
    ControlPlaneConfig,
    ControlPlaneDecision,
    ResearchAction,
    ResearchControlState,
    ResearchController,
)
from agent.research_loop import (
    ResearchLoopConfig,
    ResearchLoopContext,
    run_research_loop,
)
from harness.adaptive_selector import AdaptiveExperimentSelector, PrioritizedExperiment
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
from harness.transformation_models import (
    TransformationFamily,
    TransformationFamilyRegistry,
    TransformationVariant,
)


def _candidate(vid, family=TransformationFamily.F1_PATH_NORMALIZATION, method="GET", url="https://target/api/x"):
    return CandidateAction(
        variant_id=vid,
        family=family.value,
        method=method,
        url=url,
        expected_effect="bypass",
        rationale="deterministic",
    )


def _prioritized(exp):
    return exp


class ResearchControllerDecisionContractTests(unittest.TestCase):
    """
    针对 ResearchController 强类型 Decision Contract 的契约测试
    覆盖：合法 RUN_EXPERIMENT / STOP、未知 action、target_id 越界、
    confidence 越界、reason 超长、非法 JSON、fail closed。
    """

    def setUp(self):
        self.controller = ResearchController(max_reason_length=500)
        self.candidates = [
            _candidate("F1_A"),
            _candidate("F2_B"),
            _candidate("F3_C"),
        ]
        self.candidate_ids = {c.variant_id for c in self.candidates}
        self.state = ResearchControlState(tried_variants=set(), last_observation_summary="403")

    def test_valid_run_experiment_selects_existing_candidate(self):
        """【1】合法 RUN_EXPERIMENT 可以选择现有 candidate"""
        raw = {"action": "RUN_EXPERIMENT", "target_id": "F2_B", "reason": "try rewrite", "confidence": 0.8}
        decision = self.controller.decide(self.candidates, self.state, llm_provider=None)
        # deterministic provider path already returns a valid decision; exercise validate() directly:
        d = ControlPlaneDecision.validate(raw, self.candidate_ids, 500)
        self.assertEqual(d.action, ResearchAction.RUN_EXPERIMENT)
        self.assertEqual(d.target_id, "F2_B")
        self.assertAlmostEqual(d.confidence, 0.8)

    def test_valid_stop_is_allowed(self):
        """【2】STOP 合法"""
        d = ControlPlaneDecision.validate(
            {"action": "STOP", "target_id": None, "reason": "收敛", "confidence": 0.95},
            self.candidate_ids, 500,
        )
        self.assertEqual(d.action, ResearchAction.STOP)
        self.assertIsNone(d.target_id)

    def test_unknown_action_is_rejected(self):
        """【3】未知 action 被拒绝"""
        with self.assertRaises(ValueError):
            ControlPlaneDecision.validate(
                {"action": "HACK_IT", "target_id": "F1_A", "reason": "x", "confidence": 0.5},
                self.candidate_ids, 500,
            )

    def test_target_id_outside_candidate_set_is_rejected(self):
        """【4】target_id 不在候选集合时被拒绝"""
        with self.assertRaises(ValueError):
            ControlPlaneDecision.validate(
                {"action": "RUN_EXPERIMENT", "target_id": "F9_DOES_NOT_EXIST", "reason": "x", "confidence": 0.5},
                self.candidate_ids, 500,
            )

    def test_confidence_out_of_range_is_rejected(self):
        """【5】confidence 越界被拒绝"""
        for bad in (1.5, -0.1):
            with self.assertRaises(ValueError):
                ControlPlaneDecision.validate(
                    {"action": "STOP", "target_id": None, "reason": "x", "confidence": bad},
                    self.candidate_ids, 500,
                )
        # bool 是 int 子类，必须显式排除
        with self.assertRaises(ValueError):
            ControlPlaneDecision.validate(
                {"action": "STOP", "target_id": None, "reason": "x", "confidence": True},
                self.candidate_ids, 500,
            )

    def test_reason_too_long_is_rejected(self):
        """【6】reason 超长被拒绝"""
        with self.assertRaises(ValueError):
            ControlPlaneDecision.validate(
                {"action": "STOP", "target_id": None, "reason": "x" * 501, "confidence": 0.5},
                self.candidate_ids, 500,
            )

    def test_invalid_json_produces_no_executable_variant(self):
        """【7】非法 Decision 不会产生可执行 variant (fail closed -> 确定性回退)"""
        # 模拟模型返回非法 JSON
        mock_provider = Mock()
        mock_provider.generate_structured_json.return_value = {"action": "RUN_EXPERIMENT"}  # 缺少 target_id/confidence
        event_log = []

        def sink(evt: ResearchEvent):
            event_log.append(evt)

        decision = self.controller.decide(
            self.candidates, self.state, llm_provider=mock_provider, emit=sink
        )
        # fail closed：回退到最高优先级候选，而非执行模型提出的未知内容
        self.assertEqual(decision.action, ResearchAction.RUN_EXPERIMENT)
        self.assertEqual(decision.target_id, self.candidates[0].variant_id)
        self.assertIn(ResearchEventType.CONTROL_DECISION_REJECTED, [e.event_type for e in event_log])

    def test_llm_can_only_pick_existing_variant_not_create_one(self):
        """【8】LLM 只能选择现有 variant，不能自行制造 variant"""
        mock_provider = Mock()
        # 模型试图引用一个不存在的 variant
        mock_provider.generate_structured_json.return_value = {
            "action": "RUN_EXPERIMENT",
            "target_id": "F9_NEWLY_INVENTED",
            "reason": "make one up",
            "confidence": 0.7,
        }
        decision = self.controller.decide(
            self.candidates, self.state, llm_provider=mock_provider, emit=None
        )
        # fail closed：回退确定性候选，绝不执行自造 variant
        self.assertEqual(decision.target_id, self.candidates[0].variant_id)
        self.assertNotEqual(decision.target_id, "F9_NEWLY_INVENTED")

    def test_stop_when_no_candidates(self):
        """无候选时安全终止 (STOP)"""
        decision = self.controller.decide([], self.state, llm_provider=None)
        self.assertEqual(decision.action, ResearchAction.STOP)
        self.assertIsNone(decision.target_id)

    def test_single_action_per_call(self):
        """一次 LLM 调用只产生一个明确 action (list 被拒绝)"""
        with self.assertRaises(ValueError):
            ControlPlaneDecision.validate(
                {"action": ["RUN_EXPERIMENT", "STOP"], "reason": "x", "confidence": 0.5},
                self.candidate_ids, 500,
            )

    def test_events_record_contract_fields_without_secrets(self):
        """事件记录 action/target_id/reason/confidence/candidate_count，不含密钥"""
        mock_provider = Mock()
        mock_provider.generate_structured_json.return_value = {
            "action": "RUN_EXPERIMENT", "target_id": "F3_C",
            "reason": "chosen", "confidence": 0.6,
        }
        event_log = []
        self.controller.decide(
            self.candidates, self.state,
            llm_provider=mock_provider,
            emit=lambda evt: event_log.append(evt),
        )
        completed = [e for e in event_log if e.event_type == ResearchEventType.CONTROL_DECISION_COMPLETED][0]
        payload = completed.payload
        self.assertEqual(payload["action"], "RUN_EXPERIMENT")
        self.assertEqual(payload["target_id"], "F3_C")
        self.assertEqual(payload["candidate_count"], 3)
        self.assertIn("reason", payload)
        self.assertIn("confidence", payload)


class ResearchControllerPromptIsolationTests(unittest.TestCase):
    """Control Plane 绝不向 LLM 暴露 headers/payload 等密钥"""

    def test_prompt_excludes_secrets(self):
        controller = ResearchController()
        variant = TransformationVariant(
            variant_id="F3_REWRITE_X_REWRITE_URL",
            family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
            method="GET",
            url="https://target/api/x",
            headers={"Authorization": "Bearer SUPER_SECRET_TOKEN", "X-Rewrite-URL": "/secret"},
            payload={"token": "top_secret"},
            rationale="rewrite",
            expected_effect="bypass",
        )
        exp = PrioritizedExperiment(
            variant=variant, priority_score=8.0,
            selection_rationale="waf", expected_information_gain=5.0,
        )
        candidates = [CandidateAction.from_prioritized(exp)]
        prompt = controller._build_prompt(candidates, ResearchControlState())
        blob = "\n".join(m["content"] for m in prompt)
        self.assertNotIn("SUPER_SECRET_TOKEN", blob)
        self.assertNotIn("top_secret", blob)
        self.assertNotIn("Bearer", blob)
        # 但暴露非敏感描述字段
        self.assertIn("F3_REWRITE_X_REWRITE_URL", blob)
        self.assertIn("https://target/api/x", blob)


class ResearchControllerLoopIntegrationTests(unittest.TestCase):
    """
    最小集成测试：确定性候选 -> controller 选择 -> 被选中的 variant 真实到达 executor
    使用 mock provider + fake transport，不访问真实互联网目标。
    """

    def setUp(self):
        self.endpoint = EndpointIR(method="GET", path="/api/v1/admin/secrets")
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
        # 确定性生成候选，取最高优先级 variant 作为 LLM 应选中的目标
        self.selector = AdaptiveExperimentSelector(default_budget=10)
        all_variants = TransformationFamilyRegistry.generate_all(
            url=self.target_url, method="GET",
        )
        self.top_exp = self.selector.select(
            variants=all_variants,
            classification=self.classification,
            max_budget=5,
        )[0]
        self.top_vid = self.top_exp.variant.variant_id

    def test_controller_selected_variant_reaches_executor(self):
        context = ResearchLoopContext(
            endpoint=self.endpoint,
            target_url=self.target_url,
            baseline_observation=self.baseline_obs,
            denial_classification=self.classification,
        )
        mock_provider = Mock()
        mock_provider.generate_structured_json.return_value = {
            "action": "RUN_EXPERIMENT",
            "target_id": self.top_vid,
            "reason": "control plane picks top candidate",
            "confidence": 0.9,
        }

        dispatched = []

        class RecordingTransport:
            def request(self, method, url, payload, headers, timeout):
                dispatched.append({
                    "method": method, "url": url,
                    "headers": dict(headers), "payload": dict(payload),
                })
                class Resp:
                    pass
                r = Resp()
                r.status_code = 403
                r.text = "403 Forbidden"
                r.headers = {}
                return r

        event_log = []
        config = ResearchLoopConfig(
            max_turns=3,
            max_budget=3,
            control_plane_enabled=True,
            llm_provider=mock_provider,
        )
        run_research_loop(
            context=context,
            config=config,
            transport=RecordingTransport(),
            emit=lambda evt: event_log.append(evt.event_type),
        )

        # 第一次派发的请求必须精确对应 controller 选中的候选 variant
        self.assertTrue(dispatched, "至少应有一次派发")
        first = dispatched[0]
        self.assertEqual(first["url"], self.top_exp.variant.url)
        self.assertEqual(first["headers"], self.top_exp.variant.headers)
        self.assertEqual(first["payload"], self.top_exp.variant.payload)

        # Control Plane 事件已产生
        self.assertIn(ResearchEventType.CONTROL_DECISION_COMPLETED, event_log)
        self.assertEqual(self.top_exp.variant.family.value, "F3_HEADER_TRUST_CONTEXT")


if __name__ == "__main__":
    unittest.main()
