use std::path::PathBuf;
use invar_core::{
    ProcessResearchExecutor, ResearchOrchestrator, ResearchTask,
};

fn get_workspace_paths() -> (PathBuf, String) {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let workspace_root = manifest_dir
        .parent()
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| PathBuf::from("."));
    let pythonpath = workspace_root
        .join("python")
        .join("packages")
        .join("core")
        .join("src")
        .to_string_lossy()
        .to_string();
    (workspace_root, pythonpath)
}

#[test]
fn process_research_executor_satisfies_orchestrator_contract() {
    let (workspace_root, pythonpath) = get_workspace_paths();
    let python_project = workspace_root.join("python").to_string_lossy().to_string();

    let task = ResearchTask::new(
        "POST:/api/orders",
        "POST:/api/orders",
        "COV-TEST-01",
        None,
        "default",
        "POST",
        "/api/orders",
    );

    let executor = ProcessResearchExecutor::new(
        "uv".to_string(),
        vec![
            "run".to_string(),
            "--project".to_string(),
            python_project,
            "python".to_string(),
            "-m".to_string(),
            "harness.research_worker".to_string(),
        ],
        Some(workspace_root),
        Some(pythonpath),
    );

    let orchestrator = ResearchOrchestrator::new(executor);
    let result = orchestrator.run(&task);

    assert_eq!(result.task_id, "POST:/api/orders");
    assert!(!result.status.is_empty());
}
