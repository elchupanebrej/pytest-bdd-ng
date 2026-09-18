from __future__ import annotations

import operator
import os
import sys
from unittest.mock import patch

from packaging.version import Version
from pytest_bdd.npm_resource import check_npm, check_npm_package, find_resource, get_npm_root
from pytest_bdd.packaging import compare_distribution_version, get_distribution_version, parse_version

from pytest import mark, raises

pytestmark = mark.unit


def test_packaging_versions() -> None:
    assert parse_version("1.2.3") == Version("1.2.3")
    with patch("pytest_bdd.packaging.version", return_value="2.3.1"):
        assert get_distribution_version("pkg") == Version("2.3.1")
        assert compare_distribution_version("pkg", "2.3.1")
        assert not compare_distribution_version("pkg", "1.0.0")
        assert compare_distribution_version("pkg", "1.0.0", operator=operator.gt)


def test_npm_helpers() -> None:
    with patch("subprocess.check_output", return_value=b"/node_modules\n"):
        assert get_npm_root() == "/node_modules"
        assert check_npm()
        assert check_npm_package("some-pkg")
    with patch("subprocess.check_output", return_value=b"/global\n"):
        assert get_npm_root(global_install=True) == "/global"
    with patch("subprocess.check_output", side_effect=FileNotFoundError):
        assert not check_npm()
        assert not check_npm_package("some-pkg")
        with raises(FileNotFoundError):
            get_npm_root()


def test_npm_helpers_run_resolved_executable(monkeypatch) -> None:
    commands = []

    def fake_check_output(cmd, *args, **kwargs):
        commands.append(cmd)
        return b"/node_modules\n"

    monkeypatch.setattr("shutil.which", lambda name: "/opt/npm.cmd")
    monkeypatch.setattr("subprocess.check_output", fake_check_output)

    assert check_npm()
    assert check_npm_package("some-pkg")
    assert get_npm_root(global_install=True) == "/node_modules"
    assert commands == [
        ["/opt/npm.cmd", "--version"],
        ["/opt/npm.cmd", "list", "some-pkg"],
        ["/opt/npm.cmd", "root", "-g"],
    ]


def test_npm_helpers_find_shim_on_path(monkeypatch, tmp_path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    if sys.platform == "win32":
        shim = bin_dir / "npm.cmd"
        shim.write_text("@echo off\r\necho 10.0.0\r\n", encoding="utf-8")
    else:
        shim = bin_dir / "npm"
        shim.write_text("#!/bin/sh\necho 10.0.0\n", encoding="utf-8")
        shim.chmod(0o755)

    monkeypatch.setenv("PATH", os.pathsep.join([str(bin_dir), os.environ.get("PATH", "")]))

    assert check_npm() is True
    assert check_npm_package("some-pkg") is True
    assert get_npm_root() == "10.0.0"


def test_find_resource() -> None:
    with (
        patch("pytest_bdd.npm_resource.get_npm_root", side_effect=["/l", "/g"]),
        patch("glob.iglob", side_effect=[["/l/pkg/r.js"], ["/g/pkg/r.js"]]),
    ):
        assert list(find_resource("pkg", "r.js")) == ["/l/pkg/r.js", "/g/pkg/r.js"]
