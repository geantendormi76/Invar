# 🛡️ Invar 工业级安全研究系统升级总蓝图 

---

## 零、 认知认领与设计缺陷复盘 (Lessons Learned)

外部架构审查的批评**极其尖锐且完全切中命门**。此前草案暴露出典型的“为了快速看到表面成果而牺牲系统契约严密性”的工程坏味。在正式锁定规划前，我们首先在认知层完成 7 大技术缺陷与 3 大架构遗漏的客观定性认领：

### 1. 认领三大核心架构遗漏
1. **研究状态图 (ResearchGraph) 的缺位**：  
   `[事实]` 系统缺乏统一的长期认知载体。若仅有技能 (Skills) 与工具，智能体将退化为“无状态的单点探测器”，无法在全局拓扑中追踪：资产如何降解为端点、端点关联何种凭据、派生何种假说、产生何种观测、何时形成收敛。
2. **信息增益 (Information Gain) 决策算法的缺位**：  
   `[事实]` 静态优先级（P0~P3）只能表达先验倾向，无法量化动态探索的价值。智能体决策必须以**“预期信息增益 / 成本 / 风险”**为目标函数，优先选择最能消除系统未知状态的实验。
3. **双盲纯净复验 (Fresh Independent Verification) 隔离边界的模糊**：  
   `[事实]` 独立复验绝不能在带有探测上下文脏数据的同一会话中运行，必须确立**“仅凭最小可复现 PoC 跨越边界 (PoC-Only Crossing)”**的原则，在完全隔离的全新环境 (Fresh Sandbox) 中重新建立会话并完成同态重放。

### 2. 认领 Phase 9.7 施工草案的七大硬伤
1. **`ToolRequest` 存在逃生后门**：定义 `extra_args: List[str]` 实际上架空了强类型数据契约，重新打开了任意注入命令参数的漏洞。
2. **明文凭证泄露风险 (Plaintext Credential Leakage)**：直接序列化命令行作为 `raw_command`，导致 `Authorization`、`Cookie` 等机密直接裸露在日志与追踪流中。
3. **物理事实退化 (Degraded Physical Truth Source)**：对解析后的字符串进行二次哈希，丢失了二进制原始字节 (Raw Bytes)、编码、压缩等物理真理。
4. **自制 HTTP 解析器带来语义污染**：手工使用字符串切割解析响应头，且在解析失败时擅自默认回退为 HTTP 200，破坏了底层裁决的客观性。
5. **安全策略硬编码失控**：默认开启 `-k` (跳过证书校验)，将环境异常与正常业务响应混为一谈。
6. **测试用例缺乏物理确定性**：依赖外部黑洞 IP 测试超时，断言存在 `[SUCCESS, FAILED]` 模糊分支，无法证明真实物理能力。
7. **门禁层次混淆**：“技术漏洞成立 (Technical Vulnerability)”与“赏金项目合格 (Bounty Eligibility)”混为一谈，污染了事实真理层的独立性。

---

## 一、 终极系统拓扑与四层解耦契约

系统彻底解耦为四大物理边界层，每层仅通过显式强类型契约连接，严禁跨层窥探与旁路穿透：

```text
┌────────────────────────────────────────────────────────────────────────┐
│               Layer 4: 知识与策略层 (Knowledge & Skills)               │
│  • docs/skills/ 规范化剧本 (Playbooks: Markdown 规范 + YAML 契约元数据) │
│  • 攻防策略 (Why/When/What) ➔ 明确触发条件、前置上下文与停止信号         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            Layer 2: 决策与状态图谱层 (Research Brain & State)           │
│  • ResearchGraph: 资产/端点/主体/假说/实验/事实的动态因果知识图谱       │
│  • InformationGainPlanner: 基于不确定性熵减与风险成本的最优实验选择     │
│  • BoundedSpecialistController: 并发/单步专项智能体调度与超时熔断控制   │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
      [下发结构化 ToolRequest]                  [物理物证直接驱动]
                    │                                │
                    ▼                                ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│ Layer 3: 执行与物证网关 (Tool Gateway) │  │ Layer 1: 真实裁决法官 (Oracle) │
│ • 强类型能力契约 (Capability Spec)   │  │ • InvariantEvaluator (不变量) │
│ • RoE 物理网络前置拦截与 DNS 校验    │  │ • IdentityMatrix (多主体差分) │
│ • 敏感凭证自动化脱敏 (Redaction)     │  │ • FreshVerifier (双盲隔离复验)│
│ • 物理字节存证 (Raw Byte Artifacts)  │  │ • TechnicalFindingGate (确权) │
│ • 适配器: Curl, Ffuf, Katana, etc.   │  │ • BountyEligibilityGate (赏金)│
└──────────────────────────────────────┘  └──────────────────────────────┘
```

