import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
# 动态锁定核心库路径
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "python" / "packages" / "core" / "src"
import sys
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from harness.execution_trace import ExecutionTraceRecorder
from agent.knowledge_promoter import KnowledgeCard, KnowledgePromoter
from agent.model_provider import OpenAICompatibleProvider
from harness.candidate_models import Candidate, CandidateFingerprint, CanonicalFactors, TraceStep
from harness.config import InvarConfig
from harness.audit_checkpoint import (
    AuditCheckpoint,
    CheckpointError,
    compute_plan_digest,
    recover_trace_progress,
    repair_trace_tail,
    task_key,
)
from harness.coverage_ledger import (
    CoverageLedger,
    CoverageStatus,
    CoverageUnit,
    UnresolvedFact,
)
from harness.exporter import EndpointExporter
from harness.finding_models import ExecutionRecord, FindingRecord, Remediation, Severity, Verdict
from harness.models import EndpointIR, EndpointRegistry
from harness.domain_contracts import ResearchTaskContext
from harness.reporting import ReportProjector
from harness.research_adapter import ResearchTaskAdapter
from harness.run_models import ExecutionPolicy, ResearchRun, ResearchScope, RunProfile, RunStatus
from harness.sandbox_executor import AdaptiveSandboxExecutor
from harness.verification_gate import IndependentVerifier, PromotionGate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Invar System-2 靶向任务批量实证审计管道")
    parser.add_argument(
        "--tasks",
        type=Path,
        default=REPO_ROOT / "artifacts" / "reports" / "targeted_research_tasks_78.json",
        help="待审计的靶标任务集路径",
    )
    parser.add_argument(
        "--report-input",
        type=Path,
        default=REPO_ROOT / "tmp" / "ikuai8_endpoints_report.json",
        help="包含完整 AST 端点元数据的静态报告（用于填充 EndpointRegistry）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / "reports" / "targeted_audit_output",
        help="5 大战报及 OpenVEX 凭证投影输出目录",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="目标站点基地址覆盖（如 https://cloud.ikuai8.com）",
    )
    parser.add_argument(
        "--priority",
        type=str,
        choices=["P0", "P1", "P2", "P3", "ALL"],
        default="ALL",
        help="仅测试指定优先级的任务，默认 ALL",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="最大执行任务数上限（用于冒烟验证）",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="单次发包超时时间（秒）",
    )
    parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="激活 INVAR_LLM_BASE_URL 指向的本地模型进行结构化反思",
    )
    parser.add_argument(
        "--control-plane",
        action="store_true",
        help="启用 System-2 严格受限的 Research Control Plane 决策层",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="放弃输出目录中的既有断点并从第 1 项重新开始",
    )
    return parser.parse_args()


def load_registry(report_path: Path) -> EndpointRegistry:
    registry = EndpointRegistry()
    if report_path.exists():
        endpoints = EndpointExporter.from_json_file(report_path)
        registry.register_all(endpoints)
    return registry


def file_sha256(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_git_info() -> tuple[Optional[str], bool, Optional[str]]:
    import subprocess
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        status_out = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL).decode().strip()
        is_dirty = bool(status_out)
        diff_hash = None
        if is_dirty:
            diff_bytes = subprocess.check_output(["git", "diff", "HEAD"], stderr=subprocess.DEVNULL)
            diff_hash = hashlib.sha256(diff_bytes).hexdigest()
        return commit, is_dirty, diff_hash
    except Exception:
        return None, False, None

