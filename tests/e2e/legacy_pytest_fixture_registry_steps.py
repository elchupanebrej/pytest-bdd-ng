"""BDD steps for pytest versions that unwrap fixture functions during collection."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Any

from pytest_cuke import given, then, when


@given("a pytester child has parent steps and a child fixture override")
def pytester_child_has_parent_steps_and_child_override(testdir: Any) -> None:
    testdir.makeconftest(
        dedent(
            """\
            from pytest_cuke import given

            @given("I have a parent fixture", target_fixture="parent")
            def parent():
                return "parent"

            @given("I have an overridable fixture", target_fixture="overridable")
            def overridable():
                return "parent"
            """
        )
    )

    child = testdir.mkpydir("child")
    child.join("conftest.py").write(
        dedent(
            """\
            from pytest_cuke import given

            @given("I have an overridable fixture", target_fixture="overridable")
            def overridable():
                return "child"
            """
        )
    )

    feature_path = Path(str(testdir.tmpdir)) / "parent-and-child.feature"
    feature_path.write_text(
        dedent(
            """\
            Feature: Parent and child fixtures
              Scenario: Child fixture wins
                Given I have a parent fixture
                And I have an overridable fixture
            """
        ),
        encoding="utf-8",
    )
    child.join("test_parent_and_child.py").write(
        dedent(
            f"""\
            from pathlib import Path
            from pytest_cuke import scenario

            @scenario(Path(r"{feature_path}"), "Child fixture wins", features_base_dir="child")
            def test_parent_and_child_steps(request):
                assert request.getfixturevalue("parent") == "parent"
                assert request.getfixturevalue("overridable") == "child"
            """
        )
    )


@when("I run the pytester child in a subprocess", target_fixture="pytester_child_result")
def run_pytester_child_in_subprocess(testdir: Any) -> Any:
    return testdir.runpytest_subprocess("child/test_parent_and_child.py", "-q")


@then("the pytester child should pass its parent and override scenario")
def pytester_child_passes_parent_and_override_scenario(pytester_child_result: Any) -> None:
    pytester_child_result.assert_outcomes(passed=1)
