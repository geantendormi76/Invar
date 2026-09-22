use invar_core::{
    AuditReport, ResearchDecision, ResearchExecutor, ResearchOrchestrator, ResearchResult,
    ResearchTask,
};

#[test]
fn research_contract_supports_json_round_trip() {
    let task = ResearchTask::new(
        "case-001",
        "POST:/api/orders",
        "COV-AUTH-01",
        Some("H-AUTH-1".to_string()),
        "aggressive",
        "POST",
        "/api/orders",
    );

    let json = serde_json::to_string(&task).unwrap();
    let restored: ResearchTask = serde_json::from_str(&json).unwrap();

    assert_eq!(restored, task);
    assert_eq!(restored.endpoint_id, "POST:/api/orders");
    assert_eq!(restored.coverage_id, "COV-AUTH-01");
    assert_eq!(restored.hypothesis_id, Some("H-AUTH-1".to_string()));
}

#[test]
fn research_contract_supports_legacy_instantiation_compatibility() {
    let task = ResearchTask::from_legacy("legacy-task", "GET", "/api/items");
    assert_eq!(task.task_id, "legacy-task");
    assert_eq!(task.endpoint_id, "GET:/api/items");
    assert_eq!(task.profile, "default");
}

#[test]
fn research_result_supports_json_round_trip() {
    let result = ResearchResult {
        task_id: "case-001".to_string(),
        status: "needs_review".to_string(),
        attempts: 3,
        decision: None,
        evidence_history_count: 3,
    };

    let json = serde_json::to_string(&result).unwrap();
    let restored: ResearchResult = serde_json::from_str(&json).unwrap();

    assert_eq!(restored, result);
}

#[test]
fn research_result_preserves_decision_context() {
    let result = ResearchResult {
        task_id: "case-004".to_string(),
        status: "completed".to_string(),
        attempts: 2,
        decision: Some(ResearchDecision {
            status: "confirmed".to_string(),
            rationale: "evidence is sufficient".to_string(),
        }),
        evidence_history_count: 2,
    };

    let json = serde_json::to_string(&result).unwrap();
    let restored: ResearchResult = serde_json::from_str(&json).unwrap();

    assert_eq!(restored, result);
    assert!(restored.decision.is_some());
}

#[test]
fn research_result_supports_unresolved_decision() {
    let result = ResearchResult {
        task_id: "case-003".to_string(),
        status: "inconclusive".to_string(),
        attempts: 1,
        decision: None,
        evidence_history_count: 1,
    };

    let json = serde_json::to_string(&result).unwrap();
    let restored: ResearchResult = serde_json::from_str(&json).unwrap();

    assert_eq!(restored, result);
    assert!(restored.decision.is_none());
}

#[test]
fn research_task_supports_python_case_id_alias() {
    let python_task_json = r#"{
        "case_id": "POST:/api/orders",
        "method": "POST",
        "path": "/api/orders"
    }"#;

    let task: ResearchTask = serde_json::from_str(python_task_json).unwrap();
    assert_eq!(task.task_id, "POST:/api/orders");
    assert_eq!(task.method, "POST");
    assert_eq!(task.path, "/api/orders");
}

#[test]
fn research_result_supports_python_case_id_alias() {
    let python_result_json = r#"{
        "case_id": "POST:/api/orders",
        "status": "completed",
        "attempts": 2,
        "decision": {
            "status": "confirmed",
            "rationale": "contract met"
        },
        "evidence_history_count": 2
    }"#;

    let result: ResearchResult = serde_json::from_str(python_result_json).unwrap();
    assert_eq!(result.task_id, "POST:/api/orders");
    assert_eq!(result.attempts, 2);
    assert!(result.decision.is_some());
}

#[test]
fn research_orchestrator_supports_batch_execution() {
    let tasks = vec![
        ResearchTask::from_legacy("case-001", "GET", "/api/users"),
        ResearchTask::from_legacy("case-002", "POST", "/api/orders"),
    ];

    struct MockBatchExecutor;

    impl ResearchExecutor for MockBatchExecutor {
        fn execute(&self, task: &ResearchTask) -> ResearchResult {
            ResearchResult {
                task_id: task.task_id.clone(),
                status: "completed".to_string(),
                attempts: 1,
                decision: None,
                evidence_history_count: 1,
            }
        }
    }

    let orchestrator = ResearchOrchestrator::new(MockBatchExecutor);
    let results = orchestrator.run_all(&tasks);

    assert_eq!(results.len(), 2);
    assert_eq!(results[0].task_id, "case-001");
    assert_eq!(results[1].task_id, "case-002");
}

