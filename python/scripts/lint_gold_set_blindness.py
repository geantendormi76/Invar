#!/usr/bin/env python3
"""
Invar Phase-2: Blindness & Integrity Linter for gold_set_candidates_v1.jsonl.

Verifies that the generated gold set candidate cards are 100% blind and safe
for annotation without leaking any model predictions, rule scores, or pool origins.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

CANDIDATES_PATH = Path("data/targets/ikuai8.com/gold_set_candidates_v1.jsonl")

# 绝对禁止出现在盲卡中的敏感泄漏字段集合
FORBIDDEN_KEYWORDS = {
    # 规则轨泄露
    "risk_score", "native_risk_score", "rule_score", "rule_tags", "rule_impact_proxy", "rule_sens_proxy",
    "risk-critical", "risk-high", "risk-medium", "risk-low",
    # 神经轨泄露
    "impact_score", "sensitivity_score", "impact_expected", "sensitivity_expected",
    "impact_probs", "sensitivity_probs", "impact_distribution", "sensitivity_distribution",
    "impact_entropy", "sensitivity_entropy", "mean_entropy", "neural_rank",
    # 池别与分歧信号泄露
    "pool_origin", "pool_a", "pool_b", "pool_c", "pool_consensus",
    "discrepancy_vector", "discrepancy_signals", "rule_candidate_neural_low_priority",
    "neural_candidate_rule_quiet", "rule_neural_agreement_zone",
}


def scan_obj_for_leakage(obj: Any, path: str = "") -> List[str]:
    leaks = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            k_lower = str(k).lower()
            if k_lower in FORBIDDEN_KEYWORDS or any(fk in k_lower for fk in ["risk", "neural", "pool_", "entropy"]):
                # 排除合法的 annotation 模板键
                if k not in ["annotation"]:
                    leaks.append(f"Forbidden key '{k}' at path: {path}")
            leaks.extend(scan_obj_for_leakage(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            leaks.extend(scan_obj_for_leakage(item, f"{path}[{idx}]"))
    elif isinstance(obj, str):
        # 检查文本中是否包含池别标记
        obj_lower = obj.lower()
        for forbidden in ["pool_a_rule_must_keep", "pool_b_discrepancy", "pool_c_exploration", "pool_consensus_rest"]:
            if forbidden in obj_lower:
                leaks.append(f"Forbidden string literal '{forbidden}' found in text at: {path}")
    return leaks


def main() -> int:
    print("=" * 70)
    print(" 🔍 Invar Phase-2: 盲卡文件完整性与盲态审计 (Blindness Lint)")
    print(f" 📂 待检文件: {CANDIDATES_PATH}")
    print("=" * 70)

    if not CANDIDATES_PATH.is_file():
        print(f"[❌] 错误: 文件不存在: {CANDIDATES_PATH}")
        return 1

    card_ids: List[str] = []
    surface_ids: Set[str] = set()
    cards_missing_slice = 0
    total_leaks: List[str] = []

    with CANDIDATES_PATH.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                card = json.loads(text)
            except json.JSONDecodeError as exc:
                print(f"[❌] 第 {line_no} 行 JSON 解析错误: {exc}")
                return 1

            cid = card.get("card_id")
            sid = card.get("surface_id")
            card_ids.append(cid)
            if sid:
                surface_ids.add(sid)

            # 检查代码切片是否存在
            slices = card.get("evidence_slices", [])
            if not slices or not any(s.get("code_slice") for s in slices):
                cards_missing_slice += 1

            # 深度递归检查信息泄漏
            leaks = scan_obj_for_leakage(card)
            if leaks:
                total_leaks.extend([f"Card {cid} (line {line_no}): {msg}" for msg in leaks])

    card_count = len(card_ids)
    duplicate_card_ids = card_count - len(set(card_ids))
    duplicate_surface_ids = card_count - len(surface_ids)

    print("\n[📊 盲态审计指标结果]:")
    print(f"  ├─ card_count                : {card_count} (要求: 60)")
    print(f"  ├─ duplicate_card_id         : {duplicate_card_ids} (要求: 0)")
    print(f"  ├─ duplicate_surface_id      : {duplicate_surface_ids} (要求: 0)")
    print(f"  ├─ cards_missing_code_slice  : {cards_missing_slice} (要求: 0)")
    print(f"  └─ information_leak_detected : {len(total_leaks)} (要求: 0)")

    if total_leaks:
        print("\n[🚨 发现违规泄漏字段 (前 5 项)]:")
        for leak in total_leaks[:5]:
            print(f"  • {leak}")

    success = (
        card_count == 60
        and duplicate_card_ids == 0
        and duplicate_surface_ids == 0
        and cards_missing_slice == 0
        and len(total_leaks) == 0
    )

    print("\n" + "=" * 70)
    print(f" 🎯 盲态审计结论: {'✅ 100% 绝对盲化，安全准予人工标注！' if success else '❌ 存在信息泄漏或格式缺陷，严禁开标！'}")
    print("=" * 70 + "\n")

    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(main())
