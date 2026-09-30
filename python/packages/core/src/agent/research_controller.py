from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from agent.loop_types import ResearchEvent, ResearchEventType
from agent.model_provider import OpenAICompatibleProvider
from harness.adaptive_selector import PrioritizedExperiment


# ==========================================================================
# 1. 有限动作空间 (Finite Action Space) —— 本轮仅表达两类动作
# ==========================================================================
class ResearchAction(str, Enum):
    """
    Control Plane 有限动作枚举 (Finite Action Enum)
    LLM 只能从该集合中选择，严禁自定义动作。
    """
    RUN_EXPERIMENT = "RUN_EXPERIMENT"  # 执行某个确定性候选 variant
    STOP = "STOP"                      # 安全终止研究


# ==========================================================================
# 2. 候选动作 (Candidate Action) —— 由确定性代码生成，LLM 不可自造
# ==========================================================================
@dataclass(frozen=True)
class CandidateAction:
    """
    单条研究候选动作 (确定性代码生成)
    向 LLM 暴露的均为非敏感描述：绝不包含 headers/payload 等密钥。
    """
    variant_id: str
    family: str
    method: str
    url: str
    expected_effect: str
    rationale: str

    @classmethod
    def from_prioritized(cls, exp: PrioritizedExperiment) -> "CandidateAction":
        v = exp.variant
        return cls(
            variant_id=v.variant_id,
            family=v.family.value,
            method=v.method,
            url=v.url,
            expected_effect=v.expected_effect,
            rationale=f"{v.rationale} [priority={exp.priority_score}]",
        )


# ==========================================================================
# 3. 研究状态快照 (Research Control State)
# ==========================================================================
@dataclass
class ResearchControlState:
    """
    交付给 LLM 决策的研究状态快照 (仅非敏感摘要)
    """
    current_status: str = "EXECUTING"
    tried_variants: Set[str] = field(default_factory=set)
    last_observation_summary: str = ""


# ==========================================================================
# 4. 强类型决策契约 (Strict Decision Contract)
# ==========================================================================
@dataclass(frozen=True)
class ControlPlaneDecision:
    """
    一次 LLM 调用只产出单一决策：
      action      -> 必须来自有限 Enum (RUN_EXPERIMENT / STOP)
      target_id   -> 必须属于当前候选集合 (STOP 时必为 null)
      reason      -> 有最大长度约束
      confidence  -> 必须位于 0..1
    """
    action: ResearchAction
    target_id: Optional[str] = None
    reason: str = ""
    confidence: float = 0.0

    @classmethod
    def validate(
        cls,
        raw: Any,
        candidate_ids: Set[str],
        max_reason_length: int,
    ) -> "ControlPlaneDecision":
        """
        严格校验 LLM 返回的原始 JSON。任何违背都抛出 ValueError。
        调用方据此 fail closed：绝不执行模型提出的未知内容。
        """
        if not isinstance(raw, dict):
            raise ValueError("Decision must be a JSON object")

        # action: 必须是字符串且属于有限 Enum (拒绝多 action / 自定义 action)
        action_raw = raw.get("action")
        if not isinstance(action_raw, str):
            raise ValueError("action must be a string (got non-string or list of actions)")
        try:
            action = ResearchAction(action_raw)
        except ValueError:
            raise ValueError(f"Unknown action: {action_raw!r}")

        # confidence: 必须为数值且位于 0..1 (bool 是 int 子类，显式排除)
        conf_raw = raw.get("confidence", 0.0)
        if isinstance(conf_raw, bool) or not isinstance(conf_raw, (int, float)):
            raise ValueError("confidence must be a number")
        confidence = float(conf_raw)
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence {confidence} out of range 0..1")

        # reason: 字符串且有最大长度约束
        reason = raw.get("reason", "")
        if not isinstance(reason, str):
            raise ValueError("reason must be a string")
        if len(reason) > max_reason_length:
            raise ValueError(
                f"reason length {len(reason)} exceeds max {max_reason_length}"
            )

        # target_id: RUN_EXPERIMENT 必须命中候选集合；STOP 必须为 null
        if action == ResearchAction.RUN_EXPERIMENT:
            target_id = raw.get("target_id")
            if not isinstance(target_id, str) or target_id not in candidate_ids:
                raise ValueError(
                    f"target_id {target_id!r} not in candidate set"
                )
        else:  # STOP
            if raw.get("target_id") is not None:
                raise ValueError("STOP decision must have target_id=null")
            target_id = None

        return cls(
            action=action,
            target_id=target_id,
            reason=reason,
            confidence=confidence,
        )


# ==========================================================================
# 5. 控制层配置 (Control Plane Config)
# ==========================================================================
@dataclass
class ControlPlaneConfig:
    """Control Plane 强约束参数"""
    max_reason_length: int = 500
    max_llm_attempts: int = 1  # 有界，禁止无限 retry


