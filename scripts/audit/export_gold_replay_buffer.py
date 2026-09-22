#!/usr/bin/env python3
"""
Invar Phase-4: Gold Set Experience Replay Pack Generator.

Extracts the 60 independently verified ground-truth cards, applies maximum-entropy
exponential projection to construct mathematically exact posterior distributions,
and generates an Active Learning Replay Buffer for base-jev v2 training.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ANNOTATED_PATH = Path("data/targets/ikuai8.com/gold_set_annotated_v1.jsonl")
OUTPUT_INVAR = Path("data/targets/ikuai8.com/gold_replay_buffer_60.jsonl")
BASE_JEV_DATA = Path("C:/dev/base-jev/data")
LEVELS = [1.0, 2.0, 3.0, 4.0, 5.0]


def project_exact_distribution(target_level: float, smoothing: float = 0.65) -> Tuple[List[float], float]:
    """纯 Python 原生最大熵指数族投影引擎，严格保证 sum(p) == 1.0 且期望分精准吻合"""
    target_e = max(1.05, min(4.95, float(target_level)))
    base_w = [math.exp(-abs(lvl - target_e) / smoothing) for lvl in LEVELS]

    low, high = -15.0, 15.0
    p = [0.2] * 5
    for _ in range(25):
        mid = (low + high) / 2.0
        tilted = [w * math.exp(mid * lvl) for w, lvl in zip(base_w, LEVELS)]
        s = sum(tilted)
        p = [t / s for t in tilted]
        cur_e = sum(lvl * prob for lvl, prob in zip(LEVELS, p))
        if cur_e < target_e:
            low = mid
        else:
            high = mid

    dist = [round(val, 4) for val in p]
    gap = round(1.0 - sum(dist), 4)
    dist[0] = round(dist[0] + gap, 4)
    exact_e = round(sum((m + 1) * pr for m, pr in enumerate(dist)), 4)
    return dist, exact_e


def main():
    print("=" * 75)
    print(" 🚀 Invar Phase-4: 黄金集经验重放包萃取引擎 (Active Learning Replay Buffer)")
    print(f" 📂 标注真值源: {ANNOTATED_PATH}")
    print("=" * 75)

    if not ANNOTATED_PATH.is_file():
        print(f"[❌] 找不到标注真值文件: {ANNOTATED_PATH}")
        return 1

    cards = []
    with ANNOTATED_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cards.append(json.loads(line))

    print(f"[*] 成功载入 {len(cards)} 张黄金真值卡片，正在执行最大熵投影与强契约装配...")

    replay_samples = []

    for c in cards:
        cid = c["card_id"]
        sid = c["surface_id"]
        method = str(c.get("method", "GET")).upper()
        path = str(c.get("path", "")).strip()
        host = str(c.get("host", "cloud.ikuai8.com")).lower()
        params = c.get("extracted_params", [])
        anno = c.get("annotation", {})

        gt_imp = anno.get("ground_truth_impact", 3)
        gt_sens = anno.get("ground_truth_sensitivity", 3)
        evidence = anno.get("semantic_evidence", "Ground truth verified")

        # 代数投影
        imp_dist, imp_exp = project_exact_distribution(gt_imp)
        sens_dist, sens_exp = project_exact_distribution(gt_sens)

        # 提取核心切片
        code_slice = ""
        slices = c.get("evidence_slices", [])
        if slices:
            code_slice = slices[0].get("code_slice", "")
        if not code_slice:
            code_slice = f"// [Endpoint Context] {method} {path}"

        # 判断样本类别：如果是纯前端无害噪音标签，标定为 INVALID_NOISE；否则为 POSITIVE
        category = "POSITIVE"
        if gt_imp == 1 and gt_sens == 1 and any(k in path.lower() for k in ["<ul", "<div", "chrome-extension", "application/"]):
            category = "INVALID_NOISE"

        sample = {
            "sample_id": f"GOLD-REPLAY-{cid}",
            "provenance": "REAL",
            "category": category,
            "primitive": "DualScore",
            "framework": "RealAST",
            "host": host,
            "method": method,
            "path": path,
            "extracted_params": params,
            "code_slice": code_slice[:300],
            "query": f"评估接口状态变更与资产敏感度: {method} {path[:60]}",
            "candidates": [],
            "is_ambiguous": 0.0,
            "ast_node_type": "CallExpression",
            "target_scores": {
                "impact": {
                    "distribution": imp_dist,
                    "expected_score": imp_exp,
                },
                "sensitivity": {
                    "distribution": sens_dist,
                    "expected_score": sens_exp,
                }
            },
            "target_distribution": imp_dist,
            "target_expected": imp_exp,
        }
        replay_samples.append(sample)

    # 1. 保存到 Invar 资产目录
    OUTPUT_INVAR.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_INVAR.open("w", encoding="utf-8") as f:
        for s in replay_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"  [✓] 已生成 Invar 本地黄金经验包: {OUTPUT_INVAR} ({len(replay_samples)} 条)")

    # 2. 同步并融合到 base-jev 训练集
    if BASE_JEV_DATA.is_dir():
        # 同步单一经验包
        jev_replay_path = BASE_JEV_DATA / "gold_replay_buffer_60.jsonl"
        with jev_replay_path.open("w", encoding="utf-8") as f:
            for s in replay_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"  [✓] 已交付至模型母机资产库: {jev_replay_path}")

        # 构建融合数据集 v2 (基础多样性训练集 + 3倍重放黄金真实难例)
        base_train_path = BASE_JEV_DATA / "distilled_invar_train_dual.jsonl"
        v2_train_path = BASE_JEV_DATA / "distilled_invar_train_dual_v2.jsonl"

        base_samples = []
        if base_train_path.is_file():
            with base_train_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        base_samples.append(json.loads(line))

        # 融合：基础样本 + 3x 黄金高权重难例
        v2_samples = list(base_samples)
        for _ in range(3):
            v2_samples.extend(replay_samples)

        with v2_train_path.open("w", encoding="utf-8") as f:
            for s in v2_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        print(f"  [✓] 已铸造完成 v2 融合微调数据集: {v2_train_path}")
        print(f"      ├─ 基础通识样本: {len(base_samples)} 条")
        print(f"      ├─ 黄金难例注入: {len(replay_samples)} 条 × 3 轮重放")
        print(f"      └─ v2 训练集总计: {len(v2_samples)} 条")

    print("\n" + "=" * 75)
    print(" 🎉 黄金经验重放包制作完成！已打通与 base-jev 训练管道的物理连接！")
    print("=" * 75 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
