from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch-probe collected URLs with ProjectDiscovery httpx and classify HTTP surfaces."
    )
    parser.add_argument("--input", required=True, help="Input URL list or JSONL asset file.")
    parser.add_argument("--raw-output", required=True, help="Raw httpx JSONL output.")
    parser.add_argument("--classified-output", required=True, help="Classified JSONL output.")
    parser.add_argument("--summary-output", required=True, help="Classification summary JSON.")
    parser.add_argument(
        "--httpx",
        default="httpx.exe",
        help="Path to ProjectDiscovery httpx executable.",
    )
    parser.add_argument("--threads", type=int, default=5)
    parser.add_argument("--rate-limit", type=int, default=5)
    return parser.parse_args()


def extract_url(item: object) -> str | None:
    if isinstance(item, str):
        value = item.strip()
        return value if value.startswith(("http://", "https://")) else None

    if not isinstance(item, dict):
        return None

    candidates = [
        item.get("url"),
        item.get("URL"),
        item.get("input"),
        item.get("final_url"),
    ]

    request = item.get("request")
    if isinstance(request, dict):
        candidates.append(request.get("url"))

    response = item.get("response")
    if isinstance(response, dict):
        candidates.append(response.get("url"))

    for candidate in candidates:
        if isinstance(candidate, str):
            value = candidate.strip()
            if value.startswith(("http://", "https://")):
                return value

    return None


def load_urls(path: Path) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue

            url: str | None = None

            try:
                parsed = json.loads(line)
                url = extract_url(parsed)
            except json.JSONDecodeError:
                url = extract_url(line)

            if not url:
                continue

            if url not in seen:
                seen.add(url)
                urls.append(url)

    return urls


def field(record: dict, *names: str):
    for name in names:
        value = record.get(name)
        if value is not None:
            return value
    return None


def classify(record: dict, duplicate_hashes: dict[tuple[str, str], int]) -> tuple[str, str]:
    status = field(record, "status_code", "status-code")
    content_type = str(field(record, "content_type", "content-type") or "").lower()
    body_hash = str(field(record, "body_hash", "body-hash") or "")
    url = str(field(record, "url", "input") or "")
    location = str(field(record, "location") or "")
    server = str(field(record, "webserver", "web_server", "server") or "").lower()

    try:
        status_code = int(status) if status is not None else None
    except (TypeError, ValueError):
        status_code = None

    lower_url = url.lower()
    lower_location = location.lower()

    if any(
        marker in server
        for marker in (
            "aliyun",
            "tengine",
            "alibaba",
        )
    ):
        if status_code in {403, 405, 406, 419, 429}:
            return "WAF_OR_EDGE_BLOCK", "server fingerprint suggests edge/WAF response"

    if status_code in {301, 302, 303, 307, 308}:
        return "REDIRECT", f"HTTP {status_code} -> {location or 'no location'}"

    if status_code == 401:
        return "AUTH_REQUIRED", "HTTP 401"

    if status_code == 403:
        return "FORBIDDEN", "HTTP 403"

    if status_code == 405:
        return "METHOD_MISMATCH_OR_EDGE", "HTTP 405"

    if status_code is not None and 500 <= status_code <= 599:
        return "SERVER_ERROR", f"HTTP {status_code}"

    if status_code is not None and 400 <= status_code <= 499:
        return "CLIENT_ERROR", f"HTTP {status_code}"

    if status_code is None:
        return "NETWORK_ERROR", "no HTTP status returned"

    key = (urlparse(url).netloc.lower(), body_hash)
    repeated = body_hash and duplicate_hashes.get(key, 0) >= 2

    if repeated and "text/html" in content_type:
        return "SOFT_404_OR_SPA", "identical HTML body hash reused across multiple URLs"

    if "application/json" in content_type or content_type.endswith("+json"):
        return "LIVE_API_LIKE", "2xx JSON response"

    if "text/html" in content_type or "application/xhtml+xml" in content_type:
        return "LIVE_HTML", "2xx HTML response"

    if 200 <= status_code < 300:
        return "LIVE_OTHER", f"2xx response with content-type {content_type or 'unknown'}"

    return "UNCLASSIFIED", "response did not match a specific classifier"


