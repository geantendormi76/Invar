# -*- coding: utf-8 -*-
"""
Invar Authorization Baseline Contract Tests
对标 Claude-Red (IDOR SOP) 与 Tencent A.I.G 黄金标准。
严格约束 BOLA / IDOR 判定算子必须基于对象引用（Object Reference）与属主身份绑定，
彻底终结单纯依赖 difflib.SequenceMatcher 字符串相似度所导致的同构 JSON 致命误报陷阱。
"""
import unittest

from harness.idor_compare import IdorCompareOperator


class AuthorizationBaselineContractTests(unittest.TestCase):
    """
    授权关系基线与对象引用比对契约测试集
    """

    def test_idor_vulnerable_when_victim_object_leaked_to_attacker(self):
        """【契约 1】真正越权：攻击者请求收到了受害者（User 1001）的私密对象实体，实锤越权"""
        victim_resp = '{"user_id": 1001, "name": "alice", "balance": 9999, "role": "vip"}'
        attacker_resp = '{"user_id": 1001, "name": "alice", "balance": 9999, "role": "vip"}'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=victim_resp,
            attacker_response_text=attacker_resp,
            attacker_status_code=200,
        )

        self.assertEqual(evaluation.status, "vulnerable")
        self.assertIn("越权", evaluation.rationale)

    def test_idor_safe_when_attacker_receives_own_distinct_object_with_identical_schema(self):
        """【契约 2（核心防误报）】合法访问：攻击者拿到的是属于自己的合法数据（User 1002）。
        虽然与受害者数据 Schema 完全同构，但对象属主明确不同，绝不可误判为越权！"""
        victim_resp = '{"user_id": 1001, "name": "alice", "balance": 9999, "role": "vip"}'
        attacker_own_resp = '{"user_id": 1002, "name": "bob", "balance": 50, "role": "member"}'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=victim_resp,
            attacker_response_text=attacker_own_resp,
            attacker_status_code=200,
        )

        # 契约铁律：对象标识为 1002，属于攻击者自己的合法资产，必须判定为安全 (confirmed)
        self.assertEqual(evaluation.status, "confirmed")
        self.assertNotIn("存在水平越权", evaluation.rationale)

    def test_idor_safe_when_different_document_id_with_identical_schema(self):
        """【契约 3（核心防误报）】EXP-02 场景 3 陷阱：两份独立业务文档仅 doc_id 不同。
        字符相似度高达 0.99，但因对象标识符不同（DOC-90001 vs DOC-90002），绝不可误判为越权！"""
        doc_victim = '{"doc_id": "DOC-90001", "status": "APPROVED", "dept": "FINANCE", "valid": true}'
        doc_attacker = '{"doc_id": "DOC-90002", "status": "APPROVED", "dept": "FINANCE", "valid": true}'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=doc_victim,
            attacker_response_text=doc_attacker,
            attacker_status_code=200,
        )

        # 契约铁律：消除字符级 0.99 相似度假象，属主对象不同必须判定为安全 (confirmed)
        self.assertEqual(evaluation.status, "confirmed")

    def test_idor_vulnerable_when_victim_identifier_leaks_in_different_wrapper(self):
        """【契约 4】智能识别：即便响应加了外层包装或结构微调，只要受害者对象 ID (1001) 泄露在攻击者响应中，仍属越权"""
        victim_resp = '{"user_id": 1001, "secret": "s3cr3t"}'
        attacker_resp = '{"code": 200, "data": {"target_user_id": 1001, "secret": "s3cr3t"}, "msg": "ok"}'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=victim_resp,
            attacker_response_text=attacker_resp,
            attacker_status_code=200,
        )

        self.assertEqual(evaluation.status, "vulnerable")

    def test_idor_confirmed_safe_on_http_403_or_401(self):
        """【契约 5】常规拦截：服务端返回 401/403，安全边界守住"""
        victim_resp = '{"user_id": 1001, "balance": 9999}'
        attacker_resp = '{"error": "Forbidden"}'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=victim_resp,
            attacker_response_text=attacker_resp,
            attacker_status_code=403,
        )

        self.assertEqual(evaluation.status, "confirmed")

    def test_idor_inconclusive_on_http_500(self):
        """【契约 6】异常兜底：服务端 500 报错，不能断定安全，判定为存疑 (inconclusive)"""
        victim_resp = '{"user_id": 1001, "balance": 9999}'
        attacker_resp = 'Internal Server Error'

        evaluation = IdorCompareOperator.compare(
            victim_response_text=victim_resp,
            attacker_response_text=attacker_resp,
            attacker_status_code=500,
        )

        self.assertEqual(evaluation.status, "inconclusive")


if __name__ == "__main__":
    unittest.main()
