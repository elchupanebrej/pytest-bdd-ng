# Phase 26: Test CLI scripts in a separate Cucumber Development flow - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-20
**Phase:** 26-Test CLI scripts in a separate Cucumber Development flow
**Areas discussed:** CLI Invocation Strategy

---

## CLI Invocation Strategy

### Question 1: How should the development BDD scenarios invoke the scripts/CLIs under test?

| Option | Description | Selected |
|--------|-------------|----------|
| Option 1 | (Recommended) Use python interpreter directly (e.g., `python scripts/arch.py` or `python src/pytest_bdd/script/validate_feature_headings.py`). This is more robust against local env path differences. | ✓ |
| Option 2 | Use registered console script entrypoints (e.g., `compatibility_matrix`, `sync_messages_contract_schemas`). This directly tests that our entrypoints declared in `pyproject.toml` are correctly installed and functional. | |
| Option 3 | Agent discretion: Use whichever is cleaner for each specific script. | |

**User's choice:** Option 1 ("For entrypoint scripts -1, for other -2")
**Notes:** The user preferred using the Python interpreter directly for entrypoint scripts.

---

### Question 2: How should we locate and execute non-entrypoint scripts (like `scripts/arch.py`)?

| Option | Description | Selected |
|--------|-------------|----------|
| Option 1 | (Recommended) Use relative path from repository root (e.g., `python scripts/arch.py`), with the step runner resolving or executing with the repository root as current working directory or PYTHONPATH. | ✓ |
| Option 2 | Copy/mock the script into the temporary test directory before execution so it runs in complete isolation. | |
| Option 3 | Resolve the absolute path of the script dynamically in the step definition using the repository root. | |

**User's choice:** Option 1
**Notes:** Standardizing on executing scripts relative to the repository root.

---

### Question 3: How should BDD scenarios assert standard output and error messages?

| Option | Description | Selected |
|--------|-------------|----------|
| Option 1 | (Recommended) Substring/regex matching (e.g., `the renderer terminal output includes:` with tabular lines). This is robust against output format changes. | ✓ |
| Option 2 | Exact stdout/stderr matching (highly strict but fragile to minor changes in formatting or version output). | |
| Option 3 | Ignore stdout/stderr checking in scenarios, verifying only the exit code. | |

**User's choice:** Option 1
**Notes:** Opted for flexible substring/regex output assertions to avoid test fragility.

---

### Question 4: How should shell script execution be handled cross-platform?

| Option | Description | Selected |
|--------|-------------|----------|
| Option 1 | (Recommended) Run via shell interpreter (`bash` or `sh`), utilizing Git Bash/MSYS on Windows (as currently configured in `harness.py`). | |
| Option 2 | Convert shell scripts to python scripts so that execution is natively cross-platform without shell dependencies. | |
| Option 3 | Skip shell script BDD scenarios on Windows/non-POSIX platforms entirely. | |

**User's choice:** Free-text: "We must rely only on python scripts. If there are some shell scripts -report" (Report the presence of shell scripts as an architectural gap/risk instead of running them).
**Notes:** BDD E2E tests should only invoke Python scripts. Shell script execution will be omitted from E2E and documented as an architectural gap.

---

## the agent's Discretion
None.

## Deferred Ideas
None.
