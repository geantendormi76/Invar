# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot / Recovery Contract  
> **Project:** Invar  
> **Snapshot Date:** 2026-09-30  
> **Snapshot Time:** 18:46 +08:00 (conversation-local timestamp; exact repository inspection time is UNKNOWN)  
> **Canonical Repository Root:** `C:\dev\Invar`  
> **Canonical Handoff Path:** `C:\dev\Invar\HANDOFF.md`  
> **Snapshot Authority:** latest available source/test/config/runtime evidence in the current conversation and accessible project records; current local worktree itself is not directly mounted in this AI session.

---

## 0. Handoff Metadata

| Item | Value | Level | Evidence / Note |
|---|---|---|---|
| Project | Invar | [FACT] | Repository root is `C:\dev\Invar`. |
| Primary role | System-2 深度动态实证 / 安全研究 Harness | [FACT] | Established project architecture and current Stage-8 execution flow. |
| Active target | `ikuai8.com` | [FACT] | Project target scope entry is `data\targets\ikuai8.com\scope.txt`. |
| Current stage | Phase 8 / Stage 8 — System-2 targeted dynamic research | [FACT] | Stages 3–7 artifacts and Stage-8 P0 execution are evidenced. |
| Current objective | 修正并验证 `run_targeted_audit.py` 的 Coverage Unit 聚合语义，使多 task 共享同一 `coverage_id` 时按“全部计划 task 完成后再最终裁决”收敛 | [DECISION] | This supersedes the older Pi Runtime R1-0 objective. |
| Current next action | 只验证当前 `run_targeted_audit.py` Coverage 聚合修复：查看最新 diff + 运行最小覆盖聚合契约测试 + `git diff --check`，不得进入真实 P0 重跑 | [TODO] | Exact latest implementation result has not yet been returned in the available record. |
| Latest Provider verification | 11 passed in 0.12s | [FACT, 2026-09-30] | Latest available Provider-specific verification after the `finish_reason=length` fix. |
| Latest P0 real run | 10 tasks / 6 coverage units / 1 covered / 5 blocked / 0 findings | [FACT, 2026-09-30] | Existing production audit output. |
| Latest P0 coverage | 16.67% | [FACT, 2026-09-30] | Consistent with checkpoint metrics; known to be distorted by runner aggregation bug. |
| Vulnerability findings | 0 | [FACT, 2026-09-30] | No task reached `decision.status == vulnerable` in that run. |
| Current branch | UNKNOWN | [UNKNOWN] | No direct live Git worktree in this AI session. |
| Current commit | UNKNOWN | [UNKNOWN] | Must be verified locally. |
| Current worktree | UNKNOWN | [UNKNOWN] | Historical Git snapshots exist but are not current authority. |
| Current full-suite result | UNKNOWN | [UNKNOWN] | Historical 207 Python + 15 Rust exists; not rerun after latest modifications. |
| Old Pi R1-0 objective | SUPERSEDED | [DECISION] | Earlier handoff focused on direct Pi Runtime API identity; latest work has moved back to Stage-8 audit correctness. |

---

## 1. Project Identity

### 1.1 System Role

[FACT]

Invar is the current System-2 research and dynamic evidence engine in a broader AI engineering / security research stack.

The implemented security evidence chain is:

```text
Asset / Source / Endpoint IR
        ↓
Research Seed / Hypothesis
        ↓
Controlled Dynamic Execution
        ↓
Observation
        ↓
Invariant / Semantic Evaluation
        ↓
Evidence / Execution Trace
        ↓
Independent Verification
        ↓
Finding / Knowledge
        ↓
SARIF / OpenVEX / Markdown
```

### 1.2 Engineering Constitution

[DECISION]

The project follows these engineering rules:

```text
有依据才实现
有抽象才扩展
有测试才交付
零臆造
根因优先于补丁
目录 / 类型 / 接口视为边界
一次只推进一个逻辑动作
```

Temporary archaeology belongs under `tmp/`.

Normal engineering checks should not use long inline `python -c` commands.

---

## 2. Current Mission

[DECISION]

The long-term mission is:

> 建立一个由 AI 研究控制层驱动、由确定性安全核心执行和裁决、由证据与独立验证最终闭环的 Invar 真实漏洞研究系统，并完成第一次可复现的真实漏洞研究闭环。

Current implemented capability is not yet the full intended autonomous research control plane.

The current effective path is:

```text
Static / Seeded Research Inputs
        ↓
System-1 triage
        ↓
Targeted Research Tasks
        ↓
System-2 AdaptiveSandboxExecutor
        ↓
ResearchAgent / ResearchLoop
        ↓
Deterministic evaluation
        ↓
Optional LLM reflection fallback
        ↓
Evidence / Trace
        ↓
Reporting / Promotion
```

The project must not be reinterpreted as “an LLM scans code and declares vulnerabilities.”

---

## 3. Current Objective

### CURRENT OBJECTIVE

[DECISION]

> **修正并验证 `python/scripts/run_targeted_audit.py` 的 Coverage Unit 聚合状态机，使多个 task 共享同一 `coverage_id` 时，runner 不再被第一个 `INCONCLUSIVE`/`BLOCKED` task 锁死，而是累计该 coverage unit 的全部 task 事实，在全部计划 task 完成后再决定 `CANDIDATE` / `BLOCKED` / `COVERED`。**

### Why this is the current objective

[FACT]

The latest real P0 execution demonstrated a reproducible runner defect:

```text
api-authConf
    task 1: saveAuth
        finish_reason=length
        → inconclusive
        → unit becomes BLOCKED

    task 2: saveSmsConf
        confirmed / safe conclusion
        → later result is not incorporated into the blocked unit
```

Likewise:

```text
api-router
    task 1: peripheral
        inconclusive
        → unit becomes BLOCKED

    task 2/3/4:
        safe / REJECTED conclusions
        → later facts are skipped
```

The observed root cause is in `run_targeted_audit.py`:

```python
else:  # decision != vulnerable
    if unit.status == CoverageStatus.IN_PROGRESS:
        ...
```