#[test]
fn research_executor_allows_overriding_execute_batch() {
    let tasks = vec![
        ResearchTask::from_legacy("batch-001", "GET", "/api/items"),
    ];

    struct SpecializedBatchExecutor;

    impl ResearchExecutor for SpecializedBatchExecutor {
        fn execute(&self, _task: &ResearchTask) -> ResearchResult {
            panic!("Single execute should not be called when execute_batch is overridden");
        }

        fn execute_batch(&self, tasks: &[ResearchTask]) -> Vec<ResearchResult> {
            tasks
                .iter()
                .map(|t| ResearchResult {
                    task_id: t.task_id.clone(),
                    status: "specialized_batch".to_string(),
                    attempts: 99,
                    decision: None,
                    evidence_history_count: 99,
                })
                .collect()
        }
    }

    let orchestrator = ResearchOrchestrator::new(SpecializedBatchExecutor);
    let results = orchestrator.run_all(&tasks);

    assert_eq!(results.len(), 1);
    assert_eq!(results[0].status, "specialized_batch");
    assert_eq!(results[0].attempts, 99);
}

#[test]
fn research_orchestrator_generates_structured_audit_report() {
    let tasks = vec![
        ResearchTask::from_legacy("task-1", "GET", "/api/items"),
        ResearchTask::from_legacy("task-2", "POST", "/api/orders"),
        ResearchTask::from_legacy("task-3", "DELETE", "/api/danger"),
    ];

    struct ReportMockExecutor;

    impl ResearchExecutor for ReportMockExecutor {
        fn execute(&self, task: &ResearchTask) -> ResearchResult {
            match task.task_id.as_str() {
                "task-1" => ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "completed".to_string(),
                    attempts: 1,
                    decision: Some(ResearchDecision {
                        status: "confirmed".to_string(),
                        rationale: "ok".to_string(),
                    }),
                    evidence_history_count: 1,
                },
                "task-2" => ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "inconclusive".to_string(),
                    attempts: 3,
                    decision: None,
                    evidence_history_count: 3,
                },
                _ => ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "process_failed".to_string(),
                    attempts: 0,
                    decision: None,
                    evidence_history_count: 0,
                },
            }
        }
    }

    let orchestrator = ResearchOrchestrator::new(ReportMockExecutor);
    let report: AuditReport = orchestrator.audit(&tasks);

    assert_eq!(report.total_tasks, 3);
    assert_eq!(report.completed_tasks, 1);
    assert_eq!(report.inconclusive_tasks, 1);
    assert_eq!(report.failed_tasks, 1);
    assert_eq!(report.total_attempts, 4);
    assert_eq!(report.results.len(), 3);
}

#[test]
fn research_orchestrator_tallies_vulnerable_tasks_in_audit_report() {
    let tasks = vec![
        ResearchTask::from_legacy("vuln-task", "DELETE", "/api/danger/clear"),
        ResearchTask::from_legacy("safe-task", "GET", "/api/items"),
    ];

    struct VulnMockExecutor;

    impl ResearchExecutor for VulnMockExecutor {
        fn execute(&self, task: &ResearchTask) -> ResearchResult {
            if task.task_id == "vuln-task" {
                ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "completed".to_string(),
                    attempts: 1,
                    decision: Some(ResearchDecision {
                        status: "vulnerable".to_string(),
                        rationale: "destructive action executed without confirmation parameter requirement".to_string(),
                    }),
                    evidence_history_count: 1,
                }
            } else {
                ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "completed".to_string(),
                    attempts: 1,
                    decision: Some(ResearchDecision {
                        status: "confirmed".to_string(),
                        rationale: "auth boundary invariant holds".to_string(),
                    }),
                    evidence_history_count: 1,
                }
            }
        }
    }

    let orchestrator = ResearchOrchestrator::new(VulnMockExecutor);
    let report: AuditReport = orchestrator.audit(&tasks);

    assert_eq!(report.total_tasks, 2);
    assert_eq!(report.vulnerable_tasks, 1);
    assert_eq!(report.completed_tasks, 2);
}
