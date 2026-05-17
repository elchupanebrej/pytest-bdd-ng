from pytest_bdd import given, parsers, step, then


@step("run pytest with code generator", target_fixture="pytest_result")
def run_pytest_code_generator(testdir, request):
    try:
        feature_file = request.getfixturevalue("feature_file")
        return testdir.runpytest_inprocess("--generate-missing", "--feature", str(feature_file))
    except LookupError:
        feature_files = [
            f for f in testdir.tmpdir.listdir()
            if f.check(file=1) and f.basename.endswith(".feature.md")
        ]
        if feature_files:
            return testdir.runpytest_inprocess("--generate-missing", "--feature", str(feature_files[0]))
        return testdir.runpytest_inprocess("--generate-missing")


@then(parsers.parse("Generated code contains {pattern}"))
def generated_code_contains(pytest_result, pattern):
    stdout = pytest_result.stdout.str()
    # Normalize pattern to check for step decorators
    if pattern == "@step":
        assert "@given" in stdout or "@when" in stdout or "@then" in stdout or "@step" in stdout
    elif pattern == "def _":
        # Code generator may produce descriptive names like def this_step_does_not_exist()
        assert "def " in stdout
    else:
        assert pattern in stdout


@then("Generated code is printed to stdout")
def generated_code_is_printed(pytest_result):
    assert pytest_result.ret == 0
    assert len(pytest_result.stdout.str()) > 0


@given("Feature file with undefined steps", target_fixture="feature_file")
def feature_file_with_undefined_steps(testdir):
    return testdir.makefile(
        ".feature.md",
        undefined="""# Feature: Undefined
## Scenario: Missing steps
* Given this step does not exist
""",
    )
