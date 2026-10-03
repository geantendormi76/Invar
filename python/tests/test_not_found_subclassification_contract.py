# -*- coding: utf-8 -*-
"""
Phase 9.6-A 404 语义正交细分契约测试套件 (404 Semantic Subclassification Contract Tests)
对齐 RFC 9110 第 15.5.5 节与现代攻防标准：
严格断言：
1. ROUTE_NOT_FOUND (404-R): 静态网关路由未注册 (INSUFFICIENT + inconclusive)
2. RESOURCE_NOT_FOUND (404-E): 路由存在但实体未决 (AST 模板 ${H} 未展开, INSUFFICIENT + inconclusive)
3. HIDDEN_BY_AUTHZ (404-H):
   - 候选标头阶段: PARTIAL + inconclusive (严禁过度确权为 confirmed)
   - 差分实证阶段: SUFFICIENT + confirmed
4. evidence_id 具备 128-bit 工业级抗碰撞能力。
"""
import unittest

from harness.domain_contracts import (
    DenialCategory,
    DenialLayer,
    DenialObservation,
    DeterministicDenialClassifier,
    EndpointIR,
    EvidenceRecord,
    EvidenceSufficiency,
    HTTPRequestLog,
    HTTPResponseLog,
    NotFoundSubcategory,
    SecurityInvariant,
)
from harness.execution_trace import classify_response
from harness.invariant_evaluator import InvariantEvaluator


class NotFoundSubclassificationContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.auth_inv = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="Administrative routes require valid authentication",
        )

    def test_01_plain_static_path_404_classified_as_route_not_found(self) -> None:
        """【契约 1】纯静态未知路径返回标准 404 时，确权为 ROUTE_NOT_FOUND，层级为 ROUTER"""
        obs = DenialObservation(
            status_code=404,
            response_headers={"server": "nginx"},
            body_preview="<html><title>404 Not Found</title><body><center>nginx</center></body></html>",
            request_url="https://api.ikuai8.com/api/v1/dead_route_static",
        )
        result = DeterministicDenialClassifier.classify(obs)
        self.assertEqual(result.primary_hypothesis.category, DenialCategory.ROUTE_NOT_FOUND)
        self.assertEqual(result.primary_hypothesis.layer, DenialLayer.ROUTER)
        self.assertIn("route_not_found", result.primary_hypothesis.rationale.lower())

    def test_02_ast_template_path_404_classified_as_resource_not_found(self) -> None:
        """【契约 2】URL 包含未实例化 AST 模板 (${H} 或 {id}) 或返回 NoSuchKey 时，确权为 RESOURCE_NOT_FOUND"""
        # 场景 A: URL 包含未展开模板 ${H}
        obs_template = DenialObservation(
            status_code=404,
            response_headers={"content-type": "application/json"},
            body_preview='{"code": 404, "message": "user not found"}',
            request_url="https://api.ikuai8.com/users/${H}/reset-password",
        )
        res_template = DeterministicDenialClassifier.classify(obs_template)
        self.assertEqual(res_template.primary_hypothesis.category, DenialCategory.RESOURCE_NOT_FOUND)
        self.assertEqual(res_template.primary_hypothesis.layer, DenialLayer.APPLICATION)

        # 场景 B: 显式标记 has_unresolved_template
        obs_unresolved = DenialObservation(
            status_code=404,
            response_headers={"server": "openresty"},
            body_preview="<Error><Code>NoSuchKey</Code></Error>",
            has_unresolved_template=True,
        )
        res_unresolved = DeterministicDenialClassifier.classify(obs_unresolved)
        self.assertEqual(res_unresolved.primary_hypothesis.category, DenialCategory.RESOURCE_NOT_FOUND)

    def test_03_404_with_www_authenticate_classified_as_hidden_by_authz(self) -> None:
        """【契约 3】404 携带 WWW-Authenticate 标头时，确权为 HIDDEN_BY_AUTHZ (404 鉴权隐匿)"""
        obs_auth = DenialObservation(
            status_code=404,
            response_headers={
                "server": "gateway",
                "www-authenticate": 'Bearer realm="api.ikuai8.com", error="invalid_token"',
            },
            body_preview="404 Not Found",
            request_url="https://api.ikuai8.com/api/admin/orders",
        )
        res_auth = DeterministicDenialClassifier.classify(obs_auth)
        self.assertEqual(res_auth.primary_hypothesis.category, DenialCategory.HIDDEN_BY_AUTHZ)
        self.assertEqual(res_auth.primary_hypothesis.layer, DenialLayer.AUTHORIZATION)

    def test_04_404_with_auth_differential_classified_as_hidden_by_authz(self) -> None:
        """【契约 4】显式检测到凭据差分 (has_auth_differential=True) 时，确权为 HIDDEN_BY_AUTHZ"""
        obs_diff = DenialObservation(
            status_code=404,
            response_headers={"x-security-policy": "stealth-denial"},
            body_preview="Resource unavailable",
            has_auth_differential=True,
        )
        res_diff = DeterministicDenialClassifier.classify(obs_diff)
        self.assertEqual(res_diff.primary_hypothesis.category, DenialCategory.HIDDEN_BY_AUTHZ)

    def test_05_hidden_by_authz_partial_cannot_be_confirmed(self) -> None:
        """【契约 5 (核心修复)】单凭标头信号的 HIDDEN_BY_AUTHZ 仅为 PARTIAL 证据，绝对禁止确权为 confirmed"""
        ep_static = EndpointIR(method="GET", path="/api/v1/system/status")
        eval_hidden_candidate = InvariantEvaluator.evaluate(
            invariant=self.auth_inv,
            endpoint=ep_static,
            status_code=404,
            payload={},
            headers={"www-authenticate": "Bearer realm=restricted"},
            response_text="Not Found",
            is_auth_differential=False,
        )
        # 铁律断言：PARTIAL 必须收敛为 inconclusive，消除与形式化状态机的矛盾
        self.assertEqual(eval_hidden_candidate.status, "inconclusive")
        self.assertEqual(eval_hidden_candidate.sufficiency, EvidenceSufficiency.PARTIAL)
        self.assertIn("hidden_by_authz", eval_hidden_candidate.rationale)

    def test_06_hidden_by_authz_requires_differential_proof_for_confirmed(self) -> None:
        """【契约 6】具备真实授权物理差分验证时，方准晋升为 confirmed + SUFFICIENT"""
        ep_static = EndpointIR(method="GET", path="/api/v1/system/status")
        eval_hidden_diff = InvariantEvaluator.evaluate(
            invariant=self.auth_inv,
            endpoint=ep_static,
            status_code=404,
            payload={},
            headers={"www-authenticate": "Bearer realm=restricted"},
            response_text="Not Found",
            is_auth_differential=True,
        )
        self.assertEqual(eval_hidden_diff.status, "confirmed")
        self.assertEqual(eval_hidden_diff.sufficiency, EvidenceSufficiency.SUFFICIENT)
        self.assertIn("实锤目标资源受鉴权策略隐匿保护", eval_hidden_diff.rationale)

    def test_07_execution_trace_classify_response_supports_404_subtypes(self) -> None:
        """【契约 7】ExecutionTrace classify_response 准确识别 404 细分标签"""
        self.assertEqual(
            classify_response(404, "Cannot GET /api/foo", request_url="/api/foo"),
            "route_not_found",
        )
        self.assertEqual(
            classify_response(404, "<Error><Code>NoSuchKey</Code></Error>", request_url="/orders/${H}"),
            "resource_not_found",
        )
        self.assertEqual(
            classify_response(404, "404 Not Found", headers={"www-authenticate": "Bearer"}),
            "hidden_by_authz",
        )

    def test_08_evidence_id_collision_resistance_uses_32_hex(self) -> None:
        """【契约 8】EvidenceRecord 全局凭证采用 128-bit (32 字符) 物理哈希防碰撞标准"""
        ev = EvidenceRecord(
            endpoint=EndpointIR(method="GET", path="/test"),
            request=HTTPRequestLog(method="GET", url="https://example.com/test"),
            response=HTTPResponseLog(status_code=404, body_preview="Not Found"),
            run_id="RUN-100",
            task_id="TASK-1",
            attempt_id=2,
        )
        parts = ev.evidence_id.split(":")
        hash_part = parts[-1]
        self.assertEqual(len(hash_part), 32)
        self.assertEqual(len(ev.short_id), 8)


if __name__ == "__main__":
    unittest.main()
