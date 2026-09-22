from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


# ============================================================
# Invar Static GET Endpoint Materializer
#
# Artifact flow:
#
#   tmp/ikuai8_endpoints_report.json
#                 │
#                 │  Invar static endpoint facts
#                 ▼
#       static GET materialization
#                 │
#                 │  restricted by already observed hosts
#                 ▼
#   data/targets/ikuai8.com/
#       static_get_endpoints.jsonl
#
# This script does NOT execute network requests.
#
# It only:
#   1. reads the existing static report;
#   2. reads the existing HTTP surface;
#   3. derives observed hosts;
#   4. materializes GET endpoints into URLs;
#   5. removes obvious AST noise;
#   6. deduplicates;
#   7. validates the resulting JSONL.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TARGET_NAME = "ikuai8.com"

TARGET_ROOT = (
    PROJECT_ROOT
    / "data"
    / "targets"
    / TARGET_NAME
)

STATIC_REPORT_PATH = (
    PROJECT_ROOT
    / "tmp"
    / "ikuai8_endpoints_report.json"
)

HTTP_SURFACE_PATH = (
    TARGET_ROOT
    / "http_surface.jsonl"
)

OUTPUT_PATH = (
    TARGET_ROOT
    / "static_get_endpoints.jsonl"
)


# ============================================================
# Static path filtering
# ============================================================

HTML_FRAGMENT_RE = re.compile(r"[<>]")

URI_SCHEME_RE = re.compile(r"://")

MIME_TYPE_RE = re.compile(
    r"^(?:text|application|image|audio|video|font)/",
    re.IGNORECASE,
)

AST_LITERAL_PREFIX_RE = re.compile(
    r"^(?:image|path|src|href|text|url)\s*:",
    re.IGNORECASE,
)

REPLACEMENT_LITERAL_RE = re.compile(
    r"^\$\d+"
)

MULTI_SPACE_RE = re.compile(
    r"\s{2,}"
)

CONTROL_CHAR_RE = re.compile(
    r"[\x00-\x1f\x7f]"
)

ROUTE_CHARACTER_RE = re.compile(
    r"^[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+$"
)

SOURCE_HOST_RE = re.compile(
    r"raw_js[\\/](?P<host>[^\\/]+)[\\/]",
    re.IGNORECASE,
)


# ============================================================
# Generic helpers
# ============================================================

def normalize_host(value: Any) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip().lower().rstrip(".")

    return normalized or None


def is_in_scope_host(hostname: str | None) -> bool:
    normalized = normalize_host(hostname)

    if normalized is None:
        return False

    return (
        normalized == TARGET_NAME
        or normalized.endswith("." + TARGET_NAME)
    )


def extract_url_host(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value.strip()

    if not candidate:
        return None

    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return None

    if not parsed.netloc:
        return None

    return normalize_host(parsed.hostname)


def extract_source_host(source_file: str | None) -> str | None:
    if not source_file:
        return None

    match = SOURCE_HOST_RE.search(source_file)

    if not match:
        return None

    return normalize_host(
        match.group("host")
    )


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        result: list[str] = []

        for item in value:
            if item is None:
                continue

            text = str(item).strip()

            if text:
                result.append(text)

        return result

    if isinstance(value, str):
        text = value.strip()

        return [text] if text else []

    return [str(value).strip()]


# ============================================================
# JSON / JSONL
# ============================================================

def load_json(path: Path) -> Any:
    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON: {path}\n"
            f"line={exc.lineno}, "
            f"column={exc.colno}: "
            f"{exc.msg}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Unable to read: {path}: {exc}"
        ) from exc


def load_jsonl(
    path: Path,
) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    parse_errors = 0

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as handle:

            for line_number, raw_line in enumerate(
                handle,
                start=1,
            ):
                line = raw_line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    parse_errors += 1
                    continue

                if isinstance(record, dict):
                    records.append(record)

    except OSError as exc:
        raise RuntimeError(
            f"Unable to read JSONL: {path}: {exc}"
        ) from exc

    return records, parse_errors


# ============================================================
# Existing HTTP reality
# ============================================================

def collect_observed_hosts(
    http_records: list[dict[str, Any]],
) -> set[str]:

    observed_hosts: set[str] = set()

    for record in http_records:

        # Primary location: full URL.
        for field_name in (
            "url",
            "input",
            "final_url",
        ):
            value = record.get(field_name)

            if not isinstance(value, str):
                continue

            hostname = extract_url_host(value)

            if hostname and is_in_scope_host(hostname):
                observed_hosts.add(hostname)

        # Fallback: explicit host field.
        explicit_host = normalize_host(
            record.get("host")
        )

        if (
            explicit_host
            and is_in_scope_host(explicit_host)
        ):
            observed_hosts.add(explicit_host)

    return observed_hosts


