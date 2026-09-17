from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


def _belongs_to_target(hostname: str, target: str) -> bool:
    return hostname == target or hostname.endswith(f".{target}")


def _read_active_subdomains(
    input_path: Path,
    target: str,
) -> list[str]:
    normalized_target = target.strip().lower().rstrip(".")
    if not normalized_target:
        raise ValueError("target must not be empty")

    hostnames: set[str] = set()

    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line:
            continue

        record = json.loads(line)

        if record.get("status", "active") != "active":
            continue

        hostname = str(record.get("hostname", "")).strip().lower().rstrip(".")

        if not hostname:
            continue

        if not _belongs_to_target(hostname, normalized_target):
            continue

        hostnames.add(hostname)

    return sorted(hostnames)


def ingest_httpx(
    input_path: Path,
    output_path: Path,
    target: str,
) -> None:
    input_path = Path(input_path)
    output_path = Path(output_path)

    normalized_target = target.strip().lower().rstrip(".")
    if not normalized_target:
        raise ValueError("target must not be empty")

    hostnames: set[str] = set()

    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line:
            continue

        record = json.loads(line)
        url = str(record.get("url", "")).strip()

        if not url:
            continue

        parsed = urlparse(url)
        hostname = (parsed.hostname or "").strip().lower().rstrip(".")

        if not hostname:
            continue

        if not _belongs_to_target(hostname, normalized_target):
            continue

        hostnames.add(hostname)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for hostname in sorted(hostnames):
            record = {
                "asset_id": f"host:{hostname}",
                "asset_type": "host",
                "hostname": hostname,
                "target": normalized_target,
            }

            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")


def run_httpx(
    subdomains_path: Path,
    httpx_output_path: Path,
    target: str,
    httpx_binary: str = "httpx",
) -> int:
    hostnames = _read_active_subdomains(
        input_path=subdomains_path,
        target=target,
    )

    if not hostnames:
        raise ValueError("no active subdomain assets found")

    httpx_output_path = Path(httpx_output_path)
    httpx_output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="invar-httpx-") as temp_dir:
        host_list_path = Path(temp_dir) / "hosts.txt"

        host_list_path.write_text(
            "\n".join(hostnames) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        command = [
            httpx_binary,
            "-l",
            str(host_list_path),
            "-json",
            "-silent",
            "-o",
            str(httpx_output_path),
        ]

        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            raise RuntimeError(
                f"HTTPX failed with exit code "
                f"{completed.returncode}: {stderr}"
            )

    return len(hostnames)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read Invar subdomains.jsonl, run HTTPX, "
            "and build live_hosts.jsonl."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to subdomains.jsonl.",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Authorized root domain.",
    )

    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data") / "targets",
        help="Persistent asset data root.",
    )

    parser.add_argument(
        "--httpx-bin",
        default="httpx",
        help="HTTPX executable name or full path.",
    )

    parser.add_argument(
        "--httpx-output",
        type=Path,
        default=None,
        help="Optional raw HTTPX JSONL output path.",
    )

    args = parser.parse_args()

    target = args.target.strip().lower().rstrip(".")
    target_dir = args.data_root / target

    live_hosts_path = target_dir / "live_hosts.jsonl"

    raw_httpx_path = args.httpx_output
    if raw_httpx_path is None:
        raw_httpx_path = target_dir / "httpx.jsonl"

    host_count = run_httpx(
        subdomains_path=args.input,
        httpx_output_path=raw_httpx_path,
        target=target,
        httpx_binary=args.httpx_bin,
    )

    ingest_httpx(
        input_path=raw_httpx_path,
        output_path=live_hosts_path,
        target=target,
    )

    live_hosts = [
        line
        for line in live_hosts_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    print(f"target        : {target}")
    print(f"input         : {args.input}")
    print(f"active inputs : {host_count}")
    print(f"httpx output  : {raw_httpx_path}")
    print(f"live hosts    : {live_hosts_path}")
    print(f"live count    : {len(live_hosts)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
