# -*- coding: utf-8 -*-
"""
Phase 10.1 第一单步: 赏金资格审查门禁契约测试
验证 7 问资格核验底账、查重拦截、排除类型过滤、两权分立原则与准入裁决
"""

import unittest
from harness.gates.bounty_eligibility_gate import (
    BountyEligibilityGate,
    BountyEligibilityStatus,
)
from harness.domain_contracts import (
    FindingRecord,
    Verdict,
    Severity,
    Remediation,
    VerificationSummary,
    TraceStep,
    ResearchScope,
)

class BountyEligibilityGateContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.scope = ResearchScope(
            target_domain="ikuai8.com",
            excluded_paths=["/api/v1/excluded_logout"]
        )
        self.confirmed_finding = FindingRecord(
            finding_id="FINDING-BOLA-001",
            verdict=Verdict.CONFIRMED,
            fingerprint="fp:authorization:orders_service:abc12345",
            title="BOLA: 订单导出端点跨租户越权泄露",
            description="攻击者可通过遍历 order_id 窃取其他企业租户敏感订单详情",
            root_cause="服务端控制器缺少租户属主校验",
            severity=Severity.HIGH,
            poc_code="curl -s -i 'https://api.ikuai8.com/api/v1/orders/99901' -H 'Authorization: Bearer attacker_token'",
            endpoint_refs=["GET:/api/v1/orders/99901"],
            evidence_refs=["ev:phys:99901"],
            remediation=Remediation(summary="增加属主鉴权", guidance="校验 order.tenant_id == caller.tenant_id"),
            verification=VerificationSummary(independent_verified=True, verifier_id="fresh-verifier-prime", verdict="VERIFIED"),
            trace=[TraceStep(step_type="entrypoint", file_path="routes/orders.js", line=42, scope="exportOrder", description="调用入口")]
        )

    def test_01_compliant_finding_passes_all_seven_questions(self) -> None:
        """【契约 1】合规的实锤 BOLA 漏洞顺利通过 7 问核验，获得 ELIGIBLE 资格"""
        res = BountyEligibilityGate.evaluate(self.confirmed_finding, scope=self.scope)
        self.assertTrue(res.is_eligible)
        self.assertEqual(res.status, BountyEligibilityStatus.ELIGIBLE)
        self.assertTrue(res.checklist.all_passed())
        self.assertIn("100% 通过", res.rationale)

    def test_02_duplicate_finding_rejected_for_bounty_without_mutating_finding(self) -> None:
        """【契约 2 (两权分立)】历史已报过的重复指纹被赏金门禁拒绝，但技术漏洞本身依然维持 CONFIRMED"""
        known_history_fps = {"fp:authorization:orders_service:abc12345"}
        
        res = BountyEligibilityGate.evaluate(
            finding=self.confirmed_finding,
            scope=self.scope,
            known_fingerprints=known_history_fps
        )

        # 赏金维度被坚决打回 (杜绝重复提交)
        self.assertFalse(res.is_eligible)
        self.assertEqual(res.status, BountyEligibilityStatus.REJECTED_DUPLICATE)
        self.assertFalse(res.checklist.is_novel)
        
        # 两权分立核心断言: 技术实体本身不受污染，依然是神圣的 CONFIRMED
        self.assertEqual(self.confirmed_finding.verdict, Verdict.CONFIRMED)

    def test_03_missing_poc_strictly_blocks_submission(self) -> None:
        """【契约 3】缺少自洽复现 PoC 的漏洞被一票否决，严防向平台倾倒推论式假漏洞"""
        finding_no_poc = FindingRecord(
            finding_id="FINDING-NO-POC",
            verdict=Verdict.CONFIRMED,
            fingerprint="fp:auth:service:111",
            title="理论漏洞",
            description="描述",
            root_cause="根因",
            severity=Severity.HIGH,
            poc_code="",  # 缺少工作 PoC
            verification=VerificationSummary(independent_verified=True, verdict="VERIFIED"),
            remediation=Remediation("修复", "指引"),
            trace=[TraceStep("entry", "file.js", 1, "fn", "desc")]
        )
        res = BountyEligibilityGate.evaluate(finding_no_poc, scope=self.scope)
        self.assertFalse(res.is_eligible)
        self.assertEqual(res.status, BountyEligibilityStatus.REJECTED_NO_POC)

    def test_04_excluded_category_rejected_for_bounty(self) -> None:
        """【契约 4】平台通用排除类别 (如缺少 SPF/DMARC) 即使技术属实也坚决拦截"""
        finding_spf = FindingRecord(
            finding_id="FINDING-SPF",
            verdict=Verdict.CONFIRMED,
            fingerprint="fp:missing_spf_dmarc:dns:222",
            title="缺少 SPF 记录",
            description="DNS 缺少记录",
            root_cause="配置遗漏",
            severity=Severity.LOW,
            poc_code="dig txt example.com",
            verification=VerificationSummary(independent_verified=True, verdict="VERIFIED"),
            remediation=Remediation("配置", "添加记录"),
            trace=[TraceStep("entry", "dns", 1, "root", "desc")]
        )
        res = BountyEligibilityGate.evaluate(finding_spf, scope=self.scope)
        self.assertFalse(res.is_eligible)
        self.assertEqual(res.status, BountyEligibilityStatus.REJECTED_EXCLUDED_CATEGORY)