# ============================================================
# Static path classification
# ============================================================

def is_usable_static_path(
    raw_path: Any,
) -> bool:

    if raw_path is None:
        return False

    path = str(raw_path).strip()

    if not path:
        return False

    # Prevent giant AST/compiler literals.
    if len(path) > 300:
        return False

    # HTML / JSX / DOM fragments.
    if HTML_FRAGMENT_RE.search(path):
        return False

    # data:, image://, chrome-extension://, etc.
    if URI_SCHEME_RE.search(path):
        return False

    # MIME type literals.
    if MIME_TYPE_RE.match(path):
        return False

    # Known object-literal / metadata strings.
    if AST_LITERAL_PREFIX_RE.match(path):
        return False

    # Replacement/template artifacts.
    if REPLACEMENT_LITERAL_RE.match(path):
        return False

    # Control characters should never be in a route.
    if CONTROL_CHAR_RE.search(path):
        return False

    # Obvious prose / UI text.
    if MULTI_SPACE_RE.search(path):
        return False

    # A URL/path should consist of URL-safe characters.
    if not ROUTE_CHARACTER_RE.fullmatch(path):
        return False

    # Absolute/protocol-relative URL is accepted here;
    # host validation occurs later.
    if re.match(
        r"^https?://",
        path,
        re.IGNORECASE,
    ):
        return True

    if path.startswith("//"):
        return True

    # Normal route.
    if path.startswith("/"):
        return True

    # Common API route forms.
    route_prefixes = (
        "api/",
        "v1/",
        "v2/",
        "v3/",
        "v4/",
        "v5/",
        "component/",
        "download/",
        "download.php",
        "index.php",
    )

    if path.lower().startswith(route_prefixes):
        return True

    # Generic relative path.
    #
    # We keep it if it actually resembles a route.
    # This avoids dropping valid routes merely because
    # their prefix is not known to the static extractor.
    #
    # Examples:
    #   admin/session/list
    #   router/group
    #   user/profile
    if "/" in path:
        return True

    return False


# ============================================================
# URL materialization
# ============================================================

def materialize_url(
    source_host: str,
    raw_path: str,
) -> str | None:

    path = raw_path.strip()

    if not path:
        return None

    # --------------------------------------------------------
    # Absolute URL
    # --------------------------------------------------------

    if re.match(
        r"^https?://",
        path,
        re.IGNORECASE,
    ):
        try:
            parsed = urlsplit(path)
        except ValueError:
            return None

        target_host = normalize_host(
            parsed.hostname
        )

        if target_host != source_host:
            return None

        if not is_in_scope_host(target_host):
            return None

        return urlunsplit(
            (
                parsed.scheme.lower(),
                parsed.netloc,
                parsed.path or "/",
                parsed.query,
                parsed.fragment,
            )
        )

    # --------------------------------------------------------
    # Protocol-relative URL
    # --------------------------------------------------------

    if path.startswith("//"):

        try:
            parsed = urlsplit(
                "https:" + path
            )
        except ValueError:
            return None

        target_host = normalize_host(
            parsed.hostname
        )

        if target_host != source_host:
            return None

        if not is_in_scope_host(target_host):
            return None

        return urlunsplit(
            (
                "https",
                parsed.netloc,
                parsed.path or "/",
                parsed.query,
                parsed.fragment,
            )
        )

    # --------------------------------------------------------
    # Relative route
    # --------------------------------------------------------

    if not path.startswith("/"):
        path = "/" + path

    return f"https://{source_host}{path}"


# ============================================================
# Endpoint record conversion
# ============================================================

def build_output_record(
    endpoint: dict[str, Any],
    endpoint_url: str,
) -> dict[str, Any]:

    return {
        "url": endpoint_url,
        "method": "GET",
        "endpoint_id": endpoint.get(
            "endpoint_id"
        ),
        "source_file": endpoint.get(
            "source_file"
        ),
        "source_line": endpoint.get(
            "line"
        ),
        "risk_score": endpoint.get(
            "risk_score"
        ),
        "tags": normalize_string_list(
            endpoint.get("tags")
        ),
        "extracted_params": normalize_string_list(
            endpoint.get("extracted_params")
        ),
        "is_dynamic": endpoint.get(
            "is_dynamic"
        ),
        "confidence": endpoint.get(
            "confidence"
        ),
        "call_signature": endpoint.get(
            "call_signature"
        ),
    }


# ============================================================
# Materialization
# ============================================================

