from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pytest_cuke.feature_sources import (
    FeatureSourceError,
    normalize_features_base_url,
    resolve_feature_sources,
    resolve_feature_url,
)


class FakeConfig:
    def __init__(
        self,
        *,
        rootpath: Path,
        options: dict[str, Any] | None = None,
        ini: dict[str, Any] | None = None,
    ) -> None:
        self.rootpath = rootpath
        self.options = options or {}
        self.ini = ini or {}

    def getoption(self, name: str, default: Any = None) -> Any:
        return self.options.get(name, default)

    def getini(self, name: str) -> Any:
        return self.ini.get(name)


def test_feature_source_resolution_prefers_binding_then_cli_then_ini(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    other_cwd = tmp_path / "outside"
    project_root.mkdir()
    other_cwd.mkdir()
    monkeypatch.chdir(other_cwd)
    config = FakeConfig(
        rootpath=project_root,
        options={
            "cuke_features_dir": "cli-features",
            "cuke_features_base_url": "https://cli.example.test/cli-prefix/",
        },
        ini={
            "cuke_features_dir": "ini-features",
            "cuke_features_base_url": "https://ini.example.test/ini-prefix",
        },
    )

    cli_sources = resolve_feature_sources(config)
    binding_sources = resolve_feature_sources(
        config,
        features_base_dir="binding-features",
        features_base_url="https://binding.example.test/binding-prefix/",
    )

    assert cli_sources.features_base_dir == project_root / "cli-features"
    assert cli_sources.features_base_url == "https://cli.example.test/cli-prefix"
    assert binding_sources.features_base_dir == project_root / "binding-features"
    assert binding_sources.features_base_url == "https://binding.example.test/binding-prefix"


def test_callable_binding_overrides_receive_config_once(tmp_path: Path) -> None:
    rootpath = tmp_path / "project"
    config = FakeConfig(rootpath=rootpath)
    calls = {"directory": 0, "url": 0}

    def directory_override(session_config: FakeConfig) -> str:
        calls["directory"] += 1
        assert session_config is config
        return "bound-features"

    def url_override(session_config: FakeConfig) -> str:
        calls["url"] += 1
        assert session_config is config
        return "http://fixture.example.test/api/"

    sources = resolve_feature_sources(
        config,
        features_base_dir=directory_override,
        features_base_url=url_override,
    )

    assert sources.features_base_dir == rootpath / "bound-features"
    assert sources.features_base_url == "http://fixture.example.test/api"
    assert calls == {"directory": 1, "url": 1}


def test_ini_relative_feature_root_resolves_against_pytest_rootpath(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rootpath = tmp_path / "project"
    other_cwd = tmp_path / "outside"
    rootpath.mkdir()
    other_cwd.mkdir()
    monkeypatch.chdir(other_cwd)
    config = FakeConfig(rootpath=rootpath, ini={"cuke_features_dir": "spec/features"})

    sources = resolve_feature_sources(config)

    assert sources.features_base_dir == rootpath / "spec" / "features"


@pytest.mark.parametrize(
    ("base_url", "feature_path", "expected"),
    (
        (
            "https://example.test/project/features",
            "suite.feature",
            "https://example.test/project/features/suite.feature",
        ),
        (
            "https://example.test/project/features/",
            "/suite.feature",
            "https://example.test/project/features/suite.feature",
        ),
        (
            "https://example.test/project/features///",
            "/suite.feature",
            "https://example.test/project/features/suite.feature",
        ),
    ),
)
def test_relative_feature_url_preserves_base_prefix_and_normalizes_slashes(
    base_url: str, feature_path: str, expected: str
) -> None:
    assert resolve_feature_url(feature_path, base_url) == expected


def test_absolute_feature_url_is_not_rewritten_by_base_url() -> None:
    absolute_url = "https://origin.example.test/other/project.feature"

    assert resolve_feature_url(absolute_url, "https://example.test/project/features") == absolute_url


def test_relative_url_feature_path_requires_a_configured_base_url() -> None:
    with pytest.raises(FeatureSourceError, match=r"requires --cuke-features-base-url or cuke_features_base_url"):
        resolve_feature_url("features/suite.feature", None)


def test_malformed_features_base_url_has_setting_specific_diagnostic() -> None:
    with pytest.raises(ValueError, match=r"cuke_features_base_url.*absolute HTTP\(S\)"):
        normalize_features_base_url("not a URL")
