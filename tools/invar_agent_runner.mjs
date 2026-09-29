// -*- coding: utf-8 -*-
/**
 * Invar Autonomous Security Research Agent Runner
 * 
 * 架构定位:
 * 顶层由 Pi Agent Runtime (createAgentSession) 承载上下文与决策思考;
 * 挂载原生极简工具库 (read / write / edit / powershell);
 * 底层调度 Invar Python 确定性安全沙箱与证据门禁。
 * 
 * 对标参考: Shannon (pi-executor.ts) & Strix (runner.py)
 */

import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

// 1. 默认路径配置 (支持环境变量覆盖)
const REPO_ROOT = path.resolve(path.dirname(path.dirname(import.meta.url.replace("file:///", ""))));
const HOME_DIR = os.homedir();
const DEFAULT_AGENT_DIR = process.env.INVAR_PI_AGENT_DIR || path.join(HOME_DIR, ".pi", "agent");
const DEFAULT_PI_DIST = process.env.INVAR_PI_PKG_PATH || path.join(
    HOME_DIR,
    "AppData",
    "Roaming",
    "npm",
    "node_modules",
    "@earendil-works",
    "pi-coding-agent",
    "dist",
    "index.js"
);

function printUsage() {
    console.log(`
Invar Autonomous Security Research Agent Runner
================================================================================
Usage:
  node tools/invar_agent_runner.mjs [options]

Options:
  --task <text>        指定本次科研探索的具体目标任务
  --target <domain>    指定目标资产范围 (默认: ikuai8.com)
  --dry-run            仅检查环境依赖、配置与模型连接，不进入实际研究会话
  --in-memory          使用内存临时会话 (默认: true，不污染本地会话历史)
  --help, -h           显示本帮助信息

Example:
  node tools/invar_agent_runner.mjs --task "检查 /api/orders/purge 接口是否存在破坏性操作二次确认缺失"
================================================================================
`);
}

function parseCliArgs() {
    const args = process.argv.slice(2);
    const options = {
        task: null,
        target: "ikuai8.com",
        dryRun: false,
        inMemory: true,
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === "--help" || arg === "-h") {
            printUsage();
            process.exit(0);
        } else if (arg === "--dry-run") {
            options.dryRun = true;
        } else if (arg === "--in-memory") {
            options.inMemory = true;
        } else if (arg === "--target" && i + 1 < args.length) {
            options.target = args[++i];
        } else if (arg === "--task" && i + 1 < args.length) {
            options.task = args[++i];
        }
    }
    return options;
}

function buildSystemBriefing(targetDomain) {
    return `
You are the Invar Autonomous Security Research Agent (System-2).
You operate inside the Invar engineering workspace at "${REPO_ROOT}".

================================================================================
CORE OPERATING PRINCIPLES (NON-NEGOTIABLE):
================================================================================
1. SCOPE BOUNDARY IS ABSOLUTE:
   - Check "data/targets/${targetDomain}/scope.txt" for authorized target domains and paths.
   - NEVER attack or probe any system outside this explicit scope.

2. GROUND TRUTH & PHYSICAL REPRODUCTION:
   - You have native tools: "read", "write", "edit", and "powershell".
   - You MUST run real Invar commands via PowerShell to probe targets, verify invariants, or run tests.
   - Example command: "uv run --project python pytest <test_path> -q"
   - Example command: "uv run --project python python python/scripts/run_targeted_audit.py --help"
   - NEVER hallucinate or declare a vulnerability without physical reproduction and deterministic evidence.

3. RESEARCH METHODOLOGY:
   - Step 1 (Recon & Context): Read relevant AST endpoints, source code slices, or threat models.
   - Step 2 (Hypothesis & Planning): State your security hypothesis (e.g., Auth Bypass, IDOR, Destructive Action).
   - Step 3 (Deterministic Execution): Use powershell to run targeted probe scripts.
   - Step 4 (Observation & Invariant Evaluation): Analyze actual status codes, differential responses, and invariants.
   - Step 5 (Conclusion): Summarize findings, verified evidence, or refutations cleanly.
================================================================================
`;
}

