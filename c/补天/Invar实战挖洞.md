
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
                授权范围
                    │
                    ▼
                 scope.txt
                    │
                    ▼
                Subfinder
                    │
                    ▼
             subdomains.jsonl
                    │
                    ▼
                  HTTPX
                    │
                    ▼
             live_hosts.jsonl
                    │
                    ▼
              Katana 输入构建
                    │
                    ▼
                Katana
                    │
                    ▼
               katana.jsonl
                    │
                    ▼
            normalize_katana
             ┌──────┴──────┐
             ▼             ▼
         urls.jsonl   javascript.jsonl
             │             │
             └──────┬──────┘
                    ▼
                 raw_js/
                    │
          =====================
              INVAR CORE
          =====================
                    │
                    ▼
                   AST
                    │
                    ▼
               EndpointIR
                    │
                    ▼
               RiskEngine
                    │
                    ▼
            HypothesisEngine
                    │
                    ▼
        AdaptiveSandboxExecutor
                    │
                    ▼
                 Evidence
                    │
                    ▼
            Promotion Gate
                    │
             ┌──────┴──────┐
             ▼             ▼
          VERIFIED       REFUTED
             │
             ▼
        KnowledgeCard
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
subfinder -d "ikuai8.com" -silent -o "C:\dev\Invar\tmp\ikuai8_subdomains.txt"
```

这是**候选资产发现**。

不是 Web 存活确认。你的标准也是这样定义的。

---

## 阶段 2：Subdomain 归一化

```powershell
uv run python .\scripts\asset\ingest_subdomains.py `
    --input "C:\dev\Invar\tmp\ikuai8_subdomains.txt" `
    --target "ikuai8.com"
```

产物：

```text
data\targets\ikuai8.com\subdomains.jsonl
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
    --input "C:\dev\Invar\data\targets\ikuai8.com\subdomains.jsonl" `
    --target "ikuai8.com"
```

产物：

```text
data\targets\ikuai8.com\httpx.jsonl
data\targets\ikuai8.com\live_hosts.jsonl
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
    --input ".\data\targets\ikuai8.com\live_hosts.jsonl" `
    --output ".\tmp\ikuai8_katana_input.txt"
```

得到：

```text
tmp\ikuai8_katana_input.txt
```

内容就是：

```text
https://host1.ikuai8.com
https://host2.ikuai8.com
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
    -list ".\tmp\ikuai8_katana_input.txt" `
    -jc `
    -d 2 `
    -c 5 `
    -silent `
    -j `
    -or `
    -ob `
    -o ".\data\targets\ikuai8.com\katana.jsonl"
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
    --input ".\data\targets\ikuai8.com\katana.jsonl" `
    --urls-output ".\data\targets\ikuai8.com\urls.jsonl" `
    --javascript-output ".\data\targets\ikuai8.com\javascript.jsonl" `
    --target "ikuai8.com"
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
Get-Content .\data\targets\ikuai8.com\urls.jsonl -TotalCount 3
Get-Content .\data\targets\ikuai8.com\javascript.jsonl -TotalCount 3
```

---

# 四、JavaScript 批量下载

```powershell
uv run `
    --project "C:\dev\Invar\src-tauri\python" `
    --python 3.11 `
    python "C:\dev\Invar\scripts\asset\download_javascript.py" `
    --input "C:\dev\Invar\data\targets\ikuai8.com\javascript.jsonl" `
    --output-dir "C:\dev\Invar\tmp\raw_js" `
    --manifest "C:\dev\Invar\tmp\ikuai8_javascript_manifest.jsonl" `
    --target "ikuai8.com" `
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

## 现在执行正确的正式命令

```powershell
uv run `
    --project "C:\dev\Invar\src-tauri\python" `
    --python 3.11 `
    python "C:\dev\Invar\scripts\pipeline\scan_pipeline.py" `
    "C:\dev\Invar\tmp\raw_js" `
    -o "C:\dev\Invar\tmp\ikuai8_endpoints_report.json"
```

这里我们**先不加 `--probe`**。

原因很简单：当前阶段是先完成：

```text
209 个本地 JS
    ↓
AST
    ↓
EndpointIR
    ↓
静态报告
```

`--probe` 会进入真实探针执行逻辑，不应该和首次 AST 基线扫描混在一起。当前测试代码也明确区分了普通扫描参数和 `--probe/--base-url`。

### 目前我们已经确认的链路

```text
Subfinder
   ↓
HTTPX
   ↓
Katana
   ↓
normalize_katana
   ↓
javascript.jsonl     209
   ↓
download_javascript
   ↓
raw_js                209
   ↓
scan_pipeline         ← 现在从这里继续
   ↓
EndpointIR
```

