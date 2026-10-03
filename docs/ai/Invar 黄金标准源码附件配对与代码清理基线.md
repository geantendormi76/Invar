# Invar 黄金标准源码附件配对与代码清理基线

## 0. 使用目的

本清单用于把 Invar《工业级安全研究系统升级总蓝图》与成熟开源项目的“可审查源码参考”进行一一配对，并在进入重构开发前完成代码库净化，避免引入第二套执行链、重复状态源、不可审计的脚本后门与无效测试。

### 总原则

- 外部仓库作为“黄金参考源”，不是直接复制目标。
- 每个参考仓库固定到具体 commit/tag，并同时保存 LICENSE / NOTICE / provenance 信息。
- Shannon 等受限制许可证项目默认只做架构思想参考，不复制源码、Prompt、Skill 或测试实现。
- Invar 内部始终保持：Evidence / ExecutionTrace 为事实源；ResearchGraph 为研究状态投影，而不是第二套事实数据库。
- 任何旧代码必须先经过“保留 / 合并 / 迁移 / 隔离 / 删除”分类，不允许凭文件名直接删除。

---

## 1. 黄金标准总表

| 来源 | 定位 | 主要对齐阶段 | 可参考内容 | 迁移策略 |
|---|---|---|---|---|
| Anthropic Defending Code Reference Harness | 发现→复验→去重→报告流水线 | 9.9 / 10.0 / 10.1 | fresh verifier、PoC-only crossing、dedupe、report、pipeline 分层 | 优先参考架构与契约；Apache-2.0 内容可在遵守 NOTICE 条件下研究/适配 |
| Strix | Agent / Tool / Runtime / Skills 工程化 | 9.7 / 9.8 / 10.3 | tools、runtime、skills、scope、sandbox、tool limits | 重点参考目录边界与执行治理，不复制整个 Agent |
| Agentic-Bug-Hunter | Bug bounty 全流程 | 9.8 / 10.1 / 10.2 | recon→hunt→validate→report、7-question gate、scope/policy、安全 MCP | MIT；适合做流程/门禁参考与局部适配 |
| Claude-Red | Skill / Playbook 知识工程 | 9.8 | 单攻击面 SKILL.md、触发/方法/边界/验证知识组织 | MIT；参考格式与知识拆分 |
| RedAmon | 有界专项 Agent 编排 | 9.10 | SG-ReAct、bounded specialists、RoE、fan-out/fan-in、状态机 | 主要参考架构思想；第三方依赖单独审许可证 |
| Tencent AI-Infra-Guard | Rule-first + LLM + 可插拔引擎 | 9.8 / 9.9 / 9.10 | YAML rules、数据与代码分离、模块化扫描引擎、任务 API | Apache-2.0；重点参考规则注册与模块边界 |
| Pi Agent Core | Agent 状态/工具/事件运行时 | 9.9 / 9.10 | typed agent state、tool lifecycle、events、abort/budget | 只吸收状态/工具协议思想；不在 Invar 引入第二 Agent Runtime |
| Shannon | Source-aware DAST、exploit-first | 9.9 / 10.0 / 10.2 | source→attack path→live exploit、proven exploit、resume/dedupe 思路 | AGPL-3.0；仅概念/白皮书级参考，不复制代码/Prompt |
| Nuclei | 模板化扫描执行引擎 | 9.7 / 9.8 | SDK、TemplateEngine、flow、typed execution | 外部工具 wrapper；不把 nuclei 源码搬进 Invar |
| ffuf | 模糊测试执行模型 | 9.7 / 9.8 | Request、RunnerProvider、Job/Config、可替换执行器 | 外部工具 wrapper；学习 executor contract |
| Katana | 自动化爬虫/JS crawling | 9.7 / 10.3 | headless/non-headless、JS crawl、resume、exclude | 外部工具 wrapper |
| httpx | HTTP 探测/批处理执行 | 9.7 | 批量 probe、transport/config 组织 | 外部工具 wrapper |

---

## 2. 按 Phase 配对的“必须附件”

### Phase 9.7 — Tool Gateway & Physical Artifact Substrate

**必附：**

