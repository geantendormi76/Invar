# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot / Recovery Contract  
> **Project:** Invar  
> **Snapshot Date:** 2026-09-29  
> **Canonical Repository Root:** `C:\dev\Invar`  
> **Canonical Handoff Path:** `C:\dev\Invar\HANDOFF.md`  
> **Current Engineering Baseline:** Python 207 passed (0.41s), Rust 15 passed, Total 222 passed / 0 failed.

---

## 0. Handoff Metadata

| Item | Value | Level | Evidence / Note |
|---|---|---|---|
| Project | Invar | [FACT] | Web API 自动化安全实证研究与漏洞研究 Harness (System-2 深度动态实证引擎) |
| Active Target | `ikuai8.com` | [FACT] | `data/targets/ikuai8.com/scope.txt` |
| Current Phase | Phase R2 — Autonomous Research Mission Execution | [DECISION] | 进入首个端点领域技能标准与实操验证阶段 |
| Phase D Status | Minimal Validation Experiments (EXP-01 ~ EXP-04) | [FACT, verified] | 全部 100% 物理验证闭环，报告见 `docs/笔记/EXP-01/02/03/04-FACTS.md` |
| Python Test Baseline | 207 passed in 0.41s | [FACT, verified] | `uv run --project python pytest -q` |
| Rust Test Baseline | 15 passed | [FACT, verified] | `cargo test --workspace` |
| Combined Baseline | 222 / 222 passed | [FACT] | 全量核心契约与测试绿灯 |
| Agent Runtime | `@earendil-works/pi-coding-agent` (Node.js) | [FACT] | 唯一智能体马具，运行器 `tools/invar_agent_runner.mjs`，严禁自造 Python Agent |
| Cognitive Model | `Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE` | [FACT] | 本地 `llama-server` (port: 8080)，极简原生工具 (`read`, `write`, `powershell`) |
| Codebase Hygiene | Phase 1 Dead Code Purge Completed | [FACT, verified] | 物理切除 4 个玩具轮子与 1 个自闭测试，测试基准稳步提升至 207 passed |
| Critical Bug Resolved | IDOR Naive String Similarity False Positive Eliminated | [FACT, verified] | `idor_compare.py` 彻底重构为对象标识提取与属主对账，消除 0.99 相似度假象 |

---

## 1. Project Identity

### 1.1 System Role
[FACT]
Invar 是安全实证体系中的 **System-2 深度动态实证与事实裁决引擎**。
它的边界由两层紧密咬合：
1. **上层认知与控制平面 (Agent Runtime)**：由外部成熟的 **Pi Agent Harness** 全权承载，调度本地 35B 大模型（Ornith-1.5-35B），负责多轮记忆、会话分支压缩、规划思考以及基于极简工具（`read`, `write`, `powershell`）的操作调度；
2. **底层确定性安全核心 (Deterministic Security Core)**：由 Invar Python/Rust 引擎承载，负责真实的物理发包、重试变异自愈、双主体差分比对、安全不变量裁决、独立第三方复核与门禁确权。

### 1.2 Engineering Constitution
[DECISION]
项目严格遵循通用 AI 工程宪法：
* 零臆造、零重复造轮子、零无依据特判；
* 根因优先于表面修补（修复模型，不修补症状）；
* 目录是职责边界，类型是数据边界，接口是模块边界；
* **拿来主义与黄金标准驱动**：深度吸收 `SnailSploit/claude-red` (v0.3.0) 战术规约与 `Tencent/AI-Infra-Guard` (v4.6.3) 蓝军实证哲学；
* 一次只推进一个明确的工程动作（单步工程协作）；
* 一次性探查脚本必须封装于 `tmp/check_xxx.py`，由 PowerShell 单引号块落盘，严禁向用户输出长内联命令行。

---

## 2. Current Mission

[DECISION]
**打造一个由 AI 智能体（Pi Agent + 本地 35B 模型）自主驱动、以真实代码切片与物理发包为依据、具备确定性门禁防护的 Web API 自动化漏洞研究 Harness，并完成针对真实授权靶标首个端点（`POST:/api/v3/delegate/grant`）的全流程实证研究闭环。**

