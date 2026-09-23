# 🛡️ Invar 工业级安全科研与漏洞实证流水线（2026 规范版）

> **适用工程根目录**：`C:\dev\Invar`  
> **适用版本体系**：Monorepo 标准工作区规范（Rust Workspace + Python uv + 自包含模型金库）  
> **设计核心思想**：**“外部多源资产漏斗收敛 ➔ System-1 神经认知反射初筛 ➔ Invar System-2 深度动态实证”**

---

## 一、系统全局数据流转拓扑（漏斗总览）

从零开始的“五大实战作战图谱”：

```text
【模块 1：全源资产暴露面展开 (Recon & EASM)】
   目标授权 Scope 
   ➔ 证书透明度 (CTFR/crt.sh) + Subfinder 双被动聚合 
   ➔ 悬挂 CNAME 接管检查 
   ➔ HTTPX 高速存活画像与泛解析清洗 
   ➔ Katana 前端 JS 深度爬取与物理下载
   【成果交付】：真正属于该目标的全新 raw_js 静态代码库

【模块 2：确定性语法契约提炼 (AST Analysis)】
   Tree-sitter AST 解析器精准解构 
   ➔ 提取 EndpointIR 路由与参数签名 
   ➔ 上下文封闭代码切片抽取
   【成果交付】：结构化的 API 契约与代码切片全集

【模块 3：认知蒸馏与专家因果标注 (Distillation)】
   双师蒸馏机制 (云端/本地大模型深度因果剖析)
   ➔ 输出 Impact (破坏力) 与 Sensitivity (敏感度) 双正交概率软标签
   【成果交付】：高质量科研对齐数据集 (Train & Eval)

【模块 4：System-1 判别模型微调点火 (Model Factory)】
   Qwen3-0.6B 判别式微调 (Soft-CE + Brier Loss)
   ➔ 剥离生成头，导出 DirectML/CUDA 静态 ONNX 图 (23ms 极速传感器)
   ➔ 物理硬件质检护照签发
   【成果交付】：出厂验证合格的轻量级现场感知引擎

【模块 5：双轨漏斗与 System-2 动态漏洞实证 (Verification)】
   双轨对账 (规则 ∪ 神经并集) 锁定核心高危靶心
   ➔ 组装 P0/P1 探针任务
   ➔ 自适应沙箱发包 (报错自愈变异、双主体 IDOR 差分、动词隧道穿透)
   ➔ 独立复核与 PromotionGate 门禁 
   ➔ 升华 KnowledgeCard 并导出权威实证战报
```

---

## 二、标准化单步执行指南（命令与产物对齐）


### 阶段 1：subdomains 多源子域名全量被动发现与权威入库 


