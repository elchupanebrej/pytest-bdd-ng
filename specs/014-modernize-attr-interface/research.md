# Research: Modernize `attrs` Interface — `014-modernize-attr-interface`

**Date**: 2026-03-17
**Branch**: `014-modernize-attr-interface`

---

## 1. Current `attrs` Version

| Decision | attrs 25.4.0 is the installed runtime version |
|----------|-----------------------------------------------|
| Rationale | Confirmed via `conda run -n pytest-bdd-ng-py314 python -c "import attr; print(attr.__version__)"` → `25.4.0`. The modern `@define` / `field()` / `@frozen` API is available since attrs 20.1.0, so the entire modern API surface is available. |
| Alternatives considered | N/A — version confirmed from active environment |

---

## 2. Inventory of Classes to Migrate

### 2a. Legacy `attr.s` / `attrib()` patterns (highest priority)

These files `from attr import attrib, attrs` and use `@attrs` class decorator + `attrib()` field declarations — the pre-20.1.0 style:

| File | Classes / decorators |
|------|----------------------|
| `src/pytest_bdd/compatibility/parser.py` | 1 class with `@attrs` + `attrib()` |
| `src/pytest_bdd/steps.py` | 4 inner classes with `@attrs` / `@attrs(eq=False)` + `attrib()` |
| `src/pytest_bdd/scenario_locator.py` | 3 classes with `@attrs` + `attrib()` / `Factory` |
| `src/pytest_bdd/tag_expression.py` | 4 classes with `@attrs` + `attrib()` |
| `src/pytest_bdd/plugin/scenario_reporter/report.py` | 1 class with `@attrs` + `attrib()` / `Factory` |
| `src/pytest_bdd/plugin/struct_bdd/model_builder.py` | 4 classes with `@attrs` + `attrib()` |
| `src/pytest_bdd/plugin/struct_bdd/model.py` | 1 inner class with `@attrs` + `attrib()` |
| `src/pytest_bdd/plugin/struct_bdd/parser.py` | 1 class with `@attrs` + `attrib()` |
| `src/pytest_bdd/parser.py` | 2 classes with `@attrs` (import: `from attr import attrs`) |

**Total: ~21 class definitions** across 9 files.

### 2b. `@dataclass` patterns (medium priority)

| File | Classes | Notes |
|------|---------|-------|
| `src/pytest_bdd/model/message_outcome_mapping.py` | 3 × `@dataclass(frozen=True, slots=True)` | Pure data, frozen+slots → `@frozen` with `slots=True` implied |
| `src/pytest_bdd/model/message_registry.py` | 2 × `@dataclass(slots=True)` | Mutable, slotted → `@define(slots=True)` |
| `src/pytest_bdd/model/heading_validation.py` | 5 × `@dataclass(frozen=True)` | → `@frozen` |
| `src/pytest_bdd/model/execution_message_adapter.py` | 1 × `@dataclass(frozen=True, slots=True)` | → `@frozen` |
| `src/pytest_bdd/model/scenario_run.py` | 11 × `@dataclass(slots=True)` | Mutable, slotted → `@define(slots=True)` |
| `src/pytest_bdd/model/message_extension.py` | 3 × `@dataclass` / `(frozen=True, slots=True)` | Mixed → `@define` / `@frozen` |
| `src/pytest_bdd/model/message_governance_checklist.py` | 2 × `@dataclass(frozen=True, slots=True)` | → `@frozen` |
| `src/pytest_bdd/model/message_capability_inventory.py` | 3 × `@dataclass(frozen=True, slots=True)` | → `@frozen` |
| `src/pytest_bdd/model/message_capability.py` | 1 × `@dataclass(frozen=True, slots=True)` | → `@frozen` |
| `src/pytest_bdd/model/message_status_governance.py` | 4 × `@dataclass(frozen=True, slots=True)` | → `@frozen` |
| `src/pytest_bdd/model/message_consolidation.py` | 4 × `@dataclass` variants | Mixed → `@define`/`@frozen` |
| `src/pytest_bdd/model/coverage/tracker.py` | 1 × `@dataclass` | Mutable → `@define` |
| `src/pytest_bdd/model/coverage/inventory.py` | 2 × `@dataclass(slots=True)` | → `@define(slots=True)` |
| `src/pytest_bdd/model/message_baseline_diff.py` | 3 × `@dataclass(frozen=True, slots=True)` | → `@frozen` |
| `src/pytest_bdd/model/message_validation.py` | 3 × `@dataclass(frozen=True, slots=True)` | → `@frozen` |
| `src/pytest_bdd/compatibility/matrix.py` | 2 × `@dataclass(frozen=True)` | → `@frozen` |
| `src/pytest_bdd/feature_locator.py` | 1 × `@dataclass` | → `@define` |
| `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` | 1 × `@dataclass(kw_only=True)` | → `@define(kw_only=True)` |
| `src/pytest_bdd/script/bdd_tree_to_rst.py` | 2 × `@dataclass(frozen=True)` | Script file — still in scope |

