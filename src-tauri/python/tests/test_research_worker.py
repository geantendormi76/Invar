import io
import json
import unittest
from unittest.mock import Mock

from harness.models import EndpointIR
from harness.research_models import (
    ResearchCase,
    ResearchDecision,
    ResearchExecutionResult,
)


class ResearchWorkerTests(unittest.TestCase):
    def test_worker_runs_task_from_stdin_and_outputs_json(self) -> None:
        from harness.research_worker import run_worker

        task_payload = {
            "task_id": "POST:/api/orders",
            "method": "POST",
            "path": "/api/orders",
        }

        stdin_stream = io.StringIO(json.dumps(task_payload))
        stdout_stream = io.StringIO()

        fake_endpoint = EndpointIR(method="POST", path="/api/orders")
        fake_case = ResearchCase(case_id="POST:/api/orders", endpoint=fake_endpoint)
        fake_case.record_attempt(
            payload={"order_id": 1},
            status_code=201,
            response_preview='{"ok":true}',
            interpretation="contract passed",
        )
        fake_case.set_decision(
            ResearchDecision(status="confirmed", rationale="contract satisfied")
        )

        fake_exec_result = ResearchExecutionResult(
            evidence=Mock(),
            research_case=fake_case,
            evidence_history=[Mock()],
        )

        mock_executor = Mock()
        mock_executor.probe_endpoint_with_research.return_value = fake_exec_result

        exit_code = run_worker(
            stdin=stdin_stream,
            stdout=stdout_stream,
            executor=mock_executor,
        )

        self.assertEqual(exit_code, 0)
        output_data = json.loads(stdout_stream.getvalue())

        self.assertEqual(output_data["task_id"], "POST:/api/orders")
        self.assertEqual(output_data["status"], "completed")
        self.assertEqual(output_data["attempts"], 1)
        self.assertEqual(
            output_data["decision"],
            {"status": "confirmed", "rationale": "contract satisfied"},
        )
        self.assertEqual(output_data["evidence_history_count"], 1)

    def test_worker_handles_empty_or_malformed_input(self) -> None:
        from harness.research_worker import run_worker

        stdin_stream = io.StringIO("not-a-valid-json")
        stdout_stream = io.StringIO()
        stderr_stream = io.StringIO()

        exit_code = run_worker(
            stdin=stdin_stream,
            stdout=stdout_stream,
            stderr=stderr_stream,
        )

        self.assertNotEqual(exit_code, 0)
        output = stdout_stream.getvalue().strip()
        if output:
            data = json.loads(output)
            self.assertIn("error", data)

    def test_worker_runs_batch_tasks_from_stdin_and_outputs_json_array(self) -> None:
        from harness.research_worker import run_worker

        tasks_payload = [
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

        stdin_stream = io.StringIO(json.dumps(tasks_payload))
        stdout_stream = io.StringIO()

        def fake_probe(endpoint, base_url=None):
            case = ResearchCase(
                case_id=f"{endpoint.method}:{endpoint.path}",
                endpoint=endpoint,
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

        exit_code = run_worker(
            stdin=stdin_stream,
            stdout=stdout_stream,
            executor=mock_executor,
        )

        self.assertEqual(exit_code, 0)
        output_data = json.loads(stdout_stream.getvalue())

        self.assertIsInstance(output_data, list)
        self.assertEqual(len(output_data), 2)
        self.assertEqual(output_data[0]["task_id"], "GET:/api/users")
        self.assertEqual(output_data[0]["status"], "completed")
        self.assertEqual(output_data[1]["task_id"], "POST:/api/orders")
        self.assertEqual(output_data[1]["status"], "completed")
