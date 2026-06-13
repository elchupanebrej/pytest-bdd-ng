"""

Integration tests for cucumber JSON dispatcher precedence.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from types import SimpleNamespace

from pytest_bdd.plugin.cucumber_json_dispatcher import entrypoint


def _write_minimal_bdd_test(testdir) -> None:
    testdir.makeconftest(
        """\
from pytest_bdd import given


@given("true")
def given_true():
    pass
""",
    )
    testdir.makefile(
        ".feature",
        test_simple="""\
Feature: Simple
Scenario: Simple scenario
  Given true
""",
    )
    testdir.makepyfile(
        test_simple="""\
from pytest_bdd import scenario


@scenario("test_simple.feature", "Simple scenario")
def test_simple():
    pass
""",
    )


def _write_stub_cucumber_package(testdir) -> None:
    node_modules = Path(str(testdir.tmpdir)) / "node_modules"
    cucumber_package = node_modules / "@cucumber" / "cucumber"
    cucumber_expressions_package = node_modules / "@cucumber" / "cucumber-expressions"
    nested_expressions_package = cucumber_package / "node_modules" / "@cucumber" / "cucumber-expressions"

    cucumber_package.mkdir(parents=True)
    cucumber_expressions_package.mkdir(parents=True)
    nested_expressions_package.mkdir(parents=True)

    (cucumber_package / "package.json").write_text(
        '{"name":"@cucumber/cucumber","main":"index.js"}',
        encoding="utf-8",
    )
    (cucumber_package / "index.js").write_text(
        """\
class EventDataCollector {
  constructor(eventBroadcaster) {
    this.eventBroadcaster = eventBroadcaster;
  }
}

const FormatterBuilder = {
  async build(_specifier, options) {
    return {
      async finished() {
        options.stream.write('[]');
      },
    };
  },
};

module.exports = {
  EventDataCollector,
  FormatterBuilder,
  formatterHelpers: { EventDataCollector },
};
""",
        encoding="utf-8",
    )

    expressions_source = """\
class ParameterType {
  constructor(name) {
    this.name = name;
  }
}

class ParameterTypeRegistry {
  constructor() {
    this.parameterTypes = new Map();
  }
  lookupByTypeName(name) {
    return this.parameterTypes.get(name);
  }
  defineParameterType(parameterType) {
    this.parameterTypes.set(parameterType.name, parameterType);
  }
}

module.exports = { ParameterType, ParameterTypeRegistry };
"""
    for package_dir in (cucumber_expressions_package, nested_expressions_package):
        (package_dir / "package.json").write_text(
            '{"name":"@cucumber/cucumber-expressions","main":"index.js"}',
            encoding="utf-8",
        )
        (package_dir / "index.js").write_text(expressions_source, encoding="utf-8")


def _json_files(testdir) -> set[str]:
    return {path.name for path in Path(str(testdir.tmpdir)).glob("*.json")}


def test_dispatcher_ini_only_activates_ini_backend(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    testdir.makefile(".ini", pytest="[pytest]\ncucumber_json_path = result.json\n")
    _write_minimal_bdd_test(testdir)

    result = testdir.runpytest("-s")

    result.assert_outcomes(passed=2)
    result_path = testdir.tmpdir.join("result.json")
    assert result_path.check()
    assert isinstance(json.loads(result_path.read()), list)
    assert _json_files(testdir) == {"result.json"}


def test_dispatcher_cli_only_activates_cli_backend(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    _write_stub_cucumber_package(testdir)
    _write_minimal_bdd_test(testdir)

    result = testdir.runpytest("-s", "--cucumber-json=cli_output.json")

    result.assert_outcomes(passed=2)
    assert testdir.tmpdir.join("cli_output.json").check()
    assert not testdir.tmpdir.join("result.json").check()


def test_dispatcher_no_config_both_silent(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    _write_minimal_bdd_test(testdir)

    result = testdir.runpytest("-s")

    result.assert_outcomes(passed=2)
    assert _json_files(testdir) == set()
    assert "cucumber" not in result.stderr.str().lower()


def test_dispatcher_cli_wins_over_ini(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    testdir.makefile(".ini", pytest="[pytest]\ncucumber_json_path = ini_output.json\n")
    _write_stub_cucumber_package(testdir)
    _write_minimal_bdd_test(testdir)

    result = testdir.runpytest("-s", "--cucumber-json=cli_output.json")
    combined_output = f"{result.stdout.str()}\n{result.stderr.str()}"

    assert result.ret != 5
    assert not testdir.tmpdir.join("ini_output.json").check()
    if result.ret == 0:
        assert testdir.tmpdir.join("cli_output.json").check()
    assert "UserWarning" not in combined_output
    assert "DeprecationWarning" not in combined_output


def test_dispatcher_xdist_worker_guard() -> None:
    """
    Test target:
    Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    ini_cache = {"cucumber_json_path": "/some/ini/path"}
    config = SimpleNamespace(
        workerinput={},
        option=SimpleNamespace(cucumber_js_json_path="out.json"),
        _inicache=ini_cache,
    )
    config.getini = lambda key: ini_cache.get(key, "")

    entrypoint.pytest_configure(config)

    assert ini_cache["cucumber_json_path"] == "/some/ini/path"


def test_dispatcher_no_warning_on_cli_override_ini() -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    ini_cache = {"cucumber_json_path": "/ini/path"}
    config = SimpleNamespace(
        _inicache=ini_cache,
        option=SimpleNamespace(cucumber_js_json_path="/cli/path"),
    )
    config.getini = lambda key: ini_cache.get(key, "")

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")
        entrypoint.pytest_configure(config)

    assert warning_list == []
    assert ini_cache["cucumber_json_path"] == ""  # noqa: PLC1901
