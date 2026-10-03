# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot / Recovery Contract
> **Project:** Invar
> **Snapshot Date:** 2026-10-03 (Asia/Tokyo)
> **Canonical Repository Root:** `/home/zhz/Invar`
> **Canonical Handoff Path:** `/home/zhz/Invar/HANDOFF.md`
> **Snapshot Authority:** 当前真实终端输出、真实运行产物、源码、测试、配置，以及本文件明确标记的 UNKNOWN。
> **Historical Context:** 项目最初在 Windows 环境开发；当前工程已经迁移至 Linux Mint 22.3，并已重新执行 Phase 0~7 完成 Linux 环境重建与边走边修复。

---

## 0. Handoff Metadata

| Item | Value | Level | Evidence |
|---|---|---|---|
| Project | Invar | [FACT] | 项目源码 / `pyproject.toml` / `Cargo.toml` |
| Repository Root | `/home/zhz/Invar` | [FACT] | 当前终端 `PWD` |
| OS | Linux Mint 22.3 | [FACT] | 当前终端输出 |
| Architecture | x86_64 | [FACT] | 当前运行环境 |
| Git Branch | `main` | [FACT] | 当前终端输出 |
| Git Tracking State before Phase 8 Smoke | `main...origin/main`，无工作树差异 | [FACT] | Smoke 前真实终端输出 |
| Git Commit | UNKNOWN | [UNKNOWN] | 当前快照未记录具体 commit SHA |
| Project Version | `0.1.0` | [FACT] | 当前 Repomix 中的 `python/pyproject.toml` |
| CPU | Intel Core i5-13600KF | [FACT] | 已记录环境事实 |
| RAM | 32 GB | [FACT] | 已记录环境事实 |
| GPU | NVIDIA GeForce RTX 3060 12GB | [FACT] | 当前终端 `nvidia-smi` |
| NVIDIA Driver | `595.91.07` | [FACT] | 当前终端 `nvidia-smi` |
| Python | 3.12.3 | [FACT] | 当前终端输出 |
| uv | 0.12.21 | [FACT] | 当前终端输出 |
| Node.js | v24.21.0 | [FACT] | 当前终端输出 |
| pnpm | 12.8.1 | [FACT] | 当前终端输出 |
| Rust | 1.99.0 | [FACT] | 当前终端输出 |
| Cargo | 1.99.0 | [FACT] | 当前终端输出 |
| Python Package Manager | `uv` | [FACT] | 工程规则与当前环境 |
| Node Package Manager | `pnpm` | [FACT] | 工程规则与当前环境 |
| Rust Build System | `cargo` | [FACT] | 工程规则与当前环境 |
| Local LLM Runtime | `llama-server` | [FACT] | `/v1/models` 实际响应 |
| Local LLM Endpoint | `http://127.0.0.1:8080/v1` | [FACT] | 当前真实环境 |
| Local LLM Model | `/home/zhz/models/Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf` | [FACT] | `/v1/models` 实际响应 |
| LLM Model Format | GGUF | [FACT] | `/v1/models` |
| LLM Quantization | Q4_K - Medium | [FACT] | `/v1/models` |
| LLM Parameters | 35.505B | [FACT] | `/v1/models` |
| LLM Context Runtime | 160000 tokens | [FACT] | `/v1/models` |
| Global Pi Agent | 已存在并可使用 | [FACT] | 当前用户实测状态 |
| Pi 是否为 Invar 当前模型调用链中的必经运行时 | 未证明 | [UNKNOWN] | Invar `OpenAICompatibleProvider` 当前直接调用本地 OpenAI-compatible endpoint |
| Current System Role | System-2 动态安全实证与证据确权 Harness | [FACT] | 当前源码结构与 Handoff |
| Authorized Target | `ikuai8.com` | [FACT] | 当前研究范围与既有 Handoff |
| Reproducibility State | CONDITIONAL | [DERIVED] | Phase 0~7 已稳定；Phase 8 真实证据闭环尚未完成；存在若干待核实状态冲突 |

---

## 1. Project Identity

[FACT]

Invar 是一个 AI 辅助的安全研究与动态实证确权系统。

核心结构不是“LLM 直接发包”，而是：

```text
静态事实
  ↓
确定性研究种子
  ↓
System-2 Research Agent / Control Plane
  ↓
受限动作
  ↓
Deterministic Sandbox
  ↓
真实 Observation
  ↓
Semantic / Invariant Evaluation
  ↓
Evidence Chain
  ↓
Independent Verification
  ↓
Finding
  ↓
OpenVEX / SARIF
````

工程边界：

```text
python/
    AI / ML / 数据 / 安全研究 / 评估

crates/
    Rust 底层能力 / 强类型系统 / 高性能核心

