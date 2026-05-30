# Feature Specification: Parser Type Alignment

**Feature Branch**: `021-parser-type-alignment`
**Created**: 2026-05-09
**Status**: Draft

## Feature Description

Refactor `parser.py` to use `cucumber_messages.GherkinDocument` (the runtime dataclass) as its output type throughout, replacing the TypedDict-based `pytest_bdd.compatibility.gherkin.GherkinDocument` that does not match actual runtime values. This eliminates all lies to the type checker through `cast()` calls and aligns parser.py with the type used by the struct_bdd parser and all downstream consumers.

## User Scenarios & Testing

### Scenario 1: Developer reads parser.py and trusts the type annotations

**Given** a developer is reading `pytest_bdd/parser.py`
**When** they read the `build_feature()`, `parse()`, and `normalize_gherkin_document_payload()` method signatures
**Then** the type annotations accurately reflect what types are used at runtime
**And** there are no `cast()` calls that silently convert between incompatible types
**And** static type checkers (mypy) can validate the code without suppression

### Scenario 2: Parser output flows to downstream consumers without surprise

**Given** `GherkinParser` or `MarkdownGherkinParser` has parsed a feature file
**When** the returned `GherkinDocument` is passed to `FeatureRuntimeBinding.build()` or `_bind_feature()`
**Then** the object is a `cucumber_messages.GherkinDocument` dataclass (not a dict)
**And** attribute access (`gherkin_document.feature`, `gherkin_document.uri`) works identically to before
**And** `_pytest_bdd_filename` is still set as a dynamic attribute for filename resolution

### Scenario 3: Raw dict normalization still functions correctly

**Given** the gherkin upstream parser returns a raw dict for the feature AST
**When** `normalize_gherkin_document_payload()` processes it (setting defaults for comments, line numbers, keyword)
**Then** normalization operates on a properly typed `dict` intermediate representation
**And** normalization behavior is unchanged from before

### Edge Cases

- **Empty feature files**: Parser produces a valid `GherkinDocument` with no scenarios — typing must hold
- **Markdown features**: `MarkdownGherkinParser` has the same typing issues and must be fixed in the same pass
- **CompositeParserException path**: Early return on parse error does not reach `build_feature()` — no typing change needed there
- **Struct BDD path**: Already uses `cucumber_messages.GherkinDocument` — no changes needed

## Functional Requirements

- **FR-001**: `parser.py` MUST import `GherkinDocument` from `cucumber_messages` (not from `pytest_bdd.compatibility.gherkin`)
- **FR-002**: `BaseParser.build_feature()` MUST return `cucumber_messages.GherkinDocument` without using `cast()`
- **FR-003**: `BaseParser.normalize_gherkin_document_payload()` MUST accept a `dict` parameter (or a type alias for the raw dict shape) instead of the TypedDict `GherkinDocument`
- **FR-004**: `GherkinParser.parse()` and `MarkdownGherkinParser.parse()` MUST type the intermediate raw dict from `gherkin_parser.parse()` as `dict` rather than casting to `GherkinDocument`
- **FR-005**: `_set_feature_filename()` MUST continue to use the `_PytestBddFilenameCarrier` protocol for duck-typing the `_pytest_bdd_filename` attribute set
- **FR-006**: `ParserProtocol.parse()` return type annotation MUST be updated to `tuple[cucumber_messages.GherkinDocument, str]`
- **FR-007**: All `cast("GherkinDocument", ...)` calls in parser.py (lines 136, 172, 232) MUST be removed
- **FR-008**: The `import` of `pytest_bdd.compatibility.gherkin` in parser.py MUST be removed (or replaced with the cucumber_messages import)
- **FR-009**: Existing tests for parser.py, feature_locator.py, and scenario_locator.py MUST continue to pass without modification
- **FR-010**: Static type checking (mypy) on parser.py MUST pass without new suppressions for the refactored code

## Success Criteria

- **SC-001**: All `cast("GherkinDocument", ...)` calls are removed from `parser.py`
- **SC-002**: `parser.py` has zero `# type: ignore` suppressions related to `GherkinDocument` typing
- **SC-003**: The full existing test suite (unit, integration, e2e) passes with no regressions
- **SC-004**: `mypy` passes on `parser.py` without new errors
- **SC-005**: Downstream consumers (`feature_locator.py`, `scenario_locator.py`, `plugin.py`) require no changes — their existing cucumber_messages.GherkinDocument usage continues to work
- **SC-006**: The `compatibility/parser.py` module has its `ParserProtocol` signature updated consistently

## Key Entities

- **cucumber_messages.GherkinDocument**: The runtime dataclass representing a parsed Gherkin feature. Has `.feature`, `.comments`, `.uri` attributes.
- **Raw dict intermediate**: A plain `dict` returned by the upstream `gherkin.parser.Parser.parse()`. Used during normalization before conversion to the dataclass.
- **_PytestBddFilenameCarrier Protocol**: A structural protocol used by `_set_feature_filename()` to duck-type the `_pytest_bdd_filename` attribute set on the dataclass.

## Assumptions

- The `cucumber_messages` package is already a hard dependency and available at runtime
- The `pytest_bdd.compatibility.gherkin.GherkinDocument` TypedDict does not need to be removed at this stage — only parser.py stops using it
- No consumers of parser.py rely on dict-style access (`gd["uri"]`) to the returned GherkinDocument — all use attribute access
- The normalization logic (`normalize_gherkin_document_payload`) only needs the raw dict shape, not the full TypedDict type structure

## Scope

**In scope**:
- `src/pytest_bdd/parser.py` — all type annotation and cast fixes
- `src/pytest_bdd/compatibility/parser.py` — `ParserProtocol` return type update

**Out of scope**:
- Removing `pytest_bdd.compatibility.gherkin.GherkinDocument` entirely (other modules may still depend on it)
- Fixing type issues in other modules that use `GherkinDocument`
- Changing runtime behavior of any function
- Changing the `struct_bdd` parser path (already correct)
