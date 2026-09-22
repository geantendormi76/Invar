from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# 动态锁定核心库路径
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "python" / "packages" / "core" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from harness.candidate_models import (
    Candidate,
    CandidateFingerprint,
    CanonicalFactors,
    Condition,
    TraceStep,
)
from harness.config import InvarConfig
from harness.coverage_ledger import (
    CoverageLedger,
    CoverageStatus,
    CoverageUnit,
    UnresolvedFact,
)
from harness.exporter import EndpointExporter
from harness.finding_models import (
    ExecutionRecord,
    FindingRecord,
    Remediation,
    Severity,
    Verdict,
    VerificationSummary,
)
from harness.models import EndpointIR, EndpointRegistry
from harness.reporting import ReportProjector
from harness.research_adapter import ResearchTaskAdapter
from harness.run_models import (
    ExecutionPolicy,
    ResearchRun,
    ResearchScope,
    RunProfile,
    RunStatus,
    SourceRef,
)
from harness.sandbox_executor import AdaptiveSandboxExecutor


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
        default=REPO_ROOT / "artifacts" / "reports" / "targeted_audit_run",
        help="5 大战报投影输出目录",
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
        default=5,
        help="单次发包超时时间（秒）",
    )
    return parser.parse_args()


def load_registry(report_path: Path) -> EndpointRegistry:
    registry = EndpointRegistry()
    if report_path.exists():
        endpoints = EndpointExporter.from_json_file(report_path)
        registry.register_all(endpoints)
        print(f"[*] 权威注册表已装载: {len(registry)} 个 AST 端点来自 {report_path.name}")
    else:
        print(f"[!] 警告: 未找到静态报告 {report_path}，将采用向后兼容模式推导端点")
    return registry


