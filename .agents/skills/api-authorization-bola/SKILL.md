---
name: api-authorization-bola
description: "BOLA / IDOR cross-tenant authorization security research. Use when investigating API endpoints exposing object identifiers (e.g. order_id, user_id, uuid) or enforcing multi-tenant isolation boundaries."
allowed-tools: [curl, ffuf]
metadata:
  surface: api
  attack_class: authorization
  triggers: [object_identifier, tenant_context, idor_keywords]
  required_context: [attacker_principal, victim_principal]
  success_conditions: [cross_tenant_data_exposed, secret_fields_leaked]
  stop_conditions: [out_of_scope, rate_limited]
  evidence_requirements: [raw_response_bytes, principal_binding]
---

# BOLA / IDOR 对象级越权安全研究剧本 (Playbook)

## 0. 适用范围与交战规则 (Rules of Engagement)
- 仅针对授权范围内声明的业务 API 端点；
- 严禁执行具有破坏性的横向越权操作 (如未经授权的 DELETE / 密码重置)；
- 必须基于只读 GET 或受控状态对比进行差分断言。

## 1. 认知假说推演 (Hypothesis)
断言目标系统在微服务或控制器层仅校验了请求方的身份有效性 (Authentication)，
但彻底遗漏了针对特定资源属主与调用方租户上下文的关联校验 (Broken Object Level Authorization)。

## 2. 实验步骤与物理发包序列 (Experiment Sequence)
1. **基线获取 (Baseline Read)**：
   使用合法属主 (Victim Principal) 的凭证发起标准读取请求，记录状态码为 200，并提取私密业务标识符与数据切片；
2. **多主体差分攻击 (Differential Attack)**：
   保持请求的目标资源 URL 与对象标识符绝对不变，将凭据严格替换为潜在攻击者主体 (Attacker Principal) 的合法凭证；
   调用 `curl` 执行标准物理发包；
3. **安全不变量求值 (Invariant Evaluation)**：
   - 若攻击者收到 401 / 403 明确拦截：防御守住 (DEFENSE_HELD)；
   - 若攻击者收到 200 且响应体中赫然包含了受害者的私密数据：实锤击穿不变量 (VULNERABLE + SUFFICIENT)；
4. **合成最小复现 PoC**：
   提取物理发包物证，合成单行无损的标准 cURL 命令交付独立复核器。
