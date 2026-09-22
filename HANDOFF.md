# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot & State-Machine Recovery Contract  
> **Project Identity:** Invar (System-2 Targeted Verification & Research Engine)  
> **Triad Architecture Context:**  
>   - Model Factory: `C:\dev\Base-Jev` (System-1 SFT Foundry & ONNX Compiler)  
>   - Distillation Workshop: `C:\dev\distiller` (Dual-Teacher Distillation & Gold Firewall)  
>   - Verification Engine: `C:\dev\Invar` (System-2 Targeted Execution & Deep Verification)  
> **Canonical Root:** `C:\dev\Invar`  
> **Canonical Handoff Path:** `C:\dev\Invar\HANDOFF.md`  
> **Snapshot Date:** 2026-09-22  
> **Document Version:** 9.0.0 (403 Refusal Research Engine & pi-agent-core Headless Convergence Edition)  
> **Primary Purpose:** 当当前 AI 会话关闭、上下文丢失、开发人员忘记历史时，一个完全没有历史记忆的新 AI，仅凭本文件与当前项目源码、测试和配置，即可 100% 精确恢复当前工程状态，并从正确位置继续推进，禁止重新猜测、重新设计或重复既有成果。

---

## 0. Handoff Metadata

| Item | Value | Evidence Level | Notes |
|---|---|---|---|
| Project Name | Invar | [FACT] | System-2 深度动态执行、差分对账与安全不变量实证主引擎 |
| Repository Root | `C:\dev\Invar` | [FACT] | 标准 AI Engineering Monorepo 体系 |
| Workspace State | Clean & Upgraded (Phase A-D + pi-agent-core Core Complete) | [FACT] | 403 拒绝响应架构与 Agent 事件循环内核全面闭环 |
| Active Target | `ikuai8.com` | [FACT] | 授权测试根域，法定边界记录于 `data/targets/ikuai8.com/scope.txt` |
| Passive Recon Surface | 68 Active Subdomains | [FACT] | `crt.sh` (42) + `subfinder` (67) 多源合流去重入库 |
| Web Alive Surface | 31 Live Web Hosts | [FACT] | HTTPX 存活探测过滤，剔除 37 个僵尸/离线域名 |
| Spidered Static Code | 206 Physical JS Files | [FACT] | Katana (48,779 原始线索) $\to$ 783 URLs $\to$ 206 JS 落盘于 `tmp/raw_js/` |
| AST Endpoint IR | 1,216 API Endpoints | [FACT] | Tree-sitter 提取，剥离 298 个具参接口，存入 `tmp/ikuai8_endpoints_report.json` |
| Neural 0.6B Triage | 1,216/1,216 1:1 Aligned | [FACT] | 由 `Base-Jev` GPU 驱动物理双头完成，落盘 `tmp/base_jev_predictions_1216.jsonl` |
| Dual-Track Pools | Pool A: 48, Pool B: 30, Pool C: 30 | [FACT] | 双轨比对器规则与神经并集融合，落盘 `artifacts/reports/triage_pools_v2.json` |
| Targeted Tasks | 78 Tasks (156.07 KB) | [FACT] | P0=12, P1=41, P2=23, P3=2，固化于 `artifacts/reports/targeted_research_tasks_78.json` |
| Desktop UI State | **OUT OF SCOPE** | [DECISION] | 用户明确裁决不需要桌面端，彻底保持 Headless 纯无头高性能架构 |
| Rust Core Test Status | **15 passed; 0 failed** | [FACT] | `cargo test --workspace` (涵盖 IPC 跨进程管道实测) |
| Python Core Test Status | **181 passed in ~0.50s; 0 failed** | [FACT] | `uv run --project python pytest` (涵盖 26+ 个新增 403 与 Agent 契约测试) |

---

## 1. Project Identity

[DECISION]
本系统属于工业级三位一体架构（Triad Architecture）中的第三环：
1. **distiller** (`C:\dev\distiller`): 专家知识编译车间，负责双师蒸馏与物理防火墙隔离（`Train ∩ Gold = ∅`）。
2. **base-jev** (`C:\dev\Base-Jev`): System-1 认知反射前哨，0.6B 判别式微调工厂（DirectML FP16，~23ms），输出后验分布与风险分数。
3. **Invar** (`C:\dev\Invar`): **System-2 深度科研与动态执行验证引擎（当前工程主战场）**。
   - 彻底摆脱“单次问答找漏洞”与“200 OK 误报”的粗暴模式；
   - 贯彻彭之娘博士《A Year of Hacking with LLMs》**“The Harness is the Hack”** 哲学与 RFC 规范；
   - 吸纳开源项目 `bypass-403` 的 27 项攻防 Trick 并升华为 F1~F9 泛化变换族；
   - 吸纳 `earendil-works/pi`（`pi-agent-core`）事件流、消息双轨制、无状态纯函数算法与 Steering 双队列架构；
   - 由确定性语义等价核验（Semantic Equivalence）与证据门禁（EvidenceGate）垄断裁决权，实施真实的闭环漏洞确权。

