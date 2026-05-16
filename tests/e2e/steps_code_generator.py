from pytest_bdd import given, parsers, step, then


@step("run pytest with code generator", target_fixture="pytest_result")
def run_pytest_code_generator(testdir, request):
    # the task action asks for --generate pointing to feature file
    feature_file = request.getfixturevalue("feature_file")
    return testdir.runpytest_inprocess("--generate", "--features", str(feature_file))


@then(parsers.parse("Generated code contains {pattern}"))
def generated_code_contains(pytest_result, pattern):
    assert pattern in pytest_result.stdout.str()


@then("Generated code is printed to stdout")
def generated_code_is_printed(pytest_result):
    assert pytest_result.ret == 0
    assert len(pytest_result.stdout.str()) > 0


@given("Feature file with undefined steps", target_fixture="feature_file")
def feature_file_with_undefined_steps(testdir):
    return testdir.makefile(".feature.md", undefined="""# Feature: Undefined
## Scenario: Missing steps
Given this step does not exist
""")
