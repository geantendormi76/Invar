from __future__ import annotations

from dataclasses import asdict, dataclass, field
import difflib
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Set
from harness.denial_models import DenialObservation
from harness.transformation_models import TransformationVariant


class ThreeValuedLogic(str, Enum):
    """三值逻辑维度断言"""
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class EquivalenceVerdict(str, Enum):
    """
    语义等价最终判决（对齐规格书第 12.2 节：严禁强制二元 True/False）
    """
    SAME_RESOURCE = "SAME_RESOURCE"            # 实锤触达同一受保护目标业务资源
    DIFFERENT_RESOURCE = "DIFFERENT_RESOURCE"  # 偏移至公开首页、登录页、软404或其他非目标资源
    UNKNOWN = "UNKNOWN"                        # 证据不充分（如裸 200 且无业务特征），拒绝假定放行


@dataclass
class SemanticDimensions:
    """
    六维资源正交等价性评估（规格书第 12.3 节）
    """
    route_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    method_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    parameter_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    identity_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    action_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN
    business_effect_equivalent: ThreeValuedLogic = ThreeValuedLogic.UNKNOWN

    def to_dict(self) -> Dict[str, str]:
        return {k: v.value for k, v in asdict(self).items()}


@dataclass
class DifferentialObservation:
    """
    基线拒绝响应与变异探测响应之间的微观物理差分（规格书第 13 节）
    """
    status_delta: int
    body_length_delta: int
    body_hash_changed: bool
    content_type_changed: bool
    location_delta: Optional[str] = None
    redirect_to_auth_barrier: bool = False
    body_similarity_to_baseline: float = 0.0
    body_similarity_to_public_root: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticEquivalenceResult:
    """
    语义等价综合判定报告实体
    """
    verdict: EquivalenceVerdict
    dimensions: SemanticDimensions
    differential: DifferentialObservation
    rationale: str
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "dimensions": self.dimensions.to_dict(),
            "differential": self.differential.to_dict(),
            "rationale": self.rationale,
            "confidence": self.confidence,
        }


