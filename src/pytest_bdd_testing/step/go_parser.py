import pytest

from hamcrest import assert_that, greater_than, is_
from pytest_bdd import given, step, then
from pytest_bdd._gherkin_go._bridge import gherkin_go_available, gherkin_go_version
from pytest_bdd.util.data_table import data_table_to_dicts


@given("Go parser shared library is built")
def go_parser_built() -> None:
    if not gherkin_go_available():
        pytest.skip("Go parser not available")


@given("Go parser is not available")
def go_parser_not_available(monkeypatch) -> None:
    monkeypatch.setattr("pytest_bdd._gherkin_go._bridge.gherkin_go_available", lambda: False)
    monkeypatch.setattr("pytest_bdd._gherkin_go.gherkin_go_available", lambda: False)


@then("Go parser version is logged")
def go_parser_version_logged() -> None:
    assert_that(isinstance(gherkin_go_version(), str), is_(True))
    assert_that(len(gherkin_go_version()), greater_than(0))


@step("run pytest with environment:", target_fixture="pytest_result")
def run_pytest_with_environment(testdir, monkeypatch, step):
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    options = data_table_to_dicts(data_table)
    for name, values in options.items():
        monkeypatch.setenv(name, values[0])
    return testdir.runpytest_inprocess()
