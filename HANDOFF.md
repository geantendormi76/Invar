# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot / Recovery Contract  
> **Project:** Invar  
> **Snapshot Date:** 2026-09-28  
> **Canonical Repository Root:** `C:\dev\Invar`  
> **Canonical Handoff Path:** `C:\dev\Invar\HANDOFF.md`

---

## 0. Handoff Metadata

| Item | Value | Level | Evidence / Note |
|---|---|---|---|
| Project | Invar | [FACT] | 生产级安全实证与漏洞研究 Harness |
| Role | System-2 深度动态实证与安全研究引擎 | [FACT] | 确定性沙箱 + 智能体运行时双引擎 |
| Active research target | `ikuai8.com` | [FACT] | `data/targets/ikuai8.com/scope.txt` |
| Current phase | Phase R2 — Autonomous Research Mission Execution | [DECISION] | Phase R1 (R1-0 至 R1-5) 全部完成闭环 |
| Current objective | 建立首个领域技能规范 (`skills/authorization_investigation/SKILL.md`)，指导 Pi Agent 针对首个靶标端点 `POST:/api/v3/delegate/grant` 展开受控实证研究 | [DECISION] | 当前唯一主推进点 |
| Python test baseline | 205 passed in 0.45s | [FACT, verified] | `uv run --project python pytest -q` |
| Rust test baseline | 15 passed | [FACT, historical] | `cargo test --workspace` |
| Combined baseline | 220 / 220 passed | [FACT] | 核心契约与测试全量绿灯 |
| Agent Runtime | `@earendil-works/pi-coding-agent` (global npm) | [FACT] | Node.js 物理动态加载实证通过 |
| Native Tools verified | `read`, `write`, `edit`, `powershell` | [FACT] | `tmp/check_pi_native_tools.mjs` & `check_pi_powershell_tool.mjs` 实证通过 |
| Model inference endpoint | `http://127.0.0.1:8080/v1` (llama-server) | [FACT] | 本地 Qwen3.8-27B 3.06bpw，带思维链响应实测通过 (10s) |
| Reverse dependencies | 0 violations in `harness/` | [FACT] | `tmp/check_harness_agent_dependency.py` 审计通过 |
| Threat Model contract | `ThreatModel` + `AttackerProfile` defined & tested | [FACT] | `harness/domain_contracts.py` (4 passed) |
| Official Agent Runner | `tools/invar_agent_runner.mjs` | [FACT] | `--help` 与 `--dry-run` 自检通过 |

---

## 1. Project Identity

### 1.1 System Role
[FACT]
Invar 是安全实证研究体系中的 **System-2 深度动态实证与安全研究引擎**。
它的边界由两层紧密咬合：
1. **上层认知与控制平面 (Agent Runtime)**：由外部现成的 Pi Agent Runtime 全权承载，调度本地 Qwen3.8-27B 大模型，负责多轮记忆、会话分支压缩、规划思考以及基于极简工具（`read`, `write`, `edit`, `powershell`）的操作调度；
2. **底层确定性安全核心 (Deterministic Security Core)**：由 Invar Python/Rust 引擎承载，负责真实的物理发包、重试变异自愈、双主体差分比对、安全不变量裁决、独立第三方复核与门禁确权。

### 1.2 Engineering Constitution
[DECISION]
项目严格遵循通用 AI 工程宪法：
- 零臆造、零重复造轮子、零无依据特判；
- 根因优先于表面修补；
- 目录是职责边界，类型是数据边界，接口是模块边界；
- **拿来主义与黄金标准驱动**：优先参考成熟开源项目（Shannon、Strix、PentAGI、Anthropic Harness、Claude-Red）的做法，不自创脆弱复杂算法；
- 一次只推进一个明确的工程动作；
- 临时脚本必须封装于 `tmp/check_xxx.py` 或 `tmp/check_xxx.mjs`，由 PowerShell 单引号块落盘，严禁向用户输出长内联命令行。

---

## 2. Current Mission