Once the first task moves the unit to `BLOCKED`, later tasks no longer contribute their facts.

### Correct semantic contract

[DECISION]

For each `coverage_id`, build:

```text
coverage_id
    ├── all planned task keys
    └── all planned unique paths
```

Every task contributes facts independently.

Unit remains:

```text
IN_PROGRESS
```

while planned tasks remain incomplete.

Only after **all tasks belonging to that coverage_id are complete**:

```text
if any vulnerable/candidate evidence:
    → CANDIDATE

elif any unresolved / inconclusive evidence:
    → BLOCKED

else:
    → COVERED
```

This is the authoritative intended semantics for the current runner fix.

---

## 4. Next Single Action

### NEXT SINGLE ACTION

> **只对当前 `run_targeted_audit.py` Coverage 聚合修复执行一次本地验证：检查最新 diff，运行最小覆盖聚合契约测试，并执行 `git diff --check`；不运行真实 P0，不重扫 AST，不修改其他模块。**

### Why this is the only next action

[DERIVED]

The production run already proved the bug. The Provider fix has already been separately verified with 11 passing tests. The remaining uncertainty is whether the runner patch correctly implements the intended aggregation semantics without altering checkpoint, reporting, or security verdict behavior.

### Completion gate for this action

[TODO]

This action is complete only if the returned evidence shows all of the following:

```text
1. Multiple tasks sharing one coverage_id share one CoverageUnit.
2. starting_paths contains all unique paths planned for that coverage_id.
3. Safe + Safe:
       all tasks complete → COVERED
4. Inconclusive + Safe:
       all tasks complete → BLOCKED
       unresolved retained
5. Safe + Inconclusive:
       all tasks complete → BLOCKED
6. Inconclusive + Safe + Safe:
       all tasks complete → BLOCKED
7. Vulnerable + Safe:
       all tasks complete → CANDIDATE
8. A prior BLOCKED/CANDIDATE unit with remaining tasks can reopen to IN_PROGRESS.
9. Reopening does not silently erase prior unresolved facts or candidate evidence.
10. No changes to checkpoint schema or completed task keys.
11. `git diff --check` is clean.
```

Until these conditions are verified, do not start a new real audit run.

---

## 5. Current Scope

### 5.1 In Scope

[DECISION]

Primary file:

```text
python/scripts/run_targeted_audit.py
```

Best-fit existing tests:

```text
existing Python test suite under `python/tests/`
```

The exact current runner test file is:

[UNKNOWN]

> The latest implementation result identifying the exact chosen test file has not yet been returned.

Current semantic boundaries:

```text
CoverageLedger state
        ↓
runner task aggregation
        ↓
CoverageUnit facts
        ↓
Coverage status finalization
        ↓
checkpoint/report compatibility
```

### 5.2 Supporting, Already-Verified Area

[FACT]

The following areas are upstream/downstream context, not current edit targets:

```text
python/packages/core/src/agent/model_provider.py
python/packages/core/src/harness/coverage_ledger.py
python/packages/core/src/harness/audit_checkpoint.py
python/packages/core/src/harness/research_loop.py
python/packages/core/src/harness/sandbox_executor.py
python/packages/core/src/harness/transport.py
python/packages/core/src/harness/invariant_evaluator.py
python/packages/core/src/harness/finding_models.py
python/packages/core/src/harness/reporting.py
python/packages/core/src/agent/knowledge_promoter.py
```

They should remain unchanged during the current runner-only fix unless a new concrete source/test failure proves otherwise.

---

## 6. Out of Scope

[DECISION]

Do not touch during the current objective:

```text
AST full rerun
Asset rediscovery / subdomain collection
EndpointIR redesign
EndpointRegistry redesign
Mutation-family redesign
ResearchLoop architecture rewrite
Transport rewrite
Sandbox rewrite
Finding / Verification / Promotion redesign
Reporting / SARIF / OpenVEX redesign
Pi Runtime integration work
Skill work
React / Tauri / Desktop UI
Temporal
PostgreSQL / pgvector
LATS / MCTS
New orchestration infrastructure
Large-scale directory refactor
Unrelated technical debt
Non-authorized target expansion
```

Do not reopen the older Pi R1-0 architecture task unless the current runner work is complete and the roadmap explicitly advances there.

---

## 7. Last Known Good State

### 7.1 Latest Verified Provider State

[FACT, 2026-09-30]

Latest available focused verification:

```powershell
uv run --project python pytest python/tests/test_model_provider.py
```

Result:

```text
11 passed in 0.12s
```

Behavior locked by that work:

```text
finish_reason == "stop"
    → normal structured JSON parse

finish_reason == "length"
    → direct parse
    → one continuation only when truly incomplete
    → no bracket repair
    → no guessed fields
    → no infinite retries

other finish_reason
    → immediate provider failure
```

`git diff --check` was reported clean after the Provider fix.

### 7.2 Latest Real P0 Run

[FACT, 2026-09-30]

Input:

```text
targeted_research_tasks.json
priority = P0
LLM enabled
LLM timeout = 120s
target request timeout = 10s
```

Output:

```text
artifacts\reports\targeted_audit_production
```

Run summary:

```text
tasks = 10
coverage units = 6
covered = 1
blocked = 5
deferred = 0
coverage = 16.67%
vulnerable tasks = 0
candidate_fingerprints = 0
OpenVEX statements = 0
```

### 7.3 Real P0 Task Outcomes

[FACT]

The latest run had 5 task-level safe/confirmed conclusions and 5 unresolved/inconclusive task results.

Safe/confirmed:

```text
authConf/saveSmsConf
router/switch
router/remote_control × 2
password_reset
```

Unresolved/inconclusive:

```text
delegate/grant
authConf/saveAuth
router/peripheral
bind_recharge
users/reset-password
```

Important semantic note:

```text
CONFIRMED / REJECTED in the research report
≠ a vulnerability finding
```

A vulnerability finding is only created by the runner when:

```text
decision.status == "vulnerable"
```

