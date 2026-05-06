# Research: Test Group Ordering

**Feature**: 020-test-group-ordering  
**Date**: 2026-05-05  
**Status**: Complete

## Decision 1: Third-Party Ordering Plugin

**Decision**: Use `pytest-order` as the baseline ordering engine.

**Rationale**:
- It is a maintained pytest ordering plugin compatible with modern pytest versions.
- It supports integer `@pytest.mark.order(N)` ordinals, which map cleanly from configured group order.
- `--order-scope=session` enforces ordering across the full collection, not only within modules or classes.
- Delegating item reordering to this plugin satisfies FR-012. Project code only translates group assignments into plugin markers.

**Alternatives considered**:
- `pytest-ordering`: deprecated and not suitable for a new project dependency.
- `pytest-dependency`: dependency graph semantics do not match ordered cost tiers.
- Custom sort in `pytest_collection_modifyitems`: rejected because project hooks must not sort or reorder items directly.

---

## Decision 2: Runtime Group Barriers Under xdist

**Decision**: xdist compatibility means runtime barriers, not only deterministic collection order. No test from a later group may start until all tests in earlier groups have finished.

**Rationale**:
- The specification requires zero later-group starts before earlier-group completion in local, CI, and xdist runs.
- `pytest --collect-only -n auto` is insufficient evidence because it does not exercise worker scheduling.
- Implementation must validate observable start/end events from a small xdist suite. If `pytest-order` alone cannot guarantee barriers across workers, implementation must add or select a pytest-compatible barrier approach without moving direct sort logic into project hooks.

**Alternatives considered**:
- Collection-order-only xdist validation: rejected as too weak.
- Declaring xdist out of scope: rejected by clarified FR-009.
- Disabling all xdist parallelism globally: rejected unless no narrower group-barrier approach works.

**Implementation validation**:
- `uv run --extra full python -m pytest tests/unit/test_group_ordering.py -q -s` passed with 19 focused tests.
- `uv run --extra full python -m pytest -n auto tests/unit/test_group_ordering.py -q -s` passed with 18 xdist-distributed focused tests before the US3 marker-filter test was added.
- The xdist acceptance test records monotonic start/finish timestamps and verified that later-group starts occur only after earlier-group finishes.

---

## Decision 3: Source Utility Plus Pytest Adapter

**Decision**: Put reusable group configuration and resolution code in `src/pytest_bdd/util/test_group_ordering.py`; keep `tests/conftest.py` as a thin adapter.

**Rationale**:
- Utility code should not be hidden near tests when it implements reusable parsing, validation, and resolution behaviour.
- Source placement puts the utility under normal `ruff`, `mypy`, packaging, and import discipline.
- A thin adapter makes the pytest boundary explicit: register ini options, read config, resolve items, apply `pytest.mark.order(N)`, and register configured markers.
- This split prevents `tests/conftest.py` from becoming a project-specific utility library.

**Rejected alternative**:
- `tests/_group_ordering.py`: too close to tests and bypasses source quality gates for a reusable mechanism.

---

## Decision 4: Configuration Schema Location

**Decision**: Store group configuration only in pytest ini-style options under `[tool.pytest.ini_options]` in `pyproject.toml` or equivalent keys in `pytest.ini`.

**Rationale**:
- The clarified spec explicitly rejects separate tool-specific TOML tables.
- Custom pytest ini options can be registered with `parser.addini(...)` and read with `config.getini(...)`.
- This keeps all group ordering configuration in standard pytest configuration while still supporting structured values via line-list options.

**Schema shape**:

```toml
[tool.pytest.ini_options]
markers = [
    "instant: smallest in-process tests",
    "fast: normal fast tests",
    "medium: moderate integration tests",
    "slow: expensive local tests",
    "external: tests requiring external services",
    "order: execution ordering marker from pytest-order",
]
addopts = "--order-scope=session"
test_group_order = ["instant", "fast", "medium", "slow", "external"]
test_group_default = "fast"
test_group_paths = [
    "tests/unit/** = instant",
    "tests/e2e/** = external",
]
```

**Alternatives considered**:
- `[tool.pytest-bdd-ng.test-groups]`: rejected by clarification; would be a separate tool-specific TOML table.
- Separate `pytest-groups.toml`: rejected because it introduces a new config file type.
- Encoding everything in marker descriptions: rejected because marker descriptions are not a stable machine-readable config channel.

---

## Decision 5: Generic Five-Group Initial Example

