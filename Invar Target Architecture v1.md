# Invar Target Architecture v1

## 0. 文档定位

本文件定义 Invar 的目标工程架构、模块职责、运行轨道、平台适配边界及现有文件处置规则。

本版本的核心决策：

> **Invar 本体是通用型 AI 网络安全研究与验证武器库。**
>
> **Production 是默认运行轨道。**
>
> **Research 是研究级高级能力。**
>
> **Intelligence 是安全知识供给能力。**
>
> **Benchmark 是内部验证能力。**
>
> **Butian 是平台适配器，而不是 Invar 的核心业务定义。**

本版本遵循以下工程宪法：

```text
根因 > 补丁
抽象 > 特判
契约 > 约定
复用 > 重造
验证 > 猜测
系统最优 > 局部最优
```

---

# 1. 总体目标架构

```text
                                   INVAR
                     通用 AI 网络安全武器库
                                          │
             ┌────────────────────────────┼────────────────────────────┐
             │                            │                            │
             ▼                            ▼                            ▼
       Security Core              Runtime Tracks               Platform Adapters
             │                            │                            │
             │                ┌───────────┼───────────┐                │
             │                │           │           │                │
             │                ▼           ▼           ▼                ▼
             │          Production    Research   Intelligence        Butian
             │           默认生产轨     研究轨       情报轨           适配器
             │                │           │           │
             │                └───────────┼───────────┘
             │                            │
             ▼                            ▼
     Evidence / Finding / Verification   Knowledge
             │                            │
             └──────────────┬─────────────┘
                            ▼
                       Reporting
                            │
                            ▼
                       Submission
                            │
                            ▼
                        Benchmark
```

Benchmark 横向验证整个体系，不参与普通生产路径。

---

# 2. 一级职责边界

## 2.1 Security Core

职责：

```text
Scope
Asset Representation
Endpoint Model
HTTP Transport
Execution
Evidence
Semantic Evaluation
Security Invariant
Verification
Finding
Replay
Reporting Contract
```

Security Core 必须平台无关。

禁止出现：

```text
Butian 专用判断
平台奖励规则
平台页面字段
平台提交流程
单一平台 URL
```

---

## 2.2 Production Track

职责：

> 默认、日常、大规模、稳定的漏洞发现与验证。

```text
Asset
↓
AST
↓
System-1
↓
Triage
↓
Fast Validation
↓
Evidence
↓
Verification
↓
Finding
↓
Platform Adapter
```

Production 不要求所有任务进入 Research。

Production 可以升级到 Research。

---

## 2.3 Research Track

职责：

> 高复杂度、高价值、证据不足任务的深度研究。

保留：

```text
Hypothesis
Mutation
Adaptive Selection
Research Loop
LLM
Replay
Semantic Differential
Security Invariant
Independent Verification
Evidence Gate
```

Research Engine 不删除、不降级。

---

## 2.4 Intelligence Track

职责：

```text
安全资料
↓
知识提取
↓
知识标准化
↓
知识索引
↓
知识资产
↓
Production / Research
```

不得绕过证据系统直接产生 CONFIRMED Finding。

---

## 2.5 Benchmark

职责：

```text
Golden Set
Replay
Regression
Model Evaluation
Capability Evaluation
```

Benchmark 不参与普通生产运行。

---

# 3. 核心依赖方向

依赖方向固定为：

```text
Platform Adapter
        ↓
Reporting / Finding
        ↓
Evidence / Verification
        ↓
Security Core
```

而不是：

```text
Security Core
        ↓
Butian
```

因此：

> **核心依赖适配器接口；核心不得依赖某个具体平台。**

---

# 4. 现有目录目标归属

当前仓库目录已经包含：

```text
apps/
artifacts/
configs/
crates/
data/
docs/
models/
python/
runs/
scripts/
tools/
```

本版本不进行无理由的大规模目录重排。

---

# 5. `crates/core` 归属

目标职责：

> Rust 跨语言运行时、调度与稳定契约层。

当前：

```text
crates/core/src/lib.rs
crates/core/src/main.rs
crates/core/src/orchestrator.rs
```

## 5.1 `lib.rs`

状态：

```text
保留
```

职责：

```text
Rust Core Public Contract
```

禁止：

```text
增加 Butian 逻辑
增加具体漏洞规则
增加 Research 专属判断
```

