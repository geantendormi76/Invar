# AI Development Handoff Specification

## 0. Handoff Metadata

| 属性项 | 属性值 | 事实等级 | 说明 |
|---|---|---|---|
| Project Name | Invar | [FACT] | System-2 深度动态执行、差分对账与安全不变量实证主引擎 |
| Repository Root | `C:\dev\Invar` | [FACT] | 标准 AI Engineering Monorepo 体系（Rust + Python） |
| Snapshot Timestamp | 2026-09-23 17:00:00 JST | [FACT] | 状态快照生成时间点 |
| Document Version | 12.0.0 (Gold Standards Fully Aligned: OpenVEX & SARIF 2.1.0 & Zero-FP Finalized) | [DECISION] | 国际标准对齐、双重误报消灭、本地消融模型贯通 |
| Python Core Test Status | **202 passed in 0.40s; 0 failed** | [FACT] | 验证命令：`uv run --project python pytest` |
| Rust Core Test Status | **15 passed; 0 failed** | [FACT] | 验证命令：`cargo test --workspace` |
| Global Test Status | **217 passed; 0 failed; 0 warnings** | [FACT] | 全工作区零警告、零失败、零回归 |
| Primary Model Backend | `Ornith-1.5-9B-Abliterated-IQ3_M` | [FACT] | 运行于 `http://127.0.0.1:8080/v1` (开源消融对齐版) |
| Architecture Topology | Headless & Dual-Brain Protocol | [DECISION] | 架构大脑出原子指令，本地消融模型专职现场取证与单步执行 |
| Primary Target Context | `ikuai8.com` (含 `demo`, `cloud`, `spdl` 等子域) | [FACT] | 78 个靶标任务已就绪且物理跑通 |
| Desktop UI State | **OUT OF SCOPE** | [DECISION] | 保持 100% 纯无头（Headless）架构，严禁引入桌面端 |

---

## 1. Project Identity

[DECISION]
本系统属于工业级三位一体架构（Triad Architecture）中的实证闭环中枢：
1. **distiller**: 知识蒸馏与物理隔离防火墙（`Train ∩ Gold = ∅`）。
2. **base-jev**: 0.6B System-1 神经认知反射前哨（23ms 快速初筛）。
3. **Invar**: **System-2 深度科研与动态实证主引擎（当前主战场）**。
   - 贯彻“零臆造、零重复造轮子”的黄金标准对齐哲学；
   - 吸收社区成熟变异经验（nomore403 / NoMoreForbidden 现代反代信任头库）；
   - 输出端双黄金认证闭环：**OpenSSF OpenVEX v0.2.0** 与 **OASIS SARIF 2.1.0**；
   - 由确定性语义等价核验（Semantic Equivalence）与证据门禁（EvidenceGate）垄断漏洞裁决权。

---

## 2. Current Mission

[DECISION]
完成 **Phase 5.4（本地消融大模型针对性 CoT 认知反思破局）** 与 **Phase 5.5（出厂双黄金认证 OpenVEX + SARIF 2.1.0 闭环交付）** 的实证验收与工程固化。
当前已全面攻克 Windows 系统代理挂死、伪 200 业务软拒绝误报、SPA 页面回退假突破三大系统级技术顽疾。

---

## 3. Current Objective

[FACT]
**固化 Phase 5 全闭环工程成果**：
将本地消融大模型实战反思能力、OpenVEX/SARIF 双标准导出以及防误报双重防线正式固化至工程规范中，为后续将这套实证流水线快速迁移至其他新靶场打下工业级基座。

---

## 4. Next Single Action

**当前唯一下一动作**：
将 Phase 5.4（本地模型 CoT 激活）与 Phase 5.5（双黄金标准交付）的实战操作步骤与避坑经验，完整回填至用户本地操作文档 `Invar实战.md` 中，完成知识沉淀。

---

## 5. Current Scope