**Total: ~51 class definitions** across 19 files.

### 2c. `__init__`-based data-model classes in scope

These hand-written `__init__` constructors on classes that hold structured data:

| File | Class | Notes |
|------|-------|-------|
| `src/pytest_bdd/plugin/scenario_reporter/report.py` | `StepReport.__init__(step)` | Initialises mutable state → `@define` |
| `src/pytest_bdd/plugin/gherkin_message_reporter/service_base.py` | `ReporterServiceBase.__init__(reporter)` | Service base; stores `self.reporter` — candidate for `@define` |

**Out of scope** (`__init__` on exception/behaviour classes, not data models):
- `src/pytest_bdd/types/exception.py` — Exception subclasses: exempt
- `src/pytest_bdd/parsers.py` — `StepParser` and subclasses: these use `singledispatchmethod`-based `__init__` overloading — **architecture is not dataclass-like; exempt from migration** (they are behavioural parser strategy classes, not data holders)
- `src/pytest_bdd/plugin/gherkin_message_reporter/*_runtime.py` service classes — service/lifecycle objects with complex constructor injection; **service classes, not data-model classes; exempt**
- `src/pytest_bdd/util/toolz_extra.py` — `DefaultDict` subclass: exempt (utility subclass)

### 2d. Already-modern `attrs` usage (no change required)

Files already using `@define`, `@frozen`, `field()` correctly:

| File | Current style | Status |
|------|--------------|--------|
| `model/message_transport.py` | `@frozen` / `@define` / `field()` | ✅ already modern |
| `model/cucumber_formatter_adapter.py` | `@define` / `field()` | ✅ already modern |
| `plugin/gherkin_message_reporter/standalone_renderer.py` | `@frozen` | ✅ already modern |
| `plugin/gherkin_message_reporter/runtime_assembly.py` | `@frozen` | ✅ already modern |
| `plugin/gherkin_message_reporter/session.py` | `@frozen` | ✅ already modern |
| `plugin/gherkin_message_reporter/entrypoint.py` | `@frozen` | ✅ already modern |
| `plugin/gherkin_message_reporter/plugin.py` | `@define` / `field()` | ✅ already modern |
| `plugin/gherkin_message_reporter/runtime_support.py` | `@frozen` | ✅ already modern |
| `plugin/cucumber_formatter_support/registry.py` | `@frozen` | ✅ already modern |
| `plugin/cucumber_formatter_support/base.py` | `@frozen` | ✅ already modern |

---

## 3. Migration Mapping: Old → New

