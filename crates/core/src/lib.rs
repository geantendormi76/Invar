pub mod orchestrator;
pub use orchestrator::{
    AuditReport,
    ProcessAstExtractor,
    ProcessResearchExecutor,
    ResearchDecision,
    ResearchExecutor,
    ResearchOrchestrator,
    ResearchResult,
    ResearchTask,
};

/// 标识 Monorepo Core 引擎就绪的轻量标记结构体
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct WorkspaceCore;
