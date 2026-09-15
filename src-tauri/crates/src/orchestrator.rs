use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResearchTask {
    #[serde(alias = "case_id")]
    pub task_id: String,
    pub method: String,
    pub path: String,
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

pub trait ResearchExecutor {
    fn execute(&self, task: &ResearchTask) -> ResearchResult;
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
        let task = ResearchTask {
            task_id: "case-001".to_string(),
            method: "POST".to_string(),
            path: "/api/orders".to_string(),
        };

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
