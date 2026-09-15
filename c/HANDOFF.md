# Invar 项目会话交接文档（HANDOFF）

版本：2026-09-15 跨语言 IPC 贯通收口版  
项目根目录：`C:\dev\Invar`

---

## 0. 给新会话 AI 的最高优先级说明

这是一个正在进行中的 **Invar Rust + Python 双引擎工业级研究系统**。

当前架构定位已完全实证打通：

```text
Rust = 系统级总控 / 编排 / 生命周期 / 进程管理 / 管道 IPC / 资源管理 / 并发边界 / 强类型契约
Python = 专业研究算法 / AI / ML / AST 解析 / 自适应报错变异 / 快速安全实验
```

核心工程原则：
- 零臆造、零特判、纯泛化
- 目录结构是一级工程契约，严格维持 `src`（生产/局部单元测试）与 `tests`（集成/黑盒契约测试）的物理隔离
- 强类型优先，契约收敛优先，杜绝将 Python 动态字典粗暴灌入 Rust
- 严密遵循 TDD：红灯（确认根因）→ 最小合理生产修改 → 绿灯 → 双向全量回归
- Windows PowerShell 原样交付，禁止使用裸 `python` 或 `pip`，一律走 `uv` 环境

---

## 1. 当前工程全景状态

### 1.1 双引擎总体状态
```text
Rust 端：
  ├── Library Crate (invar_core)             ✅
  ├── ResearchTask (带 case_id 别名)          ✅
  ├── ResearchDecision (Option 包装)          ✅
  ├── ResearchResult (强类型战报)             ✅
  ├── ResearchExecutor trait (抽象特征)       ✅
  ├── ResearchOrchestrator (系统总控)         ✅
  ├── ProcessResearchExecutor (匿名管道 IPC)   ✅
  └── 单元 & 集成测试 (8 passed, 0 warnings)  ✅

Python 端：
  ├── HttpTransport (确定性发包)              ✅
  ├── FeedbackInterpreter (Go 报错模式识别)    ✅
  ├── MutationPolicy (自适应载荷变异)          ✅
  ├── ResearchCase & ProbeAttempt (单调编号)  ✅
  ├── ResearchExecutionResult                 ✅
  ├── ProbeAttemptEvidenceMapper (证据桥接)   ✅
  ├── AdaptiveSandboxExecutor (沙箱闭环引擎)  ✅
  ├── ResearchTaskAdapter (跨语言契约适配器)   ✅
  ├── ResearchWorker (标准流进程监听器)        ✅
  └── 全量回归测试集 (12 passed, 0 failed)    ✅
```

### 1.2 跨语言 IPC 通信架构已打通
```text
  ┌─────────────────────────┐
  │  Rust Orchestrator      │
  │  (ProcessResearchExec)  │
  └──────────┬──────────────┘
             │ 1. 序列化 ResearchTask JSON 灌入 stdin 管道
             ▼
  ┌─────────────────────────┐
  │  OS Anonymous Pipe      │
  └──────────┬──────────────┘
             │ 2. 操作系统内核环形缓冲区无损传输
             ▼
  ┌─────────────────────────┐
  │  Python ResearchWorker  │
  │  (harness.research_worker)
  └──────────┬──────────────┘
             │ 3. ResearchTaskAdapter 转换为 EndpointIR
             │ 4. AdaptiveSandboxExecutor 驱动自愈变异闭环
             │ 5. 结果提炼收敛为 ResearchResult JSON
             ▼
  ┌─────────────────────────┐
  │  OS Anonymous Pipe      │
  └──────────┬──────────────┘
             │ 6. stdout 回传管道
             ▼
  ┌─────────────────────────┐
  │  Rust 反序列化 ResearchResult
  │  返回给调度总控          │
  └─────────────────────────┘
```

---

## 2. 跨语言对账结论与字段契约标准

