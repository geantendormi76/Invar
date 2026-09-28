# AI Development Handoff Specification

> Invar 跨会话工程状态机快照。不是 README、会议纪要或聊天摘要。
>
> 目标：当原 AI 会话关闭、上下文丢失或历史聊天不可访问时，新 AI 仅凭本文件 + 当前源码/测试/配置/正式文档，即可恢复最新可验证状态、识别漂移、避免重复历史工作，并从 `NEXT SINGLE ACTION` 继续。

---

## 0. Handoff Metadata

| Item | Value | Level | Evidence / Note |
|---|---|---|---|
| Project | `Invar` | [FACT] | 当前工程名称。 |
| Repository Root | `C:\dev\Invar` | [FACT] | 当前工程根目录，由当前会话命令输出确认。 |
| Handoff Date | `2026-09-25` | [FACT] | 当前会话日期。 |
| Handoff Exact Time | `UNKNOWN` | [UNKNOWN] | 本轮没有可靠的完整本地时间戳。 |
| Branch | `UNKNOWN` | [UNKNOWN] | 当前用户明确要求后续不要主动操作 Git；本档案不猜。 |
| Commit | `UNKNOWN` | [UNKNOWN] | 当前会话未取得可靠实时提交号。 |
| Version / Release | `UNKNOWN` | [UNKNOWN] | 当前未确认项目版本字段。 |
| Collaboration Mode | `User executes commands; AI analyzes returned terminal output` | [DECISION] | 当前纯 Snapshot 交互；不使用 Codex Agent。 |
| Current Git Boundary | `No Git mutation by AI` | [DECISION] | 不执行 `reset/restore/checkout/clean/revert` 等修改动作；不擅自整理用户工作树。 |
| Source Precedence | `latest executable evidence > current source/tests > current config > formal docs > historical HANDOFF` | [DECISION] | 冲突时按此顺序恢复。 |

### 0.1 状态考古结论

[FACT]
本档案同时参考：当前会话真实终端输出、当前 Track Contract 变更结果、项目 Repomix 工程快照、历史 HANDOFF、项目正式工程文档以及已有测试契约。

[FACT]
历史工程文档存在明显时间漂移：旧 HANDOFF 曾记录 Phase 5 已完成、100% 覆盖等状态；随后 2026-09-24 的最新真实 Run 已显示 `BLOCKED`、42.55% coverage。因此旧数字不能覆盖最新运行事实。

[FACT]
当前最新一次 Track Contract 定向回归为 `11 passed`；这是本会话当前工作树上最晚的实时成功测试证据。

[DERIVED]
当前工程已经同时进入两个层面：
1. 安全研究闭环仍存在证据未闭环问题；
2. 工程架构正在把 `Production / Research / Intelligence / Benchmark` 从隐含语义提升为显式 Track Contract。

---

## 1. Project Identity

### 1.1 工程定位

[FACT]
Invar 是 Rust + Python Monorepo，当前核心实现集中在 Python 的 System-2 动态执行/研究、证据与验证链，同时保留 Rust core 的系统编排与基础能力。

[DECISION]
Invar 的长期架构目标是：**统一安全核心 + 运行轨道 + 平台适配器**，而不是为不同使用场景复制多个项目。

### 1.2 当前顶层分层

```text
Asset / Discovery
    ↓
Endpoint / AST Contract
    ↓
System-1 Triage
    ↓
Rule ∪ Neural Triage
    ↓
Unified Security Core
    ├── Production Track
    ├── Research Track
    ├── Intelligence Track
    └── Benchmark Track
    ↓
Evidence / Verification / Promotion
    ↓
Findings / SARIF / OpenVEX / Reports
    ↓
Platform Adapters (e.g. Butian)
```

[DECISION]
共享 `Evidence / Finding / Verification / Transport / Run` 数据与契约，不为各 Track 创建 `ProductionFinding`、`ResearchFinding`、`ButianFinding` 等平行模型。

[DECISION]
本地 LLM 只能作为 Research Proposal / Fallback Reasoning 能力，不是全局架构师，也不是最终安全事实唯一裁决者。

### 1.3 Headless

[FACT]
当前科研/审计闭环按 Headless 方式运行。

[DECISION]
`apps/desktop/` / Tauri / React 表现层当前不属于本阶段闭环，不因 Track Contract 改造而触碰。

---

## 2. Current Mission

[DECISION]
当前工程使命是把 Invar 从“可以运行 System-2 研究与报告导出”推进到：

> 每个安全命题都必须保留客观证据、能够独立复核、可以恢复/重放；证据不足时只能保持 `INCONCLUSIVE / BLOCKED`，不能把执行失败、模型失败或单一 HTTP 现象伪装成安全结论。

[DECISION]
与此同时，Track Contract 的工程化目标是让默认运行路径进入 `Production`，而现有 System-2 深度研究入口显式保持 `Research`，避免“默认 profile 改变后历史研究入口的语义漂移”。

---

## 3. Current Objective

### 当前唯一工程目标

[DECISION]
**完成 Track Contract 从数据模型到现有运行时配置系统的最小真实接通验证；在验证之前不进行目录搬迁、不重构业务模块、不新增第二套核心实现。**

当前已完成的是 Contract 建模；尚未证明的是：

```text
project.toml
    profile = production
        ↓
configs/profiles/production.toml
        ↓
existing config loader
        ↓
runtime configuration
        ↓
Production Track
```