### 7.4 Latest Engineering Baseline

[FACT, HISTORICAL — not current]

```text
Python: 207 passed
Rust:   15 passed
Total:  222 / 222
```

Canonical commands:

```powershell
uv run --project python pytest
cargo test --workspace
```

These must not be re-labelled as the current green baseline until rerun against the current worktree.

### 7.5 Current Worktree State

[UNKNOWN]

Not directly inspectable in the current AI session.

Must be established locally before claiming:

```text
current branch
current commit
current modified files
current deleted files
current untracked files
current diff cleanliness
```

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| Stage 3 JS materialization | DONE | `tmp/raw_js` exists | `python/scripts/download_javascript.py` + artifacts | Current target asset was materialized. |
| Stage 4 AST endpoint extraction | DONE | `tmp/ikuai8_endpoints_report.json` exists; 443 unique surface-like endpoints reported | AST / scan pipeline | Report is existing evidence, not a reason to rerun AST now. |
| Stage 5 System-1 ONNX triage | DONE | 1232/1232 endpoint outputs | `python/scripts/predict_triage_onnx.py` | Explicit model dir `models/invar-intent-0.6b-v1` used. |
| Stage 6 dual-track comparator | DONE | 443 surfaces; 1232 aligned; 1225 usable; 7 fallback; pools A/B/C = 56/30/30 | `python/scripts/triage_dual_track_comparator.py` | Evidence exists for current task assembly. |
| Stage 7 task assembly | DONE | 86 tasks: P0=10, P1=35, P2=35, P3=6 | `artifacts/reports/targeted_research_tasks.json` | Current P0 run uses the P0 subset. |
| Stage 8 initial P0 real run | DONE / BLOCKED | 10 tasks, 6 units, 1 covered, 5 blocked | `artifacts/reports/targeted_audit_production` | Proved runner aggregation defect. |
| Provider `finish_reason=length` recovery | DONE | 11 Provider tests passed | `model_provider.py`, `test_model_provider.py` | One continuation max; no repair/guessing. |
| Coverage aggregation fix | PARTIAL / UNVERIFIED | Implementation prompt issued; latest result not yet returned | `run_targeted_audit.py` + existing best-fit test | Must be verified before any retry run. |
| First confirmed vulnerability | TODO | None | — | Not yet produced. |
| First end-to-end Knowledge feedback loop | TODO | Not proven | `knowledge_promoter.py` and future planner boundary | Do not claim implemented. |

---

## 9. Changed Files

### 9.1 Added

[UNKNOWN — current Git state]

No reliable current `git status` is available.

Known workstream additions from historical evidence include:

```text
python/tests/test_model_provider.py
```

but the exact distinction between newly added vs previously existing in the current branch is not established by the available snapshot.

### 9.2 Modified

[FACT, workstream history; NOT a current Git status]

Files touched or explicitly involved across the current engineering slice include:

```text
python/packages/core/src/agent/model_provider.py
python/tests/test_model_provider.py
python/scripts/run_targeted_audit.py
configs/base/project.toml
configs/profiles/production.toml
configs/profiles/research.toml
python/packages/core/src/harness/run_models.py
python/packages/core/src/harness/__init__.py
```

Only the following are current-objective files:

```text
python/scripts/run_targeted_audit.py
chosen existing runner-focused test file
```

### 9.3 Deleted

[UNKNOWN]

Historical worktree snapshots showed at least one deleted Butian-related Markdown document, but its current status must not be assumed.

### 9.4 Moved

[UNKNOWN]

No trustworthy current move/rename record is available.

### 9.5 Structure

[INVARIANT]

The project uses directory boundaries:

```text
apps/                  UI / Tauri surface
crates/                Rust
python/                Python production / research / tests
configs/               configuration
data/                  target data
models/                model assets
artifacts/             reports / research outputs
docs/                  engineering / research docs
tmp/                   temporary verification / archaeology
node/                  Node / harness tooling when present
```

Do not casually move code across these boundaries.

---

## 10. Current Architecture

### 10.1 Implemented Pipeline

[FACT]

```text
Target Scope
    ↓
Passive / HTTP Asset Collection
    ↓
JavaScript Materialization
    ↓
AST Endpoint Extraction
    ↓
System-1 0.6B Triage
    ↓
Dual-Track Comparator
    ↓
Research Task Assembly
    ↓
System-2 Targeted Audit
    ↓
EndpointRegistry
    ↓
AdaptiveSandboxExecutor
    ├── Transport
    ├── Transformation / Mutation
    ├── Denial Classification
    ├── Adaptive Selector
    └── ResearchAgent / ResearchLoop
    ↓
Invariant / Semantic Evaluation
    ↓
Execution Trace / Evidence
    ↓
Independent Verification
    ↓
Promotion Gate
    ↓
Finding / Knowledge
    ↓
SARIF / OpenVEX / Markdown
```

### 10.2 Current Runtime Split

[FACT / DERIVED]

```text
Pi / local AI runtime
    = generic agent runtime environment

Invar
    = security research control + deterministic execution / evaluation
```

The previous R1-0 Pi Runtime study established that Pi and llama-server exist locally, but this is no longer the current execution objective.

### 10.3 Important Boundary

[INVARIANT]

The LLM may:

```text
propose
reflect
generate a candidate mutation
suggest a next research action
```

The LLM may not directly manufacture:

```text
CONFIRMED Finding
```

Deterministic execution and independent verification remain authoritative.

---

## 11. Architecture Decisions

### AD-01 — Deterministic Core Retains Security Authority

**Decision**

[DECISION]

Security-sensitive truth remains in deterministic components:

```text
transport
execution
observation
semantic / invariant evaluation
evidence recording
independent verification
promotion gate
```

**Why**

Prevents model prose from becoming security fact.

**Alternatives rejected**

Treating LLM output itself as final verdict.

**Evidence**

Existing provider, research loop, evidence, verification and promotion contracts; current P0 run also showed that LLM failures become inconclusive rather than findings.

**Do not revert unless**