apps/
    Tauri / React 产品壳

node/
    Agent Harness / CLI / 编排能力

configs/
    声明式配置

data/
    数据资产

models/
    本地模型权重，不进入 Git

artifacts/
    正式报告与可交付物

docs/
    长期知识与工程记录

tmp/
    一次性探针、日志、临时诊断
```

---

## 2. Current Mission

[FACT]

构建端到端 Bug Bounty / SRC 自动化实证流水线。

当前系统已经完成前半段：

```text
资产发现
→ Web 测绘
→ 前端 JS 落地
→ AST 契约提炼
→ System-1 神经推演
→ Rule ∪ Neural
→ Research Seed Inventory
```

当前核心任务已经转入后半段：

```text
Research Seed Inventory
→ AdaptiveSandboxExecutor
→ Research Control Plane
→ 本地 LLM 受限决策
→ 真实动态实验
→ Observation
→ Evidence
→ Independent Verification
→ OpenVEX / SARIF
```

---

## 3. Current Objective

### CURRENT OBJECTIVE

[DECISION]

**定位并解决首次真实 Phase 8 Smoke Test 的 `INCONCLUSIVE` 原因。**

当前最近一次真实动态实验：

```text
Target: ikuai8.com
Task: POST /fs/recursive_move
Priority: P1
Hypothesis: H-AUTH-1
Profile: p1_state_mutation_safety

Result:
    INCONCLUSIVE
    elapsed: 168.8 ms
    attempts: 1
    coverage: 0/1
    findings: 0
    OpenVEX statements: 0
```

这个结果不能解释为：

```text
“没有漏洞”
```

它只能证明：

```text
本次单任务没有达到 Invar 的证据确权条件。
```

---

## 4. Next Single Action

### NEXT SINGLE ACTION

[TODO]

**只读检查第一次 Phase 8 Smoke Test 产生的运行事实。**

检查：

```text
artifacts/reports/phase8_smoke_p1_01/execution.jsonl
artifacts/reports/phase8_smoke_p1_01/audit_checkpoint.json
artifacts/reports/phase8_smoke_p1_01/findings.json
artifacts/reports/phase8_smoke_p1_01/NEEDS-VALIDATION.md
artifacts/reports/phase8_smoke_p1_01/coverage-summary.md
```

要求：

```text
不修改生产代码
不修改测试
不重新跑目标
不 --restart
不增加任务数量
不升级依赖
```

下一 AI 必须先确定：

```text
为什么最终 verdict = INCONCLUSIVE
```

然后才能决定下一步是否需要修改实现。

---

## 5. Current Scope

### CURRENT SCOPE

当前只允许研究以下边界：

```text
python/packages/core/src/agent/
    model_provider.py
    research_agent.py
    research_controller.py
    research_loop.py

python/packages/core/src/harness/
    sandbox_executor.py
    adaptive_selector.py
    semantic evaluation
    evidence
    verification
    reporting

python/scripts/
    run_targeted_audit.py

artifacts/reports/phase8_smoke_p1_01/
    本次单任务真实实验产物

tmp/
    一次性诊断脚本
```

当前研究对象：

```text
System-2 单任务真实动态实证
```

当前关心的数据链：

```text
TriageTask
→ EndpointRegistry
→ AdaptiveSandboxExecutor
→ CandidateAction
→ ResearchController
→ ControlPlaneDecision
→ HTTP Observation
→ Semantic Evaluation
→ Evidence
→ Verdict
```

---

## 6. Out of Scope

### OUT OF SCOPE

当前阶段明确禁止：

```text
❌ 重新执行 Phase 0~7
❌ 修改 Rust 架构
❌ 开始 Tauri / React UI
❌ 大规模 Monorepo 重构
❌ 升级 CUDA
❌ 升级 ONNX Runtime
❌ 重新设计 Agent Framework
❌ 将 86 个任务一次性提交给 LLM
❌ 在未知根因前修改多个模块
❌ 使用 --restart 重跑并掩盖第一次实验事实
❌ 删除 phase8_smoke_p1_01 产物
❌ 把 INCONCLUSIVE 当成 REJECTED
❌ 把 INCONCLUSIVE 当成漏洞不存在
```

---

## 7. Last Known Good State

### System LKG

[FACT]

```text
Date:
2026-10-03

Phase:
Phase 8.0 Local Control Plane Contract Probe

Verified:

真实本地 Ornith 35B
        ↓
OpenAI-compatible /v1
        ↓
OpenAICompatibleProvider
        ↓
ResearchController
        ↓
ControlPlaneDecision.validate()
        ↓
RUN_EXPERIMENT
        ↓