---

## 二、 演进路线图全景规划 (Roadmap Phase 9.7 ~ 10.3)

我们放弃原有的简单桌面端推进，全面重构为**基于成熟工具生态与物理实证能力的八阶段演进路线**：

```text
Phase 9.7  执行基座与物理物证网关 (Tool Gateway & Physical Artifact Substrate)
   ↓
Phase 9.8  结构化技能系统与强类型算子 (Skills System & Typed Operators)
   ↓
Phase 9.9  研究状态图谱与假说记忆 (ResearchGraph & Hypothesis Memory)
   ↓
Phase 9.10 信息增益与实验规划器 (Information Gain & Experiment Selection)
   ↓
Phase 10.0 双盲纯净隔离复验 (Fresh Independent Verification & PoC Crossing)
   ↓
Phase 10.1 两权分立：技术确权与赏金资格门禁 (Technical Finding vs. Bounty Eligibility)
   ↓
Phase 10.2 真实授权现场实弹攻防基准 (Authorized Live Target Benchmark)
   ↓
Phase 10.3+ 复杂前端无头浏览器扩展 (Playwright & SPA DOM Exploration)
```

---

## 三、 各阶段核心职责与契约边界详述

### Phase 9.7：执行基座与物理物证网关 (Tool Gateway & Physical Artifact Substrate)
* **核心目标**：提供安全、受控、抗篡改、保真的物理网络执行环境，彻底解决“Python 手工拼装 HTTP 请求”和“凭据泄露”问题。
* **交付要素**：
  1. **强类型工具能力契约 (Tool Capability Contract)**：
     * 废弃 `extra_args: List[str]`，使用封闭的 `ToolOperationSpec`（如 `HttpSendSpec`、`FuzzEndpointSpec`）；
     * 明确输入、预期输出及工具专属参数的类型约束。
  2. **三权分立的命令与凭证表现 (Command Representation & Redaction)**：
     * 内部保留完整物理执行参数 `actual_argv`（用于沙箱执行）；
     * 审计、追踪及导出仅暴露脱敏参数 `redacted_argv`（凭证一律替换为安全占位符）；
     * 记录工具版本 (Tool Version)、适配器版本 (Adapter Version) 及命令哈希 (Command Fingerprint)。
  3. **真正的物理物证存盘 (Raw Byte Artifact Store)**：
     * 原始输入/输出 HTTP 报文以原始二进制字节流落盘为独立文件（如 `.raw.req`、`.raw.resp`）；
     * `ToolResult` 的 `content_hash` 基于原始字节计算，而非由 Python 处理后的字符串派生；
     * 状态码解析失败时输出强类型异常 `RESPONSE_PARSE_FAILURE`，严禁回退为 200。
  4. **受控的执行策略 (ExecutionPolicy)**：
     * TLS 证书校验默认开启 (`verify_tls = True`)；
     * 超时时间由强类型配置约束，禁止任意放宽；
     * 深度网络拦截：除 URL 字符串匹配外，增加重定向跨域与 IP 绑定检查。
  5. **确定性本地靶标测试套件 (Deterministic Local Fixture Suite)**：
     * 随测启动独立的本地 HTTP 回环测试桩，提供标准响应、404、403、大体积二进制流、延迟超时响应；
     * 测试必须且只能产生确定性断言（成功必为 200，超时必为 TIMEOUT，禁止 `assertIn([SUCCESS, FAILED])`）。

