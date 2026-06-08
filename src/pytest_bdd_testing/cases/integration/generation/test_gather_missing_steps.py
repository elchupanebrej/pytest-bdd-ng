"""Gather-missing code-generation CLI tests."""

import textwrap

from pytest_bdd.plugin.code_generator import entrypoint as code_generator_entrypoint
from pytest_bdd.plugin.pickle_runner import entrypoint as pickle_runner_entrypoint
from pytest_bdd.plugin.scenario_test_collector import entrypoint as scenario_test_collector_entrypoint


def _run_codegen(testdir, *args):
    testdir.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    return testdir.runpytest_inprocess(
        *args,
        plugins=[code_generator_entrypoint, pickle_runner_entrypoint, scenario_test_collector_entrypoint],
    )


def _write_generation_case(testdir):
    feature = testdir.tmpdir.join("generation.feature")
    feature.write(
        textwrap.dedent(
            """\
            Feature: Missing code generation

                Scenario: Bound scenario with a missing step
                    Given I have a bar
                    Then I have a custom bar

                Scenario: Unbound scenario
                    Given I have a bar
            """,
        ),
    )
    testdir.makepyfile(
        f"""\
        from pathlib import Path

        from pytest_bdd import given, scenario


        @given("I have a bar")
        def i_have_a_bar():
            return "bar"


        @scenario(Path(r"{feature}"), "Bound scenario with a missing step")
        def test_bound():
            pass
        """,
    )
    return feature


def test_legacy_generate_missing_flags_render_missing_steps(testdir):
    """Legacy codegen flags render missing-step snippets for compatibility."""
    feature = _write_generation_case(testdir)

    result = _run_codegen(testdir, "--generate-missing", "--feature", str(feature))

    assert result.ret == 0
    result.stdout.fnmatch_lines(
        [
            '*Step Then "I have a custom bar" is not defined*',
            '*Step Given "I have a bar" is not defined*',
            '*@then("I have a custom bar")*',
            '*@given("I have a bar")*',
        ],
    )


def test_gather_missing_steps_without_feature_returns_100(testdir):
    """Missing positional feature input preserves code-generation exit status."""
    result = _run_codegen(testdir, "--gather-missing-steps")

    assert result.ret == 100
    result.stdout.fnmatch_lines(["*At least one feature path is required.*"])
