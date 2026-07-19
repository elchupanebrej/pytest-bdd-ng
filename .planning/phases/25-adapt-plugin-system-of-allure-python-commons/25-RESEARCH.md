# Phase 25: Adapt plugin system of allure-python-commons - Research

**Researched:** 2026-06-13
**Domain:** pytest plugin architecture, allure-python-commons lifecycle API, xdist message consolidation
**Confidence:** HIGH

## Summary

Phase 25 replaces the current file-first Allure pytest wrapper with a pytest-native plugin that consumes `pytest_bdd_message` hook calls directly and writes Allure results through `allure-python-commons`. The current `plugin.py` already collects envelopes via `pytest_bdd_message` and already uses `allure-python-commons` in `adapter.py`, but the primary code path reads from a consolidated NDJSON file at session finish rather than consuming the live hook stream. The core architectural change is rewiring the data flow: live mode reads from the in-memory `EnvelopeRegistry` (or the collected `self.envelopes` list), while NDJSON import mode feeds the same adapter after reading from file. Both modes share the existing `convert_to_allure_commons()` adapter.

The existing adapter (`adapter.py`) already uses `AllureLifecycle`, `AllureFileLogger`, and `allure_commons.plugin_manager` to write results through `allure-python-commons`. The mapper (`mapper.py`) is the semantic reference. The consolidation layer (`message_consolidation.py`) already handles xdist ID namespacing, deduplication, and controller total stream semantics. The main work is rewiring the plugin data source, removing the file-first dependency for live mode, and adding comprehensive verification.

**Primary recommendation:** Rewire `AllureCucumberPlugin` to use in-memory envelopes (from `self.envelopes` or `EnvelopeRegistry`) instead of reading from `final_messages_file_path`. Keep the existing `adapter.py` and `mapper.py` as-is since they already work correctly through `allure-python-commons`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `pytest_bdd_message` collection | API / Backend | -- | Plugin implements the hook and stores envelopes |
| Envelope-to-Allure conversion | API / Backend | -- | `adapter.py` converts projections and writes via lifecycle |
| NDJSON file reading | API / Backend | -- | Reader module parses NDJSON into projections |
| xdist message consolidation | API / Backend | -- | Controller consolidates worker fragments |
| Allure result file writing | API / Backend | -- | `AllureFileLogger` writes JSON files to disk |
| `allure-pytest` coexistence | API / Backend | -- | Plugin detects and avoids duplicate BDD results |
| Option/INI registration | API / Backend | -- | `entrypoint.py` registers CLI and INI options |
| HTML report generation | CDN / Static | -- | External Docker/Allure CLI, not plugin responsibility |
| BDD scenario collection skip | API / Backend | -- | `pytest_collection_modifyitems` clears items in import mode |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| allure-python-commons | (in pyproject.toml) | Allure result lifecycle, file logger, plugin manager | Already a project dependency; provides `AllureLifecycle`, `AllureFileLogger`, `allure_commons.plugin_manager` |
| attrs | (in pyproject.toml) | Structured model classes | Project convention; all models use `@define` |
| pytest | >=7.0.0 | Plugin framework | Core dependency; hook implementation via pluggy |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cucumber-messages | (in pyproject.toml) | Cucumber message envelope types | Envelope/Message type definitions |
| returns | (in pyproject.toml) | Maybe monad for null handling | Used in message_registry.py and consolidation |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| allure-python-commons lifecycle | Direct JSON file writing | Lifecycle provides consistent format, attachment handling, plugin manager integration |
| EnvelopeRegistry for live mode | Custom list storage | Registry already provides stash-backed storage with identifiable object indexing |
| consolidate_message_fragments | Custom xdist merge | Existing consolidation handles ID namespacing, deduplication, diagnostics |

**Installation:** Already in `pyproject.toml` dependencies.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| allure-python-commons | PyPI | 8+ yrs | ~2M/wk | github.com/allure-framework/allure-python | OK | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### Current Architecture (file-first)

