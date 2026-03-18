# Implementation Plan: Modernize `attrs` Interface

**Branch**: `014-modernize-attr-interface` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/014-modernize-attr-interface/spec.md`

---

## Summary

Migrate every data-model class in `src/pytest_bdd/` from the legacy `attr.s` / `attrib()` API
and from `dataclasses.dataclass` to the modern `attrs` declarative API (`@define`, `@frozen`,
`field()`). Service classes, exception subclasses, and behavioural parser classes are explicitly
out of scope. The migration is purely structural — no public attribute names or constructor
keyword arguments change. The full test suite must pass at every checkpoint.

---

## Technical Context

**Language/Version**: Python 3.10–3.14 (primary test target: 3.14 via `pytest-bdd-ng-py314` conda env)
**Primary Dependencies**: `attrs >= 25.4.0` (confirmed installed), `pytest >= 7`, `ruff`, `pre-commit`
**Storage**: N/A — no persistence layer changes
**Testing**: `pytest` via `conda run -n pytest-bdd-ng-py314 tox`, `ruff check`, `pre-commit run`
**Target Platform**: Pure Python library; runs on Linux, macOS, Windows
**Project Type**: Python library
**Performance Goals**: No performance regression; `slots=True` equivalence preserved for slotted dataclasses
**Constraints**: Zero public API breakage; all existing tests pass; pre-commit clean after every commit
**Scale/Scope**: ~72 class definitions across ~28 source files in `src/`

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Spec-Driven Delivery | ✅ PASS | `spec.md` exists and is complete; plan derived from it |
| II. Independent Story Increments | ✅ PASS | Three priority stories; P1 (migrate legacy) can ship independently of P2/P3 |
| III. Validation-First Changes | ✅ PASS | Test suite run mandated after every batch; ruff + pre-commit required before commit |
| IV. Deterministic Compatibility and Contracts | ✅ PASS | Public attribute names and constructor args explicitly preserved; validated by test suite |
| V. Task-Traceable Commits | ✅ PASS | Task IDs will be used in commit messages; tasks.md updated per completed task |
| `None` anti-pattern | ✅ N/A | Migration is structural; no return-value semantics changed |
| English documentation | ✅ PASS | All planning artifacts in English |
| ISO dates | ✅ PASS | All dates in `YYYY-MM-DD` format |

**Post-design re-check**: No violations found. Complexity tracking table is not required.

---

## Project Structure

### Documentation (this feature)

```text
specs/014-modernize-attr-interface/
├── plan.md              # This file
├── research.md          # Phase 0 — class inventory and migration mapping
├── data-model.md        # Phase 1 — per-class before/after entity catalogue
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code — Files in Scope

```text
src/pytest_bdd/
│
│  # Legacy attr.s / attrib() — Group A (9 files, ~21 classes)
├── compatibility/parser.py
├── steps.py
├── scenario_locator.py
├── tag_expression.py
├── parser.py
├── plugin/
│   ├── scenario_reporter/report.py
│   ├── struct_bdd/model_builder.py
│   ├── struct_bdd/model.py
│   └── struct_bdd/parser.py
│
│  # @dataclass — Group B (19 files, ~51 classes)
├── compatibility/matrix.py
├── feature_locator.py
├── model/
│   ├── message_outcome_mapping.py
│   ├── message_registry.py
│   ├── heading_validation.py
│   ├── execution_message_adapter.py
│   ├── scenario_run.py          ← largest (11 dataclasses)
│   ├── message_extension.py
│   ├── message_governance_checklist.py
│   ├── message_capability_inventory.py
│   ├── message_capability.py
│   ├── message_status_governance.py
│   ├── message_consolidation.py
│   ├── message_baseline_diff.py
│   ├── message_validation.py
│   └── coverage/
│       ├── tracker.py
│       └── inventory.py
├── plugin/
│   └── scenario_test_collector/plugin.py
└── script/
    └── bdd_tree_to_rst.py
```

**Structure Decision**: Single-project layout. Only `src/` is modified; `tests/` is untouched
unless test files directly construct or import migrated classes in incompatible ways (none
expected given the preserved public interface).

---

## Implementation Phases

### Phase A — Migrate Legacy `attr.s` / `attrib()` Classes (P1, highest risk)

**Files**: 9 files listed in Group A above
**Strategy**: File-by-file. After each file, run `ruff check src/` + full test suite.

#### Migration rules applied per file

1. Replace import: `from attr import [attrib, attrs, Factory]` → `from attrs import define, field`
2. Replace decorator: `@attrs` → `@define`; `@attrs(eq=False)` → `@define(eq=False)`
3. Replace fields: `attrib()` → `field()`; `attrib(default=None)` → `field(default=None)`;
   `attrib(init=False)` → `field(init=False)`; `attrib(default=Factory(x))` → `field(factory=x)`
