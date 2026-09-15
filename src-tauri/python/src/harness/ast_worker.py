import json
import sys
from pathlib import Path
from typing import Optional, TextIO

from harness.extractor import JSEndpointExtractor


def run_ast_worker(
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
    extractor: Optional[JSEndpointExtractor] = None,
) -> int:
    """
    Invar 前端静态 AST 提取器进程监听器 (AST Extractor Process Worker)
    从标准输入接收代码文本或目标文件路径，利用 Tree-sitter 提炼 API 端点，向标准输出回传 ResearchTask 列表
    """
    in_stream = stdin or sys.stdin
    out_stream = stdout or sys.stdout
    err_stream = stderr or sys.stderr
    active_extractor = extractor or JSEndpointExtractor()

    raw_input = in_stream.read().strip()
    if not raw_input:
        error_resp = {"error": "Empty input received on stdin"}
        out_stream.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
        out_stream.flush()
        return 1

    try:
        payload = json.loads(raw_input)
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a JSON object")
    except Exception as exc:
        error_resp = {"error": f"Invalid JSON input: {str(exc)}"}
        out_stream.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
        out_stream.flush()
        return 1

    endpoints = []
    target_path = payload.get("target_path")
    code = payload.get("code")

    try:
        if target_path:
            p = Path(target_path)
            if p.is_file():
                endpoints = active_extractor.parse_file(p)
            elif p.is_dir():
                for js_file in p.rglob("*.js"):
                    endpoints.extend(active_extractor.parse_file(js_file))
            else:
                error_resp = {"error": f"Target path does not exist: {target_path}"}
                out_stream.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
                out_stream.flush()
                return 1
        elif code is not None:
            endpoints = active_extractor.parse_code(str(code))
        else:
            error_resp = {"error": "JSON must contain 'target_path' or 'code'"}
            out_stream.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
            out_stream.flush()
            return 1
    except Exception as exc:
        error_resp = {"error": f"Extraction failure: {str(exc)}"}
        out_stream.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
        out_stream.flush()
        return 1

    # 幂等去重并收敛为符合 Rust ResearchTask 强类型契约的标准字典
    seen = set()
    tasks = []
    for ep in endpoints:
        normalized_method = ep.method.upper()
        normalized_path = ep.path
        dedup_key = (normalized_method, normalized_path)
        if dedup_key not in seen:
            seen.add(dedup_key)
            tasks.append({
                "task_id": f"{normalized_method}:{normalized_path}",
                "method": normalized_method,
                "path": normalized_path,
            })

    out_stream.write(json.dumps(tasks, ensure_ascii=False) + "\n")
    out_stream.flush()
    return 0


if __name__ == "__main__":
    sys.exit(run_ast_worker())
