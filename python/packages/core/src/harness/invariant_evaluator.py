import json
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
    def _is_response_denial(cls, response_text: Optional[str]) -> bool:
        """
        判断响应体是否承载了明确的应用层/业务级拒绝拦截语义（软拒绝兜底或前端页面回退）
        """
        if not response_text:
            return False

        # 1. 识别前端单页应用 (SPA) / Nginx 兜底 HTML 页面（非真实后端 API 放行）
        text_strip = response_text.strip().lower()
        if text_strip.startswith("<!doctype html") or text_strip.startswith("<html"):
            return True

        # 2. 识别结构化 JSON 业务拒绝码与语义词
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                code = data.get("code")
                msg = str(data.get("message") or data.get("msg") or "").lower()
                # 命中典型 40xx 客户端/鉴权业务错误码
                if isinstance(code, int) and (code in {401, 403, 4001, 4003, 4008} or 4000 <= code <= 4999):
                    return True
                # 命中明确未授权/拒绝放行语义词
                if any(w in msg for w in [
                    "forbidden", "unauthorized", "invalid reset password token",
                    "invalid token", "not logged in", "未登录", "无权限", "鉴权失败"
                ]):
                    return True
        except Exception:
            pass
        return False

    @classmethod
    def evaluate(
        cls,
        invariant: SecurityInvariant,
        endpoint: EndpointIR,
        status_code: int,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        response_text: Optional[str] = None,
        is_soft_denial: bool = False,
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

            # 若被明确拒绝拦截（401/403 或业务软拒绝/前端兜底页面），则破坏性动作未被执行，底线守住
            if status_code in [401, 403] or is_soft_denial or cls._is_response_denial(response_text):
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale="破坏性操作被服务端安全拦截（鉴权拒绝、业务拦截或前端页面兜底），未发生非预期状态变更",
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
            normalized_headers = {k.lower(): v for k, v in (headers or {}).items()}
            has_auth = any(k in normalized_headers and bool(normalized_headers[k]) for k in AUTH_HEADERS)

            # 分支 A: 服务端明确返回了策略拒绝响应（HTTP 401/403/405、业务软拒绝或前端页面兜底）
            if status_code in [401, 403, 405] or is_soft_denial or cls._is_response_denial(response_text):
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale="服务端返回了严格的未授权拒绝响应 (401/403/405 或业务层拦截/前端页面兜底)，安全边界坚固",
                )

            # 分支 B: 状态码看似成功放行 (200~299) 且未命中拒绝
            if 200 <= status_code <= 299:
                if not has_auth:
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
        response_text: Optional[str] = None,
        is_soft_denial: bool = False,
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
                cls.evaluate(
                    inv,
                    case.endpoint,
                    status_code,
                    payload,
                    headers,
                    response_text=response_text,
                    is_soft_denial=is_soft_denial,
                )
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
