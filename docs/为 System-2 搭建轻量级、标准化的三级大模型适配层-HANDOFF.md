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
> **Document Version:** 8.0.0 (Genesis Run Full-Stack Convergence & Tri-Tier LLM System-2 Architecture Edition)  
> **Primary Purpose:** 当当前 AI 会话关闭、上下文丢失、开发人员忘记历史时，一个完全没有历史记忆的新 AI，仅凭本文件与当前项目源码、测试和配置，即可 100% 精确恢复当前工程状态，并从正确位置继续推进，禁止重新猜测、重新设计或重复既有成果。

---

## 0. Handoff Metadata

| Item | Value | Evidence Level | Notes |
|---|---|---|---|
| Project Name | Invar | [FACT] | System-2 深度动态执行、差分对账与安全不变量实证主引擎 |
| Repository Root | `C:\dev\Invar` | [FACT] | 标准 AI Engineering Monorepo 体系 |
| Workspace State | Clean (Genesis Run Completed) | [FACT] | 历史旧产物已彻底清空，从零走通模块 1 至模块 5.1 |
| Active Target | `ikuai8.com` | [FACT] | 授权测试根域，法定边界记录于 `data/targets/ikuai8.com/scope.txt` |
| Passive Recon Surface | 68 Active Subdomains | [FACT] | `crt.sh` (42) + `subfinder` (67) 多源合流去重入库 |
| Web Alive Surface | 31 Live Web Hosts | [FACT] | HTTPX 存活探测过滤，剔除 37 个僵尸/离线域名 (存活率 45.6%) |
| Spidered Static Code | 206 Physical JS Files | [FACT] | Katana (48,779 原始线索) $\to$ 783 URLs $\to$ 206 JS 落盘于 `tmp/raw_js/` |
| AST Endpoint IR | 1,216 API Endpoints | [FACT] | Tree-sitter 提取，剥离 298 个具参接口，存入 `tmp/ikuai8_endpoints_report.json` |
| Neural 0.6B Triage | 1,216/1,216 1:1 Aligned | [FACT] | 由 `Base-Jev` GPU 驱动物理双头完成，落盘 `tmp/base_jev_predictions_1216.jsonl` |
| Dual-Track Pools | Pool A: 48, Pool B: 30, Pool C: 30 | [FACT] | 双轨比对器规则与神经并集融合，落盘 `artifacts/reports/triage_pools_v2.json` |
| Targeted Tasks | 78 Tasks (156.07 KB) | [FACT] | P0=12, P1=41, P2=23, P3=2，固化于 `artifacts/reports/targeted_research_tasks_78.json` |
| Rust Core Test Status | **15 passed; 0 failed** | [FACT] | `cargo test --workspace` (含跨进程调度管道实测) |
| Python Core Test Status | **141 passed in 0.35s; 0 failed** | [FACT] | `uv run --project python pytest` (全量单元与契约测试) |

---

## 1. Project Identity

[DECISION]
本系统属于工业级三位一体架构（Triad Architecture）中的第三环：
1. **distiller** (`C:\dev\distiller`): 专家知识编译车间，负责双师蒸馏与物理防火墙隔离（`Train ∩ Gold = ∅`）。
2. **base-jev** (`C:\dev\Base-Jev`): System-1 认知反射前哨，0.6B 判别式微调工厂（DirectML FP16，~23ms），输出后验分布与分数。
3. **Invar** (`C:\dev\Invar`): **System-2 深度科研与动态执行验证引擎（当前工程主战场）**。基于 AST 语法切片、双轨比对器分层池、双主体差分比对（IDOR）、安全不变量判决（破坏性确认防护、特权认证放行）以及五维标准化交付报表，对高危端点发起真实的闭环探测与事实确权。

---

## 2. Current Mission

[DECISION]
正式由“静态代码解析与双轨离线比对”阶段，全面跨入 **Phase 5.2：Invar System-2 动态执行与漏洞实证阶段**。利用双轨比对装配出的 78 个核心靶心端点（包含规则保底 Pool A 与模型挖掘 Pool B，特别是 12 个 P0 靶点），接入经过架构确认的**三级大模型编排体系（Tri-Tier LLM Architecture）**，实施自适应发包、报错自愈变异与安全不变量实锤。

