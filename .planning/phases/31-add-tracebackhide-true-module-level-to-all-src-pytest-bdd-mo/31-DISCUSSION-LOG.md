# Phase 31: Add __tracebackhide__ = True module-level to all src/pytest_bdd/ modules - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-08
**Phase:** 31-add-tracebackhide-true-module-level-to-all-src-pytest-bdd-mo
**Areas discussed:** Module Scope, Declaration Placement, Verification Strategy, Automation Script

---

## Module Scope

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Include all modules and __init__.py files, except empty __init__.py files | Covers all modules with actual code, excluding docstring-only files | ✓ |
| Include all Python files under src/pytest_bdd/ without exceptions | Broadest scope, includes empty __init__.py files | |
| Exclude compatibility/ and testing/ directories | Only applies to core scenario/step execution runtime | |
| Exclude script/ directory | Excludes standalone CLI tools | |

**User's choice:** Include all modules and non-empty `__init__.py` files, except empty `__init__.py` files that only contain `__all__ = []` and no code.
**Notes:** Redundant function-level `__tracebackhide__` variables will be cleaned up. No `__tracebackhide__ = False` overrides will be added.

---

## Declaration Placement

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Below all module-level imports, before any classes, functions, or other constants | Standard Python module structure placement | ✓ |
| Right after from __future__ import annotations | Precedes all imports | |
| At the very end of the module file | Appended to the file | |

**User's choice:** Below all module-level imports, before any classes, functions, or other constants.
**Notes:** Standard spacing will be used: one blank line after imports, and two blank lines before any functions or classes.

---

## Verification Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Write an integration test using testdir | Asserts traceback hiding works on failure and is bypassed by --full-trace | ✓ |
| Verify only that the variable exists in globals | Checked via a unit test that imports each module | |
| Do both | Combines variable checks and integration tests | |

**User's choice:** Write an integration test using testdir that runs a failing step and asserts that no 'pytest_bdd' internal frames appear in the stdout traceback, but they DO appear when --full-trace is passed.
**Notes:** Run the full test suite first, identify any traceback-checking tests that fail, and adjust them to either expect hidden frames or run with --full-trace.

---

## Automation Script

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) A robust Python script using regex/string operations | Safe AST-compatible insert followed by ruff formatting | ✓ |
| A simple shell command/one-liner | Prepends via sed/awk | |
| Do it manually for key files | Edit them individually | |

**User's choice:** A robust Python script using regex/string operations to insert the declaration after imports, followed by ruff formatting to clean up any spacing issues.
**Notes:** The script will be stored in the local scratch directory under the active phase or conversation artifacts, executed, and not committed to the repository.

---

## the agent's Discretion

- The planner/executor decides the exact implementation details of the regex-based Python script.
- The planner decides the exact location and name of the integration test file.

## Deferred Ideas

None — discussion stayed within phase scope.
