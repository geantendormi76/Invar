# AI Development Handoff Specification

> **Document type:** Cross-session engineering state snapshot / recovery contract
> **Project:** Invar
> **Canonical project root:** `C:\dev\Invar`
> **Pi runtime workspace:** `C:\dev\agent-workspace`
> **Handoff path:** `C:\dev\Invar\c\HANDOFF.md`
> **Snapshot date:** 2026-09-18
> **Document version:** 4.0.0
> **Primary purpose:** A new AI must be able to reconstruct the current engineering/research state from this document plus the current repository source, tests, configuration, and artifacts, without relying on the old conversation.

---

## Truth-level convention

Use these levels exactly:

```text
[FACT]
[FACT — snapshot]
[FACT — historical]
[FACT — user-reported]
[DECISION]
[DERIVED]
[ASSUMPTION]
[UNKNOWN]
[TODO]
```

Rules:

```text
FACT       = directly supported by source, test, command output, config, or supplied formal material.
DECISION   = explicitly chosen engineering direction.
DERIVED    = conclusion from multiple facts; not a direct observation.
ASSUMPTION = plausible but not sufficiently verified.
UNKNOWN    = not currently established.
TODO       = future work; never describe it as implemented.
```

Historical/snapshot evidence must never be silently upgraded to current live fact.

---

# 0. Handoff Metadata

| Item | Value | Level | Notes |
|---|---|---|---|
| Project | Invar | [FACT] | Rust + Python security research platform |
| Canonical project root | `C:\dev\Invar` | [FACT] | Source repository root |
| Pi workspace | `C:\dev\agent-workspace` | [FACT] | External Agent/control workspace |
| Handoff path | `C:\dev\Invar\c\HANDOFF.md` | [FACT] | This file |
| Snapshot date | `2026-09-18` | [FACT] | Current session date |
| Current mission | Authorized web security research / SRC workflow, using Invar as deterministic research infrastructure | [DECISION] | Supersedes stale M10-only framing from earlier handoff |
| Current target family | `ikuai8.com` | [FACT — user-reported] | Research has been performed against discovered `*.ikuai8.com` hosts |
| Python package | `invar-engine 0.1.0` | [FACT — snapshot] | `src-tauri/python/pyproject.toml` |
| Python version target | `3.11` | [FACT — project convention] | Project supports `>=3.10,<3.13` |
| Rust crate | `Invar-core 0.1.0` | [FACT — snapshot] | `src-tauri/crates/Cargo.toml` |
| Rust edition | `2021` | [FACT — snapshot] | Cargo manifest |
| Pi CLI | `v0.85.1` | [FACT — snapshot] | Not freshly rechecked here |
| Inference endpoint | `http://127.0.0.1:8080/v1` | [FACT — snapshot] | Live availability not checked in this handoff generation |
| Current local model | `Ornith-1.5-9B-Abliterated-IQ3_M.gguf` | [FACT — user-reported] | Live serving state not checked here |
| Git branch | UNKNOWN | [UNKNOWN] | Live repository not mounted/queryable in this generation |
| Git HEAD | UNKNOWN | [UNKNOWN] | Do not infer from prior diffs |
| Current worktree | UNKNOWN | [UNKNOWN] | Do not infer from file names |

---

# 1. Project Identity

## 1.1 Mission

[FACT / DECISION]

Invar is a Rust + Python dual-engine system for:

```text
web/API reverse engineering
contract inference
bounded security research
research execution
evidence collection
deterministic evaluation
finding validation / promotion
multi-run research history
report projection
```

The architectural boundary is:

```text
Pi / Skill
    = cognition + planning + orchestration

Invar Core
    = authoritative state + deterministic research logic + bounded execution + evidence + gates
```

## 1.2 Security-research mission

[DECISION]

The current practical mission is to use the collected public target surface to learn and execute a disciplined Web security methodology:

```text
scope / authorization
    ↓
asset discovery
    ↓
URL + JS collection
    ↓
static extraction
    ↓
batch HTTP reality
    ↓
route / parameter discovery
    ↓
hypothesis
    ↓
minimal dynamic verification
    ↓
evidence
    ↓
independent verification
    ↓
SRC-ready finding
```

Invar is an infrastructure/measurement layer inside that workflow, not the research objective itself.

---

# 2. Current Mission

[DECISION]

The active mission is:

```text
Perform authorized, non-destructive Web security research on the current ikuai8.com surface.
Use static evidence to identify plausible HTTP entry points.
Use batch HTTP observation to establish what is actually live.
Only then perform bounded vulnerability-oriented verification.
```

The current work has deliberately moved away from spending additional time on prompt engineering or broad Invar architectural redesign.

The near-term research pipeline is:

```text
Subfinder
    ↓
Katana / URL collection
    ↓
normalize_katana.py
    ↓
urls.jsonl + javascript.jsonl
    ↓
download_javascript.py
    ↓
raw_js
    ↓
scan_pipeline.py
    ↓
ikuai8_endpoints_report.json
    ↓
probe_urls.py / HTTPX
    ↓
http_probe.jsonl + http_surface.jsonl
    ↓
materialize_static_get.py
    ↓
static_get_endpoints.jsonl
    ↓
CURRENT: tighten route classifier
    ↓
NEXT PHASE: HTTP reality probe on clean candidates
```

---

# 3. Current Objective

## Static GET candidate corpus cleanup

[FACT — current session]

The current unique objective is:

> **Tighten the static GET endpoint route classifier so that `static_get_endpoints.jsonl` contains route-like HTTP candidates rather than obvious AST/UI/display literals, while preserving legitimate routes and keeping discovery separate from execution policy.**

Current input facts:

```text
Static endpoints   = 1221
HTTPX records      = 1175
Observed hosts     = 30
```

Current output from the latest successful materialization:

```text
Materialized GET candidates = 146
Validated JSONL records      = 146
```

The 146-record output is technically valid JSONL but is **not yet research-clean** because obvious false positives remain.

Observed problematic examples include:

