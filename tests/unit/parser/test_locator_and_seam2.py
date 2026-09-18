from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.model import Feature
from pytest_bdd.parser import GherkinParser
from pytest_bdd.scenario_locator import (
    FileScenarioLocator,
    ScenarioLocatorFeatureResolver,
    ScenarioLocatorResolver,
)

from pytest import mark

pytestmark = mark.unit


if TYPE_CHECKING:
    from pathlib import Path


def _write_feature(path: Path, name: str = "Feature") -> Path:
    path.write_text(f"Feature: {name}\n  Scenario: S\n    Given a step\n", encoding="utf-8")
    return path


def test_file_scenario_locator_single_file(tmp_path: Path) -> None:
    feature_file = tmp_path / "simple.feature"
    feature_file.write_text(
        "Feature: Locator Test\n\n  Scenario: S1\n    Given step 1\n",
        encoding="utf-8",
    )
    locator = FileScenarioLocator(feature_paths=[feature_file])
    features = list(locator.resolve_features())

    assert len(features) == 1
    feat = features[0]
    assert isinstance(feat, Feature)
    assert feat.name == "Locator Test"
    assert len(feat.scenarios) == 1
    assert feat.scenarios[0].name == "S1"
    assert len(feat.scenarios[0].steps) == 1
    assert feat.scenarios[0].steps[0].name == "step 1"


def test_file_scenario_locator_directory_glob(tmp_path: Path) -> None:
    f1 = tmp_path / "f1.feature"
    f1.write_text("Feature: F1\n  Scenario: S1\n    Given a\n", encoding="utf-8")
    f2 = tmp_path / "f2.feature.md"
    f2.write_text("# Feature: F2\n## Scenario: S2\n* Given b\n", encoding="utf-8")
    f3 = tmp_path / "f3.bdd.yaml"
    f3.write_text("Name: F3\nSteps:\n  - Step:\n      Name: S3\n      Steps:\n        - Given: c\n", encoding="utf-8")

    locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=["**/*"])
    features = list(locator.resolve_features())

    names = {f.name for f in features}
    assert "F1" in names
    assert "F2" in names
    assert "F3" in names


def test_file_scenario_locator_filtering(tmp_path: Path) -> None:
    f = tmp_path / "filter.feature"
    f.write_text(
        "Feature: Filtering\n\n"
        "  @smoke\n"
        "  Scenario: Keep Me\n"
        "    Given step a\n\n"
        "  Scenario: Skip Me\n"
        "    Given step b\n",
        encoding="utf-8",
    )
    locator = FileScenarioLocator(
        feature_paths=[f],
        filter_=lambda _config, _feat, sc: sc.name == "Keep Me",
    )
    resolved = list(locator.resolve())
    assert len(resolved) == 1
    feat, sc = resolved[0]
    assert feat.name == "Filtering"
    assert sc.name == "Keep Me"


def test_protocols_conformance() -> None:
    locator = FileScenarioLocator(feature_paths=["dummy.feature"])
    assert isinstance(locator, ScenarioLocatorFeatureResolver)
    assert isinstance(locator, ScenarioLocatorResolver)


def test_url_scenario_locator_mocked() -> None:
    from unittest.mock import MagicMock, patch

    from pytest_bdd.scenario_locator import UrlScenarioLocator

    mock_resp = MagicMock()
    mock_resp.headers.get_content_type.return_value = "text/x-gherkin"
    mock_resp.read.return_value = b"Feature: Remote Feature\n  Scenario: Remote S1\n    Given remote step\n"
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False

    with patch("pytest_bdd.scenario_locator.urlopen", return_value=mock_resp):
        locator = UrlScenarioLocator(url_paths=["https://example.com/test.feature"])
        features = list(locator.resolve_features())

        assert len(features) == 1
        assert features[0].name == "Remote Feature"
        assert len(features[0].scenarios) == 1
        assert features[0].scenarios[0].name == "Remote S1"


def test_seam2_contract_all_formats(tmp_path: Path) -> None:
    """Seam 2 Contract: All parsers & locators produce pure Layer L2a Feature model trees."""
    from pytest_bdd.model import Scenario, Step

    f_gherkin = tmp_path / "test.feature"
    f_gherkin.write_text("Feature: Gherkin\n  Scenario: G\n    Given g1\n", encoding="utf-8")

    f_md = tmp_path / "test.md"
    f_md.write_text("# Feature: Markdown\n## Scenario: M\n* Given m1\n", encoding="utf-8")

    f_yaml = tmp_path / "test.bdd.yaml"
    f_yaml.write_text(
        "Name: StructBDD\nSteps:\n  - Step:\n      Name: Y\n      Steps:\n        - Given: y1\n",
        encoding="utf-8",
    )

    locator = FileScenarioLocator(feature_paths=[f_gherkin, f_md, f_yaml])
    features = list(locator.resolve_features())
    assert len(features) == 3

    for feat in features:
        assert isinstance(feat, Feature)
        assert len(feat.scenarios) >= 1
        for sc in feat.scenarios:
            assert isinstance(sc, Scenario)
            assert len(sc.steps) >= 1
            for st in sc.steps:
                assert isinstance(st, Step)
                assert st.keyword.strip() in ("Given", "When", "Then", "And", "But", "*")


def test_file_locator_outline_without_example_rows_yields_nothing(tmp_path: Path) -> None:
    feature_file = tmp_path / "no-rows.feature"
    feature_file.write_text(
        "Feature: No rows\n  Scenario Outline: SO\n    Given <x>\n    Examples:\n      | x |\n",
        encoding="utf-8",
    )

    assert list(FileScenarioLocator(feature_paths=[feature_file]).resolve()) == []


