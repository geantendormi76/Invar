use invar_core::{ResearchDecision, ResearchResult, ResearchTask};

#[test]
fn research_contract_supports_json_round_trip() {
    let task = ResearchTask {
        task_id: "case-001".to_string(),
        method: "POST".to_string(),
        path: "/api/orders".to_string(),
    };

    let json = serde_json::to_string(&task).unwrap();
    let restored: ResearchTask = serde_json::from_str(&json).unwrap();

    assert_eq!(restored, task);
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