def make_executing_run(run_id: str, report_hash: Optional[str] = None) -> ResearchRun:
    from harness.run_models import RunTrack, SourceRef
    commit, dirty, diff_hash = get_git_info()
    source_ref = SourceRef(
        vcs="git",
        commit=commit,
        worktree_dirty=dirty,
        raw_input_hash=report_hash,
        diff_hash=diff_hash,
    )
    run = ResearchRun(
        track=RunTrack.RESEARCH,
        run_id=run_id,
        target_root="ikuai8.com",
        scope=ResearchScope(target_domain="ikuai8.com"),
        source_ref=source_ref,
        profile=RunProfile(name="targeted_combat_audit"),
        execution_policy=ExecutionPolicy(allow_dynamic_testing=True),
        status=RunStatus.INIT,
    )
    run.transition_to(RunStatus.SCOPE_VERIFIED)
    run.transition_to(RunStatus.CONTEXT_READY)
    run.transition_to(RunStatus.PLAN_READY)
    run.transition_to(RunStatus.EXECUTING)
    return run


def main() -> int:
    args = parse_args()
    tasks_path = args.tasks.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== 🛡️ Invar Phase 5.5: 靶向实证批量审计与 OpenVEX 终审流水线启动 ===")
    print(f"[*] 任务输入源: {tasks_path}")
    print(f"[*] 战报输出目录: {output_dir}")

    # 1. 装载权威注册表
    registry = load_registry(args.report_input)
    print(f"[*] 权威注册表已装载: {len(registry)} 个 AST 端点来自 {args.report_input.name}")

    # 2. 读取任务
    raw_content = json.loads(tasks_path.read_text(encoding="utf-8"))
    raw_tasks = raw_content.get("tasks", []) if isinstance(raw_content, dict) else raw_content
    filtered_tasks = raw_tasks
    if args.priority != "ALL":
        filtered_tasks = [t for t in filtered_tasks if t.get("priority") == args.priority]
    if args.max_tasks is not None:
        filtered_tasks = filtered_tasks[: args.max_tasks]

    total_tasks = len(filtered_tasks)
    print(f"[*] 计划执行任务总数: {total_tasks} (筛选优先级: {args.priority})")

    # 3. 初始化本地大模型提供者 (Phase 5.4 智能体点火)
    llm_provider = None
    if args.enable_llm:
        llm_provider = OpenAICompatibleProvider(
            api_key="sk-local-dev-key",
            timeout=120,
        )
        print(
            "[*] 🧠 已激活本地模型提供者: "
            f"{llm_provider.model} ({llm_provider.base_url})"
        )

    print("[*] 开始驱动动态沙箱执行中枢...\n")

    # 4. 初始化或恢复权威运行实体、账本与逐任务断点
    execution_log_path = output_dir / "execution.jsonl"
    checkpoint_path = output_dir / "audit_checkpoint.json"
    plan_options = {
        "priority": args.priority,
        "max_tasks": args.max_tasks,
        "timeout": args.timeout,
        "base_url": args.base_url,
        "report_input": str(args.report_input.resolve()),
        "report_input_sha256": file_sha256(args.report_input.resolve()),
        "llm_enabled": llm_provider is not None,
        "llm_base_url": llm_provider.base_url if llm_provider else None,
        "llm_model": llm_provider.model if llm_provider else None,
        "llm_timeout": llm_provider.timeout if llm_provider else None,
    }
    plan_digest = compute_plan_digest(filtered_tasks, plan_options)
    planned_task_keys = [
        task_key(task, index)
        for index, task in enumerate(filtered_tasks, 1)
    ]
    if len(planned_task_keys) != len(set(planned_task_keys)):
        print("[!] 任务集中存在重复 task_id，无法建立无歧义断点")
        return 2

    if args.restart:
        checkpoint_path.unlink(missing_ok=True)
        execution_log_path.unlink(missing_ok=True)
        print("[*] 已按 --restart 放弃既有断点，将从第 1 项重新执行")

    if repair_trace_tail(execution_log_path):
        print("[*] 已修复 execution.jsonl 的中断尾记录，保留此前完整任务")

    trace_exists = (
        execution_log_path.exists()
        and execution_log_path.stat().st_size > 0
    )

    try:
        if checkpoint_path.exists():
            checkpoint = AuditCheckpoint.load(checkpoint_path)
            if checkpoint.plan_digest != plan_digest:
                raise CheckpointError(
                    "断点对应的任务集或关键参数已改变；如确认重跑，请显式传入 --restart"
                )
            if checkpoint.total_tasks != total_tasks:
                raise CheckpointError(
                    "断点任务总数与当前计划不一致: "
                    f"{checkpoint.total_tasks} != {total_tasks}"
                )

            run = checkpoint.run
            ledger = checkpoint.ledger
            findings = checkpoint.findings

            if checkpoint.completed_task_keys and not trace_exists:
                raise CheckpointError(
                    "断点声明已有完成任务，但 execution.jsonl 缺失或为空"
                )

            if trace_exists:
                progress = recover_trace_progress(
                    execution_log_path,
                    filtered_tasks,
                    expected_total=total_tasks,
                )
                if progress is None or progress.run_id != run.run_id:
                    raise CheckpointError(
                        "execution.jsonl 与 checkpoint 的 run_id 不一致"
                    )
                checkpoint_keys = set(checkpoint.completed_task_keys)
                trace_keys = set(progress.completed_task_keys)
                if not checkpoint_keys.issubset(trace_keys):
                    raise CheckpointError(
                        "checkpoint 领先于 execution.jsonl，无法证明已完成任务的物理证据"
                    )

                # trace 先于 checkpoint 落盘时，从完整的 trace 记录恢复崩溃窗口。
                if trace_keys != checkpoint_keys:
                    checkpoint.completed_task_keys = progress.completed_task_keys
                    checkpoint.last_completed_index = progress.last_completed_index
                    ledger.units.update(progress.coverage_units)
                    known_findings = {f.finding_id: f for f in findings}
                    for finding in progress.findings:
                        known_findings[finding.finding_id] = finding
                    findings[:] = list(known_findings.values())
                    checkpoint.save_atomic(checkpoint_path)

            if (
                checkpoint.status in {"completed", "blocked"}
                and len(checkpoint.completed_task_keys) == total_tasks
            ):
                print(
                    "[*] 该执行计划已经结束，无需重复发包: "
                    f"status={checkpoint.status}, run_id={run.run_id}"
                )
                return 0 if checkpoint.status == "completed" else 1
        elif trace_exists:
            # 兼容升级前已经逐项落盘、但尚无 checkpoint 的中断运行。
            progress = recover_trace_progress(
                execution_log_path,
                filtered_tasks,
                expected_total=total_tasks,
            )
            if progress is None:
                raise CheckpointError("无法从非空 execution.jsonl 恢复执行进度")
            run = make_executing_run(progress.run_id, report_hash=file_sha256(args.report_input.resolve()))
            ledger = CoverageLedger(run_id=run.run_id)
            ledger.units.update(progress.coverage_units)
            findings = list(progress.findings)
            checkpoint = AuditCheckpoint(
                run=run,
                ledger=ledger,
                findings=findings,
                plan_digest=plan_digest,
                total_tasks=total_tasks,
                completed_task_keys=progress.completed_task_keys,
                last_completed_index=progress.last_completed_index,
            )
            checkpoint.save_atomic(checkpoint_path)
        else:
            run_id = f"RUN-TARGETED-{time.time_ns()}"
            run = make_executing_run(run_id, report_hash=file_sha256(args.report_input.resolve()))
            ledger = CoverageLedger(run_id=run_id)
            findings: List[FindingRecord] = []
            checkpoint = AuditCheckpoint(
                run=run,
                ledger=ledger,
                findings=findings,
                plan_digest=plan_digest,
                total_tasks=total_tasks,
            )
            checkpoint.save_atomic(checkpoint_path)
    except CheckpointError as exc:
        print(f"[!] 断点恢复失败: {exc}")
        return 2

    run_id = run.run_id
    completed_task_keys = set(checkpoint.completed_task_keys)
    if completed_task_keys:
        print(
            f"[*] 已恢复运行 {run_id}: "
            f"完成 {len(completed_task_keys)}/{total_tasks}，"
            "将自动跳过已落盘任务"
        )

    trace_recorder = ExecutionTraceRecorder(
        run_id=run_id,
        output_path=execution_log_path,
        total_tasks=total_tasks,
        llm_enabled=llm_provider is not None,
        llm_model=(
            llm_provider.model
            if llm_provider is not None
            else None
        ),
        append=trace_exists,
    )

    # 5. 配置沙箱执行器
    cfg = InvarConfig(request_timeout=args.timeout)
    executor = AdaptiveSandboxExecutor(
        cfg=cfg,
        llm_provider=llm_provider,
        control_plane_enabled=args.control_plane,
    )

    unsubscribe_trace = executor.research_agent.subscribe(
        trace_recorder.on_event
    )

    # 6. 循环执行任务审查
    for idx, task in enumerate(filtered_tasks, 1):
        task_id = task.get("task_id", f"task-{idx}")
        cov_id = task.get("coverage_id", f"cov-{idx}")
        attack_class = task.get("attack_class", "authorization")
        path = task.get("path", "/")
        method = task.get("method", "GET").upper()
        priority = task.get("priority", "P1")
        current_task_key = planned_task_keys[idx - 1]

        if current_task_key in completed_task_keys:
            print(
                f"--- [{idx}/{total_tasks}] ({priority}) {method} {path} "
                "[断点已完成，跳过] ---"
            )
            continue

        # 注册覆盖单元
        if not ledger.contains(cov_id):
            unit = CoverageUnit(
                coverage_id=cov_id,
                surface="api",
                boundary="combat-boundary",
                subsystem=task.get("subsystem") or "core",
                attack_class=attack_class,
                starting_paths=[path],
                status=CoverageStatus.PLANNED,
            )
            ledger.add_unit(unit)
        unit = ledger.get_unit(cov_id)
        if unit.status == CoverageStatus.PLANNED:
            unit.transition_to(CoverageStatus.IN_PROGRESS)

        # 权威转译端点
        try:
            endpoint = ResearchTaskAdapter.task_to_endpoint(task, registry=registry)
        except Exception:
            endpoint = ResearchTaskAdapter.task_to_endpoint(task, registry=None)

        print(f"--- [{idx}/{total_tasks}] ({priority}) {method} {path} ---")
        trace_recorder.begin_task(
            index=idx,
            task=task,
            endpoint=endpoint,
        )

        t0 = time.perf_counter()

        task_context = ResearchTaskContext.from_task_dict(task)
        try:
            exec_res = executor.probe_endpoint_with_research(
                endpoint,
                base_url=args.base_url,
                task_context=task_context,
            )

            elapsed_ms = (
                time.perf_counter() - t0
            ) * 1000.0

            case = exec_res.research_case
            decision = case.decision

        except BaseException as exc:
            elapsed_ms = (
                time.perf_counter() - t0
            ) * 1000.0

            trace_recorder.finalize_exception(
                task=task,
                endpoint=endpoint,
                error=exc,
                elapsed_ms=elapsed_ms,
                coverage_unit=ledger.get_unit(cov_id),
            )
            unsubscribe_trace()
            trace_recorder.close()
            raise
        status_raw = decision.status if decision else "inconclusive"
        # 语义去歧义：消除“安全守住”与“漏洞确权”同名 CONFIRMED 混淆
        if status_raw == "confirmed":
            semantic_label = "DEFENSE_HELD: 安全守住"
        elif status_raw == "vulnerable":
            semantic_label = "VULNERABLE: 漏洞确权"
        else:
            semantic_label = "INCONCLUSIVE: 证据未决"
        print(f"    └─ 审计决策: [{semantic_label}] (耗时: {elapsed_ms:.1f}ms, 尝试: {len(case.attempts)} 次)")

        # 漏洞确权分支
        task_finding: Optional[FindingRecord] = None
        if decision and decision.status == "vulnerable":
            print(f"    🚨 [VULNERABLE] 安全底线被击穿: {decision.rationale}")
            factors = CanonicalFactors(
                attack_class=attack_class,
                boundary="combat_boundary",
                sink_component=f"{task.get('subsystem', 'api')}_service",
                missing_control=f"missing_{attack_class}_guard",
            )
            fp = CandidateFingerprint.from_factors(factors)
            raw_src = task.get("source_file") or "routes/api.js"
            safe_src = Path(raw_src).name if (":" in raw_src or raw_src.startswith(("\\", "/"))) else raw_src
            trace = [
                TraceStep(
                    step_type="entrypoint",
                    file_path=safe_src,
                    line=task.get("source_line") or 1,
                    scope=f"{method} {path}",
                    description="AST endpoint receiving probe request",
                ),
                TraceStep(
                    step_type="sink",
                    file_path=safe_src,
                    line=task.get("source_line") or 1,
                    scope="serviceHandler",
                    description=f"Execution sink violating invariant: {decision.rationale}",
                ),
            ]
            cand = Candidate(
                fingerprint=fp,
                title=f"Vulnerability in [{method} {path}]",
                description=decision.rationale,
                claimed_root_cause=decision.rationale,
                endpoint_refs=[f"{method}:{path}"],
                coverage_refs=[cov_id],
                evidence_refs=[exec_res.evidence.notes[:30]] if exec_res.evidence else ["evidence-probe"],
                trace=trace,
            )
            # 提取 PoC 代码 (优先从 evidence_chain 提取，若无则根据微观发包物理事实即时组装)
            chain_meta = case.metadata.get("evidence_chain") or {}
            applied_meta = chain_meta.get("applied_variant") or {}
            effective_method = (applied_meta.get("method") or method).upper()
            effective_url = applied_meta.get("url") or executor._build_url(endpoint, base_url=args.base_url)
            poc_code = chain_meta.get("poc_code")

            last_attempt = case.attempts[-1] if case.attempts else None
            exec_record = ExecutionRecord(
                status_code=last_attempt.status_code if last_attempt else 200,
                method=effective_method,
                url=effective_url,
                response_summary=last_attempt.response_preview[:200] if last_attempt else "",
            )
            if not poc_code:
                poc_code = f"curl -s -i -X {effective_method} '{effective_url}'"

            finding = FindingRecord.from_candidate(
                candidate=cand,
                run_id=run_id,
                verdict=Verdict.CONFIRMED,
                severity=Severity.HIGH if priority in {"P0", "P1"} else Severity.MEDIUM,
                root_cause=decision.rationale,
                execution=exec_record,
                remediation=Remediation(
                    summary="建议加强权限拦截与参数校验",
                    guidance="在中间件中严格校验主体权限与业务参数合法性",
                ),
                poc_code=poc_code,
            )
            findings.append(finding)
            task_finding = finding
            if unit.status == CoverageStatus.IN_PROGRESS:
                unit.candidate_fingerprints.append(fp.value)
                unit.transition_to(CoverageStatus.CANDIDATE)
        else:
            # 无论单元此前是否已被置为 COVERED，当前任务的审查路径均必须幂等累加
            if path not in unit.reviewed_paths:
                unit.reviewed_paths.append(path)
            chk_ref = f"CHK-{attack_class.upper()}"
            if chk_ref not in unit.check_refs:
                unit.check_refs.append(chk_ref)

            if unit.status == CoverageStatus.IN_PROGRESS:
                if case.metadata.get("llm_terminal_status") == "failed":
                    unresolved_description = (
                        "本地大模型反思未完成: "
                        f"{case.metadata.get('llm_error', 'unknown error')}"
                    )
                elif decision is None:
                    unresolved_description = "任务未形成可验证的安全裁决"
                elif decision.status == "inconclusive":
                    unresolved_description = (
                        f"任务裁决仍不确定: {decision.rationale}"
                    )
                else:
                    unresolved_description = None

                if unresolved_description is not None:
                    unit.unresolved.append(
                        UnresolvedFact(
                            fact_id=f"UNRESOLVED-{task_id}",
                            description=unresolved_description,
                        )
                    )
                    unit.transition_to(CoverageStatus.BLOCKED)
                else:
                    unit.transition_to(CoverageStatus.COVERED)


        trace_recorder.finalize_task(
            task=task,
            endpoint=endpoint,
            execution_result=exec_res,
            coverage_unit=ledger.get_unit(cov_id),
            elapsed_ms=elapsed_ms,
            finding=task_finding,
        )

        # execution.jsonl 已 fsync 后再推进原子断点；崩溃窗口可由 trace 自愈。
        checkpoint.completed_task_keys.append(current_task_key)
        checkpoint.last_completed_index = idx
        checkpoint.status = "executing"
        checkpoint.save_atomic(checkpoint_path)
        completed_task_keys.add(current_task_key)

    unsubscribe_trace()
    trace_recorder.close()

    # 7. 状态机推进
    run.transition_to(RunStatus.EVIDENCE_COLLECTED)
    run.transition_to(RunStatus.EVALUATED)
    ledger.validate()
    pre_report_metrics = ledger.compute_metrics()
    if pre_report_metrics["blocked_units"]:
        run.transition_to(
            RunStatus.BLOCKED,
            reason=(
                f"{pre_report_metrics['blocked_units']} 个覆盖单元因证据未闭环而受阻"
            ),
        )
    else:
        run.transition_to(RunStatus.REPORT_READY)
        run.transition_to(RunStatus.COMPLETED)

    # 8. Phase 5.5: 独立复核、科学晋级门禁与 OpenVEX 黄金标准导出
    verifier = IndependentVerifier(verifier_id="invar-independent-verifier-prime")
    gate = PromotionGate()
    promoted_cards: List[KnowledgeCard] = []

    for f in findings:
        if f.verdict == Verdict.CONFIRMED:
            verifier.verify(f, originator_id="adaptive-sandbox-executor")
            if gate.is_promotable(f):
                card = KnowledgePromoter.promote_finding(f, gate=gate)
                promoted_cards.append(card)

    vex_doc = KnowledgePromoter.export_openvex_document(
        cards=promoted_cards,
        author="Invar System-2 / Independent Verifier",
        doc_id=f"https://invar.local/vex/{run_id}",
    )
    openvex_file = output_dir / "openvex.json"
    openvex_file.write_text(json.dumps(vex_doc, indent=2, ensure_ascii=False), encoding="utf-8")

    # 9. 投影输出 6 大战报及 OpenVEX
    print(f"\n[*] 正在原子化投影 6 大权威交付物及 OpenVEX 凭证至: {output_dir}")
    projector = ReportProjector(run=run, ledger=ledger, findings=findings)
    projected_files = projector.project_all(output_dir)
    for k, v in projected_files.items():
        print(f"    ├─ [{k}]: {v}")
    print(f"    └─ [openvex_json]: {openvex_file}")

    metrics = ledger.compute_metrics()
    print(f"\n=== 审计执行完成 ===")
    print(f"[*] 覆盖单元: {metrics['covered_units']}/{metrics['in_scope_units']} (覆盖率: {metrics['coverage_percentage']}%)")
    print(f"[*] 发现漏洞: {len(findings)} 个")
    print(f"[*] OpenVEX 声明生成: {len(promoted_cards)} 条")

    checkpoint.status = (
        "blocked" if run.status == RunStatus.BLOCKED else "completed"
    )
    checkpoint.save_atomic(checkpoint_path)
    print(f"[*] 断点状态已固化: {checkpoint_path}")

    return 1 if run.status == RunStatus.BLOCKED else 0


if __name__ == "__main__":
    sys.exit(main())

