# -*- coding: utf-8 -*-
"""
Invar 权威赏金资格审查门禁 (Canonical Bounty Eligibility Gate)
对标 Agentic-Bug-Hunter 与 HackerOne / Bugcrowd 顶级审查标准：
贯彻“技术确权”与“赏金资格”两权分立原则。通过严格的 7-Question 门禁消除无效、重复与低质战报。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set

from harness.domain_contracts import (
    FindingRecord,
    Verdict,
    Severity,
    ResearchScope,
)

class BountyEligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    REJECTED_NOT_CONFIRMED = "REJECTED_NOT_CONFIRMED"
    REJECTED_OUT_OF_SCOPE = "REJECTED_OUT_OF_SCOPE"
    REJECTED_NO_POC = "REJECTED_NO_POC"
    REJECTED_NO_VERIFICATION = "REJECTED_NO_VERIFICATION"
    REJECTED_DUPLICATE = "REJECTED_DUPLICATE"
    REJECTED_EXCLUDED_CATEGORY = "REJECTED_EXCLUDED_CATEGORY"
    REJECTED_INSUFFICIENT_IMPACT = "REJECTED_INSUFFICIENT_IMPACT"

# 工业界主流 Bug Bounty / SRC 普遍拒绝受理的非实质影响类别
ALWAYS_REJECTED_ATTACK_CLASSES: Set[str] = {
    "missing_spf_dmarc",
    "clickjacking_no_impact",
    "tls_weak_cipher_suite",
    "software_version_disclosure",
    "generic_cookie_missing_httponly",
}

@dataclass(frozen=True)
class SevenQuestionsChecklist:
    """
    赏金资格 7-Question 标准核验底账
    """
    is_in_scope: bool
    has_concrete_impact: bool
    has_working_poc: bool
    has_clean_reproduction: bool
    is_novel: bool
    not_excluded_category: bool
    triager_acceptable: bool

    def all_passed(self) -> bool:
        return (
            self.is_in_scope and
            self.has_concrete_impact and
            self.has_working_poc and
            self.has_clean_reproduction and
            self.is_novel and
            self.not_excluded_category and
            self.triager_acceptable
        )

@dataclass(frozen=True)
class BountyEligibilityResult:
    """
    赏金资格审查综合裁决实体
    """
    status: BountyEligibilityStatus
    is_eligible: bool
    checklist: SevenQuestionsChecklist
    rationale: str
    finding_id: str
    fingerprint: str

class BountyEligibilityGate:
    """
    赏金资格审查门禁执行器
    """

    @classmethod
    def evaluate(
        cls,
        finding: FindingRecord,
        scope: Optional[ResearchScope] = None,
        known_fingerprints: Optional[Set[str]] = None
    ) -> BountyEligibilityResult:
        known_fps = known_fingerprints or set()
        
        # 1. 前置条件: 必须已被技术内核确权为 CONFIRMED
        if finding.verdict != Verdict.CONFIRMED:
            empty_chk = SevenQuestionsChecklist(False, False, False, False, False, False, False)
            return BountyEligibilityResult(
                status=BountyEligibilityStatus.REJECTED_NOT_CONFIRMED,
                is_eligible=False,
                checklist=empty_chk,
                rationale="该发现尚未通过底层技术确权门禁 (非 CONFIRMED 状态)",
                finding_id=finding.finding_id,
                fingerprint=finding.fingerprint
            )

        # Q1: IsInScope 范围核验
        is_in_scope = True
        if scope is not None and finding.endpoint_refs:
            for ep_ref in finding.endpoint_refs:
                parts = ep_ref.split(":", 1)
                path = parts[1] if len(parts) == 2 else ep_ref
                if scope.is_path_excluded(path):
                    is_in_scope = False
                    break

        # Q2: HasConcreteImpact 具备实质业务安全危害
        has_concrete_impact = (
            finding.severity in {Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM} and
            bool(finding.root_cause)
        )

        # Q3: HasWorkingPoC 必须包含独立自洽的物理复现 PoC
        has_working_poc = bool(finding.poc_code and finding.poc_code.strip())

        # Q4: HasCleanReproduction 必须获得独立第三方复核器签署
        has_clean_reproduction = (
            finding.verification is not None and
            finding.verification.independent_verified is True and
            finding.verification.verdict in {"VERIFIED", "CORRECTED"}
        )

        # Q5: IsNovel 查重检验 (非历史已上报重复指纹)
        is_novel = finding.fingerprint not in known_fps

        # Q6: NotExcludedCategory 非 SRC 平台通用排除类别
        attack_class = ""
        if ":" in finding.fingerprint:
            parts = finding.fingerprint.split(":")
            if len(parts) > 1:
                attack_class = parts[1].lower()
        not_excluded_category = attack_class not in ALWAYS_REJECTED_ATTACK_CLASSES

        # Q7: TriagerAcceptable 要素完备且具备修复治理指引
        triager_acceptable = (
            bool(finding.description) and
            bool(finding.remediation and finding.remediation.guidance) and
            bool(finding.trace)
        )

        checklist = SevenQuestionsChecklist(
            is_in_scope=is_in_scope,
            has_concrete_impact=has_concrete_impact,
            has_working_poc=has_working_poc,
            has_clean_reproduction=has_clean_reproduction,
            is_novel=is_novel,
            not_excluded_category=not_excluded_category,
            triager_acceptable=triager_acceptable
        )

        # 判定具体打回原因
        if not is_in_scope:
            return BountyEligibilityResult(
                status=BountyEligibilityStatus.REJECTED_OUT_OF_SCOPE,
                is_eligible=False,
                checklist=checklist,
                rationale="端点路径命中法定交战规则中的排除黑名单",
                finding_id=finding.finding_id,
                fingerprint=finding.fingerprint
            )
        if not not_excluded_category:
            return BountyEligibilityResult(
                status=BountyEligibilityStatus.REJECTED_EXCLUDED_CATEGORY,
                is_eligible=False,
                checklist=checklist,
                rationale=f"攻击类别 '{attack_class}' 属于各大 Bug Bounty 平台普遍排除受理的非实质危害类型",
                finding_id=finding.finding_id,
                fingerprint=finding.fingerprint
            )
        if not is_novel:
            return BountyEligibilityResult(
                status=BountyEligibilityStatus.REJECTED_DUPLICATE,
                is_eligible=False,
                checklist=checklist,
                rationale="该漏洞因果指纹已存在于历史提交底账中 (重复上报拦截)",
                finding_id=finding.finding_id,
                fingerprint=finding.fingerprint
            )
        if not has_working_poc:
            return BountyEligibilityResult(
                status=BountyEligibilityStatus.REJECTED_NO_POC,
                is_eligible=False,
                checklist=checklist,
                rationale="缺少自洽可复现的独立 PoC 代码，严防提交推论式伪漏洞",
                finding_id=finding.finding_id,
                fingerprint=finding.fingerprint
            )
        if not has_clean_reproduction:
            return BountyEligibilityResult(
                status=BountyEligibilityStatus.REJECTED_NO_VERIFICATION,
                is_eligible=False,
                checklist=checklist,
                rationale="未通过独立第三方复核器或双盲重放复验",
                finding_id=finding.finding_id,
                fingerprint=finding.fingerprint
            )
        if not has_concrete_impact or not triager_acceptable:
            return BountyEligibilityResult(
                status=BountyEligibilityStatus.REJECTED_INSUFFICIENT_IMPACT,
                is_eligible=False,
                checklist=checklist,
                rationale="危害等级低于提交门槛，或缺乏必要的调用追溯与修复指引",
                finding_id=finding.finding_id,
                fingerprint=finding.fingerprint
            )

        # 7 问全部通过
        return BountyEligibilityResult(
            status=BountyEligibilityStatus.ELIGIBLE,
            is_eligible=True,
            checklist=checklist,
            rationale="100% 通过 7-Question 赏金资格核验，准予生成法定提交包",
            finding_id=finding.finding_id,
            fingerprint=finding.fingerprint
        )
