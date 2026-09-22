# AI Development Handoff Specification

> **Document type:** Cross-session engineering state snapshot / recovery contract
> **Project:** base-jev + Invar + distiller (Triad Dual-Engine System)
> **Canonical project roots:**
>   - Model Factory: `C:\dev\base-jev`
>   - Upstream Distiller: `C:\dev\distiller`
>   - Downstream Verification Engine: `C:\dev\Invar`
> **Handoff path:** `c/HANDOFF.md`
> **Snapshot date:** 2026-09-22
> **Document version:** 6.0.0 (Grand Breakthrough Edition: Neural Recall Leap 0% -> 80% & Academic Suite v4.0 Verified)
> **Primary purpose:** A new AI must be able to reconstruct the current engineering/research state from this document plus the current repository source, tests, configuration, and artifacts, without relying on the old conversation.

---

## 0. Handoff Metadata

| Item | Value | Level | Notes |
|---|---|---|---|
| Project | base-jev + Invar + distiller | [FACT] | System-1 Fast Sensor (23ms) + System-2 Execution Verification |
| Model Factory Root | `C:\dev\base-jev` | [FACT] | Pure Discriminative SFT Factory & ONNX DirectML Runtime |
| Distillation Workshop | `C:\dev\distiller` | [FACT] | Dual-Teacher Distillation (Qwen-27B Local + Gemini API Cloud) |
| Execution & Verification | `C:\dev\Invar` | [FACT] | AST Parsing, DualTrack Comparator, Gold Set Academic Suite |
| Current Base Backbone | `models/Qwen3-0.6B-Base` | [FACT] | 1024D Hidden Size, `lm_head` physically stripped |
| Production ONNX SHA256 | `908db8140ab25a3230a0e541145b05421250c9a126078d0014f106b675ba11cc` | [FACT] | 1251.11 MB single-file FP16 static graph |
| Hardware Steady Latency | `23.08 ms` (P99: `24.53 ms`) | [FACT] | RTX 3060 DirectML TensorCore, verified by `base-jev-qa` |
| Gold Set Ground Truth | 60 cards, 10 true high-risk | [FACT] | Physical Firewall Verified (`Train ∩ Gold = ∅`) |
| **Model Recall on Gold Set** | **80.00% (TP=8/10, FN=2)** | [FACT] | Precision: 36.36%, F1: 0.5000 (Crushed Rule 50% / 0.3448) |
| **Pool B Discrepancy Recall** | **100.00% (TP=5/5, FN=0)** | [FACT] | Precision: 62.50%, F1: 0.7692 (Rule completely blind 0.0%) |
| **Dual-Track Ensemble Recall**| **100.00% (TP=10/10, FN=0)** | [FACT] | Rule ∪ Neural: Zero Misses, Cost dropped from 64.0 to 22.0 |

---

## 1. Project Identity

[DECISION]
The system is an industrial Triad Architecture:
1. **distiller**: Expert knowledge compiler. Employs dual teachers (Local Qwen-27B + Cloud Gemini Flash) with Tree-sitter AST and physical Gold Firewall. Outputs standardized DualScore labels (Impact & Sensitivity).
2. **base-jev**: System-1 cognitive reflex frontend. Discriminative SFT (Soft-CE + Brier + Entropy Loss). DirectML FP16 TensorCore execution (~23.08ms). Pure tensor classification, zero generative token overhead, no `lm_head`.
3. **Invar**: System-2 execution and verification. AST parsing, DualTrack Comparator, IDOR differential testing, Bounded symbolic execution, and future Cost-Aware GRPO.

---

## 2. Current Mission

[DECISION]
Transition from the completed System-1 model distillation/training phase into the **Invar System-2 dynamic execution and vulnerability verification phase**, leveraging the high-recall DualTrack triage outputs (`triage_pools_v2.json`, Pool A + Pool B) to execute targeted differential security testing without drowning in false alarms.

---

## 3. Current Objective

