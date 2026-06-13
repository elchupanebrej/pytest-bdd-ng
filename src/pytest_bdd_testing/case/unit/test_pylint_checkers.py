"""Unit tests for pytest-bdd custom Pylint checkers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]


def _run_pylint(path: Path, *symbols: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pylint",
            "--load-plugins=pytest_bdd._pylint",
            "--disable=all",
            f"--enable={','.join(symbols)}",
            "--reports=n",
            "--score=n",
            str(path),
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=cwd,
    )


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_quality_gate_checker_reports_return_none_and_unlogged_exception(tmp_path: Path) -> None:
    target = _write(
        tmp_path / "sample.py",
        """
def bad_return():
    return None

def bad_except():
    try:
        raise RuntimeError("boom")
    except Exception:
        pass
""",
    )

    result = _run_pylint(target, "no-return-none", "bare-except-exception")

    assert result.returncode != 0
    assert "BLQ901" in result.stdout
    assert "BLQ902" in result.stdout


def test_no_testcase_checker_reports_class_based_tests(tmp_path: Path) -> None:
    target = _write(
        tmp_path / "src" / "pytest_bdd_testing" / "cases" / "unit" / "test_sample.py",
        """
class TestExample:
    def test_case(self):
        assert True
""",
    )

    result = _run_pylint(target, "no-test-class")

    assert result.returncode != 0
    assert "BLQ903" in result.stdout


def test_typing_checker_reports_bare_and_unexplained_type_ignores(tmp_path: Path) -> None:
    target = _write(
        tmp_path / "typing_sample.py",
        "value = missing  # type: ignore\nother = missing_too  # type: ignore[attr-defined]\n",
    )

    result = _run_pylint(target, "bare-type-ignore", "missing-type-ignore-explanation")

    assert result.returncode != 0
    assert "BLQ1101" in result.stdout
    assert "BLQ1102" in result.stdout


def test_file_size_checker_reports_oversized_file(tmp_path: Path) -> None:
    target = _write(tmp_path / "large.py", "\n".join(f"value_{index} = {index}" for index in range(1201)))

    result = _run_pylint(target, "file-too-long")

    assert result.returncode != 0
    assert "BLQ1201" in result.stdout


def test_layer_checker_reports_downward_import(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "architecture" / "layers.toml",
        Path("docs/architecture/layers.toml").read_text(encoding="utf-8"),
    )
    _write(tmp_path / "src" / "pytest_bdd" / "__init__.py", "")
    _write(tmp_path / "src" / "pytest_bdd" / "model" / "__init__.py", "")
    _write(
        tmp_path / "src" / "pytest_bdd" / "model" / "sample.py",
        "from pytest_bdd.plugin.pickle_runner import entrypoint\n",
    )

    result = _run_pylint(
        Path("src/pytest_bdd/model/sample.py"),
        "downward-import",
        "horizontal-import",
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert "BLQ1301" in result.stdout


def test_init_checker_reports_all_namespace_package_rules(tmp_path: Path) -> None:
    package_init = _write(tmp_path / "pkg" / "__init__.py", '"""Package only."""\n')
    exports = _write(tmp_path / "exports.py", "__all__ = ['name']\nimport os as os\n")
    init_all_empty = _write(tmp_path / "pkg_empty_all" / "__init__.py", "__all__ = []\n")
    init_all_nonempty = _write(tmp_path / "pkg_nonempty_all" / "__init__.py", "__all__ = ['name']\n")

    init_result = _run_pylint(package_init, "empty-init", "init-code-required")
    exports_result = _run_pylint(exports, "all-defined", "redundant-import-alias")
    empty_all_result = _run_pylint(init_all_empty, "init-code-required")
    nonempty_all_result = _run_pylint(init_all_nonempty, "init-code-required")

    assert init_result.returncode != 0
    assert "BLQ1403" in init_result.stdout
    assert exports_result.returncode != 0
    assert "BLQ1401" in exports_result.stdout
    assert "BLQ1404" in exports_result.stdout
    assert empty_all_result.returncode == 0
    assert nonempty_all_result.returncode != 0
    assert "BLQ1403" in nonempty_all_result.stdout


def test_plugin_pattern_checker_reports_missing_plugin_files(tmp_path: Path) -> None:
    target = _write(tmp_path / "src" / "pytest_bdd" / "plugin" / "demo" / "plugin.py", "VALUE = 1\n")

    result = _run_pylint(target, "missing-plugin-file")

    assert result.returncode != 0
    assert "BLQ1001" in result.stdout


def test_test_import_checker_reports_imports_outside_allowed_cases_path(tmp_path: Path) -> None:
    target = _write(tmp_path / "sample.py", "from pytest_bdd_testing.e2e import test_e2e\n")

    result = _run_pylint(target, "test-import-outside-cases")

    assert result.returncode != 0
    assert "BLQ1601" in result.stdout


def test_responsibility_docs_checker_reports_violations(tmp_path: Path) -> None:
    # 1. Missing responsibility sections
    target_missing = _write(
        tmp_path / "missing_sections.py",
        '''"""
A module docstring without sections.
"""
''',
    )
    result_missing = _run_pylint(target_missing, "missing-responsibility-doc")
    assert result_missing.returncode != 0
    assert "BLQ910" in result_missing.stdout
    assert "missing-responsibility-doc" in result_missing.stdout

    # 2. Short responsibility docs
    target_short = _write(
        tmp_path / "short_sections.py",
        '''"""
Responsibility:
    Short.
Reason for existence:
    Too short.
Delegates:
    - None
Cohesion:
    Valid cohesion.
Separation:
    - Sibling: separate.
Main consumers:
    - Caller: imports.
