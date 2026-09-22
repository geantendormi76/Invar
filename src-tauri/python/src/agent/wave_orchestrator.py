from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from agent.coverage_critic import CoverageCritic, MissingCoverageProposal
from agent.hunter import Hunter, HunterResult
from harness.candidate_models import Candidate, CandidateConsolidator
from harness.coverage_ledger import CoverageLedger, CoverageStatus, CoverageUnit
from harness.models import EndpointIR
from harness.run_models import ResearchScope

if TYPE_CHECKING:
    from harness.sandbox_executor import AdaptiveSandboxExecutor


@dataclass
class WaveResult:
    """单轮次认知编排收敛结果战报"""
    wave_number: int
    units_assigned: int
    units_covered: int
    units_candidate: int
    units_blocked: int
    candidates_found: int
    gap_units_added: int
    metrics: Dict[str, Any]
    candidate_pool: List[Candidate]


class HunterWaveOrchestrator:
    """
    Invar 认知编排协同中枢 (Cognitive Wave Orchestrator)
    负责驱动 Hunter 搜寻、账本独占写提交、候选去重与 Critic 盲区反馈演化
    """
    def __init__(
        self,
        ledger: CoverageLedger,
        endpoints: List[EndpointIR],
        scope: Optional[ResearchScope] = None,
    ):
        self.ledger = ledger
        self.endpoints = endpoints
        self.scope = scope
        self.candidate_pool: List[Candidate] = []
        self.wave_counter: int = 0

    def run_wave(
        self,
        hunters: Optional[List[Hunter]] = None,
        critic: Optional[CoverageCritic] = None,
        executor: Optional["AdaptiveSandboxExecutor"] = None,
        base_url: Optional[str] = None,
        max_units_per_wave: int = 10,
    ) -> WaveResult:
        self.wave_counter += 1
        active_hunters = hunters or [Hunter(agent_id=f"hunter-wave-{self.wave_counter}")]
        active_critic = critic or CoverageCritic(critic_id=f"critic-wave-{self.wave_counter}")

        # 1. 提取当前处于 PLANNED 状态的覆盖单元
        planned_units = [
            u for u in self.ledger.units.values()
            if u.status == CoverageStatus.PLANNED
        ][:max_units_per_wave]

        units_covered = 0
        units_candidate = 0
        units_blocked = 0
        newly_found_candidates: List[Candidate] = []

        # 2. 并发/轮询分派 Hunter 执行深度审查
        for idx, unit in enumerate(planned_units):
            # 将单元状态切换为 in_progress
            unit.transition_to(CoverageStatus.IN_PROGRESS)

            hunter = active_hunters[idx % len(active_hunters)]
            result: HunterResult = hunter.hunt(
                unit=unit,
                endpoints=self.endpoints,
                scope=self.scope,
                executor=executor,
                base_url=base_url,
            )

            # 3. [Parent-Only Write] 主进程独占写对账提交至 CoverageLedger
            unit.owner_agent_id = hunter.agent_id
            unit.reviewed_paths = result.reviewed_paths
            unit.check_refs = result.check_refs
            unit.candidate_fingerprints = [c.fingerprint.value for c in result.candidate_proposals]
            unit.unresolved = result.unresolved_facts

            # 依据结果状态机单向跃迁
            unit.transition_to(result.status)

            if result.status == CoverageStatus.COVERED:
                units_covered += 1
            elif result.status == CoverageStatus.CANDIDATE:
                units_candidate += 1
                newly_found_candidates.extend(result.candidate_proposals)
            elif result.status == CoverageStatus.BLOCKED:
                units_blocked += 1

        # 4. 候选指纹聚合去重合并 (Candidate Deduplication)
        self.candidate_pool.extend(newly_found_candidates)
        self.candidate_pool = CandidateConsolidator.consolidate(self.candidate_pool)

        # 5. 覆盖批评家独立盲区审视 (Coverage Critic Feedback)
        missing_proposals: List[MissingCoverageProposal] = active_critic.critique(
            ledger=self.ledger,
            endpoints=self.endpoints,
            scope=self.scope,
        )

        # 6. 将批评家挖掘出的盲区单元转化为新的 planned 单元增补进账本
        gap_units_added = 0
        for prop in missing_proposals:
            cid = f"{prop.surface}-{prop.subsystem}-{prop.attack_class}"
            if not self.ledger.contains(cid):
                new_unit = CoverageUnit(
                    coverage_id=cid,
                    surface=prop.surface,
                    boundary=prop.boundary,
                    subsystem=prop.subsystem,
                    attack_class=prop.attack_class,
                    starting_paths=prop.starting_paths,
                    status=CoverageStatus.PLANNED,
                )
                self.ledger.add_unit(new_unit)
                gap_units_added += 1

        metrics = self.ledger.compute_metrics()

        return WaveResult(
            wave_number=self.wave_counter,
            units_assigned=len(planned_units),
            units_covered=units_covered,
            units_candidate=units_candidate,
            units_blocked=units_blocked,
            candidates_found=len(newly_found_candidates),
            gap_units_added=gap_units_added,
            metrics=metrics,
            candidate_pool=list(self.candidate_pool),
        )
