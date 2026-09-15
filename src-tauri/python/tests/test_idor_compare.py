import unittest

from harness.idor_compare import IdorCompareOperator


class IdorCompareOperatorTests(unittest.TestCase):
    def test_idor_vulnerable_when_attacker_receives_victim_data(self) -> None:
        # 模拟受害者 (Token A) 请求自己的资源拿到的真实基线数据
        victim_baseline_resp = '{"user_id": 1001, "secret_data": "confidential_info", "balance": 9999}'
        
        # 模拟攻击者 (Token B) 越权请求受害者资源拿到的数据
        attacker_resp = '{"user_id": 1001, "secret_data": "confidential_info", "balance": 9999}'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=victim_baseline_resp,
            attacker_response_text=attacker_resp,
            attacker_status_code=200,
        )

        self.assertEqual(evaluation.status, "vulnerable")
        self.assertIn("越权", evaluation.rationale)
        self.assertEqual(evaluation.invariant_type, "idor_boundary")

    def test_idor_confirmed_safe_when_attacker_rejected_with_403(self) -> None:
        victim_baseline_resp = '{"user_id": 1001, "secret_data": "confidential_info"}'
        attacker_resp = '{"error": "Unauthorized access to this object"}'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=victim_baseline_resp,
            attacker_response_text=attacker_resp,
            attacker_status_code=403,
        )

        self.assertEqual(evaluation.status, "confirmed")
        self.assertIn("有效隔离", evaluation.rationale)

    def test_idor_confirmed_safe_when_attacker_receives_200_but_empty_data(self) -> None:
        # 很多系统即使越权失败也会返回 200 OK，但内容是空列表或脱敏报错
        victim_baseline_resp = '{"data": {"user_id": 1001, "secret_data": "confidential_info"}, "code": 200}'
        attacker_resp = '{"data": null, "code": 200, "msg": "Resource not found or access denied"}'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=victim_baseline_resp,
            attacker_response_text=attacker_resp,
            attacker_status_code=200,
        )

        self.assertEqual(evaluation.status, "confirmed")
        self.assertIn("未发生实质性数据泄露", evaluation.rationale)