```text
https://cloud.ikuai8.com/100M/10M
https://cloud.ikuai8.com/2.5G/1G
https://cloud.ikuai8.com/Chrome/66
https://cloud.ikuai8.com/Data/
https://cloud.ikuai8.com/KB/s
https://cloud.ikuai8.com/[Getter/Setter]
https://auth.ikuai8.com/*$0*/
```

These demonstrate that the current generic route rule is too permissive.

---

# 4. Next Single Action

## NEXT SINGLE ACTION

**Modify only the route-classification logic in `scripts/asset/materialize_static_get.py` so that the known false-positive classes above are rejected while legitimate route-shaped paths remain eligible; then rerun that same script once and stop.**

Acceptance boundary for this one action:

```text
Input artifact paths do not change.
Output artifact path does not change.
No HTTP requests are introduced.
No Invar Core architecture changes.
No WAF bypass logic.
No target-specific hardcoded route list.
No dynamic vulnerability testing.
```

The classifier must separate:

```text
DISCOVERY
    = is this string route-like enough to materialize?

EXECUTION POLICY
    = is it safe/authorized to actually request this route?
```

Do not solve false positives by dropping legitimate verbs such as `logout`, `delete`, `update`, or `switch` merely because their names imply side effects. Discovery and execution policy are different layers.

After the rerun, stop. Do not begin HTTP reality probing in the same action.

---

# 5. Current Scope

## 5.1 Primary files for the current action

```text
C:\dev\Invar\scripts\asset\materialize_static_get.py
C:\dev\Invar\tmp\ikuai8_endpoints_report.json
C:\dev\Invar\data\targets\ikuai8.com\http_surface.jsonl
C:\dev\Invar\data\targets\ikuai8.com\static_get_endpoints.jsonl
```

## 5.2 Related artifacts

```text
C:\dev\Invar\data\targets\ikuai8.com\urls.jsonl
C:\dev\Invar\data\targets\ikuai8.com\javascript.jsonl
C:\dev\Invar\data\targets\ikuai8.com\http_probe.jsonl
C:\dev\Invar\tmp\raw_js\
```

## 5.3 Related source modules when the research pipeline proceeds

```text
C:\dev\Invar\scripts\asset\normalize_katana.py
C:\dev\Invar\scripts\asset\download_javascript.py
C:\dev\Invar\scripts\asset\probe_urls.py
C:\dev\Invar\scripts\pipeline\scan_pipeline.py

C:\dev\Invar\src-tauri\python\src\harness\models.py
C:\dev\Invar\src-tauri\python\src\harness\research_models.py
C:\dev\Invar\src-tauri\python\src\harness\research_adapter.py
C:\dev\Invar\src-tauri\python\src\harness\sandbox_executor.py
C:\dev\Invar\src-tauri\python\src\harness\invariant_evaluator.py
C:\dev\Invar\src-tauri\python\src\agent\hypothesis_engine.py
C:\dev\Invar\src-tauri\python\src\harness\candidate_models.py
C:\dev\Invar\src-tauri\python\src\harness\finding_models.py
C:\dev\Invar\src-tauri\python\src\harness\verification_gate.py
```

## 5.4 Architectural scope

Current focus is:

```text
asset facts
static endpoint facts
HTTP reality facts
route classification
candidate materialization
```

---

# 6. Out of Scope

Current action must not expand into:

```text
❌ M1–M9 redesign
❌ broad M10 CLI refactor
❌ M11 Pi / Skill rearchitecture
❌ embedded Agent / LLM runtime
❌ new findings database
❌ UI changes
❌ IPC redesign
❌ Tree-sitter extractor rewrite
❌ broad RiskEngine rewrite
❌ broad HypothesisEngine rewrite
❌ model-serving changes
❌ performance optimization without a measured blocker
❌ new third-party HTTP stack for this classifier
❌ WAF bypass attempts
❌ authentication bypass attempts without a concrete authorized verification plan
❌ destructive or state-changing testing
❌ credential guessing / password spraying
❌ bulk data extraction
❌ target-specific hardcoded route exceptions
❌ treating static risk scores as confirmed vulnerabilities
❌ sending all 146 current candidates to HTTP probing before classifier cleanup
```

Historical M10 work remains documented but is not the current single objective unless live source inspection explicitly re-establishes it.

---

# 7. Last Known Good State

## 7.1 Latest successful research artifact chain

[FACT — user-reported / current-session verified by command outputs]

```text
raw_js
  → static scan
  → HTTP surface probe
  → static GET materialization
```

### Static scan

[FACT — historical/current-session]

Previously verified output:

```text
AST/API nodes                 = 1221
parameter-rich endpoints      = 300
CRITICAL risk labels          = 25
HIGH risk labels              = 59
MEDIUM risk labels            = 368
evidence records captured    = 0
```

Important:

```text
risk label ≠ vulnerability proof
```

The static report has no captured evidence records.

### HTTP surface

[FACT — user-reported]

Successful batch HTTP probing:

```text
input unique URLs = 1189
HTTPX records     = 1175
JSONL parse errors = 0
```

Classification counts:

```text
AUTH_REQUIRED      1
CLIENT_ERROR      10
FORBIDDEN          2
LIVE_API_LIKE      1
LIVE_HTML        885
LIVE_OTHER       268
REDIRECT            4
WAF_OR_EDGE_BLOCK  4
```

Observed hosts:

```text
30
```

### Static GET materialization

[FACT — user-reported / current-session]

Latest successful command output:

```text
Static endpoints       1221
HTTP surface records   1175
Observed hosts          30
Materialized GETs      146
Validated records      146
Output JSONL errors      0
```

The command completed without runtime errors and wrote:

```text
C:\dev\Invar\data\targets\ikuai8.com\static_get_endpoints.jsonl
```

However, the output is **not semantically clean enough for the next HTTP probe stage**.

## 7.2 Python regression baseline

[FACT — snapshot, not freshly rerun here]

Recorded command:

```powershell
$env:PYTHONPATH = "src-tauri/python/src"
uv run --project src-tauri/python python -m unittest discover -s src-tauri/python/tests -p "test_*.py"
```

