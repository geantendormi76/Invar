# Invar 运行轨道契约 v1.0

## 1. 契约定位

本契约定义 Invar 的运行轨道（Run Track）模型。

运行轨道不是独立产品，不允许复制核心安全引擎，不允许形成平行代码体系。

Invar 必须保持：

```text
一套核心安全内核
+
一套统一数据契约
+
一套统一证据体系
+
多种运行轨道
+
统一升级机制
```

核心目标：

```text
Production 为默认入口
Research 为深度能力
Intelligence 为知识供给
Benchmark 为内部验证
```

---

# 2. 顶层架构

Invar 的运行结构定义为：

```text
                           Invar
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        Production       Research      Intelligence
         生产生成轨      深度研究轨       安全情报轨
              │              │              │
              └──────────────┼──────────────┘
                             │
                             ▼
                     Unified Core
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
      Evidence             Finding          Reporting
      Verification         Models            Export
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
                         Benchmark
```

Benchmark 不属于普通用户运行轨道，而属于内部工程验证系统。

---

# 3. 轨道优先级

轨道优先级固定为：

```text
P0  Production
P1  Research
P2  Intelligence
P3  Benchmark
```

这里的优先级表示：

```text
默认程度
资源投入
产品入口优先级
工程稳定性要求
```

不表示漏洞严重程度。

Production 永远是最高级默认运行轨道。

---

# 4. Production Track

## 4.1 定位

Production 是 Invar 的：

> 默认运行模式、日常生成模式、主要产出模式。

主要目标：

```text
低成本
高覆盖
高稳定性
快速反馈
快速获得候选
快速获得可提交证据
```

Production 优先保证：

> “系统可以稳定地每天运行。”

而不是：

> “每个任务都必须使用最复杂的研究能力。”

---

## 4.2 默认入口

默认命令语义：

```text
Invar scan <target>
```

必须进入：

```text
Production
```

禁止因为系统内部存在 Research 能力，就默认将所有任务送入 Research。

---

## 4.3 Production 标准流水线

```text
Scope
↓
Asset Discovery
↓
HTTP Surface
↓
JS / AST
↓
System-1
↓
Candidate Triage
↓
Deterministic Validation
↓
Evidence Capture
↓
Verification
↓
Finding
↓
Reporting
```

Production 可以调用 Research，但 Research 不属于 Production 的强制前置步骤。

---

## 4.4 Production 的核心原则

Production 必须遵循：

```text
事实优先
确定性优先
低成本优先
证据优先
失败隔离
按需升级
```

特别规定：

### LLM 不是 Production 的单点依赖

以下情况不得直接导致整个 Production Run 被判定为系统失败：

```text
LLM timeout
LLM unavailable
LLM malformed output
LLM finish_reason != stop
LLM reasoning failure
```

正确行为：

```text
LLM Failure
↓
记录失败事实
↓
保存已有观测
↓
进入可恢复状态
↓
尝试确定性路径
↓
必要时进入 Research
↓
仍无法闭环 → NEEDS_VALIDATION / BLOCKED
```

禁止：

```text
LLM Failure
↓
吞异常
↓
伪装完成
```

也禁止：

```text
LLM Failure
↓
自动推断“安全”
```

---

# 5. Production 自动升级机制

Production 必须支持 Escalation。

定义：

```text
Production
    │
    ├── Deterministic Fast Path
    │
    └── Escalation Decision
             │
             ├── 无需升级
             │
             ├── 可再次确定性验证
             │
             └── Research
```

Production 不直接承担所有复杂研究。

---

## 5.1 自动升级触发条件

升级条件必须由通用策略定义。

允许依据：

```text
候选价值
证据缺口
攻击面复杂度
业务边界复杂度
已有观察质量
历史知识匹配
确定性方法耗尽
```

禁止依据：

```text
某个特定 URL
某个特定域名
某个具体返回字符串
某一个样本
某一个模型名称
某一个历史漏洞
```

不得出现单案例特判。

---

# 6. Research Track

## 6.1 定位

Research 是：

> Invar 的研究级、高认知、高成本、深度验证运行轨道。

Research 必须完整保留现有研究级能力。

包括但不限于：

```text
Hypothesis
Mutation
Adaptive Selection
LLM Reflection
Research Loop
Replay
Semantic Differential
Security Invariant
Independent Verification
Evidence Gate
```

Research 是 Production 的高级能力，而不是另一个产品。

---

## 6.2 Research 入口

显式入口：

```text
Invar research <target>
```

或：

```text
Invar research --task <task-id>
```

但 Production 也可以通过升级策略自动进入 Research。

---

## 6.3 Research 的职责

Research 主要解决：