[FACT]
- Phase 1 (Forensic Audit & Firewall): **DONE**.
- Phase 2 (Contract Repair & Comparator Hash Sealing): **DONE**.
- Phase 3 (API Distillation & SFT Model Ignition & Gold Set Verification): **DONE WITH DISTINCTION**.
  - High-risk recall leaped from 0.0% to 80.00% (and 100% in Pool B).
  - Evaluator upgraded to `evaluate_gold_set_v4.py` (Average Precision AP=0.5425, Bootstrap 95% CI, Dual-Track Ensemble).

**CURRENT OBJECTIVE**:
正式将工程主战场由 `distiller` / `base-jev` 移交至 `C:\dev\Invar`。开发下游消费端逻辑：让 Invar 根据 `triage_pools_v2.json` 中的高危端点（Pool A 规则选出 + Pool B 模型捕获），基于其 Impact/Sensitivity 双正交特征自动装配测试用例（IDOR 越权 vs 未授权状态篡改），发起真实的差分验证发包。

---

## 4. Next Single Action

**CURRENT OBJECTIVE → NEXT SINGLE ACTION**

**当前唯一下一动作：**
在 `C:\dev\Invar` 中审查并重构下游执行接盘脚本（如 `scripts/pipeline/build_targets.py` 或测试任务调度器），实现对 `tmp/triage_phase1_output/triage_pools_v2.json` 中高危端点（Pool A + Pool B 共约 78 个核心靶心）的结构化加载，根据其语义标签分流生成待测任务清单（`ResearchTask`）。

---

## 5. Current Scope

**当前正在修改/研究的：**
* `Invar/scripts/pipeline/*` 或 `Invar/scripts/asset/*`（下游高危端点任务装配与策略分流）
* `Invar/tmp/triage_phase1_output/triage_pools_v2.json`（已生成的高危资产输入）
* `Invar/tmp/gold_set_eval_report_v4.json`（已固化的学术评测基准）

---

## 6. Out of Scope

**当前阶段明确禁止触碰：**
* ❌ 重新启动 `base-jev` 模型训练或修改已发布的 `system_one_unified.onnx`（出厂护照已锁定，严禁非必要重训）。
* ❌ 修改 `distiller` 蒸馏脚本（双轨蒸馏已全量落盘，数据车间已交付封箱）。
* ❌ 在 `base-jev` 引入自回归文本生成或 GRPO（范畴谬误，属于 Invar System-2）。
* ❌ 破坏 `Train ∩ Gold = ∅` 物理防火墙。
* ❌ 删除历史 `gold_replay_buffer_60.jsonl`（已物理封存进 `archive_legacy/` 作为物证，严禁删除）。

---

## 7. Last Known Good State