---

## 5.2 `main.rs`

状态：

```text
保留
```

职责：

```text
Rust Core executable entry
```

当前只是轻量初始化入口，不应强行承担大量业务逻辑。

---

## 5.3 `orchestrator.rs`

状态：

```text
保留
逐步泛化
```

目标：

```text
Cross-language orchestration
Task contract
Process boundary
Runtime dispatch
```

当前代码已经定义 `ResearchTask` 等跨语言任务契约，因此不能简单删除或重写成平台业务层。

未来应支持：

```text
profile = production
profile = research
profile = intelligence
profile = benchmark
```

而不是：

```text
profile = butian
```

---

# 6. `python/packages/core/src/harness` 定义

这是 Invar 最重要的**共享安全内核之一**。

目标：

```text
harness/
├── execution
├── evidence
├── verification
├── finding
├── coverage
├── semantic
└── transport
```

原则：

> Production、Research、Intelligence 最终都必须回到共享 Harness。

当前 Harness 已集中暴露 `ResearchRun`、`RunProfile`、`CoverageLedger`、`FindingRecord`、`VerificationGate`、`Reporting` 等能力，符合共享内核方向。

---

# 7. Harness 文件逐项归属

| 当前文件                                                     | 目标层                         | v1 处置                 |
| -------------------------------------------------------- | --------------------------- | --------------------- |
| `harness/__init__.py`                                    | Core API                    | 保留                    |
| `adaptive_selector.py`                                   | Research/Core Strategy      | 保留                    |
| `ast_worker.py`                                          | Shared Core                 | 保留                    |
| `audit_checkpoint.py`                                    | Shared Runtime              | 保留                    |
| `candidate_models.py`                                    | Shared Core                 | 保留                    |
| `config.py`                                              | Shared Runtime              | 保留并逐步承载 Track Profile |
| `coverage_ledger.py`                                     | Shared Verification         | 保留                    |
| `denial_models.py`                                       | Shared Security Logic       | 保留                    |
| `evidence_models.py`                                     | Shared Evidence             | 保留                    |
| `evidence.py`                                            | Shared Evidence             | 保留                    |
| `execution_trace.py`                                     | Shared Evidence/Trace       | 保留                    |
| `execution_trace.py.bak.execution_trace_20260923_162844` | 历史文件                        | 冻结，禁止继续引用             |
| `exporter.py`                                            | Shared Export               | 保留                    |
| `extractor.py`                                           | Shared Extraction           | 保留                    |
| `feedback.py`                                            | Research/Feedback           | 保留                    |
| `finding_models.py`                                      | Shared Finding              | 保留                    |
| `idor_compare.py`                                        | Security Operator           | 保留                    |
| `invariant_evaluator.py`                                 | Shared Security             | 保留                    |
| `method_tamper.py`                                       | Security Operator           | 保留                    |
| `models.py`                                              | Shared Data Model           | 保留                    |
| `multi_run.py`                                           | Shared Runtime              | 保留                    |
| `mutation_policy.py`                                     | Research Strategy           | 保留                    |
| `reporting.py`                                           | Shared Reporting            | 保留并平台无关化              |
| `research_adapter.py`                                    | Research Adapter            | 保留                    |
| `research_evidence.py`                                   | Research → Evidence Bridge  | 保留                    |
| `research_models.py`                                     | Research Contract           | 保留                    |
| `research_worker.py`                                     | Research Runtime            | 保留                    |
| `run_models.py`                                          | Shared Runtime              | 保留并扩展 Track           |
| `sandbox_executor.py`                                    | Shared Dynamic Execution    | 保留                    |
| `semantic_models.py`                                     | Shared Verification         | 保留                    |
| `transformation_models.py`                               | Research/Security Operators | 保留                    |
| `transport.py`                                           | Shared Transport            | 保留且作为强边界              |
| `triage_dispatcher.py`                                   | Runtime Dispatch            | 保留，未来扩展 Track         |
| `verification_gate.py`                                   | Shared Final Gate           | 保留，禁止轨道绕过             |

---

# 8. `transport.py` 特别保护

这是核心物理边界。

目标：

```text
HttpTransport
=
确定性网络传输
```

禁止：

```text
Production 专用参数
Research 专用参数
Butian 专用参数
隐式代理
隐式 payload
平台策略
```

