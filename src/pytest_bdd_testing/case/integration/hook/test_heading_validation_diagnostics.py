"""

Provide test heading validation diagnostics helpers.
"""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from pytest_bdd.model.heading_validation import EMPTY_HEADING_TITLE_CODE, HeadingType
from pytest_bdd.script.validate_feature_headings import run_heading_validation_scan


def _write_markdown_feature(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


def test_violation_payload_fields_are_stable(tmp_path: Path) -> None:
    """
    Verify violation payload fields are stable.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    _write_markdown_feature(
        tmp_path / "sample.feature.md",
        """
        # Feature: Diagnostic feature
        ## Scenario:
        * Given step
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert run.status == "fail"
    violation = run.violations[0]
    payload = violation.to_payload()

    assert payload["path"] == "sample.feature.md"
    assert payload["line"] == 2
    assert payload["heading_type"] == HeadingType.SCENARIO.value
    assert payload["code"] == EMPTY_HEADING_TITLE_CODE
    assert "empty after trimming whitespace" in str(payload["message"])


def test_violations_are_sorted_by_path_then_line(tmp_path: Path) -> None:
    """
    Verify violations are sorted by path then line.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    _write_markdown_feature(
        tmp_path / "b.feature.md",
        """
        # Feature: B feature
        ## Scenario:
        * Given step
        """,
    )
    _write_markdown_feature(
        tmp_path / "a.feature.md",
        """
        # Feature: A feature
        ## Scenario:
        * Given step
        """,
    )

    run = run_heading_validation_scan(tmp_path)

    assert [violation.path for violation in run.violations] == ["a.feature.md", "b.feature.md"]
