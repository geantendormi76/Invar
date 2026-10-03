# -*- coding: utf-8 -*-
"""
Invar 权威技能剧本契约 (Canonical Skill Contracts)
100% 契合 Pi Agent 与 Agent Skills 国际标准规范 (https://agentskills.io/specification)。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set
import re

class SkillSurface(str, Enum):
    API = "api"
    WEB = "web"
    AUTH = "auth"
    NETWORK = "network"

@dataclass(frozen=True)
class SkillMetadata:
    """
    Agent Skills Specification 规范标准元数据
    """
    name: str                                  # 官方顶级字段: <= 64 字符，小写/数字/连字符
    description: str                           # 官方顶级字段: <= 1024 字符路由描述
    surface: SkillSurface                      # Invar 攻击面分类
    attack_class: str                          # Invar 攻击类型
    allowed_tools: List[str] = field(default_factory=list)  # 官方顶级字段: 预授权工具清单
    license: Optional[str] = None              # 官方顶级字段: 许可证声明
    compatibility: Optional[str] = None        # 官方顶级字段: 环境依赖要求
    disable_model_invocation: bool = False     # 官方顶级字段: 禁用模型自动选择

    # Invar 专属语义安全元数据 (嵌套在 metadata 字典中)
    triggers: List[str] = field(default_factory=list)
    required_context: List[str] = field(default_factory=list)
    success_conditions: List[str] = field(default_factory=list)
    stop_conditions: List[str] = field(default_factory=list)
    evidence_requirements: List[str] = field(default_factory=list)
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # 断言官方命名字段合法性
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", self.name):
            raise ValueError(f"Skill name '{self.name}' violates Agent Skills Specification naming rules")
        if len(self.name) > 64:
            raise ValueError("Skill name exceeds 64 characters limit")
        if len(self.description) > 1024:
            raise ValueError("Skill description exceeds 1024 characters limit")

@dataclass(frozen=True)
class SkillDefinition:
    """
    完整的技能剧本实体 (结构化元数据 + Markdown SOP 操作规范)
    """
    metadata: SkillMetadata
    sop_markdown: str
    source_path: Optional[str] = None

    @property
    def skill_id(self) -> str:
        return self.metadata.name

    def matches_triggers(self, observed_signals: Set[str]) -> bool:
        """断言当前观测到的特征信号是否命中该技能的触发器"""
        if not self.metadata.triggers:
            return False
        return any(t.lower() in {s.lower() for s in observed_signals} for t in self.metadata.triggers)
