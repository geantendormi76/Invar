# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot & State-Machine Recovery Contract  
> **Project:** Invar (System-2 Targeted Verification & Research Engine)  
> **Triad Context:** `C:\dev\distiller` (Data) + `C:\dev\Base-Jev` (System-1 Model) + `C:\dev\Invar` (System-2 Verification)  
> **Canonical Root:** `C:\dev\Invar`  
> **Canonical Handoff Path:** `C:\dev\Invar\HANDOFF.md`  
> **Snapshot Date:** 2026-09-22  
> **Specification Version:** 7.0.0 (Phase-5 Invar System-2 Targeted Execution & Monorepo Closure Edition)  
> **Primary Purpose:** 当当前会话关闭、上下文清空后，一个完全没有历史记忆的新 AI，仅凭本文件与当前项目源码、测试和配置，即可 100% 恢复当前状态，并精准执行唯一下一步动作，禁止重新猜测、重新设计或重复既有成果。

---

## 0. Handoff Metadata

| Item | Value | Level | Notes |
|---|---|---|---|
| Project Name | Invar | [FACT] | System-2 深度动态执行、差分对账与安全不变量实证主引擎 |
| Repository Root | `C:\dev\Invar` | [FACT] | 标准 AI Engineering Monorepo 体系 |
| Workspace State | Clean (100% Git Synced, 0 Ghost Paths) | [FACT] | 历史空壳 `src/`, `src-tauri/`, `c/` 已彻底清除 |
| Rust Core Test Status | **15 passed; 0 failed** | [FACT] | `cargo test --workspace` (含跨进程调度管道实测) |
| Python Core Test Status | **138 passed in 0.29s; 0 failed** | [FACT] | `uv run pytest` (全量单元测试与契约测试) |
| Local Model Deployment | `models/invar-intent-0.6b-v1/` | [FACT] | 原子化自包含包（Passport + 1.25GB ONNX + Tokenizer） |
| ONNX Checksum | `908db8140ab25a3230a0e541145b05421250c9a126078d0014f106b675ba11cc` | [FACT] | SHA256 校验 100% 吻合，DirectML 稳态延迟 23.08ms |
| Assembled Tasks | 78 Targeted Research Tasks | [FACT] | Pool A (48) + Pool B (30) 已完成首轮用例分流 |
| Task Breakdown | P0=12, P1=40, P2=23, P3=3 | [FACT] | 固化至 `artifacts/reports/targeted_research_tasks_78.json` |

---

## 1. Project Identity

[DECISION]
本系统属于工业级三位一体架构（Triad Architecture）中的第三环：
1. **distiller** (`C:\dev\distiller`): 专家知识编译车间，负责双师蒸馏与物理防火墙隔离（`Train ∩ Gold = ∅`）。
2. **base-jev** (`C:\dev\Base-Jev`): System-1 认知反射前哨，0.6B 判别式模型（DirectML FP16，~23ms），输出后验分布与分数。
3. **Invar** (`C:\dev\Invar`): **System-2 深度科研与动态执行验证引擎（当前工程主战场）**。基于 AST 语法切片、双轨比对器分层池、双主体差分比对（IDOR）、安全不变量判决（破坏性确认防护、特权认证放行）以及五维标准化交付报表，对高危端点发起真实的闭环探测与事实确权。

---

## 2. Current Mission

[DECISION]
正式由“静态代码解析与双轨离线比对”阶段，全面跨入 **Phase 5：Invar System-2 动态执行与漏洞实证阶段**。利用双轨比对输出的 78 个高危靶心端点（包含规则保底 Pool A 与模型挖掘 Pool B），针对其 Impact / Sensitivity 特征发起自动化闭环探测与实证发包。

---

## 3. Current Objective

[FACT]
完成 `python/packages/core/src/harness/triage_dispatcher.py` 与 `assemble_triage_tasks.py` 的**轻量化（切片压缩）与脏动词纠偏升级**，使导出的 `targeted_research_tasks_78.json` 体积从 23MB 压缩回收至百 KB 级且动词 100% 合法，并交付下游执行器（`AdaptiveSandboxExecutor` / `ResearchOrchestrator`）进行这 78 个核心靶心（特别是 12 个 P0 靶点）的首次闭环发包验证。

