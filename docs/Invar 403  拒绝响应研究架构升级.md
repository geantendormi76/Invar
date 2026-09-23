# Invar 403 / 拒绝响应研究架构升级
# AI 可复现工程规格书 v1.0.0

> 文档类型：AI 可复现工程规格（Reproducible Engineering Specification）
>
> 目标：在项目源码、开发人员记忆、会话上下文全部丢失后，仅凭本规格书与明确列出的恢复材料，重新理解、重建、测试和验证 Invar 的 403 / 拒绝响应研究子系统，并保持既有 Invar 数据契约与兼容边界。
>
> 当前状态：生产代码冻结；本文件是架构研究与重建规格，不是当前实现。
>
> 证据标签：**FACT / DERIVED / ASSUMPTION / EXPERIMENT / RECOMMENDATION / UNKNOWN / TBD / UNVERIFIED**。
>
> 安全边界：任何动态探测必须处于明确授权的 `scope.txt` / engagement scope 内。本规格不授权对任何外部目标执行请求。

---

## 0. 最终判定

### 0.1 能否仅凭本规格重新实现系统？

**对 403 / 拒绝响应研究子系统：YES，功能架构可重建。**

**对 2026-09-22 当时整个 Invar 仓库的“完全历史复原”：NO，当前仍缺少若干无法推理恢复的物理资产与环境状态。**

剩余不可推理恢复项：

- **FACT**：真实 Git `commit / branch / working tree status` 不在当前快照。
- **FACT**：`uv.lock / Cargo.lock / pnpm-lock.yaml` 被快照规则排除。
- **FACT**：模型权重被快照规则排除。
- **FACT**：`targeted_research_tasks_78.json` 在 Handoff 中存在，但不在当前可访问快照文件清单。
- **FACT**：`data/targets/ikuai8.com/scope.txt` 在 Handoff 中存在，但不在当前可访问快照文件清单。
- **FACT**：`tmp/raw_js/`、运行日志、runs 输出等被快照规则排除。
- **UNVERIFIED**：当前真实工作树是否仍与 Handoff 的 2026-09-22 13:30 状态完全一致。
- **UNVERIFIED**：Handoff 声明的 Python `141 passed`；当前快照静态可数为 139 个 `test_` 函数。
- **UNKNOWN**：当前 llama.cpp / `llama-server.exe` 的确切 build/commit。
- **UNKNOWN**：当前外部目标的实时网络状态。

因此，本规格定义了**可复现的算法、状态机、数据契约、测试策略和集成边界**；若要求完全恢复历史 runtime，必须补齐第 25 节 Reproducibility Closure Bundle。

---

## 1. 证据分类法

### FACT
直接来自当前可访问源码、测试、配置、Handoff、用户提供截图/源码，或官方标准/论文的可核对内容。

### DERIVED
由两个或多个 FACT 逻辑推导，不应伪装成源码事实。

### ASSUMPTION
为后续实现暂时采用、尚未通过实验验证的前提。

### EXPERIMENT
实际执行过或必须在实现时执行的实验。

### RECOMMENDATION
架构升级建议，不代表当前源码已有。

### UNKNOWN / TBD / UNVERIFIED
信息缺失时显式保留未知状态，禁止脑补。

---

## 2. 项目身份与历史阶段

### 2.1 项目身份

**FACT（Handoff）**

Invar 是三位一体体系中的 System-2 验证引擎：

```text
Base-Jev
  = System-1 模型工厂 / 0.6B 快速意图与风险反射

distiller
  = 双师蒸馏 / Gold Firewall / 知识编译

Invar
  = System-2 动态执行 / 差分验证 / 安全不变量 / 证据确权
```

### 2.2 Handoff 历史阶段

**FACT**

- Phase 1~4：资产收集、HTTP 存活、Spider、AST、双轨初筛完成。
- Phase 5.1：78 个 targeted research tasks 完成装配。
- Handoff 原计划 Phase 5.2：`ModelProvider` + 本地 `llama-server`。

### 2.3 当前用户决策

**FACT（当前会话用户指令）**

生产代码冻结，优先升级 403 / 拒绝响应研究架构。

因此：

```text
历史 Handoff Next Action
    = LocalLlamaProvider

当前任务优先级
    = 403 Research Architecture Contracts
```

---

## 3. 可访问源材料与证据来源

### 3.1 本地工程快照

- Repomix：`39d895d3-d99d-4abc-85f4-51a0728a2973.xml`
- 用户工程规范：`47c7b3cb-6904-49bd-92f8-1208b06aaadb.md`
- 403 架构 v0.2：`Invar-403拒绝响应研究架构升级规划-v0.2.md`

快照 SHA 在文档末尾给出。

### 3.2 外部理论 / 官方资料

- Needles at Scale: https://arxiv.org/abs/2606.01364
- A Year of Hacking with LLMs: https://sites.google.com/site/zhiniangpeng/blogs/Hacking-with-LLMs
- RFC 9110 HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 3986 URI Generic Syntax: https://www.rfc-editor.org/rfc/rfc3986/
- OWASP WSTG: https://wstg.owasp.org/
- PortSwigger Access Control: https://portswigger.net/web-security/access-control

### 3.3 当前社区参考实现

- NoMore403: https://github.com/devploit/nomore403
- BypassPro: https://github.com/0x727/BypassPro
- GoByPASS403: https://github.com/slicingmelon/gobypass403
- WafRift: https://github.com/santhreal/wafrift
- Akira: https://github.com/kalpmodi/akira
- Access-Control-Testing: https://github.com/peerigon/access-control-testing
- bypass-403 (iamj0ker): https://github.com/iamj0ker/bypass-403

---

## 4. 历史 Invar System-2 基线

**FACT**

历史闭环：

```text
Targeted Research Task
      ↓
Hypothesis
      ↓
Initial Payload
      ↓
Adaptive Probe Loop
      ↓
FeedbackInterpreter
      ↓
MutationPolicy
      ↓
MethodTamper / IDOR
      ↓
InvariantEvaluator
      ↓
FindingRecord
      ↓
IndependentVerifier
      ↓
PromotionGate
      ↓
KnowledgeCard / Report
```

### 4.1 既有假说

```text
H-AUTH-1
H-DESTRUCT-1
H-IDOR-1
```

### 4.2 既有不变量

```text
destructive_confirmation
auth_boundary
idor_boundary
```

### 4.3 既有核心数据对象

#### TriageTask

```python
@dataclass
class TriageTask:
    task_id: str
    endpoint_id: str
    coverage_id: str
    hypothesis_id: Optional[str]
    profile: str
    method: str
    path: str
    surface_id: str
    pool_origin: str
    priority: str
    attack_class: str
    extracted_params: List[str]
    impact_score: float
    sensitivity_score: float
    code_slice: Optional[str]
    source_file: Optional[str]
    source_line: Optional[int]
```

