# -*- coding: utf-8 -*-
import unittest
from harness.config import InvarConfig
from harness.evidence import EvidenceRecord
from harness.models import EndpointIR
from harness.research_evidence import ProbeAttemptEvidenceMapper
from harness.research_models import ProbeAttempt, ResearchCase, ResearchExecutionResult
from harness.sandbox_executor import AdaptiveSandboxExecutor


class ResearchEvidenceAllTests(unittest.TestCase):
    """
    高内聚整合测试：覆盖科研探针尝试 (ProbeAttempt) 到证据记录 (EvidenceRecord)
    以及执行结果 (ResearchExecutionResult) 的全生命周期映射
    (合并原 evidence, evidence_bridge, evidence_history, execution_result 碎片测试)
    """

    def setUp(self):
        self.endpoint = EndpointIR(
            method="POST",
            path="/api/orders",
            extracted_params=["name"],
            source_file="routes/orders.js",
            line=12,
        )

    def test_attempt_maps_to_evidence_record_and_history(self):
        """【整合契约 1】单个与多个 ProbeAttempt 均能准确映射为标准可追溯 EvidenceRecord 事实"""
        attempt1 = ProbeAttempt(
            attempt_number=1,
            payload={"name": "test"},
            status_code=400,
            response_preview="bad request",
            interpretation="validation error",
            mutation_reason="add required field",
        )
        attempt2 = ProbeAttempt(
            attempt_number=2,
            payload={"name": "test", "id": 1},
            status_code=200,
            response_preview="success",
            interpretation="contract satisfied",
            mutation_reason="",
        )

        # 单次映射
        ev1 = ProbeAttemptEvidenceMapper.to_evidence(self.endpoint, attempt1, "https://example.com/api/orders")
        self.assertEqual(ev1.request.method, "POST")
        self.assertEqual(ev1.response.status_code, 400)
        self.assertIn("validation error", ev1.notes)

        # 序列历史全量映射
        case = ResearchCase(case_id="POST:/api/orders", endpoint=self.endpoint)
        case.add_attempt(attempt1)
        case.add_attempt(attempt2)
        history = ProbeAttemptEvidenceMapper.to_evidence_records(case, "https://example.com/api/orders")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].response.status_code, 400)
        self.assertEqual(history[1].response.status_code, 200)

    def test_sandbox_probe_produces_evidence_and_full_execution_result(self):
        """【整合契约 2】沙箱 probe_endpoint_with_research 输出包含最终 Evidence 与完整历史序列"""
        class FakeResponse:
            status_code = 200
            text = '{"code": 200, "status": "ok"}'
            headers = {"content-type": "application/json"}

        def fake_request(method, url, payload, headers, timeout):
            return FakeResponse()

        executor = AdaptiveSandboxExecutor(InvarConfig())
        executor.transport.request = fake_request

        # 1. 深度执行模式返回 ResearchExecutionResult
        exec_res = executor.probe_endpoint_with_research(self.endpoint)
        self.assertIsInstance(exec_res, ResearchExecutionResult)
        self.assertIsInstance(exec_res.evidence, EvidenceRecord)
        self.assertEqual(exec_res.evidence.response.status_code, 200)
        self.assertGreaterEqual(len(exec_res.evidence_history), 1)

        # 2. 向后兼容模式 probe_endpoint 直接返回 EvidenceRecord
        direct_ev = executor.probe_endpoint(self.endpoint)
        self.assertIsInstance(direct_ev, EvidenceRecord)
        self.assertEqual(direct_ev.response.status_code, 200)
