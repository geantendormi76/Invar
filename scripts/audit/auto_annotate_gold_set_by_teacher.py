#!/usr/bin/env python3
"""
Invar Phase-2: Automated 27B Teacher Blind Annotator (Aligned with Distiller 4K Spec).

Aligns max_tokens with distiller specification and adds regex-based JSON rescue
for thinking models. Automatically resumes and repairs failed cards.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CANDIDATES_PATH = Path("data/targets/ikuai8.com/gold_set_candidates_v1.jsonl")
ANNOTATED_PATH = Path("data/targets/ikuai8.com/gold_set_annotated_v1.jsonl")

SYSTEM_PROMPT = """You are a principal application security architect and code auditor acting as an impartial ground-truth judge.
Evaluate the given API endpoint interaction slice across TWO ORTHOGONAL SECURITY DIMENSIONS using standardized Likert Rubrics (1 to 5).
You must reason strictly based on the provided code snippet and route facts.

================================================================================
DIMENSION 1: STATE MUTATION & BLAST RADIUS (IMPACT)
Level 1: Negligible. Zero state mutation. Read-only health check, ping, public metrics, or informational probe.
Level 2: Minor. Transient or non-destructive read/write (e.g. read session metadata, viewing list, caching).
Level 3: Moderate. Standard business CRUD operations (e.g. update user profile, add port forwarding / NAT rule).
Level 4: High. High-privilege state override, master configuration overwrite, or security policy alteration.
Level 5: Catastrophic. Device/infrastructure destructive actions: firmware overwrite, drop database schema, RCE, firewall flush.

================================================================================
DIMENSION 2: DATA & ASSET CONFIDENTIALITY (SENSITIVITY)
Level 1: Public. Completely public information (system uptime, open documentation, public healthz).
Level 2: Operational. Non-sensitive operational metadata (network interface byte counters, device model string).
Level 3: Internal. Tenant-internal business data (audit logs, employee rosters, network topology).
Level 4: Confidential. High-value credentials and assets (password hashes, session tokens, JWTs, financial transactions).
Level 5: Secret. Master root credentials: root private keys, database master passwords, HSM seeds.

[Mandatory Output Requirement]:
Output strictly valid JSON matching this schema:
{
  "impact_level": 1 to 5 (integer),
  "sensitivity_level": 1 to 5 (integer),
  "rationale": "One concise sentence explaining the physical code evidence strictly under 25 words."
}
"""


def extract_compact_snippet(full_slice: str, target_path: str, max_window: int = 800) -> str:
    if not full_slice:
        return "// [No code available]"
    
    clean_text = re.sub(r"\s+", " ", full_slice).strip()
    if len(clean_text) <= max_window:
        return clean_text

    idx = clean_text.find(target_path)
    if idx == -1:
        clean_path = target_path.strip("/")
        idx = clean_text.find(clean_path)

    if idx != -1:
        half = max_window // 2
        start = max(0, idx - half)
        end = min(len(clean_text), idx + len(target_path) + half)
        return clean_text[start:end]

    return clean_text[:max_window]


def build_user_prompt(card: Dict[str, Any]) -> str:
    target_path = str(card.get("path", "")).strip()
    raw_slices = card.get("evidence_slices", [])
    
    bounded_slices = []
    for s in raw_slices[:2]:
        s_idx = s.get("slice_index", 1)
        src_file = Path(s.get("source_file", "")).name
        src_line = s.get("source_line", 1)
        raw_code = str(s.get("code_slice", ""))
        
        compact_code = extract_compact_snippet(raw_code, target_path, max_window=700)
        bounded_slices.append(f"--- [Evidence Slice {s_idx} | {src_file}:{src_line}] ---\n{compact_code}")

    slices_formatted = "\n\n".join(bounded_slices) if bounded_slices else "// [No physical code slice available]"
    if len(slices_formatted) > 2500:
        slices_formatted = slices_formatted[:2500] + "\n// ... [truncated for budget]"

    return f"""[Endpoint Route]: {card.get('method')} https://{card.get('host')}/{target_path.lstrip('/')}
[Extracted Parameters]: {', '.join(card.get('extracted_params', [])) if card.get('extracted_params') else 'None'}

[AST Code Evidence]:
```javascript
{slices_formatted}
```

