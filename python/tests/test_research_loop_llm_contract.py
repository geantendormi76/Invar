import unittest
from unittest.mock import Mock

from agent.loop_types import ResearchEvent, ResearchEventType
from agent.research_loop import (
    ResearchLoopConfig,
    ResearchLoopContext,
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
from harness.transport import TransportResponse


class ResearchLoopLLMContractTests(unittest.TestCase):
    """
    针对 Phase 5.4 大模型认知反思跃迁机制的契约测试
    """

    def setUp(self):
        self.endpoint = EndpointIR(method="POST", path="/api/v1/internal/config")
        self.target_url = "https://cloud.ikuai8.com/api/v1/internal/config"
        self.baseline_obs = DenialObservation(
            status_code=403,
            response_headers={"server": "nginx"},
            body_preview='{"code": 403, "message": "Permission denied"}',
        )
        self.classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-403-TEST",
                layer=DenialLayer.AUTHORIZATION,
                category=DenialCategory.ACCESS_POLICY_DENIAL,
                confidence=0.8,
                evidence_grade=EvidenceGrade.GRADE_B,
            ),
            frontend_component=FrontendComponent.UNKNOWN,
            raw_observation=self.baseline_obs,
        )

    def test_llm_reflection_is_triggered_when_heuristics_fail(self):
        """验证常规启发式变异耗尽后，成功唤醒大模型开展反思推导并完成证据链装配"""
        context = ResearchLoopContext(
            endpoint=self.endpoint,
            target_url=self.target_url,
            baseline_observation=self.baseline_obs,
            denial_classification=self.classification,
        )

        # 模拟模型提供者
        mock_provider = Mock()
        mock_provider.generate_structured_json.return_value = {
            "rationale": "Inferred internal management token requirement",
            "headers": {"X-Internal-Token": "secret_token_123"},
            "payload": {"force": True},
        }

        # 模拟 Transport:
        # 常规变异全部返回 403 阻断；唯有当携带了模型推导出的 X-Internal-Token 时放行 200
        class MockTransport:
            def request(self, method, url, payload, headers, timeout):
                if headers.get("X-Internal-Token") == "secret_token_123":
                    return TransportResponse(
                        status_code=200,
                        text='{"status": "ok", "config_updated": true}',
                        headers={"content-type": "application/json"},
                    )
                return TransportResponse(
                    status_code=403,
                    text='{"code": 403, "message": "Permission denied"}',
                    headers={"content-type": "application/json"},
                )

        event_log = []
        config = ResearchLoopConfig(
            max_turns=2,  # 设定少量轮次以便快速耗尽启发式变异
            max_budget=2,
            llm_provider=mock_provider,
        )

        result = run_research_loop(
            context=context,
            config=config,
            transport=MockTransport(),
            emit=lambda evt: event_log.append(evt.event_type),
        )

        # 1. 断言大模型推理开始与完成事件已被按序抛出
        self.assertIn(ResearchEventType.LLM_REASONING_STARTED, event_log)
        self.assertIn(ResearchEventType.LLM_REASONING_COMPLETED, event_log)

        # 2. 断言大模型提供者被成功调用，且收到了包含报错上下文的 Prompt
        self.assertTrue(mock_provider.generate_structured_json.called)

        # 3. 断言模型变异体突破成功，且证据链正确记录了 LLM-COT 标识
        self.assertTrue(result.breakthrough_achieved)
        self.assertEqual(result.final_verdict, EvidenceVerdict.CANDIDATE)
        self.assertIsNotNone(result.evidence_chain)
        self.assertIn("LLM-COT", result.evidence_chain.chain_id)
        self.assertEqual(
            result.evidence_chain.applied_variant.headers.get("X-Internal-Token"),
            "secret_token_123",
        )


if __name__ == "__main__":
    unittest.main()