[FACT from project snapshot]
当前 `python/packages/core/src/harness/config.py` 的 `InvarConfig` 主要从环境变量初始化 `workspace_root / output_dir / target_api_base / auth_token / auth_token_b / request_timeout / max_concurrent_workers / max_mutation_rounds / custom_headers`，快照中没有看到对 `configs/base/project.toml` 或 `configs/profiles/*.toml` 的读取逻辑。

[UNKNOWN]
以上是 2026-09-23/09-25 工程快照中的事实；当前本地 `config.py` 是否已有未进入快照的变化，本轮还没有得到实时文件全文确认。

---

## 4. Next Single Action

### 当前唯一下一动作

**只读检查当前本地 `python/packages/core/src/harness/config.py`，并确认它是否实际读取 `project.toml` / `production.toml`。**

执行约束：直接输出该文件全文或等价源码范围；不要修改任何文件，不运行 Git 修改命令，不运行完整审计。

### 为什么是它

[DERIVED]
Track Contract 已通过实时 11/11 测试。下一处真正未闭环的边界不是 `RunTrack` 类型本身，而是 `production.toml` 是否进入现有运行时配置链。

[DECISION]
在该只读验证完成前，不修改 `config.py`，不新增 config loader，不改变 `InvarConfig` 字段，不移动目录。

---

## 5. Current Scope

### 5.1 当前明确作用域

| Area | Current Role | Status |
|---|---|---|
| `python/packages/core/src/harness/run_models.py` | `RunTrack` / `ResearchRun` 运行契约 | LOCKED FOR THIS SLICE |
| `python/packages/core/src/harness/__init__.py` | 导出 `RunTrack` | LOCKED FOR THIS SLICE |
| `python/scripts/run_targeted_audit.py` | System-2 入口显式固定为 `RESEARCH` | LOCKED FOR THIS SLICE |
| `configs/base/project.toml` | 默认 profile 改为 `production` | LOCKED FOR THIS SLICE |
| `configs/profiles/production.toml` | Production profile 定义 | ACTIVE |
| `python/tests/test_run_track_contract.py` | Track 行为契约 | LOCKED TEST |
| `python/packages/core/src/harness/config.py` | 下一验证边界：profile 是否被消费 | PRIMARY NEXT INSPECTION |
| `python/packages/core/src/harness/transport.py` | 确定性 HTTP transport | LOCKED |
| `python/packages/core/src/harness/verification_gate.py` | 独立验证与晋级门禁 | LOCKED BEHAVIOR |
| `python/packages/core/src/harness/finding_models.py` | Finding 数据契约 | LOCKED CONTRACT |
| `python/packages/core/src/harness/reporting.py` | 平台无关报告投影 | LOCKED CONTRACT |
| `python/packages/core/src/agent/research_loop.py` | Research 路径 | ACTIVE / NOT THIS ACTION |
| `python/packages/core/src/agent/model_provider.py` | LLM structured-output 可靠性 | OPEN ISSUE / LATER |

### 5.2 当前源码结构契约

[FACT]
当前工程快照核心结构：

```text
apps/desktop/                     # UI；当前 OUT OF SCOPE
artifacts/                        # 运行交付物
configs/
  base/                           # default + project config
  profiles/                       # research / production profiles
  registry/                       # backend registry
  schemas/                        # config schema
data/targets/<target>/            # 目标资产
models/                           # 模型与 tokenizer
crates/core/                      # Rust core
python/
  packages/core/src/agent/        # LLM / research logic
  packages/core/src/harness/      # execution / evidence / state / verification
  scripts/                        # operational entrypoints
  tests/                          # Python tests
scripts/audit/                    # benchmark / audit tooling
docs/ai/                          # AI engineering / operation docs
runs/                             # runtime state
```

[DECISION]
目录边界就是职责边界；当前不按旧 README 自动创建/迁移目录。

---

## 6. Out of Scope

在当前 Objective 完成之前，新 AI 不应主动：

1. 移动/重命名现有业务文件；
2. 重构 `apps/desktop`、Tauri、React；
3. 复制一套 Production core 或 Research core；
4. 把 Research 逻辑重新写一份 Production 版本；
5. 改 `HttpTransport` 以解决上层业务问题；
6. 修改 Finding / Verification / Reporting 契约；
7. 为单个 endpoint 添加特判；
8. 为了消除 warning 顺手改无关文件；
9. 重新设计 Agent 架构；
10. 在最新 Run 尚未闭环前声称“无漏洞/审计通过”；
11. 主动执行 Git `reset / restore / checkout / clean / revert`；
12. 把当前 `EOF blank line` 格式问题扩展成一次大范围格式化。

---

## 7. Last Known Good State

### 7.1 当前会话最后已知良好状态

[FACT]
日期：`2026-09-25`。

[FACT]
最后成功测试命令：

```powershell
uv run --project python pytest `
    python/tests/test_run_track_contract.py `
    python/tests/test_research_run.py
```

[FACT]
测试结果：

```text
11 passed in 0.05s
0 failed
```

[FACT]
该测试环境输出：Python `3.12.13`、pytest `9.1.1`、platform `win32`。

### 7.2 本次 Track Contract 已验证行为

[FACT]
以下行为已经由 11/11 回归保护：

- 新建 `ResearchRun` 默认 `track = RunTrack.PRODUCTION`；
- `inspect()` 输出 `track` 字段；
- `RunTrack.RESEARCH` 可以通过 `to_dict()` / `from_dict()` round-trip；
- 缺少 `track` 的历史序列化 payload 在 `from_dict()` 中按兼容策略恢复为 `RunTrack.RESEARCH`；
- `ResearchRun.load()` / `save()` 的既有序列化路径未被本次 Track Contract 回归破坏。

