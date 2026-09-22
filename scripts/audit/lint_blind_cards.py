import json
import sys
from pathlib import Path

CARDS_PATH = Path("data/targets/ikuai8.com/gold_set_candidates_v1.jsonl")

if not CARDS_PATH.is_file():
    print(f"[X] 文件不存在: {CARDS_PATH}", file=sys.stderr)
    sys.exit(1)

# 严禁向标注员暴露的泄密字段黑名单
FORBIDDEN_KEYS = {
    "risk_score", "risk_tags", "native_risk_score", "native_tags",
    "impact_score", "sensitivity_score", "impact_probs", "sensitivity_probs",
    "impact_entropy", "sensitivity_entropy", "mean_entropy",
    "discrepancy", "discrepancy_signals", "pool_origin", "active_learning_pool_hint",
    "rule", "neural", "rule_score", "neural_score"
}

card_ids = set()
surface_ids = set()
forbidden_hits = 0
cards_without_slice = 0
total_cards = 0

with CARDS_PATH.open("r", encoding="utf-8") as f:
    for line_idx, line in enumerate(f, 1):
        if not line.strip():
            continue
        total_cards += 1
        data = json.loads(line)
        
        cid = data.get("card_id")
        sid = data.get("surface_id")
        
        if cid:
            card_ids.add(cid)
        if sid:
            surface_ids.add(sid)
            
        # 递归或遍历顶层检查是否含有泄密键
        for k in data.keys():
            if k in FORBIDDEN_KEYS:
                forbidden_hits += 1
                
        slices = data.get("evidence_slices", [])
        if not slices:
            cards_without_slice += 1

print("=" * 60)
print(" Invar Phase-2 黄金盲卡轻量审计报告 (Blindness Lint)")
print("=" * 60)
print(f"card_count               = {total_cards}")
print(f"unique_card_id_count     = {len(card_ids)} (重复: {total_cards - len(card_ids)})")
print(f"unique_surface_id_count  = {len(surface_ids)} (重复: {total_cards - len(surface_ids)})")
print(f"forbidden_field_leaks    = {forbidden_hits} (要求必须为 0)")
print(f"cards_lacking_code_slice = {cards_without_slice} (要求必须为 0)")
print(f"all_cards_have_code_slice= {cards_without_slice == 0}")
print("=" * 60)
