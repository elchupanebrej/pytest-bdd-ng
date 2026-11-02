import json


def test_configured_ci_environment_reaches_real_messages(pytester, monkeypatch):
    """Exercise native metadata emission; the supplied CI coordinates are test inputs."""
    environment = {
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "example/project-under-test",
        "GITHUB_RUN_ID": "42",
        "GITHUB_HEAD_REF": "branch-under-test",
        "GITHUB_SHA": "a" * 40,
        "GITHUB_REF": "refs/tags/release-under-test",
    }
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_autoload = true\ncuke_parser = python\n")
    pytester.makefile(".feature", ci="Feature: Metadata\n  Scenario: Passes\n    Given a step\n")
    pytester.makeconftest('from pytest_cuke import given\n@given("a step")\ndef a_step():\n    pass\n')
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(passed=1)
    messages = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    metadata = next(message["meta"] for message in messages if "meta" in message)
    assert metadata["ci"] == {
        "name": "GitHub Actions",
        "url": "https://github.com/example/project-under-test/actions/runs/42",
        "buildNumber": "42",
        "git": {
            "branch": "branch-under-test",
            "remote": "https://github.com/example/project-under-test.git",
            "revision": "a" * 40,
            "tag": "release-under-test",
        },
    }