---

## 3. Current Objective

### CURRENT OBJECTIVE
[DECISION]
> **基于已完成的 EXP-01 至 EXP-04 机制验证成果（对象引用模型、授权基线、单变量差分、8 维知识血统），为首个实战靶向端点 `POST:/api/v3/delegate/grant`（假说 `H-AUTH-1`）编写工业级领域技能规范（`skills/authorization_investigation/SKILL.md`），规范化定义触发条件、攻击者画像、信任边界、Invar 沙箱调用命令以及消除软 403 / SPA 200 误报的五步作业程序。**

---

## 4. Next Single Action

### NEXT SINGLE ACTION
> **执行已准备好的探查脚本 `tmp/check_target_delegate_grant.py`，从已装配的任务清单 `artifacts/reports/targeted_research_tasks_78.json` 中提取首选靶标 `POST:/api/v3/delegate/grant` 的物理元数据（真实的提取参数名、AST 代码切片位置、推荐 Profile 与关联假说），确保后续编写的 `SKILL.md` 100% 基于真实代码切片。**

执行命令：
```powershell
uv run --project python python tmp/check_target_delegate_grant.py
```

---

## 5. Current Scope

### 5.1 In Scope
- `tmp/check_target_delegate_grant.py`（靶标端点参数与切片探查）
- `skills/authorization_investigation/SKILL.md`（待新建的标准化研究技能 SOP）
- `docs/笔记/` 下的 4 份 EXP 事实核验报告（`EXP-01-FACTS.md`, `EXP-02-EXP-03-FACTS.md`, `EXP-04-FACTS.md`）
- `python/packages/core/src/harness/idor_compare.py`（已重构的对象标识符对账算子）
- `python/tests/test_authorization_baseline_contract.py`（6 项全绿的契约测试）

### 5.2 Out of Scope
- 禁止推倒重写 Invar 底层确定性沙箱；
- 禁止重新在 Python 中自造 ReAct / Multi-Agent 状态机轮子；
- 禁止修改 Rust `crates/core` 的 `ResearchTask` 结构体契约；
- 禁止编写针对未授权目标的任意扫描脚本；
- 暂不涉及桌面端 UI（Tauri / React）。

---

## 6. Out of Scope

[DECISION]
当前阶段坚决不碰：
* 重新全量扫描整个前端 AST；
* 引入重型关系数据库（PostgreSQL）或图数据库（Neo4j）；
* 引入复杂的分布式工作流（Temporal）；
* 编写任何破坏性的自动化越权写操作发包。

---

## 7. Last Known Good State

### 7.1 Engineering Baseline
[FACT, verified 2026-09-29]
```text
Python regression: 207 passed in 0.41s
Rust regression:   15 passed
Total baseline:    222 passed / 0 failed
Warnings:          0 fatal warnings
```
标准测试命令：
```powershell
uv run --project python pytest -q
cargo test --workspace
```

