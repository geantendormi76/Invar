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
$allOutputDir = "artifacts\reports\targeted_audit_all_78"

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host " 🚀 [5.2.2] 正在启动全量 78 靶向任务纵深实证审计" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# priority 设置为 ALL，全量穿透
uv run --project python python python/scripts/run_targeted_audit.py `
    --tasks $tasksFile `
    --report-input $reportInput `
    --output-dir $allOutputDir `
    --priority ALL `
    --timeout 10

# 验收输出的战报交付物
if (Test-Path "$allOutputDir\REPORT.md") {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host " 📊 靶向实证全量审计最终战报概况" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Get-Content "$allOutputDir\REPORT.md" | Select-String -Pattern "## 2. 覆盖度核心指标", "## 3. 漏洞发现总览", "实锤确认" -Context 0, 5
    Write-Host "`n[✓] 5 大权威交付物已全部原子化落盘至: $allOutputDir" -ForegroundColor Green
    Write-Host "==================================================`n" -ForegroundColor Cyan
}
```

##### 5.2.3 必须恪守的底层三大防御与避坑铁律（Ground Truth）

为了在其他新靶场复现时取得相同的高效、零误报战果，以下三大底层机制必须保持常驻：
1. **物理网络代理隔离（阻断 5.5s / 66s 幽灵挂死）**：
   `HttpTransport` 内部必须显式清理 `HTTP_PROXY` / `HTTPS_PROXY` 并设置 `NO_PROXY="*"`，严禁让请求走本地系统代理（如 Clash / v2ray 导致的握手重试超时），确保 API 物理往返在毫秒级（150ms ~ 700ms）。
2. **业务级软拒绝识别（消灭伪 200 业务报错误报）**：
   后端常用 HTTP 200 外壳承载 `{"code": 4003, "message": "forbidden"}`。`InvariantEvaluator` 与 `DenialClassifier` 必须能从响应体解析 40xx 业务码，将其判定为 `CONFIRMED`（安全底线已拦截），严禁因状态码为 200 而误判为未授权穿透。
3. **前端单页应用 SPA 兜底 HTML 过滤（消灭伪 200 页面回退误报）**：
   当 Nginx `try_files` 对不存在的 API 路由无条件回显 `index.html`（`<!DOCTYPE html...`）时，系统必须在不变量评估器中直接识别为“非真实后端 API 响应”，坚决禁止将其标记为 `VULNERABLE`。

---
* **标准化交付物（5 大权威事实战报）**：
  * `findings.json`：全量机器可读、包含根因指纹与物理发包证据的结构化数据（供下游 CI/CD 与工单系统消费）；
  * `REPORT.md`：面向安全决策层的战报总览（含执行上下文血统、客观加权覆盖率、漏洞裁决分布）；
  * `FINDINGS-DETAIL.md`：面向一线研发与审计专家的技术细节（包含调用链路跟踪、原始 HTTP 请求/响应快照、修复加固指导）；
  * `NEEDS-VALIDATION.md`：因缺少双主体凭证或前置条件不足而阻塞的攻坚清单（严禁标注假定严重度）；
  * `coverage-summary.md`：按子系统和攻击面展开的 48 个覆盖单元全景明细表。
```