### 7.3 当前生产型 Run 事实（历史运行证据）

[FACT / HISTORICAL RUN]
最新已知真实靶向审计 Run：

```text
Run ID: RUN-TARGETED-1790248241
Target: ikuai8.com
total tasks: 86
coverage units: 47
covered: 20
blocked: 27
coverage: 42.55%
findings: 0
state: BLOCKED
```

[FACT / HISTORICAL RUN]
阻断原因模式包括：

```text
LLM output incomplete: finish_reason=length
404 ambiguity
405 ambiguity
422 ambiguity
任务未形成可验证的安全裁决
```

[DERIVED]
`0 findings` 不能被解释成“安全”；27 个 Coverage Unit 尚未形成闭环。

### 7.4 历史测试锚点

[FACT / HISTORICAL]
旧 HANDOFF 曾记录：Python 202 passed、Rust 15 passed、合计 217 passed；这些数字不是当前 2026-09-25 工作树的实时结果。

[DECISION]
新 AI 不得把历史 202/15/217 直接写成当前测试结果；若需要恢复，应重新执行对应命令并根据真实输出更新状态。

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| RunTrack enum | DONE | 11/11 Track Contract tests | `run_models.py` | `PRODUCTION/RESEARCH/INTELLIGENCE/BENCHMARK` |
| ResearchRun default track | DONE | `test_default_track_is_production` | `run_models.py` | 默认改为 Production |
| inspect track exposure | DONE | `test_track_is_exposed_by_inspect` | `run_models.py` | 输出 `track` |
| Track serialization round-trip | DONE | `test_track_round_trips_through_serialization` | `run_models.py` | `to_dict()` 使用现有 `asdict(self)` 路径 |
| Legacy Research semantics | DONE | `test_legacy_run_payload_preserves_research_semantics` | `run_models.py` | 缺失 track 时恢复 RESEARCH |
| RunTrack public export | DONE | current source + tests | `harness/__init__.py` | 供其他模块使用 |
| System-2 explicit Research track | DONE | current source review | `run_targeted_audit.py` | 避免 default profile 改变导致语义漂移 |
| Default project profile | DONE | current terminal output | `configs/base/project.toml` | `profile = "production"` |
| Production profile file | DONE | current terminal output | `configs/profiles/production.toml` | 仅包含 track/runtime，不复制 Research logic |
| Track Contract test suite | DONE | 11/11 passed | `python/tests/test_run_track_contract.py` | 4 核心契约测试 |
| Runtime profile wiring | UNVERIFIED | 未完成实时 config.py 验证 | `harness/config.py` | 下一主推进点 |

---

## 9. Changed Files

### 9.1 Added / currently untracked as observed by user

[FACT / USER-REPORTED WORKTREE]

```text
configs/profiles/production.toml
python/tests/test_run_track_contract.py
0_Ornith-1.5-9B-Abliterated-IQ3_M.ps1
1_启动_27B级文本多Token流畅版.ps1
Invar Target Architecture v1.md
docs/ai/Invar 运行轨道契约.md
docs/补天漏洞响应平台（Butian）标准化漏洞提交流水线与规范指南.md
```

### 9.2 Modified as observed by user

```text
HANDOFF.md
configs/base/project.toml
python/packages/core/src/harness/__init__.py
python/packages/core/src/harness/run_models.py
python/scripts/run_targeted_audit.py
```

### 9.3 Deleted as observed by user

```text
docs/ai/补天漏洞响应平台（Butian）标准化漏洞提交流水线与规范指南.md
```

### 9.4 Moved / renamed

[UNKNOWN]
Git/status 输出同时出现一份删除路径和一份新增路径，但本档案**不把它们擅自认定为 rename/move**。关系需由用户后续明确或由不修改工作树的文件内容检查确认。

### 9.5 Structure changes

[FACT]
当前 Track Contract 阶段明确：**没有得到授权去移动现有业务文件；没有执行目录迁移。**

---

## 10. Current Architecture

### 10.1 Track model

[DECISION]
Track 是与 `RunStatus`、`RunProfile` 正交的运行语义维度：

```text
RunStatus  = 生命周期状态
RunProfile = 执行参数/轮廓
RunTrack   = 运行职责/工作轨道
```

[FACT]
当前 Track 枚举：

```text
PRODUCTION
RESEARCH
INTELLIGENCE
BENCHMARK
```

[DECISION]
默认构造新的 `ResearchRun()` 时使用 `PRODUCTION`；这是“新运行”的默认语义。

[DECISION]
对于旧的、已序列化且没有 `track` 字段的 `ResearchRun`，`from_dict()` 当前按兼容策略恢复 `RESEARCH`，因为旧对象语义历史上就是 Research Run；不得静默把旧 checkpoint 全部改标成 Production。

### 10.2 RunStatus

[FACT]
当前 RunStatus 包含：

```text
INIT
SCOPE_VERIFIED
CONTEXT_READY
PLAN_READY
EXECUTING
EVIDENCE_COLLECTED
EVALUATED
REPORT_READY
BLOCKED
COMPLETED
```

[FACT]
`BLOCKED` 是可恢复状态，历史实现允许重新进入多个中间阶段；`COMPLETED` 是终态。

[DECISION]
Track 不替换 Status；二者不得合并成一个枚举。

### 10.3 Execution layers

