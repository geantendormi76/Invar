# Invar AI 可复现工程规格书

**版本**：1.0  
**整理日期**：2026-09-15  
**工程对象**：Invar Rust + Python 双引擎研究系统  
**规格定位**：可迁移、可复用、可测试、可审计的 AI 工程复现规范  
**适用范围**：复杂 AI 工程、Agent、研究自动化、分析引擎、推理/执行引擎、桌面应用与安全研究工具链

---

## 0. 规格书定位

本规格书不是项目 README，也不是一次性重构计划。

它的目标是把本轮 Invar 演进中已经被真实代码、测试、编译器反馈和项目文档验证过的技术，整理成一个新 AI 会话可以复现、其他项目可以迁移的工程规格。

核心要求：

```text
有依据才实现
有契约才扩展
有测试才交付
有证据才晋级
```

本规格书中的内容分为四类：

| 标记 | 含义 |
|---|---|
| [FACT] | 当前源码、测试、编译器或项目档案直接支持的事实 |
| [DERIVED] | 从多个事实归纳出的可复用架构原则 |
| [RECOMMENDED] | 为复现工程而给出的规范化建议，不等同于历史源码事实 |
| [SECURITY] | 为安全研究场景建立的安全边界 |

不得把 [RECOMMENDED] 或 [DERIVED] 反写成“原项目已经实现”。

---

# 1. 工程目标与核心哲学

## 1.1 总目标

将历史的脚本式、强耦合研究代码逐步演进为：

```text
确定性工具
    ↓
研究模型 / 契约
    ↓
Skill 工作流策略
    ↓
可替换执行器
    ↓
证据轨迹
    ↓
知识晋级
    ↓
下一轮研究任务
```

系统要同时满足：

```text
可复现
可测试
可追溯
可替换
可扩展
可审计
```

## 1.2 通用工程最高标准

所有核心模块应尽量满足：

> **高内聚、低耦合、高鲁棒性、热拔插。**

定义：

- **高内聚**：单模块承担清晰、完整、可验证的职责。
- **低耦合**：模块之间依赖稳定接口，而不是彼此内部实现。
- **高鲁棒性**：异常输入、边界条件、依赖变化时仍保持可控行为。
- **热拔插**：一个执行器、算法、工具或适配器被替换时，其他层尽量无需修改。

## 1.3 零特判、纯泛化

通用修复路径：

```text
发现特殊案例
    ↓
寻找共性规律
    ↓
建立统一抽象
    ↓
类型 / 接口 / 策略
    ↓
通用实现
```

禁止：

```text
某个案例
    ↓
if 特判
    ↓
继续堆补丁
```

尤其禁止硬编码：

```text
文件名
用户名
ID
真实 URL
真实 Token
特定参数值
单一数据样本
单一模型名称
单一返回值
```

---

# 2. 架构母模型

## 2.1 五层研究边界

Invar 形成如下一级概念：

```text
             Research Goal / Security Invariant
                           |
                           v
                    +-------------+
                    |    Agent    |
                    | plan/reason |
                    +-------------+
                           |
                     selects tools
                           v
                    +-------------+
                    |    Skill    |
                    | workflow    |
                    +-------------+
                           |
                 deterministic tool calls
                           v
    +------------------------------------------------+
    |                    Harness                     |
    | AST | Risk | Transport | Feedback | Mutation  |
    +------------------------------------------------+
                           |
                           v
                    +-------------+
                    |  Evidence   |
                    | trace/log   |
                    +-------------+
                           |
                           v
                    +-------------+
                    |  Knowledge  |
                    | facts       |
                    +-------------+
                           |
                           +-----> next task
```

[FACT] 本结构已经在 Invar 架构文档中明确提出。

## 2.2 层职责

### Agent

职责：

```text
目标理解
研究规划
假设生成
工具选择
分支选择
```

不要承担：

```text
HTTP 底层实现
AST 解析底层实现
Payload 具体变异实现
证据格式细节
```

### Skill

职责是**流程策略**，不是“大 Python 类”。

示例：

```text
extract
→ classify
→ select invariant
→ observe
→ interpret
→ mutate
→ verify
→ persist
```

Skill 定义：

```text
任务顺序
选择条件
停止条件
安全边界
```

Agent 可以调整研究路径，但不应绕过 Skill 的安全边界。

### Harness

Harness 提供确定性工具：

```text
AST extractor
Risk / policy tool
HTTP transport
Feedback interpreter
Mutation policy
Evidence bridge
```

