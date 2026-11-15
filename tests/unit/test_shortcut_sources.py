import plistlib
from pathlib import Path

import pytest

from pytest_cuke.collector import FeatureFileModule, link_suffix
from pytest_cuke.feature_sources import FeatureSourceError


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("example.url", ".url"),
        ("example.URL", ".url"),
        ("example.Desktop", ".desktop"),
        ("example.WEBLOC", ".webloc"),
        ("example.feature", None),
        ("example.url.backup", None),
    ],
)
def test_link_suffixes_are_recognized_case_insensitively(tmp_path, name, expected):
    assert link_suffix(Path(name)) == expected


def test_url_file_without_url_reports_a_broken_source(tmp_path):
    path = tmp_path / "broken.url"
    path.write_text("[InternetShortcut]\n", encoding="utf-8")

    with pytest.raises(FeatureSourceError, match=r"broken\.url.*missing URL"):
        FeatureFileModule.get_feature_pathlike_from_url_file(path)


def test_webloc_without_url_reports_a_broken_source(tmp_path):
    path = tmp_path / "broken.webloc"
    path.write_bytes(plistlib.dumps({"something": "else"}))

    with pytest.raises(FeatureSourceError, match=r"broken\.webloc.*missing URL"):
        FeatureFileModule.get_feature_pathlike_from_weblock_file(path)


def test_desktop_link_without_url_reports_a_broken_source(tmp_path):
    path = tmp_path / "broken.desktop"
    path.write_text("[Desktop Entry]\nType=Link\n", encoding="utf-8")

    with pytest.raises(FeatureSourceError, match=r"broken\.desktop.*missing URL"):
        FeatureFileModule.get_feature_pathlike_from_desktop_file(path)


def test_desktop_file_with_invalid_content_reports_a_broken_source(tmp_path):
    path = tmp_path / "broken.desktop"
    path.write_text("not an ini file\n", encoding="utf-8")

    with pytest.raises(FeatureSourceError, match=r"broken\.desktop"):
        FeatureFileModule.get_feature_pathlike_from_desktop_file(path)
