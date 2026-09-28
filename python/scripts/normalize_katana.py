#!/usr/bin/env python3
"""Invar 轻量化 Katana 资产归一化解构器 (Canonical Slim Edition)"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

JS_EXTS = {".js", ".mjs", ".cjs"}


def is_target_host(hostname: str, target: str) -> bool:
    h = (hostname or "").lower().rstrip(".")
    t = target.lower().rstrip(".")
    return bool(h and t and (h == t or h.endswith(f".{t}")))


def normalize_katana_results(input_path: Path, urls_output: Path, js_output: Path, target: str) -> tuple[int, int]:
    urls_map, js_map = {}, {}
    with input_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("error"):
                continue

            endpoint = rec.get("request", {}).get("endpoint") or rec.get("endpoint")
            if not isinstance(endpoint, str) or not endpoint.strip():
                continue
            try:
                parts = urlsplit(endpoint.strip())
            except Exception:
                continue
            if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
                continue

            hostname = parts.hostname.lower().rstrip(".")
            if not is_target_host(hostname, target):
                continue

            clean_url = urlunsplit((parts.scheme.lower(), parts.netloc, parts.path, parts.query, ""))
            urls_map[clean_url] = {
                "asset_id": f"url:{clean_url}", "asset_type": "url",
                "url": clean_url, "hostname": hostname, "target": target,
            }

            path_lower = parts.path.lower()
            content_type = str(rec.get("response", {}).get("content_type", "")).lower()
            tag = str(rec.get("request", {}).get("tag", "")).lower()
            if any(path_lower.endswith(ext) for ext in JS_EXTS) or "javascript" in content_type or tag == "script":
                js_map[clean_url] = {
                    "asset_id": f"javascript:{clean_url}", "asset_type": "javascript",
                    "url": clean_url, "hostname": hostname, "target": target,
                }

    urls_output.parent.mkdir(parents=True, exist_ok=True)
    js_output.parent.mkdir(parents=True, exist_ok=True)
    with urls_output.open("w", encoding="utf-8", newline="
") as f:
        for u in sorted(urls_map):
            f.write(json.dumps(urls_map[u], ensure_ascii=False, separators=(",", ":")) + "
")
    with js_output.open("w", encoding="utf-8", newline="
") as f:
        for j in sorted(js_map):
            f.write(json.dumps(js_map[j], ensure_ascii=False, separators=(",", ":")) + "
")
    return len(urls_map), len(js_map)


def main():
    p = argparse.ArgumentParser(description="Katana JSONL 归一化解构为 URL 与 JS 资产")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--urls-output", type=Path, required=True)
    p.add_argument("--javascript-output", type=Path, required=True)
    p.add_argument("--target", required=True)
    args = p.parse_args()
    u, j = normalize_katana_results(args.input, args.urls_output, args.javascript_output, args.target)
    print(f"urls={u}
javascript={j}")


if __name__ == "__main__":
    main()