---

## 4. Next Single Action

**CURRENT OBJECTIVE → NEXT SINGLE ACTION**

[FACT]
**当前唯一下一步动作**：
在本地终端执行升级后的 `assemble_triage_tasks.py`，落盘紧凑合规版任务集，验证 `targeted_research_tasks_78.json` 的文件大小（降至 100KB 以内）与前 8 项任务的 HTTP 动词（`E/T/R` 纠偏为标准动词），并在控制台确认输出回执。

---

## 5. Current Scope

**当前正在修改/执行的代码与资产**：
* `python/packages/core/src/harness/triage_dispatcher.py`（动词标准化 `_normalize_method` 与代码切片上限截断 `_compact_slice`）
* `python/scripts/assemble_triage_tasks.py`（靶心装配 CLI 入口）
* `python/tests/test_triage_dispatcher.py`（分流器契约测试用例）
* `artifacts/reports/targeted_research_tasks_78.json`（最终生成的 78 个待测任务物证）

---

## 6. Out of Scope

**当前阶段明确禁止触碰的红线**：
* ❌ 严禁重训 `base-jev` 或修改已导出的 `system_one_unified.onnx`（出厂护照已封签）。
* ❌ 严禁破坏或修改 `Train ∩ Gold = ∅` 物理防火墙及黄金集真值。
* ❌ 严禁借动态执行之名引入无关重构、全局重构或前端 UI 逻辑修改。
* ❌ 严禁无授权针对非本地/非受控外部系统实施无边界破坏性发包。
* ❌ 严禁在 `models/` 下再次拆解碎片化子目录。

---

## 7. Last Known Good State

[FACT — Snapshot at 2026-09-22]
* **Monorepo Directory Layout**: 标准 AI Monorepo 骨架完备，根目录多余空壳 `src/` 已物理删除。
* **Ghost Path Audit**: 全库扫描 `src-tauri`、`scripts/asset`、`scripts/pipeline`、`c/HANDOFF.md` 命中数恒等于 **0**，审计通过固化在 `docs/ai/PATH_MIGRATION.md`。
* **Rust Core**: `cargo test --workspace` 编译运行 **15 passed, 0 failed, 0 warnings**。
* **Python Workspace**: `uv run pytest` 全量 **138 passed in 0.29s, 0 failed**。
* **Model Asset**: `models/invar-intent-0.6b-v1/` 自包含就绪（`MODEL_PASSPORT.json` + `system_one_unified.onnx` + `tokenizer.json`），SHA256 哈希校验一致。
* **Triage Assembler**: 成功解析 Pool A (48) + Pool B (30) 共 78 个核心靶标，分流出 P0=12, P1=40, P2=23, P3=3。

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| Monorepo 拓扑迁移 | DONE | 0 幽灵路径，全目录对齐 | `Cargo.toml`, `crates/`, `python/`, `scripts/` | 结构符合工程规范。 |
| 模型资产自包含整合 | DONE | SHA256 吻合，单路径接入 | `models/invar-intent-0.6b-v1/*` | 拒绝过度拆分，三位一体同捆管理。 |
| 脚手架与交接契约固化 | DONE | 文件就位，执行自洽 | `tools/bootstrap/ai_monorepo_scaffold.py`, `tools/repomix/1_.json` | 机械事实源锁定。 |
| 双轨靶标装配器实现 | DONE | 6 项专用测试全部通过 | `python/packages/core/src/harness/triage_dispatcher.py` | 映射 Impact/Sensitivity 到 P0/P1/P2。 |
| Rust 契约跨进程对齐 | DONE | 15 项 Rust 测试全绿 | `crates/core/tests/*` | `ResearchTask` 序列化无损互通。 |
| 78 个实战靶心首轮装配 | DONE | 78 个任务成功分类落盘 | `artifacts/reports/targeted_research_tasks_78.json` | 揭示切片膨胀与非标动词两大深层问题。 |

