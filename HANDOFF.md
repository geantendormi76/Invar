# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot / Recovery Contract  
> **Project:** Invar  
> **Snapshot Date:** 2026-10-03 (Asia/Tokyo)  
> **Canonical Repository Root:** `/home/zhz/Invar` (Linux Mint 22.3 Cinnamon)  
> **Canonical Handoff Path:** `/home/zhz/Invar/HANDOFF.md`  
> **Snapshot Authority:** 真实终端执行日志、`uv` 环境状态、`dmesg` 内核日志排查记录、阶段 1~7 真实落盘产物。

---

## 0. Handoff Metadata

| Item | Value | Level | Evidence |
|---|---|---|---|
| Project | Invar | [FACT] | `pyproject.toml`, `Cargo.toml` |
| Repository Root | `/home/zhz/Invar` | [FACT] | 终端执行输出路径 |
| Operating System | Linux Mint 22.3 Cinnamon (x86_64) | [FACT] | 终端环境上下文 |
| Hardware Profile | Intel Core i5-13600KF, 32GB RAM, NVIDIA GeForce RTX 3060 12GB | [FACT] | `free -h` 与 `nvidia-smi` 输出 |
| Current System Role | System-2 深度动态安全实证与漏洞研究 Harness 引擎 | [FACT] | 源码架构与黄金标准对齐 |
| Local LLM Runtime | `llama-server` on `http://127.0.0.1:8080/v1` (35B Model) | [FACT] | 端口探测与配置声明 |
| Active ONNX Providers | `CUDAExecutionProvider` (ONNX Runtime 1.19.2) | [FACT] | `tmp/test_cuda_preload.py` 验证输出 |
| Last Known Good State | Phase 7 完成，86 个靶向任务成功装配 | [FACT] | `artifacts/reports/targeted_research_tasks.json` |

---

## 1. Project Identity

[FACT]
Invar 是一套对标 Anthropic Reference Harness、Strix 与 Claude-Red 的工业级 AI 辅助安全研究与动态实证确权系统。
其核心哲学为：**AI 仅在有界权限内做决策，确定性核心负责物理执行与验真，双盲独立复核确权，最终生成 OASIS SARIF 2.1.0 与 OpenSSF OpenVEX 黄金战报。**

---

## 2. Current Mission

[DECISION]
构建端到端的 Bug Bounty / SRC 自动化实证流水线。
当前阶段的使命是：打通蓝图的下半场。消费已生成的 `Research Seed Inventory`（研究种子库），驱动 `AdaptiveSandboxExecutor` 进行真实发包，在遭遇 403/405 阻断时唤醒本地 35B LLM 进行受控决策（Action Selection），最终完成不变量评估并生成权威报告。

---

## 3. Current Objective

### CURRENT OBJECTIVE
[DECISION]
**正式启动阶段 8（System-2 自适应沙箱受控动态实证）。**
消费阶段 7 产出的 86 个高浓度靶向任务（`targeted_research_tasks.json`），在纯净的 CUDA 12 隔离环境下，驱动 `run_targeted_audit.py --control-plane --enable-llm` 跑通首次端到端闭环实证，获取第一份完整的 OpenVEX + SARIF 交付物。

---

## 4. Next Single Action

### NEXT SINGLE ACTION
[TODO]
在终端执行阶段 8 的启动脚本：加载 `tools/env_cuda.sh` 环境变量，运行 `uv run --project python python python/scripts/run_targeted_audit.py --tasks "artifacts/reports/targeted_research_tasks.json" --report-input "tmp/ikuai8.com_endpoints_report.json" --output-dir "artifacts/reports/targeted_audit_production" --priority ALL --enable-llm --control-plane --timeout 10`，并观察本地 LLM 的 CoT 决策与最终战报生成。

---

## 5. Current Scope

### CURRENT SCOPE
[DECISION]
- **模块**：`sandbox_executor.py`, `research_agent.py`, `research_controller.py`, `run_targeted_audit.py`
- **数据**：`artifacts/reports/targeted_research_tasks.json`
- **环境**：`tools/env_cuda.sh` 提供的纯净 CUDA 运行时。

---

## 6. Out of Scope

