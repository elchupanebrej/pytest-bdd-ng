---
phase: 20-docs-architecture-allure-md
plan: 04b
type: execute
wave: 4
depends_on:
  - 20-04a
files_modified:
  - tests/cases/contract/allure/test_cli_contract.py
  - tests/cases/contract/allure/test_converter_contract.py
  - tests/cases/contract/allure/test_golden_parity.py
  - tests/cases/contract/allure/test_hypothesis.py
  - tests/cases/integration/allure/__init__.py
  - tests/cases/integration/allure/conftest.py
  - tests/cases/integration/allure/test_plugin.py
autonomous: true
requirements:
  - REQ-05
  - REQ-09
  - REQ-02
  - REQ-04
  - REQ-01
  - REQ-07
  - REQ-08

must_haves:
  truths:
    - "Contract test for CLI registration passes: allure-cucumber registered in pyproject.toml scripts"
    - "Converter contract test passes: TestCase→TestResult mapping, unmappable→attachments, labels present"
    - "Golden parity test passes: known NDJSON → expected output structure with specific content fields"
    - "Property-based test passes: hypothesis verifies 'any valid cucumber message NDJSON produces valid Allure JSON or documented error'"
    - "Plugin integration test passes: pytest_sessionfinish triggers converter and produces output files"
  artifacts:
    - path: "tests/cases/contract/allure/test_cli_contract.py"
      provides: "CLI contract test: registration, --help, nonexistent file error, valid input success"
      exports: ["test_cli_registered_in_pyproject", "test_cli_help_exits_zero", "test_cli_nonexistent_file_exits_one"]
    - path: "tests/cases/contract/allure/test_converter_contract.py"
      provides: "Converter contract: TestCase→TestResult count, unmappable→attachments, labels"
      exports: ["test_test_case_started_creates_result", "test_unmappable_events_produce_attachments", "test_result_contains_labels"]
    - path: "tests/cases/contract/allure/test_golden_parity.py"
      provides: "Golden file parity: known NDJSON → expected Allure JSON structure (specific fields, not exact UUIDs)"
      exports: ["test_minimal_scenario_golden", "test_container_references_children"]
    - path: "tests/cases/contract/allure/test_hypothesis.py"
      provides: "Property-based invariant: any valid NDJSON → valid Allure JSON or documented error"
      exports: ["test_any_valid_ndjson_produces_valid_allure", "test_schema_invariant"]
    - path: "tests/cases/integration/allure/test_plugin.py"
      provides: "Integration test: pytest with --allure-cucumber-output produces results"
      exports: ["test_plugin_sessionfinish_emits_results", "test_plugin_respects_ini_config"]
  key_links:
    - from: "tests/cases/contract/allure/test_hypothesis.py"
      to: "converter/__init__.py"
      via: "hypothesis strategies generate NDJSON → convert() → jsonschema.validate"
      pattern: "from hypothesis import given"
    - from: "tests/cases/integration/allure/test_plugin.py"
      to: "allure_cucumber/plugin.py"
      via: "testdir runs pytest with --allure-cucumber-output"
      pattern: "--allure-cucumber-output"
---

<objective>
Contract, integration, and property-based tests: CLI contract verification, converter mapping contracts, golden file parity, hypothesis property-based invariants, and real pytest plugin integration tests. Builds on the unit test infrastructure and shared fixtures created in Plan 04a.

Purpose: Contract tests verify structural guarantees (CLI registration, converter behavior). Golden parity proves output correctness against known inputs. Hypothesis property-based testing catches edge cases no human would think of. Integration tests verify the real pytest plugin lifecycle.

Output: 5 contract test files under tests/cases/contract/allure/ and 2 integration test files under tests/cases/integration/allure/.
</objective>

<execution_context>
@C:/Users/bulky/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/bulky/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/20-docs-architecture-allure-md/20-RESEARCH.md
@.planning/phases/20-docs-architecture-allure-md/20-PATTERNS.md
@.planning/phases/20-docs-architecture-allure-md/20-VALIDATION.md
@docs/architecture/allure.md
@AGENTS.md

