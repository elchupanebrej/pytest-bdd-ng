# Allure-Cucumber Converter Architecture

## Overview

The Allure-Cucumber Converter is a post-execution, file-in/file-out tool that converts Cucumber Messages NDJSON to Allure3 JSON result files. It is designed to work with any cucumber runner, not just pytest-bdd.

## Data Flow

```
messages.ndjson (input)
  │
  ▼
reader.deserialize()
  │  Envelope → ExecutionProjection via ExecutionMessageAdapter.deserialize_dict()
  │  Unmapped envelope types → ExecutionProjection(event_type="unknown")
  ▼
collector.collect()
  │  Groups projections by testCaseStartedId
  │  Emits AllureGroup (group_id, list[ExecutionProjection])
  ▼
step_tree.build()
  │  Reconstructs step hierarchy from flat projections
  │  Emits AllureTestResult with nested AllureStepResult tree
  ▼
mapper.map()
  │  AllureTestResult → AllureTestResult with steps, attachments, status
  │  AllureAttachment from mapped events
  │  Unmapped events → structured AllureAttachment (attachment_type: "text")
  ▼
emitter.emit()
  │  Serializes Allure model objects to JSON via attrs.asdict()
  │  Writes *-result.json (per test case) and *-container.json (grouping)
  ▼
Output directory (allure-results/)
```

## Module Structure

```
src/pytest_bdd/plugin/allure_cucumber/
├── __init__.py              # Package marker
├── converter/               # Core conversion pipeline
│   ├── __init__.py          # convert() entry point
│   ├── reader.py            # NDJSON → ExecutionProjection
│   ├── collector.py         # Groups projections by testCaseStartedId
│   ├── step_tree.py         # Flat projections → nested step hierarchy
│   ├── mapper.py            # Maps cucumber events to Allure model
│   ├── emitter.py           # Serializes Allure objects to JSON files
│   └── model.py             # Allure3 model types (attrs-based)
├── cli.py                   # Standalone CLI: allure-cucumber messages.ndjson --output DIR
├── entrypoint.py            # Registers AllureCucumberPlugin with pytest
└── plugin.py                # AllureCucumberPlugin (calls converter at pytest_sessionfinish)
```

## Model Types

All Allure3 types are defined in `model.py` using `attrs` with `frozen=True`:

- `AllureStepResult` — test step with status, statusDetails, attachments, steps
- `AllureTestResult` — test case with status, statusDetails, steps, labels, links
- `AllureAttachment` — attachment with source, type, source_type
- `AllureStatusDetails` — message, known, knownDefect, muted
- `AllureGroup` — group of test results

## Mapping Decisions

### Event Type Matching

Mapper event type matching uses snake_case (`payload_kind.value`) from cucumber_messages, not PascalCase. Events are matched as:

| Cucumber Event | Mapper Handler | Allure Output |
|----------------|----------------|---------------|
| `test_case_started` | `_handle_test_case_started` | Creates base `AllureTestResult` |
| `test_step_started` | `_handle_test_step_started` | Creates `AllureStepResult` |
| `test_step_finished` | `_handle_test_step_finished` | Sets step status |
| `test_case_finished` | `_handle_test_case_finished` | Sets test status from last step |
| `attachment` | `_handle_attachment` | Creates `AllureAttachment` |
| (unmapped) | — | `map_unmappable_to_attachment()` → structured text attachment |

### Status Derivation

- Step status: derived from `test_step_finished.result.status` (PascalCase from cucumber_messages)
- Test status: derived from the **last step's** `status` (not from `test_case_finished.status` which doesn't exist in cucumber_messages)

### JSON Serialization

- Timestamps: converted to integer milliseconds (not ISO 8601 strings)
- attrs types: serialized via `attrs.asdict()` for proper type handling
- Allure3 JSON Schema: enforced by jsonschema validation in tests

## Schema Validation

The Allure3 Events JSONSchema is committed at `docs/allure3-events.schema.json` and validated via `jsonschema.validate()` in contract tests. Key constraints:

- `statusDetails` must be a non-null object (even if empty `AllureStatusDetails()`)
- `timestamp` fields must be integer milliseconds, not strings
- `statusDetails` defaults are `AllureStatusDetails()` (not `None`)

## CLI Interface

### Standalone CLI

```bash
allure-cucumber messages.ndjson --output allure-results
```

- Reads NDJSON from file path
- Converts using the full pipeline
- Writes result JSON files to output directory

### pytest Plugin

- `--allure-cucumber-output PATH` — output directory (default: `allure-results`)
- `--allure-cucumber-messages PATH` — NDJSON input path
- INI: `allure_cucumber_output_dir` — default output directory

## Testing

### Unit Tests (`tests/cases/unit/allure/`)

- `test_model.py` — Allure model types, statusDetails defaults
- `test_mapper.py` — Event handling, attachment mapping, status derivation
- `test_collector.py` — Event grouping by testCaseStartedId
- `test_step_tree.py` — Step tree building
- `test_emitter.py` — File emission and timestamp serialization
- `test_converter.py` — convert() function integration

### Contract Tests (`tests/cases/contract/allure/`)

- `test_schema_validation.py` — Allure3 JSON Schema validation
- `test_converter_contract.py` — Payload roundtrip, step count, status mapping
- `test_golden_parity.py` — Golden file parity with original mapper
- `test_hypothesis.py` — Property-based ID validation (hypothesis)
- `test_cli_contract.py` — CLI output, error handling, --help, input validation

### Integration Tests (`tests/cases/integration/allure/`)

- `test_plugin.py` — Plugin integration with pytest (testdir-based)

### Hypothesis Invariants

All property-based tests verify:
- All generated test IDs are valid Allure file names (alphanumeric, hyphens, underscores only)
- No generated test IDs contain invalid characters
- All step statuses are valid Allure statuses (passed/failed/skipped/broken/unknown)
- Empty inputs produce empty results without errors

## Deferred

- **Layer 2 validation**: Playwright-based HTML rendering validation of Allure reports
- **Non-JSON output**: YAML and Markdown serialization formats
