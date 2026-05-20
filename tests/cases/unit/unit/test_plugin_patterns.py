"""Unit tests for plugin_patterns validation rules (BLQ1001/BLQ1002/BLQ1003)."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

import pytest

from pytest_bdd._ruff.rules.plugin_patterns import (
    check_cross_plugin_imports,
    check_plugin_patterns,
    check_required_files,
    check_stashbound_coverage,
    main,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


def _write_file(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _plugin_dir(base: Path, name: str) -> Path:
    d = base / name
    d.mkdir()
    return d


def _make_valid_plugin(base: Path, name: str, entrypoint_body: str = "") -> Path:
    d = _plugin_dir(base, name)
    _write_file(d / "entrypoint.py", entrypoint_body or "def run(): pass\n")
    _write_file(d / "hook.py", "def plugin_hook(): pass\n")
    _write_file(d / "plugin.py", "class Plugin: pass\n")
    return d


class TestCheckRequiredFiles:
    def test_all_files_present_no_violations(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "my_plugin")
        violations = check_required_files(tmp_path)
        assert violations == []

    def test_missing_entrypoint_reports_violation(self, tmp_path: Path) -> None:
        d = _plugin_dir(tmp_path, "my_plugin")
        _write_file(d / "hook.py", "pass\n")
        _write_file(d / "plugin.py", "pass\n")
        violations = check_required_files(tmp_path)
        assert len(violations) == 1
        assert "BLQ1001" in violations[0].message
        assert "entrypoint.py" in violations[0].message
        assert violations[0].path == d

    def test_missing_hook_reports_violation(self, tmp_path: Path) -> None:
        d = _plugin_dir(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "pass\n")
        _write_file(d / "plugin.py", "pass\n")
        violations = check_required_files(tmp_path)
        assert len(violations) == 1
        assert "BLQ1001" in violations[0].message
        assert "hook.py" in violations[0].message

    def test_missing_plugin_reports_violation(self, tmp_path: Path) -> None:
        d = _plugin_dir(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "pass\n")
        _write_file(d / "hook.py", "pass\n")
        violations = check_required_files(tmp_path)
        assert len(violations) == 1
        assert "BLQ1001" in violations[0].message
        assert "plugin.py" in violations[0].message

    def test_multiple_missing_files_reports_all(self, tmp_path: Path) -> None:
        d = _plugin_dir(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "pass\n")
        violations = check_required_files(tmp_path)
        assert len(violations) == 2

    def test_multiple_plugins_each_checked(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "plugin_a")
        _make_valid_plugin(tmp_path, "plugin_b")
        violations = check_required_files(tmp_path)
        assert violations == []

    def test_ignores_pycache_directory(self, tmp_path: Path) -> None:
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        violations = check_required_files(tmp_path)
        assert violations == []

    def test_ignores_dot_directories(self, tmp_path: Path) -> None:
        dotdir = tmp_path / ".hidden"
        dotdir.mkdir()
        violations = check_required_files(tmp_path)
        assert violations == []


class TestCheckCrossPluginImports:
    def test_clean_plugin_no_violations(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "my_plugin")
        violations = check_cross_plugin_imports(tmp_path)
        assert violations == []

    def test_standard_library_imports_ignored(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "import os\nfrom pathlib import Path\n")
        violations = check_cross_plugin_imports(tmp_path)
        assert violations == []

    def test_intra_plugin_import_allowed(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "from pytest_bdd.plugin.my_plugin.utils import helper\n")
        violations = check_cross_plugin_imports(tmp_path)
        assert violations == []

    def test_cross_plugin_import_from_detected(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "plugin_a")
        _make_valid_plugin(tmp_path, "plugin_b")
        d_a = tmp_path / "plugin_a"
        _write_file(d_a / "entrypoint.py", "from pytest_bdd.plugin.plugin_b import something\n")
        violations = check_cross_plugin_imports(tmp_path)
        assert len(violations) == 1
        assert "BLQ1002" in violations[0].message
        assert "plugin_b" in violations[0].message
        assert "plugin_a" in violations[0].message

    def test_cross_plugin_import_detected(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "plugin_a")
        _make_valid_plugin(tmp_path, "plugin_b")
        d_b = tmp_path / "plugin_b"
        _write_file(d_b / "entrypoint.py", "import pytest_bdd.plugin.plugin_a.thing\n")
        violations = check_cross_plugin_imports(tmp_path)
        assert len(violations) == 1
        assert "BLQ1002" in violations[0].message

    def test_cross_plugin_submodule_import_detected(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "plugin_a")
        _make_valid_plugin(tmp_path, "plugin_b")
        d_a = tmp_path / "plugin_a"
        _write_file(d_a / "entrypoint.py", "from pytest_bdd.plugin.plugin_b.utils import helper\n")
        violations = check_cross_plugin_imports(tmp_path)
        assert len(violations) == 1
        assert "BLQ1002" in violations[0].message

    def test_import_from_same_plugin_package_ok(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "utils.py", "pass\n")
        _write_file(d / "entrypoint.py", "from pytest_bdd.plugin.my_plugin.utils import helper\n")
        violations = check_cross_plugin_imports(tmp_path)
        assert violations == []

    def test_malformed_syntax_skipped(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "this is not valid python {{{{{\n")
        violations = check_cross_plugin_imports(tmp_path)
        assert violations == []


class TestCheckStashboundCoverage:
    def test_no_stash_access_no_violations(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "my_plugin")
        violations = check_stashbound_coverage(tmp_path)
        assert violations == []

    def test_direct_stash_subscript_access_violation(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", 'config.stash["key"] = value\n')
        violations = check_stashbound_coverage(tmp_path)
        assert len(violations) == 1
        assert "BLQ1003" in violations[0].message

    def test_stash_get_access_violation(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", 'value = config.stash.get("key")\n')
        violations = check_stashbound_coverage(tmp_path)
        assert len(violations) == 1
        assert "BLQ1003" in violations[0].message

    def test_stash_subscript_in_ast_detected(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "x = something.stash[STASH_KEY]\n")
        violations = check_stashbound_coverage(tmp_path)
        assert len(violations) == 1

    def test_stash_get_call_in_ast_detected(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "x = obj.stash.get(STASH_KEY)\n")
        violations = check_stashbound_coverage(tmp_path)
        assert len(violations) == 1

    def test_exception_file_exempt(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "exception.py", 'self.config.stash["key"] = val\n')
        _write_file(d / "entrypoint.py", 'self.config.stash["key"] = val\n')
        violations = check_stashbound_coverage(tmp_path)
        assert len(violations) == 1  # only entrypoint, not exception.py

    def test_stash_access_file_exempt(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "stash_access.py", 'config.stash["key"] = val\n')
        _write_file(d / "entrypoint.py", 'config.stash["key"] = val\n')
        violations = check_stashbound_coverage(tmp_path)
        assert len(violations) == 1  # only entrypoint, not stash_access.py

    def test_multiple_violations_in_one_plugin(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", 'config.stash["a"] = 1\n')
        _write_file(d / "plugin.py", 'x = config.stash["b"]\n')
        violations = check_stashbound_coverage(tmp_path)
        assert len(violations) == 2

    def test_malformed_syntax_skipped(self, tmp_path: Path) -> None:
        d = _make_valid_plugin(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "this is broken {{{{{\n")
        violations = check_stashbound_coverage(tmp_path)
        assert violations == []


class TestCheckPluginPatterns:
    def test_all_checks_combined(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "plugin_a")
        _make_valid_plugin(tmp_path, "plugin_b")
        violations = check_plugin_patterns(tmp_path)
        assert violations == []

    def test_required_files_and_cross_imports_combined(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "plugin_a")
        _make_valid_plugin(tmp_path, "plugin_b")
        # Missing hook in plugin_a
        (tmp_path / "plugin_a" / "hook.py").unlink()
        # Cross-plugin import in plugin_b
        _write_file(tmp_path / "plugin_b" / "entrypoint.py", "from pytest_bdd.plugin.plugin_a import thing\n")
        violations = check_plugin_patterns(tmp_path)
        assert len(violations) == 2

    def test_empty_plugin_dir_returns_empty(self, tmp_path: Path) -> None:
        violations = check_plugin_patterns(tmp_path)
        assert violations == []


class TestMain:
    def test_clean_plugins_exit_zero(self, tmp_path: Path) -> None:
        _make_valid_plugin(tmp_path, "my_plugin")
        exit_code = main([str(tmp_path)])
        assert exit_code == 0

    def test_violations_exit_one(self, tmp_path: Path) -> None:
        d = _plugin_dir(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "pass\n")
        exit_code = main([str(tmp_path)])
        assert exit_code == 1

    def test_nonexistent_dir_exit_one(self) -> None:
        exit_code = main(["/nonexistent/path/12345"])
        assert exit_code == 1

    def test_success_message_on_clean(self, tmp_path: Path, capsys: object) -> None:
        _make_valid_plugin(tmp_path, "my_plugin")
        main([str(tmp_path)])
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "validated successfully" in captured.out

    def test_error_message_on_violations(self, tmp_path: Path, capsys: object) -> None:
        d = _plugin_dir(tmp_path, "my_plugin")
        _write_file(d / "entrypoint.py", "pass\n")
        main([str(tmp_path)])
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "violation" in captured.out