[FACT — snapshot]
* **Date**: 2026-09-22
* **Action**: Ran `evaluate_gold_set_v4.py` on 60 Gold Cards.
* **Audit & Evaluation Results**:
  - `system_one_unified.onnx` (SHA256: `908db8140ab2...`, 1251.11 MB)
  - `base-jev-qa` hardware benchmark: steady latency **23.08 ms** on RTX 3060 DirectML, Probability sum = 0.9995.
  - Model Passport: `dist/invar-intent-0.6b-v1/MODEL_PASSPORT.json` signed.
  - Prediction alignment: 1221/1221 1:1 aligned, 7 oversize fallbacks cleanly isolated.
  - Gold Set Evaluator (v4.0 Academic Suite):
    - Rule: TP=5, FP=14, FN=5, TN=36 (Recall 50.0%, Precision 26.32%, F1 0.3448, Cost 64.0)
    - Neural: TP=8, FP=14, FN=2, TN=36 (Recall 80.0%, Precision 36.36%, F1 0.5000, Cost 34.0)
    - Dual-Track Ensemble (Rule ∪ Neural): **TP=10/10, FN=0 (Recall 100.0% 零漏报!)**, Cost 22.0 (最低)
    - Pool B (Rule Blind Zone): **Neural TP=5/5, Recall 100.0%, Precision 62.50%, F1 0.7692**
    - Average Precision (AP): **0.5425** (vs Dummy baseline 0.1667)
    - Bootstrap 95% CI: Recall `[50.0%, 100.0%]`, Precision `[15.8%, 55.6%]`, F1 `[0.2424, 0.6829]`

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| Distiller Gold Firewall | DONE | E3 VERIFIED (0 overlap) | `curator.py`, `run_distillation_pipeline.py` | 10 层表面拦截网，阻断全部 60 张黄金卡片。 |
| Evaluator Fail-Closed & Metrics Fix | DONE | E6 VERIFIED, 0/60 fallbacks | `evaluate_gold_set_v1.py` | 废除旧 380% 伪召回，未对齐立即熔断。 |
| Comparator Lineage Sealing | DONE | Manifest `neural_jsonl_sha256` | `triage_dual_track_comparator.py` | 补齐输入神经预测物理哈希封签，闭环 E5。 |
| Dual-Teacher Distillation | DONE | 500 samples each | `run_api_distillation_pipeline.py`, `run_local_distillation_pipeline.py` | 本地 27B (5.5h) + 云端 Gemini (Auth keys, 断点续传)。 |
| Dataset Asset Standardization | DONE | `data/API_distilled/`, `data/Local_distilled/` | `distiller/data/`, `base-jev/data/` | 历史污染文件归档至 `archive_legacy/`。 |
| Train-Serving Parity Fix | DONE | 100% Token Isomorphism | `generate_triage_predictions.py` | 注入 `host` 属性并将 Query 截断对齐为 `[:60]`。 |
| SFT High-Risk Ignition | DONE | Loss 6.33 -> 1.58, Brier 0.0061 | `train_factory_model.py` | 6 轮训练，吸收 27.1% High-Impact 强梯度。 |
| DirectML ONNX Export & QA | DONE | 23.08ms steady latency | `export_to_onnx.py`, `base-jev-qa` | 单文件 1.25 GB，出厂护照正式签发。 |
| Full 1221 Triage Prediction | DONE | 1221/1221 aligned | `base_jev_predictions_1221.jsonl` | 7 超长异常安全降级，平均推理耗时 195ms。 |
| Gold Set Breakthrough | DONE | Recall 80% (Pool B 100%) | `gold_set_eval_report.json` | 彻底粉碎均值塌陷，高危召回率从 0% 暴涨至 80%。 |
| Academic Evaluation Suite v4.0 | DONE | AP=0.5425, Bootstrap CI | `evaluate_gold_set_v4.py` | 验证双轨协同达成 10/10 零漏报，防御代价降 65.6%。 |

---

## 9. Changed Files

### Added
* `distiller/scripts/pipeline/run_api_distillation_pipeline.py` (Gemini 3-Key 轮询与实时断点续传)
* `distiller/scripts/pipeline/run_local_distillation_pipeline.py` (本地 27B 单流守护断点续传)
* `base-jev/scripts/audit/inspect_train_and_pred_distribution.py` (训练集与预测分布显微镜)
* `base-jev/scripts/audit/compare_distilled_teachers.py` (双师共识度量对比脚本)
* `Invar/scripts/audit/evaluate_gold_set_pro.py` (多维学术全阈值评测引擎)
* `Invar/scripts/audit/evaluate_gold_set_v4.py` (v4.0 顶会终审标准套件，含 AP、CI、双轨协同)
* `distiller/data/API_distilled/*` (400 train, 100 eval)
* `distiller/data/Local_distilled/*` (400 train, 100 eval)
* `base-jev/data/API_distilled/*` (400 train, 100 eval)
* `base-jev/data/Local_distilled/*` (400 train, 100 eval)
* `base-jev/data/archive_legacy/*` (封存历史污染与废弃数据)