Harness 尽量做到：

```text
给定相同输入
    ↓
产生可重复的结果
```

### Evidence

Evidence 不是最终结论。

它是研究过程的证据轨迹：

```text
attempt 1
attempt 2
attempt 3
...
```

### Knowledge

知识晋级：

```text
observation
    ↓
candidate
    ↓
verified
    ↓
knowledge
```

只有证据明确支持的结果才能晋级为 verified / knowledge。

---

# 3. Rust + Python 双引擎职责模型

## 3.1 总体边界

[FACT]

当前 Invar 的长期方向是：

```text
Rust
= 系统级总控 / 编排 / 生命周期 / 进程 / IPC / 资源 / 并发 / 强类型契约

Python
= 专业研究算法 / AI / ML / 快速实验 / 现有研究生态
```

即：

```text
Rust Brain
        +
Python Specialist Engine
```

而不是：

```text
Rust replaces Python everywhere
```

## 3.2 为什么不是全部 Rust

Python 更适合：

```text
机器学习
AI SDK
研究原型
数据处理
快速实验
现有安全研究生态
```

Rust 更适合：

```text
进程生命周期
并发边界
系统资源
进程间通信
桌面系统集成
稳定 API
强类型状态机
```

[DERIVED] 因此最优边界不是“谁更快”，而是“谁更适合承担哪一类职责”。

---

# 4. 项目目录作为工程类型系统

## 4.1 基本原则

[FACT]

已存在目录结构属于一级工程契约。

创建文件之前必须先回答：

```text
这个文件是什么类型？
属于什么职责？
生命周期是什么？
由谁生产？
由谁消费？
```

## 4.2 Invar 目录模型

典型布局：

```text
C:\dev\Invar
├── c\
│   └── 认知中枢 / 架构 / 交接 / 规格
├── data\
│   └── 数据集 / 测试资产
├── models\
│   └── 模型权重
├── tmp\
│   └── 临时实验
├── src\
│   └── 前端表现层
├── src-tauri\
│   ├── crates\
│   │   ├── src\
│   │   └── tests\
│   └── python\
├── scripts\
│   ├── pipeline\
│   └── audit\
└── tests\
    └── 全局 E2E
```

[FACT] 当前仓库 README 与交接文档均采用这种职责划分。

## 4.3 测试目录边界

Rust：

```text
src\
    单元测试 / 生产模块内局部行为

tests\
    集成测试 / 契约测试 / 黑盒测试
```

已经验证的错误案例：

```text
错误：
crates\src\orchestrator_contract_test.rs

正确：
crates\tests\orchestrator_contract_test.rs
```

不能为了方便把 integration test 塞回 `src`。

---

# 5. 类型即契约

重要数据流必须能够回答：

```text
输入是什么？
输出是什么？
谁产生？
谁消费？
约束是什么？
失败如何表达？
```

核心契约优先使用：

```text
struct
enum
trait / interface
typed state
explicit error
versioned message
```

避免：

```text
隐式约定
魔法字符串
无限制字典
全局变量
隐藏副作用
空字符串冒充 Optional
```

---

# 6. 历史代码迁移方法

## 6.1 不复制旧目录作为新架构

旧结构：

```text
js_ast/
├── core/
├── analysis/
├── runtime/
└── experiments/
```

不应直接变成新架构。

正确迁移：

```text
legacy implementation
        ↓
行为 / 算法 / 数据契约考古
        ↓
识别稳定共性
        ↓
新 contract
        ↓
适配旧实现
        ↓
新实现
        ↓
逐步删除兼容层
```

## 6.2 1:1 行为迁移的正确理解

“1:1 迁移”指的是：

```text
输入语义
输出语义
错误语义
关键算法行为
数据字段含义
```

应保持兼容。

不等于：

```text
旧目录 1:1 复制
旧类名 1:1 复制
旧全局变量 1:1 复制
旧 hardcode 1:1 复制
```

---

# 7. Python 核心可复用接口

## 7.1 EndpointIR

EndpointIR 是：

> **代码世界 → API 世界** 的事实抽取结果。

它不应承担：

```text
研究假设
研究历史
证据轨迹
最终结论
```

这些内容应进入 ResearchCase。

## 7.2 Transport

当前结构：

```text
TransportResponse
├── status_code
├── text
└── headers

HttpTransport
└── request(...)
```

设计原则：