---

## 2. Current Mission

[DECISION]
完成 403 拒绝响应研究架构与 `pi-agent-core` 纯无头事件流内核升级后，**正式进入 78 个真实靶心任务的批量实证实战与战报投影消费阶段**。利用已装备高胜率自适应剪枝与重放验真能力的 `ResearchAgent` 与 `AdaptiveSandboxExecutor`，对 `artifacts/reports/targeted_research_tasks_78.json` 中的端点（特别是 12 个 P0 级双高核心靶点）执行端到端闭环实证，并原子化投影生成五大权威交付物。

---

## 3. Current Objective

[FACT]
编写并执行靶向实证批量审计运行脚本（如 `python/scripts/run_targeted_audit.py`），驱动升级后的 `AdaptiveSandboxExecutor`（内置 `ResearchAgent`、`AdaptiveExperimentSelector`、`SemanticEquivalenceEvaluator` 与 `EvidenceGate`），对已装配好的 78 个靶向任务实施批量实证探测，生成标准 `findings.json` 与 `REPORT.md`。

---

## 4. Next Single Action

**CURRENT OBJECTIVE → NEXT SINGLE ACTION**

[FACT]
**当前唯一下一步动作**：
编写单任务与批量靶向实证运行脚本 `python/scripts/run_targeted_audit.py`，读取 `artifacts/reports/targeted_research_tasks_78.json`，驱动沙箱执行器与 `ResearchAgent` 启动自适应实证闭环，并通过离线/可控沙箱完成前 3 个 P0 靶点的端到端实证检验。

---

## 5. Current Scope

**当前正在修改/研究的代码与资产**：
* `python/scripts/run_targeted_audit.py`（待编写的靶向任务批量调度脚本）
* `python/packages/core/src/harness/sandbox_executor.py`（已接入 `ResearchAgent` 的执行中枢）
* `python/packages/core/src/agent/research_agent.py` 与 `research_loop.py`（Agent 循环内核）
* `artifacts/reports/targeted_research_tasks_78.json`（78 个核心靶标输入）

---

## 6. Out of Scope

**当前阶段明确禁止触碰的红线**：
* ❌ **严禁开发桌面端 / Tauri / React UI 表现层**（用户明确裁决不需要桌面端，Invar 保持 100% 纯无头 Headless 架构）。
* ❌ 严禁再次重跑 Phase 1~4 的全网资产收集流水线（Genesis Run 资产已固化）。
* ❌ 严禁在测试或生产中强行依赖本地运行的 `llama-server.exe`（单测必须保持 100% 离线确定性，模型层只作为可选插拔的外部顾问）。
* ❌ 严禁无授权针对非受控外部目标实施无边界破坏性发包（所有动态测试必须受 `scope.txt` 约束）。
* ❌ 严禁在 `Invar` 内引入重型 PyTorch 训练依赖（保持纯净轻量运行时边界）。

---

## 7. Last Known Good State

[FACT — Snapshot at 2026-09-22 19:30]
* **Python Core 全量回归测试**：`uv run --project python pytest` $\to$ **181 passed in ~0.50s; 0 failed**。
* **Rust Core 工作区测试**：`cargo test --workspace` $\to$ **15 passed; 0 failed**（包含 IPC 管道全链路实测）。
* **全局测试总数**：**196 passed; 0 failed**，全工作区测试零警告、零失败。
* **Rootdir / Pythonpath 配置持久化**：根目录下已固化 `pytest.ini`，彻底根治跨目录执行 pytest 导致的 `ModuleNotFoundError`。
* **403 拒绝响应与 Agent 内核**：`denial_models.py`、`transformation_models.py`、`semantic_models.py`、`evidence_models.py`、`adaptive_selector.py`、`model_provider.py`、`loop_types.py`、`research_loop.py`、`research_agent.py` 100% 绿色交付。

---

## 8. Completed Work

