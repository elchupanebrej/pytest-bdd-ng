# ADR-006: Test Group Ordering

**Status:** Accepted

**Date:** 2026-06-08

**Deciders:** pytest-bdd-ng core team

## Context

CI pipelines need to run tests in predictable groups for parallelization and incremental validation. Without grouping, test execution order is non-deterministic across runs, making it difficult to implement fast-feedback CI stages (e.g., unit tests before integration tests) or parallelize test execution with xdist. Pytest itself does not enforce any specific ordering beyond file-system sorting.

## Decision

Test groups are configured through pytest ini-style options under `[tool.pytest.ini_options]`:
- `test_group_order` — ordered list of group names
- `test_group_default` — default group for unassigned tests
- `test_group_paths` — path-to-group mapping patterns

Shared test-group parsing, assignment, marker application, and xdist barrier logic lives in `src/pytest_bdd/util/test_group_ordering.py`. The conftest in `tests/` acts as a thin pytest adapter.

Groups are assigned via pytest markers. Filtering uses standard pytest marker expressions (`pytest -m <group>`). Non-group markers are not hardcoded into ignore lists; only configured group names participate in group resolution.

## Consequences

### Positive

- Predictable test execution ordering across CI stages
- Fast-feedback CI: unit tests can run before integration tests
- xdist parallelization benefits from ordered, grouped test execution
- Configuration-driven — adding new groups requires only config changes

### Negative

- Adds test configuration complexity (three additional pytest ini options)
- CI scripts must be aware of group names for stage separation
- xdist barrier sync adds overhead when running full-suite tests

### Neutral

- Group names are generic configuration values, not hardcoded project constants
- Path patterns use glob-style matching for flexible assignment
