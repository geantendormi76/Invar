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
            msg = choice.get("message", {})
            content = msg.get("content") or ""
        except (KeyError, IndexError):
            raise ModelProviderError("Malformed LLM response: missing choices[0].message")

        if not content:
            raise ModelProviderError("LLM returned no final content")

        # finish_reason 闸门：length 是唯一允许进入恢复流程的非 stop 取值。
        if finish_reason == "stop":
            try:
                decoded = self._extract_json_object(content)
            except ModelProviderError:
                raise
            if not isinstance(decoded, dict):
                raise ModelProviderError("LLM structured output must be a JSON object")
            return decoded

        if finish_reason == "length":
            # Step 1: 先尝试直接解析原始 content。
            try:
                decoded = self._extract_json_object(content)
            except ModelProviderError:
                # 解析失败 -> 至多一次 continuation 恢复。
                return self._recover_length_truncation(
                    messages=messages,
                    partial_content=content,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            # 成功解析：非 object 有明确错误，dict 直接返回（不因 length 而无条件失败）。
            if not isinstance(decoded, dict):
                raise ModelProviderError("LLM structured output must be a JSON object")
            return decoded

        # 其他 finish_reason：立即失败，即使 content 恰好是合法 JSON 也不绕过闸门。
        raise ModelProviderError(
            f"LLM output incomplete: finish_reason={finish_reason}"
        )

    def _extract_json_object(self, content: str) -> Any:
        """复用现有 JSON 清洗 / raw_decode 逻辑。

        返回/异常契约（无 None 哨兵，避免与合法 JSON null 冲突）：
        * 解析失败（无 JSON / JSONDecodeError）-> 抛出 ModelProviderError；
        * 解析成功 -> 返回解析值（可为 dict / list / null 等任意类型）。
        调用方负责用 isinstance(x, dict) 区分“合法非 object”与成功 dict。

        注意：raw_decode 只解析第一个 JSON 值并容忍尾部多余内容，因此对
        截断/补全拼接场景是“语法合法即接受”，不做括号补全或语义补全。
        """
        # 1. 过滤思维链标记
        clean_text = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL)
        clean_text = re.sub(r"<think>.*?</think>", "", clean_text, flags=re.DOTALL).strip()

        # 2. 剥离 Markdown 代码块 ```json ... ```
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, flags=re.DOTALL)
        try:
            if json_match:
                return json.loads(json_match.group(1))
            first_brace = clean_text.find("{")
            if first_brace == -1:
                raise ModelProviderError("LLM output contains no JSON object")
            return json.JSONDecoder().raw_decode(clean_text[first_brace:])[0]
        except json.JSONDecodeError as exc:
            raise ModelProviderError(
                f"Failed to extract valid JSON from LLM output: {exc}. Cleaned content was: {clean_text[:200]}"
            ) from exc

    def _recover_length_truncation(
        self,
        messages: List[Dict[str, str]],
        partial_content: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """finish_reason=length 且直接解析失败时的有限恢复。

        至多一次 continuation：不修改原始 messages，基于其创建新消息列表，
        把第一次输出作为 assistant 前缀，并追加“只续写剩余 JSON 后缀”的指令。
        continuation 不传 response_format（模型只返回后缀，不返回新完整 object）。
        拼接 original + continuation 后重走统一解析；任何情况不返回部分 dict。
        """
        continuation_messages = list(messages) + [
            {"role": "assistant", "content": partial_content},
            {"role": "user", "content": (
                "You already emitted part of a JSON object but was cut off by a token "
                "limit. Continue ONLY the remaining JSON suffix from the point you stopped. "
                "Do NOT repeat the already-emitted prefix, do NOT re-emit a full JSON "
                "object, do NOT add explanation or fields unrelated to the original task. "
                "Output ONLY the characters needed to complete the JSON."
            )},
        ]

        # 至多一次 continuation（不循环、不递归重试）。
        continuation_resp = self.chat_completion(
            messages=continuation_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=None,
            enable_thinking=False,
        )
        try:
            choice = continuation_resp["choices"][0]
            c_content = choice.get("message", {}).get("content") or ""
        except (KeyError, IndexError):
            raise ModelProviderError(
                "Malformed LLM continuation response: missing choices[0].message"
            )

        # Step 3: 拼接 original + continuation 后重走统一解析。
        # 解析失败（异常）-> recovery failure；成功但非 object -> object 错误。
        try:
            decoded = self._extract_json_object(partial_content + c_content)
        except ModelProviderError:
            raise ModelProviderError(
                "LLM length truncation recovery failed: first finish_reason=length and "
                "a single continuation did not yield a parseable JSON object. "
                "combined content was: {(partial_content + c_content)[:200]}"
            )
        if not isinstance(decoded, dict):
            raise ModelProviderError("LLM structured output must be a JSON object")
        return decoded
