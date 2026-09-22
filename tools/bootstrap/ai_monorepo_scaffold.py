from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from textwrap import dedent


ROOT_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "Cargo.toml",
    "README.md",
    "HANDOFF.md",
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "ai-workspace"


def py_name(value: str) -> str:
    return slugify(value).replace("-", "_")


def write_file(path: Path, content: str, *, force: bool) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return False
    path.write_text(dedent(content).lstrip(), encoding="utf-8", newline="\n")
    return True


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def create_dirs(root: Path) -> list[Path]:
    dirs = [
        # 产品 / 应用边界
        root / "apps" / "desktop" / "src",
        root / "apps" / "desktop" / "src-tauri" / "src",
        root / "apps" / "desktop" / "src-tauri" / "capabilities",
        root / "apps" / "desktop" / "src-tauri" / "icons",
        # Rust workspace
        root / "crates" / "core",
        # Python / uv workspace
        root / "python" / "packages" / "core",
        root / "python" / "scripts",
        root / "python" / "tests",
        # 配置注入层
        root / "configs" / "base",
        root / "configs" / "profiles",
        root / "configs" / "local",
        root / "configs" / "examples",
        root / "configs" / "schemas",
        root / "configs" / "registry",
        # 数据生命周期
        root / "data" / "inbox",
        root / "data" / "raw",
        root / "data" / "interim",
        root / "data" / "processed",
        root / "data" / "fixtures",
        root / "data" / "manifests",
        # 模型生命周期
        root / "models" / "registry",
        root / "models" / "checkpoints",
        root / "models" / "adapters",
        root / "models" / "tokenizers",
        root / "models" / "cache",
        # 可复现实验 / 执行记录
        root / "runs",
        # 可交付产物
        root / "artifacts" / "reports",
        root / "artifacts" / "metrics",
        root / "artifacts" / "exports",
        root / "artifacts" / "packages",
        # 测试层
        root / "tests" / "integration",
        root / "tests" / "e2e",
        root / "tests" / "contract",
        root / "tests" / "fixtures",
        # 工程自动化
        root / "scripts" / "bootstrap",
        root / "scripts" / "build",
        root / "scripts" / "data",
        root / "scripts" / "audit",
        root / "scripts" / "release",
        # 人类文档 / AI 上下文
        root / "docs" / "architecture",
        root / "docs" / "research",
        root / "docs" / "decisions",
        root / "docs" / "ai",
        # 开发工具 / 临时空间
        root / "tools" / "bootstrap",
        root / "tools" / "repomix",
        root / "tmp" / "repomix",
        root / ".github" / "workflows",
        root / "apps" / "desktop" / "src",
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
    return dirs


def create_gitkeeps(root: Path) -> None:
    keep_dirs = [
        "apps/desktop/src",
        "apps/desktop/src-tauri/src",
        "apps/desktop/src-tauri/capabilities",
        "apps/desktop/src-tauri/icons",
        "python/scripts",
        "python/tests",
        "configs/base",
        "configs/profiles",
        "configs/local",
        "configs/examples",
        "configs/schemas",
        "configs/registry",
        "data/inbox",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/fixtures",
        "data/manifests",
        "models/registry",
        "models/checkpoints",
        "models/adapters",
        "models/tokenizers",
        "models/cache",
        "runs",
        "artifacts/reports",
        "artifacts/metrics",
        "artifacts/exports",
        "artifacts/packages",
        "tests/integration",
        "tests/e2e",
        "tests/contract",
        "tests/fixtures",
        "scripts/bootstrap",
        "scripts/build",
        "scripts/data",
        "scripts/audit",
        "scripts/release",
        "docs/architecture",
        "docs/research",
        "docs/decisions",
        "docs/ai",
        "tools/repomix",
        "tmp/repomix",
    ]
    for relative in keep_dirs:
        touch(root / relative / ".gitkeep")


def generate_files(root: Path, project: str, *, force: bool) -> list[str]:
    package = py_name(project)
    rust_package = slugify(project)
    created: list[str] = []

    def put(relative: str, content: str) -> None:
        if write_file(root / relative, content, force=force):
            created.append(relative)

    put(
        ".editorconfig",
        r'''
        root = true

        [*]
        charset = utf-8
        end_of_line = lf
        insert_final_newline = true
        indent_style = space
        indent_size = 4
        trim_trailing_whitespace = true

        [*.{yaml,yml,json,toml,md}]
        indent_size = 2

        [*.{ps1,bat,cmd}]
        end_of_line = crlf
        ''',
    )

    put(
        ".gitattributes",
        r'''
        * text=auto eol=lf
        *.ps1 text eol=crlf
        *.bat text eol=crlf
        *.cmd text eol=crlf

        *.png binary
        *.jpg binary
        *.jpeg binary
        *.webp binary
        *.ico binary
        *.pdf binary
        *.onnx binary
        *.gguf binary
        *.safetensors binary
        *.pt binary
        *.pth binary
        *.bin binary
        *.wasm binary
        *.so binary
        *.dll binary
        *.dylib binary
        *.exe binary
        *.lib binary
        *.pdb binary
        ''',
    )

    put(
        ".gitignore",
        r'''
        # ---- OS / IDE ----
        .DS_Store
        Thumbs.db
        .idea/
        .vscode/*
        !.vscode/extensions.json
        !.vscode/settings.json
        *.swp
        *.swo

        # ---- Environment / secrets ----
        .env
        .env.*
        !.env.example
        configs/local/**
        !configs/local/.gitkeep

        # ---- Rust / Cargo ----
        target/
        **/target/
        **/*.rs.bk
        apps/desktop/src-tauri/gen/
        # This repository contains executable application crates, so Cargo.lock is versioned.
        !Cargo.lock

        # ---- Python / uv ----
        **/.venv/
        **/__pycache__/
        *.py[cod]
        .pytest_cache/
        .mypy_cache/
        .ruff_cache/
        .coverage
        htmlcov/
        .uv_cache/
        python/.venv/

        # ---- Node / frontend ----
        **/node_modules/
        **/dist/
        **/dist-ssr/
        .pnpm-debug.log*
        npm-debug.log*
        yarn-debug.log*
        yarn-error.log*
        *.local

        # ---- AI weights / caches ----
        models/checkpoints/**
        models/adapters/**
        models/tokenizers/**
        models/cache/**
        !models/*/.gitkeep
        *.gguf
        *.onnx
        *.safetensors
        *.pt
        *.pth
        *.bin

        # ---- User / private data ----
        data/inbox/**
        data/raw/**
        data/interim/**
        data/processed/**
        !data/*/.gitkeep

        # ---- Runs / generated artifacts / temporary workspace ----
        runs/**
        !runs/.gitkeep
        tmp/**
        !tmp/**/.gitkeep
        artifacts/**
        !artifacts/*/.gitkeep
        repomix-output*.xml
        *_report.md
        *.tmp
        *.bak
        ''',
    )

    put(
        "Cargo.toml",
        f'''
        [workspace]
        members = [
            "crates/*",
            "apps/*/src-tauri",
        ]
        resolver = "3"
        default-members = [
            "crates/*",
        ]

        [workspace.package]
        edition = "2024"
        version = "0.1.0"
        publish = false
        ''',
    )

    put(
        "package.json",
        f'''
        {{
          "name": "{package}-workspace",
          "private": true,
          "scripts": {{
            "desktop:dev": "pnpm --dir apps/desktop tauri dev",
            "desktop:build": "pnpm --dir apps/desktop tauri build"
          }}
        }}
        ''',
    )

    put(
        "pnpm-workspace.yaml",
        r'''
        packages:
          - "apps/*"
        ''',
    )

    put(
        "python/pyproject.toml",
        f'''
        [project]
        name = "{package}-workspace"
        version = "0.1.0"
        description = "Python AI workspace for {project}"
        requires-python = ">=3.11,<3.14"
        dependencies = []

        [tool.uv]
        package = false

        [tool.uv.workspace]
        members = ["packages/*"]

        [dependency-groups]
        dev = [
            "pytest>=8",
            "ruff>=0.12",
            "mypy>=1.17",
        ]
        ''',
    )

    put(
        "python/.python-version",
        "3.12\n",
    )

    put(
        f"python/packages/core/pyproject.toml",
        f'''
        [project]
        name = "{package}-core"
        version = "0.1.0"
        description = "Core Python contracts and orchestration primitives"
        requires-python = ">=3.11,<3.14"
        dependencies = [
            "pydantic>=2",
        ]

        [tool.uv]
        package = true

        [build-system]
        requires = ["uv_build>=0.12.17,<0.13"]
        build-backend = "uv_build"
        ''',
    )
    put(
        f"python/packages/core/src/{package}/__init__.py",
        '"""Core Python package for the AI workspace."""\n',
    )
    put(
        f"python/packages/core/tests/test_smoke.py",
        '''
        def test_core_package_importable() -> None:
            import PROJECT_PACKAGE

            assert PROJECT_PACKAGE.__name__ == "PROJECT_PACKAGE"
        '''.replace("PROJECT_PACKAGE", package),
    )

    put(
        "crates/core/Cargo.toml",
        f'''
        [package]
        name = "{rust_package}-core"
        version.workspace = true
        edition.workspace = true
        publish.workspace = true

        [dependencies]
        serde = {{ version = "1", features = ["derive"] }}
        serde_json = "1"
        ''',
    )
    put(
        "crates/core/src/lib.rs",
        r'''
        //! Stable Rust core boundary for shared domain contracts and engine capabilities.
        
        /// Minimal marker proving the workspace crate is wired correctly.
        #[derive(Debug, Clone, Copy, PartialEq, Eq)]
        pub struct WorkspaceCore;
        ''',
    )
    put(
        "crates/core/tests/smoke.rs",
        r'''
        use PROJECT_CORE::WorkspaceCore;
        
        #[test]
        fn workspace_core_is_available() {
            assert_eq!(WorkspaceCore, WorkspaceCore);
        }
        '''.replace("PROJECT_CORE", rust_package.replace("-", "_")),
    )

    put(
        "apps/desktop/package.json",
        r'''
        {
          "name": "desktop",
          "private": true,
          "version": "0.1.0",
          "type": "module",
          "scripts": {
            "dev": "vite",
            "build": "tsc -b && vite build",
            "preview": "vite preview",
            "tauri": "tauri"
          },
          "dependencies": {
            "@tauri-apps/api": "^2",
            "react": "^19",
            "react-dom": "^19"
          },
          "devDependencies": {
            "@tailwindcss/vite": "^4",
            "@tauri-apps/cli": "^2",
            "@types/react": "^19",
            "@types/react-dom": "^19",
            "@vitejs/plugin-react": "^5",
            "tailwindcss": "^4",
            "typescript": "^5",
            "vite": "^7"
          }
        }
        ''',
    )
    put(
        "apps/desktop/index.html",
        r'''
        <!doctype html>
        <html lang="zh-CN">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>AI Workspace</title>
          </head>
          <body>
            <div id="root"></div>
            <script type="module" src="/src/main.tsx"></script>
          </body>
        </html>
        ''',
    )
    put(
        "apps/desktop/src/main.tsx",
        r'''
        import React from "react";
        import ReactDOM from "react-dom/client";
        import App from "./App";
        import "./index.css";
        
        ReactDOM.createRoot(document.getElementById("root")!).render(
          <React.StrictMode>
            <App />
          </React.StrictMode>,
        );
        ''',
    )
    put(
        "apps/desktop/src/App.tsx",
        r'''
        export default function App() {
          return (
            <main className="min-h-screen bg-slate-950 text-slate-100">
              <section className="mx-auto flex min-h-screen max-w-6xl items-center px-8">
                <div>
                  <p className="text-sm font-medium text-slate-400">AI Engineering Workspace</p>
                  <h1 className="mt-3 text-4xl font-semibold tracking-tight">React + TypeScript + Tailwind + Tauri</h1>
                  <p className="mt-4 max-w-2xl text-slate-300">
                    UI is an application boundary. Reusable domain and compute logic belongs behind Rust/Python contracts.
                  </p>
                </div>
              </section>
            </main>
          );
        }
        ''',
    )
    put(
        "apps/desktop/src/index.css",
        r'''
        @import "tailwindcss";
        
        :root {
          font-family: Inter, ui-sans-serif, system-ui, sans-serif;
        }
        
        html,
        body,
        #root {
          min-height: 100%;
          margin: 0;
        }
        ''',
    )
    put(
        "apps/desktop/vite.config.ts",
        r'''
        import { defineConfig } from "vite";
        import react from "@vitejs/plugin-react";
        import tailwindcss from "@tailwindcss/vite";
        
        export default defineConfig({
          plugins: [react(), tailwindcss()],
          clearScreen: false,
          server: {
            port: 1420,
            strictPort: true,
          },
        });
        ''',
    )
    put(
        "apps/desktop/tsconfig.json",
        r'''
        {
          "files": [],
          "references": [
            { "path": "./tsconfig.app.json" },
            { "path": "./tsconfig.node.json" }
          ]
        }
        ''',
    )
    put(
        "apps/desktop/tsconfig.app.json",
        r'''
        {
          "compilerOptions": {
            "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
            "target": "ES2022",
            "useDefineForClassFields": true,
            "lib": ["ES2022", "DOM", "DOM.Iterable"],
            "allowJs": false,
            "skipLibCheck": true,
            "esModuleInterop": true,
            "allowSyntheticDefaultImports": true,
            "strict": true,
            "module": "ESNext",
            "moduleResolution": "Bundler",
            "resolveJsonModule": true,
            "isolatedModules": true,
            "noEmit": true,
            "jsx": "react-jsx"
          },
          "include": ["src"]
        }
        ''',
    )
    put(
        "apps/desktop/tsconfig.node.json",
        r'''
        {
          "compilerOptions": {
            "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
            "target": "ES2023",
            "lib": ["ES2023"],
            "module": "ESNext",
            "skipLibCheck": true,
            "moduleResolution": "Bundler",
            "allowImportingTsExtensions": true,
            "verbatimModuleSyntax": true,
            "moduleDetection": "force",
            "noEmit": true,
            "strict": true
          },
          "include": ["vite.config.ts"]
        }
        ''',
    )

    put(
        "apps/desktop/src-tauri/Cargo.toml",
        f'''
        [package]
        name = "{rust_package}-desktop"
        version.workspace = true
        edition.workspace = true
        publish.workspace = true
        build = "build.rs"

        [lib]
        name = "{rust_package.replace('-', '_')}_desktop_lib"
        crate-type = ["staticlib", "cdylib", "rlib"]

        [build-dependencies]
        tauri-build = {{ version = "2" }}

        [dependencies]
        serde = {{ version = "1", features = ["derive"] }}
        serde_json = "1"
        tauri = {{ version = "2" }}
        ''',
    )
    put(
        "apps/desktop/src-tauri/build.rs",
        r'''
        fn main() {
            tauri_build::build();
        }
        ''',
    )
    put(
        "apps/desktop/src-tauri/src/lib.rs",
        r'''
        #[cfg_attr(mobile, tauri::mobile_entry_point)]
        pub fn run() {
            tauri::Builder::default()
                .run(tauri::generate_context!())
                .expect("error while running Tauri application");
        }
        ''',
    )
    put(
        "apps/desktop/src-tauri/src/main.rs",
        f'''
        fn main() {{
            {rust_package.replace('-', '_')}_desktop_lib::run();
        }}
        ''',
    )
    put(
        "apps/desktop/src-tauri/tauri.conf.json",
        f'''
        {{
          "$schema": "https://schema.tauri.app/config/2",
          "productName": "{project}",
          "version": "0.1.0",
          "identifier": "com.aiworkspace.{rust_package}",
          "build": {{
            "beforeDevCommand": "pnpm dev",
            "beforeBuildCommand": "pnpm build",
            "devUrl": "http://localhost:1420",
            "frontendDist": "../dist"
          }},
          "app": {{
            "windows": [
              {{
                "title": "{project}",
                "width": 1280,
                "height": 800
              }}
            ],
            "security": {{
              "csp": {{
                "default-src": "'self' customprotocol: asset:",
                "connect-src": "ipc: http://ipc.localhost",
                "img-src": "'self' asset: http://asset.localhost blob: data:",
                "style-src": "'unsafe-inline' 'self'"
              }}
            }}
          }},
          "bundle": {{
            "active": false
          }}
        }}
        ''',
    )
    put(
        "apps/desktop/src-tauri/capabilities/default.json",
        r'''
        {
          "identifier": "default",
          "description": "Default capability set for the desktop shell.",
          "windows": ["main"],
          "permissions": ["core:default"]
        }
        ''',
    )

    put(
        "configs/README.md",
        r'''
        # Configuration Injection Contract

        `configs/` is the single declarative configuration layer of the repository.
        Product code must not scatter environment-specific constants across source files.

        ## Precedence

        The intended merge order is:

        `base -> profile -> local -> environment -> CLI`

        Later layers override earlier layers. A runtime must expose the resolved configuration
        as a typed object before entering domain logic.

        ## Directories

        - `base/`: committed defaults and stable contracts.
        - `profiles/`: named runtime profiles such as `dev`, `research`, `offline`, `prod`.
        - `local/`: machine-specific overrides; never commit secrets here.
        - `examples/`: safe templates that can be copied into `local/`.
        - `schemas/`: validation schemas and compatibility contracts.
        - `registry/`: model/backend/provider/plugin registration metadata.

        ## Hot-plug rule

        Adding or replacing an implementation should normally require:

        1. implementing the stable Rust/Python interface;
        2. registering the implementation by an explicit identifier;
        3. selecting it through configuration.

        The orchestration layer should not contain implementation-specific path checks,
        filename checks, magic numbers, or provider-specific branches.

        Secrets belong in environment variables or an OS secret store, not in tracked TOML files.
        ''',
    )
    put(
        "configs/base/project.toml",
        f'''
        [project]
        name = "{project}"
        profile = "research"

        [paths]
        data = "data"
        models = "models"
        runs = "runs"
        artifacts = "artifacts"

        [runtime]
        backend = "default"
        execution = "local"
        ''',
    )
    put(
        "configs/profiles/research.toml",
        r'''
        [runtime]
        backend = "research"
        execution = "local"
        reproducible = true
        ''',
    )
    put(
        "configs/examples/local.example.toml",
        r'''
        # Copy this file into configs/local/ and customize locally.
        # Do not place API keys or passwords in tracked config files.

        [runtime]
        # backend = "your-local-backend"

        [paths]
        # models = "D:/AI/models"
        ''',
    )
    put(
        "configs/registry/backends.toml",
        r'''
        # Declarative backend registry.
        # The implementation identifier must map to a registered adapter in code.

        [backends.default]
        implementation = "placeholder"

        [backends.research]
        implementation = "placeholder"
        ''',
    )
    put(
        "configs/schemas/config.schema.json",
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": f"{project} configuration",
                "type": "object",
                "properties": {
                    "project": {"type": "object"},
                    "paths": {"type": "object"},
                    "runtime": {"type": "object"},
                },
                "additionalProperties": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    put(
        "apps/desktop/README.md",
        r'''
        # Desktop Application

        This directory is the product shell: React + TypeScript + Tailwind + Tauri.

        The UI is presentation and interaction orchestration only. Domain logic and reusable
        compute capabilities belong in `crates/` or `python/packages/` behind explicit contracts.

        Bootstrap the actual Tauri frontend with the project-standard frontend toolchain rather
        than hand-maintaining a second copy of its generated boilerplate in this scaffold.
        ''',
    )
    
    put(
        "apps/desktop/src-tauri/README.md",
        r'''
        # Tauri Runtime Boundary

        Tauri is the application boundary, not the domain layer.

        - `src/`: application commands, lifecycle and Tauri integration.
        - `capabilities/`: Tauri permission/capability definitions.
        - `icons/`: packaged application assets.
        - shared Rust logic belongs in the root Cargo workspace under `crates/`.
        ''',
    )

    put(
        "docs/ai/HANDOFF.md",
        r'''
        # AI Engineering Handoff

        ## Current State

        - Current objective:
        - Last verified commit:
        - Last verified test command:
        - Known failures:

        ## Architecture Decisions

        Record only project-specific facts that an AI agent needs to continue safely.

        ## Active Data / Config Contracts

        - Config profile:
        - Input data location:
        - Output artifact location:

        ## Next Safe Action

        State one concrete next engineering action. Do not write speculative tasks.
        ''',
    )
    put(
        "docs/ai/README.md",
        r'''
        # AI Context

        This directory contains durable project-specific context for AI-assisted engineering.
        It is not a scratchpad.

        Keep facts that remain useful across sessions here: architecture constraints, validated
        decisions, handoff state, and stable operational knowledge.
        ''',
    )
    put(
        "docs/decisions/0001-repository-boundaries.md",
        r'''
        # ADR-0001: Repository Boundaries

        ## Decision

        Use stable top-level boundaries for applications, Rust crates, Python packages,
        configuration, data, models, runs, artifacts, tests, scripts, documentation and tools.

        ## Rationale

        Directory boundaries are treated as engineering boundaries. Generated data and model
        weights have distinct lifecycles from source code. Application shells depend on reusable
        engine packages rather than owning domain logic.
        ''',
    )

    put(
        "HANDOFF.md",
        r'''
        占位符
        ''',
    )

    put(
        "README.md",
        f'''
        # {project}

        An AI engineering monorepo for research, inference, agents, training, data processing,
        desktop applications and systems software.

        ## Repository map

        | Path | Responsibility | Lifecycle |
        |---|---|---|
        | `apps/` | shippable applications / entry points | product |
        | `crates/` | reusable Rust engines and domain modules | source |
        | `python/` | uv-managed Python workspace | source |
        | `configs/` | configuration injection and registries | declarative |
        | `data/` | datasets and transformed inputs | data |
        | `models/` | model metadata, weights, adapters and caches | large / external |
        | `runs/` | per-execution state and reproducibility records | generated |
        | `artifacts/` | intentional outputs and reports | generated |
        | `tests/` | cross-cutting verification | source |
        | `scripts/` | orchestration / maintenance | tooling |
        | `docs/` | architecture, research and AI handoff | durable knowledge |
        | `tools/` | developer tooling | tooling |
        | `tmp/` | disposable workspace | ephemeral |

        ## Core commands

        Rust workspace:

        ```text
        cargo check --workspace
        cargo test --workspace
        ```

        Frontend / Tauri:

        ```text
        pnpm install
        pnpm desktop:dev
        pnpm desktop:build
        ```

        Python workspace:

        ```text
        cd python
        uv sync
        uv run pytest
        ```

        AI context packaging:

        ```text
        npx repomix -c tools/repomix/1_.json
        ```

        The resulting context bundle is disposable and belongs under `tmp/repomix/`.

        ## Configuration contract

        Configuration is layered as:

        `base -> profile -> local -> environment -> CLI`

        Backend/model/provider selection belongs in `configs/registry/` and should be connected
        to stable adapters rather than implementation-specific branching in orchestration code.
        ''',
    )

    put(
        "tools/repomix/1_.json",
        r'''
        {
            "$schema": "https://repomix.com/schemas/latest/schema.json",

            "input": {
                "maxFileSize": 50000000
            },

            "output": {
                "filePath": "tmp/repomix/project-handoff.xml",
                "filePathStyle": "target-relative",
                "style": "xml",
                "compress": false,
                "headerText": "本文件是 AI 工程会话交接包。优先阅读 HANDOFF.md、README.md、configs/schemas，然后根据任务读取对应源码、测试和配置。不得把本文件视为替代源码树的永久事实源；实际修改前必须以仓库当前源码和测试为准。",
                "fileSummary": true,
                "directoryStructure": true,
                "includeFullDirectoryStructure": true,
                "includeEmptyDirectories": false,
                "files": true,
                "removeComments": false,
                "removeEmptyLines": false,
                "showLineNumbers": true,
                "truncateBase64": true,
                "git": {
                    "sortByChanges": true,
                    "sortByChangesMaxCommits": 100,
                    "includeDiffs": false,
                    "includeLogs": false,
                    "includeLogsCount": 50
                }
            },

            "include": [
                "HANDOFF.md",
                "README.md",
                "Cargo.toml",
                "Cargo.lock",
                "package.json",
                "pnpm-workspace.yaml",
                "pnpm-lock.yaml",
                "rust-toolchain.toml",
                ".github/**/*",
                "apps/desktop/src/**/*",
                "apps/desktop/src-tauri/src/**/*",
                "apps/desktop/src-tauri/capabilities/**/*",
                "apps/desktop/src-tauri/tauri.conf.json",
                "apps/desktop/src-tauri/Cargo.toml",
                "crates/**/*",
                "python/pyproject.toml",
                "python/uv.lock",
                "python/packages/**/*",
                "python/scripts/**/*",
                "python/tests/**/*",
                "configs/base/**/*",
                "configs/profiles/**/*",
                "configs/examples/**/*",
                "configs/schemas/**/*",
                "configs/registry/**/*",
                "data/manifests/**/*",
                "data/fixtures/**/*",
                "models/registry/**/*",
                "runs/**/manifest.*",
                "runs/**/config.*",
                "runs/**/metadata.*",
                "tests/**/*",
                "scripts/**/*",
                "docs/**/*",
                "tools/**/*"
            ],

            "ignore": {
                "useGitignore": true,
                "useDotIgnore": true,
                "useDefaultPatterns": true,
                "customPatterns": [
                    "tmp/repomix/**",
                    "**/repomix-output*.xml",
                    ".env",
                    ".env.*",
                    "**/.env",
                    "**/.env.*",
                    "**/*.pem",
                    "**/*.key",
                    "**/*.p12",
                    "**/*.pfx",
                    "**/secrets/**",
                    "**/*credentials*/**",
                    "models/checkpoints/**",
                    "models/cache/**",
                    "models/**/*.gguf",
                    "models/**/*.safetensors",
                    "models/**/*.onnx",
                    "models/**/*.bin",
                    "models/**/*.pt",
                    "models/**/*.pth",
                    "models/**/*.ckpt",
                    "models/**/*.msgpack",
                    "data/raw/**",
                    "data/interim/**",
                    "data/processed/**",
                    "data/**/*.csv",
                    "data/**/*.parquet",
                    "data/**/*.arrow",
                    "data/**/*.jsonl",
                    "data/**/*.sqlite",
                    "data/**/*.db",
                    "data/**/*.xlsx",
                    "data/**/*.xls",
                    "data/**/*.docx",
                    "data/**/*.pdf",
                    "runs/**/outputs/**",
                    "runs/**/artifacts/**",
                    "runs/**/checkpoints/**",
                    "runs/**/*.log",
                    "artifacts/**",
                    "tmp/**",
                    "**/node_modules/**",
                    "**/dist/**",
                    "**/dist-ssr/**",
                    "**/build/**",
                    "**/target/**",
                    "**/*.rs.bk",
                    "**/.venv/**",
                    "**/.uv/**",
                    "**/.uv_cache/**",
                    "**/__pycache__/**",
                    "**/*.pyc",
                    "**/*.pyo",
                    "**/.pytest_cache/**",
                    "**/.mypy_cache/**",
                    "**/.ruff_cache/**",
                    "**/.DS_Store",
                    "**/Thumbs.db",
                    "**/.idea/**",
                    "**/.vscode/**",
                    "**/*.exe",
                    "**/*.dll",
                    "**/*.so",
                    "**/*.dylib",
                    "**/*.lib",
                    "**/*.a",
                    "**/*.wasm",
                    "**/*.pdb",
                    "**/*.zip",
                    "**/*.7z",
                    "**/*.tar",
                    "**/*.gz",
                    "**/coverage/**",
                    "**/.coverage",
                    "**/*.tmp",
                    "**/*.log"
                ]
            },

            "security": {
                "enableSecurityCheck": true
            },

            "tokenCount": {
                "encoding": "o200k_base"
            }
        }
        ''',
    )

    return created


def maybe_install_self(root: Path, source: Path, *, force: bool) -> None:
    destination = root / "tools" / "bootstrap" / "ai_monorepo_scaffold.py"
    try:
        if source.resolve() == destination.resolve():
            return
    except FileNotFoundError:
        pass
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        return
    shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a reusable AI engineering monorepo skeleton.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Target repository root (default: current directory).")
    parser.add_argument("--name", help="Project name. Defaults to the target directory name.")
    parser.add_argument("--force", action="store_true", help="Overwrite files managed by this scaffold.")
    parser.add_argument("--dry-run", action="store_true", help="Create nothing; only print the planned topology.")
    args = parser.parse_args()

    root = args.root.resolve()
    project = args.name.strip() if args.name else root.name

    if args.dry_run:
        print(f"Target: {root}")
        print(f"Project: {project}")
        print("Topology: apps / crates / python / configs / data / models / runs / artifacts / tests / scripts / docs / tools / tmp")
        return 0

    root.mkdir(parents=True, exist_ok=True)
    create_dirs(root)
    create_gitkeeps(root)
    created = generate_files(root, project, force=args.force)

    source = Path(__file__).resolve()
    maybe_install_self(root, source, force=args.force)

    print("=" * 72)
    print(f"AI monorepo scaffold ready: {project}")
    print(f"Root: {root}")
    print(f"Created/updated managed files: {len(created)}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
