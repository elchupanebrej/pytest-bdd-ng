from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest

from pytest_cuke.generation_command import _binding_matches_feature_paths, _file_uri_path, _has_windows_drive_prefix


@pytest.mark.parametrize(
    "path", [r"C:\work\features\checkout.feature", "D:/work/features/*.feature", "E:relative.feature"]
)
def test_windows_drive_paths_are_not_mistaken_for_url_schemes(path: str) -> None:
    assert _has_windows_drive_prefix(path)


@pytest.mark.parametrize(
    "url", ["https://example.test/features/checkout.feature", "file:///work/features/checkout.feature"]
)
def test_url_schemes_are_not_mistaken_for_windows_drive_paths(url: str) -> None:
    assert not _has_windows_drive_prefix(url)


@pytest.mark.parametrize(
    ("uri", "expected_path"),
    [
        ("file:///tmp/my%20features/checkout.feature", "tmp/my features/checkout.feature"),
        ("file://server/share/my%20features/checkout.feature", "server/share/my features/checkout.feature"),
    ],
)
def test_file_uri_paths_decode_reserved_characters(uri: str, expected_path: str) -> None:
    decoded = _file_uri_path(urlsplit(uri)).replace("\\", "/").lstrip("/")

    assert decoded.endswith(expected_path)
    assert "%20" not in decoded


@pytest.mark.parametrize(
    ("feature_relative_path", "pattern", "expected"),
    [
        ("checkout/checkout.feature", "*/*.feature", True),
        ("checkout/nested/checkout.feature", "*/*.feature", False),
    ],
)
def test_relative_scenario_globs_match_pytest_path_segments(
    tmp_path: Path, feature_relative_path: str, pattern: str, expected: bool
) -> None:
    features_base = tmp_path / "features"
    feature_path = features_base / feature_relative_path
    feature_path.parent.mkdir(parents=True)
    feature_path.touch()

    matched = _binding_matches_feature_paths(
        (pattern,),
        {},
        SimpleNamespace(filename=str(feature_path), rel_filename=feature_relative_path),
        tmp_path / "steps.py",
        tmp_path,
        features_base,
    )

    assert matched is expected