```text
普通验证无法闭环
复杂业务逻辑
复杂授权边界
多阶段状态
高价值候选
高难度语义差分
研究型假设验证
```

Research 不应被用来替代 Production 的基本能力。

---

# 7. Intelligence Track

## 7.1 定位

Intelligence 是：

> 网络安全知识搜集、整理、结构化和知识供给轨道。

它与“扫描目标是否存在漏洞”属于不同职责。

核心职责：

```text
安全资料采集
↓
知识提取
↓
结构化
↓
去重
↓
归一化
↓
知识索引
↓
模式沉淀
↓
反哺 Invar
```

---

## 7.2 Intelligence 的知识类型

允许形成：

```text
Vulnerability Pattern
Attack Technique
Protocol Knowledge
Framework Fingerprint
Vendor Behavior
Authentication Pattern
Authorization Pattern
Error Signature
Security Research Note
Historical Finding Pattern
```

---

## 7.3 Intelligence 不直接产生确认漏洞结论

Intelligence 可以：

```text
发现知识
形成假设
提供候选模式
提供研究线索
提供检测规则建议
```

但不得直接把知识记录升级为：

```text
CONFIRMED FINDING
```

确认漏洞必须重新进入：

```text
Evidence
+
Verification
+
Finding
```

体系。

---

# 8. Benchmark Track

Benchmark 是内部工程质量保障系统。

职责：

```text
Regression
Golden Set
Replay
Capability Evaluation
False Positive Evaluation
Model Evaluation
```

Benchmark 不作为默认运行入口。

Benchmark 不参与正常漏洞生成流程。

必须保持训练集与黄金集边界隔离。

---

# 9. 统一核心原则

四条轨道必须共享以下组件。

## 9.1 Scope

统一授权边界。

```text
ResearchScope
```

必须作为所有运行轨道的共同前置。

---

## 9.2 Transport

所有轨道共享：

```text
HttpTransport
```

不得由不同轨道各自实现网络传输。

---

## 9.3 Evidence

所有轨道必须使用统一：

```text
Evidence
EvidenceChain
EvidenceRecord
```

不得产生：

```text
ProductionEvidence
ResearchEvidence
IntelligenceEvidence
```

这种平行核心证据模型。

允许轨道拥有扩展元数据，但核心证据契约必须统一。

---

## 9.4 Finding

所有最终漏洞结果统一进入：

```text
FindingRecord
```

禁止不同轨道定义不同 Finding Schema。

---

## 9.5 Verification

所有正式漏洞结果必须进入统一验证体系。

任何轨道均不得绕过：

```text
Verification
Evidence Gate
```

而直接输出 CONFIRMED。

---

## 9.6 Reporting

所有正式结果最终使用统一：

```text
Reporting / Export
```

输出体系。

轨道只决定：

```text
如何发现
如何验证
如何升级
```

不决定：

```text
Finding 数据结构
证据标准
最终报告格式
```

---

# 10. 统一运行生命周期

所有轨道共用同一运行状态机：

```text
INIT
↓
SCOPE_VERIFIED
↓
CONTEXT_READY
↓
PLAN_READY
↓
EXECUTING
↓
EVIDENCE_COLLECTED
↓
EVALUATED
↓
REPORT_READY
↓
COMPLETED
```

异常情况：

```text
任何阶段
↓
BLOCKED
```

BLOCKED 不代表：

```text
安全
无漏洞
已完成
```

BLOCKED 只代表：

> 当前证据不足以完成当前运行目标。

---

# 11. 轨道与运行状态是两个不同维度

必须明确区分：

```text
Run Track
```

和：

```text
Run Status
```

例如：

```text
track = production
status = BLOCKED
```

表示：

> Production 轨道运行中发现当前证据无法闭环。

又例如：

```text
track = research
status = COMPLETED
```

表示：

> Research 轨道完成了本次研究运行。

禁止把：

```text
PRODUCTION_BLOCKED
RESEARCH_BLOCKED
```

设计为新的状态枚举。

---

# 12. 轨道切换规则

允许：

```text
Production → Research
```

允许：

```text
Production → Needs Validation
```

允许：

```text
Research → Needs Validation
```

允许：

```text
Intelligence → Knowledge Base
```

允许知识：

```text
Intelligence
↓
Knowledge
↓
Production
```

允许：

```text
Intelligence
↓
Knowledge
↓
Research
```

禁止：

```text
Intelligence
↓
CONFIRMED
```

也禁止：

```text
LLM
↓
CONFIRMED
```

---

# 13. 轨道不可逆原则

轨道切换必须记录：

```text
source_track
target_track
reason
trigger
timestamp
run_id
task_id
```

例如：

