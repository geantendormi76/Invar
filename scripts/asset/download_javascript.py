from __future__ import annotations

import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from requests import Response
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
    HTTPError,
    RequestException,
    SSLError,
    Timeout,
)

DEFAULT_TIMEOUT = 15
DEFAULT_WORKERS = 8
MAX_REDIRECTS = 5
CHUNK_SIZE = 1024 * 1024

JS_CONTENT_TYPES = {
    "application/javascript",
    "application/ecmascript",
    "text/javascript",
    "text/ecmascript",
    "application/x-javascript",
}

HTML_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
}


def normalize_hostname(hostname: str | None) -> str:
    if not hostname:
        return ""
    return hostname.strip().lower().rstrip(".")


def normalize_target(target: str) -> str:
    target = target.strip().lower().rstrip(".")
    if target.startswith("http://"):
        target = target[7:]
    elif target.startswith("https://"):
        target = target[8:]

    target = target.split("/", 1)[0]
    target = target.split(":", 1)[0]
    return normalize_hostname(target)


def is_target_host(hostname: str, target: str) -> bool:
    hostname = normalize_hostname(hostname)
    target = normalize_target(target)

    if not hostname or not target:
        return False

    return hostname == target or hostname.endswith("." + target)


def normalize_url(url: str) -> str:
    url = url.strip()

    parsed = urlparse(url)

    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    hostname = normalize_hostname(parsed.hostname)

    if scheme not in {"http", "https"} or not hostname:
        return ""

    try:
        port = parsed.port
    except ValueError:
        return ""

    netloc = hostname

    if port is not None:
        default_port = (
            (scheme == "http" and port == 80)
            or (scheme == "https" and port == 443)
        )
        if not default_port:
            netloc = f"{hostname}:{port}"

    normalized = parsed._replace(
        scheme=scheme,
        netloc=netloc,
        fragment="",
    )

    return normalized.geturl()


def safe_file_name(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name

    if not name:
        name = "index.js"

    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)

    if not name.lower().endswith((".js", ".mjs", ".cjs")):
        name += ".js"

    return name


