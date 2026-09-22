from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from agent.loop_types import (
    AbortSignal,
    QueueMode,
    ResearchEvent,
    ResearchEventSink,
    ResearchEventType,
    ResearchMessage,
    ResearchMessageRole,
    SteeringMessage,
)
from agent.model_provider import OpenAICompatibleProvider
from harness.adaptive_selector import AdaptiveExperimentSelector, PrioritizedExperiment
from harness.denial_models import (
    DenialCategory,
    DenialClassificationResult,
    DenialObservation,
    DeterministicDenialClassifier,
)
from harness.evidence_models import (
    EvidenceChain,
    EvidenceGate,
    EvidenceVerdict,
    ReplayRecord,
)
from harness.models import EndpointIR
from harness.semantic_models import (
    EquivalenceVerdict,
    SemanticEquivalenceEvaluator,
    SemanticEquivalenceResult,
)
from harness.transformation_models import (
    TransformationFamilyRegistry,
    TransformationVariant,
)
from harness.transport import HttpTransport


@dataclass
class ResearchLoopConfig:
    """
    科研循环控制参数配置 (对齐 pi-agent-core AgentConfig)
    """
    max_turns: int = 12
    max_budget: int = 12
    queue_mode: QueueMode = QueueMode.ONE_AT_A_TIME
    steering_queue: List[SteeringMessage] = field(default_factory=list)
    follow_up_queue: List[SteeringMessage] = field(default_factory=list)
    selector: Optional[AdaptiveExperimentSelector] = None
    evaluator: Optional[SemanticEquivalenceEvaluator] = None
    expected_resource_markers: Optional[List[str]] = None
    public_root_preview: Optional[str] = None
    llm_provider: Optional[OpenAICompatibleProvider] = None


@dataclass
class ResearchLoopContext:
    """
    内轨科研上下文状态快照 (对齐 pi-agent-core AgentContext)
    """
    endpoint: EndpointIR
    target_url: str
    baseline_observation: DenialObservation
    denial_classification: DenialClassificationResult
    messages: List[ResearchMessage] = field(default_factory=list)
    tried_variants: Set[str] = field(default_factory=set)
    evidence_chain: Optional[EvidenceChain] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchLoopResult:
    """
    纯函数循环执行最终收敛结果
    """
    context: ResearchLoopContext
    final_verdict: EvidenceVerdict
    evidence_chain: Optional[EvidenceChain]
    turns_executed: int
    probes_dispatched: int
    breakthrough_achieved: bool
    aborted: bool
    abort_reason: Optional[str] = None