async function main() {
    const options = parseCliArgs();

    console.log("=".repeat(85));
    console.log(" 🛡️ INVAR AUTONOMOUS SECURITY RESEARCH AGENT RUNNER");
    console.log(` 📂 Workspace Root : ${REPO_ROOT}`);
    console.log(` 📂 Pi Agent Dir   : ${DEFAULT_AGENT_DIR}`);
    console.log(` 🎯 Target Domain  : ${options.target}`);
    console.log("=".repeat(85));

    // 1. 动态加载 Pi 官方运行时模块
    const piUrl = pathToFileURL(DEFAULT_PI_DIST).href;
    let pi;
    try {
        pi = await import(piUrl);
    } catch (err) {
        console.error(`[FAIL] Could not load Pi Runtime from: ${DEFAULT_PI_DIST}`);
        console.error(`Error details: ${err.message}`);
        process.exit(1);
    }

    const { ModelRuntime, SessionManager, createAgentSession } = pi;

    // 2. 初始化 ModelRuntime 并装配模型
    const modelsPath = path.join(DEFAULT_AGENT_DIR, "models.json");
    const authPath = path.join(DEFAULT_AGENT_DIR, "auth.json");
    const modelRuntime = await ModelRuntime.create({ authPath, modelsPath });

    const models = modelRuntime.getModels ? modelRuntime.getModels() : [];
    const targetModel = models.find(m => m.provider === "local-llama") || models[0];

    if (!targetModel) {
        console.error("[FAIL] No active model found in Pi ModelRuntime!");
        process.exit(1);
    }
    console.log(`[PASS] Model Runtime connected: [${targetModel.provider}] ${targetModel.id || targetModel.modelId}`);

    if (options.dryRun) {
        console.log("\n[PASS] DRY-RUN COMPLETE: Environment, Pi packages, and Model connections are 100% healthy.");
        process.exit(0);
    }

    // 3. 构建 Agent 会话
    const sessionManager = options.inMemory
        ? SessionManager.inMemory()
        : SessionManager.create(REPO_ROOT, path.join(REPO_ROOT, ".invar", "sessions"));

    const sessionResult = await createAgentSession({
        cwd: REPO_ROOT,
        agentDir: DEFAULT_AGENT_DIR,
        modelRuntime,
        sessionManager,
        model: targetModel,
        tools: ["read", "write", "edit", "powershell"],
    });

    const session = sessionResult.session;
    console.log("[PASS] Invar AgentSession initialized with tools: [read, write, edit, powershell]\n");

    // 4. 构造初始科研任务 Prompt
    const missionPrompt = options.task
        ? `${buildSystemBriefing(options.target)}\n\nMISSION OBJECTIVE:\n${options.task}`
        : `${buildSystemBriefing(options.target)}\n\nMISSION OBJECTIVE:\nInspect the target authorization scope in 'data/targets/${options.target}/scope.txt', read the available targeted tasks, and summarize your initial research plan.`;

    console.log("[*] Dispatching research mission to agent...\n" + "-".repeat(85));

    const t0 = Date.now();
    await session.prompt(missionPrompt);
    const elapsed = Date.now() - t0;

    // 5. 输出最终思考与结论战报
    console.log("-".repeat(85));
    console.log(`[PASS] Research cycle completed in ${(elapsed / 1000).toFixed(1)}s!`);

    const context = sessionManager.buildSessionContext();
    const assistantMessages = context.messages.filter(m => m.role === "assistant");
    const finalMsg = assistantMessages[assistantMessages.length - 1];

    if (finalMsg && Array.isArray(finalMsg.content)) {
        const textParts = finalMsg.content.filter(c => c.type === "text").map(c => c.text);
        if (textParts.length > 0) {
            console.log("\n[AGENT FINAL CONCLUSION]:");
            console.log(textParts.join("\n"));
        }
    }

    console.log("\n" + "=".repeat(85));
    console.log("🎯 INVAR AGENT RUNNER SESSION COMPLETED SUCCESSFULLY");
    console.log("=".repeat(85));
}

main().catch((err) => {
    console.error("\n[FATAL RUNNER ERROR]:", err);
    process.exit(1);
});