```text
pytest session start
  -> LifecycleService emits messages via config.hook.pytest_bdd_message()
  -> EnvelopeRegistry stores all envelopes in config.stash
  -> TransportService writes messages to NDJSON file on disk
  -> (xdist: workers forward batches to controller)
  -> (xdist: controller consolidates fragments)
  -> pytest_sessionfinish
  -> AllureCucumberPlugin reads from final_messages_file_path
  -> adapter.convert_to_allure_commons() writes Allure results
```

### Target Architecture (hook-native)

```text
pytest session start
  -> LifecycleService emits messages via config.hook.pytest_bdd_message()
  -> EnvelopeRegistry stores all envelopes in config.stash
  -> AllureCucumberPlugin.pytest_bdd_message() collects envelopes in self.envelopes
  -> (xdist: workers forward batches to controller)
  |   AllureCucumberPlugin skips Allure output on workers (workerinput check)
  -> (xdist: controller consolidates fragments via transport_runtime)
  -> pytest_sessionfinish
  -> AllureCucumberPlugin reads from self.envelopes (live mode)
  |   OR reads from NDJSON file (import mode)
  -> adapter.convert_to_allure_commons() writes Allure results through allure-python-commons
```

### Key Insight: Minimal Changes Required

The existing code is 80% there. The specific changes are:

1. `plugin.py` `pytest_sessionfinish`: Use `self.envelopes` instead of reading from `final_messages_file_path` for live mode
2. `adapter.py`: Already works through `allure-python-commons` -- no changes needed
3. `entrypoint.py`: Option names already match D-14/D-15 decisions
4. xdist: Workers already skip Allure output; controller already consolidates

### Recommended Project Structure

```text
src/pytest_bdd/plugin/allure_cucumber/
  __init__.py
  entrypoint.py          # Option registration, plugin activation
  plugin.py              # AllureCucumberPlugin (rewire data source)
  hook.py                # Hook specifications (placeholder)
  adapter.py             # convert_to_allure_commons() (keep as-is)
  cli.py                 # Standalone converter (keep, deprecate docs)
  converter/
    __init__.py
    collector.py        # group_by_test_case() (keep as-is)
    converter.py        # convert() for CLI (keep as-is)
    emitter.py          # Direct JSON emission (keep for CLI)
    mapper.py           # map_test_case_to_result() (keep as-is)
    model.py            # AllureTestResult etc. (keep as-is)
    reader.py           # read_envelopes() for NDJSON (keep as-is)
```

### Pattern 1: EnvelopeCollection via hook

**What:** Plugin implements `pytest_bdd_message` to collect envelopes during execution
**When to use:** Live mode -- the default when `--allure-cucumber-output` is passed
**Example:**

```python
# Already implemented in plugin.py line 32-34
def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:
    """Collect messages for live reporting."""
    self.envelopes.append(message)
```

### Pattern 2: Session finish conversion

**What:** At `pytest_sessionfinish`, convert collected envelopes to Allure results
**When to use:** Both live and import modes
**Example:**

```python
# Current pattern in plugin.py (needs rewiring for live mode)
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(self) -> None:
    if hasattr(self.config, "workerinput"):
        return  # Skip on xdist workers
    # ... read envelopes from file or self.envelopes ...
    from pytest_bdd.plugin.allure_cucumber.adapter import convert_to_allure_commons
    convert_to_allure_commons(projections, output_path)
```

### Pattern 3: allure-python-commons lifecycle writing

**What:** Use `AllureLifecycle` and `AllureFileLogger` to write results
**When to use:** Always -- this is the mandated output backend
**Example:**

```python
# Already implemented in adapter.py
lifecycle = AllureLifecycle()
file_logger = AllureFileLogger(str(output_dir))
allure_commons.plugin_manager.register(file_logger)
try:
    for res in results:
        write_result(res, lifecycle)
    container = TestResultContainer(
        uuid=str(uuid4()), name="Test results", children=result_uuids
    )
    allure_commons.plugin_manager.hook.report_container(container=container)
finally:
    allure_commons.plugin_manager.unregister(file_logger)
```

### Anti-Patterns to Avoid

