use std::path::PathBuf;
use invar_core::{ProcessResearchExecutor, ResearchOrchestrator, ResearchTask};

#[test]
fn process_research_executor_satisfies_orchestrator_contract() {
    let task = ResearchTask::from_legacy("POST:/api/orders", "POST", "/api/orders");

    let executor = ProcessResearchExecutor::new(
        "uv".to_string(),
        vec![
            "run".to_string(),
            "--project".to_string(),
            "C:\\dev\\Invar\\python".to_string(),
            "--python".to_string(),
            "3.11".to_string(),
            "python".to_string(),
            "-m".to_string(),
            "harness.research_worker".to_string(),
        ],
        Some(PathBuf::from("C:\\dev\\Invar")),
        Some("C:\\dev\\Invar\\python\\packages\\core\\src".to_string()),
    );

    let orchestrator = ResearchOrchestrator::new(executor);
    let result = orchestrator.run(&task);

    assert_eq!(result.task_id, "POST:/api/orders");
    assert!(!result.status.is_empty());
}
