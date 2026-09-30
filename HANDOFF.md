# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot / Recovery Contract
>
> **Project:** Invar
>
> **Snapshot Date:** 2026-10-01
>
> **Canonical Repository Root:** `C:\dev\Invar`
>
> **Canonical Handoff Path:** `C:\dev\Invar\HANDOFF.md`
>
> **Snapshot Authority:** latest accessible source snapshot, test results, implementation reports, runtime configuration supplied in the current engineering session, and verified upstream documentation. The live local worktree is not mounted in this AI session; therefore current Git state and the final post-interruption source state are explicitly marked `UNKNOWN` where applicable.

---

## 0. Handoff Metadata

| Item | Value | Level | Evidence |
|---|---|---|---|
| Project | Invar | [FACT] | Repository context |
| Root | `C:\dev\Invar` | [FACT] | Project context |
| Current system role | System-2 deep dynamic security research / evidence Harness | [FACT] | Existing project architecture |
| Long-term mission | AI-controlled authorized security research with deterministic execution, evidence, independent verification, and promotion | [DECISION] | Project direction |
| Current primary workstream | Invar Research Control Plane / autonomous research control | [DECISION] | Current session direction |
| Historical Stage-8 runner objective | Coverage Unit aggregation | [DECISION] / SUPERSEDED | Previous HANDOFF; not current mainline |
| Active authorized research target | `ikuai8.com` | [FACT, historical project scope] | Existing scope records |
| Current Git branch | `UNKNOWN` | [UNKNOWN] | No live worktree |
| Current HEAD | `UNKNOWN` | [UNKNOWN] | No live worktree |
| Current worktree status | `UNKNOWN` | [UNKNOWN] | No live worktree |
| Current full regression | `UNKNOWN` | [UNKNOWN] | Not rerun after latest Control Plane changes |
| Last known good Control Plane test | 18 passed in 0.12s | [FACT] | Session test output |
| Current final Progress Guard implementation | `UNKNOWN` | [UNKNOWN] | Pi response was interrupted during implementation |
| Temporary repair helper `tools/fix_control_plane_budget.py` | `UNKNOWN / untrusted` | [UNKNOWN] | Two generated versions failed with Python SyntaxError before execution |

---

## 1. Project Identity

### 1.1 System Role

[FACT]

Invar is the System-2 dynamic research and security evidence engine in the broader project.

Its intended evidence path is:

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
Reporting / Promotion
```

The system is **not** defined as “an LLM scans code and declares vulnerabilities.”

### 1.2 Engineering Constitution

[DECISION]

The project follows:

```text
零臆造
零盲目建目录
零破坏性删除
测试验证方可交付

事实 > 猜测
根因 > 补丁
抽象 > 特判
契约 > 约定
复用 > 重造
验证 > 猜测
系统最优 > 局部最优
```

The Clean & Deliver Protocol is the engineering baseline:

> 有依据才实现，有抽象才扩展，有契约才连接，有测试才交付。

---

## 2. Current Mission

[DECISION]

Build an AI-research-control-driven authorized security research system in which:

```text
AI decides only within bounded research authority
        ↓
deterministic Invar core executes the experiment
        ↓
real observation is collected
        ↓
deterministic evaluation interprets it
        ↓
evidence is recorded
        ↓
independent verification remains separate
        ↓
finding / knowledge can be promoted
```

The immediate product direction is AI-assisted authorized Bug Bounty / SRC research, with human review retained before any external submission.

---

## 3. Current Objective

### CURRENT OBJECTIVE

[DECISION]

**Stabilize and continue the Invar Control Plane mainline from its last known-good Observation-feedback state, without introducing the currently rejected `no_progress` heuristic.**

The Control Plane has already crossed the important feedback threshold:

```text
Candidate Actions
    ↓
Real ResearchController
    ↓
Deterministic Experiment
    ↓
Real Observation
    ↓
Persistent ResearchControlState
    ↓
Next ResearchController decision
```

The current work was then extended toward bounded lifecycle / decision budget, but that implementation was interrupted before a final validated state was established.

Therefore the current objective is now:

```text
Recover exact worktree state
        ↓
Preserve last-known-good Control Plane semantics
        ↓
Keep Observation feedback
        ↓
Keep finite Decision Budget semantics if already present and correct
        ↓
Do not revive no_progress
        ↓
Continue toward the next bounded Control Plane capability
```

---

## 4. Next Single Action

### NEXT SINGLE ACTION

[TODO]

> **Establish the live worktree delta for the Control Plane files (`research_controller.py`, `research_loop.py`, `research_agent.py`, `domain_contracts.py`, and Control Plane tests), and reconcile any partial/interrupted Progress Guard edits back to the last known-good Control Plane semantics before implementing anything new.**

This is one recovery action, not a new architecture phase.

The next AI must not:

- redesign the Control Plane;
- add more actions;
- reintroduce `no_progress`;
- run a real target;
- start a full regression before the delta is understood.

---

## 5. Current Scope

### 5.1 In Scope

[DECISION]

Primary modules:

```text
python/packages/core/src/agent/research_controller.py
python/packages/core/src/agent/research_loop.py
python/packages/core/src/agent/research_agent.py
python/packages/core/src/harness/domain_contracts.py
```

Primary tests:

```text
python/tests/test_research_controller.py
python/tests/test_control_plane_observation_feedback.py
python/tests/test_research_loop_contract.py
python/tests/test_research_agent_contract.py
```

Current architecture layer:

```text
ResearchAgent
    ↓
