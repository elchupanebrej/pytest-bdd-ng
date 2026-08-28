from __future__ import annotations

import os
import sys
from pathlib import Path

from pytest_bdd.compatibility.path import relpath, resolvepath
from pytest_bdd.compatibility.pathlib import GlobError


def test_relpath(tmp_path: Path) -> None:
    sub = tmp_path / "sub" / "file.txt"
    assert relpath(str(sub), start=str(tmp_path)) == os.path.join("sub", "file.txt")


def test_resolvepath(tmp_path: Path) -> None:
    sub = tmp_path / "a" / "b.txt"
    resolved = resolvepath(str(sub), start=str(tmp_path))
    assert Path(str(resolved)) == sub.resolve()


def test_pathlib_glob_error() -> None:
    expected_type = IndexError if sys.version_info < (3, 13) else ValueError
    assert GlobError is expected_type
