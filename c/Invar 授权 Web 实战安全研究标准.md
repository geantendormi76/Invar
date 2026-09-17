# Invar 授权 Web 实战安全研究标准

> **定位**：Invar 用于经明确授权的 Web 安全研究、漏洞验证与漏洞报告的长期标准执行流程。
>
> **核心思想**：
>
> ```text
> 资产发现
> → 资产验证
> → 资产归一化
> → Invar 接管
> → 静态分析
> → 风险量化
> → 假说生成
> → 最小真实验证
> → 证据固化
> → Promotion Gate
> → 知识沉淀
> ```
>
> **最高原则**：
>
> ```text
> 有授权才测试
> 有依据才实现
> 有抽象才扩展
> 有测试才交付
> 有证据才晋级
> ```

---

# 0. 安全与授权边界

所有主动探测、真实 HTTP 请求、认证测试、越权验证、状态改变操作，都必须发生在明确授权范围内。

必须首先确定：

```text
授权根域
授权子域
授权路径
允许的请求类型
允许的测试时间
禁止测试的系统
禁止测试的高危操作
```

推荐建立：

```text
scope.txt
```

作为所有后续工具的输入边界。

任何工具发现的资产都只是：

> **候选资产**

而不是天然获得测试授权。

---

# 1. 总体架构

Invar 的完整实战体系分成两个大的区域。

## 1.1 Invar 接管之前：资产采集层

负责：

```text
Subfinder
→ HTTPX
→ Katana
→ JS / URL / Host
→ 本地资产归档
```

这一层的目标不是判断漏洞，而是回答：

```text
目标有哪些资产？
哪些资产在线？
哪些资产值得继续分析？
哪些前端资源属于第一方？
```

---

## 1.2 Invar 接管之后：研究认知层

从：

```text
raw_js/
```

开始正式进入 Invar：

```text
AST
→ EndpointIR
→ RiskEngine
→ HypothesisEngine
→ AdaptiveSandboxExecutor
→ InvariantEvaluator
→ Evidence
→ Promotion Gate
→ KnowledgeCard
```

工程规格书已经把这一体系定义为：

```text
AST
↓
强类型契约
↓
安全不变量
↓
可替换执行器
↓
证据链
↓
假说验证
↓
知识晋级
```

并要求系统满足可复现、可测试、可追溯、可替换、可扩展和可审计。 

---

# 2. 阶段 0：授权范围建立

## 输入

```text
授权根域
授权子域
授权业务系统
授权测试时间
```

## 输出

```text
scope.txt
```

## 门禁

未进入授权范围的资产不得进入主动探测阶段。

---

# 3. 阶段 1：Subfinder 资产发现

## 目标

发现根域范围内的候选子域资产。

## 工具

```text
Subfinder
```

## 标准命令

```powershell
subfinder -d ikuai8.com -silent -o "C:\dev\Invar\tmp\ikuai8_subdomains.txt"
```

## 输出

```text
ikuai8_subdomains.txt
```

## 示例结果

当前研究中已经得到：

```text
99 个候选子域
```

## 重要认识

Subfinder 输出：

```text
候选资产
```

而不是：

```text
已确认存活资产
```

所以不能直接把所有结果送进真实研究。

---

# 4. 阶段 2：HTTPX Web 存活与技术画像

## 目标

验证 Subfinder 发现的资产是否存在 Web 服务，并建立基础画像。

## 输入

```text
资产清洗后的subdomains.jsonl
```

## 标准流程

不要只检测单个主站。

长期标准应该是：

```text
Subfinder
→ subdomains.jsonl
→ HTTPX 批量探测
```

## 建议输出

```text
live_hosts.jsonl
```

至少保留：

```text
host
scheme
status_code
title
server
technologies
redirect
content_type
```

## 示例

```powershell
httpx -l "C:\dev\Invar\tmp\ikuai8_subdomains.txt" -title -tech-detect -status-code -server -json -silent -o "C:\dev\Invar\tmp\ikuai8_httpx.jsonl"
```

## 门禁

只有：

```text
在线
+
属于授权范围
+
具备可研究 Web 服务
```

的资产，才能进入 Katana。

---

# 5. 阶段 3：Katana 深度资产采集

## 目标

从存活 Web 资产继续提取：

```text
URL
API 路径
JS
JS Chunk
前端资源
```