def materialize_endpoints(
    endpoints: list[Any],
    observed_hosts: set[str],
) -> tuple[
    list[dict[str, Any]],
    Counter[str],
]:

    counters: Counter[str] = Counter()

    # method + URL -> first complete provenance record
    materialized_by_key: dict[
        str,
        dict[str, Any],
    ] = {}

    for endpoint in endpoints:

        if not isinstance(endpoint, dict):
            counters[
                "invalid_endpoint_object"
            ] += 1
            continue

        method = str(
            endpoint.get("method", "")
        ).strip().upper()

        if method != "GET":
            counters["non_get"] += 1
            continue

        source_file = endpoint.get(
            "source_file"
        )

        if not source_file:
            counters["missing_source_file"] += 1
            continue

        source_host = extract_source_host(
            str(source_file)
        )

        if source_host is None:
            counters[
                "source_host_extraction_failed"
            ] += 1
            continue

        if not is_in_scope_host(source_host):
            counters[
                "source_host_out_of_scope"
            ] += 1
            continue

        if source_host not in observed_hosts:
            counters[
                "source_host_not_observed"
            ] += 1
            continue

        raw_path = endpoint.get("path")

        if not is_usable_static_path(raw_path):
            counters[
                "invalid_or_ast_noise_path"
            ] += 1
            continue

        endpoint_url = materialize_url(
            source_host=source_host,
            raw_path=str(raw_path),
        )

        if endpoint_url is None:
            counters[
                "url_materialization_failed"
            ] += 1
            continue

        dedupe_key = (
            f"GET|{endpoint_url}"
        )

        if dedupe_key in materialized_by_key:
            counters["duplicate"] += 1
            continue

        materialized_by_key[
            dedupe_key
        ] = build_output_record(
            endpoint=endpoint,
            endpoint_url=endpoint_url,
        )

    rows = list(
        materialized_by_key.values()
    )

    rows.sort(
        key=lambda row: (
            str(row.get("url", "")),
            str(row.get("source_file", "")),
            int(
                row.get("source_line")
                or 0
            ),
        )
    )

    return rows, counters


# ============================================================
# Output validation
# ============================================================

def validate_output_rows(
    rows: list[dict[str, Any]],
) -> None:

    seen: set[str] = set()

    for index, row in enumerate(
        rows,
        start=1,
    ):

        method = row.get("method")
        url = row.get("url")

        if method != "GET":
            raise RuntimeError(
                f"Output record {index} is not GET."
            )

        if not isinstance(url, str) or not url:
            raise RuntimeError(
                f"Output record {index} has invalid URL."
            )

        try:
            parsed = urlsplit(url)
        except ValueError as exc:
            raise RuntimeError(
                f"Output record {index} has invalid URL: {url}"
            ) from exc

        hostname = normalize_host(
            parsed.hostname
        )

        if not is_in_scope_host(hostname):
            raise RuntimeError(
                f"Output record {index} is outside scope: {url}"
            )

        dedupe_key = (
            f"GET|{url}"
        )

        if dedupe_key in seen:
            raise RuntimeError(
                f"Duplicate output URL: {url}"
            )

        seen.add(dedupe_key)


# ============================================================
# Atomic JSONL write
# ============================================================