---

## 9. Changed Files

### Current Repository Layout
```text
Invar/
├── apps/
│   └── desktop/                  # React 19 + TypeScript + Tailwind v4 + Tauri 2 骨架
├── crates/
│   └── core/                     # Rust 核心编排引擎 (ResearchOrchestrator)
│       ├── Cargo.toml
│       ├── src/ (lib.rs, main.rs, orchestrator.rs)
│       └── tests/ (15 tests: orchestrator, pipeline_e2e, process_executor, smoke)
├── python/
│   ├── packages/core/            # Python 核心库 (harness + agent)
│   │   └── src/
│   │       ├── agent/ (hunter, critic, wave_orchestrator, hypothesis, promoter)
│   │       └── harness/ (sandbox_executor, triage_dispatcher, idor, tamper, models)
│   ├── scripts/                  # 生产 CLI 入口 (scan_pipeline.py, assemble_triage_tasks.py)
│   ├── tests/                    # 138 个单元/集成测试 (test_triage_dispatcher.py 等)
│   └── pyproject.toml            # uv 管理依赖 (含 pytest>=8.0)
├── configs/
│   └── base/                     # 声明式基础配置 (default.json, project.toml)
├── data/
│   └── targets/ikuai8.com/       # 黄金集盲标资产与 HTTP surface 证据
├── models/
│   └── invar-intent-0.6b-v1/     # 自包含模型包 (Passport + 1.25GB ONNX + Tokenizer)
├── artifacts/
│   └── reports/                  # 永久物证报告 (targeted_research_tasks_78.json 等)
├── scripts/
│   ├── audit/                    # 黄金集盲态与学术评测 (evaluate_gold_set_v4.py 等)
│   └── data/                     # 资产收集、物化与比对流水线 (asset/, pipeline/)
├── docs/
│   ├── ai/                       # REPOSITORY_PLAN.md, FILE_DECISIONS.md, PATH_MIGRATION.md, REPOSITORY_CLOSURE.md
│   └── architecture/             # 架构演进 ADR
├── tools/
│   ├── bootstrap/                # ai_monorepo_scaffold.py
│   └── repomix/                  # 1_.json
├── Cargo.toml                    # 顶层工作区声明 (members = ["crates/core"])
├── HANDOFF.md                    # 本文件 (全工程唯一权威交接事实源)
└── README.md                     # 顶层工程导航与快速运行指南
```

---

## 10. Current Architecture

[DECISION]
**System-1 直觉初筛与 System-2 深度实证闭环交互流**：
```text
[HTTP Surface / Katana / AST Raw JS]
               │
               ▼
[scripts/data/asset/triage_dual_track_comparator.py]
   ├─ Rule Profile (Regex / Tags) ───► Pool A (48 核心规则靶心)
   └─ Neural Profile (0.6B ONNX)  ───► Pool B (30 盲区破盲靶心)
               │
               ▼
[python/packages/core/src/harness/triage_dispatcher.py] (★ ACTIVE DISPATCHER)
   ├─ Impact >= 3.5 & Sens >= 3.5 ───► P0 (双高特权/破坏复合 Profile)
   ├─ Impact >= 3.5              ───► P1 (破坏性确认防护 Profile: H-DESTRUCT-1)
   ├─ Sens >= 3.5 & Has ID Param ───► P1 (双主体 IDOR 差分比对 Profile: H-IDOR-1)
   └─ Pool A Rule High           ───► P2 (规则防御边界验证 Profile: H-AUTH-1)
               │
               ▼
[artifacts/reports/targeted_research_tasks_78.json]
               │
               ▼
[System-2 Verification Engine] (★ NEXT IMPLEMENTATION)
   ├─ Rust Crates Core (ResearchOrchestrator 进程管道调度)
   └─ Python Harness (AdaptiveSandboxExecutor 自适应发包与变异自愈)
```

