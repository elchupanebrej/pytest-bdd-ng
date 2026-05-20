"""Unit tests for feature file collector helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pytest_bdd.collector import FeatureFileModule
from pytest_bdd.scenario import FeaturePathType

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


def test_detect_uri_pathtype_handles_file_url() -> None:
    """detect_uri_pathtype returns path mode for file URLs."""
    path, path_type = FeatureFileModule.detect_uri_pathtype("file:///tmp/example.feature")

    assert path == "/" + "tmp/example.feature"
    assert path_type is FeaturePathType.PATH


def test_detect_uri_pathtype_handles_remote_url() -> None:
    """detect_uri_pathtype returns URL mode for remote URLs."""
    path, path_type = FeatureFileModule.detect_uri_pathtype("https://example.test/example.feature")

    assert path == "https://example.test/example.feature"
    assert path_type is FeaturePathType.URL


def test_detect_uri_pathtype_handles_relative_path() -> None:
    """detect_uri_pathtype returns undefined mode for relative paths."""
    path, path_type = FeatureFileModule.detect_uri_pathtype("example.feature")

    assert path == "example.feature"
    assert path_type is FeaturePathType.UNDEFINED


def test_get_feature_pathlike_from_url_file_reads_shortcut(tmp_path: Path) -> None:
    """URL shortcut files resolve feature URL and working directory."""
    shortcut = tmp_path / "feature.url"
    shortcut.write_text(
        "[InternetShortcut]\nURL=https://example.test/feature.feature\nWorkingDirectory=/tmp/features\n",
        encoding="utf-8",
    )

    path, path_type, working_dir = FeatureFileModule.get_feature_pathlike_from_url_file(shortcut)

    assert path == "https://example.test/feature.feature"
    assert path_type is FeaturePathType.URL
    assert working_dir == "/" + "tmp/features"


def test_get_feature_pathlike_from_desktop_file_reads_link(tmp_path: Path) -> None:
    """Desktop link files resolve their URL field."""
    shortcut = tmp_path / "feature.desktop"
    shortcut.write_text("[Desktop Entry]\nType=Link\nURL=file:///tmp/feature.feature\n", encoding="utf-8")

    path, path_type, base_dir = FeatureFileModule.get_feature_pathlike_from_desktop_file(shortcut)

    assert path == "/" + "tmp/feature.feature"
    assert path_type is FeaturePathType.PATH
    assert base_dir is None


def test_get_feature_pathlike_from_desktop_file_ignores_non_link(tmp_path: Path) -> None:
    """Desktop non-link files do not resolve feature paths."""
    shortcut = tmp_path / "feature.desktop"
    shortcut.write_text("[Desktop Entry]\nType=Application\nURL=file:///tmp/feature.feature\n", encoding="utf-8")

    path, path_type, base_dir = FeatureFileModule.get_feature_pathlike_from_desktop_file(shortcut)

    assert path is None
    assert path_type is FeaturePathType.UNDEFINED
    assert base_dir is None
