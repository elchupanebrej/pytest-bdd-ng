# Data Model: Modernize `attrs` Interface — `014-modernize-attr-interface`

**Date**: 2026-03-17
**Branch**: `014-modernize-attr-interface`

---

## Overview

This document catalogues every class that is in scope for migration, grouped by source file.
For each class it records the **before** state (current decorator + field style) and the
**after** state (target modern-`attrs` decorator + field style). The "Entity" framing maps
to the spec's Key Entities section.

---

## Entity 1 — Legacy `attrs` Classes (`@attrs` / `attrib()` style)

These classes currently use the pre-20.1.0 `attr` import path and will be migrated to
`from attrs import define, field, frozen, Factory` (as appropriate).

### 1.1 `compatibility/parser.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| `GherkinParser` | `@attrs` + `attrib(default=None, kw_only=True)` | `@define` + `field(default=None, kw_only=True)` | Single optional field |

**Import change**: `from attr import attrib, attrs` → `from attrs import define, field`

---

### 1.2 `steps.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| `StepDefinitionManager.Context` | `@attrs` + 5× `attrib()` (mix of init/no-init) | `@define` + 5× `field(...)` | Contains `attrib(init=False)` attributes set in `__attrs_post_init__` — preserve hook |
| `StepDefinitionManager.Definition` | `@attrs(eq=False)` + 9× `attrib()` + 1× `Factory(dict)` | `@define(eq=False)` + 9× `field(...)` + `field(factory=dict)` | `eq=False` preserved; `Factory(dict)` → `factory=dict` |
| `StepDefinitionManager.Registry` | `@attrs` + 2× `attrib()` | `@define` + 2× `field(...)` | `attrib(default=Factory(set))` → `field(factory=set)` |
| (inner unnamed) | `@attrs` | `@define` | Check for any other `@attrs` in file |

**Import change**: `from attr import Factory, attrib, attrs` → `from attrs import Factory, define, field`
*(Note: `Factory` is also importable from `attrs` — verify and use `factory=` kwarg spelling instead where possible)*

---

### 1.3 `scenario_locator.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| `ScenarioLocatorFilter` | `@attrs` + `attrib(default=None, kw_only=True)` | `@define` + `field(default=None, kw_only=True)` | |
| `FeatureFileLocator` | `@attrs` + 6× `attrib()` (bare) | `@define` + 6× `field()` | Bare `attrib()` → `field()` with no default means required positional |
| `FeaturePathLocator` | `@attrs` + 7× `attrib(...)` + `Factory(list)` | `@define` + 7× `field(...)` + `factory=list` | `Parser` field has complex default — preserve exactly |

**Import change**: `from attr import Factory, attrib, attrs` → `from attrs import define, field`

---

### 1.4 `tag_expression.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| `TagExpressionWrapper` | `@attrs` + `attrib()` | `@define` + `field()` | |
| `AllTagsWrapper` | `@attrs` (no fields per import grep) | `@define` | Verify no attrib fields |
| `NoneTagWrapper` | `@attrs` | `@define` | |
| `TagExpressionParser` | `@attrs` + `attrib()` | `@define` + `field()` | |

**Import change**: `from attr import attrib, attrs` → `from attrs import define, field`

---

### 1.5 `plugin/scenario_reporter/report.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| `ScenarioReport` | `@attrs` + 4× `attrib()` + `Factory(list)` | `@define` + 4× `field(...)` | `attrib(default=Factory(list))` → `field(factory=list)` |

**Import change**: `from attr import Factory, attrib, attrs` → `from attrs import define, field`

---

### 1.6 `plugin/struct_bdd/model_builder.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| `StepContext` (line 29) | `@attrs` + `attrib()` | `@define` + `field()` | |
| `StepContextExtended` (line 37) | `@attrs` + `attrib()` | `@define` + `field()` | |
| `StepContextNested` (line 62) | `@attrs` + `attrib()` | `@define` + `field()` | |
| `JoinTableContext` (line 195) | `@attrs` + `attrib()` | `@define` + `field()` | |

**Import change**: `from attr import attrib, attrs` → `from attrs import define, field`

---

### 1.7 `plugin/struct_bdd/model.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| `StepPrototype.Ref` (inner, line 303) | `@attrs` + 4× `attrib()` (bare) | `@define` + 4× `field()` | |

**Import change**: `from attr import attrib, attrs` → `from attrs import define, field`

---

### 1.8 `plugin/struct_bdd/parser.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| `StructBDDParser` (line 16) | `@attrs` + 2× `attrib(kw_only=True)` | `@define` + 2× `field(kw_only=True)` | |

**Import change**: `from attr import attrib, attrs` → `from attrs import define, field`

---

### 1.9 `parser.py`

| Class | Before | After | Notes |
|-------|--------|-------|-------|
| (line 116) | `@attrs` | `@define` | Verify attrib usage |
| (line 159) | `@attrs` | `@define` | Verify attrib usage |

