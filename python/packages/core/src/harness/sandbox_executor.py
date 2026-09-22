from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from agent.hypothesis_engine import HypothesisEngine, IDOR_KEYWORDS
from harness.config import InvarConfig
from harness.evidence import EvidenceRecord, HTTPRequestLog, HTTPResponseLog
from harness.feedback import FeedbackInterpreter
from harness.idor_compare import IdorCompareOperator
from harness.invariant_evaluator import InvariantEvaluation, InvariantEvaluator
from harness.method_tamper import MethodTamperOperator
from harness.models import EndpointIR
from harness.mutation_policy import MutationPolicy
from harness.research_evidence import ProbeAttemptEvidenceMapper
from harness.research_models import ResearchCase, ResearchExecutionResult, SecurityInvariant
from harness.transport import HttpTransport


class AdaptiveSandboxExecutor:
    def __init__(
        self,
        cfg: Optional[InvarConfig] = None,
        transport: Optional[HttpTransport] = None,
        feedback_interpreter: Optional[FeedbackInterpreter] = None,
        mutation_policy: Optional[MutationPolicy] = None,
    ) -> None:
        self.cfg = cfg or InvarConfig()
        self.transport = transport or HttpTransport()
        self.feedback_interpreter = (
            feedback_interpreter or FeedbackInterpreter()
        )
        self.mutation_policy = mutation_policy or MutationPolicy()

    def _build_initial_payload(self, endpoint: EndpointIR) -> Dict[str, object]:
        payload: Dict[str, object] = {}
        for param in endpoint.extracted_params:
            payload[param] = self.mutation_policy.infer_default_value(param)
        return payload

    def _build_url(
        self,
        endpoint: EndpointIR,
        base_url: Optional[str] = None,
    ) -> str:
        effective_base_url = (
            base_url
            if base_url is not None and base_url.strip()
            else self.cfg.target_api_base
        )
        return (
            f"{effective_base_url.rstrip('/')}/"
            f"{endpoint.path.lstrip('/')}"
        )

    def _create_research_case(self, endpoint: EndpointIR) -> ResearchCase:
        case = ResearchCase(
            case_id=f"{endpoint.method.upper()}:{endpoint.path}",
            endpoint=endpoint,
            metadata={"engine": "AdaptiveSandboxExecutor"},
        )

        # 1. 自动注入破坏性操作确认不变量
        is_destructive = (
            endpoint.method.upper() == "DELETE"
            or "destructive" in endpoint.tags
            or any(
                k in endpoint.path.lower()
                for k in ["delete", "batch", "drop", "purge", "clear", "remove"]
            )
        )
        if is_destructive:
            case.add_invariant(
                SecurityInvariant(
                    invariant_type="destructive_confirmation",
                    statement="Destructive actions must require explicit confirmation",
                )
            )

        # 2. 自动注入敏感管理路由认证边界不变量
        is_sensitive = (
            "sensitive-route" in endpoint.tags
            or "admin" in endpoint.tags
            or any(
                k in endpoint.path.lower()
                for k in ["admin", "private", "manage"]
            )
        )
        if is_sensitive:
            case.add_invariant(
                SecurityInvariant(
                    invariant_type="auth_boundary",
                    statement="Sensitive administration routes must enforce authentication",
                )
            )

        # 3. 自动注入水平越权隔离不变量 (若配置了攻击者凭证且提取到属主标识符参数)
        has_idor_param = any(
            any(k in p.lower() for k in IDOR_KEYWORDS)
            for p in endpoint.extracted_params
        )
        if has_idor_param and self.cfg.auth_token_b:
            case.add_invariant(
                SecurityInvariant(
                    invariant_type="idor_boundary",
                    statement="Object identifiers must enforce cross-tenant authorization",
                )
            )

        # 4. 认知层自主推演：自动注入先验科研假设清单 (PROPOSED)
        HypothesisEngine.attach_to_case(case)

        return case

    def _probe_endpoint_with_research_case(
        self,
        endpoint: EndpointIR,
        base_url: Optional[str] = None,
    ) -> ResearchExecutionResult:
        url = self._build_url(endpoint, base_url=base_url)
        headers = dict(self.cfg.custom_headers)
        payload = self._build_initial_payload(endpoint)
        research_case = self._create_research_case(endpoint)
        last_response = None

        # 阶段 1：主体 A 基线与自适应报错变异发包循环
        for _ in range(int(self.cfg.max_mutation_rounds)):
            try:
                response = self.transport.request(
                    method=endpoint.method,
                    url=url,
                    payload=payload,
                    headers=headers,
                    timeout=self.cfg.request_timeout,
                )
            except Exception as exc:
                evidence = EvidenceRecord(
                    endpoint=endpoint,
                    request=HTTPRequestLog(
                        method=endpoint.method.upper(),
                        url=url,
                        headers=headers,
                        body=payload,
                    ),
                    response=HTTPResponseLog(
                        status_code=0,
                        headers={},
                        body_preview="",
                    ),
                    timestamp="",
                    finding_type="TRANSPORT_ERROR",
                    is_anomaly=True,
                    notes=str(exc),
                )
                return ResearchExecutionResult(
                    evidence=evidence,
                    research_case=research_case,
                    evidence_history=[],
                )

            last_response = response
            feedback = self.feedback_interpreter.interpret(
                response.status_code,
                response.text,
            )

            contract_passed = (
                response.status_code in {200, 201, 204}
                or (
                    response.status_code in {400, 404}
                    and not feedback.has_required_field_error
                    and not feedback.has_unmarshal_error
                )
            )

            if contract_passed:
                research_case.record_attempt(
                    payload=payload,
                    status_code=response.status_code,
                    response_preview=response.text[:500],
                    interpretation="契约结果达到收敛条件",
                    mutation_reason="",
                )
                break

            mutation = self.mutation_policy.mutate(payload, feedback)

            if mutation.changed:
                research_case.record_attempt(
                    payload=payload,
                    status_code=response.status_code,
                    response_preview=response.text[:500],
                    interpretation="反馈包含可识别变异线索",
                    mutation_reason=mutation.reason,
                )
                payload = mutation.payload
                continue

            research_case.record_attempt(
                payload=payload,
                status_code=response.status_code,
                response_preview=response.text[:500],
                interpretation="无进一步变异线索，探针收敛",
                mutation_reason=mutation.reason,
            )
            break

        if not research_case.attempts:
            evidence = EvidenceRecord(
                endpoint=endpoint,
                request=HTTPRequestLog(
                    method=endpoint.method.upper(),
                    url=url,
                    headers=headers,
                    body=payload,
                ),
                response=HTTPResponseLog(
                    status_code=0,
                    headers={},
                    body_preview="",
                ),
                timestamp="",
                finding_type="ENDPOINT_PROBE",
                is_anomaly=False,
                notes=f"research_case={research_case.case_id} | attempts=0",
            )
            return ResearchExecutionResult(
                evidence=evidence,
                research_case=research_case,
                evidence_history=[],
            )

        last_status_code = last_response.status_code if last_response is not None else 0

        # 阶段 1.5：403/405 遭遇战 - 触发动词篡改与隧道穿透 (Method Tamper Operator)
        is_destruct_or_auth = any(
            h.hypothesis_id.startswith(("H-DESTRUCT", "H-AUTH"))
            for h in research_case.hypotheses
        )
        if last_status_code in {403, 405} and is_destruct_or_auth:
            carrier_method = "POST" if endpoint.method.upper() != "POST" else "POST"
            target_verb = endpoint.method.upper()
            variants = MethodTamperOperator.generate_variants(
                method=carrier_method,
                url=url,
                headers=headers,
                payload=payload,
                target_verb=target_verb,
            )

            for variant in variants:
                try:
                    resp_tampered = self.transport.request(
                        method=variant.method,
                        url=variant.url,
                        payload=variant.payload,
                        headers=variant.headers,
                        timeout=self.cfg.request_timeout,
                    )
                    # 一旦穿透返回 200~299，说明成功逃逸 WAF/代理限制！
                    if 200 <= resp_tampered.status_code <= 299:
                        last_response = resp_tampered
                        last_status_code = resp_tampered.status_code
                        research_case.record_attempt(
                            payload=variant.payload,
                            status_code=resp_tampered.status_code,
                            response_preview=resp_tampered.text[:500],
                            interpretation=f"动词隧道穿透成功 ({variant.strategy}: {variant.variant_id})",
                            mutation_reason="WAF 动词语义错位逃逸重试",
                        )
                        break
                except Exception:
                    continue

        # 阶段 2：双主体差分测试 (BOLA / IDOR 对照实验)
        idor_eval: Optional[InvariantEvaluation] = None
        has_idor_inv = any(inv.invariant_type == "idor_boundary" for inv in research_case.invariants)

        if has_idor_inv and self.cfg.auth_token_b and last_response is not None and (200 <= last_status_code <= 299):
            headers_b = dict(headers)
            headers_b["Authorization"] = f"Bearer {self.cfg.auth_token_b}"
            try:
                response_b = self.transport.request(
                    method=endpoint.method,
                    url=url,
                    payload=payload,
                    headers=headers_b,
                    timeout=self.cfg.request_timeout,
                )
                research_case.record_attempt(
                    payload=payload,
                    status_code=response_b.status_code,
                    response_preview=response_b.text[:500],
                    interpretation="双主体越权对照探针 (Subject B)",
                    mutation_reason="执行 BOLA/IDOR 双盲差异对比",
                )
                idor_eval = IdorCompareOperator.compare(
                    victim_response_text=last_response.text,
                    attacker_response_text=response_b.text,
                    attacker_status_code=response_b.status_code,
                )
            except Exception as exc:
                idor_eval = InvariantEvaluation(
                    invariant_type="idor_boundary",
                    status="inconclusive",
                    rationale=f"主体 B 越权探针发包异常: {str(exc)}",
                )

        # 阶段 3：安全不变量综合评估与假说流转
        evaluations: List[InvariantEvaluation] = []
        for inv in research_case.invariants:
            if inv.invariant_type == "idor_boundary":
                if idor_eval is not None:
                    evaluations.append(idor_eval)
                else:
                    evaluations.append(
                        InvariantEvaluation(
                            invariant_type="idor_boundary",
                            status="inconclusive",
                            rationale="未执行双主体对照或基线响应未收敛",
                        )
                    )
            else:
                evaluations.append(
                    InvariantEvaluator.evaluate(
                        inv,
                        research_case.endpoint,
                        last_status_code,
                        payload,
                        headers,
                    )
                )

        # 驱动假设状态机流转：PROPOSED -> VERIFIED / REFUTED
        HypothesisEngine.resolve_hypotheses(research_case, evaluations)

        # 合成全局综合决断
        decision = InvariantEvaluator.evaluate_case(
            case=research_case,
            status_code=last_status_code,
            payload=payload,
            headers=headers,
            evaluations=evaluations,
        )

        evidence_history = ProbeAttemptEvidenceMapper.to_evidence_records(
            research_case=research_case,
            url=url,
            headers=headers,
        )

        if last_response is not None and evidence_history:
            evidence_history[-1].response.headers = dict(
                last_response.headers
            )

        final_evidence = evidence_history[-1]

        # 若判定不变量被击穿，升级证据状态
        if decision is not None and decision.status == "vulnerable":
            final_evidence.is_anomaly = True
            final_evidence.finding_type = "VULNERABILITY_FOUND"
            final_evidence.notes = f"{final_evidence.notes} | [VULNERABILITY] {decision.rationale}"

        return ResearchExecutionResult(
            evidence=final_evidence,
            research_case=research_case,
            evidence_history=evidence_history,
        )

    def probe_endpoint_with_research(
        self,
        endpoint: EndpointIR,
        base_url: Optional[str] = None,
    ) -> ResearchExecutionResult:
        return self._probe_endpoint_with_research_case(
            endpoint,
            base_url=base_url,
        )

    def probe_endpoint(
        self,
        endpoint: EndpointIR,
        base_url: Optional[str] = None,
    ) -> EvidenceRecord:
        result = self._probe_endpoint_with_research_case(
            endpoint,
            base_url=base_url,
        )
        return result.evidence

    def probe_all(
        self,
        endpoints: List[EndpointIR],
        base_url: Optional[str] = None,
    ) -> List[EvidenceRecord]:
        results: List[EvidenceRecord] = []

        with ThreadPoolExecutor(
            max_workers=self.cfg.max_concurrent_workers
        ) as executor:
            future_map = {
                executor.submit(
                    self.probe_endpoint,
                    endpoint,
                    base_url,
                ): endpoint
                for endpoint in endpoints
            }

            for future in as_completed(future_map):
                results.append(future.result())

        return results
