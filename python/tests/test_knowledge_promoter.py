import unittest
from agent.knowledge_promoter import KnowledgeCard, KnowledgePromoter
from harness.finding_models import (
    Confidence,
    FindingRecord,
    Remediation,
    Severity,
    Verdict,
    VerificationSummary,
)
from harness.candidate_models import (
    Candidate,
    CandidateFingerprint,
    CanonicalFactors,
    TraceStep,
)
from harness.models import EndpointIR
from harness.research_models import Hypothesis, ResearchCase
from harness.verification_gate import PromotionGate


class KnowledgePromoterTests(unittest.TestCase):
    def test_promotes_verified_destruct_hypothesis_into_vulnerability_card(self) -> None:
        endpoint = EndpointIR(method="DELETE", path="/api/orders/batch")
        case = ResearchCase(case_id="DELETE:/api/orders/batch", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-DESTRUCT-1",
                statement="破坏性操作缺失确认",
                status="VERIFIED",
                evidence_notes="直接发包返回 200，未校验 confirm",
            )
        )

        cards = KnowledgePromoter.promote_case(case)
        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(card.category, "DESTRUCTIVE_GUARD_MISSING")
        self.assertEqual(card.severity, "HIGH")
        self.assertEqual(card.verification_state, "VERIFIED")
        self.assertEqual(card.confidence, 1.0)
        self.assertIn("DELETE:/api/orders/batch", f"{card.provenance_task}")

    def test_promotes_verified_auth_hypothesis_into_critical_card(self) -> None:
        endpoint = EndpointIR(method="GET", path="/api/admin/users")
        case = ResearchCase(case_id="GET:/api/admin/users", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-AUTH-1",
                statement="敏感特权路由缺失认证",
                status="VERIFIED",
                evidence_notes="未携带 Token 响应 200",
            )
        )

        cards = KnowledgePromoter.promote_case(case)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].category, "BROKEN_AUTHENTICATION")
        self.assertEqual(cards[0].severity, "CRITICAL")
        self.assertEqual(cards[0].verification_state, "VERIFIED")

    def test_promotes_verified_idor_hypothesis_into_high_card(self) -> None:
        endpoint = EndpointIR(method="GET", path="/api/orders/detail", extracted_params=["order_id"])
        case = ResearchCase(case_id="GET:/api/orders/detail", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-IDOR-1",
                statement="越权访问",
                status="VERIFIED",
                evidence_notes="主体 B 成功窃取主体 A 订单数据",
            )
        )

        cards = KnowledgePromoter.promote_case(case)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].category, "BOLA_IDOR_VULNERABILITY")
        self.assertEqual(cards[0].severity, "HIGH")

    def test_promotion_gate_blocks_unverified_proposed_hypotheses(self) -> None:
        endpoint = EndpointIR(method="GET", path="/api/orders")
        case = ResearchCase(case_id="GET:/api/orders", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-AUTH-1",
                statement="推测未鉴权",
                status="PROPOSED",
            )
        )
        cards = KnowledgePromoter.promote_case(case)
        self.assertEqual(len(cards), 0)

    def test_knowledge_card_supports_structured_serialization(self) -> None:
        card = KnowledgeCard(
            card_id="KC-AUTH-01",
            category="BROKEN_AUTHENTICATION",
            title="敏感接口未授权",
            claim="端点未对请求进行鉴权",
            severity="CRITICAL",
            verification_state="VERIFIED",
            confidence=1.0,
            source_hypothesis="H-AUTH-1",
            provenance_task="GET:/api/admin",
            remediation="添加鉴权中间件",
            evidence_summary="物理发包验证通过",
        )
        data = card.to_dict()
        self.assertEqual(data["card_id"], "KC-AUTH-01")
        self.assertEqual(data["severity"], "CRITICAL")
        self.assertEqual(data["confidence"], 1.0)

    # --------------------------------------------------------------------------
    # Phase 5.5: OpenSSF OpenVEX 黄金标准契约断言 (Gold Standard Assertions)
    # --------------------------------------------------------------------------
    def test_knowledge_card_openvex_statement_affected_contract(self) -> None:
        """断言 ①：实锤漏洞实体生成标准 OpenVEX affected 声明，且严禁泄露 justification"""
        card = KnowledgeCard(
            card_id="KC-fp:auth:admin:1234",
            category="BROKEN_AUTHENTICATION",
            title="管理员接口未授权越权访问",
            claim="端点 POST /admin/config 在无凭证下成功放行",
            severity="HIGH",
            verification_state="VERIFIED",
            confidence=1.0,
            source_hypothesis="H-AUTH-1",
            provenance_task="POST:/admin/config",
            remediation="在网关层配置强制 JWT 校验中间件",
            evidence_summary="独立复核人 [verifier-alpha] 签署，物理重放一致",
        )

        stmt = card.to_openvex_statement()

        # 契约断言
        self.assertEqual(stmt["status"], "affected")
        self.assertEqual(stmt["vulnerability"]["name"], "H-AUTH-1")
        self.assertEqual(stmt["vulnerability"]["description"], "管理员接口未授权越权访问")
        self.assertEqual(stmt["products"], ["POST:/admin/config"])
        self.assertEqual(stmt["impact_statement"], "端点 POST /admin/config 在无凭证下成功放行")
        self.assertEqual(stmt["action_statement"], "在网关层配置强制 JWT 校验中间件")
        self.assertNotIn("justification", stmt)
        self.assertTrue(bool(stmt.get("timestamp")))

    def test_knowledge_card_openvex_statement_not_affected_contract(self) -> None:
        """断言 ②：经验证已拦截的安全事实生成标准 not_affected 声明，且法定包含规范理据"""
        card = KnowledgeCard(
            card_id="KC-AUTH-SAFE-01",
            category="AUTHENTICATION_ENFORCED",
            title="敏感特权路由认证边界坚固",
            claim="端点已严格返回 403 阻断",
            severity="INFO",
            verification_state="REFUTED",
            confidence=1.0,
            source_hypothesis="H-AUTH-1",
            provenance_task="POST:/api/v3/authConf/saveAuth",
            remediation="保持现有鉴权中间件配置",
            evidence_summary="服务端返回 403 业务软拒绝，安全底线坚固",
        )

        stmt = card.to_openvex_statement()

        # 契约断言
        self.assertEqual(stmt["status"], "not_affected")
        self.assertEqual(stmt["justification"], "inline_mitigations_already_exist")
        self.assertEqual(stmt["products"], ["POST:/api/v3/authConf/saveAuth"])
        self.assertIn("保持现有", stmt["action_statement"])

    def test_export_openvex_document_schema_contract(self) -> None:
        """断言 ③：聚合导出的 OpenVEX 文档根对象 100% 契合官方 JSON-LD 规范"""
        card_vuln = KnowledgeCard(
            card_id="KC-VULN-01",
            category="VULNERABILITY",
            title="漏洞发现",
            claim="事实击穿",
            severity="HIGH",
            verification_state="VERIFIED",
            confidence=1.0,
            source_hypothesis="H-1",
            provenance_task="POST:/test",
            remediation="加固",
        )
        card_safe = KnowledgeCard(
            card_id="KC-SAFE-01",
            category="SAFE",
            title="安全防护",
            claim="成功拦截",
            severity="INFO",
            verification_state="REFUTED",
            confidence=1.0,
            source_hypothesis="H-2",
            provenance_task="GET:/test",
            remediation="保持",
        )

        vex_doc = KnowledgePromoter.export_openvex_document(
            cards=[card_vuln, card_safe],
            author="Invar Independent Verifier Prime",
            doc_id="https://invar.local/vex/20260923/test-run",
        )

        # 官方规范顶层 Schema 断言
        self.assertEqual(vex_doc["@context"], "https://openvex.dev/ns/v0.2.0")
        self.assertEqual(vex_doc["@id"], "https://invar.local/vex/20260923/test-run")
        self.assertEqual(vex_doc["author"], "Invar Independent Verifier Prime")
        self.assertEqual(vex_doc["role"], "security-researcher")
        self.assertEqual(vex_doc["version"], 1)
        self.assertEqual(len(vex_doc["statements"]), 2)
        self.assertEqual(vex_doc["statements"][0]["status"], "affected")
        self.assertEqual(vex_doc["statements"][1]["status"], "not_affected")


if __name__ == "__main__":
    unittest.main()
