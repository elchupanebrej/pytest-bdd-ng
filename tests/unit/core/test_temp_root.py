from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from pytest_bdd.util.temp_root import prefer_posix_temp_root
from pytest_bdd.util.toolz_extra import compose, flip

from pytest import mark

pytestmark = mark.unit


def test_temp_root_and_toolz() -> None:
    assert isinstance(prefer_posix_temp_root(), bool)
    fn = compose(lambda x: x * 2, lambda x: x + 1)
    assert fn(3) == 8
    flipped = flip(lambda a, b: f"{a}-{b}")
    assert flipped("x", "y") == "y-x"


def test_prefer_posix_temp_root_without_posix_temp_root(monkeypatch) -> None:
    class MissingTmpPath:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def is_dir(self) -> bool:
            return False

    monkeypatch.setattr("pytest_bdd.util.temp_root.Path", MissingTmpPath)

    assert prefer_posix_temp_root() is False


def test_prefer_posix_temp_root_moves_mnt_tempdir(monkeypatch) -> None:
    if os.name != "posix" or not Path("/tmp").is_dir():
        pytest.skip("requires a posix host with /tmp")
    monkeypatch.setattr(tempfile, "tempdir", "/mnt/c/not-a-real-temp-root")
    monkeypatch.setenv("TMPDIR", "/mnt/c/not-a-real-temp-root")
    monkeypatch.setenv("TEMP", "/mnt/c/not-a-real-temp-root")
    monkeypatch.setenv("TMP", "/mnt/c/not-a-real-temp-root")

    assert prefer_posix_temp_root() is True
    assert os.environ["TMPDIR"] == "/tmp"
    assert os.environ["TEMP"] == "/tmp"
    assert os.environ["TMP"] == "/tmp"