```text
Executor
    ↓
HttpTransport
    ↓
HTTP library
```

而不是让 Executor 直接散落 `requests.*` 调用。

## 7.3 FeedbackInterpreter

职责：

```text
HTTP response
    ↓
结构化反馈事实
```

示例：

```text
Go validator required field
        ↓
FeedbackFact
        ↓
missing_required_field
        ↓
field = OutTradeNo
```

重要原则：

> 响应解析与 Payload 变异必须分离。

## 7.4 MutationPolicy

职责：

```text
字段语义
    ↓
默认值推断
```

以及：

```text
反馈事实
    ↓
新 Payload
    ↓
mutation reason
```

当前历史兼容行为包括：

```text
id / num / count / amount / price / status
    → 1

is_ / confirm / active / enabled
    → True

email
    → 示例邮箱

其他
    → 通用测试占位值
```

注意：

这是**当前兼容实现行为**，不是建议对所有未来系统照抄的硬编码规则。

更通用的升级方向：

```text
field name
    ↓
declared schema / extracted type
    ↓
semantic hint
    ↓
typed default generator
```

---

# 8. ResearchCase 研究状态模型

当前 Python 真实模型：

```text
ResearchCase
├── case_id
├── endpoint
├── invariants
├── hypotheses
├── attempts
├── decision
└── metadata
```

## 8.1 SecurityInvariant

```text
invariant_type
statement
```

用途：

明确要求验证的系统性质。

## 8.2 Hypothesis

```text
hypothesis_id
statement
rationale
```

用途：

记录：

```text
当前假设是什么
为什么提出
```

## 8.3 ProbeAttempt

```text
attempt_number
payload
status_code
response_preview
interpretation
mutation_reason
```

其中 attempt_number 必须连续：

```text
1
2
3
...
```

跳号必须失败。

已验证的行为：

```text
expected = len(attempts) + 1

if actual != expected:
    ValueError
```

这是很有价值的通用 invariant：

> **研究轨迹必须有确定顺序。**

## 8.4 ResearchDecision

```text
status
rationale
```

`decision` 可以为空：

```text
decision = None
```

因此 Rust 对应：

```rust
Option<ResearchDecision>
```

而不是：

```rust
decision_rationale: String
```

因为：

```text
None
```

和：

```text
Some(ResearchDecision)
```

是两个不同的领域状态。

---

# 9. ResearchExecutionResult

当前 Python：

```text
ResearchExecutionResult
├── evidence
├── research_case
└── evidence_history
```

这里体现一个关键分层：

```text
ResearchCase
= 研究状态

Evidence
= 证据结果

ResearchExecutionResult
= 一次研究执行后的聚合结果
```

不要把三个概念压成一个大对象。

---

# 10. AdaptiveSandboxExecutor 的可复用设计

当前 Executor 已经从“大而全执行器”开始拆分：

```text
AdaptiveSandboxExecutor
├── InvarConfig
├── HttpTransport
├── FeedbackInterpreter
├── MutationPolicy
├── ResearchCase
├── ProbeAttemptEvidenceMapper
└── ResearchExecutionResult
```

## 10.1 关键接口

```python
_build_url(endpoint, base_url=None)

_probe_endpoint_with_research_case(
    endpoint,
    base_url=None
)

probe_endpoint_with_research(
    endpoint,
    base_url=None
) -> ResearchExecutionResult

probe_endpoint(
    endpoint,
    base_url=None
) -> EvidenceRecord

probe_all(
    endpoints,
    base_url=None
) -> List[EvidenceRecord]
```

## 10.2 URL 覆盖语义

当前真实行为：

```text
显式 base_url
    ↓
优先使用

否则
    ↓
cfg.target_api_base
```

并进行：

```text
rstrip("/")
+
"/"
+
lstrip("/")
```

从而避免：

```text
https://example.com//
```

这类简单边界错误。

---

# 11. 自适应研究闭环算法

可复用的核心思想：

```text
初始结构
    ↓
确定性生成初始输入
    ↓
执行一次 observation
    ↓
解释 response
    ↓
提取 feedback facts
    ↓
决定是否存在有效 mutation
    ↓
生成下一 payload
    ↓
再次 observation
    ↓
记录 attempt
    ↓
直到停止条件满足
```

标准化伪代码：

