# -*- coding: utf-8 -*-
"""
Invar Threat Model Contract Tests
对标 Anthropic Reference Harness 与 Strix 黄金标准，验证威胁模型一级契约的不可变性、序列化与假说派生机制。
"""
import unittest
from harness.domain_contracts import (
    AttackerProfile,
    EndpointIR,
    Hypothesis,
    SecurityInvariant,
    ThreatModel,
)


class ThreatModelContractTests(unittest.TestCase):
    def setUp(self):
        self.attacker = AttackerProfile(
            role="anonymous_external",
            token_ref=None,
            description="未登录的外部公网访问者",
            capabilities=["unauthenticated_http_requests"],
        )
        self.invariant_auth = SecurityInvariant(
            invariant_type="auth_boundary",
            statement="特权管理接口必须对未授权请求实施拦截",
        )
        self.threat_model = ThreatModel(
            model_id="TM-IKUAI-ADMIN-01",
            title="公网外部主体对内部特权管理接口的越权访问威胁",
            attacker=self.attacker,
            assets=["network_configuration", "admin_credentials"],
            trust_boundaries=["internet_to_management_plane"],
            entrypoints=["POST:/api/v1/system/config", "DELETE:/api/v1/routes"],
            expected_controls=["jwt_bearer_auth", "csrf_token_required"],
            invariants=[self.invariant_auth],
            metadata={"source": "Phase-R1.2-Baseline"},
        )

    def test_threat_model_round_trip_serialization(self):
        """【契约 1】威胁模型 100% 结构化无损往返序列化"""
        d = self.threat_model.to_dict()
        restored = ThreatModel.from_dict(d)

        self.assertEqual(restored.model_id, self.threat_model.model_id)
        self.assertEqual(restored.title, self.threat_model.title)
        self.assertEqual(restored.attacker.role, "anonymous_external")
        self.assertEqual(restored.assets, ["network_configuration", "admin_credentials"])
        self.assertEqual(restored.trust_boundaries, ["internet_to_management_plane"])
        self.assertEqual(restored.entrypoints, ["POST:/api/v1/system/config", "DELETE:/api/v1/routes"])
        self.assertEqual(len(restored.invariants), 1)
        self.assertEqual(restored.invariants[0].invariant_type, "auth_boundary")
        self.assertEqual(restored.metadata.get("source"), "Phase-R1.2-Baseline")

    def test_attacker_profile_immutability(self):
        """【契约 2】攻击者画像为不可变实体，严禁在运行过程中被隐式篡改"""
        with self.assertRaises(Exception):
            self.attacker.role = "tampered_role"  # type: ignore

    def test_threat_model_validation_catches_incomplete_definitions(self):
        """【契约 3】结构防御校验：拦截未指定模型ID、无攻击者角色、无资产或无信任边界的半成品"""
        self.assertEqual(len(self.threat_model.validate()), 0)

        # 缺少资产与信任边界
        invalid_tm = ThreatModel(
            model_id="",
            title="",
            attacker=AttackerProfile(role=""),
            assets=[],
            trust_boundaries=[],
        )
        errors = invalid_tm.validate()
        self.assertGreaterEqual(len(errors), 4)
        self.assertTrue(any("model_id" in err for err in errors))
        self.assertTrue(any("title" in err for err in errors))
        self.assertTrue(any("attacker role" in err for err in errors))
        self.assertTrue(any("protected asset" in err for err in errors))

    def test_derive_hypothesis_preserves_provenance(self):
        """【契约 4】从威胁模型受控派生 Hypothesis 时，自动注入模型血统与攻击者上下文"""
        hyp = self.threat_model.derive_hypothesis(
            hypothesis_id="H-AUTH-PRIVILEGED-01",
            statement="管理网段接口可能未校验 Authorization 凭证直接放行",
            rationale="静态 AST 发现该接口无鉴权中间件包裹",
        )
        self.assertIsInstance(hyp, Hypothesis)
        self.assertEqual(hyp.hypothesis_id, "H-AUTH-PRIVILEGED-01")
        self.assertEqual(hyp.status, "PROPOSED")
        self.assertIn("[ThreatModel: TM-IKUAI-ADMIN-01]", hyp.rationale)
        self.assertIn("(Attacker: anonymous_external)", hyp.rationale)
        self.assertIn("静态 AST 发现该接口无鉴权中间件包裹", hyp.rationale)


if __name__ == "__main__":
    unittest.main()
