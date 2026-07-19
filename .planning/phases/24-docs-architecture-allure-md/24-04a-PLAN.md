---
phase: 24-docs-architecture-allure-md
plan: 04a
type: execute
wave: 4
depends_on:
  - 24-03
files_modified:
  - pyproject.toml
  - tests/cases/unit/allure/__init__.py
  - tests/cases/unit/allure/conftest.py
  - tests/cases/contract/allure/conftest.py
  - tests/cases/unit/allure/test_reader.py
  - tests/cases/unit/allure/test_collector.py
  - tests/cases/unit/allure/test_step_tree.py
  - tests/cases/unit/allure/test_mapper.py
  - tests/cases/unit/allure/test_emitter.py
  - tests/cases/unit/allure/test_converter_e2e.py
  - tests/cases/contract/allure/test_schema_validation.py
autonomous: false
requirements:
  - REQ-05
  - REQ-02
  - REQ-04
  - REQ-01
user_setup:
  - service: factoryboy+hypothesis packages
    why: "Test fixture generation and property-based testing for Layer 1 validation"
    env_vars: []
    dashboard_config: []
    note: "Both are well-established PyPI packages (~10yrs, ~10M+ downloads/month). Needs manual verification before pip install per Package Legitimacy Gate."

must_haves:
  truths:
    - "All unit tests for converter internals pass: test_reader, test_collector, test_step_tree, test_mapper, test_emitter, test_converter_e2e"
    - "Schema validation contract test passes: output validates against allure3-events.schema.json"
    - "factoryboy and hypothesis added to test extra and importable"
  artifacts:
    - path: "tests/cases/unit/allure/test_reader.py"
      provides: "Unit tests for NDJSON reading: valid JSON, empty lines, malformed JSON, single/multi envelope"
      exports: ["TestReader"]
    - path: "tests/cases/unit/allure/test_collector.py"
      provides: "Unit tests for event grouping: multi-case, no-ID events, snake/camel case attribute names"
      exports: ["TestCollector"]
    - path: "tests/cases/unit/allure/test_step_tree.py"
      provides: "Unit tests for hierarchy: single step, siblings, nested, hooks, background, empty"
      exports: ["TestStepTree"]
    - path: "tests/cases/unit/allure/test_mapper.py"
      provides: "Unit tests for mapping: TestCase→TestResult, unmappable→attachment, status mapping"
      exports: ["TestMapper"]
    - path: "tests/cases/unit/allure/test_emitter.py"
      provides: "Unit tests for emission: file creation, JSON validity, container children"
      exports: ["TestEmitter"]
    - path: "tests/cases/unit/allure/test_converter_e2e.py"
      provides: "End-to-end test: NDJSON → output files"
      exports: ["TestConverterE2E"]
    - path: "tests/cases/contract/allure/test_schema_validation.py"
      provides: "Contract test: jsonschema validation of output against canonical schema"
      exports: ["test_output_validates_against_schema"]
  key_links:
    - from: "tests/cases/unit/allure/test_reader.py"
      to: "converter/reader.py"
      via: "imports read_envelopes"
      pattern: "from pytest_bdd.plugin.allure_cucumber.converter.reader import read_envelopes"
    - from: "tests/cases/contract/allure/test_schema_validation.py"
      to: "docs/allure3-events.schema.json"
      via: "jsonschema.validate()"
      pattern: "allure3-events.schema.json"
---

<objective>
Test infrastructure setup and unit tests for converter internals: add test dependencies (factoryboy, hypothesis), create shared fixtures, and implement comprehensive unit tests plus schema validation contract test.

Purpose: Validate every component of the converter pipeline independently. Schema validation proves output correctness. This plan establishes the test infrastructure that Plan 04b (contract/integration/hypothesis tests) builds upon.

Output: pyproject.toml updated with test extras, shared conftest fixtures, 6 unit test files, extended schema validation contract test.
</objective>

<execution_context>
@C:/Users/bulky/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/bulky/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/24-docs-architecture-allure-md/24-RESEARCH.md
@.planning/phases/24-docs-architecture-allure-md/24-PATTERNS.md
@.planning/phases/24-docs-architecture-allure-md/24-VALIDATION.md
@docs/architecture/allure.md
@AGENTS.md

