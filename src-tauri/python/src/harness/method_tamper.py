from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


@dataclass(frozen=True)
class TamperVariant:
    """
    Invar HTTP 方法与动词隧道变异请求实体 (Tamper Variant)
    包含实施特定绕过策略后的独立物理请求要素
    """
    variant_id: str
    strategy: str  # "HEADER_TUNNEL", "QUERY_TUNNEL", "VERB_SUBSTITUTION"
    method: str
    url: str
    headers: Dict[str, str]
    payload: Dict[str, Any]
    target_verb: str


class MethodTamperOperator:
    """
    Invar 高级攻防算子：HTTP 方法篡改与动词隧道穿透算子 (Method Tamper Operator)
    专门用于刺探 WAF / 反向代理与后端业务框架之间的动词语义错位，绕过针对敏感操作的粗暴拦截
    """

    TUNNEL_HEADERS = [
        "X-HTTP-Method-Override",
        "X-Method-Override",
        "X-HTTP-Method",
    ]

    TUNNEL_QUERY_PARAMS = [
        "_method",
        "method",
    ]

    @classmethod
    def _append_query_param(cls, url: str, key: str, value: str) -> str:
        parsed = urlparse(url)
        delimiter = "&" if parsed.query else "?"
        return f"{url}{delimiter}{key}={value}"

    @classmethod
    def generate_variants(
        cls,
        method: str,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        target_verb: Optional[str] = None,
    ) -> List[TamperVariant]:
        normalized_method = method.upper()
        effective_target = (target_verb or normalized_method).upper()
        variants: List[TamperVariant] = []

        # 1. 动词同义替换策略 (Verb Substitution)
        if normalized_method != effective_target:
            variants.append(
                TamperVariant(
                    variant_id=f"VERB_SUB_{effective_target}",
                    strategy="VERB_SUBSTITUTION",
                    method=effective_target,
                    url=url,
                    headers=dict(headers),
                    payload=dict(payload),
                    target_verb=effective_target,
                )
            )
        else:
            # 若原始方法已是目标动词，衍生备选同等破坏力动词 (PUT / PATCH / DELETE)
            fallback_verbs = [v for v in ["PUT", "PATCH", "DELETE"] if v != normalized_method]
            for verb in fallback_verbs:
                variants.append(
                    TamperVariant(
                        variant_id=f"VERB_SUB_{verb}",
                        strategy="VERB_SUBSTITUTION",
                        method=verb,
                        url=url,
                        headers=dict(headers),
                        payload=dict(payload),
                        target_verb=verb,
                    )
                )

        # 2. 请求头隧道穿透策略 (Header-based Verb Tunneling)
        for h_name in cls.TUNNEL_HEADERS:
            tunnel_headers = dict(headers)
            tunnel_headers[h_name] = effective_target
            variants.append(
                TamperVariant(
                    variant_id=f"HEADER_TUNNEL_{h_name.upper().replace('-', '_')}_{effective_target}",
                    strategy="HEADER_TUNNEL",
                    method=normalized_method,
                    url=url,
                    headers=tunnel_headers,
                    payload=dict(payload),
                    target_verb=effective_target,
                )
            )

        # 3. URL 查询参数隧道穿透策略 (Query-based Verb Tunneling)
        for q_param in cls.TUNNEL_QUERY_PARAMS:
            tampered_url = cls._append_query_param(url, q_param, effective_target)
            variants.append(
                TamperVariant(
                    variant_id=f"QUERY_TUNNEL_{q_param.upper()}_{effective_target}",
                    strategy="QUERY_TUNNEL",
                    method=normalized_method,
                    url=tampered_url,
                    headers=dict(headers),
                    payload=dict(payload),
                    target_verb=effective_target,
                )
            )

        return variants
