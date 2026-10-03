# -*- coding: utf-8 -*-
"""
Invar 权威工具网关契约 (Canonical Tool Gateway Contracts)
为外部成熟工具 (curl, ffuf, nuclei 等) 确立统一的输入规范、凭据脱敏、物理原始物证与安全策略边界。
对齐系统宪法：类型是数据边界，接口是模块边界。严禁 List[str] 万能参数逃生通道。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json
import re

class ToolType(str, Enum):
    CURL = "CURL"
    FFUF = "FFUF"
    NUCLEI = "NUCLEI"
    KATANA = "KATANA"
    HTTPX = "HTTPX"
    PLAYWRIGHT = "PLAYWRIGHT"

class ToolExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    PARSE_FAILURE = "PARSE_FAILURE"
    BLOCKED_BY_ROE = "BLOCKED_BY_ROE"

@dataclass(frozen=True)
class HttpSendSpec:
    """
    HTTP 发包强类型操作规范 (封闭结构，严禁 extra_args 逃生后门)
    """
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    payload_bytes: Optional[bytes] = None
    follow_redirects: bool = False
    proxy_url: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", self.method.upper().strip())
        object.__setattr__(self, "url", self.url.strip())

@dataclass(frozen=True)
class ToolExecutionPolicy:
    """
    工具安全执行与资源边界策略 (默认安全铁律: TLS 校验默认开启)
    """
    timeout_seconds: int = 10
    verify_tls: bool = True
    max_response_bytes: int = 10 * 1024 * 1024  # 10 MB 硬限制
    allowed_schemes: Tuple[str, ...] = ("http", "https")

@dataclass(frozen=True)
class ToolRequest:
    """
    发往底层工具执行器的标准请求凭据与上下文载体
    """
    tool_type: ToolType
    spec: HttpSendSpec
    policy: ToolExecutionPolicy = field(default_factory=ToolExecutionPolicy)
    task_id: Optional[str] = None
    principal_id: Optional[str] = None

    def get_redacted_headers(self) -> Dict[str, str]:
        """对敏感请求标头自动化执行安全脱敏"""
        sensitive_keys = {"authorization", "cookie", "token", "x-auth-token", "api-key", "secret"}
        redacted = {}
        for k, v in self.spec.headers.items():
            k_lower = k.lower()
            if any(s in k_lower for s in sensitive_keys):
                redacted[k] = "<REDACTED>"
            else:
                redacted[k] = v
        return redacted

    def compute_request_fingerprint(self) -> str:
        """生成不可变请求因果指纹 (16位 SHA256)"""
        h_sorted = json.dumps(self.get_redacted_headers(), sort_keys=True)
        p_hash = hashlib.sha256(self.spec.payload_bytes or b"").hexdigest()[:16]
        raw = f"{self.tool_type.value}:{self.spec.method}:{self.spec.url}:{h_sorted}:{p_hash}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

@dataclass(frozen=True)
class ToolResult:
    """
    底层工具物理执行后返回的不可变事实物证
    必须承载未经任何加工的物理原始字节 (Raw Bytes)，作为 Evidence 的单一事实源
    """
    status: ToolExecutionStatus
    raw_bytes: bytes
    content_hash: str
    status_code: Optional[int] = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body_text: Optional[str] = None
    is_binary: bool = False
    latency_ms: float = 0.0
    redacted_command: str = ""
    command_fingerprint: str = ""
    error_message: Optional[str] = None

    @classmethod
    def create(
        cls,
        status: ToolExecutionStatus,
        raw_bytes: bytes,
        status_code: Optional[int] = None,
        response_headers: Optional[Dict[str, str]] = None,
        latency_ms: float = 0.0,
        redacted_command: str = "",
        command_fingerprint: str = "",
        error_message: Optional[str] = None,
        is_binary: bool = False
    ) -> "ToolResult":
        # 事实铁律 1: 物理 Content-Hash 绝对基于原始字节计算
        content_hash = hashlib.sha256(raw_bytes).hexdigest()

        # 事实铁律 2: 尝试 UTF-8 文本解码，遇二进制则标记并保留原始字节
        body_text = None
        detected_binary = is_binary
        if raw_bytes and not is_binary:
            try:
                body_text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                detected_binary = True
                body_text = None

        # 事实铁律 3: 解析失败时状态码强制置为 None，严禁伪造 200
        eff_status_code = None if status == ToolExecutionStatus.PARSE_FAILURE else status_code

        return cls(
            status=status,
            raw_bytes=raw_bytes,
            content_hash=content_hash,
            status_code=eff_status_code,
            response_headers=response_headers or {},
            response_body_text=body_text,
            is_binary=detected_binary,
            latency_ms=latency_ms,
            redacted_command=redacted_command,
            command_fingerprint=command_fingerprint,
            error_message=error_message
        )
