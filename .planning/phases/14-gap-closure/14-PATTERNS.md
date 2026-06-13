# Phase 14: Gap Closure - Pattern Map

**Mapped:** 2026-05-20
**Files analyzed:** 21
**Analogs found:** 21 / 21

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tests/cases/unit/unit/test_tag_expression.py` (NEW) | unit test | direct-instantiation | `tests/cases/unit/unit/test_collector_batch.py` | exact |
| `tests/cases/unit/unit/test_scenario_locator.py` (NEW) | unit test | direct-instantiation | `tests/cases/unit/unit/test_collector_batch.py` | exact |
| `tests/cases/unit/unit/test_scenario.py` (NEW) | unit test | direct-instantiation | `tests/cases/unit/unit/test_collector_batch.py` | exact |
| `tests/cases/unit/unit/test_parser.py` (NEW) | unit test | direct-instantiation | `tests/cases/unit/unit/test_parsers_unit.py` | exact |
| `tests/cases/unit/unit/model/test_run_access.py` (NEW) | unit test | direct-instantiation (model) | `tests/cases/unit/unit/model/test_run.py` | exact |
| `tests/cases/unit/unit/model/test_run_refs.py` (NEW) | unit test | direct-instantiation (model) | `tests/cases/unit/unit/model/test_run.py` | exact |
| `tests/cases/unit/unit/test_collector.py` (NEW) | unit test | direct-instantiation | `tests/cases/unit/unit/test_collector_batch.py` | exact |
| `tests/cases/unit/unit/test_steps.py` (AUGMENT) | unit test | testdir-integration | `tests/cases/integration/feature/test_steps.py` | role-match |
| `tests/cases/unit/unit/test_parsers_unit.py` (AUGMENT) | unit test | direct-instantiation | itself — extend existing | self |
| `tests/cases/unit/unit/model/test_run.py` (AUGMENT) | unit test | direct-instantiation (model) | itself — extend existing | self |
| `tests/cases/unit/unit/model/test_scenario_run.py` (AUGMENT) | unit test | direct-instantiation (model) | itself — extend existing | self |
| `tests/cases/unit/unit/model/test_feature_binding.py` (AUGMENT) | unit test | direct-instantiation (model) | itself — extend existing | self |
| `tests/cases/integration/feature/test_steps.py` (AUGMENT) | integration test | testdir | itself — extend existing | self |
| `tests/cases/e2e/e2e/test_feature_NNN_*.py` (~47 NEW) | e2e test | scenario-bdd | `tests/cases/e2e/e2e/test_e2e.py` lines 41-61 | exact |
| `tests/cases/e2e/e2e/test_messages_fixed.py` (NEW) | e2e test | direct-instantiation | `tests/cases/e2e/e2e/test_e2e.py` lines 332-443 | exact |
| `tests/cases/e2e/e2e/test_e2e.py` (MODIFY/DELETE) | e2e test | scenario-bdd | itself — split into per-file modules | self |
| `tests/cases/e2e/conftest.py` (AUGMENT) | e2e step defs | pytest-fixture | itself — add step definitions | self |
| `features/XX Topic/*.feature.md` (NEW, D-15) | feature doc | gherkin | `features/01 Tutorial/01 Launch.feature.md` | exact |
| `.coveragerc` (MODIFY) | config | static | itself — optional threshold update | self |
| Pragma audit report doc (NEW, D-14) | documentation | artifact | N/A — informational only | n/a |
| `tests/cases/unit/unit/model/test_scenario_run_model.py` (AUGMENT) | unit test | direct-instantiation (model) | `tests/cases/unit/unit/model/test_scenario_run.py` | exact |

---

## Pattern Assignments

### 1. NEW Unit Tests — Direct Instantiation (coverage gap fill)

**Applies to:** `test_tag_expression.py`, `test_scenario_locator.py`, `test_scenario.py`, `test_parser.py`, `test_collector.py`, **and** model augment tests for `test_run.py`, `test_scenario_run.py`, `test_feature_binding.py`

**Primary analog:** `tests/cases/unit/unit/test_collector_batch.py` (best representative of direct-instantiation pattern)
**Secondary analog:** `tests/cases/unit/unit/model/test_run.py` (best for model classes with factory functions)
**Tertiary analog:** `tests/cases/unit/unit/test_parsers_unit.py` (best for class-method factory tests)

#### Imports pattern (test_collector_batch.py lines 1-12):
```python
"""Unit tests for <module name>."""

from __future__ import annotations

from pathlib import Path

import pytest
from cucumber_messages import GherkinDocument
# Import the module under test:
from pytest_bdd.<module> import <TargetClass>, <TargetFunction>
```

#### Marker pattern (test_run.py line 24):
```python
pytestmark = [pytest.mark.unit]
```

#### Core pattern — Direct instantiation + error paths (test_collector_batch.py lines 31-45):
```python
def test_register_appends_and_returns_count() -> None:
    """Descriptive docstring about what is tested."""
    obj = TargetClass()
    result = obj.method(some_arg)
    assert result == expected_value


def test_register_after_flush_raises() -> None:
    """Error path: method raises after invalid state."""
    obj = TargetClass()
    obj.method(Path("/fake/file.feature"))
    obj.transition_to_invalid_state()
    with pytest.raises(RuntimeError, match="specific error message"):
        obj.method(Path("/fake/file2.feature"))
```

#### Core pattern — Parameterized tests (test_parsers_unit.py lines 30-73):
```python
class TestTargetClass:
    """Tests for TargetClass.method."""

    def test_build_with_input_type_a(self) -> None:
        """descriptive docstring."""
        result = TargetClass.build(input_value)
        assert isinstance(result, ExpectedType)

    def test_build_with_input_type_b(self) -> None:
        """descriptive docstring."""
        result = TargetClass.build(other_input)
        assert result.attribute == expected
```

#### Core pattern — Model factory functions (test_run.py lines 644-709):
```python
# Module-level test helpers (private by convention)
def _build_run(**kwargs) -> Run:
    return Run(
        id="run-1",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        status=RunStatus.ok,
        **kwargs,
    )


def _build_scenario_run(run: Run | None = None, **kwargs) -> ScenarioRun:
    if run is None:
        run = _build_run()
    # ... build with sensible defaults, merge kwargs
    defaults = {"id": "ctx-1", ...}
    defaults.update(kwargs)
    return ScenarioRun(**defaults)
```

#### Core pattern — Stash-backed tests (test_run.py lines 201-258):
```python
def test_initialize_for_session_requires_stash(self) -> None:
    """initialize_for_session stores Run in stash."""
    stash: dict = {}
    session = SimpleNamespace(name="session")
    run = Run.initialize_for_session(stash=stash, session=session)
    assert stash["_pytest_bdd_run"] is run


def test_from_stash_retrieves_run(self) -> None:
    """Run can be retrieved from stash via from_stash."""
    stash: dict = {}
    session = SimpleNamespace(name="session")
    original = Run.initialize_for_session(stash=stash, session=session)
    retrieved = Run.from_stash(stash)
    assert retrieved is original
```

#### Error handling pattern — every test method has a return type annotation:
- All test methods return `-> None`
- Use `pytest.raises(ExceptionClass, match="expected substring")` for expected errors
- Use `SimpleNamespace` for mock-like objects (from `types`, not `unittest.mock`)

#### Documentation pattern:
- Module-level docstring at top: `"""Unit tests for <module>."""`
- Every test function has a one-line docstring
- Test classes group related tests with descriptive names: `class TestRunConstruction`, `class TestRunAdvanceTransition`

---

### 2. NEW E2E Per-File Modules (D-10 split)

**Applies to:** `tests/cases/e2e/e2e/test_feature_NNN_*.py` (~47 modules)

**Primary analog:** `tests/cases/e2e/e2e/test_e2e.py` lines 41-61 (individual `scenarios()` calls)
**Secondary analog:** `tests/cases/e2e/e2e/test_cucumber_formatters_feature.py` (complete per-file E2E module with step defs)

#### Per-file module pattern (from test_e2e.py lines 41-48, one per file):
```python
"""E2E tests for <Feature Area>: <Feature Name>."""

from pytest_bdd import scenarios

_EXCLUDED_TAGS = {"allure", "docker", "slow", "xdist"}


def _iter_tag_names(feature, pickle):
    yield from (str(tag.name).lstrip("@").lower() for tag in getattr(getattr(feature, "feature", None), "tags", ()))
    yield from (str(tag.name).lstrip("@").lower() for tag in getattr(pickle, "tags", ()))


def _filter(config, feature, pickle):
    tag_names = set(_iter_tag_names(feature, pickle))
    return tag_names.isdisjoint(_EXCLUDED_TAGS)


test_scenarios = scenarios("../../../../features/<NN Topic>/<NN Feature>.feature.md", filter_=_filter)
```

#### Per-file E2E with inline step definitions (from test_cucumber_formatters_feature.py):
```python
"""Provide test cucumber formatters feature helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd import given, parsers, scenarios, then, when
from pytest_bdd.testing.pytest_results import attach_command_result_outputs

test = scenarios("../../../../tests/e2e/_cucumber_formatters.feature")


@given("a fake node executable is available")
def fake_node_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Handle fake node available."""
    # ... step implementation


@when(
    parsers.parse('I run pytest with the console formatter flag "{flag}"'),
    target_fixture="pytest_result",
)
def run_pytest_with_console_formatter(testdir, flag: str, attach):
    """Run pytest with console formatter."""
    # ... step implementation
```

#### Key rules for D-10 split:
- **One module per feature file** — no `scenarios(".",...)` whole-directory loaders
- Each module MUST reference its specific feature file by path: `scenarios("../../../../features/NN Topic/NN Name.feature.md", filter_=_filter)`
- Filter function can be shared via a utility module or duplicated per module
- Step definitions that are shared across multiple feature files stay in `tests/cases/e2e/conftest.py`
- Step definitions unique to one feature file go in the per-file module

---

### 3. NEW `test_messages_fixed.py` (split non-scenario tests)

**Applies to:** `tests/cases/e2e/e2e/test_messages_fixed.py`

**Analog:** `tests/cases/e2e/e2e/test_e2e.py` lines 297-443 (non-scenario test functions)

#### Extraction pattern:

```python
"""E2E tests for messages fixed release readiness matrix."""

from types import SimpleNamespace

from pytest_bdd_testing.tool.message.capability_fixtures import make_mapping_rule

from pytest_bdd.model.message_outcome_mapping import ObservedOutcome, validate_outcome_mappings

pytestmark = [pytest.mark.e2e]


def test_messages_fixed_release_readiness_matrix_is_valid() -> None:
    """Verify messages fixed release readiness matrix is valid."""
    # ... existing test body from test_e2e.py lines 332-345


def test_messages_fixed_release_readiness_matrix_rejects_missing_parallel_worker_scenario() -> None:
    """Verify messages fixed release readiness matrix rejects missing parallel worker scenario."""
    # ... existing test body from test_e2e.py lines 347-361


def test_default_bdd_filter_excludes_tagged_slow_scenarios() -> None:
    """Verify default bdd filter excludes tagged slow scenarios."""
    # ... existing test body from test_e2e.py lines 363-443
```

---

### 4. AUGMENT E2E `conftest.py` (D-07 — add missing step definitions)

**Applies to:** `tests/cases/e2e/conftest.py` (add new step definitions)

**Analog:** `tests/cases/e2e/conftest.py` itself — follow existing step definition patterns

#### Step definition pattern (conftest.py lines 58-470):
```python
from pytest_bdd import given, parsers, step, then, when


@given("a descriptive step phrase with literal text")
def descriptive_function_name(testdir) -> None:
    """Handle descriptive step phrase."""
    # step implementation


@when(
    parsers.parse('I run command with "{param}"'),
    target_fixture="result_fixture",
)
def command_with_parameter(testdir, param: str, attach):
    """Handle command with parameter."""
    result = do_something(testdir, param)
    attach_command_result_outputs(attach, result, label="step-label", command="command string")
    return result


@then(
    parsers.parse('stdout contains the user-visible line "{visible_output}"'),
)
def stdout_contains_visible_line(pytest_result, visible_output: str) -> None:
    """Handle stdout contains user visible line."""
    stdout = pytest_result.stdout if isinstance(pytest_result.stdout, str) else pytest_result.stdout.str()
    assert fnmatch(stdout, f"*{visible_output}*")
```

#### Key import patterns for conftest.py:
```python
from pytest_bdd import given, parsers, step, then, when
from pytest_bdd.testing.pytest_results import (
    attach_command_result_outputs,
    combined_result_output,
    resolve_pytester_run_mode,
    run_quietly,
)
```

---

### 5. NEW `.feature.md` files (D-15 — undocumented behaviors)

**Applies to:** New feature files under `features/XX Topic/`

**Analog:** `features/01 Tutorial/01 Launch.feature.md`

#### Feature file pattern:
```markdown
# Feature: <Brief description of the feature under test>
    <Optional additional description for edge cases>

## Scenario: <Scenario name describing the behavior>

* <Keyword> <Step with parameters if needed>

    | column1 | column2 |
    |---------|---------|
    | value1  | value2  |

* <Keyword> <Another step>
* <Keyword> <Assertion step>
```

#### Concrete example from 01 Launch.feature.md (lines 1-16):
```markdown
# Feature: Simple project tests that use pytest-bdd-ng could be run via pytest
    Project per se: https://github.com/elchupanebrej/pytest-bdd-ng/tree/default/docs/tutorial

## Scenario: Catalog example with simplest steps

* Given Copy path from "docs/tutorial" to test path "tutorial"
* When run pytest

    | cli_args | --rootdir=tutorial | tutorial/tests |
    |----------|--------------------|----------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |
```

---

### 6. MODIFY `.coveragerc` (optional per-module threshold)

**Applies to:** `.coveragerc`

**Analog:** `.coveragerc` itself (existing configuration)

#### Current state (lines 1-6):
```ini
[run]
branch = true
source = pytest_bdd

[report]
fail_under = 70
```

#### If per-module enforcement needed, add:
```ini
[run]
branch = true
source = pytest_bdd
omit =
    */_gherkin_go/*
    */script/*
    */testing/*
    */types/*
    */__init__.py
    */entrypoint.py

