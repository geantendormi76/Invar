#!/usr/bin/env python3
"""
Invar Phase-2: Blind Stratified Gold Set v1 Generator.

Strict Experimental Contract:
  * Universe: 419 unique surface_id
  * Stratified Quotas: Pool A=20, Pool B=20, Pool C=10, Consensus=10 (Total 60)
  * Deterministic sampling without replacement (configurable seed)
  * Multi-record AST slice aggregation per surface_id with normalized-text deduplication
  * Absolute blindness: strips rule, neural, entropy, discrepancy, and pool metadata
  * Separate manifest key for post-annotation evaluation

Design notes:
  * Reads the potentially large dual-track JSONL in streaming passes; it never
    loads the full ~1.1 GB artifact into RAM.
  * Fails closed on identity/schema drift rather than silently fabricating IDs
    or source information.
  * Treats surface_id as the only research-surface identity key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

SCRIPT_VERSION = "0.3.0-phase2"
SCHEMA_VERSION = "invar.gold_set.candidates.v1"
EXPECTED_UNIVERSE = 419
EXPECTED_QUOTAS = {
    "POOL_A_RULE_MUST_KEEP": 20,
    "POOL_B_DISCREPANCY": 20,
    "POOL_C_EXPLORATION": 10,
    "POOL_CONSENSUS_REST": 10,
}


class GoldSetError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise GoldSetError(f"failed to read JSON: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise GoldSetError(f"invalid JSON: {path}: {exc}") from exc


def iter_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise GoldSetError(
                        f"invalid JSONL at {path}:{line_no}: {exc}"
                    ) from exc
                if not isinstance(obj, dict):
                    raise GoldSetError(
                        f"JSONL record must be object at {path}:{line_no}"
                    )
                yield line_no, obj
    except OSError as exc:
        raise GoldSetError(f"failed to read JSONL: {path}: {exc}") from exc


def normalized_slice_hash(text: str) -> str:
    # Collapse whitespace only. Do not alter punctuation or source tokens.
    compact = "".join(text.split())
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()[:16]


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return sorted({str(item).strip() for item in value if str(item).strip()})
    text = str(value).strip()
    return [text] if text else []


def validate_pool_contract(pools: dict[str, Any]) -> dict[str, set[str]]:
    required = {
        "pool_a_rule_must_keep": "POOL_A_RULE_MUST_KEEP",
        "pool_b_discrepancy": "POOL_B_DISCREPANCY",
        "pool_c_exploration": "POOL_C_EXPLORATION",
    }
    result: dict[str, set[str]] = {}
    for key, label in required.items():
        values = pools.get(key)
        if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
            raise GoldSetError(f"{key} must be a non-empty string array")
        result[label] = set(values)

    a, b, c = result.values()
    overlaps = (a & b) | (a & c) | (b & c)
    if overlaps:
        sample = sorted(overlaps)[:10]
        raise GoldSetError(f"Pool A/B/C overlap detected: {sample}")

    declared = {
        "POOL_A_RULE_MUST_KEEP": pools.get("pool_a_size_requested"),
        "POOL_B_DISCREPANCY": pools.get("pool_b_size_requested"),
        "POOL_C_EXPLORATION": pools.get("pool_c_size_requested"),
    }
    for label, expected in (("POOL_A_RULE_MUST_KEEP", 48), ("POOL_B_DISCREPANCY", 30), ("POOL_C_EXPLORATION", 30)):
        if len(result[label]) != expected:
            raise GoldSetError(f"{label} expected  {expected} surfaces, got {len(result[label])}")
        if declared[label] not in (None, expected):
            raise GoldSetError(f"{label} declared size mismatch: {declared[label]}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invar Phase-2 Blind Stratified Gold Set Generator"
    )
    parser.add_argument(
        "--pools",
        type=Path,
        default=Path("tmp/triage_phase1_output/triage_pools_v2.json"),
    )
    parser.add_argument(
        "--dual-track",
        type=Path,
        default=Path("tmp/triage_phase1_output/triage_dual_track_v2.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/targets/ikuai8.com"),
    )
    parser.add_argument("--seed", type=int, default=20260921)
    parser.add_argument("--quota-a", type=int, default=20)
    parser.add_argument("--quota-b", type=int, default=20)
    parser.add_argument("--quota-c", type=int, default=10)
    parser.add_argument("--quota-consensus", type=int, default=10)
    return parser.parse_args()


def resolve_input(path: Path, legacy_name: str) -> Path:
    if path.is_file():
        return path
    alt = path.parent / legacy_name
    if alt.is_file():
        return alt
    raise GoldSetError(f"input does not exist: {path}")


def first_pass_universe(
    dual_track_path: Path,
    pool_sets: dict[str, set[str]],
) -> tuple[set[str], dict[str, dict[str, Any]], int, dict[str, int]]:
    """Read only structural fields; avoid retaining giant code slices."""
    surfaces: set[str] = set()
    surface_meta: dict[str, dict[str, Any]] = {}
    record_count = 0
    status_counts: dict[str, int] = defaultdict(int)

    known_pool_membership = set().union(*pool_sets.values())

    for line_no, row in iter_jsonl(dual_track_path):
        record_count += 1
        sid = row.get("surface_id")
        rid = row.get("record_id")
        if not isinstance(sid, str) or not sid:
            raise GoldSetError(f"row {line_no}: missing surface_id")
        if not isinstance(rid, str) or not rid:
            raise GoldSetError(f"row {line_no}: missing record_id")

        surfaces.add(sid)
        code_status = str(row.get("code_slice_status", "MISSING"))
        status_counts[code_status] += 1

        entry = surface_meta.setdefault(
            sid,
            {
                "method": None,
                "host": None,
                "path": None,
                "record_ids": [],
                "extracted_params": set(),
            },
        )

        method = str(row.get("method", "")).upper().strip()
        host = str(row.get("host", "")).lower().strip()
        path = str(row.get("path", "")).strip()
        if entry["method"] is None:
            entry["method"] = method
            entry["host"] = host
            entry["path"] = path
        elif (entry["method"], entry["host"], entry["path"]) != (method, host, path):
            raise GoldSetError(
                f"surface_id {sid} maps to multiple method/host/path tuples at row {line_no}"
            )

        entry["record_ids"].append(rid)
        entry["extracted_params"].update(normalize_string_list(row.get("extracted_params")))

        # If a source is outside A/B/C it is potentially consensus; do not infer
        # pool membership from per-row fields, because that would weaken blindness.
        _ = known_pool_membership

    return surfaces, surface_meta, record_count, dict(status_counts)


def deterministic_sample(
    rng: random.Random,
    values: set[str],
    quota: int,
    label: str,
) -> list[str]:
    ordered = sorted(values)
    if len(ordered) < quota:
        raise GoldSetError(
            f"{label} has only {len(ordered)} surfaces; quota={quota} cannot be satisfied"
        )
    return rng.sample(ordered, quota)


def second_pass_collect(
    dual_track_path: Path,
    selected: set[str],
) -> dict[str, dict[str, Any]]:
    selected_data: dict[str, dict[str, Any]] = {
        sid: {
            "record_ids": [],
            "extracted_params": set(),
            "slices_by_hash": {},
            "missing_slice_rows": [],
        }
        for sid in selected
    }

    for line_no, row in iter_jsonl(dual_track_path):
        sid = row.get("surface_id")
        if sid not in selected_data:
            continue

        rid = str(row["record_id"])
        selected_data[sid]["record_ids"].append(rid)
        selected_data[sid]["extracted_params"].update(
            normalize_string_list(row.get("extracted_params"))
        )

        slice_text = row.get("code_slice")
        status = str(row.get("code_slice_status", "MISSING"))
        if not isinstance(slice_text, str) or not slice_text.strip() or status != "OK":
            selected_data[sid]["missing_slice_rows"].append(
                {"line": line_no, "record_id": rid, "status": status}
            )
            continue

        shash = normalized_slice_hash(slice_text.strip())
        if shash not in selected_data[sid]["slices_by_hash"]:
            selected_data[sid]["slices_by_hash"][shash] = {
                "record_id": rid,
                "source_file": row.get("source_file"),
                "source_line": row.get("source_line"),
                "code_slice": slice_text.strip(),
                "slice_hash": shash,
            }

    for sid, data in selected_data.items():
        if data["missing_slice_rows"]:
            sample = data["missing_slice_rows"][:3]
            raise GoldSetError(
                f"selected surface {sid} contains missing/non-OK code slices: {sample}"
            )
        if not data["slices_by_hash"]:
            raise GoldSetError(f"selected surface {sid} has no usable code_slice")

    return selected_data


def build_gold_cards(
    selected_by_origin: list[tuple[str, str]],
    surface_meta: dict[str, dict[str, Any]],
    selected_data: dict[str, dict[str, Any]],
    rng: random.Random,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    combined = list(selected_by_origin)
    rng.shuffle(combined)

    cards: list[dict[str, Any]] = []
    manifest_links: list[dict[str, Any]] = []

    for index, (sid, origin) in enumerate(combined, start=1):
        meta = surface_meta[sid]
        data = selected_data[sid]
        slices = list(data["slices_by_hash"].values())
        slices.sort(key=lambda x: (str(x.get("source_file")), int(x.get("source_line") or 0), x["slice_hash"]))

        card_id = f"GOLD-{index:02d}"
        evidence_slices = []
        for s_idx, info in enumerate(slices, start=1):
            evidence_slices.append(
                {
                    "slice_index": s_idx,
                    "record_id": info["record_id"],
                    "source_file": info.get("source_file"),
                    "source_line": info.get("source_line"),
                    "code_slice": info["code_slice"],
                }
            )

        # Strict blind card: only facts required for independent annotation.
        card = {
            "card_id": card_id,
            "surface_id": sid,
            "method": meta["method"],
            "host": meta["host"],
            "path": meta["path"],
            "extracted_params": sorted(data["extracted_params"]),
            "associated_record_count": len(data["record_ids"]),
            "evidence_slices": evidence_slices,
            "annotation": {
                "ground_truth_impact": None,
                "ground_truth_sensitivity": None,
                "semantic_evidence": "",
                "annotator_confidence": None,
            },
        }
        cards.append(card)

        manifest_links.append(
            {
                "card_id": card_id,
                "surface_id": sid,
                "pool_origin": origin,
                "record_ids": list(meta["record_ids"]),
                "slice_hashes": [info["slice_hash"] for info in slices],
            }
        )

    return cards, manifest_links


def sha256_jsonl(path: Path) -> str:
    return sha256_file(path)


def main() -> int:
    args = parse_args()

    pools_path = resolve_input(args.pools, "triage_pools.json")
    dual_path = resolve_input(args.dual_track, "triage_dual_track.jsonl")

    if args.quota_a != EXPECTED_QUOTAS["POOL_A_RULE_MUST_KEEP"]:
        raise GoldSetError("Phase-2 contract requires quota-a=20")
    if args.quota_b != EXPECTED_QUOTAS["POOL_B_DISCREPANCY"]:
        raise GoldSetError("Phase-2 contract requires quota-b=20")
    if args.quota_c != EXPECTED_QUOTAS["POOL_C_EXPLORATION"]:
        raise GoldSetError("Phase-2 contract requires quota-c=10")
    if args.quota_consensus != EXPECTED_QUOTAS["POOL_CONSENSUS_REST"]:
        raise GoldSetError("Phase-2 contract requires quota-consensus=10")

    print("=" * 78)
    print(f"Invar Phase-2 Blind Stratified Gold Set Generator {SCRIPT_VERSION}")
    print(f"Seed: {args.seed}")
    print("Quotas: A=20 B=20 C=10 Consensus=10 (total=60)")
    print("=" * 78)

    pools_data = load_json(pools_path)
    if not isinstance(pools_data, dict):
        raise GoldSetError("pool file root must be an object")
    pool_sets = validate_pool_contract(pools_data)

    print(f"[INPUT] pools       : {pools_path}")
    print(f"[INPUT] dual-track  : {dual_path}")

    pools_hash = sha256_file(pools_path)
    dual_hash = sha256_file(dual_path)
    print(f"[HASH]  pools      : {pools_hash}")
    print(f"[HASH]  dual-track : {dual_hash}")

    t0 = time.perf_counter()
    surfaces, surface_meta, record_count, status_counts = first_pass_universe(
        dual_path, pool_sets
    )

    if len(surfaces) != EXPECTED_UNIVERSE:
        raise GoldSetError(
            f"unique surface universe mismatch: expected {EXPECTED_UNIVERSE}, got {len(surfaces)}"
        )

    for label, members in pool_sets.items():
        missing = members - surfaces
        if missing:
            raise GoldSetError(
                f"{label} contains surface_ids absent from dual-track universe: {sorted(missing)[:10]}"
            )

    prioritized = set().union(*pool_sets.values())
    consensus = surfaces - prioritized
    if len(consensus) != 311:
        raise GoldSetError(f"consensus universe mismatch: expected 311, got {len(consensus)}")

    print(f"[PASS] dual-track records : {record_count}")
    print(f"[PASS] unique surfaces    : {len(surfaces)}")
    print(f"[PASS] consensus surfaces  : {len(consensus)}")
    print(f"[PASS] code-slice statuses : {status_counts}")

    rng = random.Random(args.seed)
    sampled_a = deterministic_sample(rng, pool_sets["POOL_A_RULE_MUST_KEEP"], args.quota_a, "Pool A")
    sampled_b = deterministic_sample(rng, pool_sets["POOL_B_DISCREPANCY"], args.quota_b, "Pool B")
    sampled_c = deterministic_sample(rng, pool_sets["POOL_C_EXPLORATION"], args.quota_c, "Pool C")
    sampled_consensus = deterministic_sample(rng, consensus, args.quota_consensus, "Consensus")

    sampled_pairs = (
        [(sid, "POOL_A_RULE_MUST_KEEP") for sid in sampled_a]
        + [(sid, "POOL_B_DISCREPANCY") for sid in sampled_b]
        + [(sid, "POOL_C_EXPLORATION") for sid in sampled_c]
        + [(sid, "POOL_CONSENSUS_REST") for sid in sampled_consensus]
    )
    selected = {sid for sid, _ in sampled_pairs}
    if len(selected) != 60:
        raise GoldSetError(f"selected unique surface count is {len(selected)}, expected 60")

    print(f"[SAMPLE] A          : {len(sampled_a)}")
    print(f"[SAMPLE] B          : {len(sampled_b)}")
    print(f"[SAMPLE] C          : {len(sampled_c)}")
    print(f"[SAMPLE] Consensus  : {len(sampled_consensus)}")
    print(f"[SAMPLE] Total      : {len(selected)}")

    selected_data = second_pass_collect(dual_path, selected)
    cards, manifest_links = build_gold_cards(
        sampled_pairs, surface_meta, selected_data, rng
    )

    if len(cards) != 60 or len(manifest_links) != 60:
        raise GoldSetError("gold-set cardinality validation failed")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cards_path = args.output_dir / "gold_set_candidates_v1.jsonl"
    manifest_path = args.output_dir / "gold_set_v1_manifest.json"

    with cards_path.open("w", encoding="utf-8", newline="\n") as handle:
        for card in cards:
            handle.write(json.dumps(card, ensure_ascii=False, separators=(",", ":")) + "\n")

    cards_hash = sha256_jsonl(cards_path)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "script_version": SCRIPT_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frozen_experiment_contract": {
            "model_state": "FROZEN_BASE_JEV_V1",
            "comparator_state": "FROZEN_COMPARATOR_V0_2",
            "no_tuning_permitted_on_gold_set": True,
            "research_efficiency_gain": "NOT_MEASURED_IN_PHASE_1",
            "surface_search_space_reduction": "74.2% ((419 - 108) / 419)",
        },
        "inputs": {
            "pools_path": str(pools_path),
            "pools_sha256": pools_hash,
            "dual_track_path": str(dual_path),
            "dual_track_sha256": dual_hash,
        },
        "sampling_protocol": {
            "deterministic_seed": args.seed,
            "sampling_method": "stratified_without_replacement",
            "universe_surfaces": len(surfaces),
            "quotas": dict(EXPECTED_QUOTAS),
            "total_sampled": len(cards),
            "pool_sizes": {
                "POOL_A_RULE_MUST_KEEP": len(pool_sets["POOL_A_RULE_MUST_KEEP"]),
                "POOL_B_DISCREPANCY": len(pool_sets["POOL_B_DISCREPANCY"]),
                "POOL_C_EXPLORATION": len(pool_sets["POOL_C_EXPLORATION"]),
                "POOL_CONSENSUS_REST": len(consensus),
            },
        },
        "output": {
            "cards_path": str(cards_path),
            "cards_sha256": cards_hash,
            "card_count": len(cards),
        },
        "source_slice_status": status_counts,
        "key_mappings": manifest_links,
    }

    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    total_ms = (time.perf_counter() - t0) * 1000.0
    print("=" * 78)
    print("PHASE-2 GOLD SET GENERATED")
    print(f"Cards    : {cards_path.resolve()}")
    print(f"Manifest : {manifest_path.resolve()}")
    print(f"Cards SHA: {cards_hash}")
    print(f"Elapsed  : {total_ms:.2f} ms")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GoldSetError as exc:
        print(f"[X] {exc}", file=sys.stderr)
        raise SystemExit(2)
    except KeyboardInterrupt:
        print("[STOP] interrupted", file=sys.stderr)
        raise SystemExit(130)
