from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional, Set


class DenialLayer(str, Enum):
    """请求被拒绝的网络/架构层级"""
    EDGE = "EDGE"
    PROXY = "PROXY"
    ROUTER = "ROUTER"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    APPLICATION = "APPLICATION"
    UNKNOWN = "UNKNOWN"


class DenialCategory(str, Enum):
    """拒绝发生的原因类别（与执行组件正交）"""
    ACCESS_POLICY_DENIAL = "ACCESS_POLICY_DENIAL"
    METHOD_POLICY_DENIAL = "METHOD_POLICY_DENIAL"
    ROUTING_MISMATCH = "ROUTING_MISMATCH"
    PARSER_MISMATCH = "PARSER_MISMATCH"
    IDENTITY_OR_TRUST_CONTEXT = "IDENTITY_OR_TRUST_CONTEXT"
    RATE_LIMIT = "RATE_LIMIT"
    DEFAULT_ERROR_HANDLER = "DEFAULT_ERROR_HANDLER"
    APPLICATION_POLICY = "APPLICATION_POLICY"
    UNKNOWN = "UNKNOWN"


class FrontendComponent(str, Enum):
    """前端网络拓扑组件指纹（解决 WAF 不是 Category 的核心解耦）"""
    WAF = "WAF"
    CDN = "CDN"
    REVERSE_PROXY = "REVERSE_PROXY"
    UNKNOWN = "UNKNOWN"


class EvidenceGrade(str, Enum):
    """证据可信度等级"""
    GRADE_A = "GRADE_A"  # 确定性 RFC 规范头部、已知指纹或受控单变量差分
    GRADE_B = "GRADE_B"  # 响应体特征、状态码模式、长度/哈希差异
    GRADE_C = "GRADE_C"  # 模型推断、路径命名猜测、单次无对照响应


