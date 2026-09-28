#!/usr/bin/env python3
"""
predict_triage_onnx.py — Invar 仓内纯 ONNX DirectML 原生推演引擎
- 零 PyTorch 依赖，零 CUDA Toolkit 依赖
- 纯 tokenizers (Rust) + onnxruntime-directml 高速推演
- 物理连接 Impact (破坏力) 与 Sensitivity (敏感度) 双正交头
"""
import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_JS_LANGUAGE = Language(tsjavascript.language())

CAND_ANCHOR_TOKEN = "<|cand_anchor|>"
QUERY_ANCHOR_TOKEN = "<|query_anchor|>"


class FastAstExtractor:
    """Tree-sitter AST 语法切片提取器"""
    def __init__(self, window_chars: int = 250):
        self.window_chars = window_chars
        self.parser = Parser()
        self.parser.language = _JS_LANGUAGE
        self._cache: Dict[str, Any] = {}

    def _get_tree(self, physical_file: Path, source_bytes: bytes) -> Any:
        file_key = str(physical_file.resolve())
        if file_key not in self._cache:
            self._cache[file_key] = self.parser.parse(source_bytes)
        return self._cache[file_key]

    def extract_slice(self, file_p: Optional[Path], path_str: str, call_sig: str) -> str:
        safe_path = path_str[:150]
        fallback = call_sig if (call_sig and len(call_sig) >= 6) else safe_path
        if not file_p or not file_p.is_file():
            return fallback

        try:
            content = file_p.read_text(encoding="utf-8", errors="ignore")
            source_bytes = content.encode("utf-8", errors="ignore")
            tree = self._get_tree(file_p, source_bytes)
            root = tree.root_node
            stack = [root]
            while stack:
                curr = stack.pop()
                if curr.type == "call_expression":
                    node_text = curr.text.decode("utf-8", errors="ignore")
                    if safe_path in node_text or (call_sig and call_sig in node_text):
                        enclosing = curr
                        parent = curr.parent
                        while parent and parent.type in ("expression_statement", "lexical_declaration", "variable_declaration"):
                            enclosing = parent
                            parent = parent.parent
                        enc_text = enclosing.text.decode("utf-8", errors="ignore")
                        clean = " ".join(enc_text.split())
                        return clean[: self.window_chars]
                stack.extend(curr.children)

            idx = content.find(f'"{safe_path}"')
            if idx == -1:
                idx = content.find(f"'{safe_path}'")
            if idx == -1:
                idx = content.find(safe_path)
            if idx != -1:
                start = max(0, idx - 80)
                end = min(len(content), idx + len(safe_path) + 120)
                return " ".join(content[start:end].split())[: self.window_chars]
        except Exception:
            pass
        return fallback


def build_decision_prompt(
    host: str,
    method: str,
    path: str,
    params: str,
    code_slice: str,
    endpoint_id: str,
) -> str:
    """构建与 base-jev 训练因果偏序绝对同构的 Prompt 模板"""
    state_lines = [
        "[STATE_CONTEXT]",
        "Module: router",
        "AST_Node: CallExpression",
        f"Scope: {path}",
        f"host: {host}",
        f"method: {method}",
        f"params: {params}",
        f"code: {code_slice}",
    ]
    prompt = "\n".join(state_lines) + "\n\n"
    prompt += f"[SCORE_QUESTION: {endpoint_id}_impact]\n"
    prompt += f"{QUERY_ANCHOR_TOKEN} Query: 评估接口状态变更破坏力: {method} {path[:60]} (MaxLevels: 5)\n\n"
    prompt += f"[SCORE_QUESTION: {endpoint_id}_sensitivity]\n"
    prompt += f"{QUERY_ANCHOR_TOKEN} Query: 评估接口资产敏感度: {method} {path[:60]} (MaxLevels: 5)\n\n"
    return prompt