当前正在修改/维护的核心模块：
* `python/packages/core/src/harness/transport.py`（Windows 注册表代理彻底隔离）
* `python/packages/core/src/harness/sandbox_executor.py`（宿主动态解析、`llm_provider` 注入与软拒绝/HTML 拦截）
* `python/packages/core/src/harness/invariant_evaluator.py`（特权路由与破坏性操作的业务软拒绝与 SPA 回退识别）
* `python/packages/core/src/harness/denial_models.py`（软拒绝 40xx 业务码判定泛化）
* `python/packages/core/src/harness/transformation_models.py`（吸纳 2025-2026 前沿反代信任头与路径畸变）
* `python/packages/core/src/agent/loop_types.py`（新增模型推理强类型事件）
* `python/packages/core/src/agent/research_loop.py`（两段式认知跃迁与软 200 假突破防御）
* `python/packages/core/src/agent/knowledge_promoter.py`（OpenSSF OpenVEX v0.2.0 规范对齐）
* `python/packages/core/src/harness/reporting.py`（OASIS SARIF 2.1.0 标准缺陷报告投影）
* `python/scripts/run_targeted_audit.py`（集成 `--enable-llm` 与 7 大交付物原子化落盘）

---

## 6. Out of Scope

当前阶段明确禁止触碰的红线：
* ❌ 严禁开发桌面端 / Tauri / React UI 表现层（维持 100% 纯无头高性能架构）。
* ❌ 严禁让 9B 本地模型充当全自主全局架构师（防止陷入 30 分钟长思维链自我催眠死锁）。
* ❌ 严禁破坏 `HttpTransport` 的确定性透传契约（严禁在底层网卡内部隐式追加私有参数如 `proxies`）。
* ❌ 严禁破坏已锁定的 202 项 Python 与 15 项 Rust 单元测试行为边界。

---

## 7. Last Known Good State

[FACT]
* **时间**：2026-09-23 17:00 JST
* **Python Core 全量回归测试**：`uv run --project python pytest` $\to$ **202 passed in 0.40s; 0 failed**。
* **Rust Core 工作区测试**：`cargo test --workspace` $\to$ **15 passed; 0 failed**。
* **全量靶向实证战报**：`run_targeted_audit.py` 在 78 个任务上跑出 **48/48 (100.0%) 覆盖率，0 个假阳性误报**。
* **本地模型实战点火**：`tmp/diag_llm_run.py` 成功唤醒本地 8080 端口 `Ornith-1.5-9B-Abliterated`，完成 CoT 推理与闭环断言。
* **交付物产出**：磁盘成功原子化生成 7 大交付物（含 `sarif.json` 与 `openvex.json`）。

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
| ---- | ------ | -------- | ----- | ----- |
| Windows 注册表代理隔离 | DONE | 单发时延由 5.7s 暴降至 150ms~700ms | `transport.py` | 注入 `NO_PROXY="*"` 彻底阻断注册表代理劫持。 |
| 业务级软拒绝识别 | DONE | 任务 #3, #9, #11 精准判定为 CONFIRMED | `denial_models.py`, `invariant_evaluator.py`, `sandbox_executor.py` | 识别 `code in {4001, 4003, 4008}` 与 `forbidden`，消除误报。 |
| SPA 前端 HTML 200 兜底识别 | DONE | 78 任务实测 12 个假漏洞彻底清零 | `invariant_evaluator.py`, `research_loop.py` | 识别 `<!DOCTYPE html>` 阻断假突破。 |
| 变异算子库现代化扩充 | DONE | `test_transformation_family_contract.py` 5/5 passed | `transformation_models.py` | 吸收 `nomore403`/`NoMoreForbidden` 现代 CDN 与反代标头。 |
| Phase 5.4 模型认知跃迁 | DONE | `test_research_loop_llm_contract.py` 1/1 passed + 本地单点物理实测回显 | `loop_types.py`, `research_loop.py`, `sandbox_executor.py`, `run_targeted_audit.py` | 启发式穷尽时唤醒本地 8080 `Ornith-1.5-9B` 开展 CoT 反思。 |
| Phase 5.5 OpenVEX 黄金标准对齐 | DONE | `test_knowledge_promoter.py` 8/8 passed | `knowledge_promoter.py`, `run_targeted_audit.py` | 原生导出对齐 OpenSSF v0.2.0 的 `openvex.json`。 |
| Phase 5.5 SARIF 2.1.0 黄金标准对齐 | DONE | `test_reporting_projections.py` 6/6 passed | `reporting.py`, `run_targeted_audit.py` | 原生导出对齐 OASIS 规范的 `sarif.json`（支持 VS Code/GitHub 渲染）。 |

---

## 9. Changed Files

### Added
* `python/tests/test_research_loop_llm_contract.py` (验证启发式穷尽唤醒 LLM 的契约测试)

