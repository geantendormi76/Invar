# 🛡️ Invar 工业级实战操作指南（标准版）

> **适用工程根目录**：`C:\dev\Invar`  
> **核心原则**：更换新靶场只需修改唯一的 `$target` 变量，其余步骤严格按顺序执行。  
> **双轨核心拓扑**：资产展开 ➔ AST 契约提取 ➔ 0.6B 神经反射(System-1) ➔ 双轨融合 ➔ System-2 受控动态实证 ➔ 黄金证据链导出。

---

## 0. 全局拓扑与数据流动图

```text
目标 Scope ($target)
   ↓ [Phase 1: subfinder + crt.sh]
subdomains.jsonl
   ↓ [Phase 2: ingest_httpx.py]
live_hosts.jsonl + httpx.jsonl (HTTP 边缘画像底账)
   ↓ [Phase 3: katana + download_javascript.py]
tmp/raw_js (前端代码全量物理落地)
   ↓ [Phase 4: scan_pipeline.py]
tmp/${target}_endpoints_report.json (静态 AST API 契约)
   ↓ [Phase 5: predict_triage_onnx.py (System-1 神经推演)]
tmp/${target}_predictions.jsonl
   ↓ [Phase 6: triage_dual_track_comparator.py]
artifacts/reports/triage_pools_v2.json (规则 ∪ 神经高危靶标池)
   ↓ [Phase 7: assemble_triage_tasks.py]
artifacts/reports/targeted_research_tasks.json (P0~P3 任务装配)
   ↓ [Phase 8: run_targeted_audit.py (System-2 自适应沙箱)]
artifacts/reports/targeted_audit_production/ (SARIF + OpenVEX + 战报)
```

---

## 阶段 0：换新靶场唯一入口（初始化）

```powershell
Set-Location -Path "C:\dev\Invar"

# 【全局唯一目标配置】更换测试资产只需修改此变量
$target = "example.com"

# 自动创建目标目录与工作空间
$targetDir = "data\targets\$target"
New-Item -ItemType Directory -Force -Path $targetDir, "tmp", "artifacts\reports" | Out-Null

# 建立授权声明文件
@"
$target
"@ | Set-Content -Path "$targetDir\scope.txt" -Encoding UTF8
```

---

## 阶段 1：多源子域名全量被动发现与底账入库

```powershell
# 1. Subfinder 全源检索
$subfinderOut = "tmp\${target}_subfinder.txt"
subfinder -d $target -silent -o $subfinderOut

# 2. 提取全球证书透明度日志 (crt.sh)
$crtshOut = "tmp\${target}_crtsh.txt"
uv run --project python python scripts/data/asset/ingest_crtsh.py `
    --target $target `
    --output $crtshOut

# 3. 多源合流、去重与资产账本入库
$allRaw = @(
    if (Test-Path $subfinderOut) { Get-Content $subfinderOut }
    if (Test-Path $crtshOut)     { Get-Content $crtshOut }
)
$combinedOut = "tmp\${target}_passive_combined.txt"
$allRaw |
    Where-Object { $_ -and $_.Trim() -ne "" } |
    ForEach-Object { $_.Trim().ToLower().TrimEnd(".") } |
    Sort-Object -Unique |
    Set-Content -Path $combinedOut -Encoding UTF8

uv run --project python python scripts/data/asset/ingest_subdomains.py `
    --input $combinedOut `
    --target $target `
    --data-root "data\targets"
```
* **核心产物**：
  * `data/targets/<target>/subdomains.jsonl`

---

## 阶段 2：Web 存活探测与边缘画像（HTTPX）

```powershell
uv run --project python python scripts/data/asset/ingest_httpx.py `
    --input "data\targets\$target\subdomains.jsonl" `
    --target $target
```
* **核心产物**：
  * `data/targets/<target>/httpx.jsonl`（包含技术栈与网络指纹，供阶段 6 比对器使用）
  * `data/targets/<target>/live_hosts.jsonl`（纯净存活主机，供阶段 3 Katana 爬虫使用）

---

## 阶段 3：Katana 静态资产深度爬取与前端 JS 物理下载

```powershell
$katanaInput = "tmp\${target}_katana_input.txt"
$katanaOutput = "data\targets\$target\katana.jsonl"
$urlsJsonl = "data\targets\$target\urls.jsonl"
$jsJsonl = "data\targets\$target\javascript.jsonl"
$rawJsDir = "tmp\raw_js"
$jsManifest = "tmp\${target}_javascript_manifest.jsonl"

