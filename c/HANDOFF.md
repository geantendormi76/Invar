# Invar 项目会话交接文档（HANDOFF）

版本：2026-09-16 高级研究算子列装与 55 项测试全绿版  
项目根目录：`C:\dev\Invar`

---

## 0. 给新会话 AI 的最高优先级说明

这是一个正在进行中的 **Invar Rust + Python 双引擎工业级自动化安全研究系统**。
当前核心商业目标：**以实战漏洞挖掘变现为导向，主攻高价值逻辑漏洞（越权、未授权、破坏性操作）**。

当前架构定位已完成实证贯通：

```text
Rust = 系统级总控 / 编排 / 生命周期 / 进程管理 / 管道 IPC / 资源管理 / 并发边界 / 强类型全局战报聚合
Python = 专业研究算法 / AI / ML / AST 解析 / 自适应报错变异 / 安全不变量推理 / 科研假说演绎 / 知识晋级 / 高级攻防算子
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

Python 端 (41 passed, 0 failed):
  ├── HttpTransport (确定性发包)              ✅
  ├── FeedbackInterpreter (Go 报错模式识别)    ✅
  ├── MutationPolicy (自适应载荷变异)          ✅
  ├── ResearchCase & ProbeAttempt (单调编号)  ✅
  ├── ResearchExecutionResult                 ✅
  ├── ProbeAttemptEvidenceMapper (证据桥接)   ✅
  ├── AdaptiveSandboxExecutor (沙箱闭环引擎)  ✅
  ├── ResearchTaskAdapter (多态批量契约适配器) ✅
  ├── ResearchWorker (标准流批量进程监听器)    ✅
  ├── AstWorker (Tree-sitter AST 提取监听器)  ✅
  ├── InvariantEvaluator (安全不变量评估引擎) ✅
  ├── HypothesisEngine (自主假设推演与决算机) ✅
  ├── KnowledgeCard (经验证不可变知识卡片模型) ✅
  ├── KnowledgePromoter (带门禁的安全知识晋级器) ✅
  ├── MethodTamperOperator (HTTP方法篡改算子)  ✅
  ├── IdorCompareOperator (BOLA双盲对比算子)   ✅
  └── 全量回归测试集 (41 passed, 0 failed)    ✅
```

### 1.2 高级研究算子库 (Phase 11)
| 算子标识 | 核心能力 | 解决的实战痛点 | 状态 |
| :--- | :--- | :--- | :--- |
| `http.tamper` | 生成 Header 隧道、Query 隧道与动词替换变体 | 绕过 WAF 与后端框架的动词语义错位，实现防火墙逃逸 | ✅ 已就绪 |
| `idor.compare` | 基于 `SequenceMatcher` 的双主体响应相似度对比 | 彻底消除 200 OK 误报，精准实锤水平越权 (BOLA) 漏洞 | ✅ 已就绪 |

---

## 2. 测试套件与全量验证命令

### 2.1 Rust 测试集（14 passed，0 warnings）
验证命令：
```powershell
cargo test --manifest-path 'C:\dev\Invar\src-tauri\crates\Cargo.toml'
```

### 2.2 Python 测试集（41 passed，0 failed）
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
    "C:\dev\Invar\src-tauri\python\tests\test_research_worker.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_ast_worker.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_invariant_evaluator.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_sandbox_invariant_integration.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_hypothesis_engine.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_knowledge_promoter.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_method_tamper.py" `
    "C:\dev\Invar\src-tauri\python\tests\test_idor_compare.py"
```

---

## 3. 下一步严格演进路线 (实战变现导向)

下一阶段核心任务：**将高级算子装配至沙箱，打通实战发包链路**。
1. **IDOR 实战装配**：在 `AdaptiveSandboxExecutor` 中引入双 Token 配置（`auth_token_a` 与 `auth_token_b`）。当用例存在 `H-IDOR` 假设时，沙箱自动触发 `idor.compare` 算子，完成“基线请求 -> 越权请求 -> 相似度对比 -> 漏洞定性”的全自动发包闭环。
2. **Tamper 实战装配**：当常规探测被 403 拦截且存在 `H-DESTRUCT` 或 `H-AUTH` 时，自动调用 `http.tamper` 生成变体进行逃逸重试。
3. **端到端实战靶场验收**：在本地起一个带有真实 BOLA 漏洞的 Python 靶场，用 Rust 总控一键扫描并成功输出 `vulnerable_tasks: 1` 的战报！