def write_jsonl_atomic(
    output_path: Path,
    rows: list[dict[str, Any]],
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = output_path.with_name(
        output_path.name + ".tmp"
    )

    try:
        with temp_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:

            for row in rows:
                handle.write(
                    json.dumps(
                        row,
                        ensure_ascii=False,
                        separators=(
                            ",",
                            ":",
                        ),
                    )
                )
                handle.write("\n")

        temp_path.replace(
            output_path
        )

    except Exception:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass

        raise


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Materialize Invar static GET endpoints "
            "into concrete in-scope URLs."
        )
    )

    parser.add_argument(
        "--static-report",
        type=Path,
        default=STATIC_REPORT_PATH,
        help=(
            "Static Invar endpoint report. "
            f"Default: {STATIC_REPORT_PATH}"
        ),
    )

    parser.add_argument(
        "--http-surface",
        type=Path,
        default=HTTP_SURFACE_PATH,
        help=(
            "Existing HTTP surface JSONL. "
            f"Default: {HTTP_SURFACE_PATH}"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help=(
            "Materialized JSONL output. "
            f"Default: {OUTPUT_PATH}"
        ),
    )

    return parser.parse_args()


# ============================================================
# Main
# ============================================================

def main() -> int:

    args = parse_args()

    static_report_path = (
        args.static_report.resolve()
    )

    http_surface_path = (
        args.http_surface.resolve()
    )

    output_path = (
        args.output.resolve()
    )

    print("=" * 60)
    print(" Invar 静态 GET Endpoint 物化")
    print("=" * 60)
    print()

    print("[INPUT]")
    print(
        f"  ├─ 静态报告 : {static_report_path}"
    )
    print(
        f"  └─ HTTP 现实: {http_surface_path}"
    )
    print()

    print("[OUTPUT]")
    print(
        f"  └─ Endpoint : {output_path}"
    )
    print()

    # --------------------------------------------------------
    # 1. Validate input artifacts.
    # --------------------------------------------------------

    if not static_report_path.is_file():
        raise FileNotFoundError(
            "静态 Endpoint 报告不存在:\n"
            f"  {static_report_path}"
        )

    if not http_surface_path.is_file():
        raise FileNotFoundError(
            "HTTP surface 不存在:\n"
            f"  {http_surface_path}"
        )

    # --------------------------------------------------------
    # 2. Read HTTP surface.
    # --------------------------------------------------------

    print("[1/5] 读取 HTTP surface...")

    http_records, http_parse_errors = (
        load_jsonl(
            http_surface_path
        )
    )

    observed_hosts = (
        collect_observed_hosts(
            http_records
        )
    )

    print(
        f"  ├─ HTTP records : {len(http_records)}"
    )
    print(
        f"  ├─ JSONL errors : {http_parse_errors}"
    )
    print(
        f"  └─ Observed host: {len(observed_hosts)}"
    )
    print()

    if not observed_hosts:
        raise RuntimeError(
            "HTTP surface 中没有发现任何 "
            "in-scope observed host。"
        )

    print("  已观测 Host:")

    for hostname in sorted(
        observed_hosts
    ):
        print(
            f"    - {hostname}"
        )

    print()

    # --------------------------------------------------------
    # 3. Read static report.
    # --------------------------------------------------------

    print(
        "[2/5] 读取 Invar 静态 Endpoint 报告..."
    )

    static_report = load_json(
        static_report_path
    )

    if not isinstance(
        static_report,
        dict,
    ):
        raise RuntimeError(
            "静态报告根对象必须是 JSON object。"
        )

    endpoints = static_report.get(
        "endpoints"
    )

    if not isinstance(
        endpoints,
        list,
    ):
        raise RuntimeError(
            '静态报告不存在有效的 "endpoints" 数组。'
        )

    print(
        f"  └─ Static endpoints: {len(endpoints)}"
    )
    print()

    # --------------------------------------------------------
    # 4. Materialize.
    # --------------------------------------------------------

    print(
        "[3/5] 物化静态 GET Endpoint..."
    )

    rows, counters = (
        materialize_endpoints(
            endpoints=endpoints,
            observed_hosts=observed_hosts,
        )
    )

    print(
        f"  └─ Materialized GETs: {len(rows)}"
    )
    print()

    # --------------------------------------------------------
    # 5. Validate + write.
    # --------------------------------------------------------

    print(
        "[4/5] 验证输出结构..."
    )

    validate_output_rows(rows)

    print(
        f"  └─ Validated records: {len(rows)}"
    )
    print()

    print(
        "[5/5] 写入 JSONL..."
    )

    write_jsonl_atomic(
        output_path=output_path,
        rows=rows,
    )

    print(
        f"  └─ Written: {output_path}"
    )
    print()

    # --------------------------------------------------------
    # Final report.
    # --------------------------------------------------------

    print("=" * 60)
    print(" 物化完成")
    print("=" * 60)
    print()

    print("[SUMMARY]")
    print(
        f"  ├─ Static endpoints      : {len(endpoints)}"
    )
    print(
        f"  ├─ HTTP surface records  : {len(http_records)}"
    )
    print(
        f"  ├─ Observed hosts        : {len(observed_hosts)}"
    )
    print(
        f"  ├─ Materialized GETs     : {len(rows)}"
    )
    print(
        f"  └─ Output                : {output_path}"
    )
    print()

    print("[FILTERS]")

    for counter_name in sorted(
        counters
    ):
        print(
            f"  ├─ {counter_name:<34} "
            f"{counters[counter_name]}"
        )

    print()

    print("[PREVIEW]")

    preview_limit = min(
        20,
        len(rows),
    )

    for index in range(
        preview_limit
    ):
        row = rows[index]

        print(
            f"  {index + 1:02d}. "
            f"{row['method']} "
            f"{row['url']}"
        )

    if len(rows) > preview_limit:
        print(
            f"  ... "
            f"{len(rows) - preview_limit} more"
        )

    print()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )
    except KeyboardInterrupt:
        print(
            "\n[STOP] 用户中断。",
            file=sys.stderr,
        )
        raise SystemExit(130)
    except Exception as exc:
        print(
            f"\n[ERROR] {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)