# Invar AI 可复现工程规格书

**版本**：2.0 (全五层认知大合流与双引擎 IPC 落地版)  
**整理日期**：2026-09-15  
**工程对象**：Invar Rust + Python 双引擎智能安全研究系统  
**规格定位**：可迁移、可复用、可测试、可审计的 AI 工程复现规范  
**适用范围**：复杂 AI 工程、Agent、研究自动化、分析引擎、推理/执行引擎、桌面应用与安全研究工具链

---

## 0. 规格书定位

本规格书不是项目 README，也不是一次性重构计划。

它的目标是把 Invar 演进中已经被真实代码、测试、编译器反馈和项目文档验证过的技术，整理成一个新 AI 会话可以复现、其他项目可以迁移的工业级工程规格。

核心原则：

```text
有依据才实现
有契约才扩展
有测试才交付
有证据才晋级
```

标记规范：

| 标记 | 含义 |
|---|---|
| [FACT] | 当前源码、测试、编译器或项目档案直接支持的事实 |
| [DERIVED] | 从多个事实归纳出的可复用架构原则 |
| [RECOMMENDED] | 为复现工程而给出的规范化建议 |
| [SECURITY] | 为安全研究场景建立的安全边界与沙箱红线 |

---

# 1. 工程目标与核心哲学

## 1.1 总目标

将历史脚本式、强耦合的安全研究代码演进为五层分立的现代化智能体系统：

```text
确定性静态提炼 (AST)
    ↓
研究模型与强类型契约 (Contracts)
    ↓
业务策略与安全不变量 (Skill & Invariants)
    ↓
双引擎流式管道与可替换执行器 (Batch IPC & Executor)
    ↓
证据轨迹与单调审计 (Evidence Trail)
    ↓
假说验证与知识晋级门禁 (Hypothesis & Knowledge Gate)
    ↓
指导下一轮自主研究任务
```

系统必须同时满足：
- **可复现（Reproducible）**：相同输入与环境下，工具链行为完全确定。
- **可测试（Testable）**：全链路采用 TDD 驱动，红灯先行，绿灯守门。
- **可追溯（Traceable）**：每一项结论均绑定不可篡改的报文证据快照。
- **可替换（Pluggable）**：执行器支持内存 Fake 与真实系统进程无缝热拔插。
- **可扩展（Extensible）**：不变量与假说规则高度正交，按需扩展。
- **可审计（Auditable）**：Rust 顶层全局战报量化呈现任务健康度与漏洞捕获率。

## 1.2 通用工程最高标准

所有核心模块严格符合：
> **高内聚、低耦合、高鲁棒性、热拔插。**

- **高内聚**：单模块承担清晰、完整、可验证的职责（如 `InvariantEvaluator` 专精安全断言，`HypothesisEngine` 专精因果假说推演）。
- **低耦合**：模块之间依赖稳定强类型接口，严禁侵入内部私有实现。
- **高鲁棒性**：异常输入、格式畸变、外部进程崩溃时，系统严格执行防御式收敛（Zero-Panic Contract）。
- **热拔插**：替换执行器或升级变异规则时，主控与上层协议零修改。

## 1.3 零特判、纯泛化

禁止：
- `if test_case_001`
- 硬编码特定业务 ID、真实 URL、Token、密码字典
- 单一测试样本特化分支

---

# 2. 架构母模型：五层认知分权体系

```text
  ┌─────────────────────────────────────────────────────────────┐
  │  Level 5: Agent 认知规划层                                   │
  │  • 目标理解、因果假说生成 (HypothesisEngine)                │
  │  • 假说生命周期状态机: PROPOSED -> VERIFIED / REFUTED        │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
  ┌──────────────────────────────▼─────────────────────────────┐
  │  Level 4: Skill 业务策略与安全不变量层                       │
  │  • 确定性安全断言引擎 (InvariantEvaluator)                  │
  │  • 破坏性确认防护、特权认证边界检验                         │
  │  • 合成全局决断: ResearchDecision (vulnerable / confirmed)   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
  ┌──────────────────────────────▼─────────────────────────────┐
  │  Level 3: Harness 确定性脚手架与 IPC 管道                   │
  │  • 静态语法树解析与去重 (ast_worker / Tree-sitter)           │
  │  • 单进程多态批量管道 (research_worker / 40x 极速吞吐)       │
  │  • 自适应自愈闭环变异 (AdaptiveSandboxExecutor)             │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
  ┌──────────────────────────────▼─────────────────────────────┐
  │  Level 2: Evidence 证据链留痕                               │
  │  • 连续单调编号 ProbeAttempt 报文快照                       │
  │  • 证据异常与漏洞标记 (is_anomaly, VULNERABILITY_FOUND)     │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
  ┌──────────────────────────────▼─────────────────────────────┐
  │  Level 1: Knowledge 知识晋级提纯层                           │
  │  • 严格科学晋级门禁 (Promotion Gate: 拒绝未证实推测)         │
  │  • 知识实体 KnowledgeCard: 包含 claim, severity, remediation│
  └─────────────────────────────────────────────────────────────┘
```

