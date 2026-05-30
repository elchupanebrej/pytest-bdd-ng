# Research: Parser Type Alignment

**Date**: 2026-05-09
**Feature**: 021-parser-type-alignment

## Decisions

### Decision 1: Use `cucumber_messages.GherkinDocument` as the output type

**Rationale**:
- `FeatureRuntimeBinding.load_gherkin_document()` (called by `build_feature()`) already returns a `cucumber_messages.GherkinDocument` dataclass at runtime
- The struct_bdd parser path (`GherkinDocumentBuilder`) already uses and returns this type
- All downstream consumers (`feature_locator.py`, `scenario_locator.py`, `plugin.py`) import `GherkinDocument` from `cucumber_messages`
- The `cast()` at parser.py:136 is currently a lie — removing it requires aligning the type annotation to reality

**Alternatives considered**:
- Converting to compat TypedDict: Would require writing a dict adapter that converts dataclass fields to dict keys. Adds code without benefit since no consumer uses dict-style access.
- New adapter type: Overengineered for a type annotation fix. No consumer needs a third type.

### Decision 2: Type intermediate raw dict as plain `dict`

**Rationale**:
- The upstream `gherkin.parser.Parser.parse()` returns a plain `dict` at runtime
- `normalize_gherkin_document_payload()` uses dict operations (`.setdefault()`, `.get()`, `isinstance(node, dict)`)
- No need for a TypedDict for the intermediate since its structure is not fully known and not validated
- Using `dict` is honest and accurate

**Alternatives considered**:
- `GherkinDocumentDict(TypedDict)`: Would require defining all nested types (Feature, Scenario, Step, etc.) for little benefit since the normalizer doesn't need type safety on nested structures.

### Decision 3: Keep `_set_feature_filename` Protocol pattern unchanged

**Rationale**:
- The `_PytestBddFilenameCarrier` Protocol already correctly describes the duck-typed attribute set
- Works identically on the dataclass (no `__slots__`)
- No need to change this pattern

### Decision 4: Update `ParserProtocol` in compatibility/parser.py

**Rationale**:
- The protocol must match the concrete return type
- `StructBDDParser` already returns `cucumber_messages.GherkinDocument` (imports from cucumber_messages)
- `GherkinParser` and `MarkdownGherkinParser` will return it after this refactoring

## No Envasion/Unknowns

All types and their runtime behavior were confirmed via codebase exploration during brainstorming phase. No unknowns remain.
