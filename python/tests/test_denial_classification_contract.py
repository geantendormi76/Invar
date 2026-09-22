import unittest
from harness.denial_models import (
    DenialCategory,
    DenialHypothesis,
    DenialLayer,
    DenialObservation,
    DeterministicDenialClassifier,
    EvidenceGrade,
    FrontendComponent,
)


class DenialClassificationContractTests(unittest.TestCase):
    """
    对齐《规格书 v1.0.0》第 10 节与第 22.2 节的 6 大核心拒绝契约测试
    """

    def test_403_plain_does_not_assume_waf(self):
        """【契约 1】无边缘指纹的普通 403 绝不主观断定为 WAF 拦截"""
        obs = DenialObservation(
            status_code=403,
            response_headers={"content-type": "application/json", "content-length": "42"},
            body_preview='{"error": "Forbidden access"}',
        )
        result = DeterministicDenialClassifier.classify(obs)
        # 前端指纹必须为 UNKNOWN，绝不强加 WAF 结论
        self.assertEqual(result.frontend_component, FrontendComponent.UNKNOWN)
        # 归类层级应为 AUTHORIZATION
        self.assertEqual(result.primary_hypothesis.layer, DenialLayer.AUTHORIZATION)
        self.assertEqual(result.primary_hypothesis.category, DenialCategory.ACCESS_POLICY_DENIAL)

    def test_405_with_allow_header_is_method_policy_denial(self):
        """【契约 2】RFC 9110 语义：405 + Allow 头部确定性归类为 METHOD_POLICY_DENIAL"""
        obs = DenialObservation(
            status_code=405,
            response_headers={"allow": "GET, HEAD, OPTIONS", "server": "nginx"},
            body_preview="405 Not Allowed",
        )
        result = DeterministicDenialClassifier.classify(obs)
        self.assertEqual(result.primary_hypothesis.category, DenialCategory.METHOD_POLICY_DENIAL)
        self.assertEqual(result.primary_hypothesis.layer, DenialLayer.ROUTER)
        self.assertEqual(result.primary_hypothesis.evidence_grade, EvidenceGrade.GRADE_A)
        self.assertIn("Allow: GET, HEAD, OPTIONS", result.primary_hypothesis.supporting_evidence_refs)

    def test_waf_fingerprint_decoupled_from_denial_category(self):
        """【契约 3】架构解耦：WAF 是网络拓扑组件，拒绝类别依然是 ACCESS_POLICY_DENIAL"""
        obs = DenialObservation(
            status_code=403,
            response_headers={
                "server": "aliyun-waf",
                "x-waf-event": "block-rule-403",
                "content-type": "text/html",
            },
            body_preview="<html>Blocked by Aliyun WAF</html>",
        )
        result = DeterministicDenialClassifier.classify(obs)
        # 拓扑维度命中 WAF
        self.assertEqual(result.frontend_component, FrontendComponent.WAF)
        # 决策维度依然是 ACCESS_POLICY_DENIAL，两权分立
        self.assertEqual(result.primary_hypothesis.category, DenialCategory.ACCESS_POLICY_DENIAL)
        self.assertEqual(result.primary_hypothesis.layer, DenialLayer.EDGE)
        self.assertEqual(result.primary_hypothesis.evidence_grade, EvidenceGrade.GRADE_A)

    def test_rate_limit_429_is_independent_category(self):
        """【契约 4】429 属于独立的 RATE_LIMIT，严禁误判为权限或路由故障"""
        obs = DenialObservation(
            status_code=429,
            response_headers={"retry-after": "60", "server": "nginx"},
            body_preview="Too Many Requests",
        )
        result = DeterministicDenialClassifier.classify(obs)
        self.assertEqual(result.primary_hypothesis.category, DenialCategory.RATE_LIMIT)
        self.assertEqual(result.primary_hypothesis.layer, DenialLayer.EDGE)
        self.assertEqual(result.primary_hypothesis.evidence_grade, EvidenceGrade.GRADE_A)

    def test_ambiguous_evidence_produces_multi_hypotheses(self):
        """【契约 5】信息不足时绝不武断单断言，必须保留备选假设"""
        obs = DenialObservation(
            status_code=403,
            response_headers={"server": "nginx"},
            body_preview="403 Forbidden",
        )
        result = DeterministicDenialClassifier.classify(obs)
        # 必须具备备选假设
        self.assertTrue(len(result.alternative_hypotheses) >= 1)
        alt_categories = [h.category for h in result.alternative_hypotheses]
        self.assertIn(DenialCategory.ROUTING_MISMATCH, alt_categories)

    def test_evidence_grades_and_serialization(self):
        """【契约 6】结构无损序列化与完整证据链追溯"""
        obs = DenialObservation(
            status_code=403,
            response_headers={"server": "nginx"},
            body_preview="Test Body",
        )
        result = DeterministicDenialClassifier.classify(obs)
        res_dict = result.to_dict()
        self.assertIn("primary_hypothesis", res_dict)
        self.assertIn("alternative_hypotheses", res_dict)
        self.assertIn("frontend_component", res_dict)
        self.assertEqual(res_dict["raw_observation"]["status_code"], 403)
        self.assertEqual(len(res_dict["raw_observation"]["body_hash"]), 16)


if __name__ == "__main__":
    unittest.main()