已有工程规则也明确要求保持 `HttpTransport` 的确定性透传契约。

---

# 9. `verification_gate.py` 特别保护

它是最终证据门。

任何轨道：

```text
Production
Research
Intelligence
```

都不得绕过。

必须保持：

```text
Scope
Transport
Semantic Equivalence
Security Invariant
Replay
Independent Verification
```

的统一验证体系。

现有 `EvidenceGate` 已承担这一职责，因此 v1 不重新设计第二套验证门。

---

# 10. `finding_models.py` 特别保护

这是全系统统一结果契约。

所有轨道最终都进入：

```text
FindingRecord
```

不得创建：

```text
ProductionFinding
ResearchFinding
ButianFinding
```

三套并行模型。

---

# 11. `reporting.py` 目标职责

职责：

```text
Finding
↓
标准化报告投影
```

允许：

```text
SARIF
OpenVEX
Generic Markdown
JSON
```

禁止直接承担：

```text
Butian 页面业务
平台账号逻辑
平台字段特殊判断
```

当前报告模块已有 SARIF 标准投影能力，应作为通用导出能力继续保留。

---

# 12. `agent/` 定义

`agent/` 是 Invar 的**认知与研究能力层**。

当前目录：

```text
agent/
├── coverage_critic.py
├── hunter.py
├── hypothesis_engine.py
├── knowledge_promoter.py
├── loop_types.py
├── model_provider.py
├── mutator.py
├── research_agent.py
├── research_loop.py
├── risk_engine.py
└── wave_orchestrator.py
```

总体：

```text
保留
```

不应将 Research 能力删除以“简化 Production”。

---

# 13. Agent 文件逐项归属

| 当前文件                    | 目标层                             | v1 处置    |
| ----------------------- | ------------------------------- | -------- |
| `coverage_critic.py`    | Research                        | 保留       |
| `hunter.py`             | Research / Candidate Generation | 保留       |
| `hypothesis_engine.py`  | Research                        | 保留       |
| `knowledge_promoter.py` | Intelligence ↔ Research         | 保留，未来拆职责 |
| `loop_types.py`         | Research Contract               | 保留       |
| `model_provider.py`     | Model Runtime                   | 保留       |
| `mutator.py`            | Research                        | 保留       |
| `research_agent.py`     | Research                        | 保留       |
| `research_loop.py`      | Research                        | 保留       |
| `risk_engine.py`        | Shared Strategy                 | 保留       |
| `wave_orchestrator.py`  | Research                        | 保留       |

---

# 14. `model_provider.py`

目标：

> 模型提供者抽象。

不得让：

```text
Qwen
27B
某一 LLM 服务
```

成为系统架构硬编码。

必须保持：

```text
Model Provider Interface
        ↓
Local Model
        ↓
Other Provider
```

Research 使用模型，不代表 Production 必须依赖模型。

---

# 15. `research_loop.py`

定义为：

> Research Track 核心引擎。

不得删除。

不得迁入 Production 专属目录。

不得为了 Production 的稳定性削弱 Research 的研究能力。

Production 只能：

```text
调用
升级
委托
```

而不是：

```text
复制
改写
分叉
```

---

# 16. `knowledge_promoter.py`

当前职责已经连接 Research、Finding、OpenVEX 与知识卡片，因此属于：

```text
Research
↔
Intelligence
```

桥接模块。

v1：

```text
保留
```

后续可把：

```text
Knowledge Card
OpenVEX Projection
```

拆成不同职责。

当前不做拆分。

---

# 17. 资产发现脚本归属

当前：

```text
python/scripts/data/asset/
```

包括：

```text
download_javascript.py
ingest_crtsh.py
ingest_httpx.py
ingest_katana.py
ingest_subdomains.py
materialize_static_get.py
normalize_katana.py
probe_urls.py
scan_secrets.py
triage_dual_track_comparator.py
```

统一定义为：

> Asset Discovery / Surface Intelligence Layer

它们不是 Butian 专属能力。

---

# 18. Asset 文件处置