def run_research_loop(
    context: ResearchLoopContext,
    config: ResearchLoopConfig,
    transport: HttpTransport,
    emit: Optional[ResearchEventSink] = None,
    signal: Optional[AbortSignal] = None,
) -> ResearchLoopResult:
    """
    Invar System-2 纯函数科研状态机算法 (Pure Functional Research Loop Algorithm)
    对齐 pi-agent-core runAgentLoop() 架构，支持动态干预插队与微观事件推送
    """
    def _emit(event_type: ResearchEventType, payload: Optional[Dict[str, Any]] = None) -> None:
        if emit is not None:
            emit(ResearchEvent(event_type=event_type, payload=payload or {}))

    # 1. 启动科研循环事件
    _emit(ResearchEventType.LOOP_START, {
        "target_endpoint": context.endpoint.endpoint_id,
        "target_url": context.target_url,
        "baseline_status": context.baseline_observation.status_code,
    })

    _emit(ResearchEventType.DENIAL_CLASSIFIED, {
        "primary_hypothesis": context.denial_classification.primary_hypothesis.to_dict(),
        "frontend_component": context.denial_classification.frontend_component.value,
    })

    selector = config.selector or AdaptiveExperimentSelector(default_budget=config.max_budget)
    target_verb = context.endpoint.method.upper()

    raw_variants = TransformationFamilyRegistry.generate_all(
        url=context.target_url,
        method=context.endpoint.method,
        target_verb=target_verb,
    )

    pending_variants = [v for v in raw_variants if v.variant_id not in context.tried_variants]

    prioritized_queue = selector.select(
        variants=pending_variants,
        classification=context.denial_classification,
        max_budget=config.max_budget,
    )

    turn_index = 0
    probes_count = 0
    breakthrough = False
    evidence_chain: Optional[EvidenceChain] = None

    parsed_url = urlparse(context.target_url)
    root_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    public_root_preview = config.public_root_preview

    # 2. 轮次迭代主循环 (Turn-based Inner Loop)
    while turn_index < config.max_turns and prioritized_queue:
        if signal is not None and signal.is_aborted:
            _emit(ResearchEventType.ABORTED, {"reason": signal.reason})
            break

        # 轮询 Steering 队列 (动态干预插队机制)
        if config.steering_queue:
            steer_msgs_to_process = []
            if config.queue_mode == QueueMode.ONE_AT_A_TIME:
                steer_msgs_to_process.append(config.steering_queue.pop(0))
            else:
                steer_msgs_to_process.extend(config.steering_queue)
                config.steering_queue.clear()

            for s_msg in steer_msgs_to_process:
                r_msg = s_msg.to_research_message()
                context.messages.append(r_msg)
                _emit(ResearchEventType.STEERING_INJECTED, {
                    "source": s_msg.source,
                    "instruction": s_msg.content,
                })

        turn_index += 1
        current_exp: PrioritizedExperiment = prioritized_queue.pop(0)
        variant = current_exp.variant
        context.tried_variants.add(variant.variant_id)

        _emit(ResearchEventType.TURN_START, {
            "turn": turn_index,
            "variant_id": variant.variant_id,
            "family": variant.family.value,
            "priority_score": current_exp.priority_score,
            "rationale": current_exp.selection_rationale,
        })

        _emit(ResearchEventType.VARIANT_SELECTED, {
            "variant_id": variant.variant_id,
            "priority_score": current_exp.priority_score,
        })

        _emit(ResearchEventType.PROBE_DISPATCHED, {
            "method": variant.method,
            "url": variant.url,
            "headers": variant.headers,
        })

        try:
            resp_var = transport.request(
                method=variant.method,
                url=variant.url,
                payload=variant.payload,
                headers=variant.headers,
                timeout=5,
            )
            probes_count += 1
        except Exception as exc:
            probes_count += 1
            _emit(ResearchEventType.PROBE_RESPONDED, {
                "status_code": 0,
                "error": str(exc),
            })
            _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": "transport_error"})
            continue

        _emit(ResearchEventType.PROBE_RESPONDED, {
            "status_code": resp_var.status_code,
            "body_length": len(resp_var.text),
        })

        cand_obs = DenialObservation(
            status_code=resp_var.status_code,
            response_headers=dict(resp_var.headers),
            body_preview=resp_var.text,
            redirect_url=resp_var.headers.get("Location") or resp_var.headers.get("location"),
        )

        # 懒加载公共根路由预览 (彻底剔除重写头，保证纯净首页对照)
        if variant.url.rstrip("/") == root_url.rstrip("/") and public_root_preview is None:
            try:
                clean_root_headers = {
                    k: v for k, v in variant.headers.items()
                    if not k.lower().startswith(("x-rewrite", "x-original"))
                }
                resp_root = transport.request(
                    method="GET",
                    url=root_url,
                    payload={},
                    headers=clean_root_headers,
                    timeout=5,
                )
                public_root_preview = resp_root.text
            except Exception:
                pass

        # 差分计算与语义等价核验
        sem_result = SemanticEquivalenceEvaluator.evaluate(
            baseline=context.baseline_observation,
            candidate=cand_obs,
            variant=variant,
            expected_resource_markers=config.expected_resource_markers,
            public_root_preview=public_root_preview,
        )

        _emit(ResearchEventType.DIFFERENTIAL_COMPUTED, {
            "status_delta": sem_result.differential.status_delta,
            "body_hash_changed": sem_result.differential.body_hash_changed,
            "redirect_to_auth": sem_result.differential.redirect_to_auth_barrier,
        })

        _emit(ResearchEventType.SEMANTIC_EVALUATED, {
            "verdict": sem_result.verdict.value,
            "rationale": sem_result.rationale,
        })

        if sem_result.verdict == EquivalenceVerdict.DIFFERENT_RESOURCE:
            context.messages.append(ResearchMessage(
                role=ResearchMessageRole.TOOL_RESULT,
                content=f"Rejected: {sem_result.rationale}",
                variant_ref=variant.variant_id,
            ))
            _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": "rejected_different_resource"})
            continue

        # 连续同态重放验真 (Replay Verification)
        if 200 <= resp_var.status_code <= 299:
            _emit(ResearchEventType.REPLAY_STARTED, {"variant_id": variant.variant_id})
            replay_successes = 1
            total_replays = 2
            for _ in range(total_replays - 1):
                try:
                    rep_resp = transport.request(
                        method=variant.method,
                        url=variant.url,
                        payload=variant.payload,
                        headers=variant.headers,
                        timeout=5,
                    )
                    probes_count += 1
                    if 200 <= rep_resp.status_code <= 299:
                        replay_successes += 1
                except Exception:
                    pass

            is_stable = (replay_successes == total_replays)
            _emit(ResearchEventType.REPLAY_COMPLETED, {
                "is_stable": is_stable,
                "replays_matched": f"{replay_successes}/{total_replays}",
            })

            if not is_stable:
                context.messages.append(ResearchMessage(
                    role=ResearchMessageRole.TOOL_RESULT,
                    content="Replay unstable, marked inconclusive",
                    variant_ref=variant.variant_id,
                ))
                _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": "unstable_replay"})
                continue

            breakthrough = True
            evidence_chain = EvidenceChain(
                chain_id=f"CHAIN-{context.endpoint.endpoint_id}-{variant.variant_id}",
                target_domain=parsed_url.netloc,
                is_scope_verified=True,
                baseline_observation=context.baseline_observation,
                applied_variant=variant,
                candidate_observation=cand_obs,
                semantic_result=sem_result,
                security_invariant_violated=True,
                invariant_rationale=f"403拒绝边界被变异算子成功突破: {variant.rationale}",
                replay_record=ReplayRecord(
                    total_replays=total_replays,
                    successful_replays=replay_successes,
                    is_stable=True,
                    reproduced_status_codes=[resp_var.status_code] * replay_successes,
                    rationale="同态发包稳定性核验通过",
                ),
                verdict=EvidenceVerdict.CANDIDATE,
                verdict_rationale=sem_result.rationale,
            )
            context.evidence_chain = evidence_chain
            context.messages.append(ResearchMessage(
                role=ResearchMessageRole.TOOL_RESULT,
                content=f"Breakthrough verified via {variant.variant_id}: {resp_var.text[:200]}",
                variant_ref=variant.variant_id,
            ))
            _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": "breakthrough"})
            break

        _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": "no_penetration"})

    if config.follow_up_queue:
        follow_up_msg = config.follow_up_queue.pop(0)
        context.messages.append(follow_up_msg.to_research_message())

    final_verdict = EvidenceVerdict.CANDIDATE if breakthrough else EvidenceVerdict.REJECTED
    if signal is not None and signal.is_aborted:
        final_verdict = EvidenceVerdict.INCONCLUSIVE

    _emit(ResearchEventType.LOOP_END, {
        "final_verdict": final_verdict.value,
        "turns_executed": turn_index,
        "probes_dispatched": probes_count,
        "breakthrough_achieved": breakthrough,
    })

    return ResearchLoopResult(
        context=context,
        final_verdict=final_verdict,
        evidence_chain=evidence_chain,
        turns_executed=turn_index,
        probes_dispatched=probes_count,
        breakthrough_achieved=breakthrough,
        aborted=signal.is_aborted if signal else False,
        abort_reason=signal.reason if signal else None,
    )
