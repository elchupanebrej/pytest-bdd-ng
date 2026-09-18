from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pytest_bdd.model.feature import Feature
from pytest_bdd.parser import BaseParser, ParserProtocol, ParserRegistry

from pytest import mark

pytestmark = mark.unit


if TYPE_CHECKING:
    from pathlib import Path


class DummyParser(BaseParser):
    def parse_text(self, content: str, uri: str | None = None, **kwargs: object) -> Feature:
        return Feature(name=content.strip(), uri=uri or "")


class FilenameSettingParser(BaseParser):
    def parse_text(self, content: str, uri: str | None = None, **kwargs: object) -> Feature:
        return Feature(name=content.strip(), uri=uri or "", filename="provided.feature")


def test_parser_protocol_conformance() -> None:
    parser = DummyParser()
    assert isinstance(parser, ParserProtocol)


def test_base_parser_file_reading(tmp_path: Path) -> None:
    test_file = tmp_path / "dummy.feature"
    test_file.write_text("Hello Feature", encoding="utf-8")

    parser = DummyParser()
    feature = parser.parse(test_file)
    assert feature.name == "Hello Feature"
    assert feature.filename == str(test_file.as_posix())


def test_base_parser_keeps_parser_supplied_filename(tmp_path: Path) -> None:
    test_file = tmp_path / "dummy.feature"
    test_file.write_text("Hello Feature", encoding="utf-8")

    feature = FilenameSettingParser().parse(test_file)
    assert feature.filename == "provided.feature"


def test_base_parser_parse_text_is_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        BaseParser().parse_text("content")


def test_base_parser_build_feature_from_raw_dict() -> None:
    raw = {"feature": {"name": "Raw Feature", "keyword": "Feature", "children": []}}
    feature = BaseParser().build_feature(raw, filename="raw.feature")
    assert feature.name == "Raw Feature"
    assert feature.filename == "raw.feature"


def test_parser_registry_registration_and_lookup(tmp_path: Path) -> None:
    registry = ParserRegistry()
    dummy = DummyParser()

    registry.register(".custom", dummy)
    registry.register("application/x-custom", dummy)

    assert registry.get_parser(".custom") is dummy
    assert registry.get_parser_for_mimetype("application/x-custom") is dummy

    file_path = tmp_path / "scenario.custom"
    assert registry.get_parser_for_path(file_path) is dummy
    assert registry.get_parser_for_path("scenario.unknown") is None


def test_parser_registry_factory_and_mimetype_fallback(tmp_path: Path) -> None:
    registry = ParserRegistry()
    dummy = DummyParser()

    registry.register(".factory", lambda: dummy)
    registry.register("text/x-python", dummy)

    assert registry.get_parser("missing") is None
    assert registry.get_parser(".factory") is dummy
    assert registry.get_parser_for_path(tmp_path / "script.py") is dummy
