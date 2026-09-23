from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from agent.hypothesis_engine import HypothesisEngine, IDOR_KEYWORDS
from agent.model_provider import OpenAICompatibleProvider
from agent.research_agent import ResearchAgent
from harness.adaptive_selector import AdaptiveExperimentSelector
from harness.config import InvarConfig
from harness.denial_models import DenialObservation, DeterministicDenialClassifier
from harness.evidence import EvidenceRecord, HTTPRequestLog, HTTPResponseLog
from harness.evidence_models import EvidenceChain, EvidenceVerdict, ReplayRecord
from harness.feedback import FeedbackInterpreter
from harness.idor_compare import IdorCompareOperator
from harness.invariant_evaluator import InvariantEvaluation, InvariantEvaluator
from harness.method_tamper import MethodTamperOperator
from harness.models import EndpointIR
from harness.mutation_policy import MutationPolicy
from harness.research_evidence import ProbeAttemptEvidenceMapper
from harness.research_models import ResearchCase, ResearchExecutionResult, SecurityInvariant
from harness.semantic_models import EquivalenceVerdict, SemanticEquivalenceEvaluator
from harness.transformation_models import TransformationFamilyRegistry
from harness.transport import HttpTransport


class AdaptiveSandboxExecutor:
    def __init__(
        self,
        cfg: Optional[InvarConfig] = None,
        transport: Optional[HttpTransport] = None,
        feedback_interpreter: Optional[FeedbackInterpreter] = None,
        mutation_policy: Optional[MutationPolicy] = None,
        research_agent: Optional[ResearchAgent] = None,
        llm_provider: Optional[OpenAICompatibleProvider] = None,
    ) -> None:
        self.cfg = cfg or InvarConfig()
        self.transport = transport or HttpTransport()
        self.feedback_interpreter = (
            feedback_interpreter or FeedbackInterpreter()
        )
        self.mutation_policy = mutation_policy or MutationPolicy()
        self.llm_provider = llm_provider
        self.research_agent = research_agent or ResearchAgent(
            transport=self.transport,
            llm_provider=self.llm_provider,
        )

    def _build_initial_payload(self, endpoint: EndpointIR) -> Dict[str, object]:
        payload: Dict[str, object] = {}
        for param in endpoint.extracted_params:
            payload[param] = self.mutation_policy.infer_default_value(param)
        return payload

    def _host_from_source_file(self, source_file: str) -> Optional[str]:
        if not source_file:
            return None
        source_file = source_file.replace("\\", "/")
        for token in source_file.split("/"):
            if not token or "." not in token:
                continue
            if token.endswith(".js") or token.endswith(".json"):
                continue
            if re.search(r"[A-Za-z0-9-]+\.[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+", token):
                return token
        return None

    def _base_url_from_source_file(self, endpoint: EndpointIR) -> Optional[str]:
        host = self._host_from_source_file(endpoint.source_file)
        if not host:
            return None
        return f"https://{host}"

    def _build_url(
        self,
        endpoint: EndpointIR,
        base_url: Optional[str] = None,
    ) -> str:
        effective_base_url = (
            base_url
            if base_url is not None and base_url.strip()
            else self._host_from_source_file(endpoint.source_file)
        )
        if effective_base_url:
            if not effective_base_url.startswith("http://") and not effective_base_url.startswith("https://"):
                effective_base_url = f"https://{effective_base_url}"
            return f"{effective_base_url.rstrip('/')}/{endpoint.path.lstrip('/')}"
        return f"{self.cfg.target_api_base.rstrip('/')}/{endpoint.path.lstrip('/')}"

    def _create_research_case(self, endpoint: EndpointIR) -> ResearchCase:
        case = ResearchCase(
            case_id=f"{endpoint.method.upper()}:{endpoint.path}",
            endpoint=endpoint,
            metadata={"engine": "AdaptiveSandboxExecutor"},
        )
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

        HypothesisEngine.attach_to_case(case)
        return case

    def _research_denial_loop(
        self,
        endpoint: EndpointIR,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        research_case: ResearchCase,
        last_response: Any,
        last_status_code: int,
    ) -> Tuple[Any, int]:
        baseline_obs = DenialObservation(
            status_code=last_status_code,
            response_headers=dict(last_response.headers) if last_response else {},
            body_preview=last_response.text if last_response else "",
        )
        classification = DeterministicDenialClassifier.classify(baseline_obs)
        research_case.metadata["denial_classification"] = classification.to_dict()

        self.research_agent.transport = self.transport
        if self.llm_provider and not self.research_agent.config.llm_provider:
            self.research_agent.config.llm_provider = self.llm_provider

        loop_res = self.research_agent.investigate_denial(
            endpoint=endpoint,
            url=url,
            baseline_observation=baseline_obs,
            classification=classification,
        )

        research_case.metadata["agent_turns_executed"] = loop_res.turns_executed
        research_case.metadata["agent_breakthrough"] = loop_res.breakthrough_achieved

        if loop_res.breakthrough_achieved and loop_res.evidence_chain:
            applied = loop_res.evidence_chain.applied_variant
            cand_obs = loop_res.evidence_chain.candidate_observation
            last_status_code = cand_obs.status_code

            class BreakthroughResponseMock:
                status_code = cand_obs.status_code
                headers = dict(cand_obs.response_headers)
                text = cand_obs.body_preview

            last_response = BreakthroughResponseMock()
            research_case.record_attempt(
                payload=applied.payload,
                status_code=cand_obs.status_code,
                response_preview=cand_obs.body_preview[:500],
                interpretation=f"403拒绝突破成功 ({applied.family.value}: {applied.variant_id})",
                mutation_reason=f"变异算子生效: {applied.rationale}",
            )
            research_case.metadata["evidence_chain"] = loop_res.evidence_chain.to_dict()

        return last_response, last_status_code

    def _detect_soft_denial(self, response: Any) -> bool:
        if response.status_code != 200 or not response.text:
            return False
        soft = DeterministicDenialClassifier._parse_soft_denial(
            DenialObservation(
                status_code=200,
                response_headers=dict(response.headers),
                body_preview=response.text,
            )
        )
        return soft is not None

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
                response.status_code in {201, 204}
                or (
                    response.status_code == 200
                    and not self._detect_soft_denial(response)
                    and not response.text.strip().lower().startswith(("<!doctype html", "<html"))
                )
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
        is_destruct_or_auth = any(
            h.hypothesis_id.startswith(("H-DESTRUCT", "H-AUTH", "H-IDOR"))
            for h in research_case.hypotheses
        )

        if (
            (last_status_code in {403, 405} or self._detect_soft_denial(last_response))
            and (is_destruct_or_auth or bool(research_case.invariants))
        ):
            last_response, last_status_code = self._research_denial_loop(
                endpoint=endpoint,
                url=url,
                headers=headers,
                payload=payload,
                research_case=research_case,
                last_response=last_response,
                last_status_code=last_status_code,
            )

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

        evaluations: List[InvariantEvaluation] = []
        last_response_text = last_response.text if last_response is not None else ""
        is_soft = self._detect_soft_denial(last_response) if last_response is not None else False

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
                        response_text=last_response_text,
                        is_soft_denial=is_soft,
                    )
                )

        HypothesisEngine.resolve_hypotheses(research_case, evaluations)
        decision = InvariantEvaluator.evaluate_case(
            case=research_case,
            status_code=last_status_code,
            payload=payload,
            headers=headers,
            evaluations=evaluations,
            response_text=last_response_text,
            is_soft_denial=is_soft,
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