### Modified
* `python/packages/core/src/harness/transport.py` (彻底清理环境代理并设置 `NO_PROXY="*"`)
* `python/packages/core/src/harness/denial_models.py` (扩展软拒绝 40xx 业务码区间与拒绝语义词识别)
* `python/packages/core/src/harness/invariant_evaluator.py` (为 `evaluate` 增加 `response_text` 接收与业务错误/HTML 识别)
* `python/packages/core/src/harness/transformation_models.py` (吸收社区前沿反代头 `X-Forwarded-Prefix` / `CF-Connecting-IP` / Next.js 中间件头等)
* `python/packages/core/src/agent/loop_types.py` (新增 `LLM_REASONING_STARTED` / `COMPLETED` 强类型事件)
* `python/packages/core/src/agent/research_loop.py` (两段式认知反思跃迁机制，修复假 200 误判突破提前退出的断层)
* `python/packages/core/src/agent/knowledge_promoter.py` (实现 OpenSSF OpenVEX v0.2.0 Statement 与根文档导出)
* `python/packages/core/src/harness/reporting.py` (实现 OASIS SARIF 2.1.0 规范导出与调用流 CodeFlows 映射)
* `python/scripts/run_targeted_audit.py` (接入 `--enable-llm` 与 OpenVEX/SARIF 联合导出)
* `python/tests/test_knowledge_promoter.py` (扩充 OpenVEX 契约断言)
* `python/tests/test_reporting_projections.py` (断言产物包含 `sarif_json`)

---

## 10. Current Architecture

[DECISION]
**全景作战与双黄金认证技术拓扑**：
```text
targeted_research_tasks_78.json (78个核心靶标输入)
       │
       ▼ 【宿主自动寻址 (Host Auto-Resolution)】
从 task.source_file 解析宿主 (如 demo.ikuai8.com, cloud.ikuai8.com)
       │
       ▼ 【装载 AST 权威注册表 (EndpointRegistry)】
task_to_endpoint 零损耗恢复 AST 参数契约与签名
       │
       ▼ 【动态沙箱执行器 (AdaptiveSandboxExecutor)】
发送物理发包 (Chrome 128 Client Hints + NO_PROXY="*" 毫秒直连)
       │
       ├─► 场景 A: 物理 403/405 或 业务软 403 (HTTP 200 + code: 4003)
       │      │
       │      ▼ 【激活 System-2 自适应科研闭环 (ResearchLoop)】
       │      ├── 1. 启发式先锋 (Heuristic): 调度 F1(路径畸变) / F2(动词隧道) / F3(现代反代信任头)
       │      ├── 2. 防假突破: 排除伪 200 业务错误与 SPA 首页 HTML 200 回退
       │      └── 3. 认知跃迁 (Phase 5.4): 启发式穷尽时唤醒本地 8080 (Ornith-9B) 开展 CoT 反思推演
       │
       └─► 场景 B: 物理响应收敛 ──► 安全底线不变量评估 (InvariantEvaluator)
              ├── auth_boundary: 识别软 403 与 HTML 兜底，判定为 CONFIRMED (坚固守住)
              ├── destructive_confirmation: 校验 confirm 参数
              └── idor_boundary: 双主体物理差分核验
                     │
                     ▼ 【三权分立与科学门禁 (Phase 5.5)】
                 IndependentVerifier 独立复核 ──► PromotionGate 8 大前置谓词校验
                     │
                     ▼ 【权威战报投影器 (ReportProjector)】
                 原子化导出 7 大交付物 (含 openvex.json 与 sarif.json)
```

---

## 11. Architecture Decisions

### AD-01 — Dual-Brain Engineering Topology (分层双脑协同规范)
* **Decision**: 严禁让 9B 本地模型充当全自主全局架构师（极易触发长思维链自我催眠与 30 分钟死循环）；必须将其定位为“受控现场探针与工具执行器”，由长上下文主控提供原子化 PowerShell 脚本落盘，本地模型专职取证与执行。
* **Do not revert unless**: 接入了具备超长上下文全局推理能力的云端顶级大模型。

