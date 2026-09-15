# 🛡️ Invar 项目跨会话交接档案 (HANDOFF SPECIFICATION v2.0)

> **归档时间**: 2026-09-15  
> **项目物理主权根目录**: `C:\dev\Invar`  
> **核心开发哲学**: 钱学森系统工程哲学 + 工业级 Rust/Python 双引擎 Monorepo 规范 + 彭峙酿（Zhiniang Peng）Offbyone 2026 闭环 Agent 理论  
> **面向对象**: 接管本项目的全新 AI 智能体 / 核心架构师

---

## 1. 核心背景与我们在做什么

### 1.1 业务使命
针对自研 Web API（如 Go/Gin、Vue/React 前端），构建新一代自动化逆向、契约推导与逻辑漏洞挖掘系统。
通过前端打包混淆 JS 代码，全自动提炼路由与真实参数字典，并模拟真实黑客通过运行环境报错（如 Go validator 拦截）实现**自主自省变异与闭环击穿**。

### 1.2 理论核心来源：彭峙酿《A Year of Hacking with LLMs》
我们彻底放弃了 2023 年“用微调模型做静态文本模式匹配”的死胡同，对齐其 2025–2026 年验证成功的实战范式：
1. **Deterministic Harness（确定性预处理脚手架）**: 用 Tree-sitter C 扩展直推提取 AST，不用大模型生啃海量代码，0 Token 消耗完成数据降维。
2. **Security Invariant Reasoning（安全不变量威胁建模）**: 关注权限边界破坏、破坏性动作（DELETE）、敏感路由加权，而非机械匹配已知的 CVE 文本。
3. **In-Silico Verification & Feedback Loop（物理环境执行自愈闭环）**: 发包 -> 截获 400 校验报错或堆栈 -> 解析真实结构 -> 变异 Payload -> 再次发包直至 200/404 击穿。

---

## 2. 1:1 全量资产迁移与补齐对账总表

原工程代码位于 `D:\核心开发内容\开发积累\3_核心经验算法\0_开发项目\C_逆向渗透\tools`。经白盒对账，全量代码去向与状态如下：

| 原 tools 物理文件 | 对应功能定位 | 迁移至 Invar 的物理路径 | 状态 |
| :--- | :--- | :--- | :--- |
| `js_ast/core/models.py` | API 契约中间表示 | `src-tauri/python/src/harness/models.py` | ✅ 已完成 (含多态解包容错) |
| `js_ast/core/evidence.py` | 快照级证据链 | `src-tauri/python/src/harness/evidence.py` | ✅ 已完成 (快照发包日志) |
| `js_ast/core/extractor.py` | AST 接口提取引擎 | `src-tauri/python/src/harness/extractor.py` | ✅ 已完成 (多语法下潜) |
| `js_ast/core/dataflow_analyzer.py` | AST 参数 Key 剥离 | `src-tauri/python/src/harness/extractor.py` | ✅ 已完成 (融合吸收) |
| `js_ast/analysis/sota_ast_analyzer.py` | 参数签名提取 | `src-tauri/python/src/harness/extractor.py` | ✅ 已完成 (统一标准化) |
| `js_ast/core/exporter.py` | JSON 导入导出 | `src-tauri/python/src/harness/exporter.py` | ✅ 已完成 (支持列表与复合战报) |
| `js_ast/core/config.py` | 运行环境配置 | `src-tauri/python/src/harness/config.py` | ✅ 已完成 (自适应跨平台) |
| `js_ast/core/classifier.py` | 关键词风险打标 | `src-tauri/python/src/agent/risk_engine.py` | ✅ 已完成 (加权归一化) |
| `js_ast/core/risk_engine.py` | 0.0~10.0 多维打分 | `src-tauri/python/src/agent/risk_engine.py` | ✅ 已完成 (四级风险标签) |
| `js_ast/core/sandbox_executor.py` | 沙箱探针执行器 | `src-tauri/python/src/harness/sandbox_executor.py` | ✅ 已完成 (升级第二代自适应闭环) |
| `js_ast/runtime/sota_payload_executor*.py`| 契约并发探针 | `src-tauri/python/src/harness/sandbox_executor.py` | ✅ 已完成 (多线程自愈闭环) |
| `js_ast/core/scanner.py` | 全链路扫描流水线 | `scripts/pipeline/scan_pipeline.py` | ✅ 已完成 (全链路 CLI) |
| `js_ast/core/contract_checker.py` | 契约合规检测器 | `scripts/audit/contract_checker.py` | ✅ 已完成 (松散与二次确认审计) |
| `project_inventory.py` | 资产 SHA256 盘点 | `scripts/audit/project_inventory.py` | ✅ 已完成 (17 模块全量受控) |
| `js_ast/builders/build_targets.py` | 扫描器目标构建 | `scripts/pipeline/build_targets.py` | ✅ **已补齐** (生成 Nuclei/FFUF 清单) |
| `js_ast/experiments/fetch_missing_chunk.py` | 缺失 Chunk 下载 | `scripts/pipeline/fetch_chunk.py` | ✅ **已补齐** (带 127.0.0.1:7897 代理) |
| `js_ast/experiments/exploit_jwt_and_privesc.py` | JWT 逆向与爆破 | `src-tauri/python/src/agent/jwt_auditor.py` | ⏳ **待迁移补齐 (下会话第一步)** |
| `js_ast/experiments/bypass_rate_limit_bruteforce.py` | IP 伪造抗体 (429 绕过) | 并入 `src-tauri/python/src/harness/sandbox_executor.py` | ⏳ **待迁移补齐 (下会话第二步)** |
| `js_ast/analysis/idor_extractor_engine.py` | IDOR 平行越权遍历 | `src-tauri/python/src/agent/idor_engine.py` | ⏳ **待迁移补齐 (下会话第三步)** |
| `js_ast/experiments/exploit_4cards.py` (空间2) | Base64 会话载荷注入 | 并入 `src-tauri/python/src/agent/mutator.py` | ⏳ **待迁移补齐 (下会话第四步)** |