# 3.1 存活主机转化为标准 URL 清单
uv run --project python python scripts/data/asset/ingest_katana.py `
    --input "data\targets\$target\live_hosts.jsonl" `
    --output $katanaInput

# 3.2 执行深度爬取
katana `
    -list $katanaInput `
    -jc `
    -d 2 `
    -c 5 `
    -silent `
    -j `
    -or `
    -ob `
    -o $katanaOutput

# 3.3 归一化解构业务路由与 JS 资产表
uv run --project python python scripts/data/asset/normalize_katana.py `
    --input $katanaOutput `
    --urls-output $urlsJsonl `
    --javascript-output $jsJsonl `
    --target $target

# 3.4 批量物理下载前端 JS 代码并做 SHA256 存证
uv run --project python python scripts/data/asset/download_javascript.py `
    --input $jsJsonl `
    --output-dir $rawJsDir `
    --manifest $jsManifest `
    --target $target `
    --workers 8 `
    --timeout 15 `
    --insecure `
    --retry-failed-only
```
* **核心产物**：
  * `tmp/raw_js/<host>/*.js`（目标全离子前端代码库）
  * `tmp/<target>_javascript_manifest.jsonl`（物理文件哈希指纹）

---

## 阶段 4：Tree-sitter AST 静态接口与契约提炼

```powershell
$endpointReport = "tmp\${target}_endpoints_report.json"

uv run --project python python python/scripts/scan_pipeline.py `
    "tmp\raw_js" `
    -o $endpointReport
```
* **核心产物**：
  * `tmp/<target>_endpoints_report.json`（剥离了路由、参数与破坏性标记的 API 契约）

---

## 阶段 5：System-1 神经认知反射初筛 (0.6B ONNX 原生推演)

> 本步骤使用 Invar 仓内集成的纯 DirectML/ONNX 引擎，**零 PyTorch 依赖，无需切换工作区**。

```powershell
$predictionsOut = "tmp\${target}_predictions.jsonl"

uv run --project python python scripts/data/pipeline/predict_triage_onnx.py `
    --report "tmp\${target}_endpoints_report.json" `
    --raw-js "tmp\raw_js" `
    --model-dir "models/invar-intent-0.6b-v1" `
    --output $predictionsOut
```
* **核心产物**：
  * `tmp/<target>_predictions.jsonl`（全部端点的 Impact / Sensitivity 概率软标签）

---

## 阶段 6：终审双轨比对器（规则 ∪ 神经并集融合，零漏报）

```powershell
$outputDir = "artifacts\reports"

uv run --project python python scripts/data/asset/triage_dual_track_comparator.py `
    --report "tmp\${target}_endpoints_report.json" `
    --raw-js "tmp\raw_js" `
    --neural-jsonl "tmp\${target}_predictions.jsonl" `
    --http-surface "data\targets\$target\httpx.jsonl" `
    --output-dir $outputDir
```
* **核心产物**：
  * `artifacts/reports/triage_pools_v2.json`（收敛出的 Pool A 规则高危池与 Pool B 神经破盲池）
  * `artifacts/reports/triage_dual_track_v2.jsonl`（全维度融合审计数据底账）

---

## 阶段 7：System-2 靶心任务装配与优先级调度 (Dispatch)

```powershell
$tasksFile = "artifacts\reports\targeted_research_tasks.json"

uv run --project python python python/scripts/assemble_triage_tasks.py `
    --pools "artifacts/reports/triage_pools_v2.json" `
    --dual-track "artifacts/reports/triage_dual_track_v2.jsonl" `
    --output $tasksFile `
    --target-pools pool_a_rule_must_keep pool_b_discrepancy
```
* **核心产物**：
  * `artifacts/reports/targeted_research_tasks.json`（分派了 P0/P1/P2/P3 优先级的可执行审计任务包）

---

## 阶段 8：System-2 自适应沙箱受控动态实证

### 8.1 方案 A：P0 核心靶点极速冒烟实证（耗时 < 1 分钟）
```powershell
uv run --project python python python/scripts/run_targeted_audit.py `
    --tasks "artifacts\reports\targeted_research_tasks.json" `
    --report-input "tmp\${target}_endpoints_report.json" `
    --output-dir "artifacts\reports\targeted_audit_p0" `
    --priority P0 `
    --timeout 10
```