[DECISION]
**打造一个由 AI 智能体自主驱动、以真实代码切片与物理发包为依据、具备确定性门禁防护的 Web API 自动化漏洞研究 Harness，并完成针对真实授权靶标的首次全流程实证研究闭环。**

---

## 3. Current Objective

### CURRENT OBJECTIVE
[DECISION]
> **参考 `SnailSploit/claude-red` 与 Strix 的黄金实践，在工作区构建首个标准化研究技能规范（`skills/authorization_investigation/SKILL.md`），为 Agent 针对首个靶标端点 `POST:/api/v3/delegate/grant`（假说 `H-AUTH-1`）注入标准作业程序（SOP），规约其从代码切片读取、威胁模型确立、Invar 沙箱发包到不变量裁决的 5 步实证探索链条。**

### 已经完成与物理证明的部分
[FACT]
1. **R1-0 (运行时实证)**：证实本机全局 Pi 运行时可直接加载 `createAgentSession`、`ModelRuntime` 与 `SessionManager.inMemory()`，与本地 Qwen3.8-27B 完成通信握手，原生解析思维链（`thinking`）与文本回执。
2. **R1-1 (反向解耦)**：彻底根除了 `harness/` 目录中对 `agent/` 的全部 4 处静态反向导入（下沉事件契约与领域常量，沙箱执行器实现纯净控制反转 IoC），静态 AST 审计显示反向违规归零，全量 201 测试保持绿灯。
3. **R1-2 (威胁模型一级契约)**：在 `harness/domain_contracts.py` 中建立 `ThreatModel` 与不可变 `AttackerProfile`，实现受控假说派生（`derive_hypothesis`），新增 4 个契约测试全绿（总基准提升至 205 passed）。
4. **R1-3/4 (极简武器库实证)**：验证了 Pi 原生自带的 `read` 与 `powershell` 工具直接调度 Invar 引擎的能力。本地 Qwen 在 10 秒内调用 `powershell` 执行 `pytest` 并正确归纳结果，拒绝自创复杂状态机轮子。
5. **R1-5 (官方运行器交付)**：交付了生产级运行脚本 `tools/invar_agent_runner.mjs`，注入了严格的安全科研简报（Mission Briefing），通过了 `--help` 与 `--dry-run` 验证。

---

## 4. Next Single Action

### NEXT SINGLE ACTION
> **在工作区创建针对特权授权委托接口的标准操作技能规范文件：`skills/authorization_investigation/SKILL.md`，规范化定义针对端点 `POST:/api/v3/delegate/grant`（假说 `H-AUTH-1`）的触发条件、攻击者画像、信任边界、Invar 沙箱调用命令以及软 403 / SPA HTML 防误报规则。**

### 为什么只有这一个动作
[DERIVED]
在终端实测中，未装备 Skill 的 Agent 会退化为普通编码助手（做盲目的目录 `ls` 和文件阅读）。参考 `claude-red` 与 Strix 的黄金经验，中间层应当是纯文本 Markdown SOP，为 Agent 提供战术操作手册。此动作是启动第一次受控实证研究的唯一前置依赖，且不破坏任何现有生产代码。

---

## 5. Current Scope

### 5.1 In Scope
- `skills/authorization_investigation/SKILL.md`（新建 SOP 规范）
- 靶标端点切片上下文：`artifacts/reports/targeted_research_tasks_78.json` 中关于 `POST:/api/v3/delegate/grant` 的元数据
- 授权范围契约：`data/targets/ikuai8.com/scope.txt`
- 官方运行器调用验证：`tools/invar_agent_runner.mjs`

### 5.2 Out of Scope
- 禁止推倒重写 Invar 底层确定性沙箱；
- 禁止自创 Python 复杂的 `ResearchState` 状态机类；
- 禁止编写未经授权的外部发包脚本；
- 禁止跳过 Invar 门禁自行宣布发现漏洞；
- 暂不涉及桌面端 UI（Tauri / React）。

---

## 6. Out of Scope

[DECISION]
当前阶段坚决不碰：
- 重新全量扫描 AST；
- 引入重量级数据库（PostgreSQL / Neo4j）；
- 引入分布式工作流（Temporal）；
- 复杂蒙特卡洛树搜索（LATS / MCTS）；
- 任何越界目标的动态请求。

