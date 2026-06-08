"""Generate-missing-steps target-file CLI tests."""

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


def _write_missing_step_case(testdir):
    feature = testdir.tmpdir.join("generation.feature")
    feature.write(
        textwrap.dedent(
            """\
            Feature: Missing step generation

                Scenario: Bound scenario with missing steps
                    Given I have a bar
                    Then I have a custom bar
                    And I have a custom bar
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


        @scenario(Path(r"{feature}"), "Bound scenario with missing steps")
        def test_bound():
            pass
        """,
    )
    return feature


def test_generate_missing_steps_skips_existing_equivalent_decorator(testdir):
    """AST decorator detection prevents duplicate generated steps."""
    feature = _write_missing_step_case(testdir)
    target = testdir.tmpdir.join("test_steps.py")
    target.write(
        textwrap.dedent(
            """\
            from pytest_bdd import then


            @then("I have a custom bar")
            def existing_step():
                pass
            """,
        ),
    )
    before = target.read()

    result = _run_codegen(testdir, "--generate-missing-steps", "--target-file", str(target), str(feature))

    assert result.ret == 100
    assert target.read() == before


def test_generate_missing_steps_rolls_back_invalid_target_by_default(testdir):
    """Invalid existing target syntax is restored on failed rewrite."""
    feature = _write_missing_step_case(testdir)
    target = testdir.tmpdir.join("test_steps.py")
    original = "def broken(:\n"
    target.write(original)

    result = _run_codegen(testdir, "--generate-missing-steps", "--target-file", str(target), str(feature))

    assert result.ret == 100
    assert target.read() == original


def test_generate_missing_steps_keep_generated_on_error_preserves_failed_edit(testdir):
    """Explicit keep flag preserves failed generated content."""
    feature = _write_missing_step_case(testdir)
    target = testdir.tmpdir.join("test_steps.py")
    original = "def broken(:\n"
    target.write(original)

    result = _run_codegen(
        testdir,
        "--generate-missing-steps",
        "--target-file",
        str(target),
        "--keep-generated-on-error",
        str(feature),
    )

    assert result.ret == 100
    assert target.read() != original
    assert "@then(" in target.read()
    assert "I have a custom bar" in target.read()