| Module | Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|---|
| Module 1 | CT 证书日志挖掘器 | DONE | 42 独立子域，3项测试全绿 | `scripts/data/asset/ingest_crtsh.py` | 对齐 RFC 6962，处理 Multi-SAN 与通配符。 |
| Module 1 | 多源被动资产合流 | DONE | 68 独立 active 子域名 | `scripts/data/asset/ingest_subdomains.py` | 快照对账机制，防资产下线误判。 |
| Module 2 | HTTPX 同名冲突探路器 | DONE | 存活 31 个 Web 主机 | `scripts/data/asset/ingest_httpx.py` | 排除 Python `encode/httpx` 命令行劫持。 |
| Module 3 | Katana 爬取与代码物化 | DONE | 206 个物理 JS 100% 落盘于 `tmp/raw_js/` | `download_javascript.py` | 本地物理代码库安全就绪。 |
| Module 4 | Tree-sitter AST 提取 | DONE | 1,216 API 节点，298 个具参接口 | `scan_pipeline.py`, `tmp/ikuai8_endpoints_report.json` | 离线强类型契约抽取。 |
| Module 4 | 0.6B GPU 全量推演 | DONE | 1,216/1,216 1:1 对齐 | `generate_triage_predictions.py` | 双正交打分（Impact + Sensitivity）。 |
| Module 4.3| 双轨比对器融合初筛 | DONE | Pool A (48) + Pool B (30) 锁定 78 靶心 | `triage_dual_track_comparator.py` | 规则 ∪ 神经并集，消除 93.6% 无效发包。 |
| Module 5.1| 任务分流器轻量化升级 | DONE | 78 个任务体积骤降 99.3% 至 156 KB | `triage_dispatcher.py` | 截断 800 字符，单字母动词纠偏。 |
| 403 架构 | 拒绝响应分类模型 | DONE | 6 项测试全绿 | `harness/denial_models.py` | 解耦 WAF 拓扑与拒绝原因类别，支持 RFC 9110。 |
| 403 架构 | 9大核心变换族算子库 | DONE | 5 项测试全绿 | `harness/transformation_models.py` | 收敛 `bypass-403.sh` 27 项技巧，去重生成 46 变体。 |
| 403 架构 | 语义等价与防误报门禁 | DONE | 6 项测试全绿 | `harness/semantic_models.py` | 三值逻辑，剔除首页回退与登录重定向假 200。 |
| 403 架构 | 六层证据链与重放门禁 | DONE | 6 项测试全绿 | `harness/evidence_models.py` | 8 大前置谓词校验，连续同态发包稳定性断言。 |
| 403 架构 | 变异自适应优先级剪枝 | DONE | 4 项测试全绿 | `harness/adaptive_selector.py` | 依据分类加权，多样性采样截断至 Top-12 预算。 |
| 模型抽象 | OpenAI 兼容提供者 | DONE | 4 项测试全绿 | `agent/model_provider.py` | 支持 `<thought>` 剥离与自愈解析，容错降级。 |
| pi 原语 | 消息双轨制与强类型事件 | DONE | 5 项测试全绿 | `agent/loop_types.py` | 内轨 `ResearchMessage`，外轨 `convert_to_llm`，15 类事件。 |
| pi 原语 | 纯函数科研算法循环 | DONE | 4 项测试全绿 | `agent/research_loop.py` | `run_research_loop` 纯函数，支持 `steering`/`followUp` 队列。 |
| pi 原语 | 有状态 ResearchAgent | DONE | 3 项测试全绿 | `agent/research_agent.py`, `sandbox_executor.py` | 状态机控制器，`subscribe()` 订阅总线，沙箱委托集成。 |

---

## 9. Changed Files

### Added
* `docs/architecture/Invar-403拒绝响应研究架构升级-AI可复现工程规格书-v1.0.0.md` (403 拒绝响应重构法定工程规格书)
* `pytest.ini` (项目根目录 Pytest 导航守护配置，声明 `pythonpath`)
* `python/packages/core/src/harness/denial_models.py` (拒绝分类契约模型)
* `python/packages/core/src/harness/transformation_models.py` (9 大变换族算子库)
* `python/packages/core/src/harness/semantic_models.py` (语义等价与防误报判定器)
* `python/packages/core/src/harness/evidence_models.py` (六层证据链与终审门禁)
* `python/packages/core/src/harness/adaptive_selector.py` (自适应变异优先级剪枝器)
* `python/packages/core/src/agent/model_provider.py` (OpenAI 兼容模型提供者)
* `python/packages/core/src/agent/loop_types.py` (消息双轨制与事件流契约)
* `python/packages/core/src/agent/research_loop.py` (纯函数科研循环算法内核)
* `python/packages/core/src/agent/research_agent.py` (有状态科研智能体调度器)
* `python/tests/test_denial_classification_contract.py`
* `python/tests/test_transformation_family_contract.py`
* `python/tests/test_semantic_equivalence_contract.py`
* `python/tests/test_evidence_contract.py`
* `python/tests/test_adaptive_selector_contract.py`
* `python/tests/test_model_provider.py`
* `python/tests/test_agent_loop_types_contract.py`
* `python/tests/test_research_loop_contract.py`
* `python/tests/test_research_agent_contract.py`
* `python/tests/test_sandbox_403_research_loop.py`

### Modified
* `python/packages/core/src/harness/sandbox_executor.py` (接入 `ResearchAgent` 委托与动态传输层同步)
* `python/packages/core/src/agent/__init__.py` (导出新 Agent 原语与控制器)
* `HANDOFF.md` (升级至 v9.0.0 全局交接档案)

---

## 10. Current Architecture

