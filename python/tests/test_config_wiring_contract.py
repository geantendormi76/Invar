import os
import unittest
from pathlib import Path
from harness.config import InvarConfig
from harness.run_models import RunTrack


class ConfigWiringContractTests(unittest.TestCase):
    def test_default_config_loads_project_and_production_profile(self):
        """契约 1: 默认情况下自动读取 project.toml 与 production.toml，装配 Production 轨道"""
        cfg = InvarConfig()
        self.assertEqual(cfg.profile, "production")
        self.assertEqual(cfg.track, RunTrack.PRODUCTION)
        self.assertIn("project", cfg.project_config)
        self.assertEqual(cfg.project_config["project"].get("name"), "Invar")
        self.assertIn("runtime", cfg.profile_config)

    def test_invar_profile_env_overrides_default(self):
        """契约 2: 环境变量 INVAR_PROFILE 能够覆盖 project.toml 中的配置"""
        old_val = os.environ.get("INVAR_PROFILE")
        try:
            os.environ["INVAR_PROFILE"] = "research"
            cfg = InvarConfig()
            self.assertEqual(cfg.profile, "research")
            self.assertEqual(cfg.track, RunTrack.RESEARCH)
            self.assertEqual(cfg.profile_config.get("runtime", {}).get("backend"), "research")
        finally:
            if old_val is not None:
                os.environ["INVAR_PROFILE"] = old_val
            else:
                os.environ.pop("INVAR_PROFILE", None)

    def test_invar_track_env_overrides_profile_track(self):
        """契约 3: 环境变量 INVAR_TRACK 享有最高轨道优先级"""
        old_val = os.environ.get("INVAR_TRACK")
        try:
            os.environ["INVAR_TRACK"] = "BENCHMARK"
            cfg = InvarConfig()
            self.assertEqual(cfg.track, RunTrack.BENCHMARK)
        finally:
            if old_val is not None:
                os.environ["INVAR_TRACK"] = old_val
            else:
                os.environ.pop("INVAR_TRACK", None)

    def test_fallback_when_files_missing(self):
        """契约 4: 缺少配置文件时优雅降级为默认安全配置，绝不抛异常"""
        fake_root = Path("C:/non_existent_invar_root_12345")
        cfg = InvarConfig(workspace_root=fake_root)
        self.assertEqual(cfg.profile, "production")
        self.assertEqual(cfg.track, RunTrack.PRODUCTION)
        self.assertEqual(cfg.project_config, {})
        self.assertEqual(cfg.profile_config, {})

    def test_backward_compatibility_preserved(self):
        """契约 5: 既有环境变量与核心属性完全保持兼容"""
        cfg = InvarConfig()
        self.assertTrue(hasattr(cfg, "target_api_base"))
        self.assertTrue(hasattr(cfg, "request_timeout"))
        self.assertTrue(hasattr(cfg, "max_mutation_rounds"))
        self.assertIn("User-Agent", cfg.custom_headers)
