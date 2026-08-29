from __future__ import annotations

import json

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