[DECISION]
**全景无头科研作战架构（五层全景漏斗图）**：
```text
[互联网全网数据源]
       │
       ▼ 【第 1 步: 多源被动资产侦察 (OSINT & CT Logs)】
    Subfinder (67) + crt.sh (42) ──► ingest_subdomains.py ──► subdomains.jsonl (68 个 active 子域)
       │
       ▼ 【第 2 步: Web 存活验证与边缘画像 (Live Verification)】
    ingest_httpx.py (自适应探路器驱动 HTTPX) ──► live_hosts.jsonl (31 个存活主机)
       │
       ▼ 【第 3 步: 前端代码深度爬取与物理物化 (Spidering & Materialization)】
    Katana (48,779 原始线索) ──► normalize_katana.py ──► download_javascript.py ──► tmp/raw_js/ (206 个物理 JS)
       │
       ▼ 【第 4 步: 语法解构与双轨初筛 (AST & Dual-Track Triage)】
    scan_pipeline.py (Tree-sitter) ──► 1,216 个 API 端点 (298 个具参) 
         │
         ▼ 0.6B ONNX 神经推演 (Base-Jev GPU 车间 1216 逐行对齐)
    triage_dual_track_comparator.py (双轨比对器) ──► triage_pools_v2.json (Pool A 48 + Pool B 30)
         │
         ▼ triage_dispatcher.py (切片截断 800 字符 + 动词清洗)
    artifacts/reports/targeted_research_tasks_78.json (78 个靶标，156 KB，P0=12)
       │
       ▼ 【第 5 步: Invar System-2 拒绝响应与科研智能体闭环 (Verification Engine)】★ CURRENT FOCUS
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │  ResearchAgent (有状态调度器) ──► subscribe() 事件流广播                      │
    │         │                                                                   │
    │         ▼ run_research_loop (纯函数算法内核)                                 │
    │    ┌──────────────────────────────────────────────────────────────────┐     │
    │    │ 1. DenialClassifier: 客观归因 (区分 WAF 拓扑与策略/方法拒绝)       │     │
    │    │ 2. AdaptiveSelector: 优先级与多样性剪枝 (收敛至 Top-12 变异体)     │     │
    │    │ 3. TransformationRegistry: 派发 F1/F2/F3 物理变异体 (含重写/隧道) │     │
    │    │ 4. Probe Dispatch: 网络发包与微观差分计算                         │     │
    │    │ 5. SemanticEquivalenceEvaluator: 三值逻辑 (排除首页回退/登录跳转)  │     │
    │    │ 6. Replay Verification: 连续同态发包稳定性核验                     │     │
    │    │ 7. EvidenceGate: 8 大前置谓词终审确权 ──► 装配 EvidenceChain      │     │
    │    └──────────────────────────────────────────────────────────────────┘     │
    └─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
    【交付物】：5 大权威战报 (REPORT.md / findings.json / FINDINGS-DETAIL.md 等)
```

---

## 11. Architecture Decisions

### AD-01 — Three-Tier Hierarchical LLM Allocation for System-2
* **Decision**: System-2 不把所有任务压给单一模型，内环变异载荷生成由本地 `Ornith-9B` 负责，复杂破局由本地 `Qwen-27B` 负责，低频终审由云端 Gemini 负责。

### AD-02 — Asset-Centric vs Tool-Centric Storage Boundary
* **Decision**: 废除按工具名称建立子目录（如 `subfinder/`、`httpx/`）的设想，保持 `data/targets/<target>/` 扁平单表设计（`subdomains.jsonl`、`live_hosts.jsonl` 等视为不可变数据库单表）。

### AD-03 — Compact Slice Guardrail (800 Chars Max)
* **Decision**: 任务装配与消息转译至大模型外轨边界时，必须对 `code_slice` 实施 800 字符强行截断。防止前端混淆单行引起上下文爆炸。

### AD-04 — Fail-Closed Method Sanitization
* **Decision**: 严格推行标准 HTTP 动词白名单 `{"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}`，纠偏 AST 单字母残片。

### AD-05 — Model Factory vs Combat Runtime Decoupling
* **Decision**: 保持 `Base-Jev` 为离线模型炼制工厂，保持 `Invar` 为轻量级独立战斗平台，不污染大型 PyTorch/CUDA 训练依赖。

### AD-06 — Decoupling Denial Reason from Frontend Component
* **Decision**: 拒绝原因分类严格解耦：`FrontendComponent`（WAF/CDN/代理）与 `DenialCategory`（方法不支持/访问控制/频控）作为正交维度，坚决废除“403 自动等于 WAF”的伪假设。

### AD-07 — Three-Valued Logic for Semantic Equivalence
* **Decision**: 语义等价判决严禁二元 `True/False`，采用 `SAME_RESOURCE`、`DIFFERENT_RESOURCE`、`UNKNOWN`。自动识别公共首页回退（相似度 $\ge 0.85$）与 302 登录重定向，彻底根治“假 200 误报”。

