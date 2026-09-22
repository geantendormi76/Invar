from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set
from harness.denial_models import DenialCategory, DenialClassificationResult, FrontendComponent
from harness.transformation_models import TransformationFamily, TransformationVariant


@dataclass(frozen=True)
class PrioritizedExperiment:
    """
    附带优先级权重与信息增益理由的候选实验实体
    """
    variant: TransformationVariant
    priority_score: float
    selection_rationale: str
    expected_information_gain: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant": self.variant.to_dict(),
            "priority_score": round(self.priority_score, 2),
            "selection_rationale": self.selection_rationale,
            "expected_information_gain": round(self.expected_information_gain, 2),
        }


class AdaptiveExperimentSelector:
    """
    Invar 自适应实验选择器 (Adaptive Experiment Selector)
    对齐规格书第 16 节启发式与信息增益算法模型
    """

    def __init__(self, default_budget: int = 12):
        self.default_budget = default_budget

    def select(
        self,
        variants: List[TransformationVariant],
        classification: DenialClassificationResult,
        max_budget: Optional[int] = None,
        recent_failures: Optional[Set[str]] = None,
    ) -> List[PrioritizedExperiment]:
        budget = max_budget if max_budget is not None else self.default_budget
        failures = recent_failures or set()

        primary_hyp = classification.primary_hypothesis
        category = primary_hyp.category
        frontend = classification.frontend_component

        prioritized: List[PrioritizedExperiment] = []

        for v in variants:
            score = 1.0  # 基线分
            gain = 1.0
            reasons = []

            # -------------------------------------------------------------
            # 维度 1: 依据拒绝类别与拓扑组件匹配算法加权 (规格书第 16.1 节)
            # -------------------------------------------------------------
            if category == DenialCategory.METHOD_POLICY_DENIAL:
                # 405 动词拒绝场景：F2 动词语义与隧道享有最高特权
                if v.family == TransformationFamily.F2_METHOD_SEMANTICS:
                    score += 6.0
                    gain += 4.0
                    reasons.append("匹配 405 动词策略拒绝，大幅加权 F2 动词隧道与降级变异")
                else:
                    score -= 1.0

            elif category == DenialCategory.ACCESS_POLICY_DENIAL:
                # 403 访问控制场景
                if frontend == FrontendComponent.WAF:
                    # 遭遇明确 WAF 阻断：优先调用重写杀手锏与路径规范化
                    if "X_REWRITE_URL" in v.variant_id or "X_ORIGINAL_URL" in v.variant_id:
                        score += 8.0
                        gain += 5.0
                        reasons.append("遭遇 WAF 阻断，赋予代理重写头 (X-Rewrite-URL) 最高穿透优先级")
                    elif "PERCENT_DOT" in v.variant_id or "SEMICOLON" in v.variant_id:
                        score += 5.5
                        gain += 3.5
                        reasons.append("遭遇 WAF 阻断，高优先级调度规范化畸变 (%2e, ..;/ )")
                    elif v.family == TransformationFamily.F3_HEADER_TRUST_CONTEXT:
                        score += 4.0
                        gain += 2.5
                        reasons.append("调度请求头伪造以探测边缘与后端信任链")
                    else:
                        score += 2.0
                else:
                    # 纯净 403：可能系反代 ACL、动词拦截或内部鉴权
                    if "X_REWRITE_URL" in v.variant_id or "X_ORIGINAL_URL" in v.variant_id:
                        score += 6.0
                        gain += 4.0
                        reasons.append("调度重写头以探查内部映射分歧")
                    elif v.family == TransformationFamily.F3_HEADER_TRUST_CONTEXT:
                        score += 4.5
                        gain += 2.5
                        reasons.append("调度代理信任头与内网伪装以探查 ACL 绕过可能")
                    elif v.family == TransformationFamily.F1_PATH_NORMALIZATION:
                        score += 4.0
                        gain += 2.5
                        reasons.append("调度路径规范化以探查路由匹配分歧")

            elif category == DenialCategory.IDENTITY_OR_TRUST_CONTEXT:
                # 身份与来源受限场景：强力调度内网 IP 伪装头
                if any(k in v.variant_id for k in ["FORWARDED", "HOST", "CLIENT_IP", "REAL_IP"]):
                    score += 7.0
                    gain += 5.0
                    reasons.append("匹配内网来源受限，极高优先级派发内网可信 IP 伪造头")

            elif category == DenialCategory.ROUTING_MISMATCH:
                if v.family == TransformationFamily.F1_PATH_NORMALIZATION:
                    score += 5.0
                    gain += 3.5
                    reasons.append("匹配路由不匹配，优先派发路径畸变")

            # -------------------------------------------------------------
            # 维度 2: 高危动词阻断特征加权 (DELETE/PUT/PATCH 穿透特权)
            # -------------------------------------------------------------
            is_destructive_tunnel = (
                v.family == TransformationFamily.F2_METHOD_SEMANTICS
                and any(
                    v.headers.get(h) in {"DELETE", "PUT", "PATCH"}
                    for h in ["X-HTTP-Method-Override", "X-Method-Override", "X-HTTP-Method"]
                )
            )
            if is_destructive_tunnel:
                score += 6.5
                gain += 4.0
                reasons.append("针对高危动词 (DELETE/PUT)，高优先级调度动词隧道以探查代理层动词拦截")

            # -------------------------------------------------------------
            # 维度 3: 历史失败惩罚 (Failure Penalty)
            # -------------------------------------------------------------
            if v.variant_id in failures:
                score -= 3.0
                reasons.append("已在近期尝试中失败，施加优先级惩罚")

            # -------------------------------------------------------------
            # 维度 4: 算子自身信息增益先验
            # -------------------------------------------------------------
            if "X_REWRITE_URL" in v.variant_id or "PERCENT_DOT" in v.variant_id:
                score += 1.5

            rationale_text = "; ".join(reasons) if reasons else "常规探索性调度"

            prioritized.append(PrioritizedExperiment(
                variant=v,
                priority_score=score,
                selection_rationale=rationale_text,
                expected_information_gain=gain,
            ))

        # 稳定排序：评分降序，次级按 variant_id 升序保证确定性
        prioritized.sort(key=lambda x: (-x.priority_score, x.variant.variant_id))

        # -------------------------------------------------------------
        # 维度 5: 家族多样性采样 (Diversity Sampling，规格书第 16.3 节)
        # 避免同质内网 IP 伪造头占满前 12 个预算，为动词隧道、路径畸变与重写头留足名额
        # -------------------------------------------------------------
        selected: List[PrioritizedExperiment] = []
        ip_spoof_count = 0
        max_ip_spoofs = 3

        for exp in prioritized:
            v_id = exp.variant.variant_id
            if any(k in v_id for k in ["FORWARDED", "HOST", "CLIENT_IP", "REAL_IP", "REMOTE_IP"]):
                if ip_spoof_count >= max_ip_spoofs:
                    continue
                ip_spoof_count += 1
            selected.append(exp)
            if len(selected) >= budget:
                break

        return selected