约束：

```text
method ∈ {GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS}
path 必须以 / 开头
code_slice ≤ 800 字符
```

#### ResearchTask（Rust）

```rust
pub struct ResearchTask {
    pub task_id: String,
    pub endpoint_id: String,
    pub coverage_id: String,
    pub hypothesis_id: Option<String>,
    pub profile: String,
    pub method: String,
    pub path: String,
}
```

兼容：`case_id` 可反序列化为 `task_id`。

#### ResearchCase

```text
case_id
endpoint
invariants[]
hypotheses[]
attempts[]
decision
metadata
```

`attempt_number` 必须从 1 连续递增。

#### ProbeAttempt（现有）

```text
attempt_number
payload
status_code
response_preview
interpretation
mutation_reason
```

#### EvidenceRecord（现有）

```text
HTTPRequestLog(method,url,headers,body)
HTTPResponseLog(status_code,headers,body_preview)
EvidenceRecord(endpoint,request,response,timestamp,finding_type,is_anomaly,notes)
```

#### FindingRecord（现有）

```text
finding_id
verdict
fingerprint
title
description
root_cause
claimed_root_cause
intended_behavior
rejection_reason
unresolved_blocker
trace
conditions
execution
endpoint_refs
coverage_refs
hypothesis_refs
evidence_refs
severity
confidence
remediation
verification
provenance
```

现有 Verdict：

```text
confirmed
needs_validation
rejected
```

现有严格门禁：

```text
needs_validation → 不允许 severity，必须 unresolved_blocker
confirmed → 必须 severity/root_cause/trace/evidence_refs
rejected → 必须 rejection_reason
trace.file_path → 必须 repository-relative
```

#### VerificationGate

**FACT**

- `IndependentVerifier` 禁止 self-verification。
- Verification Verdict：`VERIFIED / CORRECTED / REJECTED`。
- PromotionGate 要求 Finding 通过 schema 与独立验证。

---

## 5. 历史 403 实现与问题定位

### 5.1 MethodTamperOperator

**FACT**

当前存在三类：

```text
VERB_SUBSTITUTION
HEADER_TUNNEL
QUERY_TUNNEL
```

历史 header keys：

```text
X-HTTP-Method-Override
X-Method-Override
X-HTTP-Method
```

query keys：

```text
_method
method
```

### 5.2 当前 403/405 分支

**FACT**

`AdaptiveSandboxExecutor` 当前逻辑近似：

```text
403/405
   ↓
MethodTamperOperator.generate_variants()
   ↓
逐一请求
   ↓
若任意响应为 2xx
   ↓
记录“动词隧道穿透成功”并继续
```

### 5.3 当前测试也固化了这个旧语义

**FACT**

`test_sandbox_tamper_integration.py` 有一个典型测试：

```text
DELETE /api/orders/batch
baseline = 403
candidate = POST + X-HTTP-Method-Override: DELETE
candidate = 200
body = {"deleted": true, "count": 10}
```

并将它判为：

```text
H-DESTRUCT = VERIFIED
decision = vulnerable
finding_type = VULNERABILITY_FOUND
```

### 5.4 架构缺陷

**DERIVED**

当前系统存在职责边界错误：

```text
Access Outcome
    ↓ 被直接解释为
Security Boundary Violation
```

正确模型应当是：

```text
403/405
 ↓
Denial Classification
 ↓
Transformation Family
 ↓
Candidate Probe
 ↓
Differential Observation
 ↓
Semantic Equivalence
 ↓
Security Invariant
 ↓
Replay / Verification
 ↓
Security Verdict
```

---

# 6. 403.sh 技术考古与真实源码对齐

**FACT / 源码证据**

根据最新捕获的 `iamj0ker/bypass-403` 仓库 `bypass-403.sh` 完整 61 行代码（Commit `V35HR4J added X-Forwarded-Host header`），其真实的 27 项探测命令物理分布如下：

```bash
# 物理行号与真实命令映射 (Baseline: $1=host, $2=path)
# Line 06: 基线请求
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2

# Line 08~14: 路径点斜杠与连续斜杠畸变
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/%2e/$2
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2/.
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1//$2//
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/./$2/./

# Line 16~24: 代理头重写与内网身份伪造
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" -H "X-Original-URL: $2" $1/$2
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" -H "X-Custom-IP-Authorization: 127.0.0.1" $1/$2
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" -H "X-Forwarded-For: http://127.0.0.1" $1/$2
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" -H "X-Forwarded-For: 127.0.0.1:80" $1/$2
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" -H "X-rewrite-url: $2" $1

# Line 26~36: 空白字符、查询分隔符与锚点混淆
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2%20
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2%09
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2?
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2.html
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2/?anything
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2#

# Line 38~46: POST 协议降级、通配符、后缀混淆与 TRACE 动词
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" -H "Content-Length:0" -X POST $1/$2
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2/*
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2.php
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" $1/$2.json
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" -X TRACE $1/$2

# Line 48~57: Host 伪造、Tomcat分号畸变与 X-Forwarded-Host 补充
curl -s -o /dev/null -iL -w "%{http_code},%{size_download}" -H "X-Host: 127.0.0.1" $1/$2
curl -s -o /dev/null -iL -w "%{http_code},%{size_download}" "$1/$2../"
curl -s -o /dev/null -iL -w "%{http_code},%{size_download}" " $1/$2;/"
curl -k -s -o /dev/null -iL -w "%{http_code},%{size_download}" -X TRACE $1/$2
curl -s -o /dev/null -iL -w "%{http_code},%{size_download}" -H "X-Forwarded-Host: 127.0.0.1" $1/$2

# Line 60: 历史存档外部旁路验证
curl -s https://archive.org/wayback/available?url=$1/$2 | jq -r '.archived_snapshots.closest | {available, url}'
```

**DERIVED**

该脚本实际上已经隐含多个 transformation dimensions，适合作为 **Legacy Technique Seed**，而不是作为未来算法本体。

---

# 7. 外部理论：事实与可迁移启发

## 7.1 Needles at Scale

**FACT / WEB**

论文提出 `Symbolicate-Enrich-Sample`：先做低成本确定性结构特征，再用 LLM 做 enrichment，再以 priority-weighted importance sampling 构造研究队列。论文覆盖超过 7.2M 函数，并将其归纳为下游 detector/agent 的 selection substrate，而不是漏洞证明器。

来源：
https://arxiv.org/abs/2606.01364

