from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass(frozen=True)
class TransportResponse:
    """
    HTTP Transport 的确定性响应快照。

    本对象只承载 HTTP 层事实，不参与：
    - 风险评分
    - Payload 推理
    - Mutation
    - Research Loop
    - Finding 判定
    """

    status_code: int
    text: str
    headers: Dict[str, str]


class HttpTransport:
    """
    Invar 确定性 HTTP Transport。

    [Legacy Ground Truth]
    对齐当前 AdaptiveSandboxExecutor 的实际 HTTP 行为：

    - POST / PUT / PATCH 使用 json=payload
    - 其他 HTTP 方法使用 params=payload
    - headers 与 timeout 由调用方显式传入

    本类不修改请求数据，不解释响应，不决定是否继续循环。
    """

    JSON_METHODS = frozenset({"POST", "PUT", "PATCH"})

    def request(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]],
        headers: Dict[str, str],
        timeout: int,
    ) -> TransportResponse:
        normalized_method = method.upper()
        request_kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": timeout,
        }

        if normalized_method in self.JSON_METHODS:
            request_kwargs["json"] = payload
        else:
            request_kwargs["params"] = payload

        response = requests.request(
            normalized_method,
            url,
            **request_kwargs,
        )

        return TransportResponse(
            status_code=response.status_code,
            text=response.text,
            headers=dict(response.headers),
        )