A new source-backed architecture change explicitly changes security authority and adds corresponding tests.

---

### AD-02 — Coverage Is a Unit-Level Aggregate, Not a First-Task Status

**Decision**

[DECISION]

A `CoverageUnit` represents the aggregate research state for all planned tasks sharing the same `coverage_id`.

**Why**

The latest P0 run proved that first-task locking produces false under-reporting and discards later useful task-level conclusions.

**Correct rule**

```text
planned tasks for coverage_id
        ↓
independent task facts
        ↓
aggregate
        ↓
all tasks complete?
    ├─ NO → IN_PROGRESS
    └─ YES
         ├─ any vulnerable → CANDIDATE
         ├─ else any unresolved → BLOCKED
         └─ else → COVERED
```

**Alternatives rejected**

“Reopen BLOCKED and immediately mark COVERED when the latest task is safe.”

That is insufficient because earlier unresolved tasks may still exist.

**Do not revert unless**

A stronger coverage model explicitly records all task-level completion and derives an equivalent aggregate semantics.

---

### AD-03 — `starting_paths` Must Represent the Coverage Plan

**Decision**

[DECISION]

When a CoverageUnit is created for a `coverage_id`, `starting_paths` must contain all unique planned paths for that coverage unit in the current filtered task plan.

**Why**

Canonical ledger planning groups paths at unit level. Creating the unit with only the current task path loses the coverage plan.

**Do not revert unless**

The coverage plan itself changes to task-level units.

---

### AD-04 — One-Step Engineering Rule

**Decision**

[DECISION]

One round should advance one logical engineering action.

**Why**

Reduces multi-module debugging ambiguity and prevents speculative refactors.

---

### AD-05 — Do Not Import Heavy Orchestration Infrastructure Without Need

**Decision**

[DECISION]

Temporal, PostgreSQL/pgvector, LATS/MCTS and large new orchestration components remain deferred until a concrete Invar contract and evidence-backed need exists.

---

### AD-06 — Headless Mainline

**Decision**

[DECISION]

The research mainline remains headless. Desktop UI is not part of current research execution.

---

## 12. Data / API / Type Contracts

### 12.1 `EndpointIR`

[FACT]

Known core fields:

```text
method
path
endpoint_id
source_file
line
is_dynamic
extracted_params
tags
risk_score
confidence
call_signature
```

Canonical endpoint identity is method + path, with HTTP method normalization.

### 12.2 `EndpointRegistry`

[FACT]

Core operations:

```text
register
register_all
get
contains
to_list
```

Missing canonical endpoint references should fail explicitly.

---

### 12.3 `CoverageUnit`

[FACT]

Known fields:

```text
coverage_id
surface
boundary
subsystem
attack_class
starting_paths
status
owner_agent_id
reviewed_paths
check_refs
candidate_fingerprints
unresolved
prior_refs
weight
```

Current relevant states:

```text
PLANNED
IN_PROGRESS
COVERED
CANDIDATE
BLOCKED
DEFERRED
OUT_OF_SCOPE
```

### 12.4 Coverage State Transitions

[FACT]

Known transition capability includes:

```text
PLANNED      → IN_PROGRESS / DEFERRED / OUT_OF_SCOPE
IN_PROGRESS  → COVERED / CANDIDATE / BLOCKED / PLANNED
BLOCKED      → IN_PROGRESS / DEFERRED
COVERED      → IN_PROGRESS
CANDIDATE    → IN_PROGRESS
OUT_OF_SCOPE → no normal transition
```

Important:

> The ledger already exposes a `BLOCKED → IN_PROGRESS` recovery path. The latest defect is that the runner did not use the available capability correctly.

### 12.5 `ResearchScope`

[FACT]

Known fields:

```text
target_domain
included_subdomains
excluded_paths
allowed_methods
authorization_boundary
```

Authorized dynamic execution is represented by:

```text
AUTHORIZED_ENGAGEMENT_ONLY
```

### 12.6 `ResearchRun`

[FACT]

Core fields include:

```text
run_id
target_root
scope
source_ref
repository
raw_js_hash
profile
execution_policy
budget
status
started_at
completed_at
coverage_ledger_ref
findings_ref
prior_run_refs
block_reason
metadata
track
```

Track values known:

```text
PRODUCTION
RESEARCH
INTELLIGENCE
BENCHMARK
```

### 12.7 `ResearchLoopConfig`

[FACT]

Known relevant values:

```text
max_turns = 12
max_budget = 12
queue_mode = ONE_AT_A_TIME
steering_queue
follow_up_queue
selector
evaluator
expected_resource_markers
public_root_preview
llm_provider
```

### 12.8 `OpenAICompatibleProvider`

[FACT]

Relevant defaults / behavior:

```text
base_url:
    INVAR_LLM_BASE_URL
    else OPENAI_BASE_URL
    else http://127.0.0.1:8080/v1

api_key:
    INVAR_LLM_API_KEY
    else OPENAI_API_KEY
    else not-needed

model:
    INVAR_LLM_MODEL
    else default

timeout:
    INVAR_LLM_TIMEOUT
    else 120
```

Requests are sent to:

```text
{base_url}/chat/completions
```

### 12.9 Current Provider Failure Handling Contract

[FACT, after latest fix]

```text
stop
    → normal structured JSON parse

length
    → direct parse
    → one continuation only when truly incomplete
    → reparse strictly
    → safe provider failure if still invalid

other finish_reason
    → immediate provider failure
```

Forbidden behavior:

```text
bracket repair
field guessing
infinite retries
silently accepting unrelated finish reasons
```

---

## 13. Algorithms / Workflow

### 13.1 Current System-2 Workflow

[FACT]

```text
Task
  ↓
Resolve EndpointIR from EndpointRegistry
  ↓
Create / locate CoverageUnit
  ↓
Baseline observation
  ↓
Deterministic denial classification
  ↓
Mutation / transformation selection
  ↓
Dynamic probe
  ↓
Invariant / semantic evaluation
  ↓
Optional ResearchLoop / LLM fallback
  ↓
Evidence + trace
  ↓
Task-level decision
  ↓
CoverageUnit aggregate update
```

