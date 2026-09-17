# AI Development Handoff Specification

> **文档类型**：跨会话工程状态快照（AI Development Handoff）
> 
> **项目**：Invar
> 
> **项目物理根目录**：`C:\dev\Invar`
> 
> **本 HANDOFF 建档日期**：2026-09-16
> 
> **用途**：本文件用于在当前 AI 会话关闭、上下文丢失或原聊天不可访问后，让新的 AI 仅凭本文件 + 当前源码 / 测试 / 项目文档恢复工程状态并从正确位置继续。

---

## 0. Handoff Metadata

| 项 | 当前值 | 事实等级 |
|---|---|---|
| Project | Invar | [FACT] |
| Root | `C:\dev\Invar` | [FACT] |
| Handoff purpose | 跨会话工程状态恢复，不是 README / 会议纪要 | [DECISION] |
| Snapshot date | 2026-09-16 | [FACT] |
| Current major workstream | 授权 Web 资产发现链 → Invar 核心研究链 | [DECISION] |
| Current active phase | HTTPX 资产转换层已完成首轮真实验证，等待真实结果检查后再决定下一步 | [FACT] + [DECISION] |
| Git branch | UNKNOWN | [UNKNOWN] |
| Git commit | UNKNOWN | [UNKNOWN] |
| Git working tree clean/dirty | UNKNOWN（当前会话无法直接读取实时 Git 状态） | [UNKNOWN] |

---

# 1. Project Identity

## 1.1 项目定位

[FACT]

Invar 是一个 **Rust + Python 双引擎智能安全研究系统**。当前工程规格书将其目标定义为：将历史脚本式安全研究代码逐步演进为可复现、可测试、可追溯、可替换、可扩展、可审计的系统。

核心五层认知架构为：

```text
Level 5  Agent
         HypothesisEngine

Level 4  Skill / Invariant
         InvariantEvaluator

Level 3  Harness / IPC / Executor
         ast_worker / research_worker / AdaptiveSandboxExecutor

Level 2  Evidence
         EvidenceRecord / ProbeAttempt

Level 1  Knowledge
         KnowledgePromoter / KnowledgeCard
```

工程规格明确要求：有依据才实现、有契约才扩展、有测试才交付、有证据才晋级。该原则在正式规格书中被明确记录。 [FACT] 来源：`c/Invar AI 可复现工程规格书.md`。

## 1.2 双引擎职责

[DECISION]

```text
Rust = 系统级总控
      编排 / 生命周期 / 进程管理 / IPC / 资源管理 / 并发边界 / 强类型公共契约

Python = 专业研究引擎
         AST / 风险推理 / 安全研究逻辑 / Agent / AI/ML / 快速实验
```

禁止将 Rust 机械变成“性能版 Python”，也禁止长期让 Python 承担系统级总控。

---

# 2. Current Mission

## 2.1 当前真实实战主线

[FACT]

当前授权 Web 资产研究目标为：

```text
Target = ikuai8.com
```

当前用户声明该目标处于授权研究范围内。本 HANDOFF 不额外推断授权条款；正式授权范围仍以目标方提供的实际规则为准。

当前资产发现链已经明确为：

```text
Subfinder
    ↓
subdomains.jsonl
    ↓
HTTPX
    ↓
live_hosts.jsonl
    ↓
Katana
    ↓
urls.jsonl + javascript.jsonl
    ↓
Invar
    ↓
JS → AST → EndpointIR → RiskEngine → Research → Evidence → Knowledge
```

## 2.2 为什么建立资产基线层

[DECISION]

外部工具负责“发现事实”，Asset Registry 负责长期记账；Invar 核心负责理解、研究和验证这些事实。

因此：

```text
Subfinder TXT / HTTPX 原始 JSON
    = 原始工具运行产物

*.jsonl 规范化资产文件
    = 长期可消费的结构化事实
```

`data\targets\<target>\` 是持久化资产事实区域；`tmp\` 是本次运行的临时产物区域。

---

# 3. CURRENT OBJECTIVE

**当前唯一推进目标：完成 HTTPX 真实结果的事实检查，并在事实确认后决定 HTTPX 资产模型是否需要进一步补充。**

当前已经知道：

```text
subdomains.jsonl = 99
HTTPX active inputs = 99
HTTPX live count = 37
```

[FACT]

但 `live_hosts.jsonl` 与原始 `httpx.jsonl` 的真实字段内容在当前会话结束前尚未做逐条人工检查，因此：

```text
37 个 Live Host 的具体字段分布 = UNKNOWN
哪些 HTTPX 字段值得进入长期资产模型 = UNKNOWN
```

---

# 4. NEXT SINGLE ACTION

新的 AI 会话启动后，**只能先执行这一项**：

在 PowerShell 中检查当前真实的 `live_hosts.jsonl` 与 HTTPX 原始输出前 10 行：

```powershell
Set-Location C:\dev\Invar