class SemanticEquivalenceEvaluator:
    """
    Invar 语义等价判决器
    负责断言探测变异体是否真正触达了保护目标本身，彻底消除 200 虚假绕过
    """

    LOGIN_LOCATION_KEYWORDS: Set[str] = {
        "/login", "/auth", "/signin", "/sso", "/oauth", "login.html", "cas/login"
    }

    LOGIN_BODY_PATTERNS: List[re.Pattern] = [
        re.compile(r'<form[^>]+(?:login|auth|signin)', re.IGNORECASE),
        re.compile(r'type=["\']password["\']', re.IGNORECASE),
        re.compile(r'(?:统一身份认证|登录系统|Sign In|User Login)', re.IGNORECASE),
    ]

    GENERIC_404_PATTERNS: List[re.Pattern] = [
        re.compile(r'(?:Page Not Found|404 Not Found|页面未找到|资源不存在)', re.IGNORECASE),
    ]

    PUBLIC_ROOT_SIMILARITY_THRESHOLD: float = 0.85

    @classmethod
    def evaluate(
        cls,
        baseline: DenialObservation,
        candidate: DenialObservation,
        variant: TransformationVariant,
        expected_resource_markers: Optional[List[str]] = None,
        public_root_preview: Optional[str] = None,
    ) -> SemanticEquivalenceResult:
        # 1. 计算微观物理差分
        status_delta = candidate.status_code - baseline.status_code
        len_base = len(baseline.body_preview)
        len_cand = len(candidate.body_preview)
        body_length_delta = len_cand - len_base
        body_hash_changed = candidate.body_hash != baseline.body_hash
        content_type_changed = candidate.content_type != baseline.content_type
        location = candidate.redirect_url or candidate.response_headers.get("location")

        # 差分相似度比对
        sim_to_baseline = difflib.SequenceMatcher(
            None, baseline.body_preview, candidate.body_preview
        ).ratio()

        sim_to_root = 0.0
        if public_root_preview is not None:
            sim_to_root = difflib.SequenceMatcher(
                None, candidate.body_preview, public_root_preview
            ).ratio()

        # 2. 检查是否重定向/阻断在身份认证关卡 (Auth Barrier)
        redirect_to_auth = False
        if location:
            loc_lower = location.lower()
            if any(k in loc_lower for k in cls.LOGIN_LOCATION_KEYWORDS):
                redirect_to_auth = True

        if not redirect_to_auth and candidate.status_code in {200, 401}:
            for pat in cls.LOGIN_BODY_PATTERNS:
                if pat.search(candidate.body_preview):
                    redirect_to_auth = True
                    break

        differential = DifferentialObservation(
            status_delta=status_delta,
            body_length_delta=body_length_delta,
            body_hash_changed=body_hash_changed,
            content_type_changed=content_type_changed,
            location_delta=location,
            redirect_to_auth_barrier=redirect_to_auth,
            body_similarity_to_baseline=round(sim_to_baseline, 4),
            body_similarity_to_public_root=round(sim_to_root, 4),
        )

        dims = SemanticDimensions()

        # 3. 门禁分支 A：命中登录关卡，判定为 DIFFERENT_RESOURCE
        if redirect_to_auth:
            dims.route_equivalent = ThreeValuedLogic.NO
            dims.identity_equivalent = ThreeValuedLogic.NO
            return SemanticEquivalenceResult(
                verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                dimensions=dims,
                differential=differential,
                rationale="变异请求被引导至身份认证关卡（登录网关/表单），并未穿透至受保护目标资源",
                confidence=0.98,
            )

        # 4. 门禁分支 B：命中公共首页回退（解决 X-Rewrite-URL 引起的 200 误报）
        if (
            public_root_preview is not None
            and sim_to_root >= cls.PUBLIC_ROOT_SIMILARITY_THRESHOLD
            and 200 <= candidate.status_code < 300
        ):
            dims.route_equivalent = ThreeValuedLogic.NO
            dims.identity_equivalent = ThreeValuedLogic.NO
            return SemanticEquivalenceResult(
                verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                dimensions=dims,
                differential=differential,
                rationale=f"候选响应与站点公共根路由 (/) 页面高度重合 (相似度 {sim_to_root:.2f})，系网关重写失效后的公共页面回退",
                confidence=0.95,
            )

        # 5. 门禁分支 C：软 404 或未授权页面
        if candidate.status_code in {404, 400}:
            dims.route_equivalent = ThreeValuedLogic.NO
            return SemanticEquivalenceResult(
                verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                dimensions=dims,
                differential=differential,
                rationale=f"候选探测返回状态码 HTTP {candidate.status_code}，资源路径在应用层未被识别或未分派路由",
                confidence=0.90,
            )

        for pat in cls.GENERIC_404_PATTERNS:
            if pat.search(candidate.body_preview):
                dims.route_equivalent = ThreeValuedLogic.NO
                return SemanticEquivalenceResult(
                    verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                    dimensions=dims,
                    differential=differential,
                    rationale="响应正文包含明显的软 404 / 页面未找到标识",
                    confidence=0.92,
                )

        # 6. 门禁分支 D：业务资源标识精准核验
        if expected_resource_markers:
            matched_markers = [m for m in expected_resource_markers if m in candidate.body_preview]
            if matched_markers:
                dims.route_equivalent = ThreeValuedLogic.YES
                dims.identity_equivalent = ThreeValuedLogic.YES
                dims.action_equivalent = ThreeValuedLogic.YES
                return SemanticEquivalenceResult(
                    verdict=EquivalenceVerdict.SAME_RESOURCE,
                    dimensions=dims,
                    differential=differential,
                    rationale=f"成功匹配受保护目标的特征业务标识 [{', '.join(matched_markers)}]，证实已准确触达受控业务实体",
                    confidence=0.99,
                )
            else:
                dims.identity_equivalent = ThreeValuedLogic.NO
                return SemanticEquivalenceResult(
                    verdict=EquivalenceVerdict.DIFFERENT_RESOURCE,
                    dimensions=dims,
                    differential=differential,
                    rationale="候选响应虽返回 2xx，但缺失目标端点声明的所有预期业务特征标识，判定为非目标资源响应",
                    confidence=0.88,
                )

        # 7. 门禁分支 E：无任何业务特征参考时的裸 200（严格三值逻辑，拒绝假定成功）
        if 200 <= candidate.status_code < 300:
            dims.route_equivalent = ThreeValuedLogic.UNKNOWN
            dims.identity_equivalent = ThreeValuedLogic.UNKNOWN
            return SemanticEquivalenceResult(
                verdict=EquivalenceVerdict.UNKNOWN,
                dimensions=dims,
                differential=differential,
                rationale="候选响应返回 2xx，但调用方未提供业务实体特征参考且正文无明显标识，依据三值逻辑置为 UNKNOWN 待核验",
                confidence=0.50,
            )

        # 兜底
        return SemanticEquivalenceResult(
            verdict=EquivalenceVerdict.UNKNOWN,
            dimensions=dims,
            differential=differential,
            rationale=f"无法依据当前差分确证等价性（状态码 {candidate.status_code}）",
            confidence=0.30,
        )