| 文件                                | 目标层                    | 处置 |
| --------------------------------- | ---------------------- | -- |
| `download_javascript.py`          | Asset Discovery        | 保留 |
| `ingest_crtsh.py`                 | Asset Discovery        | 保留 |
| `ingest_httpx.py`                 | Asset Discovery        | 保留 |
| `ingest_katana.py`                | Asset Discovery        | 保留 |
| `ingest_subdomains.py`            | Asset Discovery        | 保留 |
| `materialize_static_get.py`       | Asset Discovery        | 保留 |
| `normalize_katana.py`             | Asset Normalization    | 保留 |
| `probe_urls.py`                   | Asset/HTTP Observation | 保留 |
| `scan_secrets.py`                 | Security Discovery     | 保留 |
| `triage_dual_track_comparator.py` | Candidate/Triage       | 保留 |

---

# 19. Pipeline 文件

当前：

```text
python/scripts/data/pipeline/
```

包括：

```text
build_targets.py
fetch_chunk.py
predict_triage_onnx.py
scan_pipeline.py
```

统一定义：

> Discovery → AST → Model-assisted Triage Pipeline

---

# 20. `predict_triage_onnx.py`

明确归属：

```text
System-1
```

目标：

```text
Fast Cognitive Triage
```

Production 可以调用。

Research 也可以调用。

但：

> System-1 不是最终漏洞裁决器。

---

# 21. `scan_pipeline.py`

归属：

```text
AST / Endpoint Contract Extraction
```

属于共享发现层。

不得改成：

```text
Butian scan pipeline
```

---

# 22. `python/scripts/` 现有入口

当前：

```text
python/scripts/
├── assemble_triage_tasks.py
├── diag_p0.py
├── run_targeted_audit.py
├── scan_pipeline.py
└── verify_p0.py
```

v1 不立即移动这些文件。

原因：

```text
已有调用路径
已有测试
已有文档
已有运行经验
```

先建立 Track Contract。

待契约稳定后，再决定是否物理重组。

---

# 23. `run_targeted_audit.py`

目标定义：

```text
Research Runtime Entry
```

不是 Production 唯一入口。

当前保留原路径：

```text
python/scripts/run_targeted_audit.py
```

后续可以增加：

```text
python/scripts/production/
python/scripts/research/
```

但 v1 阶段：

> **禁止为了目录漂亮立即移动。**

---

# 24. `assemble_triage_tasks.py`

目标：

```text
Task Assembly / Dispatch
```

升级方向：

```text
Production Task
Research Task
```

而不是单一：

```text
Research Task
```

---

# 25. `python/tests`

这是统一契约测试体系。

当前已有大量：

```text
Transport
Evidence
Finding
Research
Sandbox
Semantic
Triage
Reporting
```

测试不得按轨道复制为：

```text
test_production_xxx.py
test_research_xxx.py
```

除非测试的行为契约本身确实不同。

目标：

```text
Shared Contract Tests
+
Track-specific Policy Tests
```

---

# 26. 测试目录的目标结构

当前：

```text
python/tests/
python/packages/core/tests/
```

v1：

```text
保留
```

暂不大迁移。

未来可逐步形成：

```text
tests/
├── core/
├── tracks/
│   ├── production/
│   ├── research/
│   ├── intelligence/
│   └── benchmark/
└── adapters/
    └── butian/
```

但这是后续整理动作。

---

# 27. `configs/` 新目标

当前已经存在：

```text
configs/base/
configs/examples/
configs/profiles/
configs/registry/
configs/schemas/
```

这与 Track Profile 架构天然兼容。

目标：

```text
configs/
├── base/
├── examples/
├── profiles/
│   ├── production.toml
│   ├── research.toml
│   ├── intelligence.toml
│   └── benchmark.toml
├── registry/
└── schemas/
```

---

# 28. `configs/base/project.toml`

当前：

```toml
[project]
name = "Invar"
profile = "research"
```

目标必须改成：

```toml
[project]
name = "Invar"
profile = "production"
```

这是 v1 最明确的配置语义修正。

当前配置确实把默认 profile 指向了 `research`，与本架构目标冲突。

---

# 29. `configs/profiles/research.toml`

状态：

```text
保留
```

职责：

```text
Research runtime policy
```

不降级。

当前已有：

```toml
[runtime]
backend = "research"
execution = "local"
reproducible = true
```

---

# 30. 新增 Profile

必须新增：

```text
configs/profiles/production.toml
configs/profiles/intelligence.toml
configs/profiles/benchmark.toml
```

其中：

```text
production
```

是默认。

---

# 31. `configs/registry/backends.toml`

当前：

