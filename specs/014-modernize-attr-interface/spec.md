# Feature Specification: Modernize `attrs` Interface Across the Library

**Feature Branch**: `014-modernize-attr-interface`
**Created**: 2026-03-17
**Status**: Draft
**Input**: User description: "Вся библиотека должна использовать современный интерфейс attr вместо старого. Dataclass и __init__-based классы должны быть отрефакторены"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Contributors work with a uniform, modern class definition style (Priority: P1)

A contributor reading or modifying the library's source code encounters a single, consistent way
of defining data-holding classes throughout the entire codebase. Instead of mixing `dataclass`,
hand-written `__init__` constructors, and legacy `attr.s`/`attr.ib` declarations, every class
follows the modern `attrs` declarative style (`@define`, `@attrs.define`, `field()`, etc.). This
makes onboarding faster, reduces cognitive overhead when tracing object construction, and
eliminates subtle differences in behaviour between the three approaches.

**Why this priority**: Class interface uniformity is the foundational precondition for every
subsequent improvement (better type inference, serialisation, validation hooks). Without it the
codebase accumulates drift that compounds with every new class added.

**Independent Test**: Can be verified by inspecting the source tree for the absence of `@dataclass`,
bare `def __init__` constructors on data models, and deprecated `attr.s`/`attr.ib` uses, while
confirming the existing test suite still passes in full.

**Acceptance Scenarios**:

1. **Given** a contributor searches the source tree for `@dataclass` decorator usage on library
   classes, **When** the refactoring is complete, **Then** no library-owned class uses `@dataclass`
   (test-fixture dataclasses are exempt if explicitly annotated as fixtures).
2. **Given** a contributor searches for `def __init__` methods on data-model classes, **When** the
   refactoring is complete, **Then** no hand-written `__init__` on a data-model class exists;
   construction is handled entirely by the `attrs` machinery.
3. **Given** a contributor searches for `attr.s`, `attr.ib`, `attrs.attrs`, or `attrib()` call forms,
   **When** the refactoring is complete, **Then** none of these deprecated call forms appear in
   library-owned source files.

---

### User Story 2 — Library users observe no breaking changes in the public interface (Priority: P2)

A library user running their existing BDD test suite with the updated version of `pytest-bdd-ng`
expects the same observable behaviour as before. The internal refactoring is transparent: no
public attribute names change, no constructor signatures change for public APIs, and no
previously-passing test should start failing due to the migration.

**Why this priority**: Preserving backward compatibility protects the existing user base and avoids
an unnecessary major version bump driven purely by internal housekeeping.

**Independent Test**: Execute the full existing test suite against the refactored library; zero
regressions must be observed. Spot-check that previously importable symbols remain importable and
that public constructor keyword arguments are unchanged.

**Acceptance Scenarios**:

1. **Given** an existing user project imports `pytest-bdd-ng` classes by name, **When** the updated
   library is installed, **Then** all previously importable symbols remain importable without error.
2. **Given** an existing user project instantiates `pytest-bdd-ng` objects with keyword arguments,
   **When** the updated library is installed, **Then** the keyword argument names and types are
   unchanged.
3. **Given** the full test suite is executed, **When** the refactoring is applied, **Then** all
   previously-passing tests continue to pass and no new failures are introduced.

---

### User Story 3 — Static analysis tooling reports fewer type errors and warnings (Priority: P3)

A contributor running type-checking or linting on the code base finds that the uniform `attrs`
interface allows type checkers and linters to resolve attribute types correctly without special
plugin workarounds. The number of type-checker warnings related to class construction and attribute
access is reduced or eliminated.

**Why this priority**: Improved static-analysis coverage is a long-term quality benefit that
becomes realised after the core migration (P1, P2) is done. It is valuable but not blocking.

**Independent Test**: Run the project's static analysis pipeline before and after the refactoring
and compare the count of class-construction-related warnings; the post-migration count must not
increase and should decrease for modernised classes.

**Acceptance Scenarios**:

1. **Given** the linter/type-checker is run on the refactored codebase, **When** results are
   compared to the pre-migration baseline, **Then** the number of attribute-access and
   construction-related warnings does not increase.
2. **Given** a new contributor adds a class using the modern `attrs` style, **When** the linter
   is run, **Then** no special suppression comments are needed for normal attribute access.

---

### Edge Cases

