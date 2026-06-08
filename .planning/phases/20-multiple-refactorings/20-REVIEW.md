---
phase: 20-multiple-refactorings
status: clean
reviewed: 2026-06-13
depth: standard
---

# Phase 20 Code Review

## Scope

Reviewed Plan 30 and Plan 31 changes:

- Pylint plugin registration and BLQ adapter checkers
- Pylint config, pre-commit, and Makefile integration
- Parser registry refactor
- Message stream validation cycle cleanup
- Message capability governance package lookup cleanup

## Findings

No open findings.

## Fixed During Review

- Restored existing `_pylint` checker registration while adding BLQ symbol adapters. The disconnected Plan 30 agent had replaced the entrypoint with adapter-only registration, which would have silently dropped existing checker classes.
- Added a docstring to moved `collect_observed_capability_ids`.
- Moved adapter-only `Callable` and `Iterable` imports under `TYPE_CHECKING`.

## Verification

- `uv run pytest -o addopts= src/pytest_bdd_testing/cases/unit/test_pylint_checkers.py` — passed, 9 tests.
- `uv run pytest -o addopts= src/pytest_bdd_testing/cases/unit/unit/parser` — passed, 67 tests.
- `uv run --python 3.14 pylint --load-plugins=pytest_bdd._pylint --disable=all --enable=cyclic-import,duplicate-code --reports=n --score=n src/pytest_bdd/message_stream_validation src/pytest_bdd/parsers src/pytest_bdd/script/message_capability_governance` — passed.

## Residual Risk

Full `custom-rules` still surfaces existing BLQ violations across the repository. That is tracked in Plan 30/31 summaries as gate debt, not as an open review bug in the new cyclic-import/duplicate-code implementation.