合法 candidate target_id
```

最终结果：

```text
[✓] Local Control Plane contract probe PASSED
[✓] No target network request performed
[✓] No production source modified
```

### Pipeline LKG

[FACT]

```text
Date:
2026-10-02 23:16 JST

Phase:
Phase 7

Result:
86 tasks assembled
P1 = 9
P2 = 54
P3 = 23

CUDAExecutionProvider:
successfully activated

Artifact:
artifacts/reports/targeted_research_tasks.json
```

### Latest Experiment

[FACT]

```text
Date:
2026-10-03

Phase:
Phase 8.1 Smoke Test

Task:
1 × P1

Endpoint:
POST /fs/recursive_move

Result:
INCONCLUSIVE

Attempts:
1

Elapsed:
168.8 ms

Coverage:
0/1

Findings:
0

OpenVEX:
0 statements

Checkpoint:
written
```

### LKG Rule

[DECISION]

当前最近一次 `INCONCLUSIVE` 实验不是新的 LKG。

未来出现回归问题时：

```text
Phase 8.0 Control Plane PASSED
+
Phase 7 artifact intact
```

是当前恢复锚点。

---

## 8. Completed Work

| Item                           | Status  | Evidence                               | Files                               | Notes                        |
| ------------------------------ | ------- | -------------------------------------- | ----------------------------------- | ---------------------------- |
| Windows → Linux Mint migration | DONE    | 当前 Linux 真实运行环境                        | 全项目                                 | 已重新执行 0~7                    |
| Linux Phase 0~3                | DONE    | 当前阶段产物与前序日志                            | `data/`, `tmp/raw_js/`              | 不重新执行                        |
| Phase 4 AST extraction         | DONE    | `tmp/ikuai8.com_endpoints_report.json` | `python/scripts/scan_pipeline.py`   | report endpoint count = 1097 |
| Phase 5 System-1               | DONE    | 前序真实产物                                 | `predict_triage_onnx.py`            | 已完成                          |
| Phase 6 dual-track             | DONE    | `triage_pools_v2.json`                 | `triage_dual_track_comparator.py`   | Pool A = 56, Pool B = 30     |
| Phase 7 task assembly          | DONE    | 86 tasks                               | `targeted_research_tasks.json`      | P1 9 / P2 54 / P3 23         |
| CUDA isolation                 | DONE    | 当前 `tools/env_cuda.sh` 可加载             | `tools/env_cuda.sh`                 | 当前环境运行稳定                     |
| Local LLM endpoint             | DONE    | `/v1/models` 返回实际模型                    | `llama-server`                      | 模型在线                         |
| Local Control Plane probe      | DONE    | Phase 8.0 probe PASSED                 | `tmp/probe_phase8_control_plane.py` | 未访问目标                        |
| Phase 8.1 real smoke           | PARTIAL | `INCONCLUSIVE`                         | `phase8_smoke_p1_01/`               | 尚未闭环                         |

---

## 9. Changed Files

### Added

[FACT]

```text
tmp/probe_phase8_entry.sh
tmp/probe_phase8_control_plane.py
```

职责：

```text
一次性只读 / 集成诊断探针
```

不得作为生产运行时依赖。

### Modified

[FACT]

```text
HANDOFF.md
```

本文件用于当前跨会话状态恢复。

### Generated

[FACT]

```text
artifacts/reports/phase8_smoke_p1_01/
```

当前已生成：

```text
execution.jsonl
audit_checkpoint.json
findings.json
sarif.json
REPORT.md
FINDINGS-DETAIL.md
NEEDS-VALIDATION.md
coverage-summary.md
openvex.json
```

### Deleted

[UNKNOWN]

当前会话未捕获执行后的完整 Git diff，因此删除状态必须由下一次恢复时验证。

### Moved

[UNKNOWN]

当前会话未捕获迁移后的完整 Git rename history，因此不要猜测。

### Structure

[FACT]

临时诊断脚本进入：

```text
tmp/
```

正式实验产物进入：

```text
artifacts/reports/
```

生产逻辑仍保持在：

```text
python/packages/core/src/
python/scripts/
```

---

## 10. Current Architecture

### Static Front Half

```text
Authorized Target
→ Subfinder
→ HTTPX
→ Katana
→ JS download
→ Tree-sitter AST
→ EndpointIR
→ System-1 inference
→ Rule ∪ Neural
→ TriageTask Inventory
```

当前已知：

```text
AST report:
1097 endpoints

