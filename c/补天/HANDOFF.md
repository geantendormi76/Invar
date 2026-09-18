# 🛡️ AI Development Handoff Specification (AI 开发会话交接档案)

> **文档性质**：跨会话高纯度工程状态机快照与不可变基线规范
> **项目名称**：Invar
> **项目物理主根目录**：`C:\dev\Invar`
> **本档案物理落盘路径**：`C:\dev\Invar\c\HANDOFF.md`
> **档案建立时间**：2026-09-17 19:20 (UTC+8)
> **唯一目的**：当当前 AI 会话关闭、上下文丢失或原聊天记录不可访问时，全新接手的 AI 仅凭本档案 + 当前工程物理源码与测试，即可 100% 恢复当前状态机，杜绝重造轮子、杜绝推翻既定架构、杜绝重复历史错误。
> **事实分级声明**：本档案严格标注 `[FACT]`、`[DECISION]`、`[DERIVED]`、`[ASSUMPTION]`、`[UNKNOWN]`、`[TODO]`。

---

## 0. Handoff Metadata

| 属性 | 当前真实状态 | 事实等级 |
| :--- | :--- | :--- |
| **Project Name** | Invar (Symmetric Dual-Engine Platform) | `[FACT]` |
| **Physical Root** | `C:\dev\Invar` | `[FACT]` |
| **External Workspace** | `C:\dev\agent-workspace` (Pi Agent 独立调度主工作区) | `[FACT]` |
| **Handoff Timestamp** | 2026-09-17 19:20 | `[FACT]` |
| **Version Baseline** | Rust Crate `Invar-core 0.1.0` / Python Package `invar-engine 0.1.0` / Pi CLI `v0.85.1` | `[FACT]` |
| **Active Inference Endpoint** | `http://127.0.0.1:8080/v1` (OpenAI 兼容端点) | `[FACT]` |
| **Active Local Model** | `K2-Horizon-7B-Uno-Uncensored-IQ4_XS` (128K 满血上下文) | `[FACT]` |
| **Current Engine Stage** | **Phase I 闭环收口完成 ➔ 阶段 J (Invar Tool Contract Layer) 正式启动** | `[DECISION]` |

---

## 1. Project Identity

`[FACT]`
Invar 是一个基于**工业级 Monorepo 对称双引擎架构**（对齐 dmtrKovalenko/fff 哲学）的 API 逆向与闭环安全研究平台：