Recorded result:

```text
Ran 100 tests in 0.067s, OK
0 failures
0 errors
```

Do not claim this result is current after any subsequent unverified code change.

## 7.3 Rust regression baseline

[FACT — snapshot, not freshly rerun here]

Recorded command:

```powershell
cargo test --manifest-path src-tauri/Cargo.toml
```

Recorded result:

```text
Rust unit / contract tests passed
warnings = 0
errors = 0
```

Again, this is a historical/snapshot result.

## 7.4 Current research conclusion

[FACT]

```text
Confirmed vulnerability = 0
```

This is not a claim that the target has no vulnerabilities. It means no vulnerability has been independently evidenced and promoted in the current recorded workflow.

## 7.5 Warning / error history relevant to the current anchor

```text
No runtime error in the latest Python materializer execution.
Semantic false positives remain in the resulting candidate corpus.
```

---

# 8. Completed Work

| Item | Status | Evidence | Files / Artifacts | Notes |
|---|---|---|---|---|
| Target scope reference captured | DONE | user-provided SRC/bounty context | target context | Scope of every discovered subdomain remains a separate authorization question |
| URL/JS asset normalization | DONE | historical real-run record | `scripts/asset/normalize_katana.py`, `urls.jsonl`, `javascript.jsonl` | Raw Katana data kept separate from normalized assets |
| JS acquisition | DONE | historical real-run record | `scripts/asset/download_javascript.py`, `tmp/raw_js/` | 209 JS inputs succeeded |
| Static AST → EndpointIR | DONE | static scan result | `scan_pipeline.py`, AST modules | 1221 extracted API/static nodes |
| Risk classification | DONE | static report | `ikuai8_endpoints_report.json` | 25 critical / 59 high / 368 medium labels; not proof |
| Batch HTTP surface probe | DONE | user terminal output | `scripts/asset/probe_urls.py`, `http_probe.jsonl`, `http_surface.jsonl` | 1189 unique inputs → 1175 HTTPX records |
| Static GET materialization | DONE mechanically / PARTIAL semantically | user terminal output | `scripts/asset/materialize_static_get.py`, `static_get_endpoints.jsonl` | 146 records, but obvious false positives remain |
| Python/Rust governance M1–M9 | DONE in snapshot | contract tests + project snapshot | Core harness/agent modules | Not freshly re-audited in this handoff generation |
| M10 production CLI integration | UNVERIFIED / historical-current-status conflict | prior HANDOFF only | `scripts/pipeline/scan_pipeline.py` | Do not assume completion or current priority |

---

# 9. Changed Files

Because the live repository filesystem and Git index were not directly available in this handoff generation, this section distinguishes known historical/current-session changes from unknown worktree state.

## 9.1 Added / current-session artifacts

[FACT — current-session / user-reported]

```text
scripts/asset/probe_urls.py
scripts/asset/materialize_static_get.py
```

These were created as deterministic data-pipeline helpers and successfully executed in the current research workflow.

## 9.2 Historical M1–M9 additions

[FACT — snapshot]

```text
src-tauri/python/src/harness/run_models.py
src-tauri/python/src/harness/coverage_ledger.py
src-tauri/python/src/harness/candidate_models.py
src-tauri/python/src/harness/finding_models.py
src-tauri/python/src/harness/verification_gate.py
src-tauri/python/src/harness/multi_run.py
src-tauri/python/src/harness/reporting.py

src-tauri/python/src/agent/hunter.py
src-tauri/python/src/agent/coverage_critic.py
src-tauri/python/src/agent/wave_orchestrator.py

src-tauri/python/tests/test_endpoint_registry_contract.py
src-tauri/python/tests/test_research_run.py
src-tauri/python/tests/test_coverage_ledger.py
src-tauri/python/tests/test_candidate_fingerprint.py
src-tauri/python/tests/test_finding_record.py
src-tauri/python/tests/test_verification_and_promotion_gate.py
src-tauri/python/tests/test_cognitive_orchestration.py
src-tauri/python/tests/test_multi_run_continuity.py
src-tauri/python/tests/test_reporting_projections.py
```

## 9.3 Historical M1–M9 modifications

[FACT — snapshot]

```text
src-tauri/python/src/harness/models.py
src-tauri/python/src/harness/research_adapter.py
src-tauri/python/src/harness/ast_worker.py
src-tauri/python/src/agent/knowledge_promoter.py
src-tauri/python/src/harness/__init__.py

src-tauri/crates/src/orchestrator.rs
src-tauri/crates/tests/orchestrator_contract_test.rs
src-tauri/crates/tests/process_executor_contract_test.rs
```

## 9.4 Historical scan_pipeline fix

[FACT — historical/current-session]

A circular-import failure was encountered because `scan_pipeline.py` imported `AdaptiveSandboxExecutor` at module load time. The working fix moved that import into the `--probe` execution branch so the static-only path no longer triggers the circular dependency.

The static scan subsequently completed successfully and produced the 1221-node report.

Exact current diff: UNKNOWN.

## 9.5 Deleted historical Agent-runtime files

[FACT — historical user-confirmed]

```text
src-tauri/python/src/agent/model_provider.py
src-tauri/python/src/agent/research_agent.py
```

These belonged to a rejected embedded-Agent architecture direction.

## 9.6 Git status

[UNKNOWN]

No live `git status --short`, branch, or HEAD was available during this handoff generation.

---

# 10. Directory / Structure Contract

[DECISION]

The repository uses explicit responsibility boundaries:

```text
C:\dev\Invar
├── c\                         # handoff / architecture / specifications
├── data\                      # persistent research assets/facts
├── tmp\                       # regenerable temporary artifacts
├── scripts\
│   ├── asset\                 # collection / normalization / download / probe preparation
│   ├── audit\                 # audit / quality tooling
│   └── pipeline\              # pipeline orchestration
├── src\                       # presentation/frontend layer
├── src-tauri\
│   ├── crates\                # Rust core and Rust tests
│   └── python\                # Python research engine and Python tests
└── tests\                     # global E2E
```

