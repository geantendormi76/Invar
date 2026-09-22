from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_katana_input(
    input_path: Path,
    output_path: Path,
) -> None:
    input_path = Path(input_path)
    output_path = Path(output_path)

    urls: list[str] = []

    for raw_line in input_path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        record = json.loads(line)
        hostname = str(record.get("hostname", "")).strip()

        if not hostname:
            continue

        urls.append(f"https://{hostname}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(urls) + ("\n" if urls else ""),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build Katana URL input from Invar live host assets."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to live_hosts.jsonl.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to Katana URL list.",
    )

    args = parser.parse_args()

    build_katana_input(
        input_path=args.input,
        output_path=args.output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
