# -*- coding: utf-8 -*-
"""
Invar 信息增益实验规划器 (Information Gain Experiment Planner)
职责：
1. 硬约束前置：严格执行 RoE 门禁一票否决；
2. 图谱对账：结合 ResearchGraph 记忆，已证伪假说收益清零，未覆盖主体赋予最高信息增益；
3. 效用最大化：按综合效用净值输出确定性排序的研究实验序列。
"""

from typing import List, Dict, Optional, Set
from harness.planner.planner_contracts import (
    ExperimentCandidate,
    InformationGainScore,
    PlannedExperiment
)
from harness.graph.research_graph import ResearchGraph
from harness.graph.graph_models import HypothesisMemoryState
from harness.domain_contracts import RoEEnforcementGate, ResearchScope

class InformationGainPlanner:
    """
    基于系统状态图谱的信息增益驱动规划器
    """

    def __init__(self, graph: ResearchGraph, scope: Optional[ResearchScope] = None):
        self.graph = graph
        self.scope = scope

    def evaluate_candidate(self, candidate: ExperimentCandidate) -> InformationGainScore:
        """
        量化单项候选实验的信息增益期望与综合效用
        """
        # 1. 检查假说在图谱中的记忆状态
        h_state = self.graph.get_hypothesis_state(candidate.hypothesis_id)
        
        # 铁律 1: 已被证伪或已被实锤的假说，信息增益直接归零 (杜绝死循环试探)
        if h_state in {HypothesisMemoryState.REFUTED, HypothesisMemoryState.VERIFIED}:
            return InformationGainScore(
                expected_information_gain=0.0,
                cost_penalty=1.0,
                risk_penalty=0.0,
                net_utility=-1.0,
                rationale=f"假说 '{candidate.hypothesis_id}' 已在图谱中收敛为 {h_state.value}，无需重复发包"
            )

        # 2. 检查身份凭据盲区覆盖
        tested_principals = self.graph.get_tested_principals_for_endpoint(candidate.endpoint_id)
        is_new_principal = candidate.principal_id not in tested_principals

        # 基础增益模型
        gain = 5.0
        reasons = []

        # 铁律 2: 覆盖未经测试的主体交汇点 (尤其是潜在攻击者)，赋予最高信息增益 (消灭 IDOR 盲区)
        if is_new_principal:
            gain += 4.5
            reasons.append(f"探索端点上全新主体 '{candidate.principal_id}' 的权限边界")
        else:
            gain += 1.0
            reasons.append("深化既有主体的变异探索")

        # 3. 成本与耗时评估
        cost = round(min(5.0, candidate.estimated_latency_ms / 100.0), 2)

        # 4. 风险与破坏性惩罚 (宪法铁律: 风险绝不能被信息增益抵消)
        risk = 8.0 if candidate.is_destructive else 0.0
        if candidate.is_destructive:
            reasons.append("注意: 涉及破坏性状态修改，赋予重度风险惩罚")

        net_utility = round(gain - cost - risk, 2)
        rationale_text = "; ".join(reasons)

        return InformationGainScore(
            expected_information_gain=gain,
            cost_penalty=cost,
            risk_penalty=risk,
            net_utility=net_utility,
            rationale=rationale_text
        )

    def plan(self, candidates: List[ExperimentCandidate], max_budget: int = 10) -> List[PlannedExperiment]:
        """
        从候选池中完成 RoE 门禁审查、信息增益求值并生成有序执行计划
        """
        approved_plans: List[PlannedExperiment] = []

        for cand in candidates:
            # 前置 RoE 硬门禁拦截: 违背范围一票否决
            is_allowed = True
            if self.scope is not None:
                try:
                    RoEEnforcementGate.assert_allowed(
                        url=cand.send_spec.url,
                        method=cand.send_spec.method,
                        scope=self.scope
                    )
                except Exception:
                    is_allowed = False

            # 仅对 RoE 合规的候选进行信息增益优化排队
            if not is_allowed:
                continue

            score = self.evaluate_candidate(cand)
            approved_plans.append(PlannedExperiment(
                candidate=cand,
                score=score,
                is_roe_approved=True,
                selection_rank=0
            ))

        # 确定性排序: net_utility 降序排列；若效用相同，按候选指纹哈希升序保证绝对确定性
        approved_plans.sort(
            key=lambda p: (-p.score.net_utility, p.candidate.compute_fingerprint())
        )

        # 截断预算并标记最终位次
        final_plans: List[PlannedExperiment] = []
        for rank, p in enumerate(approved_plans[:max_budget], 1):
            final_plans.append(PlannedExperiment(
                candidate=p.candidate,
                score=p.score,
                is_roe_approved=p.is_roe_approved,
                selection_rank=rank
            ))

        return final_plans