```text
Production
  → 默认、日常生成/运行路径
  → 使用统一核心

Research
  → 深度研究、LLM、假说/变异/重放/语义差分/独立验证
  → 现有 System-2 research path

Intelligence
  → 安全知识采集/规范化/索引
  → 为 Production / Research 提供输入

Benchmark
  → golden/replay/regression/evaluation
```

[DECISION]
Production 是默认轨道，不意味着 Production 是 Research 的复制版；它应优先复用确定性核心，在证据不足或高价值复杂任务需要时再提升到 Research 能力。

### 10.4 Platform adapters

[DECISION]
Butian 属于平台适配/交付层，不属于核心安全引擎。

[FACT from formal guide]
Butian 交付要求强调：利用完整请求/响应证据、PoC/复现步骤、厂商归属证明，并保持截图和漏洞描述满足平台字段规范。401/403/forbidden 不能单独作为未授权漏洞成立依据，必须证明实际影响或实质数据访问。

---

## 11. Architecture Decisions

### AD-01 — Unified Core + Tracks

**Decision**
不建立第二个 Invar 项目；在现有仓库内建立统一核心 + Production/Research/Intelligence/Benchmark 轨道。

**Why**
避免核心模型、Evidence、Finding、Verification、Transport 被复制后发生语义漂移。

**Alternatives rejected**
新建独立 Production 项目；复制 Research core；每个轨道一套 Finding 模型。

**Do not revert unless**
出现新的、可验证的系统边界证据证明职责已物理分裂并且共享核心无法保持一致契约。

### AD-02 — Track 与 Status 正交

**Decision**
`RunTrack` 不替代 `RunStatus`。

**Why**
状态描述生命周期，轨道描述职责/执行语义；混合会导致状态机膨胀与语义耦合。

### AD-03 — Production 默认，Research 显式

**Decision**
新的 Run 默认 Production；现有 System-2 入口显式固定 `RESEARCH`。

**Why**
避免修改默认 profile 后历史 Research 入口隐式换轨。

### AD-04 — Legacy payload 保留 Research 语义

**Decision**
缺少 `track` 的旧 `ResearchRun` payload 在反序列化时恢复 `RESEARCH`。

**Why**
兼容历史 checkpoint；不能仅因新的默认值变化而改写过去的运行语义。

### AD-05 — 不在当前阶段移动业务文件

**Decision**
Track Contract v1 只建立契约，不进行文件迁移/重命名。

**Why**
先建立语义，再依据真实依赖关系做后续结构收口；避免“为了结构而结构”。

### AD-06 — Git 由用户控制

**Decision**
AI 不执行 Git 修改操作，不删除/回滚用户已有工作树内容。

**Why**
当前工作树存在并行工作与文档变化；自动清理可能破坏用户未提交成果。

### AD-07 — LLM 非最终裁决器

**Decision**
LLM 只提供 proposal/reasoning；最终安全事实依赖确定性 observation、evidence、verification 与 promotion gate。

**Why**
LLM truncation、malformed output、timeout 都不能成为“安全”的证据。

---

## 12. Data / API / Type Contracts

### 12.1 `RunTrack`

[FACT]

```python
class RunTrack(str, Enum):
    PRODUCTION = "PRODUCTION"
    RESEARCH = "RESEARCH"
    INTELLIGENCE = "INTELLIGENCE"
    BENCHMARK = "BENCHMARK"
```

Input: 运行轨道语义。

Output: 以上枚举值。

Compatibility: 序列化 payload 缺失 track 时兼容为 `RESEARCH`。

Failure: 非法 track 字符串应在 `RunTrack(...)` 转换处失败；不得静默创建未知轨道。

### 12.2 `ResearchRun.track`

[FACT]

```python
track: RunTrack = RunTrack.PRODUCTION
```

Default: `PRODUCTION`。

Consumer: `inspect()`、`from_dict()`、运行入口等。

### 12.3 `ResearchRun.inspect()`

[FACT]
输出包含：

```text
run_id
status
target_root
source_ref
scope
profile
track
execution_policy
budget
started_at
completed_at
coverage_ledger_ref
findings_ref
block_reason
prior_run_refs
```

### 12.4 `ResearchRun.to_dict()` / `from_dict()`

[FACT]
`to_dict()` 目前沿用：

```python
data = asdict(self)
data["status"] = self.status.value
return data
```

[DERIVED]
因此当前 Track 序列化没有再复制一套显式字段投影；真实行为由 dataclass `asdict()` + `str, Enum` Track 类型 + `from_dict()` conversion 共同保证，并已通过定向测试。

### 12.5 `ResearchScope`

[FACT]
核心字段包括：

```text
target_domain
included_subdomains
excluded_paths
allowed_methods
authorization_boundary
```

Default authorization boundary:

```text
AUTHORIZED_ENGAGEMENT_ONLY
```

### 12.6 `RunProfile`

[FACT]

```text
name
max_mutation_rounds
timeout
workers
```

### 12.7 `ExecutionPolicy`

[FACT]

```text
allow_dynamic_testing
require_independent_verification
enforce_dual_token_for_idor
max_requests_per_task
```

### 12.8 `RunBudget`

[FACT]

```text
max_tasks
max_requests
max_duration_seconds
tasks_executed
requests_made
```

### 12.9 `InvarConfig`

[FACT from project snapshot]
当前已知字段：

```text
workspace_root
output_dir
target_api_base
auth_token
auth_token_b
request_timeout
max_concurrent_workers
max_mutation_rounds
custom_headers
```