Critical artifact boundary:

```text
tmp/
    = regenerable execution/intermediate artifacts

data/targets/<target>/
    = persistent target research artifacts
```

For the current target:

```text
TMP
C:\dev\Invar\tmp\raw_js\
C:\dev\Invar\tmp\ikuai8_endpoints_report.json

PERSISTENT TARGET DATA
C:\dev\Invar\data\targets\ikuai8.com\
    ├── urls.jsonl
    ├── javascript.jsonl
    ├── http_probe.jsonl
    ├── http_surface.jsonl
    └── static_get_endpoints.jsonl
```

Do not move files between these layers merely to make paths look simpler.

---

# 11. Current Architecture

## 11.1 Security-research flow

```text
Scope / Authorization
        ↓
Asset discovery
        ↓
URL / JS normalization
        ↓
JS acquisition
        ↓
AST / EndpointIR
        ↓
Static candidate classification
        ↓
Batch HTTP Reality
        ↓
Parameter / content discovery
        ↓
Hypothesis
        ↓
ResearchCase
        ↓
Bounded execution
        ↓
Evidence
        ↓
Invariant evaluation
        ↓
FindingRecord
        ↓
Independent verification
        ↓
PromotionGate
        ↓
KnowledgeCard / report
```

## 11.2 Invar Core state spine

[FACT — snapshot]

```text
Raw JS
→ AST
→ EndpointIR
→ EndpointRegistry
→ ResearchRun
→ CoverageLedger
→ ResearchTask
→ ResearchCase
→ Evidence
→ InvariantEvaluation
→ Candidate
→ CandidateFingerprint
→ FindingRecord
→ Independent Verification
→ Promotion Gate
→ KnowledgeCard
→ ReportProjector
```

## 11.3 Pi / Invar boundary

[DECISION]

```text
Pi
    = cognition / planning / orchestration

Tool Contract
    = integration boundary

Invar Core
    = durable authoritative state + deterministic security logic
```

Pi must not create a parallel authoritative findings/coverage database.

## 11.4 Discovery vs execution boundary

[DECISION]

```text
Static materializer
    = discovers route-shaped candidates

HTTP probe / executor
    = decides whether and how an actual request may be executed
```

A route name implying mutation is not itself a reason to delete the route from discovery.

---

# 12. Architecture Decisions

## AD-01 — Source and test evidence outrank model narrative

**Decision**

```text
source / test / tool output
    >
model interpretation
```

**Why**

The handoff must survive context loss without speculative reconstruction.

**Do not revert unless**

The system gains a formally stronger evidence source.

---

## AD-02 — Pi remains external to Invar Core

**Decision**

```text
Pi → Tool Contract → Invar Core
```

**Rejected**

```text
Pi → internal Python implementation details
Invar → embedded LLM / Agent runtime
```

**Reason**

Preserves deterministic Core behavior and reusable Tool Contract boundaries.

---

## AD-03 — Static risk is not vulnerability proof

**Decision**

```text
risk label
    ≠
hypothesis
    ≠
candidate
    ≠
evidence
    ≠
confirmed finding
```

**Evidence**

Current static report has `evidence_records_captured = 0`.

---

## AD-04 — HTTPX batch reality is a separate evidence layer

**Decision**

The large URL corpus should be batch-probed before spending effort on individual endpoint hypotheses.

**Why**

Collected URLs contain redirects, HTML, SPA shells, errors, and other non-API surfaces. A batch HTTP layer cheaply establishes what is actually reachable and how it behaves.

---

## AD-05 — Python for deterministic data-pipeline scripts

**Decision — current session**

JSON/JSONL transformation, endpoint materialization, classification, and similar data processing should be implemented in Python under the project `uv` environment. PowerShell should not carry complex JSONL/business-logic pipelines.

**Why**

Recent failures demonstrated avoidable PowerShell-specific failure modes with no security-research value.

**Do not revert unless**

An existing project tool explicitly requires PowerShell semantics.

---

## AD-06 — `tmp` vs `data/targets` is an artifact contract

**Decision**

```text
tmp = regenerable

data/targets = persistent research fact/artifact layer
```

Do not guess artifact paths.

---

## AD-07 — Do not remove route candidates based on action verbs during discovery

**Decision**

Words such as:

```text
logout
delete
update
switch
reset
remove
```

are discovery metadata, not proof that the route should be excluded from static inventory.

Execution safety is handled later.

---

## AD-08 — Avoid target-specific classifier exceptions

**Decision**

False positives should be fixed through general route semantics, not by adding one-off exclusions for specific `ikuai8.com` strings.

---

# 13. Data / API / Type Contracts

## 13.1 EndpointIR

[FACT — snapshot]

```text
endpoint_id
method
path
source_file
line
is_dynamic
extracted_params
tags
risk_score
confidence
call_signature
```

Purpose:

```text
source-derived endpoint fact
```

It is not a final vulnerability record.

---

## 13.2 Current static report contract

[FACT — observed]

Root object includes:

```text
summary
agent
endpoints[]
```

Each endpoint record observed in the report contains fields such as:

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

---

## 13.3 `http_surface.jsonl`

[FACT — current artifact]

Purpose:

```text
classified HTTP reality derived from the batch URL probe
```

The current corpus contains 1175 HTTPX records with zero JSONL parse errors in the latest successful run.

---

## 13.4 `static_get_endpoints.jsonl`

[FACT — current-session implementation]

Current intended fields:

```text
url
method
endpoint_id
source_file
source_line
risk_score
tags
extracted_params
is_dynamic
confidence
call_signature
```

Invariant for this artifact:

```text
method = GET
url = in-scope concrete URL
no duplicate GET+URL
```

The artifact is a **candidate inventory**, not a vulnerability report.

---

## 13.5 ResearchTask

[FACT — snapshot]

Current governance-aligned identity fields include:

```text
task_id
endpoint_id
coverage_id
hypothesis_id
profile
method
path
```