<interfaces>
Plan 04a delivers (already importable and tested):
```python
# Shared fixtures from tests/cases/contract/allure/conftest.py
#   allure_schema_path: Path  — resolves docs/allure3-events.schema.json
#   sample_ndjson: Path       — minimal valid NDJSON
#   sample_ndjson_multi_case: Path — 2 test cases
#   sample_ndjson_with_attachment: Path — includes Attachment event
#   converter_output_dir: Path — allure-results subdir under tmp_path

# converter pipeline (fully implemented by Plans 01-02)
from pytest_bdd.plugin.allure_cucumber.converter import convert
from pytest_bdd.plugin.allure_cucumber.converter.reader import read_envelopes
from pytest_bdd.plugin.allure_cucumber.converter.collector import group_by_test_case
from pytest_bdd.plugin.allure_cucumber.converter.step_tree import build_step_tree
from pytest_bdd.plugin.allure_cucumber.converter.mapper import map_test_case_to_result, map_unmappable_to_attachment
from pytest_bdd.plugin.allure_cucumber.converter.emitter import emit_results, emit_container
from pytest_bdd.plugin.allure_cucumber.converter.model import AllureTestResult, AllureStepResult, AllureAttachment, AllureContainer

# plugin + CLI (Plan 03)
from pytest_bdd.plugin.allure_cucumber.plugin import AllureCucumberPlugin
from pytest_bdd.plugin.allure_cucumber.cli import main
from pytest_bdd.plugin.allure_cucumber.entrypoint import allure_cucumber_plugin

# factoryboy and hypothesis available (installed by Plan 04a)
```

Existing test patterns to replicate:
```python
# tests/cases/contract/contract/ — contract test patterns (pyproject.toml validation, subprocess CLI tests)
# tests/cases/integration/ — integration test patterns (testdir.makefile, testdir.runpytest_subprocess)
# tests/cases/contract/messages_coverage/ — hypothesis usage patterns
```

