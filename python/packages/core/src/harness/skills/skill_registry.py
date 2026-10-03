# -*- coding: utf-8 -*-
"""
Invar 技能注册与解析加载中枢 (Canonical Skill Registry & Parser)
全面支持 Pi Agent Skills 规范: 自动扫描 SKILL.md 及 .agents/skills/ 目录。
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from harness.skills.skill_contracts import SkillDefinition, SkillMetadata, SkillSurface

class SkillParseError(ValueError):
    """当 Skill Markdown 文件不满足规范或缺失必须字段时抛出"""

class SkillRegistry:
    """
    技能剧本内存注册表与动态发现中枢
    """

    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {}

    def register(self, skill: SkillDefinition) -> None:
        self._skills[skill.skill_id] = skill

    def get(self, skill_id: str) -> Optional[SkillDefinition]:
        return self._skills.get(skill_id)

    def list_all(self) -> List[SkillDefinition]:
        return list(self._skills.values())

    def match_skills(self, signals: Set[str]) -> List[SkillDefinition]:
        """依据系统观测信号，动态匹配可激活的技能清单"""
        return [s for s in self._skills.values() if s.matches_triggers(signals)]

    @classmethod
    def load_from_text(cls, text: str, source_path: Optional[str] = None) -> SkillDefinition:
        """
        从单份 Markdown 文本中提取 Agent Skills 规范 Frontmatter 与 SOP 正文
        采用纯标准库鲁棒分层行解析，支持 metadata 嵌套块
        """
        clean_text = text.strip()
        if not clean_text.startswith("---"):
            raise SkillParseError("Skill file must begin with YAML frontmatter delimiters '---'")

        parts = clean_text.split("---", 2)
        if len(parts) < 3:
            raise SkillParseError("Skill file must contain a closed frontmatter delimited by '---'")

        frontmatter_raw = parts[1].strip()
        sop_markdown = parts[2].strip()

        meta_dict: Dict[str, Any] = {}
        nested_metadata: Dict[str, Any] = {}
        current_section = None

        def _clean_val(val_str: str) -> Any:
            v = val_str.strip().strip("'\"")
            if v.startswith("[") and v.endswith("]"):
                return [i.strip().strip("'\"") for i in v[1:-1].split(",") if i.strip()]
            if v.lower() == "true":
                return True
            if v.lower() == "false":
                return False
            return v

        for raw_line in frontmatter_raw.splitlines():
            line = raw_line.rstrip()
            if not line or line.strip().startswith("#"):
                continue

            # 检测缩进子段 (如 metadata: 下的嵌套行)
            if line.startswith("  ") or line.startswith("\t"):
                if current_section == "metadata" and ":" in line:
                    sub_k, sub_v = line.strip().split(":", 1)
                    nested_metadata[sub_k.strip()] = _clean_val(sub_v)
                continue

            # 顶级字段解析
            if ":" in line:
                k, v = line.split(":", 1)
                k_clean = k.strip()
                v_clean = v.strip()
                if not v_clean and k_clean == "metadata":
                    current_section = "metadata"
                else:
                    current_section = None
                    meta_dict[k_clean] = _clean_val(v_clean)

        # 官方必须字段校验 (name, description)
        if "name" not in meta_dict:
            # 兼容处理: 若为旧 id 字段，自动映射为 name
            if "id" in meta_dict:
                meta_dict["name"] = meta_dict["id"].replace(".", "-")
            else:
                raise SkillParseError("Missing required frontmatter key: 'name'")

        if "description" not in meta_dict:
            raise SkillParseError("Missing required frontmatter key: 'description'")

        # 解析 Invar 扩展字段 (优先取 nested_metadata，次级取顶层平铺)
        surface_str = str(nested_metadata.get("surface") or meta_dict.get("surface") or "api").lower()
        try:
            surface_enum = SkillSurface(surface_str)
        except ValueError:
            raise SkillParseError(f"Invalid SkillSurface: '{surface_str}'")

        attack_class = str(nested_metadata.get("attack_class") or meta_dict.get("attack_class") or "vulnerability")

        def _get_list(key: str) -> List[str]:
            val = nested_metadata.get(key) or meta_dict.get(key) or []
            return val if isinstance(val, list) else [str(val)]

        allowed_tools = meta_dict.get("allowed-tools") or meta_dict.get("allowed_tools") or []
        if isinstance(allowed_tools, str):
            allowed_tools = [allowed_tools]

        metadata = SkillMetadata(
            name=str(meta_dict["name"]),
            description=str(meta_dict["description"]),
            surface=surface_enum,
            attack_class=attack_class,
            allowed_tools=allowed_tools,
            license=meta_dict.get("license"),
            compatibility=meta_dict.get("compatibility"),
            disable_model_invocation=bool(meta_dict.get("disable-model-invocation", False)),
            triggers=_get_list("triggers"),
            required_context=_get_list("required_context"),
            success_conditions=_get_list("success_conditions"),
            stop_conditions=_get_list("stop_conditions"),
            evidence_requirements=_get_list("evidence_requirements"),
            extra_metadata=nested_metadata
        )

        return SkillDefinition(
            metadata=metadata,
            sop_markdown=sop_markdown,
            source_path=source_path
        )

    @classmethod
    def load_from_directory(cls, dir_path: Path | str) -> "SkillRegistry":
        """扫描目录中所有符合 Pi 规范的 SKILL.md 文件"""
        p = Path(dir_path)
        registry = cls()
        if not p.exists():
            return registry

        for skill_file in p.rglob("SKILL.md"):
            try:
                content = skill_file.read_text(encoding="utf-8")
                skill = cls.load_from_text(content, source_path=str(skill_file.resolve()))
                registry.register(skill)
            except Exception:
                continue

        return registry