1. Strix
   - `AGENTS.md`
   - `strix/config/settings.py`
   - `docs/tools/sandbox.mdx`
   - `strix/tools/agent_browser/README.md`

2. Agentic-Bug-Hunter
   - `docs/mcp-security.md`
   - `AGENTS.md`

3. Nuclei
   - `lib/sdk.go`
   - `pkg/tmplexec/interface.go`
   - `pkg/tmplexec/flow/flow_executor.go`

4. ffuf
   - `pkg/ffuf/interfaces.go`
   - `pkg/ffuf/request.go`
   - `pkg/ffuf/config.go`
   - `pkg/runner/simple.go`

**要求 AI 从这些附件提取：**
- Tool capability contract
- tool lifecycle
- timeout / cancellation
- output/event contract
- sandbox boundary
- typed request/response model
- tool-specific options 不通过万能字符串透传

**禁止 AI 学习成以下错误模式：**
- `extra_args: List[str]`
- LLM 直接拼 shell
- target traffic 在 Tool Gateway 外执行
- secrets 进入 command log

---

### Phase 9.8 — Skills System & Typed Operators

**必附：**

1. Strix
   - `strix/skills/README.md`
   - `strix/skills/` 中代表性 vulnerability skill

2. Claude-Red
   - `README.md`
   - `Skills/web/offensive-sqli/SKILL.md`
   - `Skills/ai/offensive-ai-security/SKILL.md`

3. Agentic-Bug-Hunter
   - `skills/bug-bounty/`
   - `skills/bb-methodology/`
   - `skills/triage-validation/`
   - `skills/report-writing/`

**要求 AI 提取：**
- metadata
- trigger
- preconditions
- methodology
- allowed tools
- success/failure conditions
- stop conditions
- false-positive elimination
- minimum evidence

**Invar 原则：**

Skill = Strategy / Knowledge
Typed Operator = Deterministic implementation

不得把 PathNormalizer、MethodOverride、RequestComparator 等确定性算法写成自由文本 Prompt。

---

### Phase 9.9 — ResearchGraph & Hypothesis Memory

**必附：**

1. Agentic-Bug-Hunter
   - `tools/lead_board.py`
   - `memory/pattern_db.py`
   - `memory/audit_log.py`
   - `memory/schemas.py`

2. Pi
   - `packages/agent/README.md`
   - `packages/agent/` 中 Agent state / tool lifecycle / event 相关实现

3. AI-Infra-Guard
   - `docs/architecture_evolution.md`
   - `CLAUDE.md`
   - `common/fingerprints/`
   - `data/fingerprints/`
   - `data/vuln/`
   - `common/agent/`
   - `common/runner/`
   - `common/database/`

**Invar 强制补充：**

ResearchGraph 只能是“研究状态图/查询投影”，不能成为第二个物理事实源。

Canonical truth：
- ExecutionRecord
- EvidenceRecord
- Raw Artifact
- current-run/cross-run evidence policy

ResearchGraph 通过事件/事实引用构建，不允许独立改写物理事实。

---

### Phase 9.10 — Information Gain & Experiment Selection

**必附：**

1. RedAmon
   - AI Agent Guide
   - Agentic System Technical Whitepaper（项目仓库中的技术白皮书）
   - 与 SG-ReAct、fireteam、guardrail、fan-in/fan-out 相关实现

2. Pi
   - `packages/agent/` 状态/工具生命周期代码

3. Shannon
   - `README.md`
   - `docs/keygraph-platform.md`
   - `docs/configuration.md`

**Invar 强制规则：**

信息增益只能在“已通过安全硬约束”的实验集合中进行排序：

1. Scope / RoE / credential / method / network boundary 硬拦截
2. 再计算 information gain / cost / observation value
3. 风险不能被“信息增益高”抵消

Specialist fan-out 必须：
- 有并发上限
- 有单任务预算
- 有 wall-clock timeout
- 禁止递归 fireteam
- 输出以 finding/observation 事件汇聚

---

### Phase 10.0 — Fresh Independent Verification & PoC Crossing

**必附：**

