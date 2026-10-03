import unittest
from unittest.mock import Mock

from harness.models import EndpointIR
from harness.research_models import (
    ProbeAttempt,
    ResearchCase,
    ResearchDecision,
    ResearchExecutionResult,
)


class ResearchTaskAdapterTests(unittest.TestCase):
    def test_task_to_endpoint_converts_core_routing_fields(self) -> None:
        from harness.research_adapter import ResearchTaskAdapter

        task = {
            "task_id": "POST:/api/orders",
            "method": "POST",
            "path": "/api/orders",
        }

        endpoint = ResearchTaskAdapter.task_to_endpoint(task)

        self.assertIsInstance(endpoint, EndpointIR)
        self.assertEqual(endpoint.method, "POST")
        self.assertEqual(endpoint.path, "/api/orders")

    def test_result_to_dict_matches_rust_result_contract(self) -> None:
        from harness.research_adapter import ResearchTaskAdapter

        endpoint = EndpointIR(method="POST", path="/api/orders")
        case = ResearchCase(case_id="POST:/api/orders", endpoint=endpoint)
        case.record_attempt(
            payload={"id": 1},
            status_code=400,
            response_preview="validation failed",
            interpretation="missing field",
            mutation_reason="add field",
        )
        case.record_attempt(
            payload={"id": 1, "name": "test"},
            status_code=200,
            response_preview='{"ok":true}',
            interpretation="contract passed",
        )
        case.set_decision(
            ResearchDecision(status="confirmed", rationale="contract met")
        )

        exec_result = ResearchExecutionResult(
            evidence=Mock(),
            research_case=case,
            evidence_history=[Mock(), Mock()],
        )

        result_dict = ResearchTaskAdapter.result_to_dict(
            exec_result,
            task_id="POST:/api/orders",
        )

        self.assertEqual(result_dict["task_id"], "POST:/api/orders")
        self.assertEqual(result_dict["status"], "completed")
        self.assertEqual(result_dict["attempts"], 2)
        self.assertEqual(
            result_dict["decision"],
            {"status": "confirmed", "rationale": "contract met"},
        )
        self.assertEqual(result_dict["evidence_history_count"], 2)

    def test_result_to_dict_handles_unresolved_decision(self) -> None:
        from harness.research_adapter import ResearchTaskAdapter

        endpoint = EndpointIR(method="GET", path="/api/health")
        case = ResearchCase(case_id="GET:/api/health", endpoint=endpoint)
        case.record_attempt(
            payload={},
            status_code=500,
            response_preview="server error",
        )

        exec_result = ResearchExecutionResult(
            evidence=Mock(),
            research_case=case,
            evidence_history=[Mock()],
        )

        result_dict = ResearchTaskAdapter.result_to_dict(
            exec_result,
            task_id="GET:/api/health",
        )

        self.assertEqual(result_dict["task_id"], "GET:/api/health")
        self.assertEqual(result_dict["status"], "inconclusive")
        self.assertEqual(result_dict["attempts"], 1)
        self.assertIsNone(result_dict["decision"])
        self.assertEqual(result_dict["evidence_history_count"], 1)

    def test_execute_batch_processes_multiple_tasks_and_returns_list_of_results(
        self,
    ) -> None:
        from harness.research_adapter import ResearchTaskAdapter

        tasks = [
            {
                "task_id": "GET:/api/users",
                "method": "GET",
                "path": "/api/users",
            },
            {
                "task_id": "POST:/api/orders",
                "method": "POST",
                "path": "/api/orders",
            },
        ]

        def fake_probe(endpoint, base_url=None, task_context=None):
            case = ResearchCase(
                case_id=f"{endpoint.method}:{endpoint.path}",
                endpoint=endpoint,
                task_context=task_context,
            )
            case.record_attempt(
                payload={},
                status_code=200,
                response_preview='{"ok":true}',
            )
            case.set_decision(
                ResearchDecision(status="confirmed", rationale="probe ok")
            )
            return ResearchExecutionResult(
                evidence=Mock(),
                research_case=case,
                evidence_history=[Mock()],
            )

        mock_executor = Mock()
        mock_executor.probe_endpoint_with_research.side_effect = fake_probe

        results = ResearchTaskAdapter.execute_batch(
            tasks=tasks,
            executor=mock_executor,
        )

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["task_id"], "GET:/api/users")
        self.assertEqual(results[0]["status"], "completed")
        self.assertEqual(results[1]["task_id"], "POST:/api/orders")
        self.assertEqual(results[1]["status"], "completed")