Phase 7:
86 tasks
```

### Dynamic Back Half

```text
TriageTask
→ EndpointRegistry
→ AdaptiveSandboxExecutor
→ Baseline Probe
→ Denial Classification
→ Candidate Generation
→ ResearchController
→ ControlPlaneDecision
→ Candidate Execution
→ Observation
→ SemanticEquivalenceEvaluator
→ Invariant Evaluation
→ Evidence Chain
→ Replay / Independent Verification
→ Finding
→ PromotionGate
→ OpenVEX / SARIF
```

### Responsibility Boundary

```text
LLM:
    研究决策

ResearchController:
    决策约束与校验

AdaptiveSandboxExecutor:
    真实物理执行

Semantic Evaluator:
    Observation 语义判断

Evidence:
    事实记录

IndependentVerifier:
    独立复核

PromotionGate:
    确权门禁

ReportProjector:
    事实投影
```

---

## 11. Architecture Decisions

### Decision 1: LLM 不能直接产生任意 HTTP 请求

**Decision**

LLM 只能从确定性代码生成的候选动作中选择。

**Why**

降低模型幻觉对物理执行层的直接影响。

**Evidence**

`CandidateAction` 为确定性生成对象；`ControlPlaneDecision` 要求 `target_id` 属于当前候选集合。

**Do not revert unless**

出现新的源码事实证明当前控制模型失效。

---

### Decision 2: Control Plane Fail Closed

**Decision**

非法 JSON、未知 action、越界 target、越界 confidence 等异常必须拒绝，并回退到确定性安全路径。

**Why**

LLM 不得直接改变系统安全边界。

**Evidence**

`ResearchController.decide()` 明确执行严格校验，并在异常时使用确定性 fallback。

**Do not revert unless**

出现新的已验证控制契约。

---

### Decision 3: 86 个任务不得打包给 LLM

**Decision**

必须逐任务调度。

**Why**

安全动态实验是有状态的：

```text
Probe
→ Observation
→ Mutation
→ Observation
→ Verdict
```

**Evidence**

现有 Handoff 与 `run_targeted_audit.py` 设计都明确采用逐任务调度。

**Do not revert unless**

出现具备等价物理状态维持能力的新 Agent API。

---

### Decision 4: Sandbox 与 Agent 解耦

**Decision**

Sandbox 不能反向依赖 Agent 内部实现。

**Why**

保持执行层确定性、高内聚与低耦合。

**Evidence**

`AdaptiveSandboxExecutor` 采用可注入 `research_agent` / `llm_provider` 的控制反转方式。

**Do not revert unless**

新的架构证据明确要求修改职责边界。

---

### Decision 5: Python 环境必须通过 uv

**Decision**

不使用系统 Python / 全局 pip。

**Why**

保证依赖可复现与运行时隔离。

**Evidence**

工程宪法、README 与 Python workspace 约束。

**Do not revert unless**

出现新的正式工程规范并经项目级确认。

---

### Decision 6: CUDA 运行时必须隔离

**Decision**

当前 CUDA 环境不能随意升级或重新接入其他项目动态库。

**Why**

此前存在跨项目 `LD_LIBRARY_PATH` 污染导致 GPF 的已知问题。

**Evidence**

已有 `tools/env_cuda.sh` 与前序修复记录。

**Do not revert unless**

迁移至另一套经过验证的隔离运行时。

---

### Decision 7: Pi 是外层工程代理，不等于 Invar 内部确定性核心

[DERIVED]

当前用户已有全局 Pi Agent，并且本地 LLM 已并网。

但是现有 Invar `OpenAICompatibleProvider` 直接访问：

```text
http://127.0.0.1:8080/v1
```

因此不能把：

```text
Global Pi Agent
```

误写成：

```text
Invar Runtime Dependency
```

除非后续真实源码证明 Invar 的运行时调用路径已经通过 Pi。

---

## 12. Data / API / Type Contracts

### `TriageTask`

**Producer**

```text
assemble_triage_tasks.py
```

**Consumer**

```text
run_targeted_audit.py
→ AdaptiveSandboxExecutor
```

**Known fields**

```text
task_id
endpoint_id
priority
hypothesis_id
method
path
attack_class
code_slice
coverage_id
extracted_params
impact_score
pool_origin
profile
sensitivity_score
source_file
source_line
surface_id
```

---

### `CandidateAction`

[FACT]

确定性生成的动作候选。

核心字段：

```text
variant_id
family
method
url
expected_effect
rationale
```

Candidate 不应包含：

```text
真实 credentials
真实 secret
未经验证的任意 HTTP payload
```

---

### `ResearchControlState`

[FACT]

核心状态：

```text
current_status
tried_variants
last_observation_summary
```

用途：

```text
Observation
→ Feedback
→ Next Decision
```

---

### `ControlPlaneDecision`

[FACT]

```text
action:
    RUN_EXPERIMENT
    STOP

target_id:
    Optional[str]

reason:
    bounded string

confidence:
    0..1