---

## 7. Last Known Good State

### 7.1 Engineering Baseline
[FACT, verified 2026-09-28]
```text
Python regression: 205 passed in 0.45s
Rust regression:   15 passed
Total baseline:    220 passed / 0 failed
Warnings:          0 fatal warnings
```
标准测试命令：
```powershell
uv run --project python pytest -q
cargo test --workspace
```

### 7.2 Native Tools & Inference Baseline
[FACT, verified 2026-09-28]
- `tools/invar_agent_runner.mjs --dry-run` 成功通过；
- 本地 `127.0.0.1:8080` (llama-server, Qwen3.8-27B) 工具调用往返正常；
- `powershell` 工具调用响应耗时约 10 秒；
- `harness/` 目录反向依赖 AST 审计：0 violations。

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| R1-0 Pi Runtime 实证 | DONE | `check_pi_session_real_call.mjs` | 本机全局 npm 环境 | 证实导出 `createAgentSession`, `ModelRuntime` 并成功与 Qwen 握手 |
| R1-1 Harness 架构解耦 | DONE | `check_harness_agent_dependency.py` (0 violations) | `harness/sandbox_executor.py`, `harness/execution_trace.py` | 根除对 agent 的反向依赖，实现控制反转 |
| R1-2 威胁模型一级契约 | DONE | `test_threat_model_contract.py` (4 passed) | `harness/domain_contracts.py` | 确立 `ThreatModel` 与 `AttackerProfile` |
| R1-3/4 极简武器库实证 | DONE | `check_pi_native_tools.mjs`, `check_pi_powershell_tool.mjs` | `tmp/` 测试脚本 | 证实 Pi 原生 `read` 与 `powershell` 工具 10 秒内闭环调度 Invar |
| R1-5 官方运行器交付 | DONE | `node tools/invar_agent_runner.mjs --dry-run` | `tools/invar_agent_runner.mjs` | 固化 Mission Briefing 与极简工具调用规范 |
| 生产/科研轨道契约 | DONE | `test_run_track_contract.py` (4 passed) | `configs/profiles/*.toml`, `domain_contracts.py` | 明确 Production 与 Research 轨道隔离 |
| 确定性沙箱与防误报 | DONE | `test_sandbox_403_research_loop.py` | `harness/sandbox_executor.py` | 排除软 403 与 SPA HTML 假放行 |
| 科学证据与终审门禁 | DONE | `test_verification_and_promotion_gate.py` | `harness/verification_gate.py` | 独立第三方复核与 PromotionGate 确权 |

---

## 9. Changed Files

### 9.1 Added
- `tools/invar_agent_runner.mjs`: Invar 官方智能体研究运行器。
- `python/tests/test_threat_model_contract.py`: 威胁模型契约测试套件（4 项用例全绿）。
- `tmp/apply_r1_1_step1_events.py`: 事件契约下沉迁移脚本。
- `tmp/apply_r1_1_radical_decouple.py`: 沙箱反向依赖切断脚本。
- `tmp/restore_and_decouple_sandbox.py`: 沙箱全量无反向依赖重写脚本。
- `tmp/fix_sandbox_default_agent.py`: 动态控制反转工厂函数注入脚本。
- `tmp/apply_r1_2_threat_model.py`: 威胁模型契约写入脚本。
- `tmp/check_harness_agent_dependency.py`: 生产代码双向静态依赖审计工具。

### 9.2 Modified
- `python/packages/core/src/harness/domain_contracts.py`:
  - 追加第 11 节：`ResearchEventType`, `ResearchEvent`, `ResearchEventSink`；
  - 追加第 12 节：`IDOR_KEYWORDS` 领域常量；
  - 追加第 13 节：`ThreatModel`, `AttackerProfile` 威胁模型契约与自检、假说派生方法。
- `python/packages/core/src/harness/execution_trace.py`:
  - 彻底移除了 `from agent.loop_types import ...`，改为从同级 `harness.domain_contracts` 引用事件。