ResearchLoop
    ↓
ResearchController
    ↓
Deterministic Candidate Set
    ↓
Deterministic Experiment
    ↓
Observation
    ↓
Control State Feedback
```

### 5.2 Supporting Areas

[FACT]

Existing supporting layers include:

```text
EndpointIR / EndpointRegistry
AdaptiveExperimentSelector
TransformationFamilyRegistry
HttpTransport
DenialClassification
SemanticEquivalenceEvaluator
EvidenceChain
ExecutionTrace
IndependentVerifier
PromotionGate
KnowledgePromoter
Reporting / SARIF / OpenVEX
```

### 5.3 Out of Scope

[DECISION]

Do not touch during the current Control Plane recovery/continuation unless new source evidence directly requires it:

```text
AST full rerun
Asset rediscovery
Target expansion
EndpointIR redesign
EndpointRegistry redesign
Transport rewrite
Sandbox rewrite
Finding schema redesign
Verification redesign
Promotion redesign
Reporting redesign
UI / Tauri / React
Temporal
PostgreSQL / pgvector
LATS / MCTS
Large orchestration frameworks
Large directory refactors
Unrelated technical debt
Automatic bounty submission
Unauthorized target research
```

Do not reopen the older Coverage Unit runner objective as the main task.

---

## 6. Out of Scope: GVS5H Boundary

[DECISION]

`pi-gvs5h` is a **development-time orchestration harness**, not an Invar research-runtime dependency.

Current upstream repository:

```text
https://github.com/srossitto79/pi-gvs5h
```

Current paper:

```text
https://arxiv.org/abs/2608.26480
```

[FACT, upstream README, retrieved 2026-10-01]

The repository describes GVS5H as a Pi extension that uses fresh manager/worker sessions and a durable ledger for coding workflows. It explicitly states that worker sessions disable discovered extensions, skills, and prompt templates to prevent recursive workflows.

[DERIVED]

For Invar this means:

```text
Pi / pi-gvs5h
    = development / engineering harness

Invar ResearchController
    = research-time bounded decision layer

Invar deterministic Harness
    = authoritative execution / evaluation
```

Do not nest GVS5H as:

```text
GVS manager
    ↓
Invar controller
    ↓
LLM
    ↓
experiment
    ↓
GVS manager
```

because that creates competing control planes and weakens causal attribution.

GVS5H's published benchmark evidence is about coding tasks, not security research. Do not claim that its reported gains automatically transfer to Invar's security research workload.

---

## 7. Last Known Good State

### 7.1 Control Plane Last Known Good

[FACT, 2026-09-30]

Command:

```powershell
uv run --project python pytest python/tests/test_control_plane_observation_feedback.py python/tests/test_research_controller.py -q
```

Result:

```text
18 passed in 0.12s
```

This is the **primary current Control Plane recovery anchor**.

### 7.2 What That Green State Proved

[FACT]

The test suite proved a real controller path:

```text
Turn 1
    ↓
Real ResearchController
    ↓
fake deterministic provider selects FA
    ↓
fake transport returns HTTP 403 / permission denied
    ↓
ResearchLoop writes observation into persistent control state
    ↓
Turn 2
    ↓
Real ResearchController receives the observation
    ↓
fake provider detects the observation in the prompt
    ↓
provider selects FB
```

The second decision was therefore causally dependent on the first experiment's observation rather than merely being the second LLM call.

### 7.3 Earlier Observation Data-Flow State

[FACT]

Previous focused run:

```text
test_control_plane_observation_feedback.py: 4 passed
related existing tests: 22 passed
total: 26 passed
```

That run established the data-flow before the real-Controller path was added.

### 7.4 Provider Last Known Good

[FACT]

Command:

```powershell
uv run --project python pytest python/tests/test_model_provider.py
```

Result:

```text
11 passed in 0.12s
```

Provider behavior locked by that work:

```text
finish_reason == "stop"
    → normal structured JSON parse

finish_reason == "length"
    → parse direct result first
    → one continuation only when truly incomplete
    → strict reparse
    → safe failure if still invalid

other finish_reason
    → immediate provider failure
