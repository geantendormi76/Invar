import json

from agent.loop_types import ResearchEvent, ResearchEventType
from harness.coverage_ledger import CoverageStatus, CoverageUnit
from harness.execution_trace import ExecutionTraceRecorder
from harness.finding_models import FindingRecord, Verdict
from harness.models import EndpointIR
from harness.research_models import ResearchCase, ResearchExecutionResult


def make_coverage() -> CoverageUnit:
    return CoverageUnit(
        coverage_id="COV-001",
        surface="api",
        boundary="user-to-admin",
        subsystem="router",
        attack_class="authorization",
        status=CoverageStatus.COVERED,
        reviewed_paths=["/api/test"],
        check_refs=["CHK-AUTH-POST"],
    )


def make_execution_result() -> ResearchExecutionResult:
    endpoint = EndpointIR(
        method="POST",
        path="/api/test",
    )

    case = ResearchCase(
        case_id="POST:/api/test",
        endpoint=endpoint,
    )

    case.record_attempt(
        payload={"id": 1},
        status_code=200,
        response_preview='{"code":4003,"message":"forbidden"}',
        interpretation="业务软拒绝",
        mutation_reason="",
    )

    class Decision:
        status = "confirmed"
        rationale = "服务端拒绝请求"

    case.set_decision(Decision())

    return ResearchExecutionResult(
        evidence=None,
        research_case=case,
        evidence_history=[],
    )


def test_execution_trace_writes_one_jsonl_record(tmp_path):
    output = tmp_path / "execution.jsonl"
    endpoint = EndpointIR(method="POST", path="/api/test")

    recorder = ExecutionTraceRecorder(
        run_id="RUN-001",
        output_path=output,
        total_tasks=1,
        llm_enabled=False,
    )

    recorder.begin_task(
        index=1,
        task={
            "task_id": "POST:/api/test",
            "coverage_id": "COV-001",
            "priority": "P1",
            "method": "POST",
            "path": "/api/test",
        },
        endpoint=endpoint,
    )

    recorder.finalize_task(
        task={
            "task_id": "POST:/api/test",
            "coverage_id": "COV-001",
            "priority": "P1",
            "method": "POST",
            "path": "/api/test",
        },
        endpoint=endpoint,
        execution_result=make_execution_result(),
        coverage_unit=make_coverage(),
        elapsed_ms=12.34,
    )

    recorder.close()

    rows = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(rows) == 1
    assert rows[0]["run_id"] == "RUN-001"
    assert rows[0]["task"]["task_id"] == "POST:/api/test"
    assert rows[0]["execution"]["decision_status"] == "confirmed"
    assert rows[0]["responses"]["final_response_category"] == "soft_access_policy_denial"


def test_execution_trace_append_preserves_completed_records(tmp_path):
    output = tmp_path / "execution.jsonl"
    endpoint = EndpointIR(method="POST", path="/api/test")

    first = ExecutionTraceRecorder(
        run_id="RUN-APPEND",
        output_path=output,
        total_tasks=2,
        llm_enabled=False,
    )
    first.begin_task(
        index=1,
        task={"task_id": "TASK-1", "method": "POST", "path": "/api/test"},
        endpoint=endpoint,
    )
    first.finalize_task(
        task={"task_id": "TASK-1", "method": "POST", "path": "/api/test"},
        endpoint=endpoint,
        execution_result=make_execution_result(),
        coverage_unit=make_coverage(),
        elapsed_ms=1.0,
    )
    first.close()

    resumed = ExecutionTraceRecorder(
        run_id="RUN-APPEND",
        output_path=output,
        total_tasks=2,
        llm_enabled=False,
        append=True,
    )
    resumed.begin_task(
        index=2,
        task={"task_id": "TASK-2", "method": "POST", "path": "/api/test"},
        endpoint=endpoint,
    )
    resumed.finalize_task(
        task={"task_id": "TASK-2", "method": "POST", "path": "/api/test"},
        endpoint=endpoint,
        execution_result=make_execution_result(),
        coverage_unit=make_coverage(),
        elapsed_ms=1.0,
    )
    resumed.close()

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [row["task"]["task_id"] for row in rows] == ["TASK-1", "TASK-2"]