Stable endpoint identity/reference is preferred over blindly copying the entire EndpointIR into every task object.

---

## 13.6 ResearchCase

[FACT — snapshot]

```text
case_id
endpoint
invariants
hypotheses
attempts
decision
metadata
```

A missing `decision` is meaningful and must not be collapsed into a fabricated default.

---

## 13.7 FindingRecord

[FACT — snapshot]

```text
finding_id
verdict
fingerprint
title
description
root_cause
claimed_root_cause
intended_behavior
rejection_reason
unresolved_blocker
trace
conditions
execution
endpoint_refs
coverage_refs
hypothesis_refs
evidence_refs
severity
confidence
remediation
verification
provenance
```

No final report claim should bypass this authoritative record.

---

## 13.8 ResearchRun

[FACT — snapshot]

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
```

---

# 14. Algorithms / Workflow

## 14.1 Current asset pipeline

```text
Subfinder
    ↓
asset/subdomain corpus
    ↓
Katana
    ↓
katana.jsonl
    ↓
normalize_katana.py
    ↓
urls.jsonl + javascript.jsonl
    ↓
download_javascript.py
    ↓
raw_js
```

The raw Katana artifact is retained as a fact layer and is not treated as a clean asset database.

---

## 14.2 Static analysis

```text
raw_js
    ↓
Tree-sitter / AST
    ↓
EndpointIR
    ↓
RiskEngine
    ↓
ikuai8_endpoints_report.json
```

Current observed baseline:

```text
1221 endpoints/nodes
300 parameter-rich
25 critical labels
59 high labels
368 medium labels
0 evidence records
```

---

## 14.3 Batch HTTP reality

```text
urls.jsonl
    ↓
unique URL set
    ↓
ProjectDiscovery HTTPX
    ↓
http_probe.jsonl
    ↓
classifier
    ↓
http_surface.jsonl
```

The current implementation uses the existing `httpx.exe` under:

```text
C:\dev\bin\httpx.exe
```

and successfully processed 1189 unique URL inputs into 1175 HTTPX records in the current run.

---

## 14.4 Static endpoint materialization

Current algorithm:

```text
ikuai8_endpoints_report.json
        +
http_surface.jsonl
        ↓
collect observed in-scope hosts
        ↓
scan static endpoints
        ↓
GET only
        ↓
extract host from raw_js\<host>\...
        ↓
require host already observed by HTTP surface
        ↓
reject obvious AST / literal noise
        ↓
build concrete https://host/path URL
        ↓
dedupe method + URL
        ↓
validate JSONL
        ↓
static_get_endpoints.jsonl
```

Current failure mode is only in the **semantic route classifier**. The artifact handling and output validation are working.

---

## 14.5 Desired next workflow after classifier cleanup

```text
clean static_get_endpoints.jsonl
        ↓
HTTP reality probe
        ↓
status / content-type / body / redirect classification
        ↓
remove SPA / generic HTML / duplicate shells
        ↓
true API-like surface
        ↓
parameter/content discovery
        ↓
hypothesis generation
        ↓
bounded dynamic validation
```

---

# 15. Verified Tests

## 15.1 Static scan execution

| Test / Command | Purpose | Result | Level |
|---|---|---|---|
| `uv run --project "C:\dev\Invar\src-tauri\python" --python 3.11 python "C:\dev\Invar\scripts\pipeline\scan_pipeline.py" "C:\dev\Invar\tmp\raw_js" -o "C:\dev\Invar\tmp\ikuai8_endpoints_report.json"` | AST/Endpoint baseline | Successful; 1221 nodes | [FACT — historical/current-session] |

## 15.2 Python regression

| Test / Command | Purpose | Result | Level |
|---|---|---|---|
| `$env:PYTHONPATH = "src-tauri/python/src"; uv run --project src-tauri/python python -m unittest discover -s src-tauri/python/tests -p "test_*.py"` | M1–M9 Python regression | `100 tests, OK` | [FACT — snapshot] |

## 15.3 Rust regression

| Test / Command | Purpose | Result | Level |
|---|---|---|---|
| `cargo test --manifest-path src-tauri/Cargo.toml` | Rust unit/contract tests | Passed; warnings=0 | [FACT — snapshot] |

## 15.4 HTTP batch probe

| Test | Purpose | Result | Level |
|---|---|---|---|
| HTTPX batch over `urls.jsonl` | establish HTTP surface | 1189 unique inputs → 1175 records | [FACT — user-reported] |

## 15.5 Static materializer

| Test | Purpose | Result | Level |
|---|---|---|---|
| `materialize_static_get.py` | static GET materialization | 1221 → 146; JSONL validated | [FACT — user-reported] |

## 15.6 Test status interpretation

The current static materializer has no failing structural validation, but **semantic classifier quality is not yet accepted as research-ready**.

Tests must not be “fixed” by deleting test cases or weakening assertions merely to make the pipeline green.

---

# 16. Failure / Pitfall Registry

## F-01 — PowerShell `$host` collided with automatic variable `$Host`

**Problem**

The materialization script failed repeatedly with:

```text
Cannot overwrite variable Host because it is read-only or constant.
```

**Root Cause**

PowerShell variable names are case-insensitive and `$Host` is an automatic read-only variable. The business variable `$host` therefore attempted to overwrite the built-in.

**Wrong Approach**

Using PowerShell for complex transformation logic and inventing short variable names that collide with host/runtime variables.

**Correct Fix**

Move the transformation into Python and use explicit names such as:

```text
source_host
target_host
endpoint_url
endpoint_path
```

**Regression / Prevention**

Do not use PowerShell automatic-variable names as business variables. Prefer Python for JSON/JSONL pipeline logic.

---

## F-02 — Static report path guessed incorrectly

**Problem**

The materializer looked for:

```text
C:\dev\Invar\data\targets\ikuai8.com\ikuai8_endpoints_report.json
```

and failed.

**Root Cause**

The static report is actually written to:

```text
C:\dev\Invar\tmp\ikuai8_endpoints_report.json
```

The artifact boundary was guessed instead of read from the existing pipeline command.

**Wrong Approach**

Infer paths from naming intuition.

**Correct Fix**

Follow the actual producer command and output location.

**Future Prevention**

Artifact paths are contract data, not guesses.

---

## F-03 — JSONL was treated as one JSON document

**Problem**

A PowerShell `ConvertFrom-Json -Raw` attempt produced:

```text
Additional text encountered after finished reading JSON content
```

**Root Cause**

JSONL consists of multiple JSON objects separated by lines; it is not a single JSON document.

**Correct Fix**

Read and parse one line at a time in Python.

---

## F-04 — Static route classifier accepted generic strings containing `/`

**Problem**

The latest 146-candidate output contains obvious literals such as:

```text
100M/10M
Chrome/66
KB/s
Data/
[Getter/Setter]
```

**Root Cause**

The generic rule effectively treated `"/" in path` as sufficient evidence of a route.

**Wrong Approach**

Optimize candidate count by relaxing route semantics.

**Correct Fix**

Strengthen generic route semantics using route-like prefixes, segment structure, placeholder rejection, and display-literal rejection.

**Future Prevention**

Measure classifier precision qualitatively against known false-positive classes before HTTP probing.

---

## F-05 — Template/compiler residue entered URL candidates

**Problem**

Example:

```text
*$0*
```

was materialized as a URL path.

**Root Cause**

Static AST extraction includes template/compiler artifacts that are not literal HTTP routes.

**Correct Fix**

Reject wildcard/template/replacement residue at materialization time.

---

## F-06 — Risk labels were mistaken for vulnerabilities

**Problem**

Static extraction reported 25 critical and 59 high labels.

**Root Cause**

Confusing static heuristic severity with demonstrated impact.

**Correct Rule**

```text
risk → candidate signal only

