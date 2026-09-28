# ==============================================================================
# 1. 完整重构 docs/ai/Invar实战.md
# ==============================================================================
shizhan_md_path = REPO_ROOT / "docs" / "ai" / "Invar实战.md"
shizhan_content = '''# 🛡️ Invar 工业级实战操作指南（精简收敛版 v9.0）

> **适用工程根目录**：`C:\\dev\\Invar`  
> **核心原则**：更换新靶场只需修改唯一的 `$target` 变量，其余步骤严格按顺序执行。  
> **双轨核心拓扑**：外部三工具前置采集 ➔ AST 契约提取 ➔ 0.6B 神经反射(System-1) ➔ 双轨融合 ➔ System-2 受控动态实证 ➔ 黄金证据链导出。

---

## 0. 全局拓扑与数据流动图

```text
目标 Scope ($target)
   ↓ [Phase 1: subfinder 被动发现]
subdomains.txt
   ↓ [Phase 2: httpx 存活测绘]
live_hosts.txt + httpx.jsonl (HTTP 边缘画像底账)
   ↓ [Phase 3: katana 深度爬取 + python/scripts/download_javascript.py 快速存证]
tmp/raw_js (前端代码全量物理落地)
   ↓ [Phase 4: python/scripts/scan_pipeline.py]
tmp/${target}_endpoints_report.json (静态 AST API 契约)
   ↓ [Phase 5: python/scripts/predict_triage_onnx.py (System-1 神经推演)]
tmp/${target}_predictions.jsonl
   ↓ [Phase 6: python/scripts/triage_dual_track_comparator.py]
artifacts/reports/triage_pools_v2.json (规则 ∪ 神经高危靶标池)
   ↓ [Phase 7: python/scripts/assemble_triage_tasks.py]
artifacts/reports/targeted_research_tasks.json (P0~P3 任务装配)
   ↓ [Phase 8: python/scripts/run_targeted_audit.py (System-2 自适应沙箱)]
artifacts/reports/targeted_audit_production/ (SARIF + OpenVEX + 战报)
```

---

## 阶段 0：换新靶场唯一入口（初始化）

```powershell
Set-Location -Path "C:\\dev\\Invar"

# 【全局唯一目标配置】更换测试资产只需修改此变量
$target = "ikuai8.com"

# 自动创建目标目录与工作空间
$targetDir = "data\\targets\\$target"
New-Item -ItemType Directory -Force -Path $targetDir, "tmp", "artifacts\\reports" | Out-Null

# 建立法定授权白名单
@"
$target
"@ | Set-Content -Path "$targetDir\\scope.txt" -Encoding UTF8
```

---

## 阶段 1：外部工具多源子域名全量被动发现 (Subfinder)

```powershell
$subdomainsTxt = "$targetDir\\subdomains.txt"
subfinder -d $target -silent -o $subdomainsTxt
```
* **核心产物**：`data/targets/<target>/subdomains.txt`（纯净子域名清单）

---

## 阶段 2：外部工具 Web 存活探测与边缘画像 (HTTPX)

```powershell
$httpxJsonl = "$targetDir\\httpx.jsonl"
$liveHostsTxt = "$targetDir\\live_hosts.txt"

# 存活探测与指纹收集
httpx -l $subdomainsTxt -silent -sc -title -tech-detect -web-server -json -o $httpxJsonl

# 提取纯净存活 URL 清单供爬虫消费
Get-Content $httpxJsonl | ForEach-Object {
    $row = $_ | ConvertFrom-Json
    if ($row.url) { $row.url }
} | Sort-Object -Unique | Set-Content -Path $liveHostsTxt -Encoding UTF8
```
* **核心产物**：
  * `data/targets/<target>/httpx.jsonl`（技术栈与网络指纹底账）
  * `data/targets/<target>/live_hosts.txt`（纯净存活主机与端口）

---

## 阶段 3：Katana 静态资产深度爬取与前端 JS 快速物理下载

```powershell
$katanaOutput = "data\\targets\\$target\\katana.jsonl"
$urlsJsonl = "data\\targets\\$target\\urls.jsonl"
$jsJsonl = "data\\targets\\$target\\javascript.jsonl"
$rawJsDir = "tmp\\raw_js"
$jsManifest = "tmp\\${target}_javascript_manifest.jsonl"

# 3.1 Katana 深度爬取
katana -list $liveHostsTxt -jc -d 2 -c 5 -silent -j -or -ob -o $katanaOutput

# 3.2 归一化解构业务路由与 JS 资产表
uv run --project python python python/scripts/normalize_katana.py `
    --input $katanaOutput `
    --urls-output $urlsJsonl `
    --javascript-output $jsJsonl `
    --target $target

# 3.3 批量物理下载前端 JS 代码并做 SHA256 存证
uv run --project python python python/scripts/download_javascript.py `
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
$endpointReport = "tmp\\${target}_endpoints_report.json"

uv run --project python python python/scripts/scan_pipeline.py `
    "tmp\\raw_js" `
    -o $endpointReport
```
* **核心产物**：`tmp/<target>_endpoints_report.json`（剥离了路由、参数与破坏性标记的 API 契约）

---

## 阶段 5：System-1 神经认知反射初筛 (0.6B ONNX 原生推演)

```powershell
$predictionsOut = "tmp\\${target}_predictions.jsonl"

uv run --project python python python/scripts/predict_triage_onnx.py `
    --report $endpointReport `
    --raw-js "tmp\\raw_js" `
    --model-dir "models/invar-intent-0.6b-v1" `
    --output $predictionsOut
```
* **核心产物**：`tmp/<target>_predictions.jsonl`（全部端点的 Impact / Sensitivity 软标签）

---

## 阶段 6：终审双轨比对器（规则 ∪ 神经并集融合，零漏报）

```powershell
$outputDir = "artifacts\\reports"

uv run --project python python python/scripts/triage_dual_track_comparator.py `
    --report $endpointReport `
    --raw-js "tmp\\raw_js" `
    --neural-jsonl $predictionsOut `
    --http-surface "$targetDir\\httpx.jsonl" `
    --output-dir $outputDir
```
* **核心产物**：
  * `artifacts/reports/triage_pools_v2.json`（Pool A 规则保底池与 Pool B 神经破盲池）
  * `artifacts/reports/triage_dual_track_v2.jsonl`（全维度融合审计底账）

---

## 阶段 7：System-2 靶心任务装配与优先级调度 (Dispatch)

```powershell
$tasksFile = "artifacts\\reports\\targeted_research_tasks.json"

uv run --project python python python/scripts/assemble_triage_tasks.py `
    --pools "artifacts/reports/triage_pools_v2.json" `
    --dual-track "artifacts/reports/triage_dual_track_v2.jsonl" `
    --output $tasksFile `
    --target-pools pool_a_rule_must_keep pool_b_discrepancy
```
* **核心产物**：`artifacts/reports/targeted_research_tasks.json`（已分配 P0/P1/P2/P3 优先级）

---

## 阶段 8：System-2 自适应沙箱受控动态实证

```powershell
Set-Location -Path "C:\\dev\\Invar"

# 本地 LLM 反思服务配置
$env:INVAR_LLM_BASE_URL = "http://127.0.0.1:8080/v1"
$env:INVAR_LLM_TIMEOUT = "120"
$env:INVAR_LLM_MODEL = "Qwen3.8-27B-Uncensored"

uv run --project python python python/scripts/run_targeted_audit.py `
    --tasks "artifacts\\reports\\targeted_research_tasks.json" `
    --report-input $endpointReport `
    --output-dir "artifacts\\reports\\targeted_audit_production" `
    --priority ALL `
    --enable-llm `
    --timeout 10
```

* **最终权威交付物清单（位于 `artifacts/reports/targeted_audit_production/`）**：
  1. `execution.jsonl`：[微观事实] 全任务发包、时延、分类与 CoT 反思事件流；
  2. `findings.json`：[漏洞确权] 经独立第三方复核实锤的权威漏洞记录；
  3. `openvex.json`：[合规凭证] 100% 符合 OpenSSF OpenVEX v0.2.0 国际规范；
  4. `sarif.json`：[缺陷交换] 100% 符合 OASIS SARIF 2.1.0 规范；
  5. `REPORT.md`：[高管战报] 资产血统、加权覆盖率、发现总览；
  6. `FINDINGS-DETAIL.md`：[实锤细节] 包含攻击链路代码调用链、发包 Proof 的深度战报；
  7. `NEEDS-VALIDATION.md`：[攻坚清单] 存疑待人工介入清单；
  8. `coverage-summary.md`：[覆盖账本] 路径审查全景责任矩阵。
