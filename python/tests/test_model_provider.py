import json
import unittest
from unittest.mock import Mock, patch
import requests
from agent.model_provider import ModelProviderError, OpenAICompatibleProvider


class ModelProviderContractTests(unittest.TestCase):
    """
    针对本地与云端 OpenAI 兼容通信提供者的严格契约测试
    """

    def setUp(self):
        self.provider = OpenAICompatibleProvider(
            base_url="http://127.0.0.1:8080/v1",
            api_key="test-token",
            model="qwen-27b",
            timeout=5,
        )

    def test_chat_completion_sends_valid_openai_payload(self):
        """【契约 1】发往 LLM 的物理发包必须 100% 符合 OpenAI API 规范"""
        fake_resp = Mock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "id": "chatcmpl-001",
            "choices": [{
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "hello world"},
            }],
        }

        with patch.object(self.provider.session, "post", return_value=fake_resp) as post_mock:
            res = self.provider.chat_completion(
                messages=[{"role": "user", "content": "ping"}],
                temperature=0.3,
                max_tokens=256,
            )

        post_mock.assert_called_once()
        call_kwargs = post_mock.call_args.kwargs
        self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer test-token")
        self.assertEqual(call_kwargs["json"]["model"], "qwen-27b")
        self.assertEqual(call_kwargs["json"]["temperature"], 0.3)
        self.assertEqual(res["choices"][0]["message"]["content"], "hello world")

    def test_structured_json_extraction_filters_thoughts_and_markdown(self):
        """【契约 2】深度推理自愈：能够精准剔除 <thought> 思维链并剥离 Markdown 提取纯净 JSON"""
        raw_llm_output = """
        <thought>
        The user is asking for a custom 403 bypass proposal.
        The WAF is blocking based on the path. I should propose a custom header.
        </thought>
        Here is the JSON proposal:
        ```json
        {
            "strategy": "HEADER_CUSTOM_REWRITE",
            "suggested_header": "X-Custom-Rewrite",
            "suggested_value": "/internal/api",
            "confidence": 0.88
        }
        ```
        Hope this helps!
        """
        fake_resp = Mock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "choices": [{
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": raw_llm_output},
            }],
        }

        with patch.object(self.provider.session, "post", return_value=fake_resp):
            data = self.provider.generate_structured_json(
                messages=[{"role": "user", "content": "analyze 403"}],
            )

        self.assertIsInstance(data, dict)
        self.assertEqual(data["strategy"], "HEADER_CUSTOM_REWRITE")
        self.assertEqual(data["suggested_header"], "X-Custom-Rewrite")
        self.assertEqual(data["confidence"], 0.88)

    def test_structured_json_accepts_bare_object_and_disables_thinking(self):
        fake_resp = Mock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "choices": [{
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": '{"rationale":"test","headers":{},"payload":{}}',
                },
            }],
        }

        with patch.object(self.provider.session, "post", return_value=fake_resp) as post_mock:
            data = self.provider.generate_structured_json(
                messages=[{"role": "user", "content": "return json"}],
            )

        request_payload = post_mock.call_args.kwargs["json"]
        self.assertEqual(data["rationale"], "test")
        self.assertEqual(request_payload["max_tokens"], 256)
        self.assertEqual(request_payload["response_format"], {"type": "json_object"})
        self.assertEqual(
            request_payload["chat_template_kwargs"],
            {"enable_thinking": False},
        )
        self.assertFalse(self.provider.session.trust_env)

    def test_structured_json_length_but_complete_returns_without_continuation(self):
        """【契约 A】length 但 content 已是合法完整 JSON：成功返回，不触发 continuation。"""
        complete_json = '{"rationale":"ok","headers":{},"payload":{}}'
        fake_resp = Mock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "choices": [{
                "finish_reason": "length",
                "message": {"role": "assistant", "content": complete_json},
            }],
        }

        with patch.object(self.provider.session, "post", return_value=fake_resp) as post_mock:
            data = self.provider.generate_structured_json(
                messages=[{"role": "user", "content": "return json"}],
            )

        self.assertEqual(data, {"rationale": "ok", "headers": {}, "payload": {}})
        self.assertEqual(post_mock.call_count, 1)

    def test_structured_json_length_truncation_recovers_via_single_continuation(self):
        """【契约 B】length + 真正截断 + continuation 成功：返回完整 dict，仅调用两次。"""
        partial = '{"rationale":"test","status":"'
        suffix = 'verified"}'

        first_resp = Mock()
        first_resp.status_code = 200
        first_resp.json.return_value = {
            "choices": [{
                "finish_reason": "length",
                "message": {"role": "assistant", "content": partial},
            }],
        }
        second_resp = Mock()
        second_resp.status_code = 200
        second_resp.json.return_value = {
            "choices": [{
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": suffix},
            }],
        }

        with patch.object(
            self.provider.session, "post", side_effect=[first_resp, second_resp]
        ) as post_mock:
            data = self.provider.generate_structured_json(
                messages=[{"role": "user", "content": "return json"}],
            )

        self.assertEqual(data, {"rationale": "test", "status": "verified"})
        self.assertEqual(post_mock.call_count, 2)

        # 第二次调用必须基于原 messages 创建新列表，且包含 assistant 前缀 + 续写指令。
        second_call = post_mock.call_args_list[1]
        second_messages = second_call.kwargs["json"]["messages"]
        self.assertEqual(len(second_messages), 3)
        self.assertEqual(second_messages[1]["role"], "assistant")
        self.assertEqual(second_messages[1]["content"], partial)
        self.assertEqual(second_messages[2]["role"], "user")
        self.assertIn("suffix", second_messages[2]["content"].lower())
        # 续写不要求返回新完整 object，不传 response_format。
        self.assertNotIn("response_format", second_call.kwargs["json"])
        # 原始 messages 不被修改。
        self.assertEqual(
            second_messages[0], {"role": "user", "content": "return json"}
        )

    def test_structured_json_length_truncation_recovery_failure(self):
        """【契约 C】length + continuation 仍无法形成合法 JSON：抛错，无第三次请求。"""
        first_resp = Mock()
        first_resp.status_code = 200
        first_resp.json.return_value = {
            "choices": [{
                "finish_reason": "length",
                "message": {"role": "assistant", "content": '{"rationale":"trunc',
                            "reasoning_content": "unfinished"},
            }],
        }
        second_resp = Mock()
        second_resp.status_code = 200
        second_resp.json.return_value = {
            "choices": [{
                "finish_reason": "length",
                "message": {"role": "assistant", "content": "ated more garbage"},
            }],
        }

        with patch.object(
            self.provider.session, "post", side_effect=[first_resp, second_resp]
        ) as post_mock:
            with self.assertRaises(ModelProviderError) as ctx:
                self.provider.generate_structured_json(
                    messages=[{"role": "user", "content": "return json"}],
                )

        self.assertIn("length", str(ctx.exception))
        self.assertIn("recovery", str(ctx.exception).lower())
        self.assertEqual(post_mock.call_count, 2)

    def test_structured_json_other_finish_reason_keeps_original_failure(self):
        """【契约 D-1】非 length 的 finish_reason（content_filter）+ 非法 JSON：原失败路径，无 continuation。"""
        fake_resp = Mock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "choices": [{
                "finish_reason": "content_filter",
                "message": {"role": "assistant", "content": '{"rationale":"blocked"',
                            "reasoning_content": "filtered"},
            }],
        }

        with patch.object(self.provider.session, "post", return_value=fake_resp) as post_mock:
            with self.assertRaises(ModelProviderError) as ctx:
                self.provider.generate_structured_json(
                    messages=[{"role": "user", "content": "return json"}],
                )

        self.assertIn("content_filter", str(ctx.exception))
        self.assertEqual(post_mock.call_count, 1)

    def test_structured_json_other_finish_reason_does_not_bypass_gate_with_valid_json(self):
        """【契约 D-2】非 length 的 finish_reason（content_filter）+ 合法完整 JSON：
        仍必须 ModelProviderError，确认其他 finish_reason 不会绕过失败闸门，无 continuation。"""
        valid_json = '{"rationale":"valid","status":"ok"}'
        fake_resp = Mock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "choices": [{
                "finish_reason": "content_filter",
                "message": {"role": "assistant", "content": valid_json},
            }],
        }

        with patch.object(self.provider.session, "post", return_value=fake_resp) as post_mock:
            with self.assertRaises(ModelProviderError) as ctx:
                self.provider.generate_structured_json(
                    messages=[{"role": "user", "content": "return json"}],
                )

        self.assertIn("content_filter", str(ctx.exception))
        # 关键：即使 content 是合法完整 JSON，也不得成功，且不触发第二次请求。
        self.assertEqual(post_mock.call_count, 1)

    def test_structured_json_tool_calls_finish_reason_keeps_original_failure(self):
        """【契约 D-3】tool_calls 等其它 finish_reason 同样保持原失败路径。"""
        fake_resp = Mock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "choices": [{
                "finish_reason": "tool_calls",
                "message": {"role": "assistant", "content": '{"rationale":"valid"}'},
            }],
        }

        with patch.object(self.provider.session, "post", return_value=fake_resp) as post_mock:
            with self.assertRaises(ModelProviderError) as ctx:
                self.provider.generate_structured_json(
                    messages=[{"role": "user", "content": "return json"}],
                )

        self.assertIn("tool_calls", str(ctx.exception))
        self.assertEqual(post_mock.call_count, 1)

    def test_connection_error_raises_structured_model_provider_error(self):
        """【契约 3】网络故障或本地 llama-server 未就绪时，抛出结构化异常，优雅容错"""
        with patch.object(
            self.provider.session,
            "post",
            side_effect=requests.exceptions.ConnectionError("Connection refused to 127.0.0.1:8080"),
        ):
            with self.assertRaises(ModelProviderError) as ctx:
                self.provider.chat_completion([{"role": "user", "content": "hi"}])
            self.assertIn("connection failed", str(ctx.exception))

    def test_non_200_error_handling(self):
        """【契约 4】非 200 状态码（如 500/404）正确识别并包含上下文"""
        fake_resp = Mock()
        fake_resp.status_code = 500
        fake_resp.text = "Internal Model Runner CUDA OOM Error"

        with patch.object(self.provider.session, "post", return_value=fake_resp):
            with self.assertRaises(ModelProviderError) as ctx:
                self.provider.chat_completion([{"role": "user", "content": "hi"}])
            self.assertIn("500", str(ctx.exception))
            self.assertIn("CUDA OOM", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
