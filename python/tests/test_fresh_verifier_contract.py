# -*- coding: utf-8 -*-
"""
Phase 10.0 第一单步: 双盲纯净隔离复验引擎契约测试
基于 LocalFixtureServer 验证 PoC-Only 物理穿越、全新会话物理发包与不变量双盲重放确权
"""

import unittest
from fixtures.local_server_fixture import LocalFixtureServer
from harness.verifier.fresh_verifier import (
    FreshSandboxVerifier,
    PoCSpecification,
    PoCType,
    FreshVerificationResult,
)
from harness.domain_contracts import (
    SecurityInvariant,
    EndpointIR,
    ResearchScope,
)

class FreshVerifierContractTests(unittest.TestCase):

    def setUp(self) -> None:
        self.scope = ResearchScope(
            target_domain="127.0.0.1",
            allowed_methods=["GET", "POST"]
        )
        self.verifier = FreshSandboxVerifier(verifier_id="test-fresh-verifier", scope=self.scope)
        self.endpoint = EndpointIR(method="GET", path="/ok", endpoint_id="GET:/ok")
        self.auth_invariant = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="Protected route must require authentication headers"
        )

    def test_01_fresh_verifier_replays_poc_and_confirms_vulnerability(self) -> None:
        """【契约 1】全新隔离环境物理重放 PoC: 收到 200 且无鉴权凭据，确凿实锤击穿不变量"""
        with LocalFixtureServer() as fixture:
            # 构造最小自洽 PoC (仅含请求要素，无内部探测历史)
            poc = PoCSpecification(
                poc_type=PoCType.CURL,
                method="GET",
                target_url=f"{fixture.base_url}/ok",
                expected_status_code=200,
                expected_markers=["fixture_ready"],
                reproducible_curl=f"curl -s -i {fixture.base_url}/ok"
            )

            result = self.verifier.verify_poc(
                poc=poc,
                invariant=self.auth_invariant,
                endpoint=self.endpoint
            )

            # 断言物理重放完全成功
            self.assertTrue(result.is_reproduced)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.invariant_evaluation.status, "vulnerable")
            self.assertIn(b"fixture_ready", result.raw_bytes)
            self.assertEqual(result.verifier_id, "test-fresh-verifier")
            self.assertGreater(len(result.content_hash), 30)

    def test_02_fresh_verifier_rejects_when_defense_holds(self) -> None:
        """【契约 2】全新环境中目标返回 403 明确拦截，双盲复核坚决拒绝标记为突破"""
        with LocalFixtureServer() as fixture:
            poc_blocked = PoCSpecification(
                poc_type=PoCType.CURL,
                method="GET",
                target_url=f"{fixture.base_url}/forbidden",
                expected_status_code=200,  # 预期击穿为 200，但实际拦截为 403
                reproducible_curl=f"curl -s -i {fixture.base_url}/forbidden"
            )

            result = self.verifier.verify_poc(
                poc=poc_blocked,
                invariant=self.auth_invariant,
                endpoint=self.endpoint
            )

            # 断言复验失败，安全边界未被击穿 (confirmed defense)
            self.assertFalse(result.is_reproduced)
            self.assertEqual(result.status_code, 403)
            self.assertEqual(result.invariant_evaluation.status, "confirmed")

    def test_03_fresh_verifier_handles_clean_timeout_gracefully(self) -> None:
        """【契约 3】全新环境中目标超时，复验安全收敛为 inconclusive，绝不误判为实锤"""
        with LocalFixtureServer() as fixture:
            poc_slow = PoCSpecification(
                poc_type=PoCType.CURL,
                method="GET",
                target_url=f"{fixture.base_url}/slow?delay=2.5",
                expected_status_code=200
            )

            # 显式构造 1 秒超时的复验器，针对延迟 2.5 秒的目标触发确定性超时
            short_verifier = FreshSandboxVerifier(
                verifier_id="test-timeout-verifier",
                scope=self.scope,
                timeout_seconds=1
            )
            
            result = short_verifier.verify_poc(
                poc=poc_slow,
                invariant=self.auth_invariant,
                endpoint=self.endpoint
            )

            # 超时安全收敛，绝不误判为实锤
            self.assertFalse(result.is_reproduced)
            self.assertEqual(result.invariant_evaluation.status, "inconclusive")
