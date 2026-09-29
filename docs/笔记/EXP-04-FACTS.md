@'
# EXP-04：知识来源血统 (Knowledge Provenance) 物理验证报告

> **文档性质**：工程事实审计（FACTS AUDIT）  
> **归档位置**：`docs/笔记/EXP-04-FACTS.md`  
> **审计基准**：基于 `tmp/check_exp04_knowledge_provenance.py` 物理实测执行输出 (2026-09-29)  
> **对齐标准**：`SnailSploit/claude-red` (CONTRIBUTING 溯源规范) 与 `Tencent/AI-Infra-Guard` (v4.6.3)

---

## 1. 核心实证现象与审计事实

在 `tmp/check_exp04_knowledge_provenance.py` 的物理执行中，确认了以下关键事实：

### 1.1 现有系统 GAP-04 现状定性
* **[FACT]** `SourceRef` 仅包含 `commit`, `worktree_dirty`, `raw_input_hash`，属于工作树代码版本控制，无法描述安全研究方法论来源；
* **[FACT]** `FindingProvenance` 仅包含 `run_id`, `created_at`, `source_hash`，属于漏洞执行周期血统，无法追踪安全检测规则源头；
* **[CONCLUSION]** 现有 Invar 契约在“外部安全知识血统”层面状态定性为 **`INVAR-MISSING`**。

### 1.2 8 维知识血统契约 (KnowledgeProvenance) 规范
为彻底杜绝“版本漂移”与“神秘不可考规则”，任何被 Invar 吸收的外部机制必须携带以下 8 维不可变元数据：
1. `source_project`: 来源开源项目名称
2. `source_repository`: 来源项目官方仓库 URL
3. `source_file`: 来源具体文件相对路径
4. `source_revision`: 来源精确版本 Tag 或 Commit 哈希
5. `source_section`: 来源具体章节或段落名
6. `source_mechanism`: 提炼的原子机制名称
7. `local_adaptation`: Invar 本地适配实现模块与方法
8. `validation_status`: 验证状态 (`EXPERIMENTAL`, `VERIFIED`, `REJECTED`)

### 1.3 实操吸收建档凭证
* **凭证 [1] (Claude-Red IDOR)**：
  - 源仓库: `https://github.com/SnailSploit/Claude-Red` (`v0.3.0`)
  - 源文件: `Skills/web/offensive-idor/SKILL.md`
  - 提炼机制: `Object-Reference Extraction and Entity Ownership Matching`
  - 本地适配: `harness/idor_compare.py: IdorCompareOperator._extract_identifiers()`
  - 状态: `VERIFIED` (已通过 6 项契约测试 100% 验证)
* **凭证 [2] (腾讯 A.I.G 金丝雀与单变量)**：
  - 源仓库: `https://github.com/Tencent/AI-Infra-Guard` (`v4.6.3`)
  - 源文件: `agent-scan/skills/authorization-bypass-detection/SKILL.md`
  - 提炼机制: `Evidence-backed Canary Proof and Single-variable Mutation`
  - 本地适配: `harness/idor_compare.py` & `test_authorization_baseline_contract.py`
  - 状态: `VERIFIED` (已通过 EXP-02/03 实操核准)

### 1.4 准入知识门禁 (Approved Knowledge Gate) 拦截效力
* **[FACT]** 携带完整来源且状态为 `VERIFIED` 的凭证顺利准入；
* **[FACT]** 任何缺少 `source_repository`、`source_file`、`source_revision` 或处于未经实证状态的神秘规则，被门禁坚决抛出 `ValueError` / `PermissionError` 拦截。

---

## 2. 最终四阶段实验总决算表 (Phase D 闭环)

| 实验编号 | 验证目标 | 核心结论 | 产出物与代码状态 |
|---|---|---|---|
| **EXP-01** | 对象引用识别机制 | 确证 GAP-01 存在；**严守 Rust 契约定力，不修改 `ResearchTask`** | `docs/笔记/EXP-01-FACTS.md` |
| **EXP-02** | 授权关系基线验证 | 抓出 0.99 相似度致命误报与包装漏报；**TDD 重构 `IdorCompareOperator`** | `python/packages/core/src/harness/idor_compare.py`<br>`python/tests/test_authorization_baseline_contract.py` (207 passed) |
| **EXP-03** | 单变量差分因果归因 | 证实 80.3% 算子达标；复合隧道算子定性为合法原子变异族 | `docs/笔记/EXP-02-EXP-03-FACTS.md` |
| **EXP-04** | 外部知识来源血统 | 证实 GAP-04 缺失；**落地 8 维血统模型与准入知识门禁** | `docs/笔记/EXP-04-FACTS.md` |
'@ | Set-Content -Path "docs/笔记/EXP-04-FACTS.md" -Encoding UTF8