# Phase 26: Test CLI scripts in a separate Cucumber Development flow

This phase implements ATDD/BDD E2E tests for all repository-specific CLI tools, development scripts, and pre-commit checks in a new focused feature directory `features/18 Development/`.

---

## Proposed Changes

### Step Definitions & E2E Wrappers

#### [NEW] [development.py](file:///c:/Users/bulky/Projects/pytest-bdd/src/pytest_bdd_testing/step/development.py)
Create a new step definition file containing generic steps for executing commands in the test directory, checking exit codes, creating mockup files, and examining standard output/error.
```python
from pathlib import Path
import pytest
from hamcrest import assert_that, equal_to
from pytest_bdd import given, parsers, then

@given(parsers.parse('Mock file "{filename}" with content:'))
def mock_file_with_content(testdir, filename, step) -> None:
    doc_string = getattr(step.argument, "doc_string", None) if getattr(step, "argument", None) else None
    content = doc_string.content if doc_string else ""
    target = Path(str(testdir.tmpdir)) / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

@then(parsers.parse("the command exit code is {exit_code:d}"))
def check_command_exit_code(renderer_result, exit_code: int) -> None:
    assert_that(renderer_result.returncode, equal_to(exit_code))
```

#### [MODIFY] [conftest.py](file:///c:/Users/bulky/Projects/pytest-bdd/src/pytest_bdd_testing/case/e2e/conftest.py)
Register the new development steps package for assert rewriting and import it.
```diff
 pytest.register_assert_rewrite(
     "pytest_bdd_testing.step.batch_collection",
     "pytest_bdd_testing.step.code_generator",
     "pytest_bdd_testing.step.compatibility",
     "pytest_bdd_testing.step.debug_mcp",
+    "pytest_bdd_testing.step.development",
     "pytest_bdd_testing.step.formatters",
     "pytest_bdd_testing.step.go_parser",
     "pytest_bdd_testing.step.mimetype",
     "pytest_bdd_testing.step.scenario_reporter",
     "pytest_bdd_testing.step.struct_bdd",
     "pytest_bdd_testing.step.tag_expressions",
 )

 from pytest_bdd_testing.step.batch_collection import *  # noqa: F403, E402
 from pytest_bdd_testing.step.code_generator import *  # noqa: F403, E402
 from pytest_bdd_testing.step.compatibility import *  # noqa: F403, E402
 from pytest_bdd_testing.step.debug_mcp import *  # noqa: F403, E402
+from pytest_bdd_testing.step.development import *  # noqa: F403, E402
 from pytest_bdd_testing.step.formatters import *  # noqa: F403, E402
 from pytest_bdd_testing.step.go_parser import *  # noqa: F403, E402
 from pytest_bdd_testing.step.harness import *  # noqa: F403, E402
```

#### [NEW] [test_18_development.py](file:///c:/Users/bulky/Projects/pytest-bdd/src/pytest_bdd_testing/case/e2e/feature/test_18_development.py)
Create the E2E test collector file to run scenarios under the `18 Development` directory.
```python
import pytest
from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("18 Development")
```

---

### BDD Feature Files (`features/18 Development/`)

#### [NEW] [01 Allure Converter CLI.feature.md](file:///c:/Users/bulky/Projects/pytest-bdd/features/18%20Development/01%20Allure%20Converter%20CLI.feature.md)
BDD tests for `allure-cucumber` CLI command.
- **Scenario**: Successfully converting Cucumber Messages NDJSON to Allure results.
- **Scenario**: Handles missing NDJSON file gracefully.

#### [NEW] [02 Headings Validator.feature.md](file:///c:/Users/bulky/Projects/pytest-bdd/features/18%20Development/02%20Headings%20Validator.feature.md)
BDD tests for `validate_feature_headings` script.
- **Scenario**: Pre-commit validation passes on clean feature headings.
- **Scenario**: Pre-commit validation fails and reports empty feature/scenario headings.

#### [NEW] [03 Architecture Tooling.feature.md](file:///c:/Users/bulky/Projects/pytest-bdd/features/18%20Development/03%20Architecture%20Tooling.feature.md)
BDD tests for `scripts/arch.py` and its injection/collection functionality.
- **Scenario**: Injecting responsibility templates into a mockup Python file.
- **Scenario**: Collecting and validating architecture scores.
- **Scenario**: Running gap analysis on the collected scores.

#### [NEW] [04 Compatibility Matrix.feature.md](file:///c:/Users/bulky/Projects/pytest-bdd/features/18%20Development/04%20Compatibility%20Matrix.feature.md)
BDD tests for `compatibility_matrix` CLI.
- **Scenario**: Checking compatibility for a specific Python/pytest pair.
- **Scenario**: Generating tox environment names.
- **Scenario**: Verifying E2E migration status.

#### [NEW] [05 Messages Contract Schema Sync.feature.md](file:///c:/Users/bulky/Projects/pytest-bdd/features/18%20Development/05%20Messages%20Contract%20Schema%20Sync.feature.md)
BDD tests for `sync_messages_contract_schemas.py` drift checking.
- **Scenario**: Schema sync check passes when local schemas are up-to-date.
- **Scenario**: Schema sync check fails when a schema is altered (drift).

#### [NEW] [06 Cucumber Formatter Renderer.feature.md](file:///c:/Users/bulky/Projects/pytest-bdd/features/18%20Development/06%20Cucumber%20Formatter%20Renderer.feature.md)
BDD tests for `render_cucumber_formatters` CLI.
- **Scenario**: Standalone rendering of NDJSON to summary output.

#### [NEW] [07 Messages Coverage Audit.feature.md](file:///c:/Users/bulky/Projects/pytest-bdd/features/18%20Development/07%20Messages%20Coverage%20Audit.feature.md)
BDD tests for `scripts/run_messages_coverage_audit.sh` orchestration.
- **Scenario**: Audit run completes and outputs the governance-runtime JSON report.

---

### Roadmap Updates

#### [MODIFY] [ROADMAP.md](file:///c:/Users/bulky/Projects/pytest-bdd/.planning/ROADMAP.md)
Update Phase 26 with goals, success criteria, and plans.

---

## Open Issues / Blockers

### `test_undefined_parameter_runtime.py` probe error
- **Status**: BLOCKING for `07 Messages Coverage Audit.feature.md`
- **Problem**: Both with and without `--allow-empty-scenarios`, the test encounters an `AssertionError` from `step_matcher` fixture resolution inside the gherkin message reporter plugin, causing a `PluggyTeardownRaisedWarning`. Exit code 4 (collection error) instead of expected failure.
- **Root cause**: The `undefined_parameter.feature` scenario cannot produce `undefinedParameterType` messages because collection itself fails when the step pattern doesn't register (missing `step_matcher` fixture during runtime).
- **Options**:
  1. Use `--allow-empty-scenarios` + suppress `PluggyTeardownRaisedWarning` for this probe via pytest configuration override.
  2. Skip the `test_undefined_parameter_runtime.py` probe and mark the `undefinedParameterType` capabilities as `Not Applicable`.
  3. Fix the `step_matcher` fixture resolution in the gherkin message reporter plugin to be resilient when the scenario has no matched steps.

---

## Verification Plan

### Automated Tests
Run the newly created E2E tests:
```bash
pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py
```
Check formatting and linting:
```bash
make lint
```
Check type safety:
```bash
make custom-rules
```
