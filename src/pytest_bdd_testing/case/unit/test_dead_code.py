"""Behavioral test: vulture dead-code scan (SIM-03).

Runs `vulture src/pytest_bdd/ --min-confidence 80` and asserts 0 findings.
Uses [tool.vulture] config from pyproject.toml (ignore_names, paths).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

VULTURE_AVAILABLE: bool
try:
    subprocess.run(
        [str(Path(sys.executable)), "-m", "vulture", "--version"],
        check=True,
        capture_output=True,
        timeout=10,
    )
    VULTURE_AVAILABLE = True
except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
    VULTURE_AVAILABLE = False


@pytest.mark.skipif(not VULTURE_AVAILABLE, reason="vulture not installed")
def test_vulture_clean():
    """vulture reports zero dead-code findings in src/pytest_bdd/."""
    vulture_command = [
        str(Path(sys.executable)),
        "-m",
        "vulture",
        "src/pytest_bdd/",
        "--min-confidence",
        "80",
    ]
    result = subprocess.run(
        vulture_command,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout.strip()
    stderr = result.stderr.strip()

    # vulture exits 0 when no dead code found, non-zero otherwise
    # But it may also exit 0 with findings printed to stdout
    findings = [line for line in output.splitlines() if line.strip() and not line.startswith("vulture")]

    assert result.returncode == 0, (
        f"vulture exited with code {result.returncode}:\n"
        f"stdout:\n{output}\n"
        f"stderr:\n{stderr}\n\n"
        f"Remove the dead code or add to [tool.vulture] ignore_names in pyproject.toml."
    )

    assert len(findings) == 0, (
        f"vulture found {len(findings)} dead-code item(s) at 80%+ confidence:\n"
        + "\n".join(findings)
        + "\n\nRemove the dead code or add to [tool.vulture] ignore_names in pyproject.toml."
    )


@pytest.mark.skipif(not VULTURE_AVAILABLE, reason="vulture not installed")
def test_vulture_config_exists():
    """pyproject.toml has [tool.vulture] section with min_confidence = 80."""
    toml_path = Path("pyproject.toml")
    content = toml_path.read_text(encoding="utf-8")
    assert "[tool.vulture]" in content, (
        "[tool.vulture] section not found in pyproject.toml. Add vulture configuration or update this test."
    )
    assert "min_confidence" in content, (
        "min_confidence not found in [tool.vulture] section. Add min_confidence = 80 or update this test."
    )
