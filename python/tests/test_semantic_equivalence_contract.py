import unittest
from harness.denial_models import DenialObservation
from harness.semantic_models import (
    EquivalenceVerdict,
    SemanticEquivalenceEvaluator,
    ThreeValuedLogic,
)
from harness.transformation_models import TransformationFamily, TransformationVariant


class SemanticEquivalenceContractTests(unittest.TestCase):
    """
    对齐《规格书 v1.0.0》第 12 节与第 22.2 节的语义等价与防误报契约测试
    """

    def setUp(self):
        self.baseline_403 = DenialObservation(
            status_code=403,
            response_headers={"server": "nginx"},
            body_preview='{"error": "Forbidden"}',
        )
        self.variant = TransformationVariant(
            variant_id="F3_REWRITE_X_ORIGINAL_URL",
            family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
            method="GET",
            url="https://example.com/",
            headers={"X-Original-URL": "/api/v1/secret"},
        )
        self.public_homepage_html = "<html><title>Welcome to Example Cloud Platform</title><body>Public Home</body></html>"

    def test_same_resource_when_expected_identifiers_match(self):
        """【契约 1】当候选响应包含声明的业务实体特征时，实锤确权为 SAME_RESOURCE"""
        candidate_200 = DenialObservation(
            status_code=200,
            response_headers={"content-type": "application/json"},
            body_preview='{"secret_token": "live_corp_key_9988", "vault_id": "VAULT-001"}',
        )
        result = SemanticEquivalenceEvaluator.evaluate(
            baseline=self.baseline_403,
            candidate=candidate_200,
            variant=self.variant,
            expected_resource_markers=["secret_token", "vault_id"],
        )
        self.assertEqual(result.verdict, EquivalenceVerdict.SAME_RESOURCE)
        self.assertEqual(result.dimensions.identity_equivalent, ThreeValuedLogic.YES)
        self.assertEqual(result.dimensions.route_equivalent, ThreeValuedLogic.YES)
        self.assertIn("vault_id", result.rationale)

    def test_different_resource_when_redirected_to_login(self):
        """【契约 2】变异发包被 302 重定向到登录页时，坚决判定为 DIFFERENT_RESOURCE"""
        candidate_302 = DenialObservation(
            status_code=302,
            response_headers={"location": "https://example.com/sso/login?redirect=%2Fsecret"},
            body_preview="Redirecting to SSO Login...",
        )
        result = SemanticEquivalenceEvaluator.evaluate(
            baseline=self.baseline_403,
            candidate=candidate_302,
            variant=self.variant,
        )
        self.assertEqual(result.verdict, EquivalenceVerdict.DIFFERENT_RESOURCE)
        self.assertTrue(result.differential.redirect_to_auth_barrier)
        self.assertIn("身份认证关卡", result.rationale)

    def test_generic_200_homepage_fallback_is_not_same_resource(self):
        """【契约 3】重写头拿到 200 但内容是公共首页时，彻底识破伪装，定性为 DIFFERENT_RESOURCE"""
        # 很多代理在无法重写时直接吐出公开根路由网页 (HTTP 200)，传统脚本会误报为 bypass
        candidate_fake_200 = DenialObservation(
            status_code=200,
            response_headers={"content-type": "text/html"},
            body_preview="<html><title>Welcome to Example Cloud Platform</title><body>Public Home Page Banner</body></html>",
        )
        result = SemanticEquivalenceEvaluator.evaluate(
            baseline=self.baseline_403,
            candidate=candidate_fake_200,
            variant=self.variant,
            public_root_preview=self.public_homepage_html,
        )
        self.assertEqual(result.verdict, EquivalenceVerdict.DIFFERENT_RESOURCE)
        self.assertTrue(result.differential.body_similarity_to_public_root >= 0.85)
        self.assertIn("公共根路由", result.rationale)

    def test_different_resource_when_missing_expected_markers(self):
        """【契约 4】虽返回 200 但完全缺失预期敏感字段，判定为 DIFFERENT_RESOURCE"""
        candidate_200_empty = DenialObservation(
            status_code=200,
            response_headers={"content-type": "application/json"},
            body_preview='{"status": "ok", "items": []}',
        )
        result = SemanticEquivalenceEvaluator.evaluate(
            baseline=self.baseline_403,
            candidate=candidate_200_empty,
            variant=self.variant,
            expected_resource_markers=["secret_token", "vault_id"],
        )
        self.assertEqual(result.verdict, EquivalenceVerdict.DIFFERENT_RESOURCE)
        self.assertEqual(result.dimensions.identity_equivalent, ThreeValuedLogic.NO)

    def test_unknown_when_no_domain_markers_provided(self):
        """【契约 5】三值逻辑铁律：调用方未提供业务参考且响应无特征时，必须置为 UNKNOWN，绝不可盲目标为成功"""
        candidate_200_bare = DenialObservation(
            status_code=200,
            response_headers={"content-type": "application/json"},
            body_preview='{"success": true}',
        )
        result = SemanticEquivalenceEvaluator.evaluate(
            baseline=self.baseline_403,
            candidate=candidate_200_bare,
            variant=self.variant,
            expected_resource_markers=None,  # 未注入业务先验
        )
        self.assertEqual(result.verdict, EquivalenceVerdict.UNKNOWN)
        self.assertEqual(result.dimensions.identity_equivalent, ThreeValuedLogic.UNKNOWN)
        self.assertIn("UNKNOWN", result.rationale)

    def test_differential_metrics_accuracy(self):
        """【契约 6】物理差分度量计算绝对精准"""
        candidate_200 = DenialObservation(
            status_code=200,
            response_headers={"content-type": "application/json"},
            body_preview='{"data": 12345}',
        )
        result = SemanticEquivalenceEvaluator.evaluate(
            baseline=self.baseline_403,
            candidate=candidate_200,
            variant=self.variant,
        )
        # 403 -> 200: status_delta 应为 -203
        self.assertEqual(result.differential.status_delta, -203)
        self.assertTrue(result.differential.body_hash_changed)


if __name__ == "__main__":
    unittest.main()