### AD-08 — 8-Predicate EvidenceGate with Replay Stability Assertion
* **Decision**: 漏洞实锤（`CONFIRMED`）必须同时通过 8 大前置谓词（含连续 2 次同态发包稳定性核验）。偶发抖动一律降级为 `INCONCLUSIVE`。

### AD-09 — Heuristic & Diversity Sampling Selector
* **Decision**: 单端点实验预算收敛至 Top-12。针对 `DELETE`/`PUT` 赋予动词隧道高优先级，同时对同质内网 IP 伪造变体限制最多保留 3 个（`max_ip_spoofs = 3`），确保 F1/F2/F3 多样性。

### AD-10 — Adoption of `pi-agent-core` Primitives & Headless Enforcement
* **Decision**: 吸收 `pi-agent-core` 的无状态纯函数算法（`run_research_loop`）、推模式强类型事件流（`ResearchEventSink`）、两级队列（`steering`/`followUp`）与有状态包装器（`ResearchAgent`）。同时**坚决废除桌面端（Tauri/React）开发规划，全系统保持 100% 纯无头（Headless）高性能架构**。

---

## 12. Data / API / Type Contracts

### 1. 强类型事件与双轨消息契约 (`agent/loop_types.py`)
```python
class ResearchEventType(str, Enum):
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    DENIAL_CLASSIFIED = "denial_classified"
    VARIANT_SELECTED = "variant_selected"
    PROBE_DISPATCHED = "probe_dispatched"
    PROBE_RESPONDED = "probe_responded"
    DIFFERENTIAL_COMPUTED = "differential_computed"
    SEMANTIC_EVALUATED = "semantic_evaluated"
    REPLAY_STARTED = "replay_started"
    REPLAY_COMPLETED = "replay_completed"
    STEERING_INJECTED = "steering_injected"
    ABORTED = "aborted"

@dataclass(frozen=True)
class ResearchEvent:
    event_type: ResearchEventType
    payload: Dict[str, Any]
    timestamp: str

def convert_to_llm(messages: List[ResearchMessage], max_slice_chars: int = 800) -> List[Dict[str, str]]: ...
```

### 2. 变换变体契约 (`harness/transformation_models.py`)
```python
@dataclass(frozen=True)
class TransformationVariant:
    variant_id: str
    family: TransformationFamily
    method: str
    url: str
    headers: Dict[str, str]
    payload: Dict[str, Any]
    rationale: str
    expected_effect: str
```

### 3. 六层全景证据链契约 (`harness/evidence_models.py`)
```python
@dataclass
class EvidenceChain:
    chain_id: str
    target_domain: str
    is_scope_verified: bool
    baseline_observation: DenialObservation
    applied_variant: TransformationVariant
    candidate_observation: DenialObservation
    semantic_result: SemanticEquivalenceResult
    security_invariant_violated: bool
    invariant_rationale: str
    replay_record: Optional[ReplayRecord] = None
    independent_verified: bool = False
    verifier_id: Optional[str] = None
    verdict: EvidenceVerdict
    verdict_rationale: str
```

---

## 13. Algorithms / Workflow

### System-2 拒绝响应自适应科研闭环
```text
输入: Target Endpoint (遭遇 HTTP 403/405 拒绝响应)
  │
  ├─ 1. 构建基线: DenialObservation(status_code=403, body_preview, headers)
  │
  ├─ 2. 确定性分类: DeterministicDenialClassifier.classify()
  │     ├── 拓扑归类: WAF | CDN | ReverseProxy | Unknown
  │     └── 拒绝原因: ACCESS_POLICY_DENIAL | METHOD_POLICY_DENIAL (405+Allow) | RATE_LIMIT (429)
  │
  ├─ 3. 算子衍生与智能剪枝:
  │     TransformationFamilyRegistry.generate_all() (衍生 F1/F2/F3 变异体)
  │     ──► AdaptiveExperimentSelector.select() (多样性剪枝收敛至胜率最高前 12 个实验)
  │
  ├─ 4. 纯函数循环调度 (run_research_loop):
  │     for exp in prioritized_queue:
  │         ├── 轮询 steering_queue 注入干预指令
  │         ├── 发送变异请求 (Probe Dispatch)
  │         ├── 计算物理差分 (Differential Observation)
  │         ├── 语义等价核验 (SemanticEquivalenceEvaluator):
  │         │   ├── 命中 302 登录重定向 ──► DIFFERENT_RESOURCE (丢弃)
  │         │   ├── 命中公开首页回退 (sim >= 0.85) ──► DIFFERENT_RESOURCE (丢弃)
  │         │   └── 命中真实资源特征 ──► SAME_RESOURCE / UNKNOWN (保留)
  │         └── 连续同态重放验真 (Replay Verification 2/2 一致)
  │             └── 稳定性通过 ──► 突破成功！中断循环
  │
  ├─ 5. 终审门禁裁决 (EvidenceGate):
  │     8 大科学前置谓词校验 ──► 产出不可变 EvidenceChain
  │
  ▼
输出: ResearchLoopResult (确权证据链 + Attempt 完整记录)
```

