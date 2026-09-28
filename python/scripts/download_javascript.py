#!/usr/bin/env python3
"""Invar 轻量化前端 JS 物理下载与存证器 (Canonical Slim Edition)"""
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
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36"}


def is_target_host(hostname: str, target: str) -> bool:
    h, t = (hostname or "").lower().rstrip("."), target.lower().rstrip(".")
    return bool(h and t and (h == t or h.endswith(f".{t}")))


def safe_filename(url: str) -> str:
    path_name = Path(urlparse(url).path).name or "index.js"
    clean_name = re.sub(r"[^A-Za-z0-9._-]+", "_", path_name)
    if not clean_name.lower().endswith((".js", ".mjs", ".cjs")):
        clean_name += ".js"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return f"{digest}_{clean_name}"


def fetch_single(url: str, target: str, output_dir: Path, timeout: int, insecure: bool) -> dict:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    rec = {
        "asset_id": f"javascript:{url}", "source_url": url, "final_url": url,
        "hostname": hostname, "asset_type": "javascript", "target": target,
        "status_code": 0, "content_type": "", "local_path": None, "sha256": None,
        "status": "network_error", "error": None,
    }
    if not is_target_host(hostname, target):
        rec["status"], rec["error"] = "out_of_scope", f"Host {hostname} is out of target {target}"
        return rec

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, verify=not insecure)
        rec["status_code"] = resp.status_code
        rec["content_type"] = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        rec["final_url"] = resp.url
        if resp.status_code != 200:
            rec["status"], rec["error"] = "http_error", f"HTTP {resp.status_code}"
            return rec

        host_dir = output_dir / hostname
        host_dir.mkdir(parents=True, exist_ok=True)
        dest = host_dir / safe_filename(url)
        dest.write_bytes(resp.content)
        rec["local_path"] = str(dest)
        rec["sha256"] = hashlib.sha256(resp.content).hexdigest()
        rec["status"] = "downloaded"
    except Exception as exc:
        rec["error"] = str(exc)
    return rec


def main():
    p = argparse.ArgumentParser(description="Invar 前端 JS 并发物理下载与指纹存证器")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--timeout", type=int, default=15)
    p.add_argument("--insecure", action="store_true")
    p.add_argument("--retry-failed-only", action="store_true")
    args = p.parse_args()

    urls, seen = [], set()
    with args.input.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                try:
                    u = json.loads(line).get("url")
                    if u and u not in seen:
                        seen.add(u); urls.append(u)
                except Exception:
                    pass

    existing = {}
    if args.retry_failed_only and args.manifest.exists():
        with args.manifest.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        if r.get("source_url") and r.get("status") == "downloaded":
                            existing[r["source_url"]] = r
                    except Exception:
                        pass

    to_dl = [u for u in urls if u not in existing]
    print(f"[*] 输入总数: {len(urls)} | 跳过已下载: {len(existing)} | 待下载: {len(to_dl)}")
    results = dict(existing)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futs = {executor.submit(fetch_single, u, args.target, args.output_dir, args.timeout, args.insecure): u for u in to_dl}
        for fut in as_completed(futs):
            u = futs[fut]
            try:
                results[u] = fut.result()
            except Exception as e:
                results[u] = {"source_url": u, "status": "error", "error": str(e)}

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", encoding="utf-8", newline="
") as f:
        for u in urls:
            if u in results:
                f.write(json.dumps(results[u], ensure_ascii=False) + "
")
    downloaded = sum(1 for r in results.values() if r.get("status") == "downloaded")
    print(f"downloaded={downloaded}
failed={len(urls) - downloaded}")


if __name__ == "__main__":
    main()
