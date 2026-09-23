"""
scan_secrets.py — 前端 JS 敏感信息正则挖掘器（轻量，仅标准库）

用途：遍历 tmp/raw_js/<host>/*.js，用正则提取硬编码的
  1) API Key        2) 云厂商 Secret    3) 测试密码    4) 内网 IP
输出结构化发现报告（JSONL + 控制台汇总），供人工复核后提交漏洞披露平台。

用法：
    python scripts/data/asset/scan_secrets.py
    python scripts/data/asset/scan_secrets.py --root tmp/raw_js \
        --output tmp/secrets_findings.jsonl
"""
from __future__ import annotations

import argparse
import sys
import json
import re
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# 1. 正则规则集（按类别分组；severity 供排序/筛选用）
#    severity: high 高危(可直接提交) > medium > low
# ---------------------------------------------------------------------------
PATTERNS: list[dict[str, object]] = [
    # ---- (1) LLM / 模型 API Key ----
    {
        "category": "llm_api_key",
        "label": "LLM/API Key (OpenAI / Anthropic / Groq / Cohere ...)",
        "severity": "high",
        "regex": [
            r"sk-[A-Za-z0-9]{8,48}-[A-Za-z0-9]{4}",   # OpenAI 新版（带短横线）
            r"sk-[A-Za-z0-9]{20,48}",               # OpenAI 旧版
            r"AIza[0-9A-Za-z_\-]{35}",              # Google / Anthropic
            r"sk-ant-[A-Za-z0-9_\-]{20,}",          # Anthropic Claude
            r"gsk-[A-Za-z0-9]{32,}",               # Groq
            r"cohere-osp-[A-Za-z0-9_\-]{20,}",      # Cohere
        ],
    },
    # ---- (2) 云厂商 Secret ----
    {
        "category": "cloud_secret",
        "label": "云厂商 Secret (AWS / GCP / Azure / RDS)",
        "severity": "high",
        "regex": [
            r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}",        # AWS Access Key ID
            r"aws_secret_access_key\s*=\s*['\"]([A-Za-z0-9/+=]{40})['\"]",  # AWS Secret
            r"aws_db_password\s*=\s*['\"]([A-Za-z0-9/+=]{8,40})['\"]",       # RDS 密码
            r"sql_password\s*=\s*['\"]([A-Za-z0-9\-_]+)['\"]",              # GCP SQL
            r"oauth_client_secret\s*=\s*['\"]([A-Za-z0-9\-_]{1,50})['\"]",   # GCP OAuth
            r"(Server=[^;\"']+;Initial Catalog=[^;\"']+;)",  # Azure 连接串
        ],
    },
    # ---- (3) 测试密码 / 弱口令 ----
    {
        "category": "test_password",
        "label": "测试密码 / 弱口令 (password / passwd / pwd)",
        "severity": "medium",
        "regex": [
            r"(?:password|passwd|pwd|pass)\b[^,;=]{0,24}=\s*['\"]([^\s'\"]{1,256})['\"]",
        ],
    },
    # ---- (4) 内网 IP (RFC 1918 私有段) ----
    {
        "category": "internal_ip",
        "label": "内网 IP (RFC 1918 private range)",
        "severity": "low",
        "regex": [
            r"(?:10|172\.(?:1[6-9]|2[0-9]|3[0-9])|192\.168)\.\d{1,3}\.\d{1,3}",
        ],
    },
]

WEAK_PASSWORDS = {
    "test", "123456", "12345678", "admin", "password", "admin123",
    "1234567", "111111", "000000", "root", "123456789", "qwerty",
    "abc123", "1q2w3e", "123123", "passw0rd", "letmein", "iloveyou",
    "1234", "12345", "1234567890", "zxcvbnm", "123",
}

