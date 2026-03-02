from __future__ import annotations

import json
import os
import subprocess  # noqa: S404
import sys
from pathlib import Path

import pytest

from pytest_bdd.script.message_capability_governance import main

if not os.environ.get("PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT"):
    pytest.skip(
        "messages coverage audit suite is opt-in; set PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 to run it",
        allow_module_level=True,
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
DECISIONS_FILE = REPO_ROOT / "specs/008-maximize-messages-coverage/contracts/capability-decisions.json"
GOVERNANCE_SCHEMA = REPO_ROOT / "specs/008-maximize-messages-coverage/contracts/governance-report.schema.json"
MANDATORY_FILE = REPO_ROOT / "specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt"
MIN_IMPLEMENTED_CAPABILITIES = 20


def test_messages_capabilities_are_implemented_or_governed(tmp_path: Path) -> None:
    messages_file = tmp_path / "messages-e2e.ndjson"
    report_file = tmp_path / "governance-e2e.json"

    subprocess_env = dict(os.environ)
    subprocess_env["PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT"] = "1"

    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/messages_coverage/test_mandatory_attachments.py",
            "-q",
            "-p",
            "no:pytest-bdd-gherkin-message-reporter",
            "-p",
            "pytest_bdd.plugin.gherkin_message_reporter.entrypoint",
            "--messages-ndjson",
            str(messages_file),
            "--messages-coverage",
        ],
        env=subprocess_env,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        msg = f"Dedicated messages coverage suite failed.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        raise AssertionError(msg)

    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--baseline-release",
            "v32.current",
            "--schema",
            str(GOVERNANCE_SCHEMA),
            "--decisions",
            str(DECISIONS_FILE),
            "--mandatory-capabilities-file",
            str(MANDATORY_FILE),
            "--require-mandatory-implemented",
            "--require-fully-governed",
            "--output",
            str(report_file),
        ]
    )

    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["summary"]["blocked_capabilities"] == 0
    assert payload["summary"]["implemented_capabilities"] >= MIN_IMPLEMENTED_CAPABILITIES
    assert payload["summary"]["mandatory_capabilities_total"] == 323
    assert payload["summary"]["mandatory_capabilities_implemented"] == 323
    assert payload["summary"]["mandatory_scope_violations"] == 0
    assert all(capability["status"] != "Pending" for capability in payload["capabilities"])