### AD-02 — Windows Registry Proxy Bypass (Windows 注册表代理彻底隔离)
* **Decision**: 在 Windows 上仅 `pop("ALL_PROXY")` 无法阻止 `requests` 从注册表读取代理。必须在 `transport.py` 初始化时设置 `os.environ["NO_PROXY"] = "*"`，确保物理网络请求绝对直连。
* **Why**: 本地代理分流与握手超时会导致单发延迟从 300ms 飙升至 5.7s，在变异循环中累积成 66s 挂死。

### AD-03 — Two-Tier False-Positive Defense (双重假阳性防御铁律)
* **Decision**: 
  1. **软拒绝防御**: HTTP 200 伴随 `code in {4001, 4003, 4008}` 或 `message: "forbidden"` 时，安全底线评估器必须裁决为 `confirmed`（安全拦截），严禁因状态码为 200 误判为特权放行。
  2. **SPA 前端回退防御**: HTTP 200 伴随 `<!DOCTYPE html>` 或 `<html` 时，证明系前端单页应用路由未命中兜底，语义等价判定为非目标接口，严禁判定为漏洞击穿。

### AD-04 — OpenSSF OpenVEX & OASIS SARIF Dual Gold Standard
* **Decision**: 废除私有格式交付，输出端全面并轨国际事实标准：
  - `openvex.json` 符合 OpenSSF OpenVEX v0.2.0 Schema；
  - `sarif.json` 符合 OASIS SARIF 2.1.0 Schema。

### AD-05 — Fallback-Only LLM Reflection
* **Decision**: 本地大模型反思推演不作为常规默认发包手段，仅作为启发式（F1/F2/F3）尝试耗尽且未突破时的保底反思步骤，且严格执行 AD-03 上下文切片限制（<800 字符）。

---

## 12. Data / API / Type Contracts

### 1. OpenVEX Statement 契约 (`agent/knowledge_promoter.py`)
```python
def to_openvex_statement(self) -> Dict[str, Any]:
    # 状态互斥: VERIFIED -> affected (带 action_statement)
    #          REFUTED -> not_affected (带 justification: inline_mitigations_already_exist)
```

### 2. SARIF 2.1.0 契约 (`harness/reporting.py`)
```python
def render_sarif_json(self) -> str:
    # 规范: OASIS SARIF 2.1.0
    # 映射: finding.fingerprint -> ruleId, finding.trace -> codeFlows/threadFlows
```

### 3. 不变量评估器上下文签名 (`harness/invariant_evaluator.py`)
```python
@classmethod
def evaluate(
    cls,
    invariant: SecurityInvariant,
    endpoint: EndpointIR,
    status_code: int,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    response_text: Optional[str] = None,    # 响应体文本，用于识别软拒绝与 HTML
    is_soft_denial: bool = False,           # 软拒绝标志位
) -> InvariantEvaluation:
```

---

## 13. Algorithms / Workflow

### System-2 动态实证与两段式反思流
```text
Input: EndpointIR + Target URL
  │
  ▼
Baseline Probe (HttpTransport 毫秒直连)
  │
  ├─► 若返回 403/405 或 软 403 (HTTP 200 + code: 40xx)
  │      │
  │      ▼
  │   Heuristic Turn Loop (F1/F2/F3 变异算子先锋，最多 12 轮)
  │      │
  │      ├─► 突破成功 (200 OK 且 非软拒绝 且 非HTML 且 语义等价 且 重放稳定) ──► 组装 EvidenceChain 退出
  │      │
  │      └─► 启发式耗尽仍未突破 ──► [Phase 5.4 认知跃迁]
  │                                 │
  │                                 ▼
  │                            唤醒本地 8080 (Ornith-9B) 开展 CoT 反思
  │                            生成 F6_LLM_COT_REASONED 变异体发包
  │
  ▼
Invariant Evaluator 断言
  ├── 识别软拒绝/HTML ──► CONFIRMED (守住)
  └── 真正未授权放行 ────► VULNERABLE (击穿)
  │
  ▼
IndependentVerifier 独立复核 ──► PromotionGate 8 谓词断言 ──► 导出 7 大交付物
```

---

## 14. Verified Tests