Write-Host "===== live_hosts.jsonl ====="
Get-Content .\data\targets\ikuai8.com\live_hosts.jsonl

Write-Host "`n===== count ====="
$liveHosts = @(Get-Content .\data\targets\ikuai8.com\live_hosts.jsonl)
Write-Host "live_hosts.jsonl : $($liveHosts.Count)"

Write-Host "`n===== raw httpx sample ====="
Get-Content .\data\targets\ikuai8.com\httpx.jsonl | Select-Object -First 10
```

执行后必须等待用户真实终端结果，再决定下一步。

**禁止在拿到结果前直接进入 Katana、重构 HTTPX 资产模型或添加无证据字段。**

---

# 5. Current Scope

## 5.1 当前模块

当前只关注以下资产发现层：

```text
scripts/asset/ingest_subdomains.py
scripts/asset/ingest_httpx.py

src-tauri/python/tests/test_ingest_subdomains.py
src-tauri/python/tests/test_ingest_httpx.py

data/targets/ikuai8.com/
```

以及它们与：

```text
Subfinder
HTTPX
```

之间的输入 / 输出关系。

## 5.2 当前架构层

```text
资产发现层
    ↓
gateway / ingestion
    ↓
规范化资产层
```

还没有进入 Katana 的实现层，也没有把资产发现链接入 Rust / Python 核心研究 IPC。

---

# 6. Out of Scope

在当前 HTTPX 结果事实检查结束之前，明确不要触碰：

```text
❌ Katana 生产接入
❌ Rust ↔ Python IPC
❌ Agent 重构
❌ HypothesisEngine 重构
❌ AdaptiveSandboxExecutor 重构
❌ UI
❌ 大规模目录迁移
❌ 性能优化
❌ 非 HTTPX 相关技术债
❌ 复制历史 exploit / 真实凭据 / 真实攻击材料
```

[DECISION]

当前阶段优先保证资产层边界稳定，而不是扩大工程改动面。

---

# 7. Last Known Good State

## 7.1 时间

[FACT]

最后已知良好状态：2026-09-16，本次会话的 HTTPX 实际运行完成后。

## 7.2 Python 资产发现测试

[FACT]

`test_ingest_subdomains.py` 最终通过：

```text
8 / 8
OK
```

最后一次真实命令：

```powershell
uv run python -m unittest .\src-tauri\python\tests\test_ingest_subdomains.py -v
```

## 7.3 HTTPX 单元测试

[FACT]

`test_ingest_httpx.py` 最终通过：

```text
2 / 2
OK
```

最后一次命令：

```powershell
uv run python -m unittest .\src-tauri\python\tests\test_ingest_httpx.py -v
```

已验证的两个核心行为：

1. 同一个 Host 通过多个 URL 被 HTTPX 观察到时，只生成一个 Host Asset。
2. 非目标域名不会进入目标 Host 资产集合。

## 7.4 真实 Subfinder 资产基线

[FACT]

第一次使用真实 `ikuai8.com` Subfinder 结果完成摄取后：

```text
subdomains.jsonl : 99
changes.jsonl    : 99
manifest.jsonl   : 1
```

随后使用完全相同的原始 TXT 再摄取一次：

```text
subdomains.jsonl : 99
changes.jsonl    : 99
manifest.jsonl   : 2
```

这证明相同输入不会重复制造资产或重复制造 `created` 事件，同时每次运行都会留下 Manifest 记录。

## 7.5 真实 HTTPX 资产结果

[FACT]

已成功执行：

```powershell
uv run python .\scripts\asset\ingest_httpx.py `
    --input "C:\dev\Invar\data\targets\ikuai8.com\subdomains.jsonl" `
    --target "ikuai8.com"
