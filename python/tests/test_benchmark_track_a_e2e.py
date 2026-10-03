# -*- coding: utf-8 -*-
"""
Phase 10.2 轨道 A: 本地确定性全链路 E2E 物理基准测试
基于真实 LocalFixtureServer 物理端口，端到端打通:
Tool Gateway (cURL) -> Skill -> ResearchGraph -> Planner -> Verifier -> Gate
"""

import unittest
from pathlib import Path

from fixtures.local_server_fixture import LocalFixtureServer
from harness.tools.tool_contracts import HttpSendSpec
from harness.skills.skill_registry import SkillRegistry
from harness.graph.research_graph import ResearchGraph
from harness.graph.graph_models import HypothesisMemoryState, NodeType
from harness.planner.planner_contracts import ExperimentCandidate
from harness.planner.information_gain_planner import InformationGainPlanner
from harness.verifier.fresh_verifier import (
    FreshSandboxVerifier,
    PoCSpecification,
    PoCType,
)
from harness.gates.bounty_eligibility_gate import (
    BountyEligibilityGate,
    BountyEligibilityStatus,
)
from harness.domain_contracts import (
    EndpointIR,
    SecurityInvariant,
    ResearchScope,
    AuthPrincipal,
    FindingRecord,
    Verdict,
    Severity,
    VerificationSummary,
    Remediation,
    TraceStep,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

class BenchmarkTrackAE2ETests(unittest.TestCase):

    def test_01_complete_bounty_lifecycle_on_physical_fixture(self) -> None:
        """【轨道 A 核心验收】在物理测试桩上无 Mock 跑通规划、发包、图谱、复验与赏金门禁全生命周期"""
        with LocalFixtureServer() as fixture:
            scope = ResearchScope(
                target_domain="127.0.0.1",
                allowed_methods=["GET", "POST"]
            )
            endpoint = EndpointIR(
                method="GET",
                path="/ok",
                endpoint_id="GET:/ok",
                extracted_params=["order_id"]
            )
            auth_invariant = SecurityInvariant(
                invariant_type="auth_boundary",
                statement="Protected API route must enforce authentication token verification"
            )

            # -------------------------------------------------------------
            # 步骤 1: 技能发现与动态匹配 (Skills System)
            # -------------------------------------------------------------
            skills_dir = REPO_ROOT / ".agents" / "skills"
            skill_reg = SkillRegistry.load_from_directory(skills_dir)
            matched_skills = skill_reg.match_skills({"object_identifier", "tenant_context"})
            self.assertGreaterEqual(len(matched_skills), 1)
            active_skill = matched_skills[0]
            self.assertEqual(active_skill.skill_id, "api-authorization-bola")

            # -------------------------------------------------------------
            # 步骤 2: 状态图谱初始化 (ResearchGraph Projection)
            # -------------------------------------------------------------
            graph = ResearchGraph(run_id="RUN-BENCHMARK-TRACK-A")
            hyp_id = "H-BOLA-LOCAL-01"
            graph.project_endpoint(endpoint.endpoint_id, endpoint.method, endpoint.path, "asset:127.0.0.1")
            graph.project_hypothesis(hyp_id, endpoint.endpoint_id, "authorization", HypothesisMemoryState.PROPOSED)

            # -------------------------------------------------------------
            # 步骤 3: 信息增益科学规划 (Information Gain Planning)
            # -------------------------------------------------------------
            target_url = f"{fixture.base_url}/ok"
            candidate = ExperimentCandidate(
                candidate_id="exp-cand-01",
                endpoint_id=endpoint.endpoint_id,
                hypothesis_id=hyp_id,
                principal_id="principal_attacker_beta",
                skill_name=active_skill.skill_id,
                send_spec=HttpSendSpec(method="GET", url=target_url)
            )

            planner = InformationGainPlanner(graph=graph, scope=scope)
            plans = planner.plan([candidate], max_budget=1)
            self.assertEqual(len(plans), 1)
            best_plan = plans[0]
            self.assertEqual(best_plan.selection_rank, 1)
            self.assertGreater(best_plan.score.net_utility, 0.0)

            # -------------------------------------------------------------
            # 步骤 4: 双盲纯净隔离复验 (Fresh Independent Verification)
            # -------------------------------------------------------------
            # 由规划决策派生最小复现 PoC 规格
            poc = PoCSpecification(
                poc_type=PoCType.CURL,
                method=best_plan.candidate.send_spec.method,
                target_url=best_plan.candidate.send_spec.url,
                expected_status_code=200,
                expected_markers=["fixture_ready"],
                reproducible_curl=f"curl -s -i '{target_url}'"
            )

            verifier = FreshSandboxVerifier(verifier_id="track-a-fresh-verifier", scope=scope)
            verification_result = verifier.verify_poc(
                poc=poc,
                invariant=auth_invariant,
                endpoint=endpoint
            )

            # 断言物理网络实际击穿 (收到 200 且无鉴权凭据 -> vulnerable)
            self.assertTrue(verification_result.is_reproduced)
            self.assertEqual(verification_result.status_code, 200)
            self.assertEqual(verification_result.invariant_evaluation.status, "vulnerable")

            # -------------------------------------------------------------
            # 步骤 5: 更新状态图谱记忆 (Graph Memory Update)
            # -------------------------------------------------------------
            # 将物理复验的确凿物证回写至图谱，假说自动收敛为 VERIFIED
            from harness.graph.graph_models import ObservationRef
            obs_ref = ObservationRef(
                evidence_id="ev:benchmark:track-a:001",
                content_hash=verification_result.content_hash,
                status_code=verification_result.status_code,
                observed_at="2026-10-03T22:00:00Z",
                principal_id="principal_attacker_beta"
            )
            graph.project_observation(
                endpoint_id=endpoint.endpoint_id,
                obs_ref=obs_ref,
                verifies_hypothesis=hyp_id
            )
            self.assertEqual(graph.get_hypothesis_state(hyp_id), HypothesisMemoryState.VERIFIED)

            # -------------------------------------------------------------
            # 步骤 6: 技术确权与赏金资格两权分立门禁 (Gates Tier)
            # -------------------------------------------------------------
            finding = FindingRecord(
                finding_id="FINDING-TRACK-A-BOLA",
                verdict=Verdict.CONFIRMED,
                fingerprint="fp:authorization:local_orders:track_a_001",
                title="BOLA: 本地服务受保护端点无凭证物理放行",
                description="物理请求在未携带合法凭证状态下成功获取敏感回显",
                root_cause="端点未对调用方执行鉴权与租户属主核验",
                severity=Severity.HIGH,
                poc_code=poc.reproducible_curl,
                endpoint_refs=[endpoint.endpoint_id],
                evidence_refs=["ev:benchmark:track-a:001"],
                remediation=Remediation(summary="增加中间件鉴权", guidance="校验 Authorization 标头与属主"),
                verification=VerificationSummary(
                    independent_verified=True,
                    verifier_id=verifier.verifier_id,
                    verdict="VERIFIED"
                ),
                trace=[TraceStep(step_type="sink", file_path="server.py", line=10, scope="handle", description="放行点")]
            )

            # 赏金资格审查
            eligibility_result = BountyEligibilityGate.evaluate(
                finding=finding,
                scope=scope,
                known_fingerprints=set()  # 首次提交，非重复
            )

            # 核心断言: 全链路 100% 达标，取得赏金提交资格 (ELIGIBLE)
            self.assertTrue(eligibility_result.is_eligible)
            self.assertEqual(eligibility_result.status, BountyEligibilityStatus.ELIGIBLE)
            self.assertTrue(eligibility_result.checklist.all_passed())