### 8.2 方案 B：全量任务纵深实证（启用本地大模型反思 + 导出双黄金报告）
```powershell
Set-Location -Path "C:\dev\Invar"

# LLM 超时独立于下方目标 HTTP 的 --timeout。
# Provider 会将结构化动作限制为 256 token，并逐请求关闭 thinking，
# 避免 Qwen-27B 的隐藏推理耗尽输出预算。
$env:INVAR_LLM_BASE_URL = "http://127.0.0.1:8080/v1"
$env:INVAR_LLM_TIMEOUT = "120"
$env:INVAR_LLM_MODEL = "Qwen3.8-27B-Uncensored"

uv run --project python python python/scripts/run_targeted_audit.py `
    --tasks "artifacts\reports\targeted_research_tasks.json" `
    --report-input "tmp\ikuai8.com_endpoints_report.json" `
    --output-dir "artifacts\reports\targeted_audit_production" `
    --priority ALL `
    --enable-llm `
    --timeout 10
```

> **断点续跑**：上述命令默认启用，无需增加参数。每完成一项，程序先将完整执行记录
> `fsync` 到 `execution.jsonl`，再原子更新 `audit_checkpoint.json`。中断后重新执行
> 同一条命令，会恢复原 `run_id`、覆盖账本与已确权发现，并自动跳过已落盘任务。
> 任务集、静态报告、优先级、目标超时或 LLM 关键参数变化时，程序会拒绝错误续跑。
> 只有明确希望放弃原进度时才使用 `--restart`。

> **并发与失败门禁**：27B 服务保持 `--parallel 1`，阶段 8 按任务串行调用。
> 若 LLM 超时、输出截断、正文为空或动作 Schema 非法，该任务会记录
> `llm_reasoning_failed`。LLM 失败或任务仍为 `inconclusive` 时，覆盖单元进入
> `BLOCKED`，整次运行不得推进到 `REPORT_READY/COMPLETED`。不得把未完成验证
> 外推为“防御确认”。

* **最终 8 大权威交付物清单（位于 `artifacts/reports/targeted_audit_production/`）**：
  1. `execution.jsonl`：[微观事实] 78 任务发包、时延、分类与 CoT 反思事件流；
  2. `findings.json`：[漏洞确权] 经独立第三方复核实锤的权威漏洞记录；
  3. `openvex.json`：[合规凭证] 100% 符合 OpenSSF OpenVEX v0.2.0 国际规范；
  4. `sarif.json`：[缺陷交换] 100% 符合 OASIS SARIF 2.1.0 规范（原生映射 Trace 调用流）；
  5. `REPORT.md`：[高管战报] 资产血统、加权覆盖率、发现总览；
  6. `FINDINGS-DETAIL.md`：[实锤细节] 包含攻击链路代码调用链、发包 Proof 的深度战报；
  7. `NEEDS-VALIDATION.md`：[攻坚清单] 存疑待人工介入清单；
  8. `coverage-summary.md`：[覆盖账本] 路径审查全景责任矩阵。

---

## 阶段 9：对接「补天平台」快速提交流水线

若在 `FINDINGS-DETAIL.md` 中发现确权漏洞，按以下规范直接提取物证填写补天表单：

| 补天表单字段 | 提取来源 / 填报要求 |
|---|---|
| **厂商名称** | 标准工商全称（如：`全讯汇聚网络科技(北京)有限公司`） |
| **域名或IP** | 填写主域名：`$target`（严禁带协议和长路径） |
| **漏洞标题** | `[厂商全称/系统名] + [FINDINGS-DETAIL.md 中的漏洞标题]` |
| **漏洞URL** | 对应接口的完整请求 URL（如：`https://cloud.ikuai8.com/api/v1/...`） |
| **漏洞权重** | 爱站网查询主域权重：百度/移动权重 $\ge 1$ 选 `权重>=1`，未收录或为0必须果断选 `权重=0` |
| **简要描述** | **红线禁忌**：严禁写具体 URL 与参数！只写危害概述（如：“某接口鉴权缺失导致敏感凭证暴露”） |
| **详细细节** | 直接复制 `FINDINGS-DETAIL.md` 中的步骤、请求包、响应包及代码调用链，并附带浏览器地址栏截图 |
| **修复方案** | 直接复制 `FINDINGS-DETAIL.md` 底部对应的 `治理实操` 建议 |

---

## 终极排错速查表

```powershell
# 1. 检查 Python 核心测试
uv run --project python pytest

# 2. 检查 Rust 调度核心测试
cargo test --workspace

# 3. 校验各脚本参数帮助
uv run --project python python scripts/data/asset/ingest_httpx.py --help
uv run --project python python scripts/data/asset/triage_dual_track_comparator.py --help
uv run --project python python python/scripts/run_targeted_audit.py --help
```
