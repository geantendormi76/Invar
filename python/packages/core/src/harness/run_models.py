from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class IllegalStateTransitionError(ValueError):
    """当尝试非法跃迁 ResearchRun 状态机时抛出"""
    pass


class RunStatus(str, Enum):
    INIT = "INIT"
    SCOPE_VERIFIED = "SCOPE_VERIFIED"
    CONTEXT_READY = "CONTEXT_READY"
    PLAN_READY = "PLAN_READY"
    EXECUTING = "EXECUTING"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    EVALUATED = "EVALUATED"
    REPORT_READY = "REPORT_READY"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


# 合法状态转移拓扑定义
VALID_TRANSITIONS: Dict[RunStatus, Set[RunStatus]] = {
    RunStatus.INIT: {RunStatus.SCOPE_VERIFIED, RunStatus.BLOCKED},
    RunStatus.SCOPE_VERIFIED: {RunStatus.CONTEXT_READY, RunStatus.BLOCKED},
    RunStatus.CONTEXT_READY: {RunStatus.PLAN_READY, RunStatus.BLOCKED},
    RunStatus.PLAN_READY: {RunStatus.EXECUTING, RunStatus.BLOCKED},
    RunStatus.EXECUTING: {RunStatus.EVIDENCE_COLLECTED, RunStatus.BLOCKED},
    RunStatus.EVIDENCE_COLLECTED: {RunStatus.EVALUATED, RunStatus.BLOCKED},
    RunStatus.EVALUATED: {RunStatus.REPORT_READY, RunStatus.BLOCKED},
    RunStatus.REPORT_READY: {RunStatus.COMPLETED, RunStatus.BLOCKED},
    RunStatus.BLOCKED: {
        RunStatus.INIT,
        RunStatus.SCOPE_VERIFIED,
        RunStatus.CONTEXT_READY,
        RunStatus.PLAN_READY,
        RunStatus.EXECUTING,
        RunStatus.EVIDENCE_COLLECTED,
        RunStatus.EVALUATED,
    },
    RunStatus.COMPLETED: set(),
}


@dataclass
class SourceRef:
    """源码上下文精确溯源事实"""
    vcs: Optional[str] = "git"
    commit: Optional[str] = None
    worktree_dirty: bool = False
    raw_input_hash: Optional[str] = None

    @staticmethod
    def compute_sha256(content: str | bytes) -> str:
        data = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.sha256(data).hexdigest()


@dataclass
class ResearchScope:
    """法定科研与测试授权边界"""
    target_domain: str
    included_subdomains: List[str] = field(default_factory=list)
    excluded_paths: List[str] = field(default_factory=list)
    allowed_methods: List[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    )
    authorization_boundary: str = "AUTHORIZED_ENGAGEMENT_ONLY"

    def is_method_allowed(self, method: str) -> bool:
        return method.upper() in [m.upper() for m in self.allowed_methods]

    def is_path_excluded(self, path: str) -> bool:
        return any(ex in path for ex in self.excluded_paths)


@dataclass
class RunProfile:
    """执行轮廓与沙箱参数"""
    name: str = "default"
    max_mutation_rounds: int = 4
    timeout: int = 5
    workers: int = 10


@dataclass
class ExecutionPolicy:
    """安全与执行权限铁律"""
    allow_dynamic_testing: bool = False
    require_independent_verification: bool = True
    enforce_dual_token_for_idor: bool = True
    max_requests_per_task: int = 10


@dataclass
class RunBudget:
    """实验资源与熔断预算"""
    max_tasks: int = 100
    max_requests: int = 1000
    max_duration_seconds: int = 3600
    tasks_executed: int = 0
    requests_made: int = 0

    def is_exhausted(self) -> bool:
        return (
            self.tasks_executed >= self.max_tasks
            or self.requests_made >= self.max_requests
        )


@dataclass
class ResearchRun:
    """
    Invar 权威科研运行周期实体 (Canonical Research Run)
    """
    run_id: str
    target_root: str
    scope: ResearchScope
    source_ref: SourceRef = field(default_factory=SourceRef)
    repository: str = ""
    raw_js_hash: Optional[str] = None
    profile: RunProfile = field(default_factory=RunProfile)
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    budget: Optional[RunBudget] = None
    status: RunStatus = RunStatus.INIT
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    coverage_ledger_ref: str = ""
    findings_ref: str = ""
    prior_run_refs: List[str] = field(default_factory=list)
    block_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def transition_to(self, new_status: RunStatus, reason: Optional[str] = None) -> None:
        """
        强类型状态机跃迁卫语句，严禁非法跳步与未裁决直接宣称完成
        """
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise IllegalStateTransitionError(
                f"Invalid transition from [{self.status.value}] to [{new_status.value}]. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )

        if new_status == RunStatus.BLOCKED:
            self.block_reason = reason or "Execution blocked by prerequisite failure"
        elif self.status == RunStatus.BLOCKED:
            self.block_reason = None

        if new_status == RunStatus.COMPLETED:
            self.completed_at = datetime.now(timezone.utc).isoformat()

        self.status = new_status

    def inspect(self) -> Dict[str, Any]:
        """
        对齐 Tool Contract: run.inspect 输出规范
        """
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "target_root": self.target_root,
            "source_ref": asdict(self.source_ref),
            "scope": asdict(self.scope),
            "profile": self.profile.name,
            "execution_policy": asdict(self.execution_policy),
            "budget": asdict(self.budget) if self.budget else None,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "coverage_ledger_ref": self.coverage_ledger_ref,
            "findings_ref": self.findings_ref,
            "block_reason": self.block_reason,
            "prior_run_refs": list(self.prior_run_refs),
        }

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchRun":
        data_copy = dict(data)
        data_copy["status"] = RunStatus(data_copy["status"])
        data_copy["source_ref"] = SourceRef(**data_copy["source_ref"])
        data_copy["scope"] = ResearchScope(**data_copy["scope"])
        data_copy["profile"] = RunProfile(**data_copy["profile"])
        data_copy["execution_policy"] = ExecutionPolicy(**data_copy["execution_policy"])
        if data_copy.get("budget"):
            data_copy["budget"] = RunBudget(**data_copy["budget"])
        return cls(**data_copy)

    def save(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "ResearchRun":
        p = Path(path)
        content = p.read_text(encoding="utf-8")
        return cls.from_dict(json.loads(content))
