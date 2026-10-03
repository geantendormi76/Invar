# -*- coding: utf-8 -*-
"""
Invar Research Task Context & Hypothesis-Driven Invariant Contract Tests
对齐 Anthropic Reference Harness 与 Tencent AI-Infra-Guard 黄金标准。
断言静态端点事实 (EndpointIR) 与科研任务意图 (ResearchTaskContext) 的严格契约解耦，
确保上游派发的安全假说能够端到端穿透至沙箱层，直接指导安全不变量的建立。
"""

import unittest
from unittest.mock import Mock

from harness.domain_contracts import EndpointIR, SecurityInvariant, ResearchCase
from harness.sandbox_executor import AdaptiveSandboxExecutor
from harness.research_adapter import ResearchTaskAdapter

# 从领域契约统一中枢导入新上下文模型 (RED 预期：当前尚未实现)
try:
    from harness.domain_contracts import ResearchTaskContext
except ImportError:
    ResearchTaskContext = None


class ResearchTaskContextContractTests(unittest.TestCase):
    """
    研究任务上下文与假说驱动安全不变量契约测试集
    """

    def setUp(self) -> None:
        self.raw_task = {
            "task_id": "ikuai8.com:POST:/fs/recursive_move",
            "endpoint_id": "POST:/fs/recursive_move",
            "coverage_id": "api-fs-authorization",
            "hypothesis_id": "H-AUTH-1",
            "profile": "p1_state_mutation_safety",
            "priority": "P1",
            "attack_class": "authorization",
            "method": "POST",
            "path": "/fs/recursive_move",
            "extracted_params": ["source_path", "target_path"],
            "source_file": "cloud.ikuai8.com/chunk.js",
            "source_line": 1,
        }

    def test_01_research_task_context_model_exists_and_isolates_endpoint(self) -> None:
        """【契约 1】ResearchTaskContext 类型存在，且 task_to_endpoint 不被研究意图污染"""
        self.assertIsNotNone(
            ResearchTaskContext,
            "ResearchTaskContext 强类型数据模型必须在 domain_contracts 中声明",
        )

        # 验证从 task 构造上下文
        ctx = ResearchTaskContext.from_task_dict(self.raw_task)
        self.assertEqual(ctx.task_id, "ikuai8.com:POST:/fs/recursive_move")
        self.assertEqual(ctx.hypothesis_id, "H-AUTH-1")
        self.assertEqual(ctx.attack_class, "authorization")
        self.assertEqual(ctx.profile, "p1_state_mutation_safety")
        self.assertEqual(ctx.coverage_id, "api-fs-authorization")

        # 验证 EndpointIR 纯净性：端点事实绝不渗入 hypothesis_id 等任务意图字段
        endpoint = ResearchTaskAdapter.task_to_endpoint(self.raw_task)
        self.assertFalse(hasattr(endpoint, "hypothesis_id"))
        self.assertFalse(hasattr(endpoint, "attack_class"))
        self.assertEqual(endpoint.method, "POST")
        self.assertEqual(endpoint.path, "/fs/recursive_move")

    def test_02_sandbox_mounts_auth_invariant_driven_by_task_context(self) -> None:
        """【契约 2】非 admin 路径只要携带 H-AUTH-1 假说，沙箱必须确定性挂载 auth_boundary 不变量"""
        endpoint = EndpointIR(
            method="POST",
            path="/fs/recursive_move",
            tags=[],  # 无 admin, 无 sensitive-route
            extracted_params=["source_path", "target_path"],
        )

        ctx = None
        if ResearchTaskContext is not None:
            ctx = ResearchTaskContext.from_task_dict(self.raw_task)

        executor = AdaptiveSandboxExecutor()

        # 核心断言：传入 task_context 后，_create_research_case 必须挂载 auth_boundary
        case = executor._create_research_case(endpoint, task_context=ctx)

        invariant_types = [inv.invariant_type for inv in case.invariants]
        self.assertIn(
            "auth_boundary",
            invariant_types,
            "携带有 H-AUTH-1 / authorization 上下文的端点必须挂载 auth_boundary 安全不变量，无论 URL 字符串为何",
        )

    def test_03_adapter_execute_task_forwards_task_context_to_executor(self) -> None:
        """【契约 3】适配器调用 probe_endpoint_with_research 时必须显式透传 task_context"""
        mock_executor = Mock()
        fake_case = ResearchCase(
            case_id="POST:/fs/recursive_move",
            endpoint=EndpointIR(method="POST", path="/fs/recursive_move"),
        )
        mock_result = Mock()
        mock_result.research_case = fake_case
        mock_result.evidence_history = []
        mock_executor.probe_endpoint_with_research.return_value = mock_result

        ResearchTaskAdapter.execute_task(self.raw_task, executor=mock_executor)

        self.assertTrue(mock_executor.probe_endpoint_with_research.called)
        kwargs = mock_executor.probe_endpoint_with_research.call_args.kwargs

        self.assertIn(
            "task_context",
            kwargs,
            "ResearchTaskAdapter.execute_task 必须通过 task_context 关键字参数向执行器传递研究意图",
        )
        self.assertIsNotNone(kwargs.get("task_context"))
        self.assertEqual(kwargs["task_context"].hypothesis_id, "H-AUTH-1")


if __name__ == "__main__":
    unittest.main()
