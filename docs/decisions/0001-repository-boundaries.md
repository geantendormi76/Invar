# ADR-0001: Repository Boundaries

## Decision

Use stable top-level boundaries for applications, Rust crates, Python packages,
configuration, data, models, runs, artifacts, tests, scripts, documentation and tools.

## Rationale

Directory boundaries are treated as engineering boundaries. Generated data and model
weights have distinct lifecycles from source code. Application shells depend on reusable
engine packages rather than owning domain logic.