### 7.2 Native Tools & Inference Baseline
[FACT, verified 2026-09-29]
- 本地 `127.0.0.1:8080` (`llama-server`, `Ornith-1.5-35B`) 原生工具调用正常；
- 全局 Pi Agent Harness (`@earendil-works/pi-coding-agent`) 握手通过；
- `tools/invar_agent_runner.mjs --dry-run` 验证通过；
- `harness/` 目录反向依赖 AST 审计：0 violations（纯净 IoC）；
- EXP-01 至 EXP-04 物理实验全部闭环并通过门禁核验。

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| Phase 1 坏代码切除 | DONE | 物理删除 5 个文件，回归 201 passed | `agent/mutator.py`, `agent/hunter.py`, `agent/wave_orchestrator.py`, `agent/coverage_critic.py`, `tests/test_cognitive_orchestration.py` | 彻底切除手造的多智能体玩具轮子，纯化 Pi Harness 职责 |
| EXP-01 对象引用验证 | DONE | `docs/笔记/EXP-01-FACTS.md` | `harness/triage_dispatcher.py`, `domain_contracts.py` | 确证 GAP-01 存在；守住 Rust 契约定力，不污染 `ResearchTask` |
| EXP-02 授权基线验证 | DONE | TDD 契约红转绿，207 passed 全绿 | `harness/idor_compare.py`, `tests/test_authorization_baseline_contract.py` | 彻底修复 0.99 相似度致命误报与包装漏报，引入对象标识提取与属主对账 |
| EXP-03 单变量差分验证 | DONE | `docs/笔记/EXP-02-EXP-03-FACTS.md` | `harness/transformation_models.py` | 证实 80.3% 算子达标，复合动词/重写隧道归纳为合法原子变异族 |
| EXP-04 知识来源血统 | DONE | `docs/笔记/EXP-04-FACTS.md` | `tmp/check_exp04_knowledge_provenance.py` | 证实 GAP-04 缺失，建立 8 维血统模型与 Approved Knowledge Gate，拦截神秘伪规则 |
| 威胁模型一级契约 | DONE | `tests/test_threat_model_contract.py` (4 passed) | `harness/domain_contracts.py` | 确立 `ThreatModel` 与不可变 `AttackerProfile` |
| 跨语言执行器与流水线 | DONE | `crates/core/tests/pipeline_e2e_test.rs` | `crates/core/src/orchestrator.rs`, `harness/research_adapter.py` | Rust Orchestrator 与 Python Worker 双向转译 |

---

## 9. Changed Files

### 9.1 Added
- `python/tests/test_authorization_baseline_contract.py`: BOLA / IDOR 授权差分基线 6 项契约测试（全绿）。
- `docs/笔记/EXP-01-FACTS.md`: EXP-01 对象引用与生命周期血统事实核验报告。
- `docs/笔记/EXP-02-EXP-03-FACTS.md`: EXP-02 授权基线误报根除与 EXP-03 单变量差分审计报告。
- `docs/笔记/EXP-04-FACTS.md`: EXP-04 8 维知识血统契约与准入知识门禁核验报告。
- `tmp/check_codebase_hygiene.py`: 全库 AST 依赖拓扑与代码卫生体检工具。
- `tmp/apply_phase1_cleanup.py`: Phase 1 坏代码物理切除脚本。
- `tmp/check_exp02_exp03_baseline_diff.py`: EXP-02/03 物理探查脚本。
- `tmp/check_exp04_knowledge_provenance.py`: EXP-04 知识血统验证脚本。
- `tmp/check_target_delegate_grant.py`: 靶标端点物理切片探查脚本（待执行）。

### 9.2 Modified
- `python/packages/core/src/harness/idor_compare.py`:
  - 彻底摒弃粗暴的单纯 `difflib.SequenceMatcher` 字符比对；
  - 引入 `_extract_identifiers()` 递归提取结构化数据中承载对象身份的键值对；
  - 增加属主实体对账：受害者对象泄露判定为 `vulnerable`，持有自身独立对象判定为 `confirmed`（安全），非结构化数据平滑降级。
- `python/packages/core/src/agent/__init__.py`:
  - 瘦身并彻底移除 `PayloadMutator`, `Hunter`, `HunterResult`, `CoverageCritic`, `HunterWaveOrchestrator` 的残留导出。

### 9.3 Deleted
- `python/packages/core/src/agent/mutator.py`（0 测试、0 引用的纯死代码）
- `python/packages/core/src/agent/hunter.py`（自研玩具智能体）
- `python/packages/core/src/agent/coverage_critic.py`（自研玩具智能体）
- `python/packages/core/src/agent/wave_orchestrator.py`（自研玩具智能体）
- `python/tests/test_cognitive_orchestration.py`（自闭孤立单元测试）

---