def test_file_locator_base_dir_from_callable_ini_and_bare_config(tmp_path: Path) -> None:
    _write_feature(tmp_path / "base.feature", "Base")

    callable_locator = FileScenarioLocator(feature_paths=["base.feature"], features_base_dir=lambda _config: tmp_path)
    assert [f.name for f in callable_locator.resolve_features()] == ["Base"]

    ini_config = SimpleNamespace(getini=lambda _name: str(tmp_path))
    ini_locator = FileScenarioLocator(feature_paths=["base.feature"])
    assert [f.name for f in ini_locator.resolve_features(ini_config)] == ["Base"]

    absolute_locator = FileScenarioLocator(feature_paths=[tmp_path / "base.feature"])
    assert [f.name for f in absolute_locator.resolve_features(object())] == ["Base"]


def test_file_locator_accepts_path_objects_and_absolute_strings(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    _write_feature(features_dir / "a.feature", "A")

    by_path_dir = FileScenarioLocator(feature_paths=[features_dir])
    assert {f.name for f in by_path_dir.resolve_features()} == {"A"}

    by_absolute_dir = FileScenarioLocator(feature_paths=[str(features_dir)])
    assert {f.name for f in by_absolute_dir.resolve_features()} == {"A"}

    by_absolute_file = FileScenarioLocator(feature_paths=[str(features_dir / "a.feature")])
    assert {f.name for f in by_absolute_file.resolve_features()} == {"A"}

    by_absolute_glob = FileScenarioLocator(feature_paths=[str(features_dir / "*.feature")])
    assert {f.name for f in by_absolute_glob.resolve_features()} == {"A"}


def test_file_locator_dot_relative_path_and_dangling_symlink(tmp_path: Path) -> None:
    _write_feature(tmp_path / "dot.feature", "Dot")
    dot_locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=["."])
    assert {f.name for f in dot_locator.resolve_features()} == {"Dot"}

    nested = tmp_path / "nested"
    nested.mkdir()
    _write_feature(nested / "deep.feature", "Deep")
    nested_locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=["nested/deep.feature"])
    assert {f.name for f in nested_locator.resolve_features()} == {"Deep"}

    dangling = nested / "dangling.feature"
    try:
        dangling.symlink_to(nested / "missing.feature")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not supported on this platform")
    dangling_locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=["nested/dangling.feature"])
    assert list(dangling_locator.resolve_features()) == []


def test_file_locator_deduplicates_repeated_paths(tmp_path: Path) -> None:
    feature_file = _write_feature(tmp_path / "dup.feature", "Dup")

    locator = FileScenarioLocator(feature_paths=[feature_file, feature_file])

    assert len(list(locator.resolve_features())) == 1


def test_file_locator_parser_selection(tmp_path: Path) -> None:
    feature_file = _write_feature(tmp_path / "parser.feature", "Parser")

    by_parser_type = FileScenarioLocator(feature_paths=[feature_file], parser_type=GherkinParser)
    assert [f.name for f in by_parser_type.resolve_features()] == ["Parser"]

    by_mimetype = FileScenarioLocator(feature_paths=[feature_file], mimetype="text/x-gherkin")
    assert [f.name for f in by_mimetype.resolve_features()] == ["Parser"]


def test_file_locator_parser_from_hooks(tmp_path: Path) -> None:
    unknown_file = tmp_path / "unknown.xyz"
    unknown_file.write_text("Feature: Hooked\n  Scenario: S\n    Given a step\n", encoding="utf-8")

    assert list(FileScenarioLocator(feature_paths=[unknown_file]).resolve_features(object())) == []

    no_mimetype_config = SimpleNamespace(
        hook=SimpleNamespace(
            pytest_bdd_get_mimetype=lambda config, path: None,
            pytest_bdd_get_parser=lambda config, mimetype: None,
        )
    )
    assert list(FileScenarioLocator(feature_paths=[unknown_file]).resolve_features(no_mimetype_config)) == []

    parser = GherkinParser()
    hook_config = SimpleNamespace(
        hook=SimpleNamespace(
            pytest_bdd_get_mimetype=lambda config, path: Mimetype.gherkin_plain.value,
            pytest_bdd_get_parser=lambda config, mimetype: parser,
        )
    )
    assert [f.name for f in FileScenarioLocator(feature_paths=[unknown_file]).resolve_features(hook_config)] == [
        "Hooked"
    ]


def _http_response(content_type: str, body: bytes):
    from unittest.mock import MagicMock

    response = MagicMock()
    response.headers.get_content_type.return_value = content_type
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_url_locator_with_base_url_and_unreachable_host() -> None:
    from unittest.mock import patch

    from pytest_bdd.scenario_locator import UrlScenarioLocator

    with patch("pytest_bdd.scenario_locator.urlopen", side_effect=OSError("no server")):
        locator = UrlScenarioLocator(url_paths=["/feature"], features_base_url="http://localhost:1")

        assert list(locator.resolve_features()) == []


def test_url_locator_falls_back_to_parser_type_and_path() -> None:
    from unittest.mock import patch

    from pytest_bdd.scenario_locator import UrlScenarioLocator

    body = b"Feature: Remote\n  Scenario: S\n    Given remote step\n"

    with patch("pytest_bdd.scenario_locator.urlopen", return_value=_http_response("", body)):
        by_parser_type = UrlScenarioLocator(url_paths=["https://example.com/no-extension"], parser_type=GherkinParser)
        assert [f.name for f in by_parser_type.resolve_features()] == ["Remote"]

    with patch("pytest_bdd.scenario_locator.urlopen", return_value=_http_response("", body)):
        by_path = UrlScenarioLocator(url_paths=["https://example.com/remote.feature"])
        assert [f.name for f in by_path.resolve_features()] == ["Remote"]
