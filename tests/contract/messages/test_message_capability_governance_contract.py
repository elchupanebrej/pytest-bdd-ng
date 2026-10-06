from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
POLICY_DIR = PROJECT_ROOT / "specs" / "message-capability-governance"
BASELINE_RELEASE = "28.0.0"
BASELINE_FILE = POLICY_DIR / "capabilities-v28-0-0.json"
DECISIONS_FILE = POLICY_DIR / "decisions-v28-0-0.json"
MANDATORY_FILE = POLICY_DIR / "mandatory-v28-0-0.txt"


def _run_cuke(*arguments: str) -> subprocess.CompletedProcess[str]:
    script_name = "cuke.exe" if os.name == "nt" else "cuke"
    scripts_directory = Path(sys.executable).absolute().parent
    candidate = scripts_directory / script_name
    executable = shutil.which("cuke") or (str(candidate) if candidate.is_file() else None)
    assert executable is not None, "the pytest-cuke public 'cuke' entry point must be installed for contract tests"
    result = subprocess.run(
        [executable, *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, f"cuke {' '.join(arguments)} failed:\n{result.stdout}\n{result.stderr}"
    return result


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_public_cli_reproduces_committed_messages_capability_policy(tmp_path: Path) -> None:
    generated_inventory = tmp_path / "capabilities.json"
    _run_cuke(
        "messages",
        "capabilities",
        "sync",
        "--baseline-release",
        BASELINE_RELEASE,
        "--output",
        str(generated_inventory),
    )
    assert _read_json(generated_inventory) == _read_json(BASELINE_FILE)

    normalized_decisions = tmp_path / "validated-decisions.json"
    _run_cuke(
        "messages",
        "capabilities",
        "validate-decision",
        "--input",
        str(DECISIONS_FILE),
        "--output",
        str(normalized_decisions),
    )
    decision_result = _read_json(normalized_decisions)
    policy_decisions = _read_json(DECISIONS_FILE)["decisions"]
    assert decision_result["decisions"] == policy_decisions

    baseline_diff = tmp_path / "baseline-diff.json"
    _run_cuke(
        "messages",
        "capabilities",
        "diff",
        "--previous-baseline",
        BASELINE_RELEASE,
        "--current-baseline",
        BASELINE_RELEASE,
        "--previous",
        str(BASELINE_FILE),
        "--current",
        str(BASELINE_FILE),
        "--previous-decisions",
        str(DECISIONS_FILE),
        "--current-decisions",
        str(DECISIONS_FILE),
        "--output",
        str(baseline_diff),
    )
    diff_result = _read_json(baseline_diff)
    assert all(not value for key, value in diff_result.items() if key.endswith("_ids"))

    checklist_json = tmp_path / "checklist.json"
    _run_cuke(
        "messages",
        "capabilities",
        "checklist",
        "--capabilities",
        str(BASELINE_FILE),
        "--decisions",
        str(DECISIONS_FILE),
        "--mandatory-capabilities-file",
        str(MANDATORY_FILE),
        "--format",
        "json",
        "--output",
        str(checklist_json),
    )
    checklist = _read_json(checklist_json)
    entries = checklist["entries"]
    assert isinstance(entries, list)
    entry_statuses = {entry["capability_id"]: entry["status"] for entry in entries}
    mandatory_ids = {
        line.strip()
        for line in MANDATORY_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert mandatory_ids
    assert all(entry_statuses[capability_id] == "Implemented" for capability_id in mandatory_ids)

    checklist_markdown = tmp_path / "checklist.md"
    _run_cuke(
        "messages",
        "capabilities",
        "checklist",
        "--capabilities",
        str(BASELINE_FILE),
        "--decisions",
        str(DECISIONS_FILE),
        "--mandatory-capabilities-file",
        str(MANDATORY_FILE),
        "--format",
        "markdown",
        "--output",
        str(checklist_markdown),
    )
    rendered = checklist_markdown.read_text(encoding="utf-8")
    assert "Cucumber Messages 28.0.0 governance checklist" in rendered
    assert all(f"`{capability_id}`" in rendered for capability_id in mandatory_ids)