| Old pattern | New equivalent | Notes |
|-------------|----------------|-------|
| `from attr import attrib, attrs` + `@attrs` + `attrib()` | `from attrs import define, field` + `@define` + `field()` | Primary legacy form |
| `@attrs(eq=False)` | `@define(eq=False)` | Parameter name preserved |
| `attrib(default=None)` | `field(default=None)` | Direct substitution |
| `attrib(init=False)` | `field(init=False)` | Direct substitution |
| `attrib(default=Factory(dict))` | `field(factory=dict)` | `Factory` → `factory=` kwarg |
| `attrib(kw_only=True)` | `field(kw_only=True)` | Preserved |
| `from dataclasses import dataclass; @dataclass(frozen=True, slots=True)` | `from attrs import frozen; @frozen` | `frozen` implies `slots=True` by default in attrs ≥ 22.2.0 |
| `@dataclass(frozen=True)` | `@frozen` | Straightforward |
| `@dataclass(slots=True)` (mutable) | `@define(slots=True)` | `@define` is mutable, slotted by default in attrs ≥ 22.2.0 — verify slot param |
| `@dataclass` (mutable, no slots) | `@define(slots=False)` or `@attrs.define` | Need to decide whether to enable slots |
| `@dataclass(kw_only=True)` | `@define(kw_only=True)` | Preserved |
| `field(default_factory=list)` (dataclass) | `field(factory=list)` (attrs) | `default_factory` → `factory` |
| `dataclasses.field(compare=False)` | `attrs.field(eq=False)` | Compare → eq |

---

## 4. Semantic Equivalence Decisions

### `slots=True` policy

- `@frozen` in attrs 22.2.0+ enables `slots=True` by default.
- `@define` in attrs 22.2.0+ enables `slots=True` by default.
- **Decision**: For classes migrated from `@dataclass(slots=True)` → `@define` (default slots).
  For classes migrated from `@dataclass` (no slots) → `@define(slots=False)` to preserve existing
  memory/inheritance semantics until deliberately opted in.

### `frozen=True` policy

- **Decision**: `@dataclass(frozen=True)` → `@frozen`. `@dataclass(frozen=True, slots=True)` → `@frozen` (slots implied). This is fully equivalent.

### `eq=False` on `StepDefinitionManager.Definition`

- The single `@attrs(eq=False)` usage in `steps.py` → `@define(eq=False)`.

### `__attrs_post_init__` hook

- Any `__post_init__` (dataclass) present → rename to `__attrs_post_init__`.
- Inspect each migrated file before migration for presence of `__post_init__`.

### `allure_logger` usage of `attr.asdict`

- `from attr import asdict` → `from attrs import asdict`. Module is the same; function is available from the `attrs` package namespace.

### `steps.py` — `attrib(init=False)` with computed defaults

- Attributes declared `init=False` with no `default` are set in `__attrs_post_init__`. Confirm this pattern and preserve.

---

## 5. Compatibility and Regression Risk Assessment

| Class group | Risk | Reason |
|-------------|------|--------|
| `@attrs` + `attrib()` legacy classes | Medium | Constructor keyword arg names unchanged; validators and factories must be preserved |
| `@dataclass(frozen=True/slots=True)` in `model/` | Low | Pure data containers; public interface (attribute names) unchanged; `slots` semantics equivalent |
| `scenario_run.py` dataclasses | Medium | Large file (770+ lines), many dataclasses including mutable ones with `field(default_factory=...)` expressions |
| `parsers.py` classes | **OUT OF SCOPE** | Singledispatch __init__ overloading — not data-model pattern |
| Exception classes | **OUT OF SCOPE** | Exception subclasses |
| Service `__init__` classes | **OUT OF SCOPE** | Lifecycle/behaviour classes |

---

## 6. Test Strategy

- Run full test suite (`pytest tests/ -q`) after each file migration batch.
- Use `tox -e py314` (or equivalent) to run against the canonical Python version.
- Check `ruff check src/` + `pre-commit run --all-files` after each batch.
- Specifically verify: `tests/` contains no failures for `steps`, `scenario_locator`, `tag_expression`, `parser` modules (highest-change-surface files).

---

## 7. Outstanding Questions — All Resolved

| Question | Resolution |
|----------|-----------|
| Is `attrs >= 20.1.0` available? | ✅ Yes — 25.4.0 is installed |
| Does `@frozen` imply `slots=True`? | ✅ Yes, since attrs 22.2.0 |
| Does `@define` imply `slots=True`? | ✅ Yes, since attrs 22.2.0 — use `slots=False` when converting plain `@dataclass` (no-slot) to avoid inadvertent breakage |
| Are `parsers.py` StepParser classes in scope? | ✅ No — behavioural classes, not data models |
| Is `attr.asdict` still available from `attrs`? | ✅ Yes — available as `attrs.asdict` |
