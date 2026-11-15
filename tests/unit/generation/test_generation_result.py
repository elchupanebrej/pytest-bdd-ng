import json
import subprocess
import sys
from pathlib import Path

def _run(project: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest_cuke.cli", "generate", "steps", *arguments],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "features").mkdir(parents=True)
    (project / "features" / "one.feature").write_text(
        "Feature: Generation\n\n  Scenario: generated\n    Given a thing\n",
        encoding="utf-8",
    )
    (project / "steps.py").write_text("", encoding="utf-8")
    return project


def test_json_result_distinguishes_changed_and_unchanged(tmp_path):
    project = _project(tmp_path)

    changed = _run(project, "--feature", "features/one.feature", "--target", "steps.py", "--json")
    assert changed.returncode == 0, changed.stderr
    payload = json.loads(changed.stdout)
    assert payload["status"] == "changed"
    assert payload["target"] == str(project / "steps.py")
    assert payload["steps_added"] == 1
    assert "def step_a_thing" in (project / "steps.py").read_text(encoding="utf-8")

    unchanged = _run(project, "--feature", "features/one.feature", "--target", "steps.py", "--json")
    assert unchanged.returncode == 0, unchanged.stderr
    assert json.loads(unchanged.stdout) == {"status": "unchanged", "target": str(project / "steps.py")}


def test_json_result_reports_errors(tmp_path):
    project = _project(tmp_path)

    failed = _run(project, "--feature", "features/one.feature", "--target", "missing.py", "--json")

    assert failed.returncode == 2
    payload = json.loads(failed.stdout)
    assert payload["status"] == "error"
    assert "missing.py" in payload["error"]
    assert "missing.py" in failed.stderr