```

Forbidden:

```text
bracket repair
field guessing
infinite retries
silently accepting unrelated finish reasons
```

### 7.5 Historical Full Baseline

[FACT, HISTORICAL]

Previously recorded:

```text
Python: 207 passed
Rust:    15 passed
Total:  222 / 222
```

Commands:

```powershell
uv run --project python pytest
cargo test --workspace
```

This is a historical recovery anchor only. It is **not** a claim about the current worktree.

### 7.6 Current Worktree

[UNKNOWN]

The live worktree was not available to this AI. Therefore the following are unknown:

```text
branch
HEAD
modified files
deleted files
untracked files
final research_loop.py contents
final research_agent.py contents
current control-plane tests
current progress-guard edits
```

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| Deterministic System-2 research pipeline | DONE | Existing source / tests / artifacts | `python/packages/core/...` | Core execution and evidence path established |
| Provider `finish_reason=length` recovery | DONE | 11 provider tests passed | `model_provider.py`, `test_model_provider.py` | One continuation max |
| Coverage aggregation defect identification | DONE / HISTORICAL | Real P0 run | `run_targeted_audit.py` | No longer current mainline |
| Research Control Plane v0 finite action set | DONE | 13 controller tests reported passing | `research_controller.py`, `test_research_controller.py` | `RUN_EXPERIMENT`, `STOP` |
| Candidate-bounded controller | DONE | Controller implementation report + tests | `research_controller.py` | Controller can only select deterministic candidates |
| Observation feedback state | DONE | 26 focused tests reported passing | `research_loop.py`, feedback tests | Persistent state inside loop |
| Real Controller Observation feedback | DONE | 18 focused tests passed | `research_loop.py`, feedback tests | Most important current milestone |
| ResearchAgent Control Plane constructor wiring | DONE / UNVERIFIED CURRENT WORKTREE | Pi implementation report | `research_agent.py` | Explicit parameters reported |
| Control decision lifecycle / budget | PARTIAL / UNVERIFIED | Pi implementation was interrupted | `research_loop.py` | Must recover actual current source before continuing |
| `no_progress` heuristic | DEPRECATED / REJECTED | Queue-consumption analysis | `research_loop.py` / related tests | Do not revive under current queue model |
| First confirmed vulnerability | TODO | None | — | Not yet produced |
| First end-to-end Knowledge feedback loop | TODO | None | — | Not yet proven |

---

## 9. Changed Files

### 9.1 Added

[FACT from Control Plane implementation report]

```text
python/packages/core/src/agent/research_controller.py
python/tests/test_research_controller.py
python/tests/test_control_plane_observation_feedback.py
```

[UNKNOWN]

Whether each is currently tracked/modified exactly as reported must be checked against live Git state.

### 9.2 Modified

[FACT from implementation reports; current final content UNKNOWN]

```text
python/packages/core/src/agent/research_loop.py
python/packages/core/src/agent/research_agent.py
python/packages/core/src/harness/domain_contracts.py
```

Reported roles:

```text
research_loop.py
    → Control Plane dispatch
    → persistent Observation feedback

research_agent.py
    → explicit Control Plane constructor wiring

domain_contracts.py
    → Control Plane event types / payload contracts
```

### 9.3 Temporary / Failed Helper

[UNKNOWN]

A session-created helper was intended as:

```text
tools/fix_control_plane_budget.py
```

Two versions failed at Python parsing time:

```text
SyntaxError
```

before execution.

Therefore:

```text
it must NOT be trusted as a project implementation
it must NOT be treated as a successful repair
```

Its current filesystem state is UNKNOWN.

### 9.4 Deleted

[UNKNOWN]

### 9.5 Moved / Renamed

[UNKNOWN]

### 9.6 Directory Contract

[INVARIANT]

Maintain existing responsibility boundaries:

```text
python/packages/core/src/   production Python
python/tests/               Python tests
crates/                     Rust
configs/                    configuration
data/                       target / dataset inputs
models/                     model assets
artifacts/                  durable research outputs
docs/                       design / research documentation
tmp/                        temporary archaeology / experiments
tools/                      project utilities
.pi/                        local Pi state / configuration where applicable
```

Do not move production code into test/temporary directories.

---

## 10. Current Architecture

### 10.1 System Pipeline

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
System-1 Triage
    ↓
Research Task Assembly
    ↓
System-2 Targeted Research
    ↓
EndpointRegistry
    ↓
AdaptiveSandboxExecutor
    ├── Transport
    ├── Mutation / Transformation
    ├── Denial Classification
    ├── Adaptive Selector
    └── ResearchAgent / ResearchLoop
    ↓
Deterministic Evaluation
    ↓
Evidence / Trace
    ↓
Independent Verification
    ↓
Promotion
    ↓
Finding / Knowledge
    ↓
Reporting
```

### 10.2 Current Control Plane

[FACT, last known good]

```text
Deterministic Candidate Set
        ↓
ResearchController
        ↓
ResearchAction
        ├── RUN_EXPERIMENT
        └── STOP
        ↓
Deterministic Experiment
        ↓
Real Observation
        ↓
ResearchControlState
        ↓
Next Controller Decision
```

### 10.3 Control State

[FACT]

Reported structure:

```python
@dataclass
class ResearchControlState:
    current_status: str = "EXECUTING"
    tried_variants: Set[str] = field(default_factory=set)
    last_observation_summary: str = ""
```

The feedback implementation updates:

```text
last_observation_summary
```

from the current experiment result instead of repeatedly using the initial baseline.

### 10.4 Candidate Boundary

[FACT]

Reported `CandidateAction` fields:

```text
variant_id
family
method
url
expected_effect
rationale
```

