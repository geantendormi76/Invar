# AI Development Handoff Specification

## 0. Handoff Metadata

| 属性项 | 属性值 | 事实等级 | 说明 |
|---|---|---|---|
| Project Name | Invar | [FACT] | System-2 深度动态执行、差分对账与安全不变量实证主引擎 |
| Repository Root | `C:\dev\Invar` | [FACT] | 标准 AI Engineering Monorepo 体系（Rust + Python） |
| Snapshot Timestamp | 2026-09-23 15:50:00 JST | [FACT] | 状态快照生成时间点 |
| Document Version | 12.0.0 (Gold Standards Fully Aligned: OpenVEX & SARIF 2.1.0 & Zero-FP Finalized) | [DECISION] | 国际标准对齐、双重误报消灭、本地消融模型贯通 |
| Python Core Test Status | **202 passed in 0.40s; 0 failed** | [FACT] | 验证命令：`uv run --project python pytest` |
| Rust Core Test Status | **15 passed; 0 failed** | [FACT] | 验证命令：`cargo test --workspace` |
| Primary Model Backend | `Ornith-1.5-9B-Abliterated-IQ3_M` | [FACT] | 运行于 `http://127.0.0.1:8080/v1` (开源消融对齐版) |
| Architecture Topology | Headless & Dual-Brain Protocol | [DECISION] | 架构大脑出原子指令，本地消融模型专职现场取证与单步执行 |

---

## 1. Project Identity

[DECISION]
本系统属于工业级三位一体架构（Triad Architecture）中的实证闭环中枢：
1. **distiller**: 知识蒸馏与物理隔离防火墙（`Train ∩ Gold = ∅`）。
2. **base-jev**: 0.6B System-1 神经认知反射前哨。
3. **Invar**: **System-2 深度科研与动态实证主引擎**。
   - 贯彻“零臆造、零重复造轮子”的黄金标准对齐哲学；
   - 吸收社区成熟变异经验（nomore403 / NoMoreForbidden 现代反代信任头库）；
   - 输出端双黄金认证闭环：**OpenSSF OpenVEX v0.2.0** 与 **OASIS SARIF 2.1.0**。

---

## 2. Completed Milestones

| 战略路线 | 状态 | 关键成果与物证 |
| :--- | :--- | :--- |
| **选项 A (全量实证)** | **DONE** | 78 任务全量实证跑通，48/48 覆盖率达成。彻底消灭 Windows 注册表代理挂死（发包提速近 10 倍）；消灭软 403 业务错误码与 SPA 前端 `index.html` 兜底引发的全部 12 个假阳性误报，实证漏洞收敛至绝对真实的 0 误报基线。 |
| **选项 B (Phase 5.4 破局)** | **DONE** | 成功贯通本地开源模型 `Ornith-1.5-9B-Abliterated` (8080 端口)。新增 `LLM_REASONING_STARTED` / `COMPLETED` 强类型事件与自愈 JSON 提取，启发式变异耗尽时平滑触发单次 CoT 反思。 |
| **选项 C (Phase 5.5 交付)** | **DONE** | 全面吸纳开源标准。变异库升级 F1/F2/F3；战报投影器扩展至 7 大权威产物，全自动输出 `sarif.json`（支持 VS Code / GitHub 直接渲染）与 `openvex.json`（支持 OpenSSF 供应链合规消费）。 |

---

## 3. Architecture Decisions & Failure Registry

### AD-01 — Dual-Brain Engineering Topology (分层双脑协同规范)
* **Rule**: 严禁让 9B 本地模型充当全自主全局架构师（极易触发长思维链自我催眠与 30 分钟死循环）；必须将其定位为“受控现场探针与工具执行器”，由长上下文主控提供原子化 PowerShell 脚本落盘，本地模型专职取证与执行。

### AD-02 — Windows Registry Proxy Bypass (Windows 注册表代理彻底隔离)
* **Rule**: 在 Windows 上仅 `pop("ALL_PROXY")` 无法阻止 `requests` 从注册表读取代理。必须在 `transport.py` 初始化时设置 `os.environ["NO_PROXY"] = "*"`，确保物理网络请求绝对直连。

### AD-03 — Two-Tier False-Positive Defense (双重假阳性防御铁律)
* **Rule 1 (软拒绝识别)**: HTTP 200 伴随 `code in {4001, 4003, 4008}` 或 `message: "forbidden"` 时，安全底线评估器必须裁决为 `confirmed`（安全拦截），严禁因状态码为 200 误判为特权放行。
* **Rule 2 (SPA 前端回退识别)**: HTTP 200 伴随 `<!DOCTYPE html>` 或 `<html` 时，证明系前端单页应用路由未命中兜底，语义等价判定为非目标接口，严禁判定为漏洞击穿。

---

## 4. Current Test Baseline

* **Python Tests**: `202 passed in 0.40s; 0 failed` (`uv run --project python pytest`)
* **Rust Tests**: `15 passed; 0 failed` (`cargo test --workspace`)
* **P0 Audit Baseline**: `7/7 coverage, 0 vulnerable, openvex & sarif projected cleanly`
