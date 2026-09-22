import json
import tempfile
import unittest
from pathlib import Path

from harness.run_models import (
    ExecutionPolicy,
    IllegalStateTransitionError,
    ResearchRun,
    ResearchScope,
    RunBudget,
    RunProfile,
    RunStatus,
    SourceRef,
)


class ResearchRunTests(unittest.TestCase):
    def setUp(self):
        self.scope = ResearchScope(
            target_domain="ikuai8.com",
            included_subdomains=["api.ikuai8.com"],
            excluded_paths=["/api/v1/logout"],
            allowed_methods=["GET", "POST"],
        )
        self.source_ref = SourceRef(
            vcs="git",
            commit="a1b2c3d4e5f6",
            worktree_dirty=False,
            raw_input_hash=SourceRef.compute_sha256("console.log('test')"),
        )
        self.run = ResearchRun(
            run_id="RUN-20260918-001",
            target_root="data/targets/ikuai8.com",
            scope=self.scope,
            source_ref=self.source_ref,
            budget=RunBudget(max_tasks=50, max_requests=200),
        )

    def test_run_initial_state_is_init(self):
        self.assertEqual(self.run.status, RunStatus.INIT)
        self.assertIsNotNone(self.run.started_at)
        self.assertIsNone(self.run.completed_at)

    def test_legal_lifecycle_transitions_sequence(self):
        """验证合法的科研生命周期单向跃迁链条"""
        self.run.transition_to(RunStatus.SCOPE_VERIFIED)
        self.assertEqual(self.run.status, RunStatus.SCOPE_VERIFIED)

        self.run.transition_to(RunStatus.CONTEXT_READY)
        self.assertEqual(self.run.status, RunStatus.CONTEXT_READY)

        self.run.transition_to(RunStatus.PLAN_READY)
        self.run.transition_to(RunStatus.EXECUTING)
        self.run.transition_to(RunStatus.EVIDENCE_COLLECTED)
        self.run.transition_to(RunStatus.EVALUATED)
        self.run.transition_to(RunStatus.REPORT_READY)
        self.run.transition_to(RunStatus.COMPLETED)

        self.assertEqual(self.run.status, RunStatus.COMPLETED)
        self.assertIsNotNone(self.run.completed_at)

    def test_illegal_jump_transition_is_strictly_blocked(self):
        """验证铁律：严禁从 INIT 直接跃迁至 COMPLETED 或 REPORT_READY"""
        with self.assertRaises(IllegalStateTransitionError):
            self.run.transition_to(RunStatus.COMPLETED)

        with self.assertRaises(IllegalStateTransitionError):
            self.run.transition_to(RunStatus.REPORT_READY)

    def test_blocking_and_resuming_flow(self):
        """验证阻断（BLOCKED）与原因记录及解阻流转"""
        self.run.transition_to(RunStatus.SCOPE_VERIFIED)
        self.run.transition_to(RunStatus.BLOCKED, reason="Missing authorized proxy credential")

        self.assertEqual(self.run.status, RunStatus.BLOCKED)
        self.assertEqual(self.run.block_reason, "Missing authorized proxy credential")

        # 修复凭证后允许恢复至前置状态重新进行
        self.run.transition_to(RunStatus.SCOPE_VERIFIED)
        self.assertEqual(self.run.status, RunStatus.SCOPE_VERIFIED)
        self.assertIsNone(self.run.block_reason)

    def test_run_inspect_tool_contract(self):
        """验证 run.inspect 工具契约输出完整性与格式对齐"""
        inspected = self.run.inspect()
        self.assertEqual(inspected["run_id"], "RUN-20260918-001")
        self.assertEqual(inspected["status"], "INIT")
        self.assertEqual(inspected["scope"]["target_domain"], "ikuai8.com")
        self.assertEqual(inspected["source_ref"]["commit"], "a1b2c3d4e5f6")
        self.assertEqual(inspected["budget"]["max_tasks"], 50)

    def test_scope_boundary_enforcement(self):
        """验证测试授权边界拦截逻辑"""
        self.assertTrue(self.scope.is_method_allowed("GET"))
        self.assertTrue(self.scope.is_method_allowed("post"))
        self.assertFalse(self.scope.is_method_allowed("DELETE"))

        self.assertTrue(self.scope.is_path_excluded("/api/v1/logout"))
        self.assertFalse(self.scope.is_path_excluded("/api/v1/users"))

    def test_serialization_and_disk_roundtrip(self):
        """验证 ResearchRun 的无损 JSON 序列化与文件落盘持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "run_state.json"
            self.run.transition_to(RunStatus.SCOPE_VERIFIED)
            self.run.save(file_path)

            restored = ResearchRun.load(file_path)
            self.assertEqual(restored.run_id, self.run.run_id)
            self.assertEqual(restored.status, RunStatus.SCOPE_VERIFIED)
            self.assertEqual(restored.scope.target_domain, "ikuai8.com")
            self.assertEqual(restored.source_ref.raw_input_hash, self.source_ref.raw_input_hash)


if __name__ == "__main__":
    unittest.main()