```text
default
research
```

目标：

```text
default
production
research
intelligence
benchmark
```

但：

> backend registry 只描述后端实现，不承载漏洞业务规则。

当前 registry 本身已经是声明式设计，因此继续沿用这一方向。

---

# 32. `config.schema.json`

状态：

```text
保留
```

目标：

> 将 Track/Profile 成为显式数据契约。

当前 schema 允许扩展属性，因此 v1 可以做最小收紧，但必须先审查现有消费者再修改。

---

# 33. Butian 平台适配层

新增：

```text
python/packages/core/src/adapters/
└── butian/
```

目标：

```text
butian/
├── __init__.py
├── models.py
├── validator.py
├── projector.py
├── evidence_checklist.py
└── report_template.py
```

---

# 34. Butian Adapter 的职责

仅负责：

```text
FindingRecord
↓
ButianSubmissionModel
↓
平台字段投影
↓
提交前校验
↓
报告模板
↓
证据完整性检查
```

依据你提供的 Butian 指南：

```text
厂商名称
域名/IP
漏洞类别
漏洞标题
漏洞 URL
漏洞类型
漏洞等级
漏洞权重
简要描述
详细细节
附件
修复方案
```

属于平台提交字段。

四类必要证据：

```text
目标地址
厂商归属
系统首页
危害证明
```

属于平台适配的证据检查。

---

# 35. Butian 规则绝对不能进入 Core

例如：

```text
“简要描述不能出现 URL”
```

属于：

```text
Butian Adapter Rule
```

而不是：

```text
Finding Core Rule
```

同理：

```text
权重
活动
匿名提交
平台字段命名
```

全部属于 Adapter。

---

# 36. Butian 文档归属

现有：

```text
docs/ai/补天漏洞响应平台（Butian）标准化漏洞提交流水线与规范指南.md
docs/补天_漏洞报告_详细细节模板.md
```

定义为：

```text
Platform Adapter Documentation
```

保留。

不进入 Security Core。

---

# 37. `docs/ai/Invar实战.md`

目标：

```text
Invar Operational Runbook
```

保留。

但后续必须逐步更新为：

```text
Production
Research
Intelligence
```

三轨说明。

当前文档仍以：

```text
资产
→ AST
→ System-1
→ 双轨
→ System-2
```

为主链。

---

# 38. 历史 / 研究文档

以下：

```text
docs/1_启动_27B纯文本多Token满速版.txt
docs/理论基础研究.txt
docs/为 System-2 搭建轻量级、标准化的三级大模型适配层-HANDOFF.md
docs/我当前的启发理解.txt
```

v1：

```text
保留
```

但分类为：

```text
Research Knowledge / Historical Design
```

不得成为 Production 的运行契约。

---

# 39. `models/`

当前：

```text
models/invar-intent-0.6b-v1/
```

归属：

```text
Model Assets
```

保留。

0.6B 是：

```text
System-1
```

能力资产。

未来 Research 模型也继续存放于统一 Model Asset 边界。

---

# 40. `apps/desktop`

当前：

```text
apps/desktop/
```

目标：

```text
OUT OF SCOPE / FROZEN
```

原因：

当前工程事实已经明确桌面端处于 Out of Scope。

v1：

```text
不删除
不改造
不参与 Production
不参与 Research
```

以后若重新启用，再单独设计 UI Layer。

---

# 41. `artifacts/`

定义为：

```text
Runtime Output
```

禁止：

```text
源代码
临时调试代码
平台适配源码
```

进入 artifacts。

---

# 42. `runs/`

定义为：

```text
Canonical Runtime State / Execution Records
```

保留。

未来：

```text
runs/
├── production/
├── research/
├── intelligence/
└── benchmark/
```

可以建立逻辑划分，但当前不要立即移动历史数据。

---

# 43. `data/targets/`

定义为：

```text
Target-scoped Input / Evidence
```

当前：

```text
data/targets/ikuai8.com/
```

保留。

授权边界：

```text
scope.txt
```

必须继续成为运行前置约束。

当前 `ResearchScope` 本身也已经把授权边界建模成显式契约。

---

# 44. `scripts/audit/`

定义为：

```text
Benchmark / Audit / Evaluation Tooling
```

当前包括：