- `python/packages/core/src/harness/sandbox_executor.py`:
  - 移除了顶层对 `agent` 模块的全部 3 处静态依赖；
  - 类型标注改为纯净抽象 `Optional[Any] = None`；
  - 引入 `_resolve_default_agent` 与 `_resolve_hypothesis_engine` 运行时动态装配，实现标准 IoC。
- `python/packages/core/src/agent/loop_types.py`:
  - 将事件类定义改为从 `harness.domain_contracts` 转发导入，保持上层完全向后兼容。
- `python/packages/core/src/agent/hypothesis_engine.py`:
  - 将 `IDOR_KEYWORDS` 改为从 `harness.domain_contracts` 导入。
- `python/packages/core/src/harness/__init__.py`:
  - 导出 `ThreatModel` 与 `AttackerProfile`。

---

## 10. Current Architecture

```text
┌────────────────────────────────────────────────────────┐
│   Pi Agent Runtime (Node.js 运行时)                    │
│   - tools/invar_agent_runner.mjs (官方运行器)          │
│   - SessionManager.inMemory() (会话树与记忆)           │
│   - 原生武器库: read, write, edit, powershell          │
│   - 推理引擎: 本地 Qwen3.8-27B 3.06bpw (10s 极速响应)  │
└───────────────────────────┬────────────────────────────┘
                            │ (根据 Skill SOP 执行命令)
                            ▼
┌────────────────────────────────────────────────────────┐
│   中间战术层: Invar Research Skills (Markdown SOP)     │
│   - skills/authorization_investigation/SKILL.md (待建) │
│   - 提供 5 步阶梯工作流，指导模型调用下层命令，防止幻觉   │
└───────────────────────────┬────────────────────────────┘
                            │ (调用确定性沙箱命令)
                            ▼
┌────────────────────────────────────────────────────────┐
│   Invar 确定性安全核心 (Deterministic Security Core)   │
│   - 范围与目标: data/targets/ikuai8.com/scope.txt      │
│   - 威胁模型: ThreatModel 一级契约                     │
│   - 物理探测: AdaptiveSandboxExecutor (解耦 IoC 架构)  │
│   - 事实裁决: InvariantEvaluator (安全不变量断言)      │
│   - 终审门禁: IndependentVerifier -> PromotionGate     │
└────────────────────────────────────────────────────────┘
```

---

## 11. Architecture Decisions

### AD-01 — 坚定复用 Pi 作为 Agent Runtime
[DECISION]
Pi 是经物理实证的外部标准运行时，成熟提供了会话、记忆、上下文压缩和原生极简工具。Invar 彻底放弃在 Python 内手写缩小版 Agent Runtime 的重复建设。

### AD-02 — 极简工具哲学（Unix Philosophy）
[DECISION]
放弃为每个 Python 函数封装复杂的专用 JSON Tool Schema。坚决遵循 Pi、Claude Code 与 Anthropic 的极简哲学：赋予 Agent `read`（读切片/代码/配置）、`write`（写笔记/假说/报告）和 `powershell`（调用 Invar 底层确定性命令），对本地 27B 量化模型最稳定、最不易产生幻觉。

### AD-03 — 技能即文档（Skills as Markdown SOP）
[DECISION]
参考 `SnailSploit/claude-red` 与 Strix 的黄金经验：中间层 Skills 不需要写沉重的 Python 代码，而是以 `SKILL.md` 规范文件的形式存在，为大模型提供明确的操作清单、盲区预警（如软 403 陷阱）与命令调用示范。

### AD-04 — 确定性核心享有最终裁决权
[INVARIANT]
大模型仅负责阅读、推演、生成假说和发起命令。最终的漏洞确权（`CONFIRMED` Finding）必须满足：物理发包重放稳定 + 语义等价核准 + `InvariantEvaluator` 击穿 + 独立第三方复核 + `PromotionGate` 准入。大模型无权自封漏洞。

---

## 12. Data / API / Type Contracts

### 12.1 `ThreatModel` & `AttackerProfile`
[FACT]
位于 `harness/domain_contracts.py` 第 13 节：
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