```python
case = create_research_case(endpoint)
payload = build_initial_payload(endpoint)

for round_index in range(max_rounds):
    response = observe(endpoint, payload)
    facts = interpret(response)

    record_attempt(
        case=case,
        payload=payload,
        response=response,
        facts=facts,
    )

    decision = evaluate_stop_conditions(
        response=response,
        facts=facts,
        case=case,
    )

    if decision.should_stop:
        break

    mutation = mutation_policy.propose(
        payload=payload,
        facts=facts,
    )

    if not mutation.changed:
        break

    payload = mutation.payload

return ResearchExecutionResult(...)
```

## 11.1 停止条件

当前架构文档定义的通用停止条件：

```text
明确的 verified 结果
显式拒绝假设
目标/网络策略阻断
没有新反馈事实
达到最大迭代次数
```

不要无限循环。

---

# 12. Evidence 证据桥接

核心接口：

```text
ProbeAttemptEvidenceMapper.to_evidence(...)
ProbeAttemptEvidenceMapper.to_evidence_records(...)
```

目标：

```text
ProbeAttempt
    ↓
EvidenceRecord
```

这实现：

```text
研究模型
    →
传统证据模型
```

从而可以在不一次性重写全部报告系统的情况下，把新研究闭环接入旧证据链。

这是非常值得复用的迁移技术：

> **先做 adapter / bridge，再删除旧模型。**

---

# 13. Pipeline 与 Executor 的边界

## 13.1 Pipeline

`scan_pipeline.py` 当前承担：

```text
输入解析
    ↓
AST extractor
    ↓
RiskEngine
    ↓
AdaptiveSandboxExecutor
    ↓
报告输出
```

它属于：

> **工作流编排器 / Skill runner / CLI adapter**

## 13.2 Executor

Executor 属于：

> **单一研究执行边界**

因此：

```text
Pipeline
    ↓
调用 Executor
```

而不是：

```text
Executor
    ↓
自己负责所有 pipeline
```

## 13.3 长期目标

最终：

```text
Rust
    ↓
Skill / orchestration
    ↓
Python adapter
    ↓
Research executor
```

但迁移必须渐进。

---

# 14. Rust 总控的可复用核心

## 14.1 Library / Binary / Integration Test 三层

最终结构：

```text
crates/
├── src/
│   ├── lib.rs
│   ├── main.rs
│   └── orchestrator.rs
└── tests/
    └── orchestrator_contract_test.rs
```

职责：

```text
lib.rs
    ↓
公开核心 API

main.rs
    ↓
最薄的 binary 入口

orchestrator.rs
    ↓
编排 / 契约

tests/
    ↓
集成契约
```

## 14.2 Rust 强类型研究契约

当前最小契约：

```rust
ResearchTask {
    task_id: String,
    method: String,
    path: String,
}
```

```rust
ResearchDecision {
    status: String,
    rationale: String,
}
```

```rust
ResearchResult {
    task_id: String,
    status: String,
    attempts: u32,
    decision: Option<ResearchDecision>,
    evidence_history_count: u32,
}
```

## 14.3 可替换 Executor

核心接口：

```rust
pub trait ResearchExecutor {
    fn execute(
        &self,
        task: &ResearchTask
    ) -> ResearchResult;
}
```

编排器：

```rust
ResearchOrchestrator<E: ResearchExecutor>
```

意义：

```text
orchestrator
    ↓
trait
    ↓
真实 executor / fake executor / future executor
```

这样测试不依赖真实网络或真实 Python 进程。

---

# 15. Rust JSON 契约策略

已验证：

```text
ResearchTask
    ↕
JSON
```

以及：

```text
ResearchResult
    ↕
JSON
```

能够往返。

通用原则：

```text
Rust typed struct
    ↓
serde
    ↓
JSON
```

JSON 是：

> 跨语言传输表示

而不是：

> Rust 内部领域模型的替代品。

不要因为 Python 使用动态 `dict`，就在 Rust 中全面退化为：

```rust
serde_json::Value
```

优先保持强类型，只有真正的开放数据边界才使用动态值。

---

# 16. 跨语言契约对账规则

下一阶段必须按此流程进行：

```text
Python 真实模型
    ↓
读取真实 EndpointIR
    ↓
读取 ResearchCase.to_dict()
    ↓
字段逐项对账
    ↓
判断公共契约
    ↓
编写红灯测试
    ↓
最小 Rust 修改
    ↓
绿灯
```

对账表建议：

