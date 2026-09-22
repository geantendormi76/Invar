from typing import Any, Dict, List, Optional

from harness.models import EndpointIR, EndpointNotFoundError, EndpointRegistry
from harness.research_models import ResearchExecutionResult
from harness.sandbox_executor import AdaptiveSandboxExecutor


class ResearchTaskAdapter:
    """
    Invar 跨语言研究契约适配器 (Cross-Language Research Contract Adapter)
    负责 Rust 系统主控消息与 Python 专业研究引擎领域模型之间的双向零损耗转译
    """

    @staticmethod
    def task_to_endpoint(
        task: Dict[str, Any],
        registry: Optional[EndpointRegistry] = None,
    ) -> EndpointIR:
        """
        将跨语言 ResearchTask 字典转译为 Python 内部的标准 EndpointIR。
        - 区分 task_id (任务实例 ID) 与 endpoint_id (端点身份契约 ID)；
        - 若提供 EndpointRegistry，通过 endpoint_id 执行权威解析，零损耗复原上游 AST 上下文；
        - 若注册表中缺失该引用，显式抛出 EndpointNotFoundError，杜绝静默产生薄对象；
        - 若未提供 registry，仅在旧测试/纯动态场景下以向后兼容模式生成基线对象。
        """
        method_in_task = str(task.get("method", "")).upper() if "method" in task else ""
        path_in_task = str(task.get("path", "")) if "path" in task else ""

        canonical_route_id = (
            f"{method_in_task}:{path_in_task}"
            if method_in_task and path_in_task
            else ""
        )

        task_id = str(task.get("task_id", ""))
        legacy_id_with_colon = task_id if ":" in task_id else ""

        # 优先级：显式 endpoint_id > 动词路径投影 > 传统冒号格式 case_id / task_id
        endpoint_id = str(
            task.get("endpoint_id")
            or canonical_route_id
            or task.get("case_id")
            or legacy_id_with_colon
            or ""
        )

        if registry is not None:
            if endpoint_id and registry.contains(endpoint_id):
                return registry.get(endpoint_id)
            raise EndpointNotFoundError(
                f"Referenced endpoint '{endpoint_id}' does not exist in canonical EndpointRegistry"
            )

        # 向后兼容模式 (仅当未注入权威注册表时平滑降级)
        method = method_in_task or "GET"
        path = path_in_task or "/"
        return EndpointIR(
            method=method,
            path=path,
            endpoint_id=endpoint_id or f"{method}:{path}",
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
        registry: Optional[EndpointRegistry] = None,
    ) -> Dict[str, Any]:
        """
        承接跨语言单任务调用，驱动沙箱执行器并返回跨语言标准战报
        """
        endpoint = cls.task_to_endpoint(task, registry=registry)
        task_id = str(
            task.get("task_id")
            or task.get("case_id")
            or endpoint.endpoint_id
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
        registry: Optional[EndpointRegistry] = None,
    ) -> List[Dict[str, Any]]:
        """
        承接跨语言批量任务清单，驱动沙箱探测并返回标准战报列表
        """
        return [
            cls.execute_task(
                task=task,
                executor=executor,
                base_url=base_url,
                registry=registry,
            )
            for task in tasks
        ]
