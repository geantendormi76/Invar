# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch
from harness.models import EndpointIR
from harness.sandbox_executor import AdaptiveSandboxExecutor


class AdaptiveSandboxAllTests(unittest.TestCase):
    """
    高内聚整合测试：覆盖沙箱自适应变异、传输协议格式与反馈分界核心契约
    (合并原 baseline、integration、transport_baseline 碎片测试)
    """

    def setUp(self):
        self.endpoint_post = EndpointIR(
            method="POST",
            path="/api/orders",
            extracted_params=["name"],
        )
        self.endpoint_get = EndpointIR(
            method="GET",
            path="/api/users",
            extracted_params=["user_id"],
        )

    def test_feedback_mutation_loop_and_boundary_integration(self):
        """【整合契约 1】自适应沙箱在收到 Go 校验反馈后触发变异循环，且正确流转 Feedback 事实"""
        first_resp = Mock()
        first_resp.status_code = 400
        first_resp.text = "Key: 'Order.OutTradeNo' failed on the 'required' tag"
        first_resp.headers = {}

        second_resp = Mock()
        second_resp.status_code = 200
        second_resp.text = '{"code": 200, "status": "success"}'
        second_resp.headers = {}

        executor = AdaptiveSandboxExecutor()
        with patch.object(executor.transport, "request", side_effect=[first_resp, second_resp]) as req_mock,              patch.object(executor.feedback_interpreter, "interpret", wraps=executor.feedback_interpreter.interpret) as fb_mock:
            evidence = executor.probe_endpoint(self.endpoint_post)

            # 验证经历了 2 次网络发包与变异
            self.assertEqual(req_mock.call_count, 2)
            self.assertEqual(fb_mock.call_count, 2)
            self.assertEqual(evidence.response.status_code, 200)

            # 验证变异补齐了必填参数
            second_call_json = req_mock.call_args_list[1].kwargs.get("payload", {})
            self.assertIn("out_trade_no", second_call_json)

    def test_post_payload_sent_as_json_and_get_as_params(self):
        """【整合契约 2】传输层格式契约：POST 载荷走 json，GET 载荷走 query params"""
        resp = Mock()
        resp.status_code = 200
        resp.text = '{"ok": true}'
        resp.headers = {}

        executor = AdaptiveSandboxExecutor()
        with patch.object(executor.transport, "request", return_value=resp) as req_mock:
            # 1. 验证 POST
            executor.probe_endpoint(self.endpoint_post)
            post_call = req_mock.call_args
            self.assertEqual(post_call.kwargs.get("method"), "POST")
            self.assertIn("name", post_call.kwargs.get("payload", {}))

            # 2. 验证 GET
            req_mock.reset_mock()
            executor.probe_endpoint(self.endpoint_get)
            get_call = req_mock.call_args
            self.assertEqual(get_call.kwargs.get("method"), "GET")
            self.assertIn("user_id", get_call.kwargs.get("payload", {}))
