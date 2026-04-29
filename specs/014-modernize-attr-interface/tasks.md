# Implementation Tasks: Modernize `attrs` Interface

**Feature Branch**: `014-modernize-attr-interface`
**Generated**: 2026-03-17

## Phase 1: Setup

*(No setup tasks needed; Python environment and `attrs` 25.4.0 are already present.)*

## Phase 2: Foundational

*(No foundational tasks needed; the migration can proceed file by file in parallel or sequentially.)*

## Phase 3: User Story 1 — Contributors work with a uniform, modern class definition style

**Story Goal**: Migrate all legacy `attr.s`/`attrib()`, `@dataclass`, and hand-written `__init__` usages on data models in `src/pytest_bdd/` to the modern `attrs` interface (`@define`, `@frozen`, `field()`).

**Independent Test**:
- `ruff check src/` gives zero errors related to syntax.
- `conda run -n pytest-bdd-ng-py314 python -m pytest tests/ -q` passes with zero regressions.

> Current workflow:
> - `uv run python -m pytest tests/ -q` passes with zero regressions.


**Implementation Tasks**:

### Legacy `attr.s` Migrations (Phase A)
- [x] T001 [P] [US1] Migrate legacy `@attrs`/`attrib()` to `@define`/`field()` in `src/pytest_bdd/compatibility/parser.py` and `src/pytest_bdd/parser.py`
- [x] T002 [P] [US1] Migrate legacy `@attrs`/`attrib()` to `@define`/`field()` in `src/pytest_bdd/steps.py` (update 4 classes: `Context`, `Definition`, `Registry`, inner unnamed class)
- [x] T003 [P] [US1] Migrate legacy `@attrs`/`attrib()` to `@define`/`field()` in `src/pytest_bdd/scenario_locator.py` and `src/pytest_bdd/tag_expression.py`
- [x] T004 [P] [US1] Migrate legacy `@attrs`/`attrib()` to `@define`/`field()` in `src/pytest_bdd/plugin/scenario_reporter/report.py` and `src/pytest_bdd/plugin/struct_bdd/` (`model_builder.py`, `model.py`, `parser.py`)

### `@dataclass` Migrations (Phase B)
- [x] T005 [P] [US1] Convert `@dataclass(frozen=True, slots=True)` to `@frozen` in `src/pytest_bdd/model/` (`message_outcome_mapping.py`, `execution_message_adapter.py`, `message_governance_checklist.py`, `message_capability_inventory.py`, `message_capability.py`, `message_status_governance.py`, `message_consolidation.py`, `message_baseline_diff.py`, `message_validation.py`)
- [x] T006 [P] [US1] Convert continuous `@dataclass(frozen=True)` to `@frozen` in `src/pytest_bdd/model/heading_validation.py`, `src/pytest_bdd/compatibility/matrix.py`, and `src/pytest_bdd/script/bdd_tree_to_rst.py`
- [x] T007 [P] [US1] Convert `@dataclass(slots=True)` to `@define(slots=True)` in `src/pytest_bdd/model/` (`message_registry.py`, `scenario_run.py`, `message_consolidation.py`, `coverage/inventory.py`)
- [x] T008 [P] [US1] Convert plain `@dataclass` to `@define(slots=False)` in `src/pytest_bdd/model/` (`message_extension.py`, `coverage/tracker.py`, `feature_locator.py`), and `@dataclass(kw_only=True)` to `@define(kw_only=True)` in `src/pytest_bdd/plugin/scenario_test_collector/plugin.py`

### `__init__`-based Data Models (Phase C)
- [x] T009 [P] [US1] Convert `__init__` to `@define` fields in `StepReport` within `src/pytest_bdd/plugin/scenario_reporter/report.py` and `ReporterServiceBase` within `src/pytest_bdd/plugin/gherkin_message_reporter/service_base.py`

## Phase 4: Polish & cross-cutting concerns

- [x] T010 Run exhaustive grep checks to confirm absolutely no instances of `from attr import attrib` or `@dataclass` remain in `src/` (excluding explicit test files or non-migratable exceptions).
- [x] T011 Run `conda run -n pytest-bdd-ng-py314 pre-commit run --all-files` and fix any formatting/import ordering issues introduced by the migration.

> Current workflow:
> T011 equivalent: run `uvx pre-commit run --all-files` and fix any formatting/import ordering issues introduced by the migration.


## Execution Strategy

**Implementation Strategy**:
The structural refactoring tasks (T001-T009) can be handled in any order, but doing them grouped by migration variant ensures fewer context switches. It is highly recommended to run the unit test suite (`conda run -n pytest-bdd-ng-py314 pytest tests/`) incrementally after every file changed to spot semantic shifts immediately.

> Current workflow:
> Run the unit test suite incrementally with `uv run pytest tests/` after every file change to spot semantic shifts immediately.


**Dependencies**:
- T010 and T011 block the completion of the branch and must follow T001-T009.

**Parallel Execution Map**:
- Thread A: Legacy attributes T001-T004
- Thread B: Dataclasses T005-T008
- Thread C: Explicit inits T009