@dataclass
class DenialObservation:
    """
    底层客观网络观测快照（仅记录物理事实，不含主观判定）
    """
    status_code: int
    response_headers: Dict[str, str] = field(default_factory=dict)
    body_preview: str = ""
    body_hash: str = ""
    content_type: str = ""
    redirect_url: Optional[str] = None
    latency_ms: Optional[float] = None
    transport_error: Optional[str] = None

    is_soft_denial: bool = False
    business_code: Optional[int] = None
    business_message: Optional[str] = None

    def __post_init__(self):
        self.response_headers = {k.lower(): str(v) for k, v in self.response_headers.items()}
        if not self.body_hash and self.body_preview:
            self.body_hash = hashlib.sha256(self.body_preview.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SoftDenial:
    """
    软拒绝（Soft Denial）业务错误信息载体
    """
    business_code: Optional[int]
    business_message: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _json_loads(text: str) -> Any:
    import json
    return json.loads(text)


@dataclass
class DenialHypothesis:
    """
    针对拒绝原因的单项科学假设
    """
    hypothesis_id: str
    layer: DenialLayer
    category: DenialCategory
    confidence: float
    evidence_grade: EvidenceGrade
    supporting_evidence_refs: List[str] = field(default_factory=list)
    contradicting_evidence_refs: List[str] = field(default_factory=list)
    status: str = "PROPOSED"
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["layer"] = self.layer.value
        data["category"] = self.category.value
        data["evidence_grade"] = self.evidence_grade.value
        return data


@dataclass
class DenialClassificationResult:
    """
    拒绝响应综合分类结果
    """
    primary_hypothesis: DenialHypothesis
    alternative_hypotheses: List[DenialHypothesis] = field(default_factory=list)
    frontend_component: FrontendComponent = FrontendComponent.UNKNOWN
    raw_observation: Optional[DenialObservation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_hypothesis": self.primary_hypothesis.to_dict(),
            "alternative_hypotheses": [h.to_dict() for h in self.alternative_hypotheses],
            "frontend_component": self.frontend_component.value,
            "raw_observation": self.raw_observation.to_dict() if self.raw_observation else None,
        }


class DeterministicDenialClassifier:
    """
    Invar 确定性拒绝原因分类器
    """
    KNOWN_WAF_HEADERS: Set[str] = {
        "x-waf-event", "x-waf-rule", "x-sucuri-id", "x-firewall",
    }
    KNOWN_WAF_SERVER_TOKENS: Set[str] = {
        "waf", "guard", "shield", "aliyun", "tengine", "cloudflare", "imperva",
    }

    @classmethod
    def identify_frontend(cls, obs: DenialObservation) -> FrontendComponent:
        headers = obs.response_headers
        server = headers.get("server", "").lower()
        if any(h in headers for h in cls.KNOWN_WAF_HEADERS):
            return FrontendComponent.WAF
        if any(token in server for token in cls.KNOWN_WAF_SERVER_TOKENS):
            return FrontendComponent.WAF
        if "cf-ray" in headers or "x-amz-cf-id" in headers:
            return FrontendComponent.CDN
        if server in {"nginx", "apache", "caddy", "envoy", "traefik"}:
            return FrontendComponent.REVERSE_PROXY
        return FrontendComponent.UNKNOWN

    @classmethod
    def _parse_soft_denial(cls, obs: DenialObservation):
        if obs.status_code != 200 or not obs.body_preview:
            return None
        try:
            payload = _json_loads(obs.body_preview)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None

        code = payload.get("code")
        message = payload.get("message") or payload.get("msg")
        is_forbidden_code = isinstance(code, int) and (code in {401, 403, 4001, 4003, 4008} or 4000 <= code <= 4999)
        is_forbidden_msg = isinstance(message, str) and any(
            w in message.lower()
            for w in [
                "forbidden", "unauthorized", "invalid reset password token",
                "invalid token", "not logged in", "未登录", "无权限"
            ]
        )
        if is_forbidden_code or is_forbidden_msg:
            return SoftDenial(
                business_code=code if isinstance(code, int) else None,
                business_message=message,
            )
        return None

    @classmethod
    def classify(cls, obs: DenialObservation) -> DenialClassificationResult:
        frontend = cls.identify_frontend(obs)
        sc = obs.status_code
        headers = obs.response_headers

        if sc == 405:
            allow_header = headers.get("allow")
            has_allow = allow_header is not None and bool(allow_header.strip())
            return DenialClassificationResult(
                primary_hypothesis=DenialHypothesis(
                    hypothesis_id="DH-405-METHOD-POLICY",
                    layer=DenialLayer.ROUTER,
                    category=DenialCategory.METHOD_POLICY_DENIAL,
                    confidence=0.95 if has_allow else 0.75,
                    evidence_grade=EvidenceGrade.GRADE_A if has_allow else EvidenceGrade.GRADE_B,
                    supporting_evidence_refs=[f"HTTP {sc}"] + ([f"Allow: {allow_header}"] if has_allow else []),
                    rationale=f"服务端明确声明当前动词不被路由层允许 (Allow: {allow_header or 'N/A'})",
                ),
                frontend_component=frontend,
                raw_observation=obs,
            )

        if sc == 429:
            retry_after = headers.get("retry-after", "")
            return DenialClassificationResult(
                primary_hypothesis=DenialHypothesis(
                    hypothesis_id="DH-429-RATE-LIMIT",
                    layer=DenialLayer.EDGE,
                    category=DenialCategory.RATE_LIMIT,
                    confidence=0.95,
                    evidence_grade=EvidenceGrade.GRADE_A,
                    supporting_evidence_refs=[f"HTTP {sc}"] + ([f"Retry-After: {retry_after}"] if retry_after else []),
                    rationale="请求触发了速率或并发限制",
                ),
                frontend_component=frontend,
                raw_observation=obs,
            )

        if sc == 403:
            if frontend == FrontendComponent.WAF:
                primary = DenialHypothesis(
                    hypothesis_id="DH-403-EDGE-POLICY",
                    layer=DenialLayer.EDGE,
                    category=DenialCategory.ACCESS_POLICY_DENIAL,
                    confidence=0.85,
                    evidence_grade=EvidenceGrade.GRADE_A,
                    supporting_evidence_refs=[f"HTTP 403", f"WAF Server/Header: {headers.get('server', 'Header Token')}"],
                    rationale="请求被明确的前端防火墙安全策略阻断",
                )
                alt = DenialHypothesis(
                    hypothesis_id="DH-403-ROUTING-ALT",
                    layer=DenialLayer.ROUTER,
                    category=DenialCategory.ROUTING_MISMATCH,
                    confidence=0.40,
                    evidence_grade=EvidenceGrade.GRADE_B,
                    rationale="可能是反向代理针对内部特权路径的前缀黑名单拦截",
                )
                return DenialClassificationResult(
                    primary_hypothesis=primary,
                    alternative_hypotheses=[alt],
                    frontend_component=frontend,
                    raw_observation=obs,
                )

            primary = DenialHypothesis(
                hypothesis_id="DH-403-AUTH-OR-POLICY",
                layer=DenialLayer.AUTHORIZATION,
                category=DenialCategory.ACCESS_POLICY_DENIAL,
                confidence=0.60,
                evidence_grade=EvidenceGrade.GRADE_B,
                supporting_evidence_refs=["HTTP 403"],
                rationale="服务端业务层或网关因权限不足或策略校验拒绝放行",
            )
            alt1 = DenialHypothesis(
                hypothesis_id="DH-403-ROUTER-ALT",
                layer=DenialLayer.PROXY,
                category=DenialCategory.ROUTING_MISMATCH,
                confidence=0.45,
                evidence_grade=EvidenceGrade.GRADE_C,
                rationale="可能是反向代理/中间件的访问控制列表 (ACL) 拦截",
            )
            return DenialClassificationResult(
                primary_hypothesis=primary,
                alternative_hypotheses=[alt1],
                frontend_component=frontend,
                raw_observation=obs,
            )

        soft = cls._parse_soft_denial(obs)
        if soft is not None:
            return DenialClassificationResult(
                primary_hypothesis=DenialHypothesis(
                    hypothesis_id="DH-200-SOFT-ACCESS-POLICY",
                    layer=DenialLayer.APPLICATION,
                    category=DenialCategory.ACCESS_POLICY_DENIAL,
                    confidence=0.80,
                    evidence_grade=EvidenceGrade.GRADE_B,
                    supporting_evidence_refs=[
                        f"HTTP 200",
                        f"JSON code={soft.business_code}",
                        f"message={soft.business_message!r}",
                    ],
                    rationale=(
                        f"状态码为 200 但响应体 JSON 携带业务级拒绝码 {soft.business_code}，"
                        "判定为应用层/业务层的访问策略拒绝（软 403）"
                    ),
                ),
                frontend_component=frontend,
                raw_observation=obs,
            )

        return DenialClassificationResult(
            primary_hypothesis=DenialHypothesis(
                hypothesis_id=f"DH-{sc}-UNKNOWN",
                layer=DenialLayer.UNKNOWN,
                category=DenialCategory.UNKNOWN,
                confidence=0.30,
                evidence_grade=EvidenceGrade.GRADE_C,
                supporting_evidence_refs=[f"HTTP {sc}"],
                rationale=f"状态码 [{sc}] 当前未匹配到确定性拒绝规则，作为通用待决事实保留",
            ),
            frontend_component=frontend,
            raw_observation=obs,
        )
