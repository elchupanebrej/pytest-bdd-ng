import pytest


@pytest.mark.parametrize("source", ['"stories"', 'Path("stories")'])
def test_explicit_directory_discovers_hook_registered_extensions(pytester, source):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    directory = pytester.path / "stories" / "nested"
    directory.mkdir(parents=True)
    (directory / "custom.story").write_text("Feature: Custom\n  Scenario: Custom\n    Given a working step\n")
    (directory / "standard.feature").write_text("Feature: Standard\n  Scenario: Standard\n    Given a working step\n")
    (directory / "notes.txt").write_text("This file is not a scenario.")
    pytester.makeconftest("""
import pytest
from pytest_cuke import given
@pytest.hookimpl(tryfirst=True)
def pytest_cuke_get_mimetype(config, path):
    if path.suffix == ".story":
        return "text/x.cucumber.gherkin+plain"
@given("a working step")
def step():
    pass
""")
    pytester.makepyfile(
        test_scenarios=f"""
from pathlib import Path
from pytest_cuke import scenarios
test = scenarios({source}, features_base_dir=".")
"""
    )
    result = pytester.runpytest_subprocess("-q")
    result.assert_outcomes(passed=2)
