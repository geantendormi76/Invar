from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
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
from agent.research_controller import (
    CandidateAction,
    ControlPlaneConfig,
    ResearchAction,
    ResearchControlState,
    ResearchController,
)
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
    TransformationFamily,
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
    # Control Plane 显式功能缝 (feature seam)：默认关闭，旧路径行为不变。
    control_plane_enabled: bool = False
    controller: Optional[ResearchController] = None
    control_plane_config: Optional[ControlPlaneConfig] = None


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
    turn_history: List[Dict[str, Any]] = field(default_factory=list)
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



def format_poc_curl(variant: TransformationVariant) -> str:
    """
    将突破变异体原子化组装为可独立执行的标准 cURL 复现脚本 (PoC Command)
    """
    method = variant.method.upper()
    parts = [f"curl -s -i -X {method} '{variant.url}'"]
    for k, v in sorted(variant.headers.items()):
        parts.append(f"-H '{k}: {v}'")
    if variant.payload:
        data_str = json.dumps(variant.payload, ensure_ascii=False)
        parts.append(f"--data '{data_str}'")
    return " \
  ".join(parts)


def run_research_loop(
    context: ResearchLoopContext,
    config: ResearchLoopConfig,
    transport: HttpTransport,
    emit: Optional[ResearchEventSink] = None,
    signal: Optional[AbortSignal] = None,
) -> ResearchLoopResult:
    """
    Invar System-2 纯函数科研状态机算法 (Pure Functional Research Loop Algorithm)
    对齐 pi-agent-core runAgentLoop() 架构，支持两段式认知跃迁与软拒绝真实防线
    """
    def _emit(event_type: ResearchEventType, payload: Optional[Dict[str, Any]] = None) -> None:
        if emit is not None:
            emit(ResearchEvent(event_type=event_type, payload=payload or {}))

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
    last_response_preview = context.baseline_observation.body_preview
    # Control Plane 控制状态生命周期：last_observation_summary 随每轮真实 Observation 更新，
    # 供下一轮 _select_via_controller() 读取，形成 Observation feedback 闭环。
    max_decisions = (
        config.control_plane_config.max_decisions
        if config.control_plane_config is not None
        else config.max_budget
    )
    decisions_count = 0
    controller_stopped = False
    control_state = ResearchControlState(
        current_status="EXECUTING",
        tried_variants=set(context.tried_variants),
        last_observation_summary="",
    )

    # ------------------------------------------------------------------
    # 逐轮派发与语义评估 (提取为闭包，供阶段一与 Control Plane 阶段二复用)
    # 返回 True 表示达成突破，调用方据此中断循环。
    # ------------------------------------------------------------------
    def _run_turn(current_exp: PrioritizedExperiment) -> bool:
        nonlocal breakthrough, evidence_chain, last_response_preview, probes_count, public_root_preview
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
            last_response_preview = resp_var.text
        except Exception as exc:
            probes_count += 1
            _emit(ResearchEventType.PROBE_RESPONDED, {
                "status_code": 0,
                "error": str(exc),
            })
            _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": "transport_error"})
            return False

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
        context.turn_history.append({
            "turn": turn_index,
            "method": variant.method,
            "url": variant.url,
            "status_code": resp_var.status_code,
            "variant_id": variant.variant_id,
            "family": variant.family.value,
            "response_preview": resp_var.text[:200],
            "rationale": variant.rationale,
        })

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

        sem_result = SemanticEquivalenceEvaluator.evaluate(
            baseline=context.baseline_observation,
            candidate=cand_obs,
            variant=variant,
            expected_resource_markers=config.expected_resource_markers,
            public_root_preview=public_root_preview,
        )

        # 将本轮真实 Experiment Observation 的短摘要回写给 Control Plane state，
        # 供下一轮决策读取 (Observation feedback 闭环)。
        control_state.last_observation_summary = (
            f"status={resp_var.status_code} "
            f"semantic_verdict={sem_result.verdict.value} "
            f"differential_status_delta={sem_result.differential.status_delta} "
            f"body_preview={cand_obs.body_preview[:200]}"
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
            return False

        # 核心防线：判断是否算作真正突破（排除软拒绝与 SPA 首页 HTML 200 回退）
        is_soft = DeterministicDenialClassifier._parse_soft_denial(cand_obs) is not None
        is_html = cand_obs.body_preview.strip().lower().startswith(("<!doctype html", "<html"))

        if 200 <= resp_var.status_code <= 299 and not is_soft and not is_html:
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
                return False

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
                poc_code=format_poc_curl(variant),
            )
            context.evidence_chain = evidence_chain
            context.messages.append(ResearchMessage(
                role=ResearchMessageRole.TOOL_RESULT,
                content=f"Breakthrough verified via {variant.variant_id}: {resp_var.text[:200]}",
                variant_ref=variant.variant_id,
            ))
            _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": "breakthrough"})
            return True

        _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": "no_penetration"})
        return False

    # ------------------------------------------------------------------
    # Control Plane 决策缝：在真正 dispatch 下一 variant 之前，
    # 由 ResearchController 从确定性候选中选择单一研究动作。
    # 仅当 config.control_plane_enabled 时启用；默认关闭，旧路径行为不变。
    # ------------------------------------------------------------------
    def _select_via_controller() -> Optional[PrioritizedExperiment]:
        nonlocal decisions_count, controller_stopped
        if controller_stopped or decisions_count >= max_decisions:
            return None
        controller = (
            config.controller
            or ResearchController(
                max_reason_length=(config.control_plane_config.max_reason_length
                                   if config.control_plane_config else 500),
                max_llm_attempts=(config.control_plane_config.max_llm_attempts
                                  if config.control_plane_config else 1),
            )
        )
        candidates = [CandidateAction.from_prioritized(e) for e in prioritized_queue]
        control_state.tried_variants = set(context.tried_variants)
        control_state.current_status = "EXECUTING"
        decisions_count += 1
        decision = controller.decide(
            candidates=candidates,
            state=control_state,
            llm_provider=config.llm_provider,
            emit=(lambda evt: _emit(evt.event_type, evt.payload)) if emit is not None else None,
        )
        if decision.action == ResearchAction.STOP:
            controller_stopped = True
            return None
        # RUN_EXPERIMENT：target_id 已在 controller 内校验属于候选集合
        for i, exp in enumerate(prioritized_queue):
            if exp.variant.variant_id == decision.target_id:
                return prioritized_queue.pop(i)
        # Fail closed：target_id 解析失败时回退到最高优先级候选
        return prioritized_queue.pop(0)

    # 阶段一：常规启发式变异先锋 (Heuristic Turn Loop)
    while turn_index < config.max_turns and prioritized_queue:
        if signal is not None and signal.is_aborted:
            _emit(ResearchEventType.ABORTED, {"reason": signal.reason})
            break

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
        if config.control_plane_enabled:
            current_exp = _select_via_controller()
            if current_exp is None:
                outcome = "budget_exhausted" if decisions_count >= max_decisions else "controller_stop"
                _emit(ResearchEventType.TURN_END, {"turn": turn_index, "outcome": outcome})
                break
        else:
            current_exp = prioritized_queue.pop(0)
        if _run_turn(current_exp):
            break

    # 阶段二：Control Plane / 大模型认知反思破局
    llm_failed = False
    control_phase2_run = False
    if (
        not breakthrough
        and (signal is None or not signal.is_aborted)
    ):
        if config.control_plane_enabled:
            # 严格守卫：若控制器已明确决策 STOP，或决策预算已耗尽，严禁在 Phase 2 违背意图重复调用！
            if not controller_stopped and decisions_count < max_decisions and prioritized_queue:
                turn_index += 1
                chosen = _select_via_controller()
                if chosen is not None:
                    control_phase2_run = _run_turn(chosen)
            if control_phase2_run:
                breakthrough = True
        elif config.llm_provider is not None:
            print(f"    [*] 🧠 启发式未突破，正在唤醒本地大模型 ({config.llm_provider.model}) 开展 CoT 认知反思...")
            _emit(ResearchEventType.LLM_REASONING_STARTED, {
                "endpoint": context.endpoint.endpoint_id,
                "turns_prior": turn_index,
            })
            try:
                llm_prompt = [
                    {
                        "role": "system",
                        "content": (
                            "You are an API contract verification analyst. Analyze why the endpoint was blocked "
                            "and propose a specialized variant. Always return pure JSON with keys: "
                            "'rationale' (str), 'method' (str, HTTP method such as GET/POST/PUT/DELETE/PATCH), 'headers' (dict), 'payload' (dict)."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Endpoint: {context.endpoint.method} {context.endpoint.path}\n"
                            f"Extracted Params: {context.endpoint.extracted_params}\n"
                            f"Baseline Status: {context.baseline_observation.status_code}\n"
                            f"Error Sample: {last_response_preview[:300]}\n"
                            f"Tried Variants Count: {len(context.tried_variants)}"
                        ),
                    },
                ]
                llm_res = config.llm_provider.generate_structured_json(llm_prompt)
                if not isinstance(llm_res, dict):
                    raise ValueError("LLM action must be a JSON object")
                inferred_headers = llm_res.get("headers") or {}
                inferred_payload = llm_res.get("payload") or {}
                llm_rationale = llm_res.get("rationale")
                raw_inferred_method = llm_res.get("method")
                inferred_method = str(raw_inferred_method).upper() if raw_inferred_method else context.endpoint.method.upper()
                if not isinstance(llm_rationale, str):
                    raise ValueError("LLM action rationale must be a string")
                if not isinstance(inferred_headers, dict):
                    raise ValueError("LLM action headers must be an object")
                if not isinstance(inferred_payload, dict):
                    raise ValueError("LLM action payload must be an object")
                context.metadata["llm_terminal_status"] = "completed"
                print(f"    [+] 🧠 大模型反思完成！建议动词: {inferred_method}, 建议理据: {llm_rationale!r}")

                _emit(ResearchEventType.LLM_REASONING_COMPLETED, {
                    "inferred_headers": list(inferred_headers.keys()),
                    "inferred_method": inferred_method,
                    "rationale": llm_rationale,
                })

                # 构建大模型专属变异体并执行一次终审探测
                family = (
                    TransformationFamily.F2_METHOD_SEMANTICS
                    if inferred_method != context.endpoint.method.upper()
                    else TransformationFamily.F6_QUERY_BODY_PARSER
                )
                llm_variant = TransformationVariant(
                    variant_id="F6_LLM_COT_REASONED",
                    family=family,
                    method=inferred_method,
                    url=context.target_url,
                    headers=inferred_headers,
                    payload=inferred_payload,
                    rationale=llm_rationale,
                )
                turn_index += 1
                probes_count += 1
                resp_llm = transport.request(
                    method=llm_variant.method,
                    url=llm_variant.url,
                    payload=llm_variant.payload,
                    headers=llm_variant.headers,
                    timeout=5,
                )
                cand_llm_obs = DenialObservation(
                    status_code=resp_llm.status_code,
                    response_headers=dict(resp_llm.headers),
                    body_preview=resp_llm.text,
                )
                # 严格物证登记：将大模型建议的物理变异发包记录完整沉淀入 turn_history
                context.turn_history.append({
                    "turn": turn_index,
                    "method": llm_variant.method,
                    "url": llm_variant.url,
                    "status_code": resp_llm.status_code,
                    "variant_id": llm_variant.variant_id,
                    "family": llm_variant.family.value,
                    "response_preview": resp_llm.text[:200],
                    "rationale": f"[LLM-COT] {llm_rationale}",
                })
                sem_llm = SemanticEquivalenceEvaluator.evaluate(
                    baseline=context.baseline_observation,
                    candidate=cand_llm_obs,
                    variant=llm_variant,
                    expected_resource_markers=config.expected_resource_markers,
                    public_root_preview=public_root_preview,
                )
                is_llm_soft = DeterministicDenialClassifier._parse_soft_denial(cand_llm_obs) is not None
                is_llm_html = cand_llm_obs.body_preview.strip().lower().startswith(("<!doctype html", "<html"))

                if 200 <= resp_llm.status_code <= 299 and not is_llm_soft and not is_llm_html and sem_llm.verdict != EquivalenceVerdict.DIFFERENT_RESOURCE:
                    breakthrough = True
                    evidence_chain = EvidenceChain(
                        chain_id=f"CHAIN-{context.endpoint.endpoint_id}-LLM-COT",
                        target_domain=parsed_url.netloc,
                        is_scope_verified=True,
                        baseline_observation=context.baseline_observation,
                        applied_variant=llm_variant,
                        candidate_observation=cand_llm_obs,
                        semantic_result=sem_llm,
                        security_invariant_violated=True,
                        invariant_rationale=f"大模型思维链推断算子成功突破边界: {llm_rationale}",
                        replay_record=ReplayRecord(
                            total_replays=1,
                            successful_replays=1,
                            is_stable=True,
                            reproduced_status_codes=[resp_llm.status_code],
                            rationale="LLM 变异单发核验通过",
                        ),
                        verdict=EvidenceVerdict.CANDIDATE,
                        verdict_rationale=sem_llm.rationale,
                        poc_code=format_poc_curl(llm_variant),
                    )
                    context.evidence_chain = evidence_chain
            except Exception as e:
                llm_failed = True
                context.metadata["llm_terminal_status"] = "failed"
                context.metadata["llm_error"] = str(e)
                _emit(ResearchEventType.LLM_REASONING_FAILED, {
                    "error_type": type(e).__name__,
                    "message": str(e),
                })
                print(f"    [-] ⚠️ 大模型反思阶段异常: {e}")

    if config.follow_up_queue:
        follow_up_msg = config.follow_up_queue.pop(0)
        context.messages.append(follow_up_msg.to_research_message())

    final_verdict = EvidenceVerdict.CANDIDATE if breakthrough else EvidenceVerdict.REJECTED
    if llm_failed or (signal is not None and signal.is_aborted):
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
