# ADR-007: No Return None Policy (Quality Gate BLQ901)

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

Phase 2 quality gate analysis found 96 instances of `return None` antipattern in non-hook code across the pytest-bdd-ng codebase. Returning `None` silently propagates through call chains, masking errors and making debugging significantly harder. When a function returns `None`, callers must remember to check for it — and failures to do so result in `AttributeError: 'NoneType' object has no attribute '...'` deep in execution, far from the actual source of the problem.

The project's AGENTS.md explicitly states: "Outside pytest hook implementations, returning `None` is an antipattern; use explicit values or deterministic exceptions instead."

Many of these `return None` instances serve as sentinel values for "not found," "not applicable," or "error occurred." Without explicit handling, these silent failures propagate through the step matching, scenario execution, and reporting pipelines.

## Decision

**Enforce a zero `return None` policy in non-hook production code via a custom ruff rule (BLQ901).** Functions that would previously return `None` must instead:

1. Use `Maybe`/`Result` types from the `returns` library for optional/fallible values
2. Raise domain-specific exceptions for error conditions
3. Return explicit sentinel objects with clear semantics

The custom Pylint checker (`src/pytest_bdd/_pylint/checkers/quality_gates.py`, rule BLQ901) detects bare `return None` statements in non-hook code and reports them as errors. Pytest hook implementations (which legitimately return `None` per the pytest hook specification) are excluded from this check.

## Consequences

### Positive
- Eliminates silent `None` propagation failures — errors surface at the point of origin
- Improves type safety — callers can rely on return values being meaningful
- Makes failure modes explicit — reading code reveals what can go wrong
- Enables static analysis — mypy can check `Maybe`/`Result` types more precisely than `Optional[None]`
- Consistent with project's AGENTS.md conventions

### Negative
- Requires explicit sentinel handling at every call site — more boilerplate than `if result is None`
- `Maybe`/`Result` types add a conceptual dependency (the `returns` library)
- Migration of 96 existing antipatterns requires careful per-site analysis

### Neutral
- The BLQ901 ruff rule runs as a pre-commit hook and CI gate
- Pytest hook implementations are explicitly excluded from the check
- Migration is phased — Phase 2 handled initial elimination, ongoing enforcement via pre-commit