- **Reading from NDJSON file in live mode:** The current file-first approach requires the message reporter to write a consolidated file, which adds latency and complexity. Live mode should use in-memory envelopes.
- **Workers writing Allure results:** Only the controller should write Allure results in xdist mode. Workers must skip Allure output.
- **Depending on allure-pytest:** The plugin must work whether allure-pytest is installed or not. No imports from allure-pytest.
- **Using `--allure-bdd-*` option names:** Per D-14/D-15, the option names are `--allure-cucumber-output` and `--allure-cucumber-messages-in`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Allure JSON serialization | Custom JSON writer | `allure-python-commons` lifecycle/logger | Handles format consistency, attachment parenting, plugin manager integration |
| Envelope storage | Custom list/dict | `EnvelopeRegistry` in `config.stash` | Already provides stash-backed storage, identifiable object indexing |
| xdist message consolidation | Custom merge logic | `consolidate_message_fragments()` | Handles ID namespacing, deduplication, diagnostics, ordering |
| NDJSON file reading | Custom line parser | `converter.reader.read_envelopes()` | Already handles JSON parsing, envelope deserialization |
| Status mapping | Custom status converter | `_map_status()` in mapper.py | Already maps Cucumber statuses to Allure statuses |

**Key insight:** The existing codebase already provides all the building blocks. Phase 25 is primarily a rewiring exercise, not a new implementation.

## Common Pitfalls

### Pitfall 1: Using file-first path in live mode

**What goes wrong:** Plugin reads from `final_messages_file_path` instead of `self.envelopes`, requiring the message reporter to write a consolidated file even when not needed.
**Why it happens:** The current implementation was designed for NDJSON import mode as the primary path.
**How to avoid:** In live mode (no `--allure-cucumber-messages-in`), read from `self.envelopes` directly. Only read from file when in import mode.
**Warning signs:** Test runs that produce NDJSON files when only `--allure-cucumber-output` is passed.

### Pitfall 2: xdist workers writing Allure results

**What goes wrong:** Multiple workers each write their own Allure result directory, creating duplicate scenarios.
**Why it happens:** The `workerinput` check in `pytest_sessionfinish` must be correct.
**How to avoid:** Always check `hasattr(self.config, "workerinput")` and return early on workers.
**Warning signs:** Multiple `allure-results` directories or duplicate scenario names in the report.

### Pitfall 3: allure-pytest duplicate BDD results

**What goes wrong:** When `allure-pytest` is installed, both plugins write BDD results, creating duplicates.
**Why it happens:** `allure-pytest` may also implement `pytest_bdd_message` if it detects the hook.
**How to avoid:** The plugin must not import or depend on `allure-pytest`. Detection of duplicate results should be handled by not registering with allure-pytest plugin manager.
**Warning signs:** Double the expected number of scenarios in Allure HTML report.

### Pitfall 4: Import mode executing BDD scenarios

**What goes wrong:** When `--allure-cucumber-messages-in` is passed, BDD scenarios still run as source of truth.
**Why it happens:** The `pytest_collection_modifyitems` hook must clear items in import mode.
**How to avoid:** D-04 specifies narrow collection skip or early no-op when `--allure-cucumber-messages-in` is present.
**Warning signs:** BDD test functions executing when only NDJSON import is intended.

### Pitfall 5: Non-empty output directory overwrites

**What goes wrong:** Existing Allure results are silently overwritten.
**Why it happens:** No warning when output directory is non-empty.
**How to avoid:** D-13 specifies warning on non-empty directory, not automatic cleanup.
**Warning signs:** Previous results disappearing without warning.

### Pitfall 6: Live + import mode conflict

**What goes wrong:** User passes both `--allure-cucumber-output` and `--allure-cucumber-messages-in`, creating ambiguous behavior.
**Why it happens:** No validation for conflicting options.
**How to avoid:** D-05 specifies this must fail clearly with a usage error.
**Warning signs:** Unexpected behavior when both options are present.

## Code Examples

### Collecting envelopes via hook (already implemented)

```python
# Source: src/pytest_bdd/plugin/allure_cucumber/plugin.py
def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:
    """Collect messages for live reporting."""
    self.envelopes.append(message)
```

### Converting projections to Allure results (already implemented)

