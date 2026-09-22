from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

class EndpointNotFoundError(KeyError):
    """当引用的 endpoint_id 在权威注册表中不存在时显式抛出"""
    pass

@dataclass
class EndpointIR:
    """
    Invar 标准 API 契约中间表示模型 (Intermediate Representation)
    具备防御性解构与权威身份标识能力
    """
    method: str
    path: str
    endpoint_id: str = ""
    source_file: str = ""
    line: int = 0
    is_dynamic: bool = False
    extracted_params: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    confidence: float = 1.0
    call_signature: str = ""

    def __post_init__(self):
        normalized_method = self.method.upper()
        if not self.endpoint_id:
            self.endpoint_id = f"{normalized_method}:{self.path}"
        self.method = normalized_method

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> "EndpointIR":
        if not isinstance(data, dict):
            return cls(method="GET", path="")
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def __repr__(self) -> str:
        params_preview = f", params={self.extracted_params}" if self.extracted_params else ""
        return f"<EndpointIR [{self.endpoint_id}] (line={self.line}{params_preview})>"

class EndpointRegistry:
    """
    Invar 权威端点契约注册表 (Canonical Endpoint Registry)
    保证全局生命周期内端点元数据唯一、零损耗且可被确定性引用解析。
    """
    def __init__(self):
        self._endpoints: Dict[str, EndpointIR] = {}

    def register(self, endpoint: EndpointIR) -> str:
        if not endpoint.endpoint_id:
            endpoint.endpoint_id = f"{endpoint.method.upper()}:{endpoint.path}"
        self._endpoints[endpoint.endpoint_id] = endpoint
        return endpoint.endpoint_id

    def register_all(self, endpoints: List[EndpointIR]) -> List[str]:
        return [self.register(ep) for ep in endpoints]

    def get(self, endpoint_id: str) -> EndpointIR:
        if endpoint_id not in self._endpoints:
            raise EndpointNotFoundError(
                f"Endpoint '{endpoint_id}' not found in canonical EndpointRegistry"
            )
        return self._endpoints[endpoint_id]

    def contains(self, endpoint_id: str) -> bool:
        return endpoint_id in self._endpoints

    def __len__(self) -> int:
        return len(self._endpoints)

    def to_list(self) -> List[EndpointIR]:
        return list(self._endpoints.values())