The Control Plane does **not** accept arbitrary LLM-generated:

```text
headers
payload
new variants
arbitrary HTTP actions
```

This is a key security boundary.

### 10.5 Decision Contract

[FACT]

Reported `ControlPlaneDecision`:

```text
action
target_id
reason
confidence
```

Validation guarantees:

```text
action ∈ finite ResearchAction enum
RUN_EXPERIMENT → target_id must be in candidate_ids
STOP → target_id must be null
reason must be a string
reason length ≤ configured maximum (reported default: 500)
confidence ∈ [0, 1]
confidence boolean is invalid
raw decision must be a JSON object
```

### 10.6 Fail-Closed Behavior

[FACT]

Reported `ResearchController.decide()` behavior:

```text
no candidates
    → STOP / fallback

no provider
    → deterministic fallback candidate

invalid LLM output
    → reject
    → deterministic fallback
    → do not invent a new action
```

---

## 11. Architecture Decisions

### AD-01 — Deterministic Core Retains Security Authority

**Decision**

[DECISION]

The LLM is not the security truth source.

**Why**

Security facts must remain grounded in execution, observation, deterministic evaluation, evidence, and independent verification.

**Alternatives rejected**

Using model prose as a final vulnerability verdict.

**Evidence**

Existing EvidenceChain / verifier / promotion contracts plus the observed Control Plane design.

**Do not revert unless**

A new source-backed security architecture is intentionally approved and corresponding contracts/tests are added.

---

### AD-02 — LLM Uses a Finite Action Vocabulary

**Decision**

[DECISION]

Current Control Plane starts with:

```text
RUN_EXPERIMENT
STOP
```

**Why**

Bound model authority before expanding autonomy.

**Do not revert unless**

A new bounded action contract exists with validation, execution semantics, and tests.

---

### AD-03 — Controller Selects Existing Deterministic Candidates

**Decision**

[DECISION]

LLM cannot manufacture arbitrary experiment variants.

**Why**

Preserves deterministic execution authority and prevents direct model control over arbitrary request construction.

**Do not revert unless**

A future explicit candidate-generation boundary is created with independent validation.

---

### AD-04 — Observation Feedback Is Persistent Loop State

**Decision**

[DECISION]

The previous experiment's real observation must enter the next Control Plane decision.

Canonical path:

```text
Experiment
    ↓
Observation
    ↓
ResearchControlState
    ↓
Controller prompt
    ↓
Next decision
```

**Evidence**

18 focused tests passed on the real Controller path.

---

### AD-05 — Observation Equality Is Not a Research Progress Model

**Decision**

[DECISION]

Do not define:

```text
same Observation
=
no_progress
```

under the current architecture.

**Why**

The candidate queue is a consumptive queue. A selected experiment is removed from the queue. Therefore a sequence such as:

```text
FA → 403
FB → 403
FC → 403
```

still represents distinct experiments even when their observations match.

The queue's normal semantics already prevent indefinite same-candidate replay.

**Alternatives rejected**

- duplicate `variant_id` queue fixtures to manufacture stagnation;
- changing `pop()` semantics only to create a no-progress test;
- treating unchanged response text as equivalent to unchanged research state.

**Status**

`no_progress` guard is deprecated/rejected for the present architecture.

---

### AD-06 — Research Progress Must Eventually Be State-Based

[DERIVED]

Future progress should mean meaningful research-state advancement, not simply changed bytes.

Candidate future signals include:

```text
hypothesis transition
evidence-grade transition
new candidate family
verification state advancement
new invariant implication
terminal condition
```

This is future architecture, not current implementation.

---

### AD-07 — One-Step Engineering

[DECISION]

Each development round advances one logical action.

Do not combine:

```text
architecture change
+
large test rewrite
+
runtime integration
+
unrelated cleanup
```

in one step.

---

### AD-08 — GVS5H Stays Above the Research Runtime

[DECISION]

Use GVS5H for repository engineering when useful, but keep it outside Invar's runtime research control plane.

---

## 12. Data / API / Type Contracts

### 12.1 EndpointIR

[FACT, existing project contract]

Known core fields include:

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

Canonical endpoint identity is normalized around method + path.

### 12.2 ResearchScope

[FACT]

Known fields:

```text
target_domain
included_subdomains
excluded_paths
allowed_methods
authorization_boundary
```

Authorization boundary:

```text
AUTHORIZED_ENGAGEMENT_ONLY
```

### 12.3 ResearchLoopConfig

[FACT from pre-Control-Plane source; current Control Plane additions are partially UNVERIFIED]

Known historical fields:

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

Reported Control Plane additions:

```text
control_plane_enabled
controller
control_plane_config
```

Current exact final values are `UNKNOWN`.

### 12.4 ResearchLoopContext

[FACT]

Known fields:

```text
endpoint
target_url
baseline_observation
denial_classification
messages
tried_variants
evidence_chain
metadata
```

### 12.5 ResearchLoopResult

[FACT, existing contract]

Known fields:

```text
context
final_verdict
evidence_chain
turns_executed
probes_dispatched
breakthrough_achieved
aborted
abort_reason
```