**Import change**: `from attr import attrs` → `from attrs import define`

---

## Entity 2 — `@dataclass` Classes

These classes use `dataclasses.dataclass` and will be migrated to `attrs` equivalents.
`field(default_factory=...)` (dataclass) → `field(factory=...)` (attrs).

### Mapping Table

| `@dataclass` variant | `attrs` equivalent |
|----------------------|--------------------|
| `@dataclass` (mutable, no slots) | `@define(slots=False)` |
| `@dataclass(slots=True)` | `@define` (slots=True by default in attrs 22.2.0+) |
| `@dataclass(frozen=True)` | `@frozen` |
| `@dataclass(frozen=True, slots=True)` | `@frozen` (slots=True implied) |
| `@dataclass(kw_only=True)` | `@define(kw_only=True)` |

### 2.1 `model/` directory

| File | Classes | Target decorator |
|------|---------|-----------------|
| `message_outcome_mapping.py` | 3 × frozen+slots | `@frozen` |
| `message_registry.py` | 2 × slots only | `@define` |
| `heading_validation.py` | 5 × frozen (no slots) | `@frozen` |
| `execution_message_adapter.py` | 1 × frozen+slots | `@frozen` |
| `scenario_run.py` | 11 × slots only | `@define` |
| `message_extension.py` | 1 × plain, 2 × frozen+slots | `@define(slots=False)`, `@frozen` |
| `message_governance_checklist.py` | 2 × frozen+slots | `@frozen` |
| `message_capability_inventory.py` | 3 × frozen+slots | `@frozen` |
| `message_capability.py` | 1 × frozen+slots | `@frozen` |
| `message_status_governance.py` | 4 × frozen+slots | `@frozen` |
| `message_consolidation.py` | 3 × frozen+slots, 1 × slots | `@frozen` / `@define` |
| `message_baseline_diff.py` | 3 × frozen+slots | `@frozen` |
| `message_validation.py` | 3 × frozen+slots | `@frozen` |
| `coverage/tracker.py` | 1 × plain | `@define(slots=False)` |
| `coverage/inventory.py` | 2 × slots | `@define` |

### 2.2 Other source files

| File | Classes | Target decorator |
|------|---------|-----------------|
| `compatibility/matrix.py` | 2 × frozen (no slots) | `@frozen` |
| `feature_locator.py` | 1 × plain | `@define(slots=False)` |
| `plugin/scenario_test_collector/plugin.py` | 1 × `kw_only=True` | `@define(kw_only=True)` |
| `script/bdd_tree_to_rst.py` | 2 × frozen (no slots) | `@frozen` |

---

## Entity 3 — `__init__`-based Data-Model Classes In Scope

| File | Class | Target | Notes |
|------|-------|--------|-------|
| `plugin/scenario_reporter/report.py` | `StepReport` | `@define` | `__init__(step)` sets `self.step` + mutable list state; replace with `field()` |
| `plugin/gherkin_message_reporter/service_base.py` | `ReporterServiceBase` | `@define` + `slots=False` | `__init__(reporter)` sets `self.reporter`; service base class — use `slots=False` to allow subclass `ClassVar` |

---

## Entity 4 — Out-of-Scope Classes (Documentation Only)

These classes have `__init__` but are **not** data-model classes and are exempt:

| File | Reason |
|------|--------|
| `parsers.py` — all `StepParser` subclasses | Behavioural strategy classes with `singledispatchmethod` `__init__`; not data holders |
| `types/exception.py` | Exception subclasses |
| `plugin/gherkin_message_reporter/*_runtime.py` service classes | Lifecycle/service objects with injected dependencies |
| `plugin/allure_logger/plugin.py` | Plugin service classes |
| `plugin/gherkin_terminal_reporter/plugin.py` | Reporter service |
| `plugin/cucumber_*/plugin.py` + similar | Plugin classes |
| `util/toolz_extra.py` | Utility subclass of dict |

---

## Entity 5 — `attr.asdict` Usage

| File | Current import | Target import |
|------|---------------|--------------|
| `plugin/allure_logger/plugin.py` | `from attr import asdict` | `from attrs import asdict` |

---

## Validation Rules (enforced post-migration)

- No file in `src/` imports from `dataclasses` module (except explicit exemptions, none expected).
- No file in `src/` uses `from attr import attrib, attrs` or `attr.ib` or `attrib()`.
- `@attrs`, `@attr.s`, `@attr.attrs` decorators must not exist in `src/`.
- `@dataclass` decorator must not exist in `src/` (files migrated).
- `__post_init__` renamed to `__attrs_post_init__` where applicable.
- All `field(default_factory=...)` (dataclass) converted to `field(factory=...)` (attrs).
- All tests pass — zero regressions.