[report]
fail_under = 70
show_missing = true
```

---

## Shared Patterns

### Test File Structure (ALL new test files)

**Source:** `tests/cases/unit/unit/test_collector_batch.py`, `tests/cases/unit/unit/model/test_run.py`

```python
"""One-line module docstring describing what these tests cover."""

from __future__ import annotations  # REQUIRED per AGENTS.md convention

# stdlib imports
from pathlib import Path
from types import SimpleNamespace

# third-party
import pytest
from cucumber_messages import <specific types>

# project imports
from pytest_bdd.<module> import <TargetClass>


# ── pytest marker (ALL new test files) ──────────────────────────────────

pytestmark = [pytest.mark.unit]   # or pytest.mark.e2e, pytest.mark.integration


# ── Helper factories (for model tests) ──────────────────────────────────

def _build_target(**kwargs) -> TargetType:
    """Create a minimal TargetType for testing."""
    return TargetType(
        required_field=default_value,
        **kwargs,
    )


# ── Test classes ────────────────────────────────────────────────────────

class TestTargetConstruction:
    """Tests for TargetType construction."""

    def test_construction_with_required_fields(self) -> None:
        """TargetType can be constructed with required fields."""
        obj = _build_target()
        assert obj.field == expected_value

    def test_error_path_raises(self) -> None:
        """Error handling test with pytest.raises."""
        with pytest.raises(ExpectedError, match="expected message"):
            do_something_invalid()