```text
┌─────────────────────────────────────────────────────────────┐
│ 外部交互与驱动马具: 官方 Pi Agent CLI (v0.85.1)            │
│ 运行路径: C:\dev\agent-workspace                            │
│ 物理大脑: 本地 K2-Horizon-7B (128K 上下文, llama-server)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ (通过 Invar Tool Contract / Skill 驱动)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   INVAR 核心中枢 (C:\dev\Invar)              │
│                                                             │
│  [Rust 引擎 (src-tauri/crates)]:                            │
│    - 系统编排 (Orchestrator)、进程守护、强类型任务契约      │
│                                                             │
│  [Python 引擎 (src-tauri/python - uv 3.11)]:                │
│    - Tree-sitter 静态 AST 提取 (EndpointIR)                 │
│    - 威胁量化评分 (RiskEngine)                              │
│    - 形式化假说推演与流转 (HypothesisEngine)                │
│    - 闭环自适应沙箱与变异探测 (AdaptiveSandboxExecutor)     │
│    - 安全底线检验 (InvariantEvaluator)                      │
│    - 证据链跟踪 (EvidenceRecord) 与知识晋级 (KnowledgeCard) │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Current Mission

`[DECISION]`
完成本地推理引擎（`llama-server`）与外部驱动马具（`Pi Agent`）的解耦标准化部署，建立 Invar 专属的**工具契约层（Tool Contract Layer / Skill 模式）**，使 Pi Agent 能够在命令行中以确定性的强类型工具调用方式，调度 Invar 的自动化逆向与漏洞检验流水线。

---

## 3. CURRENT OBJECTIVE

`[DECISION]`
**在 `C:\dev\agent-workspace\skills\invar\` 目录下建立并落盘 Invar 专属的 Tool Contract 技能规范（`SKILL.md`），封装 Invar 的核心 CLI 指令，并在 Pi Agent 终端中跑通首次自主安全逆向与扫描联调。**

---

## 4. NEXT SINGLE ACTION

`[DECISION]`
**下一次接手 AI 只能执行且必须严格执行这唯一一个动作：**

> **在 `C:\dev\agent-workspace\skills\invar\SKILL.md` 写入面向 Pi Agent 的标准 Invar 技能契约规范文件，指导大模型以纯净命令行参数调用 `scripts/pipeline/scan_pipeline.py`。**

不得在执行完该动作并得到用户反馈前提前开始编写复杂扩展插件或修改 Rust/Python 内部实现。

---

## 5. Current Scope

*   `C:\dev\agent-workspace\skills\invar\SKILL.md`（新建技能元规范）
*   `C:\dev\Invar\scripts\pipeline\scan_pipeline.py`（输入输出契约调用验证）
*   Pi Agent 终端调用交互验证（通过 `/skill:invar` 或自然语言自动路由）

---

## 6. Out of Scope

当前阶段严厉禁止以下行为（任务漂移红线）：
*   ❌ 禁止重构 Invar 现有的 Rust/Python 核心模型（`EndpointIR`, `ResearchCase`, `EvidenceRecord` 等）。
*   ❌ 禁止在 Invar 内部重新引入 LLM Provider 或内置 Agent 运行时（严格捍卫 AD-01 决策）。
*   ❌ 禁止修改 `C:\Users\52484\.pi\agent\` 下已经点火成功的 `models.json` 和 `settings.json`。
*   ❌ 禁止引入复杂的第三方网络搜索或重型 IDE 插件。

---

## 7. Last Known Good State

`[FACT]` **于 2026-09-17 19:15 物理实测确认的黄金基准**：

1.  **推理底座（llama-server）**：
    *   启动命令：`& "C:\dev\agent-workspace\scripts\start_k2.ps1"`
    *   二进制：`C:\dev\bin\llama_k2\llama-server.exe`
    *   模型物理权重：`C:\Users\52484\.pi\agent\models\K2-Horizon-7B-Uno-Uncensored-GGUF\K2-Horizon-7B-Uno-Uncensored-IQ4_XS.gguf`
    *   端口状态：`127.0.0.1:8080` 监听正常，HTTP 200 流式接口就绪。
2.  **Pi Agent 终端（Pi CLI）**：
    *   版本：`pi v0.85.1`
    *   全局配置：`C:\Users\52484\.pi\agent\models.json` 与 `settings.json` 纯净初始化完成。
    *   运行状态：终端成功启动并打印：
        `↑1.3k ↓170 1.1%/128k (auto) K2-Horizon-7B-Uno-Uncensored-IQ4_XS`
    *   实测问答：向其提问“你是 谁？”，模型完整输出内部思维链并准确流式返回中文回答，128K 上下文完全激活，0 报错。
3.  **资产与扫描基线（Invar Core）**：
    *   已在真实目标（`ikuai8.com`）完成全链路：Subfinder (99) ➔ HTTPX (37 live) ➔ Katana (209 JS) ➔ JS 下载 (209/209) ➔ AST 扫描 (1221 API 节点, 300 参数接口)。

---

## 8. Completed Work

| Item | Status | Evidence | Files / Directories | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Invar 内部错误 Agent 清除** | `DONE` | 用户终端确认物理删除 | `src-tauri/python/src/agent/model_provider.py`, `research_agent.py` | 彻底拔除内置 Agent 冗余，收敛架构 |
| **四大主流 Agent 选型评测** | `DONE` | 形成深度横向评测报告 | 对比 Codex, Pi, Hermes, OMP | 明确选定 Pi Agent 作为外部极简马具 |
| **Pi 全局环境纯净重置** | `DONE` | `Test-Path $env:USERPROFILE\.pi` 返回 False 后重建 | `C:\Users\52484\.pi.legacy_bak` | 旧二开污染与残留完全隔离归档 |
| **辅助二进制防超时还原** | `DONE` | 文件大小 4008KB/4120KB 准确无误 | `C:\Users\52484\.pi\agent\bin\fd.exe`, `rg.exe` | 解决冷启动因 GitHub 访问超时问题 |
| **独立工作区目录初始化** | `DONE` | 物理目录生成完毕 | `C:\dev\agent-workspace\` | 恪守目录契约边界，不污染 Invar 根目录 |
| **K2-Horizon-7B 点火配置** | `DONE` | 端口 8080 通信成功 | `C:\dev\agent-workspace\scripts\start_k2.ps1` | 99 层全 GPU 卸载，128K 上下文，Q4_0 KV 量化 |
| **Pi CLI 官方标准注册** | `DONE` | Pi 终端完整打印 128K 与模型名 | `C:\Users\52484\.pi\agent\models.json`, `settings.json` | 官方标准配置落地，零告警 |
| **首次端到端流式对话测试** | `DONE` | 终端 TUI 渲染正常，思维链可见 | 终端实测截图证据链 | 输入仅占 1.3k，为业务留足 126K 上下文 |

---

## 9. Changed Files

### Added (本次新增/建立)
*   `C:\dev\agent-workspace\configs\`
*   `C:\dev\agent-workspace\scripts\start_k2.ps1`
*   `C:\dev\agent-workspace\skills\`
*   `C:\Users\52484\.pi\agent\models.json`
*   `C:\Users\52484\.pi\agent\settings.json`
*   `C:\Users\52484\.pi\agent\bin\fd.exe` (还原)
*   `C:\Users\52484\.pi\agent\bin\rg.exe` (还原)

### Moved / Renamed (安全归档)
*   `C:\Users\52484\.pi` ➔ `C:\Users\52484\.pi.legacy_bak`

### Deleted (此前清理)
*   `C:\dev\Invar\src-tauri\python\src\agent\model_provider.py`
*   `C:\dev\Invar\src-tauri\python\src\agent\research_agent.py`

---

## 10. Architecture Decisions

### AD-01：Pi Agent 与 Invar 必须保持“调用方与工具提供方”的物理单向解耦
*   **Decision**：Pi Agent 是顶层大脑与交互马具；Invar 是底层专业计算与安全研究引擎。Pi 运行在 `C:\dev\agent-workspace`，通过 Tool Contract / CLI 调度 Invar。
*   **Why**：防止外部通用工具（如联网抓取、文件操作）污染 Invar 的 Monorepo 结构；防止 Invar 内部重复制造脆弱的 Agent 运行时。
*   **Do not revert unless**：出现官方规范证明 Invar 应当承担多工具 Agent 宿主职责。

### AD-02：本地 GGUF 推理采用“单一端口、轮转点火”（Single-Port Profile Rotator）
*   **Decision**：固定 `http://127.0.0.1:8080/v1` 为统一服务端口。模型调度通过独立 PowerShell 脚本管理。
*   **Why**：RTX 3060 12GB 物理显存受限（27B 占用 12GB，8B 占用 7GB），无法同时并存多个进程。统一端口可使 Pi 配置文件（`models.json`）保持不可变，无需频繁改动端口。