## 核心能力

```text
URL Discovery
JS Crawling
Deep Crawling
```

## 不应长期固定为

```text
katana -u "https://www.ikuai8.com"
```

因为这只覆盖一个入口。

正确理念应该是：

```text
HTTPX 存活资产
→ Katana 批量输入
```

例如：

```powershell
katana -list "C:\dev\Invar\tmp\ikuai8_live_hosts.txt" -jc -depth 2 -concurrency 5 -silent -no-color -o "C:\dev\Invar\tmp\ikuai8_katana.txt"
```

---

# 6. 阶段 4：资产归一化

这是未来整个系统非常重要的一层。

不能让：

```text
Subfinder
HTTPX
Katana
下载器
Invar
```

各自维护互不关联的文件。

应该建立：

```text
Asset Registry
```

## 推荐模型

```text
asset_id
source
source_url
final_url
hostname
asset_type
first_party_state
status_code
content_type
local_path
sha256
```

---

# 7. 第一方资产分类

不能长期依赖：

```text
if "baidu"
if "qq"
if "7moor"
if "xxx"
```

这种人工黑名单。

长期标准应该使用：

```text
FIRST_PARTY
THIRD_PARTY
UNKNOWN
```

并结合：

```text
hostname
registrable domain
redirect
source URL
content type
```

进行归类。

其中：

```text
UNKNOWN
```

不能默认为第三方。

---

# 8. JavaScript 资产保存标准

## 当前历史结果

曾经得到：

```text
118 个 JS URL
116 个成功下载
104 个本地 JS 文件
```

这组数字必须保留为一次资产基线。

---

# 9. JS 下载器的数据完整性要求

旧下载方式存在潜在覆盖问题：

```python
filename = Path(parsed.path).name
target_path = save_dir / parsed.netloc / filename
```

例如：

```text
/a/app.js
/b/app.js
```

可能都写成：

```text
host/app.js
```

导致覆盖。

因此未来标准必须保证：

```text
URL
→ 唯一 Asset ID
→ 唯一文件
```

---

# 10. 推荐资产唯一性

推荐至少保存：

```text
source_url
final_url
sha256
local_path
```

并建立：

```text
asset_manifest.json
```

例如：

```json
{
  "asset_id": "…",
  "source_url": "…",
  "final_url": "…",
  "hostname": "…",
  "local_path": "…",
  "sha256": "…",
  "content_type": "application/javascript"
}
```

目标：

```text
可复现
可追溯
不可静默覆盖
```

这与 Invar 的工程规格一致。 

---

# 11. Invar 接管边界

## 边界定义

```text
Subfinder
HTTPX
Katana
下载器
        ↓
      raw_js/
        ↓
============================
        INVAR
============================
        ↓
AST
```

因此：

> **`raw_js/` 是资产采集层与 Invar 核心研究层的逻辑边界。**

---

# 12. 阶段 5：Tree-sitter AST 静态解析

## 输入

```text
C:\dev\Invar\tmp\raw_js
```

## 核心组件

```text
harness.extractor.JSEndpointExtractor
```

## 标准命令

```powershell
$env:PYTHONPATH="C:\dev\Invar\src-tauri\python\src"; uv run --project "C:\dev\Invar\src-tauri\python" --python 3.11 python "C:\dev\Invar\scripts\pipeline\scan_pipeline.py" "C:\dev\Invar\tmp\raw_js" -o "C:\dev\Invar\tmp\ikuai8_endpoints_report.json"
```

## 当前已验证结果

```text
104 个本地 JS
↓
419 个 API 节点
```

---

# 13. 阶段 6：EndpointIR 标准化

AST 不应该直接进入攻击逻辑。

必须先转成标准：

```text
EndpointIR
```

当前核心字段包括：

```text
method
path
source_file
line
is_dynamic
extracted_params
tags
risk_score
confidence
call_signature
```

EndpointIR 是：

> **静态代码世界 → 研究任务世界**

之间的标准中间表示。

---

# 14. 阶段 7：RiskEngine 风险量化

## 输入

```text
EndpointIR
```

## 输出

风险：

```text
CRITICAL
HIGH
MEDIUM
LOW
```

以及：

```text
tags
risk_score
```

---

# 15. 当前实际研究基线

当前真实 AST + RiskEngine 结果：

