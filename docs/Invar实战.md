# 🛡️ Invar 工业级实战操作指南

> **适用工程根目录**：`/home/zhz/Invar`  
> **运行基准环境**：Linux Mint 22.3 Cinnamon (x86_64) | NVIDIA GeForce RTX 3060 12GB | CUDA 12  
> **核心基础设施**：本地 `llama-server` (127.0.0.1:8080/v1) + Ornith 1.5 35B GGUF (160K 上下文 + MTP 投机加速)  
> **工程治理原则**：更换测试资产只需修改唯一的 `target` 变量，全流水线受制于数据契约与安全不变量，严禁局部特调。  
> **多轮自适应飞轮**：外部被动采集 ➔ AST 契约提炼 ➔ 0.6B 神经反射 (System-1) ➔ 双轨融合 ➔ System-2 受控自适应沙箱动态实证 ➔ 本地 35B 大模型 CoT 战略反思 ➔ 自主第 2 轮物理变异追击 ➔ 独立可复现 PoC 脚本与黄金证据链导出。

---

## 0. 全局拓扑与数据流动图

```text
目标 Scope ($target)
   ↓ [Phase 1: subfinder 被动发现]
subdomains.txt
   ↓ [Phase 2: httpx 存活测绘与网络指纹]
live_hosts.txt + httpx.jsonl (HTTP 边缘画像底账)
   ↓ [Phase 3: katana 深度爬取 + download_javascript.py 物理落地与哈希存证]
tmp/raw_js/ (前端代码全离子落盘)
   ↓ [Phase 4: scan_pipeline.py AST 静态语法解析]
tmp/${target}_endpoints_report.json (静态 AST API 契约, 1097 端点)
   ↓ [Phase 5: predict_triage_onnx.py (System-1 0.6B ONNX CUDA 神经推演)]
tmp/${target}_predictions.jsonl (Impact / Sensitivity 双正交软标签)
   ↓ [Phase 6: triage_dual_track_comparator.py 终审双轨比对器 (规则 ∪ 神经并集融合)]
artifacts/reports/triage_pools_v2.json (Pool A 规则必保 ∪ Pool B 神经破盲)
   ↓ [Phase 7: assemble_triage_tasks.py (词法门禁清洗 + RFC 3986 路径解构 + 任务装配)]
artifacts/reports/targeted_research_tasks.json (P0~P3 纯净靶向任务种子库, 81 个纯正任务)
   ↓ [Phase 8: 阶段 8 原型反思与历史归档 (发现单发扫描与动词死锁瓶颈)]
   ↓ [Phase 9: run_targeted_audit.py (System-2 多轮自适应追击 + 35B CoT 反思 + 独立 PoC 飞轮)]
artifacts/reports/targeted_audit_production/
    ├── findings.json (含原生 poc_code 字段的机器可读底账)
    ├── FINDINGS-DETAIL.md (含独立第 4 节可复现 cURL PoC 代码块的深度战报)
    ├── sarif.json (OASIS SARIF 2.1.0 国际标准交换格式)
    ├── openvex.json (OpenSSF OpenVEX v0.2.0 国际安全声明)
    └── REPORT.md / NEEDS-VALIDATION.md / coverage-summary.md
```

---

## 阶段 0：换新靶场唯一入口（初始化）

```bash
# 【全局唯一目标配置】更换测试资产只需修改此变量
target="ikuai8.com"

# 目标专属工作目录
target_dir="data/targets/${target}"

# 1. 递归创建目标目录、临时空间与报告归档目录
mkdir -p "${target_dir}" tmp artifacts/reports

# 2. 写入法定授权范围 (Scope) 白名单
cat << EOF > "${target_dir}/scope.txt"
${target}
EOF

# 3. 打印验证
echo "[✓] 阶段 0 初始化完成: 目标目录已就绪 -> ${target_dir}"
ls -la "${target_dir}"
```

---

## 阶段 1：外部工具多源子域名全量被动发现 (Subfinder)

```bash
subdomains_txt="data/targets/${target}/subdomains.txt"

echo "[*] 正在执行 subfinder 被动发现，目标: ${target} ..."
subfinder -d "${target}" -silent -o "${subdomains_txt}"

echo "[✓] 阶段 1 完成。产物位置: ${subdomains_txt}"
echo "    采集到子域名总数: $(wc -l < "${subdomains_txt}") 个"
```
* **核心产物**：`data/targets/<target>/subdomains.txt`（纯净子域名清单）

---

