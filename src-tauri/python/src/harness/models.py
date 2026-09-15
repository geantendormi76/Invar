from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class EndpointIR:
    """
    Invar 标准 API 契约中间表示模型 (Intermediate Representation)
    具备防御性解构与多态容错能力
    """
    method: str
    path: str
    source_file: str = ""
    line: int = 0
    is_dynamic: bool = False
    extracted_params: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    confidence: float = 1.0
    call_signature: str = ""

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
        return f"<EndpointIR [{self.method}] {self.path} (line={self.line}{params_preview})>"