### AD-03：系统提示词最小化（Minimal Harness Overhead）
*   **Decision**：严禁在 Agent 框架层堆砌重型提示词与几十个无用工具定义。
*   **Why**：确保本地开源模型（如 7B/8B/27B）宝贵的注意力不被稀释，输入上下文开销压低至 1.3K 左右，显存占用与 KV 缓存最小化。

---

## 11. Data / API / Type Contracts

### 11.1 Pi Agent `models.json` 契约
```json
{
  "providers": {
    "local-llama": {
      "baseUrl": "http://127.0.0.1:8080/v1",
      "api": "openai-completions",
      "apiKey": "sk-local-dev-key",
      "models": [
        {
          "id": "K2-Horizon-7B-Uno-Uncensored-IQ4_XS",
          "name": "K2-Horizon-7B-Uno-Uncensored (128K 满血无审查)",
          "contextWindow": 128000,
          "maxTokens": 4096
        }
      ]
    }
  }
}
```

### 11.2 Invar 核心扫描流水线 CLI 契约
```powershell
uv run `
    --project "C:\dev\Invar\src-tauri\python" `
    --python 3.11 `
    python "C:\dev\Invar\scripts\pipeline\scan_pipeline.py" `
    "<target_js_dir_or_file>" `
    -o "<output_json_path>" `
    [--probe] `
    [--base-url "<api_gateway_url>"]
