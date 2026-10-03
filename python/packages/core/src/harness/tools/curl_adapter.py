# -*- coding: utf-8 -*-
"""
Invar 生产级 cURL 工具适配器 (Production Curl Tool Adapter)
基于操作系统原生 POSIX curl 实施高保真物理网络发包。
采用三分离架构 (-o body_file, -D header_file, -w metadata) 彻底消除手工字符串解析，
原生保持物理原始字节 (Raw Bytes)，强制绑定 RoE 门禁与凭据脱敏。
"""

import subprocess
import time
import tempfile
import os
import shlex
from urllib.parse import urlparse
from typing import Optional, Dict, Tuple, List
from pathlib import Path

from harness.tools.tool_contracts import (
    ToolRequest,
    ToolResult,
    ToolExecutionStatus,
    ToolType,
)
from harness.domain_contracts import RoEEnforcementGate, ResearchScope

class CurlToolAdapter:
    """
    cURL 原子工具适配器：负责将强类型 ToolRequest 转换为受控的 curl 子进程物理执行
    """

    @classmethod
    def execute(cls, request: ToolRequest, scope: Optional[ResearchScope] = None) -> ToolResult:
        # 1. 物理网络触达前最后一毫秒执行 RoE 前置校验 (对齐权威 assert_allowed 契约)
        if scope is not None:
            RoEEnforcementGate.assert_allowed(
                url=request.spec.url,
                method=request.spec.method,
                scope=scope
            )

        # 2. Scheme 白名单校验
        parsed_url = urlparse(request.spec.url)
        if parsed_url.scheme.lower() not in request.policy.allowed_schemes:
            raise ValueError(f"Scheme '{parsed_url.scheme}' not allowed by execution policy")

        # 3. 准备响应体与响应头的临时物证文件 (保证原始二进制字节零损耗存盘)
        body_fd, body_path = tempfile.mkstemp(prefix="invar_curl_body_")
        hdr_fd, hdr_path = tempfile.mkstemp(prefix="invar_curl_hdr_")
        os.close(body_fd)
        os.close(hdr_fd)

        payload_path: Optional[str] = None
        if request.spec.payload_bytes is not None:
            p_fd, payload_path = tempfile.mkstemp(prefix="invar_curl_payload_")
            with os.fdopen(p_fd, "wb") as pf:
                pf.write(request.spec.payload_bytes)

        try:
            # 4. 组装实际物理执行命令 (actual_cmd) 与审计脱敏命令 (redacted_cmd)
            actual_cmd, redacted_cmd = cls._build_command_pair(
                request=request,
                body_path=body_path,
                hdr_path=hdr_path,
                payload_path=payload_path
            )

            redacted_command_str = " ".join(shlex.quote(c) for c in redacted_cmd)
            command_fp = request.compute_request_fingerprint()

            t_start = time.perf_counter()
            proc = subprocess.run(
                actual_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=request.policy.timeout_seconds + 2
            )
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0

            # 5. 读取物理物证原始字节 (Raw Bytes)
            raw_bytes = Path(body_path).read_bytes()
            headers_dict, last_status_code = cls._parse_dumped_headers(Path(hdr_path))

            # 提取 curl -w 打印在 stdout 的元数据 (http_code|time_total)
            meta_status_code = None
            if proc.stdout:
                stdout_parts = proc.stdout.strip().split("|")
                if len(stdout_parts) >= 1 and stdout_parts[0].isdigit():
                    meta_status_code = int(stdout_parts[0])

            effective_status_code = meta_status_code or last_status_code

            # 判定执行状态
            if proc.returncode != 0:
                status = ToolExecutionStatus.FAILED
                if proc.returncode == 28:  # curl 超时退出码
                    status = ToolExecutionStatus.TIMEOUT

                return ToolResult.create(
                    status=status,
                    raw_bytes=raw_bytes,
                    status_code=effective_status_code if status != ToolExecutionStatus.TIMEOUT else None,
                    response_headers=headers_dict,
                    latency_ms=elapsed_ms,
                    redacted_command=redacted_command_str,
                    command_fingerprint=command_fp,
                    error_message=f"cURL error (code {proc.returncode}): {proc.stderr.strip()}"
                )

            # 正常执行成功
            return ToolResult.create(
                status=ToolExecutionStatus.SUCCESS,
                raw_bytes=raw_bytes,
                status_code=effective_status_code,
                response_headers=headers_dict,
                latency_ms=elapsed_ms,
                redacted_command=redacted_command_str,
                command_fingerprint=command_fp
            )

        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            return ToolResult.create(
                status=ToolExecutionStatus.TIMEOUT,
                raw_bytes=b"",
                status_code=None,
                latency_ms=elapsed_ms,
                redacted_command=redacted_command_str,
                command_fingerprint=command_fp,
                error_message=f"Execution timed out after {request.policy.timeout_seconds}s"
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            return ToolResult.create(
                status=ToolExecutionStatus.FAILED,
                raw_bytes=b"",
                status_code=None,
                latency_ms=elapsed_ms,
                redacted_command=redacted_command_str,
                command_fingerprint=command_fp,
                error_message=str(exc)
            )
        finally:
            # 清理物理物证临时文件
            for p in [body_path, hdr_path, payload_path]:
                if p and os.path.exists(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    @classmethod
    def _build_command_pair(
        cls,
        request: ToolRequest,
        body_path: str,
        hdr_path: str,
        payload_path: Optional[str]
    ) -> Tuple[List[str], List[str]]:
        """构建成对的实际物理执行命令与脱敏审计命令"""
        base_flags = [
            "curl", "-s", "-S",
            "-o", body_path,
            "-D", hdr_path,
            "-w", "%{http_code}|%{time_total}",
            "--max-time", str(request.policy.timeout_seconds)
        ]

        if not request.policy.verify_tls:
            base_flags.append("--insecure")

        if request.spec.follow_redirects:
            base_flags.append("-L")

        if request.spec.proxy_url:
            base_flags.extend(["--proxy", request.spec.proxy_url])

        base_flags.extend(["-X", request.spec.method])

        actual_cmd = list(base_flags)
        redacted_cmd = list(base_flags)

        # 处理标头与凭据脱敏
        redacted_headers = request.get_redacted_headers()
        for k, v in request.spec.headers.items():
            actual_cmd.extend(["-H", f"{k}: {v}"])
            redacted_v = redacted_headers[k]
            redacted_cmd.extend(["-H", f"{k}: {redacted_v}"])

        # 处理 Payload
        if payload_path is not None:
            actual_cmd.extend(["--data-binary", f"@{payload_path}"])
            redacted_cmd.extend(["--data-binary", "@<PAYLOAD_BYTES>"])

        actual_cmd.append(request.spec.url)
        redacted_cmd.append(request.spec.url)

        return actual_cmd, redacted_cmd

    @classmethod
    def _parse_dumped_headers(cls, hdr_file: Path) -> Tuple[Dict[str, str], Optional[int]]:
        """从 cURL 原生 dump 的头部文件中提取最后一段状态码与标头键值对"""
        if not hdr_file.exists():
            return {}, None

        text = hdr_file.read_text(encoding="utf-8", errors="replace")
        normalized = text.replace("\r\n", "\n")
        valid_sections = [s.strip() for s in normalized.split("\n\n") if s.strip()]
        if not valid_sections:
            return {}, None

        target_section = valid_sections[-1]
        lines = target_section.splitlines()

        headers: Dict[str, str] = {}
        status_code = None

        if lines:
            first_line = lines[0].strip()
            parts = first_line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                status_code = int(parts[1])

            for line in lines[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()

        return headers, status_code