---

## 3. Current Objective

[FACT]
为 `Invar/python/packages/core/src/harness/`（或 `agent/`）构建统一的大模型适配层 **`ModelProvider`**（基于标准 OpenAI 兼容协议），打通与本地 `llama-server`（`127.0.0.1:8080`，承载 `Ornith-1.5-9B` 极速发包变异与 `Qwen3.8-27B` 深度思维链破局）的通信通道，使 `AdaptiveSandboxExecutor` 摆脱纯硬编码变异，具备由本地无审查模型驱动的“假设推演 $\to$ 载荷合成 $\to$ 反思修正”闭环能力。

---

## 4. Next Single Action

**CURRENT OBJECTIVE → NEXT SINGLE ACTION**

[FACT]
**当前唯一下一步动作**：
在 `Invar` 中编写并测试标准 OpenAI 兼容接口提供者 `LocalLlamaProvider`（位于 `python/packages/core/src/agent/model_provider.py`，或适配现有抽象），实现针对 `http://127.0.0.1:8080/v1/chat/completions` 的单端点快速推演握手，并通过离线 Mock/集成测试验证其超时重试与异常熔断机制。

---

## 5. Current Scope

**当前正在修改/研究的代码与资产**：
* `python/packages/core/src/agent/` 与 `python/packages/core/src/harness/`（模型提供者适配与沙箱发包连接器）
* `python/tests/test_model_provider.py`（模型提供者契约与握手测试）
* `artifacts/reports/targeted_research_tasks_78.json`（已落盘的 78 个待测靶心输入）

---

## 6. Out of Scope

**当前阶段明确禁止触碰的红线**：
* ❌ 严禁再次重跑 Phase 1~4 的全网收集流水线（Genesis Run 数据已锁定并验收完毕）。
* ❌ 严禁在只有 12GB 显存的同一块 GPU 上并发启动 27B 和 9B 模型（必须按需单实例运行或切换）。
* ❌ 严禁将高频动态发包直接压给云端 Gemini 免费层 API（会触发 429 滚动封锁，云端仅限用于最后的知识卡片终审）。
* ❌ 严禁无授权针对非受控外部系统实施无边界破坏性发包。
* ❌ 严禁在 `Invar` 内引入重型 PyTorch 依赖（保持纯净轻量运行时边界）。

---

## 7. Last Known Good State

[FACT — Snapshot at 2026-09-22 13:30]
* **Clean Slate Verification**: 旧历史报告与临时产物已物理清空，全新 Genesis Run 完整无损落盘。
* **Phase 1 (OSINT)**: `ingest_crtsh.py` (42) + `subfinder` (67) 完美合流去重，生成 68 个 active 子域名至 `data/targets/ikuai8.com/subdomains.jsonl`。
* **Phase 2 (HTTPX)**: 自动探路器成功避开 Python 同名库劫持，31 个活跃主机收录至 `data/targets/ikuai8.com/live_hosts.jsonl`。
* **Phase 3 (Spidering)**: Katana 爬取 48,779 条线索 $\to$ 归一化提炼 783 URLs + 206 个 JS $\to$ 206 个 JS 物理无损落盘于 `tmp/raw_js/`。
* **Phase 4.1 (AST)**: Tree-sitter 提取 1,216 个 API 端点与 298 个具参接口，写入 `tmp/ikuai8_endpoints_report.json`。
* **Phase 4.2 (Inference)**: `Base-Jev` GPU 驱动物理双头完成 1,216/1,216 1:1 对齐推演，生成 `tmp/base_jev_predictions_1216.jsonl`。
* **Phase 4.3 (Dual-Track)**: 双轨比对器融合收敛出 Pool A (48) + Pool B (30) + Pool C (30)，落盘 `artifacts/reports/triage_pools_v2.json`。
* **Phase 5.1 (Dispatch)**: `triage_dispatcher.py` 实施动词纠偏与 800 字符切片压缩，生成 78 个任务，文件体积从 23.7 MB 骤降至 **156.07 KB**，落盘至 `artifacts/reports/targeted_research_tasks_78.json`。