**DERIVED → Invar**

403 系统不应固定穷举 payload，而应：

```text
Denial Hypotheses
    ↓
Candidate Families
    ↓
Priority / Information Gain
    ↓
Next Experiment
```

---

## 7.2 A Year of Hacking with LLMs

**FACT / WEB**

文章强调：

- 一次问答不足以完成安全研究；
- Agent 应先理解行为，再判断授权；
- candidate vulnerability 必须真实验证；
- PoC 失败后应读取失败原因、修改并重试；
- Tool 应尽量确定性，Skill 决定工具使用时机与顺序；
- 研究人员负责攻击面选择、harness、skill 和最终结论。

来源：
https://sites.google.com/site/zhiniangpeng/blogs/Hacking-with-LLMs

**DERIVED → Invar**

LLM 应为 Research Planner，而不是 Ground Truth Generator。

---

## 7.3 RFC 9110

**FACT / WEB**

- 405 = 方法已知，但目标资源不支持该方法，并要求 `Allow`。
- 403 与 405 是不同语义。

来源：
https://www.rfc-editor.org/rfc/rfc9110.html

**DERIVED**

不能把：

```text
403 == WAF
405 == WAF
```

作为统一规则。

---

## 7.4 RFC 3986

**FACT / WEB**

URI 规范包含：

- percent-encoding；
- case normalization；
- percent-encoding normalization；
- dot-segment normalization。

来源：
https://www.rfc-editor.org/rfc/rfc3986/

**DERIVED**

Path / URL normalization 应作为独立 Transformation Family；它研究的是不同处理层可能如何解析/规范同一输入，而不是“神奇 payload”。

---

## 7.5 OWASP WSTG

**FACT / WEB**

授权测试需要考虑不同角色/身份与资源访问关系，包括 horizontal access control。

来源：
https://wstg.owasp.org/

**DERIVED**

Semantic Equivalence 必须至少覆盖：

```text
Actor
Resource
Action
```

---

## 7.6 PortSwigger

**FACT / WEB**

PortSwigger 的 access-control material 明确讨论：

- method discrepancies；
- URL matching discrepancies；
- 路径不同表示方式被前后端映射为相同 endpoint。

来源：
https://portswigger.net/web-security/access-control

**DERIVED**

研究目标应从“payload”提升为“interpretation discrepancy”。

---

# 8. 社区实现考古

## 8.1 NoMore403

**FACT / WEB**

公开 README 当前包含：

```text
baseline-driven comparison
auto-calibration
403=>200 / 403=>400 / 403=>404 区分
多信号评分
replay / reproducibility
retry/backoff
raw HTTP
JSON/JSONL
```

且明确说明 scoring 用来**prioritize**，不直接证明 exploitation。

来源：
https://github.com/devploit/nomore403

**RECOMMENDATION**

Invar 可复用：baseline / calibration / differential / replay；自己持有 hypothesis、semantic equivalence、evidence contract。

---

## 8.2 BypassPro

**FACT / WEB**

当前 5.1 已组织为：

```text
Auto Access Bypass
Auto WAF Bypass
Manual WAF
Raw Socket
Path/Header/Body/Encoding/Method
Parser Differential
```

来源：
https://github.com/0x727/BypassPro

**DERIVED**

Transformation Family 应是一级抽象。

---

## 8.3 GoByPASS403

**FACT / WEB**

项目强调 exact URL/path preservation，并记录 status、content length、headers、body preview、redirect、reproduction curl 等。

来源：
https://github.com/slicingmelon/gobypass403

**DERIVED**

必须区分：

```text
Logical Request
Wire Request
Observed Request
```

避免客户端 normalization 污染 parser-differential 实验。

---

## 8.4 WafRift

**FACT / WEB**

当前公开项目包含：

- differential probing；
- grammar/encoding mutation；
- evolutionary search；
- per-WAF gene-bank；
- stateful session；
- replay；
- retry-after handling。

来源：
https://github.com/santhreal/wafrift

**DERIVED**

成熟 technique 应被视为“搜索动作空间”，而不是算法本身。

---

## 8.5 Akira

**FACT / WEB**

WAF selector 使用类似：

```text
waf_fingerprint
technique
http_status
is_real_response
```

并采用 Thompson Sampling / Multi-Armed Bandit 选择技术。

来源：
https://github.com/kalpmodi/akira

**RECOMMENDATION**

未来可以研究 contextual bandit / Thompson Sampling / 信息增益；第一版仍应使用可解释 heuristic。

---

## 8.6 Access-Control-Testing

**FACT / WEB**

Peerigon 工具使用增强 OpenAPI 描述 user-resource relationship，并比较实际 allow/deny 与 policy replication；README 还明确警告 403 可能来自 IP blocking 等非授权机制。

来源：
https://github.com/peerigon/access-control-testing

**DERIVED**

403 status 本身不是 authorization verdict。

---

# 9. 新架构总图

```text
Targeted Research Task
        │
        ▼
Authorization Gate
        │
        ▼
Baseline Builder
        │
        ▼
Denial Classification
        │
        ▼
Hypothesis Engine
        │
        ▼
Transformation Family Registry
        │
        ▼
Adaptive Experiment Selector
        │
        ▼
Probe Executor
        │
        ▼
Differential Oracle
        │
        ▼
Semantic Equivalence
        │
        ▼
Security Invariant
        │
        ▼
Replay / Independent Verification
        │
        ▼
Evidence Contract
        │
        ▼
Finding / Knowledge Bank
```

---

# 10. Denial Classification Contract

## 10.1 目标

> 回答“为什么这个请求被拒绝？当前有哪些可信解释？”

这是解释层，不是漏洞判定器。

## 10.2 数据模型

### DenialObservation

```text
status_code
response_signature
selected_headers
redirect_signature
body_fingerprint
transport_facts
calibration_context
```

### DenialHypothesis

```text
hypothesis_id
layer
category
confidence
supporting_evidence_refs[]
contradicting_evidence_refs[]
status
```

## 10.3 Layer

```text
EDGE
PROXY
ROUTER
AUTHENTICATION
AUTHORIZATION
APPLICATION
UNKNOWN
```

## 10.4 Category

```text
ACCESS_POLICY_DENIAL
METHOD_POLICY_DENIAL
ROUTING_MISMATCH
PARSER_MISMATCH
IDENTITY_OR_TRUST_CONTEXT
RATE_LIMIT
DEFAULT_ERROR_HANDLER
APPLICATION_POLICY
UNKNOWN
```

### WAF 不是 category

**RECOMMENDATION**

另设：

```text
frontend_component = WAF | CDN | ReverseProxy | Unknown
```