### 12.6 TransformationVariant

[FACT, existing project contract]

Known relevant fields:

```text
variant_id
family
method
url
headers
payload
rationale
expected_effect
```

Important authority boundary:

```text
TransformationVariant headers/payload
    should originate from deterministic transformation machinery
    rather than unrestricted Control Plane model output
```

The legacy LLM reflection path previously generated headers/payload directly. Current Control Plane work intentionally avoids that authority pattern. The legacy path's current live status is `UNKNOWN`.

### 12.7 ResearchController Contract

[FACT, last known good implementation report]

```text
ResearchAction:
    RUN_EXPERIMENT
    STOP
```

```text
CandidateAction:
    variant_id: str
    family: str
    method: str
    url: str
    expected_effect: str
    rationale: str
```

```text
ResearchControlState:
    current_status: str
    tried_variants: Set[str]
    last_observation_summary: str
```

```text
ControlPlaneDecision:
    action: ResearchAction
    target_id: Optional[str]
    reason: str
    confidence: float
```

### 12.8 Provider Contract

[FACT]

Default local-provider boundary:

```text
OpenAI-compatible
http://127.0.0.1:8080/v1
```

Provider request path:

```text
{base_url}/chat/completions
```

Sensitive information must come through environment/configuration injection; never write secrets into HANDOFF.

---

## 13. Algorithms / Workflow

### 13.1 Research Mainline

```text
Research Task
    ↓
Resolve EndpointIR
    ↓
Baseline Observation
    ↓
Deterministic Denial Classification
    ↓
Deterministic Candidate Generation
    ↓
Controller selects one bounded action
    ↓
Execute one deterministic experiment
    ↓
Observe result
    ↓
Evaluate semantic/invariant effects
    ↓
Update research state
    ↓
Controller decides again
```

### 13.2 Current Loop Stop Conditions

[FACT / PARTIALLY VERIFIED]

Known existing termination mechanisms include:

```text
breakthrough
max_turns
signal.is_aborted
candidate queue exhaustion
controller STOP
```

A research-task-level Decision Budget was being added, but its final current implementation is `UNKNOWN`.

### 13.3 Progress Semantics

[DECISION]

Current architecture does **not** have a validated general `research_progress` model.

Do not use:

```text
response text unchanged
```

as the authoritative research-progress signal.

Do not use:

```text
new variant executed
```

as equivalent to:

```text
research success
```

Use the distinction:

```text
experiment_progress
    ≠
security_success
```

---

## 14. Verified Tests

### VT-01 — Research Controller Contract

[FACT, session report]

```text
13 passed
```

Purpose:

```text
finite action validation
candidate target validation
reason constraints
confidence constraints
fail-closed behavior
```

### VT-02 — Observation Feedback Data Flow

[FACT, session report]

```text
4 focused feedback tests passed
22 related existing tests passed
26 total passed
```

Purpose:

```text
real experiment result is persisted into loop control state
```

### VT-03 — Real Controller Observation Feedback

[FACT, 2026-09-30]

```powershell
uv run --project python pytest python/tests/test_control_plane_observation_feedback.py python/tests/test_research_controller.py -q
```

Result:

```text
18 passed in 0.12s
```

Purpose:

```text
ResearchController.decide()
→ _build_prompt()
→ validation
→ observation-dependent provider response
→ next selected candidate
```

### VT-04 — Provider Contract

[FACT, 2026-09-30]

```text
11 passed in 0.12s
```

### VT-05 — Historical Full Regression

[FACT, HISTORICAL]

```text
Python 207 passed
Rust 15 passed
222 / 222
```

Not current.

### VT-06 — Progress Guard

[UNVERIFIED]

No validated final Progress Guard state exists.

Do not record green results that came from interrupted/truncated implementation reasoning.

---

## 15. Failure / Pitfall Registry

### FP-01 — LLM Treated as the Whole Research System

**Problem**

Model output was allowed to be conceptualized as the research system itself.

**Root Cause**

Model generation and research control were conflated.

**Wrong Approach**

Let model prose directly determine final security truth.

**Correct Fix**

Separate:

```text
Research Control
+
Deterministic Security Core
+
Evidence / Verification
```

---

### FP-02 — Observation Feedback Missing

**Problem**

Controller repeatedly received baseline observation rather than the previous real experiment result.

**Root Cause**

`last_observation_summary` was rebuilt from the initial baseline.

**Correct Fix**

Use persistent loop-local `ResearchControlState`.

**Regression**

18 focused tests passed on the real Controller path.

---

### FP-03 — `no_progress` Defined as Unchanged Observation

**Problem**

Repeated 403 responses were interpreted as research stagnation.

**Root Cause**

Observation equality was confused with research-state equality.

**Wrong Approach**

```text
same response
→ no_progress
```

**Correct Fix**

Rejected for current architecture.

---

### FP-04 — Candidate Queue Semantics Ignored

**Problem**

Progress Guard design tried to force the loop to replay already-consumed variants.

**Root Cause**

The queue is consumptive:

```text
select
→ pop
→ execute
→ tried_variants
```