```

执行结果：

```text
active inputs : 99
live count    : 37
```

产生：

```text
C:\dev\Invar\data\targets\ikuai8.com\httpx.jsonl
C:\dev\Invar\data\targets\ikuai8.com\live_hosts.jsonl
```

## 7.6 Rust / 既有核心测试基线

[FACT - 来自既有 HANDOFF / 当前会话历史]

在本次资产发现层加入之前，既有项目基线记录为：

```text
Rust 14 passed
Python 44 passed
总计 58 tests
0 warning
0 error
```

既有 Rust 测试命令：

```powershell
cargo test --manifest-path 'C:\dev\Invar\src-tauri\crates\Cargo.toml'
```

**注意**：本会话新增资产层测试加入后，没有再次执行完整项目总套件，因此“加入资产层后新的全项目总测试数”不能标记为已验证。新会话需要重新跑完整回归后再更新本节。

---

# 8. Completed Work

| Item | Status | Evidence | Files | Notes |
|---|---|---|---|---|
| Subfinder 原始结果生成 | DONE | 用户实际运行 Subfinder；获得约 99 条结果 | `tmp/ikuai8_subdomains.txt` | 原始采集产物 |
| Subdomain 清洗 / 规范化 / 去重 | DONE | 8/8 测试通过 | `scripts/asset/ingest_subdomains.py` + tests | 当前第一版契约已锁定 |
| target 归属校验 | DONE | 外部域名测试通过 | 同上 | `hostname == target` 或 `hostname.endswith("." + target)` |
| 稳定 `asset_id` | DONE | 测试通过 | 同上 | 规则：`subdomain:<hostname>` |
| Subdomain 增量更新 | DONE | 重复摄取测试通过 | 同上 | `first_seen` 保持、`last_seen` 更新 |
| Subdomain 状态 active / inactive | DONE | 完整扫描缺失资产测试通过 | 同上 | 仅针对已完成扫描路径实现 |
| Subdomain `changes.jsonl` | DONE | created / status_changed 测试通过 | 同上 | 已验证基本幂等性 |
| Subdomain `manifest.jsonl` | DONE | completed 测试通过 | 同上 | 当前记录 source=subfinder |
| 真实 Subdomain 基线 | DONE | 99 条 | `data/targets/ikuai8.com/subdomains.jsonl` | 第一次真实摄取 |
| 真实 Subdomain 幂等性 | DONE | 99/99/2 结果保持预期 | 同上 | 第二次相同输入没有增加 created |
| HTTPX URL → Host 聚合 | DONE | 2/2 HTTPX 测试通过 | `scripts/asset/ingest_httpx.py` + tests | 同一 Host 多 URL 只生成一个 Host Asset |
| HTTPX target 边界 | DONE | 外部域名测试通过 | 同上 | 不把非目标 Host 纳入资产 |
| HTTPX CLI 收口 | DONE | CLI 实际执行成功 | `scripts/asset/ingest_httpx.py` | 读取 `subdomains.jsonl`，调用系统 `httpx`，生成规范化 Host JSONL |
| 真实 HTTPX 探测 | DONE | active inputs=99, live count=37 | `httpx.jsonl`, `live_hosts.jsonl` | 37 个 Live Host 已生成 |
| Katana 批量接入 | TODO | 尚未实现 | - | 必须等待 HTTPX 结果事实检查 |
| Rust ↔ Python IPC | PARTIAL | 既有契约骨架存在 | `src-tauri/crates`, `src-tauri/python` | 真实 subprocess/IPC 仍未连接 |

---

# 9. Changed Files

> 本节记录本次会话中确认的文件变化。由于当前 AI 无法读取用户实时工作树，Git 层面是否还有其他未列出的修改为 [UNKNOWN]。

## 9.1 Added

```text
scripts/__init__.py
scripts/asset/__init__.py
scripts/asset/ingest_subdomains.py
scripts/asset/ingest_httpx.py
src-tauri/python/tests/test_ingest_subdomains.py
src-tauri/python/tests/test_ingest_httpx.py
```

## 9.2 Modified

```text
c/HANDOFF.md
```

以及本会话中持续修改过的测试 / 资产脚本属于上面的 Added/当前工作树项；若实际工作树显示为 Modified，应以 Git 实际状态为准。

## 9.3 Generated / Runtime Data

```text
data/targets/ikuai8.com/subdomains.jsonl
data/targets/ikuai8.com/changes.jsonl
data/targets/ikuai8.com/manifest.jsonl
data/targets/ikuai8.com/httpx.jsonl
data/targets/ikuai8.com/live_hosts.jsonl
tmp/ikuai8_subdomains.txt
```

## 9.4 Deleted

```text
UNKNOWN / 本会话未删除工程文件。
```

## 9.5 Moved

```text
无已验证移动。
```

---

# 10. Structure

当前项目目录契约来自正式工程文档：

```text
C:\dev\Invar
├── c\                          # 规格书、HANDOFF、认知中枢
├── data\                       # 持久化测试资产 / 研究数据
├── models\                     # 本地模型权重
├── tmp\                        # 临时实验与运行产物
├── src\                        # 前端
├── src-tauri\
│   ├── crates\                 # Rust 核心
│   │   ├── src\                # 生产代码
│   │   └── tests\              # Rust 集成测试
│   └── python\                 # Python 核心服务
│       ├── src\                # agent / harness
│       └── tests\              # Python 测试
├── scripts\                    # 项目级脚本、资产采集适配器、审计工具
└── tests\                      # 全局 E2E
```

[FACT]

正式工程文档明确“目录结构是工程类型系统的一部分”，测试、生产代码、数据和临时产物必须保持职责分离。

---

# 11. Architecture Decisions

## AD-01：资产发现层与 Invar 核心分层

**Decision**

```text
Subfinder / HTTPX / Katana
    = 机械资产发现

