# -*- coding: utf-8 -*-
"""
Phase 9.10 第一单步: 信息增益与实验规划器契约测试
断言 RoE 前置硬拦截、假说证伪记忆增益清零、全新主体盲区增益优先与综合效用确定性排序
"""

import unittest
from harness.graph.research_graph import ResearchGraph
from harness.graph.graph_models import HypothesisMemoryState, ObservationRef
from harness.tools.tool_contracts import HttpSendSpec
from harness.domain_contracts import ResearchScope
from harness.planner.planner_contracts import ExperimentCandidate
from harness.planner.information_gain_planner import InformationGainPlanner

class InformationGainPlannerContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.graph = ResearchGraph(run_id="RUN-PLAN-001")
        self.endpoint_id = "GET:/api/v1/orders/99901"
        self.target_url = "https://api.ikuai8.com/api/v1/orders/99901"
        self.graph.project_endpoint(self.endpoint_id, "GET", "/api/v1/orders/99901", "asset:api.ikuai8.com")
        
        self.scope = ResearchScope(
            target_domain="ikuai8.com",
            allowed_methods=["GET", "POST"],
            excluded_paths=["/api/v1/forbidden"]
        )

    def test_01_refuted_hypothesis_has_zero_information_gain(self) -> None:
        """【契约 1】已被图谱证伪 (REFUTED) 的假说，其信息增益期望直接清零，防止死循环发包"""
        hyp_id = "H-AUTH-REFUTED"
        self.graph.project_hypothesis(hyp_id, self.endpoint_id, "authorization", state=HypothesisMemoryState.REFUTED)

        cand = ExperimentCandidate(
            candidate_id="cand-01",
            endpoint_id=self.endpoint_id,
            hypothesis_id=hyp_id,
            principal_id="attacker",
            skill_name="api-bypass-403",
            send_spec=HttpSendSpec(method="GET", url=self.target_url)
        )

        planner = InformationGainPlanner(graph=self.graph, scope=self.scope)
        score = planner.evaluate_candidate(cand)

        self.assertEqual(score.expected_information_gain, 0.0)
        self.assertLess(score.net_utility, 0.0)
        self.assertIn("已在图谱中收敛", score.rationale)

    def test_02_untested_principal_receives_highest_information_gain(self) -> None:
        """【契约 2】探测尚未测试过的主体凭据交汇点时，赋予最高信息增益以破除 IDOR 盲区"""
        hyp_id = "H-IDOR-ACTIVE"
        self.graph.project_hypothesis(hyp_id, self.endpoint_id, "authorization", state=HypothesisMemoryState.PROPOSED)

        # 候选 A: 针对全新未测主体 (Attacker)
        cand_new_principal = ExperimentCandidate(
            candidate_id="cand-new",
            endpoint_id=self.endpoint_id,
            hypothesis_id=hyp_id,
            principal_id="principal_attacker_beta",
            skill_name="api-authorization-bola",
            send_spec=HttpSendSpec(method="GET", url=self.target_url)
        )

        # 模拟已知主体 (Victim) 已经有观测记录
        obs_ref = ObservationRef("ev-1", "hash-1", 200, "time", principal_id="principal_victim_alpha")
        self.graph.project_observation(self.endpoint_id, obs_ref)

        # 候选 B: 针对已测过的主体 (Victim)
        cand_known_principal = ExperimentCandidate(
            candidate_id="cand-known",
            endpoint_id=self.endpoint_id,
            hypothesis_id=hyp_id,
            principal_id="principal_victim_alpha",
            skill_name="api-authorization-bola",
            send_spec=HttpSendSpec(method="GET", url=self.target_url)
        )

        planner = InformationGainPlanner(graph=self.graph, scope=self.scope)
        score_new = planner.evaluate_candidate(cand_new_principal)
        score_known = planner.evaluate_candidate(cand_known_principal)

        # 断言全新主体的信息增益与净效用显著高于已知主体
        self.assertGreater(score_new.expected_information_gain, score_known.expected_information_gain)
        self.assertGreater(score_new.net_utility, score_known.net_utility)

    def test_03_roe_violation_strictly_excluded_from_plan(self) -> None:
        """【契约 3】违背 RoE 范围的候选实验被前置一票否决，绝对禁止进入最终执行计划"""
        hyp_id = "H-AUTH-OUT"
        self.graph.project_hypothesis(hyp_id, self.endpoint_id, "authorization", state=HypothesisMemoryState.PROPOSED)

        # 越界候选 (非授权主机)
        cand_out_of_scope = ExperimentCandidate(
            candidate_id="cand-out",
            endpoint_id=self.endpoint_id,
            hypothesis_id=hyp_id,
            principal_id="attacker",
            skill_name="api-bypass-403",
            send_spec=HttpSendSpec(method="GET", url="https://evil.internal.corp/secret")
        )

        # 合规候选
        cand_in_scope = ExperimentCandidate(
            candidate_id="cand-in",
            endpoint_id=self.endpoint_id,
            hypothesis_id=hyp_id,
            principal_id="attacker",
            skill_name="api-bypass-403",
            send_spec=HttpSendSpec(method="GET", url=self.target_url)
        )

        planner = InformationGainPlanner(graph=self.graph, scope=self.scope)
        plans = planner.plan([cand_out_of_scope, cand_in_scope], max_budget=5)

        # 只有在范围内的候选进入计划
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].candidate.candidate_id, "cand-in")
        self.assertTrue(plans[0].is_roe_approved)
        self.assertEqual(plans[0].selection_rank, 1)
