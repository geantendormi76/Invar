from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from harness.models import EndpointIR
from harness.run_models import ResearchScope


class IllegalCoverageStateTransitionError(ValueError):
    """当覆盖单元尝试发生非法状态转移时抛出"""
    pass


class CoverageValidationError(ValueError):
    """当覆盖账本违背核心不变性约束时抛出"""
    pass


class CoverageStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COVERED = "covered"
    CANDIDATE = "candidate"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    OUT_OF_SCOPE = "out_of_scope"


VALID_COVERAGE_TRANSITIONS: Dict[CoverageStatus, Set[CoverageStatus]] = {
    CoverageStatus.PLANNED: {
        CoverageStatus.IN_PROGRESS,
        CoverageStatus.DEFERRED,
        CoverageStatus.OUT_OF_SCOPE,
    },
    CoverageStatus.IN_PROGRESS: {
        CoverageStatus.COVERED,
        CoverageStatus.CANDIDATE,
        CoverageStatus.BLOCKED,
        CoverageStatus.PLANNED,
    },
    CoverageStatus.BLOCKED: {
        CoverageStatus.IN_PROGRESS,
        CoverageStatus.DEFERRED,
    },
    CoverageStatus.DEFERRED: {
        CoverageStatus.PLANNED,
        CoverageStatus.OUT_OF_SCOPE,
    },
    CoverageStatus.COVERED: {
        CoverageStatus.IN_PROGRESS,  # 支持重新开启二次复测
    },
    CoverageStatus.CANDIDATE: {
        CoverageStatus.IN_PROGRESS,
    },
    CoverageStatus.OUT_OF_SCOPE: set(),
}


@dataclass
class UnresolvedFact:
    """阻塞覆盖单元验收的具体未决事实"""
    fact_id: str
    description: str
    blocking_reason: str = ""
    safe_validation_plan: str = ""


@dataclass
class CoverageUnit:
    """
    Invar 最小确定性科研覆盖单元 (Coverage Unit)
    """
    coverage_id: str
    surface: str  # 例如: "api", "ui", "file", "network"
    boundary: str  # 信任边界，例如: "user-to-admin", "tenant-isolation"
    subsystem: str  # 业务子系统，例如: "authConf", "order", "user"
    attack_class: str  # 攻击类型，例如: "authorization", "destructive_action", "authentication"
    starting_paths: List[str] = field(default_factory=list)
    status: CoverageStatus = CoverageStatus.PLANNED
    owner_agent_id: Optional[str] = None
    reviewed_paths: List[str] = field(default_factory=list)
    check_refs: List[str] = field(default_factory=list)
    candidate_fingerprints: List[str] = field(default_factory=list)
    unresolved: List[UnresolvedFact] = field(default_factory=list)
    prior_refs: List[str] = field(default_factory=list)
    weight: float = 1.0

    def transition_to(self, new_status: CoverageStatus) -> None:
        allowed = VALID_COVERAGE_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise IllegalCoverageStateTransitionError(
                f"Invalid coverage transition from [{self.status.value}] to [{new_status.value}]. "
                f"Allowed transitions: {[s.value for s in allowed]}"
            )
        self.status = new_status

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoverageUnit":
        data_copy = dict(data)
        data_copy["status"] = CoverageStatus(data_copy["status"])
        data_copy["unresolved"] = [
            UnresolvedFact(**f) if isinstance(f, dict) else f
            for f in data_copy.get("unresolved", [])
        ]
        return cls(**data_copy)


