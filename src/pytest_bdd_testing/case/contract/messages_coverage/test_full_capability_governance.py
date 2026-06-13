"""

Provide test full capability governance helpers.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pytest_bdd.script.message_capability_governance import main

pytestmark = pytest.mark.skipif(
    not os.environ.get("PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT"),
    reason="messages coverage audit suite is opt-in; set PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 to run it",
)

REPO_ROOT = Path(__file__).resolve().parents[5]
DECISIONS_FILE = REPO_ROOT / "specs/008-maximize-messages-coverage/contracts/capability-decisions.json"
GOVERNANCE_SCHEMA = REPO_ROOT / "specs/008-maximize-messages-coverage/contracts/governance-report.schema.json"
MANDATORY_FILE = REPO_ROOT / "specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt"
RUNTIME_REQUIRED_FILE = REPO_ROOT / "specs/008-maximize-messages-coverage/runtime-required-capability-ids.txt"
MIN_IMPLEMENTED_CAPABILITIES = 20
REQUIRED_BACKGROUND_DESCRIPTION_CAPABILITIES = (
    "gherkinDocument.feature.children.background.description",
    "gherkinDocument.feature.children.rule.children.background.description",
)
PROBE_CASES = (
    (
        "tests/messages_coverage/test_mandatory_attachments.py",
        False,
        {"GITHUB_REF": "refs/heads/coverage-audit", "GITHUB_REF_TYPE": "branch", "GITHUB_REF_NAME": "coverage-audit"},
    ),
    (
        "tests/messages_coverage/test_mandatory_attachments.py",
        False,
        {"GITHUB_REF": "refs/tags/v32.0.0", "GITHUB_REF_TYPE": "tag", "GITHUB_REF_NAME": "v32.0.0"},
    ),
    ("tests/messages_coverage/probes/test_failing_step_runtime.py", True, {}),
    ("tests/messages_coverage/probes/test_undefined_parameter_runtime.py", True, {}),
    ("tests/messages_coverage/probes/test_parse_error_runtime.py", True, {}),
)


def _run_capture_case(
    *,
    messages_file: Path,
    env: dict[str, str],
    target: str,
    expect_failure: bool,
    env_overrides: dict[str, str],
) -> None:
    effective_env = dict(env)
    effective_env.update(env_overrides)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            target,
            "-q",
            "--messages-ndjson",
            str(messages_file),
        ],
        env=effective_env,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if expect_failure:
        assert result.returncode != 0, (
            f"Probe expected failure but passed: {target}\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )
    elif result.returncode != 0:
        msg = f"Coverage capture failed.\nTarget: {target}\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        raise AssertionError(msg)


def test_messages_capabilities_are_implemented_or_governed(tmp_path: Path) -> None:
    """
    Verify messages capabilities are implemented or governed.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    messages_file = tmp_path / "messages-e2e.ndjson"
    report_file = tmp_path / "governance-e2e.json"

    subprocess_env = dict(os.environ)
    subprocess_env["PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT"] = "1"
    subprocess_env.update(
        {
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_RUN_NUMBER": "42",
            "GITHUB_RUN_ID": "4242",
            "GITHUB_REF": "refs/heads/coverage-audit",
            "GITHUB_REF_TYPE": "branch",
            "GITHUB_REF_NAME": "coverage-audit",
            "GITHUB_SHA": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            "GITHUB_SERVER_URL": "https://github.com",
            "GITHUB_REPOSITORY": "pytest-dev/pytest-bdd-ng",
        },
    )

    for target, expect_failure, env_overrides in PROBE_CASES:
        _run_capture_case(
            messages_file=messages_file,
            env=subprocess_env,
            target=target,
            expect_failure=expect_failure,
            env_overrides=env_overrides,
        )

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
            "--runtime-required-capabilities-file",
            str(RUNTIME_REQUIRED_FILE),
            "--require-runtime-required-covered",
            "--require-non-runtime-classified",
            "--require-fully-governed",
            "--output",
            str(report_file),
        ],
    )

    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["summary"]["blocked_capabilities"] == 0
    assert payload["summary"]["implemented_capabilities"] >= MIN_IMPLEMENTED_CAPABILITIES
    assert payload["summary"]["runtime_required_total"] == payload["summary"]["runtime_required_covered"]
    assert payload["summary"]["runtime_required_missing"] == 0
    assert payload["summary"]["non_runtime_required_total"] >= payload["summary"]["non_runtime_covered"]
    assert payload["summary"]["non_runtime_required_total"] >= payload["summary"]["non_runtime_classified"]
    assert payload["summary"]["mandatory_scope_violations"] == 0
    assert all(
        not capability["runtime_required"] or capability["observed_runtime"] for capability in payload["capabilities"]
    )
    assert all(capability["status"] != "Pending" for capability in payload["capabilities"])

    capabilities_by_id = {capability["capability_id"]: capability for capability in payload["capabilities"]}
    for capability_id in REQUIRED_BACKGROUND_DESCRIPTION_CAPABILITIES:
        capability = capabilities_by_id[capability_id]
        assert capability["observed_runtime"], f"{capability_id} must be covered by runtime evidence"
        assert capability["status"] == "Implemented"
