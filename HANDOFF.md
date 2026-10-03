# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot & Autonomous Agent Handover Contract
> **Project:** Invar (AI-Assisted Security Research & Invariant Verification Harness)
> **Snapshot Date:** 2026-10-03 (Asia/Tokyo)
> **Canonical Repository Root:** `/home/zhz/Invar`
> **Snapshot Authority:** 252 项全绿单元测试断言、真实物理发包战报 (`phase8_p1_canonical`)、`llama-server` 本地推理底账及 Git Commit 记录。
> **Strategic Alignment:** 彻底中止路线 A（机械刷 54 个 P2 扫描批次），全力转向**路线 B（构建“假说 -> 自主设计下一步实验 -> 真实多轮发包 -> 生成 PoC”的真正渗透智能体飞轮）**。

---

## 0. Handoff Metadata

| Item | Value | Level | Evidence |
|---|---|---|---|
| Project | Invar | [FACT] | `Cargo.toml` / `pyproject.toml` |
| Repository Root | `/home/zhz/Invar` | [FACT] | 终端物理 `PWD` |
| OS / Kernel | Linux Mint 22.3 Cinnamon (x86_64, Ubuntu 24.04 LTS upstream) | [FACT] | 宿主系统事实 |
| CPU | Intel Core i5-13600KF (8 P-Cores pinned) | [FACT] | `3-pi-agent-llama.md` 底账 |
| RAM | 32 GB DDR4/DDR5 | [FACT] | 宿主系统事实 |
| GPU | NVIDIA GeForce RTX 3060 12GB GDDR6 (Driver 595.91+, CUDA 12/13) | [FACT] | `nvidia-smi` 物理证据 |
| Python Toolchain | Python 3.12.3 via `uv 0.12.21` (严禁系统 pip) | [FACT] | `python/pyproject.toml` |
| Rust Toolchain | Rust 1.99.0 / Cargo 1.99.0 (Edition 2021/2024) | [FACT] | `Cargo.toml` |
| Node / Package | Node.js v24.21.0 / pnpm 12.8.1 | [FACT] | 前端应用壳工作区 |
| Local LLM Backend | `llama-server` on `http://127.0.0.1:8080/v1` | [FACT] | `/health` 探针返回 `{"status":"ok"}` |
| Local LLM Model | `Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf` | [FACT] | `/v1/models` 物理响应 |
| LLM Tuning | `-ngl 99 --n-cpu-moe 28 -c 160000 --reasoning on -fa on --spec-type draft-mtp` | [FACT] | `~/llama_38B.sh` 生产脚本 |
| LLM Max Tokens | `INVAR_LLM_MAX_TOKENS=8192` (4096 default, 8192 full budget) | [FACT] | `model_provider.py` & Pi `models.json` |
| Global Pi Agent | `~/.pi/agent/` (earendil-works/pi v0.99.2, 共享本地 35B 推理服务) | [FACT] | 外轨结对编程代理事实 |
| Authorized Target | `ikuai8.com` (已获授权 Bug Bounty / SRC 测试范围) | [FACT] | `data/targets/ikuai8.com/` |
| Test Baseline | **252 passed in 0.59s** (100% 纯绿) | [FACT] | `uv run pytest` 最新战报 |
| Last Known Good State | `commit 7ca00075d90b4b3f317ed3eb1aa5970dbccd3271` + Phase 8.4 Canonical Run | [FACT] | Git 历史与真实物理战报 |
| Reproducibility Status | **FULLY REPRODUCIBLE** | [FACT] | 环境、依赖、全量单测、本地模型与真实靶场发包均经验证 |

---

## 1. Project Identity

[FACT]

Invar 不是普通的漏洞扫描器，也不是单纯的聊天机器人，而是**AI 辅助安全研究与动态实证确权机架 (Domain Verification Harness)**。

它的核心系统工程公式：
$$\mathbf{Agent = Model (灵魂/推理) + Invar\ Harness (机架/不变量/证据链)}$$

* **Invar 与 Pi Agent 的分工**：
  * **Pi Agent** 是外轨人机伴生工程代理 (Coding Agent)，辅助开发者在终端中读写代码、执行重构；
  * **Invar Harness** 是内轨受控实证机架，通过 AST 契约提炼、有限动作空间 (F1~F9)、假说驱动安全不变量 (Security Invariants) 与双主体差分对账，向真实网络发包并生成具备法定效力的 OpenVEX 与 OASIS SARIF 凭证。