RESEARCH.md lines 440-449: property-based test spec: "any valid NDJSON → valid Allure JSON or documented error"
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Create CLI contract, converter contract, and golden parity tests</name>
  <files>
    tests/cases/contract/allure/test_cli_contract.py
    tests/cases/contract/allure/test_converter_contract.py
    tests/cases/contract/allure/test_golden_parity.py
  </files>
  <read_first>
    - tests/cases/contract/contract/test_cucumber_formatter_cli_contract.py (contract test pattern — pyproject.toml validation, CLI contract)
    - tests/cases/contract/allure/conftest.py (shared fixtures: sample_ndjson, allure_schema_path, converter_output_dir)
    - .planning/phases/20-docs-architecture-allure-md/20-PATTERNS.md (lines 775-813 — contract test patterns: plugin structure, schema validation, CLI contract, golden parity)
    - src/pytest_bdd/plugin/allure_cucumber/cli.py (main, parse_args — to test via subprocess)
    - src/pytest_bdd/plugin/allure_cucumber/converter/__init__.py (convert — to test mapping contracts)
  </read_first>
  <behavior>
    - test_cli_contract: allure-cucumber entry exists in pyproject.toml [project.scripts]; CLI --help exits 0; CLI with nonexistent file exits 1; CLI with valid NDJSON succeeds and emits files
    - test_converter_contract: Each TestCaseStarted in NDJSON produces one TestResult; unmappable events produce attachments (not silently dropped); results contain feature/suite labels
    - test_golden_parity: Known minimal NDJSON → specific output structure (name, status, step count, step names); container.children references match result UUIDs
  </behavior>
  <action>
    Create 3 contract test files:

    **test_cli_contract.py** (new, PATTERNS.md lines 775-813):
    - `test_cli_registered_in_pyproject`: loads pyproject.toml, asserts "allure-cucumber" in [project.scripts].
    - `test_cli_help_exits_zero`: runs `subprocess.run([sys.executable, "-m", "pytest_bdd.plugin.allure_cucumber.cli", "--help"])`, asserts returncode == 0 and output contains "usage" or "Convert".
    - `test_cli_nonexistent_file_exits_one`: runs CLI with a nonexistent NDJSON path, asserts returncode == 1.
    - `test_cli_valid_ndjson_succeeds`: runs CLI with sample_ndjson fixture and --output to tmp_path, asserts returncode == 0 and output files exist.
    Import: `subprocess`, `sys`, `pathlib.Path`, `tomllib` (or `pytest_bdd.compatibility.tomllib.loads`).

    **test_converter_contract.py** (new, PATTERNS.md lines 775-813):
    - `test_test_case_started_creates_result`: verifies that each TestCaseStarted in NDJSON produces one TestResult in output.
    - `test_unmappable_events_produce_attachments`: creates NDJSON with an unknown event type, runs convert, verifies the result has attachments.
    - `test_result_contains_labels`: verifies TestResult has feature/suite labels derived from test case name.
    Import: convert, json, pathlib, allure_schema_path fixture.

    **test_golden_parity.py** (new):
    - Define inline expected structure for a known "minimal scenario" NDJSON (one test case, one step, passed).
    - `test_minimal_scenario_golden`: Create NDJSON, run convert, load output, assert: result["name"] matches expected, result["status"] == "passed", len(result["steps"]) == 1, result["steps"][0]["name"] matches step name.
    - `test_container_references_children`: Create multi-case NDJSON (sample_ndjson_multi_case fixture), run convert, verify container.children has exactly the UUIDs of the result files.
    Import: convert, json, pathlib.

    All test files use `from __future__ import annotations` and appropriate `pytestmark` (pytest.mark.contract).
  </action>
  <verify>
    <automated>uv run pytest tests/cases/contract/allure/test_cli_contract.py tests/cases/contract/allure/test_converter_contract.py tests/cases/contract/allure/test_golden_parity.py -x -v</automated>
  </verify>
  <done>CLI contract: registration, help, error handling, and valid input all verified. Converter contract: TestCase→TestResult mapping, unmappable→attachments, labels present. Golden parity: known NDJSON produces expected output structure with specific content fields and correct container references.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create hypothesis property-based test and integration test</name>
  <files>
    tests/cases/contract/allure/test_hypothesis.py
    tests/cases/integration/allure/__init__.py
    tests/cases/integration/allure/conftest.py
    tests/cases/integration/allure/test_plugin.py
  </files>
  <read_first>
    - tests/cases/contract/messages/test_messages_feature_suite.py (contract test patterns for message handling)
    - tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py (integration test with testdir pattern)
    - tests/cases/contract/allure/conftest.py (shared fixtures: sample_ndjson, allure_schema_path, converter_output_dir)
    - .planning/phases/20-docs-architecture-allure-md/20-PATTERNS.md (lines 817-861 — integration test patterns: test_plugin with testdir)
    - .planning/phases/20-docs-architecture-allure-md/20-RESEARCH.md (lines 440-449 — property-based test: "any valid NDJSON → valid Allure JSON or documented error")
    - src/pytest_bdd/plugin/allure_cucumber/entrypoint.py (pytest_addoption, pytest_configure — to verify from testdir)
  </read_first>
  <behavior>
    - test_hypothesis: @given valid NDJSON strategy, convert() produces output that validates against schema OR raises documented exception (never crashes silently)
    - test_plugin: pytest with --allure-cucumber-output creates output dir with result files; plugin respects INI config; plugin skips registration on xdist workers
  </behavior>
  <action>
    Create 2 test files plus integration directory scaffold:

    **test_hypothesis.py** (new):
    - `test_any_valid_ndjson_produces_valid_allure`: Use `@given(valid_ndjson_strategy())` from hypothesis. The strategy generates valid NDJSON strings (list of valid cucumber message envelope dicts, each as a JSON line). The test: write to tmp_path, call convert(), load output JSON files, validate each against schema. If convert() raises ValueError (malformed JSON in reader), that's acceptable — catch and assert isinstance of exception. If convert() raises something else unexpected, fail the test.
    - Define `valid_ndjson_strategy()`: uses `hypothesis.strategies.lists()` of envelope dicts built with `hypothesis.strategies.fixed_dictionaries()` for required message types. Start simple: generate sequences with testRunStarted, 1+ testCaseStarted/Finished pairs with 1+ testStepStarted/Finished pairs each, testRunFinished. Use `assume()` to enforce ordering (no Finished before Started).
    - `test_schema_invariant`: @given any valid TestResult dict (generated by hypothesis from schema), validate → no error.
    Import: `hypothesis` (given, strategies, assume, settings), `jsonschema`, `json`, `pytest`.

    **tests/cases/integration/allure/__init__.py**: Empty file.

    **tests/cases/integration/allure/conftest.py**: Create with `from __future__ import annotations`, `pytestmark = [pytest.mark.integration]`.

    **test_plugin.py** (integration, new, PATTERNS.md lines 817-861):
    - `test_plugin_sessionfinish_emits_results(testdir, tmp_path)`: Uses pytester pattern. Create a .feature file and conftest with step definition. Run pytest with `--allure-cucumber-output` pointing to tmp_path. Assert result.assert_outcomes(passed=1). Verify output_dir exists and contains at least one JSON file.
    - `test_plugin_respects_ini_config(testdir, tmp_path)`: Set INI option `allure_cucumber_output_dir` in testdir's config. Run pytest without CLI flag. Verify output appears in the INI-specified directory.
    Import: `pathlib.Path`, `pytest`.

    All test files use `from __future__ import annotations` and appropriate `pytestmark`.
  </action>
  <verify>
    <automated>uv run pytest tests/cases/contract/allure/test_hypothesis.py tests/cases/integration/allure/ -x -v</automated>
  </verify>
  <done>Hypothesis property-based test passes: any valid NDJSON produces valid Allure JSON or documented ValueError. Schema invariant verified. Plugin integration test passes: real pytest session with --allure-cucumber-output produces result files; INI config respected.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| hypothesis generated NDJSON → convert() | Property-based testing generates arbitrary valid NDJSON — must handle unexpected but valid input gracefully |