### Phase 9.8：结构化技能系统与强类型算子 (Skills System & Typed Operators)
* **核心目标**：解耦“攻击知识”与“执行代码”，将现有硬编码的 `F1~F9` 下沉为模块化剧本与专用算子。
* **交付要素**：
  1. **技能剧本规范 (Skill Playbook Specification)**：
     * 吸收 Strix 与 Claude-Red 经验，采用统一的 YAML 元数据 + Markdown SOP 结构；
     * 包含元数据字段：`id`, `surface`, `attack_class`, `triggers`, `required_context`, `allowed_tools`, `success_conditions`, `stop_conditions`；
     * Markdown 正文明确：研究意图、先验特征、推荐变异序列、误报消除规则与最小证据要求。
  2. **强类型底层算子 (Typed Operators)**：
     * 剧本负责战略推演 (Strategy)，强类型算子负责确定性数据变换（如 `PathNormalizer`、`MethodOverrideHeaderInjector`）；
     * 严禁把确定性的算法降级为大模型的自由发挥文本生成。
  3. **技能注册与加载中枢 (SkillRegistry & Dynamic Loader)**：
     * 支持从 `docs/skills/` 动态热加载技能；
     * 依据当前端点的特征打标（如包含对象 ID、动词受限等）完成技能的激活过滤。

### Phase 9.9：研究状态图谱与假说记忆 (ResearchGraph & Hypothesis Memory)
* **核心目标**：构建长期研究记忆，彻底终结“瞎试”与“重复发包”。
* **交付要素**：
  1. **因果拓扑图模型 (ResearchGraph Model)**：
     * 节点类型：`Asset` (主机/域名) ➔ `Endpoint` (路由契约) ➔ `Principal` (认证主体) ➔ `Hypothesis` (安全假说) ➔ `Experiment` (物理实验) ➔ `Observation` (物理观测) ➔ `FindingCandidate` (候选发现)；
     * 边关系：`EXPOSES`, `APPLIES_TO`, `TESTS`, `PRODUCES`, `CONFIRMS`, `REFUTES`。
  2. **历史对账与盲区记忆 (Exploration Ledger)**：
     * 记录已证伪的假说（避免死循环推演）；
     * 记录各主体对各端点的覆盖矩阵，精准暴露未经测试的身份交汇点。

### Phase 9.10：信息增益与实验规划器 (Information Gain & Experiment Selection)
* **核心目标**：借鉴 Shannon 哲学，把盲目试探升级为以数学期望为指导的科学探索。
* **交付要素**：
  1. **信息增益评估函数 (Information Gain Evaluator)**：
     * 评估候选实验对于当前假说状态空间的期望熵减（哪个发包最能区分“真鉴权”与“假放行”）；
     * 综合权衡：`Expected Information Gain / (Resource Cost + Risk Level)`。
  2. **多专项智能体并行与熔断 (Bounded Specialist Orchestration)**：
     * 参考 RedAmon 的 SG-ReAct 模式：Auth 专员、IDOR 专员各司其职；
     * 全局严格受制于交战规则 (RoE) 预算守卫与墙钟超时熔断。

### Phase 10.0：双盲纯净隔离复验 (Fresh Independent Verification & PoC Crossing)
* **核心目标**：对标顶会审计与现代红队标准，彻底终结“误将偶发状态当实锤”。
* **交付要素**：
  1. **PoC-Only 物理穿越原则 (PoC-Only Crossing Boundary)**：
     * 发现智能体输出候选发现时，仅被允许输出**标准、自洽、最小化的可复现 PoC 代码 (cURL 或 Python 脚本)**；
     * 禁止向复验环境传递内部探测上下文、中间变量或推论提示词。
  2. **纯净复验沙箱 (Fresh Sandbox Replay)**：
     * 启动全新会话（清空 Cookie、重置连接池、全新拉取或刷新认证主体凭证）；
     * 在隔离环境中盲跑该 PoC，捕获物理发包事实；
     * 由 `IndependentVerifier` 仅比对该纯净响应是否真正破坏了安全不变量。

### Phase 10.1：两权分立：技术确权与赏金资格门禁 (Technical Finding vs. Bounty Eligibility)
* **核心目标**：将客观事实判断与商业业务规则完全隔离，消除误报并提升赏金质量。
* **交付要素**：
  1. **技术发现门禁 (Technical Finding Gate)**：
     * 仅回答唯一问题：**“目标系统是否存在安全边界击穿的客观事实？”**；
     * 满足不变量击穿 + 纯净复验成功 ➔ 确权为 `TechnicalFinding` (CONFIRMED)。
  2. **赏金资格门禁 (Bounty Eligibility Gate)**：
     * 吸收 Agentic-Bug-Hunter 的 7-Question 思想；
     * 仅回答商业/法规问题：是否在授权范围？是否具备实质危害？是否为已排除场景（如弱密码字典、已知重复漏洞）？是否为无利用价值的信息泄露？
     * 仅当通过该门禁后，方准调用 `ReportProjector` 组装正式的 `BOUNTY-SUBMISSION.md`；未通过但技术属实的转入内部治理底账。