def deterministic_file_name(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return f"{digest}_{safe_file_name(url)}"


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def normalize_content_type(value: str | None) -> str:
    if not value:
        return ""

    return value.split(";", 1)[0].strip().lower()


def looks_like_javascript(url: str, content_type: str, body: bytes) -> bool:
    content_type = normalize_content_type(content_type)

    if content_type in JS_CONTENT_TYPES:
        return True

    path = urlparse(url).path.lower()

    if path.endswith((".js", ".mjs", ".cjs")):
        return True

    if content_type in HTML_CONTENT_TYPES:
        sample = body[:256 * 1024].decode("utf-8", errors="ignore").lower()

        if "<script" in sample:
            return True

        return False

    sample = body[:4096].decode("utf-8", errors="ignore").lower()

    js_markers = (
        "function ",
        "const ",
        "let ",
        "var ",
        "=>",
        "webpack",
        "sourceMappingURL",
    )

    return any(marker in sample for marker in js_markers)


def classify_exception(exc: Exception) -> str:
    if isinstance(exc, SSLError):
        return "tls_error"

    if isinstance(exc, Timeout):
        return "network_error"

    if isinstance(exc, RequestsConnectionError):
        return "network_error"

    if isinstance(exc, HTTPError):
        return "http_error"

    if isinstance(exc, RequestException):
        return "network_error"

    return "network_error"


def exception_type_name(exc: Exception) -> str:
    return type(exc).__name__


def build_base_record(
    asset: dict[str, Any],
    *,
    target: str,
    tls_verified: bool,
) -> dict[str, Any]:
    url = normalize_url(str(asset.get("url", "")))
    parsed = urlparse(url)

    return {
        "asset_id": asset.get("asset_id", f"javascript:{url}"),
        "source": "katana",
        "source_url": url,
        "final_url": None,
        "hostname": normalize_hostname(parsed.hostname),
        "asset_type": "javascript",
        "target": target,
        "first_party_state": None,
        "status_code": None,
        "content_type": None,
        "local_path": None,
        "sha256": None,
        "status": None,
        "error_type": None,
        "error": None,
        "tls_verified": tls_verified,
    }


def classify_first_party(hostname: str, target: str) -> str:
    if is_target_host(hostname, target):
        return "FIRST_PARTY"
    return "THIRD_PARTY"


def fetch_one(
    asset: dict[str, Any],
    *,
    target: str,
    output_dir: Path,
    timeout: int,
    insecure: bool,
) -> dict[str, Any]:
    tls_verified = not insecure

    record = build_base_record(
        asset,
        target=target,
        tls_verified=tls_verified,
    )

    source_url = record["source_url"]

    if not source_url:
        record["status"] = "network_error"
        record["error_type"] = "InvalidURL"
        record["error"] = "Invalid or empty URL"
        return record

    parsed_source = urlparse(source_url)
    source_hostname = normalize_hostname(parsed_source.hostname)

    if not is_target_host(source_hostname, target):
        record["status"] = "external_redirect_blocked"
        record["error_type"] = "TargetBoundaryViolation"
        record["error"] = (
            f"Source host '{source_hostname}' is outside target '{target}'"
        )
        return record

    current_url = source_url

    session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        ),
        "Accept": (
            "application/javascript, text/javascript, "
            "application/x-javascript, */*;q=0.1"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "close",
    }

    try:
        for _ in range(MAX_REDIRECTS + 1):
            parsed_current = urlparse(current_url)
            current_hostname = normalize_hostname(parsed_current.hostname)

            if not is_target_host(current_hostname, target):
                record["status"] = "external_redirect_blocked"
                record["error_type"] = "TargetBoundaryViolation"
                record["error"] = (
                    f"Redirect target '{current_hostname}' "
                    f"is outside target '{target}'"
                )
                record["final_url"] = current_url
                return record

            try:
                response: Response = session.get(
                    current_url,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=False,
                    verify=not insecure,
                )
            except SSLError as exc:
                record["status"] = "tls_error"
                record["error_type"] = exception_type_name(exc)
                record["error"] = str(exc)
                record["final_url"] = current_url
                return record
            except Timeout as exc:
                record["status"] = "network_error"
                record["error_type"] = exception_type_name(exc)
                record["error"] = str(exc)
                record["final_url"] = current_url
                return record
            except RequestsConnectionError as exc:
                record["status"] = "network_error"
                record["error_type"] = exception_type_name(exc)
                record["error"] = str(exc)
                record["final_url"] = current_url
                return record
            except RequestException as exc:
                record["status"] = classify_exception(exc)
                record["error_type"] = exception_type_name(exc)
                record["error"] = str(exc)
                record["final_url"] = current_url
                return record

            record["status_code"] = response.status_code
            record["content_type"] = normalize_content_type(
                response.headers.get("Content-Type")
            )
            record["final_url"] = current_url

            if response.is_redirect or response.status_code in {
                301,
                302,
                303,
                307,
                308,
            }:
                location = response.headers.get("Location")

                if not location:
                    record["status"] = "http_error"
                    record["error_type"] = "RedirectWithoutLocation"
                    record["error"] = (
                        f"HTTP {response.status_code} redirect "
                        "without Location header"
                    )
                    return record

                next_url = normalize_url(urljoin(current_url, location))

                if not next_url:
                    record["status"] = "http_error"
                    record["error_type"] = "InvalidRedirectURL"
                    record["error"] = (
                        f"Invalid redirect target: {location}"
                    )
                    return record

                next_hostname = normalize_hostname(
                    urlparse(next_url).hostname
                )

                if not is_target_host(next_hostname, target):
                    record["status"] = "external_redirect_blocked"
                    record["error_type"] = "TargetBoundaryViolation"
                    record["error"] = (
                        f"Redirect target '{next_hostname}' "
                        f"is outside target '{target}'"
                    )
                    record["final_url"] = next_url
                    return record

                current_url = next_url
                continue

            try:
                response.raise_for_status()
            except HTTPError as exc:
                record["status"] = "http_error"
                record["error_type"] = exception_type_name(exc)
                record["error"] = str(exc)
                return record

            body = response.content

            final_hostname = normalize_hostname(
                urlparse(current_url).hostname
            )

            record["first_party_state"] = classify_first_party(
                final_hostname,
                target,
            )

            if not looks_like_javascript(
                current_url,
                record["content_type"] or "",
                body,
            ):
                record["status"] = "not_javascript"
                record["error_type"] = "ContentTypeMismatch"
                record["error"] = (
                    "Response does not appear to contain JavaScript"
                )
                return record

            host_dir = output_dir / final_hostname
            host_dir.mkdir(parents=True, exist_ok=True)

            file_name = deterministic_file_name(source_url)
            destination = host_dir / file_name

            temp_path = destination.with_suffix(destination.suffix + ".part")

            try:
                temp_path.write_bytes(body)
                digest = compute_sha256(temp_path)
                temp_path.replace(destination)
            except Exception:
                if temp_path.exists():
                    temp_path.unlink()
                raise

            record["local_path"] = str(destination)
            record["sha256"] = digest
            record["status"] = "downloaded"

            return record

        record["status"] = "http_error"
        record["error_type"] = "TooManyRedirects"
        record["error"] = (
            f"Redirect limit exceeded ({MAX_REDIRECTS})"
        )
        return record

    except Exception as exc:
        record["status"] = "network_error"
        record["error_type"] = exception_type_name(exc)
        record["error"] = str(exc)
        return record
    finally:
        session.close()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    if not path.exists():
        return records

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSONL at {path}:{line_number}: {exc}"
                ) from exc

            if isinstance(value, dict):
                records.append(value)

    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

    temp_path.replace(path)


