from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


class ModelProviderError(RuntimeError):
    """模型提供器调用失败。"""


@dataclass(frozen=True)
class ModelResponse:
    model: str
    content: str


class OpenAICompatibleProvider:
    """
    OpenAI 兼容模型提供器。

    通过环境变量配置：
      INVAR_LLM_BASE_URL
      INVAR_LLM_API_KEY
      INVAR_LLM_MODEL

    默认不从代码中写死任何模型、地址或密钥。
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("INVAR_LLM_BASE_URL", "")
        ).strip().rstrip("/")

        self.api_key = (
            api_key or os.getenv("INVAR_LLM_API_KEY", "")
        ).strip()

        self.model = (
            model or os.getenv("INVAR_LLM_MODEL", "")
        ).strip()

        self.timeout = timeout

        if not self.base_url:
            raise ModelProviderError(
                "未配置 INVAR_LLM_BASE_URL。"
            )

        if not self.model:
            raise ModelProviderError(
                "未配置 INVAR_LLM_MODEL。"
            )

    @property
    def endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url

        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"

        return f"{self.base_url}/v1/chat/completions"

    def chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 6000,
    ) -> ModelResponse:
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                response = client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:2000]
            raise ModelProviderError(
                f"模型服务 HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise ModelProviderError(
                f"模型服务网络错误: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ModelProviderError(
                "模型服务返回的不是合法 JSON。"
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelProviderError(
                "模型响应缺少 choices[0].message.content。"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise ModelProviderError(
                "模型返回了空内容。"
            )

        return ModelResponse(
            model=str(data.get("model") or self.model),
            content=content,
        )
