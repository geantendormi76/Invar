# -*- coding: utf-8 -*-
"""
Phase 9.6-B 跨 Run 证据隔离与历史对账契约测试套件 (Cross-Run Evidence Isolation Contract Tests)
对齐顶级安全顶会与形式化审计标准：
断言 Run A 的物理证据绝不能隐式跨轮次渗透到 Run B 的裁决中，
且历史证据若要被当前轮次采纳，必须满足五维严格采纳性一致性核验 (Admissibility Gate)。
"""
import unittest

from harness.domain_contracts import (
    CrossRunEvidenceAdmissibilityGate,
    CrossRunEvidenceLeakError,
    EndpointIR,
    EvidenceAdmissibility,
    EvidenceAdmissibilityError,
    EvidenceRecord,
    EvidenceRef,
    EvidenceSufficiency,
    HTTPRequestLog,
    HTTPResponseLog,
    ResearchCase,
    ResearchDecision,
    SecurityInvariant,
)
from harness.invariant_evaluator import InvariantEvaluator


class CrossRunEvidenceIsolationContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.endpoint_reset = EndpointIR(
            method="POST",
            path="/users/admin/reset-password",
            endpoint_id="POST:/users/admin/reset-password",
        )
        self.auth_invariant = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="Administrative routes require valid authentication",
        )

        # 模拟 Run A：曾经在 Attempt #14 真实拿到 403 access_policy_denial
        self.evidence_run_a = EvidenceRecord(
            endpoint=self.endpoint_reset,
            request=HTTPRequestLog(
                method="PUT",
                url="https://api.ikuai8.com/users/admin/reset-password",
                headers={"X-HTTP-Method-Override": "PUT"},
                body={},
            ),
            response=HTTPResponseLog(
                status_code=403,
                body_preview='{"code": 403, "msg": "Forbidden: access denied"}',
            ),
            run_id="RUN-A-20261003",
            task_id="TASK-4",
            attempt_id=14,
            classification="access_policy_denial",
        )

        # 模拟 Run B：当轮物理探测 Attempt #14 仅拿到 404 not_found
        self.evidence_run_b = EvidenceRecord(
            endpoint=self.endpoint_reset,
            request=HTTPRequestLog(
                method="GET",
                url="https://api.ikuai8.com/users/admin/reset-password",
                headers={},
                body={},
            ),
            response=HTTPResponseLog(
                status_code=404,
                body_preview="Not Found",
            ),
            run_id="RUN-B-20261004",
            task_id="TASK-4",
            attempt_id=14,
            classification="not_found",
        )

    def test_01_evidence_record_has_first_class_provenance_and_hash(self) -> None:
        """【契约 1】EvidenceRecord 具备一等公民血统元数据与物理抗篡改哈希"""
        self.assertEqual(self.evidence_run_a.run_id, "RUN-A-20261003")
        self.assertEqual(self.evidence_run_a.task_id, "TASK-4")
        self.assertEqual(self.evidence_run_a.attempt_id, 14)
        self.assertTrue(self.evidence_run_a.evidence_id.startswith("ev:RUN-A-20261003:TASK-4:14:"))
        self.assertTrue(len(self.evidence_run_a.content_hash) == 64)

    def test_02_same_run_evidence_resolves_as_current_run_only(self) -> None:
        """【契约 2】当前 Run 内部证据引用默认为 CURRENT_RUN_ONLY，合法可用"""
        ref_b = self.evidence_run_b.make_ref(current_run_id="RUN-B-20261004")
        verified_ref = CrossRunEvidenceAdmissibilityGate.verify_admissibility(
            evidence=self.evidence_run_b,
            ref=ref_b,
            current_run_id="RUN-B-20261004",
        )
        self.assertEqual(verified_ref.admissibility, EvidenceAdmissibility.CURRENT_RUN_ONLY)
        self.assertEqual(verified_ref.run_id, "RUN-B-20261004")

    def test_03_cross_run_evidence_cannot_leak_implicitly_into_current_run(self) -> None:
        """【契约 3（核心防线）】未经显式声明的跨 Run 证据隐式解析必须直接抛出 CrossRunEvidenceLeakError"""
        # 尝试在 Run B 的上下文中直接解析 Run A 的证据
        ref_a_raw = self.evidence_run_a.make_ref(current_run_id="RUN-A-20261003")

        with self.assertRaises(CrossRunEvidenceLeakError) as ctx:
            CrossRunEvidenceAdmissibilityGate.verify_admissibility(
                evidence=self.evidence_run_a,
                ref=ref_a_raw,
                current_run_id="RUN-B-20261004",  # 当前是 Run B
                allow_cross_run=False,             # 未显式允许跨轮次
            )
        self.assertIn("Implicit cross-run evidence resolution is strictly forbidden", str(ctx.exception))

    def test_04_explicit_cross_run_reference_succeeds_when_all_invariants_satisfied(self) -> None:
        """【契约 4】显式声明并满足端点与内容哈希完全一致时，核验晋升为 CROSS_RUN_EXPLICIT"""
        ref_a_explicit = EvidenceRef(
            run_id="RUN-A-20261003",
            evidence_id=self.evidence_run_a.evidence_id,
            relation="HISTORICAL_BASELINE",
            admissibility=EvidenceAdmissibility.CROSS_RUN_EXPLICIT,
            expected_content_hash=self.evidence_run_a.content_hash,
            endpoint_id=self.endpoint_reset.endpoint_id,
        )

        verified = CrossRunEvidenceAdmissibilityGate.verify_admissibility(
            evidence=self.evidence_run_a,
            ref=ref_a_explicit,
            current_run_id="RUN-B-20261004",
            current_endpoint=self.endpoint_reset,
            allow_cross_run=True,
        )
        self.assertEqual(verified.admissibility, EvidenceAdmissibility.CROSS_RUN_EXPLICIT)
        self.assertEqual(verified.run_id, "RUN-A-20261003")

    def test_05_cross_run_reference_hash_mismatch_is_rejected(self) -> None:
        """【契约 5】跨轮次证据物理哈希一旦不匹配，强制拒绝并抛出 EvidenceAdmissibilityError"""
        ref_a_tampered = EvidenceRef(
            run_id="RUN-A-20261003",
            evidence_id=self.evidence_run_a.evidence_id,
            relation="HISTORICAL_BASELINE",
            admissibility=EvidenceAdmissibility.CROSS_RUN_EXPLICIT,
            expected_content_hash="tampered_hash_00000000000000000000000000000000000000000000000000",
            endpoint_id=self.endpoint_reset.endpoint_id,
        )

        with self.assertRaises(EvidenceAdmissibilityError) as ctx:
            CrossRunEvidenceAdmissibilityGate.verify_admissibility(
                evidence=self.evidence_run_a,
                ref=ref_a_tampered,
                current_run_id="RUN-B-20261004",
                current_endpoint=self.endpoint_reset,
                allow_cross_run=True,
            )
        self.assertIn("Content hash mismatch", str(ctx.exception))

    def test_06_current_verdict_strictly_forbids_rejected_cross_run_references(self) -> None:
        """【契约 6】裁决准入门禁：当前裁决若引用了 CROSS_RUN_REJECTED 证据，一票否决"""
        rejected_ref = EvidenceRef(
            run_id="RUN-A-20261003",
            evidence_id="ev:RUN-A:TASK-4:1:abc",
            admissibility=EvidenceAdmissibility.CROSS_RUN_REJECTED,
        )

        with self.assertRaises(CrossRunEvidenceLeakError) as ctx:
            CrossRunEvidenceAdmissibilityGate.assert_admissible_for_verdict(
                refs=[rejected_ref],
                current_run_id="RUN-B-20261004",
            )
        self.assertIn("cannot reference rejected cross-run evidence", str(ctx.exception))

    def test_07_state_freshness_isolation_run_a_confirmed_run_b_inconclusive(self) -> None:
        """【契约 7（总体验收）】Run A 即使 confirmed，Run B 测出 404 也绝不沿用历史证据，物理状态保鲜"""
        # Run A: 物理 403 -> confirmed
        eval_a = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_reset,
            status_code=403,
            payload={},
        )
        self.assertEqual(eval_a.status, "confirmed")
        self.assertEqual(eval_a.sufficiency, EvidenceSufficiency.SUFFICIENT)

        # Run B: 物理 404 -> 必须诚实为 inconclusive，不受 Run A 物理存在影响
        eval_b = InvariantEvaluator.evaluate(
            invariant=self.auth_invariant,
            endpoint=self.endpoint_reset,
            status_code=404,
            payload={},
        )
        self.assertEqual(eval_b.status, "inconclusive")
        self.assertEqual(eval_b.sufficiency, EvidenceSufficiency.INSUFFICIENT)


if __name__ == "__main__":
    unittest.main()