# ==========================================================================
# 6. ResearchController —— Research State + Candidate Actions
#    + LLM Decision + Decision Validation
# ==========================================================================
class ResearchController:
    """
    Invar Research Control Plane 控制决策层
    只负责：研究状态 + 候选动作 + LLM 决策 + 决策校验。
    不负责：HTTP / Transport / 变异构造 / 不变量评估 / 证据 / 上报。
    """

    def __init__(
        self,
        max_reason_length: int = 500,
        max_llm_attempts: int = 1,
    ):
        self.max_reason_length = max_reason_length
        self.max_llm_attempts = max_llm_attempts

    def decide(
        self,
        candidates: List[CandidateAction],
        state: ResearchControlState,
        llm_provider: Optional[OpenAICompatibleProvider] = None,
        emit: Optional[Callable[[ResearchEvent], None]] = None,
    ) -> ControlPlaneDecision:
        """
        从确定性候选中产出单一决策。

        Fail Closed 语义：
          * 无候选            -> STOP (安全终止)
          * 无 LLM provider   -> 确定性回退 (取最高优先级候选)
          * LLM 返回非法      -> 确定性回退，绝不执行未知内容
        绝不自动递归调用 LLM、绝不无限 retry、绝不字段猜测/隐式默认动作。
        """
        candidate_ids = {c.variant_id for c in candidates}

        def _fallback() -> ControlPlaneDecision:
            if candidates:
                return ControlPlaneDecision(
                    action=ResearchAction.RUN_EXPERIMENT,
                    target_id=candidates[0].variant_id,
                    reason="deterministic-fallback: highest-priority candidate",
                    confidence=0.0,
                )
            return ControlPlaneDecision(
                action=ResearchAction.STOP,
                target_id=None,
                reason="deterministic-fallback: no candidate actions available",
                confidence=0.0,
            )

        def _emit_requested() -> None:
            if emit is not None:
                emit(ResearchEvent(
                    event_type=ResearchEventType.CONTROL_DECISION_REQUESTED,
                    payload={"candidate_count": len(candidates)},
                ))

        def _emit_completed(decision: ControlPlaneDecision) -> None:
            if emit is not None:
                emit(ResearchEvent(
                    event_type=ResearchEventType.CONTROL_DECISION_COMPLETED,
                    payload={
                        "action": decision.action.value,
                        "target_id": decision.target_id,
                        "reason": decision.reason,
                        "confidence": decision.confidence,
                        "candidate_count": len(candidates),
                    },
                ))

        def _emit_rejected(error: str) -> None:
            if emit is not None:
                emit(ResearchEvent(
                    event_type=ResearchEventType.CONTROL_DECISION_REJECTED,
                    payload={"error": error},
                ))

        _emit_requested()

        # 无候选 -> 安全终止 (STOP)
        if not candidates:
            decision = _fallback()
            _emit_completed(decision)
            return decision

        # 无 LLM provider -> 确定性回退
        if llm_provider is None:
            decision = _fallback()
            _emit_completed(decision)
            return decision

        # 有界地调用一次 LLM，fail closed 回退
        try:
            prompt = self._build_prompt(candidates, state)
            raw = llm_provider.generate_structured_json(prompt)
            decision = ControlPlaneDecision.validate(
                raw, candidate_ids, self.max_reason_length
            )
        except Exception as exc:  # 非法 JSON / 未知 action / target 越界 / 越界 confidence / 超长 reason
            _emit_rejected(f"{type(exc).__name__}: {exc}")
            decision = _fallback()
            _emit_completed(decision)
            return decision

        _emit_completed(decision)
        return decision

    def _build_prompt(
        self,
        candidates: List[CandidateAction],
        state: ResearchControlState,
    ) -> List[Dict[str, str]]:
        """
        构造受约束 Prompt：LLM 只能在候选中选择，不能自造请求。
        绝不向模型暴露 headers/payload 等密钥。
        """
        cand_lines = [
            (
                f"- variant_id: {c.variant_id} | family: {c.family} | "
                f"method: {c.method} | url: {c.url} | "
                f"expected_effect: {c.expected_effect} | rationale: {c.rationale}"
            )
            for c in candidates
        ]
        system = (
            "You are Invar's research control decision layer. "
            "You must choose EXACTLY ONE next research action from the deterministic "
            "candidate actions below. Respond with a pure JSON object containing ONLY "
            "these keys: 'action' (string, 'RUN_EXPERIMENT' or 'STOP'), "
            "'target_id' (a variant_id string when action is RUN_EXPERIMENT, null when "
            "STOP), 'reason' (short string, at most 500 chars), "
            "'confidence' (a number between 0 and 1). "
            "Do NOT invent new variants. Do NOT return headers or payloads. "
            "Do NOT return prose instead of a decision."
        )
        user = (
            "Candidate actions (already generated deterministically by Invar):\n"
            + "\n".join(cand_lines)
            + "\nAlready tried variants: "
            + (", ".join(sorted(state.tried_variants)) if state.tried_variants else "none")
            + "\nLast observation summary: "
            + (state.last_observation_summary or "n/a")
            + "\nChoose the next action."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
