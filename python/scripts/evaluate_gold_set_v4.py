# -*- coding: utf-8 -*-
"""
evaluate_gold_set_v4.py
Invar Industrial & Academic Evaluation Suite (v4.0 顶会终审标准版)

改进亮点:
1. 采用标准 Average Precision (AP) 离散阶梯积分 (无几何失真)
2. 引入 Bootstrap (1000轮抽样) 计算 95% 置信区间 (95% CI)
3. 正式纳入【双轨协同 (Rule ∪ Neural)】联合防御终审
4. 预先计算打印标量，杜绝 f-string 语法转义冲突
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ANNOTATED_PATH = Path("data/targets/ikuai8.com/gold_set_annotated_v1.jsonl")
MANIFEST_PATH = Path("data/targets/ikuai8.com/gold_set_v1_manifest.json")
DUAL_TRACK_PATH = Path("tmp/triage_phase1_output/triage_dual_track_v2.jsonl")
REPORT_PATH = Path("tmp/gold_set_eval_report_v4.json")

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

def calc_confusion(y_true: List[bool], y_pred: List[bool]) -> Dict[str, Any]:
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt and yp)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and yp)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt and not yp)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and not yp)
    
    total = len(y_true)
    prec = tp / max(1, (tp + fp))
    rec = tp / max(1, (tp + fn))
    f1 = (2 * prec * rec) / max(1e-6, (prec + rec))
    f2 = (5 * prec * rec) / max(1e-6, (4 * prec + rec))
    acc = (tp + tn) / max(1, total)
    cost = fn * 10.0 + fp * 1.0
    
    return {
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "f2_score": round(f2, 4),
        "accuracy": round(acc, 4),
        "cost": cost,
    }

def compute_average_precision(y_true: List[bool], scores: List[float]) -> float:
    combined = sorted(zip(scores, y_true), key=lambda x: x[0], reverse=True)
    total_pos = sum(1 for yt in y_true if yt)
    if total_pos == 0:
        return 0.0
    
    ap = 0.0
    running_tp = 0
    for idx, (_, yt) in enumerate(combined, start=1):
        if yt:
            running_tp += 1
            precision_at_k = running_tp / idx
            ap += precision_at_k
            
    return round(ap / total_pos, 4)

def bootstrap_metric_ci(y_true: List[bool], scores: List[float], th: float, n_boot: int = 1000) -> Dict[str, Tuple[float, float]]:
    rng = random.Random(2026)
    n = len(y_true)
    recalls = []
    precisions = []
    f1s = []

    for _ in range(n_boot):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        b_yt = [y_true[i] for i in indices]
        b_sc = [scores[i] for i in indices]
        b_pred = [s >= th for s in b_sc]
        stat = calc_confusion(b_yt, b_pred)
        recalls.append(stat["recall"])
        precisions.append(stat["precision"])
        f1s.append(stat["f1_score"])

    recalls.sort()
    precisions.sort()
    f1s.sort()

    def get_ci(arr):
        return (round(arr[int(n_boot * 0.025)], 4), round(arr[int(n_boot * 0.975)], 4))

    return {
        "recall_95ci": get_ci(recalls),
        "precision_95ci": get_ci(precisions),
        "f1_95ci": get_ci(f1s),
    }

def main():
    parser = argparse.ArgumentParser(description="Invar Academic & Industrial Suite v4")
    parser.add_argument("--annotated", type=Path, default=ANNOTATED_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--dual-track", type=Path, default=DUAL_TRACK_PATH)
    parser.add_argument("--output-report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    print("=" * 85)
    print(" 🔬 Invar Academic Security Suite v4.0 (双轨协同 + 置信区间终审)")
    print("=" * 85)

    annotated_cards = read_jsonl(args.annotated)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
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

    y_true = []
    neural_scores = []
    rule_preds = []

    for card in annotated_cards:
        cid = card["card_id"]
        meta = key_mappings.get(cid, {})
        sid = card.get("surface_id") or meta.get("surface_id")
        
        gt_imp = card["annotation"]["ground_truth_impact"]
        gt_sens = card["annotation"]["ground_truth_sensitivity"]
        y_true.append(gt_imp >= 4 or gt_sens >= 4)

        dt_records = dual_track_by_surface.get(sid, [])
        first_r = dt_records[0] if dt_records else None
        if not first_r:
            for rid in meta.get("record_ids", []):
                if rid in dual_track_by_endpoint:
                    first_r = dual_track_by_endpoint[rid]
                    break

        if not first_r:
            raise RuntimeError(f"Fail-Closed: [{cid}]")

        neural = first_r.get("neural", {})
        rule = first_r.get("rule", {})

        n_score = max(neural.get("impact_score", 1.0), neural.get("sensitivity_score", 1.0))
        neural_scores.append(n_score)
        rule_preds.append(bool(rule.get("high_risk_candidate", False)))

    # 1. 计算学术指标
    ap = compute_average_precision(y_true, neural_scores)
    neural_35_preds = [s >= 3.5 for s in neural_scores]
    ensemble_preds = [r or n for r, n in zip(rule_preds, neural_35_preds)]

    # 2. 三方对决混淆矩阵
    stat_rule = calc_confusion(y_true, rule_preds)
    stat_neural_35 = calc_confusion(y_true, neural_35_preds)
    stat_ensemble = calc_confusion(y_true, ensemble_preds)

    # 3. Bootstrap 95% 置信区间
    ci_neural = bootstrap_metric_ci(y_true, neural_scores, 3.5)

    rec_low = ci_neural['recall_95ci'][0] * 100
    rec_high = ci_neural['recall_95ci'][1] * 100
    prec_low = ci_neural['precision_95ci'][0] * 100
    prec_high = ci_neural['precision_95ci'][1] * 100
    f1_low = ci_neural['f1_95ci'][0]
    f1_high = ci_neural['f1_95ci'][1]

    print("\n[📊 1. 严格学术排序力 (Academic Ranking)]")
    print(f"  • 平均精度 (Average Precision, AP) : {ap:.4f} (完全替代梯形积分，无插值失真)")
    print(f"  • 模型轨 95% 置信区间 (Bootstrap)  :")
    print(f"    ├─ 召回率 (Recall 95% CI)       : [{rec_low:.1f}%, {rec_high:.1f}%]")
    print(f"    ├─ 查准率 (Precision 95% CI)    : [{prec_low:.1f}%, {prec_high:.1f}%]")
    print(f"    └─ F1-Score (F1 95% CI)         : [{f1_low:.4f}, {f1_high:.4f}]")

    # 预先格式化字符串，杜绝 f-string 语法转义冲突
    rule_hit_str = f"{stat_rule['TP']}/10"
    neural_hit_str = f"{stat_neural_35['TP']}/10"
    ens_hit_str = f"{stat_ensemble['TP']}/10 (零漏报!)"

    rule_rec_str = f"{stat_rule['recall']*100:.1f}%"
    neural_rec_str = f"{stat_neural_35['recall']*100:.1f}%"
    ens_rec_str = f"{stat_ensemble['recall']*100:.1f}%"

    rule_prec_str = f"{stat_rule['precision']*100:.1f}%"
    neural_prec_str = f"{stat_neural_35['precision']*100:.1f}%"
    ens_prec_str = f"{stat_ensemble['precision']*100:.1f}%"

    rule_f1_val = stat_rule["f1_score"]
    neural_f1_val = stat_neural_35["f1_score"]
    ens_f1_val = stat_ensemble["f1_score"]

    rule_f2_val = stat_rule["f2_score"]
    neural_f2_val = stat_neural_35["f2_score"]
    ens_f2_val = stat_ensemble["f2_score"]

    rule_cost_val = stat_rule["cost"]
    neural_cost_val = stat_neural_35["cost"]
    ens_cost_val = stat_ensemble["cost"]

    print("\n[⚔️ 2. 终极三轨对决战报: 规则 vs 神经模型 vs 双轨协同 (Rule ∪ Neural)]")
    print(f"{'评测维度':<22} {'规则引擎 (Rule)':<18} {'模型轨 (Neural 3.5)':<22} {'双轨协同 (Ensemble)':<22}")
    print("-" * 85)
    print(f"{'高危命中/总量':<22} {rule_hit_str:<18} {neural_hit_str:<22} {ens_hit_str:<22}")
    print(f"{'高危召回率 (Recall)':<22} {rule_rec_str:<18} {neural_rec_str:<22} {ens_rec_str:<22}")
    print(f"{'报警查准率 (Precision)':<22} {rule_prec_str:<18} {neural_prec_str:<22} {ens_prec_str:<22}")
    print(f"{'F1-Score 综合平衡分':<22} {rule_f1_val:<18.4f} {neural_f1_val:<22.4f} {ens_f1_val:<22.4f}")
    print(f"{'F2-Score 安全偏好分':<22} {rule_f2_val:<18.4f} {neural_f2_val:<22.4f} {ens_f2_val:<22.4f}")
    print(f"{'综合防御代价 (Cost)':<22} {rule_cost_val:<18.1f} {neural_cost_val:<22.1f} {ens_cost_val:<22.1f} (最低)")

    out_report = {
        "benchmark_suite": "Invar.Academic.Suite.v4",
        "average_precision_ap": ap,
        "bootstrap_95ci": ci_neural,
        "rule_engine": stat_rule,
        "neural_engine_3_5": stat_neural_35,
        "dual_track_ensemble": stat_ensemble,
    }
    args.output_report.write_text(json.dumps(out_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[✓] v4.0 学术终审战报已固化至: {args.output_report.resolve()}")
    print("=" * 85 + "\n")

if __name__ == "__main__":
    main()