```text
generate_gold_set_v1.py
evaluate_gold_set_v1.py
evaluate_gold_set_v4.py
evaluate_gold_set_pro.py
export_gold_replay_buffer.py
auto_annotate_gold_set_by_teacher.py
lint_blind_cards.py
lint_gold_set_blindness.py
contract_checker.py
project_inventory.py
```

全部：

```text
保留
```

定位为：

```text
Benchmark / Engineering Audit
```

---

# 45. 顶层启动脚本

当前：

```text
0_Ornith-1.5-9B-Abliterated-IQ3_M.ps1
1_启动_27B纯文本多Token满速版.ps1
```

v1：

```text
保留
```

但标记：

```text
Research / Local Model Operations
```

不得成为 Production 默认入口。

---

# 46. 顶层工程元文件

以下保持原位：

```text
AGENTS.md
HANDOFF.md
README.md
Cargo.toml
package.json
pnpm-workspace.yaml
pytest.ini
.gitignore
.gitattributes
.editorconfig
```

职责：

```text
工程入口
依赖
测试
协作
版本控制
```

禁止引入平台专属业务规则。

---

# 47. `HANDOFF.md` 的目标角色

`HANDOFF.md`：

```text
工程状态交接文档
```

不是：

```text
永恒架构真相
```

以后必须明确区分：

```text
Architecture Contract
Current State
Historical State
Next Action
```

避免历史运行结果覆盖真实当前状态。

---

# 48. Track Contract

统一增加：

```text
RunTrack
```

候选类型：

```text
PRODUCTION
RESEARCH
INTELLIGENCE
BENCHMARK
```

它与：

```text
RunStatus
```

完全分离。

---

# 49. RunTrack ≠ RunStatus

例如：

```text
track = PRODUCTION
status = BLOCKED
```

意味着：

> Production 运行遇到证据或执行阻塞。

不是：

```text
ProductionBlocked
```

同理：

```text
track = RESEARCH
status = COMPLETED
```

是正常状态组合。

---

# 50. 自动升级契约

Production：

```text
Production
↓
Evidence Gap
↓
Escalation Policy
↓
Research
```

必须记录：

```text
source_track
target_track
reason
trigger
timestamp
run_id
task_id
```

不得静默切换。

---

# 51. LLM 失败隔离

固定：

```text
LLM Failure
↓
事实记录
↓
Recovery / Retry
↓
Deterministic Resolver
↓
Research / Needs Validation
```

禁止：

```text
LLM Failure
↓
假装完成
```

也禁止：

```text
LLM Failure
↓
确认安全
```

这是整个 Invar 的真实性原则。

---

# 52. 当前 27 个 BLOCKED 对架构的意义

当前问题不定义为：

```text
Research 不应该存在
```

而定义为：

```text
Research 失败不应阻塞整个 Production
```

因此：

```text
失败隔离
+
证据持久化
+
恢复队列
+
自动升级
```

属于 Architecture v1 的核心要求。

---

# 53. 当前文件处置总表

## A. 核心保留

```text
crates/core/*
python/packages/core/src/harness/*
python/packages/core/src/agent/*
python/scripts/data/asset/*
python/scripts/data/pipeline/*
python/tests/*
```

---

## B. 研究能力保留

```text
research_loop.py
research_agent.py
hypothesis_engine.py
mutator.py
coverage_critic.py
adaptive_selector.py
research_worker.py
research_adapter.py
research_models.py
research_evidence.py
model_provider.py
wave_orchestrator.py
```

全部保留。

---

## C. 平台文档保留，但与 Core 分离

```text
docs/ai/补天漏洞响应平台（Butian）标准化漏洞提交流水线与规范指南.md
docs/补天_漏洞报告_详细细节模板.md
```

---

## D. 桌面端冻结

```text
apps/desktop/*
```

---

## E. 历史备份冻结

```text
execution_trace.py.bak.execution_trace_20260923_162844
```

不得导入。

不得继续修改。

不得在没有测试与引用清查前直接删除。

---

## F. Gold / Benchmark 保留

```text
scripts/audit/*
```

---

# 54. v1 新增内容

严格限定新增为：

```text
configs/profiles/production.toml
configs/profiles/intelligence.toml
configs/profiles/benchmark.toml
```

以及：

```text
python/packages/core/src/adapters/
└── butian/
```

以及必要的 Track Contract 定义。

除此之外：

> **v1 不允许为了架构“漂亮”大量新增目录。**