| Python 字段 | Python 类型 | Rust 候选类型 | 是否跨语言 | 理由 |
|---|---|---|---|---|
| task/case id | str | String | 是 | 路由研究实例标识 |
| method | str | String / enum | 是 | 执行任务基本事实 |
| path | str | String | 是 | 执行任务基本事实 |
| endpoint 内部附加字段 | EndpointIR | 待核实 | 待定 | 先读真实模型 |
| invariants | list | 待设计 | 待定 | 研究目标上下文 |
| hypotheses | list | 待设计 | 待定 | 是否由 Agent 控制 |
| attempts | list | 待设计 | 待定 | 是否跨语言完整传输 |
| decision | Optional | Option<...> | 很可能是 | 已确认 Optional 语义 |
| metadata | dict | 不应直接复制 | 通常否 | 内部实现信息 |
| evidence | Any | 待设计 | 待定 | 需要明确证据契约 |
| evidence_history | list[Any] | 待设计 | 待定 | 需确定传输粒度 |

原则：

> **没有真实源码依据，就不填最终类型。**

---

# 17. 测试策略

## 17.1 TDD 闭环

标准流程：

```text
现象
→ 最小测试
→ 红灯
→ 定位根因
→ 最小修改
→ 绿灯
→ 回归
```

不要跳过红灯。

## 17.2 测试不是“让代码通过”

测试应该表达：

```text
架构意图
数据契约
行为 invariant
错误语义
兼容性
```

## 17.3 当前已经验证的测试类别

Python：

```text
Transport
Feedback
MutationPolicy
Research loop
Evidence bridge
Evidence history
Execution result
base_url compatibility
Pipeline integration
```

最近一次相关 Python 回归：

```text
7 passed / 0 failed
```

Rust：

```text
Replaceable executor
ResearchTask JSON round-trip
ResearchResult JSON round-trip
Optional decision
Decision context
```

最近一次：

```text
library unit tests: 1 passed
integration tests: 4 passed
warnings: 0
errors: 0
```

---

# 18. 测试验收矩阵

一个可复用的研究系统至少应有以下验收层：

| 层 | 最小验收 |
|---|---|
| 类型层 | struct / enum 构造与约束 |
| 序列化层 | JSON round-trip |
| 单元层 | 核心算法 |
| 契约层 | 输入输出稳定 |
| 集成层 | 模块接缝 |
| 回归层 | 旧行为不被破坏 |
| E2E 层 | 完整工作流 |
| 安全门禁 | 禁止真实凭据/目标泄露 |

---

# 19. 静态迁移门禁

当前项目已经提出 `scripts/audit/refactor_gate.py` 一类静态门禁。

其思想：

```text
扫描源代码
    ↓
发现建筑性回归
    ↓
失败
```

目前用于捕获：

```text
hard-coded bearer token
password dictionary
live target default
```

注意：

> 静态门禁不能证明系统绝对安全，只能阻止已定义的架构回归。

通用化后可继续扩展：

```text
真实 Secret
真实目标 URL
危险默认配置
测试专用分支
禁用 TLS 验证
异常吞噬
无界循环
硬编码业务 ID
```

---

# 20. 历史技术中可复用的算法思想

## 20.1 AST → EndpointIR

历史系统最有价值的算法资产之一：

```text
前端 JavaScript
    ↓
AST
    ↓
路由 / Method / Path
    ↓
参数提取
    ↓
EndpointIR
```

价值：

```text
减少模型上下文
降低 token 成本
结果可重复
支持批量处理
```

这类“确定性预处理先做数据降维”的思想可推广到：

```text
代码审计
日志分析
配置分析
协议解析
数据抽取
```

## 20.2 反馈驱动 Payload 演化

历史实现中可抽象为：

```text
Initial Payload
    ↓
Backend Feedback
    ↓
Extract Fact
    ↓
Mutation
    ↓
Re-observe
```

关键不是某个具体字段，而是：

> **让系统从被测环境反馈中获得下一轮输入所需的信息。**

## 20.3 多轮而非单轮推理

传统：

```text
静态分析
    ↓
一次请求
    ↓
最终结论
```

升级：

```text
分析
→ 假设
→ observation
→ feedback
→ mutation
→ observation
→ evidence
→ conclusion
```

这个闭环特别适合 AI Agent。

---

# 21. 哪些历史内容不能复用

历史资料中曾出现：

```text
真实 JWT
真实账号
真实目标 URL
真实认证 Header
密码字典
会话接管
主动 exploit
限流绕过
```

[SECURITY] 这些不能进入通用 Harness。