## 10. Current Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 认知大脑: 本地 35B 大模型 (Ornith-1.5-35B-A3B-...-MTPv2)             │
│    - 负责策略思考、反思推演、阅读切片代码                                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 本地 HTTP (llama-server:8080)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. 现成 Agent 马具 (Pi Agent Harness): @earendil-works/pi-coding-agent │
│    - 唯一智能体运行时！会话分支树、记忆压缩、任务排期                   │
│    - 运行入口: tools/invar_agent_runner.mjs                            │
│    - 极简武器库: read (读代码), powershell (跑命令), write (写笔记)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 遵从战术手册规范 (SKILL.md)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. 领域战术层: Invar Research Skills (Markdown SOP - Phase E 核心)     │
│    - skills/authorization_investigation/SKILL.md (待建)                │
│    - 吸纳 Claude-Red 7 段式结构 + A.I.G 单变量变异与金丝雀物证原则       │
│    - 注入 EXP-04 8 维知识血统元数据，彻底杜绝神秘伪规则                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ powershell 执行确定性沙箱命令
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. Invar 确定性安全执行与事实裁决底座 (Deterministic Security Core)    │
│    - 范围契约: data/targets/ikuai8.com/scope.txt                       │
│    - 威胁模型: ThreatModel + AttackerProfile (不可变一级契约)          │
│    - 调度转译: TriageTask -> ResearchTask (Rust) -> ResearchCase       │
│    - 沙箱执行: AdaptiveSandboxExecutor (IoC 解耦架构)                  │
│    - 授权比对: IdorCompareOperator (对象标识提取 + 属主实体对账)       │
│    - 终审门禁: IndependentVerifier -> PromotionGate -> OpenVEX / SARIF │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Architecture Decisions

### AD-01 — 坚决使用 Pi Agent 作为唯一 Agent Harness
[DECISION]
Pi Agent (`@earendil-works/pi-coding-agent`) 拥有工业级的会话树和极简工具原语。Invar 彻底放弃在 Python 中自造多智能体运行时的重复建设，已物理清理 `hunter.py`、`wave_orchestrator.py`。

### AD-02 — 极简工具哲学（Unix Philosophy）
[DECISION]
坚决不给 Python 沙箱写复杂的专属 JSON Tool Schema。仅通过 Pi 原生的 `read`（读切片/代码）、`write`（写笔记）和 `powershell`（调用底层 Invar 命令）驱动，对本地量化大模型最稳定、最不易产生幻觉。

### AD-03 — 技能即文档（Skills as Markdown SOP）
[DECISION]
战术层不写重型 Python 代码，严格采用 Claude-Red 的 7 段式 Markdown 规范（`Scope`, `Trigger`, `Preconditions`, `Procedure`, `Expected Evidence`, `Failure Modes`, `References`）。

### AD-04 — 授权判定必须基于对象引用提取与属主对账
[DECISION]
彻底摒弃 `difflib.SequenceMatcher` 纯文本相似度算法。IDOR 判定的金科玉律是：**受害者特有对象标识符是否泄漏给攻击者，以及攻击者是否持有自身合法独立对象**。

### AD-05 — 保持 Rust `ResearchTask` 极简强类型契约定力
[DECISION]
绝不将对象引用树或复杂安全语义塞进 Rust `crates/core` 的 `ResearchTask` 结构体。`ResearchTask` 仅仅是轻量调度凭证；对象引用语义保留在上层 Context 与 `SKILL.md` 中。

### AD-06 — 吸收外部机制必须经过 8 维知识血统审查（EXP-04）
[DECISION]
任何吸收进 Invar 的外部研究方法必须附带 8 维元数据（`source_project`, `source_repository`, `source_file`, `source_revision`, `source_section`, `source_mechanism`, `local_adaptation`, `validation_status`），受 `ApprovedKnowledgeGate` 强制检验。

---

## 12. Data / API / Type Contracts

### 12.1 `KnowledgeProvenance` (EXP-04 知识血统契约)
[FACT]
```python
@dataclass(frozen=True)
class KnowledgeProvenance:
    source_project: str
    source_repository: str
    source_file: str
    source_revision: str
    source_section: str
    source_mechanism: str
    local_adaptation: str
    validation_status: str = "EXPERIMENTAL"  # EXPERIMENTAL, VERIFIED, REJECTED
```