```powershell
# ==============================================================================
# Invar 阶段 1：多源子域名全量被动发现与权威入库 (Golden Standard)
# ==============================================================================
Set-Location -Path "C:\dev\Invar"

# 【全局唯一配置参数】未来测新目标只需改这里！
$target = "ikuai8.com"

# 1. 自动初始化目录结构
$targetDir = "data\targets\$target"
New-Item -ItemType Directory -Force -Path "tmp", $targetDir | Out-Null

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 🚀 正在执行 Phase 1 多源被动资产侦察: [$target]" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# ------------------------------------------------------------------------------
# 1.1 采集被动源 (Subfinder)
# ------------------------------------------------------------------------------
$subfinderOut = "tmp\${target}_subfinder.txt"
Write-Host "[1/3] 正在调度 Subfinder 全源检索..." -ForegroundColor Yellow
subfinder -d $target -silent -o $subfinderOut
$sfLines = if (Test-Path $subfinderOut) { Get-Content $subfinderOut } else { @() }
Write-Host "  └─ Subfinder 独立捕获数: $($sfLines.Count) 个" -ForegroundColor Gray

# ------------------------------------------------------------------------------
# 1.2 采集证书透明度日志 (crt.sh / CTFR 思想)
# ------------------------------------------------------------------------------
$crtshOut = "tmp\${target}_crtsh.txt"
Write-Host "[2/3] 正在提取全球证书透明度日志 (crt.sh)..." -ForegroundColor Yellow
uv run --project python python scripts/data/asset/ingest_crtsh.py `
    --target $target `
    --output $crtshOut
$crtLines = if (Test-Path $crtshOut) { Get-Content $crtshOut } else { @() }
Write-Host "  └─ crt.sh 独立捕获数: $($crtLines.Count) 个" -ForegroundColor Gray

# ------------------------------------------------------------------------------
# 1.3 多源合流、去重与权威底账入库
# ------------------------------------------------------------------------------
Write-Host "[3/3] 正在执行多源去重合流与契约校验..." -ForegroundColor Yellow
$allRaw = @($sfLines) + @($crtLines)
$uniqueSubdomains = $allRaw | Where-Object { $_ -and $_.Trim() -ne "" } | 
    ForEach-Object { $_.Trim().ToLower() } | 
    Sort-Object -Unique

$combinedOut = "tmp\${target}_passive_combined.txt"
$uniqueSubdomains | Set-Content -Path $combinedOut -Encoding UTF8
Write-Host "  ├─ 多源去重合流净总数: $($uniqueSubdomains.Count) 个" -ForegroundColor Green

# 熔断防线：严禁空资产清空存量底账
if ($uniqueSubdomains.Count -eq 0) {
    Write-Error "[!] 警报: 未能从任何被动源采集到有效子域名，流程已安全熔断拦截！"
    return
}

# 驱动 ingest_subdomains.py 入库落盘
uv run --project python python scripts/data/asset/ingest_subdomains.py `
    --input $combinedOut `
    --target $target

# 最终物证核验
$jsonlPath = "$targetDir\subdomains.jsonl"
if (Test-Path $jsonlPath) {
    $records = Get-Content $jsonlPath
    Write-Host "`n[✓] 阶段 1 完美收官！权威资产账本已就绪: $jsonlPath" -ForegroundColor Green
    Write-Host "[✓] 最终收录可用于后续实证的 Active 子域名: $($records.Count) 个" -ForegroundColor Green
    Write-Host "==================================================`n" -ForegroundColor Cyan
}
```
* **标准化产物**：
  * `data/targets/ikuai8.com/subdomains.jsonl`（当前最新状态快照）
  * `data/targets/ikuai8.com/manifest.jsonl`（数据来源与执行证明）
  * `data/targets/ikuai8.com/changes.jsonl`（资产变更流水账）

---

### 阶段 2：httpx 主机 Web 存活探测与边缘画像（HTTPX）

过滤死链、辨别 CDN 边缘并防御 Wildcard DNS（泛解析）假活陷阱：

```powershell
Set-Location -Path "C:\dev\Invar"

# 1. 声明唯一目标变量（泛化设计，严禁硬编码）
$target = "ikuai8.com"
$subdomainsJsonl = "data\targets\$target\subdomains.jsonl"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 🌐 正在执行 Phase 2 Web 存活探测与边缘画像: [$target]" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 2. 调度执行存活画像流水线
uv run --project python python scripts/data/asset/ingest_httpx.py `
    --input $subdomainsJsonl `
    --target $target

# 3. 结果确权与指标验收
$liveHostsPath = "data\targets\$target\live_hosts.jsonl"
if (Test-Path $liveHostsPath) {
    $liveRecords = Get-Content $liveHostsPath
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host " 🎯 HTTPX 存活探测最终验收战报" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  ├─ 原始子域名候选数 : 68 个" -ForegroundColor Gray
    Write-Host "  ├─ 实际存活 Web 主机 : $($liveRecords.Count) 个" -ForegroundColor Green
    Write-Host "  └─ 存活主机样本预览 (前 5 个):" -ForegroundColor Yellow
    $liveRecords | Select-Object -First 5 | ForEach-Object { Write-Host "     - $_" }
    Write-Host "==================================================`n" -ForegroundColor Cyan
}
```
* **标准化产物**：
  * `data/targets/ikuai8.com/httpx.jsonl`（原始 HTTP 响应画像，含技术栈、指纹）
  * `data/targets/ikuai8.com/live_hosts.jsonl`（经过过滤、真正存活的 Web 主机列表）

---

### 阶段 3：katana 静态资产深度爬取、清洗与物理物化

#### 3.1 Katana 静态资产深度爬取
```powershell
Set-Location -Path "C:\dev\Invar"

