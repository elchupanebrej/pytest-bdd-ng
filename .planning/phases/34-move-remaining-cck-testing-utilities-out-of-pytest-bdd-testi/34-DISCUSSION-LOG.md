# Phase 34: Move remaining CCK testing utilities out of pytest_bdd/testing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-12
**Phase:** 34-move-remaining-cck-testing-utilities-out-of-pytest-bdd-testi
**Areas discussed:** Destination in toolchain, Import path updates, Package cleanup

---

## Destination in toolchain

| Option | Description | Selected |
|--------|-------------|----------|
| `pytest_bdd_toolchain/testing/cck.py` | Mirrors the original location — clear migration intent, semantically correct | |
| `pytest_bdd_toolchain/cck.py` | Top-level, simplest path. But the package has no other top-level utility modules | |
| `pytest_bdd_toolchain/tool/cck.py` | Into the existing tool/ directory, which contains backend utilities like docker support | |
| `src/pytest_bdd_toolchain/case` | User-specified destination | ✓ |

**Follow-up: Where specifically under case/?**
| `case/contract/cck/cck.py` | Right next to the CCK tests that use it — tightest cohesion, imports become relative | ✓ |
| `case/cck.py` | At case/ level — shared across any CCK-related test directories, not just contract | |

**User's choice:** `src/pytest_bdd_toolchain/case/contract/cck/cck.py`
**Notes:** Co-locate the utility with its test consumers for maximum cohesion. The three files in that directory already import from it.

---

## Import path updates

| Option | Description | Selected |
|--------|-------------|----------|
| Direct updates only | Change all 4 imports to new paths. No shims — zero external consumers exist | ✓ |
| With compatibility shim | Update imports AND leave a forwarding stub in old location with deprecation warning | |
| You decide | Planner chooses the cleanest approach based on the consumer analysis | |

**User's choice:** Direct updates only
**Notes:** Three files use relative imports (`from .cck import`), one file (`step/steps_cck_allure.py`) uses full path change. No external consumers, no config references.

---

## Package cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Delete the directory entirely | Remove testing/__init__.py and the directory — no purpose remains | ✓ |
| Leave empty directory | Keep testing/ with its empty __init__.py for potential future use | |
| You decide | Planner determines based on project conventions around empty packages | |

**User's choice:** Delete the directory entirely
**Notes:** `src/pytest_bdd/testing/` has only `__init__.py` with `__all__ = []`. No parent `__init__.py` references it. No `pyproject.toml` config references it.

---

## the agent's Discretion

- Order of operations for the move (copy-then-delete vs. git mv)
- Whether `cck.py` needs any internal changes beyond the module move
- Verification strategy (run CCK contract tests, import checks, lint checks)

## Deferred Ideas

None — discussion stayed within phase scope.
