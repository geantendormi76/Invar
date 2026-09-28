import os
from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from typing import Any, Dict, Optional

from harness.run_models import RunTrack

# 动态解析 Monorepo 根目录 (从 python/packages/core/src/harness 回溯 5 层)
_REPO_ROOT = Path(__file__).resolve().parents[5]


def _load_toml_safe(path: Path) -> Dict[str, Any]:
    """安全解析 TOML 文件，不存在或解析异常时优雅返回空字典"""
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _resolve_track_from_name(track_name: Optional[str], default: RunTrack = RunTrack.PRODUCTION) -> RunTrack:
    """将名称安全转换为 RunTrack 枚举"""
    if not track_name:
        return default
    tn = str(track_name).strip().upper()
    try:
        return RunTrack(tn)
    except ValueError:
        return default


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

    # 运行轨道与 Profile 契约字段
    profile: Optional[str] = None
    track: Optional[RunTrack] = None
    project_config: Dict[str, Any] = field(default_factory=dict)
    profile_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. 读取 configs/base/project.toml 基础配置
        proj_toml_path = self.workspace_root / "configs" / "base" / "project.toml"
        self.project_config = _load_toml_safe(proj_toml_path)

        # 2. 确定 active profile（环境变量 INVAR_PROFILE > 显式参数 > project.toml > 默认 "production"）
        if self.profile is None:
            env_profile = os.getenv("INVAR_PROFILE")
            if env_profile:
                self.profile = env_profile
            else:
                proj_info = self.project_config.get("project", {})
                self.profile = proj_info.get("profile", "production")

        # 3. 读取 configs/profiles/{self.profile}.toml
        prof_toml_path = self.workspace_root / "configs" / "profiles" / f"{self.profile}.toml"
        self.profile_config = _load_toml_safe(prof_toml_path)

        # 4. 确定 active track（环境变量 INVAR_TRACK > 显式参数 > profile.toml 的 [track].name > profile 语义推断 > 默认 PRODUCTION）
        if self.track is None:
            env_track = os.getenv("INVAR_TRACK")
            if env_track:
                self.track = _resolve_track_from_name(env_track, RunTrack.PRODUCTION)
            else:
                track_info = self.profile_config.get("track", {})
                track_name = track_info.get("name")
                if not track_name:
                    track_name = self.profile
                self.track = _resolve_track_from_name(track_name, RunTrack.PRODUCTION)

        # 5. 既有请求头与鉴权处理
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