## 阶段 2：外部工具 Web 存活探测与边缘画像 (HTTPX)

```bash
# 1. 存活探测与边缘画像
httpx -l "data/targets/${target}/subdomains.txt" -silent -sc -title -tech-detect -web-server -json -o "data/targets/${target}/httpx.jsonl"

# 2. Linux 原生极简提取与去重
jq -r '.url // empty' "data/targets/${target}/httpx.jsonl" | sort -u > "data/targets/${target}/live_hosts.txt"

# 3. 统计
echo "[✓] 存活 Web 目标总数: $(wc -l < "data/targets/${target}/live_hosts.txt") 个"
```
* **核心产物**：
  * `data/targets/<target>/httpx.jsonl`（技术栈与网络指纹底账）
  * `data/targets/<target>/live_hosts.txt`（纯净存活主机与端口）

---

## 阶段 3：Katana 静态资产深度爬取与前端 JS 快速物理下载

```bash
katana_output="data/targets/${target}/katana.jsonl"
urls_jsonl="data/targets/${target}/urls.jsonl"
js_jsonl="data/targets/${target}/javascript.jsonl"
raw_js_dir="tmp/raw_js"
js_manifest="tmp/${target}_javascript_manifest.jsonl"

mkdir -p "${raw_js_dir}"

# 3.1 Katana 深度爬取存活主机
echo "[*] 3.1 启动 katana 深度爬取..."
katana -list "data/targets/${target}/live_hosts.txt" -jc -d 2 -c 5 -silent -j -or -ob -o "${katana_output}"

# 3.2 归一化解构业务路由与 JS 资产表
echo "[*] 3.2 归一化解构资产路由..."
uv run --project python python python/scripts/normalize_katana.py \
    --input "${katana_output}" \
    --urls-output "${urls_jsonl}" \
    --javascript-output "${js_jsonl}" \
    --target "${target}"

# 3.3 批量并发下载前端 JS 代码并计算 SHA256 存证
echo "[*] 3.3 批量并发下载前端 JS 代码..."
uv run --project python python python/scripts/download_javascript.py \
    --input "${js_jsonl}" \
    --output-dir "${raw_js_dir}" \
    --manifest "${js_manifest}" \
    --target "${target}" \
    --workers 8 \
    --timeout 15 \
    --insecure \
    --retry-failed-only

# 3.4 输出统计结果
echo "[✓] 阶段 3 完成。"
echo "    爬取原始记录: $(wc -l < "${katana_output}") 条"
echo "    解构 URL 总数: $(wc -l < "${urls_jsonl}") 条"
echo "    待下 JS 总数: $(wc -l < "${js_jsonl}") 条"
echo "    已落地 JS 文件数: $(find "${raw_js_dir}" -type f -name "*.js" | wc -l) 个"
```

---

## 阶段 4：Tree-sitter AST 静态接口与契约提炼

```bash
endpoint_report="tmp/${target}_endpoints_report.json"

echo "[*] 启动 Tree-sitter AST 静态语法解析流水线..."
uv run --project python python python/scripts/scan_pipeline.py \
    "tmp/raw_js" \
    -o "${endpoint_report}"

# 打印提炼成果统计
echo "[✓] 阶段 4 完成。"
echo "    静态 API 契约报告已生成: ${endpoint_report}"
if command -v jq >/dev/null 2>&1; then
    echo "    提炼端点总数: $(jq '.endpoints | length' "${endpoint_report}") 个"
    echo "    严重高危接口: $(jq '.summary.critical_risk_count' "${endpoint_report}") 个"
    echo "    高风险接口:   $(jq '.summary.high_risk_count' "${endpoint_report}") 个"
fi
```

---

## 阶段 5：System-1 神经认知反射初筛 (0.6B ONNX 原生推演)

```bash
# 1. 确保加载 Base-Jev 验证通过的 CUDA 驱动链穿透环境
source tools/env_cuda.sh

# 2. 阶段 5 变量与路径
endpoint_report="tmp/${target}_endpoints_report.json"
predictions_out="tmp/${target}_predictions.jsonl"
raw_js_dir="tmp/raw_js"
model_dir="models/invar-intent-0.6b-v2"

echo "==========================================================================="
echo " 🚀 启动 System-1 0.6B ONNX 神经认知推演 (RTX 3060 CUDA 全速点火)"
echo " 📂 模型路径 : ${model_dir}"
echo " 📄 端点报告 : ${endpoint_report}"
echo " 🎯 预测输出 : ${predictions_out}"
echo "==========================================================================="

uv run --project python python python/scripts/predict_triage_onnx.py \
    --report "${endpoint_report}" \
    --raw-js "${raw_js_dir}" \
    --model-dir "${model_dir}" \
    --output "${predictions_out}"

# 3. 统计推演成果
echo "[✓] 阶段 5 完成！"
echo "    生成预测条数: $(wc -l < "${predictions_out}")"
echo "    原始端点总数: $(jq '.endpoints | length' "${endpoint_report}")"
```

