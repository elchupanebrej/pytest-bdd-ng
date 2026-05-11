# Go↔Python JSON Bridge Contract

**Feature**: Go Gherkin Parser (023-go-gherkin-parser)
**Type**: Cross-language data contract
**Format**: JSON (UTF-8 encoded C strings passed via ctypes)

## C ABI Functions

### `ParseGherkinDocument`

```
Signature:  char* ParseGherkinDocument(char* text)
Purpose:    Parse plain Gherkin (.feature) text
Input:      Null-terminated UTF-8 string containing full Gherkin feature content
Output:     Null-terminated UTF-8 JSON string (see Return Formats below)
Memory:     Caller MUST call FreeCString on the returned pointer after use
```

### `ParseGherkinMarkdown`

```
Signature:  char* ParseGherkinMarkdown(char* text)
Purpose:    Parse Markdown Gherkin (.feature.md) text
Input:      Null-terminated UTF-8 string containing full Markdown + Gherkin content
Output:     Null-terminated UTF-8 JSON string (see Return Formats below)
Memory:     Caller MUST call FreeCString on the returned pointer after use
```

### `FreeCString`

```
Signature:  void FreeCString(char* s)
Purpose:    Free memory allocated by Go for a C string
Input:      Pointer previously returned by ParseGherkinDocument or ParseGherkinMarkdown
Output:     None
Notes:      Idempotent (safe to call with NULL). Must be called exactly once per parse result.
```

### `Version`

```
Signature:  char* Version()
Purpose:    Return the version string of the linked gherkin Go library
Output:     Version string (e.g., "v28.1.0")
Memory:     Caller MUST call FreeCString on the returned pointer after use
```

## Return Formats

### Success Response

```json
{
  "type": "GherkinDocument",
  "feature": {
    "type": "Feature",
    "language": "en",
    "keyword": "Feature",
    "name": "Example Feature",
    "description": "",
    "children": [
      {
        "type": "Scenario",
        "keyword": "Scenario",
        "name": "Example scenario",
        "steps": [...],
        "tags": [...],
        "location": {"line": 3, "column": 3}
      }
    ],
    "tags": []
  },
  "comments": []
}
```

**Rules**:
- Top-level object with `"type": "GherkinDocument"` (first character `{`)
- `feature` is `null` if the source has no Feature keyword
- All nodes have `type`, `location` fields
- Field names are camelCase matching protobuf JSON convention
- Empty collections (`children`, `tags`, `comments`) are `[]` not omitted

### Error Response

```json
[
  {
    "source": {
      "uri": "path/to/file.feature",
      "location": {"line": 3, "column": 1}
    },
    "message": "Parser error: expected one of: #Language, #TagLine, #FeatureLine, #Comment, #Empty..."
  }
]
```

**Rules**:
- JSON array (first character `[`)
- Each element has `source` (with `uri` and `location`) and `message`
- Fields match `CompositeParserException.errors` structure from Python gherkin library

## Contract Verification

The Python side validates:
1. First character of output: `{` = document, `[` = error array
2. For documents: `type` field equals `"GherkinDocument"`
3. For errors: each element has `source.uri`, `source.location.line`, `message`

Cross-backend equivalence: `message_converter.from_dict(go_result)` must equal `message_converter.from_dict(python_result)` for all valid Gherkin fixtures in `gherkin/testdata/good/`.
