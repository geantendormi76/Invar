# -*- coding: utf-8 -*-
"""
Phase 9.9 第一单步: 研究状态图谱与假说记忆契约测试
断言图谱拓扑构建、只读单向投影、假说证伪记忆与多主体覆盖查询
"""

import unittest
from harness.graph.graph_models import (
    NodeType,
    EdgeType,
    HypothesisMemoryState,
    ObservationRef,
)
from harness.graph.research_graph import ResearchGraph

class ResearchGraphContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.graph = ResearchGraph(run_id="RUN-TEST-001")
        self.asset_id = "asset-ikuai8.com"
        self.endpoint_id = "GET:/api/v1/orders/99901"
        self.hyp_id = "H-BOLA-ORDER-01"

    def test_01_project_endpoint_and_asset_topology(self) -> None:
        """【契约 1】端点与资产拓扑投影建立有向 EXPOSES 关系"""
        self.graph.project_endpoint(
            endpoint_id=self.endpoint_id,
            method="GET",
            path="/api/v1/orders/99901",
            asset_id=self.asset_id
        )

        ep_node = self.graph.get_node(self.endpoint_id)
        self.assertIsNotNone(ep_node)
        self.assertEqual(ep_node.node_type, NodeType.ENDPOINT)

        edges = self.graph.get_edges_from(self.asset_id, EdgeType.EXPOSES)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].target_id, self.endpoint_id)

    def test_02_project_hypothesis_and_memory_state(self) -> None:
        """【契约 2】假说投影初始化为 PROPOSED 状态，并正确绑定目标端点"""
        self.graph.project_endpoint(self.endpoint_id, "GET", "/api/v1/orders/99901", self.asset_id)
        self.graph.project_hypothesis(
            hypothesis_id=self.hyp_id,
            endpoint_id=self.endpoint_id,
            attack_class="authorization",
            state=HypothesisMemoryState.PROPOSED
        )

        self.assertEqual(self.graph.get_hypothesis_state(self.hyp_id), HypothesisMemoryState.PROPOSED)
        self.assertFalse(self.graph.is_hypothesis_refuted(self.hyp_id))

    def test_03_observation_projection_verifies_hypothesis(self) -> None:
        """【契约 3】物理观测事实投影成功实锤假说，假说状态自动迁移为 VERIFIED"""
        self.graph.project_endpoint(self.endpoint_id, "GET", "/api/v1/orders/99901", self.asset_id)
        self.graph.project_hypothesis(self.hyp_id, self.endpoint_id, "authorization")

        obs_ref = ObservationRef(
            evidence_id="ev-128bit-hash-001",
            content_hash="sha256-physical-bytes-abc",
            status_code=200,
            observed_at="2026-10-03T20:00:00Z",
            principal_id="principal_attacker_beta"
        )

        obs_id = self.graph.project_observation(
            endpoint_id=self.endpoint_id,
            obs_ref=obs_ref,
            verifies_hypothesis=self.hyp_id
        )

        # 断言假说状态变为 VERIFIED
        self.assertEqual(self.graph.get_hypothesis_state(self.hyp_id), HypothesisMemoryState.VERIFIED)
        
        # 断言边关系正确关联
        edges = self.graph.get_edges_from(obs_id, EdgeType.VERIFIES)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].target_id, self.hyp_id)

    def test_04_observation_projection_refutes_hypothesis_memory(self) -> None:
        """【契约 4】物理观测 (如收到 403) 证伪假说，记录为 REFUTED，防止智能体死循环"""
        self.graph.project_endpoint(self.endpoint_id, "GET", "/api/v1/orders/99901", self.asset_id)
        self.graph.project_hypothesis(self.hyp_id, self.endpoint_id, "authorization")

        obs_ref_blocked = ObservationRef(
            evidence_id="ev-128bit-hash-002",
            content_hash="sha256-403-bytes-def",
            status_code=403,
            observed_at="2026-10-03T20:01:00Z",
            principal_id="principal_attacker_beta"
        )

        self.graph.project_observation(
            endpoint_id=self.endpoint_id,
            obs_ref=obs_ref_blocked,
            refutes_hypothesis=self.hyp_id
        )

        # 断言已被明确证伪
        self.assertEqual(self.graph.get_hypothesis_state(self.hyp_id), HypothesisMemoryState.REFUTED)
        self.assertTrue(self.graph.is_hypothesis_refuted(self.hyp_id))

    def test_05_query_tested_principals_for_endpoint(self) -> None:
        """【契约 5】图谱准确回答端点已测试主体凭据清单，暴露盲区"""
        self.graph.project_endpoint(self.endpoint_id, "GET", "/api/v1/orders/99901", self.asset_id)

        # 第一次观测: 匿名访问
        obs1 = ObservationRef("ev-1", "hash-1", 401, "time1", principal_id="anonymous")
        self.graph.project_observation(self.endpoint_id, obs1)

        # 第二次观测: 受害者自身
        obs2 = ObservationRef("ev-2", "hash-2", 200, "time2", principal_id="victim_alpha")
        self.graph.project_observation(self.endpoint_id, obs2)

        tested = self.graph.get_tested_principals_for_endpoint(self.endpoint_id)
        self.assertEqual(tested, {"anonymous", "victim_alpha"})
        self.assertNotIn("attacker_beta", tested, "正确暴露潜在攻击者尚未测试的盲区")

    def test_06_project_canonical_evidence_unfolds_complete_provenance_topology(self) -> None:
        """【契约 6】原生物理桥接: 传入真实的 EndpointIR 与 EvidenceRecord，自动展开全拓扑"""
        from harness.domain_contracts import (
            EndpointIR,
            EvidenceRecord,
            HTTPRequestLog,
            HTTPResponseLog,
            AuthPrincipal
        )

        endpoint = EndpointIR(method="GET", path="/api/v1/orders/99901", endpoint_id="GET:/api/v1/orders/99901")
        principal = AuthPrincipal(
            principal_id="principal_attacker_beta",
            role="authenticated_user",
            tenant_id="tenant_beta",
            credential_fingerprint="fp_cred_123"
        )
        evidence = EvidenceRecord(
            endpoint=endpoint,
            request=HTTPRequestLog(method="GET", url="https://api.ikuai8.com/api/v1/orders/99901"),
            response=HTTPResponseLog(status_code=200, body_preview='{"order_id": 99901}'),
            principal=principal,
            content_hash="sha256-phys-bytes-99901",
            evidence_id="ev:phys:order:99901"
        )

        # 预先挂载假说
        self.graph.project_endpoint(endpoint.endpoint_id, "GET", "/api/v1/orders/99901", "asset:api.ikuai8.com")
        self.graph.project_hypothesis("H-IDOR-ORDERS", endpoint.endpoint_id, "authorization")

        # 执行原生桥接投影
        obs_id = self.graph.project_canonical_evidence(
            endpoint=endpoint,
            evidence=evidence,
            verifies_hypothesis="H-IDOR-ORDERS"
        )

        # 1. 断言资产节点自动生成
        asset_node = self.graph.get_node("asset:api.ikuai8.com")
        self.assertIsNotNone(asset_node)
        self.assertEqual(asset_node.node_type, NodeType.ASSET)

        # 2. 断言主体节点自动生成并关联 AUTHENTICATES
        p_node = self.graph.get_node("principal:principal_attacker_beta")
        self.assertIsNotNone(p_node)
        self.assertEqual(p_node.properties["tenant_id"], "tenant_beta")
        auth_edges = self.graph.get_edges_from("principal:principal_attacker_beta", EdgeType.AUTHENTICATES)
        self.assertEqual(len(auth_edges), 1)
        self.assertEqual(auth_edges[0].target_id, endpoint.endpoint_id)

        # 3. 断言假说状态被成功实锤为 VERIFIED
        self.assertEqual(self.graph.get_hypothesis_state("H-IDOR-ORDERS"), HypothesisMemoryState.VERIFIED)