1. Anthropic Reference Harness
   - `README.md`
   - `docs/triage.md`
   - `docs/customizing.md`
   - `harness/cli.py`
   - `harness/find.py`
   - `harness/grade.py`
   - `harness/report.py`
   - `tests/test_auth.py`

2. Shannon
   - `README.md`
   - `docs/keygraph-platform.md`

**必须吸收：**
- fresh environment
- separate verifier
- PoC-only crossing
- dedupe before report
- finding lifecycle
- reproducible proof

**Invar 进一步收紧：**

PoC 跨边界最好不是任意可执行 Python，而是“typed PoC specification / request sequence”。

允许 verifier 根据这个规范重新生成执行动作；禁止把发现 Agent 的任意 shell / Python 变量环境一起带过去。

---

### Phase 10.1 — Technical Finding vs Bounty Eligibility

**必附：**

1. Agentic-Bug-Hunter
   - `SKILL.md`
   - `commands/report.md`
   - `docs/mcp-security.md`

**Invar 分层：**

TechnicalFindingGate：真实安全边界击穿？

BountyEligibilityGate：当前项目是否值得提交？

不能合并为一个状态。

---

### Phase 10.2 — Authorized Live Target Benchmark

**必附：**

- Agentic-Bug-Hunter `docs/mcp-security.md`
- Strix `AGENTS.md`
- Strix `docs/tools/sandbox.mdx`
- Nuclei / Katana / httpx / ffuf 的 adapter-relevant interface/source snapshots

**验收必须拆成：**

Track A — deterministic local fixture
Track B — authorized live target

Track A 证明工程契约；Track B 证明真实发现能力。

不能用 mock exploit contract test 代替 Track B。

---

### Phase 10.3+ — Playwright / SPA / Browser

**必附：**

- Strix `strix/tools/agent_browser/README.md`
- Strix `docs/tools/sandbox.mdx`
- Strix browser / runtime related adapter source

浏览器必须作为 Tool Gateway 的特权组件，不允许被 Research Brain 直接操作宿主系统。

---

## 3. 许可证与来源管理要求

### 每个外部附件必须同时保存

- repository URL
- project name
- exact commit SHA / tag
- source path
- source license
- copyright owner
- retrieved date
- Invar 使用方式：`COPY / ADAPT / INSPIRE / EXTERNAL-TOOL / CONCEPT-ONLY`

### 特别处理

- Strix：当前 `pyproject.toml` 标明 Apache-2.0。
- Agentic-Bug-Hunter：MIT。
- Claude-Red：MIT。
- Anthropic Reference Harness：Apache-2.0 证据可从其源码 SPDX header 验证。
- Shannon：AGPL-3.0，默认 `CONCEPT-ONLY`。

Shannon 只允许进入“architecture/reference packet”，不得把其源码、Prompt、Skill 或测试代码直接放入 Invar。

---

# 4. Invar 代码库净化阶段（建议插入 Phase 9.6.5）

## 目标

在任何新架构进入 `python/packages/core/src` 前，把旧实现、死代码、重复执行路径和误导性测试清理掉。

### 4.1 文件分类法

每个可疑模块必须先标记为：

- KEEP — 当前 canonical source of truth
- ADAPT — 保留文件但重构其职责
- MERGE — 合并进入唯一 canonical 模块
- DEPRECATE — 保留短期兼容路径，并明确删除条件
- QUARANTINE — 无法立即确定是否仍有价值，移到隔离目录
- DELETE — 已证明无调用、无契约价值、无测试价值

禁止直接“看名字删文件”。

---

## 5. 现阶段优先清理对象

### 高优先级候选

1. 旧的目标网络直接执行路径
   - 任何绕过未来 Tool Gateway 的直接 target traffic
   - 旧 requests-based target mutation path

2. 旧的 F1~F9 执行实现
   - 不删除知识本身
   - 将知识提取到 Skill
   - 将必要的确定性变换提炼成 Typed Operator

3. 平行 transport / adapter
   - 只有一个 canonical target execution path
   - `transport.py` 最终只能保留“协议接口/兼容 façade”或彻底退休

4. 旧 Sandbox / Research Adapter 中重复的执行包装
   - 必须明确 owner
   - 不允许两个模块都可以直接发目标请求

