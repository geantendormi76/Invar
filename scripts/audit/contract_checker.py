import sys
import json
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "python" / "packages" / "core" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from harness.config import config
from harness.models import EndpointIR

class TypeRuleInference:
    """
    推导 AST 参数名对应的后端强类型契约标准
    """
    @staticmethod
    def infer_type(param_name: str) -> str:
        p = param_name.lower()
        if p in ["confirm", "is_admin", "active", "enabled", "verified"]:
            return "boolean"
        elif "ids" in p or "list" in p:
            return "array[integer]"
        elif any(k in p for k in ["id", "count", "max", "min", "version", "num", "amount"]):
            return "integer"
        elif any(k in p for k in ["filter", "body", "data", "params", "setting", "config"]):
            return "object"
        else:
            return "string"

class ContractComplianceChecker:
    """
    Invar 强类型契约合规性检测器 (Strongly-typed Contract Compliance Auditor)
    """
    def __init__(self, report_path: Path):
        self.report_path = report_path

    def load_endpoints(self) -> List[EndpointIR]:
        if not self.report_path.exists():
            return []
        with open(self.report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        endpoints_data = data.get("endpoints", [])
        return [EndpointIR.from_dict(e) for e in endpoints_data]

    def audit_endpoint_contract(self, endpoint: EndpointIR) -> Dict[str, Any]:
        params = endpoint.extracted_params
        method = endpoint.method.upper()
        path = endpoint.path.lower()

        type_schema = {p: TypeRuleInference.infer_type(p) for p in params}
        compliance_issues = []
        contract_status = "COMPLIANT"

        if params == ["body"]:
            compliance_issues.append("契约过松：仅定义 generic 'body' 容器，缺乏字段级强类型约束")
            contract_status = "LOOSE_CONTRACT"

        is_destructive = method == "DELETE" or "delete" in path or "batch" in path
        has_confirmation = any(p in params for p in ["confirm", "confirmation_token", "csrf"])

        if is_destructive and not has_confirmation:
            compliance_issues.append("高危动作防护缺失：破坏性接口缺失 'confirm' 校验字段")
            if contract_status == "COMPLIANT":
                contract_status = "NON_COMPLIANT"

        return {
            "method": endpoint.method,
            "path": endpoint.path,
            "risk_score": endpoint.risk_score,
            "extracted_params": params,
            "inferred_type_schema": type_schema,
            "contract_status": contract_status,
            "compliance_issues": compliance_issues,
            "source_file": endpoint.source_file
        }

    def run_audit(self) -> Dict[str, Any]:
        endpoints = self.load_endpoints()
        high_risk = [e for e in endpoints if e.risk_score >= 5.0]
        results = [self.audit_endpoint_contract(e) for e in high_risk]

        compliant_count = sum(1 for r in results if r["contract_status"] == "COMPLIANT")
        loose_count = sum(1 for r in results if r["contract_status"] == "LOOSE_CONTRACT")
        non_compliant_count = sum(1 for r in results if r["contract_status"] == "NON_COMPLIANT")

        return {
            "total_audited": len(results),
            "summary": {
                "compliant_contracts": compliant_count,
                "loose_contracts": loose_count,
                "non_compliant_protection": non_compliant_count
            },
            "audit_details": results
        }

if __name__ == "__main__":
    report_file = ROOT / "tmp" / "test_pipeline_report.json"
    checker = ContractComplianceChecker(report_file)
    audit_report = checker.run_audit()

    print("==================================================")
    print(" 🛡️ Invar 强类型契约合规性审计雷达")
    print("==================================================")
    print(f"  ├─ 🔍 审计高危接口数: {audit_report['total_audited']} 个")
    print(f"  ├─ ✅ 完全合规契约 : {audit_report['summary']['compliant_contracts']} 个")
    print(f"  ├─ ⚠️  松散定义契约 : {audit_report['summary']['loose_contracts']} 个")
    print(f"  └─ 🚨 防护缺失不合规: {audit_report['summary']['non_compliant_protection']} 个\n")

    compliance_output = ROOT / "tmp" / "contract_compliance_report.json"
    with open(compliance_output, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False)
    print(f"[✓] 合规审计结果已保存至: {compliance_output}")
