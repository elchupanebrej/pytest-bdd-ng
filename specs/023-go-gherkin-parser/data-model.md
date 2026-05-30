# Data Model: Go Gherkin Parser

**Feature**: Go Gherkin Parser (023-go-gherkin-parser)
**Date**: 2026-05-11

## Entities

### GherkinGoResult

Represents the result of a Go parser call.

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Always `"GherkinDocument"` for success |
| `feature` | `dict | None` | Parsed Feature node (or `None` for empty documents) |
| `comments` | `list[dict]` | Comment nodes from the source file |

**Validation**: `type` field must equal `"GherkinDocument"`. First character of JSON is `{`.

### GherkinGoError

Represents a structured parse error from the Go parser.

| Field | Type | Description |
|-------|------|-------------|
| `source.uri` | `str` | URI of the feature file |
| `source.location.line` | `int` | Line number (1-indexed) |
| `source.location.column` | `int` | Column number (1-indexed) |
| `message` | `str` | Human-readable error message |

**Validation**: Returned as a JSON array `[{...}, ...]`. First character of JSON is `[`.

### GherkinParseError (Python exception)

Wraps the structured error list from Go.

| Attribute | Type | Description |
|-----------|------|-------------|
| `errors` | `list[GherkinGoError]` | List of structured parse errors |

**Inherits**: `Exception`

### GherkinGoNotAvailable (Python exception)

Raised when the Go shared library cannot be loaded.

| Attribute | Type | Description |
|-----------|------|-------------|
| `reason` | `str` | Human-readable reason for unavailability |

**Inherits**: `RuntimeError`

### Mimetype

Existing enum from `scenario_test_collector/plugin.py`. Used to select Go function.

| Value | Go Function | Python Equivalent |
|-------|------------|-------------------|
| `gherkin_plain` | `ParseGherkinDocument` | `GherkinParser` |
| `gherkin_markdown` | `ParseGherkinMarkdown` | `MarkdownGherkinParser` |

**No new values needed.**

### Backend

Internal enum for parser backend selection.

| Value | Behavior |
|-------|----------|
| `auto` | Try Go, fall back to Python per-file |
| `go` | Only Go, raise on any failure |
| `python` | Only Python (current behavior) |

**Source**: Environment variable `PYTEST_BDD_GHERKIN_BACKEND`

## State Transitions

### Parser Backend Selection

```text
                 ┌──────────────────────────┐
                 │ PYTEST_BDD_GHERKIN_BACKEND│
                 └───────────┬──────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
        ┌──────┐        ┌──────┐        ┌──────────┐
        │ auto │        │  go  │        │ python   │
        └──┬───┘        └──┬───┘        └────┬─────┘
           │               │                 │
           ▼               ▼                 ▼
    Try Go import     Try Go import    Use Python parser
         │                 │
    ┌────┴────┐       ┌────┴────┐
    │ success │       │ success │
    └────┬────┘       └────┬────┘
         ▼                 ▼
    Use Go parser    Use Go parser
         │
    ┌────┴────┐
    │ failure │
    └────┬────┘
         ▼
    Use Python parser    GherkinGoNotAvailable
    (log WARNING)        raised
```

### Parse Call Flow

```text
_parse_feature_file(path, content)
  │
  ├─ decode content → text
  │
  ├─ [if go backend] _gherkin_go.parse(text, mimetype=mimetype)
  │     │
  │     ├─ _bridge.parse_gherkin_document(text)  ─→ Go → JSON string
  │     │     │
  │     │     ├─ json.loads() → dict
  │     │     │
  │     │     ├─ isinstance(list)? → raise GherkinParseError(list)
  │     │     │
  │     │     └─ else → return dict
  │     │
  │     └─ try/except GherkinGoNotAvailable → fallback to Python
  │
  └─ [if python backend] Parser(AstBuilder()).parse(text) → dict
        │
        └─ return dict
```

## Relationships

```
GherkinGoNotAvailable ──triggers──► Python fallback (auto mode)
GherkinGoNotAvailable ──triggers──► fatal error (go mode)
GherkinParseError ──wraps──► GherkinGoError[]
GherkinGoError ──maps to──► CompositeParserException (existing Python)
GherkinGoResult ──feeds into──► message_converter.from_dict()
                                  └─► cucumber_messages.GherkinDocument
```