def test_execution_trace_serializes_finding_for_crash_recovery(tmp_path):
    output = tmp_path / "execution.jsonl"
    endpoint = EndpointIR(method="POST", path="/api/test")
    finding = FindingRecord(
        finding_id="FINDING-1",
        verdict=Verdict.CONFIRMED,
        fingerprint="fp-1",
        title="Confirmed test finding",
        description="Physical evidence was recorded",
    )
    recorder = ExecutionTraceRecorder(
        run_id="RUN-FINDING",
        output_path=output,
        total_tasks=1,
        llm_enabled=False,
    )
    recorder.begin_task(
        index=1,
        task={"task_id": "TASK-1", "method": "POST", "path": "/api/test"},
        endpoint=endpoint,
    )
    recorder.finalize_task(
        task={"task_id": "TASK-1", "method": "POST", "path": "/api/test"},
        endpoint=endpoint,
        execution_result=make_execution_result(),
        coverage_unit=make_coverage(),
        elapsed_ms=1.0,
        finding=finding,
    )
    recorder.close()

    row = json.loads(output.read_text(encoding="utf-8"))
    assert row["finding"]["finding_id"] == "FINDING-1"


def test_llm_event_marks_actual_invocation(tmp_path):
    output = tmp_path / "execution.jsonl"
    endpoint = EndpointIR(method="GET", path="/api/admin/test")

    recorder = ExecutionTraceRecorder(
        run_id="RUN-002",
        output_path=output,
        total_tasks=1,
        llm_enabled=True,
        llm_model="Ornith-1.5-9B-Abliterated-IQ3_M",
    )

    recorder.begin_task(
        index=1,
        task={
            "task_id": "GET:/api/admin/test",
            "priority": "P1",
            "method": "GET",
            "path": "/api/admin/test",
        },
        endpoint=endpoint,
    )

    recorder.on_event(
        ResearchEvent(
            event_type=ResearchEventType.LLM_REASONING_STARTED,
            payload={
                "endpoint": endpoint.endpoint_id,
                "turns_prior": 12,
            },
        )
    )

    recorder.on_event(
        ResearchEvent(
            event_type=ResearchEventType.LLM_REASONING_COMPLETED,
            payload={
                "rationale": "Authorization context requires further validation",
                "inferred_headers": ["Authorization"],
            },
        )
    )

    recorder.finalize_task(
        task={
            "task_id": "GET:/api/admin/test",
            "priority": "P1",
            "method": "GET",
            "path": "/api/admin/test",
        },
        endpoint=endpoint,
        execution_result=make_execution_result(),
        coverage_unit=None,
        elapsed_ms=1.0,
    )

    recorder.close()

    row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])

    assert row["llm"]["enabled"] is True
    assert row["llm"]["invoked"] is True
    assert row["llm"]["started_count"] == 1
    assert row["llm"]["completed_count"] == 1
    assert row["llm"]["failed_count"] == 0
    assert row["llm"]["terminal_status"] == "completed"
    assert row["llm"]["model"] == "Ornith-1.5-9B-Abliterated-IQ3_M"


def test_sensitive_values_are_redacted(tmp_path):
    output = tmp_path / "execution.jsonl"
    endpoint = EndpointIR(method="GET", path="/api/test")

    recorder = ExecutionTraceRecorder(
        run_id="RUN-003",
        output_path=output,
        total_tasks=1,
        llm_enabled=True,
    )

    recorder.begin_task(
        index=1,
        task={
            "task_id": "GET:/api/test",
            "method": "GET",
            "path": "/api/test",
        },
        endpoint=endpoint,
    )

    recorder.on_event(
        ResearchEvent(
            event_type=ResearchEventType.PROBE_DISPATCHED,
            payload={
                "headers": {
                    "Authorization": "Bearer SECRET-TOKEN",
                    "Accept": "application/json",
                }
            },
        )
    )

    recorder.finalize_exception(
        task={
            "task_id": "GET:/api/test",
            "method": "GET",
            "path": "/api/test",
        },
        endpoint=endpoint,
        error=RuntimeError("authorization failed"),
        elapsed_ms=2.0,
    )

    recorder.close()

    content = output.read_text(encoding="utf-8")

    assert "SECRET-TOKEN" not in content
    assert "<REDACTED>" in content


def test_coverage_status_is_separate_from_execution_decision(tmp_path):
    output = tmp_path / "execution.jsonl"
    endpoint = EndpointIR(method="GET", path="/api/test")

    recorder = ExecutionTraceRecorder(
        run_id="RUN-004",
        output_path=output,
        total_tasks=1,
        llm_enabled=False,
    )

    recorder.begin_task(
        index=1,
        task={
            "task_id": "GET:/api/test",
            "coverage_id": "COV-004",
            "method": "GET",
            "path": "/api/test",
        },
        endpoint=endpoint,
    )

    recorder.finalize_task(
        task={
            "task_id": "GET:/api/test",
            "coverage_id": "COV-004",
            "method": "GET",
            "path": "/api/test",
        },
        endpoint=endpoint,
        execution_result=make_execution_result(),
        coverage_unit=make_coverage(),
        elapsed_ms=5.0,
    )

    recorder.close()

    row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])

    assert row["coverage"]["status"] == "covered"
    assert row["execution"]["decision_status"] == "confirmed"

