from harness.domain_contracts import EvidenceSufficiency
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
    sufficiency: EvidenceSufficiency = EvidenceSufficiency.SUFFICIENT


class InvariantEvaluator:
    """
    Invar 安全不变量逻辑评估引擎 (Security Invariant Evaluator)
    基于接口静态特征与探测事实，对声明的安全不变量执行确定性断言
    对齐黄金标准：严格维持证据事实 (Physical Evidence) 与裁决解释 (Rationale) 的单射映射
    """

    @classmethod
    def _is_html_fallback(cls, response_text: Optional[str]) -> bool:
        if not response_text:
            return False
        text_strip = response_text.strip().lower()
        return text_strip.startswith("<!doctype html") or text_strip.startswith("<html")

    @classmethod
    def _is_business_soft_denial(cls, response_text: Optional[str]) -> bool:
        if not response_text:
            return False
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                code = data.get("code")
                msg = str(data.get("message") or data.get("msg") or "").lower()
                if isinstance(code, int) and (code in {401, 403, 4001, 4003, 4008} or 4000 <= code <= 4999):
                    return True
                if any(w in msg for w in [
                    "forbidden", "unauthorized", "invalid reset password token",
                    "invalid token", "not logged in", "未登录", "无权限", "鉴权失败"
                ]):
                    return True
        except Exception:
            pass
        return False

    @classmethod
    def _is_response_denial(cls, response_text: Optional[str]) -> bool:
        return cls._is_html_fallback(response_text) or cls._is_business_soft_denial(response_text)

    @classmethod
    def _resolve_denial_rationale(
        cls,
        status_code: int,
        is_soft_denial: bool,
        response_text: Optional[str],
        prefix: str = "",
    ) -> str:
        """
        根据底层物理观测事实，精准装配单射、客观的证据裁决理据
        杜绝混合大杂烩模版与主观过度推断
        """
        pfx = f"{prefix}: " if prefix else ""
        if status_code == 403:
            return f"{pfx}服务端返回 HTTP 403 [access_policy_denial] 访问控制拒绝响应，未观察到未授权特权操作在当前测试上下文成功执行"
        if status_code == 401:
            return f"{pfx}服务端返回 HTTP 401 [authentication_required] 身份鉴权缺失响应，目标操作明确受访问控制屏障保护"
        if is_soft_denial or cls._is_business_soft_denial(response_text):
            return f"{pfx}应用层返回业务拒绝事实 [business_soft_denial]，未授权请求被业务逻辑有效拦截"
        if cls._is_html_fallback(response_text):
            return f"{pfx}服务端返回前端网关兜底页面 [gateway_fallback_html]，未触达并暴露后端敏感 API 逻辑"
        return f"{pfx}服务端返回拒绝响应 [status_code={status_code}]，目标操作未被放行"

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
        is_auth_differential: bool = False,
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

            # 若被明确拒绝拦截（401/403 或业务软拒绝/前端兜底页面），破坏性动作未被执行，底线守住
            if status_code in [401, 403] or is_soft_denial or (status_code == 200 and cls._is_response_denial(response_text)):
                rationale_text = cls._resolve_denial_rationale(
                    status_code,
                    is_soft_denial,
                    response_text,
                    prefix="破坏性操作被服务端安全拦截",
                )
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale=rationale_text,
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

            # 分支 A1: 动词策略拦截 (RFC 9110 HTTP 405) —— 局部证据 (PARTIAL)
            if status_code == 405:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale="服务端在动词策略层实施拒绝拦截 (HTTP 405 Method Not Allowed)，未暴露特权操作接口",
                    sufficiency=EvidenceSufficiency.PARTIAL,
                )

            # 分支 A2: 显式权限拒绝 (HTTP 401/403 或业务软拒绝/页面兜底) —— 充分证据 (SUFFICIENT)
            if status_code in [401, 403] or is_soft_denial or (status_code == 200 and cls._is_response_denial(response_text)):
                rationale_text = cls._resolve_denial_rationale(
                    status_code,
                    is_soft_denial,
                    response_text,
                )
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="confirmed",
                    rationale=rationale_text,
                    sufficiency=EvidenceSufficiency.SUFFICIENT,
                )

            # 分支 B: 状态码成功放行区间 (200~299)
            if 200 <= status_code <= 299:
                if not has_auth:
                    return InvariantEvaluation(
                        invariant_type=inv_type,
                        status="vulnerable",
                        rationale="敏感特权路由在未携带有效凭证时被异常放行，安全不变量被击穿",
                        sufficiency=EvidenceSufficiency.SUFFICIENT,
                    )
                else:
                    return InvariantEvaluation(
                        invariant_type=inv_type,
                        status="confirmed",
                        rationale="认证边界受控，未发现越权放行",
                        sufficiency=EvidenceSufficiency.SUFFICIENT,
                    )
            elif status_code == 404:
                norm_headers = {k.lower(): v for k, v in (headers or {}).items()}
                has_www_auth = any(k in norm_headers for k in ["www-authenticate", "x-auth-realm", "x-security-policy", "x-security-denial"])
                if has_www_auth or is_auth_differential:
                    if is_auth_differential:
                        return InvariantEvaluation(
                            invariant_type=inv_type,
                            status="confirmed",
                            rationale="服务端返回 HTTP 404 [hidden_by_authz] 经差分对照实锤目标资源受鉴权策略隐匿保护，安全底线守住",
                            sufficiency=EvidenceSufficiency.SUFFICIENT,
                        )
                    return InvariantEvaluation(
                        invariant_type=inv_type,
                        status="inconclusive",
                        rationale="服务端返回 HTTP 404 [hidden_by_authz] 观察到鉴权隐匿相关特征标头，但当前单变量证据不足以证明其由授权层必然产生，裁决收敛为存疑待验",
                        sufficiency=EvidenceSufficiency.PARTIAL,
                    )

                path_str = endpoint.path or ""
                resp_text = (response_text or "").lower()
                is_template = (
                    "${" in path_str or "{" in path_str
                    or ":" in path_str.split("/")[-1]
                    or "nosuchkey" in resp_text
                    or "does not exist" in resp_text
                    or "user not found" in resp_text
                    or '"code": 404' in resp_text
                    or '"code":404' in resp_text
                )
                if is_template:
                    return InvariantEvaluation(
                        invariant_type=inv_type,
                        status="inconclusive",
                        rationale="服务端返回 HTTP 404 [resource_not_found] 资源实体未决，存在未实例化的模板变量或目标业务对象不存在",
                        sufficiency=EvidenceSufficiency.INSUFFICIENT,
                    )

                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="inconclusive",
                    rationale="服务端返回 HTTP 404 [route_not_found] 路由不存在，目标 API 未在该网关/节点暴露",
                    sufficiency=EvidenceSufficiency.INSUFFICIENT,
                )
            else:
                return InvariantEvaluation(
                    invariant_type=inv_type,
                    status="inconclusive",
                    rationale=f"服务端返回状态码 [{status_code}]，无法直接证明认证不变量是否违背",
                    sufficiency=EvidenceSufficiency.INSUFFICIENT,
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
                sufficiency=EvidenceSufficiency.SUFFICIENT,
            )
            case.set_decision(decision)
            return decision

        inconclusive_evals = [e for e in effective_evaluations if e.status == "inconclusive"]
        if inconclusive_evals:
            decision = ResearchDecision(
                status="inconclusive",
                rationale="; ".join(e.rationale for e in inconclusive_evals),
                sufficiency=EvidenceSufficiency.INSUFFICIENT,
            )
            case.set_decision(decision)
            return decision

        # confirmed 场景的证据充分性聚合：若含有 PARTIAL 则整单判定为 PARTIAL，否则为 SUFFICIENT
        eff_sufficiency = EvidenceSufficiency.SUFFICIENT
        if any(e.sufficiency == EvidenceSufficiency.PARTIAL for e in effective_evaluations):
            eff_sufficiency = EvidenceSufficiency.PARTIAL

        decision = ResearchDecision(
            status="confirmed",
            rationale="; ".join(e.rationale for e in effective_evaluations),
            sufficiency=eff_sufficiency,
        )
        case.set_decision(decision)
        return decision