Asset Registry
    = 事实规范化 + 长期基线

Invar Core
    = AST / EndpointIR / Risk / Research / Evidence / Knowledge
```

**Why**

避免把机械资产收集逻辑和安全研究逻辑耦合。

**Alternatives rejected**

```text
❌ 每个项目手工维护扫描结果
❌ 直接把第三方工具原始输出喂给 Invar 核心
❌ 让 `scan_pipeline.py` 同时承担所有资产发现与研究职责
```

**Evidence**

当前真实 Subfinder → JSONL → HTTPX → Live Host 链已实际跑通。

**Do not revert unless**

新的真实源码或数据契约证明当前分层不能满足工程要求。

---

## AD-02：`data/targets/<target>/` 是长期资产事实区

**Decision**

目标级资产持久化位于：

```text
data\targets\<target>\
```

**Why**

避免每次工具运行覆盖历史基线。

**Evidence**

真实 `ikuai8.com` 已成功建立并二次幂等验证：99/99/2。

**Do not revert unless**

有新的持久化存储架构替代它，并保留完整可迁移资产历史。

---

## AD-03：原始工具结果与规范化资产分离

**Decision**

```text
tmp\*.txt / httpx.jsonl
    = 原始工具运行产物

subdomains.jsonl / live_hosts.jsonl / urls.jsonl / javascript.jsonl
    = 规范化资产事实
```

**Why**

保证上游工具可替换、可审计、可重放，避免 Invar 直接依赖某个工具的原始输出格式。

---

## AD-04：TDD 采用“核心契约优先”，避免过度开发

**Decision**

Subfinder 已完成较细的契约保护；HTTPX/Katana 后续采用更小的核心契约集，不为每一个工具字段建立独立测试。

**Why**

用户明确反馈过度细碎的红灯测试会使实战流程失焦；同时项目规格要求测试保护行为而不是制造无意义测试。

**Evidence**

HTTPX 当前仅以两个核心行为测试即完成首轮 Green。

---

## AD-05：Live Host 文件名采用 `live_hosts.jsonl`

**Decision**

不用宽泛的 `hosts.jsonl` 表示 HTTPX 的第一阶段输出；正式使用：

```text
live_hosts.jsonl
```

**Why**

该名称明确表达“已经观察到 Web 服务”的语义，与 `subdomains.jsonl` 的“候选子域资产”形成层级区别。

**Do not revert unless**

新的资产类型命名规范整体替换，并完成兼容性迁移。

---

# 12. Data / API / Type Contracts

## 12.1 Subdomain Asset

当前已验证结构：

```json
{
  "asset_id": "subdomain:api.ikuai8.com",
  "asset_type": "subdomain",
  "hostname": "api.ikuai8.com",
  "target": "ikuai8.com",
  "first_seen": "<ISO-8601>",
  "last_seen": "<ISO-8601>",
  "status": "active"
}
```

[FACT]

## 12.2 Subdomain Change

已验证：

创建事件：

```json
{
  "change_type": "created",
  "asset_id": "subdomain:api.ikuai8.com",
  "target": "ikuai8.com",
  "observed_at": "<ISO-8601>"
}
```

状态变化事件：

```json
{
  "change_type": "status_changed",
  "asset_id": "subdomain:www.ikuai8.com",
  "target": "ikuai8.com",
  "old_status": "active",
  "new_status": "inactive",
  "observed_at": "<ISO-8601>"
}
```

[FACT]

## 12.3 Subdomain Manifest

当前已验证最小结构：

```json
{
  "target": "ikuai8.com",
  "source": "subfinder",
  "asset_type": "subdomain",
  "observed_at": "<ISO-8601>",
  "status": "completed"
}
```

[FACT]

## 12.4 Host Asset

当前 HTTPX 规范化实现已验证的最小结构：

```json
{
  "asset_id": "host:api.ikuai8.com",
  "asset_type": "host",
  "hostname": "api.ikuai8.com",
  "target": "ikuai8.com"
}
```

[FACT]

### 尚未确定

```text
status_code 是否进入长期 host schema = UNKNOWN
url 是否进入长期 host schema = UNKNOWN
title 是否进入长期 host schema = UNKNOWN
webserver 是否进入长期 host schema = UNKNOWN
tech 是否进入长期 host schema = UNKNOWN
Host 层是否立即复用 Subdomain 的 first_seen/last_seen/changes/manifest 机制 = UNKNOWN
```

这些必须根据真实 `httpx.jsonl` 内容和后续数据模型讨论确定，不能猜。

---

# 13. Asset Workflow

## 13.1 当前资产发现流

```text
授权范围
    ↓
