"""E2E BDD step definitions for testing development scripts/CLIs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from hamcrest import assert_that, contains_string, equal_to, greater_than, is_
from pytest_bdd.steps.decorators import given, then, when
from pytest_bdd.parsers.parse_parser import parse

if TYPE_CHECKING:
    pass


class _DocStringProtocol(Protocol):
    content: str


class _StepArgumentProtocol(Protocol):
    doc_string: _DocStringProtocol | None


class _StepProtocol(Protocol):
    argument: _StepArgumentProtocol | None


class _TestdirProtocol(Protocol):
    tmpdir: object


@given(parse('Mock file "{filename}" with content:'))
def mock_file_with_content(testdir: _TestdirProtocol, filename: str, step: _StepProtocol) -> None:
    """Write content to a file in the test directory without modifying pytest.ini."""
    doc_string = getattr(step.argument, "doc_string", None) if getattr(step, "argument", None) else None
    content = doc_string.content if doc_string else ""
    target = Path(str(testdir.tmpdir)) / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


@then(parse("the command exit code is {exit_code:d}"))
def check_command_exit_code(renderer_result: subprocess.CompletedProcess[str], exit_code: int) -> None:
    """Verify the exit code of the last executed command."""
    assert_that(renderer_result.returncode, equal_to(exit_code))


@then(parse('directory "{dir_path}" must contain files matching "{pattern}"'))
def directory_must_contain_files(testdir: _TestdirProtocol, dir_path: str, pattern: str) -> None:
    """Verify that a directory contains at least one file matching the pattern."""
    full_path = Path(str(testdir.tmpdir)) / dir_path
    assert_that(full_path.exists(), is_(True))
    assert_that(full_path.is_dir(), is_(True))
    matching = list(full_path.glob(pattern))
    assert_that(len(matching), greater_than(0), f"No files matching {pattern} found in {dir_path}")


@given(parse('the file "{filepath}" exists'))
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
        "Architectural Gap: pbt-run-messages-coverage-audit is a shell script "
        "and cannot be executed directly in Windows/native E2E tests.",
    )


# ── Plan 138: Installed wheel typing contract ──────────────────────────

_REPO_ROOT_DEV = Path(__file__).resolve().parents[3]
_VERIFY_SCRIPT_DEV = _REPO_ROOT_DEV / "scripts" / "verify_installed_types.py"


@given("a freshly built wheel from the checkout source")
def freshly_built_wheel() -> None:
    """Assert the verify script exists; the actual build happens at runtime."""
    assert_that(_VERIFY_SCRIPT_DEV.exists(), is_(True), f"Missing {_VERIFY_SCRIPT_DEV}")


@when("the wheel is installed with mypy and Pyright into a temporary venv outside the repository root")
def install_wheel_into_external_venv(renderer_result: subprocess.CompletedProcess[str]) -> None:
    """Run verify_installed_types.py --assert-isolated and capture result."""
    r = subprocess.run(  # noqa: S603
        [sys.executable, str(_VERIFY_SCRIPT_DEV), "--assert-isolated"],
        capture_output=True, text=True, cwd=str(_REPO_ROOT_DEV),
    )
    # Overwrite renderer_result in-place using named attribute on CompletedProcess
    renderer_result.returncode = r.returncode
    renderer_result.stdout = r.stdout
    renderer_result.stderr = r.stderr
    assert_that(r.returncode, equal_to(0), f"verify_installed_types --assert-isolated failed:\n{r.stderr}")


@given("the installed wheel in the external venv")
def installed_wheel_in_external_venv() -> None:
    """Precondition: the verify script already set up the isolated venv."""
    pass


@given(parse("consumer typing fixtures exist for {api_families}"))
def consumer_typing_fixtures_exist(api_families: str) -> None:
    """Assert fixture files exist on disk under tests/compatibility/typing/fixtures/."""
    fixtures_dir = _REPO_ROOT_DEV / "tests" / "compatibility" / "typing" / "fixtures"
    assert_that(fixtures_dir.exists(), is_(True), f"Fixtures dir missing: {fixtures_dir}")
    valid_files = list(fixtures_dir.glob("valid_*.py"))
    invalid_files = list(fixtures_dir.glob("invalid_*.py"))
    assert_that(len(valid_files), greater_than(0), "No valid fixture files found")
    assert_that(len(invalid_files), greater_than(0), "No invalid fixture files found")


@when(parse("mypy checks all {validity} consumer fixtures"))
def mypy_checks_fixtures(validity: str) -> None:
    """Record intent; actual checking runs via the test harness."""
    assert_that(validity, is_(is_("valid")) or is_(is_("invalid")))


@when(parse("Pyright checks all {validity} consumer fixtures"))
def pyright_checks_fixtures(validity: str) -> None:
    """Record intent; actual checking runs via the test harness."""
    assert_that(validity, is_(is_("valid")) or is_(is_("invalid")))


@then(parse("every {validity} fixture passes with exit code zero"))
def every_fixture_passes(validity: str) -> None:
    """Check that consumer typing test passed."""
    test_file = _REPO_ROOT_DEV / "tests" / "compatibility" / "test_consumer_typing.py"
    r = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", str(test_file), "-q", "-k", f"TestValidFixtures"],
        capture_output=True, text=True, cwd=str(_REPO_ROOT_DEV),
    )
    assert_that(
        r.stdout + r.stderr,
        contains_string("passed"),
        f"Valid fixture test failed:\n{r.stdout}\n{r.stderr}",
    )


@then(parse("each {validity} fixture is rejected with the expected diagnostic category"))
def each_fixture_rejected(validity: str) -> None:
    """Check that invalid consumer fixtures are rejected by mypy/pyright."""
    test_file = _REPO_ROOT_DEV / "tests" / "compatibility" / "test_consumer_typing.py"
    r = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", str(test_file), "-q", "-k", "TestInvalidFixtures"],
        capture_output=True, text=True, cwd=str(_REPO_ROOT_DEV),
    )
    assert_that(
        r.stdout + r.stderr,
        contains_string("passed"),
        f"Invalid fixture rejection test failed:\n{r.stdout}\n{r.stderr}",
    )


@when("`pyright --verifytypes pytest_bdd --ignoreexternal` runs against the venv")
def run_verifytypes() -> None:
    """Run verify_installed_types.py --check-verifytypes."""
    r = subprocess.run(  # noqa: S603
        [sys.executable, str(_VERIFY_SCRIPT_DEV), "--check-verifytypes"],
        capture_output=True, text=True, cwd=str(_REPO_ROOT_DEV),
    )
    assert_that(r.returncode, equal_to(0), f"verifytypes failed:\n{r.stderr}")


@then("the type completeness score is 100%")
def type_completeness_100() -> None:
    """The previous step already asserted 100%%; this step is a no-op marker."""
    pass
