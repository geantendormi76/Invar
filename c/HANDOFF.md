# Invar 项目会话交接文档（HANDOFF）

版本：2026-09-16 高级研究算子沙箱实战装配与 58 项测试全绿版  
项目根目录：`C:\dev\Invar`

---

## 0. 给新会话 AI 的最高优先级说明

这是一个正在进行中的 **Invar Rust + Python 双引擎工业级自动化安全研究系统**。
当前核心商业目标：**以实战漏洞挖掘变现为导向，主攻高价值逻辑漏洞（越权 BOLA/IDOR、未授权、破坏性操作二次确认缺失），赚取补天等 SRC 平台漏洞赏金（目标：5000元购入 7900 XTX 24G）**。

当前架构定位与分工：
```text
Rust = 系统级总控 / 编排 / 生命周期 / 进程管理 / 匿名管道 Batch IPC / 资源管理 / 强类型全局战报聚合
Python = 专业研究算法 / AI / AST 参数深度剥离 / 自适应报错变异 / 安全不变量推理 / 科研假说演绎 / 知识晋级门禁 / 高级攻防算子库
```

核心工程原则：
- 零臆造、零特判、纯泛化
- 严密遵循 TDD：红灯（确认根因）→ 最小合理生产修改 → 绿灯 → 双向全量回归
- 目录结构是一级工程契约，严格维持 `src` 与 `tests` 的物理隔离
- Windows PowerShell 原样交付，一律使用 `uv run` 环境

---

## 1. 当前工程全景状态（58 passed, 0 failed）

### 1.1 双引擎总体状态
```text
Rust 端 (14 passed, 0 warnings):
  ├── Library Crate (invar_core)             ✅
  ├── ResearchTask (带 case_id 别名)          ✅
  ├── ResearchDecision (Option 包装)          ✅
  ├── ResearchResult (强类型战报)             ✅
  ├── AuditReport (包含 vulnerable_tasks)     ✅
  ├── ResearchExecutor trait (execute_batch)  ✅
  ├── ResearchOrchestrator (run, run_all, audit) ✅
  ├── ProcessResearchExecutor (匿名管道批量 IPC) ✅
  ├── ProcessAstExtractor (匿名管道 AST 提取器)  ✅
  └── 全量单元与集成测试 (14 passed)          ✅

Python 端 (44 passed, 0 failed):
  ├── HttpTransport (确定性发包)              ✅
  ├── FeedbackInterpreter (Go 报错模式识别)    ✅
  ├── MutationPolicy (自适应载荷变异)          ✅
  ├── ResearchCase & ProbeAttempt (单调编号)  ✅
  ├── ResearchExecutionResult                 ✅
  ├── ProbeAttemptEvidenceMapper (证据桥接)   ✅
  ├── InvariantEvaluator (安全不变量评估引擎) ✅
  ├── HypothesisEngine (自主假设推演与决算机) ✅
  ├── KnowledgeCard (经验证不可变知识卡片模型) ✅
  ├── KnowledgePromoter (带门禁的安全知识晋级器，含 DESTRUCT / AUTH / IDOR) ✅
  ├── MethodTamperOperator (HTTP 方法篡改算子) ✅
  ├── IdorCompareOperator (BOLA 双盲对比算子) ✅
  ├── AdaptiveSandboxExecutor (双装配完成: 双 Token 越权差分 + 403 动词隧道穿透) ✅
  ├── ResearchTaskAdapter (多态批量契约适配器) ✅
  ├── ResearchWorker (标准流批量进程监听器)    ✅
  ├── AstWorker (Tree-sitter AST 提取监听器)  ✅
  └── 全量回归测试集 (44 passed, 0 failed)    ✅
```

### 1.2 高级研究算子武器库状态 (Phase 11)
| 算子标识 | 核心实战能力 | 沙箱装配状态 | 集成测试守门 |
| :--- | :--- | :--- | :--- |
| `http.tamper` | 遭遇 403/405 自动生成 Header 隧道 (`X-HTTP-Method-Override`)、Query 隧道与动词替换变体重试 | ✅ 已装配进入沙箱 | `test_sandbox_tamper_integration.py` (Passed) |
| `idor.compare` | 针对属主参数 (`order_id` 等) 自动调度 Token A 与 Token B 发起对照发包，基于 `SequenceMatcher` 相似度实锤水平越权 | ✅ 已装配进入沙箱 | `test_sandbox_idor_integration.py` (Passed) |

---

## 2. 测试套件与全量验证命令

### 2.1 Rust 测试集（14 passed，0 warnings）
```powershell
cargo test --manifest-path 'C:\dev\Invar\src-tauri\crates\Cargo.toml'
```

### 2.2 Python 测试集（44 passed，0 failed）
```powershell
$env:PYTHONPATH="C:\dev\Invar\src-tauri\python\src"; uv run --project "C:\dev\Invar\src-tauri\python" --python 3.11 python -m unittest `
    "C:\dev\Invar\src-tauri\python\tests\test_research_evidence_bridge.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_evidence_history.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_execution_result.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_loop_integration.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_sandbox_base_url_compatibility.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_scan_pipeline_integration.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_task_adapter.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_research_worker.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_ast_worker.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_invariant_evaluator.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_sandbox_invariant_integration.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_hypothesis_engine.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_knowledge_promoter.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_method_tamper.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_idor_compare.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_sandbox_idor_integration.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_sandbox_tamper_integration.py"
```

---

## 3. 下一步严格演进路线 (实战变现导向)

下一阶段核心任务：**Step 11.4 端到端实战靶场验收**。
1. 构建一个高仿真实战靶场服务（本地轻量 HTTP Server），内置真实的 BOLA（水平越权）与 403 动词隧道穿透漏洞端点；
2. 由 Rust 总控调度（`ResearchOrchestrator` -> 匿名管道 Batch IPC -> Python 沙箱引擎）；
3. 全自动完成真实发包扫描，最终在终端输出带有不可辩驳报文证据的 `AuditReport: vulnerable_tasks >= 1` 全局战报！