### Modified
* `Invar/scripts/asset/triage_dual_track_comparator.py` (计算并写入 `neural_jsonl_sha256`)
* `Invar/scripts/audit/evaluate_gold_set_v1.py` (升级为 Fail-Closed 与标准混淆矩阵)
* `base-jev/scripts/pipeline/generate_triage_predictions.py` (补齐 `host` 属性与 `[:60]` 契约同构)
* `base-jev/recipes/recipe_invar_0.6b.json` (指向 `data/API_distilled/`，Epochs=6)
* `base-jev/scripts/audit/audit_experiment_lineage_v1.py` (修复 E5 动态哈希断言逻辑)

---

## 10. Current Architecture

[DECISION]
**Triad Industrial Dual-Engine Architecture:**
```text
[distiller Workshop]
   ├─ Local 27B Teacher (Qwen3.8-27B-Uncensored at 127.0.0.1:8080)
   └─ Cloud Frontier Teacher (Gemini 3.8/3.5 Flash Auth Keys)
           │
           ▼ (Prometheus 2 Likert + Maximum Entropy Projection)
[DualScore Dataset (Train 400 / Eval 100)]
   │ 🛡️ 10-Layer Gold Firewall (Zero Contamination: Train ∩ Gold = ∅)
   ▼
[base-jev Model Factory]
   ├─ Qwen3-0.6B-Base Backbone (lm_head physically stripped)
   ├─ LoRA Adaptor (r=16, alpha=32) + Unified Dual-Heads (Impact & Sensitivity)
   ├─ Joint Calibrated RLCD Loss (Soft-CE + Brier + Ambiguity Entropy)
   └─ Single-File ONNX Compiler -> DirectML TensorCore Runtime (23.08ms, 1.25GB)
           │
           ▼ (generate_triage_predictions.py - 1221 Endpoints)
[base_jev_predictions_1221.jsonl]
           │
           ▼
[Invar DualTrack Comparator]
   ├─ Rule Profile (Regex / Tags / Keywords)
   └─ Neural Profile (Impact / Sensitivity Scores & Probabilities)
           │
           ▼ (triage_pools_v2.json: Pool A 48 + Pool B 30 + Pool C 30)
[Invar System-2 Execution Engine] (★ NEXT ACTIVE FOCUS)
   ├─ Targeted Vulnerability Dispatch (IDOR vs Unauthorized Overwrite)
   ├─ Adaptive Sandbox & Differential Packet Fuzzing
   └─ FindingRecord -> KnowledgeCard Verification
```

---

## 11. Architecture Decisions

### AD-01 — Strict Gold Set Isolation (Zero-Contamination Boundary)
* **Decision**: 60 张黄金卡片严禁流入训练集或重放缓冲区。
* **Why**: 保证评估结果具备学术级与工业级外推真实性。
* **Evidence**: E3 审计确认：Surface Overlap = 0，Route Overlap = 0。

### AD-02 — base-jev is Pure Discriminative SFT (No Token Generation)
* **Decision**: 剔除 `lm_head`，直接外挂分类投影头，输出后验概率张量。
* **Why**: 极速感知传感器（23ms vs 大模型数十秒），杜绝自回归幻觉，节省 1GB+ 显存死重。

### AD-03 — Train-Serving Parity is Mandatory
* **Decision**: 训练与推理必须保证 `TypedStateSnapshot` 序列打包 100% 同构。
* **Why**: 缺少 `host` 属性会导致前向注意力位置偏移，削弱特征识别。

### AD-04 — Dual-Track Ensemble (Rule ∪ Neural) for Zero Misses
* **Decision**: 线上分流采取“规则报警 OR 神经网络报警”并集策略。
* **Why**: 规则擅长确定性字面语法（Pool A 100%），神经网络擅长复杂代码语义（Pool B 100%）。两者盲区完全正交，并集实现 10/10 真实高危零漏报，防御综合成本降低 65.6%。

---

## 12. Data / API / Type Contracts

