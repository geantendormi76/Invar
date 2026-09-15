import unittest

from harness.models import EndpointIR
from harness.research_models import Hypothesis, ResearchCase


class KnowledgePromoterTests(unittest.TestCase):
    def test_promotes_verified_destruct_hypothesis_into_vulnerability_card(self) -> None:
        from agent.knowledge_promoter import KnowledgeCard, KnowledgePromoter

        endpoint = EndpointIR(method="DELETE", path="/api/orders/batch")
        case = ResearchCase(case_id="DELETE:/api/orders/batch", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-DESTRUCT-1",
                statement="破坏性操作可能缺失二次确认",
                status="VERIFIED",
                evidence_notes="后端在无confirm参数时成功返回200并清空数据",
            )
        )

        cards = KnowledgePromoter.promote_case(case)

        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertIsInstance(card, KnowledgeCard)
        self.assertTrue(card.card_id.startswith("KC-"))
        self.assertEqual(card.category, "DESTRUCTIVE_GUARD_MISSING")
        self.assertEqual(card.severity, "HIGH")
        self.assertEqual(card.verification_state, "VERIFIED")
        self.assertEqual(card.confidence, 1.0)
        self.assertEqual(card.source_hypothesis, "H-DESTRUCT-1")
        self.assertEqual(card.provenance_task, "DELETE:/api/orders/batch")
        self.assertIn("二次确认", card.title)
        self.assertIn("建议在路由中间件中强制拦截", card.remediation)

    def test_promotes_verified_auth_hypothesis_into_critical_card(self) -> None:
        from agent.knowledge_promoter import KnowledgePromoter

        endpoint = EndpointIR(method="GET", path="/api/admin/users")
        case = ResearchCase(case_id="GET:/api/admin/users", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-AUTH-1",
                statement="特权管理路由可能缺失认证",
                status="VERIFIED",
                evidence_notes="未携带Token时后端异常放行返回200",
            )
        )

        cards = KnowledgePromoter.promote_case(case)

        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(card.category, "BROKEN_AUTHENTICATION")
        self.assertEqual(card.severity, "CRITICAL")
        self.assertEqual(card.verification_state, "VERIFIED")
        self.assertIn("强制校验 Authorization", card.remediation)

    def test_promotes_verified_idor_hypothesis_into_high_card(self) -> None:
        from agent.knowledge_promoter import KnowledgeCard, KnowledgePromoter

        endpoint = EndpointIR(method="GET", path="/api/orders/detail", extracted_params=["order_id"])
        case = ResearchCase(case_id="GET:/api/orders/detail", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-IDOR-1",
                statement="对象标识符参数可能允许跨租户/跨用户越权访问",
                status="VERIFIED",
                evidence_notes="攻击者成功获取受害者资源，响应相似度达 1.00，存在水平越权 (IDOR / BOLA) 漏洞",
            )
        )

        cards = KnowledgePromoter.promote_case(case)

        self.assertEqual(len(cards), 1, "未经验证的提炼门禁或未实现 H-IDOR 知识卡片晋级")
        card = cards[0]
        self.assertIsInstance(card, KnowledgeCard)
        self.assertEqual(card.category, "BOLA_IDOR_VULNERABILITY")
        self.assertEqual(card.severity, "HIGH")
        self.assertEqual(card.verification_state, "VERIFIED")
        self.assertIn("水平越权", card.title)
        self.assertIn("数据访问层", card.remediation)

    def test_promotion_gate_blocks_unverified_proposed_hypotheses(self) -> None:
        from agent.knowledge_promoter import KnowledgePromoter

        endpoint = EndpointIR(method="GET", path="/api/orders")
        case = ResearchCase(case_id="GET:/api/orders", endpoint=endpoint)
        case.add_hypothesis(
            Hypothesis(
                hypothesis_id="H-IDOR-1",
                statement="可能存在越权",
                status="PROPOSED",  # 仅仅是推测，尚未被事实证实
                evidence_notes="",
            )
        )

        cards = KnowledgePromoter.promote_case(case)

        # 门禁铁律：未经验证的假设绝对不能晋级为知识卡片！
        self.assertEqual(len(cards), 0)

    def test_knowledge_card_supports_structured_serialization(self) -> None:
        from agent.knowledge_promoter import KnowledgeCard

        card = KnowledgeCard(
            card_id="KC-TEST-001",
            category="TEST_CATEGORY",
            title="测试标题",
            claim="测试断言",
            severity="MEDIUM",
            verification_state="VERIFIED",
            confidence=1.0,
            source_hypothesis="H-TEST-1",
            provenance_task="TEST:/api/test",
            remediation="测试修复建议",
            evidence_summary="测试证据摘要",
        )

        data = card.to_dict()

        self.assertEqual(data["card_id"], "KC-TEST-001")
        self.assertEqual(data["category"], "TEST_CATEGORY")
        self.assertEqual(data["severity"], "MEDIUM")
        self.assertEqual(data["provenance_task"], "TEST:/api/test")
