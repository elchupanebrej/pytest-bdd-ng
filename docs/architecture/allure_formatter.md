# Allure Formatter Architecture

## Overview

The Allure Formatter provides two modes for generating Allure3 JSON result files from Cucumber Messages:

1. **pytest-native plugin mode** (preferred): The `AllureFormatter` listener intercepts `pytest_bdd_message` hook calls in real-time and writes Allure results through the `allure-python-commons` lifecycle during test execution. This mode requires no manual NDJSON file handoff.

2. **Standalone formatter mode** (deprecated for primary use): A file-in/file-out CLI tool (`allure-formatter`) that converts Cucumber Messages NDJSON files to Allure3 JSON result files. This mode is useful for post-execution conversion but is no longer the recommended approach.

## Data Flow

### pytest-native Data Flow (Live mode — real-time interception)

```text
LifecycleService emits message via config.hook.pytest_bdd_message(config, message)
       │
       ▼
AllureFormatterPlugin.pytest_bdd_message(config, message)  # hookimpl
       │
       ├─ Deserialize: message → ExecutionProjection via ExecutionMessageAdapter
       │
       ├─ Route by payload_kind to AllureFormatter:
       │   ├─ test_case_started  → lifecycle.schedule_test_case(uuid)
       │   ├─ test_step_started  → lifecycle.start_step(uuid, parent_uuid)
       │   ├─ test_step_finished → lifecycle.stop_step(uuid, status, statusDetails)
       │   ├─ test_case_finished → lifecycle.write_test_case(uuid)
       │   ├─ attachment         → lifecycle.attach_data() / lifecycle.attach_file()
       │   ├─ test_run_started   → initialize run context
       │   └─ test_run_finished  → finalize run context
       │
       ▼
AllureLifecycle (allure-python-commons)
       │
       ▼
AllureFileLogger → writes *-result.json and *-container.json to output_dir
```

### Standalone Formatter Data Flow (deprecated)

```text
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
  │
  ▼
Output directory (allure-results/)
```

## Module Structure

```text
src/pytest_bdd/plugin/allure_formatter/
├── __init__.py              # Package marker
├── entrypoint.py            # pytest_addoption, pytest_configure, pytest_unconfigure
├── listener.py              # AllureFormatter — receives pytest_bdd_message, maps to lifecycle
├── api_hooks.py             # AllureFormatterApiHooks — implements allure_commons hooks
├── message_adapter.py       # CucumberEnvelopeAdapter — envelope → AllureLifecycle state machine
├── plugin.py                # Plugin class AllureFormatterPlugin
├── hook.py                  # AllureFormatterHookSpec for cross-plugin hooks
├── cli.py                   # Standalone CLI: allure-formatter messages.ndjson --output DIR
└── converter/               # Core conversion pipeline (used by standalone mode)
    ├── __init__.py          # convert() entry point
    ├── reader.py            # NDJSON → ExecutionProjection
    ├── collector.py         # Groups projections by testCaseStartedId
    ├── step_tree.py         # Flat projections → nested step hierarchy
    ├── mapper.py            # Maps cucumber events to Allure model
    ├── emitter.py           # Serializes Allure objects to JSON files
    └── model.py             # Allure3 model types (attrs-based)
```

## Plugin Architecture

### Pattern: allure-pytest-bdd

The plugin architecture follows `allure-pytest-bdd` patterns adapted for Cucumber Message envelopes:

| Component | allure-pytest-bdd | Our Implementation |
|-----------|-------------------|-------------------|
| Listener class | `PytestBDDListener(lifecycle)` | `AllureFormatter(lifecycle, output_dir)` |
| Hook interception | `@pytest.hookimpl pytest_bdd_before_scenario` | `pytest_bdd_message` routes `test_case_started` |
| Step lifecycle | `@pytest.hookimpl pytest_bdd_before_step` | `pytest_bdd_message` routes `test_step_started` |
| API hooks | `AllurePytestBddApiHooks(config, lifecycle)` | `AllureFormatterApiHooks(config, lifecycle)` |
| Registration | `allure_commons.plugin_manager.register(listener)` | Same pattern |
| Cleanup | `cleanup_factory(plugin)` → `config.add_cleanup()` | Same pattern |
| File logger | `AllureFileLogger(report_dir, clean)` | Same API |
| UUID cache | `ItemCache` (dict-based) | `EnvelopeStateCache` (test_case_started_id → uuid) |

