"""Bind-feature code-generation CLI tests."""

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


def _write_feature(testdir):
    feature = testdir.tmpdir.join("features").join("bind.feature")
    feature.ensure()
    feature.write(
        textwrap.dedent(
            """\
            Feature: Bind feature

                Scenario: Generated binding
                    Given a step
            """,
        ),
    )
    return feature


def test_bind_feature_detects_existing_pytest_bdd_scenarios_call(testdir):
    """AST detection treats pytest_bdd.scenarios as an existing binding."""
    feature = _write_feature(testdir)
    target = testdir.tmpdir.join("test_bind.py")
    target.write(
        textwrap.dedent(
            """\
            import pytest_bdd


            pytest_bdd.scenarios("features/bind.feature")
            """,
        ),
    )

    result = _run_codegen(testdir, "--bind-feature", "--target-file", str(target), str(feature))

    assert result.ret == 0
    assert target.read().count("scenarios(") == 1


def test_bind_feature_rolls_back_invalid_target_by_default(testdir):
    """Invalid existing target syntax is restored on failed rewrite."""
    feature = _write_feature(testdir)
    target = testdir.tmpdir.join("test_bind.py")
    original = "def broken(:\n"
    target.write(original)

    result = _run_codegen(testdir, "--bind-feature", "--target-file", str(target), str(feature))

    assert result.ret == 100
    assert target.read() == original


def test_bind_feature_keep_generated_on_error_preserves_failed_edit(testdir):
    """Explicit keep flag preserves failed generated content."""
    feature = _write_feature(testdir)
    target = testdir.tmpdir.join("test_bind.py")
    original = "def broken(:\n"
    target.write(original)

    result = _run_codegen(
        testdir,
        "--bind-feature",
        "--target-file",
        str(target),
        "--keep-generated-on-error",
        str(feature),
    )

    assert result.ret == 100
    assert target.read() != original
    assert "scenarios(" in target.read()
    assert "features/bind.feature" in target.read()