**Wrong Approach**

Introduce duplicate variant IDs or alter `pop()` just to create a test.

**Correct Fix**

Respect current queue semantics. Defer general research-progress modeling until dynamic replanning exists.

---

### FP-05 — Pi / Local Model Response Truncation

**Problem**

The local model/Pi repeatedly produced responses ending with:

```text
Response was truncated before completion
```

during Progress Guard reasoning.

**Root Cause**

`UNKNOWN`.

Potential contributors were discussed, but no authoritative root-cause evidence was produced.

**Correct Fix**

Do not treat the suspected cause as proven. Current engineering policy is to stop delegating this particular implementation step to the local Pi/model and use deterministic, human-directed code changes.

---

### FP-06 — Generated Repair Script SyntaxError

**Problem**

`tools/fix_control_plane_budget.py` failed twice with Python SyntaxError.

**Root Cause**

The generated helper itself contained invalid Python string construction.

**Wrong Approach**

Repeatedly patch the helper.

**Correct Fix**

Do not trust the helper. Inspect the real diff and make source changes from confirmed structure.

---

### FP-07 — Historical HANDOFF Used as Current Source of Truth

**Problem**

The previous HANDOFF still described Coverage Unit aggregation as the current objective.

**Root Cause**

The project moved forward, but the handoff snapshot had not yet been regenerated.

**Correct Fix**

This HANDOFF explicitly supersedes the old runner objective and labels current live Git state as unknown when it cannot be verified.

---

## 16. Do Not Repeat

```text
不要把旧 HANDOFF 的 Coverage runner 目标当成当前主线。

不要把历史 Git 状态写成当前 Git 状态。

不要把 222/222 historical regression 写成 current green。

不要把 Pi 的自我报告当成源代码事实。

不要把 Observation 相同直接等价为 no_progress。

不要为了制造 no_progress 测试而修改 candidate queue pop 语义。

不要使用重复 variant_id 作为真实架构行为的替代品。

不要让 Control Plane LLM 直接生成任意 headers/payload。

不要让 LLM 直接制造 confirmed Finding。

不要把 candidate execution 等同于 security success。

不要因为 GVS5H 能改善 coding workflow 就让它成为 Invar runtime controller。

不要把 GVS5H paper 的 coding benchmark 结果写成 security-research benchmark 结果。

不要通过长 prompt 让本地模型承担无限制架构推理。

不要一次修改多个未经验证的边界。

不要用大型 regex/自动修复脚本猜测当前源代码结构。

不要把脚本 SyntaxError 误认为项目源码已经损坏。

不要覆盖已有真实研究产物来“重新跑一遍”。

不要将真实 Token、Cookie、Password、Private Key、API Secret 写进 HANDOFF。

不要在未确认授权的目标上执行动态研究。
```

---

## 17. Invariants

### 17.1 Engineering Invariants

```text
事实等级必须明确
源码 > 测试 > 配置 > 运行结果 > HANDOFF > 模型记忆
目录 = 职责边界
接口 = 模块边界
类型 = 数据边界
测试 = 行为契约
```

### 17.2 Research Invariants

