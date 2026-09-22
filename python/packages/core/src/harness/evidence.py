from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import EndpointIR

@dataclass
class HTTPRequestLog:
    """
    HTTP 发包原始请求快照
    """
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None

@dataclass
class HTTPResponseLog:
    """
    HTTP 响应快照
    """
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body_preview: str = ""

@dataclass
class EvidenceRecord:
    """
    Invar 标准可追溯证据链记录对象 (Evidence Object)
    """
    endpoint: EndpointIR
    request: HTTPRequestLog
    response: HTTPResponseLog
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    finding_type: str = "ENDPOINT_PROBE"
    is_anomaly: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceRecord":
        endpoint_data = data.get("endpoint", {})
        request_data = data.get("request", {})
        response_data = data.get("response", {})

        return cls(
            endpoint=EndpointIR.from_dict(endpoint_data),
            request=HTTPRequestLog(**request_data),
            response=HTTPResponseLog(**response_data),
            timestamp=data.get("timestamp", ""),
            finding_type=data.get("finding_type", "ENDPOINT_PROBE"),
            is_anomaly=data.get("is_anomaly", False),
            notes=data.get("notes", "")
        )