---

## 11. Architecture Decisions

### AD-01 — Self-Contained Atomic Model Package
* **Decision**: 废除将模型拆散到 `checkpoints/`、`registry/`、`tokenizers/` 的过度设计，统一收拢至 `models/<model-id>/` 独立目录。
* **Why**: 交付期模型是三位一体强绑定的发行包，单路径加载（`--model-dir`）降低心智负荷，换模型秒级热插拔，生命周期管理绝对干净。
* **Evidence**: `models/invar-intent-0.6b-v1/` 集中管理后，SHA256 校验依然 100% 吻合，`.gitignore` 规则通过后缀过滤依然生效。

### AD-02 — Dual-Track Orthogonal Priority Dispatching
* **Decision**: 任务分级不采用单一标量混杂分数，而是基于 Impact（状态破坏）与 Sensitivity（敏感泄露）双正交矩阵：
  - Dual-High $\to$ P0 最高优先级；
  - Single-High $\to$ P1 专项目标；
  - Rule-Only $\to$ P2 保底核验。
* **Why**: 破坏性漏洞关注未授权状态篡改（缺少 confirm/csrf），敏感数据关注双主体越权（IDOR/BOLA）。将正交因果特征直接映射到测试 Profile，避免盲目全量扫描。

### AD-03 — Strict Monorepo Responsibility Boundaries
* **Decision**: 根目录禁止存放无主业务代码（如旧 `src/`），Rust 核心驻留 `crates/core`，Python 驻留 `python/packages/core`，CLI 脚本驻留 `python/scripts`，数据流水线脚本驻留 `scripts/data`。
* **Why**: 保证跨语言调用、测试路径与持续集成的确定性。

---

## 12. Data / API / Type Contracts

### 1. `TriageTask` Python 契约 (`harness/triage_dispatcher.py`)
```python
@dataclass
class TriageTask:
    task_id: str                      # "sid:method:path"
    endpoint_id: str                  # "method:path"
    coverage_id: str                  # "api-{subsystem}-{attack_class}"
    hypothesis_id: Optional[str]      # "H-DESTRUCT-1" | "H-IDOR-1" | "H-AUTH-1" | None
    profile: str                      # "p0_dual_high_state_and_confidentiality" | ...
    method: str                       # 标准 HTTP 动词 (大写)
    path: str                         # 以 "/" 开头的合规路径
    surface_id: str                   # 24位唯一表面哈希
    pool_origin: str                  # "POOL_A_RULE_MUST_KEEP" | "POOL_B_DISCREPANCY"
    priority: str                     # "P0" | "P1" | "P2" | "P3"
    attack_class: str                 # "unauthorized_state_and_idor" | "idor_boundary" | ...
    extracted_params: List[str]       # AST 提取的参数列表
    impact_score: float               # 1.0 ~ 5.0
    sensitivity_score: float          # 1.0 ~ 5.0
    code_slice: Optional[str]         # 截断上限 800 字符的上下文代码
    source_file: Optional[str]
    source_line: Optional[int]
```

### 2. Rust `ResearchTask` 序列化对齐契约 (`crates/core/src/orchestrator.rs`)
```rust
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResearchTask {
    #[serde(alias = "case_id")]
    pub task_id: String,
    #[serde(default)]
    pub endpoint_id: String,
    #[serde(default)]
    pub coverage_id: String,
    pub hypothesis_id: Option<String>,
    #[serde(default)]
    pub profile: String,
    #[serde(default)]
    pub method: String,
    #[serde(default)]
    pub path: String,
}
```

---

## 13. Algorithms / Workflow

