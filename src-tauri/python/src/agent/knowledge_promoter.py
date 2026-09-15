from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from harness.research_models import ResearchCase


@dataclass(frozen=True)
class KnowledgeCard:
    """
    Invar 经验证不可变安全知识卡片 (Promoted Knowledge Card)
    从已被实锤证实的科研假设与证据链中提炼出的高置信度事实与治理指引
    """
    card_id: str
    category: str
    title: str
    claim: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    verification_state: str  # "VERIFIED", "REFUTED"
    confidence: float
    source_hypothesis: str
    provenance_task: str
    remediation: str
    evidence_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class KnowledgePromoter:
    """
    Invar 安全知识晋级器 (Security Knowledge Promoter)
    设立严格的科学证据晋级门禁 (Promotion Gate)，将已裁决的假设升华收敛为标准知识卡片
    """

    @classmethod
    def promote_case(cls, case: ResearchCase) -> List[KnowledgeCard]:
        cards: List[KnowledgeCard] = []

        for h in case.hypotheses:
            # 晋级门禁铁律：只有被事实裁决证实 (VERIFIED) 或证伪 (REFUTED) 的假设才允许晋级！
            if h.status not in {"VERIFIED", "REFUTED"}:
                continue

            # 1. 提炼破坏性操作确认防护知识
            if h.hypothesis_id.startswith("H-DESTRUCT"):
                if h.status == "VERIFIED":
                    card = KnowledgeCard(
                        card_id=f"KC-DESTRUCT-{case.case_id}",
                        category="DESTRUCTIVE_GUARD_MISSING",
                        title="破坏性操作缺失二次确认防护",
                        claim=f"端点 [{case.endpoint.method} {case.endpoint.path}] 允许在未提供确认参数 (confirm/csrf) 的情况下直接执行破坏性动作",
                        severity="HIGH",
                        verification_state="VERIFIED",
                        confidence=1.0,
                        source_hypothesis=h.hypothesis_id,
                        provenance_task=case.case_id,
                        remediation="建议在路由中间件中强制拦截缺失 confirm 或二次验证令牌的破坏性请求",
                        evidence_summary=h.evidence_notes,
                    )
                    cards.append(card)
                elif h.status == "REFUTED":
                    card = KnowledgeCard(
                        card_id=f"KC-DESTRUCT-SAFE-{case.case_id}",
                        category="DESTRUCTIVE_GUARD_VERIFIED",
                        title="破坏性操作二次确认防护坚固",
                        claim=f"端点 [{case.endpoint.method} {case.endpoint.path}] 已有效强制执行二次确认校验",
                        severity="INFO",
                        verification_state="REFUTED",
                        confidence=1.0,
                        source_hypothesis=h.hypothesis_id,
                        provenance_task=case.case_id,
                        remediation="保持现有确认防护中间件配置",
                        evidence_summary=h.evidence_notes,
                    )
                    cards.append(card)

            # 2. 提炼敏感特权路由认证边界知识
            elif h.hypothesis_id.startswith("H-AUTH"):
                if h.status == "VERIFIED":
                    card = KnowledgeCard(
                        card_id=f"KC-AUTH-{case.case_id}",
                        category="BROKEN_AUTHENTICATION",
                        title="敏感特权路由缺失认证鉴权",
                        claim=f"端点 [{case.endpoint.method} {case.endpoint.path}] 在未携带有效凭证时被异常放行",
                        severity="CRITICAL",
                        verification_state="VERIFIED",
                        confidence=1.0,
                        source_hypothesis=h.hypothesis_id,
                        provenance_task=case.case_id,
                        remediation="建议在路由拦截器中强制校验 Authorization 身份凭证并严密核验 JWT 签名",
                        evidence_summary=h.evidence_notes,
                    )
                    cards.append(card)
                elif h.status == "REFUTED":
                    card = KnowledgeCard(
                        card_id=f"KC-AUTH-SAFE-{case.case_id}",
                        category="AUTHENTICATION_ENFORCED",
                        title="敏感特权路由认证边界坚固",
                        claim=f"端点 [{case.endpoint.method} {case.endpoint.path}] 已有效执行严格的 401/403 鉴权拦截",
                        severity="INFO",
                        verification_state="REFUTED",
                        confidence=1.0,
                        source_hypothesis=h.hypothesis_id,
                        provenance_task=case.case_id,
                        remediation="保持现有鉴权中间件配置",
                        evidence_summary=h.evidence_notes,
                    )
                    cards.append(card)

            # 3. 提炼水平越权 / 属主鉴权隔离知识 (BOLA / IDOR)
            elif h.hypothesis_id.startswith("H-IDOR"):
                if h.status == "VERIFIED":
                    card = KnowledgeCard(
                        card_id=f"KC-IDOR-{case.case_id}",
                        category="BOLA_IDOR_VULNERABILITY",
                        title="对象级属主鉴权缺失 (BOLA / IDOR 水平越权)",
                        claim=f"端点 [{case.endpoint.method} {case.endpoint.path}] 允许攻击者跨租户/跨主体直接访问受害者对象资源",
                        severity="HIGH",
                        verification_state="VERIFIED",
                        confidence=1.0,
                        source_hypothesis=h.hypothesis_id,
                        provenance_task=case.case_id,
                        remediation="建议在服务端业务逻辑与数据访问层 (DAL) 强制校验当前会话主体与请求目标对象标识符的属主绑定关系",
                        evidence_summary=h.evidence_notes,
                    )
                    cards.append(card)
                elif h.status == "REFUTED":
                    card = KnowledgeCard(
                        card_id=f"KC-IDOR-SAFE-{case.case_id}",
                        category="BOLA_IDOR_ENFORCED",
                        title="对象级属主访问控制坚固",
                        claim=f"端点 [{case.endpoint.method} {case.endpoint.path}] 已有效实施租户与属主隔离，越权探测未发生数据泄露",
                        severity="INFO",
                        verification_state="REFUTED",
                        confidence=1.0,
                        source_hypothesis=h.hypothesis_id,
                        provenance_task=case.case_id,
                        remediation="保持现有属主访问控制逻辑",
                        evidence_summary=h.evidence_notes,
                    )
                    cards.append(card)

        return cards
