# EXP-02 & EXP-03：授权关系基线与单变量差分物理实证报告

> **文档性质**：工程事实审计（FACTS AUDIT）  
> **归档位置**：`docs/笔记/EXP-02-EXP-03-FACTS.md`  
> **审计基准**：基于 `tmp/check_exp02_exp03_baseline_diff.py` 物理实测执行输出 (2026-09-29)  
> **对齐标准**：`SnailSploit/claude-red` (IDOR SOP) 与 `Tencent/AI-Infra-Guard` (A.I.G v4.6.3)

---

## 1. EXP-02 核心发现：现存算子的致命误报陷阱

### 1.1 实测现象与事实表
在 `tmp/check_exp02_exp03_baseline_diff.py` 针对三组场景的物理执行中，现有 `IdorCompareOperator` 表现如下：

| 实验场景 | 输入数据特征 | 期望安全结论 | 现存算子判定 | 判定理据 | 偏差定性 |
|---|---|---|---|---|---|
| **场景 1 (同态泄露)** | 攻击者完全拿到受害者的 User 1001 私密数据 | `VULNERABLE` (击穿) | **`VULNERABLE`** | 相似度 1.00 $\ge$ 0.80 | 正确实锤 |
| **场景 2 (合法自身数据)** | 攻击者访问属于自己的 User 1002 数据 | `CONFIRMED` (安全) | **`VULNERABLE`** | 相似度 0.83 $\ge$ 0.80 | **严重误报 🚨** |
| **场景 3 (同构独立文档)** | 攻击者访问合法的 DOC-90002 文档 | `CONFIRMED` (安全) | **`VULNERABLE`** | 相似度 0.99 $\ge$ 0.80 | **致命误报 🚨** |

### 1.2 根因分析（Root Cause Analysis）
* **病灶代码**：`python/packages/core/src/harness/idor_compare.py`
  ```python
  similarity = difflib.SequenceMatcher(None, victim_response_text, attacker_response_text).ratio()
  if similarity >= cls.SIMILARITY_THRESHOLD:  # 0.80
      return InvariantEvaluation(status="vulnerable", ...)
  ```
* **根因本质**：
  1. **字符级比较无语义感知**：现代 Web API 的 JSON 响应具有相同的键名（Schema）。两份完全合法、仅 ID 和数值不同的数据，结构相似度天然处于 0.85 ~ 0.99 之间；
  2. **缺失对象属主校验（GAP-02 确凿存在）**：系统未建立 `(Subject A, Object A) -> Allowed` 与 `(Subject B, Object A) -> Denied` 的三元组授权基线，而是把“响应长得像”直接等同于“越权数据泄露”。

### 1.3 黄金标准对齐方案（Claude-Red & A.I.G）
* **Claude-Red 的对象引用核准（Object Identification）**：
  判定 IDOR 不能看全文比对，而必须精准比对：**“受害者 A 的核心对象标识符与特有敏感字段，是否赫然出现在攻击者 B 的响应体内”**。
* **腾讯 A.I.G 的金丝雀物证原则（Canary Proof）**：
  严禁没有物理证据支撑的推论判定（Reduce evidence-free false positives）。

---

## 2. EXP-03 核心发现：单变量差分与变异算子现状

### 2.1 物理实测数据
针对端点 `POST https://cloud.ikuai8.com/api/v3/delegate/grant` 生成的 66 个物理变体：
* **单变量变异算子**：53 / 66（占比 **80.3%**），严格做到只改变 1 个物理维度（如仅动路径编码或仅注入单项 IP 伪装头）；
* **多变量协同变异算子**：9 / 66（占比 **13.6%**），主要集中在 `F2_METHOD_SEMANTICS`（动词隧道）与 `F3_HEADER_TRUST_CONTEXT`（重写头）。

### 2.2 变异算子多变量特征客观定性
* **协议必需性**：HTTP 动词隧道（如 `X-HTTP-Method-Override: DELETE`）在物理上必然同时变动“载体动词”与“请求头”，这在 HTTP 规范下属于合法的**原子复合变异族**，不可强行拆散；
* **因果追踪缺口（GAP-03 确凿存在）**：
  - `ProbeAttempt` 目前仅有 `mutation_reason: str` 纯文本描述；
  - 缺乏强类型的 `differential_variable` 与 `transformation_family` 枚举标签，阻碍了下游门禁与测试复盘的自动化机器归因。

---

## 3. 架构结论与演进路线

1. **`GAP-02 (Authorization Baseline)` 状态定为 `INVAR-MISSING`**：
   必须重构 `idor_compare.py`，彻底摒弃粗暴的纯文本相似度，引入基于对象引用提取（Object Reference Extraction）与属主绑定的真正的授权基线判决器。
2. **`GAP-03 (Differential Variable)` 状态定为 `INVAR-PARTIAL`**：
   算子库 80% 已经达标；需为 `ProbeAttempt` 补充结构化的变异族元数据。
3. **Rust 契约保持定力**：
   所有上述改进纯属 Python Harness 内部语义评估，**绝对不需要修改 Rust 的 `ResearchTask` 结构体**！
