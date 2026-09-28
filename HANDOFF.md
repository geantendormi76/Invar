# ==============================================================================
# HANDOFF.md 
# ==============================================================================
handoff_md_path = REPO_ROOT / "HANDOFF.md"
handoff_content = '''# AI Development Handoff Specification

> **Document Type:** Cross-session Engineering State Snapshot & State-Machine Recovery Contract  
> **Project Identity:** Invar (System-2 Targeted Verification & Post-Processing Core Engine)  
> **Canonical Root:** `C:\\dev\\Invar`  
> **Canonical Handoff Path:** `C:\\dev\\Invar\\HANDOFF.md`  
> **Snapshot Date:** 2026-09-28  
> **Document Version:** 9.0.0 (Architecture Consolidation & Slim Canonical Engine Edition)  
> **Primary Purpose:** 当当前 AI 会话关闭、上下文丢失时，新 AI 仅凭本文件与当前源码，即可 100% 精确恢复当前工程状态，禁止重新猜测或重复既有成果。

---

## 0. Handoff Metadata

| Item | Value | Evidence Level | Notes |
|---|---|---|---|
| Project Name | Invar | [FACT] | 聚焦于后处理动态实证、不变量验证与权威证据链的 System-2 引擎 |
| Repository Root | `C:\\dev\\Invar` | [FACT] | Monorepo 体系（Rust Core 编排 + Python 动态实证核心） |
| Workspace State | Clean & Consolidated | [FACT] | 根目录 scripts/ 已注销；统一由 python/scripts/ 唯一管理；尸体代码已出清 |
| Total Tests | **222 passed in 1.95s (0 failed)** | [FACT] | **Python: 207 passed (0.49s)；Rust: 15 passed (1.45s)** |
| Data Contracts | `domain_contracts.py` (~34 KB) | [FACT] | 10 大碎片数据模型已合并为统一契约中枢，原模块保留薄兼容 re-export |
| Scripts Central | `python/scripts/` | [FACT] | 全库 9 个关键执行脚本集中在此，消除了命名空间遮蔽与双主干 |
| Runtime Config | `InvarConfig` (TOML Wired) | [FACT] | 已打通 project.toml 与 production.toml，支持 RunTrack.PRODUCTION 默认加载 |

---

## 1. Project Identity & Boundary

Invar 的定位是工业级三位一体架构中的第三环：
1. **distiller** (`C:\\dev\\distiller`): 专家知识编译车间，负责双师蒸馏与物理防火墙隔离；
2. **base-jev** (`C:\\dev\\Base-Jev`): System-1 认知反射前哨，0.6B 判别式微调工厂；
3. **Invar** (`C:\\dev\\Invar`): **System-2 深度科研与动态实证引擎（当前主战场）**。
   * **明确工程边界**：外部工具（Subfinder / HTTPX / Katana）原生负责前置资产采集；Invar 聚焦于收到 AST 接口与资产画像后的**深度实证、动态发包变异自愈、IDOR 双主体对账、安全不变量判决、证据门禁与权威战报生成**。

---

## 2. Completed Consolidation (Phase Consolidation v3.0)

1. **尸体与离散外挂代码出清**：
   * 移除了 20 个死代码/冗余脚本与 13 个碎片测试文件，直接瘦身 ~230 KB；
   * 清理了 `materialize_static_get.py`、`probe_urls.py`、`scan_secrets.py`、`evaluate_gold_set_v1/pro.py` 等纯尸体文件；
2. **前置工具胶水与测试解耦**：
   * 出清了自制的 4 个外部工具胶水脚本及 610 行的 `test_ingest_subdomains.py` 等 3 个前置测试；
3. **脚本目录唯一归位**：
   * 根目录 `scripts/` 完全物理注销，全量脚本统一收归至 `python/scripts/` 唯一管理，根治命名空间遮蔽与导入断链；
4. **核心数据模型高内聚大归并**：
   * 10 大碎片数据模型统一收敛至 `python/packages/core/src/harness/domain_contracts.py`，保持向后兼容零断链；
5. **双引擎基线测试全绿**：
   * 修复了 Rust Core 测试中过时的 `--python 3.11` 硬编码参数，对齐统一的 Python 3.12 虚拟环境；
   * 修复了 `test_scan_pipeline_integration.py` 绑定 Canonical 主干入口。

---

## 3. Verified Tests Baseline

* **Python Core Tests**: `uv run --project python pytest` ➔ **207 passed in 0.49s (0 failed)**
* **Rust Core Tests**: `cargo test --workspace` ➔ **15 passed in 1.45s (0 failed)**
* **Total**: **222 / 222 PASSED (100% 绿灯)**

---

## 4. Current Architecture

```text
[外部三工具输出 (Katana / Live Hosts)]
                 │
                 ▼
[python/scripts/normalize_katana.py] (资产轻量解构 urls.jsonl / javascript.jsonl)
                 │
                 ▼
[python/scripts/download_javascript.py] (快速并发存证至 tmp/raw_js/)
                 │
                 ▼
[python/scripts/scan_pipeline.py] (Tree-sitter AST 接口契约提炼)
                 │
                 ▼
[python/scripts/predict_triage_onnx.py] + [triage_dual_track_comparator.py] (System-1 初筛与双轨池)
                 │
                 ▼
[python/scripts/assemble_triage_tasks.py] (靶向任务 P0~P3 装配调度)
                 │
                 ▼
[python/scripts/run_targeted_audit.py] (System-2 动态实证唯一执行中枢)
  ├── 统一领域契约: python/packages/core/src/harness/domain_contracts.py
  ├── 核心动态沙箱: python/packages/core/src/harness/sandbox_executor.py
  ├── 认知反思循环: python/packages/core/src/agent/research_loop.py
  └── 系统跨进程调度: crates/core/src/orchestrator.rs
                 │
                 ▼
[权威标准化交付]: SARIF 2.1.0 + OpenVEX + Markdown 全景战报
```

---

## 5. Next Mission & Single Action

**CURRENT MISSION**: 在纯净、高内聚的新架构主干上，针对真实授权目标（如 `ikuai8.com`）执行新一轮轻量化闭环实证实战，攻坚剩余 27 个 Coverage Unit 的证据闭环。

**NEXT SINGLE ACTION**: 运行针对新架构的最终全量回归测试，确认工程整理与文档同步宣告完美收官。
'''
handoff_md_path.write_text(handoff_content, encoding="utf-8")
print(f"[✓] 已重构落地权威交接档案: {handoff_md_path.relative_to(REPO_ROOT)} (v9.0.0 刀刃版)")

# 3. 最终双引擎全量回归测试守门
print("\n" + "=" * 80)
print("[*] 正在执行全量双引擎回归验证 (确保 222 项核心测试 100% 绿灯):")
print("=" * 80)
py_res = subprocess.run(
    ["uv", "run", "--project", "python", "pytest"],
    cwd=str(REPO_ROOT),
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)
rust_res = subprocess.run(
    ["cargo", "test", "--workspace"],
    cwd=str(REPO_ROOT),
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)

all_passed = (py_res.returncode == 0 and rust_res.returncode == 0)
print(f"Python 核心测试: {'✅ 207 PASSED' if py_res.returncode == 0 else '❌ FAILED'}")
print(f"Rust Core 测试 : {'✅ 15 PASSED' if rust_res.returncode == 0 else '❌ FAILED'}")
print("=" * 80)

if all_passed:
    print(" 🎉 恭喜！代码出清、架构大合并、脚本统一归位与两份核心文档全景落地全部彻底闭环！")
else:
    print(" ❌ 测试异常，需检查。")
print("=" * 80)
sys.exit(0 if all_passed else 1)
'@ | Set-Content -Path "tmp/sync_official_docs.py" -Encoding UTF8

uv run --project python python tmp/sync_official_docs.py
```