---

# 3. Rust + Python 双引擎职责模型

## 3.1 总体边界 [FACT]

```text
Rust Brain (系统级主脑):
  • 系统级总控编排 (ResearchOrchestrator)
  • 操作系统进程生命周期托管与资源无损释放 (RAII)
  • 匿名管道 IPC 通道构建 (ProcessResearchExecutor, ProcessAstExtractor)
  • 强类型状态机与 Serde 别名防腐校验 (serde alias = "case_id")
  • 全局战报战略度量规约 (AuditReport: total, vulnerable_tasks)
  • Tauri 跨平台桌面端原生宿主集成

Python Specialist Engine (专业研究引擎):
  • Tree-sitter JavaScript AST 深度逆向分析与参数剥离
  • 基于后端报错反馈的自适应载荷变异 (MutationPolicy)
  • 业务安全不变量逻辑评估 (InvariantEvaluator)
  • 科研假说先验推演与决算 (HypothesisEngine)
  • 经验证安全知识卡片提纯 (KnowledgePromoter)
```

## 3.2 为什么不是全部 Python 也不是全部 Rust [DERIVED]

- **不用纯 Python 当总控**：彻底规避 Python 的 GIL 并发死锁、GC 内存泄漏、未捕获异常崩溃闪退、Windows 命令行截断以及缺乏强类型约束导致的“数据腐烂”。
- **不用纯 Rust 重写所有算法**：避免在借用检查器与复杂动态语法树解析中耗尽心智，最大限度复用 Python 成熟的安全与 AI 生态。

---

# 4. 项目目录作为工程类型系统 [FACT]

```text
C:\dev\Invar
├── c\                          # 认知中枢、规格书、交接文档 (HANDOFF)
├── data\                       # 只读数据集与测试资产 (严禁硬编码攻击载荷)
├── models\                     # 本地 AI 大模型权重金库 (GGUF, Safetensors)
├── tmp\                        # 临时实验与审计战报输出
├── src\                        # 前端表现层 (Vue3 / TypeScript / Tailwind)
├── src-tauri\
│   ├── crates\                 # Rust 核心引擎
│   │   ├── src\                # 生产模块 (lib.rs, main.rs, orchestrator.rs)
│   │   └── tests\              # 物理隔离的集成契约测试 (*_test.rs)
│   └── python\                 # Python 核心服务 (uv 管理)
│       ├── src\
│       │   ├── agent\          # 认知层 (hypothesis_engine, risk_engine, knowledge_promoter)
│       │   └── harness\        # 确定性工具与沙箱 (ast_worker, research_worker, evaluator...)
│       └── tests\              # Python 单元与回归测试集 (test_*.py)
├── scripts\                    # 流水线与离线审计工具
└── tests\                      # 全局端到端 E2E 验收测试
```

---

# 5. 跨语言强类型契约模型与 IPC 规范

## 5.1 Rust 核心领域模型 [FACT]

```rust
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResearchTask {
    #[serde(alias = "case_id")]
    pub task_id: String,
    pub method: String,
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResearchDecision {
    pub status: String,
    pub rationale: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResearchResult {
    #[serde(alias = "case_id")]
    pub task_id: String,
    pub status: String,
    pub attempts: u32,
    pub decision: Option<ResearchDecision>,
    pub evidence_history_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AuditReport {
    pub total_tasks: usize,
    pub completed_tasks: usize,
    pub inconclusive_tasks: usize,
    pub failed_tasks: usize,
    pub vulnerable_tasks: usize,
    pub total_attempts: u32,
    pub results: Vec<ResearchResult>,
}
```

## 5.2 匿名管道批量 IPC（Single-Invocation Batch IPC）[FACT]

为消除 Windows 进程冷启动开销，Rust 执行器特征采用默认批处理方法模式：

```rust
pub trait ResearchExecutor {
    fn execute(&self, task: &ResearchTask) -> ResearchResult;

    // 默认遍历回退实现，允许重型执行器特化重写
    fn execute_batch(&self, tasks: &[ResearchTask]) -> Vec<ResearchResult> {
        tasks.iter().map(|task| self.execute(task)).collect()
    }
}
```

