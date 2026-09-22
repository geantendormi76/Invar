from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from harness.candidate_models import CandidateFingerprint
from harness.coverage_ledger import CoverageLedger, CoverageStatus, CoverageUnit, UnresolvedFact
from harness.finding_models import FindingRecord, Verdict
from harness.models import EndpointIR
from harness.run_models import ResearchRun, SourceRef


@dataclass
class MultiRunDiffSummary:
    """两轮次之间的科学事实差异体检摘要"""
    source_changed: bool
    prior_run_id: str
    current_run_id: str
    confirmed_revalidation_count: int = 0
    unresolved_resurfaced_count: int = 0
    carried_confirmed_count: int = 0
    new_units_planned_count: int = 0


@dataclass
class MultiRunReconciliationResult:
    """跨轮次对账合成结果"""
    diff_summary: MultiRunDiffSummary
    reconciled_ledger: CoverageLedger
    carried_findings: List[FindingRecord] = field(default_factory=list)
    revalidation_units: List[CoverageUnit] = field(default_factory=list)


class MultiRunReconciler:
    """
    Invar 跨轮次科研历史继承与差异对账引擎 (Multi-Run Reconciler)
    依据源码哈希变化与历史账本事实，实现增量演进与优先算力倾斜
    """

    @classmethod
    def is_source_identical(cls, current_run: ResearchRun, prior_run: ResearchRun) -> bool:
        c_hash = current_run.source_ref.raw_input_hash
        p_hash = prior_run.source_ref.raw_input_hash
        c_commit = current_run.source_ref.commit
        p_commit = prior_run.source_ref.commit

        if c_hash and p_hash:
            return c_hash == p_hash
        if c_commit and p_commit:
            return c_commit == p_commit and not current_run.source_ref.worktree_dirty

        return False

    @classmethod
    def reconcile(
        cls,
        current_run: ResearchRun,
        prior_run: ResearchRun,
        prior_ledger: CoverageLedger,
        prior_findings: List[FindingRecord],
        current_endpoints: List[EndpointIR],
    ) -> MultiRunReconciliationResult:
        source_identical = cls.is_source_identical(current_run, prior_run)
        source_changed = not source_identical

        # 初始化当前轮次的全新权威覆盖账本
        new_ledger = CoverageLedger(run_id=current_run.run_id)

        carried_findings: List[FindingRecord] = []
        revalidation_units: List[CoverageUnit] = []
        unresolved_resurfaced_count = 0

        # 记录当前实际存在的端点路由
        current_paths = {ep.path for ep in current_endpoints}

        # 1. 继承历史未决盲区 (needs_validation / blocked)
        # 铁律：未决阻塞绝不能因轮次更替而静默丢失！
        for u in prior_ledger.units.values():
            if u.status in {CoverageStatus.BLOCKED, CoverageStatus.DEFERRED}:
                reopened_unit = CoverageUnit(
                    coverage_id=u.coverage_id,
                    surface=u.surface,
                    boundary=u.boundary,
                    subsystem=u.subsystem,
                    attack_class=u.attack_class,
                    starting_paths=list(u.starting_paths),
                    status=CoverageStatus.PLANNED,
                    unresolved=list(u.unresolved),
                    prior_refs=[f"{prior_run.run_id}:{u.coverage_id}"],
                    weight=u.weight * 1.5,  # 提升历史未决单元的审查权重
                )
                new_ledger.add_unit(reopened_unit)
                unresolved_resurfaced_count += 1

        for f in prior_findings:
            if f.verdict == Verdict.NEEDS_VALIDATION:
                cid = f"reval-gap-{f.fingerprint}"
                if not new_ledger.contains(cid):
                    gap_unit = CoverageUnit(
                        coverage_id=cid,
                        surface="api",
                        boundary="prior-unresolved-gap",
                        subsystem="revalidation",
                        attack_class="unresolved_gap",
                        starting_paths=list(f.endpoint_refs),
                        status=CoverageStatus.PLANNED,
                        unresolved=[
                            UnresolvedFact(
                                fact_id=f"FACT-{f.fingerprint}",
                                description=f.unresolved_blocker or "Prior needs_validation blocker",
                                blocking_reason="Unresolved gap carried over from prior run",
                            )
                        ],
                        prior_refs=[f"{prior_run.run_id}:{f.finding_id}"],
                        weight=2.0,
                    )
                    new_ledger.add_unit(gap_unit)
                    unresolved_resurfaced_count += 1

        # 2. 处理历史实锤发现 (Confirmed Findings)
        confirmed_findings = [f for f in prior_findings if f.verdict == Verdict.CONFIRMED]

        for f in confirmed_findings:
            # 无论源码是否变更，如果相关端点已被完全从代码中删除，则不再继承
            endpoints_survived = any(
                ref in current_paths or any(p in ref for p in current_paths)
                for ref in f.endpoint_refs
            )
            if not endpoints_survived and current_paths:
                continue

            if source_identical:
                # 场景 A: 源码完全一致 -> 历史实锤可平移继承至当前轮次候选池
                carried_findings.append(f)
            else:
                # 场景 B: 源码已发生变动 -> 强制建立靶向复测单元 (Revalidation Target)
                reval_cid = f"reval-confirmed-{f.fingerprint}"
                if not new_ledger.contains(reval_cid):
                    reval_unit = CoverageUnit(
                        coverage_id=reval_cid,
                        surface="api",
                        boundary="revalidation-target",
                        subsystem="security-regression",
                        attack_class="regression_verification",
                        starting_paths=list(f.endpoint_refs),
                        status=CoverageStatus.PLANNED,
                        candidate_fingerprints=[f.fingerprint],
                        prior_refs=[f"{prior_run.run_id}:{f.finding_id}"],
                        weight=3.0,  # 漏洞回溯复测具有最高优先权重
                    )
                    new_ledger.add_unit(reval_unit)
                    revalidation_units.append(reval_unit)

        # 3. 规划当前轮次的新增基线单元 (Baseline Units)
        base_ledger = CoverageLedger.plan_from_endpoints(
            run_id=current_run.run_id,
            endpoints=current_endpoints,
            scope=current_run.scope,
        )
        new_units_planned = 0
        for cid, u in base_ledger.units.items():
            if not new_ledger.contains(cid):
                new_ledger.add_unit(u)
                new_units_planned += 1

        diff_summary = MultiRunDiffSummary(
            source_changed=source_changed,
            prior_run_id=prior_run.run_id,
            current_run_id=current_run.run_id,
            confirmed_revalidation_count=len(revalidation_units),
            unresolved_resurfaced_count=unresolved_resurfaced_count,
            carried_confirmed_count=len(carried_findings),
            new_units_planned_count=new_units_planned,
        )

        return MultiRunReconciliationResult(
            diff_summary=diff_summary,
            reconciled_ledger=new_ledger,
            carried_findings=carried_findings,
            revalidation_units=revalidation_units,
        )
