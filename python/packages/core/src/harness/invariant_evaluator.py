from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from harness.models import EndpointIR
from harness.research_models import ResearchCase, ResearchDecision, SecurityInvariant

CONFIRMATION_KEYS = {"confirm", "confirmation_token", "force", "csrf", "csrf_token"}
DESTRUCTIVE_METHODS = {"DELETE"}
DESTRUCTIVE_PATH_KEYWORDS = {"delete", "batch", "drop", "purge", "clear", "remove"}
AUTH_HEADERS = {"authorization", "x-auth-token", "token"}


@dataclass(frozen=True)
class InvariantEvaluation:
    """
    单条安全不变量检验结果事实
    """
    invariant_type: str
    status: str  # "confirmed" (底线守住), "vulnerable" (底线被击穿), "inconclusive" (证据不足)
    rationale: str


class InvariantEvaluator:
    """
    Invar 安全不变量逻辑评估引擎 (Security Invariant Evaluator)
    基于接口静态特征与探测事实，对声明的安全不变量执行确定性断言
    """

    @classmethod
    def evaluate(
        cls,
        invariant: SecurityInvariant,
        endpoint: EndpointIR,
        status_code: int,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> InvariantEvaluation:
        inv_type = invariant.invariant_type

        # 1. 破坏性操作二次确认不变量
        if inv_type == "destructive_confirmation":
            is_destructive = (
                endpoint.method.upper() in DESTRUCTIVE_METHODS
                or "destructive" in endpoint.tags
                or any(k in endpoint.path.lower() for k in DESTRUCTIVE_PATH_KEYWORDS)
            )

            if not is_destructive:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale="非破坏性端点，不要求二次确认防护",
                )

            has_confirm = any(k in payload for k in CONFIRMATION_KEYS)
            if not has_confirm and (200 <= status_code <= 299):
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="vulnerable",
                    rationale="破坏性操作在缺失确认参数的情况下被成功执行，安全不变量被击穿",
                )
            else:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale="破坏性操作携带了合法的确认字段或被服务端拦截，安全不变量成立",
                )

        # 2. 敏感路由认证与授权边界不变量
        elif inv_type == "auth_boundary":
            is_sensitive = (
                "sensitive-route" in endpoint.tags
                or "admin" in endpoint.tags
                or any(k in endpoint.path.lower() for k in ["admin", "private", "manage"])
            )

            normalized_headers = {k.lower(): v for k, v in (headers or {}).items()}
            has_auth = any(k in normalized_headers and bool(normalized_headers[k]) for k in AUTH_HEADERS)

            if 200 <= status_code <= 299:
                if not has_auth and is_sensitive:
                    return InvariantEvaluation(
                        invariant_type=inv_type,
                        status="vulnerable",
                        rationale="敏感特权路由在未携带有效凭证时被异常放行，安全不变量被击穿",
                    )
                else:
                    return InvariantEvaluation(
                        invariant_type=inv_type,
                        status="confirmed",
                        rationale="认证边界受控，未发现越权放行",
                    )
            elif status_code in [401, 403]:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale="服务端返回了严格的未授权拒绝响应 (401/403)，安全边界坚固",
                )
            else:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="inconclusive",
                    rationale=f"服务端返回状态码 [{status_code}]，无法直接证明认证不变量是否违背",
                )

        return InvariantEvaluation(
            invariant_type=inv_type,
            status="inconclusive",
            rationale=f"未识别的不变量类型: {inv_type}",
        )

    @classmethod
    def evaluate_case(
        cls,
        case: ResearchCase,
        status_code: int,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        evaluations: Optional[List[InvariantEvaluation]] = None,
    ) -> Optional[ResearchDecision]:
        """
        对 ResearchCase 挂载的全部安全不变量执行综合评估，合成全局 ResearchDecision
        可直接接收外部专业算子 (如 IdorCompareOperator) 的既成评估事实列表
        """
        if not case.invariants:
            return None

        effective_evaluations = evaluations
        if effective_evaluations is None:
            effective_evaluations = [
                cls.evaluate(inv, case.endpoint, status_code, payload, headers)
                for inv in case.invariants
            ]

        # 优先级：vulnerable (击穿) > inconclusive (存疑) > confirmed (安全)
        vulnerable_evals = [e for e in effective_evaluations if e.status == "vulnerable"]
        if vulnerable_evals:
            decision = ResearchDecision(
                status="vulnerable",
                rationale="; ".join(e.rationale for e in vulnerable_evals),
            )
            case.set_decision(decision)
            return decision

        inconclusive_evals = [e for e in effective_evaluations if e.status == "inconclusive"]
        if inconclusive_evals:
            decision = ResearchDecision(
                status="inconclusive",
                rationale="; ".join(e.rationale for e in inconclusive_evals),
            )
            case.set_decision(decision)
            return decision

        decision = ResearchDecision(
            status="confirmed",
            rationale="; ".join(e.rationale for e in effective_evaluations),
        )
        case.set_decision(decision)
        return decision
