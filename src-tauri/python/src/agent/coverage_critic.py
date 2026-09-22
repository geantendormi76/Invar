from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from harness.coverage_ledger import CoverageLedger, CoverageStatus, CoverageUnit
from harness.models import EndpointIR
from harness.run_models import ResearchScope


@dataclass
class MissingCoverageProposal:
    """
    Coverage Critic 提出的盲区覆盖单元补充提案
    """
    surface: str
    boundary: str
    subsystem: str
    attack_class: str
    starting_paths: List[str]
    reason: str


class CoverageCritic:
    """
    Invar 覆盖批评家 (Coverage Critic)
    天职：独立审视全局，专门识别未覆盖的业务子系统、缺失的破坏性动作检查与遗漏的越权边界
    """
    def __init__(self, critic_id: str = "critic-prime"):
        self.critic_id = critic_id

    def critique(
        self,
        ledger: CoverageLedger,
        endpoints: List[EndpointIR],
        scope: Optional[ResearchScope] = None,
    ) -> List[MissingCoverageProposal]:
        proposals: List[MissingCoverageProposal] = []
        existing_unit_ids = set(ledger.units.keys())

        # 1. 扫描未覆盖的子系统 (Subsystem Coverage Gap)
        # 归类所有 AST 端点所属的子系统
        subsystem_map: Dict[str, List[EndpointIR]] = {}
        for ep in endpoints:
            parts = [p for p in ep.path.strip("/").split("/") if p and not p.startswith("v")]
            subsystem = parts[1] if len(parts) > 1 and parts[0] == "api" else (parts[0] if parts else "root")
            subsystem_map.setdefault(subsystem, []).append(ep)

        covered_subsystems = {u.subsystem for u in ledger.units.values()}

        for sub, eps in subsystem_map.items():
            if sub not in covered_subsystems:
                cid = f"api-{sub}-authorization"
                if cid not in existing_unit_ids:
                    proposals.append(
                        MissingCoverageProposal(
                            surface="api",
                            boundary="uncovered-subsystem-boundary",
                            subsystem=sub,
                            attack_class="authorization",
                            starting_paths=sorted(list({e.path for e in eps})),
                            reason=f"Subsystem [{sub}] present in AST but completely absent from coverage ledger",
                        )
                    )

        # 2. 扫描高危破坏性动作防护盲区 (Destructive Action Gap)
        for sub, eps in subsystem_map.items():
            has_destructive = any(
                e.method.upper() == "DELETE" or "destructive" in e.tags
                for e in eps
            )
            destruct_cid = f"api-{sub}-destructive_guard"
            if has_destructive and destruct_cid not in existing_unit_ids:
                destruct_paths = [e.path for e in eps if e.method.upper() == "DELETE" or "destructive" in e.tags]
                proposals.append(
                    MissingCoverageProposal(
                        surface="api",
                        boundary="state-mutation-safety",
                        subsystem=sub,
                        attack_class="destructive_action",
                        starting_paths=sorted(list(set(destruct_paths))),
                        reason=f"Subsystem [{sub}] contains destructive operations without dedicated destructive guard coverage unit",
                    )
                )

        # 3. 扫描对象属主标识符越权盲区 (IDOR / BOLA Gap)
        idor_keywords = {"id", "user_id", "uid", "account_id", "order_id"}
        for sub, eps in subsystem_map.items():
            idor_eps = [
                e for e in eps
                if any(any(k in p.lower() for k in idor_keywords) for p in e.extracted_params)
            ]
            idor_cid = f"api-{sub}-idor_boundary"
            if idor_eps and idor_cid not in existing_unit_ids:
                proposals.append(
                    MissingCoverageProposal(
                        surface="api",
                        boundary="tenant-resource-isolation",
                        subsystem=sub,
                        attack_class="idor_boundary",
                        starting_paths=sorted(list({e.path for e in idor_eps})),
                        reason=f"Subsystem [{sub}] contains direct client-controlled object identifiers without IDOR differential coverage unit",
                    )
                )

        return proposals