---

## 2. Current Mission: 终极蓝图对账与战略纠偏

根据 `真正想做的是.md`，系统的终极形态是：
```text
渗透入门者 ──► 输入已授权目标 ──► AI 理解目标并发现攻击面 ──► 形成漏洞假说
  ──► 自主设计下一步实验 ──► 真实发包 ──► 根据结果调整策略 (核心研究飞轮)
  ──► 漏洞证实 ──► 生成可复现 PoC ──► 独立证据链复核 ──► 生成战报 ──► 人工确认提交
```

* **战略决断 [DECISION]**：
  * **坚决放弃路线 A**：停止盲目刷跑 54 个 P2 规则批次任务。单纯刷批次只会让系统退化为死板的“单发扫描器 (Scanner)”；
  * **全面进入路线 B**：将已打通的单发实证引擎，升华为**“具有自主推进能力、能根据上一轮发包结果发起多轮追击、并产出 PoC 脚本”的真正渗透智能体**！

---

## 3. Current Objective

### CURRENT OBJECTIVE

[DECISION]

**打通“大模型反思建议 ➔ 自主派发第 2 轮物理追击发包 ➔ 动态策略调整 ➔ 导出独立 PoC 脚本”的多轮动态研究闭环 (Multi-Turn Autonomous Research & PoC Flywheel)。**

以已捕获真实 405 动词拒绝且大模型已给出完美推理建议的密码重置接口 `POST /users/${H}/reset-password` 为纵深攻坚靶点，让系统真正执行大模型提出的“改换 GET 动词探测”建议，而不是在单次发包后草草收工。

---

## 4. Next Single Action

### NEXT SINGLE ACTION

[TODO]

在 `python/tests/test_research_loop_contract.py` 中编写 TDD RED 失败契约测试：**断言当首轮探测遭遇服务端策略阻断 (如 405 Method Not Allowed) 且大模型反思推导出明确动作建议 (Actionable Steer / 动词变换) 时，研究循环必须自主调度第 2 轮变异实验发包，并在突破或确权后产出可独立执行的 PoC 发包复现代码。**

---

## 5. Current Scope

当前仅允许在以下核心研究循环模块内展开工作：
```text
python/packages/core/src/agent/
    research_loop.py            # 研究循环多轮调度状态机 (对齐 pi-agent-core 纯函数循环)
    research_controller.py      # Control Plane 有限动作选择与大模型决策解析
    model_provider.py           # 本地 35B 大模型通信驱动

python/packages/core/src/harness/
    sandbox_executor.py         # 自适应沙箱物理发包中枢
    domain_contracts.py         # ResearchTaskContext, EvidenceChain, PoC Package 契约

python/tests/
    test_research_loop_contract.py # 多轮追击与 PoC 契约测试
```

---

## 6. Out of Scope

当前阶段严禁触碰：
* ❌ 严禁启动 Phase 8.5 P2 的 54 个任务批量跑批（严禁为了凑数字浪费算力）；
* ❌ 严禁修改 Rust 工作区 (`crates/core`)；
* ❌ 严禁触碰前端应用壳 (`apps/desktop/` Tauri/React)；
* ❌ 严禁重构静态流水线 Phase 0~4 (Subfinder/Katana/AST 已稳定)；
* ❌ 严禁破坏已全绿的 252 项单元测试断言；
* ❌ 严禁针对单个测试用例入参硬编码 `if "xxx"` 特判。

---

## 7. Last Known Good State (LKG)

```text
Commit Hash: 7ca00075d90b4b3f317ed3eb1aa5970dbccd3271 + Phase 8.4 Canonical Worktree
Full Test Suite: 252 passed in 0.59s (100% GREEN)
Hardware Topology: RTX 3060 12GB (11.2GB allocated, Zero OOM)
Local LLM: llama-server online (127.0.0.1:8080), Ornith 35B, Max Tokens=8192
P1 Real Audit Artifact: artifacts/reports/phase8_p1_canonical/
    ├── Task 1-3 (/fs/*)      : CONFIRMED (140~148ms, html_fallback 伪 200 被识破)
    ├── Task 4 (reset-password): CONFIRMED (9.7s 35B CoT 反思完成，405 动词拒绝收敛)
    └── Task 5 (audit-logs)   : INCONCLUSIVE (S3 404 NoSuchKey，依法诚实记录为未决)
Weighted Coverage: 66.67% (2/3 责任单元完全闭环，真实可信)
```

