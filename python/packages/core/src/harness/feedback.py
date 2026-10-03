# -*- coding: utf-8 -*-
"""
=============================================================================
⚠️ [DEPRECATED - Phase 9.6.5 架构净化标记]
本模块已被正式标记为待退役/合并资产 (Stale / Redundant Candidate)。
• 演进去向: Phase 9.8 (Feedback Interpreter Skill Component)
• 判定理由: 硬编码特定语言错误正则模式。将在 Phase 9.8 与变异策略统一封装下沉。
• 架构铁律: 严禁在此模块追加任何新业务逻辑或特调补丁；现有接口保持冻结兼容，
            直至对应技能剧本与工具网关就绪后彻底物理退役。
=============================================================================
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FeedbackFact:
    """
    Invar 确定性 HTTP 反馈事实。

    本对象只描述观察结果，不负责：
    - Payload Mutation
    - Research Loop 决策
    - 风险评分
    - Finding 判定
    """

    status_code: int
    response_text: str
    has_required_field_error: bool
    required_struct: Optional[str]
    required_field: Optional[str]
    has_unmarshal_error: bool
    unmarshal_source_type: Optional[str]
    unmarshal_struct: Optional[str]
    unmarshal_field: Optional[str]
    unmarshal_expected_type: Optional[str]


class FeedbackInterpreter:
    """
    将 HTTP 响应正文解释成结构化 FeedbackFact。

    [Legacy Ground Truth]
    当前规则直接对应现有 PayloadMutator 使用的两类 Go 错误模式：

    1. Key: 'Struct.Field' failed on the 'required' tag
    2. cannot unmarshal <type> into Go struct field <Struct>.<Field> of type <type>
    """

    def interpret(self, status_code: int, response_text: str) -> FeedbackFact:
        import re

        required_match = re.search(
            r"Key:\s*'(\w+)\.(\w+)'\s*failed\s*on\s*the\s*'required'\s*tag",
            response_text,
        )

        if not required_match:
            required_match = re.search(
                r"Key:\s*'(\w+)\.(\w+)'",
                response_text,
            )

        unmarshal_match = re.search(
            r"cannot unmarshal\s+(\w+)\s+into Go struct field\s+(\w+)\.(\w+)\s+of type\s+(\w+)",
            response_text,
        )

        return FeedbackFact(
            status_code=status_code,
            response_text=response_text,
            has_required_field_error=required_match is not None,
            required_struct=required_match.group(1) if required_match else None,
            required_field=required_match.group(2) if required_match else None,
            has_unmarshal_error=unmarshal_match is not None,
            unmarshal_source_type=unmarshal_match.group(1) if unmarshal_match else None,
            unmarshal_struct=unmarshal_match.group(2) if unmarshal_match else None,
            unmarshal_field=unmarshal_match.group(3) if unmarshal_match else None,
            unmarshal_expected_type=unmarshal_match.group(4) if unmarshal_match else None,
        )


if __name__ == "__main__":
    interpreter = FeedbackInterpreter()
    fact = interpreter.interpret(
        400,
        "Key: 'VerifyOrderRequest.UserId' failed on the 'required' tag",
    )
    print(fact)
