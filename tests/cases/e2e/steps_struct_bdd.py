import pytest

from pytest_bdd import given, parsers, step, then
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED

if not STRUCT_BDD_INSTALLED:
    pytest.skip("StructBDD not installed", allow_module_level=True)


@given(parsers.parse("StructBDD format is {fmt}"), target_fixture="struct_bdd_file")
def struct_bdd_format(testdir, fmt):
    testdir.makeini("""
[pytest]
bdd_features_base_dir = .
    """)
    content = ""
    if fmt == "yaml":
        content = (
            "Name: StructBDD Feature\nSteps:\n  - Step:\n      Name: Scenario\n      Steps:\n        - Given: a step"
        )
        return testdir.makefile(".bdd.yaml", test=content)
    if fmt == "json":
        content = (
            '{"Name": "StructBDD Feature", "Steps": [{"Step": {"Name": "Scenario", "Steps": [{"Given": "a step"}]}}]}'
        )
        return testdir.makefile(".bdd.json", test=content)
    if fmt == "hocon":
        content = 'Name = "StructBDD Feature"\nSteps = [{Step = {Name = "Scenario", Steps = [{"Given": "a step"}]}}]'
        return testdir.makefile(".bdd.hocon", test=content)
    if fmt == "toml":
        content = (
            'Name = "StructBDD Feature"\n'
            "[[Steps]]\n"
            "[Steps.Step]\n"
            'Name = "Scenario"\n'
            "[[Steps.Step.Steps]]\n"
            'Given = "a step"'
        )
        return testdir.makefile(".bdd.toml", test=content)
    return testdir.makefile(
        ".bdd.yaml",
        test="Name: Default\nSteps:\n  - Step:\n      Name: Scenario\n      Steps:\n        - Action: a step",
    )


@given("StructBDD parse error occurs", target_fixture="struct_bdd_file")
def struct_bdd_parse_error(testdir):
    content = "Invalid StructBDD: [}"
    return testdir.makefile(".bdd.yaml", struct=content)


@given("StructBDD is not installed")
def struct_bdd_not_installed(monkeypatch):
    monkeypatch.setattr("pytest_bdd.compatibility.struct_bdd.STRUCT_BDD_INSTALLED", False)


@then("skipped gracefully")
def skipped_gracefully(pytest_result):
    stdout = pytest_result.stdout.str()
    assert "skipped" in stdout.lower() or "no tests ran" in stdout.lower()


@then("StructBDD deserialization fails with expected error")
def struct_bdd_deserialization_fails_expected(pytest_result):
    stdout = pytest_result.stdout.str()
    stderr = pytest_result.stderr.str()
    combined = stdout + stderr
    assert "error" in combined.lower() or "failed" in combined.lower() or "invalid" in combined.lower()


@step("run pytest with StructBDD feature", target_fixture="pytest_result")
def run_pytest_struct_bdd(testdir, struct_bdd_file):
    return testdir.runpytest_inprocess("--features", str(struct_bdd_file))


@then("print pytest output")
def print_pytest_output(pytest_result):
    print("STDOUT:", pytest_result.stdout.str())  # noqa: T201
    print("STDERR:", pytest_result.stderr.str())  # noqa: T201