[UNKNOWN]
当前本地 `InvarConfig` 是否已经增加 profile loading / track loading 字段，需要下一动作实时确认。

### 12.10 Transport contract

[DECISION]
`HttpTransport` 只负责确定性 HTTP 发送/响应快照，不负责风险评分、Payload 推理、Mutation、Research Loop 或 Finding 判定。

---

## 13. Algorithms / Workflow

### 13.1 当前统一执行抽象

```text
Input
  ↓
Scope verification
  ↓
Endpoint / task preparation
  ↓
Track selection
  ↓
Execution
  ↓
Observation
  ↓
Evidence
  ↓
Invariant evaluation
  ↓
Verification / Promotion Gate
  ↓
Finding / Report / Blocked queue
```

### 13.2 当前 Production / Research 语义

```text
New Run
  ↓
Track default = PRODUCTION
  ↓
确定性核心优先
  ↓
证据充分 → 继续标准生产路径
  ↓
证据不足 / 高价值复杂性
  ↓
允许升级到 RESEARCH 能力（后续阶段实现）
```

[TODO]
Production→Research 自动升级策略目前尚未实现；不能在当前状态中声称已存在。

### 13.3 最新 Run 的真实阻塞模式

[FACT / HISTORICAL]

```text
LLM structured output truncation
404/405/422 response ambiguity
insufficient evidence
→ BLOCKED / inconclusive
```

[DECISION]
任何 timeout / malformed output / LLM failure 均不能变成 confirmed safe。

---

## 14. Verified Tests

### 14.1 当前实时验证

[FACT]
命令：

```powershell
uv run --project python pytest `
    python/tests/test_run_track_contract.py `
    python/tests/test_research_run.py
```

结果：

```text
11 passed
0 failed
```

覆盖：Track default、inspect、serialization round-trip、legacy compatibility，以及既有 `ResearchRun` 测试。

### 14.2 直接 Python 导入试验

[FACT]
曾执行 `uv run --project python python -c ...` 做对象核验时得到 `ModuleNotFoundError: No module named 'harness'`，同时终端输入内容被粘贴/串行破坏。

[FACT]
仓库 `pytest.ini` 定义了 Python test path：

```text
python/packages/core/src
python
```

[DERIVED]
当前 `pytest` 能导入 `harness`，不意味着裸 `python -c` 自动拥有相同 `PYTHONPATH`。这个失败不是当前 Track Contract 失败的证据。

[DECISION]
未来验证 Python 模块时优先使用项目正式测试入口；若必须裸 Python 运行，显式配置模块搜索路径，不通过修改源码解决环境问题。

### 14.3 Git hygiene 检查

[FACT / USER-REPORTED]
`git diff --check` 当前曾报告 4 个目标文件在 EOF 存在额外空白行：

```text
configs/base/project.toml
python/packages/core/src/harness/__init__.py
python/packages/core/src/harness/run_models.py
python/scripts/run_targeted_audit.py
```

[DECISION]
这是格式卫生问题，不等同于运行逻辑错误；除非用户授权，否则不因该问题执行全局格式化或 Git 清理。

### 14.4 Historical tests

[FACT / HISTORICAL]
历史 HANDOFF 记录：Python 202、Rust 15、合计 217；当前未重新运行，因此状态为 `HISTORICAL ONLY`。

---

## 15. Failure / Pitfall Registry

### P-01 — Unsigned PowerShell script

**Problem**
通过 `.ps1` 文件执行时遇到 PowerShell “not digitally signed”。

**Symptom**
脚本无法直接执行。

**Root Cause**
本地执行策略阻止未签名脚本，而当前协作模式要求用户显式复制执行命令。

**Wrong Approach**
依赖下载/生成的 `.ps1` 直接执行。

**Correct Fix**
优先提供用户可直接粘贴的 PowerShell 代码；不要要求修改执行策略。

**Regression**
当前后续交互统一采用“直接命令 + 用户反馈”。

### P-02 — `to_dict()` anchor 假设错误

**Problem**
补丁脚本试图在 `to_dict()` 中寻找显式的 `"profile": self.profile.name` 行。

**Symptom**
anchor match = 0。

**Root Cause**
实际 `to_dict()` 使用 `asdict(self)`，没有显式逐字段构造 dict。

**Wrong Approach**
继续猜字符串锚点并插入一条重复序列化逻辑。

**Correct Fix**
尊重现有抽象：`asdict(self)` 保持不变，只在 `from_dict()` 做明确的 Enum reconstruction；测试证实这一方案工作。

### P-03 — 缺少 track field 导致半更新状态

**Problem**
`inspect()` / `from_dict()` 已引用 `track`，但 `ResearchRun` 字段一度没有同时落地。

**Symptom**
`AttributeError: ... no attribute 'track'` / `unexpected keyword argument 'track'`。

**Root Cause**
契约更新不完整。

**Correct Fix**
让 dataclass 字段、inspect、serialization compatibility 和 tests 一起形成一个完整最小闭环。

**Regression**
11/11 Track Contract + ResearchRun tests passed。

### P-04 — 裸 Python 导入路径误判

**Problem**
`uv run --project python python -c` 直接 import `harness` 失败。

**Root Cause**
`pytest.ini` 提供的 pythonpath 不等同于裸 Python shell 的模块搜索路径；并且当次 pasted command 本身发生内容串行破坏。

**Correct Fix**
以项目 pytest 为正式验证入口；裸 Python 需显式 PYTHONPATH。

### P-05 — EOF blank line