---

## 8. Completed Work

| Module | Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|---|
| Module 1 | CT 证书日志挖掘器 | DONE | 42 独立子域，3项单元测试全绿 | `scripts/data/asset/ingest_crtsh.py`, `python/tests/test_ingest_crtsh.py` | 对齐 RFC 6962，处理 Multi-SAN 与通配符。 |
| Module 1 | 多源被动资产合流 | DONE | 68 独立 active 子域名 | `scripts/data/asset/ingest_subdomains.py`, `data/targets/ikuai8.com/subdomains.jsonl` | 快照对账机制，防资产下线误判。 |
| Module 2 | HTTPX 同名二进制解冲突 | DONE | 识别 ProjectDiscovery 路径，存活 31 个主机 | `scripts/data/asset/ingest_httpx.py`, `data/targets/ikuai8.com/live_hosts.jsonl` | 排除 Python `encode/httpx` 命令行劫持。 |
| Module 3 | Katana 爬取与代码物化 | DONE | 48,779 线索 $\to$ 206 个物理 JS 100% 落盘 | `scripts/data/asset/normalize_katana.py`, `download_javascript.py`, `tmp/raw_js/` | 本地物理代码库安全就绪。 |
| Module 4 | Tree-sitter AST 提取 | DONE | 1,216 API 节点，298 个具参接口 | `python/scripts/scan_pipeline.py`, `tmp/ikuai8_endpoints_report.json` | 吻合度 99.6%，离线强类型契约抽取。 |
| Module 4 | 0.6B GPU 全量推演 | DONE | 1,216/1,216 1:1 对齐，平均 140ms/端点 | `C:\dev\Base-Jev\python\scripts\generate_triage_predictions.py` | 双正交打分（Impact + Sensitivity）全量就绪。 |
| Module 4.3| 双轨比对器融合初筛 | DONE | Pool A (48) + Pool B (30) 精准锁定 78 靶心 | `scripts/data/asset/triage_dual_track_comparator.py`, `triage_pools_v2.json` | 规则 ∪ 神经并集，消除 93.6% 无效发包。 |
| Module 5.1| 任务分流器轻量化升级 | DONE | 体积从 23.7 MB 降至 156 KB，单字母动词清零 | `python/packages/core/src/harness/triage_dispatcher.py`, `assemble_triage_tasks.py` | 截断 800 字符，E/T/R 纠偏为合法动词。 |

---

## 9. Changed Files

### Added
* `scripts/data/asset/ingest_crtsh.py` (证书透明度日志被动检索工具)
* `python/tests/test_ingest_crtsh.py` (证书日志解析与通配符清洗单元测试)
* `data/targets/ikuai8.com/scope.txt` (阶段 0 法定测试范围白名单)

### Modified
* `scripts/data/asset/ingest_httpx.py` (内置 `_find_projectdiscovery_httpx` 自适应探路器，根治同名命令冲突与 stderr 吞报错问题)
* `python/packages/core/src/harness/triage_dispatcher.py` (新增 `_compact_slice`、`_normalize_method`、`_normalize_path` 契约防线)
* `artifacts/reports/targeted_research_tasks_78.json` (重构生成 156 KB 紧凑合规任务集)
* `HANDOFF.md` (升级至 v8.0.0 全局交接档案)

---

## 10. Current Architecture