real vulnerability requires:
observable behavior + security invariant failure + evidence + verification
```

---

## F-07 — WAF blocking was not evidence of traversal

**Problem**

Path traversal payloads against `www.ikuai8.com/download.php` returned `405` WAF blocking responses.

**Correct Interpretation**

Traversal hypothesis remains unconfirmed.

**Wrong Approach**

Continue with encoded/bypass variations merely to defeat the edge filter.

**Correct Rule**

Record `BLOCKED / UNCONFIRMED`; do not turn WAF bypass into an uncontrolled side project.

---

## F-08 — `demo.ikuai8.com/admin/session/list` was an SPA shell, not proof of exposed sessions

**Observed**

The route returned HTML corresponding to an AList V3 SPA.

**Correct Interpretation**

A route-looking URL returning a generic SPA shell is not evidence of the claimed backend API.

**Prevention**

Classify by content and response behavior, not pathname alone.

---

## F-09 — Manual curl can be useful for diagnosis but must not replace the formal research loop

**Decision**

Ad-hoc `curl` may verify a narrow fact during diagnostics, but formal research evidence should flow through the bounded research/evidence path when the finding is being established.

---

## F-10 — Missing subagent result must not be replaced by parent inference

**Correct Rule**

```text
missing child result
    → FAILED / STALLED / UNKNOWN
```

Never claim an independent result that was not actually returned.

---

# 17. Do Not Repeat

```text
Do not guess current artifact paths.
Do not infer current Git state from memory.
Do not use complex PowerShell as a substitute for Python data processing.
Do not use PowerShell automatic-variable names for business state.
Do not parse JSONL as a single JSON document.
Do not treat route strings containing '/' as sufficient proof of an HTTP endpoint.
Do not turn a static risk score into a confirmed vulnerability.
Do not turn a WAF block into evidence of a bypass or traversal flaw.
Do not classify an SPA shell as a backend API merely because the path looks interesting.
Do not remove legitimate routes from discovery merely because their names imply mutation.
Do not create target-specific hardcoded route exceptions.
Do not start HTTP probing on a visibly noisy candidate corpus just to increase activity.
Do not start WAF bypass work without a concrete, authorized research reason.
Do not embed another Agent/LLM runtime into Invar Core.
Do not create a second authoritative state store in Pi.
Do not modify multiple unrelated modules before validating the current change.
Do not move tests into production source directories.
Do not delete or weaken existing tests merely to make them pass.
Do not use `find /` or equivalent unbounded filesystem searches for artifact discovery.
Do not fabricate subagent completion or evidence.
Do not start future roadmap phases early.
```

---

# 18. Invariants

## I-01 — Evidence hierarchy

```text
source / tool output / test
    >
model interpretation
```

## I-02 — Static risk separation

```text
risk label ≠ vulnerability verdict
```

## I-03 — Discovery / execution separation

```text
route discovery does not imply route execution
```

## I-04 — Artifact boundary

```text
tmp = regenerable

data/targets = persistent target artifacts
```

## I-05 — Endpoint provenance

Every materialized candidate must retain:

```text
source_file
source_line
endpoint_id
```

where available.

## I-06 — Scope boundary

Only in-scope hosts may be materialized.

Observed by HTTP tooling does not by itself prove bounty authorization for every discovered subdomain.

## I-07 — Deduplication

`GET + URL` must be unique in `static_get_endpoints.jsonl`.

## I-08 — No placeholder leakage

Static compiler/template residue must not be emitted as concrete HTTP candidates.

## I-09 — Optional semantics

Within Core models:

```text
None
empty list
empty string
explicit absence
```

are not interchangeable unless the contract explicitly defines them as equivalent.

## I-10 — Core authority

```text
Pi proposes
    ↓
Tool Contract
    ↓
