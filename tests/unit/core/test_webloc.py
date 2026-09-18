from __future__ import annotations

from pytest_bdd.util.webloc import read, write
from pytest_bdd.webloc import read as legacy_read
from pytest_bdd.webloc import write as legacy_write

from pytest import mark

pytestmark = mark.unit


def test_webloc_read_write(tmp_path) -> None:
    file_path = tmp_path / "test.webloc"
    assert read(file_path) is None
    write(file_path, "https://example.com")
    assert read(file_path) == "https://example.com"


def test_legacy_webloc_creates_missing_parent_directories(tmp_path) -> None:
    target = tmp_path / "nested" / "dir" / "link.webloc"
    legacy_write(target, "https://example.com/nested")
    assert legacy_read(target) == "https://example.com/nested"