因为“谁拒绝”与“为什么拒绝”是不同维度。

## 10.5 多假设

首次 403 通常信息不足，应允许：

```text
primary_hypothesis
alternative_hypotheses[]
```

不得要求系统在无证据时强制单标签。

## 10.6 证据等级

### A 强证据
- 明确 edge/WAF fingerprint；
- RFC/HTTP 语义直接支持；
- calibration 同构响应；
- 仅改变一个变量即产生可重复结构变化。

### B 中证据
- body marker；
- header pattern；
- redirect pattern；
- hash/length；
- timing。

### C 弱证据
- LLM 推断；
- URL 名字；
- 纯技术栈猜测；
- 单次异常响应。

LLM 不得把 C 级推测升级为事实。

---

# 11. Transformation Family Contract

### F1 Path / URL Normalization
研究路径表示与规范化差异。

### F2 Method Semantics
研究 HTTP method 表示与代理/路由方法解释差异。

### F3 Header / Trust Context
研究 forwarded/original URL/代理信任上下文。

### F4 Host / Authority / Scheme
研究 authority、Host、scheme 等路由/信任语义。

### F5 Encoding / Decoding
研究 percent-encoding、多阶段解码、body charset 等。

### F6 Query / Body Parser
研究参数重复、separator、body parser 差异。

### F7 Protocol / Wire Representation
研究 HTTP version、raw request、header/wire exactness。

### F8 Cache / Routing Interpretation
研究 cache key、router、frontend/backend interpretation。

### F9 Session / Authorization Context
研究 actor/role/resource ownership/authorization 状态。

**约束：** F9 不应与“WAF bypass”混为一谈。

---

# 12. Semantic Equivalence Contract

## 12.1 三层身份

### Wire Identity

```text
method
request-target
headers
body
http_version
```

### Routing Identity

```text
scheme/host
normalized route
router-selected handler
```

### Business Resource Identity

```text
actor
resource
object identifiers
action
expected business effect
```

## 12.2 Verdict

只能是：

```text
SAME_RESOURCE
DIFFERENT_RESOURCE
UNKNOWN
```

不允许强制二元 `True/False`。

## 12.3 Dimensions

```text
route_equivalent
method_equivalent
parameter_equivalent
identity_equivalent
action_equivalent
business_effect_equivalent
```

每一维可以是 `YES / NO / UNKNOWN`。

## 12.4 证据优先级

```text
backend route/handler evidence
→ response semantic markers
→ resource identifiers
→ structured payload
→ stable response fingerprint
→ URL normalization reasoning
→ LLM interpretation
```

**规则：** response body similarity 是 signal，不是最终 proof。

---

# 13. Differential Observation Contract

每个 candidate 必须包含：

```text
BaselineObservation
CandidateObservation
Transformation
DifferentialObservation
```

最小字段：

```text
status_delta
header_delta
body_length_delta
body_hash_changed
content_type_changed
location_delta
redirect_chain_delta
latency_delta
transport_delta
```

后续可扩展：

```text
route_delta
resource_identity_delta
authorization_delta
business_effect_delta
```

### 解释原则

```text
403 → 200
    = access outcome changed
    ≠ confirmed vulnerability

403 → 404/400
    = parser/routing candidate
    ≠ bypass

403 → 302
    = must inspect final redirect/login barrier
```

---

# 14. Evidence Contract

## 14.1 六层证据

### Layer 0 — Authorization Context

```text
scope
target
actor
role
session
credential fingerprint
```

### Layer 1 — Baseline

```text
logical request
wire request reference
response
calibration
```

### Layer 2 — Transformation

```text
family
transformation_id
before
after
rationale
expected_effect
```

### Layer 3 — Observation

```text
status
headers
body hash
body length
content type
location
redirect chain
latency
transport outcome
```

### Layer 4 — Differential

```text
status_delta
header_delta
body_delta
route_delta
resource_identity_delta
authorization_delta
```

### Layer 5 — Verification

```text
replay_count
replay_consistency
independent_verification
invariant_result
```

### Layer 6 — Verdict

```text
candidate
inconclusive
rejected
confirmed
```

## 14.2 Confirmed 门禁

必须同时满足：

```text
scope_verified
AND baseline_established
AND semantic_equivalence == SAME_RESOURCE
AND security_invariant == VIOLATED
AND replay_successful
AND replay_stable
AND evidence_complete
AND not rate-limited
AND not transport-failed
AND independent_verification_passed
```

否则不得 `CONFIRMED`。

---

# 15. State Machine

```text
INIT
  ↓
SCOPE_VERIFIED
  ↓
BASELINE_ESTABLISHED
  ↓
DENIAL_CLASSIFIED
  ↓
HYPOTHESES_READY
  ↓
FAMILY_SELECTED
  ↓
CANDIDATE_GENERATED
  ↓
PROBED
  ↓
DIFFERENTIAL_EVALUATED
  ├─ no meaningful delta → FAMILY_DEPRIORITIZED
  ├─ parser/routing delta → NEW_HYPOTHESIS
  └─ access outcome delta → SEMANTIC_CHECK
                                  ↓
                         SAME_RESOURCE?
                      ┌──────┼──────┐
                      ↓      ↓      ↓
                   SAME  DIFFERENT UNKNOWN
                      ↓      ↓      ↓
                INVARIANT REJECTED INCONCLUSIVE
                      ↓
                    REPLAY
                      ↓
              INDEPENDENT VERIFY
                      ↓
                  CONFIRMED
```

独立状态：

```text
RATE_LIMITED
TRANSPORT_FAILED
OUT_OF_SCOPE
BUDGET_EXHAUSTED
```

这些状态不得自动映射为 `NO_BYPASS`。

---

# 16. Adaptive Experiment Selection

## 16.1 第一版推荐策略

使用可解释 heuristic，而不是直接引入复杂在线学习：

```text
priority =
    denial_hypothesis_support
  + family_relevance
  + expected_information_gain
  + historical_success_signal
  + target_fingerprint_match
  - recently_failed_penalty
  - rate_limit_penalty
  - duplicate_penalty
```

以上是算法结构，不是要求固定魔法常数。

## 16.2 Information Gain

研究目标不是“最常成功的 payload”，而是：

> 哪个实验最能减少当前假设空间的不确定性？

## 16.3 未来研究

可选：

```text
Contextual Bandit
Thompson Sampling
Bayesian update
Diversity/Novelty sampling
Per-fingerprint gene bank
```

第一版不直接依赖这些高级学习器。

---

# 17. LLM Boundary

## 17.1 LLM 可以

```text
Observation
→ Hypothesis generation
→ Transformation proposal
→ Expected observation
→ Post-experiment interpretation
→ Next experiment suggestion
```