<interfaces>
Plans 01-03 deliver (already importable):
```python
# converter pipeline
from pytest_bdd.plugin.allure_cucumber.converter import convert
from pytest_bdd.plugin.allure_cucumber.converter.reader import read_envelopes
from pytest_bdd.plugin.allure_cucumber.converter.collector import group_by_test_case
from pytest_bdd.plugin.allure_cucumber.converter.step_tree import build_step_tree
from pytest_bdd.plugin.allure_cucumber.converter.mapper import map_test_case_to_result, map_unmappable_to_attachment
from pytest_bdd.plugin.allure_cucumber.converter.emitter import emit_results, emit_container
from pytest_bdd.plugin.allure_cucumber.converter.model import AllureTestResult, AllureStepResult, AllureAttachment, AllureContainer

# plugin
from pytest_bdd.plugin.allure_cucumber.plugin import AllureCucumberPlugin
from pytest_bdd.plugin.allure_cucumber.entrypoint import allure_cucumber_plugin

# adapter
from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter, ExecutionProjection
```

Existing test patterns to replicate:
```python
# tests/cases/unit/unit/ — existing unit test patterns (from __future__, pytestmark = [pytest.mark.unit])
# tests/cases/contract/contract/ — contract test patterns (SimpleNamespace mocks, pyproject.toml validation, pytest.raises)
```

RESEARCH.md Open Question #4: factoryboy and hypothesis go in `test` extra (not a new extra) since they're general-purpose testing tools.
</interfaces>
</context>

<tasks>

<task type="checkpoint:human-verify" gate="blocking-human">
  <name>Task 0: Verify factoryboy and hypothesis packages before install</name>
  <files></files>
  <action>The test plan requires adding `factory-boy` and `hypothesis` to the `test` extra in pyproject.toml. Both packages are tagged [ASSUMED] in the Package Legitimacy Audit (RESEARCH.md lines 72-86) — slopcheck was not available at research time. Before installing, the human must verify both packages on PyPI are legitimate (not typosquats). The agent will not proceed until the human approves.</action>
  <verify>
    <automated>MISSING — manual verification required (checkpoint)</automated>
    <human-check>
      1. Open https://pypi.org/project/factory-boy/ — verify this is the legitimate `factory_boy` package (not a typosquat). Check: maintainer is `rbarrois` or FactoryBoy org, project age >10 years, recent downloads.
      2. Open https://pypi.org/project/hypothesis/ — verify this is the legitimate `hypothesis` package (not a typosquat). Check: maintainer is `DRMacIver` or HypothesisWorks org, project age >10 years, recent downloads.
      3. If both look legitimate, type "approved" to proceed with installation.
      4. If either looks suspicious, type the package name and concern.
    </human-check>
  </verify>
  <done>Human has verified factoryboy and hypothesis package legitimacy on PyPI; agent proceeds to Task 1 to add deps to pyproject.toml and install.</done>
</task>