Invar Core commits authoritative state
```

## I-11 — Finding promotion

Final knowledge requires:

```text
source trace
+ evidence
+ invariant evaluation
+ demonstrated impact
+ schema validity
+ independent verification
+ no unresolved blocker
```

## I-12 — Directory boundaries

Production code, tests, scripts, temporary artifacts, persistent data, and documentation must remain separated.

---

# 19. Open Issues

## O-01 — Static route classifier is still too permissive

**Impact**

The 146-candidate output still includes display/unit/compiler literals, so HTTP reality probing now would add noise.

**Current Evidence**

Latest successful preview includes:

```text
100M/10M
2.5G/1G
Chrome/66
Data/
KB/s
[Getter/Setter]
*$0*
```

**Known**

The artifact writer, scope filter, dedupe, and structural validation work.

**Unknown**

Exact optimum route-classification heuristic; this requires empirical tuning against the current corpus.

**Next Verification**

The single action in §4.

---

## O-02 — Authorization scope of every discovered subdomain

**Status:** UNKNOWN / CONDITIONAL

**Known**

The user supplied SRC/bounty context for `www.ikuai8.com` and indicated the vendor asset range shown there was unrestricted.

**Unknown**

Whether every discovered `*.ikuai8.com` service is explicitly authorized for active dynamic testing has not been independently verified in the current handoff.

**Rule**

Do not infer dynamic authorization for every discovered subdomain solely from DNS/HTTP discovery.

---

## O-03 — `http_surface.jsonl` classifier semantics

**Status:** PARTIAL

**Known**

The batch classifier successfully categorized 1175 HTTPX records.

**Unknown**

Whether all current category heuristics optimally distinguish SPA shells, APIs, generic HTML, and other live services.

**Next Verification**

After route cleanup, sample the clean static candidates against actual responses.

---

## O-04 — Parameter discovery is not yet applied to the cleaned static GET corpus

**Status:** TODO

The current static report already contains `extracted_params` for some endpoints, but HTTP-side hidden-parameter discovery has not yet been incorporated into the current target workflow.

---

## O-05 — Dynamic vulnerability verification remains unconfirmed

**Status:** TODO / CONDITIONAL

No current finding has reached independent verification and promotion.

---

## O-06 — Live Git provenance

**Status:** UNKNOWN

Current branch, HEAD, staged files, and worktree delta need a live query before any history-sensitive cleanup or reset operation.

---

## O-07 — Current M10 integration state

**Status:** UNKNOWN / STALE SNAPSHOT

An older handoff defined M10 as production CLI integration. The present research session has shifted to practical Web security research, and no current source inspection was available here to re-establish M10 completion state.

Do not revive M10 work merely because it appears in historical documentation.

---

# 20. Environment / Toolchain

## 20.1 OS

[FACT — user environment]

```text
Windows
PowerShell
```

Exact Windows build: UNKNOWN.

---

## 20.2 Python

[FACT — project config]

```text
requires-python = ">=3.10,<3.13"
preferred project runtime = Python 3.11
package manager = uv
```

Project invocation pattern:

```powershell
uv run `
    --project "C:\dev\Invar\src-tauri\python" `
    --python 3.11 `
    python "..."
```

Avoid bare `python` and `pip` for project work.

---

## 20.3 Python dependencies

[FACT — project config snapshot]

```text
pydantic>=2.0.0
tree-sitter>=0.26.0
tree-sitter-javascript>=0.25.0
requests>=2.31.0
httpx>=0.27.0
httpx-socks>=0.8.0
socksio>=1.0.0
```

Installed versions: UNKNOWN.

---

## 20.4 Rust

[FACT — project config snapshot]

```text
crate = Invar-core
version = 0.1.0
edition = 2021
```

Dependencies recorded:

```text
serde = 1.x
serde_json = 1.x
```

Exact installed toolchain versions: UNKNOWN.

---

## 20.5 Discovery tools

[FACT — current workflow]

```text
Subfinder
HTTPX
Katana
```

Installed versions are UNKNOWN unless measured.

Known local HTTPX executable:

```text
C:\dev\bin\httpx.exe
```

---

## 20.6 Pi / model

[FACT — user-reported/snapshot]

```text
Pi workspace = C:\dev\agent-workspace
Pi CLI = v0.85.1
local model = Ornith-1.5-9B-Abliterated-IQ3_M.gguf
inference endpoint = http://127.0.0.1:8080/v1
```

Live availability and exact model-serving configuration: UNKNOWN.

---

# 21. Roadmap

Roadmap is not the current task queue.

## Phase A — Asset and HTTP surface

```text
DONE
Subfinder / Katana / normalization
JS acquisition
static extraction
batch HTTP reality
```

## Phase B — Clean static candidate corpus

```text
CURRENT
route classifier cleanup
```

## Phase C — HTTP reality of static endpoints

```text
TODO
batch probe clean static candidates
classify API / SPA / HTML / auth / forbidden / redirect
```

## Phase D — Parameter/content discovery

```text
TODO
query parameter discovery
hidden route refinement
API method/parameter enumeration where authorized
```

## Phase E — Security hypothesis validation

```text
TODO
IDOR/BOLA
authentication boundaries
authorization boundaries
method/state boundary
input validation
sensitive data exposure
```

## Phase F — Evidence / verification / SRC

```text
TODO
ResearchCase
Evidence
InvariantEvaluator
FindingRecord
Independent Verification
PromotionGate
SRC report projection
```

## Historical engineering roadmap

```text
M1 ResearchTask contract
M2 ResearchRun
M3 CoverageLedger
M4 CandidateFingerprint
M5 FindingRecord / Schema
M6 Independent Verification / PromotionGate
M7 Hunter / Coverage Critic
M8 Multi-run reconciliation
M9 ReportProjector
M10 Production CLI integration
M11 Pi / Skill runtime integration
```

Those historical milestones remain architectural context only. They do not override §3 CURRENT OBJECTIVE.

---

# 22. Recovery Protocol

A fresh AI must perform these actions in order:

```text
1. Read this HANDOFF.md.
2. Read the actual current source files listed in CURRENT SCOPE.
3. Read the current tests that cover those files.
4. Query live Git branch / HEAD / worktree.
5. Verify artifact paths and file existence under C:\dev\Invar.
6. Reconcile the live source against this handoff.
7. Verify CURRENT OBJECTIVE.
8. Execute only NEXT SINGLE ACTION.
9. Stop and wait for real command output.
10. Update HANDOFF after a meaningful state transition.
```