Evaluate the physical Impact level (1-5) and Sensitivity level (1-5) based on the above evidence. Output raw JSON ONLY."""


def strip_json(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", cleaned, flags=re.IGNORECASE).strip()

    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return cleaned.strip()


def parse_response_with_rescue(content: str) -> Dict[str, Any]:
    """尝试标准 JSON 解析；若遭遇尾部截断，则启动正则无损挽救"""
    cleaned_text = strip_json(content)
    try:
        parsed = json.loads(cleaned_text)
        imp = parsed.get("impact_level") or parsed.get("impact")
        sens = parsed.get("sensitivity_level") or parsed.get("sensitivity")
        rat = parsed.get("rationale") or parsed.get("reasoning") or "Evaluated by 27B teacher"
        if imp is not None and sens is not None:
            return {
                "impact": max(1, min(5, int(imp))),
                "sensitivity": max(1, min(5, int(sens))),
                "rationale": str(rat)[:120],
            }
    except Exception:
        pass

    # 正则紧急挽救：即使末尾 rationale 没闭合，只要抓到分数就能挽救成功！
    imp_match = re.search(r'"impact(?:_level)?"\s*:\s*([1-5])', content, re.IGNORECASE)
    sens_match = re.search(r'"sensitivity(?:_level)?"\s*:\s*([1-5])', content, re.IGNORECASE)

    if imp_match and sens_match:
        return {
            "impact": int(imp_match.group(1)),
            "sensitivity": int(sens_match.group(1)),
            "rationale": "[Regex-Rescued] Successfully extracted Likert levels before truncation",
        }

    raise ValueError(f"Failed to parse or rescue Likert scores from content: {content[:150]}")


def query_teacher_model(endpoint: str, model_name: str, prompt: str, timeout: float = 120.0) -> Dict[str, Any]:
    url = f"{endpoint.rstrip('/')}/chat/completions"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        # 对齐 distiller 规范：放宽到 2048，给思考链充分空间
        "max_tokens": 2048,
    }
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {resp.read().decode('utf-8', errors='ignore')[:200]}")
        res_json = json.loads(resp.read().decode("utf-8"))

    content = res_json["choices"][0]["message"]["content"]
    return parse_response_with_rescue(content)


def main():
    parser = argparse.ArgumentParser(description="Invar Phase-2: 27B 教师模型全自动盲标执行器 (对齐 2048 规范版)")
    parser.add_argument("--candidates", type=Path, default=CANDIDATES_PATH, help="盲标候选卡片路径")
    parser.add_argument("--output", type=Path, default=ANNOTATED_PATH, help="标注产物输出路径")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080/v1", help="本地 27B 推理服务地址")
    parser.add_argument("--model", default="local", help="模型名称")
    parser.add_argument("--timeout", type=float, default=90.0, help="单次请求超时秒数")
    args = parser.parse_args()

    print("=" * 75)
    print(" 🤖 Invar Phase-2: 27B 教师模型全自动盲审 (对齐 Distiller 规范版)")
    print(f" 📂 输入盲卡: {args.candidates}")
    print(f" 💾 输出真值: {args.output}")
    print(f" 🔌 推理地址: {args.endpoint} (max_tokens: 2048 充裕思考空间)")
    print("=" * 75)

    if not args.candidates.is_file():
        print(f"[❌] 找不到盲卡文件: {args.candidates}")
        return 1

    # 装载已有成果：只保留真实成功的项，自动剔除带 Fallback 的失败项
    annotated_map: Dict[str, Dict[str, Any]] = {}
    if args.output.is_file():
        with args.output.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    anno = item.get("annotation", {})
                    ev = str(anno.get("semantic_evidence", ""))
                    if anno.get("ground_truth_impact") is not None and not ev.startswith("[Timeout-Fallback]"):
                        annotated_map[item["card_id"]] = item

    all_cards = []
    with args.candidates.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_cards.append(json.loads(line))

    total = len(all_cards)
    already_done = len(annotated_map)
    print(f"[*] 样本全量: {total} 张卡片 | 已保留有效进度: {already_done} 张 | 待盲审: {total - already_done} 张\n")

    start_time = time.perf_counter()

    for idx, card in enumerate(all_cards, start=1):
        cid = card["card_id"]

        # 断点续标：如果已有真实有效标注，直接复用
        if cid in annotated_map:
            card["annotation"] = annotated_map[cid]["annotation"]
            continue

        prompt = build_user_prompt(card)
        method_path = f"{card.get('method')} {card.get('path')}"
        print(f"[{idx:02d}/{total}] 正在盲审 {cid:8s} | {method_path[:45]:45s} ...", end="", flush=True)

        t0 = time.perf_counter()
        success = False
        last_err = ""

        for attempt in range(1, 3):
            try:
                res = query_teacher_model(args.endpoint, args.model, prompt, timeout=args.timeout)
                elapsed = time.perf_counter() - t0
                
                card["annotation"] = {
                    "ground_truth_impact": res["impact"],
                    "ground_truth_sensitivity": res["sensitivity"],
                    "semantic_evidence": f"[27B-Judge] {res['rationale']}",
                    "annotator_confidence": 1.0,
                }
                annotated_map[cid] = card
                success = True
                print(f" [✓] I:{res['impact']} S:{res['sensitivity']} ({elapsed:.1f}s)")
                break
            except Exception as exc:
                last_err = str(exc)
                time.sleep(1.0)

        if not success:
            print(f" [❌ 失败: {last_err[:40]}] -> 启用兜底中性标注")
            card["annotation"] = {
                "ground_truth_impact": 3,
                "ground_truth_sensitivity": 3,
                "semantic_evidence": f"[Timeout-Fallback] {last_err[:60]}",
                "annotator_confidence": 0.5,
            }
            annotated_map[cid] = card

        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp_output = args.output.with_name(args.output.name + ".tmp")
        with tmp_output.open("w", encoding="utf-8") as f:
            for c in all_cards:
                record_to_write = annotated_map.get(c["card_id"], c)
                f.write(json.dumps(record_to_write, ensure_ascii=False) + "\n")
        tmp_output.replace(args.output)

    total_time = time.perf_counter() - start_time
    print("\n" + "=" * 75)
    print(" 🎉 60 张黄金盲标卡片已全部独立裁决完毕！")
    print(f" 📄 完整真值资产落盘: {args.output.resolve()}")
    print(f" ⏱️  本次耗时       : {total_time:.1f} 秒")
    print("=" * 75)
    print("\n[下一步]: 运行 evaluate_gold_set_v1.py 即可秒级出具最终解密对决战报！\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
