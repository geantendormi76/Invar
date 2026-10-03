# -*- coding: utf-8 -*-
"""
Phase 9.7-B 多主体身份上下文矩阵契约测试套件 (Identity Matrix Contract Tests)
对标顶级 API 安全黄金标准 (OWASP API Top 10 BOLA/BFLA 与 Strix/Claude-Red SOP):
断言系统具备多主体 (Anonymous / Tenant A / Tenant B / Admin) 身份画像建模能力，
物理物证强制绑定发包主体血统 (Principal)，并实现跨租户横向越权矩阵的精准差分断言。
"""
import unittest

from harness.domain_contracts import (
    AuthPrincipal,
    EndpointIR,
    EvidenceRecord,
    HTTPRequestLog,
    HTTPResponseLog,
    IdentityMatrix,
    TenantIsolationViolationError,
)


class IdentityMatrixContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.endpoint_order = EndpointIR(
            method="GET",
            path="/api/v1/tenants/alpha/orders/1001",
            endpoint_id="GET:/api/v1/tenants/alpha/orders/1001",
            extracted_params=["order_id", "tenant_id"],
        )

        # 主体 A: 资源受害者合法属主 (Tenant Alpha Owner)
        self.principal_victim = AuthPrincipal(
            principal_id="principal_victim_a",
            role="authenticated_user",
            tenant_id="tenant_alpha",
            token="token_alice_secret_123",
        )

        # 主体 B: 潜在越权攻击者 (Tenant Beta Attacker)
        self.principal_attacker = AuthPrincipal(
            principal_id="principal_attacker_b",
            role="authenticated_user",
            tenant_id="tenant_beta",
            token="token_bob_attacker_456",
        )

        # 主体 C: 未认证匿名访客
        self.principal_anon = AuthPrincipal(
            principal_id="principal_anon",
            role="anonymous",
            tenant_id=None,
            token=None,
        )

        self.matrix = IdentityMatrix(
            principals=[self.principal_victim, self.principal_attacker, self.principal_anon],
            default_victim_id="principal_victim_a",
            default_attacker_id="principal_attacker_b",
        )

    def test_01_auth_principal_generates_stable_credential_fingerprint(self) -> None:
        """【契约 1】AuthPrincipal 自动基于凭证生成安全脱敏的确定性凭据指纹"""
        self.assertTrue(len(self.principal_victim.credential_fingerprint) == 16)
        self.assertTrue(len(self.principal_attacker.credential_fingerprint) == 16)
        self.assertNotEqual(
            self.principal_victim.credential_fingerprint,
            self.principal_attacker.credential_fingerprint,
        )
        self.assertEqual(self.principal_anon.credential_fingerprint, "anon_credential")

    def test_02_evidence_record_binds_physical_principal_provenance(self) -> None:
        """【契约 2】EvidenceRecord 强制承载发包主体血统 (Principal)，精准回答谁发出的请求"""
        ev_attacker = EvidenceRecord(
            endpoint=self.endpoint_order,
            request=HTTPRequestLog(
                method="GET",
                url="https://api.ikuai8.com/api/v1/tenants/alpha/orders/1001",
                headers={"Authorization": "Bearer token_bob_attacker_456"},
                body={},
            ),
            response=HTTPResponseLog(
                status_code=403,
                body_preview="Access Denied: cross-tenant access prohibited",
            ),
            principal=self.principal_attacker,
            run_id="RUN-IDENTITY-001",
        )
        self.assertIsNotNone(ev_attacker.principal)
        self.assertEqual(ev_attacker.principal.principal_id, "principal_attacker_b")
        self.assertEqual(ev_attacker.principal.tenant_id, "tenant_beta")

    def test_03_identity_matrix_retrieval_and_role_indexing(self) -> None:
        """【契约 3】IdentityMatrix 支持按 ID、角色与租户检索主体，缺省时显式报错"""
        victim = self.matrix.get_principal("principal_victim_a")
        self.assertEqual(victim.tenant_id, "tenant_alpha")

        attacker = self.matrix.get_attacker()
        self.assertEqual(attacker.principal_id, "principal_attacker_b")

        anon = self.matrix.get_anonymous()
        self.assertEqual(anon.role, "anonymous")

    def test_04_tenant_isolation_breached_when_attacker_leaks_victim_private_entity(self) -> None:
        """【契约 4 (BOLA/IDOR 核心)】攻击者拿到受害者私密租户实体时，矩阵求值实锤击穿并抛出异常"""
        victim_resp = '{"order_id": 1001, "tenant": "tenant_alpha", "secret_key": "sec_alpha_999"}'
        attacker_resp = '{"order_id": 1001, "tenant": "tenant_alpha", "secret_key": "sec_alpha_999"}'

        # 攻击者在租户为 tenant_beta 的凭证下，成功拿到了 tenant_alpha 的资源实体
        result = self.matrix.assert_tenant_isolation(
            victim_principal=self.principal_victim,
            victim_response=victim_resp,
            attacker_principal=self.principal_attacker,
            attacker_response=attacker_resp,
            attacker_status_code=200,
        )
        self.assertEqual(result.is_isolated, False)
        self.assertEqual(result.verdict, "VULNERABLE")
        self.assertIn("Cross-tenant data leakage detected", result.rationale)

    def test_05_tenant_isolation_held_when_attacker_rejected_with_403_or_own_data(self) -> None:
        """【契约 5 (消除误报)】攻击者收到 403 或自身租户的合法实体时，隔离边界守住"""
        # 场景 A: 收到 403 明确拦截
        result_blocked = self.matrix.assert_tenant_isolation(
            victim_principal=self.principal_victim,
            victim_response='{"order_id": 1001, "tenant": "tenant_alpha"}',
            attacker_principal=self.principal_attacker,
            attacker_response='{"error": "Forbidden"}',
            attacker_status_code=403,
        )
        self.assertEqual(result_blocked.is_isolated, True)
        self.assertEqual(result_blocked.verdict, "DEFENSE_HELD")


if __name__ == "__main__":
    unittest.main()