复用规则：

```text
攻击材料
    ↓
提取算法思想
    ↓
抽象成 operator
    ↓
fixture / mock / localhost
    ↓
测试
```

不要：

```text
复制历史脚本
→ 换个类名
→ 放进新项目
```

---

# 22. 安全研究 Operator 插槽

通用 Skill 可使用以下 operator 槽位：

```text
ast.extract
risk.classify
http.observe
response.interpret
payload.mutate
idor.compare
jwt.inspect
rate_limit.observe
evidence.persist
```

安全边界：

```text
idor.compare
    → lab / fixture target only

jwt.inspect
    → 默认仅 decode / inspect

rate_limit.observe
    → 默认只检测，不携带绕过策略
```

凭据、目标 ID、令牌、密码字典：

```text
外部注入
    ↓
授权环境
```

而不是写进 reusable Skill。

---

# 23. 可复用接口模板

## 23.1 Tool Interface

```text
Tool
├── name
├── input schema
├── output schema
├── errors
├── deterministic guarantee
└── side effects
```

## 23.2 Skill Interface

```text
Skill
├── goal
├── preconditions
├── steps
├── decision points
├── stop conditions
├── safety policy
└── artifacts
```

## 23.3 Executor Interface

```text
Executor
├── execute(task)
├── typed result
├── controlled side effects
├── bounded iteration
└── injectable dependencies
```

## 23.4 Evidence Interface

```text
Evidence
├── attempt id
├── input
├── observation
├── interpretation
├── mutation reason
├── timestamp
└── provenance
```

## 23.5 Knowledge Interface

```text
Knowledge
├── source evidence
├── claim
├── confidence
├── state
└── provenance
```

---

# 24. 故障与异常设计

错误不能通过：

```text
except Exception:
    pass
```

无限吞掉。

对于生产系统，建议：

```text
可恢复异常
    → structured error

不可恢复异常
    → fail fast / terminate bounded task

研究失败
    → ResearchDecision / explicit failure state
```

并保留：

```text
失败原因
发生阶段
相关 task_id
attempt number
```

[DERIVED] 研究系统的失败本身也是数据。

---

# 25. 配置与环境隔离

配置应通过：

```text
环境变量
配置文件
CLI 参数
注入对象
```

不要写死：

```text
真实 API
真实 token
真实路径
个人目录
```

同时允许：

```text
base_url override
timeout override
worker count
custom headers
```

这样才能：

```text
local
CI
lab
mock
staging
production-like
```

之间切换。

---

# 26. 可复现运行模型

推荐运行链：

```text
固定输入 fixture
    ↓
固定配置
    ↓
固定版本
    ↓
确定性工具
    ↓
结构化输出
    ↓
snapshot / JSON
    ↓
测试比较
```

研究实验若存在随机性，应显式记录：

```text
seed
model/version
prompt version
tool version
config version
timestamp
```

这样才能回放。

---

# 27. AI 实现提示词：工程总控版

下面这段可直接作为新项目 AI 编程会话的基础提示词。

```text
你是本项目的工程架构师、代码实现器、测试执行器和技术研究助手。

最高原则：

1. 有依据才实现。
2. 有抽象才扩展。
3. 有测试才交付。
4. 不凭空猜接口。
5. 不复制历史硬编码。
6. 不围绕单个案例堆 if 特判。
7. 不为了通过测试修改生产行为。
8. 不机械重写已有成熟实现。
9. 优先复现真实代码已经证明的行为。
10. 目录结构属于一级工程契约。

执行顺序：

理解问题
→ 读取真实源码
→ 读取已有测试
→ 识别现有数据流
→ 确认职责边界
→ 定义最小契约
→ 先写最小红灯测试
→ 定位根因
→ 最小生产修改
→ 绿灯
→ 回归
→ 再进入下一步。

如果发现复杂度上升，优先检查：
“是否缺少抽象？”
而不是增加更多特殊分支。

如果需要创建文件：
先判断文件类型、职责和生命周期，
严格放入已有目录。
集成测试必须进入项目规定的 tests 目录。

如果系统采用多语言：
不要复制另一语言的内部对象。
只建立真正需要跨语言的稳定公共契约。

跨语言通信必须优先：
强类型 schema
→ JSON/IPC contract
→ round-trip test
→ adapter
→ process integration。

安全研究环境：
默认使用 fixture / mock / localhost。
禁止把真实 Token、真实目标、真实凭据、密码字典和 exploit payload 写入 reusable module。
只提取算法思想并做受控验证。

输出代码时：
给出完整文件内容。
不要省略关键逻辑。
不要使用 TODO 替代实现。
不要假设隐藏文件存在。

每完成一个局部修改：
立即测试。
等待结果。
不要一次跨越多个未验证阶段。
```

