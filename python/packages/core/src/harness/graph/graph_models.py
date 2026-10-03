# -*- coding: utf-8 -*-
"""
Invar 权威研究状态图谱数据模型 (Canonical ResearchGraph Models)
对标顶级安全工程标准：Graph 纯粹作为物理事实 (ExecutionRecord/EvidenceRecord) 的投影 (Projection)，
严禁作为第二套事实真理源。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set
import hashlib
import json

class NodeType(str, Enum):
    ASSET = "ASSET"
    ENDPOINT = "ENDPOINT"
    PRINCIPAL = "PRINCIPAL"
    HYPOTHESIS = "HYPOTHESIS"
    OBSERVATION = "OBSERVATION"
    FINDING = "FINDING"

class EdgeType(str, Enum):
    EXPOSES = "EXPOSES"                    # Asset -> Endpoint
    AUTHENTICATES = "AUTHENTICATES"        # Principal -> Endpoint
    TARGETS = "TARGETS"                    # Hypothesis -> Endpoint
    PRODUCED = "PRODUCED"                  # Endpoint -> Observation
    VERIFIES = "VERIFIES"                  # Observation -> Hypothesis
    REFUTES = "REFUTES"                    # Observation -> Hypothesis
    SUPPORTS = "SUPPORTS"                  # Observation -> Finding

class HypothesisMemoryState(str, Enum):
    PROPOSED = "PROPOSED"
    TESTING = "TESTING"
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"

@dataclass(frozen=True)
class GraphNode:
    """
    状态图谱通用节点基类
    """
    node_id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GraphEdge:
    """
    状态图谱有向边契约
    """
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)

    @property
    def edge_key(self) -> str:
        return f"{self.source_id}->{self.edge_type.value}->{self.target_id}"

@dataclass(frozen=True)
class ObservationRef:
    """
    物理观测弱引用 (Projection Voucher)
    严密绑定源证据的物理唯一凭据与抗篡改 content_hash
    """
    evidence_id: str
    content_hash: str
    status_code: int
    observed_at: str
    principal_id: Optional[str] = None