```text
419 EndpointIR
↓
90 参数丰富接口
↓
8 CRITICAL
25 HIGH
```

因此：

```text
33 个 HIGH / CRITICAL
```

进入高价值研究候选空间。

但是必须明确：

```text
33 个高风险接口
≠
33 个漏洞
```

风险评分只能产生：

> **研究候选**

不能产生漏洞结论。

---

# 16. 阶段 8：研究候选提炼

从：

```text
419
```

逐渐收缩：

```text
419
 ↓
90 参数接口
 ↓
33 HIGH / CRITICAL
 ↓
研究语义分类
```

重点识别：

```text
ID
user_id
order_id
role
admin
token
auth
delete
batch
remove
config
private
```

以及：

```text
state-changing
sensitive-route
destructive
```

---

# 17. 阶段 9：HypothesisEngine

RiskEngine 不直接决定漏洞。

它首先产生：

```text
Hypothesis
假说
```

当前主要研究类型：

```text
H-IDOR
H-AUTH
H-DESTRUCT
```

---

# 18. IDOR / BOLA 研究模型

## 假说

```text
对象标识符可能允许跨租户 / 跨用户访问
```

## 标准验证思想

```text
Subject A
→ 自己的资源
→ 建立基线

Subject B
→ 请求 A 的资源
→ 获得对照响应

       ↓

IdorCompareOperator
       ↓

差分判断
```

这与现有双主体 IDOR 测试契约一致。

---

# 19. IDOR 判断标准

不能：

```text
200 = 漏洞
```

必须：

```text
401 / 403
→ confirmed

2xx
→ 深度响应差分

高相似
→ vulnerable

低相似
→ confirmed

异常状态
→ inconclusive
```

当前 `IdorCompareOperator` 使用响应结构相似度作为一个确定性判断因素。

---

# 20. AUTH 研究模型

重点关注：

```text
/admin
/private
/manage
/config
```

等敏感路由。

研究目标：

```text
无凭证
→ 是否被拒绝？

错误凭证
→ 是否被拒绝？

低权限主体
→ 是否可以访问高权限资源？
```

注意：

```text
静态命中 admin
≠
存在未授权
```

必须进入真实验证。

---

# 21. DESTRUCT 研究模型

关注：

```text
DELETE
batch
delete
drop
purge
clear
remove
```

研究目标：

```text
破坏性操作
→ 是否具有必要确认机制？
```

不能直接执行破坏性请求。

必须受到：

```text
授权范围
测试环境
最小影响
安全保护
```

约束。

---

# 22. HTTP Method Tamper

当前已装配：

```text
MethodTamperOperator
```

支持：

```text
HEADER_TUNNEL
QUERY_TUNNEL
VERB_SUBSTITUTION
```

当前代码支持：

```text
X-HTTP-Method-Override
X-Method-Override
X-HTTP-Method
```

以及：

```text
_method
method
```

等变体。

---

# 23. Method Tamper 的正确定位

它不是：

> “看到 403 就无限绕过。”

它应该是：

```text
明确研究假说
+
403 / 405
+
允许进行该类验证
```

时，作为：

> **语义解耦研究算子**

进入验证链。

核心研究对象：

```text
WAF
↓
反向代理
↓
Web Server
↓
框架
↓
业务路由
```

之间的 HTTP 方法解释差异。

---

# 24. AdaptiveSandboxExecutor

这是当前 Invar 的真实执行中心。

职责：

```text
构造请求
↓
主体 A 基线
↓
反馈解释
↓
自适应变异
↓
高级算子
↓
主体 B 对照
↓
不变量评估
↓
假说决算
↓
证据生成
```

目前已经实际装配：

```text
IdorCompareOperator
MethodTamperOperator
```

源码中 IDOR 分支会使用 `auth_token_b` 发送 Subject B 请求，并进入 `IdorCompareOperator.compare(...)`。

---

# 25. Evidence 证据链

所有真实研究必须形成：

```text
Evidence
```

而不是：

```text
AI 认为存在漏洞
```

至少记录：

```text
Request
Response
Status Code
Headers
Payload
Attempt Number
Mutation
Interpretation
Timestamp
Finding Type
```

---

# 26. Promotion Gate

这是整个系统最重要的可信度门禁之一。

状态：

```text
PROPOSED
```

