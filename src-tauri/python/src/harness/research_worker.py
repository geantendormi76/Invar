import json
import sys
from typing import Optional, TextIO

from harness.research_adapter import ResearchTaskAdapter
from harness.sandbox_executor import AdaptiveSandboxExecutor


def run_worker(
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
    executor: Optional[AdaptiveSandboxExecutor] = None,
    base_url: Optional[str] = None,
) -> int:
    """
    Invar 跨语言研究工作者主进程监听器 (Research Worker Process Runner)
    从标准输入读取 ResearchTask JSON，调度研究沙箱，向标准输出回传 ResearchResult JSON
    """
    in_stream = stdin or sys.stdin
    out_stream = stdout or sys.stdout
    err_stream = stderr or sys.stderr
    active_executor = executor or AdaptiveSandboxExecutor()

    raw_input = in_stream.read().strip()
    if not raw_input:
        error_resp = {"error": "Empty input received on stdin"}
        out_stream.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
        out_stream.flush()
        return 1

    try:
        task_payload = json.loads(raw_input)
        if not isinstance(task_payload, dict):
            raise ValueError("Task payload must be a JSON object")
    except Exception as exc:
        error_resp = {"error": f"Invalid JSON input: {str(exc)}"}
        out_stream.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
        out_stream.flush()
        return 1

    try:
        result_dict = ResearchTaskAdapter.execute_task(
            task=task_payload,
            executor=active_executor,
            base_url=base_url,
        )
        out_stream.write(json.dumps(result_dict, ensure_ascii=False) + "\n")
        out_stream.flush()
        return 0
    except Exception as exc:
        error_resp = {"error": f"Execution failure: {str(exc)}"}
        out_stream.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
        out_stream.flush()
        return 1


if __name__ == "__main__":
    sys.exit(run_worker())