### 13.2 Current Coverage Aggregation Contract

[DECISION]

For a filtered task plan:

```text
coverage_id
    ↓
planned_task_keys = all task keys in that coverage
planned_paths      = all unique paths in that coverage
```

Per task:

```text
safe / confirmed
    → reviewed_paths
    → check_refs

inconclusive / decision missing / LLM failure
    → unresolved

vulnerable
    → candidate / finding facts
```

Then:

```text
remaining tasks > 0
    → IN_PROGRESS

remaining tasks == 0:
    candidate exists
        → CANDIDATE
    else unresolved exists
        → BLOCKED
    else
        → COVERED
```

### 13.3 Resume Semantics

[DECISION]

If an old checkpoint contains:

```text
BLOCKED
```

or:

```text
CANDIDATE
```

but planned tasks for the unit remain incomplete:

```text
→ reopen to IN_PROGRESS
→ preserve prior unresolved facts
→ preserve candidate evidence
→ process remaining tasks
```

Do not silently clear evidence merely to obtain `COVERED`.

### 13.4 Checkpoint Semantics

[FACT]

Existing checkpoint fields include:

```text
completed_task_keys
last_completed_index
status
run
ledger
findings
plan_digest
```

Current runner behavior skips already completed task keys on resume.

Therefore:

```text
old blocked run
+
same output dir
+
all task keys already completed
```

does not automatically replay all tasks.

### 13.5 Safe Retry Strategy After Current Fix

[TODO]

Use a **new output directory** to preserve the first production run as a baseline.

Preferred conceptual shape:

```text
artifacts/reports/targeted_audit_p0_retry
```

Do not destroy the prior production evidence.

---

## 14. Verified Tests

### 14.1 Provider Contract

[FACT]

```powershell
uv run --project python pytest python/tests/test_model_provider.py
```

Result:

```text
11 passed in 0.12s
```

### 14.2 Historical Full Regression

[FACT, HISTORICAL]

```powershell
uv run --project python pytest
cargo test --workspace
```

Historical result:

```text
Python 207 passed
Rust   15 passed
Combined 222 / 222
```

This is a recovery anchor, not a current green claim.

### 14.3 Track Contract

[FACT, HISTORICAL]

```powershell
uv run --project python pytest python/tests/test_run_track_contract.py python/tests/test_research_run.py
```

Result:

```text
11 passed in 0.05s
```

### 14.4 Existing Important Contract Suites

[FACT]

```text
python/tests/test_research_agent_contract.py
python/tests/test_research_loop_contract.py
python/tests/test_research_loop_integration.py
python/tests/test_research_loop_llm_contract.py
python/tests/test_model_provider.py
python/tests/test_adaptive_sandbox_all.py
python/tests/test_adaptive_selector_contract.py
python/tests/test_invariant_evaluator.py
python/tests/test_evidence_contract.py
python/tests/test_verification_and_promotion_gate.py
python/tests/test_reporting_projections.py
python/tests/test_coverage_ledger.py
```

### 14.5 Required New Runner Tests

[TODO]

The runner-focused test set must cover at least:

```text
safe + safe → COVERED

inconclusive + safe → BLOCKED
safe + inconclusive → BLOCKED

inconclusive + safe + safe → BLOCKED

vulnerable + safe → CANDIDATE

old BLOCKED + remaining task → IN_PROGRESS
```

And must assert:

```text
reviewed_paths
check_refs
unresolved
candidate_fingerprints
starting_paths
remaining task semantics
```

---

## 15. Failure / Pitfall Registry

### FP-01 — Python `httpx` vs ProjectDiscovery `httpx`

**Problem**

Same command name may resolve to the Python CLI instead of ProjectDiscovery.

**Root Cause**

Executable precedence / PATH collision.

**Wrong Approach**

Trust the filename.

**Correct Fix**

Verify executable identity explicitly.

---

### FP-02 — Long JavaScript Context Explosion

**Root Cause**

AST slices became too large for downstream research prompts.

**Correct Fix**

Research `code_slice` has a bounded size; historical contract uses an 800-character ceiling.

---

### FP-03 — Invalid HTTP Methods From Dynamic JS Fragments

**Root Cause**

Unrelated JS tokens were interpreted as HTTP methods.

**Correct Fix**

Normalize to standard HTTP verbs and canonical paths.

---

### FP-04 — Windows Registry Proxy Hang

**Root Cause**

HTTP client inherited Windows proxy configuration and could hang for long periods.

**Correct Fix**

Deterministic transport behavior with local bypass / proxy isolation.

---

### FP-05 — HTTP 200 Treated as Success

**Root Cause**

Transport-level status was confused with business-level authorization outcome.

**Correct Fix**

Interpret business code / response semantics together with HTTP status.

---

### FP-06 — SPA HTML Treated as API Breakthrough

**Root Cause**

SPA / index fallback returned HTTP 200.

**Correct Fix**

HTML fallback and resource-equivalence checks prevent false breakthroughs.

---

### FP-07 — LLM Fallback Short-Circuit

**Root Cause**

A soft-200 / false breakthrough prematurely skipped later reflection.

**Correct Fix**

Breakthrough determination excludes soft denial and SPA fallback.

---

### FP-08 — LLM Mistaken For Whole Research System

**Root Cause**

Model generation capability was conflated with research control architecture.

**Correct Fix**

Keep:

```text
Research Control
+
Deterministic Security Core
```

as separate responsibilities.

---

### FP-09 — String Search Used as Runtime Integration Proof

**Root Cause**

Text matches cannot establish actual package exports or runtime execution identity.

**Correct Fix**

Runtime compatibility must be proven by actual import / require / execution.

---

### FP-10 — Local Pi Extension Lockfile Mistaken For Global Pi Install

**Root Cause**

Local extension workspace and global Pi npm environment were conflated.

**Correct Fix**

Verify local extension workspace, global npm root, and CLI wrapper separately.

---

### FP-11 — PowerShell `$PID` Collision

