"""Behavioral test: ruff ERA001 — no commented-out code (SIM-03).

Runs `ruff check src/pytest_bdd/ --select ERA001` and asserts 0 violations.
ERA001 catches commented-out Python code (e.g. `# return None`).
"""

from __future__ import annotations

import subprocess  # noqa: S404
import sys
from pathlib import Path


class TestNoCommentedCode:
    """SIM-03: No commented-out code in source (ERA001 clean)."""

    def test_ruff_era001_clean(self):
        """ruff ERA001 reports zero violations in src/pytest_bdd/."""
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "ruff", "check", "src/pytest_bdd/", "--select", "ERA001"],
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

    def test_ruff_era001_is_configured(self):
        """ERA rule is in pyproject.toml [tool.ruff.lint].select."""
        toml_path = Path("pyproject.toml")
        content = toml_path.read_text(encoding="utf-8")
        assert '"ERA"' in content or "'ERA'" in content, (
            "ERA rule (eradicate) not found in pyproject.toml [tool.ruff.lint].select. "
            "If ERA001 is removed from the config, this test should be updated."
        )
