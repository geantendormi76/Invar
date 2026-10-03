# -*- coding: utf-8 -*-
"""
Invar 权威研究状态图谱与假说记忆引擎 (Canonical ResearchGraph Engine)
职责：
1. 投影构建：纯粹通过上游物理事实流 (EndpointIR, EvidenceRecord) 构建只读拓扑，绝不制造第二套事实；
2. 假说记忆：回答“该端点在特定凭据下，哪些假说已被证伪，哪些实验已完成”；
3. 拓扑查询：为决策层 (Brain) 提供当前未覆盖的身份交汇点与高价值目标。
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse

from harness.graph.graph_models import (
    NodeType,
    EdgeType,
    HypothesisMemoryState,
    GraphNode,
    GraphEdge,
    ObservationRef
)
from harness.domain_contracts import EndpointIR, EvidenceRecord

class ResearchGraph:
    """
    内存研究因果图谱与假说记忆中枢
    """

    def __init__(self, run_id: str = "RUN-GRAPH-001"):
        self.run_id = run_id
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        # 索引：邻接表 source -> edges, target -> edges
        self._out_edges: Dict[str, List[GraphEdge]] = {}
        self._in_edges: Dict[str, List[GraphEdge]] = {}

    def add_node(self, node: GraphNode) -> None:
        self._nodes[node.node_id] = node
        if node.node_id not in self._out_edges:
            self._out_edges[node.node_id] = []
        if node.node_id not in self._in_edges:
            self._in_edges[node.node_id] = []

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            raise KeyError(f"Both source '{edge.source_id}' and target '{edge.target_id}' must exist in graph")
        
        self._edges[edge.edge_key] = edge
        self._out_edges[edge.source_id].append(edge)
        self._in_edges[edge.target_id].append(edge)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_edges_from(self, source_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        edges = self._out_edges.get(source_id, [])
        if edge_type is None:
            return list(edges)
        return [e for e in edges if e.edge_type == edge_type]

    def get_edges_to(self, target_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        edges = self._in_edges.get(target_id, [])
        if edge_type is None:
            return list(edges)
        return [e for e in edges if e.edge_type == edge_type]

    # -------------------------------------------------------------
    # 状态投影快捷操作 (Projection Primitives)
    # -------------------------------------------------------------

    def project_endpoint(self, endpoint_id: str, method: str, path: str, asset_id: str = "asset-default") -> None:
        """投影端点及其与资产的归属关系"""
        if asset_id not in self._nodes:
            self.add_node(GraphNode(node_id=asset_id, node_type=NodeType.ASSET, label=asset_id))
        
        if endpoint_id not in self._nodes:
            ep_node = GraphNode(
                node_id=endpoint_id,
                node_type=NodeType.ENDPOINT,
                label=f"{method.upper()}:{path}",
                properties={"method": method.upper(), "path": path}
            )
            self.add_node(ep_node)
            self.add_edge(GraphEdge(source_id=asset_id, target_id=endpoint_id, edge_type=EdgeType.EXPOSES))

    def project_hypothesis(self, hypothesis_id: str, endpoint_id: str, attack_class: str, state: HypothesisMemoryState = HypothesisMemoryState.PROPOSED) -> None:
        """投影端点上挂载的安全假说及其当前状态"""
        if endpoint_id not in self._nodes:
            raise KeyError(f"Endpoint '{endpoint_id}' must exist before projecting hypothesis")

        if hypothesis_id not in self._nodes:
            h_node = GraphNode(
                node_id=hypothesis_id,
                node_type=NodeType.HYPOTHESIS,
                label=hypothesis_id,
                properties={"attack_class": attack_class, "state": state.value}
            )
            self.add_node(h_node)
            self.add_edge(GraphEdge(source_id=hypothesis_id, target_id=endpoint_id, edge_type=EdgeType.TARGETS))

    def project_observation(
        self,
        endpoint_id: str,
        obs_ref: ObservationRef,
        verifies_hypothesis: Optional[str] = None,
        refutes_hypothesis: Optional[str] = None
    ) -> str:
        """
        将物理 EvidenceRecord 投影为 Observation 节点并更新假说因果链
        绝不重新制造事实，强制绑定源物理证据凭证
        """
        obs_node_id = f"obs:{obs_ref.evidence_id}"
        obs_node = GraphNode(
            node_id=obs_node_id,
            node_type=NodeType.OBSERVATION,
            label=f"HTTP {obs_ref.status_code}",
            properties={
                "evidence_id": obs_ref.evidence_id,
                "content_hash": obs_ref.content_hash,
                "status_code": obs_ref.status_code,
                "principal_id": obs_ref.principal_id
            }
        )
        self.add_node(obs_node)
        self.add_edge(GraphEdge(source_id=endpoint_id, target_id=obs_node_id, edge_type=EdgeType.PRODUCED))

        # 关联假说验证状态
        if verifies_hypothesis and verifies_hypothesis in self._nodes:
            self.add_edge(GraphEdge(source_id=obs_node_id, target_id=verifies_hypothesis, edge_type=EdgeType.VERIFIES))
            old_h = self._nodes[verifies_hypothesis]
            new_props = dict(old_h.properties)
            new_props["state"] = HypothesisMemoryState.VERIFIED.value
            self._nodes[verifies_hypothesis] = GraphNode(
                node_id=old_h.node_id,
                node_type=old_h.node_type,
                label=old_h.label,
                properties=new_props
            )

        if refutes_hypothesis and refutes_hypothesis in self._nodes:
            self.add_edge(GraphEdge(source_id=obs_node_id, target_id=refutes_hypothesis, edge_type=EdgeType.REFUTES))
            old_h = self._nodes[refutes_hypothesis]
            new_props = dict(old_h.properties)
            new_props["state"] = HypothesisMemoryState.REFUTED.value
            self._nodes[refutes_hypothesis] = GraphNode(
                node_id=old_h.node_id,
                node_type=old_h.node_type,
                label=old_h.label,
                properties=new_props
            )

        return obs_node_id

    def project_canonical_evidence(
        self,
        endpoint: EndpointIR,
        evidence: EvidenceRecord,
        verifies_hypothesis: Optional[str] = None,
        refutes_hypothesis: Optional[str] = None
    ) -> str:
        """
        【原生物理桥接】直接从标准 EndpointIR 与 EvidenceRecord 投影拓扑
        自动解析归属资产、身份主体与物理凭据哈希
        """
        # 1. 提取资产与端点
        parsed_url = urlparse(evidence.request.url)
        asset_id = f"asset:{parsed_url.hostname or 'unknown-host'}"
        ep_id = endpoint.endpoint_id or f"{endpoint.method.upper()}:{endpoint.path}"
        self.project_endpoint(endpoint_id=ep_id, method=endpoint.method, path=endpoint.path, asset_id=asset_id)

        # 2. 若物证带有主体血统 (Principal)，投影主体节点并关联 AUTHENTICATES
        principal_id = None
        if evidence.principal is not None:
            principal_id = evidence.principal.principal_id
            p_node_id = f"principal:{principal_id}"
            if p_node_id not in self._nodes:
                self.add_node(GraphNode(
                    node_id=p_node_id,
                    node_type=NodeType.PRINCIPAL,
                    label=principal_id,
                    properties={
                        "role": evidence.principal.role,
                        "tenant_id": evidence.principal.tenant_id,
                        "credential_fingerprint": evidence.principal.credential_fingerprint
                    }
                ))
            edge_key = f"{p_node_id}->{EdgeType.AUTHENTICATES.value}->{ep_id}"
            if edge_key not in self._edges:
                self.add_edge(GraphEdge(source_id=p_node_id, target_id=ep_id, edge_type=EdgeType.AUTHENTICATES))

        # 3. 构造物证弱引用并投影 Observation
        obs_ref = ObservationRef(
            evidence_id=evidence.evidence_id,
            content_hash=evidence.content_hash,
            status_code=evidence.response.status_code,
            observed_at=evidence.observed_at,
            principal_id=principal_id
        )

        return self.project_observation(
            endpoint_id=ep_id,
            obs_ref=obs_ref,
            verifies_hypothesis=verifies_hypothesis,
            refutes_hypothesis=refutes_hypothesis
        )

    # -------------------------------------------------------------
    # 假说记忆与盲区查询 (Memory Queries for Research Brain)
    # -------------------------------------------------------------

    def get_hypothesis_state(self, hypothesis_id: str) -> Optional[HypothesisMemoryState]:
        """获取特定假说当前经由物理事实判定的状态"""
        node = self.get_node(hypothesis_id)
        if not node or node.node_type != NodeType.HYPOTHESIS:
            return None
        return HypothesisMemoryState(node.properties.get("state", HypothesisMemoryState.PROPOSED.value))

    def is_hypothesis_refuted(self, hypothesis_id: str) -> bool:
        """判定假说是否已被事实确凿证伪 (避免智能体死循环探索)"""
        return self.get_hypothesis_state(hypothesis_id) == HypothesisMemoryState.REFUTED

    def get_tested_principals_for_endpoint(self, endpoint_id: str) -> Set[str]:
        """查询某端点已经使用哪些身份凭据发包观测过"""
        obs_edges = self.get_edges_from(endpoint_id, EdgeType.PRODUCED)
        tested = set()
        for e in obs_edges:
            obs_node = self.get_node(e.target_id)
            if obs_node and obs_node.properties.get("principal_id"):
                tested.add(obs_node.properties["principal_id"])
        return tested
