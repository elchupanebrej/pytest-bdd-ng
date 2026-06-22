"""E2E BDD step definitions for testing development scripts/CLIs."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from hamcrest import assert_that, equal_to, greater_than, is_
from pytest_bdd import given, parsers, then

if TYPE_CHECKING:
    import subprocess
    from pytest_bdd.compatibility.pytest import Testdir


@given(parsers.parse('Mock file "{filename}" with content:'))
def mock_file_with_content(testdir: Testdir, filename: str, step: getattr) -> None:
    """Write content to a file in the test directory without modifying pytest.ini."""
    doc_string = getattr(step.argument, "doc_string", None) if getattr(step, "argument", None) else None
    content = doc_string.content if doc_string else ""
    target = Path(str(testdir.tmpdir)) / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


@then(parsers.parse("the command exit code is {exit_code:d}"))
def check_command_exit_code(renderer_result: subprocess.CompletedProcess[str], exit_code: int) -> None:
    """Verify the exit code of the last executed command."""
    assert_that(renderer_result.returncode, equal_to(exit_code))


@then(parsers.parse('directory "{dir_path}" must contain files matching "{pattern}"'))
def directory_must_contain_files(testdir: Testdir, dir_path: str, pattern: str) -> None:
    """Verify that a directory contains at least one file matching the pattern."""
    full_path = Path(str(testdir.tmpdir)) / dir_path
    assert_that(full_path.exists(), is_(True))
    assert_that(full_path.is_dir(), is_(True))
    matching = list(full_path.glob(pattern))
    assert_that(len(matching), greater_than(0), f"No files matching {pattern} found in {dir_path}")


@given(parsers.parse('the file "{filepath}" exists'))
def check_file_exists(filepath: str) -> None:
    """Verify that a file exists relative to the repository root."""
    repo_root = Path(__file__).resolve().parents[3]
    full_path = repo_root / filepath
    assert_that(full_path.exists(), is_(True), f"File {filepath} does not exist")


@then("its execution is reported as an architectural gap in BDD")
def report_architectural_gap() -> None:
    """Document/report the shell script as a BDD E2E execution gap."""
    # Log this as an explicit architectural gap to satisfy D-04
    import logging

    logging.getLogger(__name__).warning(
        "Architectural Gap: scripts/run_messages_coverage_audit.sh is a shell script "
        "and cannot be executed directly in Windows/native E2E tests.",
    )