## 17.2 LLM 不可以单独决定

```text
200 == vulnerable
same_resource == true
evidence == sufficient
security_boundary_broken == true
```

事实必须来自 deterministic evidence + oracle + invariant + replay + verification。

---

# 18. 与现有 Invar 的兼容设计

## 18.1 Transport

### 当前 FACT

```text
TransportResponse
├── status_code
├── text
└── headers
```

### 未来 RECOMMENDATION

```text
status_code
text
headers
request_ref
redirect_chain
latency
transport_error
wire_request_ref
```

具体字段名 TBD，必须先测试后实现。

## 18.2 ProbeAttempt

### 当前 FACT

```text
attempt_number
payload
status_code
response_preview
interpretation
mutation_reason
```

### 未来 RECOMMENDATION

```text
attempt_id
parent_attempt_id
baseline_ref
transformation_ref
logical_request_ref
wire_request_ref
transport_result
response_observation
differential_ref
semantic_equivalence_ref
expected_observation
actual_observation
state_transition
```

## 18.3 IdorCompareOperator

**FACT**：当前 `SIMILARITY_THRESHOLD = 0.80`。

**RECOMMENDATION**：保留为 semantic signal，不再作为最终 verdict。

## 18.4 FindingRecord

建议继续保持当前 `confirmed / needs_validation / rejected`，避免无必要破坏 reporting contract。

Candidate/inconclusive 更适合留在 ResearchCase/Candidate 层。

---

# 19. 迁移策略

## Phase A — Contract First

新增契约测试：

```text
test_denial_classification_contract.py
test_semantic_equivalence_contract.py
test_evidence_contract.py
```

不写生产实现。

## Phase B — Adapterize Existing Techniques

把：

```text
MethodTamperOperator
bypass-403.sh
成熟社区 technique
```

映射到 Transformation Family。

## Phase C — Deterministic Loop

```text
Baseline
→ Classification
→ Family
→ Probe
→ Diff
→ Equivalence
→ Invariant
→ Replay
```

先不用 LLM。

## Phase D — Adaptive Selector

加入信息增益、历史效果、fingerprint、预算和 diversity。

## Phase E — LLM Planner

再把 `ModelProvider` 接入 hypothesis / experiment planning / interpretation。

## Phase F — Knowledge Bank

沉淀：

```text
target fingerprint
denial pattern
family
transformation
differential
equivalence
verdict
```

---

# 20. 当前行为兼容要求

以下不得无测试直接改变：

1. HTTP 7 动词白名单。
2. canonical path 以 `/` 开头。
3. `code_slice <= 800`。
4. MutationPolicy 的 required-field/type-correction 行为。
5. ResearchCase attempt 连续性。
6. FindingRecord strict schema。
7. IndependentVerifier 禁止 self-verification。
8. PromotionGate 规则。
9. Rust `ResearchTask` JSON alias/默认字段行为。
10. Rust Python worker 的 JSON stdin/stdout 互操作。

---

# 21. 关键踩坑与根因

## P1 HTTPX 同名命令冲突

**FACT**：Python 依赖 `httpx` 与 ProjectDiscovery `httpx` 同名。

根因：PATH collision。

历史修复：`_find_projectdiscovery_httpx` + `-version` 检查。

## P2 code slice 造成任务爆炸

**FACT**：23.7 MB → 156 KB。

根因：混淆代码长单行没有截断。

修复：`_compact_slice <= 800`。

## P3 非法单字母 HTTP method

**FACT**：出现 `E/T/R` 等 AST 残片。

根因：动态调用解构捕获局部变量字符。

修复：`_normalize_method()` + `_normalize_path()`。

## P4 ONNX wrapper 双头缺失

**FACT**：历史审查发现 wrapper 未直接输出 sensitivity head。

处理原则：不猜 tensor 语义；以真实源码/模型图为准。

## P5 403 误判

**FACT + DERIVED**：403/405 candidate 的 2xx 被直接当成 tunnel success。

根因：验证层职责边界错误。

修复方向：把它拆成 classification → candidate → equivalence → invariant → replay → evidence。

---

# 22. 测试与验收

## 22.1 旧测试资产

当前高相关测试：

```text
python/tests/test_adaptive_sandbox_baseline.py
python/tests/test_adaptive_sandbox_integration.py
python/tests/test_adaptive_sandbox_transport_baseline.py
python/tests/test_http_transport.py
python/tests/test_method_tamper.py
python/tests/test_mutation_policy.py
python/tests/test_idor_compare.py
python/tests/test_invariant_evaluator.py
python/tests/test_sandbox_idor_integration.py
python/tests/test_sandbox_invariant_integration.py
python/tests/test_sandbox_tamper_integration.py
python/tests/test_finding_record.py
python/tests/test_verification_and_promotion_gate.py
python/tests/test_research_models.py
python/tests/test_research_evidence.py
python/tests/test_research_loop_integration.py
python/tests/test_research_run.py
python/tests/test_research_task_adapter.py
python/tests/test_research_worker.py
```

## 22.2 新契约测试

### Denial Classification

至少覆盖：

- 403 不自动等于 WAF；
- 405 + Allow → METHOD_POLICY_DENIAL；
- WAF fingerprint 与 denial category 分离；
- Rate limit 独立；
- 无证据时 UNKNOWN/多假设；
- LLM 不能替代 deterministic evidence。

### Semantic Equivalence

至少覆盖：

- 同路由、同资源 ID → SAME_RESOURCE；
- 不同资源 ID → DIFFERENT_RESOURCE；
- login redirect → UNKNOWN 或 DIFFERENT_RESOURCE；
- generic 200 → 不得自动 SAME_RESOURCE；
- body similarity alone → 不得 confirmed；
- actor/resource/action 缺失 → UNKNOWN。

### Evidence Contract

至少覆盖：

- 无 baseline → 不能 confirmed；
- 无 semantic equivalence → 不能 confirmed；
- 无 replay → 不能 confirmed；
- transport failure → TRANSPORT_FAILED/INCONCLUSIVE；
- rate limit → RATE_LIMITED；
- evidence 可回溯 transformation；
- evidence 可回溯 finding；
- independent verification 缺失 → PromotionGate fail；
- LLM 输出不能直接作为 fact。

## 22.3 验收矩阵

