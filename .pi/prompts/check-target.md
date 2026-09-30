---
description: 探查靶标端点的物理代码切片、参数与假说元数据
argument-hint: "[endpoint_id]"
---
你现在是 Invar System-2 的研究规划智能体。请针对端点 `${1:-POST:/api/v3/delegate/grant}` 完成物理元数据探查。

### 任务目标
从任务清单（`artifacts/reports/targeted_research_tasks_78.json` 或 `targeted_research_tasks.json`）中提取该端点的真实切片事实，严禁凭空臆造。

### 执行步骤
1. **检查与准备探查脚本**：
   检查是否存在 `tmp/check_target_delegate_grant.py`。如果不存在，请编写并写入该脚本，逻辑要求：
   - 锚定项目根目录；
   - 搜索 `artifacts/reports/targeted_research_tasks_78.json`（若不存在则回退至 `artifacts/reports/targeted_research_tasks.json`）；
   - 检索 endpoint 匹配 `${1:-POST:/api/v3/delegate/grant}` 的任务项；
   - 打印该任务的 `priority`、`profile`、`hypothesis_id`、`extracted_params`、`source_file`、`source_line` 以及真实的 `code_slice`。

2. **执行探查**：
   使用 powershell 工具执行：
   ```powershell
   uv run --project python python tmp/check_target_delegate_grant.py
   ```

3. **输出汇报格式**：
   执行完成后，请用清晰的中文结构汇报以下物理事实：
   - **端点标识** (Endpoint ID) 与 **所在子系统** (Subsystem)
   - **分流优先级** (Priority) 与 **关联假说** (Hypothesis)
   - **AST 提取的业务参数列表** (Extracted Parameters)
   - **源码物理定位** (Source File & Line)
   - **真实代码切片内容** (Code Slice)
