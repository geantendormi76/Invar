# -*- coding: utf-8 -*-
"""
=============================================================================
⚠️ [DEPRECATED - Phase 9.6.5 架构净化标记]
本模块已被正式标记为待退役/合并资产 (Stale / Redundant Candidate)。
• 演进去向: Phase 9.8 (Business Context Mutation Skill)
• 判定理由: 属于针对特定语言框架 (Go struct) 的局部特调硬编码。将在 Phase 9.8 下沉为业务上下文解析策略。
• 架构铁律: 严禁在此模块追加任何新业务逻辑或特调补丁；现有接口保持冻结兼容，
            直至对应技能剧本与工具网关就绪后彻底物理退役。
=============================================================================
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, Tuple

from .feedback import FeedbackFact


@dataclass(frozen=True)
class MutationResult:
    """
    确定性 Payload Mutation 结果。

    changed:
        是否产生有效变异。

    payload:
        变异后的 Payload。

    reason:
        与旧 PayloadMutator 行为对应的变异原因。
    """

    changed: bool
    payload: Dict[str, Any]
    reason: str


class MutationPolicy:
    """
    Invar 确定性 Payload 变异策略。

    [Legacy Ground Truth]
    该策略严格承接现有 PayloadMutator.mutate_from_response()
    的两类已存在行为：

    1. required 字段缺失：
       Struct.Field -> snake_case -> infer_default_value

    2. Go JSON 类型错误：
       int/int64/int32/float64 -> 1
       bool -> True

    本类不负责：
    - HTTP
    - Feedback 解析
    - 循环控制
    - 风险评分
    - Finding 判定
    """

    @staticmethod
    def to_snake_case(name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    @staticmethod
    def infer_default_value(field_name: str) -> Any:
        p = field_name.lower()

        if any(
            k in p
            for k in ["id", "num", "count", "amount", "price", "status"]
        ):
            return 1

        if any(
            k in p
            for k in ["is_", "confirm", "active", "enabled"]
        ):
            return True

        if "email" in p:
            return "invar_probe@example.com"

        return "TEST_PROBE_VALUE"

    def mutate(
        self,
        current_payload: Dict[str, Any],
        feedback: FeedbackFact,
    ) -> MutationResult:
        new_payload = dict(current_payload)

        if feedback.has_required_field_error and feedback.required_field:
            snake_field = self.to_snake_case(
                feedback.required_field
            )

            if snake_field not in new_payload:
                new_payload[snake_field] = (
                    self.infer_default_value(snake_field)
                )

                struct_name = (
                    feedback.required_struct or "UnknownStruct"
                )

                reason = (
                    f"捕获到 Go 结构体 [{struct_name}] "
                    f"缺失必填字段 [{feedback.required_field}]，"
                    f"已自动转译为 [{snake_field}] 补全契约"
                )

                return MutationResult(
                    changed=True,
                    payload=new_payload,
                    reason=reason,
                )

        if (
            feedback.has_unmarshal_error
            and feedback.unmarshal_field
            and feedback.unmarshal_expected_type
        ):
            snake_field = self.to_snake_case(
                feedback.unmarshal_field
            )

            expected_type = feedback.unmarshal_expected_type

            if expected_type in [
                "int",
                "int64",
                "int32",
                "float64",
            ]:
                new_payload[snake_field] = 1

                reason = (
                    f"修复字段 [{snake_field}] 类型不匹配，"
                    f"已由字符串校正为数值类型 [{expected_type}]"
                )

                return MutationResult(
                    changed=True,
                    payload=new_payload,
                    reason=reason,
                )

            if expected_type == "bool":
                new_payload[snake_field] = True

                reason = (
                    f"修复字段 [{snake_field}] 类型不匹配，"
                    "已校正为布尔类型 [bool]"
                )

                return MutationResult(
                    changed=True,
                    payload=new_payload,
                    reason=reason,
                )

        return MutationResult(
            changed=False,
            payload=dict(current_payload),
            reason="未识别到已知报错特征，保持原载荷",
        )


if __name__ == "__main__":
    interpreter = __import__(
        "harness.feedback",
        fromlist=["FeedbackInterpreter"],
    ).FeedbackInterpreter()

    policy = MutationPolicy()

    fact = interpreter.interpret(
        400,
        "Key: 'VerifyOrderRequest.UserId' "
        "failed on the 'required' tag",
    )

    result = policy.mutate(
        {"out_trade_no": "TEST_PROBE_VALUE"},
        fact,
    )

    print(result)