## 22.1 Conflict resolution

### Handoff vs source

```text
latest current source
    >
historical handoff
```

Record the contradiction instead of silently rewriting history.

### Handoff vs tests

```text
latest real tests
    >
historical snapshot claims
```

### Handoff vs command output

```text
actual command output
    >
assumption
```

### Missing information

Use:

```text
UNKNOWN
```

Do not fabricate a value to make the document look complete.

---

# 23. AI Collaboration Protocol

## 23.1 Language

```text
Chinese first
```

Code identifiers, APIs, CLI flags, file paths, and schema names remain exact.

## 23.2 Working rhythm

```text
ONE logical action
    ↓
user executes / tool executes
    ↓
real output
    ↓
analysis
    ↓
next action
```

Do not provide a bundle of unrelated unverified modifications.

## 23.3 User executes commands

The current human/AI contract is:

```text
AI designs the smallest bounded action.
User runs it in the Windows environment.
User returns exact terminal output.
AI interprets evidence.
```

Never assume command success.

## 23.4 Python

Use:

```text
uv
project Python
```

Do not use:

```text
pip
bare python
```

## 23.5 Windows file modification

For large complete-file replacements, project convention permits:

```powershell
@'
<complete file>
'@ | Set-Content -Encoding UTF8 "C:\dev\Invar\..."
```

However, Python is preferred for transformation logic and artifact generation.

## 23.6 Subagents

Default subagent role:

```text
read-only scout / auditor / reviewer
```

Rules:

```text
direct child result = usable evidence
missing child result = FAILED / STALLED / UNKNOWN
no artifact-path guessing
no unbounded filesystem discovery
no parent substitution pretending to be independent verification
```

## 23.7 Reporting format

Default AI output after takeover:

```text
# 1. 当前目标
# 2. 黄金标准出处溯源
# 3. 原理与解说
# 4. 执行内容

## 反馈要求
```

The feedback section should request only the output required for the current single action.

---

# 24. Security / Sensitive Data Boundary

## 24.1 Authorization

Current research is described as authorized SRC work by the user.

The user supplied bounty context for:

```text
vendor: 全讯汇聚网络科技（北京）有限公司
primary target: www.ikuai8.com
```

The user reported the vendor page displayed an unrestricted asset-range statement.

This is a user-provided authorization reference, not an independently verified authorization database.

Therefore:

```text
Publicly discoverable
    ≠
automatically authorized for every action
```

Before active dynamic testing of a discovered subdomain, verify that the specific asset is within the allowed program scope.

## 24.2 Non-destructive boundary

Default dynamic research posture:

```text
read-only
low-rate
minimal requests
minimal data
minimal impact
no credential abuse
no destructive mutations
no bulk extraction
no WAF bypass as an objective
```

## 24.3 Sensitive data

Never write into HANDOFF:

```text
real passwords
real tokens
cookies
JWTs
private keys
authentication headers
personal secrets
```

Use:

```text
redacted
fixture
mock
environment variable
localhost
controlled test account
```

---

# 25. Reproducibility Status

## `PARTIALLY REPRODUCIBLE`

[DERIVED]

Reason:

```text
The research pipeline, artifact paths, static/HTTP outputs, major architectural contracts,
known failure modes, and the exact current single objective are sufficiently recorded.
```

But the following are not live-verified in this handoff generation:

```text
current Git branch
current Git HEAD
current working-tree delta
exact current source contents of all referenced files
current installed tool versions
current Pi process/model-server state
exact authorization scope of every discovered subdomain
fresh full Python regression after all latest modifications
fresh Rust regression after all latest modifications
```

Therefore the status must not be upgraded to `FULLY REPRODUCIBLE`.

---

# 26. Handoff Self-Check

```text
[x] New AI knows the canonical Invar root.
[x] New AI knows the Pi workspace.
[x] New AI knows the current practical mission.
[x] New AI knows the current unique objective.
[x] New AI knows the single next action.
[x] New AI knows the exact input artifacts for that action.
[x] New AI knows the exact output artifact for that action.
[x] New AI knows the latest successful materializer result.
[x] New AI knows why the 146-row result is not yet research-clean.
[x] New AI knows the known false-positive classes.
[x] New AI knows discovery and execution must remain separate.
[x] New AI knows static risk is not vulnerability proof.
[x] New AI knows the HTTP batch surface baseline.
[x] New AI knows the static scan baseline.
[x] New AI knows the artifact boundary between tmp and data/targets.
[x] New AI knows the Python runtime contract.
[x] New AI knows the historical M1–M9 architecture context.
[x] New AI knows the historical M10 context is stale/uncertain for the current mission.
[x] New AI knows the recent PowerShell and path-guessing failures and their root causes.
[x] New AI knows the current security boundary and authorization uncertainty.
[x] New AI knows which information is UNKNOWN.
[x] New AI knows how to reconcile handoff conflicts with live source/tests/output.
[x] New AI knows the one-action collaboration protocol.
[x] New AI will not start the HTTP reality stage during the current classifier-cleanup action.
```

---

# 27. Final Recovery Anchor

A new AI should resume at exactly this state:

```text
CURRENT STATE

1221 static endpoints
        +
1175 HTTP surface records
        ↓
static GET materialization
        ↓
146 mechanically valid candidates
        ↓
KNOWN FALSE POSITIVES REMAIN
        ↓
CURRENT OBJECTIVE:
 tighten route classifier
        ↓
NEXT SINGLE ACTION:
 modify materialize_static_get.py classifier,
 rerun once, stop
```

Do not resume by:

```text
rebuilding M1–M9
redesigning Invar
rewriting the AST extractor
rewriting the Agent
starting M10 from scratch
starting M11
probing the target again before classifier cleanup
bypassing WAF
claiming a vulnerability from a risk label
```

The recovery principle is:

```text
Real artifacts establish state.
Current source establishes implementation.
Tests establish behavior contracts.
Architecture decisions constrain changes.
Evidence establishes security conclusions.
One logical action advances the project.
```

# END OF HANDOFF
