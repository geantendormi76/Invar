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