**Problem**
`git diff --check` 报 4 个目标文件 EOF blank line。

**Root Cause**
之前的 UTF-8 写回逻辑产生了额外空行。

**Status**
UNRESOLVED FORMATTING / LOW RISK。

**Important**
不能把该问题描述成源码逻辑破坏，也不能为了它扩大修改范围。

### P-06 — LLM `finish_reason=length`

**Problem**
最新真实 Run 多个任务出现 `LLM output incomplete: finish_reason=length`。

**Impact**
Coverage Unit 进入 BLOCKED，当前不能把未完成 reasoning 当作安全结论。

**Root Cause**
当前 provider 对结构化输出截断的恢复能力未闭环。

**Status**
OPEN ISSUE；不是当前 Track Contract 主动作。

### P-07 — 404/405/422 不能单独证明安全

**Problem**
不同 endpoint 返回 404/405/422。

**Root Cause**
状态码只提供有限网络事实，不能直接证明目标安全不变量。

**Correct Fix**
需要额外业务语义/差分证据；缺失时保持 INCONCLUSIVE/BLOCKED。

---

## 16. Do Not Repeat

1. 不要猜源码结构或 anchor；先读真实源码。
2. 不要因为 `0 findings` 就写成“目标安全”。
3. 不要把 404/405/422 当作自动 safe。
4. 不要让 LLM timeout、truncation 或 malformed output 绕过安全门禁。
5. 不要让 LLM 成为最终安全事实裁决器。
6. 不要为单个 endpoint 写不可泛化特判。
7. 不要为当前任务移动/复制整个核心目录。
8. 不要把 tests 放入 production source 目录。
9. 不要擅自清理用户工作树或 Git 未提交内容。
10. 不要把历史测试数字当当前实时结果。
11. 不要为了消除单个格式 warning 做无关重构。
12. 不要在未验证前一次修改多个核心层。
13. 不要在 HANDOFF 中写入 Token、Cookie、Password、Private Key、API Key。
14. 不要重复已经明确完成并通过测试的 Track Contract。

---

## 17. Invariants

### I-01 — Authorized Scope

[DECISION]
动态测试必须受 `scope.txt` / `ResearchScope` / `AUTHORIZED_ENGAGEMENT_ONLY` 约束。

### I-02 — Transport Purity

[DECISION]
`HttpTransport` 保持确定性透传，不替上层解释响应。

### I-03 — No Safety-by-Failure

[DECISION]
Timeout、LLM failure、malformed output、incomplete reasoning、网络错误不能变成 confirmed safe。

### I-04 — Coverage Integrity

[FACT]
`COVERED` 必须具有 reviewed path 与 check refs；`BLOCKED` 必须有 unresolved facts。

### I-05 — Finding Integrity

[FACT]
`CONFIRMED` 需要 severity/root cause/trace/evidence；`NEEDS_VALIDATION` 不应伪造 severity；`REJECTED` 必须有 rejection reason。

### I-06 — Independent Verification

[FACT]
Finding originator 不得自我复核。

### I-07 — Repository-relative traces

[FACT]
Finding trace path 必须 repository-relative，不得依赖绝对路径。

### I-08 — Standard projections

[DECISION]
SARIF/OpenVEX/reporting 保持标准契约，不为单个 finding 绕过标准格式。

### I-09 — Train / Gold separation

[DECISION / HISTORICAL]
保持 `Train ∩ Gold = ∅`。

### I-10 — Directory boundary

[DECISION]
Production source / tests / scripts / docs / runs / artifacts 职责分离。

### I-11 — One-Action Development

[DECISION]
每轮只推进一个逻辑动作；用户执行并反馈后，再决定下一动作。

### I-12 — Track / Status orthogonality

[DECISION]
RunTrack 与 RunStatus 不合并。

---

## 18. Open Issues

### O-01 — Production profile runtime wiring

**Impact**
如果 `production.toml` 只是“存在”而未被 config loader 消费，那么 `project.toml profile=production` 只是文档/配置状态，尚不能证明实际 runtime 已切换。

**Current Evidence**
已有 `project.toml` + `production.toml`；快照中的 `InvarConfig` 未展示 profile 文件加载逻辑。

**Known**
Track Contract 数据模型已经通过 11/11。

**Unknown**
当前 live `config.py` 是否已有 profile loader，或者是否存在其他真正消费 profile 的路径。

**Next Verification**
只读检查当前 `harness/config.py` 以及 profile 搜索引用。

### O-02 — Production execution path

**Impact**
目前还不能声称 Production Track 已经拥有独立、完整、可实战的执行路径。

**Known**
Track Contract 已完成；existing System-2 research entry 已显式 pinned to RESEARCH。

**Unknown**
哪些执行组件已经天然兼容 Production，哪些仍假定 Research。

### O-03 — LLM truncation recovery

**Impact**
最新 Run 的多个 Coverage Unit 被 `finish_reason=length` 阻断。

**Next Verification**
另一个独立工程动作：读取 `model_provider.py`、现有 provider tests，再设计最小恢复机制。

### O-04 — Coverage closure

**Impact**
最新 Run 27/47 Coverage Unit 仍 BLOCKED。

**Next Verification**
在 Provider / response resolver 等前置问题稳定后再处理。

### O-05 — EOF blank-line hygiene

**Impact**
`git diff --check` 非零退出，但不是当前运行逻辑失败。

**Next Verification**
由用户决定何时进行单独格式清理；不要与 runtime wiring 混合。

### O-06 — Current worktree document relocation semantics