* **DualScore Target Schema (`contracts.py`)**:
  ```python
  class ScoreDimensionTarget(BaseModel):
      model_config = ConfigDict(extra="forbid")
      distribution: List[float] = Field(description="5档归一化后验概率分布 (和恒为1.0)")
      expected_score: float = Field(description="精确代数加权期望值 sum(m*p)")
  ```
* **Surface ID Formula**:
  $$\text{surface\_id} = \text{SHA256}(\text{METHOD} \parallel \text{HOST} \parallel \text{NORMALIZED\_PATH})[:24]$$
* **Model Passport (`MODEL_PASSPORT.json`)**:
  - `model_uuid`: `uuid-908db8140ab2`
  - `sha256`: `908db8140ab25a32...`
  - `steady_latency_ms`: `23.080639`
  - `clean_accuracy`: `0.8419`
  - `brier_score`: `0.0061`

---

## 13. Verified Tests

| Test / Script | Purpose | Protected Invariant | Result |
|---|---|---|---|
| `base-jev-qa` | Rust 原生硬件质检 | 3 大生死红线 (延迟<=45ms, 概率和=1.0, 分值[1,5]) | Passed (23.08ms, Sum=0.9995, Exp=3.65) |
| `audit_experiment_lineage_v1.py` | E1~E8 司法取证审计 | 零污染、逐行对齐、密码学血缘封签 | E1, E2, E3, E4, E5, E6, E7 VERIFIED |
| `evaluate_gold_set_v4.py` | v4.0 顶会多维评测 | AP 离散积分、Bootstrap 95% CI、双轨协同 | Passed (AP=0.5425, Ensemble 10/10 零漏报) |
| `py_compile` | 语法无损校验 | 杜绝 f-string 转义与贪婪正则语法错误 | Passed 100% |

---

## 14. Failure / Pitfall Registry

* **Problem**: 方案 A 训练的模型在黄金集全军覆没 ($Recall=0.0\%$, $TP=0$)。
  * **Root Cause**: 方案 A 使用干跑模拟数据，标签均值塌陷至 2.33。模型学到了投机捷径（一律输出 2.31），不敢跨过 3.5 报警门槛。
  * **Correct Fix**: 切换至方案 B（真实大模型因果蒸馏），注入 27.1% High-Impact / 29.4% High-Sensitivity 强梯度，并在推理端补齐 `host` 属性同构对齐。
  * **Result**: 召回率直接暴涨至 **80.00%**，Pool B 召回率 **100.0%**。
* **Problem**: Google API 503 与 429 报错崩溃。
  * **Root Cause**: Google 免费层对 429 实行 60 秒滚动窗口，脚本仅休眠 5 秒且连试 6 次导致异常熔断；503 是云端突发高峰。
  * **Correct Fix**: 引入实时断点续传（`CheckpointManager`，单条 flush）、指数退避、并建立多 Key / 多模型平滑轮换。
* **Problem**: Python f-string 嵌套引号报 `SyntaxError`。
  * **Root Cause**: 在 `{...}` 表达式内使用带反斜杠转义的字典索引。
  * **Correct Fix**: 预先将待打印字段格式化为独立变量，前置执行 `py_compile`。

---

## 15. Do Not Repeat

* ❌ 严禁再次使用未经验证的干跑模拟数据进行 SFT 微调。
* ❌ 严禁在只有 12GB 显存的同一块 GPU 上并发启动 27B 教师推演与 0.6B SFT 训练（必 OOM）。
* ❌ 严禁在评测脚本中使用单一准确率（Accuracy=73.33%）自我蒙蔽，必须依赖 PR-AUC、AP、F2-Score。
* ❌ 严禁在评估器中进行静默 3.0 兜底，必须保持 Fail-Closed 熔断。

---

## 16. Invariants

