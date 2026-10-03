# AI Development Handoff Specification

## 0. Handoff Metadata
| Item | Value | Level | Evidence |
|---|---|---|---|
| Project | Invar | [FACT] | `pyproject.toml` / `Cargo.toml` |
| Snapshot Date | 2026-10-03 20:00 JST | [FACT] | System Time |
| Canonical Root | `/home/zhz/Invar` | [FACT] | PWD |
| Test Baseline | **287 passed in ~0.60s** | [FACT] | `uv run pytest` output |
| LLM Backend | `127.0.0.1:8080/v1` (Ornith 35B) | [FACT] | `/health` probe |

## 1. Project Identity
[FACT] Invar 是一套 **AI 辅助安全研究与动态实证确权机架 (Domain Verification Harness)**。
[DERIVED] 系统已跨越“漏洞扫描器”阶段，正式演进为对标 Shannon、Strix 与 PentAGI 的 **Bug Bounty / SRC 自动化研究与交付系统**。核心哲学为：LLM 仅作为行动规划器 (Action Proposer)，物理发包证据 (Physical Evidence) 才是唯一裁决真理 (Truth Oracle)。

## 2. Current Mission
[DECISION] **路线 B：智能体多轮自适应追击与 PoC 飞轮 (Autonomous Multi-Turn Security Agent & PoC Flywheel)**。
当前核心任务已从“证明系统能拒绝误报”升级为“证明系统能发现已知漏洞、实锤它、独立复现它，并生成研究员可直接提交的高质量漏洞包”。

## 3. Current Objective
[FACT] **Phase 9.7: Bounty Readiness Validation (桌面端与端到端同源事实闭环)**。
底层核心机架（RoE 门禁、身份矩阵、跨 Run 隔离、404 细分、PoC 飞轮、战报组合器）已全部在契约层闭环。当前唯一目标是：将 `apps/desktop` (React/Tauri) 产品壳与底层 Python 机架物理贯通，断言 UI 显示的结论与 `execution.jsonl` / `BOUNTY-SUBMISSION.md` 严格同源。

## 4. Next Single Action
[TODO] **建立 Tauri IPC 战报读取契约**。
当前唯一下一动作：
在 `crates/core` 或 `apps/desktop/src-tauri` 中编写 Rust IPC Command，读取 `artifacts/reports/targeted_audit_phase9_p1_canonical/execution.jsonl` 与 `findings.json`，将其反序列化为强类型 Struct 并传递给 React 前端，验证前端 UI 渲染的数据与底层 Canonical ExecutionRecord 绝对一致。

## 5. Current Scope
[FACT] 当前正在修改/研究的边界：
* `apps/desktop/src-tauri/src/` (Rust Tauri IPC Commands)
* `apps/desktop/src/` (React UI 状态管理)
* `crates/core/src/orchestrator.rs` (跨语言战报解析契约)

## 6. Out of Scope
[DECISION] 当前阶段明确禁止触碰：
* ❌ Python 核心逻辑 (`invariant_evaluator.py`, `domain_contracts.py` 等已锁死的契约)
* ❌ 静态流水线 Phase 0~4 (Subfinder/Katana/AST)
* ❌ 引入新的大模型推理框架或 Agent 规划逻辑
* ❌ 浏览器/DOM 攻击面 (Browser Surface 属于 Phase 9.8)

## 7. Last Known Good State
```text
Last Known Good State
    ↓
PYTHONPATH="python/packages/core/src" uv run --project python python -m pytest -q
    ↓
287 passed / 0 failed in 0.60s
    ↓
warnings = 0
    ↓
已验证的主要行为：
1. 跨 Run 证据隔离与 128-bit 哈希防碰撞
2. 404 语义正交细分 (Route/Resource/HiddenByAuthz)
3. Scope/RoE 前置发包门禁
4. 多主体身份上下文矩阵 (IdentityMatrix) 与跨租户 BOLA 差分
5. 独立 PoC 飞轮与 BOUNTY-SUBMISSION.md 战报生成
```

