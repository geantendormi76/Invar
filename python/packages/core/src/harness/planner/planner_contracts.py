# -*- coding: utf-8 -*-
"""
Invar 权威实验规划与信息增益数据契约 (Canonical Experiment Planning Contracts)
对标 Shannon 与 RedAmon 黄金标准：
将盲目试探升级为以状态熵减和信息增益期望驱动的科学研究规划。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import hashlib
import json

from harness.tools.tool_contracts import HttpSendSpec

@dataclass(frozen=True)
class ExperimentCandidate:
    """
    待评估的单项候选研究实验实体
    """
    candidate_id: str
    endpoint_id: str
    hypothesis_id: str
    principal_id: str
    skill_name: str
    send_spec: HttpSendSpec
    is_destructive: bool = False
    estimated_latency_ms: float = 50.0

    def compute_fingerprint(self) -> str:
        raw = f"{self.endpoint_id}:{self.hypothesis_id}:{self.principal_id}:{self.skill_name}:{self.send_spec.method}:{self.send_spec.url}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

@dataclass(frozen=True)
class InformationGainScore:
    """
    信息增益与探索效用量化结果
    """
    expected_information_gain: float  # 0.0 ~ 10.0 (评估消除当前假说未决状态的期望)
    cost_penalty: float               # 0.0 ~ 5.0  (网络耗时与资源消耗)
    risk_penalty: float               # 0.0 ~ 10.0 (破坏性与交战风险)
    net_utility: float                # 综合效用净值 = Gain - Cost - Risk
    rationale: str                    # 决策理据

@dataclass(frozen=True)
class PlannedExperiment:
    """
    经由信息增益优化器决策并经 RoE 门禁核准的最终实验计划
    """
    candidate: ExperimentCandidate
    score: InformationGainScore
    is_roe_approved: bool
    selection_rank: int