- A public class that currently exposes a hand-written `__init__` with complex default logic must
  preserve identical observable defaults after migration (e.g., mutable defaults handled via
  `attrs` factory functions).
- Classes that rely on `__post_init__` (dataclass convention) must have their validation logic
  preserved using the `attrs` equivalent (`__attrs_post_init__`).
- Subclasses of library classes defined by users in plugin code must continue to work without
  changes; the migration must not tighten the inheritance contract.
- Classes used as `pytest` fixtures or internally by `pluggy` must remain passable as fixture
  return values and hook implementations without behavioural change.
- If a class is referenced by `pickle`, `copy`, or other serialisation mechanisms in existing
  tests, the refactored class must maintain compatibility with those mechanisms.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every data-model class in the library MUST be defined using the modern `attrs`
  declarative interface (`@define`, `@attrs.define`, or equivalent current-generation decorator
  form with `field()` for attribute declarations).
- **FR-002**: No library-owned class MUST use the `@dataclass` decorator from the standard library.
- **FR-003**: No library-owned data-model class MUST contain a hand-written `__init__` constructor
  method; all construction logic MUST be expressed through `attrs` field declarations, factories,
  validators, or `__attrs_post_init__`.
- **FR-004**: Deprecated `attr.s`, `attr.ib`, `attrs.attrs`, and `attrib()` forms MUST NOT appear
  in library-owned source files after the migration.
- **FR-005**: All previously-public attribute names on migrated classes MUST remain unchanged.
- **FR-006**: All previously-valid constructor keyword arguments on public classes MUST remain
  valid after migration.
- **FR-007**: The full existing test suite MUST pass without modification after the refactoring
  (test code is exempt from the migration scope unless it directly tests refactored class
  construction).
- **FR-008**: Mutable default values (lists, dicts, sets) MUST be expressed using `attrs` factory
  functions, preserving the same per-instance isolation semantics that were in place before.
- **FR-009**: Any validation logic previously in `__init__` or `__post_init__` MUST be preserved
  using `attrs` validators or `__attrs_post_init__` hooks.
- **FR-010**: The migration MUST be auditable: a clear mapping of every changed class (before/after
  decorator and field-definition style) MUST be produced as part of the implementation.

### Key Entities

- **Data-model class**: A class whose primary purpose is to hold structured data and expose it via
  attributes; identified by current use of `@dataclass`, hand-written `__init__`, or legacy `attr`
  decorators.
- **Modern `attrs` interface**: The current-generation API consisting of `@define` (or
  `@attrs.define`) for class-level decoration and `field()` (or `attrs.field()`) for individual
  attribute declarations, as opposed to deprecated `attr.s`/`attr.ib` forms.
- **Public attribute**: An attribute whose name does not begin with an underscore and that appears
  in public documentation or is accessed by user-written code or tests.
- **Fixture class**: A class that exists solely as a test fixture or test helper; exempt from the
  migration requirement unless its structure would benefit from the change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % of library-owned data-model classes use the modern `attrs` declarative style;
  zero occurrences of `@dataclass`, bare `def __init__` on data models, or deprecated `attr.s` /
  `attr.ib` / `attrib()` forms remain in library source files.
- **SC-002**: The full existing test suite passes with a 100 % pass rate (zero regressions) after
  the migration.
- **SC-003**: The count of static-analysis (type-checker / linter) warnings related to class
  construction and attribute access does not increase compared to the pre-migration baseline.
- **SC-004**: Every changed class is documented in a migration audit log that maps the before and
  after state, enabling future contributors to trace the rationale for each change.

## Assumptions

- Test-fixture classes (classes whose sole purpose is to serve as `pytest` fixture return values
  in the `tests/` tree) are out of scope unless they mirror library internals.
- The migration targets the `src/` tree; the `tests/` tree is only modified where test code
  directly constructs or subclasses migrated library classes in ways that would break after
  migration.
- The `attrs` library is already a declared runtime dependency of `pytest-bdd-ng`; no new
  dependency needs to be added.
- The minimum supported version of `attrs` is high enough to provide `@define` and `field()`;
  this is verified against the current `pyproject.toml` / `setup.cfg` dependency constraints
  before implementation begins.
- "Modern interface" means the `attrs >= 20.1.0` API (`@define` / `field()`); the older
  `attr.s` / `attr.ib` API is considered legacy for the purposes of this feature.