---

## 14. Verified Tests

| Test Suite | File | Passed / Total | Result | Notes |
|---|---|---|---|---|
| 拒绝分类契约测试 | `test_denial_classification_contract.py` | 6 / 6 | **PASSED** | WAF 解耦、RFC 9110 405 分类、429 频控独立 |
| 变换族算子库测试 | `test_transformation_family_contract.py` | 5 / 5 | **PASSED** | F1 路径规范化、F2 动词隧道、F3 重写与 IP 伪装 |
| 语义等价防误报测试 | `test_semantic_equivalence_contract.py` | 6 / 6 | **PASSED** | 首页回退排除、302 登录拦截、三值逻辑 |
| 证据门禁契约测试 | `test_evidence_contract.py` | 6 / 6 | **PASSED** | 8 大前置谓词检验、重放稳定性断言、独立复核 |
| 沙箱 403 闭环集成测试 | `test_sandbox_403_research_loop.py` | 3 / 3 | **PASSED** | 重写穿透突破、首页伪 200 拦截、登录跳转拦截 |
| 自适应选择器测试 | `test_adaptive_selector_contract.py` | 4 / 4 | **PASSED** | 分类优先级加权、高危动词加权、多样性采样 |
| 大模型提供者测试 | `test_model_provider.py` | 4 / 4 | **PASSED** | OpenAI 规范、思维链 `<thought>` 剥离与自愈 |
| Agent 消息与事件契约 | `test_agent_loop_types_contract.py` | 5 / 5 | **PASSED** | 双轨消息转译、800 字符截断、推模式事件流 |
| 纯函数科研循环测试 | `test_research_loop_contract.py` | 4 / 4 | **PASSED** | 纯函数算法闭环、Steering 插队、熔断取消 |
| ResearchAgent 控制器测试 | `test_research_agent_contract.py` | 3 / 3 | **PASSED** | 状态机流转、事件订阅总线、沙箱集成 |
| Python Core 全量回归 | `uv run --project python pytest` | **181 / 181** | **PASSED in 0.50s** | 全工作区零失败 |
| Rust Core 全量回归 | `cargo test --workspace` | **15 / 15** | **PASSED** | IPC 管道与审计战报零失败 |

---

## 15. Failure / Pitfall Registry

### Pitfall 1: Python 虚拟环境与工具路径被劫持
* **Problem**: 运行 `ingest_httpx.py` 误调用了 Python 库命令而非 ProjectDiscovery 安全工具。
* **Root Cause**: `pyproject.toml` 依赖了 `encode/httpx`，在 `.venv/Scripts/` 生成了同名 `httpx.exe`。
* **Correct Fix**: 编写 `_find_projectdiscovery_httpx` 自适应探路器，检查 `-version` 包含 `projectdiscovery`。

### Pitfall 2: 前端代码长行引发任务文件体积爆炸
* **Problem**: 78 个任务落盘文件暴增至 23.7 MB。
* **Root Cause**: Webpack 混淆代码单行长达数十万字符，AST 切片未设边界。
* **Correct Fix**: 引入 `_compact_slice()` 实施 800 字符强行截断，任务集体积骤降至 156 KB。

### Pitfall 3: AST 语法残片导致非标单字母 HTTP 动词
* **Problem**: 出现 `E api/...`、`T api/...` 等非法单字母动词。
* **Root Cause**: 动态调用解构时提取器抓到了局部变量字符残片。
* **Correct Fix**: 引入 `_normalize_method()` 白名单校验与启发式纠偏，以及 `_normalize_path()` 强制前导 `/`。

### Pitfall 4: ONNX 模型导出包装器缺失敏感度头
* **Problem**: `SystemOneOnnxWrapper` 只调用了单打分头 `forward_score`。
* **Correct Fix**: 严格查明源码事实，不盲目写单头 ONNX 推理器，当前推演继续复用已跑出的真实双头 PyTorch 预测。

### Pitfall 5: 传统 403 工具将假 200 误判为漏洞
* **Problem**: 携带 `X-Rewrite-URL` 或后缀时，网关返回公开首页或重定向至登录页（状态码 200），传统工具误报为突破。
* **Root Cause**: 混淆了“状态码变化（Access Outcome）”与“资源身份同一性（Resource Identity）”。
* **Correct Fix**: 引入 `SemanticEquivalenceEvaluator`，利用公开根路由预览相似度比对与登录表单特征过滤假 200。