def main() -> int:
    parser = argparse.ArgumentParser(description="Invar 纯 ONNX DirectML 原生推演引擎")
    parser.add_argument("--report", type=str, default="tmp/ikuai8_endpoints_report.json", help="AST 提取报告路径")
    parser.add_argument("--raw-js", type=str, default="tmp/raw_js", help="下载的 JS 源码目录")
    parser.add_argument("--model-dir", type=str, default="models/invar-intent-0.6b-v2", help="ONNX 模型包目录")
    parser.add_argument("--output", type=str, default="tmp/base_jev_predictions_1216.jsonl", help="预测输出 JSONL 路径")
    parser.add_argument("--limit", type=int, default=None, help="限制推演端点数 (调试用)")
    args = parser.parse_args()

    report_p = (PROJECT_ROOT / args.report).resolve()
    raw_js_p = (PROJECT_ROOT / args.raw_js).resolve()
    model_dir_p = (PROJECT_ROOT / args.model_dir).resolve()
    output_p = (PROJECT_ROOT / args.output).resolve()
    output_p.parent.mkdir(parents=True, exist_ok=True)

    print("===========================================================================")
    print(" 🚀 Invar 纯 ONNX DirectML 原生推演点火 (Zero-PyTorch Single-Binary)")
    print(f" 📂 模型目录   : {model_dir_p}")
    print(f" 📄 AST 报告   : {report_p}")
    print(f" 🎯 目标输出   : {output_p}")
    print("===========================================================================")

    # 1. 加载分词器
    tokenizer_path = model_dir_p / "tokenizer.json"
    if not tokenizer_path.is_file():
        print(f"[-] 错误: 分词器不存在: {tokenizer_path}", file=sys.stderr)
        return 1
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    query_anchor_id = tokenizer.token_to_id(QUERY_ANCHOR_TOKEN)
    if query_anchor_id is None:
        print(f"[-] 错误: 分词器中未找到特殊锚点 {QUERY_ANCHOR_TOKEN}", file=sys.stderr)
        return 1

    # 2. 初始化 ONNX Session (优先 DirectML GPU，无 GPU 自动优雅退化为 CPU)
    onnx_path = model_dir_p / "system_one_unified.onnx"
    if not onnx_path.is_file():
        print(f"[-] 错误: ONNX 模型文件不存在: {onnx_path}", file=sys.stderr)
        return 1

    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    available_providers = ort.get_available_providers()
    providers = []
    if "DmlExecutionProvider" in available_providers:
        providers.append("DmlExecutionProvider")
    providers.append("CPUExecutionProvider")

    print(f"  [*] 正在装配 ONNX 执行提供商: {providers} ...")
    session = ort.InferenceSession(str(onnx_path), sess_options, providers=providers)
    active_providers = session.get_providers()
    print(f"  [✓] ONNX 运行时就绪！激活引擎: {active_providers[0]}")

    # 3. 读取待推演端点
    with report_p.open("r", encoding="utf-8") as f:
        report_data = json.load(f)
    endpoints = report_data.get("endpoints", [])
    if args.limit:
        endpoints = endpoints[: args.limit]
    total_endpoints = len(endpoints)
    print(f"  [✓] 待推演目标端点总数: {total_endpoints} 个\n")

    ast_extractor = FastAstExtractor(window_chars=250)
    t_start = time.perf_counter()
    results = []

    for idx, ep in enumerate(endpoints, 1):
        t_sample_start = time.perf_counter()
        endpoint_id = ep.get("endpoint_id") or ep.get("id") or f"EP-{idx:04d}"
        method = str(ep.get("method", "GET")).strip().upper()[:10]
        raw_path = str(ep.get("path", "")).strip()
        safe_path = raw_path[:200]
        source_file = ep.get("source_file")
        call_sig = str(ep.get("call_signature", ""))[:150]

        target_file = None
        if source_file:
            cand = raw_js_p / source_file
            if cand.is_file():
                target_file = cand
            else:
                found = list(raw_js_p.rglob(Path(source_file).name))
                target_file = found[0] if found else None

        code_slice = ast_extractor.extract_slice(target_file, safe_path, call_sig)
        params = [str(p).strip()[:40] for p in ep.get("extracted_params", []) if str(p).strip()]
        params_str = ",".join(params[:8])

        parts = Path(source_file).parts if source_file else []
        host_val = parts[1] if len(parts) > 1 and parts[0] == "raw_js" else "cloud.ikuai8.com"

        prompt = build_decision_prompt(
            host=host_val,
            method=method,
            path=safe_path,
            params=params_str,
            code_slice=code_slice,
            endpoint_id=endpoint_id,
        )

        encoded = tokenizer.encode(prompt, add_special_tokens=True)
        input_ids = encoded.ids
        seq_len = len(input_ids)

        # 序列超长保护
        if seq_len > 1800:
            res_item = {
                "endpoint_id": endpoint_id,
                "impact_score": 3.0,
                "sensitivity_score": 3.0,
                "impact_probs": [0.2] * 5,
                "sensitivity_probs": [0.2] * 5,
                "runner_provenance": "oversize_fallback_uniform",
                "elapsed_ms": 0.0,
            }
            results.append(res_item)
            continue

        query_positions = [i for i, t_id in enumerate(input_ids) if t_id == query_anchor_id]
        if len(query_positions) < 2:
            imp_pos = min(seq_len - 1, 30)
            sens_pos = min(seq_len - 1, 30)
        else:
            imp_pos = query_positions[0]
            sens_pos = query_positions[1]

        # 组装纯 NumPy 输入张量
        inputs = {
            "input_ids": np.array([input_ids], dtype=np.int64),
            "attention_mask": np.ones((1, seq_len), dtype=np.int64),
            "choice_q_pos": np.array([0], dtype=np.int64),
            "choice_cand_pos": np.array([[0]], dtype=np.int64),
            "choice_mask": np.array([[0.0]], dtype=np.float16),
            "bool_q_pos": np.array([0], dtype=np.int64),
            "impact_q_pos": np.array([imp_pos], dtype=np.int64),
            "sensitivity_q_pos": np.array([sens_pos], dtype=np.int64),
        }

        outputs = session.run(
            [
                "impact_dist",
                "impact_expected",
                "sensitivity_dist",
                "sensitivity_expected",
            ],
            inputs,
        )

        imp_dist = [round(float(p), 4) for p in outputs[0][0]]
        imp_exp = round(float(outputs[1][0][0]), 4)
        sens_dist = [round(float(p), 4) for p in outputs[2][0]]
        sens_exp = round(float(outputs[3][0][0]), 4)
        sample_elapsed = (time.perf_counter() - t_sample_start) * 1000.0

        res_item = {
            "endpoint_id": endpoint_id,
            "impact_score": imp_exp,
            "sensitivity_score": sens_exp,
            "impact_probs": imp_dist,
            "sensitivity_probs": sens_dist,
            "runner_provenance": "onnx-directml-v2-dual",
            "elapsed_ms": round(sample_elapsed, 2),
        }
        results.append(res_item)

        if idx % 100 == 0 or idx == total_endpoints:
            elapsed_so_far = time.perf_counter() - t_start
            rate = idx / elapsed_so_far if elapsed_so_far > 0 else 0
            print(f"  ├─ [{idx:>4}/{total_endpoints}] 推演中... 瞬时均速: {rate:>5.1f} 端点/秒 (当前时延: {sample_elapsed:>5.1f} ms)")

    # 写入物证
    with output_p.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    total_time = time.perf_counter() - t_start
    avg_speed = total_endpoints / total_time if total_time > 0 else 0
    print("\n===========================================================================")
    print(" 🎉 Invar 纯 ONNX 原生推演圆满收官！")
    print(f" 📄 输出物证路径 : {output_p}")
    print(f" 📊 生成结果总数 : {len(results)} 行 (1:1 逐行对齐)")
    print(f" ⏱️ 全量耗时     : {total_time:.2f} 秒 (平均速度: {avg_speed:.1f} 端点/秒)")
    print("===========================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
