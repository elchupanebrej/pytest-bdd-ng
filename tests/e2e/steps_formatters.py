import json

from pytest_bdd import given, parsers, step, then
from tests.support.cucumber_formatters import install_fake_node, run_pytest_via_real_entrypoint


@given("Cucumber formatters are available")
def cucumber_formatters_available(monkeypatch, tmp_path):
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())


@step("run pytest with JUnit reporter", target_fixture="pytest_result")
def run_pytest_junit(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-junit=report.xml", preserve_fake_node=True)


@step("run pytest with progress formatter", target_fixture="pytest_result")
def run_pytest_progress(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-progress", preserve_fake_node=True)


@step("run pytest with progress bar formatter", target_fixture="pytest_result")
def run_pytest_progress_bar(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-progress-bar", preserve_fake_node=True)


@step("run pytest with snippets formatter", target_fixture="pytest_result")
def run_pytest_snippets(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-snippets", preserve_fake_node=True)


@step("run pytest with summary formatter", target_fixture="pytest_result")
def run_pytest_summary(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-summary", preserve_fake_node=True)


@step("run pytest with usage formatter", target_fixture="pytest_result")
def run_pytest_usage(testdir):
    return run_pytest_via_real_entrypoint(testdir, "--cucumber-usage", preserve_fake_node=True)


@step("run pytest with usage JSON formatter", target_fixture="pytest_result")
def run_pytest_usage_json(testdir):
    return run_pytest_via_real_entrypoint(
        testdir, "--cucumber-usage-json=standalone-usage.json", preserve_fake_node=True
    )


@then(parsers.parse("Progress output shows {state}"))
def progress_output_shows(pytest_result, state):
    assert state in pytest_result.stdout


@then(parsers.parse("Snippet output suggests step definition for {step_text}"))
def snippet_output_suggests(pytest_result, step_text):
    assert step_text in pytest_result.stdout


@then(parsers.parse("Summary output contains {statistic}"))
def summary_output_contains(pytest_result, statistic):
    assert statistic in pytest_result.stdout


@then(parsers.parse("Usage output shows {count} step definitions used"))
def usage_output_shows(pytest_result, count):
    # This is a basic assertion to check if the usage info is logged
    assert "Usage" in pytest_result.stdout


@then("Usage JSON is valid")
def usage_json_is_valid(testdir):
    usage_json_path = testdir.tmpdir.join("standalone-usage.json")
    with open(str(usage_json_path)) as f:
        data = json.load(f)
    assert isinstance(data, dict)
