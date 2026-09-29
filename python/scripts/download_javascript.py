#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Invar 前端 JavaScript 物理下载与 SHA256 存证器。"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "Chrome/128.0.0.0 Safari/537.36"
    )
}

JS_EXTENSIONS = (".js", ".mjs", ".cjs")
CHUNK_SIZE = 1024 * 1024


def is_target_host(hostname: str, target: str) -> bool:
    host = (hostname or "").lower().rstrip(".")
    scope = target.lower().rstrip(".")
    return bool(
        host
        and scope
        and (host == scope or host.endswith(f".{scope}"))
    )


def safe_filename(url: str) -> str:
    path_name = Path(urlparse(url).path).name or "index.js"
    clean_name = re.sub(r"[^A-Za-z0-9._-]+", "_", path_name)

    if not clean_name.lower().endswith(JS_EXTENSIONS):
        clean_name += ".js"

    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return f"{digest}_{clean_name}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def destination_path(
    source_url: str,
    output_dir: Path,
) -> tuple[str, Path] | None:
    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").lower().rstrip(".")

    if not hostname:
        return None

    host_dir = output_dir / hostname
    destination = host_dir / safe_filename(source_url)
    return hostname, destination


def is_reusable_download(
    record: dict,
    *,
    target: str,
    output_dir: Path,
) -> bool:
    source_url = record.get("source_url")
    expected_sha256 = record.get("sha256")

    if not isinstance(source_url, str) or not source_url:
        return False

    if not isinstance(expected_sha256, str) or not expected_sha256:
        return False

    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").lower().rstrip(".")

    if not is_target_host(hostname, target):
        return False

    location = destination_path(source_url, output_dir)
    if location is None:
        return False

    _, destination = location

    if not destination.is_file():
        return False

    try:
        return sha256_file(destination) == expected_sha256
    except OSError:
        return False


def fetch_single(
    url: str,
    target: str,
    output_dir: Path,
    timeout: int,
    insecure: bool,
) -> dict:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")

    record = {
        "asset_id": f"javascript:{url}",
        "source_url": url,
        "final_url": url,
        "hostname": hostname,
        "asset_type": "javascript",
        "target": target,
        "status_code": 0,
        "content_type": "",
        "local_path": None,
        "sha256": None,
        "status": "network_error",
        "error": None,
    }

    if not is_target_host(hostname, target):
        record["status"] = "out_of_scope"
        record["error"] = (
            f"Host {hostname} is out of target {target}"
        )
        return record

    try:
        with requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            verify=not insecure,
            allow_redirects=True,
            stream=True,
        ) as response:
            record["status_code"] = response.status_code
            record["content_type"] = (
                response.headers.get("content-type", "")
                .split(";", 1)[0]
                .strip()
                .lower()
            )
            record["final_url"] = response.url

            final_parsed = urlparse(response.url)
            final_hostname = (
                final_parsed.hostname or ""
            ).lower().rstrip(".")

            if not is_target_host(final_hostname, target):
                record["status"] = "out_of_scope"
                record["error"] = (
                    "Redirected outside target scope: "
                    f"{final_hostname}"
                )
                return record

            if response.status_code != 200:
                record["status"] = "http_error"
                record["error"] = (
                    f"HTTP {response.status_code}"
                )
                return record

            location = destination_path(url, output_dir)
            if location is None:
                record["status"] = "network_error"
                record["error"] = "URL has no valid hostname"
                return record

            _, destination = location
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temp_path = destination.with_name(
                destination.name + ".part"
            )

            digest = hashlib.sha256()

            try:
                with temp_path.open("wb") as stream:
                    for chunk in response.iter_content(
                        chunk_size=CHUNK_SIZE
                    ):
                        if not chunk:
                            continue
                        stream.write(chunk)
                        digest.update(chunk)

                temp_path.replace(destination)
            except Exception:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise

            record["local_path"] = str(destination)
            record["sha256"] = digest.hexdigest()
            record["status"] = "downloaded"
            return record

    except Exception as exc:
        record["status"] = "network_error"
        record["error"] = str(exc)
        return record


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Invar 前端 JS 并发物理下载与指纹存证器"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--target",
        required=True,
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
    )
    parser.add_argument(
        "--retry-failed-only",
        action="store_true",
    )

    args = parser.parse_args()

    if args.workers < 1:
        parser.error("--workers 必须 >= 1")

    if args.timeout < 1:
        parser.error("--timeout 必须 >= 1")

    urls: list[str] = []
    seen: set[str] = set()

    with args.input.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as stream:
        for line in stream:
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            source_url = record.get("url")

            if (
                isinstance(source_url, str)
                and source_url
                and source_url not in seen
            ):
                seen.add(source_url)
                urls.append(source_url)

    existing: dict[str, dict] = {}

    if args.retry_failed_only and args.manifest.exists():
        with args.manifest.open(
            "r",
            encoding="utf-8",
            errors="replace",
        ) as stream:
            for line in stream:
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                source_url = record.get("source_url")

                if (
                    isinstance(source_url, str)
                    and record.get("status") == "downloaded"
                    and is_reusable_download(
                        record,
                        target=args.target,
                        output_dir=args.output_dir,
                    )
                ):
                    existing[source_url] = record

    to_download = [
        url for url in urls
        if url not in existing
    ]

    print(
        "[*] 输入总数: "
        f"{len(urls)} | "
        f"跳过已验证下载: {len(existing)} | "
        f"待下载: {len(to_download)}"
    )

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results: dict[str, dict] = dict(existing)

    with ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:
        futures = {
            executor.submit(
                fetch_single,
                url,
                args.target,
                args.output_dir,
                args.timeout,
                args.insecure,
            ): url
            for url in to_download
        }

        for future in as_completed(futures):
            url = futures[future]

            try:
                results[url] = future.result()
            except Exception as exc:
                results[url] = {
                    "source_url": url,
                    "status": "error",
                    "error": str(exc),
                }

    args.manifest.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_manifest = args.manifest.with_name(
        args.manifest.name + ".tmp"
    )

    try:
        with temporary_manifest.open(
            "w",
            encoding="utf-8",
            newline="\r\n",
        ) as stream:
            for url in urls:
                if url in results:
                    stream.write(
                        json.dumps(
                            results[url],
                            ensure_ascii=False,
                        )
                        + "\r\n"
                    )

        temporary_manifest.replace(args.manifest)

    except Exception:
        try:
            temporary_manifest.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    downloaded = sum(
        1
        for record in results.values()
        if record.get("status") == "downloaded"
    )

    failed = len(urls) - downloaded

    print(f"downloaded={downloaded}")
    print(f"failed={failed}")


if __name__ == "__main__":
    main()