---

## 8. Completed Work Table

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| **Phase 7 分流语义治理** | DONE | `test_triage_dispatcher_semantics.py` 绿通 | `triage_dispatcher.py` | 消除 `state_mutation`，对齐 `authorization` 与 `H-AUTH-1` |
| **ResearchTaskContext 契约** | DONE | `test_research_task_context_contract.py` 3/3 绿通 | `domain_contracts.py` | 静态端点 `EndpointIR` 与动态任务意图彻底解耦 |
| **假说驱动安全不变量** | DONE | 离线沙箱全链路演练全绿 (`[🎉 演练全绿]`) | `sandbox_executor.py` | 消除 `if "admin" in path`，由假说驱动挂载 `auth_boundary` |
| **主审计管道意图透传** | DONE | Phase 8.2 单任务真实实证 100% COVERED | `run_targeted_audit.py` | 建立 `task_context` 端到端跨层透传管道 |
| **测试桩与配置中心补齐** | DONE | 核心回归 19/19 绿通 | `configs/profiles/research.toml` | 补齐场景画像配置，对齐 `fake_probe` 契约签名 |
| **上游端点词法清洗门禁** | DONE | `test_triage_sanitization_contract.py` 3/3 绿通 | `triage_dispatcher.py` | 过滤大段中文法律条款与 `this._instance...` 客户端代码 |
| **RFC 3986 路径规范化** | DONE | 任务库从 86 纯化为 81，P1 从 9 纯化为 5 | `triage_dispatcher.py` | 采用标准 `urlsplit`，彻底剔除 `?${` 字符串截断特判 |
| **RFC 9110 405 动词拒绝收敛** | DONE | `test_invariant_evaluator_contract.py` 2/2 绿通 | `invariant_evaluator.py` | 405 确定性确权为未授权安全拦截 (`confirmed`) |
| **35B 大模型 8192 预算打通** | DONE | Task 4 耗时 9.7s 输出高质量 CoT 决策 | `model_provider.py` | 默认提升至 4096 并支持 8192 环境变量覆盖，修复 f-string Bug |
| **全量单元回归保障** | DONE | `252 passed in 0.59s` | `python/tests/` | 每次重构全量单测零回归 |

---

## 9. Changed Files

### Modified (已纳入 Git 追踪或工作区核心实现)
* `python/packages/core/src/harness/domain_contracts.py`：新增 `ResearchTaskContext` 强类型实体，为 `ResearchCase` 扩充上下文容器；
* `python/packages/core/src/harness/triage_dispatcher.py`：实现 `_is_valid_api_path` 词法门禁，集成 `urlsplit` 规范化，强化 `_extract_subsystem`；
* `python/packages/core/src/harness/invariant_evaluator.py`：收敛 RFC 9110 405 动词拒绝，剔除 `is_sensitive` 字符串特判与 `NoSuchKey` 特调；
* `python/packages/core/src/harness/sandbox_executor.py`：重构假说驱动不变量挂载（作用域严格隔离在 `_create_research_case`）；
* `python/packages/core/src/harness/research_adapter.py`：全流程透传 `task_context`；
* `python/packages/core/src/agent/model_provider.py`：生成预算升级至 4096/8192，修复截断报错 f-string；
* `python/scripts/run_targeted_audit.py`：审计循环显式提取并注入 `task_context`；
* `python/tests/test_model_provider.py`：增加环境变量隔离与 4096 契约断言；
* `python/tests/test_research_task_adapter.py` & `test_research_worker.py`：对齐测试桩签名；
* `artifacts/reports/targeted_research_tasks.json`：原子重装配后的 81 个纯净种子库；
* `HANDOFF.md`：本档案。

### Added
* `configs/profiles/research.toml`：声明式科研场景画像配置文件；
* `python/tests/test_research_task_context_contract.py`：任务意图解耦契约测试套件 (3 项测试)；
* `python/tests/test_triage_sanitization_contract.py`：词法清洗门禁契约测试套件 (3 项测试)；
* `python/tests/test_invariant_evaluator_contract.py`：405 动词拒绝与假说驱动求值测试套件 (2 项测试)。