---

## 阶段 6：终审双轨比对器（规则 ∪ 神经并集融合，零漏报）

```bash
endpoint_report="tmp/${target}_endpoints_report.json"
predictions_out="tmp/${target}_predictions.jsonl"
raw_js_dir="tmp/raw_js"
http_surface="${target_dir}/httpx.jsonl"
output_dir="artifacts/reports"

mkdir -p "${output_dir}"

uv run --project python python python/scripts/triage_dual_track_comparator.py \
    --report "${endpoint_report}" \
    --raw-js "${raw_js_dir}" \
    --neural-jsonl "${predictions_out}" \
    --http-surface "${http_surface}" \
    --output-dir "${output_dir}"

# 验证融合产物
echo -e "\n[✓] 阶段 6 完成！"
echo "    融合底账: ${output_dir}/triage_dual_track_v2.jsonl"
echo "    分流靶标池: ${output_dir}/triage_pools_v2.json"
if command -v jq >/dev/null 2>&1; then
    echo "    • Pool A (规则必保面): $(jq '.pool_a_rule_must_keep | length' "${output_dir}/triage_pools_v2.json") 个 Surface"
    echo "    • Pool B (神经破盲面): $(jq '.pool_b_discrepancy | length' "${output_dir}/triage_pools_v2.json") 个 Surface"
    echo "    • Pool C (参数探索面): $(jq '.pool_c_exploration | length' "${output_dir}/triage_pools_v2.json") 个 Surface"
fi
```

---

## 阶段 7：System-2 靶心任务装配与优先级调度 (Dispatch)

```bash
pools_json="artifacts/reports/triage_pools_v2.json"
dual_track_jsonl="artifacts/reports/triage_dual_track_v2.jsonl"
tasks_output="artifacts/reports/targeted_research_tasks.json"

PYTHONPATH="python/packages/core/src" uv run --project python python python/scripts/assemble_triage_tasks.py \
    --pools "${pools_json}" \
    --dual-track "${dual_track_jsonl}" \
    --output "${tasks_output}" \
    --target-pools pool_a_rule_must_keep pool_b_discrepancy

echo -e "\n[✓] 阶段 7 完成！"
echo "    高浓度纯净研究种子库已生成: ${tasks_output}"
if command -v jq >/dev/null 2>&1; then
    echo "    • 装配纯净任务总数: $(jq '.total_tasks' "${tasks_output}") 个"
    echo "    • 优先级分布      : $(jq -c '.priority_breakdown' "${tasks_output}")"
    echo "    • 假说分布        : $(jq -c '.hypothesis_breakdown' "${tasks_output}")"
fi
```

---

## 阶段 8：System-2 多轮自适应追击与可复现 PoC 闭环飞轮 

> **【阶段 8 核心突破与智能体飞轮机制】**：
> 1. **大模型决策支配物理发包 (Actionable Steer Dispatch)**：解除动词硬编码死锁。当目标返回 405 或策略阻断时，本地 35B 模型在思维链 (CoT) 中反思出的 `method="GET"` 建议能够端到端穿透，自主调度第 2 轮变异发包（归入 `F2_METHOD_SEMANTICS` 族）；
> 2. **可复现 PoC 原子组装 (PoC Code Synthesis)**：突破达成后，系统自动基于生效变异体组装出标准、无损的 `cURL` 命令行复现代码，存入 `EvidenceChain.poc_code`；
> 3. **全链路战报原生贯通 (End-to-End Deliverables Projection)**：
>    - `findings.json`：原生承载 `"poc_code"` 属性，机器可读；
>    - `FINDINGS-DETAIL.md`：原生呈现独立的 **【第 4 节：独立漏洞复现 PoC (Reproducible PoC)】** 代码块，治理建议自动顺延为第 5 节；
>    - 完全满足 SRC / Bug Bounty 法定报告要求。

