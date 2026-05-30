# Implementation Plan: Standardize Project Workflows on `uv`

**Branch**: `018-uv-workflow-migration` | **Date**: 2026-04-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/018-uv-workflow-migration/spec.md`

## Summary

Migrate the project's canonical testing infrastructure and test matrix coordination to be driven by `uv` and `tox-uv`. This includes explicitly tracking `uv` in `pyproject.toml` (specifically `testenv` optional dependency scopes) to decouple internal dependency tracking from outer feature testing constraints. Additionally, ensure internal validation scripts and governance hooks perform identically via native `[project.scripts]` entrypoints without requiring the previous environment-manager workflow or global pip environments.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `uv`, `tox-uv`, `astral-sh/setup-uv`
**Storage**: N/A
**Testing**: `pytest`, `tox-uv`
**Target Platform**: GitHub Actions CI, local shells (Linux/macOS/Windows)
**Project Type**: Python library and CLI tooling
**Performance Goals**: Reduce testing and bootstrapping time by eliminating previous environment-manager locking overhead.
**Constraints**: Must strictly retain compatibility matrix configurations inside `tox.ini` alongside `tool.mypy` bounds.
**Scale/Scope**: Impacts all active contributors running functional tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle IV. Broad Compatibility**: Preserved by checking all Python versions via test environments managed securely under `uv`.
- **Principle V. Quality & Formatting Discipline**: Ensures validation scripts directly map to `uvx` behavior natively by tracking them in `[project.scripts]`.
- **Development Practices**: Constitution directly asserts the use of `uv` for environment provisioning. Tracking `uv` locally satisfies tests without bloating core logic boundaries.

## Agentic Implementation Strategy

*GATE: Define how Superpowers and subagents will be leveraged.*

**Superpowers**: `subagent-driven-development`, `test-driven-development`.
**Subagent Dispatch**: Subordinate agents will handle `.github/workflows` conversions (replacing actions/setup-python with astral-sh/setup-uv) sequentially while the primary orchestration aligns top-level components (e.g. `pyproject.toml`, `Makefile`, and document links) avoiding interference.

## Project Structure

### Documentation (this feature)

```text
specs/018-uv-workflow-migration/
├── plan.md              # This file
├── research.md          # Output
├── data-model.md        # N/A
├── quickstart.md        # Output
└── tasks.md             # Pending
```

### Source Code (repository root)

```text
pyproject.toml
tox.ini
Makefile
.github/workflows/
├── main.yml
├── messages-baseline-drift.yml
└── release.yaml
docs/
└── internal/feature-heading-validation.rst
README.rst
DOCUMENTATION.rst
```

**Structure Decision**: Global configuration migration overlay applied to root toolchains, `.github`, and `.rst` documentation artifacts.

## Complexity Tracking

N/A. Overwhelming reduction in complexity via removal of legacy layers.