---

## 3. 当前精确停驻节点 (Checkpoint)

- **物理位置**: `C:\dev\Invar`
- **当前状态**: 
  1. 核心大一统 Monorepo 框架已建立，`uv sync` 锁死，Rust/Python 结构健全；
  2. 核心脚手架（AST 提取、模型、导出器、自愈沙箱执行器、威胁评估）全部经过 TDD 断言测试（100% 绿灯通过）；
  3. 查漏补缺任务已完成第一项（`build_targets.py`）和第二项（`fetch_chunk.py`）；
  4. 综合流水线 `scan_pipeline.py`、合规审计 `contract_checker.py` 与资产盘点 `project_inventory.py` 运行顺畅。

---

## 4. 下一个会话启动后的立即可执行计划

新会话打开后，请立即按以下顺序收尾剩余的 4 项实战算子移植：

### 任务 1：迁移落盘 `src-tauri/python/src/agent/jwt_auditor.py`
- 将原 `exploit_jwt_and_privesc.py` 的算法抽象为规范的类：
  - JWT Header / Payload 解码（Base64 URL Safe）；
  - 提取角色属性（role, user_id, email）；
  - 常见弱口令 HMAC-SHA256 对称密钥本地碰撞爆破器；
  - 普通用户 Token 垂直越权管理员接口探测矩阵。

### 任务 2：为 `AdaptiveSandboxExecutor` 注入 429 绕过抗体
- 将 `bypass_rate_limit_bruteforce.py` 中的 IP 伪造算法提炼为注入选项：
  - 发包时动态生成随机公网 IP 并注入 `X-Forwarded-For`、`X-Real-IP`、`Client-IP`；
  - 遭遇 429 Too Many Requests 时自动轮换 IP 再次重发。

### 任务 3：迁移落盘 `src-tauri/python/src/agent/idor_engine.py`
- 将原 `idor_extractor_engine.py` 规范化为 IDOR 遍历器：
  - 读取 AST 提炼出的带 `${...}` 或 `dynamic: True` 接口；
  - 遍历测试典型业务 ID（如真实订单号列表、递增 ID）；
  - 依据状态码与返回数据长度沉淀 IDOR 漏洞凭证。

---

## 5. 核心避坑与绝对红线数据库 (Pitfalls DB)

新会话的 AI **必须严格遵守以下法则，绝对严禁触犯**：

1. ❌ **严禁在 PowerShell 中使用 `python -c "..."` 拼接含复杂双引号或 JSON 的长代码**：
   - PowerShell 的 Quote Stripping 会导致引号剥离破损，报 `SyntaxError: unterminated string literal`。
   - **铁律**: 一律通过 PowerShell `@' ... '@` 原样单引号字符串落盘到 `tmp/xxx.py`，再使用 `uv run` 执行！
2. ❌ **严禁调用系统 `pip` 或裸 `python`**：
   - 本地无系统级 Python，依赖全部由 `src-tauri/python/pyproject.toml` 约束。
   - **铁律**: 执行任何脚本统一使用：`uv run --project "C:\dev\Invar\src-tauri\python" python <脚本路径>`。
3. ❌ **严禁引入硬编码 Linux 绝对路径**：
   - 彻底废除 `/home/zhz/ST/`，统一使用 `Path(__file__).resolve().parents[...]` 或 `harness.config.InvarConfig` 动态寻路。
4. ❌ **严禁在命令行开头带有 `#` 注释**：
   - 防止 PowerShell 将整段复合执行流截断。
5. ❌ **严禁丢失数据契约的防御性容错**：
   - 任何读取 JSON 的函数（如 `EndpointExporter`），必须同时兼容 `dict` 外壳与 `list` 裸数组，严禁假设输入单一结构。
