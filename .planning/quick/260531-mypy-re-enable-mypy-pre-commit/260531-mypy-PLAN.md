---
quick_id: 260531-mypy
status: planned
created: 2026-05-31
---

# Quick Task 260531-mypy: Re-enable mypy in pre-commit hook and fix all type errors

## Tasks

| Task | Files | Action | Verify |
|------|-------|--------|--------|
| 1 | `.pre-commit-config.yaml` | Re-enable mypy as a local pre-commit hook using `uv run`. | Check that `pre-commit run mypy` runs. |
| 2 | `src/` and `tests/` files | Fix all type check errors reported by mypy. | Run `uv run mypy --config-file pyproject.toml src tests` and verify it succeeds with 0 errors. |
| 3 | `.planning/quick/260531-mypy-re-enable-mypy-pre-commit/260531-mypy-SUMMARY.md`, `.planning/STATE.md` | Summarize fixes and update state. | Clean git status. |

## Must-Haves
- `mypy` pre-commit hook configured via `uv run` to avoid tox's environment creation overhead.
- All type check issues in both `src/` and `tests/` resolved.