```python
# Source: src/pytest_bdd/plugin/allure_cucumber/adapter.py
def convert_to_allure_commons(projections, output_dir):
    grouped, structural = group_by_test_case(projections)
    results = []
    for case_id, case_projections in grouped.items():
        if case_id.startswith("run:"):
            continue
        result = map_test_case_to_result(case_id, case_projections, structural)
        results.append(result)
    if not results:
        return
    lifecycle = AllureLifecycle()
    file_logger = AllureFileLogger(str(output_dir))
    allure_commons.plugin_manager.register(file_logger)
    try:
        for res in results:
            write_result(res, lifecycle)
        container = TestResultContainer(
            uuid=str(uuid4()), name="Test results", children=result_uuids
        )
        allure_commons.plugin_manager.hook.report_container(container=container)
    finally:
        allure_commons.plugin_manager.unregister(file_logger)
```

### Reading envelopes from NDJSON file (already implemented)

```python
# Source: src/pytest_bdd/plugin/allure_cucumber/converter/reader.py
def read_envelopes(messages_path):
    with messages_path.open(encoding="utf-8") as f:
        for raw_line in f:
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue
            envelope_dict = json.loads(stripped_line)
            yield ExecutionMessageAdapter.deserialize_dict(envelope_dict)
```

### xdist worker skip (already implemented)

```python
# Source: src/pytest_bdd/plugin/allure_cucumber/plugin.py
def pytest_sessionfinish(self) -> None:
    if hasattr(self.config, "workerinput"):
        return  # Skip on xdist workers
```

### Collecting items in import mode (already implemented)

```python
# Source: src/pytest_bdd/plugin/allure_cucumber/plugin.py
def pytest_collection_modifyitems(self, items):
    if self.messages_in is not None:
        items.clear()  # Skip BDD scenario execution in import mode
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| File-first: read consolidated NDJSON at session finish | Hook-native: collect envelopes via `pytest_bdd_message` hook | Phase 25 | Eliminates dependency on message reporter file output |
| Standalone converter only | Plugin + standalone converter | Phase 20 to 21 | Plugin is now primary path; standalone converter deprecated |
| No allure-python-commons dependency | Uses allure-python-commons lifecycle/logger | Phase 25 | Writes results through standard Allure lifecycle |
| Option names `--allure-bdd-*` | Option names `--allure-cucumber-*` | Phase 25 (D-14/D-15) | Matches naming convention; `--allure-cucumber-messages` removed |

**Deprecated/outdated:**

- `--allure-cucumber-messages` option: Removed per D-16. Use `--allure-cucumber-messages-in` instead.
- Standalone converter CLI: Deprecated for primary use. Still available for compatibility.
- File-first plugin path: Replaced by hook-native path for live mode.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=7.0.0 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/cases/contract/cck/ -m contract -m not docker -m not browser` |
| Full suite command | `pytest tests/cases/contract/cck/` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-01 | pytest-native Allure plugin writes without --messages-ndjson | e2e | `pytest tests/cases/e2e/ --allure-cucumber-output` | To be created |
| REQ-02 | allure-python-commons backend | contract | `pytest tests/cases/contract/cck/ -m contract` | Exists (adapter tests) |
| REQ-03 | No allure-pytest coupling | e2e | Run with and without allure-pytest installed | To be created |
| REQ-04 | pytest_bdd_message ingestion | unit | Hook-level test emitting envelopes | To be created |
| REQ-05 | Hook compatibility full feature surface | e2e | `features/17 Allure Converter/` | Exists |
| REQ-06 | NDJSON import mode | e2e | `pytest --allure-cucumber-messages-in` | To be created |
| REQ-07 | Single ingestion pipeline golden test | contract | Compare hook vs import mode output | To be created |
| REQ-08 | xdist total report | e2e | `pytest -n 2 --allure-cucumber-output` | To be created |

### Sampling Rate

- Per task commit: Quick contract tests (no docker/browser)
- Per wave merge: Full contract + e2e tests
- Phase gate: Full suite including Docker/Playwright HTML verification

### Wave 0 Gaps

