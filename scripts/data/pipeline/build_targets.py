import re
import argparse
from pathlib import Path

# 动态绑定环境
ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT / "python" / "packages" / "core" / "src"
import sys
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from harness.exporter import EndpointExporter

def build_scanner_targets(input_json_path: Path, nuclei_out: Path, ffuf_out: Path):
    if not input_json_path.exists():
        print(f"[X] 错误: 输入 JSON 文件不存在: {input_json_path}")
        return

    endpoints = EndpointExporter.from_json_file(input_json_path)
    nuclei_urls = set()
    ffuf_urls = set()

    for ep in endpoints:
        source_file = ep.source_file
        raw_path = ep.path

        # 1. 域名归一化映射 (支持根据来源文件名推导子域名)
        domain = "https://www.dieqiyun.top"
        if "jiankong" in source_file:
            domain = "https://jiankong.dieqiyun.top"
        elif "hao" in source_file:
            domain = "https://hao.dieqiyun.top"

        # 2. 清洗前端未展开模板变量 (如 ${Y})
        clean_path = re.sub(r'^\$\{Y\}', '', raw_path)
        if not clean_path.startswith('/'):
            clean_path = '/' + clean_path

        # 3. 动态占位符分流 (Nuclei 用静态探测值 '1', FFUF 用爆破占位符 'FUZZ')
        if ep.is_dynamic or "${" in clean_path:
            fuzz_path = re.sub(r'\$\{[^}]+\}', 'FUZZ', clean_path)
            static_path = re.sub(r'\$\{[^}]+\}', '1', clean_path)
            ffuf_urls.add(f"{domain}{fuzz_path}")
            nuclei_urls.add(f"{domain}{static_path}")
        else:
            nuclei_urls.add(f"{domain}{clean_path}")

    nuclei_out.parent.mkdir(parents=True, exist_ok=True)
    ffuf_out.parent.mkdir(parents=True, exist_ok=True)

    nuclei_out.write_text("\n".join(sorted(list(nuclei_urls))), encoding="utf-8")
    ffuf_out.write_text("\n".join(sorted(list(ffuf_urls))), encoding="utf-8")

    print("==================================================")
    print(" 🎯 Invar 扫描探针目标清单构建完成")
    print("==================================================")
    print(f"  ├─ 📦 读取 Endpoint 总数 : {len(endpoints)} 条")
    print(f"  ├─ 🔭 Nuclei 静态探针目标: {len(nuclei_urls)} 条 -> {nuclei_out}")
    print(f"  └─ 💣 FFUF 动态爆破目标  : {len(ffuf_urls)} 条 -> {ffuf_out}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Invar 扫描器目标构建器 (Nuclei & FFUF)")
    parser.add_argument("-i", "--input", default="tmp/test_pipeline_report.json", help="输入的 API JSON 报告路径")
    parser.add_argument("--nuclei", default="tmp/nuclei_targets.txt", help="Nuclei 目标文件输出路径")
    parser.add_argument("--ffuf", default="tmp/ffuf_targets.txt", help="FFUF 目标文件输出路径")

    args = parser.parse_args()
    build_scanner_targets(Path(args.input), Path(args.nuclei), Path(args.ffuf))
