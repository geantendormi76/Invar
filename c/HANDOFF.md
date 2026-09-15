# Invar 项目会话交接文档（HANDOFF）

版本：2026-09-15 五层认知架构全面合流收口版  
项目根目录：`C:\dev\Invar`

---

## 0. 给新会话 AI 的最高优先级说明

这是一个正在进行中的 **Invar Rust + Python 双引擎工业级自动化安全研究系统**。

当前架构定位已完成实证贯通：

```text
Rust = 系统级总控 / 编排 / 生命周期 / 进程管理 / 管道 IPC / 资源管理 / 并发边界 / 强类型全局战报聚合
Python = 专业研究算法 / AI / ML / Tree-sitter AST 解析 / 自适应报错变异 / 安全不变量推理 / 科研假说演绎 / 知识晋级提纯
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

Python 端 (34 passed, 0 failed):
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
  └── 全量回归测试集 (34 passed, 0 failed)    ✅
```

### 1.2 彭峙酿五层认知体系实证映射
```text
┌─────────────────────────────────────────────────────────────┐
│  Level 5: Agent 认知规划层                                   │
│  • HypothesisEngine 自主生成 H-IDOR, H-AUTH, H-DESTRUCT     │
│  • 假设状态机: PROPOSED -> VERIFIED / REFUTED               │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│  Level 4: Skill 业务策略与安全不变量层                       │
│  • InvariantEvaluator: destructive_confirmation, auth_bound │
│  • 合成 ResearchDecision (vulnerable / confirmed)           │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│  Level 3: Harness 确定性脚手架与双向管道                     │
│  • Tree-sitter AST 解析器 + 去重 (ast_worker)               │
│  • 匿名管道 Batch IPC 通道 (40x 极速吞吐)                   │
│  • 自适应闭环沙箱变异 (AdaptiveSandboxExecutor)             │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│  Level 2: Evidence 证据链留痕                               │
│  • 连续单调编号 ProbeAttempt 变异轨迹                       │
│  • EvidenceRecord 异常标注 (is_anomaly, VULN_FOUND)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│  Level 1: Knowledge 知识晋级提纯层                           │
│  • KnowledgePromoter: 严格晋级门禁 (拒绝未证实推测)         │
│  • KnowledgeCard: 包含 claim, severity, remediation, prov   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 核心知识卡片范例（提纯成果）

| 卡片类型 | 归类 (Category) | 严重性 | 触发条件 | 产出修复指引 (Remediation) |
| :--- | :--- | :--- | :--- | :--- |
| 破坏性接口二次确认缺失 | `DESTRUCTIVE_GUARD_MISSING` | **HIGH** | `H-DESTRUCT` 假设被证实（无 confirm 成功清空数据） | 建议在路由中间件中强制拦截缺失 confirm 或二次验证令牌的破坏性请求 |
| 敏感特权路由缺失认证 | `BROKEN_AUTHENTICATION` | **CRITICAL** | `H-AUTH` 假设被证实（未带 Token 被异常放行 200） | 建议在路由拦截器中强制校验 Authorization 身份凭证并严密核验 JWT 签名 |
| 安全基线事实卡片 | `DESTRUCTIVE_GUARD_VERIFIED` / `AUTHENTICATION_ENFORCED` | **INFO** | 对应假设被证伪（服务端坚守 401/403 或强制确认） | 记录防御生效证据，作为后续 Agent 长期记忆，防止重复试探 |

---

## 3. 测试套件与全量验证命令

### 3.1 Rust 测试集（14 passed，0 warnings）
验证命令：
```powershell
cargo test --manifest-path 'C:\dev\Invar\src-tauri\crates\Cargo.toml'
```
覆盖清单：
- 库单元测试（1 passed）
- 契约、批量调度与漏洞指标集成测试 `orchestrator_contract_test.rs`（10 passed）
- 跨进程 IPC 测试 `process_executor_contract_test.rs`（2 passed）
- 全链路端到端闭环测试 `pipeline_e2e_test.rs`（1 passed）

### 3.2 Python 测试集（34 passed，0 failed）
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
    "C:\dev\Invar\src-tauri\python\tests\test_knowledge_promoter.py"
```

---

## 4. 下一步演进路线

下一阶段核心任务（Phase K：Tauri 桌面表现层接入）：
1. **Tauri Command 调度桥接**：在 Rust 侧暴露 `audit_target` 命令，接收前端传入的源码路径或代码文本，一键驱动双引擎流水线。
2. **流式进度事件（Streaming Events）**：通过 Tauri 事件总线（Event Emitter）向前端 Vue3 实时推送“端点提炼中”、“沙箱自愈变异中”、“漏洞捕获警报”等动态状态。
3. **知识卡片大屏渲染**：前端直接消费 Rust 回传的 `AuditReport` 与结构化知识卡片，呈现现代化安全审计可视化看板！