SEV_RANK = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# 2. 工具函数
# ---------------------------------------------------------------------------
def iter_js_files(root: Path) -> Iterator[Path]:
    """遍历 root，按 host 子目录产出全部 .js 文件（含 .min.js / chunk）。"""
    if not root.exists():
        raise FileNotFoundError(f"raw_js 目录不存在: {root}")
    for host_dir in sorted(root.iterdir()):
        if not host_dir.is_dir():
            continue
        for js_file in sorted(host_dir.glob("*.js")):
            yield js_file


def read_text(path: Path) -> str:
    """尽力读取；解码失败时退化为 latin-1，保证不抛异常。"""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _ip_valid(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    return all(0 <= int(p) <= 255 for p in parts)


def scan_text(text: str, patterns: list[dict[str, object]]) -> list[dict[str, object]]:
    """对单段文本逐规则匹配，产出发现列表。"""
    findings: list[dict[str, object]] = []
    for rule in patterns:
        for regex in rule["regex"]:
            for match in re.finditer(regex, text):
                groups = match.groups()
                value = groups[0] if len(groups) == 1 else match.group(0)
                if len(value) < 4:
                    continue
                if rule["category"] == "internal_ip" and not _ip_valid(value):
                    continue
                start = match.start()
                context = text[max(0, start - 80):start] if start is not None else ""
                findings.append(
                    {
                        "category": rule["category"],
                        "label": rule["label"],
                        "severity": rule["severity"],
                        "value": value,
                        "context": context.strip(),
                    }
                )
    return findings


def scan_js_file(path: Path, js_file: Path) -> list[dict[str, object]]:
    text = read_text(path)
    findings = scan_text(text, PATTERNS)
    for finding in findings:
        finding["file"] = str(js_file)
    return findings


def scan(root: Path, output: Path) -> list[dict[str, object]]:
    """扫描全部 JS，按 (file, value) 去重后落盘 JSONL，返回发现列表。"""
    findings: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for js_file in iter_js_files(root):
        for finding in scan_js_file(js_file, js_file):
            key = (str(js_file), finding["value"])
            if key not in seen:
                seen.add(key)
                findings.append(finding)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for finding in findings:
            handle.write(json.dumps(finding, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")

    return findings


# ---------------------------------------------------------------------------
# 3. 汇总与入口
# ---------------------------------------------------------------------------
def print_summary(findings: list[dict[str, object]], output: Path) -> None:
    by_category: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for f in findings:
        by_category[f["category"]] = by_category.get(f["category"], 0) + 1
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

    print("\n" + "=" * 60)
    print(" 🎯 敏感信息挖掘战报")
    print("=" * 60)
    print(f"  去重后发现总数     : {len(findings)} 条")
    print(f"  ├─ high (高危)     : {by_severity.get('high', 0)}")
    print(f"  ├─ medium (中危)   : {by_severity.get('medium', 0)}")
    print(f"  └─ low (低危)      : {by_severity.get('low', 0)}")
    print("-" * 60)
    for category, count in sorted(by_category.items(), key=lambda kv: -kv[1]):
        print(f"  [{category}] : {count} 条")
    print("=" * 60)
    print(f"  报告已落盘         : {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从 tmp/raw_js 前端 JS 正则挖掘 API Key / 云 Secret / 测试密码 / 内网 IP"
    )
    parser.add_argument(
        "--root",
        default="tmp/raw_js",
        help="raw_js 根目录（默认 tmp/raw_js），结构为 <root>/<host>/*.js",
    )
    parser.add_argument(
        "--output",
        default="tmp/secrets_findings.jsonl",
        help="发现报告输出路径（JSONL，默认 tmp/secrets_findings.jsonl）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="最多输出 N 条发现（0 = 全部）",
    )
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    root = Path(args.root)
    output = Path(args.output)

    findings = scan(root, output)
    findings.sort(key=lambda f: (SEV_RANK.get(f["severity"], 9), f["category"]))

    if args.limit and args.limit > 0:
        findings = findings[: args.limit]

    print_summary(findings, output)

    if not findings:
        print("\n(未发现敏感信息)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
