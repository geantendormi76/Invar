from __future__ import annotations
import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import requests

class ModelProviderError(RuntimeError):
    """大模型提供者调用或解析异常"""
    pass

class OpenAICompatibleProvider:
    """
    通用 OpenAI 兼容协议大模型提供者
    适配本地 llama-server 以及任何标准兼容端点
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv("INVAR_LLM_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or "http://127.0.0.1:8080/v1"
        ).rstrip("/")
        self.api_key = (
            api_key
            or os.getenv("INVAR_LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or "not-needed"
        )
        self.model = (
            model
            or os.getenv("INVAR_LLM_MODEL")
            or "default"
        )
        self.timeout = int(os.getenv("INVAR_LLM_TIMEOUT") or timeout)
        self.session = session or requests.Session()
        if session is None and urlparse(self.base_url).hostname in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            self.session.trust_env = False

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
        enable_thinking: Optional[bool] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        if enable_thinking is not None:
            payload["chat_template_kwargs"] = {
                "enable_thinking": enable_thinking,
            }

        try:
            resp = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=(5, self.timeout),
            )
            if resp.status_code != 200:
                raise ModelProviderError(
                    f"LLM API returned non-200 status code [{resp.status_code}]: {resp.text[:300]}"
                )
            data = resp.json()
            if not isinstance(data, dict) or "choices" not in data:
                raise ModelProviderError(f"LLM API returned invalid OpenAI schema: {resp.text[:300]}")
            return data
        except requests.exceptions.Timeout as exc:
            raise ModelProviderError(f"LLM request timed out after {self.timeout}s: {exc}") from exc
        except requests.exceptions.ConnectionError as exc:
            raise ModelProviderError(f"LLM endpoint connection failed ({self.base_url}): {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ModelProviderError(f"Failed to parse LLM response as JSON: {exc}") from exc

    def generate_structured_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 256,
    ) -> Dict[str, Any]:
        raw_resp = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            enable_thinking=False,
        )
        try:
            choice = raw_resp["choices"][0]
            finish_reason = choice.get("finish_reason")
            if finish_reason != "stop":
                raise ModelProviderError(
                    f"LLM output incomplete: finish_reason={finish_reason}"
                )
            msg = choice.get("message", {})
            content = msg.get("content") or ""
        except (KeyError, IndexError):
            raise ModelProviderError("Malformed LLM response: missing choices[0].message")

        if not content:
            raise ModelProviderError("LLM returned no final content")

        # 1. 过滤思维链标记
        clean_text = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL)
        clean_text = re.sub(r"<think>.*?</think>", "", clean_text, flags=re.DOTALL).strip()

        # 2. 剥离 Markdown 代码块 ```json ... ```
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, flags=re.DOTALL)
        try:
            if json_match:
                decoded = json.loads(json_match.group(1))
            else:
                first_brace = clean_text.find("{")
                if first_brace == -1:
                    raise ModelProviderError("LLM output contains no JSON object")
                decoded, _ = json.JSONDecoder().raw_decode(
                    clean_text[first_brace:]
                )
        except json.JSONDecodeError as exc:
            raise ModelProviderError(
                f"Failed to extract valid JSON from LLM output: {exc}. Cleaned content was: {clean_text[:200]}"
            ) from exc

        if not isinstance(decoded, dict):
            raise ModelProviderError("LLM structured output must be a JSON object")
        return decoded