**Decision**: Use `instant`, `fast`, `medium`, `slow`, and `external` as the initial project example groups.

**Rationale**:
- These names describe testing cost tiers generically and are not tied to one implementation detail.
- The schema still supports any number of user-defined groups and any valid group names.
- The ordered list itself is the source of truth for execution priority; names do not carry hidden behaviour.

**Implementation constraint**:
- The utility must never hardcode these names. Tests must include custom group names to prove the resolver is generic.

---

## Decision 6: Existing Test Tree Policy

**Decision**: Do not move or rename existing test files or directories. Express classification through pytest ini path mappings, existing directory naming matches when applicable, and explicit pytest group markers where required.

**Rationale**:
- The feature is group ordering, not test tree migration.
- Moving tests would mix behaviour changes with repository cleanup and make regressions harder to isolate.
- Config path mappings can classify the current mixed tree without disrupting history or developer workflows.

**Initial example mapping to audit during implementation**:

| Group | Example paths |
|-------|---------------|
| `instant` | `tests/unit/**`, `tests/model/**` |
| `fast` | `tests/args/**`, `tests/hook/**`, `tests/steps/**` |
| `medium` | `tests/feature/**`, `tests/gherkin_integration/**`, `tests/library/**`, `tests/struct_bdd/**` |
| `slow` | `tests/allure_/**`, `tests/compatibility/**`, `tests/contract/**`, `tests/doc/**`, `tests/generation/**`, `tests/messages/**`, `tests/messages_coverage/**`, `tests/scripts/**` |
| `external` | `tests/e2e/**` |

This mapping is an initial configuration target. Implementation tasks must audit and adjust it based on actual test behaviour, without moving files.

---

## Decision 7: Marker Participation Rules

**Decision**: Only names declared in `GroupConfig.groups` are group signals. All other pytest markers are ignored by the grouping resolver.

**Rationale**:
- This removes the need for hardcoded ignore lists such as `skip`, `xfail`, `parametrize`, or project-specific marks.
- Ordinary pytest marks remain available for pytest semantics and do not affect group assignment.
- Unknown markers are outside group resolution unless they are declared as groups in configuration.

**Validation boundary**:
- Validate group configuration and group-name collisions with pytest built-in markers.
- Do not warn because a test has a non-group marker; it is not group input.

---

## Decision 8: Resolution Cascade

**Decision**: Resolve each item using this priority cascade, lowest to highest:

| Priority | Mechanism | Notes |
|----------|-----------|-------|
| 1 | Directory naming convention | An exact path segment matching a configured group name supplies the base group. |
| 2 | Configured path mapping | Matching pytest ini path mappings override naming convention. |
| 3 | Directory-level pytest markers | Group markers inherited from `conftest.py` override path assignment. |
| 4 | Test-file or function pytest markers | Most specific configured group marker wins. |

At the same cascade level, multiple configured group markers resolve to the latest group in configured order. Duplicate configured group names are warned about and normalized before resolution, so exact directory matching cannot be ambiguous.

---

## Decision 9: Fixture Skip and Overhead Validation

**Decision**: Validate fixture-driven skips with an acceptance fixture that calls `pytest.skip()`, and measure overhead as collection-phase wall-clock delta for `pytest --collect-only` with grouping enabled versus disabled.

**Rationale**:
- Fixture skips are the specified mechanism for unavailable external resources; testing this directly prevents accidental group-level prerequisite logic.
- Collection-phase overhead isolates the grouping resolver and adapter better than full-suite runtime, which is noisy due to test execution cost.

**Alternatives considered**:
- Full-suite runtime delta: rejected as too noisy.
- Per-item microbenchmark only: useful as a diagnostic but insufficient as the success criterion measurement.

**Measured validation notes**:
- Full-suite collection with grouping enabled and full optional test extras: `uv run --extra full python -m pytest --collect-only -q -s` collected 768 tests in 19.53 seconds during initial validation, then 773 tests after adding focused acceptance coverage.
- Collection timing with grouping enabled was 25.01 seconds. A minimal single-group override was 24.33 seconds, for an observed grouping overhead of 0.68 seconds in this local environment.
- Per-group collect-only validation with `-s` selected 25 `instant`, 204 `fast`, 115 `medium`, 265 `slow`, and 164 `external` tests from 773 collected items.
- The exact collect-only commands without `-s` currently hit an unrelated pytest capture teardown `FileNotFoundError` in this Python 3.14 local environment; `-s` is required for reliable local validation until that capture issue is fixed.
