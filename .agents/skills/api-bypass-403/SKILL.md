---
name: api-bypass-403
description: "403 Forbidden and WAF access control bypass research. Use when investigating sensitive API endpoints blocked by reverse proxies, WAFs, or restrictive ACLs."
allowed-tools: [curl, ffuf]
metadata:
  surface: api
  attack_class: access_control
  triggers: [status_403, waf_blocked, access_policy_denial]
  required_context: [target_url, baseline_headers]
  success_conditions: [status_200_with_business_data, internal_header_exposed]
  stop_conditions: [out_of_scope, rate_limited, html_homepage_fallback]
  evidence_requirements: [raw_response_bytes, differential_hash]
---

# 403 / WAF 访问控制绕过安全研究剧本 (Playbook)

## 0. 适用范围与交战规则 (Rules of Engagement)
- 仅针对授权范围内声明的受保护业务端点；
- 严禁对非授权的主机资产发起网络扫描；
- 必须基于单变量差分原则验证有效突破。

## 1. 认知假说推演 (Hypothesis)
断言前端反向代理（如 Nginx、Tomcat、云原生 WAF）与后端微服务框架之间存在路径解析语义错位（Path Discrepancy）或动词信任假设缺失。

## 2. 调度执行序列 (Operator Dispatch Sequence)
1. **F1 路径规范化 (Path Normalization)**：
   调度 `PathNormalizationOperator`，探测 Tomcat 分号 `;` 截断、点号 `%2e` 与多斜杠歧义；
2. **F2 动词语义与隧道 (Method Tunneling)**：
   调度 `MethodTunnelOperator`，测试 `X-HTTP-Method-Override` 或动词同义替换；
3. **F3 请求头与代理信任 (Header Trust Context)**：
   调度 `HeaderTrustOperator`，注入 `X-Rewrite-URL`、`X-Original-URL` 或内网 IP 伪造头；
4. **防误报终审 (False-Positive Elimination)**：
   若收到 200，必须核实响应正文绝非公共首页或登录页 HTML 回退，必须包含真实业务私密字段方准立项。