```

关键约束：

```text
RUN_EXPERIMENT
    → target_id 必须来自 candidate_ids

STOP
    → target_id 必须为 null
```

---

### `EvidenceVerdict`

[FACT]

系统存在至少以下确权状态：

```text
CONFIRMED
CANDIDATE
INCONCLUSIVE
REJECTED
```

`INCONCLUSIVE` 不等于 `REJECTED`。

---

### OpenVEX Promotion

[FACT]

只有通过 Finding / Verification / Promotion Gate 的结果才可晋级为知识卡片与 OpenVEX 声明。

因此：

```text
findings = 0
openvex statements = 0
```

不能直接推导：

```text
target has no vulnerability
```

只能说明：

```text
本次实验没有产生可晋级的确权发现。
```

---

## 13. Algorithms / Workflow

### Phase 8 Current Workflow

```text
Input
    targeted_research_tasks.json

↓

Select one TriageTask

↓

Resolve EndpointIR

↓

Baseline Probe

↓

Classify Baseline

↓

Generate deterministic CandidateAction set

↓

ResearchController

↓

LLM chooses one bounded action
    OR
deterministic fallback

↓

AdaptiveSandboxExecutor

↓

Real HTTP Observation

↓

SemanticEquivalenceEvaluator

↓

Invariant / Differential Evaluation

↓

Evidence update

↓

Optional next decision

↓

Replay

↓

Independent Verification

↓

Final Verdict

↓

Finding

↓

PromotionGate

↓

OpenVEX / SARIF / Reports
```

### Current Stop Conditions

```text
No valid candidate
→ STOP

Invalid LLM decision
→ fail closed

Decision budget exhausted
→ safe convergence

Evidence insufficient
→ INCONCLUSIVE

Evidence contradicted
→ REJECTED

All confirmation predicates satisfied
→ CONFIRMED
```

---

## 14. Verified Tests

### Test 1 — Phase 8 Entry Preflight

[EXPERIMENT RESULT]

Verified:

```text
Linux Mint 22.3
Python 3.12.3
uv 0.12.21
Node 24.21.0
pnpm 12.8.1
Rust 1.99.0
Cargo 1.99.0
RTX 3060 12GB
```

Phase 7 artifact:

```text
86 tasks
```

AST report:

```text
1097 endpoints
```

Local LLM:

```text
/v1/models
→ Ornith 35B GGUF
```

---

### Test 2 — Phase 8.0 Local Control Plane

[EXPERIMENT RESULT]

Command:

```bash
env -u LD_LIBRARY_PATH \
    PYTHONPATH="/home/zhz/Invar/python/packages/core/src" \
    INVAR_LLM_BASE_URL="http://127.0.0.1:8080/v1" \
    INVAR_LLM_MODEL="/home/zhz/models/Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf" \
    INVAR_LLM_TIMEOUT="30" \
    uv run --project python python tmp/probe_phase8_control_plane.py
```

Result:

```text
PASSED