**Root Cause**

PowerShell reserves `$PID` case-insensitively.

**Correct Fix**

Use names such as `$ownerPid`.

---

### FP-12 — Multi-line PowerShell Pipeline Parser Hazard

**Root Cause**

Interactive multi-line PowerShell syntax can produce parser errors when pasted.

**Correct Fix**

Put complex checking logic into `tmp/check_xxx.py`; PowerShell should mostly launch it.

---

### FP-13 — Provider `finish_reason=length` Hard Failure

**Problem**

Structured output was rejected immediately whenever `finish_reason != stop`.

**Root Cause**

Provider treated any non-stop finish as unrecoverable without first checking whether the returned content was already complete.

**Correct Fix**

For `length`, parse the returned content first; only when incomplete, issue one continuation; fail safely if continuation does not produce a strict object.

**Regression**

11 Provider tests passed after the fix.

---

### FP-14 — Coverage Unit First-Task Locking

**Problem**

A unit became `BLOCKED` after its first inconclusive task and later safe task results were ignored.

**Root Cause**

`run_targeted_audit.py` performed aggregate state transitions inside a branch guarded by:

```python
if unit.status == CoverageStatus.IN_PROGRESS:
```

**Wrong Approach**

Treat the latest safe task as sufficient to reopen and immediately mark the whole unit `COVERED`.

**Correct Fix**

Aggregate all planned task facts and only finalize the unit after all planned tasks finish.

**Regression**

Required tests are listed in Section 14.5 and must be completed before retry.

---

## 16. Do Not Repeat

1. 不要把旧 HANDOFF 的 R1-0 Pi Runtime 目标当成当前目标。
2. 不要把文件名、字符串命中、package-lock 命中当成 runtime integration 证明。
3. 不要把模型可用误写成自主研究控制平面已经完成。
4. 不要把 LLM 输出直接升级为 `CONFIRMED` Finding。
5. 不要把 HTTP 200 当成成功或漏洞条件。
6. 不要把单个 task 的安全结论直接当成整个 shared Coverage Unit 已覆盖。
7. 不要在还有未完成 task 时把 CoverageUnit 提前标记 `COVERED`。
8. 不要清除旧 `unresolved` / candidate facts 来“让状态通过”。
9. 不要修改 `coverage_ledger.py` 仅仅因为 runner 尚未正确使用已有状态转移能力。
10. 不要把历史 Git 状态写成当前 Git 状态。
11. 不要覆盖上一轮真实 P0 产物作为“修复后的对照组”。
12. 不要为了当前 Coverage bug 重写 ResearchLoop、Transport、Sandbox、Reporting 或 Promotion。
13. 不要一次修改多个未验证边界。
14. 不要复制真实 token、cookie、password、private key 或 API secret 到 HANDOFF。
15. 不要使用长 `python -c` 作为本项目常规检查方式。
16. 不要为了“看起来先进”直接引入 Temporal / PostgreSQL / LATS / 新 sandbox 等大型依赖。

---

## 17. Invariants

### 17.1 Engineering Invariants

```text
目录 = 职责边界
类型 = 数据边界
接口 = 模块边界
测试 = 行为契约
事实等级必须明确
历史状态不得冒充当前状态
```

### 17.2 Research Invariants

```text
Observation ≠ Hypothesis
Hypothesis ≠ Finding
Finding ≠ Knowledge
```

Canonical chain:

```text
Observation
→ Hypothesis
→ Evidence
→ Verification
→ Finding
→ Promotion
```

### 17.3 Coverage Invariants

```text
shared coverage_id = one aggregate CoverageUnit

starting_paths = all unique planned paths of that coverage_id

remaining tasks > 0
    → IN_PROGRESS

all tasks complete + candidate
    → CANDIDATE

all tasks complete + unresolved
    → BLOCKED

all tasks complete + no unresolved + no candidate
    → COVERED
```

### 17.4 Security Invariants

```text
Authorization scope is mandatory for dynamic execution.
LLM cannot directly manufacture final security facts.
Independent verification remains separate from original discovery.
Evidence must be tied to real observations.
```

### 17.5 Checkpoint Invariants

```text
completed_task_keys represent physically completed work.
Resume must not claim progress not supported by execution evidence.
New retry runs should preserve prior evidence rather than overwrite it.
```

---

## 18. Open Issues

### OI-01 — Current runner patch not yet verified

**Impact**

Determines whether the coverage under-count is actually fixed.

**Known**

The correct semantic contract is established.

**Unknown**

Whether the latest local implementation precisely satisfies it.

**Next Verification**

Current `NEXT SINGLE ACTION`.

---

### OI-02 — Current Git branch / commit / worktree

**Impact**

Without live Git state, exact current code drift cannot be asserted.

**Known**

Historical `git status` snapshots exist.

**Unknown**

Current branch, HEAD, modified/deleted/untracked files.

**Next Verification**

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

Do not treat these as optional before a final release claim.

---

### OI-03 — Full regression after latest modifications

**Impact**

Provider and runner changes may affect broader tests.

**Known**

Historical full baseline is 222 / 222.

**Unknown**

Current full-suite result after latest changes.

**Next Verification**

After the current runner-focused fix is fully verified, run the appropriate regression slice according to the one-step rule; do not combine it with the current implementation step.

---

### OI-04 — `users/reset-password` remains inconclusive

**Impact**

The latest task returned HTTP 405 and did not close the authorization invariant.

**Known**

LLM output suggested a possible method mismatch hypothesis.

**Unknown**

Whether the endpoint is truly vulnerable.

**Next Verification**

A dedicated, authorized follow-up experiment is required; do not call it safe solely because the task verdict was `REJECTED`.

---

### OI-05 — `delegate/grant`, `router/peripheral`, `bind_recharge` remain unresolved

**Impact**

These tasks currently prevent their coverage units from converging safely.

**Known**

They produced inconclusive outcomes in the first P0 run.

**Unknown**

Whether they are safe, vulnerable, or merely transport / method mismatches.

**Next Verification**

