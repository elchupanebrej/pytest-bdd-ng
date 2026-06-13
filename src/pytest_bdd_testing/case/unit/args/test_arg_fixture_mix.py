"""

Provide test arg fixture mix helpers.
"""

from __future__ import annotations

from textwrap import dedent

import pytest

pytestmark = [pytest.mark.unit]


def test_arg_fixture_mix(testdir, tmp_path):
    """
    Verify arg fixture mix.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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
    subdir = testdir.mkpydir("arg_fixture_mix")
    subdir.join("test_a.py").write(
        dedent(
            # language=python
            f"""\
            import pytest
            from pytest_bdd import scenario, given, then, parsers
            from pathlib import Path

            @pytest.fixture
            def foo():
                return "fine"

            @scenario(
                Path(r"{tmp_path}") / "arg_and_fixture_mix.feature",
                'Use the step argument with the same name as fixture of another test',
            )
            def test_args():
                pass

            @given(parsers.parse('foo is "{{foo}}"'))
            def foo1(foo):
                pass

            @then(parsers.parse('foo should be "{{foo_value}}"'))
            def foo_should_be(foo, foo_value):
                assert foo == foo_value

            @scenario(
                Path(r"{tmp_path}") / "arg_and_fixture_mix.feature", 'Everything is fine',
            )
            def test_bar():
                pass

            @given('it is all fine')
            def fine():
                return "fine"

            @then('foo should be fine')
            def foo_should_be_fine(foo):
                assert foo == "fine"
            """,
        ),
    )

    subdir.join("test_b.py").write(
        dedent(
            # language=python
            f"""\
            import pytest
            from pytest_bdd import scenario, given, then
            from pathlib import Path

            @scenario(
                Path(r"{tmp_path}") / "arg_and_fixture_mix.feature", 'Everything is fine',
            )
            def test_args():
                pass

            @pytest.fixture
            def foo():
                return "fine"

            @given('it is all fine')
            def fine():
                return "fine"

            @then('foo should be fine')
            def foo_should_be(foo):
                assert foo == "fine"

            def test_bar(foo):
                assert foo == 'fine'
            """,
        ),
    )

    with (tmp_path / "arg_and_fixture_mix.feature").open(mode="w+") as f:
        f.write(
            dedent(
                # language=gherkin
                """\
                Feature: Arg and fixture mix
                    Scenario: Use the step argument with the same name as fixture of another test
                        Given foo is "Hello"
                        Then foo should be "Hello"


                    Scenario: Everything is fine
                        Given it is all fine
                        Then foo should be fine
                """,
            ),
        )
        f.flush()

    result = testdir.runpytest("-k arg_fixture_mix")
    result.assert_outcomes(passed=4)
