from typing import Any, Dict, List, Optional

from harness.models import EndpointIR
from harness.research_models import ResearchExecutionResult
from harness.sandbox_executor import AdaptiveSandboxExecutor


class ResearchTaskAdapter:
    """
    Invar 跨语言研究契约适配器 (Cross-Language Research Contract Adapter)
    负责 Rust 系统主控消息与 Python 专业研究引擎领域模型之间的双向零损耗转译
    """

    @staticmethod
    def task_to_endpoint(task: Dict[str, Any]) -> EndpointIR:
        """
        将跨语言 ResearchTask 字典转译为 Python 内部的标准 EndpointIR
        """
        method = str(task.get("method", "GET")).upper()
        path = str(task.get("path", "/"))
        return EndpointIR(
            method=method,
            path=path,
        )

    @staticmethod
    def result_to_dict(
        execution_result: ResearchExecutionResult,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        将 Python ResearchExecutionResult 收敛为符合 Rust ResearchResult 强类型契约的标准字典
        """
        case = execution_result.research_case
        effective_task_id = task_id or case.case_id

        decision_dict: Optional[Dict[str, str]] = None
        if case.decision is not None:
            status = "completed"
            decision_dict = {
                "status": case.decision.status,
                "rationale": case.decision.rationale,
            }
        else:
            status = "inconclusive"

        return {
            "task_id": effective_task_id,
            "status": status,
            "attempts": len(case.attempts),
            "decision": decision_dict,
            "evidence_history_count": len(execution_result.evidence_history),
        }

    @classmethod
    def execute_task(
        cls,
        task: Dict[str, Any],
        executor: AdaptiveSandboxExecutor,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        承接跨语言单任务调用，驱动沙箱执行器并返回跨语言标准战报
        """
        endpoint = cls.task_to_endpoint(task)
        task_id = str(
            task.get("task_id")
            or task.get("case_id")
            or f"{endpoint.method}:{endpoint.path}"
        )
        execution_result = executor.probe_endpoint_with_research(
            endpoint,
            base_url=base_url,
        )
        return cls.result_to_dict(execution_result, task_id=task_id)

    @classmethod
    def execute_batch(
        cls,
        tasks: List[Dict[str, Any]],
        executor: AdaptiveSandboxExecutor,
        base_url: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        承接跨语言批量任务清单，以热态单进程环境驱动沙箱探测并返回标准战报列表
        """
        return [
            cls.execute_task(task=task, executor=executor, base_url=base_url)
            for task in tasks
        ]
