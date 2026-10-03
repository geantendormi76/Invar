# -*- coding: utf-8 -*-
"""
Invar 确定性本地测试桩 (Deterministic Local Server Fixture)
基于标准库 http.server，为工具网关提供完全离线、确定性、多场景的本地物理 HTTP 服务。
"""

import json
import time
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Generator
from contextlib import contextmanager

class LocalFixtureHandler(BaseHTTPRequestHandler):
    """
    确定性 HTTP 测试路由处理器
    """

    def log_message(self, format, *args):
        # 静默常规日志，避免污染单测输出
        pass

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_PUT(self):
        self._handle_request()

    def do_DELETE(self):
        self._handle_request()

    def _handle_request(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        # 1. 正常放行端点
        if path == "/ok":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Invar-Echo", "fixture-ok")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","message":"fixture_ready"}\n')
            return

        # 2. 标头回显端点 (验证物理发包是否送达了未脱敏的凭据)
        if path == "/echo_headers":
            headers_dict = {k: v for k, v in self.headers.items()}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(headers_dict).encode("utf-8") + b"\n")
            return

        # 3. 请求体回显端点
        if path == "/echo_body":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("X-Body-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)
            return

        # 4. 权限拒绝端点 (403)
        if path == "/forbidden":
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"forbidden","code":40301}\n')
            return

        # 5. 路由未找到端点 (404)
        if path == "/not_found":
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"route_not_found","code":40401}\n')
            return

        # 6. 精确可控的慢速超时端点 (用于确定性 TIMEOUT 断言)
        if path == "/slow":
            delay_sec = float(query.get("delay", ["0.5"])[0])
            time.sleep(delay_sec)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"slow_completed"}\n')
            return

        # 7. 纯二进制端点 (含 Null 字节与不可见字符，验证原始物证存留)
        if path == "/binary":
            binary_data = b"\x00\x01\x02\x03\xff\xfe\xaa\xbb BINARY_RAW_PAYLOAD \x00"
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(binary_data)
            return

        # 8. 畸形响应端点 (模拟损坏的 HTTP 报文流，验证 PARSE_FAILURE)
        if path == "/corrupt":
            # 绕过标准 HTTP 封装，直接往底层套接字塞垃圾文本并强制中断
            self.wfile.write(b"GARBAGE_NON_HTTP_RESPONSE_STREAM_WITHOUT_HEADERS\n")
            return

        # 默认 404
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error":"unknown_fixture_route"}\n')

class LocalFixtureServer:
    """
    自管理生命周期的本地测试桩服务上下文
    """

    def __init__(self, host: str = "127.0.0.1"):
        self.host = host
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.port: int = 0

    def start(self) -> str:
        """绑定系统随机分配的空闲端口并启动后台服务线程"""
        self.server = HTTPServer((self.host, 0), LocalFixtureHandler)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.base_url

    def stop(self) -> None:
        """关闭服务并释放端口"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            self.thread = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def __enter__(self) -> "LocalFixtureServer":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
