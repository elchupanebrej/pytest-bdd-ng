"""BDD steps for pytester child-local feature roots."""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

from pytest_cuke import given, then, when


@given("a pytester child has a plain Python test that checks its local feature root")
def pytester_child_has_plain_python_test(pytester: Any) -> None:
    pytester.makepyfile(
        test_child="""
from pathlib import Path


def test_feature_root_is_the_child_project_root(pytestconfig):
    feature_root = Path(pytestconfig.rootpath) / pytestconfig.getini("cuke_features_dir")
    assert feature_root.resolve() == Path(__file__).parent.resolve()
    assert feature_root.is_dir()
"""
    )


@given("the pytester child has a nonstandard config file without a feature-root setting")
def pytester_child_has_nonstandard_config(pytester: Any) -> None:
    project_path = getattr(pytester, "path", None)
    if project_path is None:
        project_path = pytester.tmpdir
    Path(str(project_path), "child-pytest.ini").write_text("[pytest]\n", encoding="utf-8")


@when(
    re.compile(r'I run the pytester child with arguments "(?P<arguments>[^"]*)"'),
    target_fixture="pytester_child_result",
)
def run_pytester_child(arguments: str, pytester: Any) -> Any:
    return pytester.runpytest_subprocess(*shlex.split(arguments))


@then("the pytester child should have one passing test")
def pytester_child_has_one_passing_test(pytester_child_result: Any) -> None:
    pytester_child_result.assert_outcomes(passed=1)


@then("the pytester child should report its selected missing feature root")
def pytester_child_reports_missing_feature_root(pytester_child_result: Any) -> None:
    assert pytester_child_result.ret != 0
    output = f"{pytester_child_result.stdout.str()}\n{pytester_child_result.stderr.str()}"
    assert "missing-features" in output
    assert "does not exist" in output
