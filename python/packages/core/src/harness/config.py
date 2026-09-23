import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

# 动态解析 Monorepo 根目录 (从 python/packages/core/src/harness 回溯 5 层)
_REPO_ROOT = Path(__file__).resolve().parents[5]


@dataclass
class InvarConfig:
    workspace_root: Path = field(default_factory=lambda: Path(os.getenv("INVAR_WORKSPACE", str(_REPO_ROOT))))
    output_dir: Path = field(default_factory=lambda: Path(os.getenv("INVAR_OUTPUT_DIR", str(_REPO_ROOT / "tmp"))))
    target_api_base: str = field(default_factory=lambda: os.getenv("INVAR_API_BASE", "https://hao.dieqiyun.top/api/v1"))
    auth_token: Optional[str] = field(default_factory=lambda: os.getenv("INVAR_AUTH_TOKEN", None))
    auth_token_b: Optional[str] = field(default_factory=lambda: os.getenv("INVAR_AUTH_TOKEN_B", None))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("INVAR_TIMEOUT", "10")))
    max_concurrent_workers: int = field(default_factory=lambda: int(os.getenv("INVAR_WORKERS", "10")))
    max_mutation_rounds: int = field(default_factory=lambda: int(os.getenv("INVAR_MAX_MUTATIONS", "4")))
    custom_headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Sec-Ch-Ua": '"Chromium";v="128", "Google Chrome";v="128", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Content-Type": "application/json",
        }
        for k, v in default_headers.items():
            if k not in self.custom_headers:
                self.custom_headers[k] = v

        if self.auth_token and "Authorization" not in self.custom_headers:
            self.custom_headers["Authorization"] = f"Bearer {self.auth_token}"


config = InvarConfig()