### Key Differences from allure-pytest-bdd

1. **Data source**: allure-pytest-bdd uses pytest-bdd hooks (`pytest_bdd_before_scenario`, etc.). We use `pytest_bdd_message` which emits Cucumber Message envelopes — a lower-level, framework-agnostic interface.

2. **State machine**: allure-pytest-bdd receives structured events (feature, scenario, step objects). We receive raw envelopes that must be deserialized and routed by `payload_kind`.

3. **No step function access**: allure-pytest-bdd receives `step_func` and `step_func_args`. We only receive the Cucumber Message envelope — step names and parameters come from the message, not from pytest fixtures.

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

| Cucumber Event | Listener Handler | Allure Lifecycle Call |
|----------------|------------------|----------------------|
| `test_case_started` | `_handle_test_case_started` | `lifecycle.schedule_test_case(uuid)` |
| `test_step_started` | `_handle_test_step_started` | `lifecycle.start_step(uuid, parent_uuid)` |
| `test_step_finished` | `_handle_test_step_finished` | `lifecycle.stop_step(uuid, status)` |
| `test_case_finished` | `_handle_test_case_finished` | `lifecycle.write_test_case(uuid)` |
| `attachment` | `_handle_attachment` | `lifecycle.attach_data()` / `lifecycle.attach_file()` |
| `test_run_started` | `_handle_test_run_started` | (initialize run context) |
| `test_run_finished` | `_handle_test_run_finished` | (finalize run context) |
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

### Standalone Formatter CLI (deprecated for primary use)

```bash
allure-formatter messages.ndjson --output allure-results
```

- Reads NDJSON from file path
- Converts using the full pipeline
- Writes result JSON files to output directory
- **Note**: The standalone CLI is deprecated for primary use. Prefer the pytest-native plugin mode.

### pytest Plugin

**Live mode** (default when only `--allure-formatter-output` is passed):
- `--allure-formatter-output PATH` — output directory for Allure results (default: `allure-results`)
- The plugin intercepts `pytest_bdd_message` hooks **in real-time** during test execution
- Each envelope is deserialized, routed, and written through `AllureLifecycle` incrementally
- Allure result files appear in the output directory as tests execute

**Import mode** (when `--cucumber-messages` is passed):
- `--cucumber-messages PATH` — NDJSON input path for post-execution conversion
- The plugin clears all collected tests via `pytest_collection_modifyitems`
- The NDJSON file is read and fed through the same `AllureFormatter` pipeline
- Exit code 5 (NO_TESTS_COLLECTED) is expected and valid

**Configuration error**: Using both `--allure-formatter-output` and `--cucumber-messages` together is not supported.

- INI: `allure_formatter_output_dir` — default output directory

## Testing

### Unit Tests (`tests/cases/unit/formatters/allure_formatter/`)

- `test_model.py` — Allure model types, statusDetails defaults
- `test_mapper.py` — Event handling, attachment mapping, status derivation
- `test_collector.py` — Event grouping by testCaseStartedId
- `test_step_tree.py` — Step tree building
- `test_emitter.py` — File emission and timestamp serialization
- `test_converter.py` — convert() function integration

### Contract Tests (`tests/cases/contract/formatters/allure_formatter/`)

- `test_schema_validation.py` — Allure3 JSON Schema validation
- `test_converter_contract.py` — Payload roundtrip, step count, status mapping
- `test_golden_parity.py` — Golden file parity with original mapper
- `test_hypothesis.py` — Property-based ID validation (hypothesis)
- `test_cli_contract.py` — CLI output, error handling, --help, input validation
- `test_allure_plugin_hook_ingestion.py` — Hook ingestion contract tests
- `test_allure_plugin_ndjson_import.py` — NDJSON import contract tests

### Integration Tests (`tests/cases/integration/formatters/allure_formatter/`)

- `test_plugin.py` — Plugin integration with pytest (testdir-based)
- `test_realtime_interception.py` — Real-time event interception tests

### Hypothesis Invariants

All property-based tests verify:
- All generated test IDs are valid Allure file names (alphanumeric, hyphens, underscores only)
- No generated test IDs contain invalid characters
- All step statuses are valid Allure statuses (passed/failed/skipped/broken/unknown)
- Empty inputs produce empty results without errors

## Deferred

- **Layer 2 validation**: Playwright-based HTML rendering validation of Allure reports
- **Non-JSON output**: YAML and Markdown serialization formats
