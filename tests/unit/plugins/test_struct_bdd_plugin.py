from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("pydantic")

from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.model import Feature, Scenario, Step
from pytest_cuke.parser import default_parser_registry
from pytest_cuke.plugin import (
    _deduplicate_feature_scenarios,
    pytest_cuke_is_collectible as core_is_collectible,
)
from pytest_cuke.scenario_locator import FileScenarioLocator
from pytest_cuke.struct_bdd import parser as struct_bdd_parser_module
from pytest_cuke.struct_bdd.parser import StructBDDParser
from pytest_cuke.struct_bdd.plugin import StructBDDPlugin


def test_struct_bdd_plugin_get_parser() -> None:
    plugin = StructBDDPlugin()
    config = MagicMock()

    parser_partial = plugin.pytest_cuke_get_parser(config, Mimetype.struct_bdd_yaml.value)
    assert parser_partial is not None
    assert parser_partial.keywords["kind"] == StructBDDParser.KIND.YAML.value

    parser_toml = plugin.pytest_cuke_get_parser(config, Mimetype.struct_bdd_toml.value)
    assert parser_toml is not None
    assert parser_toml.keywords["kind"] == StructBDDParser.KIND.TOML.value

    assert plugin.pytest_cuke_get_parser(config, "unknown/mimetype") is None


def test_struct_bdd_plugin_get_mimetype() -> None:
    plugin = StructBDDPlugin()
    config = MagicMock()

    assert plugin.pytest_cuke_get_mimetype(config, Path("features/test.bdd.yaml")) == Mimetype.struct_bdd_yaml.value
    assert plugin.pytest_cuke_get_mimetype(config, Path("features/test.bdd.toml")) == Mimetype.struct_bdd_toml.value
    assert plugin.pytest_cuke_get_mimetype(config, Path("features/test.bdd.json")) == Mimetype.struct_bdd_json.value
    assert plugin.pytest_cuke_get_mimetype(config, Path("features/test.feature")) is None
    assert plugin.pytest_cuke_get_mimetype(config, Path("features/test.BDD.JSON")) == Mimetype.struct_bdd_json.value
    assert plugin.pytest_cuke_get_mimetype(config, Path("features/test.BDD")) == Mimetype.struct_bdd_yaml.value
    assert plugin.pytest_cuke_get_mimetype(config, Path("features/test.yaml")) is None
    assert plugin.pytest_cuke_get_mimetype(config, Path("features/test.json")) is None


def test_struct_bdd_plugin_is_collectible() -> None:
    plugin = StructBDDPlugin()
    config = MagicMock()

    assert plugin.pytest_cuke_is_collectible(config, Path("features/test.bdd.yaml")) is True
    assert plugin.pytest_cuke_is_collectible(config, Path("features/test.BDD.HOCON")) is True
    assert plugin.pytest_cuke_is_collectible(config, Path("features/test.feature")) is None
    assert plugin.pytest_cuke_is_collectible(config, Path("features/test.yaml")) is None
    assert plugin.pytest_cuke_is_collectible(config, Path("features/test.bdd.txt")) is None


@pytest.mark.parametrize(
    ("path", "expected_kind"),
    [
        ("feature.bdd", "yaml"),
        ("feature.bdd.yaml", "yaml"),
        ("feature.bdd.yml", "yaml"),
        ("feature.bdd.hocon", "hocon"),
        ("feature.bdd.json5", "json5"),
        ("feature.bdd.json", "json"),
        ("feature.bdd.hjson", "hjson"),
        ("feature.bdd.toml", "toml"),
        ("FEATURE.BDD.JSON", "json"),
    ],
)
def test_parser_registry_uses_longest_supported_suffix(path: str, expected_kind: str) -> None:
    parser = default_parser_registry.get_parser_for_path(path)

    assert isinstance(parser, StructBDDParser)
    assert parser.kind == expected_kind


@pytest.mark.parametrize("path", ["ordinary.yaml", "ordinary.yml", "ordinary.json", "unknown.bdd.txt"])
def test_parser_registry_does_not_select_struct_bdd_for_data_files(path: str) -> None:
    assert default_parser_registry.get_parser_for_path(path) is None


def test_core_collectibility_defers_unsupported_extensions_to_plugins() -> None:
    assert core_is_collectible(MagicMock(), Path("ordinary.yaml")) is None
    assert core_is_collectible(MagicMock(), Path("feature.BDD.JSON5")) is None