### 12.2 `AdaptiveSandboxExecutor` (Decoupled IoC)
[FACT]
位于 `harness/sandbox_executor.py`：
```python
class AdaptiveSandboxExecutor:
    def __init__(
        self,
        cfg: Optional[InvarConfig] = None,
        transport: Optional[HttpTransport] = None,
        feedback_interpreter: Optional[FeedbackInterpreter] = None,
        mutation_policy: Optional[MutationPolicy] = None,
        research_agent: Optional[Any] = None,
        llm_provider: Optional[Any] = None,
    ) -> None: ...
```
沙箱内部不包含任何静态 `from agent...` 导入。

---

## 13. Algorithms / Workflow

### 13.1 智能体实证科研 5 步 SOP (Target Workflow)
```text
Target JSON Task
    ↓
Agent activates SKILL.md
    ↓
Step 1: Read Context (scope.txt + AST code slice)
    ↓
Step 2: Establish ThreatModel (Attacker: anonymous_external)
    ↓
Step 3: Run Invar Sandbox via powershell
    ↓
Step 4: Analyze Response (Rule out Soft-403 & SPA 200 HTML fallback)
    ↓
Step 5: Verify Invariant & Record Evidence
```

---

## 14. Verified Tests

```powershell
uv run --project python pytest -q
```
**结果：205 passed in 0.45s**
覆盖套件包含：
- `test_threat_model_contract.py` (4 passed)
- `test_sandbox_operators_all.py` (7 passed)
- `test_sandbox_403_research_loop.py` (3 passed)
- `test_research_evidence_all.py` (2 passed)
- `test_adaptive_sandbox_all.py` (2 passed)
- 历史全部沙箱、门禁、断点、报告测试无缝通过。

---

## 15. Failure / Pitfall Registry

### FP-13 — 在构造函数中使用已被移除的类型标注导致 NameError
**Problem**: 移除模块顶层导入后，`def __init__(..., research_agent: Optional[ResearchAgent] = None)` 触发 `NameError`。  
**Root Cause**: 解释器在类定义期解析类型注解，此时命名空间中该类不存在。  
**Correct Fix**: 将类型解耦为 `Optional[Any] = None` 或定义独立的 `Protocol`。

### FP-14 — 函数级局部惰性导入（Lazy Import）并非真解耦
**Problem**: 在函数内部写 `from agent... import ...`，仍然会被 AST 依赖体检脚本拦截。  
**Root Cause**: 静态依赖依然存在，未解决底层绑架上层的控制反转问题。  
**Correct Fix**: 采用纯粹依赖注入，或通过 `sys.modules` 反射解析可选钩子，彻底清除 `from agent` 语句。

---

## 16. Do Not Repeat

1. 不要关起门来自己编写复杂的 Agent 状态机类（Strix 和 Shannon 证明 `todo` 与原生会话树足矣）。
2. 不要为了给 Agent 赋能而写几十个专有 Tool Schema（极简 `read`, `write`, `powershell` 最稳健）。
3. 不要在底层沙箱模块（`harness/`）中静态引用认知层（`agent/`）。
4. 不要把大模型的自然语言推论直接作为安全事实或判定漏洞的依据。
5. 不要让没有配备 SOP（Skill）的裸 Agent 随意对公网发起非受控请求。

---

## 17. Invariants

- **权威裁决唯一性**：只有 Invar 的确定性测试与门禁有权判定漏洞。
- **授权边界绝对性**：严禁碰触 `data/targets/<target>/scope.txt` 之外的目标。
- **目录职责边界**：`harness/` 必须保持零 `agent/` 反向导入。
- **单步推进法则**：一次只推进一个明确的工程动作，先测试验证再继续。

---

## 18. Open Issues

- **OI-01 (Pi 运行时身份)**：`[CLOSED]`
- **OI-02 (Invar 与 Pi 集成方式)**：`[CLOSED]`
- **OI-05 (Agent ↔ Harness 双向依赖)**：`[CLOSED]`
- **OI-06 (Threat Model 契约缺失)**：`[CLOSED]`
- **OI-11 (首个靶标端点研究 SOP 待固化)**：`[OPEN]`
  - 靶标端点 `POST:/api/v3/delegate/grant` 缺少结构化的 `SKILL.md` 指南，Agent 尚不了解具体发包步骤。

