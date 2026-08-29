from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.struct_bdd.parser import StructBDDParser
from pytest_bdd.struct_bdd.plugin import StructBDDPlugin


def test_struct_bdd_plugin_get_parser() -> None:
    plugin = StructBDDPlugin()
    config = MagicMock()

    parser_partial = plugin.pytest_bdd_get_parser(config, Mimetype.struct_bdd_yaml.value)
    assert parser_partial is not None
    assert parser_partial.keywords["kind"] == StructBDDParser.KIND.YAML.value

    parser_toml = plugin.pytest_bdd_get_parser(config, Mimetype.struct_bdd_toml.value)
    assert parser_toml is not None
    assert parser_toml.keywords["kind"] == StructBDDParser.KIND.TOML.value

    assert plugin.pytest_bdd_get_parser(config, "unknown/mimetype") is None


def test_struct_bdd_plugin_get_mimetype() -> None:
    plugin = StructBDDPlugin()
    config = MagicMock()

    assert plugin.pytest_bdd_get_mimetype(config, Path("features/test.bdd.yaml")) == Mimetype.struct_bdd_yaml.value
    assert plugin.pytest_bdd_get_mimetype(config, Path("features/test.bdd.toml")) == Mimetype.struct_bdd_toml.value
    assert plugin.pytest_bdd_get_mimetype(config, Path("features/test.bdd.json")) == Mimetype.struct_bdd_json.value
    assert plugin.pytest_bdd_get_mimetype(config, Path("features/test.feature")) is None


def test_struct_bdd_plugin_is_collectible() -> None:
    plugin = StructBDDPlugin()
    config = MagicMock()

    assert plugin.pytest_bdd_is_collectible(config, Path("features/test.bdd.yaml")) is True
    assert plugin.pytest_bdd_is_collectible(config, Path("features/test.feature")) is None