---

# 28. AI 实现提示词：研究闭环版

```text
你正在实现一个基于确定性工具的研究 Skill。

研究流程：

1. Extract
2. Classify
3. Select invariant
4. Form behavior hypothesis
5. Form authorization hypothesis
6. Observe
7. Interpret feedback
8. Mutate within policy
9. Re-observe
10. Record evidence
11. Evaluate stop condition
12. Promote only verified claims

要求：

- 工具必须尽量确定性。
- Skill 负责顺序和停止条件。
- Agent 负责规划和分支。
- Evidence 必须记录逐轮轨迹。
- Knowledge 不得直接来自未经验证的模型推测。
- 单次异常响应不得直接等价于漏洞结论。
```

---

# 29. AI 实现提示词：跨语言契约版

```text
先读取 Python 真实模型和真实接口。

不要直接把 Python dataclass 全量翻译成 Rust。

建立字段对账表：

Python field
Python type
Semantic meaning
Producer
Consumer
Rust candidate
Cross-language required?
Optional?
Error semantics?

然后：

1. 选择最小公共契约。
2. 写 Rust JSON round-trip 测试。
3. 写 Python/Rust 字段兼容测试。
4. 红灯。
5. 最小修改。
6. 绿灯。
7. 回归。
8. 最后再实现 subprocess / IPC。

任何字段无法证明必须跨语言：
默认暂留 Python 内部。
```

---

# 30. AI 实现提示词：代码修改版

```text
不要先写大重构。

先执行：
- 查看目标文件
- 查看上下游调用
- 查看相关测试
- 查看目录规则

然后只做一个逻辑变更。

输出：
1. 当前目标
2. 真实代码事实
3. 最小设计
4. 修改文件
5. 完整写文件命令
6. 测试命令
7. 验收标准

执行后等待终端输出。

没有看到测试结果之前：
不要假设成功。
不要继续下一步。
```

---

# 31. 已验证的踩坑清单

## 坑 1：先设计大 Agent

错误：

```text
不了解 Executor / Pipeline
→ 直接设计总 Agent
```

修复：

```text
先读真实接口
→ 最小编排契约
→ 再 Agent
```

## 坑 2：为了性能把 Python 全部 Rust 化

修复：

```text
Rust = system brain
Python = specialist
```

## 坑 3：把 integration test 放进 src

修复：

```text
crates/tests/
```

## 坑 4：没有 lib.rs 就直接写 integration test

修复：

```text
src/lib.rs
```

先建立 library boundary。

## 坑 5：错误处理 crate 名

当前真实配置：

```toml
[package]
name = "Invar-core"

[lib]
name = "invar_core"
```

测试：

```rust
use invar_core::...
```

## 坑 6：用 lint suppression 掩盖结构问题

不要：

```rust
#[allow(non_snake_case)]
```

优先修正确的 crate identifier。

## 坑 7：Optional 被压缩为空字符串

错误：

```text
None → ""
```

正确：

```text
Option<T>
```

## 坑 8：凭经验猜源码

正确：

```text
真实文件
→ 真实调用
→ 真实测试
→ 编译器反馈
```

## 坑 9：为了测试创造生产分支

禁止：

```text
if test_case_001
if test_mode
```

应通过 dependency injection / fake executor / fixture。

## 坑 10：历史 exploit 原样迁移

只提取：

```text
算法
数据流
反馈模式
```

不复制：

```text
目标
凭据
攻击材料
```

## 坑 11：一次做太多修改

坚持：

```text
one logical change
→ test
→ result
→ next
```

---

# 32. 从本项目提炼出的“最小可复现核心”

如果其他项目只需要复制最精华的部分，建议从以下组件开始：

```text
core/
├── contracts
│   ├── Task
│   ├── Decision
│   └── Result
├── executor
│   └── interface
├── evidence
│   └── Attempt / Record
└── orchestration
    └── Orchestrator
```

然后增加：

```text
tools/
├── parser
├── transport
├── interpreter
└── mutation_policy

skills/
└── research_skill

adapters/
└── language / process / IPC

tests/
├── contract
├── unit
├── integration
└── e2e
```