```json
{
  "source_track": "production",
  "target_track": "research",
  "reason": "evidence_gap",
  "trigger": "semantic_equivalence_unknown"
}
```

任何自动升级都必须具备可追踪性。

---

# 14. 运行轨道不能复制业务实现

禁止：

```text
production/
research/
intelligence/
```

分别复制整个业务系统。

不得出现：

```text
finding_models_production.py
finding_models_research.py
```

不得出现：

```text
transport_production.py
transport_research.py
```

不得出现：

```text
verification_production.py
verification_research.py
```

正确结构必须是：

```text
Shared Core
    ↓
Track Policy
    ↓
Track Runner
```

---

# 15. 配置契约

运行轨道通过 Profile 表达。

建议：

```text
configs/
├── base/
│   ├── default.json
│   └── project.toml
│
└── profiles/
    ├── production.toml
    ├── research.toml
    ├── intelligence.toml
    └── benchmark.toml
```

其中：

```text
production
```

必须成为默认 Profile。

---

# 16. Profile 职责

## production.toml

定义：

```text
低成本
快速执行
确定性优先
有限动态验证
允许自动升级
```

## research.toml

定义：

```text
深度研究
LLM
Mutation
Research Loop
Replay
复杂验证
```

## intelligence.toml

定义：

```text
知识采集
知识标准化
知识索引
知识更新
```

## benchmark.toml

定义：

```text
Gold
Replay
Regression
Evaluation
```

---

# 17. 默认策略

用户不指定轨道：

```text
→ Production
```

用户明确要求深度研究：

```text
→ Research
```

用户明确要求安全知识搜集：

```text
→ Intelligence
```

测试模型能力：

```text
→ Benchmark
```

---

# 18. 默认升级策略

Production 默认允许：

```text
Production
↓
Research
```

但必须：

```text
有明确升级原因
有可追踪记录
不改变授权边界
不改变证据标准
不降低验证要求
```

---

# 19. 资源预算原则

Production：

```text
资源预算低
并发较高
单任务成本低
优先快速出结果
```

Research：

```text
资源预算高
允许更长时间
允许更多实验轮次
允许 LLM
```

Intelligence：

```text
长期运行
批处理
知识更新
```

Benchmark：

```text
受控环境
确定性优先
固定输入
固定评价
```

---

# 20. 失败隔离原则

一个轨道失败：

> 不得破坏其他轨道。

例如：

```text
Research 失败
```

不得导致：

```text
Production Engine 失效
```

又例如：

```text
Intelligence 数据源失败
```

不得导致：

```text
Production 无法执行
```

---

# 21. 知识反哺原则

允许：

```text
Intelligence
↓
Knowledge Base
↓
Pattern
↓
Production Candidate Generation
```

允许：

```text
Intelligence
↓
Knowledge Base
↓
Research Hypothesis
```

允许：

```text
Research
↓
Validated Knowledge
↓
Knowledge Base
```

但研究结果进入知识库前必须经过明确的事实等级与来源记录。

---

# 22. 运行轨道契约最终关系

最终关系固定为：

```text
                ┌──────────────┐
                │ Intelligence │
                └──────┬───────┘
                       │
                       ▼
                 Knowledge Base
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
         Production          Research
              │                 │
              └────────┬────────┘
                       │
                       ▼
                    Evidence
                       │
                       ▼
                  Verification
                       │
                       ▼
                    Finding
                       │
                       ▼
                   Reporting
                       │
                       ▼
                   Submission
```

Benchmark 横向验证整个体系：

```text
Benchmark
   ├── Production
   ├── Research
   ├── Intelligence
   └── Shared Core
```

---

# 23. 架构最终判定

Invar 不采用：

```text
普通版
研究版
情报版
```

三个独立系统。

Invar 采用：

> **Unified Core + Multi-Track Runtime**

最终运行策略：

```text
Production = 默认
Research = 升级
Intelligence = 供给
Benchmark = 验证
```

最终核心原则：

> **默认简单，遇难升级；能力集中，职责分轨；证据统一，结果统一。**

---

# 24. 工程红线

运行轨道升级不得违反母级工程宪法。

始终遵守：

```text
零臆造
零重复实现
零单案例特判
零魔法硬编码
目录职责明确
类型即契约
测试即契约
根因优先
已有工程优先
最小合理修改
```

轨道系统必须满足：

```text
高内聚
低耦合
高鲁棒性
热拔插
```

最终目标：

> **增加 Research 能力不会使 Production 变复杂。**
>
> **增加 Intelligence 能力不会破坏扫描主链。**
>
> **增加未来高危研究能力不需要重写核心架构。**
>
> **任何轨道最终都必须回到统一证据与验证体系。**
