---
last_mapped_commit: c59470a9bc50f5ae0f628a572832a5b614d862a7
mapped_at: 2026-05-12
focus: quality
---

# Testing Patterns

**Analysis Date:** 2026-05-12

## Test Framework

**Runner:**
- `pytest` (>=7.0.0) with `pytester` plugin enabled by default.
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`.
- `tox` for matrix testing across Python 3.10-3.14 × pytest 7.0-latest.

**Assertion Library:**
- Vanilla `assert` statements (pytest native).
- `PyHamcrest` used in allure-specific tests (`tests/e2e/allure/conftest.py`): `assert_that()`, `has_entry()`, `has_item()`, `equal_to()`.

**Run Commands:**
```bash
uv run pytest tests/ -q                    # Run all tests (quick)
uv run pytest tests/ -x                    # Stop on first failure
uv run pytest tests/unit/                  # Run specific test directory
uv run python -m pytest tests/ -q          # Using python -m
uvx --with tox-uv tox -l                   # List tox environments
uvx --with tox-uv tox                      # Run full tox matrix
make test                                  # Run tox + render HTML reports
```

**Coverage:**
```bash
uv run pytest tests/ --cov=pytest_bdd --cov-report=html
```
Config: `.coveragerc` — branch coverage enabled, includes `pytest_bdd/*` and `tests/*`.

## Test File Organization

**Location:**
- All tests under `tests/` directory, organized by type into subdirectories.
- Tests are **not** co-located with source code — separate `tests/` tree mirrors source structure conceptually.

**Naming:**
- Test files: `test_*.py` (e.g., `test_collector_batch.py`, `test_steps.py`).
- Tests for specific source modules: `tests/unit/test_collector_batch.py` tests `src/pytest_bdd/collector_batch.py`.

**Structure:**
```
tests/
├── __init__.py               # Module docstring only
├── conftest.py               # Shared fixtures: group ordering, test parameterization
├── unit/                     # Unit tests (fast, no I/O)
│   ├── test_collector_batch.py
│   ├── test_gherkin_go_parse.py
│   ├── test_gherkin_go_fallback.py
│   ├── test_gherkin_go_bridge.py
│   ├── test_group_ordering.py
│   ├── test_performance_batch.py
│   └── test_threshold_finder.py
├── model/                    # Model-level unit tests
│   ├── gherkin_document/
│   │   └── test_feature_context_lookup.py
│   └── test_cucumber_formatter_adapter.py
├── feature/                  # Integration tests (testdir-based)
│   ├── test_steps.py
│   ├── test_outline.py
│   ├── test_autoload.py
│   ├── test_report.py
│   ├── test_cucumber_json.py
│   ├── test_run_lifecycle.py
│   └── ...
├── e2e/                      # End-to-end tests
│   ├── conftest.py           # BDD step definitions for feature files
│   ├── test_e2e.py           # Entry point: scenarios(".", ...)
│   ├── test_xdist_message_aggregation.py
│   ├── test_cucumber_formatters.py
│   ├── allure/
│   │   ├── conftest.py
│   │   └── test_e2e_allure.py
│   └── fixtures/
│       └── remote_xdist/     # Docker compose fixtures for remote xdist tests
├── hook/                     # Hook lifecycle tests
│   ├── test_hooks.py         (actually at tests/test_hooks.py)
├── steps/                    # Step definition tests
│   ├── test_given.py
│   └── test_unicode.py
├── args/                     # Argument matching tests
│   ├── regex/test_args.py
│   ├── parse_/test_args.py
│   ├── cucumber_expression/test_args.py
│   └── cfparse/test_args.py
├── struct_bdd/               # StructBDD (YAML/JSON/HOCON) tests
│   ├── test_steps.py
│   └── test_deserialization.py
├── generation/               # Code generation tests
│   ├── test_generate.py
│   └── test_template_packaging.py
├── messages/                 # Cucumber Messages protocol tests
│   ├── test_messages_feature_suite.py
│   └── test_message_typing_regression.py
├── messages_coverage/        # Message coverage probes
│   ├── conftest.py
│   ├── test_mandatory_attachments.py
│   ├── test_run_governance_regression.py
│   ├── test_full_capability_governance.py
│   └── probes/
│       ├── test_undefined_parameter_runtime.py
│       ├── test_parse_error_runtime.py
│       └── test_failing_step_runtime.py
├── compatibility/            # Compatibility matrix validation tests
│   ├── test_public_api_exports.py
│   ├── test_matrix_rules.py
│   └── ...
├── support/                  # Test support utilities (not tests)
│   ├── cucumber_formatters.py
│   ├── docker.py
│   ├── docker_cluster.py
│   └── pytest_results.py
├── scripts/                  # Script tests
│   └── test_sync_messages_contract_schemas.py
└── library/                  # Library-level tests
```

## Test Structure

**Suite Organization:**

Unit tests are simple functions with descriptive names and inline setup:
```python
def test_register_appends_and_returns_count() -> None:
    parser = FeatureBatchParser()
    count = parser.register(Path("/fake/file1.feature"))
    assert count == 1
    count = parser.register(Path("/fake/file2.feature"))
    assert count == 2
    assert len(parser._pending) == 2
```

Integration tests (testdir-based) follow a three-phase pattern — arrange (write files), act (run pytest), assert (check outcomes):
```python
def test_steps(testdir):
    """Verify steps."""
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Steps are executed one by one
            Scenario: Executed step by step
                Given I have a foo fixture with value "foo"
                ...
    """,
    )
    testdir.makeconftest("""\
        from pytest_bdd import given, when, then
        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"
        ...
    """)
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)
```

**Patterns:**
- **Setup:** Inline file creation via `testdir.makefile()`, `testdir.makeconftest()`, or direct `tmp_path` writes. Parametrized fixtures for data-driven tests.
- **Teardown:** Relies on pytest fixture cleanup (`tmp_path`, `testdir` auto-cleanup). No explicit teardown in most tests.
- **Assertion pattern:** Simple `assert` statements with descriptive failure messages:
  ```python
  assert result.returncode == 0, result.stdout + "\n" + result.stderr
  assert validation_result.status == "pass"
  assert payload_counts["meta"] == 1
  ```

## Mocking

**Framework:** `unittest.mock` (stdlib). Used sparingly — primarily for:
- Patching Go parser availability in `tests/unit/test_gherkin_go_*.py`:
  ```python
  from unittest.mock import patch

  with (
      patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=True),
      patch("pytest_bdd._gherkin_go.parse_gherkin_document", return_value=VALID_GHERKIN_DOCUMENT),
  ):
      result = parse("Feature: Test", mimetype=Mimetype.gherkin_plain)
  ```
- Allure plugin mocking in `tests/e2e/allure/conftest.py`:
  ```python
  from unittest import mock

  with mock.patch(path) as reporter_mock:
      reporter_mock.return_value = logger
      yield
  ```
- `unittest.mock.MagicMock` and `unittest.mock.Mock` used sparingly in a few tests.

**What to Mock:**
- External/native library availability (Go shared library).
- Plugin registrations (Allure).
- Network-dependent behavior.

**What NOT to Mock:**
- Internal pytest-bdd components (prefer integration tests via `testdir`).
- `cucumber_messages` models (use real `GherkinDocument`, `Pickle`, etc. via factories).
- pytest itself (use real `testdir.runpytest()` / `testdir.runpytest_inprocess()`).

## Fixtures and Factories

**Test Data:**

Model-level tests use factory functions for constructing message objects:
```python
def _build_gherkin_document() -> GherkinDocument:
    scenario_step = Step(
        id="ast-step-1",
        keyword="Given ",
        location=Location(line=3, column=1),
        text="a step",
    )
    scenario_node = Scenario(...)
    return GherkinDocument(comments=[], feature=feature_message, uri="file:features/example.feature")
```

Integration tests use inline multi-line string content with `# language=gherkin` comments:
```python
testdir.makefile(
    ".feature",
    # language=gherkin
    steps="""\
        Feature: Steps are executed one by one
            Scenario: Executed step by step
                Given I have a foo fixture with value "foo"
    """,
)
```

**Location:**
- Test data is inline in test files rather than in separate fixture files.
- The `tests/support/` directory provides shared test utilities (`pytest_results.py`, `docker.py`, `cucumber_formatters.py`).

## Coverage

**Requirements:** None explicitly enforced. Config exists in `.coveragerc`:
```ini
[run]
branch = true
include =
    pytest_bdd/*
    tests/*
```

**View Coverage:**
```bash
uv run python -m pytest tests/ --cov=pytest_bdd --cov-report=html
```

## Test Types

**Unit Tests:**
- Location: `tests/unit/`, `tests/model/`
- Scope: Single function/class behavior, no filesystem I/O.
- Group: `instant` (fastest, runs first).
- Approach: Direct instantiation of classes under test; `Path("/fake/...")` for path-like arguments.
- Example: `tests/unit/test_collector_batch.py` — tests `FeatureBatchParser` state machine without real files.

**Integration Tests (testdir-based):**
- Location: `tests/feature/`
- Scope: End-to-end pytest-bdd workflow within a test directory (creates `.feature` files, conftest, runs `pytest`).
- Group: `medium`.
- Approach: Uses `testdir` fixture from `pytester` plugin. Creates feature files and step definitions, runs pytest via `testdir.runpytest()`, asserts outcomes.
- Example: `tests/feature/test_steps.py` — verifies step execution ordering, fixture injection, parametrized steps.

**Hook Tests:**
- Location: `tests/test_hooks.py`
- Scope: pytest hook integration (e.g., `pytest_pyfunc_call`, `pytest_generate_tests`).
- Approach: Writes conftest with custom hooks into `testdir`, verifies hook invocation counts and effects.
- Example: `tests/test_hooks.py::test_item_collection_does_not_break_on_non_function_items` — regression test for custom `pytest.Item` subclasses.

**E2E Tests:**
- Location: `tests/e2e/`
- Scope: Full end-to-end BDD scenarios, Docker/xdist integration, formatter output validation.
- Group: `external` (slowest, runs last or excluded by default).
- Approach: Uses `scenarios(".", filter_=...)` to load feature files from `features/` directory. Step definitions in `tests/e2e/conftest.py` map Gherkin steps to test actions (run pytest subprocess, check outputs).
- Example: `tests/e2e/test_e2e.py` — loads all feature files with tag-based filtering; `tests/e2e/conftest.py` — 470 lines of step definitions covering file creation, pytest execution, output assertions.

**Model Tests:**
- Location: `tests/model/`
- Scope: Data model correctness (stash access, message conversion, registry lookups).
- Group: `instant`.
- Approach: Direct instantiation of model objects, no testdir. Uses `SimpleNamespace` for mock config.
- Example: `tests/model/gherkin_document/test_feature_context_lookup.py` — tests `Run.ensure_feature_binding()` with hand-crafted `GherkinDocument` objects.

**Messages Coverage Tests:**
- Location: `tests/messages_coverage/`
- Scope: Cucumber Messages protocol compliance — validates that all message types are emitted, governance rules pass.
- Group: `slow`.
- Approach: Probes exercise specific runtime paths (parse errors, step failures, undefined parameters) and verify NDJSON message streams.
- Example: `tests/messages_coverage/probes/test_failing_step_runtime.py` — exercises step failure to verify `TestStepFinished` emission.

**StructBDD Tests:**
- Location: `tests/struct_bdd/`
- Scope: YAML/JSON/HOCON/TOML-based BDD feature parsing.
- Group: `medium`.
- Conditionally skipped if `STRUCT_BDD_INSTALLED` is `False`.

## Common Patterns

**Parametrized Tests:**
```python
@pytest.mark.parametrize(
    "pickle_path",
    (pytest.param(file, id=file.name) for file in (test_data / "good").glob("*.pickles.ndjson")),
)
def test_simple_load_pickle(pickle_path: Path): ...


@pytest.mark.parametrize("mapping_string", ["{...: None}", "False", "()"])
def test_disallow_mapping(mapping_string: str): ...
```

**Error Testing:**
```python
def test_register_after_flush_raises() -> None:
    parser = FeatureBatchParser()
    parser.register(Path("/fake/file.feature"))
    parser.flush()
    with pytest.raises(RuntimeError, match="flushed"):
        parser.register(Path("/fake/file2.feature"))


def test_raises_on_parse_error(self) -> None:
    with (
        patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=True),
        patch("pytest_bdd._gherkin_go.parse_gherkin_document", return_value=PARSE_ERROR_ARRAY),
    ):
        with pytest.raises(GherkinParseError, match="Parse error"):
            parse("invalid", mimetype=Mimetype.gherkin_plain)
```

**Conditional/Platform-Specific Skipping:**
```python
# Module-level pytestmark for conditional skip
pytestmark = [pytest.mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed")]

# Inline skip
if jq is None:
    pytest.skip("jq package is unavailable on this platform")
```

**Test Marker Assignment (Test Groups):**
Markers declared in `pyproject.toml` (`[tool.pytest.ini_options].markers`). Group ordering configured via:
```python
test_group_default = "fast"
test_group_order = ["instant", "fast", "medium", "slow", "external"]
test_group_paths = [
    "tests/unit/** = instant",
    "tests/model/** = instant",
    "tests/args/** = fast",
    "tests/hook/** = fast",
    "tests/steps/** = fast",
    "tests/feature/** = medium",
    ...
    "tests/e2e/** = external"
]
```
File-level markers override via `pytestmark`:
```python
pytestmark = pytest.mark.slow
pytestmark = [pytest.mark.xdist, pytest.mark.docker, pytest.mark.slow]
```

**Test Output Assertions:**
- `result.assert_outcomes(passed=1, failed=0)` — standard pytester assertion.
- `result.stdout.fnmatch_lines("*ExpectedPattern*")` — glob-style line matching.
- `result.returncode == pytest.ExitCode.TESTS_FAILED` — exit code checking.
- `assert "expected text" in output_path.read_text()` — raw file content checks.
- Hand-rolled `_parse_outcome_counts()` for environments where `.assert_outcomes()` is unavailable.

**Async Testing:**
- Not used. No `async def test_*` functions detected in the test suite other than plugin test scenarios using `testdir`.

---

*Testing analysis: 2026-05-12*
