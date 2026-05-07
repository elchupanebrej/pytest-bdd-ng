# Implementation Plan: Test Group Ordering

**Branch**: `020-test-group-ordering` | **Date**: 2026-05-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/spec.md`

## Summary

Add a generic, configurable test-group ordering mechanism for the pytest-bdd-ng test suite. Projects declare an ordered list of group names, a default group, and optional path mappings through pytest ini-style configuration only: `[tool.pytest.ini_options]` in `pyproject.toml` or `pytest.ini`. The initial project configuration will use five generic cost-tier examples: `instant`, `fast`, `medium`, `slow`, and `external`.

Reusable configuration parsing, validation, and item-resolution logic lives in `src/pytest_bdd/util/test_group_ordering.py`. The root `tests/conftest.py` stays as a thin pytest adapter: it registers and reads custom pytest ini options, translates each resolved group into a `pytest-order` ordinal marker, and does not sort or reorder collected items itself. Existing test files and directories remain in place; classification is represented through pytest ini path mappings, existing directory-name matches, and explicit pytest group markers only.

Runtime ordering must preserve group barriers under xdist: no test from a later group may start before every test in all earlier groups has finished. Parallel execution may continue within one group.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `pytest >= 7`, `pytest-order` (new, test dependency), `pytest-xdist >= 3.8.0` (existing)
**Storage**: N/A
**Testing**: `pytest`, `tox`, `pre-commit`, `ruff`, `mypy` where applicable
**Target Platform**: Windows (native), Linux, macOS
**Project Type**: Python library plus internal test infrastructure
**Performance Goals**: <= 2 seconds collection-phase wall-clock overhead compared between `pytest --collect-only` with grouping enabled and disabled
**Constraints**: No hardcoded group names; no test tree moves; no direct item sorting in project hooks; xdist runtime group barriers; pytest ini-style configuration only; all documentation in English
**Scale/Scope**: Existing mixed `tests/` tree classified through pytest ini path mappings and markers; initial example config contains five groups

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pure BDD Integration | Pass | No feature-file syntax or pytest-bdd runtime behaviour changes |
| II. Realistic Runtime Evidence | Pass | No synthetic reporter/runtime payloads introduced |
| III. Explicit Returns & Determinism | Pass | Source utility returns explicit dataclasses or deterministic warnings/fallbacks; pytest hooks may follow pytest hook return conventions |
| IV. Broad Compatibility | Pass | Uses pytest-supported ini/marker APIs and maintained pytest plugins for Python 3.10-3.14 |
| V. Quality & Formatting Discipline | Pass | New source utility is covered by repository lint/type gates; docs and plans remain in English |

**Post-Phase-1 re-check**: Pass. The design keeps ordering delegated to pytest plugins, moves reusable logic into `src/pytest_bdd/util/`, keeps `tests/conftest.py` as adapter-only code, and uses pytest ini-style configuration only.

## Agentic Implementation Strategy

**Superpowers**:
- `test-driven-development` for RED-GREEN-REFACTOR implementation of config parsing, validation, resolution, adapter behaviour, and runtime ordering validation.
- `systematic-debugging` for any ordering, plugin, xdist scheduling, or fixture-skip interaction failures.

**Subagent Dispatch**:
- **Subagent A (source utility)**: Implement `src/pytest_bdd/util/test_group_ordering.py` with tests for pytest ini parsing, validation warnings, path matching, marker recognition, default fallback, and ordinal calculation.
- **Subagent B (pytest adapter and configuration)**: Update `tests/conftest.py`, `pyproject.toml`, and dependency declarations so the adapter registers custom ini options, applies `pytest.mark.order(N)`, and never sorts `items`.
- **Subagent C (runtime validation)**: Implement acceptance validation for fixture-driven skips, xdist runtime group barriers, per-group marker filtering, and collection overhead.
- **Subagent D (existing-tree classification)**: Audit existing `tests/` directories and express the initial five-group mapping through pytest ini path mappings and minimal group markers, without moving or renaming tests.

All implementation subagents must avoid hardcoded ignore lists for non-group markers. The resolver must treat only configured group names as group signals.

## Project Structure

### Documentation (this feature)

```text
specs/020-test-group-ordering/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── group-config.md
└── tasks.md
```

### Source Code (repository root)

```text
src/pytest_bdd/util/
└── test_group_ordering.py       # reusable parser, validator, resolver, adapter helpers

tests/
├── conftest.py                  # thin pytest adapter; ini registration + marker translation only
└── [existing dirs]/             # preserved; no moves or renames for this feature

pyproject.toml                   # pytest ini options, marker registration, pytest-order options
```

**Structure Decision**: Reusable logic belongs under `src/pytest_bdd/util/` so it is linted, type-checked, and reusable outside the test tree. `tests/conftest.py` may register pytest ini options and adapt source utility output to pytest collection, but must not contain core parsing or resolution algorithms.

## Complexity Tracking

No constitution violations requiring justification.

---

## Phase 0: Research Findings

Complete. See [research.md](./research.md).

Key decisions:
- **Plugin**: `pytest-order` provides the baseline collection ordering through `order(N)` markers.
- **Runtime barriers**: xdist requires explicit runtime validation; if `pytest-order` alone cannot guarantee cross-worker barriers, implementation must add or select a pytest-compatible barrier mechanism while preserving the no-direct-sort rule for project hooks.
- **Utility location**: `src/pytest_bdd/util/test_group_ordering.py`.
- **Adapter boundary**: `tests/conftest.py` registers/reads pytest ini options and translates resolved group names into `order(N)` marks only.
- **Config**: pytest ini-style options under `[tool.pytest.ini_options]` or `pytest.ini`; no `[tool.pytest-bdd-ng.*]` table.
- **Examples**: Initial five-group example order is `instant`, `fast`, `medium`, `slow`, `external`; names are configurable and not hardcoded.
- **Tree policy**: Existing test tree remains unchanged.
- **Marker policy**: Only configured group names are group markers; all other pytest markers are ignored without hardcoded ignore lists.

## Phase 1: Design & Contracts

Complete.

| Artifact | Path | Status |
|----------|------|--------|
| Data model | [data-model.md](./data-model.md) | Done |
| Configuration contract | [contracts/group-config.md](./contracts/group-config.md) | Done |
| Quickstart | [quickstart.md](./quickstart.md) | Done |

## Phase 2 Preview

`/speckit.tasks` must regenerate implementation tasks because previous task output targeted a tool-specific TOML table and only collect-only xdist validation.