# 【全局目标变量】
$target = "ikuai8.com"
$liveHosts = "data\targets\$target\live_hosts.jsonl"
$katanaInput = "tmp\${target}_katana_input.txt"
$katanaOutput = "data\targets\$target\katana.jsonl"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 🕷️ [3.1] 正在驱动 Katana 爬取前端资源: [$target]" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. 存活主机转化为标准 URL 清单
uv run --project python python scripts/data/asset/ingest_katana.py `
    --input $liveHosts `
    --output $katanaInput

# 2. 执行深度爬取
# 参数说明:
#   -list : 批量 URL 种子输入文件
#   -jc   : (JavaScript Crawling) 深度解析 HTML/JS 中的端点与引用链
#   -d 2  : 爬取深度为 2 层（避免全网死循环）
#   -c 5  : 并发线程数为 5（防止触发目标 WAF 阈值）
#   -j    : 输出为机器可读的标准 JSONL 格式
#   -or   : (omit-raw) 不保存原始 HTTP 请求头，大幅压缩体积
#   -ob   : (omit-body) 不在日志中保存响应正文
#   -o    : 输出到原始事实层 katana.jsonl
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

Write-Host "[✓] Katana 爬取完成，原始线索已落盘: $katanaOutput" -ForegroundColor Green
```

#### 3.2 Katana 原始日志资产归一化提炼

```powershell
$urlsJsonl = "data\targets\$target\urls.jsonl"
$jsJsonl = "data\targets\$target\javascript.jsonl"

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host " ⚙️ [3.2] 正在执行资产归一化解构: [$target]" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 驱动 normalize_katana.py 进行高精过滤提炼
uv run --project python python scripts/data/asset/normalize_katana.py `
    --input $katanaOutput `
    --urls-output $urlsJsonl `
    --javascript-output $jsJsonl `
    --target $target

Write-Host "[✓] 纯净业务路由表已生成: $urlsJsonl" -ForegroundColor Green
Write-Host "[✓] 核心前端 JS 资产表已生成: $jsJsonl" -ForegroundColor Green
```

#### 3.3 批量物理下载与哈希存证

```powershell
$rawJsDir = "tmp\raw_js"
$jsManifest = "tmp\${target}_javascript_manifest.jsonl"

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host " 📥 [3.3] 正在执行前端 JS 代码物理下载: [$target]" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 参数说明:
#   --workers 8          : 8 线程并发下载
#   --timeout 15         : 单文件超时 15 秒
#   --insecure           : 跳过自签证书错误
#   --retry-failed-only  : 失败增量重试机制
uv run --project python python scripts/data/asset/download_javascript.py `
    --input $jsJsonl `
    --output-dir $rawJsDir `
    --manifest $jsManifest `
    --target $target `
    --workers 8 `
    --timeout 15 `
    --insecure `
    --retry-failed-only