- **单进程通信**：`ProcessResearchExecutor::execute_batch` 一次性将 `&[ResearchTask]` 序列化为 JSON 数组 `[ {...}, {...} ]`，灌入 `child.stdin`。
- **多态监听**：Python `research_worker.py` 自动识别 `list` 输入，调用 `ResearchTaskAdapter.execute_batch`，一次性写回结果数组 `[ {...}, {...} ]`。
- **性能飞跃**：50 个端点由原先的 50 次子进程启动（~50 秒）骤降为 1 次启动（~1.2 秒），吞吐量提升 40x 以上。

---

# 6. Python 认知与推理体系核心模块

## 6.1 自主假设推演引擎 (`agent.hypothesis_engine`) [FACT]

```python
@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str
    rationale: str = ""
    status: str = "PROPOSED"      # PROPOSED, VERIFIED, REFUTED, INCONCLUSIVE
    evidence_notes: str = ""
```

推演规则：
1. `extracted_params` 命中 `id` / `user_id` / `order_id` → 生成 `H-IDOR-1`（越权访问假说）。
2. `tags` 或 `path` 命中 `admin` / `sensitive-route` → 生成 `H-AUTH-1`（特权未授权假说）。
3. `method == "DELETE"` 或命中 `destructive` → 生成 `H-DESTRUCT-1`（破坏性二次确认缺失假说）。

## 6.2 确定性安全不变量评估器 (`harness.invariant_evaluator`) [FACT]

```python
@dataclass(frozen=True)
class InvariantEvaluation:
    invariant_type: str
    status: str      # confirmed, vulnerable, inconclusive
    rationale: str
```

断言规则：
1. **`destructive_confirmation`**：破坏性操作缺失 `confirm`/`csrf` 且服务端返回 `200~299` → 判定 `vulnerable`；否则判定 `confirmed`。
2. **`auth_boundary`**：特权路由缺失凭证且返回 `200~299` → 判定 `vulnerable`；返回 `401/403` → 判定 `confirmed`。

## 6.3 知识卡片与晋级门禁 (`agent.knowledge_promoter`) [FACT]

```python
@dataclass(frozen=True)
class KnowledgeCard:
    card_id: str
    category: str
    title: str
    claim: str
    severity: str             # CRITICAL, HIGH, MEDIUM, LOW, INFO
    verification_state: str   # VERIFIED, REFUTED
    confidence: float
    source_hypothesis: str
    provenance_task: str
    remediation: str
    evidence_summary: str = ""
```

**晋级门禁铁律（Promotion Gate）**：
- 严格拦截任何仍处于 `PROPOSED`（未经验证推测）的假说，绝不出具知识卡片。
- 仅当假说被沙箱评判为 `VERIFIED`（证实漏洞）或 `REFUTED`（证伪防御坚固）时，方可提炼生成附带修复指导的不可变知识卡片。

---

# 7. 全自动化流水线收口闭环 [FACT]

在 `crates/tests/pipeline_e2e_test.rs` 中已实证贯通无人工干预全自动流水线：

```text
前端 JavaScript 源码 / 文件目标
        ↓ (stdin 管道)
Python: ast_worker (Tree-sitter AST 解析 + 幂等去重)
        ↓ (stdout 管道)
Rust: ProcessAstExtractor 生成 Vec<ResearchTask>
        ↓
Rust: ResearchOrchestrator 批量调度
        ↓ (stdin 单进程 Batch IPC 管道)
Python: research_worker
        ├── 假设引擎注入先验假说 (PROPOSED)
        ├── 自适应沙箱执行自愈变异
        ├── 不变量评估器定性判决
        └── 决算假说状态机 (VERIFIED / REFUTED)
        ↓ (stdout Batch IPC 管道)
Rust: ResearchOrchestrator::audit 规约
        ↓
强类型战报 AuditReport (含 total, vulnerable_tasks, results)
```

---

# 8. 测试验收矩阵与当前系统状态 [FACT]

截至 2026-09-15，全系统 **48 项自动化测试 100% 保持绿灯，0 错误、0 警告、0 退化**：

### 🦀 Rust 引擎测试集 (14 passed)
- 库单元测试（1 passed）
- 契约、序列化、别名、批量与战报集成测试 `orchestrator_contract_test.rs`（10 passed）
- 跨进程 IPC 测试 `process_executor_contract_test.rs`（2 passed）
- 端到端全自动闭环集成测试 `pipeline_e2e_test.rs`（1 passed）

