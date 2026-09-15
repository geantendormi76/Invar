import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

@dataclass
class InvarConfig:
    """
    Invar 全局跨平台动态环境与网络配置模型
    支持双主体凭证 (auth_token: 主体A受害者 / auth_token_b: 主体B攻击者)
    """
    workspace_root: Path = field(default_factory=lambda: Path(os.getenv("INVAR_WORKSPACE", "C:/dev/Invar")))
    output_dir: Path = field(default_factory=lambda: Path(os.getenv("INVAR_OUTPUT_DIR", "C:/dev/Invar/tmp")))
    target_api_base: str = field(default_factory=lambda: os.getenv("INVAR_API_BASE", "https://hao.dieqiyun.top/api/v1"))
    auth_token: Optional[str] = field(default_factory=lambda: os.getenv("INVAR_AUTH_TOKEN", None))
    auth_token_b: Optional[str] = field(default_factory=lambda: os.getenv("INVAR_AUTH_TOKEN_B", None))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("INVAR_TIMEOUT", "5")))
    max_concurrent_workers: int = field(default_factory=lambda: int(os.getenv("INVAR_WORKERS", "10")))
    max_mutation_rounds: int = field(default_factory=lambda: int(os.getenv("INVAR_MAX_MUTATIONS", "4")))
    custom_headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Invar-Agent/3.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        for k, v in default_headers.items():
            if k not in self.custom_headers:
                self.custom_headers[k] = v
        if self.auth_token and "Authorization" not in self.custom_headers:
            self.custom_headers["Authorization"] = f"Bearer {self.auth_token}"

config = InvarConfig()
