import unittest
from harness.transformation_models import (
    TransformationFamily,
    TransformationFamilyRegistry,
    TransformationVariant,
)


class TransformationFamilyContractTests(unittest.TestCase):
    """
    针对 9 大变换族算子库的完整契约与不变性验证
    """

    def setUp(self):
        self.base_url = "https://example.com/api/v1/secret"
        self.base_headers = {"Accept": "application/json", "Authorization": "Bearer token123"}
        self.base_payload = {"id": 100}

    def test_f1_path_normalization_covers_essential_tricks(self):
        """【契约 1】F1 族完整覆盖 bypass-403 的点号、斜杠、分号与后缀变异"""
        variants = TransformationFamilyRegistry.generate_f1_path_variants(
            url=self.base_url,
            method="GET",
            headers=self.base_headers,
            payload=self.base_payload,
        )
        urls = [v.url for v in variants]

        # 1. 必须覆盖点号与多斜杠
        self.assertTrue(any("/%2e/api/v1/secret" in u for u in urls))
        self.assertTrue(any("/api/v1/secret/." in u for u in urls))
        self.assertTrue(any("//api/v1/secret//" in u for u in urls))
        # 2. 必须覆盖 Tomcat 分号畸变
        self.assertTrue(any("/api/v1/secret..;/" in u for u in urls))
        self.assertTrue(any("/api/v1/secret;/" in u for u in urls))
        # 3. 必须覆盖空白符与查询分隔符
        self.assertTrue(any("/api/v1/secret%20" in u for u in urls))
        self.assertTrue(any("/api/v1/secret?" in u for u in urls))
        self.assertTrue(any("/api/v1/secret#" in u for u in urls))
        # 4. 必须覆盖后缀混淆
        self.assertTrue(any("/api/v1/secret.json" in u for u in urls))
        self.assertTrue(any("/api/v1/secret.html" in u for u in urls))

    def test_f2_method_semantics_covers_post_trace_and_verb_tunnels(self):
        """【契约 2】F2 族完整覆盖 POST 空体降级、TRACE 与动词隧道请求头"""
        variants = TransformationFamilyRegistry.generate_f2_method_variants(
            url=self.base_url,
            method="DELETE",
            headers=self.base_headers,
            payload=self.base_payload,
        )
        # 1. POST Content-Length: 0
        post_var = next((v for v in variants if v.variant_id == "F2_POST_EMPTY_BODY"), None)
        self.assertIsNotNone(post_var)
        self.assertEqual(post_var.method, "POST")
        self.assertEqual(post_var.headers.get("Content-Length"), "0")
        # 2. TRACE 动词
        trace_var = next((v for v in variants if v.variant_id == "F2_VERB_TRACE"), None)
        self.assertIsNotNone(trace_var)
        self.assertEqual(trace_var.method, "TRACE")
        # 3. 动词隧道头
        override_var = next((v for v in variants if "X_HTTP_METHOD_OVERRIDE" in v.variant_id), None)
        self.assertIsNotNone(override_var)
        self.assertEqual(override_var.headers.get("X-HTTP-Method-Override"), "DELETE")

    def test_f3_header_trust_covers_rewrite_and_ip_spoofing(self):
        """【契约 3】F3 族完整覆盖 X-Rewrite-URL 移花接木与 IP 伪造头"""
        variants = TransformationFamilyRegistry.generate_f3_header_trust_variants(
            url=self.base_url,
            method="GET",
            headers=self.base_headers,
            payload=self.base_payload,
        )
        # 1. 代理重写头：目标请求 URL 被指向根路由 '/'，但请求头指定内部路径
        rw_var = next((v for v in variants if "X_REWRITE_URL" in v.variant_id), None)
        self.assertIsNotNone(rw_var)
        self.assertEqual(rw_var.url, "https://example.com/")
        self.assertEqual(rw_var.headers.get("X-Rewrite-URL"), "/api/v1/secret")
        # 2. 内网 IP 伪装头：X-Forwarded-For 与 X-Host
        xff_var = next((v for v in variants if "X_FORWARDED_FOR_127_0_0_1" in v.variant_id), None)
        self.assertIsNotNone(xff_var)
        self.assertEqual(xff_var.headers.get("X-Forwarded-For"), "127.0.0.1")
        xhost_var = next((v for v in variants if "X_HOST" in v.variant_id), None)
        self.assertIsNotNone(xhost_var)
        self.assertEqual(xhost_var.headers.get("X-Host"), "127.0.0.1")

    def test_original_headers_and_payload_immutability(self):
        """【契约 4】不变性保障：所有变异实体均不污染调用方传入的原始字典"""
        orig_headers = {"User-Agent": "Invar"}
        orig_payload = {"key": "val"}
        variants = TransformationFamilyRegistry.generate_all(
            url=self.base_url,
            method="GET",
            headers=orig_headers,
            payload=orig_payload,
        )
        # 原始字典未被修改
        self.assertEqual(orig_headers, {"User-Agent": "Invar"})
        self.assertEqual(orig_payload, {"key": "val"})
        # 变异体是不可变的 frozen dataclass
        self.assertIsInstance(variants[0], TransformationVariant)
        with self.assertRaises(Exception):
            variants[0].method = "HACKED"  # type: ignore

    def test_deterministic_deduplication(self):
        """【契约 5】幂等去重：同一配置下多族组合产出的变异清单无重复"""
        variants = TransformationFamilyRegistry.generate_all(
            url=self.base_url,
            method="GET",
            headers=self.base_headers,
            payload=self.base_payload,
        )
        self.assertTrue(len(variants) >= 20)
        # 保证 variant_id 全局唯一
        var_ids = [v.variant_id for v in variants]
        self.assertEqual(len(var_ids), len(set(var_ids)))


if __name__ == "__main__":
    unittest.main()