| 输入 / 结果 | 必须输出 |
|---|---|
| 403，无额外证据 | DENIAL_CLASSIFIED + UNKNOWN/多假设 |
| 405 + Allow | METHOD_POLICY_DENIAL |
| 403 → 404 | parser/routing candidate |
| 403 → 302 → login | non-confirmed |
| 403 → 200 generic page | non-confirmed |
| 403 → 200 same resource + invariant violation + replay | candidate → verification → confirmed |
| 403 → 200 different resource | rejected candidate |
| replay 不稳定 | INCONCLUSIVE |
| rate limit | RATE_LIMITED |
| network/transport exception | TRANSPORT_FAILED |
| scope 不允许 | OUT_OF_SCOPE |
| request budget exhausted | BUDGET_EXHAUSTED |

---

# 23. 环境与依赖

## 23.1 OS / Shell

**FACT**：Windows 11；PowerShell。

## 23.2 Python

**FACT**：`.python-version = 3.12`。

Python root：`>=3.10,<3.13`。

Core：`>=3.11,<3.14`。

依赖：

```text
pydantic>=2
tree-sitter>=0.26
tree-sitter-javascript>=0.25
requests>=2.31
httpx>=0.27
httpx-socks>=0.8
socksio>=1.0
pytest>=8
```

精确 resolved versions：**UNKNOWN**，lockfile 未提供。

## 23.3 Rust

**FACT**：Cargo 1.80+（Handoff），edition 2021；依赖 `serde`, `serde_json`。

精确 Cargo.lock 版本：**UNKNOWN**。

## 23.4 Desktop

当前源码是 React 19 + TypeScript + Tailwind 4 + Tauri 2 + Vite 7。

**FACT conflict**：README 仍描述旧的 Vue3 `src/` 布局，因此 README 这一部分应视为 stale。

## 23.5 Local LLM

**FACT from Handoff**：

```text
llama-server.exe
127.0.0.1:8080
Qwen3.8-27B-Uncensored-IQ3_XXS.gguf
Ornith-1.5-9B-Abliterated-IQ3_M.gguf
RTX 3060 12GB
```

**UNVERIFIED**：模型权重、commit、quantization、当前性能指标。

---

# 24. 从零重建路线

1. 恢复真实 Git / lockfiles / scope / 生成 artifacts。
2. 按旧契约重建核心数据对象。
3. 恢复 legacy sandbox + tests。
4. 固化旧行为 baseline。
5. 创建三组新的 contract tests。
6. 使现有 method tamper / bypass-403 技术成为 transformation adapter。
7. 实现 deterministic denial classification。
8. 实现 differential oracle。
9. 实现 semantic equivalence 三值逻辑。
10. 实现 evidence lineage。
11. 接入 replay + verification。
12. 通过全部 contract tests 后，再集成 Adaptive Selector。
13. 最后接入 ModelProvider/LLM Planner。
14. 建立 Knowledge Bank。
15. 做全量回归。

---

# 25. Reproducibility Closure Bundle

若要把“历史状态可复现”从 NO 变成 YES，至少必须补齐：

### RCB-01
真实 Git repository / Git bundle：

```text
branch
commit
working-tree state
```

### RCB-02

```text
uv.lock
Cargo.lock
pnpm-lock.yaml
```

### RCB-03

```text
data/targets/<target>/scope.txt
```

### RCB-04

```text
artifacts/reports/targeted_research_tasks_78.json
```

### RCB-05

```text
data/targets/<target>/subdomains.jsonl
live_hosts.jsonl
urls.jsonl
javascript.jsonl
tmp/ikuai8_endpoints_report.json
tmp/base_jev_predictions_1216.jsonl
artifacts/reports/triage_pools_v2.json
```

### RCB-06

模型 passport + 权重 + tokenizer。

### RCB-07

`llama-server` 的准确 build/commit。

### RCB-08

`docs/research` 下原始资料的独立可访问快照。

### RCB-09

实际运行后的 pytest / cargo test 日志。

### RCB-10

当前 branch/status/commit 与快照 hash。

---

# 26. AI Implementation Prompt

```text
你接管 Invar 403 / 拒绝响应研究架构。

规则：
1. 真实源码、真实测试、Git 状态优先于任何历史文档。
2. 先事实，后抽象；先契约，后实现；先测试，后交付。
3. 不把 403 当 WAF。
4. 不把 2xx 当漏洞。
5. 不让 LLM 充当 ground truth。
6. 不新增无依据特判。
7. 所有动态测试必须受授权 scope 限制。
8. 一次只推进一个工程动作。

恢复：
- 读取 HANDOFF.md。
- 检查 branch / commit / worktree。
- 读取 transport.py、sandbox_executor.py、method_tamper.py、evidence.py、research_models.py、idor_compare.py、invariant_evaluator.py、finding_models.py、verification_gate.py。
- 阅读相关测试。

第一工程动作：
只新增 Denial Classification / Semantic Equivalence / Evidence Contract 的契约测试。
不实现生产逻辑。
不写 LocalLlamaProvider。
不扩展 403 payload 列表。
不访问真实目标。

契约必须验证：
- 403/405 classification；
- multi-hypothesis；
- SAME_RESOURCE / DIFFERENT_RESOURCE / UNKNOWN；
- 2xx 不自动等于 bypass；
- evidence lineage；
- replay；
- independent verification；
- rate-limit / transport failure / out-of-scope 的独立状态。

测试通过后等待下一条工程指令。
```

---

# 27. AI Memory-Recovery Prompt

```text
你是一个完全没有历史上下文的新 AI。

只依据《Invar 403 / 拒绝响应研究架构升级 AI 可复现工程规格书》恢复项目。

先输出：
1. 项目身份
2. 当前阶段
3. 生产代码是否冻结
4. 历史 Handoff 的 next action
5. 当前用户决策如何覆盖历史 next action
6. Denial Classification
7. Transformation Family
8. Semantic Equivalence
9. Evidence Contract
10. 当前已知缺陷
11. 当前唯一允许下一动作

必须标记：
FACT / DERIVED / ASSUMPTION / EXPERIMENT / RECOMMENDATION / UNKNOWN / TBD / UNVERIFIED

如果真实源码与本规格冲突：
- 报告冲突；
- 不自动修正文档；
- 不自动修改源码；
- 真实源码/测试优先。

如果关键文件缺失：
- 报告缺失项；
- 不猜内容；
- 不声称完全复现。

禁止：
- 直接重写整个架构；
- 直接实现 ModelProvider；
- 直接把 403 技巧塞入 MutationPolicy；
- 403→200 自动变成 Vulnerable；
- LLM 替代 deterministic oracle；
- 对未授权目标执行测试。

恢复后只执行用户明确批准的一个工程动作。
```

---

# 28. 完整性自检

## 已完成