只能代表：

> 假说

不能代表：

> 漏洞

只有：

```text
真实证据
↓
InvariantEvaluation
↓
VERIFIED / REFUTED
```

才允许进入知识层。

规格书明确规定，不允许未经验证的假说直接生成知识卡片。

---

# 27. KnowledgeCard

经过晋级后，形成：

```text
KnowledgeCard
```

保存：

```text
claim
severity
verification_state
confidence
source_hypothesis
provenance_task
remediation
evidence_summary
```

这样一次真实研究才真正从：

```text
HTTP 请求
```

转变成：

```text
可复用知识
```

---

# 28. TDD 在实战系统里的正确位置

TDD 不意味着：

```text
每次实战前都要先造假靶场
```

正确理解：

## 软件层

```text
TDD
→ 验证 Invar 自己是否正确
```

## 实战层

```text
真实授权目标
→ 真实 HTTP
→ 真实证据
```

两者最后汇合：

```text
软件正确性证据
+
真实目标行为证据
=
可靠研究结论
```

当前 Invar 已经完成：

```text
Python 44/44
Rust 全绿
IDOR 集成测试
Tamper 集成测试
```

因此软件契约已经具备进入真实资产研究的基础。

---

# 29. 研究漏斗

未来每个目标都尽量遵循：

```text
授权资产
   ↓
Subfinder
   ↓
候选子域
   ↓
HTTPX
   ↓
存活 Web
   ↓
Katana
   ↓
URL / JS
   ↓
第一方资产
   ↓
raw_js
   ↓
AST
   ↓
EndpointIR
   ↓
RiskEngine
   ↓
高风险候选
   ↓
HypothesisEngine
   ↓
研究假说
   ↓
AdaptiveSandboxExecutor
   ↓
真实 HTTP
   ↓
Evidence
   ↓
InvariantEvaluator
   ↓
VERIFIED / REFUTED
   ↓
Promotion Gate
   ↓
KnowledgeCard
```

---

# 30. 研究对象优先级

不直接使用“看起来危险”作为标准。

优先寻找：

```text
身份边界
对象边界
权限边界
状态改变
资源拥有关系
敏感业务逻辑
```

尤其关注：

```text
ID
user_id
order_id
role
admin
owner
account
group
tenant
resource
```

以及：

```text
DELETE
PUT
PATCH
POST
batch
export
import
config
```

---

# 31. 真实请求原则

所有真实探测遵循：

```text
最小请求
最小变异
最小副作用
最少次数
可恢复
可审计
```

不要把：

```text
大量 Payload
大量字典
大量无意义请求
```

当成研究质量。

核心原则：

> **算法重于字典。**

规格书已经明确反对把大规模 Payload 字典硬塞入沙箱，而要求优先利用结构化安全不变量和精准验证。

---

# 32. Windows 工程标准

始终：

```text
Windows
PowerShell
uv
Cargo
```

Python：

```text
uv run --project ...
```

禁止：

```text
pip
裸 python
```

跨进程通信优先：

```text
stdin
stdout
Stdio::piped()
```

避免：

```text
命令行 JSON 参数
```

这是当前工程已经验证过的 Windows IPC 经验。

---

# 33. 性能标准

禁止：

```text
一个 Endpoint
→ Spawn 一个 Python
```

必须尽可能：

```text
多个 ResearchTask
→ 一个 Python Worker
→ Batch IPC
```

当前工程已经将 Single-Invocation Batch IPC 作为核心性能模型。

---

# 34. 不允许的工程模式

禁止：

```text
if endpoint == xxx
if filename == xxx
if user_id == xxx
if token == xxx
```

禁止：

```text
一个失败
→ 加一个 if
→ 再加一个特殊变量
→ 再加一个例外
```

必须优先检查：

```text
接口
类型
数据契约
职责边界
抽象
复用
```

---

# 35. 不允许的研究结论

禁止：

```text
200 OK
→ 漏洞
```

禁止：

```text
403
→ 肯定有 WAF 绕过
```

禁止：

```text
静态高风险
→ 已经存在漏洞
```

禁止：

```text
AI 推测
→ 漏洞报告
```

正确结论只能来自：

```text
真实 HTTP 事实
+
确定性不变量判断
+
证据链
```

---

# 36. 每个目标的标准产物