Must happen in a later audit pass after current coverage aggregation correctness is verified.

---

### OI-06 — Checkpoint unresolved de-duplication across reruns

**Impact**

Could affect long-lived blocked state and evidence clarity.

**Known**

Current report showed unresolved facts keyed with task-derived identifiers.

**Unknown**

Whether repeated reruns can accumulate duplicate unresolved facts.

**Next Verification**

Inspect checkpoint restore / merge behavior directly before relying on repeated resume in the same output directory.

---

### OI-07 — 78 vs 86 research seed naming discrepancy

**Impact**

Can confuse future AI about task inventory history.

**Known**

Historical artifact naming contained `78`, while latest task assembly evidence reports 86 tasks.

**Unknown**

Exact reason for the naming discrepancy.

**Next Verification**

Read the seed checker and task JSON directly if this discrepancy becomes relevant to planning.

---

### OI-08 — Real Pi Runtime integration remains unresolved but is not current

**Impact**

Future control-plane architecture.

**Known**

Pi CLI and local llama-server existed in prior verified runtime evidence.

**Unknown**

Full direct Pi Session API compatibility and best minimal integration boundary.

**Next Verification**

Return to runtime contract testing only after the current Stage-8 correctness work is complete.

---

## 19. Environment / Toolchain

| Component | Known State | Level |
|---|---|---|
| OS | Windows | [FACT] |
| Shell | PowerShell | [FACT] |
| Python | 3.12.13 in recent test output | [FACT] |
| Python package manager | `uv` | [FACT] |
| Pytest | 9.1.1 in recent targeted test output | [FACT] |
| Python requirement | `>=3.11,<3.14` | [FACT, project snapshot] |
| Rust | Cargo workspace | [FACT] |
| Rust edition | 2021 | [FACT, historical project state] |
| JS workspace | pnpm workspace | [FACT, project snapshot] |
| Main research mode | Headless | [DECISION] |
| Local LLM provider | OpenAI-compatible | [FACT] |
| LLM endpoint | `http://127.0.0.1:8080/v1` | [FACT] |
| LLM model env used in P0 run | `Qwen3.8-27B-Uncensored` | [FACT, run configuration] |
| LLM timeout | 120s | [FACT, run configuration] |
| Target HTTP timeout | 10s | [FACT, run configuration] |
| Local model family | Qwen3.8-27B Uncensored | [FACT] |
| Quantization | `IQ3_XXS - 3.0625 bpw` | [FACT, runtime snapshot] |
| llama context | 65536 | [FACT, runtime snapshot] |
| Pi configured context | 81920 | [FACT, historical Pi config snapshot] |
| Target authorization | `AUTHORIZED_ENGAGEMENT_ONLY` | [FACT / INVARIANT] |

### Canonical Commands

Python full tests:

```powershell
uv run --project python pytest
```

Rust tests:

```powershell
cargo test --workspace
```

Provider test:

```powershell
uv run --project python pytest python/tests/test_model_provider.py
```

Temporary verification:

```powershell
uv run --project python python tmp/check_xxx.py
```

Git state:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

---

## 20. Roadmap

Roadmap is descriptive only. It does not override `CURRENT OBJECTIVE`.

### Phase A — Current Runner Correctness

**Status:** CURRENT / IN PROGRESS

```text
Coverage aggregation fix
→ targeted tests
→ diff-check
→ controlled P0 retry
→ compare baseline
```

### Phase B — Stable P0 Research Closure

**Status:** TODO

Resolve remaining P0 inconclusive tasks without changing the evidence boundary.

### Phase C — Expand P1 / P2 Research

**Status:** TODO

Only after P0 correctness and resume semantics are trustworthy.

### Phase D — First Verified Vulnerability

**Status:** TODO

Produce:

```text
Observation
→ Evidence
→ Independent Verification
→ FindingRecord
→ PromotionGate
```

### Phase E — Agent-driven Research Control Plane

**Status:** TODO

Move beyond primarily fixed mutation fallback toward explicit goal / hypothesis / planning / state transitions.

### Phase F — Pi Runtime Reuse Boundary

**Status:** TODO / BLOCKED BY PRIOR VERIFICATION

Close the real Pi Session / Skill / Tool boundary using direct runtime evidence.

### Phase G — Knowledge Feedback

**Status:** TODO

```text
Verified Finding
→ Pattern
→ KnowledgeCard
→ Future Research Input
```

### Phase H — Cross-target Generalization

**Status:** TODO

Only after first end-to-end proven research cycle.

---

## 21. Recovery Protocol

A new AI must recover in exactly this order:

```text
1. Read HANDOFF
2. Read real source / current repo tree
3. Read the current runner-focused tests
4. Verify the Last Known Good State
5. Verify CURRENT OBJECTIVE
6. Check Git drift
7. Execute only NEXT SINGLE ACTION
```

### Conflict resolution

If HANDOFF conflicts with source:

```text
latest verifiable source > HANDOFF
```

If HANDOFF conflicts with tests:

```text
latest verifiable tests > HANDOFF
```

If information is missing:

```text
UNKNOWN
```

Never repair uncertainty with intuition.

### Current recovery focus

Read first:

```text
python/scripts/run_targeted_audit.py
python/packages/core/src/harness/coverage_ledger.py
python/packages/core/src/harness/audit_checkpoint.py
python/tests/test_coverage_ledger.py
chosen runner-focused tests
python/packages/core/src/agent/model_provider.py
python/tests/test_model_provider.py
```

Then inspect actual current Git state.

---

## 22. AI Collaboration Protocol

### 22.1 Language

[DECISION]

Default language:

```text
中文
```

Keep real identifiers / symbols / paths in their original form.

### 22.2 One-Step Rule

[DECISION]

```text
一个会话轮次
    ↓
一个明确工程动作
    ↓
用户执行
    ↓
返回真实输出
    ↓
下一动作
```

### 22.3 Evidence Discipline

Always use:

```text
[FACT]
[DECISION]
[DERIVED]
[ASSUMPTION]
[UNKNOWN]
[TODO]
```

