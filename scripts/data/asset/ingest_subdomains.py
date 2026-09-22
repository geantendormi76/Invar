from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _belongs_to_target(hostname: str, target: str) -> bool:
    return hostname == target or hostname.endswith(f".{target}")


def ingest_subdomains(
    input_path: Path,
    output_path: Path,
    target: str,
    observed_at: datetime,
    changes_path: Path | None = None,
    manifest_path: Path | None = None,
) -> None:
    input_path = Path(input_path)
    output_path = Path(output_path)

    normalized_target = target.strip().lower().rstrip(".")
    if not normalized_target:
        raise ValueError("target must not be empty")

    if changes_path is not None:
        changes_path = Path(changes_path)

    if manifest_path is not None:
        manifest_path = Path(manifest_path)

    hostnames: set[str] = set()

    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        hostname = raw_line.strip().lower().rstrip(".")

        if not hostname:
            continue

        if not _belongs_to_target(hostname, normalized_target):
            continue

        hostnames.add(hostname)

    existing_records: dict[str, dict] = {}

    if output_path.exists():
        for raw_line in output_path.read_text(
            encoding="utf-8"
        ).splitlines():
            line = raw_line.strip()

            if not line:
                continue

            record = json.loads(line)
            asset_id = record["asset_id"]
            existing_records[asset_id] = record

    observed_timestamp = observed_at.isoformat()
    created_changes: list[dict] = []

    observed_asset_ids = {
        f"subdomain:{hostname}"
        for hostname in hostnames
    }

    for hostname in sorted(hostnames):
        asset_id = f"subdomain:{hostname}"
        existing = existing_records.get(asset_id)

        if existing is None:
            existing_records[asset_id] = {
                "asset_id": asset_id,
                "asset_type": "subdomain",
                "hostname": hostname,
                "target": normalized_target,
                "first_seen": observed_timestamp,
                "last_seen": observed_timestamp,
                "status": "active",
            }

            created_changes.append(
                {
                    "change_type": "created",
                    "asset_id": asset_id,
                    "target": normalized_target,
                    "observed_at": observed_timestamp,
                }
            )
            continue

        existing["last_seen"] = observed_timestamp
        existing["status"] = "active"

    for asset_id, record in existing_records.items():
        if asset_id in observed_asset_ids:
            continue

        old_status = record["status"]

        if old_status != "inactive":
            record["status"] = "inactive"

            created_changes.append(
                {
                    "change_type": "status_changed",
                    "asset_id": asset_id,
                    "target": normalized_target,
                    "old_status": old_status,
                    "new_status": "inactive",
                    "observed_at": observed_timestamp,
                }
            )

    manifest = {
        "target": normalized_target,
        "source": "subfinder",
        "asset_type": "subdomain",
        "observed_at": observed_timestamp,
        "status": "completed",
    }

    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        with manifest_path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                json.dumps(
                    manifest,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for asset_id in sorted(existing_records):
            handle.write(
                json.dumps(
                    existing_records[asset_id],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")

    if changes_path is not None and created_changes:
        changes_path.parent.mkdir(parents=True, exist_ok=True)

        with changes_path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            for change in created_changes:
                handle.write(
                    json.dumps(
                        change,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                )
                handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Subfinder results into the Invar Asset Registry."
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Subfinder output TXT file.",
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

    args = parser.parse_args()

    target_dir = args.data_root / args.target.strip().lower().rstrip(".")

    output_path = target_dir / "subdomains.jsonl"
    changes_path = target_dir / "changes.jsonl"
    manifest_path = target_dir / "manifest.jsonl"

    observed_at = datetime.now(timezone.utc)

    ingest_subdomains(
        input_path=args.input,
        output_path=output_path,
        changes_path=changes_path,
        manifest_path=manifest_path,
        target=args.target,
        observed_at=observed_at,
    )

    print(f"target     : {args.target}")
    print(f"input      : {args.input}")
    print(f"subdomains : {output_path}")
    print(f"changes    : {changes_path}")
    print(f"manifest   : {manifest_path}")


if __name__ == "__main__":
    main()