- [x] 事实考古
- [x] 证据溯源
- [x] 架构提取
- [x] 契约提取
- [x] 403 历史算法行为
- [x] 社区算法对照
- [x] 兼容边界
- [x] 踩坑与根因
- [x] 测试与验收
- [x] 环境与依赖
- [x] 从零重建路线
- [x] AI 实现 Prompt
- [x] AI 失忆恢复 Prompt
- [x] 完整性自检

## 未达到“历史完全可复现”的原因

- [ ] 真实 Git state
- [ ] lockfiles
- [ ] generated target artifacts
- [ ] scope.txt
- [ ] model weights
- [ ] llama-server build
- [ ] current external target state

以上缺口已显式记录，不允许用猜测填充。

---

# 29. 结论

**架构结论：**

> Invar 不需要自研第二个 `bypass-403.sh`；应该自研的是“拒绝响应研究引擎”。

其核心不是：

```text
更多 payload
```

而是：

```text
为什么被拒绝
→ 改变哪个解释维度
→ 实验产生了什么差分
→ 是否仍是同一资源/同一动作
→ 安全不变量是否被击穿
→ 能否 replay
→ 能否独立验证
→ 证据是否完整
```

最终公式：

```text
Authorized Scope
× Deterministic Baseline
× Denial Hypothesis Set
× Transformation Family
× Adaptive Experiment Selection
× Differential Observation
× Semantic Equivalence
× Security Invariant
× Replay
× Independent Verification
= Evidence-grounded Finding
```

这条公式是 **DERIVED architecture model**，不是任何单一论文或社区项目的原文定理。

---

# Appendix A — Snapshot hashes

- Repomix XML SHA-256: `2e23c46a85e7e05eb814a1cda20d2f61bd6dfb490d8d11bd767c9b44c36c5756`
- AI Engineering Constitution SHA-256: `a5d7e0a42b83a02ebc708c1eebdfb1cc121fc6b552c65996766afcac52d96b56`
- 403 architecture v0.2 SHA-256: `04b11a7f4b0dab39db100b8376a860aaaffe6b26b80130cd4e95f893419496bd`

# Appendix B — Snapshot inventory

- `.github/workflows/.gitkeep`
- `Cargo.toml`
- `HANDOFF.md`
- `README.md`
- `apps/desktop/index.html`
- `apps/desktop/package.json`
- `apps/desktop/src/.gitkeep`
- `apps/desktop/src/App.tsx`
- `apps/desktop/src/index.css`
- `apps/desktop/src/main.tsx`
- `apps/desktop/src-tauri/Cargo.toml`
- `apps/desktop/src-tauri/build.rs`
- `apps/desktop/src-tauri/capabilities/.gitkeep`
- `apps/desktop/src-tauri/capabilities/default.json`
- `apps/desktop/src-tauri/src/.gitkeep`
- `apps/desktop/src-tauri/src/lib.rs`
- `apps/desktop/src-tauri/src/main.rs`
- `apps/desktop/src-tauri/tauri.conf.json`
- `apps/desktop/tsconfig.app.json`
- `apps/desktop/tsconfig.json`
- `apps/desktop/tsconfig.node.json`
- `apps/desktop/vite.config.ts`
- `configs/base/.gitkeep`
- `configs/base/default.json`
- `configs/base/project.toml`
- `configs/profiles/.gitkeep`
- `configs/profiles/research.toml`
- `configs/registry/.gitkeep`
- `configs/registry/backends.toml`
- `configs/schemas/.gitkeep`
- `configs/schemas/config.schema.json`
- `crates/core/Cargo.toml`
- `crates/core/src/lib.rs`
- `crates/core/src/main.rs`
- `crates/core/src/orchestrator.rs`
- `crates/core/tests/orchestrator_contract_test.rs`
- `crates/core/tests/pipeline_e2e_test.rs`
- `crates/core/tests/process_executor_contract_test.rs`
- `crates/core/tests/smoke.rs`
- `data/manifests/.gitkeep`
- `models/invar-intent-0.6b-v1/MODEL_PASSPORT.json`
- `package.json`
- `pnpm-workspace.yaml`
- `python/.python-version`
- `python/packages/core/pyproject.toml`
- `python/packages/core/src/__init__.py`
- `python/packages/core/src/agent/__init__.py`
- `python/packages/core/src/agent/coverage_critic.py`
- `python/packages/core/src/agent/hunter.py`
- `python/packages/core/src/agent/hypothesis_engine.py`
- `python/packages/core/src/agent/knowledge_promoter.py`
- `python/packages/core/src/agent/mutator.py`
- `python/packages/core/src/agent/risk_engine.py`
- `python/packages/core/src/agent/wave_orchestrator.py`
- `python/packages/core/src/harness/__init__.py`
- `python/packages/core/src/harness/ast_worker.py`
- `python/packages/core/src/harness/candidate_models.py`
- `python/packages/core/src/harness/config.py`
- `python/packages/core/src/harness/coverage_ledger.py`
- `python/packages/core/src/harness/evidence.py`
- `python/packages/core/src/harness/exporter.py`
- `python/packages/core/src/harness/extractor.py`
- `python/packages/core/src/harness/feedback.py`
- `python/packages/core/src/harness/finding_models.py`
- `python/packages/core/src/harness/idor_compare.py`
- `python/packages/core/src/harness/invariant_evaluator.py`
- `python/packages/core/src/harness/method_tamper.py`
- `python/packages/core/src/harness/models.py`
- `python/packages/core/src/harness/multi_run.py`
- `python/packages/core/src/harness/mutation_policy.py`
- `python/packages/core/src/harness/reporting.py`
- `python/packages/core/src/harness/research_adapter.py`
- `python/packages/core/src/harness/research_evidence.py`
- `python/packages/core/src/harness/research_models.py`
- `python/packages/core/src/harness/research_worker.py`
- `python/packages/core/src/harness/run_models.py`
- `python/packages/core/src/harness/sandbox_executor.py`
- `python/packages/core/src/harness/transport.py`
- `python/packages/core/src/harness/triage_dispatcher.py`
- `python/packages/core/src/harness/verification_gate.py`
- `python/packages/core/src/invar/__init__.py`
- `python/packages/core/tests/test_smoke.py`
- `python/pyproject.toml`
- `python/scripts/assemble_triage_tasks.py`
- `python/scripts/scan_pipeline.py`
- `python/tests/test_adaptive_sandbox_baseline.py`
- `python/tests/test_adaptive_sandbox_integration.py`
- `python/tests/test_adaptive_sandbox_transport_baseline.py`
- `python/tests/test_ast_worker.py`
- `python/tests/test_candidate_fingerprint.py`
- `python/tests/test_cognitive_orchestration.py`
- `python/tests/test_coverage_ledger.py`
- `python/tests/test_endpoint_registry_contract.py`
- `python/tests/test_feedback_interpreter.py`
- `python/tests/test_finding_record.py`
- `python/tests/test_http_transport.py`
- `python/tests/test_hypothesis_engine.py`
- `python/tests/test_idor_compare.py`
- `python/tests/test_ingest_httpx.py`
- `python/tests/test_ingest_subdomains.py`
- `python/tests/test_invariant_evaluator.py`
- `python/tests/test_knowledge_promoter.py`
- `python/tests/test_method_tamper.py`
- `python/tests/test_multi_run_continuity.py`
- `python/tests/test_mutation_policy.py`
- `python/tests/test_reporting_projections.py`
- `python/tests/test_research_evidence.py`
- `python/tests/test_research_evidence_bridge.py`
- `python/tests/test_research_evidence_history.py`
- `python/tests/test_research_execution_result.py`
- `python/tests/test_research_loop_integration.py`
- `python/tests/test_research_models.py`
- `python/tests/test_research_run.py`
- `python/tests/test_research_task_adapter.py`
- `python/tests/test_research_worker.py`
- `python/tests/test_sandbox_base_url_compatibility.py`
- `python/tests/test_sandbox_idor_integration.py`
- `python/tests/test_sandbox_invariant_integration.py`
- `python/tests/test_sandbox_tamper_integration.py`
- `python/tests/test_scan_pipeline_integration.py`
- `python/tests/test_triage_dispatcher.py`
- `python/tests/test_verification_and_promotion_gate.py`
- `scripts/audit/contract_checker.py`
- `scripts/audit/evaluate_gold_set_v4.py`
- `scripts/audit/project_inventory.py`
- `scripts/data/asset/__init__.py`
- `scripts/data/asset/download_javascript.py`
- `scripts/data/asset/ingest_crtsh.py`
- `scripts/data/asset/ingest_httpx.py`
- `scripts/data/asset/ingest_katana.py`
- `scripts/data/asset/ingest_subdomains.py`
- `scripts/data/asset/materialize_static_get.py`
- `scripts/data/asset/normalize_katana.py`
- `scripts/data/asset/probe_urls.py`
- `scripts/data/asset/triage_dual_track_comparator.py`
- `scripts/data/pipeline/__init__.py`
- `scripts/data/pipeline/build_targets.py`
- `scripts/data/pipeline/fetch_chunk.py`
- `scripts/data/pipeline/scan_pipeline.py`