Never convert:

```text
TODO → DONE
DERIVED → FACT
ASSUMPTION → FACT
historical snapshot → current state
```

### 22.4 Execution Preference

[DECISION]

Provide executable commands / complete code blocks.

For PowerShell-heavy operations:

```text
prefer single-line or simple commands
avoid fragile long multi-line interactive pipelines
```

For complex checks:

```text
tmp/check_xxx.py
```

### 22.5 Current Feedback Loop

The user normally:

```text
receives one command / one logical action
→ executes locally in Pi / PowerShell
→ pastes exact terminal output
→ AI analyzes
→ AI provides next single action
```

Do not assume success.

---

## 23. Security / Sensitive Data Boundary

[INVARIANT]

Never place the following in HANDOFF:

```text
real token
password
cookie
private key
API secret
session credential
unnecessary personal data
unnecessary real attack payload
```

Use:

```text
environment variable
runtime injection
redacted
fixture
mock
localhost
placeholder
```

### Authorized Target Boundary

[FACT]

Dynamic testing must remain under:

```text
data/targets/ikuai8.com/scope.txt
AUTHORIZED_ENGAGEMENT_ONLY
```

Do not expand target scope because a new AI thinks additional assets “would be useful.”

---

## 24. Reproducibility Status

### Overall Rating

**CONDITIONALLY REPRODUCIBLE**

### Reason

[DERIVED]

The core software contracts, test entry points, current Stage-3~8 artifacts, Provider fix behavior, and Coverage bug evidence are sufficiently documented to recover the current engineering thread.

Full end-to-end reproducibility remains conditional because:

```text
current live Git state = UNKNOWN
current worktree = not mounted in this AI session
full regression after latest changes = not rerun
current runner patch = not yet verified in this snapshot
real target behavior = environment-dependent
LLM runtime availability = external runtime dependency
authorization scope = must remain explicitly verified
```

### Layered assessment

```text
Python core contracts            = HIGH
Rust core contracts              = HIGH (historical)
Provider fix behavior            = HIGH
Stage 3–7 artifact existence     = HIGH
Initial P0 execution evidence    = HIGH
Coverage aggregation bug         = HIGH
Current runner patch correctness = UNKNOWN
Current Git state                = UNKNOWN
Full current regression          = UNKNOWN
Real target behavior             = CONDITIONAL
First real vulnerability finding = NOT YET REPRODUCIBLE
```

---

## 25. Handoff Self-Check

```text
[x] 一个新 AI 是否知道当前项目是什么？
    YES — Invar System-2 security research / dynamic evidence engine.

[x] 一个新 AI 是否知道当前到底在做什么？
    YES — 修正并验证 run_targeted_audit.py Coverage Unit 聚合语义。

[x] 一个新 AI 是否知道为什么要做？
    YES — P0 实证证明 shared CoverageUnit 被 first-task BLOCKED 锁死。

[x] 一个新 AI 是否知道最后一次已知良好状态？
    YES — Provider focused test 11 passed; historical full baseline 222/222.

[x] 一个新 AI 是否知道哪些事实是当前的，哪些只是历史？
    YES — current vs historical labels are explicit.

[x] 一个新 AI 是否知道最后一次真实 P0 的状态？
    YES — 10 tasks, 6 units, 1 covered, 5 blocked, 0 findings.

[x] 一个新 AI 是否知道哪些 task 是安全结论，哪些仍未闭环？
    YES — Section 7.3.

[x] 一个新 AI 是否知道当前唯一下一步？
    YES — runner diff + minimal aggregation tests + git diff --check.

[x] 一个新 AI 是否知道不能做什么？
    YES — Out of Scope is explicit.

[x] 一个新 AI 是否知道 Coverage 的正确状态机？
    YES — Section 3 / 13 / 17.

[x] 一个新 AI 是否知道为什么“后续 safe task → 立即 COVERED”是错误的？
    YES — earlier unresolved facts may remain.

[x] 一个新 AI 是否知道如何避免覆盖旧证据？
    YES — new retry output directory.

[x] 一个新 AI 是否知道当前 Git 是否干净？
    NO — correctly recorded as UNKNOWN.

[x] 一个新 AI 是否知道哪些信息尚未确定？
    YES — Section 18.

[x] 一个新 AI 是否知道如何恢复测试与协作方式？
    YES — Sections 14 / 19 / 21 / 22.

[x] HANDOFF 是否包含真实 secret？
    NO.
```

---

# Final Recovery Statement

[DECISION]

> **当前不要重新设计 Invar。**
>
> Invar 的确定性动态执行、端点身份、研究循环、证据链、独立验证、PromotionGate、SARIF/OpenVEX 投影等基础能力已有事实证据。
>
> 最新 P0 真实运行暴露的直接工程问题是 **Coverage Unit 聚合状态机在 runner 层实现错误**：同一 `coverage_id` 的第一个 inconclusive task 可以把 unit 置为 `BLOCKED`，导致后续 task 的安全结论没有进入 aggregate state。这个问题已经通过真实执行结果定位，而不是推测。
>
> 当前正确的修复不是“看到后续 safe task 就直接 COVERED”，而是：
>
> ```text
> 按 coverage_id 聚合全部 planned task
> → 每个 task 独立贡献事实
> → 未完成全部 task 前保持 IN_PROGRESS
> → 全部完成后
>      vulnerable → CANDIDATE
>      unresolved → BLOCKED
>      otherwise → COVERED
> ```
>
> 因此：
>
> ```text
> CURRENT OBJECTIVE
>     ↓
> run_targeted_audit.py Coverage aggregation correctness
>     ↓
> NEXT SINGLE ACTION
>     ↓
> inspect diff + targeted aggregation tests + git diff --check
>     ↓
> only after verification
>     ↓
> new-output-dir P0 retry
> ```
>
> **不要在当前验证完成前修改 Coverage Ledger、Provider、ResearchLoop、Transport、Sandbox、Reporting、OpenVEX、Pi、Skill、UI 或其他无关边界。**
