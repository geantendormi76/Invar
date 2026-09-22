from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable, List, Set
import requests

# 根域名属于目标判断
def belongs_to_target(hostname: str, target: str) -> bool:
    h = hostname.strip().lower().rstrip(".")
    t = target.strip().lower().rstrip(".")
    if not h or not t:
        return False
    return h == t or h.endswith(f".{t}")

# 清洗通配符与非标准字符
def clean_subdomain(candidate: str, target: str) -> str | None:
    c = candidate.strip().lower()
    # 剔除通配符前缀 *.
    if c.startswith("*."):
        c = c[2:]
    c = c.rstrip(".")
    
    # 过滤邮箱、非法字符与非目标域名
    if "@" in c or not c:
        return None
    if not re.match(r"^[a-z0-9._-]+$", c):
        return None
    if not belongs_to_target(c, target):
        return None
    return c

def extract_subdomains_from_crtsh_data(records: Iterable[dict[str, Any]], target: str) -> List[str]:
    """
    解析 crt.sh 响应数据结构：
    - name_value 字段可能包含换行符分隔的 Multi-SAN 域名
    - common_name 包含证书主要公用名
    """
    found: Set[str] = set()
    for item in records:
        if not isinstance(item, dict):
            continue
        
        # 1. 抽取 common_name
        cn = item.get("common_name")
        if isinstance(cn, str):
            cleaned = clean_subdomain(cn, target)
            if cleaned:
                found.add(cleaned)
        
        # 2. 抽取 name_value (Multi-SAN)
        nv = item.get("name_value")
        if isinstance(nv, str):
            for part in nv.splitlines():
                cleaned = clean_subdomain(part, target)
                if cleaned:
                    found.add(cleaned)
                    
    return sorted(found)

def fetch_crtsh_records(target: str, timeout: int = 30, max_retries: int = 3) -> List[dict[str, Any]]:
    """
    向全球公开证书透明度搜索引擎 crt.sh 发起检索
    带指数退避重试，防止上游 504 / 429 熔断
    """
    url = f"https://crt.sh/?q=%.{target}&output=json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Invar-Recon/1.0",
        "Accept": "application/json",
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, list):
                        return data
                    return []
                except json.JSONDecodeError:
                    raise RuntimeError("crt.sh 返回了非合法 JSON 格式正文")
            elif resp.status_code in (429, 502, 503, 504):
                if attempt < max_retries:
                    wait_sec = attempt * 3
                    time.sleep(wait_sec)
                    continue
                resp.raise_for_status()
            else:
                resp.raise_for_status()
        except (requests.RequestException, RuntimeError) as exc:
            if attempt == max_retries:
                raise RuntimeError(f"crt.sh 查询失败（已重试 {max_retries} 次）: {exc}") from exc
            time.sleep(attempt * 3)
    return []

def run_crtsh_harvest(target: str, output_path: Path, timeout: int = 30) -> int:
    target = target.strip().lower().rstrip(".")
    if not target:
        raise ValueError("目标根域名不能为空")
        
    records = fetch_crtsh_records(target, timeout=timeout)
    subdomains = extract_subdomains_from_crtsh_data(records, target)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        for sub in subdomains:
            f.write(f"{sub}\n")
            
    return len(subdomains)

def main() -> int:
    parser = argparse.ArgumentParser(description="Invar 证书透明度日志 (Certificate Transparency) 子域名采集器")
    parser.add_argument("--target", required=True, help="目标根域名，如 ikuai8.com")
    parser.add_argument("--output", type=Path, required=True, help="输出的子域名列表 txt 路径")
    parser.add_argument("--timeout", type=int, default=30, help="网络请求超时时间 (秒)")
    args = parser.parse_args()
    
    count = run_crtsh_harvest(args.target, args.output.resolve(), timeout=args.timeout)
    print(f"target: {args.target}")
    print(f"output: {args.output}")
    print(f"count : {count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
