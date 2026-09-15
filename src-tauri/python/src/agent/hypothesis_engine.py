from typing import List, Set
from harness.invariant_evaluator import InvariantEvaluation
from harness.models import EndpointIR
from harness.research_models import Hypothesis, ResearchCase

IDOR_KEYWORDS: Set[str] = {
    "id", "user_id", "uid", "account_id", "order_id",
    "member_id", "customer_id", "tenant_id", "doc_id"
}


class HypothesisEngine:
    """
    Invar 认知层：安全研究假设自主推演与验证状态机 (Hypothesis Reasoning & Verification Engine)
    负责先验假设推演、用例绑定、以及根据底层不变量事实执行假设证实 (VERIFIED) 与证伪 (REFUTED) 决算
    """

    @classmethod
    def generate_hypotheses(cls, endpoint: EndpointIR) -> List[Hypothesis]:
        hypotheses: List[Hypothesis] = []

        # 1. 越权与属主隔离假设 (IDOR / BOLA)
        matched_id_params = [
            p for p in endpoint.extracted_params
            if any(k in p.lower() for k in IDOR_KEYWORDS)
        ]
        if matched_id_params:
            param_names = ", ".join(matched_id_params)
            hypotheses.append(
                Hypothesis(
                    hypothesis_id="H-IDOR-1",
                    statement="对象标识符参数可能允许跨租户/跨用户越权访问",
                    rationale=f"静态参数提取中检测到直接客户端可控的属主标识符参数 [{param_names}]，后端可能缺失会话鉴权强绑定",
                    status="PROPOSED",
                )
            )

        # 2. 敏感管理路由认证边界假设 (Broken Authentication)
        is_sensitive = (
            "sensitive-route" in endpoint.tags
            or "admin" in endpoint.tags
            or any(
                k in endpoint.path.lower()
                for k in ["admin", "manage", "config", "audit", "private"]
            )
        )
        if is_sensitive:
            hypotheses.append(
                Hypothesis(
                    hypothesis_id="H-AUTH-1",
                    statement="特权管理路由可能缺失有效认证或未强制校验凭证",
                    rationale=f"路径 [{endpoint.path}] 被打上敏感特权路由标签，前端包显式引用可能存在未授权直接放行风险",
                    status="PROPOSED",
                )
            )

        # 3. 高危破坏性动作二次确认防护假设 (Missing Confirmation Guard)
        is_destructive = (
            endpoint.method.upper() == "DELETE"
            or "destructive" in endpoint.tags
            or any(
                k in endpoint.path.lower()
                for k in ["delete", "batch", "drop", "purge", "clear", "remove"]
            )
        )
        if is_destructive:
            hypotheses.append(
                Hypothesis(
                    hypothesis_id="H-DESTRUCT-1",
                    statement="破坏性操作可能在缺失二次确认参数的情况下被直接执行",
                    rationale=f"检测到高危破坏性动作 [{endpoint.method.upper()} {endpoint.path}]，需验证是否存在 confirm 防护校验",
                    status="PROPOSED",
                )
            )

        return hypotheses

    @classmethod
    def attach_to_case(cls, case: ResearchCase) -> ResearchCase:
        """
        为研究案例自动推导并一键绑定候选假设清单
        """
        hypotheses = cls.generate_hypotheses(case.endpoint)
        for h in hypotheses:
            case.add_hypothesis(h)
        return case

    @classmethod
    def resolve_hypotheses(
        cls,
        case: ResearchCase,
        evaluations: List[InvariantEvaluation],
    ) -> List[Hypothesis]:
        """
        将底层不变量事实检验结果对账至用例假设，完成假设生命周期状态跃迁
        """
        resolved: List[Hypothesis] = []
        eval_map = {e.invariant_type: e for e in evaluations}

        for h in case.hypotheses:
            new_status = h.status
            notes = h.evidence_notes

            # 决算破坏性动作假设
            if h.hypothesis_id.startswith("H-DESTRUCT"):
                if "destructive_confirmation" in eval_map:
                    ev = eval_map["destructive_confirmation"]
                    if ev.status == "vulnerable":
                        new_status = "VERIFIED"
                        notes = ev.rationale
                    elif ev.status == "confirmed":
                        new_status = "REFUTED"
                        notes = ev.rationale
                    elif ev.status == "inconclusive":
                        new_status = "INCONCLUSIVE"
                        notes = ev.rationale

            # 决算特权路由认证假设
            elif h.hypothesis_id.startswith("H-AUTH"):
                if "auth_boundary" in eval_map:
                    ev = eval_map["auth_boundary"]
                    if ev.status == "vulnerable":
                        new_status = "VERIFIED"
                        notes = ev.rationale
                    elif ev.status == "confirmed":
                        new_status = "REFUTED"
                        notes = ev.rationale
                    elif ev.status == "inconclusive":
                        new_status = "INCONCLUSIVE"
                        notes = ev.rationale

            resolved.append(
                Hypothesis(
                    hypothesis_id=h.hypothesis_id,
                    statement=h.statement,
                    rationale=h.rationale,
                    status=new_status,
                    evidence_notes=notes,
                )
            )

        case.hypotheses = resolved
        return resolved
