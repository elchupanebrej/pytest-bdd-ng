"""

Code generation and assertion tests.
"""

import ast
import itertools

import pytest

from pytest_bdd.plugin.code_generator import entrypoint as code_generator_entrypoint
from pytest_bdd.plugin.code_generator.collection import process_single_item
from pytest_bdd.plugin.code_generator.rendering import make_python_docstring, make_string_literal
from pytest_bdd.plugin.pickle_runner import entrypoint as pickle_runner_entrypoint
from pytest_bdd.plugin.scenario_test_collector import entrypoint as scenario_test_collector_entrypoint
from pytest_bdd.scenario import get_python_name_generator


def _run_codegen(testdir, *args):
    testdir.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    return testdir.runpytest_inprocess(
        *args,
        plugins=[code_generator_entrypoint, pickle_runner_entrypoint, scenario_test_collector_entrypoint],
    )


def test_python_name_generator():
    """
    Test python name generator function.

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
    assert list(itertools.islice(get_python_name_generator("Some name"), 3)) == [
        "test_some_name",
        "test_some_name_1",
        "test_some_name_2",
    ]


@pytest.mark.parametrize(
    "value",
    [
        "trailing backslash\\",
        "line one\nline two",
        "single ' quote",
        'triple """ quote',
    ],
)
def test_generated_python_literals_preserve_valid_gherkin_text(value: str) -> None:
    """
    Verify generated Python literals preserve valid Gherkin text.

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
    assert ast.literal_eval(make_string_literal(value)) == value
    assert ast.literal_eval(make_python_docstring(value)) == value
    ast.parse(f"def test_generated():\n    {make_python_docstring(value)}\n")


def test_process_single_item_tears_down_after_fixture_error() -> None:
    """
    Verify code-generation item setup is torn down after fixture errors.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
    events = []

    class SetupState:
        def setup(self, item):
            events.append(("setup", item))

        def teardown_exact(self, item):
            events.append(("teardown", item))

    class Session:
        _setupstate = SetupState()

    class FixtureRequest:
        def getfixturevalue(self, name):
            msg = f"{name} fixture failed"
            raise RuntimeError(msg)

    class Item:
        session = Session()
        _request = FixtureRequest()

    item = Item()

    with pytest.raises(RuntimeError, match="pickle fixture failed"):
        process_single_item(item, set(), [])

    assert events == [("setup", item), ("teardown", None)]


def test_generate_missing_with_step_parsers(testdir):
    """
    Test that step parsers are correctly discovered and won't be part of the missing steps.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
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
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        # language=gherkin
        generation="""\
            Feature: Missing code generation with step parsers

                Scenario: Step parsers are correctly discovered
                    Given I use the string parser without parameter
                    And I use parsers.parse with parameter 1
                    And I use parsers.re with parameter 2
                    And I use parsers.cfparse with parameter 3
            """,
    )

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, parsers

        @given("I use the string parser without parameter")
        def i_have_a_bar():
            return None

        @given(parsers.parse("I use parsers.parse with parameter {param}"))
        def i_have_n_baz(param):
            return param

        @given(parsers.re(r"^I use parsers.re with parameter (?P<param>.*?)$"))
        def i_have_n_baz(param):
            return param

        @given(parsers.cfparse("I use parsers.cfparse with parameter {param:d}"))
        def i_have_n_baz(param):
            return param
        """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd import scenario


        @scenario("generation.feature", "Step parsers are correctly discovered")
        def test_step_parsers():
            pass
        """,
    )

    result = _run_codegen(testdir, "--gather-missing-steps", "generation.feature")
    assert not result.stderr.str()
    assert result.ret == 0

    output = result.stdout.str()

    assert "I use the string parser" not in output
    assert "I use parsers.parse" not in output
    assert "I use parsers.re" not in output
    assert "I use parsers.cfparse" not in output


def test_generate_missing_without_feature_returns_100(testdir):
    """
    Verify missing feature option preserves code-generation exit status.

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
    result = _run_codegen(testdir, "--gather-missing-steps")

    assert result.ret == 100
    result.stdout.fnmatch_lines(["*At least one feature path is required.*"])
