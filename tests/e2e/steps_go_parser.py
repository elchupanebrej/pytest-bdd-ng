import pytest
from pytest_bdd import given, step, then

from pytest_bdd._gherkin_go._bridge import gherkin_go_available, gherkin_go_version


@given("Go parser shared library is built")
def go_parser_built():
    if not gherkin_go_available():
        pytest.skip("Go parser not available")


@given("Go parser is not available")
def go_parser_not_available(monkeypatch):
    monkeypatch.setattr("pytest_bdd._gherkin_go._bridge.gherkin_go_available", lambda: False)
    monkeypatch.setattr("pytest_bdd._gherkin_go.gherkin_go_available", lambda: False)


@then("Go parser version is logged")
def go_parser_version_logged():
    assert isinstance(gherkin_go_version(), str)
    assert len(gherkin_go_version()) > 0


@step("run pytest with Go backend", target_fixture="pytest_result")
def run_pytest_go(testdir, monkeypatch):
    monkeypatch.setenv("PYTEST_BDD_GHERKIN_BACKEND", "go")
    return testdir.runpytest_inprocess()


@step("run pytest with Python backend", target_fixture="pytest_result")
def run_pytest_python(testdir, monkeypatch):
    monkeypatch.setenv("PYTEST_BDD_GHERKIN_BACKEND", "python")
    return testdir.runpytest_inprocess()
