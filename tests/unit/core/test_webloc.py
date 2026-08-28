from __future__ import annotations

from pytest_bdd.util.webloc import read, write


def test_webloc_read_write(tmp_path) -> None:
    file_path = tmp_path / "test.webloc"
    assert read(file_path) is None
    write(file_path, "https://example.com")
    assert read(file_path) == "https://example.com"