[DECISION]
**全景作战体系：从混沌互联网资产到实锤漏洞证据链（五层全景漏斗图）**：
```text
[互联网全网数据源]
       │
       ▼ 【第 1 步: 多源被动资产侦察 (OSINT & CT Logs)】
    Subfinder (67) + crt.sh (42) ──► ingest_subdomains.py ──► subdomains.jsonl (68 个 active 子域)
       │
       ▼ 【第 2 步: Web 存活验证与边缘画像 (Live Verification)】
    ingest_httpx.py (自适应探路器驱动 HTTPX) ──► live_hosts.jsonl (31 个存活主机，含 auth/audit 等高危资产)
       │
       ▼ 【第 3 步: 前端代码深度爬取与物理物化 (Spidering & Materialization)】
    Katana (48,779 原始线索) ──► normalize_katana.py ──► download_javascript.py ──► tmp/raw_js/ (206 个物理 JS)
       │
       ▼ 【第 4 步: 语法解构与神经反射初筛 (AST & Fast Triage)】
    scan_pipeline.py (Tree-sitter) ──► 1,216 个 API 端点 (298 个具参) 
         │
         ▼ 0.6B ONNX 神经推演 (Base-Jev GPU 车间 1216 逐行对齐)
    triage_dual_track_comparator.py (双轨比对器) ──► triage_pools_v2.json (Pool A 48 + Pool B 30)
         │
         ▼ triage_dispatcher.py (切片截断 800 字符 + 动词合法性清洗)
    artifacts/reports/targeted_research_tasks_78.json (78 个靶标，156 KB，P0=12)
       │
       ▼ 【第 5 步: Invar System-2 动态执行与实证判决 (Verification)】★ CURRENT FOCUS
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 梯队 1【Ornith-1.5-9B (本地 50 t/s, 80K)】: 动态发包载荷生成与快速自愈变异   │
    │ 梯队 2【Qwen3.8-27B (本地思维链 ~20 t/s)】: 403 动词隧道逃逸、IDOR 双主体对账│
    │ 梯队 3【Gemini Flash (云端 3-Key 轮询)】: 独立第三方复核与 KnowledgeCard 终审 │
    └─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
    【交付物】：5 大权威战报 (REPORT.md / findings.json / FINDINGS-DETAIL.md 等)
```

---

## 11. Architecture Decisions

### AD-01 — Three-Tier Hierarchical LLM Allocation for System-2
* **Decision**: System-2 不把所有任务压给单一模型，采用三级金字塔分工：
  - 梯队 1（内环高频发包载荷生成）：`Ornith-1.5-9B-Abliterated`（本地 50 t/s，80K 窗口，无审查，抗并发）；
  - 梯队 2（复杂逻辑深层破局与逃逸）：`Qwen3.8-27B-Uncensored`（本地 20 t/s，CoT 思维链，解决 WAF 动词拦截与 IDOR 差异）；
  - 梯队 3（宏观事实确权与战报结晶）：`Gemini Flash API`（云端 3-Key 轮询与断点管理，用于最终阶段低频事实审核）。
* **Why**: 彭之娘博士《A Year of Hacking with LLMs》指明，单次问答大模型无法应对真实安全实证。必须依赖本地无审查模型进行动态试错闭环，避免触发云端商业 API 的 429 频控熔断或伦理拒答。

### AD-02 — Asset-Centric vs Tool-Centric Storage Boundary
* **Decision**: 废除按工具名称建立子目录（如 `subfinder/`、`httpx/`）的设想，保持 `data/targets/<target>/` 扁平单表设计。
* **Why**: 工具会随技术发展更替淘汰，而“资产实体表”（`subdomains.jsonl`、`live_hosts.jsonl`、`urls.jsonl`、`javascript.jsonl`）是不可变的领域数据模型。将文件视为“数据库单表”可保持最大的工程兼容性。

### AD-03 — Compact Slice Guardrail (800 Chars Max)
* **Decision**: 任务装配时对 `code_slice` 实施 800 字符紧凑截断，并在 Rust 任务结构中完全剔除长文本负载。
* **Why**: 前端混淆单行代码单行可达数百 KB，未截断直接塞入任务文件会导致文件暴增至 23.7 MB，引发跨进程 STDIN 管道阻塞与 OOM 故障。

### AD-04 — Fail-Closed Method Sanitization
* **Decision**: 严格推行标准 HTTP 动词白名单 `{"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}`，对 AST 产生的单字母残片（`E`, `T`, `R`）进行启发式纠偏。
* **Why**: 底层网络传输栈（requests, httpx, reqwest）遇到非标动词会直接抛出非法协议异常。

### AD-05 — Model Factory vs Combat Runtime Decoupling
* **Decision**: 保持 `Base-Jev` 为离线模型炼制工厂，保持 `Invar` 为轻量级独立战斗平台。
* **Why**: Invar 不应污染数个 GB 的 PyTorch / CUDA 训练重型依赖。未来通过升级 ONNX 物理双头包装器，达成纯 `onnxruntime` 独立推理。