<task type="auto">
  <name>Task 1: Add test dependencies and create shared fixtures</name>
  <files>
    pyproject.toml
    tests/cases/unit/allure/conftest.py
    tests/cases/contract/allure/conftest.py
  </files>
  <read_first>
    - pyproject.toml (lines 136-150 — [project.optional-dependencies] test extra: existing deps list ending with pytest-bdd-ng[doc-gen])
    - tests/cases/contract/allure/conftest.py (current state from Plan 01 — allure_schema_path fixture)
    - .planning/phases/24-docs-architecture-allure-md/24-PATTERNS.md (lines 866-905 — conftest.py fixture patterns: sample_ndjson fixture, allure_schema_path fixture, collect_ignore_glob)
    - .planning/phases/24-docs-architecture-allure-md/24-RESEARCH.md (lines 468-471 — Open Question #4: add to test extra, not new extra)
    - tests/cases/contract/messages_coverage/conftest.py (existing fixture pattern with collect_ignore_glob)
    - tests/cases/contract/contract/test_cucumber_formatter_cli_contract.py (contract test imports and patterns)
  </read_first>
  <action>
    **pyproject.toml**: Add `"factory-boy"` and `"hypothesis"` to the `test` extra in `[project.optional-dependencies]`. Insert them alphabetically: `"factory-boy"` before `"GitPython"` (line 139), `"hypothesis"` after `"execnet>=2.1.2"` (line 138) — maintain alphabetical order within the list.

    **tests/cases/unit/allure/conftest.py**: Create with `from __future__ import annotations`, `collect_ignore_glob = []` (empty — no fixture files to ignore in unit dir). No shared fixtures needed for unit tests (each test creates its own tmp_path NDJSON).

    **tests/cases/contract/allure/conftest.py**: Extend existing file (from Plan 01) with additional fixtures:
    - `sample_ndjson(tmp_path: Path) -> Path`: Fixture that creates a minimal valid NDJSON file with testRunStarted, testCaseStarted, testStepStarted, testStepFinished, testCaseFinished, testRunFinished. Uses `json.dumps()` per line with newline. Returns Path.
    - `sample_ndjson_multi_case(tmp_path: Path) -> Path`: Like sample_ndjson but with 2 test cases (different testCaseStartedId), each with 2 steps. Returns Path.
    - `sample_ndjson_with_attachment(tmp_path: Path) -> Path`: NDJSON including an Attachment event with testCaseStartedId and testStepId references.
    - `converter_output_dir(tmp_path: Path) -> Path`: Creates and returns a subdirectory `allure-results` under tmp_path.

    After adding deps, run `uv sync --extra test` to install factoryboy and hypothesis.
  </action>
  <verify>
    <automated>uv run python -c "import factory; import hypothesis; print('factoryboy OK'); print('hypothesis OK')"</automated>
  </verify>
  <done>factoryboy and hypothesis added to test extra, installed. Shared fixtures created for contract tests: sample_ndjson variants and output dir fixture. Unit conftest created with collect_ignore_glob.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Create unit tests for converter internals + extend schema validation test</name>
  <files>
    tests/cases/unit/allure/test_reader.py
    tests/cases/unit/allure/test_collector.py
    tests/cases/unit/allure/test_step_tree.py
    tests/cases/unit/allure/test_mapper.py
    tests/cases/unit/allure/test_emitter.py
    tests/cases/unit/allure/test_converter_e2e.py
    tests/cases/contract/allure/test_schema_validation.py
  </files>
  <read_first>
    - src/pytest_bdd/plugin/allure_cucumber/converter/reader.py (read_envelopes signature — to test)
    - src/pytest_bdd/plugin/allure_cucumber/converter/collector.py (group_by_test_case signature — to test)
    - src/pytest_bdd/plugin/allure_cucumber/converter/step_tree.py (build_step_tree signature — to test)
    - src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py (map_test_case_to_result, map_unmappable_to_attachment — to test)
    - src/pytest_bdd/plugin/allure_cucumber/converter/emitter.py (emit_results, emit_container — to test)
    - src/pytest_bdd/plugin/allure_cucumber/converter/__init__.py (convert — to test)
    - src/pytest_bdd/plugin/allure_cucumber/converter/model.py (AllureTestResult, AllureStepResult, etc.)
    - .planning/phases/24-docs-architecture-allure-md/24-PATTERNS.md (lines 713-771 — unit test patterns: fixtures with tmp_path, class-based test organization, pytestmark, test file naming)
    - tests/cases/unit/unit/test_plugin_patterns.py (existing unit test pattern for imports and structure)
  </read_first>
  <behavior>
    For each module under test, the behaviors were defined in Plan 02's task-level `<behavior>` blocks. The executor MUST re-derive exact test cases from those specs. At minimum:
    - test_reader.py: test_parses_single_envelope, test_parses_multiple_envelopes, test_skips_empty_lines, test_raises_on_malformed_json, test_handles_empty_file
    - test_collector.py: test_groups_by_test_case_id, test_multi_case_grouping, test_skips_no_id_events, test_handles_snake_case_ids, test_handles_camel_case_ids, test_empty_iterator
    - test_step_tree.py: test_single_step_single_result, test_two_sibling_steps, test_nested_steps, test_hook_steps_separated, test_empty_projection_list, test_status_mapping
    - test_mapper.py: test_maps_test_case_to_result, test_unmappable_becomes_attachment, test_status_mapping, test_empty_projections, test_multiple_attachments
    - test_emitter.py: test_emits_result_files, test_emits_container_file, test_output_dir_created, test_json_is_valid, test_matching_uuids
    - test_converter_e2e.py: test_convert_produces_output_files, test_convert_empty_ndjson_no_error, test_convert_output_validates_against_schema
    - test_schema_validation.py: extend with test_converter_output_validates (full NDJSON → convert → validate each output JSON against allure_schema_path) and test_invalid_output_rejected (malformed JSON missing uuid → jsonschema.ValidationError)
  </behavior>
  <action>
    Create 6 unit test files under `tests/cases/unit/allure/` following the PATTERNS.md patterns (lines 713-771). Each test file:
    - Uses `from __future__ import annotations`
    - Has `pytestmark = [pytest.mark.unit]` (for test group assignment)
    - Uses class-based test organization: `class TestReader:`, `class TestCollector:`, etc.
    - Uses `tmp_path` fixture for temporary NDJSON files and output directories
    - Writes NDJSON content with `tmp_path / "file.ndjson"` write_text pattern
    - Asserts on typed results (not just dict comparisons)
    - Test names follow `test_<scenario>` pattern
    - Covers happy paths, edge cases (empty input, malformed input), and error paths

    For test_step_tree.py: this is the most complex module. Create tests for each of the 6 behavior specs from Plan 02:
    - Single step: one Started/Finished pair → one root AllureStepResult
    - Two siblings: sequential independent steps → two roots
    - Hooks: steps with hook_id → separated into hook list
    - Interleaved/nested: A[start], B[start], B[finish], A[finish] with parent-child relationship → nested
    - Background: steps before regular with different pickleId → correctly attributed
    - Empty: empty list → empty result list

    For test_mapper.py: verify unmappable events (e.g., projections with payload_kind not in the known set) produce attachments on the result, not silently dropped. Also verify status mapping from cucumber (PASSED/FAILED/SKIPPED) to Allure (passed/failed/skipped).

    For test_converter_e2e.py: create a full NDJSON scenario using tmp_path fixture, call convert(), verify output files exist and can be parsed as JSON. Optionally validate against schema.

    **Extend test_schema_validation.py** (created by Plan 01 Task 3): Add `test_converter_output_validates` that creates NDJSON via sample_ndjson fixture, runs convert(), loads each output JSON file, and validates against allure_schema_path with `jsonschema.validate(instance=result_json, schema=schema)`. Add `test_invalid_output_rejected` that creates intentionally malformed JSON output (missing uuid) and asserts jsonschema.ValidationError is raised with specific path.

    Import directly from the converter modules (not through __init__ for unit tests; use __init__ only for e2e). Use `pathlib.Path`, `json`, `pytest`.
  </action>
  <verify>
    <automated>uv run pytest tests/cases/unit/allure/ tests/cases/contract/allure/test_schema_validation.py -x -v</automated>
  </verify>
  <done>All 6 unit test files pass with comprehensive coverage: reader (5+ tests), collector (6+ tests), step_tree (6+ tests), mapper (5+ tests), emitter (4+ tests), converter_e2e (3+ tests). Schema validation test extended: converter output validates against schema, malformed output correctly rejected. Covers happy paths, edge cases, and error paths.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| test fixtures → converter | Factory-created fixtures must match real-world NDJSON shape |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-20-11 | Tampering | package install (factoryboy, hypothesis) | mitigate | Human-verify checkpoint (Task 0) before pip install — verify on PyPI and GitHub repos |

</threat_model>

<verification>
After Plan 04a completes, verify:
```bash
# Unit tests
uv run pytest tests/cases/unit/allure/ -x -v

# Schema validation contract test
uv run pytest tests/cases/contract/allure/test_schema_validation.py -x -v

# Dependencies importable
uv run python -c "import factory; import hypothesis; print('Deps OK')"
```
</verification>

<success_criteria>
- [ ] factoryboy and hypothesis added to test extra, installed, human verified
- [ ] 6 unit test files created with comprehensive coverage of converter internals
- [ ] Schema validation contract test extended: converter output validates, malformed rejected
- [ ] Shared fixtures (sample_ndjson variants, converter_output_dir) created
- [ ] No regressions in existing test suite
- [ ] All new tests follow test group conventions (path-based auto-assignment)
</success_criteria>

<output>
Create `.planning/phases/24-docs-architecture-allure-md/24-04a-SUMMARY.md` when done
</output>
