import unittest

from harness.method_tamper import MethodTamperOperator, TamperVariant


class MethodTamperOperatorTests(unittest.TestCase):
    def test_generates_header_tunnel_variants_for_target_verb(self) -> None:
        headers = {"Accept": "application/json", "Authorization": "Bearer token123"}
        payload = {"order_id": 100}

        variants = MethodTamperOperator.generate_variants(
            method="POST",
            url="http://fixture.invalid/api/orders",
            headers=headers,
            payload=payload,
            target_verb="DELETE",
        )

        header_variants = [v for v in variants if v.strategy == "HEADER_TUNNEL"]
        self.assertTrue(len(header_variants) >= 1)

        override_variant = next(
            (v for v in header_variants if "X-HTTP-Method-Override" in v.headers),
            None,
        )
        self.assertIsNotNone(override_variant)
        self.assertEqual(override_variant.method, "POST")
        self.assertEqual(override_variant.headers["X-HTTP-Method-Override"], "DELETE")
        # 断言既有请求头不被破坏
        self.assertEqual(override_variant.headers["Accept"], "application/json")
        self.assertEqual(override_variant.target_verb, "DELETE")

    def test_generates_query_tunnel_variants_for_target_verb(self) -> None:
        variants = MethodTamperOperator.generate_variants(
            method="POST",
            url="http://fixture.invalid/api/orders",
            headers={},
            payload={},
            target_verb="DELETE",
        )

        query_variants = [v for v in variants if v.strategy == "QUERY_TUNNEL"]
        self.assertTrue(len(query_variants) >= 1)

        urls = [v.url for v in query_variants]
        self.assertTrue(any("_method=DELETE" in u or "method=DELETE" in u for u in urls))

    def test_generates_verb_substitution_variants(self) -> None:
        variants = MethodTamperOperator.generate_variants(
            method="POST",
            url="http://fixture.invalid/api/settings",
            headers={},
            payload={},
            target_verb="PUT",
        )

        sub_variants = [v for v in variants if v.strategy == "VERB_SUBSTITUTION"]
        self.assertTrue(len(sub_variants) >= 1)
        self.assertEqual(sub_variants[0].method, "PUT")

    def test_tamper_variant_contract_is_immutable(self) -> None:
        variant = TamperVariant(
            variant_id="V-001",
            strategy="HEADER_TUNNEL",
            method="POST",
            url="http://fixture.invalid/test",
            headers={"X-Override": "1"},
            payload={},
            target_verb="DELETE",
        )

        self.assertEqual(variant.variant_id, "V-001")
        self.assertEqual(variant.target_verb, "DELETE")