### 12.2 `IdorCompareOperator` (EXP-02 授权基线比对契约)
[FACT]
位于 `python/packages/core/src/harness/idor_compare.py`：
```python
class IdorCompareOperator:
    SIMILARITY_THRESHOLD = 0.80

    @classmethod
    def _extract_identifiers(cls, data: Any, prefix: str = "") -> Dict[str, Any]: ...

    @classmethod
    def compare(
        cls,
        victim_response_text: str,
        attacker_response_text: str,
        attacker_status_code: int,
    ) -> InvariantEvaluation: ...
```
- 输入：受害者基线响应文本、攻击者响应文本、攻击者响应状态码。
- 输出：`InvariantEvaluation(invariant_type="idor_boundary", status="confirmed"|"vulnerable"|"inconclusive", rationale=...)`。
- 逻辑：自动递归提取对象 ID 键值对，若泄漏受害者 ID 判 `vulnerable`；若攻击者持有自身独立 ID 判 `confirmed`；非结构化数据回退至文本相似度。

### 12.3 `ThreatModel` & `AttackerProfile`
[FACT]
位于 `harness/domain_contracts.py`：
```python
@dataclass(frozen=True)
class AttackerProfile:
    role: str
    token_ref: Optional[str] = None
    description: str = ""
    capabilities: List[str] = field(default_factory=list)

@dataclass
class ThreatModel:
    model_id: str
    title: str
    attacker: AttackerProfile
    assets: List[str]
    trust_boundaries: List[str]
    entrypoints: List[str]
    expected_controls: List[str]
    invariants: List[SecurityInvariant]
    metadata: Dict[str, Any]
```

---

## 13. Algorithms / Workflow

### 13.1 钉死的生产代码 5 步完整生命周期链路
[FACT, verified 2026-09-29 via 92-file AST audit]
```text
 ┌──────────────┐
 │  TriageTask  │ (harness/triage_dispatcher.py:190)
 └──────┬───────┘
        │ 经由 ResearchTaskAdapter 转译为 EndpointIR
        ▼
 ┌──────────────┐
 │ ResearchCase │ 谁创建？➔ AdaptiveSandboxExecutor._create_research_case() (sandbox_executor.py:129)
 └──────┬───────┘
        │ 动态发包与反馈变异自愈循环中
        ▼
 ┌──────────────┐
 │ ProbeAttempt │ 谁创建？➔ ResearchCase.record_attempt() (domain_contracts.py:864)
 └──────┬───────┘
        │ 探针收敛后映射微观物理尝试为可追溯凭证
        ▼
 ┌──────────────┐
 │EvidenceRecord│ 谁创建？➔ ProbeAttemptEvidenceMapper.to_evidence_records() (research_evidence.py:41)
 └──────┬───────┘
        │ 安全不变量裁决判定 vulnerable 击穿底线时
        ▼
 ┌──────────────┐
 │  Candidate   │ 谁创建？➔ run_targeted_audit.py (scripts/run_targeted_audit.py:417)
 └──────┬───────┘
        │ 候选实体通过 FindingRecord.from_candidate() 升级后
        ▼
 ┌──────────────┐
 │ Verification │ 哪里接入？➔ IndependentVerifier.verify() ➔ PromotionGate (verification_gate.py:47, 137)
 └──────────────┘
```

---

## 14. Verified Tests

```powershell
uv run --project python pytest -q
```
**结果：207 passed in 0.41s**
关键保护测试集：
- `test_authorization_baseline_contract.py` (6 passed, 保护对象属主实体对账与消除同构误报)
- `test_threat_model_contract.py` (4 passed, 保护威胁模型与假说派生)
- `test_sandbox_operators_all.py` (7 passed, 保护破坏性二次确认与 IDOR 联动)
- `test_sandbox_403_research_loop.py` (3 passed, 保护防软 403 / SPA 首页 HTML 假放行)
- `test_research_evidence_all.py` (2 passed, 保护证据链映射)
- `test_verification_and_promotion_gate.py` (5 passed, 保护独立复核与 OpenVEX 门禁)