### OUT OF SCOPE
[DECISION]
- 重新执行阶段 1~7 的数据采集与静态分析（已固化）。
- 升级或修改 `onnxruntime-gpu` 版本（已锁定 1.19.2 以规避 GPF 段错误）。
- 修改 Rust `crates/core` 架构。
- 前端 UI 开发。
- 将 86 个任务一次性打包放入 LLM Prompt（严禁，必须由沙箱逐个调度）。

---

## 7. Last Known Good State

### Last Known Good State
```text
Date: 2026-10-02 23:16 JST
    ↓
Phase 7: assemble_triage_tasks.py
    ↓
86 tasks assembled (9 P1, 54 P2, 23 P3)
    ↓
CUDAExecutionProvider successfully activated (0 Segfaults)
    ↓
artifacts/reports/targeted_research_tasks.json successfully written
```

---

## 8. Completed Work

| Item | Status | Evidence | Files | Notes |
| ---- | ------ | -------- | ----- | ----- |
| Phase 0-3: 资产采集与 JS 下载 | DONE | `tmp/raw_js/` 包含 217 个文件 | `download_javascript.py` | 物理文件已落地 |
| Phase 4: AST 契约提炼 | DONE | `tmp/ikuai8.com_endpoints_report.json` | `scan_pipeline.py` | 提炼 1097 个端点 |
| Linux CUDA 隔离与自愈 | DONE | `tmp/test_cuda_preload.py` 输出成功 | `pyproject.toml`, `env_cuda.sh` | 解决跨项目库污染导致的 GPF |
| Phase 5: System-1 神经推演 | DONE | `tmp/ikuai8.com_predictions.jsonl` | `predict_triage_onnx.py` | 1097 行 1:1 对齐，耗时 34s |
| Phase 6: 双轨比对融合 | DONE | `triage_pools_v2.json` | `triage_dual_track_comparator.py` | 融合出 56 个 Pool A, 30 个 Pool B |
| Phase 7: 靶向任务装配 | DONE | `targeted_research_tasks.json` | `assemble_triage_tasks.py` | 生成 86 个高浓度种子任务 |

---

## 9. Changed Files

### Modified
- `python/pyproject.toml`: 锁定 `onnxruntime-gpu==1.19.2`，移除冗余的 PyTorch 依赖，添加 `nvidia-*-cu12` 核心库。
- `python/scripts/predict_triage_onnx.py`: 注入 `ensure_cuda_libraries()` 运行时自愈函数，使用 `ctypes.CDLL` 显式注册 CUDA 库。

### Added
- `tools/env_cuda.sh`: 纯净的 CUDA 环境变量装载脚本，彻底切断与其他项目（如 Base-Jev）的 `LD_LIBRARY_PATH` 串线。

### Structure
- `data/targets/ikuai8.com/`: 存放被动采集与存活探测底账。
- `tmp/raw_js/`: 存放前端源码。
- `artifacts/reports/`: 存放双轨比对产物与装配任务。

---

## 10. Current Architecture

[FACT]
```text
[Phase 1-3: 外部工具采集] -> subdomains, live_hosts, raw_js
       ↓
[Phase 4: AST 提取] -> endpoints_report.json (1097 个)
       ↓
[Phase 5: System-1 ONNX 推演] -> predictions.jsonl (CUDA 加速)
       ↓
[Phase 6: 双轨比对] -> triage_pools_v2.json (Pool A ∪ Pool B)
       ↓
[Phase 7: 任务装配] -> targeted_research_tasks.json (86 个种子)
       ↓
[Phase 8: System-2 沙箱实证] -> (当前阶段) 逐个调度 -> 物理发包 -> LLM 决策 -> 证据链 -> SARIF/OpenVEX
```

---

## 11. Architecture Decisions

### Decision: 显式注册 CUDA 库与环境绝对隔离
**Why**: Linux 下 `onnxruntime-gpu` 懒加载机制与跨项目 `LD_LIBRARY_PATH` 污染会导致严重的 General Protection Fault (GPF) 段错误。
**Alternatives rejected**: 依赖系统全局安装 CUDA（污染宿主机）、使用 `onnxruntime-gpu>=1.27`（需要 CUDA 13，与本地 cu12 拓扑不符）。
**Evidence**: `dmesg` 内核日志显示 `libonnxruntime.so` 发生 segfault；采用 `ctypes.CDLL(mode=RTLD_GLOBAL)` 预加载后 100% 稳定。
**Do not revert unless**: 迁移至完全隔离的 Docker 容器或升级全局 CUDA 13 驱动。