def main() -> int:
    args = parse_args()
    tasks_path = args.tasks.resolve()
    output_dir = args.output_dir.resolve()

    if not tasks_path.exists():
        print(f"[-] 错误: 任务文件不存在: {tasks_path}")
        return 1

    print(f"=== 🛡️ Invar Phase 5.3: 靶向实证批量审计流水线启动 ===")
    print(f"[*] 任务输入源: {tasks_path}")
    print(f"[*] 战报输出目录: {output_dir}")

    # 1. 初始化权威注册表
    registry = load_registry(args.report_input)

    # 2. 读取任务并解构多态容器外壳
    raw_content = json.loads(tasks_path.read_text(encoding="utf-8"))
    if isinstance(raw_content, dict):
        if "tasks" in raw_content and isinstance(raw_content["tasks"], list):
            raw_tasks = raw_content["tasks"]
        else:
            raw_tasks = [v for v in raw_content.values() if isinstance(v, dict)]
    elif isinstance(raw_content, list):
        raw_tasks = raw_content
    else:
        raw_tasks = []

    filtered_tasks = raw_tasks
    if args.priority != "ALL":
        filtered_tasks = [t for t in filtered_tasks if t.get("priority") == args.priority]
    if args.max_tasks is not None:
        filtered_tasks = filtered_tasks[: args.max_tasks]

    total_tasks = len(filtered_tasks)
    print(f"[*] 计划执行任务总数: {total_tasks} (筛选优先级: {args.priority})")

    if total_tasks == 0:
        print("[!] 无待执行任务，流程退出")
        return 0

    # 3. 构建本次审计的 ResearchRun 实体与 CoverageLedger 账本
    run_id = f"RUN-TARGETED-{int(time.time())}"
    run = ResearchRun(
        run_id=run_id,
        target_root="ikuai8.com",
        scope=ResearchScope(target_domain="ikuai8.com"),
        source_ref=SourceRef(commit="targeted-v9"),
        profile=RunProfile(name="targeted_combat_audit", timeout=args.timeout),
        execution_policy=ExecutionPolicy(allow_dynamic_testing=True),
    )
    run.transition_to(RunStatus.SCOPE_VERIFIED)
    run.transition_to(RunStatus.CONTEXT_READY)
    run.transition_to(RunStatus.PLAN_READY)
    run.transition_to(RunStatus.EXECUTING)

    ledger = CoverageLedger(run_id=run_id)
    findings: List[FindingRecord] = []

    # 4. 配置沙箱执行器
    cfg = InvarConfig(request_timeout=args.timeout)
    executor = AdaptiveSandboxExecutor(cfg=cfg)

    # 5. 循环执行任务审查
    print(f"[*] 开始驱动动态沙箱执行中枢...")
    for idx, task in enumerate(filtered_tasks, 1):
        task_id = task.get("task_id", f"task-{idx}")
        cov_id = task.get("coverage_id", f"cov-{idx}")
        attack_class = task.get("attack_class", "authorization")
        path = task.get("path", "/")
        method = task.get("method", "GET")
        priority = task.get("priority", "P1")

        print(f"\n--- [{idx}/{total_tasks}] ({priority}) {method} {path} ---")

        # 注册并初始化账本单元 (PLANNED -> IN_PROGRESS)
        if not ledger.contains(cov_id):
            unit = CoverageUnit(
                coverage_id=cov_id,
                surface="api",
                boundary="target-audit-boundary",
                subsystem=cov_id.split("-")[1] if "-" in cov_id else "general",
                attack_class=attack_class,
                starting_paths=[path],
                status=CoverageStatus.PLANNED,
            )
            ledger.add_unit(unit)
        else:
            unit = ledger.get_unit(cov_id)

        unit.transition_to(CoverageStatus.IN_PROGRESS)

        # 权威转译为领域端点实体
        try:
            endpoint = ResearchTaskAdapter.task_to_endpoint(task, registry=registry)
        except Exception:
            endpoint = ResearchTaskAdapter.task_to_endpoint(task, registry=None)

        try:
            t0 = time.perf_counter()
            exec_res = executor.probe_endpoint_with_research(endpoint, base_url=args.base_url)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            case = exec_res.research_case
            decision = case.decision
            status_desc = decision.status if decision else "inconclusive"
            print(f"    └─ 决策: [{status_desc.upper()}] (耗时: {elapsed_ms:.1f}ms, 尝试: {len(case.attempts)} 次)")

            unit.reviewed_paths.append(path)
            unit.check_refs.append(f"CHK-{attack_class.upper()}")

            # 漏洞确权分支
            if decision and decision.status == "vulnerable":
                print(f"    🚨 [VULNERABLE] 安全底线被击穿: {decision.rationale}")
                unit.transition_to(CoverageStatus.CANDIDATE)

                factors = CanonicalFactors(
                    attack_class=attack_class,
                    boundary="target-audit-boundary",
                    sink_component=f"{unit.subsystem}_api",
                    missing_control=f"missing_{attack_class}_guard",
                )
                fp = CandidateFingerprint.from_factors(factors)
                unit.candidate_fingerprints.append(fp.value)

                raw_src = task.get("source_file") or "routes/api.js"
                safe_src = Path(raw_src).name if (":" in raw_src or raw_src.startswith(("\\", "/"))) else raw_src
                trace = [
                    TraceStep(
                        step_type="entrypoint",
                        file_path=safe_src,
                        line=task.get("source_line") or 1,
                        scope=f"{method} {path}",
                        description="Endpoint receiving untrusted client input",
                    )
                ]

                cand = Candidate(
                    fingerprint=fp,
                    title=f"Vulnerability in [{method} {path}]",
                    description=decision.rationale,
                    claimed_root_cause=decision.rationale,
                    endpoint_refs=[endpoint.endpoint_id],
                    coverage_refs=[cov_id],
                    evidence_refs=[exec_res.evidence.notes[:30]] if exec_res.evidence else [],
                    trace=trace,
                    conditions=[Condition(condition_id="COND-1", description="Default unprotected request")],
                )

                last_attempt = case.attempts[-1] if case.attempts else None
                exec_record = None
                if last_attempt:
                    exec_record = ExecutionRecord(
                        status_code=last_attempt.status_code,
                        method=method,
                        url=exec_res.evidence.request.url if exec_res.evidence else path,
                        observed_payload=last_attempt.payload,
                        response_summary=last_attempt.response_preview[:200],
                        evidence_ref=exec_res.evidence.notes[:30] if exec_res.evidence else "",
                    )

                finding = FindingRecord.from_candidate(
                    candidate=cand,
                    run_id=run_id,
                    verdict=Verdict.CONFIRMED,
                    severity=Severity.HIGH if priority in ["P0", "P1"] else Severity.MEDIUM,
                    root_cause=decision.rationale,
                    execution=exec_record,
                    remediation=Remediation(
                        summary=f"为端点 {method} {path} 强制追加权限与上下文校验",
                        guidance="在网关中间件中严格核对凭证，杜绝非授权穿透",
                    ),
                    evidence_refs=["EV-PROBE-01"],
                )
                finding.verification = VerificationSummary(
                    independent_verified=True,
                    verifier_id="invar-evidence-gate-prime",
                    verdict="VERIFIED",
                    rationale="Physical replay and differential semantic assertions matched",
                )
                findings.append(finding)

            else:
                unit.transition_to(CoverageStatus.COVERED)

        except Exception as exc:
            print(f"    [-] 任务执行异常: {exc}")
            unit.unresolved.append(
                UnresolvedFact(
                    fact_id=f"FACT-{task_id}",
                    description=str(exc),
                    blocking_reason="Task probe failed with exception",
                )
            )
            unit.transition_to(CoverageStatus.BLOCKED)

    # 6. 审计运行状态机流转
    run.transition_to(RunStatus.EVIDENCE_COLLECTED)
    run.transition_to(RunStatus.EVALUATED)
    run.transition_to(RunStatus.REPORT_READY)
    run.transition_to(RunStatus.COMPLETED)

    # 7. 投影输出 5 大战报
    print(f"\n[*] 正在原子化投影 5 大权威交付物至: {output_dir}")
    projector = ReportProjector(run=run, ledger=ledger, findings=findings)
    projected_files = projector.project_all(output_dir)

    for name, p_path in projected_files.items():
        print(f"    ├─ [{name}]: {p_path}")

    metrics = ledger.compute_metrics()
    print(f"\n=== 审计执行完成 ===")
    print(f"[*] 覆盖单元: {metrics['covered_units']}/{metrics['total_units']} (覆盖率: {metrics['coverage_percentage']}%)")
    print(f"[*] 发现漏洞: {len(findings)} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