### 1. 运行时环境变量配置 (对齐 Pi 生产级算力)
```bash
# 验证本地推理后端健康状态
echo -n "[*] 检查 llama-server 健康状态: " && curl -s http://127.0.0.1:8080/health && echo ""

# 注入大模型运行时环境变量
export INVAR_LLM_BASE_URL="http://127.0.0.1:8080/v1"
export INVAR_LLM_MODEL="/home/zhz/models/Ornith-1.5-35B-A3B-Abliterated-CyberTiel_Calibrated-MTPv2-23G-ICE.gguf"
export INVAR_LLM_TIMEOUT="120"
export INVAR_LLM_MAX_TOKENS="8192"
```

### 2. 调度执行多轮实证流水线 (以 P1 纯净全量批次为例)
```bash
endpoint_report="tmp/${target}_endpoints_report.json"
output_dir="artifacts/reports/targeted_audit_production"

PYTHONPATH="python/packages/core/src" uv run --project python python python/scripts/run_targeted_audit.py \
    --tasks "artifacts/reports/targeted_research_tasks.json" \
    --report-input "${endpoint_report}" \
    --output-dir "${output_dir}" \
    --priority "P1" \
    --enable-llm \
    --timeout 10
```

### 3. 阶段 9 最终权威交付物清单 (位于指定输出目录)
1. `execution.jsonl`：[微观事实] 毫秒级物理发包事实、多轮发包时延、动词变更与 CoT 反思事件流；
2. `findings.json`：[漏洞确权] 承载 `poc_code` 复现字段的机器可读漏洞记录；
3. `FINDINGS-DETAIL.md`：[实锤细节] **包含独立第 4 节可复现 cURL PoC 代码块**、代码调用链、发包 Proof 的深度战报；
4. `openvex.json`：[合规凭证] 100% 符合 Linux 基金会 OpenSSF OpenVEX v0.2.0 国际规范；
5. `sarif.json`：[缺陷交换] 100% 符合 OASIS SARIF 2.1.0 国际规范；
6. `REPORT.md`：[决策总览] 资产血统、加权覆盖率、发现总览；
7. `NEEDS-VALIDATION.md`：[攻坚清单] 存疑待人工介入清单；
8. `coverage-summary.md`：[覆盖账本] 路径审查全景责任矩阵。

---

## 核心支撑组件完成度对齐表 (Phase 9.1 LKG 基线)

| 核心组件 | 关键算子与设计规范 | 对齐黄金标准 | 状态与验证水平 |
| :--- | :--- | :--- | :--- |
| **AST 契约提取器** | Tree-sitter 纯净语法解析 + 词法合法性门禁 (`_is_valid_api_path`) | 彭峙酿《Hacking with LLMs》[1] | **100%** (已过滤非 ASCII 与前端代码调用) |
| **System-1 神经认知推演** | 0.6B ONNX GPU 快速推演 (Impact / Sensitivity 双正交头) | 微软 DirectML / NVIDIA CUDA 原生加速 | **100%** (推演全量 1097 个静态端点) |
| **终审双轨比对器** | 规则必保 (Pool A) ∪ 神经破盲 (Pool B) 并集融合 | 现代学术顶会双轨无偏采样标准 | **100%** (生成 81 个纯净靶向任务) |
| **Invar 确定性核心** | 9 大变换族变异 (F1~F9) + 双主体 IDOR 差分 + 不变量系统 | Claude-Red (BOLA/IDOR SOP) [4] | **100%** (算子库完备) |
| **语义等价评估器** | 六维正交比对 (三值逻辑防误报，识破单页应用 `html_fallback` 伪 200) | Anthropic Reference Harness [2] | **100%** (实战识破 demo.ikuai8.com 首页回退) |
| **认知决策控制面** | 本地 Ornith 35B 结构化决策 + 8192 Token 满血思维链预算 | Pi Agent Harness (`earendil-works/pi`) [8] | **100%** (单用例 9.7s 输出高水准 CoT 决策) |
| **多轮变异追击状态机** | 动词契约动态解耦 + 大模型建议驱动 Turn 2 物理追击发包 | 路线 B 自主渗透智能体标准 | **100%** (测试用例全绿通过) |
| **可复现 PoC 战报结晶** | 自动生成开箱即用 cURL PoC + FINDINGS-DETAIL.md 原生代码块渲染 | 工业级 SRC / 顶会实证标准 | **100%** (254 项单测全绿，端到端贯通) |
| **工业合规战报投影** | OASIS SARIF 2.1.0 + OpenSSF OpenVEX v0.2.0 原生物理投影 | OpenSSF 工业合规标准 | **100%** (一键原子化导出全量 8 大产物) |
