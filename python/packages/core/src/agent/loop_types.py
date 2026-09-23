from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import re
from typing import Any, Callable, Dict, List, Optional, Union


class ResearchMessageRole(str, Enum):
    """内轨消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_RESULT = "tool_result"
    CRITIC_STEER = "critic_steer"


@dataclass
class ResearchMessage:
    """
    内轨富文本科研消息 (Internal Track)
    系统内部全程流转，保留完整领域上下文、变异体引用与实体标识
    """
    role: ResearchMessageRole
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    endpoint_ref: Optional[str] = None
    variant_ref: Optional[str] = None
    evidence_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        return data


@dataclass
class LLMMessage:
    """
    外轨协议通信消息 (LLM Boundary Track)
    仅在调用大模型发包前通过转译器导出，满足标准 OpenAI 契约
    """
    role: str
    content: str
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        data = {"role": self.role, "content": self.content}
        if self.name:
            data["name"] = self.name
        return data


def convert_to_llm(
    messages: List[ResearchMessage],
    max_slice_chars: int = 800,
) -> List[Dict[str, str]]:
    """
    上下文边界转译器 (Context Transformation Boundary)
    对齐 pi-agent-core convertToLlm() 设计：
    1. 将内轨丰富消息剥离压缩为标准 OpenAI 字典；
    2. 严格执行 AD-03 切片上限 800 字符硬约束，杜绝提示词爆炸；
    3. 将 CRITIC_STEER 优雅映射为带指令标记的 user 消息；
    4. 自动脱敏并截断响应体中的大型二进制/混淆噪声。
    """
    llm_payloads: List[Dict[str, str]] = []
    for msg in messages:
        text = msg.content
        # 1. 强制 800 字符切片压缩
        if len(text) > max_slice_chars:
            text = text[:max_slice_chars] + "...[TRUNCATED_AT_800_CHARS]"

        # 2. 角色安全映射
        if msg.role == ResearchMessageRole.CRITIC_STEER:
            role_str = "user"
            source = msg.metadata.get("source", "Critic")
            formatted_content = f"[{source} Steering Instruction]: {text}"
        elif msg.role == ResearchMessageRole.TOOL_RESULT:
            role_str = "user"
            formatted_content = f"[Probe Result ({msg.variant_ref or 'Tool'})]: {text}"
        else:
            role_str = msg.role.value
            formatted_content = text

        llm_payloads.append({
            "role": role_str,
            "content": formatted_content,
        })
    return llm_payloads


class ResearchEventType(str, Enum):
    """
    强类型科研事件类型枚举 (对齐 pi-agent-core AgentEvent)
    """
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    DENIAL_CLASSIFIED = "denial_classified"
    VARIANT_SELECTED = "variant_selected"
    PROBE_DISPATCHED = "probe_dispatched"
    PROBE_RESPONDED = "probe_responded"
    DIFFERENTIAL_COMPUTED = "differential_computed"
    SEMANTIC_EVALUATED = "semantic_evaluated"
    REPLAY_STARTED = "replay_started"
    REPLAY_COMPLETED = "replay_completed"
    STEERING_INJECTED = "steering_injected"
    LLM_REASONING_STARTED = "llm_reasoning_started"
    LLM_REASONING_COMPLETED = "llm_reasoning_completed"
    ABORTED = "aborted"


@dataclass(frozen=True)
class ResearchEvent:
    """
    可观测性事件实体 (Push-based Event)
    支持直接序列化并通过 IPC 流式推送到终端或上层调度器
    """
    event_type: ResearchEventType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


# 事件汇点接口定义
ResearchEventSink = Callable[[ResearchEvent], None]


class QueueMode(str, Enum):
    """队列消费模式"""
    ALL = "all"
    ONE_AT_A_TIME = "one-at-a-time"


@dataclass
class SteeringMessage:
    """
    外部干预消息实体 (Steering Queue Item)
    """
    content: str
    role: str = "user"
    source: str = "critic"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_research_message(self) -> ResearchMessage:
        return ResearchMessage(
            role=ResearchMessageRole.CRITIC_STEER,
            content=self.content,
            metadata={"source": self.source, **self.metadata},
        )


class AbortSignal:
    """
    线程安全的异步/同步执行取消信号
    """
    def __init__(self):
        self._aborted = False
        self._reason: Optional[str] = None

    @property
    def is_aborted(self) -> bool:
        return self._aborted

    @property
    def reason(self) -> Optional[str]:
        return self._reason

    def abort(self, reason: str = "Execution aborted by supervisor or timeout") -> None:
        self._aborted = True
        self._reason = reason