### Phase 10.2：真实授权现场实弹攻防基准 (Authorized Live Target Benchmark)
* **核心目标**：用真实的授权外部资产验证全链路有效性，取代单机 Mock 自嗨。
* **交付要素**：
  1. **双轨验证矩阵 (Dual-Track Benchmark Framework)**：
     * **轨道 A (Local Fixture)**：确定性回归，验证逻辑正确性；
     * **轨道 B (Authorized Live Target)**：真实资产交互，验证漏洞挖掘与突破有效性。
  2. **低风险渐进式发包策略**：
     * 严格遵守只读与认证差分发包；
     * 涉及破坏性动词（DELETE / 清库 / 重置）强制置为高危并阻断，直到人类明确签署授权。

### Phase 10.3+：复杂前端无头浏览器扩展 (Playwright & SPA DOM Exploration)
* **核心目标**：从纯 HTTP 维度扩展至现代前端渲染与浏览器上下文攻击面。
* **交付要素**：
  * 引入 Playwright 适配器作为 Tool Gateway 的特权组件；
  * 捕获 DOM 事件、跨域通信 (postMessage)、前端 Storage 状态与动态路由流。

---

## 四、 第三方资产与开源合规准则 (Provenance & Compliance Protocol)

在项目根目录下正式建立并持久化维护知识产权与来源追踪体系：

1. **结构落地**：
   * 建立 `docs/compliance/THIRD_PARTY_NOTICES.md`：记录所有吸收的思想、结构模板及其原始许可说明；
   * 建立 `docs/compliance/provenance_ledger.json`：追踪每一个技能剧本、算子模型的灵感来源。
2. **严格隔离原则**：
   * 对 `Shannon` (AGPL-3.0)：严格限制在**“架构白皮书阅读与原理推演”**，代码实现由团队自主根据 Invar 契约重构，**物理隔离其任何源码片段进入 Git 历史**；
   * 对 `Strix` / `Anthropic Harness` (Apache 2.0)：合法引用其接口设计，并在派生或参考模块头部完整保留原作者著作权声明与 NOTICE 引用。

---

## 五、 Phase 9.7 施工硬核验收标准 (Definition of Done)

为确保进入 Phase 9.7 代码实现阶段时不偏离航线，我们预先锁定该阶段必须无条件满足的 **10 大物理验收门禁**：

1. **[零字符串漏洞]** `ToolRequest` 不存在 `extra_args` 或类似的无约束 `List[str]` 字段。
2. **[零凭据外泄]** 生成的所有审计记录、日志与可观测事件中，`Authorization`、`Token`、`Cookie` 明文泄漏率为 **0%**。
3. **[纯真物理物证]** `ToolResult` 包含未处理的原始响应字节流 (Raw Bytes) 文件路径，物理 Content-Hash 基于原始字节直接生成。
4. **[零伪造状态码]** 响应解析失败时输出专门的强类型异常事实，HTTP 状态码绝不被篡改或默认置为 200。
5. **[策略默认安全]** TLS 证书校验默认开启，除非显式配置覆盖，否则禁止发起非信任发包。
6. **[物理 RoE 门禁]** 在产生任何本地 Socket 连接或 CLI 进程前，完成域名白名单、排除路径及动词核验；违规发包阻断率 **100%**。
7. **[100% 本地确定性测试]** 测试套件完全依赖本地回环桩，不依赖任何不可控外部网络，断言不存在二义性分支。
8. **[契约单射映射]** `ToolResult` 能够无损转换为 Invar 既有的 `EvidenceRecord` 实体，完全兼容后续不变量评估。
9. **[旧路径零重复]** 新的 Tool Gateway 明确取代旧有的直接调用方式，系统不建立平行的第二套发包逻辑。
10. **[历史全量回归]** 既有 287 项单元/契约测试保持 **100% 全绿通过**。

