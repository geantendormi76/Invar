# -*- coding: utf-8 -*-
"""
Invar 双盲纯净隔离复验引擎 (Fresh Independent Verifier)
对标 Anthropic Reference Harness 与 Shannon 黄金标准：
严格遵循 PoC-Only 物理穿越原则。复验环境与发现环境绝对隔离，仅凭最小 PoC 规范重新发包复验。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import hashlib
import json
import time

from harness.tools.tool_contracts import (
    ToolRequest,
    ToolType,
    HttpSendSpec,
    ToolExecutionPolicy,
    ToolExecutionStatus,
)
from harness.tools.curl_adapter import CurlToolAdapter
from harness.invariant_evaluator import InvariantEvaluator, InvariantEvaluation
from harness.domain_contracts import (
    SecurityInvariant,
    EndpointIR,
    AuthPrincipal,
    ResearchScope,
)

class PoCType(str, Enum):
    CURL = "CURL"
    PYTHON = "PYTHON"

@dataclass(frozen=True)
class PoCSpecification:
    """
    跨越隔离边界的最小自洽可复现 PoC 契约 (PoC-Only Crossing Object)
    严禁包含任何内部探测历史、上下文变量或推论提示词
    """
    poc_type: PoCType
    method: str
    target_url: str
    headers: Dict[str, str] = field(default_factory=dict)
    payload_bytes: Optional[bytes] = None
    expected_status_code: int = 200
    expected_markers: List[str] = field(default_factory=list)
    reproducible_curl: str = ""

@dataclass(frozen=True)
class FreshVerificationResult:
    """
    在隔离环境中执行双盲物理重放后的确凿裁决事实
    """
    is_reproduced: bool
    status_code: Optional[int]
    raw_bytes: bytes
    content_hash: str
    invariant_evaluation: InvariantEvaluation
    latency_ms: float
    verifier_id: str
    reproduced_curl: str
    error_message: Optional[str] = None

class FreshSandboxVerifier:
    """
    双盲纯净复验器：在无污染环境中独立驱动 cURL 重放 PoC
    """

    def __init__(
        self,
        verifier_id: str = "fresh-verifier-prime",
        scope: Optional[ResearchScope] = None,
        timeout_seconds: int = 10
    ):
        self.verifier_id = verifier_id
        self.scope = scope
        self.timeout_seconds = timeout_seconds

    def verify_poc(
        self,
        poc: PoCSpecification,
        invariant: SecurityInvariant,
        endpoint: EndpointIR
    ) -> FreshVerificationResult:
        """
        仅凭 PoCSpecification 在全新环境中发起物理网络请求，绝不带入历史会话
        """
        # 1. 构造全新的、纯净的物理发包请求 (Clean Environment)
        spec = HttpSendSpec(
            method=poc.method.upper(),
            url=poc.target_url,
            headers=dict(poc.headers),
            payload_bytes=poc.payload_bytes
        )
        policy = ToolExecutionPolicy(
            timeout_seconds=self.timeout_seconds,
            verify_tls=False  # 适应渗透测试与本地靶标
        )
        clean_request = ToolRequest(
            tool_type=ToolType.CURL,
            spec=spec,
            policy=policy,
            task_id="FRESH-REPLAY-VERIFY"
        )

        # 2. 独立调用底层 Tool Gateway 物理发包
        tool_result = CurlToolAdapter.execute(clean_request, scope=self.scope)

        if tool_result.status != ToolExecutionStatus.SUCCESS or tool_result.status_code is None:
            # 物理发包失败或超时
            failed_eval = InvariantEvaluation(
                invariant_type=invariant.invariant_type,
                status="inconclusive",
                rationale=f"双盲复验发包失败: {tool_result.error_message or '状态码为空'}"
            )
            return FreshVerificationResult(
                is_reproduced=False,
                status_code=tool_result.status_code,
                raw_bytes=tool_result.raw_bytes,
                content_hash=tool_result.content_hash,
                invariant_evaluation=failed_eval,
                latency_ms=tool_result.latency_ms,
                verifier_id=self.verifier_id,
                reproduced_curl=tool_result.redacted_command,
                error_message=tool_result.error_message
            )

        # 3. 对全新环境中的物理物证执行不变量求值
        body_text = tool_result.response_body_text or ""
        parsed_payload: Dict[str, Any] = {}
        if poc.payload_bytes:
            try:
                parsed_payload = json.loads(poc.payload_bytes.decode("utf-8"))
            except Exception:
                pass

        eval_result = InvariantEvaluator.evaluate(
            endpoint=endpoint,
            invariant=invariant,
            headers=tool_result.response_headers,
            payload=parsed_payload,
            status_code=tool_result.status_code,
            response_text=body_text
        )

        # 4. 判定复现稳定性：状态码符合预期且不变量实锤被击穿 (vulnerable)
        markers_matched = True
        if poc.expected_markers:
            markers_matched = all(m in body_text for m in poc.expected_markers)

        is_reproduced = (
            tool_result.status_code == poc.expected_status_code and
            eval_result.status == "vulnerable" and
            markers_matched
        )

        return FreshVerificationResult(
            is_reproduced=is_reproduced,
            status_code=tool_result.status_code,
            raw_bytes=tool_result.raw_bytes,
            content_hash=tool_result.content_hash,
            invariant_evaluation=eval_result,
            latency_ms=tool_result.latency_ms,
            verifier_id=self.verifier_id,
            reproduced_curl=tool_result.redacted_command
        )