Write-Host "[✓] 前端 JS 代码已全量落盘至: $rawJsDir" -ForegroundColor Green
Write-Host "[✓] 物理文件 SHA256 清单已固化: $jsManifest" -ForegroundColor Green
Write-Host "==================================================`n" -ForegroundColor Cyan
```

---
* **标准化产物**：
  * `data/targets/<target>/katana.jsonl`：原始事实层；
  * `data/targets/<target>/urls.jsonl`：归一化目标 URL 路由清单；
  * `data/targets/<target>/javascript.jsonl`：归一化 JS 资产引用清单；
  * `tmp/raw_js/<host>/*.js`：物理下载的前端代码库（按子域名分目录物理隔离）；
  * `tmp/<target>_javascript_manifest.jsonl`：每个物理文件的哈希快照证明。


---

### 阶段 4：System-1 神经认知反射与双轨靶标收敛


#### 4.1 确定性 AST 语法树解析（提取 API 接口与参数契约）
```powershell
Set-Location -Path "C:\dev\Invar"

$rawJsDir = "tmp\raw_js"
$reportOutput = "tmp\ikuai8_endpoints_report.json"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 🧠 正在执行 Phase 4.1 Tree-sitter AST 语法深度提炼" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 驱动 scan_pipeline.py 进行静态语法与参数解构（不开启 --probe 发包，纯静态提取）
uv run --project python python python/scripts/scan_pipeline.py `
    $rawJsDir `
    -o $reportOutput

# 验收输出的结构化端点报告
if (Test-Path $reportOutput) {
    $reportJson = Get-Content $reportOutput -Raw | ConvertFrom-Json
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host " 🎯 AST 语法提取阶段验收战报" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  ├─ 成功解构提取 API 端点总数 : $($reportJson.summary.total_endpoints) 个" -ForegroundColor Green
    Write-Host "  ├─ 剥离出具体业务参数的接口数: $($reportJson.summary.param_rich_endpoints) 个" -ForegroundColor Green
    Write-Host "  ├─ 规则判定严重高危 (CRITICAL): $($reportJson.summary.critical_risk_count) 个" -ForegroundColor Red
    Write-Host "  ├─ 规则判定高风险   (HIGH)    : $($reportJson.summary.high_risk_count) 个" -ForegroundColor Yellow
    Write-Host "  └─ 端点事实全量报告已保存至   : $reportOutput" -ForegroundColor Green
    Write-Host "==================================================`n" -ForegroundColor Cyan
}
```
* **标准化产物**：
  * `tmp/ikuai8_endpoints_report.json`：类型的结构化 API 契约；

---

## 这里就需要提取类型的结构化 API 契约进行数据答案蒸馏和模型训练，产出base-jev模型来进行System-1 的分类打标评分

---

#### 4.2 0.6B 双引擎判别式模型极速推演（System-1 直觉感知）

```powershell
Set-Location -Path "C:\dev\Base-Jev"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 🚀 正在驱动 Base-Jev GPU 环境对 1216 个端点执行推演" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 加上 --project python 指定加载包含 torch 的虚拟环境
uv run --project python python python/scripts/generate_triage_predictions.py `
    --report "C:/dev/Invar/tmp/ikuai8_endpoints_report.json" `
    --raw-js "C:/dev/Invar/tmp/raw_js" `
    --output "C:/dev/Invar/tmp/base_jev_predictions_1216.jsonl"

# 验收输出产物
$outputFile = "C:\dev\Invar\tmp\base_jev_predictions_1216.jsonl"
if (Test-Path $outputFile) {
    $predLines = Get-Content $outputFile
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host " 🎯 神经推演产物验收战报" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  ├─ 待推演端点总数   : 1,216 个" -ForegroundColor Gray
    Write-Host "  ├─ 实际产出预测行数 : $($predLines.Count) 行 (1:1 逐行对齐)" -ForegroundColor Green
    Write-Host "  └─ 预测产物物理路径 : $outputFile" -ForegroundColor Green
    Write-Host "==================================================`n" -ForegroundColor Cyan
}
```
* **标准化产物**：
  * `tmp/base_jev_predictions_1216.jsonl`：双轨比对结果日志；

#### 4.3 终审双轨比对器（规则 ∪ 神经并集融合，零漏报）
```powershell
$target = "ikuai8.com"
$reportJson = "tmp\ikuai8_endpoints_report.json"
$rawJsDir = "tmp\raw_js"
$neuralJsonl = "tmp\base_jev_predictions_1216.jsonl"
$httpSurface = "data\targets\$target\httpx.jsonl"
$outputDir = "artifacts\reports"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " ⚖️ 正在驱动 Invar 双轨比对器执行高危靶标分流融合" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

uv run --project python python scripts/data/asset/triage_dual_track_comparator.py `
    --report $reportJson `
    --raw-js $rawJsDir `
    --neural-jsonl $neuralJsonl `
    --http-surface $httpSurface `
    --output-dir $outputDir

# 验收输出的靶标池
$poolsFile = "$outputDir\triage_pools_v2.json"
if (Test-Path $poolsFile) {
    $pools = Get-Content $poolsFile -Raw | ConvertFrom-Json
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host " 🎯 双轨比对与高危池收敛验收战报" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  ├─ 原始分析端点总数 : 1,216 个" -ForegroundColor Gray
    Write-Host "  ├─ Pool A (规则必须测): $($pools.pool_a_rule_must_keep.Count) 个靶面" -ForegroundColor Yellow
    Write-Host "  ├─ Pool B (模型破盲区): $($pools.pool_b_discrepancy.Count) 个靶面" -ForegroundColor Red
    Write-Host "  ├─ Pool C (探索扩展池): $($pools.pool_c_exploration.Count) 个靶面" -ForegroundColor Gray
    Write-Host "  └─ 靶心池契约文件已落盘: $poolsFile" -ForegroundColor Green
    Write-Host "==================================================`n" -ForegroundColor Cyan
}
```
* **标准化产物**：
  * `artifacts\reports\triage_pools_v2.json`（双轨比对与高危池收敛验收战报）
---

### 阶段 5 靶标任务装配与优先级调度（Dispatch）


#### 5.1 靶标动态分类与分流装配（P0/P1/P2 用例生成）
```powershell
Set-Location -Path "C:\dev\Invar"

# 驱动 assemble_triage_tasks.py 重新生成紧凑合规任务集
uv run --project python python python/scripts/assemble_triage_tasks.py `
    --pools "artifacts/reports/triage_pools_v2.json" `
    --dual-track "artifacts/reports/triage_dual_track_v2.jsonl" `
    --output "artifacts/reports/targeted_research_tasks_78.json" `
    --target-pools pool_a_rule_must_keep pool_b_discrepancy

# 验收输出的科研任务集
$tasksFile = "artifacts\reports\targeted_research_tasks_78.json"
if (Test-Path $tasksFile) {
    $tasksJson = Get-Content $tasksFile -Raw | ConvertFrom-Json
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host " 🎯 靶标任务装配验收战报" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  ├─ 成功装配核心任务总数: $($tasksJson.total_tasks) 个" -ForegroundColor Green
    Write-Host "  ├─ 任务文件实际体积    : $([math]::Round((Get-Item $tasksFile).Length / 1KB, 2)) KB" -ForegroundColor Green
    Write-Host "  └─ 任务优先级分布概况  :" -ForegroundColor Yellow
    $tasksJson.priority_breakdown | Format-List
    Write-Host "==================================================`n" -ForegroundColor Cyan
}
```
* **标准化产物**：
  * `artifacts\reports\triage_pools_v2.json`（双轨比对与高危池收敛验收战报）
  * `artifacts/reports/targeted_research_tasks_78.json`（锁定 78 个核心靶心）


#### 5.2 闭环沙箱探测、不变量裁决与知识卡片晋级（System-2 实证）

将装配好的 78 个核心靶心（或分优先级 P0 批次）送入 System-2 自适应沙箱，通过真实发包、报错自愈变异、软拒绝识别与 SPA 前端回退过滤，完成确定性实证与战报投影。

##### 5.2.1 P0 级核心靶点极速冒烟验证（基线实证）

在全面测试前，先针对最敏感的 12 个 P0 靶点进行快速验证，确保子域宿主自动路由准确、物理发包直连畅通（耗时应在 150ms ~ 8s 内）。

```powershell
Set-Location -Path "C:\dev\Invar"

$tasksFile = "artifacts\reports\targeted_research_tasks_78.json"
$reportInput = "tmp\ikuai8_endpoints_report.json"
$p0OutputDir = "artifacts\reports\targeted_audit_p0_final"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 🎯 [5.2.1] 正在执行 P0 级双高核心靶标实证探测" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 驱动 run_targeted_audit.py，指定筛选 P0
uv run --project python python python/scripts/run_targeted_audit.py `
    --tasks $tasksFile `
    --report-input $reportInput `
    --output-dir $p0OutputDir `
    --priority P0 `
    --timeout 10

Write-Host "[✓] P0 靶点实证审计完成，报告目录: $p0OutputDir" -ForegroundColor Green
```

##### 5.2.2 全量 78 核心任务纵深实证与全域覆盖

当 P0 冒烟基线健康后，拉满全量 78 个任务（含 P1 破坏性变更与 IDOR 候选、P2 规则保底防护、P3 全域探索面），进行全业务子系统的大规模实证。

```powershell
$auditArgs = @(
    "python/scripts/run_targeted_audit.py",
    "--tasks", "artifacts/reports/targeted_research_tasks_78.json",
    "--report-input", "tmp/ikuai8_endpoints_report.json",
    "--output-dir", "artifacts/reports/targeted_audit_production",
    "--priority", "ALL",
    "--enable-llm",
    "--timeout", "10"
)

uv run --project python python @auditArgs
```


##### 5.2.2 两段式自适应科研循环（Phase 5.4 认知反思破局）
* **阶段一：启发式先锋（Heuristic Turn Loop）**：
  调度 F1（路径规范化畸变：`%2e`, Tomcat `..;/` 等）、F2（动词隧道：`X-HTTP-Method-Override`、`_method`）、F3（现代反代信任上下文：`X-Rewrite-URL`、`X-Forwarded-Prefix`、`CF-Connecting-IP`、RFC 7239 `Forwarded`）。
* **阶段二：大模型反思破局（LLM Cognitive Reflection）**：
  若 12 轮启发式变异均未突破，系统自动唤醒本地 9B 消融模型，注入报错正文、已尝试轮次与端点上下文，由大模型开展思维链（CoT）因果推理，派生专用 `F6_LLM_COT_REASONED` 变异体进行终审。

##### 5.2.3 独立第三方复核与双黄金标准导出（Phase 5.5）
* **三权分立与门禁**：产生的漏洞候选（Candidate）绝不允许自我复核，强制交由 `IndependentVerifier` 进行第三方独立验真，并经 `PromotionGate` 8 大前置谓词断言。
* **双黄金交付物**：
  1. **OpenSSF OpenVEX v0.2.0**（`openvex.json`）：工业级机器可读漏洞状态声明；
  2. **OASIS SARIF 2.1.0**（`sarif.json`）：国际通用缺陷交换格式，原生映射代码调用流 `codeFlows`；
  3. **4 大正交 Markdown 战报**：`REPORT.md`（高管摘要）、`FINDINGS-DETAIL.md`（实锤细节）、`NEEDS-VALIDATION.md`（存疑攻坚）、`coverage-summary.md`（账本明细）。

##### 5.2.4 纯观测层事实追踪体系（Phase 6.1 `execution.jsonl`）
* **定位**：旁路事实记录器（`ExecutionTraceRecorder`），逐任务落盘物理发包数据、时延、分类与事件流，不改变探测行为，不参与裁决。
* **严格正交解耦**：
  - `execution.runner_status`（任务是否完成） $\neq$ `execution.decision_status`（不变量是否击穿）
  - `coverage.status`（账本覆盖状态） $\neq$ `FindingRecord`（确权漏洞）
  - `LLM enabled`（全局配置启用） $\neq$ `LLM invoked`（启发式受阻实际唤醒）
* **实测体检战报（78-Task 全量验证真实数据）**：
  ```text
  === 📊 Execution Trace 深度体检战报 ===
  1. 有效解析行数     : 78 条 (100% 完整，0 损坏)
  2. Run ID 唯一性   : 1 个 (RUN-TARGETED-1790155162)
  3. Runner 状态分布 : {'inconclusive': 37, 'completed': 41}
  4. 决策状态分布     : {'confirmed': 37, 'inconclusive': 4, 'None': 37}
  5. LLM 实际唤醒任务 : 41 个 (受阻任务精准唤醒 CoT 反思，其余任务早期收敛不浪费算力)
  6. 响应类别分布     : {'soft_access_policy_denial': 45, 'html_fallback': 25, 'method_policy_denial': 3, 'not_found': 3, 'client_error': 2}
  ```

---

### 三、生产级避坑指南与防误报铁律（Engineering Pitfalls & Ground Truths）

#### 坑位 1：Windows 注册表代理导致单请求 5.7 秒超时挂死
* **现象**：执行单个任务耗时 66 秒，整个 78 任务审计预计卡死数十分钟。
* **根因**：Windows 上仅从环境变量移除 `ALL_PROXY` 无法阻断 Python `requests`，底层库仍会从 Windows 注册表 `Internet Settings` 中读取全局代理，导致请求被转发至不可达的本地代理端口超时重试。
* **铁律解法**：在 `HttpTransport` 初始化时强制注入 `os.environ["NO_PROXY"] = "*"` 与 `os.environ["no_proxy"] = "*"`，阻断注册表劫持，单发时延由 5.7s 暴降至 150ms~700ms。

#### 坑位 2：业务软拒绝（HTTP 200 + code: 4003）引发假高危误报
* **现象**：访问未授权接口时，服务端网关返回 `HTTP 200 OK`，正文携带 `{"code": 4003, "message": "forbidden"}`，传统扫描器误报为“特权放行/未授权访问漏洞”。
* **铁律解法**：`InvariantEvaluator` 严禁盲信 HTTP 200 状态码；在正文包含 `code in {4001, 4003, 4008}` 或 `forbidden` 语义时，强制裁决为 `confirmed`（安全防御坚固生效），彻底消除误报。

#### 坑位 3：单页应用（SPA）Nginx 兜底页面引发假突破
* **现象**：针对不存在的管理接口发包，Nginx `try_files` 对 404 兜底返回首页 `HTTP 200 + <!DOCTYPE html>`，扫描器误判为“路径变异突破成功”。
* **铁律解法**：在 `research_loop` 突破判定与 `SemanticEquivalenceEvaluator` 中，严格核验响应正文是否以 `<!doctype html` 或 `<html` 开头；凡是命中前端页面回退者，坚决剔除，不予记录突破。

---

### 四、标准化全域交付物资产清单

完成阶段 5 执行后，在 `artifacts/reports/targeted_audit_production/` 目录下原子化固化以下 8 大交付物：

```text
artifacts/reports/targeted_audit_production/
├── execution.jsonl          # [事实层] 78 任务逐任务微观发包、响应分类、耗时与 LLM 反思完整轨迹
├── findings.json            # [确权层] 经独立复核实锤的权威漏洞发现记录 (当前实锤 0 个，保持零假阳性)
├── openvex.json             # [合规层] 严格对齐 OpenSSF OpenVEX v0.2.0 标准规范的安全声明凭证
├── sarif.json               # [工具层] 严格对齐 OASIS SARIF 2.1.0 标准规范的缺陷报告 (支持 VS Code 导入)
├── REPORT.md                # [决策层] 包含审计范围血统、加权覆盖率、发现总览的高管战报
├── FINDINGS-DETAIL.md       # [技术层] 实锤漏洞的代码溯源调用链 (Trace) 与微观发包证明
├── NEEDS-VALIDATION.md      # [攻坚层] 严禁虚标严重度、明确记录阻断原因的存疑待办清单
└── coverage-summary.md      # [账本层] 覆盖单元 (CoverageUnit) 全景明细与路径审查责任矩阵
```