---

## 10. Current Architecture

```text
[Authorized Target: ikuai8.com]
       │
       ▼ (Phase 0~3: Subfinder + HTTPX + Katana + JS Download)
[tmp/raw_js/*.js (物理代码库)]
       │
       ▼ (Phase 4: Tree-sitter AST Extractor)
[tmp/ikuai8.com_endpoints_report.json (1097 Endpoints)]
       │
       ▼ (Phase 5~6: System-1 0.6B ONNX 推演 + 双轨比对)
[artifacts/reports/triage_pools_v2.json (Pool A + Pool B)]
       │
       ▼ (Phase 7: TriageDispatcher 词法清洗 + RFC 3986 urlsplit)
[artifacts/reports/targeted_research_tasks.json (81 Clean Tasks)]
       │
       ▼ (Phase 8: System-2 自适应沙箱审计流水线)
┌────────────────────────────────────────────────────────────────────────┐
│                        run_targeted_audit.py                           │
│                                                                        │
│   TriageTask ──► ResearchTaskContext (H-AUTH-1 / authorization)        │
│                         │                                              │
│                         ▼                                              │
│       AdaptiveSandboxExecutor._create_research_case()                  │
│       [挂载 SecurityInvariant: auth_boundary]                          │
│                         │                                              │
│                         ▼                                              │
│         HttpTransport.request() 物理发包 (毫秒级测时)                   │
│                         │                                              │
│                         ▼                                              │
│       【核心分水岭：单发扫描 vs 多轮追击智能体】                         │
│   • 命中 405/403/阻断 ──► 唤醒本地 Ornith 35B (8192 Tokens CoT)        │
│   • 模型输出战略建议: "改换 GET 动词探测"                              │
│   • [当前已达]: 存入日志 ──► InvariantEvaluator 判定 confirmed         │
│   • [路线B目标]: ControlPlane 调度第 2 轮真实发包 ──► 追击至 PoC 闭环    │
│                         │                                              │
│                         ▼                                              │
│         ReportProjector 导出 6 大交付物 (SARIF + OpenVEX)              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Architecture Decisions

### Decision 1: 坚决选择路线 B，中止路线 A (Pivot to Agentic Research Flywheel)
* **Decision**: 停止去跑 54 个 P2 扫描批次，将全部工程精力聚焦于“让模型的反思建议真正支配沙箱发起下一轮物理发包，并生成 PoC 脚本”。
* **Why**: 对齐 `真正想做的是.md` 终极蓝图。自动化发单包是传统扫描器（Nessus/Nuclei），能够根据上一步反馈自主调整策略并发起后续攻击的才是安全智能体。
* **Do not revert unless**: 出现必须满足特定大规模基准测试性能指标的外部审计要求。

### Decision 2: 绝不为了数字好看进行任何特调 (Anti-Hacking & Anti-Patching)
* **Decision**: 彻底拔除 `"?${"` 字符串切割与 `"NoSuchKey"` 云厂商专属硬编码。
* **Why**: 违反宪法“抽象 > 特判，根因 > 补丁”。404 端点资源不存在法定就是前置条件未决，必须诚实记录在 `BLOCKED` 中。标准 URI 解构必须依赖官方 RFC 3986 `urlsplit`。
* **Do not revert unless**: 国际 RFC 规范发生重构。

### Decision 3: 认知推理模型必须配置满血生成预算 (8192 Token Budget)
* **Decision**: `generate_structured_json` 默认预算设为 4096，并通过 `INVAR_LLM_MAX_TOKENS=8192` 完全对齐 Pi 生产环境。
* **Why**: 现代 35B+ MoE 推理模型（如 Ornith/R1/Qwen-Thinking）的思维链本身需要占用 1000~2000 个 Token，256 Token 会在思考阶段将模型直接腰斩导致崩溃。
* **Do not revert unless**: 使用无任何思维链的极小型轻量分类模型。

### Decision 4: 三界律契约绝对隔离 (Type Isolation Invariant)
* **Decision**: `EndpointIR` 纯粹表示静态端点事实，任务意图与假说由 `ResearchTaskContext` 独立承载。
* **Why**: 保持面向对象与领域边界的高内聚、低耦合，杜绝业务假说污染基础 AST 端点定义。

---

## 12. Data / API / Type Contracts

### `ResearchTaskContext` (领域意图契约)
```python
@dataclass(frozen=True)
class ResearchTaskContext:
    task_id: str
    hypothesis_id: Optional[str] = None
    attack_class: Optional[str] = None
    profile: Optional[str] = None
    coverage_id: Optional[str] = None
    priority: Optional[str] = None

    @classmethod
    def from_task_dict(cls, task: Dict[str, Any]) -> "ResearchTaskContext":
        return cls(...)
