from typing import Dict, List

from harness.evidence import EvidenceRecord
from harness.models import EndpointIR
from harness.research_models import ResearchCase, ProbeAttempt


class ProbeAttemptEvidenceMapper:
    @staticmethod
    def to_evidence(
        endpoint: EndpointIR,
        attempt: ProbeAttempt,
        url: str,
        headers: Dict[str, str] | None = None,
    ) -> EvidenceRecord:
        from harness.evidence import HTTPRequestLog, HTTPResponseLog

        request_log = HTTPRequestLog(
            method=endpoint.method.upper(),
            url=url,
            headers=dict(headers or {}),
            body=dict(attempt.payload),
        )

        response_log = HTTPResponseLog(
            status_code=attempt.status_code,
            headers={},
            body_preview=attempt.response_preview,
        )

        notes = [
            f"research_attempt={attempt.attempt_number}",
        ]

        if attempt.interpretation:
            notes.append(attempt.interpretation)

        if attempt.mutation_reason:
            notes.append(f"mutation={attempt.mutation_reason}")

        return EvidenceRecord(
            endpoint=endpoint,
            request=request_log,
            response=response_log,
            timestamp="",
            finding_type="ENDPOINT_PROBE",
            is_anomaly=False,
            notes=" | ".join(notes),
        )

    @classmethod
    def to_evidence_records(
        cls,
        research_case: ResearchCase,
        url: str,
        headers: Dict[str, str] | None = None,
    ) -> List[EvidenceRecord]:
        return [
            cls.to_evidence(
                endpoint=research_case.endpoint,
                attempt=attempt,
                url=url,
                headers=headers,
            )
            for attempt in research_case.attempts
        ]