```

---

## 12. Verified Tests

*   `Test-NetConnection -ComputerName 127.0.0.1 -Port 8080` ➔ `Listening: True`
*   `pi` 首次交互测试 ➔ `↑1.3k ↓170 1.1%/128k (auto) K2-Horizon-7B-Uno-Uncensored-IQ4_XS`，完整推理并输出中文，流式无卡顿。
*   `test_ingest_subdomains.py` ➔ 8/8 通过。
*   `test_ingest_httpx.py` ➔ 2/2 通过。

---

## 13. Failure / Pitfall Registry

### F-01：清空旧目录后 Pi 启动因 GitHub 网络超时报警
*   **Symptom**：`Warning: Failed to download fd/ripgrep: The operation was aborted due to timeout`。
*   **Root Cause**：Pi 首次冷启动需要 `fd.exe` 与 `rg.exe`，默认从 GitHub Release 拉取，国内直连超时。
*   **Correct Fix**：从备份 `C:\Users\52484\.pi.legacy_bak\agent\bin` 中直接物理拷贝还原这两个二进制文件，彻底杜绝外网依赖。

### F-02：模型自称为“Claude”的表象误解
*   **Symptom**：提问“你是谁”，本地 K2-Horizon 模型回答“我是 Claude，由 Anthropic 构建”。
*   **Root Cause**：Pi Agent 的内置底层系统引导词设定了“You are Claude... operating inside pi”，本地模型严格遵循了 Prompt。
*   **Correct Fix**：无需误判为被云端劫持，属于高指令遵循度正常表现；后续可通过自定义 `SKILL` 或覆写 `system-prompt.md` 注入真实主体定义。

---

## 14. Do Not Repeat (绝对禁止复发红线)

*   ❌ **绝对禁止在 `C:\dev\Invar` 根目录里乱放 Pi Agent 的全局运行配置或下载脚本**（职责边界隔离）。
*   ❌ **绝对禁止使用 pip 和裸 python 执行任何 Python 脚本**，必须且只能使用 `uv run --project "C:\dev\Invar\src-tauri\python" --python 3.11`。
*   ❌ **绝对禁止在当前多模型单卡（12GB）环境下同时运行两个 `llama-server` 进程**。
*   ❌ **绝对禁止遇到配置告警就盲目执行 `npm uninstall -g` 重新下载**，必须以真实根因排查为准。

---

## 15. Invariants (工程不可变约束)

*   **I-01 物理路径不变性**：Invar 物理根目录严格为 `C:\dev\Invar`；Pi 工作区严格为 `C:\dev\agent-workspace`。
*   **I-02 接口统一性**：本地模型推理服务统一在 `http://127.0.0.1:8080/v1` 提供，上层工具无感复用。
*   **I-03 单步协作法则**：一次只推进一个明确的技术动作，测试通过后方可推进下一步。

---

## 16. Roadmap

*   [x] **Phase I：工程整理、反模式代码收口与稳定基线固化**
*   [x] **Phase GGUF：本地多模型调度中台与 K2-Horizon-7B 点火**
*   [x] **Phase Pi：官方标准 Pi Agent CLI 安装、配置与握手验证**
*   [ ] **Phase J：Invar Tool Contract Layer（Skill 封装与双向闭环调度）** ◄── **当前所处阶段**
*   [ ] **Phase K：复杂多目标逆向实战与端到端自动化挖掘演练**

---

## 17. Recovery Protocol (新会话恢复执行协议)

全新 AI 接手本工程后，必须严格按照以下步骤顺序恢复：

```text
步骤 1：完整通读本文件 C:\dev\Invar\c\HANDOFF.md；
步骤 2：检查推理端口是否保持活跃：
        Test-NetConnection -ComputerName 127.0.0.1 -Port 8080 -InformationLevel Quiet
        若为 False，告知用户执行：& "C:\dev\agent-workspace\scripts\start_k2.ps1"；
步骤 3：确认 CURRENT OBJECTIVE 与 NEXT SINGLE ACTION；
步骤 4：严格按照单步工程协作模式，推进 Phase J：编写 C:\dev\agent-workspace\skills\invar\SKILL.md；
步骤 5：禁止任何架构越界重构。
```

---

## 18. AI Collaboration Protocol

*   **语言习惯**：中文优先。代码对象与真实路径保留英文。
*   **代码交付**：Windows 环境下，大段脚本与代码优先使用 PowerShell `@' ... '@ | Set-Content -Encoding UTF8` 交付落盘。
*   **协作节奏**：一次给出一个明确指令，等待用户执行并反馈真实终端输出后，再分析并推进下一步。

---

## 19. Reproducibility Status

```text
╔════════════════════════════════════════════════════════════════╗
║                STATUS: FULLY REPRODUCIBLE                      ║
╚════════════════════════════════════════════════════════════════╝
证明依据：
1. 本地 GGUF 推理服务 (128K K2-Horizon) 与点火脚本已物理固化且验证通过；
2. 官方 Pi Agent CLI v0.85.1 纯净初始化配置已落盘，终端联调成功；
3. Invar 核心逆向与漏洞检测流水线 (Subfinder -> HTTPX -> Katana -> AST) 已真实跑通；
4. 环境变量、物理目录划分、配置文件格式完全锁定，无未知黑盒。
```

---

## 20. Handoff Self-Check

- [x] 新 AI 是否知道当前在做什么？（是：正在为已点火的 Pi Agent 构建 Invar Tool Contract 技能）
- [x] 新 AI 是否知道最后一次成功状态？（是：K2-Horizon 8080 端口与 Pi CLI 终端联调 100% 成功）
- [x] 新 AI 是否知道当前唯一步骤？（是：编写 `C:\dev\agent-workspace\skills\invar\SKILL.md`）
- [x] 新 AI 是否知道绝对禁止做什么？（是：严禁内置 Agent、严禁单卡双起模型、严禁裸 pip/python）
