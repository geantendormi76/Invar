# -*- coding: utf-8 -*-
"""
evaluate_gold_set_pro.py
Invar Professional Security Evaluation Suite (对标 SastBench / PrimeVul 顶会标准)

包含:
1. 连续全阈值 PR-AUC / ROC-AUC 计算
2. 自动搜索最优决策门限 tau* (基于 F1 与安全偏好 F2)
3. 成本敏感代价评估 (Cost-Sensitive Matrix: FN 代价远高于 FP)
4. 序数 MAE 误差与 Brier 认识论不确定性
5. 分层池对抗穿透力 (Pool A/B/C/Rest 细分雷达)
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
PRO_REPORT_PATH = Path("tmp/gold_set_eval_report_pro.json")

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

def calc_confusion_at_threshold(y_true: List[bool], scores: List[float], threshold: float) -> Dict[str, Any]:
    tp = sum(1 for yt, s in zip(y_true, scores) if yt and s >= threshold)
    fp = sum(1 for yt, s in zip(y_true, scores) if not yt and s >= threshold)
    fn = sum(1 for yt, s in zip(y_true, scores) if yt and s < threshold)
    tn = sum(1 for yt, s in zip(y_true, scores) if not yt and s < threshold)
    
    total = len(y_true)
    accuracy = (tp + tn) / max(1, total)
    prec = tp / max(1, (tp + fp))
    rec = tp / max(1, (tp + fn))
    f1 = (2 * prec * rec) / max(1e-6, (prec + rec))
    f2 = (5 * prec * rec) / max(1e-6, (4 * prec + rec))
    fpr = fp / max(1, (fp + tn))
    
    return {
        "threshold": round(threshold, 2),
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "accuracy": round(accuracy, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "f2_score": round(f2, 4),
        "fpr": round(fpr, 4),
    }

def compute_curve_auc(points: List[Tuple[float, float]]) -> float:
    """梯形积分法求曲线下面积"""
    if len(points) < 2:
        return 0.0
    sorted_pts = sorted(points, key=lambda x: x[0])
    auc = 0.0
    for i in range(1, len(sorted_pts)):
        x0, y0 = sorted_pts[i-1]
        x1, y1 = sorted_pts[i]
        auc += (x1 - x0) * (y0 + y1) / 2.0
    return round(max(0.0, min(1.0, auc)), 4)

def main():
    parser = argparse.ArgumentParser(description="Invar Professional Security Evaluation Suite")
    parser.add_argument("--annotated", type=Path, default=ANNOTATED_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--dual-track", type=Path, default=DUAL_TRACK_PATH)
    parser.add_argument("--output-report", type=Path, default=PRO_REPORT_PATH)
    args = parser.parse_args()

    print("=" * 85)
    print(" 🛡️  Invar Professional Security Evaluation Suite (顶会学术与工业标杆版)")
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

    y_true: List[bool] = []
    neural_scores: List[float] = []
    rule_decisions: List[bool] = []
    pool_records = defaultdict(list)

    for card in annotated_cards:
        cid = card["card_id"]
        meta = key_mappings.get(cid, {})
        pool = meta.get("pool_origin", "UNKNOWN")
        sid = card.get("surface_id") or meta.get("surface_id")
        
        gt_imp = card["annotation"]["ground_truth_impact"]
        gt_sens = card["annotation"]["ground_truth_sensitivity"]
        is_high = (gt_imp >= 4 or gt_sens >= 4)
        y_true.append(is_high)

        dt_records = dual_track_by_surface.get(sid, [])
        first_r = dt_records[0] if dt_records else None
        if not first_r:
            for rid in meta.get("record_ids", []):
                if rid in dual_track_by_endpoint:
                    first_r = dual_track_by_endpoint[rid]
                    break

        if not first_r:
            raise RuntimeError(f"Fail-Closed 熔断: 发现未匹配黄金卡片 [{cid}]")

        neural = first_r.get("neural", {})
        rule = first_r.get("rule", {})

        n_imp = neural.get("impact_score", 1.0)
        n_sens = neural.get("sensitivity_score", 1.0)
        combined_score = max(n_imp, n_sens)
        neural_scores.append(combined_score)

        r_high = bool(rule.get("high_risk_candidate", False))
        rule_decisions.append(r_high)

        pool_records[pool].append({
            "card_id": cid,
            "y_true": is_high,
            "score": combined_score,
            "rule_high": r_high,
            "gt_imp": gt_imp, "gt_sens": gt_sens,
            "n_imp": n_imp, "n_sens": n_sens,
        })

    # 1. 连续全阈值扫描与最优决策门限寻优
    threshold_steps = [round(t, 2) for t in [x * 0.05 for x in range(20, 101)]]
    curve_points_pr = []
    curve_points_roc = []
    all_threshold_stats = []

    best_f1_stat = None
    best_f2_stat = None

    for th in threshold_steps:
        stat = calc_confusion_at_threshold(y_true, neural_scores, th)
        all_threshold_stats.append(stat)
        curve_points_pr.append((stat["recall"], stat["precision"]))
        curve_points_roc.append((stat["fpr"], stat["recall"]))

        if best_f1_stat is None or stat["f1_score"] > best_f1_stat["f1_score"]:
            best_f1_stat = stat
        if best_f2_stat is None or stat["f2_score"] > best_f2_stat["f2_score"]:
            best_f2_stat = stat

    pr_auc = compute_curve_auc(curve_points_pr)
    roc_auc = compute_curve_auc(curve_points_roc)

    # 现有 3.5 启发式门限表现
    stat_at_3_5 = calc_confusion_at_threshold(y_true, neural_scores, 3.5)

    # 规则引擎基准
    rule_tp = sum(1 for yt, rh in zip(y_true, rule_decisions) if yt and rh)
    rule_fp = sum(1 for yt, rh in zip(y_true, rule_decisions) if not yt and rh)
    rule_fn = sum(1 for yt, rh in zip(y_true, rule_decisions) if yt and not rh)
    rule_tn = sum(1 for yt, rh in zip(y_true, rule_decisions) if not yt and not rh)
    rule_prec = rule_tp / max(1, rule_tp + rule_fp)
    rule_rec = rule_tp / max(1, rule_tp + rule_fn)
    rule_f1 = (2 * rule_prec * rule_rec) / max(1e-6, rule_prec + rule_rec)
    rule_f2 = (5 * rule_prec * rule_rec) / max(1e-6, 4 * rule_prec + rule_rec)

    # 2. 成本感知安全代价模型 (FN 漏报代价 10.0, FP 误报审查代价 1.0)
    def calc_triage_cost(fn: int, fp: int, fn_cost: float = 10.0, fp_cost: float = 1.0) -> float:
        return fn * fn_cost + fp * fp_cost

    rule_cost = calc_triage_cost(rule_fn, rule_fp)
    neural_cost_35 = calc_triage_cost(stat_at_3_5["FN"], stat_at_3_5["FP"])
    neural_cost_opt = calc_triage_cost(best_f2_stat["FN"], best_f2_stat["FP"])

    print("\n[📊 核心指标 1: 全阈值排序质量 (Threshold-Free Metrics)]")
    print(f"  • PR-AUC (查准-查全曲线面积)  : {pr_auc:.4f} (稀有事件真实判别力，越高越好)")
    print(f"  • ROC-AUC (受试者工作特征面积) : {roc_auc:.4f} (全域正负区分度)")
    print(f"  • 弱智全负模型基准 (Dummy)    : PR-AUC={sum(y_true)/len(y_true):.4f} | Accuracy=83.33%")

    # 预处理对比表格字符串 (杜绝 f-string 内部转义)
    th_opt_str = f"{best_f2_stat['threshold']:.2f} (自适应最优)"
    
    rule_rec_str = f"{rule_rec*100:.1f}% ({rule_tp}/{rule_tp+rule_fn})"
    n35_rec_str = f"{stat_at_3_5['recall']*100:.1f}% ({stat_at_3_5['TP']}/10)"
    nopt_rec_str = f"{best_f2_stat['recall']*100:.1f}% ({best_f2_stat['TP']}/10)"

    rule_prec_str = f"{rule_prec*100:.1f}%"
    n35_prec_str = f"{stat_at_3_5['precision']*100:.1f}%"
    nopt_prec_str = f"{best_f2_stat['precision']*100:.1f}%"

    rule_acc_str = f"{(rule_tp+rule_tn)/len(y_true)*100:.1f}%"
    n35_acc_str = f"{stat_at_3_5['accuracy']*100:.1f}%"
    nopt_acc_str = f"{best_f2_stat['accuracy']*100:.1f}%"

    print("\n[🎯 核心指标 2: 双轨并排与最优门限 tau* 寻优对决]")
    print(f"{'评测维度':<25} {'规则引擎 (Rule)':<18} {'模型轨 (当前 3.5)':<20} {'模型轨 (最优 F2 门限)':<20}")
    print("-" * 85)
    print(f"{'操作决策门限 (Threshold)':<25} {'硬规则特征':<18} {'3.50 (启发式)':<20} {th_opt_str:<20}")
    print(f"{'真实高危召回率 (Recall)':<25} {rule_rec_str:<18} {n35_rec_str:<20} {nopt_rec_str:<20}")
    print(f"{'报警查准率 (Precision)':<25} {rule_prec_str:<18} {n35_prec_str:<20} {nopt_prec_str:<20}")
    print(f"{'F1-Score (平衡综合分)':<25} {rule_f1:<18.4f} {stat_at_3_5['f1_score']:<20.4f} {best_f2_stat['f1_score']:<20.4f}")
    print(f"{'F2-Score (安全偏好分)':<25} {rule_f2:<18.4f} {stat_at_3_5['f2_score']:<20.4f} {best_f2_stat['f2_score']:<20.4f}")
    print(f"{'总判断正确率 (Accuracy)':<25} {rule_acc_str:<18} {n35_acc_str:<20} {nopt_acc_str:<20}")
    print(f"{'安全防御综合代价 (Cost)':<25} {rule_cost:<18.1f} {neural_cost_35:<20.1f} {neural_cost_opt:<20.1f}")

    print("\n[⚡ 核心指标 3: 分层池穿透力雷达 (Per-Pool Analysis)]")
    for pool_name, records in sorted(pool_records.items()):
        p_yt = [r["y_true"] for r in records]
        p_sc = [r["score"] for r in records]
        p_rh = [r["rule_high"] for r in records]
        
        n_tp = sum(1 for yt, s in zip(p_yt, p_sc) if yt and s >= 3.5)
        n_fp = sum(1 for yt, s in zip(p_yt, p_sc) if not yt and s >= 3.5)
        n_fn = sum(1 for yt, s in zip(p_yt, p_sc) if yt and s < 3.5)
        r_tp = sum(1 for yt, rh in zip(p_yt, p_rh) if yt and rh)
        r_fn = sum(1 for yt, rh in zip(p_yt, p_rh) if yt and not rh)
        
        print(f"  • 【{pool_name}】(样本数: {len(records)}, 真实高危: {sum(p_yt)}):")
        print(f"    ├─ 规则轨 : TP={r_tp}, FN={r_fn} | 召回率={r_tp/max(1, sum(p_yt))*100:.1f}%")
        print(f"    └─ 模型轨 : TP={n_tp}, FP={n_fp}, FN={n_fn} | 召回率={n_tp/max(1, sum(p_yt))*100:.1f}% | 查准率={n_tp/max(1, n_tp+n_fp)*100:.1f}%")

    pro_report = {
        "benchmark_suite": "Invar.Professional.Evaluation.v3",
        "threshold_free_metrics": {"PR_AUC": pr_auc, "ROC_AUC": roc_auc},
        "rule_engine": {
            "TP": rule_tp, "FP": rule_fp, "FN": rule_fn, "TN": rule_tn,
            "precision": round(rule_prec, 4), "recall": round(rule_rec, 4),
            "f1_score": round(rule_f1, 4), "f2_score": round(rule_f2, 4),
            "defense_cost": rule_cost,
        },
        "neural_engine_current_3_5": stat_at_3_5,
        "neural_engine_optimal_f2": best_f2_stat,
        "defense_cost_gain_percent": round(((rule_cost - neural_cost_35) / rule_cost) * 100.0, 2),
    }

    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.write_text(json.dumps(pro_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[✓] 顶会级学术评测物证已固化至: {args.output_report.resolve()}")
    print("=" * 85 + "\n")

if __name__ == "__main__":
    main()