State and side effects:
    None.
Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""
''',
    )
    result_short = _run_pylint(target_short, "short-responsibility-doc")
    assert result_short.returncode != 0
    assert "BLQ911" in result_short.stdout
    assert "short-responsibility-doc" in result_short.stdout

    # 3. Unfilled responsibility placeholder
    target_placeholder = _write(
        tmp_path / "placeholder_sections.py",
        '''"""
Responsibility:
    This is a long responsibility description that is at least 140 characters long to satisfy the length check
    requirement for this entity.
Reason for existence:
    This is another long reason for existence description that is at least 140 characters long to satisfy the length
    check requirement for this entity.
Delegates:
    - <Collaborator>: description
Cohesion:
    Valid cohesion.
Separation:
    - Sibling: separate.
Main consumers:
    - Caller: imports.
State and side effects:
    None.
Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""
''',
    )
    result_placeholder = _run_pylint(target_placeholder, "unfilled-responsibility-placeholder")
    assert result_placeholder.returncode != 0
    assert "BLQ914" in result_placeholder.stdout
    assert "unfilled-responsibility-placeholder" in result_placeholder.stdout

    # 4. Missing architecture score (specifically checking new ones like entity_fullness)
    target_missing_score = _write(
        tmp_path / "missing_score.py",
        '''"""
Responsibility:
    This is a long responsibility description that is at least 140 characters long to satisfy the length check
    requirement for this entity.
Reason for existence:
    This is another long reason for existence description that is at least 140 characters long to satisfy the length
    check requirement for this entity.
Delegates:
    - None.
Cohesion:
    Valid cohesion.
Separation:
    - Sibling: separate.
Main consumers:
    - Caller: imports.
State and side effects:
    None.
Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
"""
''',
    )
    result_missing_score = _run_pylint(target_missing_score, "missing-architecture-score")
    assert result_missing_score.returncode != 0
    assert "BLQ913" in result_missing_score.stdout
    assert "missing-architecture-score" in result_missing_score.stdout
    assert "entity_fullness" in result_missing_score.stdout
    assert "locational_stability" in result_missing_score.stdout


def test_test_responsibility_docs_checker_reports_violations(tmp_path: Path) -> None:
    # 1. Missing test responsibility sections in function docstring
    target_missing = _write(
        tmp_path / "src" / "pytest_bdd_testing" / "cases" / "unit" / "test_missing_sections.py",
        '''
def test_func():
    """
    A function docstring without sections.
    """
    pass
''',
    )
    result_missing = _run_pylint(target_missing, "missing-test-responsibility-doc")
    assert result_missing.returncode != 0
    assert "BLQ920" in result_missing.stdout
    assert "missing-test-responsibility-doc" in result_missing.stdout

    # 2. Short test scenario description
    target_short = _write(
        tmp_path / "src" / "pytest_bdd_testing" / "cases" / "unit" / "test_short_sections.py",
        '''
def test_func():
    """
    Test target:
        pytest_bdd.sample
    Test type:
        Unit test
    Test scenario:
        Short.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        No reduction possible.
    Escalation:
        No escalation possible.
    Atomicity:
        Atomic.
    Autonomy:
        Autonomous.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pass
''',
    )
    result_short = _run_pylint(target_short, "short-test-responsibility-doc")
    assert result_short.returncode != 0
    assert "BLQ921" in result_short.stdout
    assert "short-test-responsibility-doc" in result_short.stdout

    # 3. Unfilled test responsibility placeholder
    target_placeholder = _write(
        tmp_path / "src" / "pytest_bdd_testing" / "cases" / "unit" / "test_placeholder_sections.py",
        '''
def test_func():
    """
    Test target:
        <target_under_test>
    Test type:
        Unit test
    Test scenario:
        This is a long test scenario description that is at least 30 characters long to satisfy the length check.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        No reduction possible.
    Escalation:
        No escalation possible.
    Atomicity:
        Atomic.
    Autonomy:
        Autonomous.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pass
''',
    )
    result_placeholder = _run_pylint(target_placeholder, "unfilled-test-responsibility-placeholder")
    assert result_placeholder.returncode != 0
    assert "BLQ923" in result_placeholder.stdout
    assert "unfilled-test-responsibility-placeholder" in result_placeholder.stdout

    # 4. Missing test quality score
    target_missing_score = _write(
        tmp_path / "src" / "pytest_bdd_testing" / "cases" / "unit" / "test_missing_score.py",
        '''
def test_func():
    """
    Test target:
        pytest_bdd.sample
    Test type:
        Unit test
    Test scenario:
        This is a long test scenario description that is at least 30 characters long to satisfy the length check.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        No reduction possible.
    Escalation:
        No escalation possible.
    Atomicity:
        Atomic.
    Autonomy:
        Autonomous.
    Test quality score:
        #test-eval:isolation=5
    """
    pass
''',
    )
    result_missing_score = _run_pylint(target_missing_score, "missing-test-quality-score")
    assert result_missing_score.returncode != 0
    assert "BLQ922" in result_missing_score.stdout
    assert "missing-test-quality-score" in result_missing_score.stdout


def test_test_responsibility_docs_checker_reports_violations_for_functions(tmp_path: Path) -> None:
    # 1. Missing test responsibility sections in function docstring
    target_missing = _write(
        tmp_path / "src" / "pytest_bdd_testing" / "cases" / "unit" / "test_func_missing.py",
        '''
def test_something():
    """
    Missing sections here.
    """
    pass
''',
    )
    result_missing = _run_pylint(target_missing, "missing-test-responsibility-doc")
    assert result_missing.returncode != 0
    assert "BLQ920" in result_missing.stdout
    assert "function test_something -> Test target" in result_missing.stdout
