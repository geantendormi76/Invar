from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from harness.finding_models import FindingRecord
from harness.research_models import ResearchCase
from harness.verification_gate import PromotionGate


@dataclass(frozen=True)
class KnowledgeCard:
    """
    Invar 经验证不可变安全知识卡片 (Promoted Knowledge Card)
    从已被独立复核实锤证实的 FindingRecord 与科研假设中升华出的高置信度事实与治理指引
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
    设立严格的科学证据晋级门禁 (Promotion Gate)，将已裁决且经独立复核的事实升华为标准知识卡片
    """

    @classmethod
    def promote_finding(
        cls,
        finding: FindingRecord,
        gate: Optional[PromotionGate] = None,
    ) -> KnowledgeCard:
        """
        [Phase M6 新通道] 严格通过 PromotionGate 校验后，将结构化 FindingRecord 晋升为 KnowledgeCard
        """
        active_gate = gate or PromotionGate()
        active_gate.assert_promotable(finding)

        cat_part = "VULNERABILITY"
        if finding.fingerprint and ":" in finding.fingerprint:
            parts = finding.fingerprint.split(":")
            cat_part = parts[1].upper() if len(parts) > 1 else "VULNERABILITY"

        endpoints_str = ", ".join(finding.endpoint_refs) if finding.endpoint_refs else "Target Service"
        remedy_text = finding.remediation.guidance if finding.remediation else "建议实施细粒度访问控制与输入校验"

        return KnowledgeCard(
            card_id=f"KC-{finding.fingerprint}",
            category=cat_part,
            title=finding.title,
            claim=f"端点 [{endpoints_str}] 经证实存在安全漏洞: {finding.root_cause}",
            severity=finding.severity.value if finding.severity else "HIGH",
            verification_state="VERIFIED",
            confidence=1.0,
            source_hypothesis=finding.hypothesis_refs[0] if finding.hypothesis_refs else finding.fingerprint,
            provenance_task=finding.endpoint_refs[0] if finding.endpoint_refs else finding.finding_id,
            remediation=remedy_text,
            evidence_summary=f"已通过独立复核 [{finding.verification.verifier_id}]，物理证据链: {', '.join(finding.evidence_refs)}",
        )

    @classmethod
    def promote_case(cls, case: ResearchCase) -> List[KnowledgeCard]:
        """
        [向后兼容模式] 针对纯 ResearchCase 假设的直升通道
        """
        cards: List[KnowledgeCard] = []

        for h in case.hypotheses:
            if h.status not in {"VERIFIED", "REFUTED"}:
                continue

            if h.hypothesis_id.startswith("H-DESTRUCT"):
                if h.status == "VERIFIED":
                    cards.append(KnowledgeCard(
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
                    ))
                elif h.status == "REFUTED":
                    cards.append(KnowledgeCard(
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
                    ))

            elif h.hypothesis_id.startswith("H-AUTH"):
                if h.status == "VERIFIED":
                    cards.append(KnowledgeCard(
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
                    ))
                elif h.status == "REFUTED":
                    cards.append(KnowledgeCard(
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
                    ))

            elif h.hypothesis_id.startswith("H-IDOR"):
                if h.status == "VERIFIED":
                    cards.append(KnowledgeCard(
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
                    ))
                elif h.status == "REFUTED":
                    cards.append(KnowledgeCard(
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
                    ))

        return cards
