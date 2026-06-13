"""

Provide test spec prefix resolution helpers.
"""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
COMMON_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "common.sh"
CHECK_PREREQUISITES_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
CREATE_FEATURE_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "create-new-feature.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_common_script_contains_prefix_lookup_function() -> None:
    """
    Verify common script contains prefix lookup function.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    script_text = _read(COMMON_SCRIPT)
    assert "find_feature_dir_by_prefix" in script_text


def test_check_prerequisites_supports_paths_json_mode() -> None:
    """
    Verify check prerequisites supports paths json mode.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    script_text = _read(CHECK_PREREQUISITES_SCRIPT)
    assert "--paths-only" in script_text
    assert "FEATURE_DIR" in script_text
    assert "TASKS" in script_text


def test_create_new_feature_contains_monotonic_prefix_logic() -> None:
    """
    Verify create new feature contains monotonic prefix logic.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    script_text = _read(CREATE_FEATURE_SCRIPT)
    assert "check_existing_branches" in script_text
    assert "FEATURE_NUM" in script_text