def main() -> int:
    args = parse_args()

    input_path = Path(args.input).resolve()
    raw_output = Path(args.raw_output).resolve()
    classified_output = Path(args.classified_output).resolve()
    summary_output = Path(args.summary_output).resolve()

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    for target in (raw_output, classified_output, summary_output):
        target.parent.mkdir(parents=True, exist_ok=True)

    urls = load_urls(input_path)
    if not urls:
        raise RuntimeError(f"No HTTP/HTTPS URLs could be extracted from {input_path}")

    print(f"[+] Loaded unique URLs: {len(urls)}")

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        delete=False,
    ) as temp:
        input_txt = Path(temp.name)
        for url in urls:
            temp.write(url + "\n")

    command = [
        args.httpx,
        "-l",
        str(input_txt),
        "-j",
        "-silent",
        "-sc",
        "-cl",
        "-ct",
        "-location",
        "-title",
        "-server",
        "-td",
        "-hash",
        "sha256",
        "-rt",
        "-method",
        "-t",
        str(args.threads),
        "-rl",
        str(args.rate_limit),
        "-o",
        str(raw_output),
    ]

    print("[+] Running ProjectDiscovery httpx")
    print(f"    threads    = {args.threads}")
    print(f"    rate-limit = {args.rate_limit}/s")
    print(f"    raw output = {raw_output}")

    try:
        completed = subprocess.run(command, check=False)
    finally:
        try:
            input_txt.unlink()
        except FileNotFoundError:
            pass

    if completed.returncode != 0:
        raise RuntimeError(
            f"httpx exited with code {completed.returncode}"
        )

    if not raw_output.is_file():
        raise RuntimeError(f"httpx did not create output: {raw_output}")

    records: list[dict] = []

    with raw_output.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSONL at {raw_output}:{line_number}"
                ) from exc

            if isinstance(record, dict):
                records.append(record)

    duplicate_hashes: dict[tuple[str, str], int] = Counter()

    for record in records:
        url = str(field(record, "url", "input") or "")
        body_hash = str(field(record, "body_hash", "body-hash") or "")
        host = urlparse(url).netloc.lower()

        if host and body_hash:
            duplicate_hashes[(host, body_hash)] += 1

    counts: Counter[str] = Counter()
    by_host: defaultdict[str, Counter[str]] = defaultdict(Counter)

    with classified_output.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for record in records:
            classification, reason = classify(record, duplicate_hashes)

            url = str(field(record, "url", "input") or "")
            host = urlparse(url).netloc.lower() or "<unknown>"

            result = {
                "url": url,
                "classification": classification,
                "reason": reason,
                "status_code": field(record, "status_code", "status-code"),
                "content_type": field(record, "content_type", "content-type"),
                "content_length": field(record, "content_length", "content-length"),
                "title": field(record, "title"),
                "location": field(record, "location"),
                "webserver": field(record, "webserver", "web_server", "server"),
                "technology": field(record, "tech", "technology"),
                "body_hash": field(record, "body_hash", "body-hash"),
                "response_time": field(record, "response_time", "response-time"),
                "method": field(record, "method"),
            }

            counts[classification] += 1
            by_host[host][classification] += 1

            handle.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )

    summary = {
        "input_file": str(input_path),
        "raw_output": str(raw_output),
        "classified_output": str(classified_output),
        "input_unique_urls": len(urls),
        "httpx_records": len(records),
        "classification_counts": dict(sorted(counts.items())),
        "hosts": {
            host: dict(sorted(host_counts.items()))
            for host, host_counts in sorted(by_host.items())
        },
    }

    summary_output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("")
    print("=" * 64)
    print("HTTP SURFACE CLASSIFICATION")
    print("=" * 64)
    for name, count in sorted(counts.items()):
        print(f"{name:28} {count}")
    print("=" * 64)
    print(f"Raw:        {raw_output}")
    print(f"Classified: {classified_output}")
    print(f"Summary:    {summary_output}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
