from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# 确保定位到 python/packages/core/src
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "python" / "packages" / "core" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from harness.triage_dispatcher import TriageDispatcher, TriageTask


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Invar System-2 靶标任务装配与优先级调度器")
    parser.add_argument(
        "--pools",
        type=Path,
        default=REPO_ROOT / "artifacts" / "reports" / "triage_pools_v2.json",
        help="triage_pools_v2.json 路径",
    )
    parser.add_argument(
        "--dual-track",
        type=Path,
        default=REPO_ROOT / "tmp" / "triage_phase1_output" / "triage_dual_track_v2.jsonl",
        help="triage_dual_track_v2.jsonl 路径",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "artifacts" / "reports" / "targeted_research_tasks_78.json",
        help="装配后的科研任务清单输出路径",
    )
    parser.add_argument(
        "--target-pools",
        nargs="+",
        default=["pool_a_rule_must_keep", "pool_b_discrepancy"],
        help="需要消费的目标池，默认包含 Pool A 和 Pool B",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pools_path = args.pools.resolve()
    dual_track_path = args.dual_track.resolve()
    output_path = args.output.resolve()

    print("=" * 75)
    print(" 🎯 Invar System-2 靶向科研任务装配与分流调度器")
    print(f" 📂 靶标池清单: {pools_path}")
    print(f" 📂 双轨物理特征: {dual_track_path}")
    print(f" 💾 输出任务文件: {output_path}")
    print(f" 🎯 目标分流池: {args.target_pools}")
    print("=" * 75)

    if not pools_path.is_file():
        # 兼容性容错：检查 tmp/ 历史位置
        alt_pools = REPO_ROOT / "tmp" / "triage_phase1_output" / "triage_pools_v2.json"
        if alt_pools.is_file():
            pools_path = alt_pools
        else:
            print(f"[❌] 找不到靶标池文件: {pools_path}", file=sys.stderr)
            return 1

    if not dual_track_path.is_file():
        print(f"[❌] 找不到双轨数据文件: {dual_track_path}", file=sys.stderr)
        return 1

    dispatcher = TriageDispatcher(impact_threshold=3.5, sensitivity_threshold=3.5)
    tasks = dispatcher.assemble_from_files(
        pools_path=pools_path,
        dual_track_path=dual_track_path,
        target_pools=args.target_pools,
    )

    # 统计梯队分布
    priority_counts = Counter(t.priority for t in tasks)
    profile_counts = Counter(t.profile for t in tasks)
    hypothesis_counts = Counter(t.hypothesis_id or "NONE" for t in tasks)
    origin_counts = Counter(t.pool_origin for t in tasks)

    # 持久化输出
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "invar.targeted_research_tasks.v1",
        "total_tasks": len(tasks),
        "priority_breakdown": dict(priority_counts),
        "profile_breakdown": dict(profile_counts),
        "hypothesis_breakdown": dict(hypothesis_counts),
        "pool_breakdown": dict(origin_counts),
        "tasks": [t.to_dict() for t in tasks],
        "rust_tasks": [t.to_rust_task_dict() for t in tasks],
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] 成功装配靶标任务: {len(tasks)} 个")
    print(f"  ├─ 优先级分布: P0={priority_counts.get('P0', 0)} 个, P1={priority_counts.get('P1', 0)} 个, P2={priority_counts.get('P2', 0)} 个, P3={priority_counts.get('P3', 0)} 个")
    print(f"  ├─ 来源池构成: Pool A={origin_counts.get('POOL_A_RULE_MUST_KEEP', 0)} 个, Pool B={origin_counts.get('POOL_B_DISCREPANCY', 0)} 个")
    print(f"  └─ 假说分流: {dict(hypothesis_counts)}")

    print("\n[🎯 优先梯队预览 (前 8 个最高优先级任务)]:")
    for idx, t in enumerate(tasks[:8], 1):
        print(f"  {idx:02d}. [{t.priority}] [{t.pool_origin[:6]}] {t.method:<6} {t.path:<40} (I:{t.impact_score:.1f} S:{t.sensitivity_score:.1f}) -> 假说: {t.hypothesis_id}")

    print(f"\n[✓] 权威任务集已固化至: {output_path}")
    print("=" * 75 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
