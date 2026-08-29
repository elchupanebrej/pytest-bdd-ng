from __future__ import annotations

import json
from pathlib import Path  # noqa: TCH003

from pytest_bdd.struct_bdd.parser import StructBDDParser


def test_parse_yaml_struct_bdd_feature() -> None:
    yaml_text = """
    Name: YAML Feature
    Description: Testing YAML struct BDD
    Tags:
      - "@yaml"
    Steps:
      - Step:
          Name: Simple YAML Scenario
          Tags:
            - "@smoke"
          Steps:
            - Given: setup step
            - When: action step
            - Then: verify step
    """
    parser = StructBDDParser(kind="yaml")
    feature = parser.parse_text(yaml_text, uri="test.bdd.yaml")

    assert feature.name == "YAML Feature"
    assert feature.description == "Testing YAML struct BDD"
    assert [t.name for t in feature.tags] == ["@yaml"]
    assert len(feature.scenarios) == 1

    sc = feature.scenarios[0]
    assert sc.name == "Simple YAML Scenario"
    assert len(sc.steps) == 3
    assert [s.name for s in sc.steps] == ["setup step", "action step", "verify step"]


def test_parse_json_struct_bdd_feature() -> None:
    data = {
        "Name": "JSON Feature",
        "Tags": ["@json"],
        "Steps": [
            {
                "Step": {
                    "Name": "JSON Scenario",
                    "Steps": [
                        {"Given": "json given"},
                        {"When": "json when"},
                        {"Then": "json then"},
                    ],
                }
            }
        ],
    }
    json_text = json.dumps(data)
    parser = StructBDDParser(kind="json")
    feature = parser.parse_text(json_text, uri="test.bdd.json")

    assert feature.name == "JSON Feature"
    assert len(feature.scenarios) == 1
    sc = feature.scenarios[0]
    assert sc.name == "JSON Scenario"
    assert [s.name for s in sc.steps] == ["json given", "json when", "json then"]


def test_parse_toml_struct_bdd_feature() -> None:
    import tomli_w

    data = {
        "Name": "TOML Feature",
        "Tags": ["@toml"],
        "Steps": [
            {
                "Step": {
                    "Name": "TOML Scenario",
                    "Steps": [
                        {"Given": "toml given"},
                        {"Then": "toml then"},
                    ],
                }
            }
        ],
    }
    toml_text = tomli_w.dumps(data)
    parser = StructBDDParser(kind="toml")
    feature = parser.parse_text(toml_text, uri="test.bdd.toml")

    assert feature.name == "TOML Feature"
    assert len(feature.scenarios) == 1
    sc = feature.scenarios[0]
    assert sc.name == "TOML Scenario"
    assert [s.name for s in sc.steps] == ["toml given", "toml then"]


def test_parse_struct_bdd_file(tmp_path: Path) -> None:
    yaml_file = tmp_path / "sample.bdd.yaml"
    yaml_file.write_text(
        "Name: File YAML Feature\nSteps:\n  - Step:\n      Name: Scenario One\n      Steps:\n        - Given: step\n",
        encoding="utf-8",
    )
    parser = StructBDDParser(kind="yaml")
    feature = parser.parse(yaml_file)
    assert feature.name == "File YAML Feature"
    assert feature.filename == str(yaml_file.as_posix())


def test_registry_lookup_struct_bdd() -> None:
    from pytest_bdd.parser import default_parser_registry

    p_yaml = default_parser_registry.get_parser_for_path("test.bdd.yaml")
    p_json = default_parser_registry.get_parser_for_path("test.bdd.json")
    p_toml = default_parser_registry.get_parser_for_path("test.bdd.toml")

    assert isinstance(p_yaml, StructBDDParser)
    assert isinstance(p_json, StructBDDParser)
    assert isinstance(p_toml, StructBDDParser)
