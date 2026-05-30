# Implementation Plan: Parser Type Alignment

**Branch**: `021-parser-type-alignment` | **Date**: 2026-05-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/021-parser-type-alignment/spec.md`

## Summary

Refactor `parser.py` and `compatibility/parser.py` to use `cucumber_messages.GherkinDocument` (the runtime dataclass) instead of the TypedDict-based `pytest_bdd.compatibility.gherkin.GherkinDocument`. Remove all `cast("GherkinDocument", ...)` calls and fix type annotations so they match actual runtime types. No runtime behavior changes.

## Technical Context

**Language/Version**: Python 3.10–3.14
**Primary Dependencies**: `cucumber_messages`, `gherkin`, `attrs`, `pytest >= 7`
**Storage**: N/A (no new storage)
**Testing**: pytest (existing suite in `tests/`)
**Target Platform**: Cross-platform Python library
**Project Type**: Python library (CLI tooling + pytest plugin)
**Performance Goals**: N/A (no performance impact — type-only changes)
**Constraints**: No runtime behavior changes; existing tests must pass unchanged
**Scale/Scope**: Two files changed: `src/pytest_bdd/parser.py` (~20 lines changed), `src/pytest_bdd/compatibility/parser.py` (~2 lines changed)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| No new dependencies | ✅ PASS | No new packages introduced |
| No runtime behavior changes | ✅ PASS | Pure type annotation fix |
| Existing tests pass | ✅ PASS | Verified requirement: tests unchanged |
| Follows existing conventions (attrs over dataclasses) | ✅ PASS | No structural changes, uses existing types |
| mypy compatibility | ✅ PASS | Goal is to improve mypy accuracy |

## Agentic Implementation Strategy

**Superpowers**: test-driven-development — write no new tests but verify existing suite passes before claiming completion; systematic-debugging — if any test fails after refactoring.

**Subagent Dispatch**: Single-file task. No subagent dispatch needed. This is a focused, linear change to two files.

## Project Structure

### Documentation (this feature)

```text
specs/021-parser-type-alignment/
├── plan.md              # This file
├── research.md          # Phase 0 output (minimal)
├── data-model.md        # Phase 1 output (minimal)
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Source Code

```text
src/pytest_bdd/
├── parser.py                          # PRIMARY: import change, cast removal, type fixes
└── compatibility/
    └── parser.py                      # SECONDARY: ParserProtocol return type update
```

**Structure Decision**: Existing single-project layout. Only two files changed.

## Complexity Tracking

None — no constitution violations.
