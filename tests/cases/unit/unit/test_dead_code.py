"""Behavioral test: vulture dead-code check at 80%+ confidence (SIM-03).

Known false positives (pytest hooks, TYPE_CHECKING imports, protocol parameters)
are allowlisted. Any new finding NOT in the allowlist fails the test.
"""

from __future__ import annotations

import subprocess  # noqa: S404
import sys
from pathlib import Path

import pytest

SRC_ROOT = Path("src/pytest_bdd")

# Known false positives at 80%+ confidence.
# These are expected and must not cause a test failure.
# Each entry: (file_path, line, message_fragment).
# The message_fragment is matched case-insensitively via `in`.

KNOWN_FALSE_POSITIVES: set[tuple[str, int, str]] = {
    # TYPE_CHECKING imports (used in string-forward-reference only)
    ("hook.py", 21, "FunctionType"),
    ("feature_binding.py", 32, "GherkinDocumentWithURI"),
    ("message_converter.py", 10, "AttrsInstance"),
    ("session.py", 27, "Traversable"),
    ("definition.py", 33, "FunctionType"),
    ("inspect_extra.py", 11, "CodeType"),
    ("inspect_extra.py", 11, "FrameType"),
    ("inspect_extra.py", 11, "FunctionType"),
    ("inspect_extra.py", 11, "MethodType"),
    ("inspect_extra.py", 11, "TracebackType"),
    # Protocol/pytest hook parameter names (dynamic dispatch)
    ("compatibility/pytest/__init__.py", 135, "fixturemanager"),
    ("message_stream.py", 39, "event"),
    ("message_stream.py", 45, "controller"),
    ("plugin.py", 62, "fixturefunc"),  # pickle_runner/plugin.py
    ("plugin.py", 185, "nextitem"),  # pickle_runner/plugin.py
    ("plugin.py", 284, "module_path"),  # scenario_test_collector/plugin.py
    ("plugin.py", 309, "manager"),  # scenario_test_collector/plugin.py
    ("plugin.py", 169, "module_path"),  # struct_bdd/plugin.py
    # String-forward-reference cast("Match", ...)
    ("parsers.py", 9, "Match"),
}

pytestmark = [pytest.mark.unit]


def _run_vulture() -> list[str]:
    """Run vulture at 80% confidence, return stdout lines."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "vulture", str(SRC_ROOT), "--min-confidence", "80"],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout.splitlines()


def _parse_vulture_line(line: str) -> tuple[str, int, str] | None:
    """Parse a vulture output line into (file, line_no, message).

    Lines look like:
        src\\pytest_bdd\\hook.py:21: unused import 'FunctionType' (90% confidence)
    Path separators vary by platform; we normalise to forward slashes.
    """
    line = line.strip()
    if not line:
        return None
    # Split at the first colon after ".py" to separate: file_path_part : rest
    # Vulture format: path:line: message
    try:
        # Find position of ":<digits>:" which marks line number
        import re

        m = re.match(r"^(.+?):(\d+):\s*(.+)$", line)
        if not m:
            return None
        file_path = m.group(1)
        line_no = int(m.group(2))
        message = m.group(3).strip()
        # Normalise path separators and strip "src/pytest_bdd/" prefix
        file_path = file_path.replace("\\", "/")
    except (ValueError, IndexError):
        return None
    else:
        prefix = "src/pytest_bdd/"
        file_path = file_path.removeprefix(prefix)
        return (file_path, line_no, message)


def _is_known_false_positive(parsed: tuple[str, int, str]) -> bool:
    """Check if a parsed finding matches any known false positive."""
    file_path, line_no, message = parsed
    for fp_file, fp_line, fp_msg in KNOWN_FALSE_POSITIVES:
        if line_no != fp_line:
            continue
        if fp_msg.lower() not in message.lower():
            continue
        # File match: the parsed path must end with fp_file
        if file_path.endswith(fp_file):
            return True
    return False


class TestVultureDeadCode:
    """SIM-03: No dead code at vulture 80%+ confidence."""

    def test_vulture_only_reports_known_false_positives(self):
        """vulture 80%+ output contains ONLY allowlisted false positives."""
        lines = _run_vulture()
        unknown: list[str] = []

        for raw_line in lines:
            parsed = _parse_vulture_line(raw_line)
            if parsed is None:
                continue  # skip empty/header lines
            if not _is_known_false_positive(parsed):
                unknown.append(raw_line)

        assert unknown == [], (
            f"vulture found {len(unknown)} unknown dead-code item(s) "
            f"at 80%+ confidence:\n"
            + "\n".join(f"  {item}" for item in unknown)
            + "\n\nEither remove the dead code or add to KNOWN_FALSE_POSITIVES."
        )

    def test_vulture_runs_without_error(self):
        """vulture does not crash or produce stderr errors."""
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "vulture", str(SRC_ROOT), "--min-confidence", "80"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # vulture may write warnings to stderr but should exit 0 or 3
        # Exit 0 = clean, Exit 3 = findings found (our known false positives)
        assert result.returncode in {0, 3}, f"vulture exited with code {result.returncode}\nstderr:\n{result.stderr}"

    @pytest.mark.parametrize("fp_entry", KNOWN_FALSE_POSITIVES)
    def test_known_false_positive_still_present(self, fp_entry: tuple[str, int, str]):
        """Regression: each allowlisted false positive still appears in vulture output.

        If a false-positive entry disappears (because the dead code was actually
        removed), the entry should be cleaned from KNOWN_FALSE_POSITIVES to keep
        the allowlist accurate. This test reminds you to do that.
        """
        file_path, line_no, message = fp_entry
        lines = _run_vulture()
        found = False
        for raw_line in lines:
            parsed = _parse_vulture_line(raw_line)
            if parsed is None:
                continue
            if _is_known_false_positive(parsed) and parsed == (file_path, line_no, message):
                found = True
                break
            # Also check: does any parsed line match this entry?
            pf, pl, pm = parsed
            if pl == line_no and file_path in pf and message.lower() in pm.lower():
                found = True
                break

        if not found:
            pytest.fail(
                f"Known false-positive entry no longer found by vulture:\n"
                f"  File: {file_path}:{line_no}\n"
                f"  Message: {message}\n\n"
                f"Remove this entry from KNOWN_FALSE_POSITIVES in test_dead_code.py.",
            )