```text
Observation ≠ Hypothesis
Hypothesis ≠ Evidence
Evidence ≠ Finding
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

### 17.3 Control Plane Invariants

```text
LLM action ∈ finite Action Enum
LLM cannot invent arbitrary action types
RUN_EXPERIMENT target_id must come from deterministic candidate set
STOP target_id must be null
invalid model decision → fail closed
controller must receive real previous Observation
```

### 17.4 Security Invariants

```text
AUTHORIZED_ENGAGEMENT_ONLY
dynamic execution requires authorized scope
independent verification remains separate
evidence must correspond to real observations
```

### 17.5 State Invariants

```text
tried_variants accumulates executed variant identifiers
candidate queue consumption must remain deterministic
research success must not be inferred from model confidence
```

### 17.6 Checkpoint / Evidence Invariants

```text
completed task keys represent physically completed work
resume must not invent progress
previous evidence should not be silently erased
new retry outputs should use a new directory
```

---

## 18. Open Issues

### OI-01 — Current live Control Plane source state

**Impact**

Future AI cannot safely distinguish completed Control Plane code from interrupted Progress Guard edits without checking the worktree.

**Known**

Last known good is the 18-pass Observation feedback state.

**Unknown**

Exact current contents after interrupted Pi modifications.

**Next Verification**

Current `git diff` for the Control Plane files.

---

### OI-02 — Decision Budget final implementation

**Impact**

Finite controller lifecycle is a core anti-loop requirement.

**Known**

A budget was being added after the 18-pass state.

**Unknown**

Whether the final implementation exists, is correct, or was partially modified.

**Next Verification**

Inspect the live `research_loop.py` / `research_controller.py` diff.

---

### OI-03 — Phase-2 Controller lifecycle

**Impact**

The Control Plane must not accidentally issue extra controller decisions after an explicit stop/budget exhaustion.

**Known**

Pi's interrupted reasoning identified a potential Phase-2 duplicate-decision issue.

**Unknown**

Final current implementation.

**Next Verification**

Inspect live Phase-2 control branch before modifying it.

---

### OI-04 — Legacy direct LLM reflection path

**Impact**

Historical `ResearchLoop` reflection directly requested:

```text
rationale
headers
payload
```

and created a specialized variant.

**Known**

The new Control Plane was designed specifically to prevent this authority pattern.

**Unknown**

Whether the latest worktree still contains and/or activates that path under current configuration.

**Next Verification**

Inspect current `research_loop.py` phase-2 logic.

**Do not silently claim it has been removed.**

---

### OI-05 — Candidate URL sensitivity

**Impact**

`CandidateAction` includes `url`.

**Known**

Headers/payload are excluded.

**Unknown**

Whether any candidate URL can contain sensitive query parameters, signatures, or tokens under the current transformation families.

**Next Verification**

Inspect candidate-generation URL construction and redaction boundaries before exposing it to a real model.

---

### OI-06 — Current local model runtime stability

**Impact**

Pi/local-model implementation work was repeatedly truncated.

**Known**

The user adjusted llama-server configuration after the issue.

**Unknown**

Whether the final current runtime is stable and which exact parameter change was causal.

**Next Verification**

Only if runtime stability becomes a direct blocker; do not make model tuning the current research objective.

---

### OI-07 — First verified vulnerability

**Impact**

Long-term mission milestone.

**Known**

No confirmed vulnerability has yet been produced by the current evidence chain.

**Unknown**

Future finding.

**Next Verification**

Future authorized research after the Control Plane becomes stable enough for autonomous target progression.

---

## 19. Environment / Toolchain

### 19.1 Project Environment

[FACT, project snapshot]

```text
OS: Windows
Shell: PowerShell
Python project manager: uv
Python requirement in root python project: >=3.10,<3.13
Core package requirement: >=3.11,<3.14
Package/test dependency: pytest
Rust: Cargo workspace
JS: pnpm workspace in project snapshot
```

### 19.2 Canonical Commands

Python tests:

```powershell
uv run --project python pytest
```

Focused provider test:

```powershell
uv run --project python pytest python/tests/test_model_provider.py
```

Focused Control Plane test:

```powershell
uv run --project python pytest python/tests/test_control_plane_observation_feedback.py python/tests/test_research_controller.py -q
```

Rust tests:

```powershell
cargo test --workspace
```

Git recovery:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

### 19.3 Local LLM Runtime

[FACT from user-supplied runtime configuration]

OpenAI-compatible local endpoint:

```text
http://127.0.0.1:8080/v1
```

Current model family/name supplied during this session:

```text
Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf
```

The user supplied an earlier high-pressure configuration involving:

```text
draft-mtp
160000 context
large batch / ubatch
MoE CPU offload
FlashAttention
reasoning on
```

The user subsequently adjusted the configuration.

[UNKNOWN]

The exact final post-adjustment launch arguments and runtime stability are not confirmed in this snapshot.

### 19.4 Pi / GVS5H

[FACT, upstream current README]

Current GVS5H repository states:

```text
Node >=22.19.0
tested with Pi 0.85.1
```

Those versions describe the upstream project's tested environment, **not the user's verified current local versions**.

---

## 20. Roadmap

Roadmap is descriptive only.

### Phase A — Deterministic Security Harness

**Status: DONE / MATURE**

```text
EndpointIR
→ deterministic transport
→ mutation
→ evaluation
→ evidence
→ independent verification
→ reporting
```

### Phase B — Bounded Control Plane

**Status: DONE / PROVEN**

```text
finite action set
→ candidate-bounded decision
→ Observation feedback
```

### Phase C — Stable Control Lifecycle

**Status: CURRENT / PARTIAL**

```text
Observation feedback
→ bounded decision budget
→ explicit terminal semantics
→ correct Phase-1 / Phase-2 lifecycle
```

### Phase D — Expand Finite Research Actions

**Status: TODO**

Potential future bounded actions:

```text
VERIFY
NEED_EVIDENCE
RELATIONSHIP_CHECK
REPORT_READY
```

These are not current implementation claims.

### Phase E — Dynamic Research State / Replanning

**Status: TODO**

Move from:

```text
fixed candidate queue
```

toward:

```text
Research Goal
→ Hypothesis
→ Research State
→ Candidate generation
→ Action
→ Observation
→ State transition
→ Replanning
```

This is the point at which a real general `research_progress` model becomes meaningful.

### Phase F — First End-to-End Verified Research Cycle

**Status: TODO**

```text
Observation
→ Evidence
→ Independent Verification
→ FindingRecord
→ PromotionGate
→ KnowledgeCard
```

### Phase G — Knowledge Feedback

**Status: TODO**

```text
Verified Finding
→ Knowledge
→ Future Research Input
```

### Phase H — Cross-target Generalization

**Status: TODO**

Only after the core authorized research loop is proven reproducible.

---

## 21. Recovery Protocol

A new AI must follow exactly:

```text
1. Read HANDOFF.md
2. Read current source
3. Read current relevant tests
4. Establish current Git state
5. Compare against Last Known Good State
6. Determine whether partial/interrupted edits exist
7. Confirm CURRENT OBJECTIVE
8. Execute only NEXT SINGLE ACTION
```

### Conflict resolution

If HANDOFF conflicts with source:

```text
latest verifiable source > HANDOFF
```

If HANDOFF conflicts with tests:

```text
latest real test result > HANDOFF
```

If source and tests conflict:

```text
record the conflict
do not guess
```

If information is missing:

```text
UNKNOWN
```

Do not use model memory to fill gaps.

---

## 22. AI Collaboration Protocol

[DECISION]

Current engineering interaction has changed from Pi-delegated implementation to **direct assistant-led engineering guidance** for this narrow Control Plane workstream because the local model/Pi repeatedly interrupted before completing the task.

Default collaboration:

```text
AI
  ↓