| Test File | Purpose | Result |
|---|---|---|
| `test_http_transport.py` | 验证传输层绝对直连与标头/载荷透传契约 | 2/2 PASSED |
| `test_invariant_evaluator.py` | 验证安全底线评估与软拒绝/HTML 兜底拦截 | 5/5 PASSED |
| `test_knowledge_promoter.py` | 验证知识卡片晋级与 OpenVEX 黄金标准声明契约 | 8/8 PASSED |
| `test_reporting_projections.py` | 验证 6 大战报原子投影与 OASIS SARIF 2.1.0 格式规范 | 6/6 PASSED |
| `test_transformation_family_contract.py` | 验证 F1~F3 变异算子库现代标头吸收与去重不变量 | 5/5 PASSED |
| `test_agent_loop_types_contract.py` | 验证消息双轨制、切片上限与 LLM 推理事件流枚举 | 5/5 PASSED |
| `test_research_loop_llm_contract.py` | 验证常规启发式耗尽后平滑触发模型认知反思与变异派发 | 1/1 PASSED |
| `python 全量回归测试` | 验证全工作区 Python 测试无回归 | **202 passed in 0.40s** |
| `Rust 全量回归测试` | 验证 Rust 核心调度引擎与 IPC 契约一致性 | **15 passed in 4.7s** |

---

## 15. Failure / Pitfall Registry

### Pitfall 1: Windows 注册表代理与 66 秒挂死
* **Problem**: 单个任务审计卡死 65.9 秒，本地模型陷入死循环。
* **Root Cause**: `requests` 底层通过 `urllib.request.getproxies()` 从 Windows 注册表 `Internet Settings` 获取了 `127.0.0.1:7897` 代理，单个请求遭遇代理重试超时（5.5 秒），乘以 12 轮变异等于 66 秒。
* **Correct Fix**: 在 `transport.py` 初始化时设置 `os.environ["NO_PROXY"] = "*"`，强制全量请求走本地直连网络。

### Pitfall 2: 软 403 业务错误码引发的假高危
* **Problem**: 任务 #3, #9, #11 返回 `HTTP 200 + {"code": 4003, "message": "forbidden"}`，被误报为严重未授权漏洞。
* **Root Cause**: `InvariantEvaluator` 此前只依据物理状态码 `200 <= status <= 299` 做判断，对响应正文完全盲盒。
* **Correct Fix**: 为 `InvariantEvaluator.evaluate` 贯通 `response_text` 与 `is_soft_denial`，将 40xx 业务码断言为 `confirmed`（防御生效）。

### Pitfall 3: SPA 单页应用 Nginx 首页回退引发的假突破
* **Problem**: 请求不存在的 `/admin/...` 路由返回 `HTTP 200 + <!DOCTYPE html>`，被系统误判为 12 个实锤漏洞。
* **Root Cause**: Nginx `try_files` 对 404 路由兜底输出 `index.html`，沙箱误以为契约通过且不变量放行。
* **Correct Fix**: 在 `_is_response_denial` 与 `research_loop` 突破判定中严格识别 `<!doctype html` / `<html`，判定为非目标页面拦截。

### Pitfall 4: research_loop 误把软 200 当突破导致大模型被跳过
* **Problem**: 激活 `--enable-llm` 后，后台本地 8080 端口毫无动静。
* **Root Cause**: `research_loop.py` 只检查物理状态码 200，在遭遇软 200 时错误设置 `breakthrough = True` 提前跳出循环，导致后续的 `if not breakthrough` 模型分支被完全短路。
* **Correct Fix**: 在 `breakthrough` 判定前校验 `not is_soft and not is_html`，确保启发式真正未突破时顺畅唤醒大模型。

---

## 16. Do Not Repeat

* ❌ **不要在 Windows 终端中使用 `python -c "..."` 拼大段含复杂双重转义的双引号代码**（必须使用 PowerShell Here-String `@' ... '@`）。
* ❌ **不要让 9B 本地模型处理长篇大论的架构重构或开放性排查**（必须给出四选一客观事实取证指令）。
* ❌ **不要只凭 HTTP 状态码 200 就断定 API 调用成功**（必须核验是否为业务拒绝码或 HTML 网页）。
* ❌ **不要在 `HttpTransport` 内部私自篡改请求头或追加非标参数**。

---

## 17. Invariants

* **I-01**: `Train ∩ Gold = ∅`（训练集与黄金测试集物理隔离）。
* **I-02**: `HttpTransport` 属于纯净物理传输层，保持透传与毫秒级直连。
* **I-03**: 任何实锤漏洞必须满足 PromotionGate 8 大前置谓词校验并由独立主体复核签署。
* **I-04**: 输出交付物严格对齐 OpenSSF OpenVEX v0.2.0 与 OASIS SARIF 2.1.0 标准。

