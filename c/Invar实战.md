
# 一、从现在开始，Invar 统一采用这一条标准流水线

标准本身已经规定，Invar 接管前属于“资产采集层”，由：

```text
Subfinder
→ HTTPX
→ Katana
→ JS / URL / Host
→ 本地资产归档
```

负责。

因此以后一个目标，固定执行下面这条链：

```text
┌──────────────────────────────────────────────┐
│              Clean Research Run              │
└──────────────────────────────────────────────┘

                 授权 Scope
                     │
                     ▼
                Asset Discovery
                     │
                     ▼
                    raw_js
                     │
                     ▼
                    AST
                     │
                     ▼
                EndpointIR
                     │
                     ▼
             EndpointRegistry
                     │
                     ▼
                ResearchRun
                     │
                     ▼
              CoverageLedger
                     │
                     ▼
              ResearchTask
                     │
                     ▼
          Hunter / Research Wave
                     │
                     ▼
               ResearchCase
                     │
                     ▼
        Adaptive Sandbox / Evidence
                     │
                     ▼
          Invariant Evaluation
                     │
                     ▼
                 Candidate
                     │
                     ▼
           CandidateFingerprint
                     │
                     ▼
              FindingRecord
                     │
                     ▼
        Independent Verification
                     │
                     ▼
              Promotion Gate
                     │
                     ▼
              KnowledgeCard
                     │
                     ▼
             ReportProjector
```

这与我文档中正式定义的研究漏斗一致。

---

# 二、以后独立复现时，只需要执行这一套命令

我们这次已经验证过的命令整理成**正式执行顺序**。

## 阶段 0：授权范围

每个新目标首先建立：

```text
scope.txt
```

项目标准明确要求主动探测必须受授权根域、授权子域、路径、请求类型、时间和禁止项约束，而且发现资产仍然只是“候选资产”，并不会自动获得测试授权。

---

## 阶段 1：Subfinder

```powershell
subfinder -d "127.0.0.1.com" -silent -o "C:\dev\Invar\tmp\127.0.0.1_subdomains.txt"
```

这是**候选资产发现**。

不是 Web 存活确认。你的标准也是这样定义的。

---

## 阶段 2：Subdomain 归一化

```powershell
uv run python .\scripts\asset\ingest_subdomains.py `
    --input "C:\dev\Invar\tmp\127.0.0.1_subdomains.txt" `
    --target "127.0.0.1.com"
```

产物：

```text
data\targets\127.0.0.1.com\subdomains.jsonl
```

这一层负责：

```text
清洗
规范化
去重
目标边界
持久化
```

---

## 阶段 3：HTTPX

```powershell
uv run python .\scripts\asset\ingest_httpx.py `
    --input "C:\dev\Invar\data\targets\127.0.0.1.com\subdomains.jsonl" `
    --target "127.0.0.1.com"
```

产物：

```text
data\targets\127.0.0.1.com\httpx.jsonl
data\targets\127.0.0.1.com\live_hosts.jsonl
```

项目标准明确规定 HTTPX 的职责是确认 Web 存活和建立基础画像，然后只有“在线 + 授权范围 + 可研究 Web 服务”的资产才能进入 Katana。

---

## 阶段 4：构造 Katana 输入

这个步骤现在已经有正式程序：

```text
scripts\asset\ingest_katana.py
```

执行：

```powershell
uv run .\scripts\asset\ingest_katana.py `
    --input ".\data\targets\127.0.0.1.com\live_hosts.jsonl" `
    --output ".\tmp\127.0.0.1_katana_input.txt"
```

得到：

```text
tmp\127.0.0.1_katana_input.txt
```

内容就是：

```text
https://host1.127.0.0.1.com
https://host2.127.0.0.1.com
...
```

这一步以后不再需要人工生成。

项目的标准明确要求 Katana 从 HTTPX 存活资产进行批量采集，并面向：

```text
URL
API
JS
JS Chunk
前端资源
```

进行深度采集。

所以正式执行应该固定成为：

```powershell
katana `
    -list ".\tmp\127.0.0.1_katana_input.txt" `
    -jc `
    -d 2 `
    -c 5 `
    -silent `
    -j `
    -or `
    -ob `
    -o ".\data\targets\127.0.0.1.com\katana.jsonl"