def test_recursive_locator_uses_casefolded_struct_bdd_suffixes_and_ignores_plain_data(tmp_path: Path) -> None:
    feature_root = tmp_path / "features"
    feature_root.mkdir()
    expected_names = {"contract.BDD.YAML", "contract.bdd", "contract.bdd.json5"}
    ignored_names = {"ordinary.yaml", "ordinary.json", "unsupported.bdd.txt"}
    for name in expected_names | ignored_names:
        (feature_root / name).write_text("", encoding="utf-8")

    locator = FileScenarioLocator(feature_paths=[feature_root], features_base_dir=tmp_path)

    assert {path.name for path in locator._gen_feature_paths(tmp_path)} == expected_names


def test_file_locator_deduplicates_overlapping_paths_after_normalization(tmp_path: Path) -> None:
    feature_path = tmp_path / "features" / "nested" / "contract.bdd.yaml"
    feature_path.parent.mkdir(parents=True)
    feature_path.write_text("Name: Feature\nSteps:\n  - Step:\n      Name: Scenario\n", encoding="utf-8")
    locator = FileScenarioLocator(
        feature_paths=[tmp_path / "features", Path("features/nested/contract.bdd.yaml"), feature_path],
        features_base_dir=tmp_path,
    )

    requests = locator.build_batch_requests()

    assert len(requests) == 1
    assert requests[0].path.resolve() == feature_path.resolve()


def test_missing_optional_parser_loader_has_actionable_path_attributed_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    feature_path = tmp_path / "optional.bdd.json5"
    feature_path.write_text("{}", encoding="utf-8")

    def missing_loader(module_name: str) -> None:
        raise ModuleNotFoundError(f"No module named '{module_name}'", name=module_name)

    monkeypatch.setattr(struct_bdd_parser_module, "import_module", missing_loader)

    with pytest.raises(FeatureConcreteParseError) as error:
        StructBDDParser(kind="json5").parse(feature_path)

    message = str(error.value)
    assert "json5" in message
    assert "pytest-cuke[struct-bdd]" in message
    assert str(feature_path.resolve()) in message


def test_structured_parse_failure_does_not_claim_a_missing_optional_loader(tmp_path: Path) -> None:
    feature_path = tmp_path / "malformed.bdd.json"
    feature_path.write_text('{"Name": "Feature", "Steps": [', encoding="utf-8")

    with pytest.raises(FeatureConcreteParseError) as error:
        StructBDDParser(kind="json").parse(feature_path)

    assert "Failed to parse structured BDD" in str(error.value)
    assert str(feature_path.resolve()) in str(error.value)
    assert "pytest-cuke[struct-bdd]" not in str(error.value)


def test_scenario_generation_deduplicates_known_sources_and_preserves_distinct_scenarios(tmp_path: Path) -> None:
    first_path = tmp_path / "first.bdd"
    second_path = tmp_path / "second.bdd"
    first_path.touch()
    second_path.touch()
    feature = Feature(name="first", filename=str(first_path))
    same_feature_alias = Feature(name="first", filename=str(first_path.parent / "nested" / ".." / first_path.name))
    other_feature = Feature(name="second", filename=str(second_path))
    scenario = Scenario(
        name="first scenario",
        id="scenario-1",
        steps=(Step(name="a step", keyword="Given"),),
    )
    distinct_scenario = Scenario(name="second scenario", steps=(Step(name="another step", keyword="Then"),))

    unique = _deduplicate_feature_scenarios(
        [
            (feature, scenario),
            (same_feature_alias, scenario),
            (feature, distinct_scenario),
            (other_feature, scenario),
        ]
    )

    assert len(unique) == 3
    assert unique == [
        (feature, scenario),
        (feature, distinct_scenario),
        (other_feature, scenario),
    ]


def test_scenario_generation_deduplicates_uri_sources_but_keeps_source_less_results() -> None:
    scenario = Scenario(name="scenario")
    same_uri_feature = Feature(name="one", uri="https://example.test/features/one.bdd")
    different_uri_feature = Feature(name="two", uri="https://example.test/features/two.bdd")
    source_less_feature = Feature(name="custom")

    unique = _deduplicate_feature_scenarios(
        [
            (same_uri_feature, scenario),
            (same_uri_feature, scenario),
            (different_uri_feature, scenario),
            (source_less_feature, scenario),
            (source_less_feature, scenario),
        ]
    )

    assert unique == [
        (same_uri_feature, scenario),
        (different_uri_feature, scenario),
        (source_less_feature, scenario),
        (source_less_feature, scenario),
    ]