---

## 15. Failure / Pitfall Registry

### FP-15 — 单纯依赖 difflib.SequenceMatcher 计算 JSON 相似度引发双向致盲
**Problem**: 在 EXP-02 实测中，合法访问 Bob 自身数据被误判为 `vulnerable`（相似度 0.83）；访问仅 ID 不同的 DOC-90002 被误判为 `vulnerable`（相似度 0.99）；而外层包裹 `{"code":200,"data":...}` 的真实泄露反被错判为 `confirmed`（相似度暴跌）。  
**Symptom**: 同构合法 JSON 全量误报，包装结构泄露全量漏报。  
**Root Cause**: 字符级比对缺乏结构与语义感知，违背了“越权是受害者对象标识符外泄与属主越界”的本质规律。  
**Wrong Approach**: 简单将相似度阈值从 0.80 改为 0.95（打补丁式修补）。  
**Correct Fix**: 引入 `_extract_identifiers()` 提取身份键值对，比对攻击者是否非法获得了受害者对象 ID，或是否合法持有自身 ID。  
**Regression Test**: `python/tests/test_authorization_baseline_contract.py`（6 项用例全绿）。  
**Future Prevention**: 涉及结构化数据的安全性比较，严禁使用非语义的纯字符距离算法。

---

## 16. Do Not Repeat

1. **绝对不要自造 Python Agent 状态机或多智能体框架**：Pi Agent Harness (`tools/invar_agent_runner.mjs`) 是唯一的智能体马具，已被物理清理的代码严禁复活。
2. **绝对不要修改 Rust `ResearchTask` 结构体来承载战术语义**：`ResearchTask` 保持纯洁的跨语言物理调度契约，对象引用语义放在 Upper Context 和 `SKILL.md` 中。
3. **绝对不要跳过验证步骤直接写代码**：必须严格遵循 EXP-01 至 EXP-04 的物理实验验证闭环，证据不足绝不推进。
4. **绝对不要照搬 A.I.G 的对话诱导越权或 30+ payload 硬编码**：Invar 面对的是 Web API HTTP 契约，受严格的沙箱熔断预算约束。
5. **绝对不要相信没有对象标识符核验的纯文本相似度**。

---

## 17. Invariants

- **权威裁决唯一性**：只有 Invar 的确定性沙箱与门禁（`PromotionGate`）有权确权漏洞，大模型绝无自封漏洞的权力。
- **授权边界绝对性**：动态测试严格限定在 `data/targets/ikuai8.com/scope.txt`。
- **知识血统不可变性**：吸收的外部机制必须具备 8 维血统事实，拒绝无来源的 AI 幻觉规则。
- **单步工程协作法则**：一次只推进一个明确的工程动作，验证闭环后再继续。

---

## 18. Open Issues

- **OI-11 (首个靶标端点研究 SOP 待固化)**：`[IN_PROGRESS]`
  - 靶标端点 `POST:/api/v3/delegate/grant`（假说 `H-AUTH-1`）即将通过 `skills/authorization_investigation/SKILL.md` 落地。
- **OI-12 (EXP-03 差分变量因果标签待结构化)**：`[OPEN]`
  - `ProbeAttempt` 的 `mutation_reason` 目前仍为纯文本，后续可择机为它扩充可选的 `transformation_family` 强类型标签。

---

## 19. Environment / Toolchain

| Component | Known State |
|---|---|
| OS | Windows 11 (PowerShell) |
| Python | 3.12 (`uv` managed, `python/pyproject.toml`) |
| Node.js | v24.18.0 |
| Global Pi Package | `@earendil-works/pi-coding-agent` |
| Local Model Server | `llama-server.exe` (port: 8080) |
| Local Model Weights | `Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE` |
| Runner Script | `tools/invar_agent_runner.mjs` |