### Decision: 拒绝将 86 个任务打包放入单次 LLM Prompt
**Why**: 漏洞实证是高度有状态的物理实验（发包->观测->变异）。LLM 无法在纯文本中维持微观代码逻辑的严密推演，会导致认知稀释与幻觉。
**Evidence**: 黄金标准（Anthropic/Strix）均采用单兵作战、各个击破的沙箱调度模式。
**Do not revert unless**: 出现具备原生 HTTP 发包与状态机维持能力的 Agentic LLM 底层 API。

---

## 12. Data / API / Type Contracts

### `TriageTask` (JSON Schema)
- **生产者**: `assemble_triage_tasks.py`
- **消费者**: `run_targeted_audit.py` -> `AdaptiveSandboxExecutor`
- **核心字段**: `task_id`, `endpoint_id`, `priority` (P0-P3), `hypothesis_id`, `method`, `path`。

### `ControlPlaneDecision`
- **约束**: `action` 必须为 `RUN_EXPERIMENT` 或 `STOP`。`target_id` 必须在候选列表中。严禁 LLM 自由伪造 HTTP 报文。

---

## 13. Algorithms / Workflow

### System-2 动态实证工作流 (Phase 8)
```text
Input (targeted_research_tasks.json)
  → 逐个任务进入 AdaptiveSandboxExecutor
  → Baseline Probe (基线探测)
  → Decision: 若 200 OK 且无软拒绝 -> 契约收敛，跳过
  → Decision: 若 403/405 阻断 -> 唤醒 ResearchAgent
  → Execution: 启发式变异发包
  → Observation: 捕获响应，SemanticEquivalenceEvaluator 识破假 200
  → Feedback: 状态反哺至 ResearchController
  → LLM CoT: 若启发式耗尽，唤醒 35B 模型进行反思决策
  → Next State: 确权 (VULNERABLE) 或 存疑 (INCONCLUSIVE)
  → Outputs: SARIF, OpenVEX, REPORT.md
```

---

## 14. Verified Tests

### `tmp/test_cuda_preload.py`
- **Purpose**: 验证 ONNX Runtime 是否能成功挂载 `CUDAExecutionProvider` 且不发生 GPF。
- **Behavior protected**: 确保 Python 进程的动态链接库环境纯净，`ctypes.CDLL` 预加载生效。
- **Result**: `[✓] 激活首选执行提供商: CUDAExecutionProvider`。

---

## 15. Failure / Pitfall Registry

### Problem: 终端执行 `uv sync` 或 ONNX 推理时直接崩溃闪退
- **Symptom**: 终端消失，`dmesg` 显示 `traps: python[...] general protection fault`。
- **Root Cause**: 环境变量 `LD_LIBRARY_PATH` 串线，加载了其他项目 (`Base-Jev`) 的动态库，导致 C++ ABI 错位与 CUDA 内存越界。
- **Wrong Approach**: 盲目升级 `onnxruntime-gpu` 到最新版（会导致索取 `libcublasLt.so.13` 再次报错）。
- **Correct Fix**: 清空全局 `LD_LIBRARY_PATH`，在 `pyproject.toml` 锁定 `onnxruntime-gpu==1.19.2`，使用 `tools/env_cuda.sh` 仅扫描当前项目的 `.venv`。
- **Future Prevention**: 严禁跨项目共享虚拟环境或全局环境变量。

---

## 16. Do Not Repeat

- **不要猜接口**：严格遵循 `EndpointIR` 与 `TriageTask` 的字段定义。
- **不要把 86 个任务打包扔给 LLM**：必须由沙箱逐个调度。
- **不要使用 `onnxruntime-gpu>=1.20`**：在当前 Python 3.12 + CUDA 12 环境下会导致 GPF。
- **不要在终端输出 `python -c` 单行命令**：所有探针必须写入 `tmp/` 独立脚本执行。

---

## 17. Invariants

- **目录边界**：`python/` 负责 AI/ML，`crates/` 负责底层引擎，严禁混淆。
- **环境隔离**：Python 依赖必须由 `uv` 管理，严禁使用系统 `pip`。
- **决策有界性**：LLM 动作空间严格受制于 `ResearchAction` 枚举。
- **审计不可篡改性**：SARIF 与 OpenVEX 必须由底层事实对象自动投影衍生。

