from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


JS_EXTENSIONS = {
    ".js",
    ".mjs",
    ".cjs",
}

JS_CONTENT_TYPES = {
    "application/javascript",
    "application/x-javascript",
    "text/javascript",
    "text/ecmascript",
    "application/ecmascript",
}


def _iter_jsonl(path: Path):
    path = Path(path)

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSONL at {path}:{line_number}: {exc}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(
                    f"JSONL record must be an object at "
                    f"{path}:{line_number}"
                )

            yield record


def _normalize_target(target: str) -> str:
    target = target.strip().lower().rstrip(".")

    if not target:
        raise ValueError("target must not be empty")

    return target


def _normalize_url(endpoint: str) -> tuple[str, str] | None:
    endpoint = endpoint.strip()

    if not endpoint:
        return None

    try:
        parts = urlsplit(endpoint)
        hostname = parts.hostname
        _ = parts.port
    except ValueError:
        return None

    if parts.scheme.lower() not in {"http", "https"}:
        return None

    if not hostname:
        return None

    hostname = hostname.rstrip(".").lower()

    normalized_url = urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc,
            parts.path,
            parts.query,
            "",
        )
    )

    return normalized_url, hostname


def _is_target_hostname(
    hostname: str,
    target: str,
) -> bool:
    hostname = hostname.lower().rstrip(".")
    target = _normalize_target(target)

    return (
        hostname == target
        or hostname.endswith(f".{target}")
    )


def _extract_content_type(
    response: dict[str, Any],
) -> str:
    content_type = response.get("content_type")

    if content_type:
        return str(content_type).split(";", 1)[0].strip().lower()

    headers = response.get("headers")

    if not isinstance(headers, dict):
        return ""

    for key, value in headers.items():
        if str(key).lower() == "content-type":
            return str(value).split(";", 1)[0].strip().lower()

    return ""


def _is_javascript(
    url: str,
    request: dict[str, Any],
    response: dict[str, Any],
) -> bool:
    parsed = urlsplit(url)
    path = parsed.path.lower()

    for extension in JS_EXTENSIONS:
        if path.endswith(extension):
            return True

    content_type = _extract_content_type(response)

    if (
        content_type in JS_CONTENT_TYPES
        or "javascript" in content_type
    ):
        return True

    tag = str(request.get("tag", "")).lower()
    attribute = str(request.get("attribute", "")).lower()

    if tag == "script" and attribute == "src":
        return True

    return False


def _build_url_asset(
    url: str,
    hostname: str,
    target: str,
) -> dict[str, str]:
    return {
        "asset_id": f"url:{url}",
        "asset_type": "url",
        "url": url,
        "hostname": hostname,
        "target": _normalize_target(target),
    }


def _build_javascript_asset(
    url: str,
    hostname: str,
    target: str,
) -> dict[str, str]:
    return {
        "asset_id": f"javascript:{url}",
        "asset_type": "javascript",
        "url": url,
        "hostname": hostname,
        "target": _normalize_target(target),
    }


def normalize_katana_results(
    input_path: Path,
    urls_output: Path,
    javascript_output: Path,
    target: str,
) -> tuple[int, int]:
    input_path = Path(input_path)
    urls_output = Path(urls_output)
    javascript_output = Path(javascript_output)
    target = _normalize_target(target)

    url_assets: dict[str, dict[str, str]] = {}
    javascript_assets: dict[str, dict[str, str]] = {}

    for record in _iter_jsonl(input_path):
        # Katana errors remain in katana.jsonl.
        # They are not promoted to persistent URL assets.
        if record.get("error"):
            continue

        request = record.get("request")

        if not isinstance(request, dict):
            continue

        endpoint = request.get("endpoint")

        if not isinstance(endpoint, str):
            continue

        normalized = _normalize_url(endpoint)

        if normalized is None:
            continue

        url, hostname = normalized

        if not _is_target_hostname(hostname, target):
            continue

        response = record.get("response")

        if not isinstance(response, dict):
            response = {}

        if url not in url_assets:
            url_assets[url] = _build_url_asset(
                url=url,
                hostname=hostname,
                target=target,
            )

        if _is_javascript(
            url=url,
            request=request,
            response=response,
        ):
            if url not in javascript_assets:
                javascript_assets[url] = _build_javascript_asset(
                    url=url,
                    hostname=hostname,
                    target=target,
                )

    urls_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    javascript_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with urls_output.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for url in sorted(url_assets):
            handle.write(
                json.dumps(
                    url_assets[url],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")

    with javascript_output.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for url in sorted(javascript_assets):
            handle.write(
                json.dumps(
                    javascript_assets[url],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")

    return (
        len(url_assets),
        len(javascript_assets),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize Katana JSONL results into "
            "Invar URL and JavaScript assets."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to raw Katana JSONL.",
    )

    parser.add_argument(
        "--urls-output",
        type=Path,
        required=True,
        help="Path to normalized urls.jsonl.",
    )

    parser.add_argument(
        "--javascript-output",
        type=Path,
        required=True,
        help="Path to normalized javascript.jsonl.",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Authorized target domain, for example ikuai8.com.",
    )

    args = parser.parse_args()

    url_count, javascript_count = normalize_katana_results(
        input_path=args.input,
        urls_output=args.urls_output,
        javascript_output=args.javascript_output,
        target=args.target,
    )

    print(f"urls={url_count}")
    print(f"javascript={javascript_count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
