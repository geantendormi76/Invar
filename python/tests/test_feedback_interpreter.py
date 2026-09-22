import unittest

from harness.feedback import FeedbackFact, FeedbackInterpreter


class TestFeedbackInterpreter(unittest.TestCase):
    def setUp(self):
        self.interpreter = FeedbackInterpreter()

    def test_required_field_feedback(self):
        fact = self.interpreter.interpret(
            400,
            "Key: 'VerifyOrderRequest.UserId' failed on the 'required' tag",
        )

        self.assertIsInstance(fact, FeedbackFact)
        self.assertEqual(fact.status_code, 400)
        self.assertTrue(fact.has_required_field_error)
        self.assertEqual(fact.required_struct, "VerifyOrderRequest")
        self.assertEqual(fact.required_field, "UserId")
        self.assertFalse(fact.has_unmarshal_error)

    def test_unmarshal_feedback(self):
        fact = self.interpreter.interpret(
            400,
            "cannot unmarshal string into Go struct field Order.Amount of type int",
        )

        self.assertFalse(fact.has_required_field_error)
        self.assertTrue(fact.has_unmarshal_error)
        self.assertEqual(fact.unmarshal_source_type, "string")
        self.assertEqual(fact.unmarshal_struct, "Order")
        self.assertEqual(fact.unmarshal_field, "Amount")
        self.assertEqual(fact.unmarshal_expected_type, "int")

    def test_unknown_feedback_is_still_a_fact(self):
        fact = self.interpreter.interpret(
            403,
            "forbidden",
        )

        self.assertEqual(fact.status_code, 403)
        self.assertEqual(fact.response_text, "forbidden")
        self.assertFalse(fact.has_required_field_error)
        self.assertFalse(fact.has_unmarshal_error)


if __name__ == "__main__":
    unittest.main()
