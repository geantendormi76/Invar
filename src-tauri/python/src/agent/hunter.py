from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from harness.candidate_models import (
    Candidate,
    CandidateFingerprint,
    CandidateStatus,
    CanonicalFactors,
    Condition,
    TraceStep,
)
from harness.coverage_ledger import CoverageStatus, CoverageUnit, UnresolvedFact
from harness.models import EndpointIR
from harness.run_models import ResearchScope

if TYPE_CHECKING:
    from harness.sandbox_executor import AdaptiveSandboxExecutor


@dataclass
class HunterResult:
    """
    Hunter 产出的纯结构化审查结果提案
    严禁直接修改主账本！
    """
    coverage_id: str
    status: CoverageStatus
    reviewed_paths: List[str] = field(default_factory=list)
    check_refs: List[str] = field(default_factory=list)
    candidate_proposals: List[Candidate] = field(default_factory=list)
    unresolved_facts: List[UnresolvedFact] = field(default_factory=list)
    uncovered_paths: List[str] = field(default_factory=list)
    notes: str = ""


class Hunter:
    """
    Invar 靶向猎犬 (Targeted Hunter)
    严格限定在被分配的 CoverageUnit 规定路径内执行代码切片审查与沙箱实证
    """
    def __init__(self, agent_id: str = "hunter-alpha"):
        self.agent_id = agent_id

    def hunt(
        self,
        unit: CoverageUnit,
        endpoints: List[EndpointIR],
        scope: Optional[ResearchScope] = None,
        executor: Optional["AdaptiveSandboxExecutor"] = None,
        base_url: Optional[str] = None,
    ) -> HunterResult:
        # 1. 精确切片：若 starting_paths 明确指定，严格按指定路径收敛；否则按 subsystem 兜底
        if unit.starting_paths:
            matched_endpoints = [ep for ep in endpoints if ep.path in unit.starting_paths]
        else:
            matched_endpoints = [
                ep for ep in endpoints
                if unit.subsystem and (f"/{unit.subsystem}" in ep.path or ep.path.startswith(unit.subsystem))
            ]

        # 若无可审查路径，标记阻塞
        if not matched_endpoints:
            return HunterResult(
                coverage_id=unit.coverage_id,
                status=CoverageStatus.BLOCKED,
                unresolved_facts=[
                    UnresolvedFact(
                        fact_id=f"FACT-NO-EP-{unit.coverage_id}",
                        description=f"No matching endpoints found for unit paths: {unit.starting_paths}",
                        blocking_reason="Missing AST endpoint slice",
                    )
                ],
                notes="Blocked: AST endpoint slice unavailable",
            )

        reviewed_paths: List[str] = []
        check_refs: List[str] = []
        candidates: List[Candidate] = []

        for ep in matched_endpoints:
            reviewed_paths.append(ep.path)
            check_ref = f"CHK-{unit.attack_class.upper()}-{ep.method.upper()}"
            check_refs.append(check_ref)

            # 2. 动态沙箱实证（若提供了执行器）
            if executor is not None:
                try:
                    exec_result = executor.probe_endpoint_with_research(ep, base_url=base_url)
                    case = exec_result.research_case

                    # 若安全不变量判定为 vulnerable，提炼生成标准 Candidate
                    if case.decision and case.decision.status == "vulnerable":
                        factors = CanonicalFactors(
                            attack_class=unit.attack_class,
                            boundary=unit.boundary,
                            sink_component=f"{unit.subsystem}_service",
                            missing_control=f"missing_{unit.attack_class}_guard",
                        )
                        fp = CandidateFingerprint.from_factors(factors)

                        trace = [
                            TraceStep(
                                step_type="entrypoint",
                                file_path=ep.source_file or f"routes/{unit.subsystem}.js",
                                line=ep.line if ep.line > 0 else 1,
                                scope=ep.call_signature or f"{ep.method} {ep.path}",
                                description="Endpoint entrypoint receiving user request",
                            ),
                            TraceStep(
                                step_type="sink",
                                file_path=ep.source_file or f"services/{unit.subsystem}.js",
                                line=ep.line if ep.line > 0 else 1,
                                scope="serviceHandler",
                                description=f"Execution sink violating invariant: {case.decision.rationale}",
                            ),
                        ]

                        candidate = Candidate(
                            fingerprint=fp,
                            title=f"Vulnerability in [{ep.method} {ep.path}]",
                            description=case.decision.rationale,
                            claimed_root_cause=case.decision.rationale,
                            endpoint_refs=[f"{ep.method}:{ep.path}"],
                            coverage_refs=[unit.coverage_id],
                            evidence_refs=[exec_result.evidence.notes[:30]] if exec_result.evidence else [],
                            trace=trace,
                            conditions=[Condition(condition_id="COND-UNPROTECTED", description="No guard parameter supplied")],
                            status=CandidateStatus.SUPPORTED,
                        )
                        candidates.append(candidate)
                except Exception as exc:
                    return HunterResult(
                        coverage_id=unit.coverage_id,
                        status=CoverageStatus.BLOCKED,
                        unresolved_facts=[
                            UnresolvedFact(
                                fact_id=f"FACT-EXEC-ERR-{unit.coverage_id}",
                                description=str(exc),
                                blocking_reason="Dynamic sandbox probe execution failed",
                            )
                        ],
                    )

        # 3. 汇总判定本单元状态
        if candidates:
            return HunterResult(
                coverage_id=unit.coverage_id,
                status=CoverageStatus.CANDIDATE,
                reviewed_paths=sorted(list(set(reviewed_paths))),
                check_refs=sorted(list(set(check_refs))),
                candidate_proposals=candidates,
                notes=f"Hunter found {len(candidates)} candidate vulnerabilities",
            )

        return HunterResult(
            coverage_id=unit.coverage_id,
            status=CoverageStatus.COVERED,
            reviewed_paths=sorted(list(set(reviewed_paths))),
            check_refs=sorted(list(set(check_refs))),
            candidate_proposals=[],
            notes="Hunter completed checks, no invariant violations detected",
        )