Subfinder
    ↓
tmp/ikuai8_subdomains.txt
    ↓
Subdomain Asset Ingestion
    ↓
data/targets/ikuai8.com/subdomains.jsonl
    ↓
HTTPX
    ↓
data/targets/ikuai8.com/httpx.jsonl
    ↓
HTTPX Asset Ingestion
    ↓
data/targets/ikuai8.com/live_hosts.jsonl
```

## 13.2 目标最终工作流

```text
Subfinder
    ↓
subdomains.jsonl
    ↓
HTTPX
    ↓
live_hosts.jsonl
    ↓
Katana
    ├── urls.jsonl
    └── javascript.jsonl
    ↓
Invar
    ↓
JS
    ↓
Tree-sitter AST
    ↓
EndpointIR
    ↓
RiskEngine
    ↓
ResearchTask
    ↓
HypothesisEngine
    ↓
AdaptiveSandboxExecutor
    ↓
Evidence
    ↓
KnowledgePromoter
    ↓
KnowledgeCard
```

[DECISION]

---

# 14. Verified Tests

## 14.1 `test_ingest_subdomains.py`

**最终结果：8/8 Green** [FACT]

覆盖：

```text
1. 重复子域去重
2. 外部域名拒绝
3. 已有资产更新而不是重复创建
4. 新资产只产生一次 created
5. manifest.status = completed
6. 完整扫描后未发现旧资产 → inactive
7. active → inactive 生成 status_changed
8. inactive → inactive 不重复生成状态变化
```

命令：

```powershell
uv run python -m unittest .\src-tauri\python\tests\test_ingest_subdomains.py -v
```

## 14.2 `test_ingest_httpx.py`

**最终结果：2/2 Green** [FACT]

覆盖：

```text
1. HTTP / HTTPS 等多个 URL 指向同一 Host 时只形成一个 Host Asset
2. 外部域名不会进入目标 Host 资产集合
```

命令：

```powershell
uv run python -m unittest .\src-tauri\python\tests\test_ingest_httpx.py -v
```

## 14.3 Existing Python / Rust 基线

[FACT - 既有 HANDOFF]

资产层实现前：

```text
Python 44 passed
Rust 14 passed
总计 58
```

完整 Rust 命令：

```powershell
cargo test --manifest-path 'C:\dev\Invar\src-tauri\crates\Cargo.toml'
```

资产层加入后尚未执行完整项目回归；这是新的验证任务，而不是已完成事项。

---

# 15. Failure / Pitfall Registry

## F-01：测试接口与生产接口不同步

**Problem**

新增 `observed_at` 参数后旧测试仍未传参。

**Symptom**

```text
TypeError: ingest_subdomains() missing 1 required positional argument: 'observed_at'
```

**Root Cause**

生产接口契约升级后旧测试调用未同步。

**Correct Fix**

更新旧测试以使用统一接口。

**Regression**

3/3 → 后续继续扩展，最终 8/8 Green。

**Future Prevention**

接口契约升级后先统一测试调用，再判断业务失败。

---

## F-02：使用错误的 PowerShell `-replace` 参数数量

**Problem**

一次测试文件修改命令误写为多操作数 `-replace`。

**Symptom**

```text
The -replace operator allows only two elements to follow it, not 4.
```

**Root Cause**

PowerShell `-replace` 运算符语法使用错误。

**Correct Fix**

直接完整覆盖测试文件，而不是进行复杂文本替换。

**Future Prevention**

大型文件修改优先使用完整 PowerShell 原样落盘。

---

## F-03：一次扫描缺失不能自动视为资产消失

**Problem**

不能因为某次 Subfinder 结果中没有资产，就直接将资产标记 inactive。

**Root Cause**

扫描可能不完整或数据源异常。

**Correct Fix**

只有已确认 `manifest.status = completed` 的完整扫描才允许进入“本轮未发现 → inactive”的判断路径。

**Regression**

Subdomain inactive 测试、status_changed 测试已通过。

**Future Prevention**

不得删除这一安全边界。

---

## F-04：HTTPX URL 数量不能直接等于 Host 资产数量

**Problem**

同一主机可能被 HTTPX 以多个 scheme / URL 观察。

**Root Cause**

工具输出是 URL 级观察，资产模型是 Host 级实体。

**Correct Fix**

按 hostname 聚合并使用 `host:<hostname>` 稳定身份。

**Regression**

HTTPX 第一枚测试已通过。

---

# 16. Do Not Repeat

```text
不要凭文件名猜当前实现
不要跳过真实源码阅读
不要把 TODO 写成 DONE
不要把架构建议写成历史事实
不要把一轮扫描缺失直接解释成资产删除
不要把 URL 直接当 Host 资产
不要为了每个 HTTPX 字段创建一个测试
不要为单一 ikuai8 案例增加特判
不要复制真实 Token / Cookie / JWT
不要复活历史 exploit 代码
不要把测试塞进生产目录
不要用裸 python
不要使用 pip
不要使用 Linux 路径
不要一次推进多个未验证阶段
不要为了消 warning 乱改 package identity
不要为了“看起来复杂”增加无依据字段
不要未经真实结果检查就进入 Katana
```

这些约束与既有工程规格保持一致。

---

# 17. Environment / Toolchain

## 17.1 OS

[FACT]

```text
Windows 11
```

既有项目档案记录没有 WSL Kali / Docker。

## 17.2 外部工具

[FACT - 既有 HANDOFF]

```text
httpx.exe   ProjectDiscovery v1.12.0
subfinder.exe ProjectDiscovery v2.16.0
katana.exe  ProjectDiscovery v1.7.0
```

工具目录：

```text
C:\dev\bin
```

## 17.3 Python

[FACT]

项目 Python 使用 `uv`。

`src-tauri/python/pyproject.toml`：

```toml
[project]
name = "invar-engine"
version = "0.1.0"
requires-python = ">=3.10,<3.13"

