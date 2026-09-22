import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class AstWorkerTests(unittest.TestCase):
    def test_ast_worker_extracts_tasks_from_code(self) -> None:
        from harness.ast_worker import run_ast_worker

        js_code = """
        fetch('/api/users', { method: 'GET' });
        axios.post('/api/orders');
        """
        stdin_stream = io.StringIO(json.dumps({"code": js_code}))
        stdout_stream = io.StringIO()

        exit_code = run_ast_worker(
            stdin=stdin_stream,
            stdout=stdout_stream,
        )

        self.assertEqual(exit_code, 0)
        output_data = json.loads(stdout_stream.getvalue())

        self.assertIsInstance(output_data, list)
        self.assertEqual(len(output_data), 2)
        task_ids = [t["task_id"] for t in output_data]
        self.assertIn("GET:/api/users", task_ids)
        self.assertIn("POST:/api/orders", task_ids)

    def test_ast_worker_extracts_tasks_from_file_path(self) -> None:
        from harness.ast_worker import run_ast_worker

        js_code = "fetch('/api/products', { method: 'GET' });"
        with TemporaryDirectory() as temp_dir:
            target_file = Path(temp_dir) / "app.js"
            target_file.write_text(js_code, encoding="utf-8")

            stdin_stream = io.StringIO(json.dumps({"target_path": str(target_file)}))
            stdout_stream = io.StringIO()

            exit_code = run_ast_worker(
                stdin=stdin_stream,
                stdout=stdout_stream,
            )

            self.assertEqual(exit_code, 0)
            output_data = json.loads(stdout_stream.getvalue())
            self.assertEqual(len(output_data), 1)
            self.assertEqual(output_data[0]["task_id"], "GET:/api/products")
            self.assertEqual(output_data[0]["method"], "GET")
            self.assertEqual(output_data[0]["path"], "/api/products")
