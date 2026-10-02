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
# 阶段 1：子域名被动采集
subdomains_txt="data/targets/${target}/subdomains.txt"

echo "[*] 正在执行 subfinder 被动发现，目标: ${target} ..."
subfinder -d "${target}" -silent -o "${subdomains_txt}"

echo "[✓] 阶段 1 完成。产物位置: ${subdomains_txt}"
echo "    采集到子域名总数: $(wc -l < "${subdomains_txt}") 个"
```
* **核心产物**：`data/targets/<target>/subdomains.txt`（纯净子域名清单）

---

## 阶段 2：外部工具 Web 存活探测与边缘画像 (HTTPX)

Linux Mint 通常预装或 `udo apt install jq` :

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
# 阶段 3 路径与变量定义
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

# 3.3 批量物理下载前端 JS 代码并计算 SHA256 存证
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
* **核心产物**：
  * `tmp/raw_js/<host>/*.js`（目标全离子前端代码库）
  * `tmp/<target>_javascript_manifest.jsonl`（物理文件哈希指纹）

---

## 阶段 4：Tree-sitter AST 静态接口与契约提炼

```bash
# 阶段 4 路径定义
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
* **核心产物**：`tmp/<target>_endpoints_report.json`（剥离了路由、参数与破坏性标记的 API 契约）

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
* **核心产物**：`tmp/<target>_predictions.jsonl`（全部端点的 Impact / Sensitivity 软标签）

---

## 阶段 6：终审双轨比对器（规则 ∪ 神经并集融合，零漏报）

```bash
# 阶段 6 路径与输入
endpoint_report="tmp/${target}_endpoints_report.json"
predictions_out="tmp/${target}_predictions.jsonl"
raw_js_dir="tmp/raw_js"
http_surface="${target_dir}/httpx.jsonl"
output_dir="artifacts/reports"

mkdir -p "${output_dir}"

echo "==========================================================================="
echo " ⚖️ 启动 Invar 终审双轨比对器 (规则 ∪ 神经并集融合)"
echo " 📄 静态报告 : ${endpoint_report}"
echo " 🧠 神经物证 : ${predictions_out}"
echo " 🌐 边缘画像 : ${http_surface}"
echo " 🎯 战报输出 : ${output_dir}"
echo "==========================================================================="

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
* **核心产物**：
  * `artifacts/reports/triage_pools_v2.json`（Pool A 规则保底池与 Pool B 神经破盲池）
  * `artifacts/reports/triage_dual_track_v2.jsonl`（全维度融合审计底账）

---

## 阶段 7：System-2 靶心任务装配与优先级调度 (Dispatch)

```bash
pools_json="artifacts/reports/triage_pools_v2.json"
dual_track_jsonl="artifacts/reports/triage_dual_track_v2.jsonl"
tasks_output="artifacts/reports/targeted_research_tasks.json"

uv run --project python python python/scripts/assemble_triage_tasks.py \
    --pools "${pools_json}" \
    --dual-track "${dual_track_jsonl}" \
    --output "${tasks_output}" \
    --target-pools pool_a_rule_must_keep pool_b_discrepancy

# 输出装配战报统计
echo -e "\n[✓] 阶段 7 完成！"
echo "    高浓度研究种子库已生成: ${tasks_output}"
if command -v jq >/dev/null 2>&1; then
    echo "    • 装配任务总数: $(jq '.total_tasks' "${tasks_output}") 个"
    echo "    • 优先级分布  : $(jq -c '.priority_breakdown' "${tasks_output}")"
    echo "    • 假说分布    : $(jq -c '.hypothesis_breakdown' "${tasks_output}")"
fi
```
* **核心产物**：`artifacts/reports/targeted_research_tasks.json`（已分配 P0/P1/P2/P3 优先级）

这个阶段就是 LLM 的“高浓度研究种子库（Research Seed Inventory）”，而不是让 LLM 在一次 Prompt 里把 86 个任务全部打包吞下去。

---

## 阶段 8：System-2 自适应沙箱受控动态实证

```bash
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
  8. `coverage-summary.md`：[覆盖账本] 路径审查全景责任矩阵。	90% (契约已测，等待点火)
5. Invar Deterministic Core	9 大变换族变异 (F1~F3) + 双主体 IDOR 差分 + 不变量系统	Claude-Red (BOLA/IDOR SOP)	95% (算子与 CUDA 已打通)
6. Observation / Semantic Eval	SemanticEquivalenceEvaluator (三值逻辑防误报、识破假 200)	Anthropic Harness (语义等价性检验)	90% (单测全绿，等待实战)
7. Evidence & Verification	Layer 0~6 证据链 + 同态重放 + IndependentVerifier + PromotionGate	顶级科研标准 (无偏独立复核)	90% (门禁完备)
8. Finding / PoC Package	KnowledgeCard + OpenVEX v0.2.0 + OASIS SARIF 2.1.0 导出	OpenSSF 工业合规标准	90% (投影器已