[tool.uv]
package = false
```

依赖包括：

```text
pydantic
Tree-sitter
requests
httpx
httpx-socks
socksio
```

**重要矛盾 / 待验证点**：本会话终端日志显示 uv 当前实际启动了 CPython 3.14，而项目正式 `pyproject.toml` 要求 `>=3.10,<3.13`。这意味着当前运行环境与项目声明存在潜在漂移。

状态：**OPEN / UNKNOWN**。

新会话应在适当时验证：

```powershell
uv run --project "C:\dev\Invar\src-tauri\python" --python 3.11 python --version
```

但这不是当前 HTTPX 事实检查的第一动作；不得因该问题任务漂移。

## 17.4 Rust

Cargo workspace：

```text
C:\dev\Invar\src-tauri\Cargo.toml
```

内容已确认：

```toml
[workspace]
members = ["crates"]
resolver = "2"
```

## 17.5 PATH / Windows 命令约束

```text
Python：统一 uv
Rust：Cargo
禁止 bare python
禁止 pip
禁止 Linux absolute path
```

---

# 18. Current Core Architecture

## 18.1 Python 研究引擎

[FACT]

关键模块包括：

```text
src-tauri/python/src/agent/
├── hypothesis_engine.py
├── knowledge_promoter.py
├── mutator.py
└── risk_engine.py

src-tauri/python/src/harness/
├── ast_worker.py
├── config.py
├── evidence.py
├── exporter.py
├── extractor.py
├── feedback.py
├── idor_compare.py
├── invariant_evaluator.py
├── method_tamper.py
├── models.py
├── mutation_policy.py
├── research_adapter.py
├── research_evidence.py
├── research_models.py
├── research_worker.py
├── sandbox_executor.py
└── transport.py
```

## 18.2 当前已有高级安全算子

[FACT]

```text
IdorCompareOperator
MethodTamperOperator
```

并已有对应单元 / 集成测试。

## 18.3 AdaptiveSandboxExecutor

[FACT]

`AdaptiveSandboxExecutor` 当前已具备：

```text
_build_initial_payload
_build_url
_create_research_case
_probe_endpoint_with_research_case
probe_endpoint_with_research
probe_endpoint
probe_all
```

并已包含：

```text
H-IDOR
H-AUTH
H-DESTRUCT
```

相关集成测试已验证 Token A / Token B IDOR 研究路径以及 Method Tamper 路径。

这些属于已有 Invar 核心能力，当前资产发现层开发不得随意改动。

---

# 19. Open Issues

## O-01：HTTPX Host 长期 schema 尚未完全冻结

**Impact**

决定 `live_hosts.jsonl` 是否保存 HTTPX 详细观测字段。

**Current Evidence**

已经生成 37 个 Live Host。

**Known**

Host 聚合、target 边界已经验证。

**Unknown**

```text
status_code/title/webserver/tech/url 等是否进入长期 Host schema
```

**Next Verification**

读取真实 `live_hosts.jsonl` 和原始 `httpx.jsonl` 前 10 行。

---

## O-02：Host 层是否采用和 Subdomain 层一样的增量状态机制

**Impact**

决定 `live_hosts.jsonl` 是否成为长期基线而不是一次性扫描结果。

**Current Evidence**

Subdomain 层已实现完整状态 / changes / manifest 闭环。

**Unknown**

Host 层是否必须完全复用相同机制，目前尚未根据真实 Host 数据与流程需求最终确认。

**Next Verification**

先确认 O-01，再设计最小 Host 持久化契约。

---

## O-03：`data/assets` 是否继续作为抽象概念

**Current Decision**

当前真正的物理事实源使用：

```text
data/targets/<target>/
```

而不是把 `data/assets` 当作另一个事实存储。

**Status**

DECISION。

**Unknown**

未来 Invar Core 是否需要一个逻辑 Asset Provider 抽象层，尚未实现。

---

## O-04：实时 Git 状态

```text
UNKNOWN
```

新会话如需正式发布、提交或大规模变更，先读取真实 Git 状态。

---

## O-05：完整项目测试回归

**Status**

UNVERIFIED（资产层新增后尚未执行）。

**Next Verification**

在 HTTPX/Katana 边界稳定后，执行完整 Python + Rust 回归。

---

# 20. Roadmap

仅记录路线，不等同于 CURRENT OBJECTIVE。

```text
Phase A  Subfinder Asset Registry
         ✅ 完成