### 靶标分流与假说装配算法 (`classify_and_assemble`)
```text
输入: DualTrack Row (Method, Path, Params, RuleTags, ImpactScore, SensScore)
  │
  ├─ 1. 动词清洗: _normalize_method (剔除 E/T/R 等 AST 噪音残片，纠偏为标准动词)
  ├─ 2. 切片压缩: _compact_slice (上限保留 800 字符，杜绝 IPC 膨胀)
  ├─ 3. 维度判定: is_high_impact = (Impact >= 3.5), is_high_sens = (Sens >= 3.5)
  ├─ 4. 特征判定: has_id_param = (参数包含 ID 关键词), is_destructive = (DELETE 或含破坏词)
  │
  ▼
分流决策树:
  ├── [Impact >= 3.5 AND Sens >= 3.5]
  │     └─ Priority: P0 | Profile: p0_dual_high | Hypothesis: (H-DESTRUCT-1 if destructive else H-AUTH-1)
  ├── [Impact >= 3.5]
  │     └─ Priority: P1 | Profile: p1_state_mutation | Hypothesis: (H-DESTRUCT-1 if destructive else H-AUTH-1)
  ├── [Sens >= 3.5]
  │     └─ Priority: P1 | Profile: p1_differential_idor | Hypothesis: (H-IDOR-1 if has_id_param else H-AUTH-1)
  ├── [Rule.HighRisk == True]
  │     └─ Priority: P2 | Profile: p2_rule_defense | Hypothesis: H-AUTH-1
  └── [Default]
        └─ Priority: P3 | Profile: p3_surface_exploration | Hypothesis: None
```

---

## 14. Verified Tests

| Test Target | Command | Passed / Total | Result |
|---|---|---|---|
| Rust Core 全量集成测试 | `cargo test --workspace` | 15 / 15 | **PASSED** (含 IPC 子进程实测) |
| Python Core 契约测试全集 | `cd python && uv run pytest` | 138 / 138 | **PASSED in 0.29s** |
| 双轨比对器数学自检 | `uv --project python run python scripts/data/asset/triage_dual_track_comparator.py --self-test` | 1 / 1 | **PASSED (`SELF_TEST_OK`)** |
| 幽灵路径全局扫描 | 自动化字面量探针扫描 | 103 / 103 文件 | **PASSED (0 残留)** |

---

## 15. Failure / Pitfall Registry

### Pitfall 1: 模型资产过度拆解导致碎片化
* **Problem**: 把单模型拆分到 `registry/`、`checkpoints/`、`tokenizers/`，带来路径指定复杂与版本错配隐患。
* **Root Cause**: 混淆了微调训练期（基座共享）与推理交付期（原子发包）的生命周期差异。
* **Correct Fix**: 采用自包含模型包 `models/<model-id>/`（Passport + ONNX + Tokenizer 同捆集中存放）。

### Pitfall 2: 前端 AST 提取的动态残片导致脏动词
* **Problem**: 提取到 `E api/...`、`T api/...`、`R /fs/...` 等单字母非标 HTTP 动词。
* **Root Cause**: 前端动态数组或三元表达式提取时，语法解析器截取到变量末尾单个字符。
* **Correct Fix**: 引入 `_normalize_method()` 启发式纠偏与标准 HTTP 动词白名单过滤。

### Pitfall 3: 代码切片未截断引发 JSON 文件体积膨胀
* **Problem**: 78 个任务落盘文件暴增至 23.1 MB。
* **Root Cause**: AST 切片直接捕获了打包混淆文件的超长单行，未设边界原样 dump。
* **Correct Fix**: 在 `_compact_slice()` 中设置 800 字符紧凑截断上限，并对 `rust_tasks` 剔除长文本负载。

---

## 16. Do Not Repeat

* ❌ 严禁使用字符串拼接方式写死跨项目绝对路径（如 `C:\dev\Base-Jev`）。
* ❌ 严禁向非破坏性端点分配 `H-DESTRUCT-1` 假说（会导致不变量评估器因非破坏性而提前短路）。
* ❌ 严禁将未压缩的原始代码大文本直接塞入跨进程 IPC 数据管道。
* ❌ 严禁跳过测试直接修改上游数据格式。

---

## 17. Invariants

