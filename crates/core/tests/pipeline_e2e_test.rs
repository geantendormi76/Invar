use std::path::PathBuf;
use invar_core::{
    ProcessAstExtractor, ProcessResearchExecutor, ResearchOrchestrator,
};

#[test]
fn e2e_pipeline_extracts_ast_and_produces_audit_report() {
    // 1. 模拟被测前端打包工程的真实 JS 代码片段
    let js_code = r#"
        fetch('/api/users', { method: 'GET' });
        axios.post('/api/orders');
    "#;

    // 2. 配置 Rust 侧 AST 提取器 (指向 python -m harness.ast_worker)
    let ast_extractor = ProcessAstExtractor::new(
        "uv".to_string(),
        vec![
            "run".to_string(),
            "--project".to_string(),
            "C:\\dev\\Invar\\python".to_string(),
            "--python".to_string(),
            "3.11".to_string(),
            "python".to_string(),
            "-m".to_string(),
            "harness.ast_worker".to_string(),
        ],
        Some(PathBuf::from("C:\\dev\\Invar")),
        Some("C:\\dev\\Invar\\python\\packages\\core\\src".to_string()),
    );

    // 3. 驱动上游管道：提炼标准任务切片
    let tasks = ast_extractor.extract_from_code(js_code);
    assert_eq!(tasks.len(), 2);
    assert_eq!(tasks[0].task_id, "GET:/api/users");
    assert_eq!(tasks[1].task_id, "POST:/api/orders");

    // 4. 配置 Rust 侧批量研究执行器 (指向 python -m harness.research_worker)
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

    // 5. 驱动中枢调度与下游战报生成
    let orchestrator = ResearchOrchestrator::new(executor);
    let report = orchestrator.audit(&tasks);

    // 6. 断言全链路战报指标与契约一致性
    assert_eq!(report.total_tasks, 2);
    assert_eq!(report.results.len(), 2);
    assert_eq!(report.results[0].task_id, "GET:/api/users");
    assert_eq!(report.results[1].task_id, "POST:/api/orders");
}