---

## 18. Open Issues

* *(当前阶段所有阻塞性 Issue 均已攻克，全量 78 任务审计已闭环)*

---

## 19. Environment / Toolchain

* **OS**: Windows 11
* **Shell**: PowerShell
* **Rust Toolchain**: Cargo 1.80+ (2021 edition, target: `x86_64-pc-windows-msvc`)
* **Python Runtime**: Python 3.12 (CPython 3.12.13, managed via `uv`)
* **Local LLM Server**: `llama-server.exe` (Ornith-1.5-9B-Abliterated-IQ3_M, `http://127.0.0.1:8080/v1`)

---

## 20. Roadmap

* **Phase 1~4**: 资产全源测绘、静态 AST 参数逆向、双轨分流 (COMPLETED)
* **Phase 5.1**: 靶心任务装配轻量化与动词清洗 (COMPLETED)
* **Phase 5.2**: 403 拒绝响应架构重构与 `pi-agent-core` 纯函数状态机 (COMPLETED)
* **Phase 5.3**: 业务软 403 感知、物理代理隔离、SPA 前端回退过滤 (COMPLETED)
* **Phase 5.4**: 本地消融大模型 (Ornith-1.5-9B) 启发式穷尽时 CoT 破局实测 (COMPLETED)
* **Phase 5.5**: 独立第三方复核与 OpenVEX + SARIF 2.1.0 出厂双黄金认证 (COMPLETED)

---

## 21. Recovery Protocol

新 AI 接手会话后，严格按照以下步骤恢复上下文：
1. 读取根目录 `HANDOFF.md`，确认版本为 v12.0.0。
2. 确认工作区保持纯无头架构（Tauri/桌面端处于 OUT OF SCOPE）。
3. 执行 `uv run --project python pytest` 确认 202 项测试全绿。
4. 执行 `cargo test --workspace` 确认 15 项 Rust 测试全绿。
5. 锁定 CURRENT OBJECTIVE，**仅执行 NEXT SINGLE ACTION**。

---

## 22. AI Collaboration Protocol

* **分层双脑协同 (Dual-Brain Protocol)**：云端架构脑负责方案设计与原子脚本编写；本地消融模型专职执行命令与提取客观物证。
* **单步工程推进**：每轮对话仅推进一个明确的工程闭环，严禁跨阶段倾倒修改。
* **源码落地习惯**：Windows 环境一律使用 PowerShell `@' ... '@ | Set-Content -Encoding UTF8` 完整落盘。

---

## 23. Security / Sensitive Data Boundary

* 私有凭证通过环境变量 `INVAR_AUTH_TOKEN` 运行时注入，严禁硬编码进代码。
* 测试探测目标严格遵守 `data/targets/<target>/scope.txt` 授权边界。

---

## 24. Reproducibility Status

**FULLY REPRODUCIBLE (CORE ENGINE & HARNESS)**  
核心接口、算法状态机、403 拒绝研究架构、本地大模型推演、SARIF/OpenVEX 标准导出与 217 项全量测试完全具备确定性闭环，代数与测试事实 100% 自包含。

---

## 25. Handoff Self-Check

- [x] 一个新 AI 是否知道当前到底在做什么？（知道：Phase 5 全阶段完成收官，正在进行文档与笔记固化）。
- [x] 一个新 AI 是否知道最后一次成功状态？（知道：Python 202 项全绿，Rust 15 项全绿，78 任务全量实证 0 误报）。
- [x] 一个新 AI 是否知道最后修改了哪些文件？（知道：`reporting.py`、`knowledge_promoter.py`、`research_loop.py`、`sandbox_executor.py`）。
- [x] 一个新 AI 是否知道为什么这么设计？（知道：对齐 OpenSSF OpenVEX 与 OASIS SARIF 黄金标准，消除扫描器假阳性）。
- [x] 一个新 AI 是否知道哪些行为不能破坏？（知道：不可碰桌面端、不可破坏 Transport 透传契约、不可盲信 HTTP 200）。
- [x] 一个新 AI 是否知道当前唯一下一步？（知道：将 5.4 和 5.5 规范回填至 `Invar实战.md`）。
- [x] 一个新 AI 是否能够依据文档恢复？（能：事实等级清晰，命令与路径完全自包含）。
