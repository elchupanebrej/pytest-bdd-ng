# Tasks: Parser Type Alignment

**Feature**: 021-parser-type-alignment
**Branch**: `021-parser-type-alignment`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Task Summary

All three user scenarios are served by the same code changes — this is a linear refactoring, not separable stories. Tasks are ordered by dependency.

---

## Phase 1: Setup (verify baseline)

- [x] T001 Run existing test suite to confirm baseline — `uv run python -m pytest tests/compatibility -q` (39 passed)
- [x] T002 Run mypy on current parser.py to capture existing type errors — clean baseline, no issues found

## Phase 2: Protocol update (foundational — must complete before Phase 3)

- [x] T003 Update `ParserProtocol.parse()` return type in `src/pytest_bdd/compatibility/parser.py` — already correct (already imports cucumber_messages.GherkinDocument)

## Phase 3: Parser type alignment (main refactoring)

- [x] T004 Replace `GherkinDocument` import in `src/pytest_bdd/parser.py` — removed compat import, added to cucumber_messages import block
- [x] T005 Update `BaseParser.normalize_gherkin_document_payload()` parameter type from `GherkinDocument` to `dict[str, Any]`
- [x] T006 Update `BaseParser.build_feature()` to return `cucumber_messages.GherkinDocument` without `cast()`; removed TODO comment
- [x] T007 Remove the intermediate `cast("GherkinDocument", ...)` calls — replaced with `cast("dict[str, Any]", ...)` to bridge upstream TypedDict → dict
- [x] T008 Verify `_set_feature_filename()` Protocol pattern continues to work unchanged

## Phase 4: Verify

- [x] T009 Run existing test suite — `uv run python -m pytest tests/compatibility -q` — 39 passed, no regressions
- [x] T010 Run mypy on changed files — `uv run python -m mypy src/pytest_bdd/parser.py src/pytest_bdd/compatibility/parser.py` — Success: no issues found
- [x] T011 Run ruff lint — ruff not in project venv; project ruff via pre-commit has pre-existing pyproject.toml parse error (unrelated to this change)
- [x] T012 Run pre-commit — `uvx pre-commit run --all-files` — all hooks pass except ruff-check/ruff-format (pre-existing TOML parse error)

## Dependencies

```
T001, T002 (baseline)
    ↓
T003 (protocol update)
    ↓
T004 → T005 → T006 → T007 → T008 (sequential within parser.py)
    ↓
T009, T010, T011, T012 (verification)
```

T001 and T002 can run in parallel. T003 is independent of T001/T002 in code but depends on understanding the target type. T004–T008 are sequential changes within the same file. T009–T012 can run in parallel.

## Implementation Strategy

**MVP**: This is already minimal scope — the entire feature is two files. Execute T001–T012 in order.

**Parallel opportunities**: T001 ∥ T002, T009 ∥ T010 ∥ T011 ∥ T012.

**Verification gate**: T009 must pass before claiming completion. T010 confirms no new mypy issues.
