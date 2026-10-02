use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResearchTask {
    #[serde(alias = "case_id")]
    pub task_id: String,
    #[serde(default)]
    pub endpoint_id: String,
    #[serde(default)]
    pub coverage_id: String,
    pub hypothesis_id: Option<String>,
    #[serde(default)]
    pub profile: String,
    #[serde(default)]
    pub method: String,
    #[serde(default)]
    pub path: String,
}

impl ResearchTask {
    pub fn new(
        task_id: impl Into<String>,
        endpoint_id: impl Into<String>,
        coverage_id: impl Into<String>,
        hypothesis_id: Option<String>,
        profile: impl Into<String>,
        method: impl Into<String>,
        path: impl Into<String>,
    ) -> Self {
        Self {
            task_id: task_id.into(),
            endpoint_id: endpoint_id.into(),
            coverage_id: coverage_id.into(),
            hypothesis_id,
            profile: profile.into(),
            method: method.into(),
            path: path.into(),
        }
    }

    pub fn from_legacy(
        task_id: impl Into<String>,
        method: impl Into<String>,
        path: impl Into<String>,
    ) -> Self {
        let m = method.into();
        let p = path.into();
        let ep_id = format!("{}:{}", m.to_uppercase(), p);
        Self {
            task_id: task_id.into(),
            endpoint_id: ep_id,
            coverage_id: String::new(),
            hypothesis_id: None,
            profile: "default".to_string(),
            method: m,
            path: p,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResearchDecision {
    pub status: String,
    pub rationale: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResearchResult {
    #[serde(alias = "case_id")]
    pub task_id: String,
    pub status: String,
    pub attempts: u32,
    pub decision: Option<ResearchDecision>,
    pub evidence_history_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AuditReport {
    pub total_tasks: usize,
    pub completed_tasks: usize,
    pub inconclusive_tasks: usize,
    pub failed_tasks: usize,
    pub vulnerable_tasks: usize,
    pub total_attempts: u32,
    pub results: Vec<ResearchResult>,
}

pub trait ResearchExecutor {
    fn execute(&self, task: &ResearchTask) -> ResearchResult;

    fn execute_batch(&self, tasks: &[ResearchTask]) -> Vec<ResearchResult> {
        tasks.iter().map(|task| self.execute(task)).collect()
    }
}

pub struct ResearchOrchestrator<E: ResearchExecutor> {
    executor: E,
}

impl<E: ResearchExecutor> ResearchOrchestrator<E> {
    pub fn new(executor: E) -> Self {
        Self { executor }
    }

    pub fn run(&self, task: &ResearchTask) -> ResearchResult {
        self.executor.execute(task)
    }

    pub fn run_all(&self, tasks: &[ResearchTask]) -> Vec<ResearchResult> {
        self.executor.execute_batch(tasks)
    }

    pub fn audit(&self, tasks: &[ResearchTask]) -> AuditReport {
        let results = self.run_all(tasks);
        let total_tasks = results.len();
        let mut completed_tasks = 0;
        let mut inconclusive_tasks = 0;
        let mut failed_tasks = 0;
        let mut vulnerable_tasks = 0;
        let mut total_attempts = 0;

        for r in &results {
            total_attempts += r.attempts;
            match r.status.as_str() {
                "completed" => completed_tasks += 1,
                "inconclusive" => inconclusive_tasks += 1,
                _ => failed_tasks += 1,
            }

            if let Some(ref d) = r.decision {
                if d.status == "vulnerable" {
                    vulnerable_tasks += 1;
                }
            }
        }

        AuditReport {
            total_tasks,
            completed_tasks,
            inconclusive_tasks,
            failed_tasks,
            vulnerable_tasks,
            total_attempts,
            results,
        }
    }
}

#[derive(Serialize)]
struct AstCodeRequest<'a> {
    code: &'a str,
}

#[derive(Serialize)]
struct AstPathRequest<'a> {
    target_path: &'a str,
}

#[derive(Debug, Clone)]
pub struct ProcessAstExtractor {
    pub program: String,
    pub args: Vec<String>,
    pub working_dir: Option<PathBuf>,
    pub pythonpath: Option<String>,
}

impl ProcessAstExtractor {
    pub fn new(
        program: String,
        args: Vec<String>,
        working_dir: Option<PathBuf>,
        pythonpath: Option<String>,
    ) -> Self {
        Self {
            program,
            args,
            working_dir,
            pythonpath,
        }
    }

    pub fn extract_from_code(&self, code: &str) -> Vec<ResearchTask> {
        let req = AstCodeRequest { code };
        match serde_json::to_string(&req) {
            Ok(json) => self.invoke_worker(&json),
            Err(_) => Vec::new(),
        }
    }

    pub fn extract_from_path(&self, target_path: &Path) -> Vec<ResearchTask> {
        let path_str = target_path.to_string_lossy();
        let req = AstPathRequest {
            target_path: &path_str,
        };
        match serde_json::to_string(&req) {
            Ok(json) => self.invoke_worker(&json),
            Err(_) => Vec::new(),
        }
    }

    fn invoke_worker(&self, input_json: &str) -> Vec<ResearchTask> {
        let mut cmd = Command::new(&self.program);
        cmd.args(&self.args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        if let Some(ref dir) = self.working_dir {
            cmd.current_dir(dir);
        }

        if let Some(ref py_path) = self.pythonpath {
            cmd.env("PYTHONPATH", py_path);
        }

        let mut child = match cmd.spawn() {
            Ok(c) => c,
            Err(_) => return Vec::new(),
        };

        if let Some(mut stdin) = child.stdin.take() {
            let _ = stdin.write_all(input_json.as_bytes());
        }

        let output = match child.wait_with_output() {
            Ok(o) => o,
            Err(err) => {
                eprintln!("[ProcessAstExtractor] Failed to wait for child: {err}");
                return Vec::new();
            }
        };

        let stdout_str = String::from_utf8_lossy(&output.stdout);
        let trimmed = stdout_str.trim();

        if !trimmed.is_empty() {
            if let Ok(tasks) = serde_json::from_str::<Vec<ResearchTask>>(trimmed) {
                return tasks;
            }
        }

        Vec::new()
    }
}

#[derive(Debug, Clone)]
pub struct ProcessResearchExecutor {
    pub program: String,
    pub args: Vec<String>,
    pub working_dir: Option<PathBuf>,
    pub pythonpath: Option<String>,
}

impl ProcessResearchExecutor {
    pub fn new(
        program: String,
        args: Vec<String>,
        working_dir: Option<PathBuf>,
        pythonpath: Option<String>,
    ) -> Self {
        Self {
            program,
            args,
            working_dir,
            pythonpath,
        }
    }
}

impl ResearchExecutor for ProcessResearchExecutor {
    fn execute(&self, task: &ResearchTask) -> ResearchResult {
        let task_json = match serde_json::to_string(task) {
            Ok(json) => json,
            Err(err) => {
                return ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "serialization_error".to_string(),
                    attempts: 0,
                    decision: Some(ResearchDecision {
                        status: "failed".to_string(),
                        rationale: format!("Failed to serialize task: {err}"),
                    }),
                    evidence_history_count: 0,
                };
            }
        };

        let mut cmd = Command::new(&self.program);
        cmd.args(&self.args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        if let Some(ref dir) = self.working_dir {
            cmd.current_dir(dir);
        }

        if let Some(ref py_path) = self.pythonpath {
            cmd.env("PYTHONPATH", py_path);
        }

        let mut child = match cmd.spawn() {
            Ok(child) => child,
            Err(err) => {
                return ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "spawn_error".to_string(),
                    attempts: 0,
                    decision: Some(ResearchDecision {
                        status: "failed".to_string(),
                        rationale: format!("Failed to spawn child process: {err}"),
                    }),
                    evidence_history_count: 0,
                };
            }
        };

        if let Some(mut stdin) = child.stdin.take() {
            if let Err(err) = stdin.write_all(task_json.as_bytes()) {
                return ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "stdin_error".to_string(),
                    attempts: 0,
                    decision: Some(ResearchDecision {
                        status: "failed".to_string(),
                        rationale: format!("Failed to write to stdin: {err}"),
                    }),
                    evidence_history_count: 0,
                };
            }
        }

        let output = match child.wait_with_output() {
            Ok(output) => output,
            Err(err) => {
                return ResearchResult {
                    task_id: task.task_id.clone(),
                    status: "io_error".to_string(),
                    attempts: 0,
                    decision: Some(ResearchDecision {
                        status: "failed".to_string(),
                        rationale: format!("Failed to wait for child process: {err}"),
                    }),
                    evidence_history_count: 0,
                };
            }
        };

        let stdout_str = String::from_utf8_lossy(&output.stdout);
        let trimmed = stdout_str.trim();

        if !trimmed.is_empty() {
            if let Ok(result) = serde_json::from_str::<ResearchResult>(trimmed) {
                return result;
            }
        }

        let stderr_str = String::from_utf8_lossy(&output.stderr);
        let rationale = if !stderr_str.trim().is_empty() {
            format!("Process failed with stderr: {}", stderr_str.trim())
        } else if !trimmed.is_empty() {
            format!("Failed to parse child output: {trimmed}")
        } else {
            format!("Process exited with status code: {:?}", output.status.code())
        };

        ResearchResult {
            task_id: task.task_id.clone(),
            status: "process_failed".to_string(),
            attempts: 0,
            decision: Some(ResearchDecision {
                status: "failed".to_string(),
                rationale,
            }),
            evidence_history_count: 0,
        }
    }

    fn execute_batch(&self, tasks: &[ResearchTask]) -> Vec<ResearchResult> {
        if tasks.is_empty() {
            return Vec::new();
        }

        let tasks_json = match serde_json::to_string(tasks) {
            Ok(json) => json,
            Err(err) => {
                return tasks
                    .iter()
                    .map(|task| ResearchResult {
                        task_id: task.task_id.clone(),
                        status: "serialization_error".to_string(),
                        attempts: 0,
                        decision: Some(ResearchDecision {
                            status: "failed".to_string(),
                            rationale: format!("Failed to serialize task batch: {err}"),
                        }),
                        evidence_history_count: 0,
                    })
                    .collect();
            }
        };

        let mut cmd = Command::new(&self.program);
        cmd.args(&self.args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        if let Some(ref dir) = self.working_dir {
            cmd.current_dir(dir);
        }

        if let Some(ref py_path) = self.pythonpath {
            cmd.env("PYTHONPATH", py_path);
        }

        let mut child = match cmd.spawn() {
            Ok(child) => child,
            Err(err) => {
                return tasks
                    .iter()
                    .map(|task| ResearchResult {
                        task_id: task.task_id.clone(),
                        status: "spawn_error".to_string(),
                        attempts: 0,
                        decision: Some(ResearchDecision {
                            status: "failed".to_string(),
                            rationale: format!("Failed to spawn child process: {err}"),
                        }),
                        evidence_history_count: 0,
                    })
                    .collect();
            }
        };

        if let Some(mut stdin) = child.stdin.take() {
            if let Err(err) = stdin.write_all(tasks_json.as_bytes()) {
                return tasks
                    .iter()
                    .map(|task| ResearchResult {
                        task_id: task.task_id.clone(),
                        status: "stdin_error".to_string(),
                        attempts: 0,
                        decision: Some(ResearchDecision {
                            status: "failed".to_string(),
                            rationale: format!("Failed to write batch to stdin: {err}"),
                        }),
                        evidence_history_count: 0,
                    })
                    .collect();
            }
        }

        let output = match child.wait_with_output() {
            Ok(output) => output,
            Err(err) => {
                return tasks
                    .iter()
                    .map(|task| ResearchResult {
                        task_id: task.task_id.clone(),
                        status: "io_error".to_string(),
                        attempts: 0,
                        decision: Some(ResearchDecision {
                            status: "failed".to_string(),
                            rationale: format!("Failed to wait for child process: {err}"),
                        }),
                        evidence_history_count: 0,
                    })
                    .collect();
            }
        };

        let stdout_str = String::from_utf8_lossy(&output.stdout);
        let trimmed = stdout_str.trim();

        if !trimmed.is_empty() {
            if let Ok(results) = serde_json::from_str::<Vec<ResearchResult>>(trimmed) {
                if results.len() == tasks.len() {
                    return results;
                }
            }
        }

        let stderr_str = String::from_utf8_lossy(&output.stderr);
        let rationale = if !stderr_str.trim().is_empty() {
            format!("Batch process failed with stderr: {}", stderr_str.trim())
        } else if !trimmed.is_empty() {
            format!("Failed to parse batch output: {trimmed}")
        } else {
            format!("Batch process exited with status code: {:?}", output.status.code())
        };

        tasks
            .iter()
            .map(|task| ResearchResult {
                task_id: task.task_id.clone(),
                status: "process_failed".to_string(),
                attempts: 0,
                decision: Some(ResearchDecision {
                    status: "failed".to_string(),
                    rationale: rationale.clone(),
                }),
                evidence_history_count: 0,
            })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::{
        ResearchDecision, ResearchExecutor, ResearchOrchestrator, ResearchResult, ResearchTask,
    };

    struct FakeResearchExecutor;

    impl ResearchExecutor for FakeResearchExecutor {
        fn execute(&self, task: &ResearchTask) -> ResearchResult {
            ResearchResult {
                task_id: task.task_id.clone(),
                status: "completed".to_string(),
                attempts: 2,
                decision: Some(ResearchDecision {
                    status: "confirmed".to_string(),
                    rationale: "evidence is sufficient".to_string(),
                }),
                evidence_history_count: 2,
            }
        }
    }

    #[test]
    fn research_orchestrator_supports_replaceable_executor() {
        let task = ResearchTask::from_legacy("case-001", "POST", "/api/orders");

        let orchestrator = ResearchOrchestrator::new(FakeResearchExecutor);
        let result = orchestrator.run(&task);

        assert_eq!(result.task_id, "case-001");
        assert_eq!(result.status, "completed");
        assert_eq!(result.attempts, 2);
        assert_eq!(
            result.decision.as_ref().unwrap().rationale,
            "evidence is sufficient"
        );
    }
}