- [ ] Hook-level unit test for `pytest_bdd_message` ingestion
- [ ] NDJSON import mode e2e test
- [ ] Hook vs import golden equivalence test
- [ ] xdist total report test with `pytest -n 2`
- [ ] `allure-pytest` absent/present coexistence test
- [ ] via/socket distributed verification test

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Validate NDJSON file content before processing |
| V6 Cryptography | no | No cryptographic operations in this phase |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via NDJSON input | Tampering | Resolve and validate input path exists |
| Duplicate result injection | Tampering | Controller-only output; worker skip pattern |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | allure-python-commons version in pyproject.toml is compatible with the lifecycle API used in adapter.py | Standard Stack | Medium -- adapter may need updates if API changed |
| A2 | The existing convert_to_allure_commons() function works correctly for both live and import modes | Architecture Patterns | Low -- already tested via CCK conversion tests |
| A3 | EnvelopeRegistry is available in config.stash during pytest_sessionfinish | Architecture Patterns | Low -- registered by LifecycleService at session start |
| A4 | The workerinput attribute check correctly identifies xdist workers | Common Pitfalls | Low -- established pattern in existing code |

## Open Questions (RESOLVED)

1. **How should the strict/fail mode for consolidation diagnostics work?**
   - RESOLVED: Default to generating a partial report with a warning. Provide optional `--allure-cucumber-strict` CLI flag that raises `pytest.UsageError` on consolidation diagnostics. Agent discretion on flag name per CONTEXT.md the agent's Discretion section.

2. **Should the adapter be refactored to use allure-python-commons `allure.step` decorator?**
   - RESOLVED: No. `allure.step` is designed for test code instrumentation, not adapter-level conversion. Current manual `TestStepResult` construction in `adapter.py` is correct and should remain unchanged.

3. **How should the plugin handle the case where allure-python-commons is not installed?**
   - RESOLVED: Fail hard with a clear error message. `allure-python-commons` is a declared dependency in `pyproject.toml`. The `entrypoint.py` plugin activation should catch `ImportError` and raise `pytest.UsageError("allure-python-commons is required for Allure reporting. Install with: pip install allure-python-commons")`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| allure-python-commons | Allure result writing | Yes | in pyproject.toml | None (hard dependency) |
| Docker | CCK HTML report verification | Yes (per Phase 20) | -- | Skip Docker-marked tests |
| Playwright | Browser validation of reports | Yes (per Phase 20) | -- | Skip browser-marked tests |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:**

- Docker: CCK rendering tests skip gracefully with `require_docker_daemon()`
- Playwright: Browser tests skip gracefully when browsers not installed

## Sources

### Primary (HIGH confidence)

- `src/pytest_bdd/plugin/allure_cucumber/adapter.py` -- existing allure-python-commons integration
- `src/pytest_bdd/plugin/allure_cucumber/plugin.py` -- current plugin implementation
- `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` -- option registration
- `src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py` -- semantic mapping reference
- `src/pytest_bdd/plugin/allure_cucumber/converter/collector.py` -- test case grouping
- `src/pytest_bdd/plugin/allure_cucumber/converter/reader.py` -- NDJSON reading
- `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py` -- pytest_bdd_message hook spec
- `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py` -- message emission
- `src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py` -- xdist transport
- `src/pytest_bdd/model/message_consolidation.py` -- xdist consolidation
- `src/pytest_bdd/model/message_registry.py` -- EnvelopeRegistry
- `src/pytest_bdd/model/execution_message_adapter.py` -- ExecutionProjection
- Context7 `/allure-framework/allure-python` -- allure-python-commons lifecycle API

### Secondary (MEDIUM confidence)

- `25-CONTEXT.md` -- locked decisions D-01 through D-22
- `25-SPEC.md` -- locked requirements 1-8
- `tests/cases/contract/cck/` -- existing CCK test patterns

### Tertiary (LOW confidence)

- None -- all findings verified against source code

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH -- all libraries already in pyproject.toml, adapter.py confirmed working
- Architecture: HIGH -- data flow traced through source code; existing patterns are reusable
- Pitfalls: HIGH -- derived from actual code analysis and existing test patterns

**Research date:** 2026-06-13
**Valid until:** 2026-07-13 (30 days for stable domain)