```

### Integration Test (testdir) Pattern (ALL testdir tests)

**Source:** `tests/cases/integration/feature/test_steps.py` lines 12-67, `test_step_matching_priority.py` lines 6-37

```python
import textwrap


def test_descriptive_name(testdir):
    """Descriptive docstring for the test."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        steps="""\
            Feature: Feature Description
                Scenario: Scenario Name
                    Given I have a step
                    When I do something
                    Then it should work
        """,
    )

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, when, then

        @given("I have a step")
        def have_step():
            return "value"

        @when("I do something")
        def do_something():
            pass

        @then("it should work")
        def check_works():
            assert True
    """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)
```

### Error Testing with `testdir.runpytest_subprocess`

**Source:** `tests/cases/integration/feature/test_steps.py` lines 71-94

```python
def test_zero_match_scenario_raises_usage_error(testdir):
    """Verify scenarios with no matching step definitions fail during collection."""
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Missing steps
                Scenario: No registered steps match
                    Given nothing is registered for this step
        """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd import scenarios

        test_steps = scenarios("steps.feature")
        """,
    )
    result = testdir.runpytest_subprocess("-s", "--disable-feature-autoload")
    result.stderr.fnmatch_lines(["*Scenarios with zero matched step definitions found:*"])
```

### E2E Tag Filter Pattern (ALL E2E per-file modules)

**Source:** `tests/cases/e2e/e2e/test_e2e.py` lines 10-44

```python
_EXCLUDED_TAGS = {"allure", "docker", "slow", "xdist"}