# Appendix C — Static Python test inventory

- `python/tests/test_adaptive_sandbox_baseline.py`: 1
- `python/tests/test_adaptive_sandbox_integration.py`: 1
- `python/tests/test_adaptive_sandbox_transport_baseline.py`: 2
- `python/tests/test_ast_worker.py`: 2
- `python/tests/test_candidate_fingerprint.py`: 5
- `python/tests/test_cognitive_orchestration.py`: 4
- `python/tests/test_coverage_ledger.py`: 9
- `python/tests/test_endpoint_registry_contract.py`: 5
- `python/tests/test_feedback_interpreter.py`: 3
- `python/tests/test_finding_record.py`: 6
- `python/tests/test_http_transport.py`: 2
- `python/tests/test_hypothesis_engine.py`: 7
- `python/tests/test_idor_compare.py`: 3
- `python/tests/test_ingest_httpx.py`: 5
- `python/tests/test_ingest_subdomains.py`: 8
- `python/tests/test_invariant_evaluator.py`: 5
- `python/tests/test_knowledge_promoter.py`: 5
- `python/tests/test_method_tamper.py`: 4
- `python/tests/test_multi_run_continuity.py`: 4
- `python/tests/test_mutation_policy.py`: 4
- `python/tests/test_reporting_projections.py`: 6
- `python/tests/test_research_evidence.py`: 3
- `python/tests/test_research_evidence_bridge.py`: 1
- `python/tests/test_research_evidence_history.py`: 1
- `python/tests/test_research_execution_result.py`: 2
- `python/tests/test_research_loop_integration.py`: 2
- `python/tests/test_research_models.py`: 5
- `python/tests/test_research_run.py`: 7
- `python/tests/test_research_task_adapter.py`: 4
- `python/tests/test_research_worker.py`: 3
- `python/tests/test_sandbox_base_url_compatibility.py`: 1
- `python/tests/test_sandbox_idor_integration.py`: 1
- `python/tests/test_sandbox_invariant_integration.py`: 2
- `python/tests/test_sandbox_tamper_integration.py`: 1
- `python/tests/test_scan_pipeline_integration.py`: 1
- `python/tests/test_triage_dispatcher.py`: 6
- `python/tests/test_verification_and_promotion_gate.py`: 7
- `python/packages/core/tests/test_smoke.py`: 1

**Static count: 139 test functions across 38 test files.**

# Appendix D — Static Rust test inventory

- `crates/core/src/orchestrator.rs`: 1
- `crates/core/tests/orchestrator_contract_test.rs`: 11
- `crates/core/tests/pipeline_e2e_test.rs`: 1
- `crates/core/tests/process_executor_contract_test.rs`: 1
- `crates/core/tests/smoke.rs`: 1

**Static count: 15 Rust `#[test]` attributes.**

# Appendix E — 当前关键源码索引

```text
python/packages/core/src/harness/models.py
python/packages/core/src/harness/triage_dispatcher.py
python/packages/core/src/harness/research_models.py
python/packages/core/src/harness/transport.py
python/packages/core/src/harness/evidence.py
python/packages/core/src/harness/research_evidence.py
python/packages/core/src/harness/finding_models.py
python/packages/core/src/harness/verification_gate.py
python/packages/core/src/harness/invariant_evaluator.py
python/packages/core/src/harness/idor_compare.py
python/packages/core/src/harness/method_tamper.py
python/packages/core/src/harness/mutation_policy.py
python/packages/core/src/harness/sandbox_executor.py
python/packages/core/src/agent/hypothesis_engine.py
python/packages/core/src/agent/mutator.py
python/packages/core/src/agent/risk_engine.py
python/packages/core/src/harness/candidate_models.py
python/packages/core/src/harness/coverage_ledger.py
python/packages/core/src/harness/reporting.py
python/packages/core/src/harness/run_models.py
crates/core/src/orchestrator.rs
scripts/data/asset/probe_urls.py
```

# Appendix F — Non-negotiable engineering rules

```text
Root cause > patch
Abstraction > special-case
Contract > convention
Reuse > reimplementation
Validation > guessing
Deterministic evidence > LLM assertion
Same-resource proof > status-code optimism
Replay > single observation
Independent verification > self-confirmation
Authorized scope > convenience
```