## 8. Completed Work
| Item | Status | Evidence | Files | Notes |
| ---- | ------ | -------- | ----- | ----- |
| **Canonical ExecutionRecord** | DONE | `test_execution_trace.py` | `execution_trace.py` | `attempts` 列表与 `decision_sufficiency` 完整投影至 JSONL，实现单一事实来源。 |
| **跨 Run 证据隔离** | DONE | `test_cross_run_evidence_isolation_contract.py` | `domain_contracts.py` | 建立五维采纳性门禁，杜绝历史证据隐式污染当前 Run。 |
| **404 语义正交细分** | DONE | `test_not_found_subclassification_contract.py` | `domain_contracts.py`, `invariant_evaluator.py` | 拆分为 ROUTE_NOT_FOUND, RESOURCE_NOT_FOUND, HIDDEN_BY_AUTHZ。 |
| **Scope / RoE 前置门禁** | DONE | `test_roe_enforcement_gate_contract.py` | `domain_contracts.py` | 物理发包前强制拦截越界域名、排除路径与非授权动词。 |
| **多主体身份矩阵** | DONE | `test_identity_matrix_contract.py` | `domain_contracts.py` | 引入 `AuthPrincipal`，实现跨租户 BOLA/IDOR 物理差分断言。 |
| **赏金 PoC 飞轮与战报** | DONE | `test_bounty_poc_flywheel_contract.py` | `domain_contracts.py`, `reporting.py` | 自动合成 cURL PoC、独立复验并生成 `BOUNTY-SUBMISSION.md`。 |

## 9. Changed Files
### Modified
* `python/packages/core/src/harness/domain_contracts.py` (注入 RoEGate, IdentityMatrix, AuthPrincipal, BountySubmissionPackage, EvidenceRef)
* `python/packages/core/src/harness/invariant_evaluator.py` (重构 404 单射理据，修复 HIDDEN_BY_AUTHZ 语义倒置)
* `python/packages/core/src/harness/execution_trace.py` (修复 attempts 投影断层，修复 Enum 序列化污染)
* `python/packages/core/src/harness/reporting.py` (挂载 `BOUNTY-SUBMISSION.md` 投影器)
* `python/packages/core/src/harness/verification_gate.py` (支持 Candidate 独立双盲复验)
* `python/tests/test_*.py` (新增 6 大契约测试套件，总计 287 项)

## 10. Current Architecture
[FACT] 系统已形成严格的“漏洞研究与证据裁决内核”：
```text
AST / Research Tasks
        ↓
Scope / RoE Enforcement Gate (越界物理阻断)
        ↓
Identity Matrix (多主体/多租户上下文)
        ↓
Multi-round Pursuit & LLM Action Proposal
        ↓
Physical Evidence (绑定 AuthPrincipal)
        ↓
Denial Subclassification (含 404 正交细分)
        ↓
Evidence Sufficiency & Invariant Evaluation
        ↓
Canonical ExecutionRecord (单一事实来源)
        ↓
Cross-Run Evidence Gate (历史对账与隔离)
        ↓
Independent Verification & PoC Synthesis
        ↓
Bounty Submission Package (SARIF / OpenVEX / MD)
```

## 11. Architecture Decisions
* **Decision**: `attempts_count` 必须由 `len(attempts)` 物理派生。
  * **Why**: 杜绝标量与数组双源维护导致的投影断层 (Projection Gap)。
  * **Do not revert unless**: JSONL 结构发生根本性重构。
* **Decision**: `HIDDEN_BY_AUTHZ` 单凭标头只能是 `PARTIAL + inconclusive`。
  * **Why**: 必须具备物理差分对照事实 (`is_auth_differential=True`) 方准晋升为 `SUFFICIENT + confirmed`，严禁主观过度确权。
  * **Do not revert unless**: 形式化状态机偏序规则被推翻。
* **Decision**: 跨 Run 证据必须显式声明并经过五维门禁核验。
  * **Why**: 保证 State Freshness，防止 Run A 的证据悄悄污染 Run B 的裁决。

