from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from harness.config import InvarConfig
from harness.evidence import EvidenceRecord, HTTPRequestLog, HTTPResponseLog
from harness.feedback import FeedbackInterpreter
from harness.models import EndpointIR
from harness.mutation_policy import MutationPolicy
from harness.research_evidence import ProbeAttemptEvidenceMapper
from harness.research_models import ResearchCase, ResearchExecutionResult
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
        return ResearchCase(
            case_id=f"{endpoint.method.upper()}:{endpoint.path}",
            endpoint=endpoint,
            metadata={"engine": "AdaptiveSandboxExecutor"},
        )

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
