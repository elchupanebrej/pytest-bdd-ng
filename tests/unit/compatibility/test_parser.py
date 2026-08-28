from __future__ import annotations

from pathlib import Path

from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol


def test_parsed_feature_instantiation() -> None:
    feature = ParsedFeature(
        gherkin_document=None,  # type: ignore[arg-type]
        filename="test.feature",
        raw_data="Feature: Test\n",
    )
    assert feature.filename == "test.feature"
    assert feature.raw_data == "Feature: Test\n"


def test_parser_protocol_conformance() -> None:
    class CustomParser:
        id_generator = None

        def parse(self, config: object, path: Path, uri: str, *args: object, **kwargs: object) -> ParsedFeature:
            return ParsedFeature(gherkin_document=None, filename=str(path), raw_data="")  # type: ignore[arg-type]

    parser = CustomParser()
    assert isinstance(parser, ParserProtocol)
    result = parser.parse(None, Path("test.feature"), "test.feature")
    assert result.filename == "test.feature"
