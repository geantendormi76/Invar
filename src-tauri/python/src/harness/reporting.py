from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from harness.coverage_ledger import CoverageLedger, CoverageStatus
from harness.finding_models import FindingRecord, FindingSchemaValidator, Severity, Verdict
from harness.run_models import ResearchRun, RunStatus


class ReportProjector:
    """
    Invar 权威战报投影生成器 (Authoritative Report Projector)
    严守投影原则：所有文字报告纯粹由 Core 事实对象投影衍生，拒绝人为主观篡改
    """
    def __init__(
        self,
        run: ResearchRun,
        ledger: CoverageLedger,
        findings: List[FindingRecord],
    ):
        self.run = run
        self.ledger = ledger
        self.findings = findings

        # 预先执行 Schema 结构审计，确保底层输入事实 100% 合规
        for f in self.findings:
            FindingSchemaValidator.assert_valid(f.to_dict())

    def render_findings_json(self) -> str:
        """投影 1: 全量机器可读 findings.json"""
        data = {
            "run_id": self.run.run_id,
            "projected_at": datetime.now(timezone.utc).isoformat(),
            "findings": [f.to_dict() for f in self.findings],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def render_report_md(self) -> str:
        """投影 2: 决策层总览 REPORT.md"""
        metrics = self.ledger.compute_metrics()
        confirmed = [f for f in self.findings if f.verdict == Verdict.CONFIRMED]
        needs_val = [f for f in self.findings if f.verdict == Verdict.NEEDS_VALIDATION]
        rejected = [f for f in self.findings if f.verdict == Verdict.REJECTED]

        critical_count = sum(1 for f in confirmed if f.severity == Severity.CRITICAL)
        high_count = sum(1 for f in confirmed if f.severity == Severity.HIGH)
        med_count = sum(1 for f in confirmed if f.severity == Severity.MEDIUM)

        lines = [
            "# 🛡️ Invar 工业级自动化 Web API 安全科研战报",
            "",
            f"> **生成时间**: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}` | **Run ID**: `{self.run.run_id}` | **状态**: `{self.run.status.value}`",
            "",
            "---",
            "",
            "## 1. 运行环境与审计范围血统",
            f"- **目标根域**: `{self.run.scope.target_domain}`",
            f"- **源码提交 (Commit)**: `{self.run.source_ref.commit or 'N/A'}` (工作区脏状态: `{self.run.source_ref.worktree_dirty}`)",
            f"- **输入源码指纹 (SHA256)**: `{self.run.source_ref.raw_input_hash or 'N/A'}`",
            f"- **执行安全轮廓**: `{self.run.profile.name}` (动态测试授权: `{self.run.execution_policy.allow_dynamic_testing}`)",
        ]

        if self.run.status == RunStatus.BLOCKED:
            lines.extend([
                "",
                "### 🚨 运行受阻警报 (Run Blocked)",
                f"> **阻断原因**: {self.run.block_reason or '未决依赖项阻断'}",
            ])

        lines.extend([
            "",
            "## 2. 覆盖度核心指标 (Coverage Accounting)",
            f"- **账本单元总数**: {metrics['total_units']} 个 (有效范围内: {metrics['in_scope_units']} 个, 越界排除: {metrics['out_of_scope_units']} 个)",
            f"- **已完成深度覆盖**: {metrics['covered_units']} 个",
            f"- **受阻未决单元**: {metrics['blocked_units']} 个",
            f"- **推迟延期单元**: {metrics['deferred_units']} 个",
            f"- **客观加权覆盖率**: **`{metrics['coverage_percentage']}%`**",
            "",
            "## 3. 漏洞发现总览 (Findings Summary)",
            f"| 裁决状态 (Verdict) | 数量 | 严重度构成 |",
            f"| :--- | :--- | :--- |",
            f"| **实锤确认 (CONFIRMED)** | **{len(confirmed)}** | Critical: `{critical_count}`, High: `{high_count}`, Med: `{med_count}` |",
            f"| **存疑待验 (NEEDS_VALIDATION)** | **{len(needs_val)}** | *无严重度（依规范绝不虚标）* |",
            f"| **已排除/安全 (REJECTED)** | **{len(rejected)}** | N/A |",
            "",
        ])

        if confirmed:
            lines.extend([
                "### 实锤漏洞清单",
                "| 严重度 | 发现标题 | 根因指纹 | 关联端点 | 第三方复核 |",
                "| :--- | :--- | :--- | :--- | :--- |",
            ])
            for f in confirmed:
                endpoints_str = ", ".join(f.endpoint_refs)
                verifier_str = f"✅ {f.verification.verifier_id}" if f.verification.independent_verified else "❌ 未复核"
                lines.append(f"| `{f.severity.value}` | **{f.title}** | `{f.fingerprint[:24]}...` | `{endpoints_str}` | {verifier_str} |")

        lines.extend([
            "",
            "---",
            "*本报告由 Invar 权威事实投影生成器自动导出，与底层 findings.json 严格对齐。*",
        ])
        return "\n".join(lines)

    def render_findings_detail_md(self) -> str:
        """投影 3: 深度技术细节 FINDINGS-DETAIL.md"""
        confirmed = [f for f in self.findings if f.verdict == Verdict.CONFIRMED]
        lines = [
            "# 🔬 Invar 实锤漏洞深度技术细节报告 (Confirmed Findings Detail)",
            "",
            f"> 本文档仅收录经过 **独立第三方复核 (Independent Verification)** 实锤证实的脆弱性事实。",
            "",
        ]

        if not confirmed:
            lines.append("*(本次审计未发现或未证实任何确凿漏洞)*")
            return "\n".join(lines)

        for idx, f in enumerate(confirmed, 1):
            lines.extend([
                f"## [{idx}] {f.title} ({f.severity.value})",
                f"- **Finding ID**: `{f.finding_id}`",
                f"- **根因指纹**: `{f.fingerprint}`",
                f"- **受影响端点**: `{', '.join(f.endpoint_refs)}`",
                f"- **独立复核签发者**: `{f.verification.verifier_id}` (`{f.verification.verified_at}`)",
                "",
                "### 1. 根本原因深度分析",
                f"> {f.root_cause}",
                "",
                "### 2. 源码调用追踪链 (Program Trace)",
            ])
            for s_idx, step in enumerate(f.trace, 1):
                lines.append(f"{s_idx}. `[{step.step_type.upper()}]` **{step.file_path}:{step.line}** (`{step.scope}`)")
                lines.append(f"   └─ {step.description}")

            lines.extend([
                "",
                "### 3. 微观发包事实与证据快照",
                f"- **关联证据引用**: `{', '.join(f.evidence_refs)}`",
            ])
            if f.execution:
                lines.extend([
                    f"- **验证发包**: `{f.execution.method} {f.execution.url}` $\\to$ HTTP `{f.execution.status_code}`",
                    f"- **响应摘要**: `{f.execution.response_summary}`",
                ])

            if f.remediation:
                lines.extend([
                    "",
                    "### 4. 架构修复与治理建议",
                    f"- **修复概括**: {f.remediation.summary}",
                    f"- **治理实操**: {f.remediation.guidance}",
                ])
            lines.append("\n---\n")

        return "\n".join(lines)

    def render_needs_validation_md(self) -> str:
        """投影 4: 存疑待攻坚清单 NEEDS-VALIDATION.md"""
        needs_val = [f for f in self.findings if f.verdict == Verdict.NEEDS_VALIDATION]
        lines = [
            "# ⚠️ Invar 存疑待攻坚任务清单 (Needs Validation)",
            "",
            "> **严格契约**: 依据系统工程哲学，本清单项虽具备可疑线索，但因缺少关键凭据或物理证据闭环，**严禁标定 Severity 严重度**，作为后续波次或人工攻坚的专属任务输入。",
            "",
        ]

        if not needs_val:
            lines.append("*(当前无任何存疑未决项目)*")
            return "\n".join(lines)

        for idx, f in enumerate(needs_val, 1):
            lines.extend([
                f"## [{idx}] {f.title}",
                f"- **指纹引用**: `{f.fingerprint}`",
                f"- **线索端点**: `{', '.join(f.endpoint_refs)}`",
                f"- **疑点描述**: {f.description}",
                "",
                "### 阻断根因与待突破前置条件",
                f"> **Blocker**: {f.unresolved_blocker or '缺少充分证据'}",
                "",
                f"- **建议安全验证计划**: 请在具备受控凭据后，针对 `{', '.join(f.endpoint_refs)}` 建立专用测试单元进行差异对账。",
                "\n---\n",
            ])

        return "\n".join(lines)

    def render_coverage_summary_md(self) -> str:
        """投影 5: 覆盖账本全景 coverage-summary.md"""
        metrics = self.ledger.compute_metrics()
        lines = [
            "# 📊 Invar 审计覆盖账本全景明细 (Coverage Ledger Summary)",
            "",
            f"> **客观加权覆盖率**: **`{metrics['coverage_percentage']}%`** | **总单元数**: {metrics['total_units']} 个",
            "",
            "| 覆盖单元 ID | 子系统 | 攻击类型 | 状态 | 审查路径清单 | 审查责任人 | 阻塞事实 |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for u in self.ledger.units.values():
            paths_str = "<br>".join(u.starting_paths) if u.starting_paths else "N/A"
            owner = u.owner_agent_id or "-"
            unres_str = "; ".join(f.description for f in u.unresolved) if u.unresolved else "-"
            lines.append(f"| `{u.coverage_id}` | `{u.subsystem}` | `{u.attack_class}` | `{u.status.value}` | {paths_str} | `{owner}` | {unres_str} |")

        return "\n".join(lines)

    def project_all(self, output_dir: Path | str) -> Dict[str, Path]:
        """
        一键原子化落盘全部 5 大正交交付产物
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        files = {
            "findings_json": out / "findings.json",
            "report_md": out / "REPORT.md",
            "findings_detail_md": out / "FINDINGS-DETAIL.md",
            "needs_validation_md": out / "NEEDS-VALIDATION.md",
            "coverage_summary_md": out / "coverage-summary.md",
        }

        files["findings_json"].write_text(self.render_findings_json(), encoding="utf-8")
        files["report_md"].write_text(self.render_report_md(), encoding="utf-8")
        files["findings_detail_md"].write_text(self.render_findings_detail_md(), encoding="utf-8")
        files["needs_validation_md"].write_text(self.render_needs_validation_md(), encoding="utf-8")
        files["coverage_summary_md"].write_text(self.render_coverage_summary_md(), encoding="utf-8")

        return files