推荐最终形成：

```text
tmp/
├── scope.txt
├── subdomains.txt
├── httpx.jsonl
├── katana.txt
├── js_urls.txt
├── first_party_js.txt
├── raw_js/
├── asset_manifest.json
├── endpoints_report.json
├── research_candidates.json
├── evidence/
├── knowledge_cards/
└── final_report/
```

这样每一次研究都具有独立可复现性。

---

# 37. 每个阶段都必须回答的问题

## 资产阶段

```text
我测到了哪些资产？
这些资产是否授权？
哪些在线？
```

## AST 阶段

```text
代码中发现了什么？
有哪些 EndpointIR？
参数是什么？
```

## Risk 阶段

```text
哪些值得进一步研究？
为什么？
```

## Hypothesis 阶段

```text
具体怀疑什么？
依据是什么？
```

## Sandbox 阶段

```text
实际发了什么？
服务端返回什么？
```

## Evidence 阶段

```text
证据是否足够？
```

## Promotion 阶段

```text
事实证明还是证伪了什么？
```

---

# 38. 当前 Invar 已达到的真实基线

截至当前工程状态：

```text
资产发现
        ✅

HTTP / Web 画像
        ✅

Katana URL / JS 采集
        ✅

JS 本地化
        ✅

AST
        ✅

EndpointIR
        ✅

RiskEngine
        ✅

HypothesisEngine
        ✅

IDOR Compare
        ✅

Method Tamper
        ✅

AdaptiveSandbox 装配
        ✅

Evidence
        ✅

Promotion Gate
        ✅

Python
44 / 44
✅

Rust
全绿
✅
```

当前真实研究资产基线：

```text
99  个候选子域
118 个 JS URL
116 个下载成功
104 个本地 JS
419 个 API 节点
90  个参数丰富接口
8   个 CRITICAL
25  个 HIGH
```

---

# 39. 当前真实研究阶段

因此当前不再属于：

```text
工具安装阶段
```

也不再属于：

```text
Invar 基础架构验证阶段
```

而是正式进入：

```text
真实资产
    ↓
研究候选提炼
    ↓
真实 HTTP 验证
```

即：

> **Invar 核心研究框架已经具备接管真实授权资产的条件。**

---

# 40. 未来每次实战的最简执行口诀

```text
先定范围
↓
找资产
↓
验在线
↓
爬入口
↓
收资源
↓
资产归一化
↓
交给 Invar
↓
AST
↓
风险
↓
假说
↓
最小验证
↓
证据
↓
晋级
```

进一步浓缩成：

```text
资产 → 结构 → 风险 → 假说 → 证据 → 知识
```

---

# 41. 永远不要忘记的核心边界

```text
发现 ≠ 授权
在线 ≠ 可攻击
静态风险 ≠ 漏洞
200 ≠ 越权
403 ≠ 安全
假说 ≠ 事实
测试通过 ≠ 真实目标存在漏洞
VERIFIED 才是知识晋级门槛
```

---

# 42. Invar 的最终研究模型

```text
                世界
                 │
                 ▼
          外部资产采集工具
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
 Subfinder     HTTPX       Katana
     │           │           │
     └───────────┼───────────┘
                 ▼
           Asset Registry
                 │
                 ▼
              raw_js
                 │
════════════ INVAR CORE ════════════
                 │
                 ▼
               AST
                 │
                 ▼
            EndpointIR
                 │
                 ▼
            RiskEngine
                 │
                 ▼
         HypothesisEngine
                 │
                 ▼
       AdaptiveSandboxExecutor
          │                 │
          ▼                 ▼
       IDOR Compare     Method Tamper
          │                 │
          └────────┬────────┘
                   ▼
           InvariantEvaluator
                   │
                   ▼
                Evidence
                   │
                   ▼
             Promotion Gate
                   │
            ┌──────┴──────┐
            ▼             ▼
         VERIFIED       REFUTED
            │             │
            └──────┬──────┘
                   ▼
             KnowledgeCard
```

> **这套流程的目的，不是让 Invar “自动打更多请求”，而是让机械资产采集逐渐收敛成高价值、可解释、可复现、可审计的安全研究任务。**
>
> **工具负责发现世界；Invar 负责理解世界；Evidence 负责证明世界；Promotion Gate 负责阻止猜测冒充事实。**