| testdir subprocess → plugin | pytester isolates plugin under test in subprocess — trusted test boundary |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-20-10 | Denial of Service | hypothesis test generation | accept | hypothesis settings limit max examples (default 100); test timeout via pytest-timeout (already in test deps) |

</threat_model>

<verification>
After Plan 04b completes, verify:
```bash
# Contract tests (CLI, converter, golden)
uv run pytest tests/cases/contract/allure/test_cli_contract.py tests/cases/contract/allure/test_converter_contract.py tests/cases/contract/allure/test_golden_parity.py -x -v

# Hypothesis property-based test
uv run pytest tests/cases/contract/allure/test_hypothesis.py -x -v

# Integration tests
uv run pytest tests/cases/integration/allure/ -x -v

# All allure tests
uv run pytest tests/cases/ -k "allure" -x -v
```
</verification>

<success_criteria>
- [ ] CLI contract test passes: allure-cucumber registered, help works, error handling works
- [ ] Converter contract test passes: TestCase→TestResult mapping, unmappable→attachments, labels
- [ ] Golden parity test passes: known NDJSON → expected output structure
- [ ] Hypothesis property-based test passes: any valid NDJSON → valid Allure or documented error
- [ ] Plugin integration test passes: real pytest session with plugin produces output files; INI config works
- [ ] No regressions in existing test suite
- [ ] All new tests follow test group conventions (path-based auto-assignment)
</success_criteria>

<output>
Create `.planning/phases/20-docs-architecture-allure-md/20-04b-SUMMARY.md` when done
</output>
