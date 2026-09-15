from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from harness.models import EndpointIR


@dataclass(frozen=True)
class SecurityInvariant:
    invariant_type: str
    statement: str


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str
    rationale: str = ""


@dataclass(frozen=True)
class ProbeAttempt:
    attempt_number: int
    payload: Dict[str, Any]
    status_code: int
    response_preview: str
    interpretation: str = ""
    mutation_reason: str = ""


@dataclass(frozen=True)
class ResearchDecision:
    status: str
    rationale: str


@dataclass
class ResearchCase:
    case_id: str
    endpoint: EndpointIR
    invariants: List[SecurityInvariant] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    attempts: List[ProbeAttempt] = field(default_factory=list)
    decision: Optional[ResearchDecision] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_invariant(self, invariant: SecurityInvariant) -> None:
        self.invariants.append(invariant)

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        self.hypotheses.append(hypothesis)

    def add_attempt(self, attempt: ProbeAttempt) -> None:
        expected_number = len(self.attempts) + 1
        if attempt.attempt_number != expected_number:
            raise ValueError(
                f"attempt_number must be contiguous: expected {expected_number}, "
                f"got {attempt.attempt_number}"
            )
        self.attempts.append(attempt)

    def record_attempt(
        self,
        payload: Dict[str, Any],
        status_code: int,
        response_preview: str,
        interpretation: str = "",
        mutation_reason: str = "",
    ) -> ProbeAttempt:
        attempt = ProbeAttempt(
            attempt_number=len(self.attempts) + 1,
            payload=dict(payload),
            status_code=status_code,
            response_preview=response_preview,
            interpretation=interpretation,
            mutation_reason=mutation_reason,
        )
        self.add_attempt(attempt)
        return attempt

    def set_decision(self, decision: ResearchDecision) -> None:
        self.decision = decision

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "endpoint": self.endpoint.to_dict(),
            "invariants": [
                {
                    "invariant_type": item.invariant_type,
                    "statement": item.statement,
                }
                for item in self.invariants
            ],
            "hypotheses": [
                {
                    "hypothesis_id": item.hypothesis_id,
                    "statement": item.statement,
                    "rationale": item.rationale,
                }
                for item in self.hypotheses
            ],
            "attempts": [
                {
                    "attempt_number": item.attempt_number,
                    "payload": dict(item.payload),
                    "status_code": item.status_code,
                    "response_preview": item.response_preview,
                    "interpretation": item.interpretation,
                    "mutation_reason": item.mutation_reason,
                }
                for item in self.attempts
            ],
            "decision": (
                None
                if self.decision is None
                else {
                    "status": self.decision.status,
                    "rationale": self.decision.rationale,
                }
            ),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ResearchExecutionResult:
    evidence: Any
    research_case: ResearchCase
    evidence_history: List[Any] = field(default_factory=list)
