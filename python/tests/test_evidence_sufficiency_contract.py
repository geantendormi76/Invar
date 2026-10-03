# -*- coding: utf-8 -*-
"""
Phase 9.5 证据充分性契约测试套件 (Evidence Sufficiency Contract Tests)
对齐现代形式化验证与顶会科研标准：
断言安全裁决必须伴随确定性的证据完备度评级 (SUFFICIENT / PARTIAL / INSUFFICIENT)，
彻底杜绝将 405 动词拦截或 404 模板未决过度推断为“充分的认证有效性证明”，
并且断言拒绝物理事实与裁决理据维持严格的 1-to-1 精准单射。
"""
import unittest

from harness.domain_contracts import (
    EndpointIR,
    EvidenceSufficiency,
    ResearchCase,
    SecurityInvariant,
)
from harness.invariant_evaluator import InvariantEvaluator


class EvidenceSufficiencyContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.auth_invariant = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="Sensitive administration routes must enforce authentication",
        )
        self.endpoint_post = EndpointIR(method="POST", path="/api/v1/admin/users")

    def test_01_http_401_or_403_has_sufficient_evidence(self) -> None:
        """【契约 1】明确的 401/403 鉴权拦截属于充分证据 (SUFFICIENT)，且理据精确对应底层事实"""
        eval_401 = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=401,
            payload={},
            headers={},
            response_text='{"code": 401, "message": "Unauthorized"}',
        )
        self.assertEqual(eval_401.status, "confirmed")
        self.assertEqual(eval_401.sufficiency, EvidenceSufficiency.SUFFICIENT)
        self.assertIn("HTTP 401", eval_401.rationale)
        self.assertIn("authentication_required", eval_401.rationale)

        eval_403 = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=403,
            payload={},
            headers={},
            response_text='{"code": 403, "message": "Forbidden"}',
        )
        self.assertEqual(eval_403.status, "confirmed")
        self.assertEqual(eval_403.sufficiency, EvidenceSufficiency.SUFFICIENT)
        self.assertIn("HTTP 403", eval_403.rationale)
        self.assertIn("access_policy_denial", eval_403.rationale)

    def test_02_http_405_method_denial_has_partial_evidence(self) -> None:
        """【契约 2】RFC 9110 405 动词拒绝仅构成局部证据 (PARTIAL)，防御未击穿但未进入深度认证层"""
        eval_405 = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=405,
            payload={},
            headers={"Allow": "GET, OPTIONS"},
            response_text='{"code": 405, "message": "Method Not Allowed"}',
        )
        self.assertEqual(eval_405.status, "confirmed")
        self.assertEqual(eval_405.sufficiency, EvidenceSufficiency.PARTIAL)
        self.assertIn("动词策略层实施拒绝拦截", eval_405.rationale)

    def test_03_http_404_resource_not_found_is_insufficient(self) -> None:
        """【契约 3】404 资源不存在或动态模板未解析属于证据不足 (INSUFFICIENT)，必须收敛为 inconclusive"""
        eval_404 = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=404,
            payload={},
            headers={},
            response_text="<Error><Code>NoSuchKey</Code></Error>",
        )
        self.assertEqual(eval_404.status, "inconclusive")
        self.assertEqual(eval_404.sufficiency, EvidenceSufficiency.INSUFFICIENT)

    def test_04_unauthenticated_200_bypass_has_sufficient_evidence_for_vulnerability(self) -> None:
        """【契约 4】无凭据下物理放行 200 属于证据充分 (SUFFICIENT) 实锤击穿不变量"""
        eval_200 = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=200,
            payload={},
            headers={},
            response_text='{"status": "success", "admin_data": "sensitive_leaked"}',
        )
        self.assertEqual(eval_200.status, "vulnerable")
        self.assertEqual(eval_200.sufficiency, EvidenceSufficiency.SUFFICIENT)

    def test_05_case_evaluation_aggregates_evidence_sufficiency(self) -> None:
        """【契约 5】综合决策层自动聚合充分性：若底层存在 INSUFFICIENT，案例全局裁决降级为 INSUFFICIENT"""
        case = ResearchCase(case_id="POST:/api/v1/admin/users", endpoint=self.endpoint_post)
        case.add_invariant(self.auth_invariant)

        decision = InvariantEvaluator.evaluate_case(
            case=case,
            status_code=404,
            payload={},
            headers={},
            response_text="Not Found",
        )
        self.assertIsNotNone(decision)
        self.assertEqual(decision.status, "inconclusive")
        self.assertEqual(decision.sufficiency, EvidenceSufficiency.INSUFFICIENT)

    def test_06_soft_denial_and_html_fallback_have_exact_rationales(self) -> None:
        """【契约 6】业务软拒绝与前端 HTML 兜底具有精确的证据标签与单射理据"""
        eval_soft = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=200,
            payload={},
            headers={},
            response_text='{"code": 4003, "msg": "forbidden"}',
            is_soft_denial=True,
        )
        self.assertEqual(eval_soft.status, "confirmed")
        self.assertEqual(eval_soft.sufficiency, EvidenceSufficiency.SUFFICIENT)
        self.assertIn("business_soft_denial", eval_soft.rationale)

        eval_html = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=200,
            payload={},
            headers={},
            response_text='<!DOCTYPE html><html><head><title>App</title></head><body>SPA Root</body></html>',
        )
        self.assertEqual(eval_html.status, "confirmed")
        self.assertEqual(eval_html.sufficiency, EvidenceSufficiency.SUFFICIENT)
        self.assertIn("gateway_fallback_html", eval_html.rationale)


if __name__ == "__main__":
    unittest.main()

    def test_07_status_and_sufficiency_semantic_coherence_matrix(self) -> None:
        """【契约 7】裁决状态与证据充分性遵循绝对相容偏序，严禁语义倒置"""
        # 1. 击穿 (vulnerable) 必须是 SUFFICIENT
        eval_vuln = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=200,
            payload={},
            headers={},
            response_text='{"status": "ok", "leaked": true}',
        )
        self.assertEqual(eval_vuln.status, "vulnerable")
        self.assertEqual(eval_vuln.sufficiency, EvidenceSufficiency.SUFFICIENT)

        # 2. 动词拦截 (405) confirmed 必须是 PARTIAL
        eval_405 = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=405,
            payload={},
            headers={},
        )
        self.assertEqual(eval_405.status, "confirmed")
        self.assertEqual(eval_405.sufficiency, EvidenceSufficiency.PARTIAL)

        # 3. 访问控制拦截 (403) confirmed 必须是 SUFFICIENT
        eval_403 = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=403,
            payload={},
            headers={},
        )
        self.assertEqual(eval_403.status, "confirmed")
        self.assertEqual(eval_403.sufficiency, EvidenceSufficiency.SUFFICIENT)

        # 4. 资源未决 (404) inconclusive 必须是 INSUFFICIENT
        eval_404 = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_post,
            status_code=404,
            payload={},
            headers={},
        )
        self.assertEqual(eval_404.status, "inconclusive")
        self.assertEqual(eval_404.sufficiency, EvidenceSufficiency.INSUFFICIENT)