---

# 55. v1 暂不做的事情

禁止在本阶段同时做：

```text
大规模文件移动
大规模 package 重命名
删除 Research Engine
删除 Desktop
重写 Rust Core
重写全部 Harness
复制 Production / Research 两套核心
重写所有测试
重建 Gold Set
重做模型
```

---

# 56. 目录目标形态

最终目标：

```text
C:\dev\Invar
│
├── crates/
│   └── core/
│
├── python/
│   ├── packages/
│   │   └── core/
│   │       └── src/
│   │           ├── harness/          # Shared Security Core
│   │           ├── agent/            # Research / Cognitive Engine
│   │           └── adapters/
│   │               └── butian/       # Platform Adapter
│   │
│   ├── scripts/
│   │   ├── data/
│   │   │   ├── asset/
│   │   │   └── pipeline/
│   │   └── ...
│   │
│   └── tests/
│
├── configs/
│   ├── base/
│   ├── profiles/
│   │   ├── production.toml
│   │   ├── research.toml
│   │   ├── intelligence.toml
│   │   └── benchmark.toml
│   ├── registry/
│   └── schemas/
│
├── data/
│   └── targets/
│
├── models/
│
├── runs/
│
├── artifacts/
│
├── scripts/
│   └── audit/
│
├── docs/
│
└── apps/
    └── desktop/                     # Frozen / Out of Scope
```

---

# 57. 最终职责关系

```text
                  ┌───────────────────┐
                  │   Security Core   │
                  └─────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
         Production      Research    Intelligence
              │             │             │
              └─────────────┼─────────────┘
                            │
                            ▼
                     Evidence / Finding
                            │
                            ▼
                      Verification
                            │
                            ▼
                        Reporting
                            │
                            ▼
                     Platform Adapter
                            │
                            ▼
                          Butian
```

---

# 58. 最终架构原则

Invar 不做：

```text
Butian Scanner
```

Invar 做：

```text
AI Security Weapon Core
```

Butian 做：

```text
Submission Adapter
```

Production 做：

```text
Default Operating Track
```

Research 做：

```text
Advanced Research Engine
```

Intelligence 做：

```text
Knowledge Supply
```

Benchmark 做：

```text
Engineering Validation
```

---

# 59. v1 的唯一迁移策略

不要一次大改。

必须：

```text
Step 1
Track Contract

↓
Step 2
Production Profile

↓
Step 3
Default = Production

↓
Step 4
Production → Research Escalation

↓
Step 5
Butian Adapter

↓
Step 6
Production Submission Flow

↓
Step 7
Intelligence Track

↓
Step 8
Benchmark Consolidation
```

每一步：

```text
修改
→ 测试
→ 用户执行
→ 获取事实
→ 下一步
```

严格遵循单步工程协作。

---

# 60. v1 的绝对禁止事项

## 禁止改变

```text
Evidence Gate
Finding Schema
Transport Contract
Scope Contract
Security Invariants
Research Engine 核心语义
```

除非出现经过测试证明的契约问题。

## 禁止创建

```text
production_core/
research_core/
butian_core/
```

三套平行核心。

## 禁止建立

```text
ProductionFinding
ResearchFinding
ButianFinding
```

平行结果模型。

## 禁止出现

```text
if platform == "butian"
```

式的核心安全逻辑。

## 禁止删除

```text
Research Engine
0.6B Model
Gold / Benchmark
```

仅仅因为 Production 是默认模式。

---

# 61. 最终工程决策

### 项目数量

```text
当前：1 个 Invar
```

### 核心数量

```text
1 个 Security Core
```

### 运行轨道

```text
4 个：
Production
Research
Intelligence
Benchmark
```

### 平台适配器

```text
1 个起步：
Butian
```

### 默认模式

```text
Production
```

### 深度模式

```text
Research
```

### 知识模式

```text
Intelligence
```

### 验证模式

```text
Benchmark
```

---

# 62. 最终定义

> **Invar = 通用安全武器库**
>
> **Production = 日常作战**
>
> **Research = 深度武器**
>
> **Intelligence = 情报与知识供给**
>
> **Benchmark = 内部靶场**
>
> **Butian = 第一个交付渠道**

最终目标：

> **默认简单，遇难升级；能力集中，职责分轨；证据统一，平台解耦。**
