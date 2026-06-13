"""

Provide test report doc gathering html helpers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd import scenario

pytestmark = [pytest.mark.slow]


@scenario(
    Path(__file__).resolve().parents[4] / "features" / "07 Report" / "02 Gathering.feature.md",
    "HTML report could be produced on the feature run",
)
def test_html_report_generation_from_markdown_doc():
    """
    Verify html report generation from markdown doc.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
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