### 🐍 Python 引擎测试集 (34 passed)
- 证据映射桥接与历史保留（2 passed）
- 执行结果聚合与向后兼容（2 passed）
- 自愈变异循环与网关覆盖（2 passed）
- 流水线接缝与适配器多态批量转译（5 passed）
- 进程工作者单任务与批量标准流监听 `test_research_worker.py`（3 passed）
- Tree-sitter AST 提取监听器 `test_ast_worker.py`（2 passed）
- 业务安全不变量逻辑评估 `test_invariant_evaluator.py`（5 passed）
- 沙箱自适应不变量与决断集成 `test_sandbox_invariant_integration.py`（2 passed）
- 假说自主推演与验证状态机 `test_hypothesis_engine.py`（7 passed）
- 知识卡片提纯与晋级门禁 `test_knowledge_promoter.py`（4 passed）

---

# 9. 已验证的实战踩坑清单 (新增与更新)

## 坑 1：盲目将开源 Payload 字典倒进沙箱
- **错误**：把 SecLists、Penetration-List 的万条字典硬编码塞入沙箱发包。
- **根治**：算法重于字典。字典放入 `data/` 作为只读资产；仅提炼出结构化的安全不变量（Invariant）与敏感参数规则，实施精准定向验证。

## 坑 2：Windows 跨进程命令行长度与转义地狱
- **错误**：尝试使用命令行参数（`--task '{"..."}'`）向子进程传参，遭遇 8191 字符截断及引号转义崩溃。
- **根治**：全量采用系统内核匿名管道（`Stdio::piped()`），基于 `stdin/stdout` 进行纯流式无损传输。

## 坑 3：子进程未捕获异常引发 IPC 死锁
- **错误**：Python 代码抛出原生 Traceback 崩溃退出，Rust 在管道读端无限阻塞等待。
- **根治**：Python Worker 设立全局异常防护墙，捕获所有异常并封装为 JSON 错误结构写回管道，规范返回退出码 1。

## 坑 4：单端点单进程启动造成的性能灾难
- **错误**：扫描 50 个端点唤醒 50 次子进程，在 Windows 上因页表与解释器初始化耗时近 1 分钟。
- **根治**：升级为 Single-Invocation Batch IPC，单次进程启动处理整个 JSON 数组，耗时压缩至 1.2 秒。

## 坑 5：AI 幻觉污染安全知识库
- **错误**：将大模型生成的假设或未经证实的推测直接作为漏洞卡片落盘。
- **根治**：设立严格的知识晋级门禁（Promotion Gate），只有状态流转到 `VERIFIED` 的假设才允许生成 `KnowledgeCard`。

## 坑 6：把集成测试放进 `src`
- **根治**：严格遵守目录契约，Rust 集成测试必须放在 `crates/tests/` 目录下。

## 坑 7：用空字符串冒充 `Optional`
- **根治**：强类型系统中 `None` 与 `Some(...)` 属于不同领域状态，严格采用 `Option<T>`。

---

# 10. 阶段演进路线图更新

```text
Phase 1: 确定性工具 + 基础契约                     [已完成 ✅]
Phase 2: ResearchCase + 证据链模型                  [已完成 ✅]
Phase 3: 可替换执行器特征 (ResearchExecutor)         [已完成 ✅]
Phase 4: 跨语言别名对账 (case_id <-> task_id)        [已完成 ✅]
Phase 5: 匿名管道进程级 IPC 贯通                    [已完成 ✅]
Phase 6: 单进程批量 IPC 吞吐量优化 (40x 跃升)       [已完成 ✅]
Phase 7: AST 全自动化流水线双引擎收口               [已完成 ✅]
Phase 8: 安全不变量推理与脆弱性指标收敛             [已完成 ✅]
Phase 9: 智能体假说推演、状态机与知识卡片晋级       [已完成 ✅]
Phase 10: 桌面端表现层接入 (Tauri UI Bridge)        [🎯 下一步]
Phase 11: 高级研究算子 (BOLA 对比 / 方法篡改)        [待启动 ⏳]
Phase 12: 大模型 Agent 多轮对话与全自主规划         [待启动 ⏳]
```

---

# 11. 最终工程宣言

Invar 不追求单点零件的表面炫技，而追求整套双引擎架构的**协同最优**。

```text
代码世界 (AST)
      │
      ▼
先验假说 (Hypothesis PROPOSED)
      │
      ▼
物理发包 (Adaptive Mutation)
      │
      ▼
不变量断言 (Invariant Evaluated)
      │
      ▼
假说证实 (Hypothesis VERIFIED)
      │
      ▼
知识晋级 (Knowledge Card)
      │
      ▼
全局战报 (Audit Report: Vulnerable Found)
```

**可复现、可解释、可测试、可替换、可扩展、可审计。**  
这就是 Invar AI 工程体系不可动摇的核心基准。