---

## 12. Data / API / Type Contracts

### 1. 紧凑型科研任务契约 (`harness/triage_dispatcher.py`)
```python
@dataclass
class TriageTask:
    task_id: str                      # "surface_id:method:path"
    endpoint_id: str                  # "method:path" (已纠偏标准大写动词)
    coverage_id: str                  # "api-{subsystem}-{attack_class}"
    hypothesis_id: Optional[str]      # "H-DESTRUCT-1" | "H-IDOR-1" | "H-AUTH-1" | None
    profile: str                      # 测试轮廓
    method: str                       # 标准合法 HTTP 动词
    path: str                         # 以 "/" 开头的合法 URI
    surface_id: str                   # 24位唯一表面哈希
    pool_origin: str                  # "POOL_A_RULE_MUST_KEEP" | "POOL_B_DISCREPANCY"
    priority: str                     # "P0" | "P1" | "P2" | "P3"
    attack_class: str                 # 攻击面类型
    extracted_params: List[str]       # AST 提取的参数列表
    impact_score: float               # 1.0 ~ 5.0
    sensitivity_score: float          # 1.0 ~ 5.0
    code_slice: Optional[str]         # 截断上限 800 字符的代码上下文
    source_file: Optional[str]
    source_line: Optional[int]
```

### 2. Rust 跨进程任务轻量契约 (`crates/core/src/orchestrator.rs`)
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

### System-2 动态漏洞实证核心闭环
```text
输入: Targeted Research Task (来自 targeted_research_tasks_78.json)
  │
  ├─ 1. 挂载攻防假说: H-AUTH-1 (特权绕过) / H-DESTRUCT-1 (破坏确认) / H-IDOR-1 (双主体越权)
  │
  ├─ 2. 梯队 1 本地 9B 模型载荷推演:
  │     根据 endpoint.extracted_params 与 code_slice 生成初始合理 JSON 载荷
  │
  ├─ 3. 沙箱发包与报错自愈循环 (Adaptive Probe Loop):
  │     发包 ──► 捕获状态码与报错文本
  │     ├── 若命中 Go validator 必填字段缺失 ──► 自适应变异补齐缺失字段 ──► 重试
  │     ├── 若命中 JSON 反序列化类型错误 ──► 自动纠偏数据类型 (str -> int/bool) ──► 重试
  │     └── 若遭遇 403/405 WAF 拦截 ──► 唤醒梯队 2 (27B 深度思维链) 生成动词隧道头 (X-HTTP-Method-Override)
  │
  ├─ 4. 双主体差分实验 (BOLA / IDOR):
  │     若目标携带 ID 参数 ──► 携带 Token A 请求受害者资源 (基线)
  │     ──► 携带 Token B 越权请求同一资源 ──► difflib 响应结构相似度对账
  │
  ├─ 5. 安全不变量综合评定 (Invariant Evaluation):
  │     底线被击穿 ──► Vulnerable ──► 梯队 3 (Gemini / 27B) 编写 Trace 调用链与漏洞根因
  │     底线坚守   ──► Confirmed (证伪假说，确认安全)
  │
  ▼
输出: 经独立复核签署的 FindingRecord ──► PromotionGate ──► KnowledgeCard 与交付战报
```

---

## 14. Verified Tests

| Test Target | Command | Passed / Total | Result | Notes |
|---|---|---|---|---|
| Rust Core 全量集成测试 | `cargo test --workspace` | 15 / 15 | **PASSED** | 涵盖 IPC 管道、跨进程调度与审计战报 |
| Python 证书透明度测试 | `uv run --project python pytest python/tests/test_ingest_crtsh.py` | 3 / 3 | **PASSED** | 离线断言 Multi-SAN 解析与通配符清洗 |
| Python 任务分流器测试 | `uv run --project python pytest python/tests/test_triage_dispatcher.py` | 6 / 6 | **PASSED** | 验证正交优先级与分流假说装配 |
| Python Core 契约测试全集 | `uv run --project python pytest` | 141 / 141 | **PASSED in 0.35s** | 涵盖沙箱、差分、不变量、多轮对账 |