Phase B  HTTPX Live Host Registry
         🟡 当前进行中

Phase C  Katana URL / JavaScript Asset Registry
         TODO

Phase D  Invar AST → EndpointIR
         已有能力，需接入新资产源

Phase E  RiskEngine / ResearchTask
         已有能力，需接入新资产源

Phase F  HypothesisEngine
         已有能力

Phase G  AdaptiveSandbox / Evidence
         已有能力

Phase H  Knowledge Promotion
         已有能力

Phase I  Rust ↔ Python 真正 subprocess / IPC
         TODO / 既有契约骨架已存在
```

---

# 21. Invariants

以下是当前必须保护的工程不变量。

## I-01 资产身份稳定

```text
同一 hostname
    ↓
同一 asset_id
```

## I-02 Target 边界不可跨越

```text
target = ikuai8.com

api.ikuai8.com      ✅
example.com         ❌
ikuai8.com.example.com ❌
```

## I-03 重复扫描不制造重复资产

```text
Same input
    ↓
Same asset IDs
    ↓
No duplicate created events
```

## I-04 原始运行数据与长期资产分离

```text
tmp = transient
 data = persistent fact
```

## I-05 资产消失必须有完整扫描证据

```text
未发现
≠
已消失
```

只有完成扫描事实存在时才可进入 inactive 判定。

## I-06 URL 与 Host 不混淆

```text
多个 URL
    ↓
一个 Host Asset（同 hostname）
```

## I-07 不破坏既有 Invar 核心契约

当前资产发现层不得未经证据修改：

```text
ResearchTask
ResearchResult
EvidenceRecord
EndpointIR
HypothesisEngine
AdaptiveSandboxExecutor
```

---

# 22. Security / Sensitive Data Boundary

[SECURITY]

不得在 HANDOFF 中记录：

```text
真实 Token
真实 Password
Private Key
Cookie
JWT
真实认证头
```

本项目既有历史资料包含真实研究目标、认证材料和主动 exploit 代码；新会话禁止直接复活这些历史攻击材料。算法迁移优先使用：

```text
fixture
mock
localhost
controlled lab
```

当前 `ikuai8.com` 属于用户声明的授权研究目标，但 HANDOFF 不保存敏感凭据。

---

# 23. Failure Recovery Rules

如果新会话发现：

```text
HANDOFF ≠ 源码
```

执行：

```text
停止猜测
↓
读取真实源码
↓
记录冲突
↓
以最新可验证源码 / 测试为准
```

如果：

```text
HANDOFF ≠ 测试结果
```

优先检查最新真实测试。

如果信息不足：

```text
UNKNOWN
```

不得脑补。

---

# 24. AI Collaboration Protocol

新 AI 接手后必须遵守：

```text
中文优先
第一次出现专业术语时给中文 + English
代码中的真实英文名称保留

一次只推进一个逻辑动作
先读取真实源码 / 测试
先定义最小契约
红灯
最小修改
绿灯
真实数据验证
再进入下一层
```

用户是编程初学者，因此命令必须：

```text
Windows / PowerShell 可直接执行
代码完整
不使用省略号
不使用伪代码
不要求手工编辑大型文件
```

Python：

```text
uv
```

Rust：

```text
cargo
```

每轮最后只要求用户执行**当前步骤**。

---

# 25. AI Output Format Protocol

新会话默认采用：

```text
# 1. 当前目标
# 2. 黄金标准出处溯源（GS Grounding）
# 3. 原理与解说
# 4. 执行内容
## 反馈要求
```

要求：

```text
只给当前动作
等待真实终端输出
再决定下一步
```

禁止把 Roadmap 当成当前执行清单。

---

# 26. Reproducibility Status

## 当前评级：PARTIALLY REPRODUCIBLE

**原因**：

### 已可复现

```text
Subfinder → subdomains.jsonl