```

这里的含义固定下来：

```text
-list   批量 Host 输入
-jc     JavaScript crawling
-d 2    正式研究深度
-c 5    并发控制
-j      JSONL
-or     不保存原始请求/响应
-ob     不保存响应正文
```

## 阶段 4：Katana 原始结果必须保留

正式产物：

```text
katana.jsonl
```

它是：

> Katana 原始事实层。

不能把它直接当成资产库。

因为其中同时存在：

```text
成功 URL
错误记录
max depth reached
timeout
source
tag
attribute
response
```

所以我们现在做的：

```text
katana.jsonl
       ↓
normalize_katana.py
```

是正确的架构方向。

---

# 三、URL / JavaScript 资产归一化固定为正式步骤

正式执行：

```powershell
uv run .\scripts\asset\normalize_katana.py `
    --input ".\data\targets\127.0.0.1.com\katana.jsonl" `
    --urls-output ".\data\targets\127.0.0.1.com\urls.jsonl" `
    --javascript-output ".\data\targets\127.0.0.1.com\javascript.jsonl" `
    --target "127.0.0.1.com"
```

这一步的职责是：

```text
Katana 原始事实
        ↓
资产归一化
        ↓
URL Asset
JavaScript Asset
```

这与标准要求的“资产归一化”层是吻合的。


```powershell
# 做一次轻量的结构确认，直接看两个正式输出文件的前 3 行
Get-Content .\data\targets\127.0.0.1.com\urls.jsonl -TotalCount 3
Get-Content .\data\targets\127.0.0.1.com\javascript.jsonl -TotalCount 3
```

---

# 四、JavaScript 批量下载

```powershell
uv run `
    --project "C:\dev\Invar\src-tauri\python" `
    --python 3.11 `
    python "C:\dev\Invar\scripts\asset\download_javascript.py" `
    --input "C:\dev\Invar\data\targets\127.0.0.1.com\javascript.jsonl" `
    --output-dir "C:\dev\Invar\tmp\raw_js" `
    --manifest "C:\dev\Invar\tmp\127.0.0.1_javascript_manifest.jsonl" `
    --target "127.0.0.1.com" `
    --workers 8 `
    --timeout 15 `
    --insecure `
    --retry-failed-only
```

当前真实结果：

```text
输入 JS              209
成功下载              209
HTTP 错误               0
非 JS                   0
外部跳转阻断             0
TLS 错误                 0
网络错误                 0
其他错误                 0
```


---

# 五、然后才进入 Invar

```powershell
uv run `
    --project "C:\dev\Invar\src-tauri\python" `
    --python 3.11 `
    python "C:\dev\Invar\scripts\pipeline\scan_pipeline.py" `
    "C:\dev\Invar\tmp\raw_js" `
    -o "C:\dev\Invar\tmp\ikuai8_endpoints_report.json"
```


```powershell
uv run python "C:\dev\Invar\scripts\pipeline\generate_triage_predictions.py triage_dual_track_comparator.py"
```

```text
【资产收集阶段】
    Subfinder ➔ HTTPX ➔ Katana ➔ download_javascript.py
                         │
                         ▼
                     tmp/raw_js (下载了 209 个目标 JS 文件)
                         │
                         ▼
        scan_pipeline.py (AST 语法分析器)
                         │
                         ▼
            ikuai8_endpoints_report.json (从 JS 提取出 1221 个 API 接口)
═════════════════════════╪═════════════════════════════════════════════
                         │  🚨 这里！你的 0.6B 模型正式上战场！
                         ▼
        【步骤 A：0.6B 模型光速推演】
        generate_triage_predictions.py
        (加载你的 system_one_unified.onnx，以 23ms 单端点的速度，
         在 2~3 分钟内把这 1221 个接口的代码切片全读一遍！)
                         │
                         ▼
            base_jev_predictions_1221.jsonl (每个接口被打上 Impact/Sensitivity 分数)
                         │
                         ▼
        【步骤 B：双轨比对融合】
        triage_dual_track_comparator.py
        (将“规则”与“0.6B模型预测”进行逻辑合流，筛选出真正的高危目标)
                         │
                         ▼
           triage_pools_v2.json (高危优先级池：Pool A + Pool B)
═════════════════════════╪═════════════════════════════════════════════
                         │  🎯 下游：开始执行动态挖掘与验证！
                         ▼
                 Invar System-2 (深度验证引擎)
```