---

## 15. Failure / Pitfall Registry

### Pitfall 1: Python 虚拟环境与工具路径被劫持
* **Problem**: 运行 `ingest_httpx.py` 报错 `RuntimeError: HTTPX failed with exit code 1:`。
* **Root Cause**: `pyproject.toml` 依赖了 Python 客户端 `encode/httpx`，在 `.venv/Scripts/` 生成了同名 `httpx.exe`。当使用 `uv run` 时，虚拟环境路径前置，导致误调用了 Python 库命令而非 ProjectDiscovery 的安全扫描工具。
* **Correct Fix**: 在 `ingest_httpx.py` 中编写 `_find_projectdiscovery_httpx` 自适应探路器，检查 `-version` 包含 `projectdiscovery`，主动排除 `.venv` 干扰。

### Pitfall 2: 前端代码长行引发任务文件体积爆炸
* **Problem**: 78 个任务落盘文件暴增至 23,771 KB（23.2 MB）。
* **Root Cause**: Webpack 混淆代码单行长达数十万字符，AST 切片未设边界原样塞入任务 JSON。
* **Correct Fix**: 引入 `_compact_slice()` 实施 800 字符强行截断，任务集体积骤降 99.3% 至 156 KB。

### Pitfall 3: AST 语法残片导致非标单字母 HTTP 动词
* **Problem**: 出现 `E api/...`、`T api/...`、`R /fs/...` 等非法单字母动词且缺少前导斜杠。
* **Root Cause**: 动态调用代码解构时提取器抓到了局部变量字符残片。
* **Correct Fix**: 引入 `_normalize_method()` 白名单校验与启发式纠偏，以及 `_normalize_path()` 强制前导 `/`。

### Pitfall 4: ONNX 模型导出包装器缺失敏感度头
* **Problem**: 查看 `export_to_onnx.py` 发现计算图只输出了 `score_dist` 和 `score_expected`。
* **Root Cause**: `SystemOneOnnxWrapper` 只调用了单打分头 `forward_score`（对应 `impact_head`），历史微调的双头中 `sensitivity_head` 未连入 ONNX 输出图。
* **Correct Fix**: 严格查明源码事实，不盲目写单头 ONNX 推理器，当前推演继续复用已跑出的真实双头 PyTorch 预测（1,216 行已落盘存证）。

---

## 16. Do Not Repeat

* ❌ 严禁在直接执行 `uv run python` 时遗漏 `--project python`（会导致找不到虚拟环境包）。
* ❌ 严禁把工具名称（`subfinder/`、`httpx/`）当作核心资产存储目录。
* ❌ 严禁在未读取真实源码的情况下，猜测 ONNX 计算图的输出张量语义。
* ❌ 严禁将大批量高频动态测试直接发送至云端 Gemini 免费层。
* ❌ 严禁破坏 `Train ∩ Gold = ∅` 物理防火墙。

---

## 17. Invariants

* **I-01**: `Train ∩ Gold = ∅` (训练集与黄金测试集 Surface 重叠恒等于 0)。
* **I-02**: `subdomains.jsonl`、`live_hosts.jsonl`、`urls.jsonl`、`javascript.jsonl` 是不可破坏的单表数据契约。
* **I-03**: 任务清单中的 HTTP 动词必须严格属于标准 7 大动词白名单，路径必须以前导 `/` 开头。
* **I-04**: 根目录 `HANDOFF.md` 为全工程唯一权威交接事实源。

---

## 18. Open Issues

* **Issue 1**: `Base-Jev` 的 ONNX 导出包装器需升级为物理双头（支持直接输出 `impact_expected` 与 `sensitivity_expected`），以便未来在 Invar 仓内实现纯 `onnxruntime` 独立推演。
* **Issue 2**: `targeted_research_tasks_78.json` 需接入本地 `llama-server` 进行第一波真实发包测试。

---

## 19. Environment / Toolchain