* **I-01**: `Train ∩ Gold = ∅` (训练集与黄金测试集 Surface 重叠恒等于 0)。
* **I-02**: Rust Core 与 Python Harness 的任务交互数据结构必须严格双向兼容。
* **I-03**: 根目录 `HANDOFF.md` 为全工程唯一权威交接事实源。
* **I-04**: 幽灵路径数量在任何重构后必须保持为 **0**。

---

## 18. Open Issues

* **Issue 1**: AST 切片包含混淆代码的换行折叠问题（当前通过 `_compact_slice` 规避，后续可引入纯 AST 封闭作用域提取）。
* **Issue 2**: 部分动态生成的端点路径缺失前导 `/`（已在分流器中通过 `path = "/" + raw_path.lstrip("/")` 完成防护）。

---

## 19. Environment / Toolchain

* **OS**: Windows 11
* **Shell**: PowerShell
* **Rust Toolchain**: Cargo 1.80+ (2021/2024 edition, target: `x86_64-pc-windows-msvc`)
* **Python Runtime**: Python 3.12 (CPython 3.12.13, managed via `uv`)
* **Hardware GPU**: NVIDIA GeForce RTX 3060 (12GB VRAM, DirectML / Direct3D 12)
* **Testing Engines**: `pytest>=8.0.0` (Python), `cargo test` (Rust)

---

## 20. Roadmap

* **Phase 0-4**: 蒸馏取证、SFT 80% 破局、学术评测 v4.0、Monorepo 归一化 (ALL COMPLETED)
* **Phase 5.1**: 靶心任务分流与用例装配器 `TriageDispatcher` (COMPLETED)
* **Phase 5.2**: **任务集紧凑化与脏动词清洗升级 (CURRENT FOCUS)**
* **Phase 5.3**: 闭环沙箱探测发包与双主体差分实证 (NEXT FOCUS)
* **Phase 5.4**: Finding 权威生成与 PromotionGate 知识卡片晋级

---

## 21. Recovery Protocol

新会话恢复上下文时，必须且仅需执行以下动作：
1. 读取根目录 `HANDOFF.md`，确认版本为 v7.0.0。
2. 确认当前分支为 `main`，执行 `git status` 确认工作区干净。
3. 执行 `cargo test --workspace` 与 `cd python && uv run pytest` 验证 Last Known Good State。
4. 确认 CURRENT OBJECTIVE，**仅执行 NEXT SINGLE ACTION**。

---

## 22. AI Collaboration Protocol

* **中文优先**：解释与汇报全部采用中文，保留代码中的真实英文标识。
* **单步工程推进**：每轮对话仅推进一个明确的工程闭环，严禁倾倒未经验证的跨阶段修改。
* **源码落地习惯**：Windows 环境一律使用 PowerShell `@' ... '@ | Set-Content -Encoding UTF8` 完整落盘。
* **测试守门**：任何功能代码修改必须伴随测试通过证明方可交付。

---

## 23. Security / Sensitive Data Boundary

* 本地配置已通过 `configs/base/default.json` 脱敏。
* 私有敏感凭证通过环境变量 `INVAR_AUTH_TOKEN` 与 `INVAR_AUTH_TOKEN_B` 运行时注入，严禁硬编码进代码或提交进 Git。

---

## 24. Reproducibility Status

**FULLY REPRODUCIBLE**
* 依赖版本、Rust 工作区、Python `uv` 虚拟环境、自包含模型包与全量测试套件 100% 具备确定性。

---

## 25. Handoff Self-Check

- [x] 新 AI 是否清楚当前在做什么？（知道：Phase 5 动态执行阶段，正在处理 78 个核心靶心的装配清洗与实证发包）。
- [x] 新 AI 是否知道最后一次成功状态？（知道：15 项 Rust 测试 + 138 项 Python 测试全绿，78 个靶标首轮装配完成）。
- [x] 新 AI 是否知道为什么模型目录集中存放？（知道：推理交付期自包含模型包优于过度拆解）。
- [x] 新 AI 是否知道当前唯一步骤？（知道：执行 `triage_dispatcher.py` 升级，压缩 23MB 文件并纠偏 `E/T/R` 脏动词）。