---

## 20. Roadmap

- [x] **Phase A**: 外部材料考古 (Claude-Red + A.I.G 源码级解剖)
- [x] **Phase B**: 17 个机制归一化与三方矩阵建立
- [x] **Phase C**: 识别 4 大真缺口与 3 大致命冲突
- [x] **Phase D**: 最小机制验证实验 (EXP-01 至 EXP-04)
  - [x] EXP-01: 对象引用语义验证 (`docs/笔记/EXP-01-FACTS.md`)
  - [x] 代码卫生切除 (清除玩具轮子，201 passed)
  - [x] EXP-02: 授权关系基线重构 (`docs/笔记/EXP-02-EXP-03-FACTS.md`, 207 passed)
  - [x] EXP-03: 单变量差分归因审计
  - [x] EXP-04: 知识来源血统物理验证 (`docs/笔记/EXP-04-FACTS.md`)
- [ ] **Phase E**: 准入批准与正式生成技能规范
  - [ ] **E-1**: 探查首选靶标 `POST:/api/v3/delegate/grant` 的一手物理切片数据 (当前唯一下一步)
  - [ ] **E-2**: 编写 `skills/authorization_investigation/SKILL.md` (注入 Claude-Red 7 段式与 EXP 成果)
  - [ ] **E-3**: 点火驱动 Pi Agent 开展针对真实端点的实证科研闭环

---

## 21. Recovery Protocol

新 AI 接手后恢复顺序：
1. 读取 `HANDOFF.md`；
2. 运行 `uv run --project python pytest -q` 确认 207 passed 基准；
3. 检查 `docs/笔记/` 下的 EXP 事实核验报告；
4. 确认当前唯一下一步为 **E-1**；
5. 执行 `NEXT SINGLE ACTION`（运行 `tmp/check_target_delegate_grant.py`）。

---

## 22. AI Collaboration Protocol

- 默认中文；专业术语第一次出现时标注英文。
- 遵循单步工程协作，每轮只要求用户执行一个物理动作。
- 代码修改使用 PowerShell 单引号块落盘至指定路径。
- 回复格式遵循：目标 ➔ 黄金标准出处溯源 ➔ 原理与解说 ➔ 执行内容 ➔ 反馈要求。

---

## 23. Security / Sensitive Data Boundary

- 严禁把真实 Cookie、Authorization Token、私钥或凭证写入 HANDOFF 或代码库。
- 动态测试必须严格限定在 `data/targets/ikuai8.com/scope.txt`。

---

## 24. Reproducibility Status

**FULLY REPRODUCIBLE (100%)**  
- 核心代码、沙箱、契约与测试（207 passed）完全通过；
- 本机 Pi 运行时、`llama-server` 与本地 35B 模型链路实测通过；
- EXP-01 至 EXP-04 物理验证脚本均位于 `tmp/` 可随时复现。

---

## 25. Handoff Self-Check

- [x] 新 AI 是否知道当前到底在做什么？（知道：Phase D 实验全量闭环，正准备探查靶标切片以编写 `skills/authorization_investigation/SKILL.md`）
- [x] 新 AI 是否知道最后一次成功状态？（知道：207 passed 全绿，EXP-04 验证通过）
- [x] 新 AI 是否知道最后修改了哪些文件？（知道：切除 5 个玩具轮子文件，重构 `harness/idor_compare.py`，新增契约测试）
- [x] 新 AI 是否知道为什么这么设计？（知道：对标 Claude-Red 与 A.I.G 黄金标准，排除同构 JSON 0.99 相似度误报陷阱）
- [x] 新 AI 是否知道哪些行为不能破坏？（知道：严禁修改 Rust `ResearchTask`，严禁自造 Python Agent，严禁无来源神秘规则）
- [x] 新 AI 是否知道当前唯一下一步？（知道：执行 `tmp/check_target_delegate_grant.py`）
- [x] 新 AI 是否知道如何运行测试？（知道：`uv run --project python pytest -q`）
