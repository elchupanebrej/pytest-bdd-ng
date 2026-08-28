from __future__ import annotations

import operator
from unittest.mock import patch

from packaging.version import Version
from pytest_bdd.npm_resource import check_npm, check_npm_package, find_resource, get_npm_root
from pytest_bdd.packaging import compare_distribution_version, get_distribution_version, parse_version


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


def test_find_resource() -> None:
    with (
        patch("pytest_bdd.npm_resource.get_npm_root", side_effect=["/l", "/g"]),
        patch("glob.iglob", side_effect=[["/l/pkg/r.js"], ["/g/pkg/r.js"]]),
    ):
        assert list(find_resource("pkg", "r.js")) == ["/l/pkg/r.js", "/g/pkg/r.js"]