**Impact**
用户工作树同时观察到旧 Butian 文档删除路径与新文档路径。

**Unknown**
是否为用户手动移动、复制还是其他变更。

**Rule**
不得擅自恢复、删除、合并或重命名。

---

## 19. Environment / Toolchain

### 19.1 Current verified environment

[FACT]

```text
OS: Windows (win32)
Python: 3.12.13
pytest: 9.1.1
Package manager / runner: uv
```

### 19.2 Repository test configuration

[FACT]
`pytest.ini` 提供：

```text
pythonpath = python/packages/core/src python
testpaths = python/tests python/packages/core/tests
```

### 19.3 Rust

[FACT / HISTORICAL]
`Cargo.toml` / `crates/core/` 存在 Rust workspace/core。

[UNKNOWN]
当前会话没有在 Track Contract 修改后重新执行 `cargo test --workspace`。

[FACT / HISTORICAL]
旧工程状态曾记录 Rust 15 tests passed，但这不是当前实时结果。

### 19.4 Model runtime

[FACT / HISTORICAL]
系统-1 模型目录存在：

```text
models/invar-intent-0.6b-v1/
```

[FACT / HISTORICAL]
Research 路径支持 OpenAI-compatible local model provider。

[UNKNOWN]
当前本地 LLM server 的精确模型文件 hash、launch flags、实际当前模型实例未由本轮确认。

### 19.5 Secrets

[DECISION]
真实凭据仅通过环境变量或运行时注入；HANDOFF 不保存 secret 内容。

---

## 20. Roadmap

### Phase A — Track Contract v1

Status: **DONE for model contract**

```text
RunTrack
→ ResearchRun.track
→ inspect
→ serialization compatibility
→ explicit Research entry
→ production.toml
→ 11/11 regression
```

### Phase B — Profile Runtime Wiring

Status: **CURRENT**

```text
Inspect config loader
→ confirm source of truth
→ minimal wiring design
→ test
→ verify production/research distinction
```

### Phase C — Production Execution Path

[TODO]

```text
Production default
→ deterministic fast path
→ evidence collection
→ verification
→ optional Research escalation
```

### Phase D — Evidence Closure

[TODO / historical roadmap]

```text
LLM recovery
→ response resolvers
→ explicit evidence sufficiency
→ verdict semantic split
→ Coverage Claim 2.0
→ replay / independence
→ blocked queue recovery
```

### Phase E — Benchmark / Golden Replay

[TODO]
建立可重放样本，覆盖：LLM truncation、404/405/422、soft 200、SPA HTML、IDOR dual-token、transport failures、checkpoint recovery、promotion failures。

### Phase F — Platform Delivery

[TODO]
在 core 稳定之后维护 Butian / SARIF / OpenVEX 等 downstream adapters，不把平台字段直接渗透进核心 Finding model。

[DECISION]
Roadmap 不等于当前任务。当前 AI 只能执行 `CURRENT OBJECTIVE → NEXT SINGLE ACTION`。

---

## 21. Recovery Protocol

### 21.1 新 AI 接手顺序

```text
1. 读取本 HANDOFF.md
2. 读取 CURRENT OBJECTIVE
3. 读取 NEXT SINGLE ACTION
4. 读取相关真实源码
5. 读取相关 contract tests
6. 检查当前工作树是否存在用户报告的漂移
7. 验证 Last Known Good State
8. 只执行 NEXT SINGLE ACTION
9. 运行该动作的最小回归测试
10. 根据真实终端结果更新 HANDOFF
```

### 21.2 Git 边界

[DECISION]
新 AI **不得主动修改 Git 工作树**。除非用户明确要求，禁止：

```text
git reset
git restore
git checkout
git clean
git revert
```

[DECISION]
本 HANDOFF 可以记录用户提供的 Git/status 输出，但不能把它当作 AI 有权清理这些文件的授权。

### 21.3 冲突处理

如果 HANDOFF 与源码冲突：

```text
不要猜
→ 以最新可验证源码为准
→ 记录 Open Issue
```

如果 HANDOFF 与测试冲突：

```text
优先运行/检查最新真实测试
→ 不用历史通过数字覆盖当前失败
```

信息不足：

```text
UNKNOWN
```

### 21.4 一动作原则

每轮必须：

```text
inspect
→ one logical change
→ targeted test
→ report
→ next action
```

不得一次输出一整套未经验证的连续重构。

---

## 22. AI Collaboration Protocol

### 22.1 Communication

[DECISION]
中文优先；代码、路径、枚举、CLI 命令保持英文原样。

### 22.2 Interaction

[DECISION]
当前模式是 Snapshot：

```text
AI 给命令/代码
↓
用户执行
↓
用户返回完整终端结果
↓
AI 根据真实结果分析
↓
只给下一动作
```

不得假设本地命令已经执行成功。

### 22.3 Command preference

[DECISION]
Windows 修改代码优先使用可直接粘贴的 PowerShell + UTF-8 落盘方式；避免依赖未签名 `.ps1`。

### 22.4 Python

[FACT]
标准测试入口：

```powershell
uv run --project python pytest
```

当前 Track Contract 最小回归：

```powershell
uv run --project python pytest `
    python/tests/test_run_track_contract.py `
    python/tests/test_research_run.py
```

### 22.5 Rust

[FACT]
标准 workspace 测试入口：

```powershell
cargo test --workspace
```

但当前 Track Contract 修改后尚未重新实时运行。

### 22.6 File safety

