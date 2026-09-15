import re
from typing import Dict, Any, Tuple

class PayloadMutator:
    """
    Invar 核心认知层：基于执行环境与报错反馈的 Payload 自愈变异引擎
    """
    @staticmethod
    def to_snake_case(name: str) -> str:
        """
        将 PascalCase / camelCase 转换为标准 Go 结构体 tag 偏好的 snake_case
        """
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    @classmethod
    def infer_default_value(cls, field_name: str) -> Any:
        """
        基于字段名语义推断合理的基础类型占位符
        """
        p = field_name.lower()
        if any(k in p for k in ["id", "num", "count", "amount", "price", "status"]):
            return 1
        elif any(k in p for k in ["is_", "confirm", "active", "enabled"]):
            return True
        elif "email" in p:
            return "invar_probe@example.com"
        else:
            return "TEST_PROBE_VALUE"

    def mutate_from_response(
        self,
        current_payload: Dict[str, Any],
        status_code: int,
        response_text: str
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        根据 HTTP 响应状态码及报错正文，分析是否能够进行自主变异推导
        返回值: (是否发生有效变异, 变异后的新 Payload, 变异原因说明)
        """
        new_payload = dict(current_payload)
        
        # 1. 拦截 Go validator/v10 必填字段缺失错误
        # 典型特征: Key: 'VerifyOrderRequest.OutTradeNo' failed on the 'required' tag
        match_required = re.search(r"Key:\s*'(\w+)\.(\w+)'\s*failed\s*on\s*the\s*'required'\s*tag", response_text)
        if not match_required:
            match_required = re.search(r"Key:\s*'(\w+)\.(\w+)'", response_text)

        if match_required:
            struct_name = match_required.group(1)
            raw_field = match_required.group(2)
            snake_field = self.to_snake_case(raw_field)

            if snake_field not in new_payload:
                new_payload[snake_field] = self.infer_default_value(snake_field)
                reason = f"捕获到 Go 结构体 [{struct_name}] 缺失必填字段 [{raw_field}]，已自动转译为 [{snake_field}] 补全契约"
                return True, new_payload, reason

        # 2. 拦截 Go JSON 反序列化类型不匹配错误
        # 典型特征: cannot unmarshal string into Go struct field Order.amount of type int
        match_unmarshal = re.search(
            r"cannot unmarshal\s+(\w+)\s+into Go struct field\s+(\w+)\.(\w+)\s+of type\s+(\w+)",
            response_text
        )
        if match_unmarshal:
            raw_field = match_unmarshal.group(3)
            expected_type = match_unmarshal.group(4)
            snake_field = self.to_snake_case(raw_field)

            if expected_type in ["int", "int64", "int32", "float64"]:
                new_payload[snake_field] = 1
                reason = f"修复字段 [{snake_field}] 类型不匹配，已由字符串校正为数值类型 [{expected_type}]"
                return True, new_payload, reason
            elif expected_type == "bool":
                new_payload[snake_field] = True
                reason = f"修复字段 [{snake_field}] 类型不匹配，已校正为布尔类型 [bool]"
                return True, new_payload, reason

        return False, current_payload, "未识别到已知报错特征，保持原载荷"
