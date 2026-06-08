---
created: 2026-06-11T13:38:58.412Z
title: Create custom pylint rule for noqa without reason
area: tooling
files:
  - src/pytest_bdd/_pylint/checkers/typing_rules.py:10
---

## Problem

The codebase enforces strict code quality gates, but currently there is no custom rule or check to prevent developers from using bare `# noqa` comments (which suppress all warnings on the line) or using `# noqa: CODE` without a following explanation. Suppressing linter warnings without an explanation or suppressing all warnings blindly makes codebase maintenance harder and can mask potential bugs.

## Solution

Implement a custom Pylint checker or rule (similar to `TypingRulesChecker` in `src/pytest_bdd/_pylint/checkers/typing_rules.py`) that scans codebase comments for `# noqa` violations:

1. Detect bare `# noqa` comments (e.g. comment matches `# noqa` without a colon/code like `# noqa: <CODE>`).
2. Detect `# noqa: CODE` comments that lack a reason/explanation (e.g., they do not have a subsequent comment explaining the rationale like `# noqa: BLE001  # explanation` or `# noqa: BLE001 explanation`).
3. Add unit tests verifying detections under `src/pytest_bdd_testing/cases/unit/test_pylint_checkers.py`.
4. If a new checker class/module is created, ensure it is configured in `pyproject.toml` and registered in `src/pytest_bdd/_pylint/__init__.py`.