* **OS**: Windows 11
* **Shell**: PowerShell
* **Rust Toolchain**: Cargo 1.80+ (2021 edition, target: `x86_64-pc-windows-msvc`)
* **Python Runtime**: Python 3.12 (CPython 3.12.13, managed via `uv`)
* **Local LLM Server**: `llama-server.exe` (监听 `127.0.0.1:8080`)
  - 主脑模型 1: `Qwen3.8-27B-Uncensored-IQ3_XXS.gguf` (~20 t/s, 32K context, reasoning on)
  - 先锋模型 2: `Ornith-1.5-9B-Abliterated-IQ3_M.gguf` (~50 t/s, 80K context, abliterated)
* **Cloud API**: Google Gemini Flash API (3-Key 轮询池)
* **Compute Hardware**: NVIDIA GeForce RTX 3060 (12GB VRAM, DirectML / CUDA 12.4)

---

## 20. Roadmap

* **Phase 1~4**: 资产全源收集、存活画像、Katana 爬取、AST 解析、双轨融合 (ALL COMPLETED)
* **Phase 5.1**: 靶心任务装配轻量化与动词清洗 (COMPLETED, 156 KB)
* **Phase 5.2**: **三级大模型适配层 `ModelProvider` 搭建与本地 `llama-server` 握手 (CURRENT FOCUS)**
* **Phase 5.3**: P0 靶点动态沙箱发包实证（IDOR 双主体对账与动词隧道逃逸）
* **Phase 5.4**: 独立复核与 PromotionGate 门禁，生成不可变 `KnowledgeCard` 与交付战报

---

## 21. Recovery Protocol

新 AI 接手会话后，严格按照以下步骤恢复上下文：
1. 读取根目录 `HANDOFF.md`，确认版本为 v8.0.0。
2. 确认当前分支与工作区干净。
3. 执行 `cargo test --workspace` 与 `uv run --project python pytest` 验证 Last Known Good State。
4. 确认 `artifacts/reports/targeted_research_tasks_78.json` 已经就绪（156 KB，78 个靶标）。
5. 锁定 CURRENT OBJECTIVE（搭建与测试 `ModelProvider`，对接本地 `127.0.0.1:8080`），**仅执行 NEXT SINGLE ACTION**。

---

## 22. AI Collaboration Protocol

* **中文优先**：解释与汇报全部采用中文，保留代码中的真实英文标识。
* **单步工程推进**：每轮对话仅推进一个明确的工程闭环，严禁倾倒未经验证的跨阶段修改。
* **源码落地习惯**：Windows 环境一律使用 PowerShell `@' ... '@ | Set-Content -Encoding UTF8` 完整落盘。
* **测试守门**：任何功能代码修改必须伴随测试通过证明方可交付。

---

## 23. Security / Sensitive Data Boundary

* 私有敏感凭证通过环境变量 `INVAR_AUTH_TOKEN` 与 `GEMINI_API_KEYS` 运行时注入，严禁硬编码进代码或提交进 Git。
* 所有针对目标的探测必须受 `data/targets/<target>/scope.txt` 授权边界约束。

---

## 24. Reproducibility Status

**FULLY REPRODUCIBLE**  
从互联网资产发现到任务装配落盘，全流程 100% 具备确定性代数闭环，哈希与输出规模完全受测试与代码约束。

---

## 25. Handoff Self-Check

- [x] 新 AI 是否知道当前到底在做什么？（知道：Phase 5.2，正在为 78 个已装配靶心构建大模型适配层进行动态实证）。
- [x] 新 AI 是否知道最后一次成功状态？（知道：Genesis Run 全量走通，78 个任务以 156KB 格式合规落盘）。
- [x] 新 AI 是否知道最后修改了哪些文件？（知道：`ingest_crtsh.py`、`ingest_httpx.py`、`triage_dispatcher.py`）。
- [x] 新 AI 是否知道为什么采用三级大模型编排？（知道：9B 极速高频载荷生成、27B 深度思维链破局、云端 Gemini 终审复核）。
- [x] 新 AI 是否知道哪些行为不能破坏？（知道：不能动单表资产契约、不能把长切片原样塞入任务、不能跨仓硬编码）。
- [x] 新 AI 是否知道当前唯一步骤？（知道：编写并测试 `LocalLlamaProvider` 握手适配器）。
- [x] 新 AI 是否能够依据文档继续恢复？（完全可以）。