one logical action
  ↓
user executes locally
  ↓
exact terminal output returned
  ↓
AI evaluates
  ↓
next single action
```

Requirements:

```text
中文优先
一次只推进一个逻辑动作
先确认源码，再修改
不要假设命令成功
不要假设测试成功
不要把计划当事实
不要一次给出多个互相依赖的未经验证修改
```

For local PowerShell execution:

```text
prefer short deterministic commands
avoid long inline Python / regex mutation scripts
put complex deterministic logic in a checked file
```

The user has explicitly requested that Pi not be used to drive forward implementation of this specific Control Plane repair until the architecture is stable again.

---

## 23. Security / Sensitive Data Boundary

[INVARIANT]

Never put into this HANDOFF:

```text
real token
password
cookie
private key
API secret
authorization bearer
unnecessary personal data
```

Use:

```text
<REDACTED>
fixture
mock
localhost
environment variable
secret-injected-runtime
```

Dynamic security research must remain inside:

```text
AUTHORIZED_ENGAGEMENT_ONLY
```

No automatic external bounty submission is part of the current runtime.

---

## 24. Reproducibility Status

### PARTIALLY REPRODUCIBLE

Reason:

[FACT]

The following are reproducible from recorded evidence:

```text
project structure
core research architecture
Provider contract
Control Plane contracts
Observation feedback behavior
18-pass real-controller focused test
historical provider test result
historical full regression baseline
```

But:

```text
current live Git state
final post-interruption research_loop.py
final post-interruption progress-budget implementation
current local model runtime stability
```

remain `UNKNOWN`.

Therefore the project must not be marked `FULLY REPRODUCIBLE` from this snapshot alone.

---

## 25. Handoff Self-Check

```text
[x] 一个新 AI 是否知道当前项目是什么？
    YES — Invar System-2 dynamic security research / evidence engine.

[x] 一个新 AI 是否知道当前主线？
    YES — continue the bounded Research Control Plane.

[x] 一个新 AI 是否知道当前唯一下一步？
    YES — establish the live Control Plane diff and reconcile interrupted edits.

[x] 一个新 AI 是否知道最后一次已知良好状态？
    YES — 18 focused Control Plane tests passed in 0.12s.

[x] 一个新 AI 是否知道哪些内容已经证明？
    YES — real ResearchController receives previous Observation and changes next decision input.

[x] 一个新 AI 是否知道哪些内容尚未证明？
    YES — final Decision Budget / Phase-2 lifecycle / current worktree state.

[x] 一个新 AI 是否知道为什么 no_progress 被拒绝？
    YES — current consumptive queue makes Observation equality an invalid general progress proxy.

[x] 一个新 AI 是否知道哪些文件是当前主要边界？
    YES — research_controller.py, research_loop.py, research_agent.py, domain_contracts.py, focused tests.

[x] 一个新 AI 是否知道不能碰什么？
    YES — Out of Scope is explicit.

[x] 一个新 AI 是否知道真实测试命令？
    YES — focused commands are recorded.

[x] 一个新 AI 是否知道历史 222/222 不能写成当前绿？
    YES.

[x] 一个新 AI 是否知道 GVS5H 的边界？
    YES — development harness only, not Invar runtime authority.

[x] 一个新 AI 是否知道不要相信失败的 repair helper？
    YES — helper SyntaxError, status untrusted.

[x] 一个新 AI 是否知道当前 Git 状态？
    NO — correctly marked UNKNOWN and must be established locally.

[x] 一个新 AI 是否包含真实 secrets？
    NO.

[x] 一个新 AI 是否能够在当前上下文丢失后继续？
    YES, after verifying the live worktree against this snapshot.
```

---

## Final Recovery Statement

[DECISION]

> **Do not redesign Invar.**
>
> The project has already crossed the key Control Plane milestone: a real bounded `ResearchController` can receive a previous experiment's Observation and influence the next decision input.
>
> The attempted `no_progress` layer was the wrong abstraction for the current consumptive candidate-queue architecture and is explicitly rejected.
>
> The remaining uncertainty is not conceptual architecture; it is the exact live worktree state after the interrupted Decision Budget / lifecycle implementation.
>
> The next AI must first recover that state against the 18-pass Last Known Good Control Plane state, make only the minimum reconciliation required, and then continue the autonomous-research mainline.
