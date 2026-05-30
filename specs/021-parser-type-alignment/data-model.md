# Data Model: Parser Type Alignment

**Date**: 2026-05-09
**Feature**: 021-parser-type-alignment

No new data entities are introduced by this refactoring. The existing type relationships are documented below for clarity.

## Type Flow in `parser.py` (after refactoring)

```text
  gherkin.parser.Parser.parse(feature_text)
       │
       │  Returns: plain dict (runtime)
       │  Typed as: dict[str, object]
       ▼
  [Intermediate: raw dict]
       │
       │  Mutations: ["uri"] = uri, .setdefault("keyword", "")
       │  normalization: fill missing line/column defaults
       ▼
  FeatureRuntimeBinding.load_gherkin_document(raw_dict)
       │
       │  Returns: cucumber_messages.GherkinDocument (dataclass)
       ▼
  _set_feature_filename(dataclass, path)
       │
       │  Sets: _pytest_bdd_filename attribute (duck-typed via Protocol)
       ▼
  Returns: tuple[cucumber_messages.GherkinDocument, str]
```

## Existing Types (unchanged)

| Type | Module | Kind | Used by parser.py after refactoring? |
|------|--------|------|--------------------------------------|
| `cucumber_messages.GherkinDocument` | `cucumber_messages._messages` | `@dataclass` | **Yes** — output type |
| `pytest_bdd.compatibility.gherkin.GherkinDocument` | `pytest_bdd.compatibility.gherkin` | `TypedDict` (extends gherkin.parser_types.GherkinDocument) | **No** — removed from parser.py imports |
| `gherkin.parser_types.GherkinDocument` | `gherkin.parser_types` | `TypedDict` | **No** — upstream type, not directly used |

## Protocol (unchanged)

```python
class _PytestBddFilenameCarrier(Protocol):
    _pytest_bdd_filename: str | None
```

Used by `_set_feature_filename()` to duck-type the dynamic attribute set on the dataclass.
