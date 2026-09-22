from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
import requests


class ModelProviderError(RuntimeError):
    """大模型提供者调用或解析异常"""
    pass


class OpenAICompatibleProvider:
    """
    通用 OpenAI 兼容协议大模型提供者
    无缝适配本地 llama-server (127.0.0.1:8080) 以及任何标准兼容端点
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
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
        self.timeout = timeout
        self.session = session or requests.Session()

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发起标准 /chat/completions 调用并返回标准响应字典
        """
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

        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
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
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        调用模型并自愈提取纯净 JSON 对象
        自动过滤大模型返回的思维链思考过程 (<thought>...</thought>) 与 Markdown 代码块标记
        """
        raw_resp = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            content = raw_resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ModelProviderError("Malformed LLM response: missing choices[0].message.content")

        # 1. 过滤思维链标记
        clean_text = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL)
        clean_text = re.sub(r"<think>.*?</think>", "", clean_text, flags=re.DOTALL).strip()

        # 2. 剥离 Markdown 代码块 ```json ... ```
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, flags=re.DOTALL)
        if json_match:
            candidate_json = json_match.group(1)
        else:
            # 尝试截取最外层的 { 和 }
            first_brace = clean_text.find("{")
            last_brace = clean_text.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                candidate_json = clean_text[first_brace:last_brace + 1]
            else:
                candidate_json = clean_text

        try:
            return json.loads(candidate_json)
        except json.JSONDecodeError as exc:
            raise ModelProviderError(
                f"Failed to extract valid JSON from LLM output: {exc}. Cleaned content was: {clean_text[:200]}"
            ) from exc