5. 已生成、临时、调试、快照型文件
   - 旧 tmp 输出
   - 手工 debug JSON
   - 旧 report snapshots
   - 临时 patch / scratch scripts
   - 缓存与 bytecode

---

## 6. 测试代码净化规则

### A. 必须保护的黄金契约测试

- RoE enforcement
- Evidence sufficiency
- Cross-run evidence isolation
- Identity Matrix
- 404 semantic subclassification
- ExecutionRecord / attempts canonicality
- Invariant evaluator
- Promotion gate

这些不是“测试废料”，而是 Invar 的架构法律。

### B. 必须迁移/重命名的测试

“模拟漏洞成立”的测试，如果输入是人工预构造 victim/attacker response：

- 保留：用于证明 Oracle / Promotion / Reporting contract
- 禁止标记：live discovery / E2E exploit proof
- 必要时重命名为 `*_promotion_contract_test.py` / `*_oracle_contract_test.py`

### C. 优先淘汰的测试

- 依赖真实外网的脆弱测试
- 使用黑洞 IP 判断 timeout 的测试
- `assertIn([SUCCESS, FAILED])` 之类允许失败路径通过的测试
- 重复验证同一个旧接口的测试
- 只验证实现内部细节、而不验证契约的测试
- 针对已经退休模块的测试

### D. 新标准

网络执行测试统一走 deterministic local fixture。

Live target benchmark 不进入默认单元测试套件；进入单独 benchmark / manual approval 流程。

---

## 7. 防止未来屎山的持续护栏

### 代码边界

- Research Brain 不得直接 `requests.*`
- Research Brain 不得直接 `subprocess.*`
- Skill 不得直接持有宿主级执行权限
- Target network traffic 只能经过 Tool Gateway
- Evidence 只能来自物理 Artifact / ExecutionRecord

### 状态边界

- ExecutionRecord 是执行事实源
- EvidenceRecord 是物证登记源
- ResearchGraph 是研究状态投影
- Report 是 Evidence/Finding 的投影

禁止第二套 parallel truth store。

### 类型边界

- 禁止万能 `dict[str, Any]` 跨层传递核心安全数据
- 禁止万能 `List[str]` 作为工具能力透传
- 工具参数必须是 ToolOperationSpec 子类型

### 测试边界

- contract test：验证不变量与模块边界
- unit test：验证纯函数
- integration test：只在 local fixture 上做确定性 IO
- benchmark：单独执行真实授权目标

---

## 8. 重构前必须输出的“净化战报”

AI 在任何删除/迁移前，必须先生成：

1. `CODEBASE-INVENTORY.md`
2. `MODULE-OWNERSHIP.md`
3. `DUPLICATE-EXECUTION-PATHS.md`
4. `STALE-CODE-CANDIDATES.md`
5. `STALE-TEST-CANDIDATES.md`
6. `GOLDEN-CONTRACTS.md`
7. `DELETE-PLAN.md`

每一个 DELETE 项必须给出：

- 文件
- 符号
- 全仓引用结果
- 测试引用结果
- 替代者
- 删除理由
- 风险
- 删除后验证命令

只有这份战报通过后，才执行实际删除。

---

## 9. Phase 9.6.5 Definition of Done

- [ ] 无重复 target execution path
- [ ] 无未经批准的直接 target subprocess
- [ ] 无旧 transport 与新 gateway 并行发包
- [ ] 无未分类的旧 F1~F9 实现
- [ ] 无误导性的“mock exploit = live discovery”测试
- [ ] 黄金契约测试全部保留
- [ ] 本地 fixture 测试 deterministic
- [ ] ResearchGraph 被定义为 projection 而非 truth source
- [ ] 所有外部参考附带 provenance + license + commit
- [ ] 删除清单先审后删
- [ ] 全量回归通过

---

# 10. 给 AI 重构者的总规则

> 先清理，再扩展；先确定 canonical owner，再增加模块；先固定 source-of-truth，再建立 ResearchGraph；先固定 Tool Contract，再增加工具；先证明真实发现能力，再扩展 UI。
>
> 不允许为了“看起来更智能”增加第二套执行器、第二套状态机、第二套证据系统或第二套测试语义。
