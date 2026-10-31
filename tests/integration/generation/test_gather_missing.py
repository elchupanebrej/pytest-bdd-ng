"""The canonical gather command preserves the machine consumer contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest


@pytest.fixture
def project(tmp_path):
    (tmp_path / "features").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\ncuke_features_dir = features\ncuke_parser = python\n")
    (tmp_path / "conftest.py").write_text(
        "from pathlib import Path\n"
        "import pytest\n"
        "from pytest_cuke import given\n"
        "@given('known step')\n"
        "def known(): pass\n"
        "@pytest.fixture(autouse=True)\n"
        "def lifecycle():\n"
        "    Path('setup.marker').write_text('setup')\n"
        "    yield\n"
        "    Path('teardown.marker').write_text('teardown')\n"
    )
    (tmp_path / "tests/test_binding.py").write_text(
        "from pathlib import Path\n"
        "from pytest_cuke import scenario\n"
        "@scenario(Path('features/probe.feature'), 'bound', features_base_dir='.')\n"
        "def test_bound(): Path('executed.marker').write_text('executed')\n"
    )
    return tmp_path


def gather(project, *, select_features=True):
    environment = os.environ.copy()
    environment.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
    options = {
        "cwd": project,
        "env": environment,
        "capture_output": True,
        "text": True,
        "timeout": 120,
    }
    if not select_features:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-c",
                "pytest.ini",
                "--rootdir=.",
                "--confcutdir=.",
                "--cuke-no-autoload",
                "--cuke-parser=python",
                "--cuke-gather-missing-steps",
                "tests/test_binding.py",
            ],
            check=False,
            **options,
        )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pytest.ini",
            "--rootdir=.",
            "--confcutdir=.",
            "--cuke-no-autoload",
            "--cuke-parser=python",
            "--cuke-gather-missing-steps",
            "--cuke-feature",
            "features/probe.feature",
            "tests/test_binding.py",
        ],
        check=False,
        **options,
    )


def test_gather_reports_named_scenarios_and_steps_as_ndjson_without_running_bodies(project):
    feature = project / "features/probe.feature"
    feature.write_text(
        "Feature: Machine consumer\n"
        "  Scenario: bound\n"
        "    Given known step\n"
        "    Then missing result\n"
        "  Scenario: unbound\n"
        "    Given missing context\n"
    )
    result = gather(project)
    assert result.returncode == 100, result.stdout + result.stderr
    assert [json.loads(line) for line in result.stdout.splitlines() if line.strip()] == [
        {"type": "missing_scenario_binding", "feature": str(feature), "scenario": "unbound", "line": 5},
        {
            "type": "missing_step_definition",
            "feature": str(feature),
            "scenario": "bound",
            "keyword": "Then",
            "text": "missing result",
            "line": 4,
        },
    ]
    assert not (project / "executed.marker").exists()
    assert (project / "setup.marker").read_text() == "setup"
    assert (project / "teardown.marker").read_text() == "teardown"


def test_gather_clean_project_has_zero_status_and_empty_event_stream(project):
    feature = project / "features/probe.feature"
    feature.write_text("Feature: Machine consumer\n  Scenario: bound\n    Given known step\n")
    result = gather(project)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stdout.strip()
    assert not (project / "executed.marker").exists()


def test_gather_reports_a_bound_scenario_with_no_matching_definitions(project):
    feature = project / "features/probe.feature"
    feature.write_text("Feature: Machine consumer\n  Scenario: bound\n    Given missing context\n")
    result = gather(project)
    assert result.returncode == 100, result.stdout + result.stderr
    assert [json.loads(line) for line in result.stdout.splitlines() if line.strip()] == [
        {
            "type": "missing_step_definition",
            "feature": str(feature),
            "scenario": "bound",
            "keyword": "Given",
            "text": "missing context",
            "line": 3,
        }
    ]
    assert not (project / "executed.marker").exists()


def test_gather_does_not_report_unselected_features(project):
    feature = project / "features/probe.feature"
    feature.write_text("Feature: Machine consumer\n  Scenario: bound\n    Given known step\n")
    (project / "features/unselected.feature").write_text(
        "Feature: Unselected\n  Scenario: unbound\n    Given other missing step\n"
    )
    result = gather(project)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stdout.strip()


def test_gather_keeps_each_missing_step_scenario_and_source_position(project):
    feature = project / "features/probe.feature"
    feature.write_text(
        "Feature: Machine consumer\n"
        "  Scenario: bound\n"
        "    Given known step\n"
        "    Then shared missing result\n"
        "  Scenario: other\n"
        "    Given known step\n"
        "    Then shared missing result\n"
    )
    with (project / "tests/test_binding.py").open("a") as target:
        target.write(
            "@scenario(Path('features/probe.feature'), 'other', features_base_dir='.')\n"
            "def test_other(): Path('executed.marker').write_text('executed')\n"
        )
    result = gather(project)
    assert result.returncode == 100, result.stdout + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert events == [
        {
            "type": "missing_step_definition",
            "feature": str(feature),
            "scenario": scenario,
            "keyword": "Then",
            "text": "shared missing result",
            "line": line,
        }
        for scenario, line in (("bound", 4), ("other", 7))
    ]
    assert not (project / "executed.marker").exists()


def test_gather_requires_explicit_feature_selection(project):
    result = gather(project, select_features=False)
    assert result.returncode == 100
    assert not result.stdout.strip()
    assert "--cuke-feature" in result.stderr


def test_gather_collection_errors_are_not_reported_as_a_clean_scan(project):
    feature = project / "features/probe.feature"
    feature.write_text("Feature: Machine consumer\n  Scenario: bound\n    Given known step\n")
    (project / "tests/test_binding.py").write_text("this is not valid Python!\n")
    result = gather(project)
    assert result.returncode not in {0, 100}
    assert not result.stdout.strip()
    assert "SyntaxError" in result.stderr


pytestmark = pytest.mark.integration