8/8 资产摄取测试

真实 99 条 Subdomain 基线

真实二次幂等验证

HTTPX → live_hosts.jsonl

2/2 HTTPX 核心测试

真实 HTTPX：99 inputs → 37 live hosts
```

### 尚未完全复现 / 尚未验证

```text
HTTPX Host schema 最终字段尚未冻结
Host 层完整增量机制尚未冻结
完整项目全套回归尚未在资产层加入后重跑
实时 Git 状态未读取
Python uv 实际执行版本与 pyproject 要求存在待核对漂移
```

因此不能标记为 FULLY REPRODUCIBLE。

---

# 27. Recovery Protocol

新 AI 严格按以下顺序恢复：

```text
1. 读取本 HANDOFF

2. 读取：
   c/Invar AI 可复现工程规格书.md
   c/ARCHITECTURE.md（若存在）
   README.md

3. 读取当前真实源码：
   scripts/asset/ingest_subdomains.py
   scripts/asset/ingest_httpx.py
   src-tauri/python/tests/test_ingest_subdomains.py
   src-tauri/python/tests/test_ingest_httpx.py

4. 读取当前真实数据：
   data/targets/ikuai8.com/

5. 验证 Last Known Good State

6. 检查 Git 状态 / 代码漂移

7. 恢复 CURRENT OBJECTIVE

8. 只执行 NEXT SINGLE ACTION

9. 等待终端真实结果

10. 再决定下一步
```

如果新会话发现这份 HANDOFF 与源码不一致：

> 以最新真实源码和测试证据为准，并显式记录冲突；不要静默覆盖历史。

---

# 28. Next Session Start Phrase

新会话可以直接从下面这句话开始：

> **请读取 `C:\dev\Invar\c\HANDOFF.md`，先恢复 Last Known Good State 和 CURRENT OBJECTIVE；不要修改代码。然后只执行 CURRENT OBJECTIVE 的 NEXT SINGLE ACTION：检查 `data\targets\ikuai8.com\live_hosts.jsonl` 与 `httpx.jsonl` 的真实内容，确认 37 个 Live Host 的实际字段结构，再给出事实对账结果。不要提前进入 Katana。**

---

# 29. Handoff Self-Check

```text
[x] 新 AI 是否知道当前到底在做什么？
    是：HTTPX 真实结果字段检查。

[x] 新 AI 是否知道最后一次成功状态？
    是：HTTPX 99 → 37，2/2 测试 Green；Subfinder 99 基线已建立并幂等验证。

[x] 新 AI 是否知道最后修改了哪些文件？
    是：资产脚本、资产测试、HANDOFF，以及生成的数据文件已记录。

[x] 新 AI 是否知道为什么这么设计？
    是：资产发现 / Asset Registry / Invar Core 分层与原因已记录。

[x] 新 AI 是否知道哪些行为不能破坏？
    是：Invariants / Do Not Repeat 已记录。

[x] 新 AI 是否知道当前唯一下一步？
    是：检查 live_hosts.jsonl + httpx.jsonl。

[x] 新 AI 是否知道当前阶段不能做什么？
    是：Out of Scope 已记录。

[x] 新 AI 是否知道如何运行测试？
    是：Python / Rust 命令已记录。

[x] 新 AI 是否知道哪些信息尚未确定？
    是：UNKNOWN / Open Issues 已记录。

[x] 新 AI 是否能够在源码缺失部分情况下依据文档继续恢复？
    是，但必须在恢复协议中重新读取真实源码并验证。
```

---

# 30. Final State Snapshot

```text
============================================================
Invar — 2026-09-16 Session Close Snapshot
============================================================

Asset Discovery

Subfinder
    ↓
subdomains.jsonl
    ↓
99 candidate subdomains
    ↓
HTTPX
    ↓
99 active inputs
    ↓
37 live hosts
    ↓
live_hosts.jsonl

Current exact state:

Subfinder Asset Registry       ✅
8/8 tests                     ✅
Real baseline                ✅ 99
Second-run idempotency       ✅ 99 / 99 / 2

HTTPX Asset Adapter           ✅
2/2 tests                     ✅
Real execution               ✅ 99 → 37

Current blocker / next point:

37 Live Hosts
    ↓
inspect real schema
    ↓
decide Host persistence contract
    ↓
ONLY THEN Katana

============================================================
Current Objective:
Inspect HTTPX real outputs.

Next Single Action:
Run the inspection command in Section 4.

Do not skip ahead.
============================================================
```
