"""Test scenarios shortcut."""

from textwrap import dedent

import pytest

from pytest_cuke.compatibility.pytest import assert_outcomes

from pytest import mark

pytestmark = mark.integration


def test_scenarios(testdir, pytest_params, tmp_path):
    """Test scenarios shortcut used together with @scenario"""
    testdir.makeini(
        f"""\
        [pytest]
        console_output_style=classic
        cuke_features_dir={tmp_path}
        """
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_cuke import given

        @given('I have a bar')
        def i_have_bar():
            print('bar!')
            return 'bar'

        @given('I have a failing bar')
        def i_have_a_failing_bar():
            raise AssertionError('the failing step was executed')
        """
    )

    (tmp_path / "features" / "subfolder").mkdir(parents=True)

    (tmp_path / "features" / "test.feature").write_text(
        dedent(
            # language=gherkin
            """\
            Feature: Test scenarios

                Scenario: Test scenario
                    Given I have a bar
            """
        )
    )
    (tmp_path / "features" / "subfolder" / "test.feature").write_text(
        # language=gherkin
        """\
        Feature: Test scenarios
            Scenario: Test subfolder scenario
                Given I have a bar

            Scenario: Test failing subfolder scenario
                Given I have a failing bar

            Scenario: Test already bound scenario
                Given I have a bar

            Scenario: Test scenario
                Given I have a bar
        """
    )
    testdir.makepyfile(
        # language=python
        """\
        from pytest_cuke import scenarios, scenario

        test_feature = scenarios('features/subfolder/test.feature')

        @scenario('features/subfolder/test.feature', 'Test already bound scenario')
        def test_already_bound():
            pass
        """
    )
    runpytest = testdir.runpytest_subprocess if pytest_params == ["--import-mode=append"] else testdir.runpytest
    result = runpytest("-v", "-s", *pytest_params)
    assert_outcomes(result, passed=4, failed=1)
    result.stdout.fnmatch_lines(["*collected 5 items"])
    result.stdout.fnmatch_lines(["*test*test.feature-Test scenarios-Test subfolder scenario* bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test*test.feature-Test scenarios-Test scenario* bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test*test.feature-Test scenarios-Test failing subfolder scenario* FAILED"])
    result.stdout.fnmatch_lines(["*AssertionError: the failing step was executed*"])
    result.stdout.fnmatch_lines(["*test_already_bound* bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test*test.feature-Test scenarios-Test scenario* bar!", "PASSED"])


def test_explicit_scenario_without_matching_step_definition_is_collection_error(testdir):
    testdir.makeini(
        """\
        [pytest]
        cuke_autoload = false
        cuke_features_dir = .
        """
    )
    testdir.makefile(
        ".feature",
        unmatched="""\
            Feature: Missing step definition
                Scenario: Explicit scenario has an undefined step
                    Given I do not have a matching definition
            """,
    )
    testdir.makepyfile(
        """\
        from pytest_cuke import scenario

        @scenario("unmatched.feature", "Explicit scenario has an undefined step")
        def test_unmatched_explicit_scenario():
            pass
        """
    )

    result = testdir.runpytest_subprocess()

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    output = result.stdout.str() + result.stderr.str()
    assert "Explicit scenarios with steps but no matching step definitions were found" in output
    assert "Given I do not have a matching definition" in output
    assert "PluggyTeardownRaisedWarning" not in output


def test_explicit_scenario_accepts_step_registered_in_overridden_registry_fixture(testdir):
    testdir.makeini(
        """\
        [pytest]
        cuke_autoload = false
        cuke_features_dir = .
        """
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        fixture_step="""\
            Feature: Dynamic step registry
                Scenario: Step is registered by the fixture
                    Given the fixture registers this step
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from types import SimpleNamespace

        from pytest_cuke import given
        from pytest_cuke.steps import Registry

        @pytest.fixture
        def step_registry():
            @given("the fixture registers this step")
            def fixture_registered_step():
                print("fixture step ran")
                return None

            return Registry(namespace=SimpleNamespace(fixture_registered_step=fixture_registered_step))
        """
    )
    testdir.makepyfile(
        # language=python
        """\
        from pytest_cuke import scenario

        @scenario("fixture_step.feature", "Step is registered by the fixture")
        def test_fixture_registered_step():
            pass
        """
    )

    result = testdir.runpytest_subprocess("-v", "-s")

    assert_outcomes(result, passed=1)
    result.stdout.fnmatch_lines(["*fixture step ran*"])


def test_scenarios_none_found(testdir, pytest_params):
    """Test scenarios shortcut when no scenarios found."""
    testpath = testdir.makepyfile(
        # language=python
        """\
        from pytest_cuke import scenarios

        test_feature = scenarios('.')
        """
    )
    result = testdir.runpytest_subprocess(testpath, *pytest_params)
    assert_outcomes(result, skipped=1)


def test_scenarios_none_found_inprocess(testdir):
    """Test scenarios shortcut when no scenarios found, in the same process."""
    testpath = testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import scenarios

        test_feature = scenarios('.')
        """
    )
    result = testdir.runpytest(testpath)
    assert_outcomes(result, skipped=1)