@dataclass
class CoverageLedger:
    """
    Invar 权威科研覆盖账本 (Authoritative Coverage Ledger)
    主进程独占写，全局覆盖进度的唯一真理载体
    """
    run_id: str
    units: Dict[str, CoverageUnit] = field(default_factory=dict)

    def add_unit(self, unit: CoverageUnit) -> None:
        if unit.coverage_id in self.units:
            raise ValueError(f"CoverageUnit with ID '{unit.coverage_id}' already exists in ledger")
        self.units[unit.coverage_id] = unit

    def get_unit(self, coverage_id: str) -> CoverageUnit:
        if coverage_id not in self.units:
            raise KeyError(f"CoverageUnit '{coverage_id}' not found in ledger")
        return self.units[coverage_id]

    def contains(self, coverage_id: str) -> bool:
        return coverage_id in self.units

    def validate(self) -> List[str]:
        """
        全量断言账本的核心不变性约束 (Invariants)
        """
        errors = []
        for cid, unit in self.units.items():
            # 约束 1：COVERED 必须具有明确的审查路径与检查项
            if unit.status == CoverageStatus.COVERED:
                if not unit.reviewed_paths:
                    errors.append(f"Unit [{cid}] is marked COVERED but has empty reviewed_paths")
                if not unit.check_refs:
                    errors.append(f"Unit [{cid}] is marked COVERED but has empty check_refs")

            # 约束 2：CANDIDATE 必须关联至少一个候选指纹
            elif unit.status == CoverageStatus.CANDIDATE:
                if not unit.candidate_fingerprints:
                    errors.append(f"Unit [{cid}] is marked CANDIDATE but has no candidate_fingerprints")

            # 约束 3：BLOCKED 必须列出具体未决事实
            elif unit.status == CoverageStatus.BLOCKED:
                if not unit.unresolved:
                    errors.append(f"Unit [{cid}] is marked BLOCKED but has no unresolved facts listed")

        if errors:
            raise CoverageValidationError("Coverage ledger failed invariant validation:\n" + "\n".join(errors))
        return errors

    def compute_metrics(self) -> Dict[str, Any]:
        """
        基于确定性单元与权重的客观覆盖率测算
        """
        total_units = len(self.units)
        in_scope_units = [u for u in self.units.values() if u.status != CoverageStatus.OUT_OF_SCOPE]
        covered_units = [u for u in in_scope_units if u.status in {CoverageStatus.COVERED, CoverageStatus.CANDIDATE}]
        blocked_units = [u for u in in_scope_units if u.status == CoverageStatus.BLOCKED]
        deferred_units = [u for u in in_scope_units if u.status == CoverageStatus.DEFERRED]
        out_of_scope_units = [u for u in self.units.values() if u.status == CoverageStatus.OUT_OF_SCOPE]

        total_weight = sum(u.weight for u in in_scope_units)
        covered_weight = sum(u.weight for u in covered_units)

        percentage = round((covered_weight / total_weight) * 100.0, 2) if total_weight > 0 else 0.0

        return {
            "total_units": total_units,
            "in_scope_units": len(in_scope_units),
            "covered_units": len(covered_units),
            "blocked_units": len(blocked_units),
            "deferred_units": len(deferred_units),
            "out_of_scope_units": len(out_of_scope_units),
            "total_in_scope_weight": total_weight,
            "covered_weight": covered_weight,
            "coverage_percentage": percentage,
        }

    @classmethod
    def plan_from_endpoints(
        cls,
        run_id: str,
        endpoints: List[EndpointIR],
        scope: Optional[ResearchScope] = None,
    ) -> "CoverageLedger":
        """
        从 AST 静态提炼出的 API 端点清单，自动、确定性地构建初始覆盖账本
        """
        ledger = cls(run_id=run_id)

        # 归纳子系统与路径
        grouped: Dict[str, List[EndpointIR]] = {}
        for ep in endpoints:
            # 提取路径中的一级主业务作为 subsystem (如 /api/v1/users -> users)
            parts = [p for p in ep.path.strip("/").split("/") if p and not p.startswith("v")]
            subsystem = parts[1] if len(parts) > 1 and parts[0] == "api" else (parts[0] if parts else "root")
            grouped.setdefault(subsystem, []).append(ep)

        for subsystem, ep_list in sorted(grouped.items()):
            paths = sorted(list({ep.path for ep in ep_list}))
            methods = {ep.method.upper() for ep in ep_list}
            tags = {t for ep in ep_list for t in ep.tags}

            # 1. 认证鉴权维度覆盖规划
            auth_unit_id = f"api-{subsystem}-authorization"
            auth_status = CoverageStatus.PLANNED
            if scope and any(scope.is_path_excluded(p) for p in paths):
                auth_status = CoverageStatus.OUT_OF_SCOPE

            ledger.add_unit(
                CoverageUnit(
                    coverage_id=auth_unit_id,
                    surface="api",
                    boundary="user-to-privileged-boundary",
                    subsystem=subsystem,
                    attack_class="authorization",
                    starting_paths=paths,
                    status=auth_status,
                )
            )

            # 2. 若存在破坏性动作 (DELETE / state-changing)，规划二次确认与防护覆盖单元
            if "DELETE" in methods or "destructive" in tags:
                destruct_unit_id = f"api-{subsystem}-destructive_guard"
                destruct_paths = [ep.path for ep in ep_list if ep.method.upper() == "DELETE" or "destructive" in ep.tags]
                ledger.add_unit(
                    CoverageUnit(
                        coverage_id=destruct_unit_id,
                        surface="api",
                        boundary="state-mutation-safety",
                        subsystem=subsystem,
                        attack_class="destructive_action",
                        starting_paths=sorted(list(set(destruct_paths))),
                        status=CoverageStatus.PLANNED,
                    )
                )

        return ledger

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "metrics": self.compute_metrics(),
            "units": {cid: u.to_dict() for cid, u in self.units.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoverageLedger":
        run_id = data.get("run_id", "")
        ledger = cls(run_id=run_id)
        raw_units = data.get("units", {})
        for cid, u_data in raw_units.items():
            ledger.units[cid] = CoverageUnit.from_dict(u_data)
        return ledger

    def save(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "CoverageLedger":
        p = Path(path)
        content = p.read_text(encoding="utf-8")
        return cls.from_dict(json.loads(content))
