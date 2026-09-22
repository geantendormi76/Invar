import unittest
from harness.adaptive_selector import AdaptiveExperimentSelector
from harness.denial_models import (
    DenialCategory,
    DenialClassificationResult,
    DenialHypothesis,
    DenialLayer,
    EvidenceGrade,
    FrontendComponent,
)
from harness.transformation_models import (
    TransformationFamily,
    TransformationFamilyRegistry,
)


class AdaptiveSelectorContractTests(unittest.TestCase):
    """
    对齐《规格书 v1.0.0》第 16 节自适应实验选择与优先级剪枝测试
    """

    def setUp(self):
        self.selector = AdaptiveExperimentSelector(default_budget=10)
        self.variants = TransformationFamilyRegistry.generate_all(
            url="https://target.corp.local/api/v1/admin/secrets",
            method="GET",
        )

    def test_waf_access_denial_prioritizes_rewrite_and_path_normalization(self):
        """【契约 1】遭遇 WAF 阻断时，Top 实验必须优先下发 X-Rewrite-URL 与 %2e 路径变异"""
        classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-403-EDGE",
                layer=DenialLayer.EDGE,
                category=DenialCategory.ACCESS_POLICY_DENIAL,
                confidence=0.9,
                evidence_grade=EvidenceGrade.GRADE_A,
            ),
            frontend_component=FrontendComponent.WAF,
        )
        selected = self.selector.select(
            variants=self.variants,
            classification=classification,
            max_budget=5,
        )
        self.assertEqual(len(selected), 5)
        top_vids = [exp.variant.variant_id for exp in selected]

        # 第一名必须是杀手锏 X-Rewrite-URL 或 X-Original-URL
        self.assertTrue("X_REWRITE_URL" in top_vids[0] or "X_ORIGINAL_URL" in top_vids[0])
        # 前 5 名中必须包含核心路径畸变
        self.assertTrue(any("PERCENT_DOT" in vid or "SEMICOLON" in vid for vid in top_vids))

    def test_method_policy_denial_prioritizes_f2_verb_tunnels(self):
        """【契约 2】遭遇 405 动词策略拒绝时，Top 实验必须优先下发 F2 动词隧道"""
        classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-405-METHOD",
                layer=DenialLayer.ROUTER,
                category=DenialCategory.METHOD_POLICY_DENIAL,
                confidence=0.95,
                evidence_grade=EvidenceGrade.GRADE_A,
            ),
            frontend_component=FrontendComponent.REVERSE_PROXY,
        )
        selected = self.selector.select(
            variants=self.variants,
            classification=classification,
            max_budget=4,
        )
        top_families = [exp.variant.family for exp in selected]
        # 前几名必须全量被 F2 动词语义族包揽
        self.assertEqual(top_families[0], TransformationFamily.F2_METHOD_SEMANTICS)
        self.assertEqual(top_families[1], TransformationFamily.F2_METHOD_SEMANTICS)

    def test_budget_capping_prunes_long_tail_variants(self):
        """【契约 3】预算熔断控制：46 个变异体被精准截断至指定的预算上限"""
        classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-TEST",
                layer=DenialLayer.UNKNOWN,
                category=DenialCategory.UNKNOWN,
                confidence=0.5,
                evidence_grade=EvidenceGrade.GRADE_B,
            ),
        )
        # 指定预算为 8
        selected = self.selector.select(
            variants=self.variants,
            classification=classification,
            max_budget=8,
        )
        self.assertEqual(len(selected), 8)

    def test_failure_penalty_deprioritizes_failed_variants(self):
        """【契约 4】失败惩罚机制：近期失败的变异体优先级受到压制并下沉"""
        classification = DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id="DH-WAF",
                layer=DenialLayer.EDGE,
                category=DenialCategory.ACCESS_POLICY_DENIAL,
                confidence=0.9,
                evidence_grade=EvidenceGrade.GRADE_A,
            ),
            frontend_component=FrontendComponent.WAF,
        )
        # 惩罚此前最高分的变异体
        target_failed_vid = "F3_REWRITE_X_REWRITE_URL"
        selected_normal = self.selector.select(self.variants, classification, max_budget=10)
        normal_vids = [exp.variant.variant_id for exp in selected_normal]

        selected_penalized = self.selector.select(
            self.variants,
            classification,
            max_budget=10,
            recent_failures={target_failed_vid},
        )
        penalized_scores = {exp.variant.variant_id: exp.priority_score for exp in selected_penalized}

        # 受到惩罚的算子分值必须显著低于正常情况
        normal_scores = {exp.variant.variant_id: exp.priority_score for exp in selected_normal}
        self.assertTrue(penalized_scores[target_failed_vid] < normal_scores[target_failed_vid])


if __name__ == "__main__":
    unittest.main()