### Pitfall 6: 根目录执行 Pytest 丢失 Pythonpath 导致 39 个 ModuleNotFoundError
* **Problem**: 在根目录执行 `uv run --project python pytest` 报 39 个收集错误。
* **Root Cause**: Pytest 默认以当前根目录为 `rootdir`，未加载 `python/pyproject.toml` 里的 `pythonpath`。
* **Correct Fix**: 在仓库根目录建立守护 `pytest.ini`，声明 `pythonpath = python/packages/core/src python`。

### Pitfall 7: 变换变体 ID 碰撞与前导双斜杠拼写缺陷
* **Problem**: 46 个变体生成后去重只剩 38 个；前导双斜杠未生效。
* **Root Cause**: `clean_val_id` 替换 `http://` 后与裸 IP 碰撞；小写重写头大写转换后重名；`f"/{path.lstrip('/')}//"` 少了一个斜杠。
* **Correct Fix**: 引入 `HTTP_` 前缀区分 URL 型 IP，小写重写头赋予 `_LOWER` 后缀，路径改用 `f"//{clean_p}//"`。

### Pitfall 8: 根路由基准探测请求头污染引发自我否定
* **Problem**: `run_research_loop` 无法触发突破成功断言。
* **Root Cause**: 探测公共根路由基准时，误将带有 `X-Rewrite-URL` 的 `variant.headers` 传给了 `/`，导致基准自身变成了机密页面，相似度 100% 被误判为首页回退。
* **Correct Fix**: 探测根路由前严格清洗剥离 `X-Rewrite-URL` / `X-Original-URL` 等重写头。

### Pitfall 9: 测试 Mock 传输层脱钩引发 3 分钟网络超时假死
* **Problem**: 集成测试耗时高达 180.94 秒（3 分钟）且断言失败。
* **Root Cause**: 测试中使用 `patch.object(executor, "transport", Mock)` 只替换了执行器表面引用，内部 `self.research_agent.transport` 仍然死绑定着最初的真实物理网卡，去真实公网解析测试域名超时。
* **Correct Fix**: 在 `_research_denial_loop` 入口处执行动态同步：`self.research_agent.transport = self.transport`，测试耗时由 180 秒骤降至 0.1 秒。

### Pitfall 10: 21 个同质内网 IP 变体霸榜吞噬 Top-12 预算
* **Problem**: 403 阻断场景下，动词隧道 `X-HTTP-Method-Override` 未能被调度发包。
* **Root Cause**: 21 个 IP 伪造头加分后霸占了前 12 个预算名额，动词隧道算子被挤出。
* **Correct Fix**: 实施多样性采样守护（`max_ip_spoofs = 3`），限制同质 IP 变体最多取 3 个，并对针对高危动词（`DELETE`/`PUT`）的动词隧道赋予 `+6.5` 强力加权。

---

## 16. Do Not Repeat

* ❌ **绝对不要启动或编写桌面端（Tauri / React UI）代码**（用户已明确裁决不需要桌面端，Invar 保持纯无头）。
* ❌ 严禁在单元测试和契约测试中强行依赖本地大模型 `llama-server` 服务。
* ❌ 严禁在直接执行 `uv run python` 时遗漏 `--project python`（会导致找不到虚拟环境包）。
* ❌ 严禁把工具名称（`subfinder/`、`httpx/`）当作核心资产存储目录。
* ❌ 严禁把 403 粗暴等同于 WAF，严禁把 200 粗暴等同于漏洞突破。
* ❌ 严禁破坏 `Train ∩ Gold = ∅` 物理防火墙。
* ❌ 严禁单次运行两次重复测试（用户明确指示执行一次测试验证即可）。

---

## 17. Invariants

* **I-01**: `Train ∩ Gold = ∅` (训练集与黄金测试集 Surface 重叠恒等于 0)。
* **I-02**: `subdomains.jsonl`、`live_hosts.jsonl`、`urls.jsonl`、`javascript.jsonl` 是不可破坏的单表数据契约。
* **I-03**: 任务清单中的 HTTP 动词必须严格属于标准 7 大动词白名单，路径必须以前导 `/` 开头。
* **I-04**: 根目录 `HANDOFF.md` 为全工程唯一权威交接事实源。
* **I-05**: 任何实锤漏洞（`CONFIRMED`）必须满足 8 大前置谓词校验并通过连续同态发包稳定性核验。
* **I-06**: 系统架构保持纯无头（Headless），专注 Rust Core 进程编排与 Python System-2 科研实证。

---

## 18. Open Issues

* **Issue 1**: 78 个 targeted research tasks 需要通过批量实证脚本跑通真实的批量审计验证流程。
* **Issue 2**: 本地 `llama-server`（`Qwen-27B`）的思维链破局兜底逻辑需在 Phase D 启发式穷尽时作为备选分支接入。

---

## 19. Environment / Toolchain

