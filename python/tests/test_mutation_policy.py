import unittest

from harness.feedback import FeedbackInterpreter
from harness.mutation_policy import MutationPolicy


class TestMutationPolicy(unittest.TestCase):
    def setUp(self):
        self.interpreter = FeedbackInterpreter()
        self.policy = MutationPolicy()

    def test_required_field_mutation_matches_legacy_behavior(self):
        fact = self.interpreter.interpret(
            400,
            "Key: 'VerifyOrderRequest.UserId' "
            "failed on the 'required' tag",
        )

        result = self.policy.mutate(
            {"out_trade_no": "TEST_PROBE_VALUE"},
            fact,
        )

        self.assertTrue(result.changed)
        self.assertEqual(
            result.payload,
            {
                "out_trade_no": "TEST_PROBE_VALUE",
                "user_id": 1,
            },
        )
        self.assertIn("VerifyOrderRequest", result.reason)
        self.assertIn("user_id", result.reason)

    def test_unmarshal_integer_mutation_matches_legacy_behavior(self):
        fact = self.interpreter.interpret(
            400,
            "cannot unmarshal string into Go struct field "
            "Order.Amount of type int",
        )

        result = self.policy.mutate(
            {"amount": "wrong"},
            fact,
        )

        self.assertTrue(result.changed)
        self.assertEqual(result.payload, {"amount": 1})
        self.assertIn("int", result.reason)

    def test_unmarshal_bool_mutation_matches_legacy_behavior(self):
        fact = self.interpreter.interpret(
            400,
            "cannot unmarshal string into Go struct field "
            "Order.Active of type bool",
        )

        result = self.policy.mutate(
            {"active": "wrong"},
            fact,
        )

        self.assertTrue(result.changed)
        self.assertEqual(result.payload, {"active": True})

    def test_unknown_feedback_does_not_mutate(self):
        fact = self.interpreter.interpret(
            403,
            "forbidden",
        )

        original = {"name": "alice"}

        result = self.policy.mutate(
            original,
            fact,
        )

        self.assertFalse(result.changed)
        self.assertEqual(result.payload, original)
        self.assertEqual(
            result.reason,
            "未识别到已知报错特征，保持原载荷",
        )


if __name__ == "__main__":
    unittest.main()
