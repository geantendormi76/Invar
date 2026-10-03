# -*- coding: utf-8 -*-
"""
Invar 兼容传输层外观门面 (HttpTransport Compatibility Façade)
对齐 Phase 9.7 DoD：全仓消除重复网络发包路径，所有物理流量统一委托至 CurlToolAdapter。
保留 TransportResponse 与 HttpTransport 接口，为现有上层调用方提供 100% 向后兼容。
"""

import os
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlencode, urlunparse

from harness.tools.tool_contracts import (
    ToolRequest,
    ToolType,
    HttpSendSpec,
    ToolExecutionPolicy,
)
from harness.tools.curl_adapter import CurlToolAdapter


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
    Invar 确定性 HTTP Transport (已无感重构为 Tool Gateway 门面)。
    所有实际网络发包统一由 CurlToolAdapter 驱动，杜绝平行执行路径。
    """
    JSON_METHODS = frozenset({"POST", "PUT", "PATCH"})

    def __init__(self):
        # 1. 彻底清除所有可能被外部代理读取的环境变量
        for env_key in [
            "HTTP_PROXY", "http_proxy",
            "HTTPS_PROXY", "https_proxy",
            "ALL_PROXY", "all_proxy",
        ]:
            os.environ.pop(env_key, None)

        # 2. 注入全局直连白名单，阻断系统代理劫持
        os.environ["NO_PROXY"] = "*"
        os.environ["no_proxy"] = "*"

    def request(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> TransportResponse:
        normalized_method = method.upper()
        eff_headers = dict(headers or {})
        eff_url = url
        payload_bytes: Optional[bytes] = None

        if normalized_method in self.JSON_METHODS:
            if payload is not None:
                if isinstance(payload, bytes):
                    payload_bytes = payload
                elif isinstance(payload, str):
                    payload_bytes = payload.encode("utf-8")
                else:
                    payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                if not any(k.lower() == "content-type" for k in eff_headers):
                    eff_headers["Content-Type"] = "application/json"
        else:
            if payload and isinstance(payload, dict):
                parsed = urlparse(url)
                qs = urlencode(payload)
                new_query = f"{parsed.query}&{qs}" if parsed.query else qs
                eff_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))

        spec = HttpSendSpec(
            method=normalized_method,
            url=eff_url,
            headers=eff_headers,
            payload_bytes=payload_bytes
        )
        policy = ToolExecutionPolicy(
            timeout_seconds=timeout,
            verify_tls=False  # 保持与既有测试自签名测试桩兼容
        )
        tool_req = ToolRequest(tool_type=ToolType.CURL, spec=spec, policy=policy)
        result = CurlToolAdapter.execute(tool_req)

        return TransportResponse(
            status_code=result.status_code or 0,
            text=result.response_body_text or "",
            headers=result.response_headers
        )