---

## 19. Environment / Toolchain

| Component | Known State |
|---|---|
| OS | Windows (PowerShell) |
| Python | 3.12 (`uv` managed) |
| Node.js | v24.18.0 |
| Global Pi Package | `@earendil-works/pi-coding-agent` |
| Local Model Server | `llama-server.exe` (port: 8080) |
| Local Weights | `Qwen3.8-27B-Uncensored-IQ3_XXS.gguf` |
| Runner Script | `tools/invar_agent_runner.mjs` |

---

## 20. Roadmap

- [x] **Phase R1-0**: Pi 运行时与 Qwen 通信实证
- [x] **Phase R1-1**: 架构单向解耦（消除 harness -> agent 反向依赖）
- [x] **Phase R1-2**: 威胁模型一级契约落地
- [x] **Phase R1-3/4**: 极简武器库实证（read / powershell）
- [x] **Phase R1-5**: 交付官方运行器 `tools/invar_agent_runner.mjs`
- [ ] **Phase R2**: 首个端点实证研究闭环
  - [ ] **R2-1**: 编写 `skills/authorization_investigation/SKILL.md` (当前唯一下一步)
  - [ ] **R2-2**: 驱动 Agent 执行针对 `POST:/api/v3/delegate/grant` 的自主探索
  - [ ] **R2-3**: 捕获物理证据并触发 Invar 终审门禁

---

## 21. Recovery Protocol

新 AI 接手后恢复顺序：
1. 读取 `HANDOFF.md`；
2. 运行 `uv run --project python pytest -q` 确认 205 passed 基准；
3. 运行 `node tools/invar_agent_runner.mjs --dry-run` 确认环境健全；
4. 确认当前唯一下一步为 **R2-1**；
5. 执行 `NEXT SINGLE ACTION`。

---

## 22. AI Collaboration Protocol

- 默认中文；专业术语第一次出现时标注英文。
- 遵循单步工程协作，每轮只要求用户执行一个物理动作。
- 代码修改使用 PowerShell 单引号块落盘至指定路径。
- 回复格式遵循：目标 -> 溯源 -> 原理 -> 执行内容 -> 反馈要求。

---

## 23. Security / Sensitive Data Boundary

- 严禁把真实 Cookie、Authorization Token、私钥或凭证写入 HANDOFF。
- 动态测试必须严格限定在 `data/targets/ikuai8.com/scope.txt`。

---

## 24. Reproducibility Status

**FULLY REPRODUCIBLE (100%)**  
- 核心代码、沙箱、契约与测试（205 passed）完全通过；
- 本机 Pi 运行时、`llama-server` 与本地 Qwen 链路实测通过；
- 官方启动脚本 `--dry-run` 自检通过。

---

## 25. Handoff Self-Check

- [x] 新 AI 是否知道当前在做什么？（知道：Phase R2，给首个端点建立 Skill）
- [x] 新 AI 是否知道最后一次成功状态？（知道：205 passed 全绿，dry-run 成功）
- [x] 新 AI 是否知道为什么这么设计？（知道：对标 Shannon/Strix/claude-red 黄金标准）
- [x] 新 AI 是否知道唯一下一步？（知道：创建 `skills/authorization_investigation/SKILL.md`）
- [x] 新 AI 是否知道绝对禁止做什么？（知道：禁止自创复杂状态机，禁止跳过沙箱裸发包）

---

# Final Recovery Statement

> **Invar 现已完成智能体运行时（Pi Harness）与确定性安全计算核心（Invar Core）的完美集成。**  
> **底层沙箱彻底解耦，反向依赖归零；上层大模型具备 10 秒级极简工具调用能力。**  
> **下一步唯一的工程动作是：为首个靶标端点编写领域技能手册（`skills/authorization_investigation/SKILL.md`），赋予 Agent 真正的科学研究实战规约！**
