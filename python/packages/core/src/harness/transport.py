import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
import requests


@dataclass(frozen=True)
class TransportResponse:
    """
    HTTP Transport 的确定性响应快照。
    本对象只承载 HTTP 层事实，不修改请求数据，不参与业务决策。
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

    def __init__(self):
        # 1. 彻底清除所有可能被 requests / urllib 读取的代理环境变量
        for env_key in [
            "HTTP_PROXY", "http_proxy",
            "HTTPS_PROXY", "https_proxy",
            "ALL_PROXY", "all_proxy",
        ]:
            os.environ.pop(env_key, None)

        # 2. 注入全局直连白名单，阻断 Windows 注册表 (Internet Settings) 代理劫持
        os.environ["NO_PROXY"] = "*"
        os.environ["no_proxy"] = "*"

    def request(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]],
        headers: Dict[str, str],
        timeout: int,
    ) -> TransportResponse:
        normalized_method = method.upper()
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        request_kwargs = {
            "headers": headers,
            "timeout": timeout,
            "verify": False,
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