```

### `TriageDispatcher._is_valid_api_path` (词法门禁契约)
* **输入**: `path: str`
* **规则**:
  1. `len(path) >= 2` 且不为空；
  2. 不含 `\n`, `\r`, `\t`；
  3. `path.encode("ascii")` 纯 ASCII（拦截任何大段中文免责条款）；
  4. 不含前端类调用签名（`this.`, `window.`, `endpointfor(`, `requestrouter`）。
* **输出**: `bool` (合法 API 返回 True，脏样本返回 False)。

### `InvariantEvaluator.evaluate` (不变量求值契约)
* **401, 403, 405 或 soft_denial / html_fallback**: 确权为 `confirmed`（策略防御拦截，安全底线坚固）；
* **200~299 真实放行**: 若无鉴权凭据，确权为 `vulnerable`（底线击穿，产生漏洞确权）；
* **404 / 500 等异常**: 判定为 `inconclusive`，收敛入 `CoverageLedger` 的未决阻塞事实 (`UnresolvedFact`)。

---

## 13. Algorithms / Workflow (路线 B 多轮追击状态机蓝图)

路线 B 即将建立的智能体核心闭环算法：

```text
Turn 1: Baseline Request (POST /users/${H}/reset-password)
  ↓
Observation: HTTP 405 MethodNotAllowed
  ↓
Control Plane Invocation: llama-server (Ornith 35B CoT)
  ↓
Decision Generation:
  • action: RUN_EXPERIMENT
  • target_strategy: METHOD_SUBSTITUTION (switch to GET)
  • rationale: "Bucket level object rejects POST, test safe idempotent read"
  ↓
Turn 2: Follow-Up Action Dispatch (GET /users/.../reset-password)
  ↓
Observation 2: Evaluate Response (200 Data Leak vs 403 Access Denied)
  ↓
Branch A (Breakthrough):
  ➔ Security Invariant Violated
  ➔ Generate Reproducible PoC (poc.py / curl command)
  ➔ Independent Verification ➔ Confirmed Finding ➔ OpenVEX Affected
  ↓
Branch B (Terminal Denial):
  ➔ Security Invariant Holds
  ➔ Record Multi-turn Evidence Chain ➔ OpenVEX Not-Affected
```

---

## 14. Verified Tests (252 项全绿行为契约)

执行指令：
```bash
PYTHONPATH="python/packages/core/src" uv run --project python python -m pytest -q
# 输出: 252 passed in 0.59s
```

* **核心防护测试集**：
  * `test_research_task_context_contract.py`：端点事实与意图解耦、假说驱动不变量挂载；
  * `test_triage_sanitization_contract.py`：中文法律声明与前端 SDK 表达式过滤；
  * `test_invariant_evaluator_contract.py`：RFC 9110 405 动词策略确权、去除 admin 特判；
  * `test_model_provider.py`：思维链剥离、4096/8192 预算对齐、环境变量隔离；
  * `test_sandbox_operators_all.py`：IDOR 双主体差分、动词隧道篡改、破坏性动作二次确认；
  * `test_adaptive_sandbox_all.py`：自适应变异循环、传输层格式契约；
  * `test_audit_checkpoint.py`：断点原子落盘与崩溃自愈恢复。

---

## 15. Failure / Pitfall Registry (血泪经验底账)

### Problem 1 — 客户端 `max_tokens: 256` 导致推理模型腰斩
* **Symptom**: `LLM length truncation recovery failed: first finish_reason=length`
* **Root Cause**: Ornith 35B 等强推理模型内置思维链，`<think>` 阶段即消耗 1000+ Token，256 硬编码导致生成在思考途中被掐断。
* **Correct Fix**: 提升默认至 4096，并通过 `INVAR_LLM_MAX_TOKENS=8192` 环境变量与 Pi 生产环境对齐。
* **Prevention**: 针对推理模型，严禁设置低于 4096 的 token 预算。

### Problem 2 — 字符串截断与云厂商错误码特调
* **Symptom**: 试图通过 `if "?${" in p` 和 `if "NoSuchKey" in response` 强行将 404 刷成 `confirmed`。
* **Root Cause**: 违反宪法“抽象 > 特判”，为了局部通过率掩盖真实网络事实。
* **Correct Fix**: 采用标准 RFC 3986 `urlsplit(p).path` 正交分离路径与参数；404 诚实收敛为未决 `inconclusive` 并记入账本。
* **Prevention**: 严禁在领域核心层编写任何针对特定厂商报错文本的 `if` 特判。

### Problem 3 — 单元测试未隔离外部环境变量
* **Symptom**: 终端执行了 `export INVAR_LLM_MAX_TOKENS=8192` 导致单测断言 `4096 != 8192` 失败。
* **Root Cause**: 单元测试直接读取系统环境变量，缺乏上下文隔离。
* **Correct Fix**: 在单测内部使用 `patch.dict(os.environ)` 显式弹出外部变量。
* **Prevention**: 任何测试默认环境变量行为的用例必须实施 `patch.dict` 隔离。

### Problem 4 — 前端 AST 提炼混入非 API 脏数据
* **Symptom**: 中文用户协议与 `this._instance...` 变成 API 路径，导致覆盖账本崩塌。
* **Root Cause**: 提炼器缺乏合法性校验，仅凭包含 `/` 即放行。
* **Correct Fix**: 在 `TriageDispatcher` 建立词法合法性门禁 (`_is_valid_api_path`)，严格要求纯 ASCII 且拦截 JS 调用签名。
* **Prevention**: 进入任务库的一切端点必须通过词法门禁审查。

---

## 16. Do Not Repeat (终极行为红线)

```text
❌ 严禁去跑 54 个 P2 扫描批次（坚决执行路线 B，不搞假大空刷数据）
❌ 严禁在没有测试前直接改生产代码（坚决执行 TDD: Red -> Green -> Refactor）
❌ 严禁使用 python -c 输出单行脚本（所有诊断进 tmp/ 独立脚本，经由 uv run 执行）
❌ 严禁要求用户手动创建/编辑文件（必须输出完整 Here-Doc 自动化脚本）
❌ 严禁为了凑覆盖率把 404 特调成 confirmed
❌ 严禁在核心评估器里写死任何具体云厂商的错误码 (如 NoSuchKey)
❌ 严禁把任务意图塞回 EndpointIR（必须维护 ResearchTaskContext 独立契约）
❌ 严禁破坏已全绿的 252 项行为测试
❌ 严禁在输出给用户的命令中遗漏 2>&1 | tee /dev/tty | xclip -sel clip 三通剪贴板管道
```

---

## 17. Engineering Invariants (不可破坏约束)

1. **三界律**: 目录是职责边界，类型是数据边界，接口是模块边界；
2. **纯粹 POSIX 路径**: 强制全量 POSIX 标准路径（`/home/zhz/...`），严禁 Windows 反斜杠；
3. **Python uv 独占统治**: 绝对只读系统 Python，所有运行、测试、脚本必须经由 `uv run --project python` 调度；
4. **有限动作空间**: 大模型永远只能在确定性生成的候选算子集 (`CandidateAction`) 中做选择，严禁允许模型自行拼接任意不可控的原始网络发包；
5. **证据三权分立**: 执行发包者 (`executor`)、不变量评估者 (`evaluator`) 与证据终审者 (`verifier`) 必须彼此独立。

---

## 18. Open Issues (路线 B 核心攻坚点)

### OI-01: 大模型战略反思支配下一步物理追击发包 (Actionable Steer Wiring)
* **现状**: 本地 35B 模型在 Task 4 中已准确给出“改换 GET 动词探测”的建议，但该建议当前仅作为日志文本留存，沙箱未发起 Turn 2 追击。
* **目标**: 打通 `ResearchController` ➔ `AdaptiveExperimentSelector` ➔ `AdaptiveSandboxExecutor`，使模型生成的策略建议能够即时派生出新的 `TransformationVariant` 并由沙箱真实发出后续 HTTP 请求。
* **验证**: 以 `POST /users/${H}/reset-password` 为切入点，验证系统自适应发起第 2 次 GET 探测并记录完整因果序列。

### OI-02: 自动化可复现 PoC 生成器 (PoC Package Composer)
* **现状**: 系统已能生成 OpenVEX 和 SARIF，但缺少面向人类渗透者的最终交付物——可一键执行的 `poc.py` 或 `curl` 复现脚本。
* **目标**: 当证据链确权为 `vulnerable` 时，由 `ReportProjector` 自动组装出包含 HTTP 原始报文、前置凭据说明与回显验证逻辑的独立 PoC 脚本。

---

## 19. Environment / Toolchain

```text
OS: Linux Mint 22.3 Cinnamon (x86_64)
Kernel: 6.8.0-xx-generic
CPU: Intel Core i5-13600KF
RAM: 32 GB
GPU: NVIDIA GeForce RTX 3060 12GB GDDR6 (Driver 595.91.07, CUDA 12/13)
Python: 3.12.3 (uv managed, pyproject.toml root at python/)
Rust: 1.99.0 (Cargo workspace at crates/core/)
Node: v24.21.0 / pnpm 12.8.1

Local LLM Server:
    Runtime: /opt/llama.cpp/llama-server
    Endpoint: http://127.0.0.1:8080/v1
    Launch Script: ~/llama_38B.sh
    Model Path: /home/zhz/models/Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf
    Config: -ngl 99 --n-cpu-moe 28 -c 160000 --reasoning on -fa on --spec-type draft-mtp

Environment Variables:
    export INVAR_LLM_BASE_URL="http://127.0.0.1:8080/v1"
    export INVAR_LLM_MODEL="/home/zhz/models/Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf"
    export INVAR_LLM_TIMEOUT="120"
    export INVAR_LLM_MAX_TOKENS="8192"
    export PYTHONPATH="python/packages/core/src"
```

---

## 20. Roadmap (路线 B 专属智能体演进路线)

```text
Phase 8.1~8.4 [已完成]
    单发实证引擎物理闭环、假说驱动不变量、URI 词法门禁、8192 Token 满血打通
    ✅ COMPLETE (252 passed)

Phase 9.0 (路线 B 核心突破) [CURRENT]
    让大模型反思真正支配下一步发包：连接 ResearchController 与 SandBox，
    在遭遇 405/403 阻断后，将模型建议转化为实际 Turn 2 追击请求
    ⏳ NEXT SINGLE ACTION

Phase 9.1 (单点深度攻坚与 PoC 闭环)
    在密码重置 / IDOR 场景下，跑通完整多轮自适应实证，并自动导出独立可复现的 PoC 脚本 (poc.py)
    ⏳ FUTURE

Phase 9.2 (人类确认与交互工作流)
    挂载终端交互界面或 Tauri 应用壳，将高质量战报与 PoC 呈现在渗透入门者面前，确认后一键提交
    ⏳ FUTURE
```

---

## 21. Recovery Protocol (新 AI 接管零猜忌标准协议)

新 AI 接收到本交接档案后，必须严格按照以下顺序执行恢复，严禁跳步与自由发挥：

```text
1. 确认身份与环境:
   检查本 HANDOFF.md，确认为 Linux Mint 22.3 环境，Python 必须由 uv 调度。

2. 验证 Last Known Good State:
   运行: PYTHONPATH="python/packages/core/src" uv run --project python python -m pytest -q
   预期必须为: 252 passed in ~0.6s。若有任何报错，必须就地解决，严禁带病推进。

3. 验证本地 LLM 存活:
   运行: curl -s http://127.0.0.1:8080/health
   预期必须为: {"status":"ok"}。

4. 锁定当前唯一目标:
   读取 Section 3 (CURRENT OBJECTIVE) 与 Section 4 (NEXT SINGLE ACTION)。
   牢记战略决断：坚决不跑 P2 批量扫描，全力推进路线 B（多轮追击发包与 PoC 生成）。

5. 实施单步工程动作:
   严格按照 TDD 流程编写失败契约测试 (RED)，以挂载剪贴板三通管道的非交互式 Bash 脚本交付给用户。
```

---

## 22. AI Collaboration Protocol (极客协作与交付纪律)

1. **中文优先，术语双语**：沟通默认中文；核心技术术语首次出现时必须标注“中文 (English)”，后续纯中文；
2. **消灭手工操作**：严禁要求用户手动创建、复制、编辑文件，交付必须是自解释的 `cat << 'EOF' > ...` 脚本；
3. **剪贴板零摩擦交付律 (xclip 统治法则)**：所有需要用户执行并回传日志的命令，末尾**强制挂载**：
   ```bash
   2>&1 | tee /dev/tty | xclip -sel clip
   ```
4. **单步闭环**：一次交互只推进一个原子动作，绝不一次性输出跨越多阶段的代码清单；
5. **绝对禁止伪代码与缩写**：交付代码严禁出现 `// ... 省略其余代码`、`/* TODO */`，必须全量、自洽、开箱即用。

---

## 23. Security & Sensitive Data Boundary

* 本项目严格运行在合规授权范围 (`ikuai8.com`) 内；
* 本文档及 Git 历史中严禁记录真实 Cookie、私钥、内部生产 Token；
* 本地大模型推理完全运行在 `127.0.0.1:8080` 回环网络，不向任何第三方公有云泄露目标资产报文与切片。

---

## 24. Reproducibility Status

### **FULLY REPRODUCIBLE (完全可复现)**

* **依据**：
  * 全量 252 项单元与契约测试在本地可在 0.6 秒内确定性回归通过；
  * 本地推理后端、显存卸载参数与模型版本完全固化且探针验证通过；
  * Phase 8.4 真实网络实证物理战报在 `artifacts/reports/phase8_p1_canonical/` 完整留存可溯源；
  * 工作区状态由 Git Commit 锚定，零临时环境悬挂。

---

## 25. Handoff Self-Check (交接自检清单)

- [x] 新 AI 知道当前项目是什么？（Invar 是安全实证机架，不是玩具扫描器）
- [x] 新 AI 知道战略已全面转向路线 B？（放弃 P2 跑批，攻坚自主多轮追击与 PoC 飞轮）
- [x] 新 AI 知道最后一次已知完好状态？（252 passed, LKG Commit `7ca0007`, phase8_p1_canonical 战报）
- [x] 新 AI 知道为什么 Task 4 能够反思成功？（8192 Token 满血预算解除了思考截断）
- [x] 新 AI 知道为什么 Task 5 会返回 404？（S3 存储桶无此 Key，系统依法诚实判定为未决，拒绝 NoSuchKey 特调）
- [x] 新 AI 知道当前唯一下一动作？（编写支持多轮物理追击发包的 TDD RED 测试）
- [x] 新 AI 知道当前阶段禁止做什么？（禁止跑 P2 批次，禁止改 Rust，禁止写 UI，禁止打特调补丁）
- [x] 新 AI 知道如何运行测试与环境隔离？（`PYTHONPATH="python/packages/core/src" uv run pytest`）
- [x] 新 AI 知道交付命令必须挂载 xclip 剪贴板管道？（`2>&1 | tee /dev/tty | xclip -sel clip`）
- [x] 新 AI 能够零猜忌从正确位置接管？（协议、数据流、测试边界完全对齐）

---

# State Recovery Summary (致新会话 AI)

```text
PROJECT: Invar
STATUS: Phase 8.4 Canonical Complete (Fully Tested Baseline: 252 passed)
STRATEGY: ROUTE B (Autonomous Multi-Turn Security Agent & PoC Flywheel)
CANONICAL TARGET: ikuai8.com
LOCAL LLM: 127.0.0.1:8080/v1 (Ornith 35B GGUF, 8192 Max Tokens Ready)

CURRENT OBJECTIVE:
    Wire LLM actionable recommendations to trigger Turn-2 physical probes & PoC generation.

NEXT SINGLE ACTION:
    Write a TDD RED contract test in test_research_loop_contract.py asserting multi-turn
    probe dispatch upon receiving actionable verb-substitution guidance.

REDLINES:
    NO P2 Batch Scanning! NO Hardcoded Vendor Hacks! POSIX & uv Only!
    Append standard pipe: 2>&1 | tee /dev/tty | xclip -sel clip
```