---

## 18. Open Issues

### Issue: LLM Context Length & Stability during Phase 8
- **Impact**: 在连续处理 86 个任务时，本地 35B 模型是否会触发 `finish_reason=length` 或产生幻觉。
- **Current Evidence**: 尚未在全量 86 个任务上进行压力测试。
- **Next Verification**: 在阶段 8 运行过程中密切监控 `execution.jsonl` 中的 `llm_terminal_status`。

---

## 19. Environment / Toolchain

[FACT]
- **OS**: Linux Mint 22.3 Cinnamon (x86_64)
- **Language versions**: Python 3.12.3, Rust 2021, Node.js v24.21.0
- **Package manager**: `uv` (Python), `cargo` (Rust), `pnpm` (Node)
- **GPU**: NVIDIA GeForce RTX 3060 12GB
- **Important versions**: `onnxruntime-gpu==1.19.2`, CUDA 12
- **External services**: `llama-server` on `http://127.0.0.1:8080/v1` (35B Model)
- **Environment variables**: 必须 `source tools/env_cuda.sh`

---

## 20. Roadmap

- [x] Phase 1-4: 资产采集与 AST 提取
- [x] Phase 5-7: System-1 神经推演与靶向任务装配
- [ ] **Phase 8: System-2 自适应沙箱受控动态实证 (CURRENT OBJECTIVE)**
- [ ] Phase 9: 人工复核与漏洞提交
- [ ] Phase 10: 桌面端产品可视化呈现 (Tauri + React 19)

---

## 21. Recovery Protocol

新 AI 接手后，必须按以下步骤恢复：
1. 读取本 `HANDOFF.md`。
2. 验证 Last Known Good State：检查 `artifacts/reports/targeted_research_tasks.json` 是否存在且包含 86 个任务。
3. 验证环境：执行 `source tools/env_cuda.sh`。
4. 验证 CURRENT OBJECTIVE：准备执行阶段 8。
5. **只执行 NEXT SINGLE ACTION**：启动 `run_targeted_audit.py`。

---

## 22. AI Collaboration Protocol

- **中文优先**：技术解释使用中文，代码标识保留英文。
- **单步推进**：一次只推进一个逻辑动作。
- **极客交付**：代码修改使用 Bash 脚本落盘（`cat << 'EOF' > ...`），严禁要求用户手动复制粘贴。
- **用户反馈**：用户执行命令并反馈终端输出，AI 据此推进。

---

## 23. Security / Sensitive Data Boundary

- 本文档不包含真实 Token、密码或私钥。
- 目标端点使用已授权的 `ikuai8.com`。
- 若需注入凭据，请通过环境变量（如 `INVAR_AUTH_TOKEN`）传递，严禁硬编码。

---

## 24. Reproducibility Status

**FULLY REPRODUCIBLE**
核心接口、算法、环境（CUDA 隔离修复）、依赖（`uv` 锁定的 1.19.2）和前 7 个阶段的数据产物均已在 Linux Mint + RTX 3060 环境下物理确认并固化。

---

## 25. Handoff Self-Check

- [x] 一个新 AI 是否知道当前到底在做什么？ (准备执行阶段 8 动态实证)
- [x] 一个新 AI 是否知道最后一次成功状态？ (阶段 7 完成，86 个任务装配完毕，CUDA 修复)
- [x] 一个新 AI 是否知道最后修改了哪些文件？ (`pyproject.toml`, `env_cuda.sh`)
- [x] 一个新 AI 是否知道为什么这么设计？ (防止 GPF 段错误，防止 LLM 幻觉)
- [x] 一个新 AI 是否知道哪些行为不能破坏？ (CUDA 1.19.2 版本锁定，单任务调度机制)
- [x] 一个新 AI 是否知道当前唯一下一步？ (运行 `run_targeted_audit.py`)
- [x] 一个新 AI 是否知道当前阶段不能做什么？ (不能重构 Rust，不能改 UI)
- [x] 一个新 AI 是否知道如何运行测试？ (通过 `uv run pytest`)
- [x] 一个新 AI 是否知道哪些信息尚未确定？ (LLM 在 86 个任务下的长程稳定性)
- [x] 一个新 AI 是否能够在源码缺失部分情况下依据文档继续恢复？ (可以)
```
