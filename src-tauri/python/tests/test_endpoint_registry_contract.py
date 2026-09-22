import unittest
from unittest.mock import Mock

from harness.models import EndpointIR, EndpointNotFoundError, EndpointRegistry
from harness.research_adapter import ResearchTaskAdapter
from harness.research_models import ResearchCase, ResearchExecutionResult


class EndpointRegistryContractTests(unittest.TestCase):
    def setUp(self):
        self.rich_endpoint = EndpointIR(
            method="POST",
            path="/api/v3/authConf/saveAuth",
            endpoint_id="POST:/api/v3/authConf/saveAuth",
            source_file="frontend/src/views/auth/config.js",
            line=142,
            is_dynamic=False,
            extracted_params=["auth_type", "secret_key", "confirm"],
            tags=["sensitive-route", "admin", "state-changing"],
            risk_score=8.5,
            confidence=0.98,
            call_signature="client.post('/api/v3/authConf/saveAuth', data)",
        )
        self.registry = EndpointRegistry()
        self.registry.register(self.rich_endpoint)

    def test_canonical_resolution_preserves_provenance(self):
        """断言 ①：源码文件路径、精确代码行号与调用签名零损耗存活"""
        task = {
            "task_id": "TASK-001",
            "endpoint_id": "POST:/api/v3/authConf/saveAuth",
            "method": "POST",
            "path": "/api/v3/authConf/saveAuth",
        }
        resolved = ResearchTaskAdapter.task_to_endpoint(task, registry=self.registry)

        self.assertEqual(resolved.source_file, "frontend/src/views/auth/config.js")
        self.assertEqual(resolved.line, 142)
        self.assertEqual(resolved.call_signature, "client.post('/api/v3/authConf/saveAuth', data)")

    def test_canonical_resolution_preserves_extracted_parameters(self):
        """断言 ②：上游 AST 提炼出的业务字段参数零损耗存活，杜绝盲发包"""
        task = {
            "task_id": "TASK-002",
            "endpoint_id": "POST:/api/v3/authConf/saveAuth",
        }
        resolved = ResearchTaskAdapter.task_to_endpoint(task, registry=self.registry)

        self.assertEqual(resolved.extracted_params, ["auth_type", "secret_key", "confirm"])

    def test_canonical_resolution_preserves_tags_and_risk_score(self):
        """断言 ③：接口风险打分与威胁标签零损耗存活，不被重置为默认值"""
        task = {
            "task_id": "TASK-003",
            "endpoint_id": "POST:/api/v3/authConf/saveAuth",
        }
        resolved = ResearchTaskAdapter.task_to_endpoint(task, registry=self.registry)

        self.assertEqual(resolved.risk_score, 8.5)
        self.assertIn("sensitive-route", resolved.tags)
        self.assertIn("admin", resolved.tags)

    def test_missing_reference_fails_explicitly(self):
        """断言 ④：引用的 endpoint_id 若不存在，显式抛出异常，严禁造假制造薄对象"""
        non_existent_task = {
            "task_id": "TASK-999",
            "endpoint_id": "DELETE:/api/non_existent",
        }
        with self.assertRaises(EndpointNotFoundError) as ctx:
            ResearchTaskAdapter.task_to_endpoint(non_existent_task, registry=self.registry)

        self.assertIn("DELETE:/api/non_existent", str(ctx.exception))

    def test_backward_compatibility_when_registry_omitted(self):
        """向后兼容保障：在未注入注册表的旧代码路径中仍可平滑降级"""
        legacy_task = {
            "task_id": "LEGACY-001",
            "method": "GET",
            "path": "/api/legacy",
        }
        endpoint = ResearchTaskAdapter.task_to_endpoint(legacy_task, registry=None)
        self.assertEqual(endpoint.method, "GET")
        self.assertEqual(endpoint.path, "/api/legacy")
        self.assertEqual(endpoint.endpoint_id, "GET:/api/legacy")


if __name__ == "__main__":
    unittest.main()
