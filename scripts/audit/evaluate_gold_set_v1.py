# -*- coding: utf-8 -*-
"""
evaluate_gold_set_v1.py
Invar Phase-3: 独立黄金集真实业务解密与双轨终审评估台 (Fail-Closed 混淆矩阵终极版)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ANNOTATED_PATH = Path("data/targets/ikuai8.com/gold_set_annotated_v1.jsonl")
MANIFEST_PATH = Path("data/targets/ikuai8.com/gold_set_v1_manifest.json")
DUAL_TRACK_PATH = Path("tmp/triage_phase1_output/triage_dual_track_v2.jsonl")
OUTPUT_REPORT_PATH = Path("tmp/gold_set_eval_report.json")

def load_json(p: Path) -> Any:
    with p.open("r", encoding="utf-8-sig") as f:
        return json.load(f)

def read_jsonl(p: Path) -> List[Dict[str, Any]]:
    rows = []
    with p.open("r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line.strip()))
    return rows

def compute_surface_id(r: Dict[str, Any]) -> str:
    if "surface_id" in r and r["surface_id"]:
        return r["surface_id"]
    from urllib.parse import urlparse
    m = str(r.get("method", "GET")).upper().strip()
    p = str(r.get("path", "")).strip()
    parsed = urlparse(p)
    h = parsed.hostname.lower() if (parsed.scheme and parsed.hostname) else "<unknown-host>"
    norm_p = parsed.path or "/"
    if parsed.scheme and parsed.hostname and parsed.query:
        norm_p = f"{norm_p}?{parsed.query}"
    payload = "\x1f".join([m, h, norm_p]).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:24]

def calc_confusion_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, Any]:
    prec = tp / max(1, (tp + fp))
    rec = tp / max(1, (tp + fn))
    f1 = (2 * prec * rec) / max(1e-6, (prec + rec))
    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
    }

def main():
    parser = argparse.ArgumentParser(description="Invar Phase-3: 独立黄金集双轨对决评估台 (Fail-Closed 混淆矩阵版)")
    parser.add_argument("--annotated", type=Path, default=ANNOTATED_PATH, help="标注真值卡片路径")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="Gold Set 清单路径")
    parser.add_argument("--dual-track", type=Path, default=DUAL_TRACK_PATH, help="比较器产出的 DualTrack 路径")
    parser.add_argument("--output-report", type=Path, default=OUTPUT_REPORT_PATH, help="评测物证 JSON 输出路径")
    parser.add_argument("--allow-defaults", action="store_true", help="是否允许静默 3.0 兜底 (违背宪法，默认关闭)")
    args = parser.parse_args()

    print("=" * 80)
    print(" ⚖️  Invar Phase-3: 黄金集真实业务解密与双轨对决评估台 (Fail-Closed 规范版)")
    print("=" * 80)

    if not args.annotated.is_file():
        print(f"[❌] 找不到标注真值文件: {args.annotated}")
        return 1
    if not args.manifest.is_file():
        print(f"[❌] 找不到解密清单钥匙: {args.manifest}")
        return 1
    if not args.dual_track.is_file():
        print(f"[❌] 找不到双轨记录文件: {args.dual_track}")
        return 1

    annotated_cards = read_jsonl(args.annotated)
    manifest = load_json(args.manifest)
    dual_track_rows = read_jsonl(args.dual_track)

    key_mappings = {m["card_id"]: m for m in manifest.get("key_mappings", [])}
    dual_track_by_surface = defaultdict(list)
    dual_track_by_endpoint = {}

    for r in dual_track_rows:
        sid = compute_surface_id(r)
        dual_track_by_surface[sid].append(r)
        epid = r.get("endpoint_id") or r.get("record_id")
        if epid:
            dual_track_by_endpoint[str(epid)] = r

    print(f"[*] 载入 {len(annotated_cards)} 张真值卡片与 DualTrack 数据，执行双轨度量对账...")

    per_pool_stats = defaultdict(lambda: {
        "count": 0,
        "neural_impact_err": [],
        "neural_sens_err": [],
        "gt_high_risk_count": 0,
        "rule_tp": 0, "rule_fp": 0, "rule_fn": 0, "rule_tn": 0,
        "neural_tp": 0, "neural_fp": 0, "neural_fn": 0, "neural_tn": 0,
        "discrepancy_verdicts": Counter(),
    })

    pool_b_drilldown = []
    matched_cards_count = 0
    default_cards = []

    for card in annotated_cards:
        cid = card["card_id"]
        meta = key_mappings.get(cid, {})
        pool = meta.get("pool_origin", "UNKNOWN")
        sid = card.get("surface_id") or meta.get("surface_id")
        gt_imp = card["annotation"]["ground_truth_impact"]
        gt_sens = card["annotation"]["ground_truth_sensitivity"]
        evidence = card["annotation"].get("semantic_evidence", "")

        dt_records = dual_track_by_surface.get(sid, [])
        first_r = dt_records[0] if dt_records else None
        if not first_r:
            for rid in meta.get("record_ids", []):
                if rid in dual_track_by_endpoint:
                    first_r = dual_track_by_endpoint[rid]
                    break

        if not first_r:
            default_cards.append(cid)
            first_r = {}
        else:
            matched_cards_count += 1

        neural_data = first_r.get("neural", {})
        rule_data = first_r.get("rule", {})
        n_imp = neural_data.get("impact_score") if neural_data.get("impact_score") is not None else 3.0
        n_sens = neural_data.get("sensitivity_score") if neural_data.get("sensitivity_score") is not None else 3.0
        r_high = bool(rule_data.get("high_risk_candidate", False))
        n_high = (n_imp >= 3.5 or n_sens >= 3.5)
        is_gt_high = (gt_imp >= 4 or gt_sens >= 4)

        stat = per_pool_stats[pool]
        stat["count"] += 1
        stat["neural_impact_err"].append(abs(n_imp - gt_imp))
        stat["neural_sens_err"].append(abs(n_sens - gt_sens))

        if is_gt_high:
            stat["gt_high_risk_count"] += 1

        # 规则轨标准混淆矩阵
        if is_gt_high and r_high:
            stat["rule_tp"] += 1
        elif not is_gt_high and r_high:
            stat["rule_fp"] += 1
        elif is_gt_high and not r_high:
            stat["rule_fn"] += 1
        else:
            stat["rule_tn"] += 1

        # 模型轨标准混淆矩阵
        if is_gt_high and n_high:
            stat["neural_tp"] += 1
        elif not is_gt_high and n_high:
            stat["neural_fp"] += 1
        elif is_gt_high and not n_high:
            stat["neural_fn"] += 1
        else:
            stat["neural_tn"] += 1

        # Pool B 语义冲突仲裁
        if pool == "POOL_B_DISCREPANCY":
            if n_high == is_gt_high and r_high != is_gt_high:
                verdict = "🏆 NEURAL_WINS (模型感知语义，纠正规则)"
            elif r_high == is_gt_high and n_high != is_gt_high:
                verdict = "🛡️ RULE_WINS (规则保底正确，模型偏离)"
            elif n_high == is_gt_high and r_high == is_gt_high:
                verdict = "🤝 BOTH_CORRECT (双轨达成共识)"
            else:
                verdict = "⚠️ BOTH_MISSED (双轨均未捕捉)"
            stat["discrepancy_verdicts"][verdict] += 1
            pool_b_drilldown.append({
                "card_id": cid,
                "surface": f"{card['method']} {card['path']}",
                "gt": f"I:{gt_imp}, S:{gt_sens}",
                "neural": f"I:{n_imp:.2f}, S:{n_sens:.2f}",
                "rule_high": r_high,
                "verdict": verdict,
                "evidence": evidence,
            })

    print(f"\n[📊 评估状态]: 匹配卡片数: {matched_cards_count}/{len(annotated_cards)} | 默认 3.0 兜底卡片数: {len(default_cards)}")

    # 🚨 宪法红线：Fail-Closed 熔断防御
    if default_cards and not args.allow_defaults:
        print(f"\n[❌ 契约熔断] 存在 {len(default_cards)} 张 Gold Card 未能物理对齐 ({default_cards[:5]}...)，严禁静默 3.0 兜底！", file=sys.stderr)
        return 2

    # 全局总混淆矩阵统计
    all_rule_tp = sum(s["rule_tp"] for s in per_pool_stats.values())
    all_rule_fp = sum(s["rule_fp"] for s in per_pool_stats.values())
    all_rule_fn = sum(s["rule_fn"] for s in per_pool_stats.values())
    all_rule_tn = sum(s["rule_tn"] for s in per_pool_stats.values())
    all_neural_tp = sum(s["neural_tp"] for s in per_pool_stats.values())
    all_neural_fp = sum(s["neural_fp"] for s in per_pool_stats.values())
    all_neural_fn = sum(s["neural_fn"] for s in per_pool_stats.values())
    all_neural_tn = sum(s["neural_tn"] for s in per_pool_stats.values())
    total_gt_high = sum(s["gt_high_risk_count"] for s in per_pool_stats.values())

    rule_overall = calc_confusion_metrics(all_rule_tp, all_rule_fp, all_rule_fn, all_rule_tn)
    neural_overall = calc_confusion_metrics(all_neural_tp, all_neural_fp, all_neural_fn, all_neural_tn)

    print("\n" + "=" * 80)
    print(" 🎯 全局双轨混淆矩阵与严格度量战报 (Global Standard Metrics):")
    print("=" * 80)
    print(f"  • 评测样本总量 (Surfaces) : {len(annotated_cards)} 个")
    print(f"  • 真实高危总量 (GT High)  : {total_gt_high} 个 (占比 {total_gt_high/max(1, len(annotated_cards))*100:.1f}%)")
    print("-" * 80)
    print(f"  【规则轨 (Rule Engine)】:")
    print(f"    ├─ 混淆矩阵 : TP={all_rule_tp}, FP={all_rule_fp}, FN={all_rule_fn}, TN={all_rule_tn}")
    print(f"    ├─ 准确率 (Precision): {rule_overall['precision']*100:.2f}%")
    print(f"    ├─ 召回率 (Recall)   : {rule_overall['recall']*100:.2f}%")
    print(f"    └─ F1 分数           : {rule_overall['f1_score']:.4f}")
    print("-" * 80)
    print(f"  【模型轨 (base-jev System 1)】:")
    print(f"    ├─ 混淆矩阵 : TP={all_neural_tp}, FP={all_neural_fp}, FN={all_neural_fn}, TN={all_neural_tn}")
    print(f"    ├─ 准确率 (Precision): {neural_overall['precision']*100:.2f}%")
    print(f"    ├─ 召回率 (Recall)   : {neural_overall['recall']*100:.2f}%")
    print(f"    └─ F1 分数           : {neural_overall['f1_score']:.4f}")
    print("=" * 80)

    # 机器可读物证落盘
    report_dict = {
        "schema_version": "invar.gold_set_evaluation.v2",
        "total_cards": len(annotated_cards),
        "total_gt_high": total_gt_high,
        "matched_cards": matched_cards_count,
        "default_cards_count": len(default_cards),
        "rule_metrics": rule_overall,
        "neural_metrics": neural_overall,
        "per_pool": {
            k: {
                "count": v["count"],
                "gt_high": v["gt_high_risk_count"],
                "rule_metrics": calc_confusion_metrics(v["rule_tp"], v["rule_fp"], v["rule_fn"], v["rule_tn"]),
                "neural_metrics": calc_confusion_metrics(v["neural_tp"], v["neural_fp"], v["neural_fn"], v["neural_tn"]),
                "avg_impact_mae": round(sum(v["neural_impact_err"]) / max(1, v["count"]), 4),
                "avg_sensitivity_mae": round(sum(v["neural_sens_err"]) / max(1, v["count"]), 4),
            } for k, v in per_pool_stats.items()
        }
    }
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.write_text(json.dumps(report_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [✓] 评测物证已固化落盘: {args.output_report.resolve()}")

    print("\n" + "=" * 80)
    print(" 🎉 Phase-3 黄金集评估完毕，混淆矩阵已完全规范！")
    print("=" * 80 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