* **I-01**: `TRAIN ∩ GOLD = ∅` (Surface 重叠必须恒等于 0)。
* **I-02**: `len(predictions) == len(endpoints)` (1221/1221 1:1 逐行对齐)。
* **I-03**: `base-jev` 属于 System-1 快速传感器，输出纯张量，不输出自回归 Token。
* **I-04**: 评测未匹配卡片必须 Fail-Fast 阻断，严禁静默默认分。

---

## 17. Open Issues

* **Issue**: E8 AST Evidence Context Purity 存在历史上下文窗口。
  * **Impact**: Gold Set 证据切片包含 +-40 行物理窗口，存在少许邻居上下文噪音。
  * **Next Verification**: 在后续 Invar 语法分析器重构时，全面推进纯 AST 封闭作用域提取（Phase 5）。

---

## 18. Environment / Toolchain

* **OS**: Windows 11
* **Shell**: PowerShell
* **Python Runtime**: Python 3.12 (managed via `uv`)
* **Rust Toolchain**: Cargo 1.80+ (2021 edition)
* **Compute Hardware**: NVIDIA GeForce RTX 3060 (12GB VRAM)
* **Acceleration**: DirectML (Direct3D 12) + CUDA 12.4

---

## 19. Roadmap

* **Phase 0**: 实验法医取证 (DONE)
* **Phase 1**: 防火墙与纯净数据集闭环 (DONE)
* **Phase 2**: 比较器哈希封签与评估器 Fail-Closed 重构 (DONE)
* **Phase 3**: 方案 B 真实大模型蒸馏 + SFT 点火 + 80% 召回率破局 (DONE)
* **Phase 4**: 双师一致性融合消融研究 (Optional / Backlog)
* **Phase 5**: **Invar System-2 动态执行与差分漏洞验证 (CURRENT ACTIVE PHASE)**

---

## 20. Recovery Protocol

新 AI 接管会话后，严格按照以下步骤恢复上下文：
1. 阅读本 `c/HANDOFF.md`，确认版本为 v6.0.0。
2. 确认 `distiller` 和 `base-jev` 的模型与数据已完成物理交付（`models/system_one_unified.onnx`、`dist/invar-intent-0.6b-v1/MODEL_PASSPORT.json` 已锁定）。
3. 确认高危资产池已就绪：`Invar/tmp/triage_phase1_output/triage_pools_v2.json`。
4. **将工作目录切换至 `C:\dev\Invar`**，锁定 CURRENT OBJECTIVE（开发 Invar System-2 动态测试与差分验证执行逻辑）。
5. 严禁无故重训模型或修改上游数据。

---

## 21. AI Collaboration Protocol

* 中文优先。
* 一次只推进一个明确的工程动作。
* 代码修改使用 PowerShell `@' ... '@ | Set-Content -Encoding UTF8` 格式完整原样落盘。
* 严禁静默兜底，遇到不匹配必须 Fail-Fast。
* 遵循系统宪法：根因 > 补丁，契约 > 约定，抽象 > 特判。

---

## 22. Reproducibility Status

**FULLY REPRODUCIBLE**
模型权重、ONNX 静态图、出厂护照、预测 JSONL、比较器清单与评测脚本均具备密码学哈希对齐链条。环境与运行命令具备 100% 确定性。

---

## 23. Handoff Self-Check

* [x] 新 AI 是否知道当前在做什么？（知道：主战场已转移至 Invar System-2 动态执行与漏洞实战挖掘）。
* [x] 新 AI 是否知道最后一次成功状态？（知道：0.6B 模型召回率 80.00%，双轨协同召回率 100.0%）。
* [x] 新 AI 是否知道为什么之前是 0% 而现在是 80%？（知道：均值塌陷被真实因果蒸馏标签打破）。
* [x] 新 AI 是否知道当前不能做什么？（知道：禁止重训模型、禁止重跑蒸馏、禁止触碰防火墙）。
* [x] 新 AI 是否知道唯一下一步？（知道：在 Invar 侧开发对 `triage_pools_v2.json` 的动态用例装配逻辑）。