---

# 33. 推荐的项目演进顺序

不要一次完成全部系统。

建议：

```text
Phase 1
确定性工具 + contracts

Phase 2
ResearchCase + Evidence

Phase 3
可替换 Executor

Phase 4
Skill runner

Phase 5
Rust system orchestrator

Phase 6
JSON / IPC contract

Phase 7
Python specialist adapter

Phase 8
Knowledge promotion

Phase 9
Agent planning

Phase 10
高级研究 operator
```

其中越靠后的层越不应该在底层契约尚未稳定时提前实现。

---

# 34. 复现验收清单

新项目完成一个阶段后，至少验证：

```text
[ ] 真实源码已检查
[ ] 目录职责正确
[ ] 输入输出契约明确
[ ] Optional 语义正确
[ ] 错误语义明确
[ ] 没有新增硬编码目标
[ ] 没有真实凭据
[ ] 有最小红灯测试
[ ] 红灯原因明确
[ ] 最小修改后绿灯
[ ] 相关 regression 通过
[ ] integration boundary 正确
[ ] JSON round-trip 通过
[ ] adapter 可替换
[ ] stop condition 明确
[ ] evidence 可追溯
[ ] knowledge 有来源
```

---

# 35. 当前 Invar 真实状态

截至 2026-09-15：

```text
Python
├── Transport                   ✅
├── FeedbackInterpreter         ✅
├── MutationPolicy              ✅
├── ResearchCase                ✅
├── ResearchDecision            ✅
├── ProbeAttempt                ✅
├── ResearchExecutionResult     ✅
├── Evidence Bridge             ✅
├── Sandbox Executor             ✅
├── Pipeline seam               ✅
└── Related regression           ✅

Rust
├── Workspace                    ✅
├── Library crate                ✅
├── Binary entry                 ✅
├── ResearchTask                 ✅
├── ResearchDecision             ✅
├── ResearchResult               ✅
├── ResearchExecutor trait       ✅
├── ResearchOrchestrator         ✅
├── JSON round-trip              ✅
├── Integration tests             ✅
└── Python IPC                   ⏳
```

重要：

> Rust 总控尚未完成。

当前完成的是：

> **Rust 总控的最小强类型契约骨架。**

下一步应继续：

```text
真实 EndpointIR
    ↓
真实 ResearchCase.to_dict()
    ↓
字段逐项对账
    ↓
最小公共跨语言契约
    ↓
IPC / subprocess
```

---

# 36. 事实来源与证据地图

本规格书主要依据以下工程材料：

1. `c/HANDOFF.md`  
   当前会话交接、真实测试状态、Rust 架构演进和踩坑记录。

2. `c/ARCHITECTURE.md`  
   Research Architecture v1、Agent / Skill / Harness / Evidence / Knowledge 五层模型、迁移顺序与安全边界。

3. `scripts/audit/refactor_gate.py`  
   静态迁移门禁与可复用架构回归扫描思想。

4. `src-tauri/python/src/skills_web_api_research.md`  
   Web API Research Skill 的 workflow、reasoning contract、stop conditions、operator slots。

5. `tests/test_refactor_contracts.py`  
   研究契约、attempt 单调性、feedback 解释等测试范式。

6. 历史 `js_ast` 代码归档  
   用于算法考古和行为迁移。只提取算法思想，不复制真实攻击材料。

7. `通用 AI 工程研究与软件系统开发宪法 v4.0`  
   零臆造、零无依据特判、目录即类型系统、TDD、已有工程优先、高内聚低耦合高鲁棒性热拔插等母规范。

---

# 37. 最终复现原则

一个新的 AI 会话不应该从：

```text
“帮我写一个 Agent”
```

开始。

正确起点是：

```text
读取真实源码
    ↓
读取真实接口
    ↓
读取真实测试
    ↓
画出数据流
    ↓
定义最小边界
    ↓
红灯
    ↓
最小修改
    ↓
绿灯
    ↓
回归
    ↓
继续下一层
```

最终工程模型：

```text
       Agent
         │
       Skill
         │
   typed contracts
         │
   deterministic tools
         │
      Harness
         │
      Evidence
         │
      Knowledge
         │
   next research task
```

系统不追求某一个模块局部“最聪明”，而追求整个系统：

```text
可复现
+
可解释
+
可测试
+
可替换
+
可扩展
+
可审计
```

这就是本规格的核心工程不变量。
