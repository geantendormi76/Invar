#!/usr/bin/env python3
"""
Invar Phase-1 dual-track comparator v0.2

Key correction from v0.1:
- `endpoint_id` is NOT treated as a unique primary key.
- Report rows and neural predictions are aligned by physical row order, with
  endpoint_id equality checked as an integrity assertion.
- Each AST record gets a unique `record_id`.
- Each concrete research surface gets a deterministic `surface_id`.
- Pool A/B/C are deduplicated at surface level, while the full observation
  corpus keeps every AST record.
- Neural fallback rows (e.g. oversize-token fallback) remain in coverage but
  are excluded from neural ranking / entropy / Pool B/C evidence.

Read-only. No network requests. No Invar Core mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence
from urllib.parse import urlparse

SCRIPT_VERSION = "0.2.0-phase1"
SCHEMA_VERSION = "invar.triage.dual-track.v2"


class ComparatorError(RuntimeError):
    pass


@dataclass
class TimingSeries:
    values_ms: list[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        self.values_ms.append(float(value))

    def summary(self) -> dict[str, float | int | None]:
        if not self.values_ms:
            return {"count": 0, "mean_ms": None, "p50_ms": None, "p95_ms": None, "p99_ms": None}
        values = sorted(self.values_ms)

        def pct(p: float) -> float:
            if len(values) == 1:
                return values[0]
            k = (len(values) - 1) * p
            lo = math.floor(k)
            hi = math.ceil(k)
            if lo == hi:
                return values[lo]
            return values[lo] * (hi - k) + values[hi] * (k - lo)

        return {
            "count": len(values),
            "mean_ms": statistics.fmean(values),
            "p50_ms": pct(0.50),
            "p95_ms": pct(0.95),
            "p99_ms": pct(0.99),
        }


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def stable_id(*parts: Any) -> str:
    payload = "\x1f".join("" if p is None else str(p) for p in parts).encode("utf-8")
    return sha256_bytes(payload)[:24]


def raw_js_manifest_hash(root: Path) -> str:
    if not root.exists() or not root.is_dir():
        raise ComparatorError(f"raw_js root does not exist or is not directory: {root}")
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        h.update(rel + b"\0" + sha256_file(path).encode("ascii") + b"\n")
    return h.hexdigest()


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except OSError as exc:
        raise ComparatorError(f"failed to read JSON: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ComparatorError(f"invalid JSON: {path}: {exc}") from exc


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ComparatorError(f"invalid JSONL {path}:{line_no}: {exc}") from exc
                if not isinstance(obj, dict):
                    raise ComparatorError(f"JSONL record must be object {path}:{line_no}")
                rows.append(obj)
    except OSError as exc:
        raise ComparatorError(f"failed to read JSONL: {path}: {exc}") from exc
    return rows


def first(mapping: Mapping[str, Any], keys: Sequence[str], default: Any = None) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def normalize_params(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value]
    return [str(value)]


def normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return sorted({str(x) for x in value})
    return [str(value)]


def make_surface_id(method: str, path: str) -> str:
    parsed = urlparse(path)
    if parsed.scheme and parsed.hostname:
        host = parsed.hostname.lower()
        normalized_path = parsed.path or "/"
    else:
        host = "<unknown-host>"
        normalized_path = path or "/"
    # Query is intentionally retained in the surface identity only when the
    # extracted endpoint itself is explicitly a URL with a query. This preserves
    # the existing EndpointIR semantics without fabricating URL normalization.
    if parsed.scheme and parsed.hostname and parsed.query:
        normalized_path = f"{normalized_path}?{parsed.query}"
    return stable_id(method.upper(), host, normalized_path)


def normalize_endpoints(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = report.get("endpoints")
    if not isinstance(raw, list):
        raise ComparatorError("report must contain endpoints[]")

    out: list[dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ComparatorError(f"endpoint[{idx}] is not object")
        legacy_id = first(item, ["endpoint_id", "id"])
        method = str(first(item, ["method"], "GET")).upper()
        path = str(first(item, ["path"], ""))
        if not legacy_id:
            raise ComparatorError(f"endpoint[{idx}] missing endpoint_id")
        source_file = first(item, ["source_file"])
        source_line = first(item, ["line", "source_line"])
        params = normalize_params(first(item, ["extracted_params", "params"], []))
        tags = normalize_tags(first(item, ["tags"], []))
        record_id = stable_id(
            idx,
            method,
            path,
            source_file,
            source_line,
            first(item, ["call_signature"]),
            "|".join(params),
        )
        surface_id = make_surface_id(method, path)
        out.append({
            "record_index": idx,
            "record_id": record_id,
            "surface_id": surface_id,
            "endpoint_id": str(legacy_id),
            "method": method,
            "path": path,
            "source_file": source_file,
            "source_line": source_line,
            "is_dynamic": bool(first(item, ["is_dynamic"], False)),
            "extracted_params": params,
            "tags": tags,
            "risk_score": first(item, ["risk_score"]),
            "confidence": first(item, ["confidence"]),
            "call_signature": first(item, ["call_signature"]),
        })
    return out


def locate_source_file(raw_root: Path, source_file: Any) -> Path | None:
    if source_file is None:
        return None
    candidate = Path(str(source_file))
    if candidate.is_absolute() and candidate.exists():
        return candidate
    rel = raw_root / str(source_file)
    if rel.exists():
        return rel
    matches = list(raw_root.rglob(candidate.name))
    return matches[0] if len(matches) == 1 else None


def extract_code_slice(raw_root: Path, source_file: Any, source_line: Any, radius: int) -> tuple[str | None, str]:
    path = locate_source_file(raw_root, source_file)
    if path is None:
        return None, "SOURCE_FILE_NOT_FOUND"
    try:
        line_no = max(1, int(source_line)) if source_line is not None else 1
    except (TypeError, ValueError):
        line_no = 1
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None, "SOURCE_READ_ERROR"
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return "\n".join(lines[start - 1:end]), "OK"


def load_http_hosts(path: Path | None) -> tuple[set[str], int]:
    if path is None:
        return set(), 0
    hosts: set[str] = set()
    rows = read_jsonl(path)
    for record in rows:
        url = first(record, ["url", "input", "final_url"])
        if isinstance(url, str) and url:
            try:
                host = urlparse(url).hostname
            except ValueError:
                host = None
            if host:
                hosts.add(host.lower())
    return hosts, len(rows)


def entropy_from_probs(value: Any) -> float | None:
    if not isinstance(value, list) or len(value) != 5:
        return None
    try:
        probs = [float(x) for x in value]
    except (TypeError, ValueError):
        return None
    if any((not math.isfinite(x)) or x < 0 for x in probs):
        return None
    total = sum(probs)
    if total <= 0 or not math.isfinite(total):
        return None
    probs = [x / total for x in probs]
    return -sum(p * math.log(p) for p in probs if p > 0)


def score(value: Any, name: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise ComparatorError(f"{name} must be numeric: {value!r}") from exc
    if not math.isfinite(x) or not 1.0 <= x <= 5.0:
        raise ComparatorError(f"{name} outside [1,5]: {x}")
    return x


def validate_prediction_rows(predictions: list[dict[str, Any]], endpoints: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    if len(predictions) != len(endpoints):
        raise ComparatorError(
            f"row-count mismatch: report={len(endpoints)}, neural={len(predictions)}. "
            "For Phase 1, predictions must preserve 1:1 row alignment with the report."
        )

    aligned: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for idx, (pred, endpoint) in enumerate(zip(predictions, endpoints)):
        pred_id = str(first(pred, ["endpoint_id", "id"], ""))
        expected_id = endpoint["endpoint_id"]
        if pred_id != expected_id:
            mismatches.append(f"row {idx}: report={expected_id!r} neural={pred_id!r}")
        impact = score(first(pred, ["impact_score", "impact_expected", "impact"]), "impact_score")
        sensitivity = score(first(pred, ["sensitivity_score", "sensitivity_expected", "sensitivity"]), "sensitivity_score")
        impact_probs = first(pred, ["impact_probs", "impact_distribution"])
        sensitivity_probs = first(pred, ["sensitivity_probs", "sensitivity_distribution"])
        provenance = str(first(pred, ["runner_provenance"], ""))
        fallback = any(token in provenance.lower() for token in ("fallback", "oversize", "truncated", "exception"))
        aligned.append({
            "impact_score": impact,
            "sensitivity_score": sensitivity,
            "impact_probs": impact_probs,
            "sensitivity_probs": sensitivity_probs,
            "impact_entropy": entropy_from_probs(impact_probs),
            "sensitivity_entropy": entropy_from_probs(sensitivity_probs),
            "latency_ms": first(pred, ["latency_ms"]),
            "model_version": first(pred, ["model_version"]),
            "runner_provenance": provenance,
            "neural_usable": not fallback,
        })
    if mismatches:
        raise ComparatorError(
            "report/prediction row alignment mismatch (first 5): " + "; ".join(mismatches[:5])
        )
    return aligned, mismatches


def native_rule_profile(endpoint: Mapping[str, Any], observed_hosts: set[str]) -> dict[str, Any]:
    tags = set(endpoint["tags"])
    path = str(endpoint["path"])
    parsed = urlparse(path)
    host = parsed.hostname.lower() if parsed.hostname else None
    return {
        "high_risk_candidate": bool(tags.intersection({"risk-critical", "risk-high"})),
        "state_changing": "state-changing" in tags,
        "destructive": "destructive" in tags,
        "sensitive_route": "sensitive-route" in tags,
        "sensitive_params": "sensitive-params" in tags,
        "observed_host": bool(host and host in observed_hosts),
        "native_risk_score": endpoint["risk_score"],
        "native_tags": sorted(tags),
        "method": endpoint["method"],
    }


def representative_score(row: dict[str, Any]) -> tuple[float, float, int, float, str]:
    neural = row["neural"]
    return (
        max(neural["impact_score"], neural["sensitivity_score"]),
        neural["sensitivity_score"],
        len(row["extracted_params"]),
        float(row["rule"]["native_risk_score"] or 0.0),
        row["record_id"],
    )


def build_surface_representatives(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["neural"]["neural_usable"]:
            groups.setdefault(row["surface_id"], []).append(row)
    reps: dict[str, dict[str, Any]] = {}
    for surface_id, group in groups.items():
        reps[surface_id] = max(group, key=representative_score)
    return reps


def assign_surface_ranks(reps: dict[str, dict[str, Any]]) -> dict[str, tuple[int, int]]:
    impact_order = sorted(reps.items(), key=lambda kv: (-kv[1]["neural"]["impact_score"], kv[0]))
    sens_order = sorted(reps.items(), key=lambda kv: (-kv[1]["neural"]["sensitivity_score"], kv[0]))
    impact_rank = {sid: i + 1 for i, (sid, _) in enumerate(impact_order)}
    sens_rank = {sid: i + 1 for i, (sid, _) in enumerate(sens_order)}
    return {sid: (impact_rank[sid], sens_rank[sid]) for sid in reps}


def classify_signal(row: dict[str, Any], surface_rank: tuple[int, int] | None, total_surfaces: int, top_k: int) -> list[str]:
    signals: list[str] = []
    rule = row["rule"]
    neural = row["neural"]
    if not neural["neural_usable"]:
        return ["NEURAL_FALLBACK_EXCLUDED"]
    high_rule = bool(rule["high_risk_candidate"])
    if surface_rank is None:
        return ["NEURAL_NOT_RANKED"]
    impact_rank, sens_rank = surface_rank
    top_neural = impact_rank <= top_k or sens_rank <= top_k
    if high_rule and not top_neural:
        signals.append("RULE_CANDIDATE_NEURAL_LOW_PRIORITY")
    if top_neural and not high_rule:
        signals.append("NEURAL_CANDIDATE_RULE_QUIET")
    entropy_values = [neural["impact_entropy"], neural["sensitivity_entropy"]]
    valid = [x for x in entropy_values if x is not None]
    if valid:
        mean_entropy = statistics.fmean(valid)
        max_entropy = math.log(5.0)
        if mean_entropy >= 0.75 * max_entropy:
            signals.append("NEURAL_HIGH_ENTROPY")
        elif mean_entropy <= 0.35 * max_entropy:
            signals.append("NEURAL_LOW_ENTROPY")
    if high_rule and top_neural:
        signals.append("RULE_NEURAL_AGREEMENT_ZONE")
    if neural["impact_score"] + 0.5 < neural["sensitivity_score"]:
        signals.append("NEURAL_CROSS_DIMENSION_SENSITIVITY_LEAN")
    elif neural["sensitivity_score"] + 0.5 < neural["impact_score"]:
        signals.append("NEURAL_CROSS_DIMENSION_IMPACT_LEAN")
    if not signals:
        signals.append("NO_STRONG_DISCREPANCY_SIGNAL")
    return signals


def best_pool_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        rows,
        key=lambda r: (
            int(r["rule"]["high_risk_candidate"]),
            max(r["neural"]["impact_score"], r["neural"]["sensitivity_score"]) if r["neural"]["neural_usable"] else -1.0,
            len(r["extracted_params"]),
            float(r["rule"]["native_risk_score"] or 0.0),
            r["record_id"],
        ),
    )


def build_pools(rows: list[dict[str, Any]], pool_b_size: int, pool_c_size: int, top_k: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_surface: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_surface.setdefault(row["surface_id"], []).append(row)

    reps_all = {sid: best_pool_row(group) for sid, group in by_surface.items()}
    pool_a = [r for r in reps_all.values() if r["rule"]["high_risk_candidate"]]

    excluded = {r["surface_id"] for r in pool_a}
    pool_b_candidates = [
        r for r in reps_all.values()
        if r["surface_id"] not in excluded
        and r["neural"]["neural_usable"]
        and any(s in r["discrepancy_signals"] for s in (
            "NEURAL_CANDIDATE_RULE_QUIET",
            "NEURAL_HIGH_ENTROPY",
            "NEURAL_CROSS_DIMENSION_SENSITIVITY_LEAN",
            "NEURAL_CROSS_DIMENSION_IMPACT_LEAN",
        ))
    ]
    pool_b_candidates.sort(key=lambda r: (
        int("NEURAL_CANDIDATE_RULE_QUIET" in r["discrepancy_signals"]),
        int("NEURAL_HIGH_ENTROPY" in r["discrepancy_signals"]),
        int(len(r["extracted_params"]) > 0),
        max(r["neural"]["impact_score"], r["neural"]["sensitivity_score"]),
    ), reverse=True)
    pool_b = pool_b_candidates[:pool_b_size]
    excluded |= {r["surface_id"] for r in pool_b}

    pool_c_candidates = [
        r for r in reps_all.values()
        if r["surface_id"] not in excluded and r["neural"]["neural_usable"]
    ]
    pool_c_candidates.sort(key=lambda r: (
        int(r["rule"]["sensitive_params"]),
        len(r["extracted_params"]),
        int(r["rule"]["observed_host"]),
        int(r["rule"]["sensitive_route"]),
        r["surface_id"],
    ), reverse=True)
    pool_c = pool_c_candidates[:pool_c_size]
    return pool_a, pool_b, pool_c


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Invar read-only Phase-1 dual-track comparator v0.2")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--report", type=Path, required=False)
    p.add_argument("--raw-js", type=Path, required=False)
    p.add_argument("--http-surface", type=Path)
    p.add_argument("--neural-jsonl", type=Path)
    p.add_argument("--output-dir", type=Path, required=False)
    p.add_argument("--code-radius", type=int, default=40)
    p.add_argument("--pool-b-size", type=int, default=30)
    p.add_argument("--pool-c-size", type=int, default=30)
    p.add_argument("--neural-top-k", type=int, default=30)
    return p.parse_args()


def run_self_test() -> None:
    assert entropy_from_probs([0.1, 0.2, 0.3, 0.2, 0.2]) is not None
    assert stable_id("a", "b") == stable_id("a", "b")
    report = {"endpoints": [{"endpoint_id": "GET:/a", "method": "GET", "path": "/a", "source_file": "x.js", "line": 1}]}
    eps = normalize_endpoints(report)
    preds = [{"endpoint_id": "GET:/a", "impact_score": 2, "sensitivity_score": 3, "impact_probs": [1,0,0,0,0], "sensitivity_probs": [0,0,1,0,0]}]
    aligned, _ = validate_prediction_rows(preds, eps)
    assert aligned[0]["neural_usable"]
    print("SELF_TEST_OK")


def main() -> int:
    args = parse_args()
    if args.self_test:
        run_self_test()
        return 0
    if not args.report or not args.raw_js or not args.output_dir:
        raise ComparatorError("--report, --raw-js and --output-dir are required outside --self-test")

    if not args.neural_jsonl:
        raise ComparatorError("Phase 1 requires --neural-jsonl")
    for p in (args.report, args.raw_js, args.neural_jsonl):
        if not p.exists():
            raise ComparatorError(f"input does not exist: {p}")
    if args.http_surface and not args.http_surface.exists():
        raise ComparatorError(f"http surface does not exist: {args.http_surface}")

    total_timer = time.perf_counter()
    report = load_json(args.report)
    if not isinstance(report, dict):
        raise ComparatorError("report root must be object")
    endpoints = normalize_endpoints(report)
    predictions = read_jsonl(args.neural_jsonl)
    neural_rows, _ = validate_prediction_rows(predictions, endpoints)

    manifest_hash = raw_js_manifest_hash(args.raw_js)
    report_hash = sha256_file(args.report)
    neural_hash = sha256_file(args.neural_jsonl)
    observed_hosts, http_count = load_http_hosts(args.http_surface)

    timing_prepare = time.perf_counter()
    rows: list[dict[str, Any]] = []
    source_status: dict[str, int] = {}
    for endpoint, neural in zip(endpoints, neural_rows):
        code_slice, status = extract_code_slice(args.raw_js, endpoint["source_file"], endpoint["source_line"], args.code_radius)
        source_status[status] = source_status.get(status, 0) + 1
        row = {
            **endpoint,
            "rule": native_rule_profile(endpoint, observed_hosts),
            "neural": neural,
            "code_slice": code_slice,
            "code_slice_status": status,
        }
        rows.append(row)
    prepare_ms = (time.perf_counter() - timing_prepare) * 1000.0

    usable_rows = [r for r in rows if r["neural"]["neural_usable"]]
    reps_for_rank = build_surface_representatives(usable_rows)
    surface_ranks = assign_surface_ranks(reps_for_rank)
    total_surfaces = len(reps_for_rank)

    merge_start = time.perf_counter()
    for row in rows:
        rank = surface_ranks.get(row["surface_id"]) if row["neural"]["neural_usable"] else None
        row["surface_rank_impact"] = rank[0] if rank else None
        row["surface_rank_sensitivity"] = rank[1] if rank else None
        row["discrepancy_signals"] = classify_signal(row, rank, total_surfaces, args.neural_top_k)
        row["prediction_alignment"] = "ROW_ALIGNED"
    merge_ms = (time.perf_counter() - merge_start) * 1000.0

    pool_a, pool_b, pool_c = build_pools(rows, args.pool_b_size, args.pool_c_size, args.neural_top_k)
    pool_a_surfaces = {r["surface_id"] for r in pool_a}

    report_path = args.output_dir / "triage_dual_track_v2.jsonl"
    pools_path = args.output_dir / "triage_pools_v2.json"
    summary_path = args.output_dir / "triage_summary_v2.json"
    manifest_path = args.output_dir / "triage_run_manifest_v2.json"

    serial_start = time.perf_counter()
    serial_rows = []
    for r in rows:
        serial_rows.append({
            "schema_version": SCHEMA_VERSION,
            "record_index": r["record_index"],
            "record_id": r["record_id"],
            "surface_id": r["surface_id"],
            "endpoint_id": r["endpoint_id"],
            "method": r["method"],
            "path": r["path"],
            "extracted_params": r["extracted_params"],
            "source_file": r["source_file"],
            "source_line": r["source_line"],
            "code_slice": r["code_slice"],
            "code_slice_status": r["code_slice_status"],
            "rule": r["rule"],
            "neural": r["neural"],
            "surface_rank_impact": r["surface_rank_impact"],
            "surface_rank_sensitivity": r["surface_rank_sensitivity"],
            "discrepancy_signals": r["discrepancy_signals"],
            "prediction_alignment": r["prediction_alignment"],
        })
    write_jsonl(report_path, serial_rows)

    write_json(pools_path, {
        "schema_version": SCHEMA_VERSION,
        "identity_contract": {
            "record_id": "unique AST evidence row",
            "surface_id": "deduplicated method+host+path research surface",
            "endpoint_id": "legacy human-readable label, not unique",
        },
        "rule_safe_union_contract": "RuleHighRisk is always retained; neural has no deletion authority.",
        "pool_a_rule_must_keep": [r["surface_id"] for r in pool_a],
        "pool_b_discrepancy": [r["surface_id"] for r in pool_b],
        "pool_c_exploration": [r["surface_id"] for r in pool_c],
        "pool_a_size_requested": len(pool_a),
        "pool_b_size_requested": args.pool_b_size,
        "pool_c_size_requested": args.pool_c_size,
        "notes": [
            "No synthetic R_impact/R_sens rule scale is created.",
            "No scalar RuleScore-vs-neural composite discrepancy is created.",
            "Novelty is not fabricated in Phase 1.",
            "Neural fallback rows remain in coverage but are excluded from neural ranking and B/C evidence.",
        ],
    })
    serial_ms = (time.perf_counter() - serial_start) * 1000.0

    total_ms = (time.perf_counter() - total_timer) * 1000.0
    surface_count = len({r["surface_id"] for r in rows})
    fallback_count = sum(not r["neural"]["neural_usable"] for r in rows)
    entropy_available = sum(r["neural"]["impact_entropy"] is not None and r["neural"]["sensitivity_entropy"] is not None for r in usable_rows)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "script_version": SCRIPT_VERSION,
        "read_only": True,
        "inputs": {
            "report": str(args.report),
            "report_sha256": report_hash,
            "raw_js_root": str(args.raw_js),
            "raw_js_manifest_sha256": manifest_hash,
            "http_surface": str(args.http_surface) if args.http_surface else None,
            "neural_jsonl": str(args.neural_jsonl),
            "neural_jsonl_sha256": neural_hash,
        },
        "counts": {
            "report_rows": len(endpoints),
            "unique_surface_ids": surface_count,
            "unique_legacy_endpoint_ids": len({r["endpoint_id"] for r in rows}),
            "neural_rows": len(predictions),
            "neural_usable_rows": len(usable_rows),
            "neural_fallback_rows": fallback_count,
            "http_surface_records": http_count,
            "observed_hosts": len(observed_hosts),
            "pool_a_surfaces": len(pool_a),
            "pool_b_surfaces": len(pool_b),
            "pool_c_surfaces": len(pool_c),
        },
        "coverage": {
            "row_alignment": len(predictions) == len(endpoints),
            "neural_row_coverage": len(predictions) / len(endpoints) if endpoints else 0.0,
            "neural_usable_coverage": len(usable_rows) / len(endpoints) if endpoints else 0.0,
            "entropy_full_pair_rate_over_usable": entropy_available / len(usable_rows) if usable_rows else 0.0,
        },
        "source_slice_status": source_status,
        "timings_ms": {
            "endpoint_prepare": prepare_ms,
            "merge_and_pool": merge_ms,
            "serialization": serial_ms,
            "total": total_ms,
        },
    }
    write_json(manifest_path, manifest)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "report_rows": len(endpoints),
        "unique_surfaces": surface_count,
        "unique_legacy_endpoint_ids": len({r["endpoint_id"] for r in rows}),
        "rule_high_risk_surfaces": len(pool_a),
        "pool_b_surfaces": len(pool_b),
        "pool_c_surfaces": len(pool_c),
        "neural_coverage_rows": len(predictions) / len(endpoints) if endpoints else 0.0,
        "neural_usable_coverage_rows": len(usable_rows) / len(endpoints) if endpoints else 0.0,
        "fallback_rows": fallback_count,
        "research_efficiency_gain": {
            "status": "NOT_MEASURED_IN_PHASE_1",
            "reason": "Requires an independent Gold Set and downstream research-effort experiment.",
        },
    }
    write_json(summary_path, summary)

    print(f"[OK] report rows          : {len(endpoints)}")
    print(f"[OK] unique surfaces      : {surface_count}")
    print(f"[OK] legacy endpoint_ids  : {len({r['endpoint_id'] for r in rows})}")
    print(f"[OK] neural aligned rows  : {len(predictions)}/{len(endpoints)}")
    print(f"[OK] neural usable rows   : {len(usable_rows)}")
    print(f"[OK] fallback rows        : {fallback_count}")
    print(f"[OK] Pool A surfaces      : {len(pool_a)}")
    print(f"[OK] Pool B surfaces      : {len(pool_b)}")
    print(f"[OK] Pool C surfaces      : {len(pool_c)}")
    print(f"[OK] total analysis ms    : {total_ms:.2f}")
    print(f"[OK] output dir            : {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ComparatorError as exc:
        print(f"[X] {exc}", file=sys.stderr)
        raise SystemExit(2)