[DECISION]
在未读取真实源码之前不得猜改；所有非必要文件必须保持原样；用户已有 parallel changes 不得被新 AI 自动覆盖。

---

## 23. Security / Sensitive Data Boundary

### 23.1 Scope

[FACT]
最新已知 Run 的授权边界为：

```text
AUTHORIZED_ENGAGEMENT_ONLY
```

[DECISION]
新 AI 不得在无法确认授权边界时扩大动态测试目标。

### 23.2 Sensitive data

[DECISION]
HANDOFF 不写入：

```text
Token
Password
Cookie
Private Key
API Key
Session Credential
```

仅记录：

```text
ENV VAR NAME
REDACTED
FIXTURE
MOCK
```

### 23.3 Evidence

[DECISION]
真实请求/响应证据应保存在授权的 runtime artifacts 中；HANDOFF 只记录证据类型、状态与引用关系，不复制敏感 payload。

---

## 24. Reproducibility Status

### Current rating

**CONDITIONALLY REPRODUCIBLE**

### Why

[FACT]
Track Contract 的当前最小行为已经可以通过项目 Python 测试复现，最新定向回归为 11/11。

[FACT]
完整工程闭环仍不能称为 fully reproducible，因为：

- 当前生产 profile 是否进入 `InvarConfig` runtime 尚未实时确认；
- 最新完整审计 Run 为 BLOCKED；
- 27/47 Coverage Unit 尚未闭环；
- LLM 本地运行环境的完整指纹尚未确认；
- 最新工作树的提交号未可靠记录；
- Track Contract 修改后尚未重新运行完整 Python/Rust 测试套件。

### Reproducible now

```text
RunTrack behavior
ResearchRun serialization compatibility
explicit Research entry semantics
production.toml presence/content
```

### Not yet fully reproducible

```text
production profile → runtime config → actual execution path
full audit completion
full current test matrix
```

---

## 25. Handoff Self-Check

- [x] 新 AI 知道当前项目是什么：Invar，Rust + Python Monorepo。
- [x] 新 AI 知道当前 Track Contract 已做到哪里：11/11 通过。
- [x] 新 AI 知道最新安全 Run 不能被写成“安全”：42.55%，27 blocked。
- [x] 新 AI 知道当前唯一下一步：只读检查 `harness/config.py` profile wiring。
- [x] 新 AI 知道哪些文件在本轮变更：Added / Modified / Deleted 已记录。
- [x] 新 AI 知道当前不允许做什么：不移动业务文件、不做大重构、不修改 Git 工作树。
- [x] 新 AI 知道 RunTrack / RunStatus / RunProfile 的边界。
- [x] 新 AI 知道 404/405/422 与 LLM truncation 的证据语义。
- [x] 新 AI 知道 Python 正式测试入口与 `pytest.ini` pythonpath 事实。
- [x] 新 AI 知道敏感信息不能写进 HANDOFF。
- [x] 新 AI 知道历史 217 tests 只能作为历史锚点，不能冒充当前实时结果。
- [x] 新 AI 知道用户采用“AI 给一步命令 → 用户执行 → 返回输出”的协作协议。

### Stop Condition

[DECISION]
若新的源码、测试或用户命令输出与本档案冲突，先更新事实状态，再继续工程动作；不得为了保持文档叙事而修改代码或强行恢复旧数字。

---

## Appendix A — Current Track Contract Snapshot

```text
RunTrack
├── PRODUCTION      ← new-run default
├── RESEARCH       ← legacy + explicit System-2 research
├── INTELLIGENCE   ← knowledge / normalization track
└── BENCHMARK      ← replay / regression track
```

```text
ResearchRun
├── profile
├── track
├── execution_policy
├── budget
├── status
├── scope
└── evidence/report references
```

```text
project.toml
└── profile = "production"

production.toml
├── [track]
│   └── name = "production"
└── [runtime]
    ├── backend = "default"
    ├── execution = "local"
    └── reproducible = true
```

```text
run_targeted_audit.py
└── explicit track = RESEARCH
```

---

## Appendix B — Current User-Reported Worktree Snapshot

[FACT / USER-REPORTED, 2026-09-25]

```text
Modified:
  HANDOFF.md
  configs/base/project.toml
  python/packages/core/src/harness/__init__.py
  python/packages/core/src/harness/run_models.py
  python/scripts/run_targeted_audit.py

Deleted:
  docs/ai/补天漏洞响应平台（Butian）标准化漏洞提交流水线与规范指南.md

Added / untracked:
  0_Ornith-1.5-9B-Abliterated-IQ3_M.ps1
  1_启动_27B级文本多Token流畅版.ps1
  Invar Target Architecture v1.md
  configs/profiles/production.toml
  docs/ai/Invar 运行轨道契约.md
  docs/补天漏洞响应平台（Butian）标准化漏洞提交流水线与规范指南.md
  python/tests/test_run_track_contract.py
```

[DECISION]
This snapshot is descriptive only. It is not authorization to delete, restore, move, or reset any of these files.

---

## Appendix C — Golden Recovery Rule

> Evidence > Guess
>
> Current source > historical narrative
>
> Test result > assumption
>
> One logical action > batch mutation
>
> Shared contract > duplicated implementations
>
> Root cause > symptom patch
>
> User-controlled Git > automatic cleanup

```text
HANDOFF
   ↓
Current Objective
   ↓
Next Single Action
   ↓
Real Source
   ↓
Minimal Change
   ↓
Targeted Test
   ↓
Observed Result
   ↓
Update HANDOFF
```

**End of Handoff.**