| Rust 契约字段 | 类型 | Python 对应事实 | 是否跨语言 | 架构理由 |
| :--- | :--- | :--- | :--- | :--- |
| `task_id` | `String` | `case_id` | **是** | 主键标识。Rust 配置 `#[serde(alias = "case_id")]` 实现双向兼容 |
| `method` | `String` | `endpoint.method` | **是** | HTTP 请求动作（GET/POST/PUT/DELETE 等） |
| `path` | `String` | `endpoint.path` | **是** | 目标 API 路径 |
| `status` | `String` | 状态推导结果 | **是** | `"completed"` / `"inconclusive"` / `"process_failed"` |
| `attempts` | `u32` | `len(case.attempts)` | **是** | 探测轮次统计，避免跨语言传递全部庞大的动态报文 |
| `decision` | `Option<Decision>` | `case.decision` | **是** | 最终决断上下文（status 与 rationale） |
| `evidence_history_count` | `u32` | `len(evidence_history)` | **是** | 证据链快照计数，用以审计核验 |

---

## 3. 测试套件与验证命令

### 3.1 Rust 测试集（8 passed）
包含：
- `orchestrator::tests::research_orchestrator_supports_replaceable_executor`
- `tests/orchestrator_contract_test.rs`（6 个契约与别名测试）
- `tests/process_executor_contract_test.rs`（1 个跨语言真实管道测试）

验证命令：
```powershell
cargo test --manifest-path 'C:\dev\Invar\src-tauri\crates\Cargo.toml'
```

### 3.2 Python 测试集（12 passed）
包含：
- `test_research_evidence_bridge.py`
- `test_research_evidence_history.py`
- `test_research_execution_result.py`
- `test_research_loop_integration.py`
- `test_sandbox_base_url_compatibility.py`
- `test_scan_pipeline_integration.py`
- `test_research_task_adapter.py`
- `test_research_worker.py`

验证命令：
```powershell
$env:PYTHONPATH="C:\dev\Invar\src-tauri\python\src"; uv run --project "C:\dev\Invar\src-tauri\python" --python 3.11 python -m unittest `
    "C:\dev\Invar\src-tauri\python\tests\test_research_evidence_bridge.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_evidence_history.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_execution_result.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_loop_integration.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_sandbox_base_url_compatibility.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_scan_pipeline_integration.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_task_adapter.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_worker.py"
```

---

## 4. 踩坑与避坑铁律（新增沉淀）

1. **Windows 跨进程命令行长度与转义陷阱**：严禁尝试用命令行参数（如 `--task '{"..."}'`）传递复杂数据，必须坚持使用匿名管道（`Stdio::piped()`）进行标准流传递。
2. **未捕获异常死锁风险**：Python Worker 必须包裹全局异常捕获，即使输入完全畸形也必须向 `stdout` 输出结构化错误并正常退出，严禁抛出原生堆栈崩溃导致 Rust 读端永远挂起。
3. **集成测试命名与路径契约**：Rust 集成测试必须放在 `crates/tests/` 目录下；如果需要引用 crate 导出的结构体，必须确保在 `src/lib.rs` 中显式公开导出（`pub use`）。
4. **无意义警告零容忍**：引入新结构体时若在测试中产生 `unused import` 警告，必须及时清理，保持编译器净空。

---

## 5. 下一步严格演进路线

下一阶段核心任务：
1. **多任务批量编排与并发控制**：在 Rust `ResearchOrchestrator` 中引入 `run_all(&[ResearchTask]) -> Vec<ResearchResult>` 批量执行接口。
2. **子进程生命周期与常驻优化（Daemon/Streaming 评估）**：评估当前单次任务启动与持久子进程（Long-running Worker）的性能开销，设计更平滑的任务流通道。
3. **AST 全链路贯通（Pipeline Migration）**：将前端 AST 解析产出的多个 `EndpointIR`，交由 Rust 总控批量生成 `ResearchTask` 队列并统一调度回 Python 沙箱执行。