* **OS**: Windows 11
* **Shell**: PowerShell
* **Rust Toolchain**: Cargo 1.80+ (2021 edition, target: `x86_64-pc-windows-msvc`)
* **Python Runtime**: Python 3.12 (CPython 3.12.13, managed via `uv`)
* **Local LLM Server**: `llama-server.exe` (监听 `127.0.0.1:8080`，按需开启，非测试依赖)
  - 主脑模型 1: `Qwen3.8-27B-Uncensored-IQ3_XXS.gguf`
  - 先锋模型 2: `Ornith-1.5-9B-Abliterated-IQ3_M.gguf`
* **Compute Hardware**: NVIDIA GeForce RTX 3060 (12GB VRAM, DirectML / CUDA 12.4)

---

## 20. Roadmap

* **Phase 1~4**: 资产全源收集、存活画像、Katana 爬取、AST 解析、双轨融合 (COMPLETED)
* **Phase 5.1**: 靶心任务装配轻量化与动词清洗 (COMPLETED, 156 KB)
* **Phase 5.2 (403架构)**: 403 拒绝响应架构重构与 `pi-agent-core` 循环内核落地 (COMPLETED, 181+ 测试全绿)
* **Phase 5.3 (实证实战)**: **消费 78 个靶向任务，跑通批量实证审计流水线并输出 5 大战报 (CURRENT FOCUS)**
* **Phase 5.4 (模型破局)**: 启发式变异穷尽时唤醒本地 `llama-server` 进行 CoT 思维链非标载荷破局
* **Phase 5.5**: 独立第三方复核与 PromotionGate 门禁，生成不可变 `KnowledgeCard`

---

## 21. Recovery Protocol

新 AI 接手会话后，严格按照以下步骤恢复上下文：
1. 读取根目录 `HANDOFF.md`，确认版本为 v9.0.0。
2. 确认当前分支与工作区干净，**确认桌面端（Tauri / React UI）彻底处于 OUT OF SCOPE**。
3. 执行 `uv run --project python pytest` 与 `cargo test --workspace` 验证全量回归（应为 181+ 与 15 全绿）。
4. 确认 `artifacts/reports/targeted_research_tasks_78.json` 已经就绪（156 KB，78 个靶标）。
5. 锁定 CURRENT OBJECTIVE（消费 78 靶标任务，构建批量实证审计管道），**仅执行 NEXT SINGLE ACTION**。

---

## 22. AI Collaboration Protocol

* **中文优先**：解释与汇报全部采用中文，保留代码中的真实英文标识。
* **单步工程推进**：每轮对话仅推进一个明确的工程闭环，严禁倾倒未经验证的跨阶段修改。
* **单次测试原则**：每轮只执行一次测试验证，杜绝重复多次运行测试套件。
* **源码落地习惯**：Windows 环境一律使用 PowerShell `@' ... '@ | Set-Content -Encoding UTF8` 完整落盘。
* **测试守门**：任何功能代码修改必须伴随测试通过证明方可交付。

---

## 23. Security / Sensitive Data Boundary

* 私有敏感凭证通过环境变量 `INVAR_AUTH_TOKEN` 与 `GEMINI_API_KEYS` 运行时注入，严禁硬编码进代码或提交进 Git。
* 所有针对目标的探测必须受 `data/targets/<target>/scope.txt` 授权边界约束。

---

## 24. Reproducibility Status

**FULLY REPRODUCIBLE (CORE ENGINE & HARNESS)**  
核心接口、算法状态机、403 拒绝研究架构、pi 事件循环、环境依赖和 196 项全量测试完全具备确定性闭环，代数与测试事实 100% 自包含。

---

## 25. Handoff Self-Check

- [x] 一个新 AI 是否知道当前到底在做什么？（知道：已彻底完成 403 与 pi 原语重构，正在准备消费 78 个真实靶心任务跑批量实证）。
- [x] 一个新 AI 是否知道最后一次成功状态？（知道：Python 181+ 项全绿，Rust 15 项全绿，全工程零报错）。
- [x] 一个新 AI 是否知道最后修改了哪些文件？（知道：`sandbox_executor.py`、`research_agent.py`、`research_loop.py` 等）。
- [x] 一个新 AI 是否知道为什么这么设计？（知道：解耦 WAF 拓扑与拒绝类型、三值逻辑语义等价防 200 误报、吸收 pi 事件循环与双队列）。
- [x] 一个新 AI 是否知道哪些行为不能破坏？（知道：单表资产契约不能破坏、不可碰桌面端、实锤必须过重放验真）。
- [x] 一个新 AI 是否知道当前唯一下一步？（知道：编写靶向任务实证实战批量调度管道 `run_targeted_audit.py`）。
- [x] 一个新 AI 是否知道当前阶段不能做什么？（知道：绝对不要做桌面端 UI，不要盲目跑全网扫描，不要依赖外部大模型跑单测）。
- [x] 一个新 AI 是否知道如何运行测试？（知道：根目录直接 `uv run --project python pytest` 和 `cargo test --workspace`，单次运行）。
