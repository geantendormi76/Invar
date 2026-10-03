# -*- coding: utf-8 -*-
"""
Phase 9.8 第二单步: 对齐 Pi Agent Skills 规范的契约测试
验证官方字段 (name, description, allowed-tools, metadata)、命名规范断言与目录发现
"""

import unittest
from pathlib import Path
from harness.skills.skill_contracts import SkillSurface, SkillDefinition
from harness.skills.skill_registry import SkillRegistry, SkillParseError

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = REPO_ROOT / ".agents" / "skills" / "api-authorization-bola" / "SKILL.md"

class PiAgentSkillContractsTests(unittest.TestCase):

    def test_01_load_canonical_pi_skill_file(self) -> None:
        """【契约 1】成功解析规范的 .agents/skills/api-authorization-bola/SKILL.md 实体"""
        content = SKILL_PATH.read_text(encoding="utf-8")
        skill = SkillRegistry.load_from_text(content, source_path=str(SKILL_PATH))
        meta = skill.metadata

        # 官方顶级字段断言
        self.assertEqual(meta.name, "api-authorization-bola")
        self.assertIn("BOLA / IDOR cross-tenant", meta.description)
        self.assertEqual(meta.allowed_tools, ["curl", "ffuf"])

        # Invar 扩展元数据断言
        self.assertEqual(meta.surface, SkillSurface.API)
        self.assertEqual(meta.attack_class, "authorization")
        self.assertIn("object_identifier", meta.triggers)
        self.assertIn("attacker_principal", meta.required_context)

        # 正文内容断言
        self.assertIn("# BOLA / IDOR 对象级越权安全研究剧本", skill.sop_markdown)
        self.assertIn("多主体差分攻击 (Differential Attack)", skill.sop_markdown)

    def test_02_skill_naming_validation(self) -> None:
        """【契约 2】命名必须严格遵循小写/数字/连字符，违背规范显式拦截"""
        invalid_name_md = """---
name: INVALID_UPPERCASE_NAME
description: "Testing invalid naming"
---
# Content
"""
        with self.assertRaises(ValueError) as ctx:
            SkillRegistry.load_from_text(invalid_name_md)
        self.assertIn("violates Agent Skills Specification", str(ctx.exception))

    def test_03_directory_discovery_loads_skill_md(self) -> None:
        """【契约 3】load_from_directory 原生扫描发现目录中的 SKILL.md"""
        skills_root = REPO_ROOT / ".agents" / "skills"
        registry = SkillRegistry.load_from_directory(skills_root)
        
        skill = registry.get("api-authorization-bola")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.skill_id, "api-authorization-bola")

        # 触发器匹配
        matched = registry.match_skills({"tenant_context"})
        self.assertEqual(len(matched), 1)
