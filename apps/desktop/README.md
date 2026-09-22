# Desktop Application

This directory is the product shell: React + TypeScript + Tailwind + Tauri.

The UI is presentation and interaction orchestration only. Domain logic and reusable
compute capabilities belong in `crates/` or `python/packages/` behind explicit contracts.

Bootstrap the actual Tauri frontend with the project-standard frontend toolchain rather
than hand-maintaining a second copy of its generated boilerplate in this scaffold.