def _iter_tag_names(feature, pickle):
    yield from (str(tag.name).lstrip("@").lower() for tag in getattr(getattr(feature, "feature", None), "tags", ()))
    yield from (str(tag.name).lstrip("@").lower() for tag in getattr(pickle, "tags", ()))


def _filter(config, feature, pickle):  # noqa: ARG001
    tag_names = set(_iter_tag_names(feature, pickle))
    return tag_names.isdisjoint(_EXCLUDED_TAGS)


test_feature_NNN = scenarios("../../../../features/NN Topic/NN Feature.feature.md", filter_=_filter)
```

### Stash-Backed Test Pattern (model tests that use stash)

**Source:** `tests/cases/unit/unit/model/test_run.py` lines 201-258

```python
def test_initialize_for_session_requires_stash(self) -> None:
    """initialize_for_session stores Target in stash."""
    stash: dict = {}
    session = SimpleNamespace(name="session")
    target = Target.initialize_for_session(stash=stash, session=session)
    assert stash["_pytest_bdd_<key>"] is target
    assert target.status == ExpectedStatus.ok
```

### `attrs` Data Class Usage (tests use real attrs objects, not mocks)

**Source:** `tests/cases/unit/unit/model/test_run.py` lines 30-55, 663-669

```python
# Build real attrs objects with defaults + kwargs override pattern
def _build_run(**kwargs) -> Run:
    return Run(
        id="run-1",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        status=RunStatus.ok,
        **kwargs,
    )
```

### `SimpleNamespace` for Mock-Like Objects (NOT unittest.mock)

**Source:** `tests/cases/unit/unit/model/test_run.py` lines 204, 302-303

```python
# Use SimpleNamespace for thin mock objects
session = SimpleNamespace(name="session")
request = SimpleNamespace(config=SimpleNamespace(stash={}), node=SimpleNamespace(nodeid="test-1"))
```

---

## No Analog Found

All files have close matches in the codebase. No exceptions.

| File | Reason Analog Found |
|------|-------------------|
| Pragma audit report | Documentation artifact — no code pattern needed. Report format is free-form markdown listing each `# pragma: no cover` instance with justification. |

---

## Metadata

**Analog search scope:** `tests/cases/unit/`, `tests/cases/integration/`, `tests/cases/e2e/`, `features/`
**Files scanned:** 12 key analog files read
**Pattern extraction date:** 2026-05-20
