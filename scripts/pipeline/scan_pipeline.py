import os
import sys
import json
import argparse
from pathlib import Path

# 动态绑定 Monorepo 内的 Python 核心包路径
ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src-tauri" / "python" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from harness.config import config
from harness.models import EndpointIR
from harness.extractor import JSEndpointExtractor
from harness.exporter import EndpointExporter
from harness.sandbox_executor import AdaptiveSandboxExecutor
from agent.risk_engine import RiskEngine

def main():
    parser = argparse.ArgumentParser(description="Invar 工业级自动化 Web API 逆向与闭环审计流水线")
    parser.add_argument("target", help="目标 JS 文件或包含 JS 文件的目录路径")
    parser.add_argument("-o", "--output", default="tmp/invar_audit_report.json", help="输出全量审计凭证链报告路径")
    parser.add_argument("--probe", action="store_true", help="是否启动闭环自适应沙箱探针")
    parser.add_argument("--base-url", default=None, help="覆盖默认的目标网关 API 基地址")

    args = parser.parse_args()
    target_path = Path(args.target)

    if not target_path.exists():
        print(f"[X] 错误: 目标路径 '{args.target}' 不存在！")
        sys.exit(1)

    print("==================================================")
    print(" 🛡️ Invar 全链路自动化逆向与闭环安全流水线启动")
    print("==================================================")
    print(f"  ├─ 目标资产路径: {target_path.resolve()}")
    print(f"  ├─ 沙箱探针模式: {'⚡ 已启用 (包含自愈变异循环)' if args.probe else '🔒 未启用 (仅做静态分析)'}")
    print(f"  └─ 产出报告目标: {args.output}\n")

    # 1. 确定性静态 AST 解析
    extractor = JSEndpointExtractor()
    raw_endpoints = []
    if target_path.is_file():
        raw_endpoints = extractor.parse_file(target_path)
    else:
        for js_file in target_path.rglob("*.js"):
            raw_endpoints.extend(extractor.parse_file(js_file))

    print(f"[+] [阶段 1: AST 解析] 成功提取原始 API 节点: {len(raw_endpoints)} 个")

    # 2. 多维风险量化评估
    evaluated = RiskEngine.evaluate_all(raw_endpoints)
    param_rich_count = sum(1 for e in evaluated if len(e.extracted_params) > 0)
    print(f"[+] [阶段 2: 威胁评估] 完成量化打分，成功下潜剥离参数字典的接口: {param_rich_count} 个")

    # 3. 自适应闭环沙箱探测 (可选)
    evidences = []
    if args.probe:
        print(f"[*] [阶段 3: 闭环探针] 正在并发执行自适应探测 (最大变异重试: {config.max_mutation_rounds} 轮)...")
        executor = AdaptiveSandboxExecutor()
        evidences = executor.probe_all(evaluated, base_url=args.base_url)
        print(f"[+] [阶段 3: 闭环探针] 探测结束，捕获有效凭证记录: {len(evidences)} 条")

    # 4. 全量结构化战报持久化
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "summary": {
            "total_endpoints": len(evaluated),
            "param_rich_endpoints": param_rich_count,
            "critical_risk_count": sum(1 for e in evaluated if "risk-critical" in e.tags),
            "high_risk_count": sum(1 for e in evaluated if "risk-high" in e.tags),
            "medium_risk_count": sum(1 for e in evaluated if "risk-medium" in e.tags),
            "evidence_records_captured": len(evidences)
        },
        "endpoints": [e.to_dict() for e in evaluated],
        "evidences": [record.to_dict() for record in evidences]
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print("\n==================================================")
    print(" 🎯 Invar 自动化流水线任务总览")
    print("==================================================")
    print(f"  ├─ 📦 提炼 API 节点总数   : {len(evaluated)} 个")
    print(f"  ├─ 🎯 剥离具体参数接口数 : {param_rich_count} 个")
    print(f"  ├─ 🚨 严重高危 (CRITICAL) : {report_data['summary']['critical_risk_count']} 个")
    print(f"  ├─ ⚠️  高风险 (HIGH)       : {report_data['summary']['high_risk_count']} 个")
    print(f"  ├─ 🔬 捕获完整快照凭证   : {len(evidences)} 条")
    print(f"  └─ 📄 全量战报文件已保存 : {output_path.resolve()}")
    print("==================================================\n")

if __name__ == "__main__":
    main()