action = RUN_EXPERIMENT
target_id = SMOKE_A
confidence = 0.7
```

No target request.

No production source change.

---

### Test 3 — Phase 8.1 Real P1 Smoke

[EXPERIMENT RESULT]

Task:

```text
POST /fs/recursive_move
```

Result:

```text
INCONCLUSIVE
attempts = 1
elapsed = 168.8 ms
coverage = 0/1
findings = 0
openvex = 0
```

Interpretation:

```text
System-2 executable path was entered.
Evidence chain did not reach a confirming state.
Root cause is not yet established.
```

---

### Existing Contract Tests

[FACT]

源码中存在以下契约测试集合：

```text
python/tests/test_research_controller.py
python/tests/test_research_agent_contract.py
python/tests/test_coverage_ledger.py
python/tests/test_sandbox_operators_all.py
python/tests/test_semantic_equivalence_contract.py
python/tests/test_idor_compare.py
python/tests/test_endpoint_registry_contract.py
python/tests/test_research_worker.py
python/tests/test_hypothesis_engine.py
```

[UNKNOWN]

当前会话没有执行完整 `uv run pytest`，因此不能将上述测试写成当前会话“全绿”。

---

## 15. Failure / Pitfall Registry

### Problem 1 — `jq 'length'` 误判任务数量

**Symptom**

```text
jq 'length'
→ 8
```

**Root Cause**

`targeted_research_tasks.json` 顶层是对象，不是裸任务数组。

**Correct Interpretation**

```text
.total_tasks = 86
.tasks | length = 86
```

**Future Prevention**

以后检查任务总数必须：

```bash
jq '.total_tasks'
```

或者：

```bash
jq '.tasks | length'
```

---

### Problem 2 — standalone probe import failure

**Symptom**

```text
ModuleNotFoundError: No module named 'agent'
```

**Root Cause**

`pytest` 的 `pythonpath` 配置不会自动作用于直接执行的独立脚本。

**Correct Fix**

使用：

```text
PYTHONPATH=/home/zhz/Invar/python/packages/core/src
```

然后：

```text
uv run --project python python ...
```

**Future Prevention**

任何 `tmp/*.py` 独立探针必须显式建立源码导入路径。

---

### Problem 3 — LLM model env unset

**Symptom**

最初环境：

```text
INVAR_LLM_MODEL=<unset>
```

**Root Cause**

`OpenAICompatibleProvider` 在没有显式 model 时使用：

```text
default
```

而本地 llama-server 实际暴露的是完整 GGUF model ID。

**Correct Fix**

实际运行前显式设置：

```bash
export INVAR_LLM_BASE_URL="http://127.0.0.1:8080/v1"
export INVAR_LLM_MODEL="/home/zhz/models/Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf"
export INVAR_LLM_TIMEOUT="120"
```

---

### Problem 4 — AST report vs EndpointRegistry count mismatch

**Observed**

```text
AST report:
1097 endpoints

Phase 8 runtime:
437 AST endpoints loaded into registry
```

**Root Cause**

UNKNOWN.

**Do Not Guess**

可能涉及：

```text
registry filtering
endpoint canonicalization
task/report resolution
duplicate collapse
report-reader behavior
```

但没有源码执行证据前不得选择任何一个作为根因。

**Next Verification**

检查 `EndpointRegistry` 装载过程以及 Phase 8 runtime 的 registry filtering / canonical resolution。

---

### Problem 5 — current `INCONCLUSIVE`

**Symptom**

```text
POST /fs/recursive_move
→ INCONCLUSIVE
```

**Root Cause**

UNKNOWN.

**Known**

```text
1 attempt
168.8 ms
coverage 0/1
no finding
no OpenVEX statement
```

**Unknown**

```text
baseline status
candidate selected
probe response
semantic verdict
evidence predicate
replay status
verification status
control-plane event sequence
```

**Correct Next Step**

只读检查：

```text
execution.jsonl
audit_checkpoint.json
findings.json
NEEDS-VALIDATION.md
coverage-summary.md
```

---

### Problem 6 — Snapshot configuration conflict

**Observed in Repomix snapshot**

`python/pyproject.toml` contains:

```text
onnxruntime-gpu>=1.20.0,<1.21.0
```

while historical Handoff states:

```text
onnxruntime-gpu==1.19.2
```

**Status**

[UNKNOWN]

The uploaded Repomix snapshot may predate subsequent live edits.

**Do Not Guess**

The live repository must be inspected before any dependency change.

---

### Problem 7 — Windows historical material

部分历史文档仍然存在旧 Windows 路径与旧命令示例。

**Rule**

当前 canonical environment is Linux Mint 22.3.

新 AI 不得直接复制历史 Windows commands into the current workflow.

---

## 16. Do Not Repeat

```text
不要猜 EndpointRegistry 行为

不要猜 INCONCLUSIVE 根因

不要把 1097 与 437 的差异直接解释为 bug

不要把 INCONCLUSIVE 当 REJECTED

不要把 findings=0 当成“没有漏洞”

不要把 openvex=0 当成“目标安全”

不要忘记显式设置 INVAR_LLM_MODEL

不要把 Global Pi Agent 当成 Invar runtime dependency

不要把 86 tasks 一次性发送给 LLM

不要在未读取 execution.jsonl 前修改多个模块

不要直接重新跑 86 个任务

不要使用 --restart 覆盖第一次实验状态

不要升级 ONNX Runtime

不要升级 CUDA

不要使用系统 Python

不要使用 pip

不要使用 python -c

不要让 tmp 探针成为生产运行时依赖

不要修改 Repomix 交接包代替真实源码

不要跳过测试契约

不要为了通过测试删除已有测试

不要为了单个样本添加第二个特判分支
```

---

## 17. Invariants

### Directory Invariant

```text
python/
    AI / ML / Research

crates/
    Rust core

apps/
    UI / Tauri

node/
    Agent / CLI

tmp/
    temporary diagnosis only
```

---

### Environment Invariant

```text
uv only
no system pip
no global virtualenv
```

---

### Decision Invariant

```text
LLM
→ bounded action selection

never

LLM
→ arbitrary HTTP execution
```

---

### Execution Invariant

```text
Sandbox
→ deterministic physical execution
```

---

### Evidence Invariant

```text
No evidence
→ no confirmation
```

---

### Promotion Invariant

```text
No independent verification
→ no CONFIRMED promotion
```

---

### Reporting Invariant

```text
SARIF / OpenVEX
→ derived from authoritative fact objects
```

---

### Collaboration Invariant

```text
One interaction
→ one atomic action
→ user executes
→ user returns log
→ next action based on evidence
```

---

## 18. Open Issues

### OI-01 — Phase 8.1 `INCONCLUSIVE`

**Impact**

当前无法证明真实动态实验闭环已经成功。

**Current Evidence**

```text
1 task
1 attempt
INCONCLUSIVE
coverage 0/1
```

**Known**

System-2 path executed.

**Unknown**

Exact evidence predicate that stopped promotion.

**Next Verification**

Read `execution.jsonl` and related artifacts.

---

### OI-02 — Registry count mismatch

**Impact**

可能影响 Phase 8 endpoint resolution / coverage semantics。

**Known**

```text
AST report = 1097
Registry runtime load = 437
```

**Unknown**

Whether difference is intentional filtering, canonicalization, deduplication, or defect.

**Next Verification**

Trace `EndpointRegistry.register_all()` and Phase 8 registry loading.

---

### OI-03 — Full LLM long-run stability

**Impact**

86-task continuous execution has not yet been validated.

**Known**

Single real task reached a deterministic final result.

**Unknown**

```text
long-horizon context stability
finish_reason behavior
repeated reasoning quality
decision budget behavior
```

**Next Verification**

Only after OI-01 is understood and one-task behavior is stable.

---

### OI-04 — Current post-smoke Git state

**Status**

UNKNOWN.

The only captured Git status is the pre-Smoke state:

```text
main...origin/main
clean
```

Temporary probes and Phase 8 artifacts were generated afterward.

**Next Verification**

Read-only `git status --short`.

---

## 19. Environment / Toolchain

```text
OS:
    Linux Mint 22.3

CPU:
    Intel Core i5-13600KF

RAM:
    32GB

GPU:
    NVIDIA GeForce RTX 3060 12GB

NVIDIA Driver:
    595.91.07

Python:
    3.12.3

uv:
    0.12.21

Node.js:
    24.21.0

pnpm:
    12.8.1

Rust:
    1.99.0

Cargo:
    1.99.0

CUDA:
    CUDA 12 runtime topology

ONNX Runtime:
    Historical Handoff claims 1.19.2
    Current live version must be re-verified before dependency work

Local LLM:
    llama-server

LLM Endpoint:
    http://127.0.0.1:8080/v1

LLM Model:
    /home/zhz/models/Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf

LLM Quantization:
    Q4_K - Medium

LLM Parameters:
    35.505B

LLM Runtime Context:
    160000

Required runtime variables:
    INVAR_LLM_BASE_URL
    INVAR_LLM_MODEL
    INVAR_LLM_TIMEOUT

CUDA isolation:
    source tools/env_cuda.sh

Python execution:
    uv run --project python python ...

Tests:
    uv run pytest
```

---

## 20. Roadmap

```text
Phase 0
    environment / scope initialization
    ✅ COMPLETE

Phase 1-3
    asset acquisition / web mapping / JS acquisition
    ✅ COMPLETE

Phase 4
    AST endpoint extraction
    ✅ COMPLETE

Phase 5
    System-1 inference
    ✅ COMPLETE

Phase 6
    Rule ∪ Neural dual-track
    ✅ COMPLETE

Phase 7
    Research Seed Inventory
    ✅ COMPLETE

Phase 8.0
    Local LLM + Control Plane contract
    ✅ COMPLETE

Phase 8.1
    First real single-task dynamic smoke
    ⚠ PARTIAL / INCONCLUSIVE

Phase 8.2
    Resolve INCONCLUSIVE root cause
    ⏳ FUTURE

Phase 8.3
    Re-run one validated task
    ⏳ FUTURE

Phase 8.4
    Small controlled P1 batch
    ⏳ FUTURE

Phase 8.5
    Full 86-task dynamic validation
    ⏳ FUTURE

Phase 9
    Human review / authorized submission
    ⏳ FUTURE

Phase 10
    Tauri + React product presentation
    ⏳ FUTURE
```

Roadmap does not authorize skipping `CURRENT OBJECTIVE`.

---

## 21. Recovery Protocol

新 AI 接手后必须严格执行：

```text
1. Read HANDOFF.md

2. Read relevant source files:
   - run_targeted_audit.py
   - research_agent.py
   - research_controller.py
   - sandbox_executor.py
   - evidence / verification modules

3. Read the Phase 8 smoke artifacts

4. Verify the Last Known Good State

5. Verify current objective

6. Check for source / HANDOFF drift

7. Execute ONLY:
   NEXT SINGLE ACTION
```

冲突处理：

```text
HANDOFF vs source
    → newer verifiable source / runtime evidence wins

HANDOFF vs test
    → latest real test evidence wins

source vs runtime
    → inspect exact execution context before choosing

insufficient evidence
    → UNKNOWN
```

禁止：

```text
guess
```

---

## 22. AI Collaboration Protocol

```text
Language:
    Chinese first

Execution model:
    one atomic action per turn

User role:
    executes command in terminal or Pi Agent

AI role:
    analyzes returned logs and produces the next action

Default delivery:
    complete Bash command
    OR
    complete Pi Agent prompt

Never:
    assume command succeeded

Never:
    ask for manual file editing

Never:
    output python -c

Never:
    silently modify multiple modules in one phase

Debugging:
    reproduce
    → identify root cause
    → minimal correction
    → verify
    → continue
```

### Current Pi Collaboration Boundary

[FACT]

The user has a global Pi Agent with local LLM connectivity.

[DERIVED]

Pi should currently be treated as:

```text
outer engineering / development agent
```

while Invar remains:

```text
deterministic research / execution / evidence core
```

Do not merge these responsibilities without new architecture evidence.

---

## 23. Security / Sensitive Data Boundary

不得写入本文件：

```text
真实 Token
真实 Cookie
真实 Password
真实 Private Key
真实 Authorization header
无必要个人信息
```

本项目运行时凭据应使用：

```text
environment variable
redacted
fixture
mock
```

当前真实 LLM endpoint：

```text
localhost only
```

本 HANDOFF 不保存任何真实认证 Secret。

当前研究目标必须遵守既有授权范围。

---

## 24. Reproducibility Status

### CONDITIONAL REPRODUCIBLE

理由：

```text
✅ Linux Mint 22.3 environment established
✅ uv / Node / Rust / GPU runtime established
✅ Phase 0~7 re-executed successfully
✅ 86 task inventory confirmed
✅ local LLM endpoint confirmed
✅ Control Plane real-model probe passed
✅ first real Phase 8 task executed

BUT

⚠ Phase 8 evidence chain is not yet fully closed
⚠ First real task ended INCONCLUSIVE
⚠ 1097 AST vs 437 registry count requires verification
⚠ live ONNX Runtime version needs direct re-verification before dependency changes
⚠ post-Smoke Git state was not captured
```

因此不得写：

```text
FULLY REPRODUCIBLE
```

直到上述关键未知项被重新验证。

---

## 25. Handoff Self-Check

```text
[x] 新 AI 知道当前项目是什么
[x] 新 AI 知道当前运行环境
[x] 新 AI 知道 Phase 0~7 已完成
[x] 新 AI 知道 86 个任务仍然是研究输入
[x] 新 AI 知道 Phase 8.0 Control Plane 已通过
[x] 新 AI 知道 Phase 8.1 当前为 INCONCLUSIVE
[x] 新 AI 不会把 INCONCLUSIVE 当成无漏洞
[x] 新 AI 知道当前唯一下一动作
[x] 新 AI 知道为什么不能直接继续全量运行
[x] 新 AI 知道关键架构边界
[x] 新 AI 知道当前 LLM 的真实 model id
[x] 新 AI 知道 Python / CUDA 运行要求
[x] 新 AI 知道历史 Windows 内容不能直接照搬
[x] 新 AI 知道 1097 / 437 mismatch 是 UNKNOWN
[x] 新 AI 知道当前 ONNX Runtime 版本存在快照冲突，需要重新验证
[x] 新 AI 知道如何处理 HANDOFF / source / test 冲突
[x] 新 AI 知道当前协作模式是“用户执行 → 返回日志 → AI 下一步”
[x] 新 AI 知道 tmp 探针不是生产运行时依赖
[x] 新 AI 知道不能一次推进多个未经验证的修改阶段
```

---

# State Recovery Summary

```text
PROJECT
    Invar

ENVIRONMENT
    Linux Mint 22.3
    RTX 3060 12GB
    uv / Python / Node / pnpm / Rust ready

STATIC PIPELINE
    Phase 0~7 ✅

TASK INVENTORY
    86 tasks
    P1 9
    P2 54
    P3 23

LOCAL LLM
    Ornith 1.5 35B GGUF
    /v1 online ✅

CONTROL PLANE
    real local LLM probe ✅

REAL DYNAMIC TEST
    1 × P1
    POST /fs/recursive_move
    INCONCLUSIVE ⚠

CURRENT OBJECTIVE
    diagnose current INCONCLUSIVE

NEXT SINGLE ACTION
    read Phase 8.1 execution artifacts

DO NOT
    rerun 86 tasks
    modify multiple modules
    upgrade CUDA / ONNX
    touch UI / Rust
    guess root cause
```

