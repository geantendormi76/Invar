# EXP-01：Object Reference 与生命周期血统事实核验报告

> **文档性质**：工程事实审计（FACTS AUDIT）  
> **归档位置**：`docs/笔记/EXP-01-FACTS.md`  
> **审计范围**：基于 92 个源码文件的精确 AST 符号流向分析（commit/snapshot 2026-09-29）  
> **核心结论**：Invar 具备完整确定性生命周期链路；GAP-01（对象引用语义缺失）确凿存在；无需修改 Rust `ResearchTask` 契约。

---

## 1. 钉死的生产代码 5 步完整生命周期链路

经 AST 符号定位与调用流分析，Invar 运行时的数据生命周期血统（Lifecycle Provenance）100% 确认如下：

```text
 ┌──────────────┐
 │  TriageTask  │ (harness/triage_dispatcher.py:190)
 └──────┬───────┘
        │ 经由 ResearchTaskAdapter 转译为 EndpointIR
        ▼
 ┌──────────────┐
 │ ResearchCase │ 谁创建？➔ AdaptiveSandboxExecutor._create_research_case()
 └──────┬───────┘ (harness/sandbox_executor.py:129)
        │ 动态发包与反馈变异自愈循环中
        ▼
 ┌──────────────┐
 │ ProbeAttempt │ 谁创建？➔ ResearchCase.record_attempt()
 └──────┬───────┘ (harness/domain_contracts.py:864 / sandbox_executor.py)
        │ 探针收敛后映射微观物理尝试为可追溯凭证
        ▼
 ┌──────────────┐
 │EvidenceRecord│ 谁创建？➔ ProbeAttemptEvidenceMapper.to_evidence_records()
 └──────┬───────┘ (harness/research_evidence.py:41)
        │ 安全不变量裁决判定 vulnerable 击穿底线时
        ▼
 ┌──────────────┐
 │  Candidate   │ 谁创建？➔ Hunter.hunt() / run_targeted_audit.py
 └──────┬───────┘ (agent/hunter.py:118 / scripts/run_targeted_audit.py:417)
        │ 候选实体通过 FindingRecord.from_candidate() 升级后
        ▼
 ┌──────────────┐
 │ Verification │ 哪里接入？➔ IndependentVerifier.verify() ➔ PromotionGate
 └──────────────┘ (harness/verification_gate.py:47, 137)
```

### 1.1 节点确切创建者事实表
| 节点实体 | 确切创建者（函数/方法） | 物理文件与行号 | 触发时机 | 输出去向 |
|---|---|---|---|---|
| **TriageTask** | `TriageDispatcher.classify_and_assemble()` | `triage_dispatcher.py:190` | 双轨产物池分流装配 | 导出为 Rust 字典或任务清单 |
| **ResearchCase** | `AdaptiveSandboxExecutor._create_research_case()` | `sandbox_executor.py:129` | 沙箱执行探测第一步 | 挂载不变量与假说，承载全流程实验状态 |
| **ProbeAttempt** | `ResearchCase.record_attempt()` | `domain_contracts.py:864` | 每次物理发包响应后 | 存入 `case.attempts` 序列，保证编号递增 |
| **EvidenceRecord** | `ProbeAttemptEvidenceMapper.to_evidence_records()` | `research_evidence.py:41` | 沙箱变异循环收敛后 | 构成不可变微观证据链，供门禁核验 |
| **Candidate** | `Hunter.hunt()` / `run_targeted_audit.py` | `hunter.py:118` / `run_targeted_audit.py:417` | `decision.status == "vulnerable"` 时 | 提取规范因子，生成确定性指纹 |
| **Verification** | `IndependentVerifier.verify()` ➔ `PromotionGate.assert_promotable()` | `verification_gate.py:47, 137` | Finding 晋升前夕 | 8 大谓词严格校验，拒绝自发自审 |

---

## 2. 异构事实澄清与盲区消除

1. **`VerificationGate` 符号为 0 的原因**：
   * **[FACT]** 生产代码文件名是 `verification_gate.py`，但其内部严格按照单一职责拆分为了两个核心类：
     - `IndependentVerifier`（独立第三方复核器契约）
     - `PromotionGate`（科学证据晋级门禁断言器）
   * **[FACT]** 校验逻辑完整存在且被全量测试覆盖，仅为类命名更加精确。
2. **`ResearchTask` 在 Python 侧无 Class 定义的原因**：
   * **[FACT]** `ResearchTask` 结构体属于 Rust 核心引擎（`crates/core/src/orchestrator.rs`）的一级强类型契约。
   * **[DECISION]** Python 侧通过 `to_rust_task_dict()` 和 `ResearchTaskAdapter` 直接使用原生字典透传，彻底避免跨语言多处 Class 定义引发的 Schema 漂移风险。

---

## 3. EXP-01 核心核验：Object Reference Gap 确凿存在

### 3.1 现状与代码病灶
* **[FACT]** 当前代码中的越权假说生成（`hypothesis_engine.py:21`）与沙箱双主体越权探针（`sandbox_executor.py:166`），全量硬编码绑定于：
  ```python
  any(k in p.lower() for k in IDOR_KEYWORDS) for p in endpoint.extracted_params
  ```
* **[FACT]** `IDOR_KEYWORDS` 仅包含 `id`, `user_id`, `uid`, `account_id`, `order_id`, `member_id`, `customer_id`, `tenant_id`, `doc_id`。
* **[INFERENCE]** 现行实现仅为 **“参数名关键词启发式（Parameter Name Heuristic）”**，并非真正理解 **“对象引用（Object Reference）”**：
  1. 若接口为 `POST /api/v3/delegate/grant`，参数为 `{"grantee": "guest", "scope": "admin"}`，虽无 `id` 关键词，但属于典型的特权委托对象操作，现有启发式直接**失明**；
  2. 若接口包含嵌套 JSON 对象或 URL 路径分段，现有启发式无法识别。

### 3.2 架构定力结论
* **[DECISION]** **绝对不需要修改 Rust 的 `ResearchTask` 契约**！
* `ResearchTask` 是跨语言的物理调度凭证，必须保持干净轻量；
* 对象引用语义与上下文观察，应当作为战术上下文注入给上层 **Pi Agent + `SKILL.md`**，并在 Python Context 层流动，不污染 Rust 底层契约。

---

## 4. 体系定位与工具链划分（防止重造轮子）

* **认知大脑**：本地大模型 `Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE`
* **Agent 运行时（Harness）**：现成全局 `@earendil-works/pi-coding-agent`（Node.js，运行器：`tools/invar_agent_runner.mjs`）
* **战术层（SOP）**：`skills/*/SKILL.md`（吸纳 Claude-Red 7 段式规范与 A.I.G 蓝军实证哲学）
* **确定性安全核心**：Invar Python / Rust 沙箱与门禁系统（物理发包、变异自愈、双主体差分、不变量确权）
