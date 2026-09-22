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
            "choices": [{"message": {"role": "assistant", "content": "hello world"}}],
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
            "choices": [{"message": {"role": "assistant", "content": raw_llm_output}}],
        }

        with patch.object(self.provider.session, "post", return_value=fake_resp):
            data = self.provider.generate_structured_json(
                messages=[{"role": "user", "content": "analyze 403"}],
            )

        self.assertIsInstance(data, dict)
        self.assertEqual(data["strategy"], "HEADER_CUSTOM_REWRITE")
        self.assertEqual(data["suggested_header"], "X-Custom-Rewrite")
        self.assertEqual(data["confidence"], 0.88)

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
