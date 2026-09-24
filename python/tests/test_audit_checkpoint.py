import json

import pytest

from harness.audit_checkpoint import (
    AuditCheckpoint,
    CheckpointError,
    compute_plan_digest,
    recover_trace_progress,
    repair_trace_tail,
    task_key,
)
from harness.coverage_ledger import CoverageLedger, CoverageStatus, CoverageUnit
from harness.finding_models import FindingRecord, Verdict
from harness.run_models import (
    ExecutionPolicy,
    ResearchRun,
    ResearchScope,
    RunProfile,
    RunStatus,
)


def make_run(run_id: str = "RUN-RESUME-001") -> ResearchRun:
    return ResearchRun(
        run_id=run_id,
        target_root="example.test",
        scope=ResearchScope(target_domain="example.test"),
        profile=RunProfile(name="resume-test"),
        execution_policy=ExecutionPolicy(allow_dynamic_testing=True),
        status=RunStatus.EXECUTING,
    )


def test_checkpoint_round_trip_is_atomic_and_preserves_state(tmp_path):
    path = tmp_path / "targeted_audit_checkpoint.json"
    run = make_run()
    ledger = CoverageLedger(run_id=run.run_id)
    ledger.add_unit(
        CoverageUnit(
            coverage_id="COV-1",
            surface="api",
            boundary="test",
            subsystem="router",
            attack_class="authorization",
            status=CoverageStatus.COVERED,
            reviewed_paths=["/api/one"],
            check_refs=["CHK-AUTH"],
        )
    )
    checkpoint = AuditCheckpoint(
        run=run,
        ledger=ledger,
        findings=[],
        plan_digest="abc123",
        total_tasks=3,
        completed_task_keys=["TASK-1"],
        last_completed_index=1,
    )

    checkpoint.save_atomic(path)
    loaded = AuditCheckpoint.load(path)

    assert loaded.run.run_id == run.run_id
    assert loaded.run.status == RunStatus.EXECUTING
    assert loaded.completed_task_keys == ["TASK-1"]
    assert loaded.ledger.get_unit("COV-1").status == CoverageStatus.COVERED
    assert not path.with_suffix(path.suffix + ".tmp").exists()


def test_plan_digest_rejects_changed_tasks_or_options():
    tasks = [{"task_id": "TASK-1", "method": "GET", "path": "/api/one"}]
    options = {"priority": "ALL", "timeout": 10, "llm_enabled": True}

    base = compute_plan_digest(tasks, options)

    assert base != compute_plan_digest(
        [{"task_id": "TASK-2", "method": "GET", "path": "/api/two"}],
        options,
    )
    assert base != compute_plan_digest(tasks, {**options, "timeout": 20})


def test_trace_recovery_skips_errors_and_restores_coverage(tmp_path):
    trace = tmp_path / "execution.jsonl"
    tasks = [
        {"task_id": "TASK-1", "method": "GET", "path": "/api/one"},
        {"task_id": "TASK-2", "method": "GET", "path": "/api/two"},
    ]
    coverage = CoverageUnit(
        coverage_id="COV-1",
        surface="api",
        boundary="test",
        subsystem="router",
        attack_class="authorization",
        status=CoverageStatus.COVERED,
        reviewed_paths=["/api/one"],
        check_refs=["CHK-AUTH"],
    ).to_dict()
    rows = [
        {
            "run_id": "RUN-TRACE-1",
            "task": {"index": 1, "total": 2, "task_id": "TASK-1"},
            "execution": {"runner_status": "completed", "decision_status": "confirmed"},
            "coverage": coverage,
        },
        {
            "run_id": "RUN-TRACE-1",
            "task": {"index": 2, "total": 2, "task_id": "TASK-2"},
            "execution": {"runner_status": "error", "decision_status": None},
            "coverage": None,
            "error": {"type": "RuntimeError", "message": "interrupted"},
        },
    ]
    trace.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    progress = recover_trace_progress(trace, tasks, expected_total=2)

    assert progress.run_id == "RUN-TRACE-1"
    assert progress.completed_task_keys == ["TASK-1"]
    assert progress.last_completed_index == 1
    assert progress.coverage_units["COV-1"].status == CoverageStatus.COVERED
    assert progress.findings == []


def test_trace_recovery_refuses_uncheckpointed_vulnerability(tmp_path):
    trace = tmp_path / "execution.jsonl"
    tasks = [{"task_id": "TASK-1", "method": "GET", "path": "/api/one"}]
    trace.write_text(
        json.dumps(
            {
                "run_id": "RUN-TRACE-1",
                "task": {"index": 1, "total": 1, "task_id": "TASK-1"},
                "execution": {
                    "runner_status": "completed",
                    "decision_status": "vulnerable",
                },
                "coverage": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CheckpointError, match="vulnerable"):
        recover_trace_progress(trace, tasks, expected_total=1)


def test_trace_recovery_restores_serialized_vulnerable_finding(tmp_path):
    trace = tmp_path / "execution.jsonl"
    tasks = [{"task_id": "TASK-1", "method": "GET", "path": "/api/one"}]
    finding = FindingRecord(
        finding_id="FINDING-1",
        verdict=Verdict.CONFIRMED,
        fingerprint="fp-1",
        title="Confirmed test finding",
        description="Physical evidence was recorded",
    )
    trace.write_text(
        json.dumps(
            {
                "run_id": "RUN-TRACE-1",
                "task": {"index": 1, "total": 1, "task_id": "TASK-1"},
                "execution": {
                    "runner_status": "completed",
                    "decision_status": "vulnerable",
                },
                "coverage": None,
                "finding": finding.to_dict(),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    progress = recover_trace_progress(trace, tasks, expected_total=1)

    assert progress.completed_task_keys == ["TASK-1"]
    assert [item.finding_id for item in progress.findings] == ["FINDING-1"]


def test_task_key_falls_back_to_stable_content_hash():
    task = {"method": "post", "path": "/api/test", "coverage_id": "COV-1"}

    assert task_key(task, 1) == task_key(dict(task), 99)


def test_trace_tail_repair_discards_only_torn_final_record(tmp_path):
    trace = tmp_path / "execution.jsonl"
    complete = {
        "run_id": "RUN-TRACE-1",
        "task": {"index": 1, "total": 2, "task_id": "TASK-1"},
        "execution": {"runner_status": "completed"},
    }
    trace.write_bytes(
        (json.dumps(complete) + "\n").encode("utf-8")
        + b'{"run_id":"RUN-TRACE-1","task":'
    )

    assert repair_trace_tail(trace) is True
    assert trace.read_text(encoding="utf-8") == json.dumps(complete) + "\n"


def test_trace_tail_repair_finishes_valid_record_without_newline(tmp_path):
    trace = tmp_path / "execution.jsonl"
    row = {
        "run_id": "RUN-TRACE-1",
        "task": {"index": 1, "total": 1, "task_id": "TASK-1"},
        "execution": {"runner_status": "completed"},
    }
    trace.write_text(json.dumps(row), encoding="utf-8")

    assert repair_trace_tail(trace) is True
    assert trace.read_bytes().endswith(b"\n")
