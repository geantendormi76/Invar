import re
from typing import List
from harness.models import EndpointIR

SENSITIVE_PARAM_KEYWORDS = {
    "token", "secret", "key", "password", "pwd", "auth",
    "confirm", "confirmation_token", "filter", "ids", "id",
    "role", "admin", "amount", "price", "order", "credit", "endpoint"
}

SENSITIVE_PATH_KEYWORDS = {
    "admin", "payment", "user", "role", "key", "secret",
    "auth", "config", "setting", "audit", "group", "event",
    "login", "session", "oauth", "password", "logout", "register",
    "upload", "download", "file", "export", "import"
}

class RiskEngine:
    """
    Invar 核心认知层：多维 API 风险量化评分与威胁决策推演引擎
    """
    @staticmethod
    def evaluate(endpoint: EndpointIR) -> EndpointIR:
        score = 0.0
        tags = set(endpoint.tags)

        # 1. HTTP 动作破坏性加权
        method = endpoint.method.upper()
        if method in ["POST", "PUT", "PATCH"]:
            score += 3.0
            tags.add("state-changing")
        elif method == "DELETE":
            score += 4.0
            tags.add("state-changing")
            tags.add("destructive")
        else:
            score += 1.0

        # 2. 路由路径语义敏感度加权
        path_lower = endpoint.path.lower()
        matched_path_kw = [kw for kw in SENSITIVE_PATH_KEYWORDS if kw in path_lower]
        if matched_path_kw:
            score += min(3.0, len(matched_path_kw) * 1.5)
            tags.add("sensitive-route")
            if any(k in path_lower for k in ["login", "auth", "token", "session"]):
                tags.add("auth")
            if any(k in path_lower for k in ["admin", "setting", "config", "audit"]):
                tags.add("sensitive")
            if any(k in path_lower for k in ["upload", "download", "file", "export"]):
                tags.add("file-op")

        # 3. AST 剥离出的真实参数敏感度加权
        param_score = 0.0
        for param in endpoint.extracted_params:
            p_lower = param.lower()
            if any(skw in p_lower for skw in SENSITIVE_PARAM_KEYWORDS):
                param_score += 1.5

        if param_score > 0:
            tags.add("sensitive-params")
            score += min(3.0, param_score)

        # 4. 分值归一化与风险等级打标 (0.0 ~ 10.0)
        final_score = round(min(10.0, score), 2)
        endpoint.risk_score = final_score

        if final_score >= 7.5:
            tags.add("risk-critical")
        elif final_score >= 5.0:
            tags.add("risk-high")
        elif final_score >= 2.5:
            tags.add("risk-medium")
        else:
            tags.add("risk-low")

        endpoint.tags = sorted(list(tags))
        return endpoint

    @staticmethod
    def evaluate_all(endpoints: List[EndpointIR]) -> List[EndpointIR]:
        return [RiskEngine.evaluate(e) for e in endpoints]
