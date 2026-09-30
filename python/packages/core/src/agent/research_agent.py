from __future__ import annotations

from dataclasses import field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

from agent.loop_types import (
    AbortSignal,
    QueueMode,
    ResearchEvent,
    ResearchEventSink,
    ResearchEventType,
    ResearchMessage,
    SteeringMessage,
)
from agent.model_provider import OpenAICompatibleProvider

# 哨兵：用于区分“未传 control_plane_enabled”与“显式传 False”，
# 保证默认行为不变、现有调用方无需修改。
_UNSET = object()
from agent.research_controller import ControlPlaneConfig, ResearchController
from agent.research_loop import (
    ResearchLoopConfig,
    ResearchLoopContext,
    ResearchLoopResult,
    run_research_loop,
)
from harness.adaptive_selector import AdaptiveExperimentSelector
from harness.denial_models import (
    DenialClassificationResult,
    DenialObservation,
    DeterministicDenialClassifier,
)
from harness.evidence_models import EvidenceVerdict
from harness.models import EndpointIR
from harness.semantic_models import SemanticEquivalenceEvaluator
from harness.transport import HttpTransport


class AgentState(str, Enum):
    """科研智能体生命周期状态机 (对齐 pi-agent-core AgentState)"""
    IDLE = "IDLE"
    RESEARCHING = "RESEARCHING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    ERROR = "ERROR"


class ResearchAgent:
    """
    Invar System-2 有状态科研智能体中枢 (Stateful Research Agent Controller)
    对齐 pi/packages/agent/src/agent.ts 架构，管理生命周期、事件总线分发与两级队列干预
    """

    def __init__(
        self,
        agent_id: str = "research-agent-prime",
        config: Optional[ResearchLoopConfig] = None,
        transport: Optional[HttpTransport] = None,
        llm_provider: Optional[OpenAICompatibleProvider] = None,
        control_plane_enabled: object = _UNSET,
        controller: Optional[ResearchController] = None,
        control_plane_config: Optional[ControlPlaneConfig] = None,
    ):
        self.agent_id = agent_id
        self.config = config or ResearchLoopConfig()
        self.transport = transport or HttpTransport()
        self.llm_provider = llm_provider
        if self.llm_provider:
            self.config.llm_provider = self.llm_provider
        # 显式 Control Plane 启用入口：仅当参数显式提供时才写入 config，
        # 默认 control_plane_enabled=False，旧路径行为不变。
        if control_plane_enabled is not _UNSET:
            self.config.control_plane_enabled = control_plane_enabled
        if controller is not None:
            self.config.controller = controller
        if control_plane_config is not None:
            self.config.control_plane_config = control_plane_config

        self._state = AgentState.IDLE
        self._listeners: Set[ResearchEventSink] = set()
        self._abort_signal: Optional[AbortSignal] = None
        self._last_result: Optional[ResearchLoopResult] = None

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def last_result(self) -> Optional[ResearchLoopResult]:
        return self._last_result

    def subscribe(self, listener: ResearchEventSink) -> Callable[[], None]:
        """
        订阅强类型微观事件流 (支持 Tauri 桌面端 / UI 实时响应)
        返回值: 取消订阅的可调用函数 (Unsubscribe Handle)
        """
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    def _emit(self, event: ResearchEvent) -> None:
        """广播事件给全部订阅者"""
        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception:
                pass

    def steer(self, content: str, source: str = "critic", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        向 Steering 队列注入动态干预指令 (对齐 agent.steer())
        在下一轮 Turn 发包前强制生效并调整推演策略
        """
        msg = SteeringMessage(content=content, source=source, metadata=metadata or {})
        self.config.steering_queue.append(msg)

    def follow_up(self, content: str, source: str = "critic", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        向 Follow-Up 队列注入追加任务 (对齐 agent.followUp())
        在当前突破收敛后顺延触发派生探索
        """
        msg = SteeringMessage(content=content, source=source, metadata=metadata or {})
        self.config.follow_up_queue.append(msg)

    def abort(self, reason: str = "Execution aborted by supervisor") -> None:
        """人工或超时熔断中止信号 (对齐 agent.abort())"""
        if self._abort_signal is not None:
            self._abort_signal.abort(reason)
        self._state = AgentState.ABORTED

    def reset(self) -> None:
        """重置内部队列与上下文状态"""
        self._state = AgentState.IDLE
        self.config.steering_queue.clear()
        self.config.follow_up_queue.clear()
        self._abort_signal = None
        self._last_result = None

    def run(self, context: ResearchLoopContext) -> ResearchLoopResult:
        """
        执行科研探索主循环
        """
        self._state = AgentState.RESEARCHING
        self._abort_signal = AbortSignal()

        try:
            result = run_research_loop(
                context=context,
                config=self.config,
                transport=self.transport,
                emit=self._emit,
                signal=self._abort_signal,
            )
            self._last_result = result
            if result.aborted:
                self._state = AgentState.ABORTED
            else:
                self._state = AgentState.COMPLETED
            return result
        except Exception as exc:
            self._state = AgentState.ERROR
            self._emit(ResearchEvent(
                event_type=ResearchEventType.ABORTED,
                payload={"error": str(exc), "agent_id": self.agent_id},
            ))
            raise

    def investigate_denial(
        self,
        endpoint: EndpointIR,
        url: str,
        baseline_observation: DenialObservation,
        classification: Optional[DenialClassificationResult] = None,
        expected_resource_markers: Optional[List[str]] = None,
        public_root_preview: Optional[str] = None,
    ) -> ResearchLoopResult:
        """
        高阶入口：对 403/405 拒绝响应端点开展全自动实证调查
        """
        cl = classification or DeterministicDenialClassifier.classify(baseline_observation)
        context = ResearchLoopContext(
            endpoint=endpoint,
            target_url=url,
            baseline_observation=baseline_observation,
            denial_classification=cl,
        )
        if expected_resource_markers:
            self.config.expected_resource_markers = expected_resource_markers
        if public_root_preview:
            self.config.public_root_preview = public_root_preview

        return self.run(context)