def index_manifest(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for record in records:
        source_url = normalize_url(str(record.get("source_url", "")))

        if source_url:
            result[source_url] = record

    return result


def load_input_assets(
    input_path: Path,
    *,
    target: str,
) -> list[dict[str, Any]]:
    raw_assets = read_jsonl(input_path)

    unique: dict[str, dict[str, Any]] = {}

    for asset in raw_assets:
        url = normalize_url(str(asset.get("url", "")))

        if not url:
            continue

        hostname = normalize_hostname(urlparse(url).hostname)

        if not is_target_host(hostname, target):
            continue

        normalized_asset = dict(asset)
        normalized_asset["url"] = url
        normalized_asset["asset_type"] = "javascript"
        normalized_asset["hostname"] = hostname
        normalized_asset["target"] = target

        unique[url] = normalized_asset

    return list(unique.values())


def select_assets(
    input_assets: list[dict[str, Any]],
    previous_manifest: dict[str, dict[str, Any]],
    *,
    retry_failed_only: bool,
) -> tuple[list[dict[str, Any]], int]:
    selected: list[dict[str, Any]] = []
    skipped_downloaded = 0

    for asset in input_assets:
        url = normalize_url(str(asset.get("url", "")))
        previous = previous_manifest.get(url)

        if (
            retry_failed_only
            and previous is not None
            and previous.get("status") == "downloaded"
        ):
            skipped_downloaded += 1
            continue

        selected.append(asset)

    return selected, skipped_downloaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download normalized JavaScript assets."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to javascript.jsonl",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for downloaded JavaScript files",
    )

    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to JSONL download manifest",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Target registrable domain, e.g. ikuai8.com",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Concurrent workers, default={DEFAULT_WORKERS}",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds, default={DEFAULT_TIMEOUT}",
    )

    parser.add_argument(
        "--insecure",
        action="store_true",
        help=(
            "Disable TLS certificate verification. "
            "Not enabled by default."
        ),
    )

    parser.add_argument(
        "--retry-failed-only",
        action="store_true",
        help=(
            "Only process assets that are not already marked "
            "'downloaded' in the existing manifest."
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    manifest_path = Path(args.manifest).resolve()

    target = normalize_target(args.target)

    if not target:
        raise SystemExit("ERROR: invalid --target")

    if args.workers < 1:
        raise SystemExit("ERROR: --workers must be >= 1")

    if args.timeout < 1:
        raise SystemExit("ERROR: --timeout must be >= 1")

    if not input_path.exists():
        raise SystemExit(f"ERROR: input file not found: {input_path}")

    input_assets = load_input_assets(
        input_path,
        target=target,
    )

    previous_records = read_jsonl(manifest_path)
    previous_manifest = index_manifest(previous_records)

    selected_assets, skipped_downloaded = select_assets(
        input_assets,
        previous_manifest,
        retry_failed_only=args.retry_failed_only,
    )

    print(f"input_urls={len(read_jsonl(input_path))}")
    print(f"unique_target_urls={len(input_assets)}")

    if args.retry_failed_only:
        print(f"previous_downloaded_skipped={skipped_downloaded}")

    print(f"to_process={len(selected_assets)}")
    print(f"tls_verified={'false' if args.insecure else 'true'}")

    if not selected_assets:
        final_records = []

        for asset in input_assets:
            url = normalize_url(str(asset.get("url", "")))

            if url in previous_manifest:
                final_records.append(previous_manifest[url])

        write_jsonl(manifest_path, final_records)

        print("downloaded=0")
        print("http_error=0")
        print("not_javascript=0")
        print("external_redirect_blocked=0")
        print("tls_error=0")
        print("network_error=0")
        print("other_failures=0")
        return 0

    results: dict[str, dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(
                fetch_one,
                asset,
                target=target,
                output_dir=output_dir,
                timeout=args.timeout,
                insecure=args.insecure,
            ): normalize_url(str(asset.get("url", "")))
            for asset in selected_assets
        }

        for future in as_completed(future_map):
            url = future_map[future]

            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "asset_id": f"javascript:{url}",
                    "source": "katana",
                    "source_url": url,
                    "final_url": None,
                    "hostname": normalize_hostname(
                        urlparse(url).hostname
                    ),
                    "asset_type": "javascript",
                    "target": target,
                    "first_party_state": None,
                    "status_code": None,
                    "content_type": None,
                    "local_path": None,
                    "sha256": None,
                    "status": "network_error",
                    "error_type": exception_type_name(exc),
                    "error": str(exc),
                    "tls_verified": not args.insecure,
                }

            results[url] = result

    final_records: list[dict[str, Any]] = []

    for asset in input_assets:
        url = normalize_url(str(asset.get("url", "")))

        if url in results:
            final_records.append(results[url])
        elif url in previous_manifest:
            final_records.append(previous_manifest[url])

    write_jsonl(
        manifest_path,
        final_records,
    )

    counts = {
        "downloaded": 0,
        "http_error": 0,
        "not_javascript": 0,
        "external_redirect_blocked": 0,
        "tls_error": 0,
        "network_error": 0,
        "other_failures": 0,
    }

    for record in final_records:
        status = record.get("status")

        if status in counts:
            counts[status] += 1
        elif status:
            counts["other_failures"] += 1

    print(f"downloaded={counts['downloaded']}")
    print(f"http_error={counts['http_error']}")
    print(f"not_javascript={counts['not_javascript']}")
    print(
        "external_redirect_blocked="
        f"{counts['external_redirect_blocked']}"
    )
    print(f"tls_error={counts['tls_error']}")
    print(f"network_error={counts['network_error']}")
    print(f"other_failures={counts['other_failures']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