## 12. Data / API / Type Contracts
* **`EvidenceRecord`**: 必须包含 `run_id`, `task_id`, `attempt_id`, `evidence_id` (128-bit hash), `content_hash`, `principal`。
* **`AuthPrincipal`**: 必须包含 `principal_id`, `role`, `tenant_id`, `credential_fingerprint`。
* **`EvidenceRef`**: 必须包含 `admissibility` (`CURRENT_RUN_ONLY`, `CROSS_RUN_EXPLICIT`, `CROSS_RUN_REJECTED`)。
* **`BountySubmissionPackage`**: 必须包含 `step_by_step_poc`, `poc_code`, `security_impact`, `remediation`。

## 13. Algorithms / Workflow
[FACT] 赏金 PoC 飞轮工作流 (The PoC Flywheel)：
```text
Input: Known-Vuln Endpoint + Identity Matrix
→ Execution: Tenant B requests Tenant A's resource
→ Observation: 200 OK with leaked data
→ Decision: VULNERABLE + SUFFICIENT
→ Synthesis: Generate reproducible cURL PoC
→ Verification: IndependentVerifier replays PoC -> VERIFIED
→ Promotion: PromotionGate checks 8 invariants -> CONFIRMED
→ Output: BOUNTY-SUBMISSION.md
```

## 14. Verified Tests
* `test_execution_trace.py`: 验证 `attempts` 列表投影与 `sanitize()` 枚举无损解包。
* `test_cross_run_evidence_isolation_contract.py`: 验证五维采纳性门禁与零隐式穿透。
* `test_not_found_subclassification_contract.py`: 验证 404-R, 404-E, 404-H 的正交分类与单射理据。
* `test_roe_enforcement_gate_contract.py`: 验证越界域名、排除路径与危险动词的物理阻断。
* `test_identity_matrix_contract.py`: 验证跨租户 BOLA 差分断言与主体血统绑定。
* `test_bounty_poc_flywheel_contract.py`: 验证从物理击穿到法定赏金包导出的全链路飞轮。

## 15. Failure / Pitfall Registry
* **Problem**: `(str, Enum)` 在 Python 3.11+ 序列化时泄漏类名前缀（如 `EvidenceSufficiency.SUFFICIENT`）。
  * **Root Cause**: `isinstance(value, str)` 检查排在了 `hasattr(value, "value")` 前面。
  * **Correct Fix**: 在 `sanitize()` 中优先解包 `.value`。
* **Problem**: `Candidate.to_finding_record()` 触发 `NameError: name 'Verdict' is not defined`。
  * **Root Cause**: 方法默认实参 `verdict: Verdict = Verdict.CONFIRMED` 在类加载时提前求值，引发时序冲突。
  * **Correct Fix**: 改为 `Optional[Verdict] = None` 并在函数体内延迟解包。

## 16. Do Not Repeat
* ❌ **不要把 404 强行算作安全**：必须细分为 ROUTE / RESOURCE / HIDDEN_BY_AUTHZ，并诚实降级为 INCONCLUSIVE。
* ❌ **不要让 `attempts_count` 成为第二个事实源**：必须严格等于 `len(attempts)`。
* ❌ **不要在 `bash -c` 中嵌套单引号**：严格遵守终端净化律，复杂脚本必须 `cat << 'EOF'` 落盘。
* ❌ **不要猜接口**：遇到骨架态代码，必须使用 `tools/context/inspect.sh` 拉取真实源码。

## 17. Invariants
* **Single Source of Truth**: `execution.jsonl` 必须能独立重建本次审计的全部物理事实。
* **Status ↔ Sufficiency Coherence**: `vulnerable` 必 `SUFFICIENT`；`confirmed` 必 `{SUFFICIENT, PARTIAL}`；`inconclusive` 必 `{INSUFFICIENT, PARTIAL}`。
* **State Freshness**: 当前 Run 的裁决只依赖当前 Run 的物理观测，除非显式通过跨 Run 门禁。

## 18. Open Issues
* **Issue**: Browser / DOM 攻击面缺失。
  * **Impact**: 当前系统极强于 HTTP/API，但无法处理 SPA 状态、CSRF、postMessage 等纯前端漏洞。
  * **Next Verification**: Phase 9.8 需引入 Browser Agent / Playwright 观测层。