4. Preserve `__attrs_post_init__` if already present; rename any `__init__` on these classes
   that performs post-init logic to `__attrs_post_init__` and add it below the field declarations.
5. Special case — `plugin/allure_logger/plugin.py`: `from attr import asdict` → `from attrs import asdict`

#### Acceptance gate

- `ruff check src/` → 0 errors
- `conda run -n pytest-bdd-ng-py314 python -m pytest tests/ -q` → 0 failures
- `grep -rn "from attr import attrib" src/` → 0 matches

---

### Phase B — Migrate `@dataclass` Classes (P1/P2, lower risk per class)

**Files**: 19 files listed in Group B above
**Strategy**: Batch by decorator variant to apply uniform transformation:

#### Batch B-1: `@dataclass(frozen=True, slots=True)` → `@frozen`

Applies to: `message_outcome_mapping`, `execution_message_adapter`, `message_governance_checklist`,
`message_capability_inventory`, `message_capability`, `message_status_governance`,
`message_consolidation` (frozen subset), `message_baseline_diff`, `message_validation`.

Steps:
1. Remove `from dataclasses import dataclass[, field]`
2. Add `from attrs import frozen[, field]`
3. Replace `@dataclass(frozen=True, slots=True)` with `@frozen`
4. Replace `dataclasses.field(default_factory=x)` with `attrs.field(factory=x)`
5. Replace `dataclasses.field(compare=False)` with `attrs.field(eq=False)`

#### Batch B-2: `@dataclass(frozen=True)` (no explicit slots) → `@frozen`

Applies to: `heading_validation`, `compatibility/matrix`, `script/bdd_tree_to_rst`.

Same steps as B-1. Note: `@frozen` in attrs 22.2.0+ enables slots by default;
if class is subclassed anywhere, verify with `slots=False` option if needed.

#### Batch B-3: `@dataclass(slots=True)` (mutable) → `@define`

Applies to: `message_registry`, `scenario_run` (11 classes), `message_consolidation` (slotted subset),
`coverage/inventory`.

Steps:
1. Remove `from dataclasses import dataclass[, field]`
2. Add `from attrs import define[, field]`
3. Replace `@dataclass(slots=True)` with `@define`
4. Replace `field(default_factory=x)` with `field(factory=x)`
5. Rename any `__post_init__` to `__attrs_post_init__`

#### Batch B-4: `@dataclass` plain (mutable, no slots) → `@define(slots=False)`

Applies to: `feature_locator`, `message_extension` (plain subset), `coverage/tracker`.

Same steps as B-3 but use `@define(slots=False)` to preserve no-slots semantics
(avoids breaking any subclassing or dynamic attribute assignment patterns).

#### Batch B-5: `@dataclass(kw_only=True)` → `@define(kw_only=True)`

Applies to: `plugin/scenario_test_collector/plugin.py`.

**Acceptance gate after each batch**:
- `ruff check src/` → 0 errors
- `conda run -n pytest-bdd-ng-py314 python -m pytest tests/ -q` → 0 failures

---

### Phase C — Migrate `__init__`-based Data-Model Classes (P1)

**Files**:
- `src/pytest_bdd/plugin/scenario_reporter/report.py` (`StepReport`)
- `src/pytest_bdd/plugin/gherkin_message_reporter/service_base.py` (`ReporterServiceBase`)

**Strategy**:
1. For `StepReport`: Replace `__init__(step)` body with `@define` fields; preserve mutable list state as `field(factory=list)`.
2. For `ReporterServiceBase`: Replace `__init__(reporter)` with `@define(slots=False)` to allow `ClassVar` attributes and inheritance from service subclasses.

**Acceptance gate**: Same as above.

---

### Phase D — Final Audit and Cleanup

1. Run exhaustive grep checks:
   ```
   grep -rn "@dataclass\|from dataclasses import\|from attr import attrib\|@attrs\b\|attrib(" src/
   ```
   All must return zero results.
2. Run full pre-commit suite: `conda run -n pytest-bdd-ng-py314 pre-commit run --all-files`
3. Run full test suite one final time.
4. Update `tasks.md` — mark all tasks complete.
5. Produce migration audit summary (can be appended to `research.md`).

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `slots=True` breakage for subclassed classes | Low | Medium | Use `slots=False` for classes known to be subclassed; confirm with grep |
| `__post_init__` → `__attrs_post_init__` missed | Low | High | Grep for `__post_init__` before and after each batch |
| `field(default_factory=…)` not converted to `factory=…` | Medium | High | Ruff rule `B` or manual grep; ruff will flag type errors |
| `attr.asdict` / `attr.exceptions` references missed | Low | Medium | Grep for `from attr import` after Phase A |
| `Factory(x)` from old attrs not replaced everywhere | Low | High | Grep for `Factory(` in src/ after Phase A |
| Large file (`scenario_run.py`, 770+ lines) regression | Medium | Medium | Migrate this file last in its batch; run tests immediately after |
