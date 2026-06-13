"""

Behavioral test: ruff ERA001 — no commented-out code (SIM-03).

Runs `ruff check src/pytest_bdd/ --select ERA001` and asserts 0 violations.
ERA001 catches commented-out Python code (e.g. `# return None`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]


def test_no_commented_code_ruff_era001_clean():
    """
    Ruff ERA001 reports zero violations in src/pytest_bdd/.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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
    ruff_command = [str(Path(sys.executable)), "-m", "ruff", "check", "src/pytest_bdd/", "--select", "ERA001"]
    result = subprocess.run(
        ruff_command,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout.strip()
    stderr = result.stderr.strip()

    # Build assertion message
    diagnostic = output or stderr

    assert result.returncode == 0, (
        f"ruff ERA001 found commented-out code violations (exit code {result.returncode}):\n"
        f"{diagnostic}\n\n"
        f"Remove or noqa the commented-out code. "
        f"See tests/unit/test_no_commented_code.py for details."
    )

    # Verify the expected "All checks passed!" message
    assert "All checks passed!" in output, (
        f"ruff ERA001 did not produce expected success message.\nstdout:\n{output}\nstderr:\n{stderr}"
    )


def test_no_commented_code_ruff_era001_is_configured():
    """
    ERA rule is in pyproject.toml [tool.ruff.lint].select.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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
    toml_path = Path("pyproject.toml")
    content = toml_path.read_text(encoding="utf-8")
    assert '"ERA"' in content or "'ERA'" in content, (
        "ERA rule (eradicate) not found in pyproject.toml [tool.ruff.lint].select. "
        "If ERA001 is removed from the config, this test should be updated."
    )