* **Issue**: 缺乏真实漏洞基准集 (Known-Vuln Corpus)。
  * **Impact**: 287 项测试全绿只能证明契约严密，不能证明对真实 0-day 的召回率。
  * **Next Verification**: Phase 9.9 需建立本地靶场 Benchmark。

## 19. Environment / Toolchain
* **OS**: Linux Mint 22.3 Cinnamon (x86_64)
* **Language**: Python 3.12.3 (uv 0.12.21), Rust 1.99.0 (Edition 2021/2024)
* **Local LLM**: `127.0.0.1:8080/v1` (Ornith 35B GGUF)
* **LLM Config**: `INVAR_LLM_MAX_TOKENS=8192`, `INVAR_LLM_TIMEOUT=120`

## 20. Roadmap
* **Phase 9.7**: Bounty Readiness Validation (桌面端与端到端同源事实闭环) ➔ **[CURRENT]**
* **Phase 9.8**: Browser / Web UI Surface (浏览器攻击面)
* **Phase 9.9**: Benchmark + Known-Vuln Corpus (真实漏洞基准集)
* **Phase 10.0**: Authorized Submission Adapter (平台化自动提交适配器)

## 21. Recovery Protocol
新 AI 接手后，必须严格执行：
1. 读取本 `HANDOFF.md`。
2. 运行 `PYTHONPATH="python/packages/core/src" uv run --project python python -m pytest -q` 验证 287 项测试全绿。
3. 验证 `CURRENT OBJECTIVE` (Phase 9.7 桌面端贯通)。
4. 只执行 `NEXT SINGLE ACTION` (编写 Tauri IPC 读取战报)，绝不提前发散或重构 Python 内核。

## 22. AI Collaboration Protocol
* **中文优先**：专业术语首次双语，后续纯中文。
* **单步推进**：一次只推进一个逻辑动作，先测试后继续。
* **剪贴板零摩擦**：所有交付命令末尾强制挂载 `2>&1 | tee /dev/tty | xclip -sel clip`。
* **脚本落盘**：复杂逻辑必须通过 `cat << 'EOF' > tmp/xxx.py` 落盘执行。

## 23. Security / Sensitive Data Boundary
* 严禁在交接文档中记录真实 Token、Cookie 或私钥。
* 物理发包测试必须使用 `localhost` 或已授权的 `ikuai8.com` fixture。
* `EvidenceRecord` 中的敏感凭据必须经过 `sanitize()` 脱敏为 `<REDACTED>`。

## 24. Reproducibility Status
**FULLY REPRODUCIBLE**
核心接口、算法、环境、依赖和 287 项测试均已确认。`SourceRef` 已完整实现 `commit` + `worktree_dirty` + `diff_hash` 的工业级血统采样，任何 Run 均可 100% 字节级复现。

## 25. Handoff Self-Check
- [x] 一个新 AI 是否知道当前到底在做什么？ (Phase 9.7 桌面端同源事实闭环)
- [x] 一个新 AI 是否知道最后一次成功状态？ (287 passed, 0.60s)
- [x] 一个新 AI 是否知道最后修改了哪些文件？ (domain_contracts, invariant_evaluator, execution_trace 等)
- [x] 一个新 AI 是否知道为什么这么设计？ (防止历史证据污染，确保物理事实与理据单射)
- [x] 一个新 AI 是否知道哪些行为不能破坏？ (Single Source of Truth, Status ↔ Sufficiency 偏序)
- [x] 一个新 AI 是否知道当前唯一下一步？ (编写 Tauri IPC 读取 execution.jsonl)
- [x] 一个新 AI 是否知道当前阶段不能做什么？ (禁止修改 Python 核心契约与静态流水线)
- [x] 一个新 AI 是否知道如何运行测试？ (`uv run pytest`)
- [x] 一个新 AI 是否知道哪些信息尚未确定？ (Browser 攻击面与真实漏洞召回率)
- [x] 一个新 AI 是否能够在源码缺失部分情况下依据文档继续恢复？ (是，契约已详尽记录)
```
