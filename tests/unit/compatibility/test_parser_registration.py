from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from attrs import evolve
from gherkin.ast_builder import AstBuilder
from gherkin.parser import Parser
from messages import GherkinDocument
import pytest
import pytest_cuke

from pytest_cuke.batch_collection import BatchFeatureRequest
from pytest_cuke.compatibility.parser import LegacyParserAdapter, ParsedFeature
from pytest_cuke.gherkin_builder import build_feature_from_dict
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.model import Feature
from pytest_cuke.parser import GherkinParser, ParserRegistration, ParserRegistry
from pytest_cuke.utils import IdGenerator

LEGACY_SOURCE = """@feature-tag
Feature: Legacy document
  Background: Shared setup
    Given setup

  @scenario-tag
  Scenario Outline: A row <value>
    When I use <value>
    Then it is preserved

    Examples: Values
      | value |
      | one   |
"""


def test_registration_types_stay_outside_the_seven_name_root_facade() -> None:
    assert set(pytest_cuke.__all__) == {"given", "when", "then", "step", "parsers", "scenario", "scenarios"}
    assert not hasattr(pytest_cuke, "ParserRegistration")
    assert not hasattr(pytest_cuke, "ParsedFeature")


def _document(id_generator: IdGenerator) -> GherkinDocument:
    parser_factory = cast(Any, Parser)
    ast_builder_factory = cast(Any, AstBuilder)
    ast = parser_factory(ast_builder_factory(id_generator=id_generator)).parse(LEGACY_SOURCE)
    ast["uri"] = "legacy-input"
    return GherkinDocument.model_validate(ast)


class _RecordingLegacyParser:
    id_generator: IdGenerator | None = None

    def __init__(self) -> None:
        self.calls: list[tuple[Any, Path, str, tuple[object, ...], dict[str, object]]] = []
        self.last_document: GherkinDocument | None = None

    def parse(
        self,
        config: object,
        path: Path,
        uri: str,
        *args: object,
        **kwargs: object,
    ) -> ParsedFeature:
        self.calls.append((config, path, uri, args, kwargs))
        assert self.id_generator is not None
        self.last_document = _document(self.id_generator)
        return ParsedFeature(
            gherkin_document=self.last_document,
            filename="legacy-result-name.custom",
            raw_data=path.read_text(encoding=str(kwargs["encoding"])),
        )


def test_legacy_adapter_forwards_historical_inputs_and_converts_full_model(tmp_path: Path) -> None:
    source = tmp_path / "legacy.feature"
    source.write_text(LEGACY_SOURCE, encoding="utf-8")
    config = SimpleNamespace(pytest_cuke_id_generator=IdGenerator())
    parser = _RecordingLegacyParser()
    adapter = LegacyParserAdapter(parser=parser, config=config)
    parse_args = SimpleNamespace(args=("loader-flag",), kwargs={"encoding": "utf-8", "mode": "custom"})

    feature = adapter.parse(
        source,
        uri="file:features/legacy.feature",
        encoding="ascii",
        _pytest_cuke_parse_args=parse_args,
    )

    assert parser.calls[0][0] is config
    assert parser.calls[0][1:4] == (source, "file:features/legacy.feature", ("loader-flag",))
    assert parser.calls[0][4] == {"encoding": "utf-8", "mode": "custom"}
    assert parser.id_generator is config.pytest_cuke_id_generator
    assert feature.filename == "legacy-result-name.custom"
    assert feature.uri == "file:features/legacy.feature"
    assert feature.source_content == LEGACY_SOURCE
    assert feature.name == "Legacy document"
    assert feature.tags[0].name == "@feature-tag"
    assert feature.background is not None
    assert feature.background.steps[0].name == "setup"
    scenario = feature.scenarios[0]
    assert scenario.name == "A row <value>"
    assert scenario.tags[0].name == "@scenario-tag"
    assert scenario.id is not None
    assert scenario.steps[0].id is not None
    assert scenario.examples[0].rows[0].cells[0].value == "one"
    assert parser.last_document is not None
    raw_feature = parser.last_document.model_dump(mode="json", exclude_none=True, by_alias=True)["feature"]
    expected = build_feature_from_dict(
        {"feature": raw_feature},
        uri="file:features/legacy.feature",
        filename="legacy-result-name.custom",
    )
    expected = evolve(
        expected,
        source_content=LEGACY_SOURCE,
        source_media_type=Mimetype.gherkin_plain.value,
    )
    assert feature == expected

    native = GherkinParser(id_generator=IdGenerator()).parse_text(
        LEGACY_SOURCE,
        uri="file:features/legacy.feature",
        parser_mode="python",
    )
    native = evolve(
        native,
        filename="legacy-result-name.custom",
        source_content=LEGACY_SOURCE,
        source_media_type=Mimetype.gherkin_plain.value,
    )
    assert feature == native


def test_legacy_parser_type_error_is_not_retried_or_wrapped(tmp_path: Path) -> None:
    class BrokenParser:
        id_generator: IdGenerator | None = None

        def parse(self, config: object, path: Path, uri: str, *args: object, **kwargs: object) -> ParsedFeature:
            raise TypeError("inside extension")

    source = tmp_path / "broken.custom"
    source.write_text("anything", encoding="utf-8")
    error = TypeError("inside extension")
    adapter = LegacyParserAdapter(parser=BrokenParser(), config=object())

    with pytest.raises(TypeError, match="inside extension") as caught:
        adapter.parse(source, uri="file:broken.custom")

    assert type(caught.value) is type(error)


@pytest.mark.parametrize(
    ("result", "reason"),
    [
        (object(), "ParsedFeature"),
        (ParsedFeature(gherkin_document=None, filename="x", raw_data=""), "gherkin_document"),  # type: ignore[arg-type]
    ],
)
def test_legacy_parser_invalid_result_is_actionable(
    tmp_path: Path,
    result: object,
    reason: str,
) -> None:
    class InvalidParser:
        id_generator: IdGenerator | None = None

        def parse(self, config: object, path: Path, uri: str, *args: object, **kwargs: object) -> object:
            return result

    source = tmp_path / "invalid.custom"
    source.write_text("anything", encoding="utf-8")
    adapter = LegacyParserAdapter(parser=InvalidParser(), config=object())

    with pytest.raises(ValueError) as error:
        adapter.parse(source, uri="file:invalid.custom")

    assert "InvalidParser" in str(error.value)
    assert str(source) in str(error.value)
    assert "ParserRegistration.legacy" in str(error.value)
    assert reason in str(error.value)


def test_registration_provider_lifetime_is_scoped_per_config() -> None:
    created: list[_RecordingLegacyParser] = []

    def factory() -> _RecordingLegacyParser:
        parser = _RecordingLegacyParser()
        created.append(parser)
        return parser

    registration = ParserRegistration.legacy(factory)
    first_config = SimpleNamespace()
    second_config = SimpleNamespace()

    first = registration.resolve(first_config)
    assert registration.resolve(first_config) is first
    second = registration.resolve(second_config)

    assert first is not second
    assert len(created) == 2


def test_class_provider_is_instantiated_once_per_config() -> None:
    registration = ParserRegistration.legacy(_RecordingLegacyParser)
    first_config = SimpleNamespace()
    second_config = SimpleNamespace()

    first = registration.resolve(first_config)
    assert registration.resolve(first_config) is first
    second = registration.resolve(second_config)

    assert isinstance(first, LegacyParserAdapter)
    assert isinstance(second, LegacyParserAdapter)
    assert first.parser is not second.parser


def test_legacy_instance_provider_is_used_exactly_as_supplied() -> None:
    parser = _RecordingLegacyParser()
    registration = ParserRegistration.legacy(parser)

    first = registration.resolve(SimpleNamespace())
    second = registration.resolve(SimpleNamespace())

    assert isinstance(first, LegacyParserAdapter)
    assert isinstance(second, LegacyParserAdapter)
    assert first.parser is parser
    assert second.parser is parser


def test_instance_provider_is_used_exactly_as_supplied() -> None:
    class NativeParser:
        def parse(self, path: Path, uri: str | None = None, encoding: str = "utf-8", **kwargs: object) -> Any:
            raise NotImplementedError

        def parse_text(self, content: str, uri: str | None = None, **kwargs: object) -> Any:
            raise NotImplementedError

    parser = NativeParser()
    registration = ParserRegistration.native(parser)

    assert cast(object, registration.resolve(SimpleNamespace())) is parser
    assert cast(object, registration.resolve(SimpleNamespace())) is parser


def test_native_descriptor_preserves_native_parser_result() -> None:
    class NativeParser:
        def parse(self, path: Path, uri: str | None = None, encoding: str = "utf-8", **kwargs: object) -> Any:
            raise NotImplementedError

        def parse_text(self, content: str, uri: str | None = None, **kwargs: object) -> Any:
            return Feature(name="native-result")

    parser = NativeParser()
    resolved = ParserRegistration.native(parser).resolve(SimpleNamespace())

    assert resolved.parse_text("content").name == "native-result"


@pytest.mark.parametrize("provider_kind", ["class", "factory"])
def test_native_class_and_factory_providers_are_cached_per_config(provider_kind: str) -> None:
    instances: list[object] = []

    class NativeParser:
        def __init__(self) -> None:
            instances.append(self)

        def parse(self, path: Path, uri: str | None = None, encoding: str = "utf-8", **kwargs: object) -> Any:
            raise NotImplementedError

        def parse_text(self, content: str, uri: str | None = None, **kwargs: object) -> Any:
            return Feature(name=content)

    def factory() -> NativeParser:
        return NativeParser()

    provider = NativeParser if provider_kind == "class" else factory
    registration = ParserRegistration.native(provider)
    first_config = SimpleNamespace()
    second_config = SimpleNamespace()

    first = registration.resolve(first_config)
    assert registration.resolve(first_config) is first
    second = registration.resolve(second_config)

    assert first is not second
    assert len(instances) == 2
    assert first.parse_text("native").name == "native"


def test_parser_registry_can_store_an_explicit_registration() -> None:
    registration = ParserRegistration.legacy(_RecordingLegacyParser)
    registry = ParserRegistry()
    registry.register(".custom", registration)

    assert registry.get_parser(".custom") is registration


def test_distinct_legacy_providers_do_not_share_a_batch_cache_entry(tmp_path: Path) -> None:
    class OtherLegacyParser(_RecordingLegacyParser):
        pass

    config = SimpleNamespace()
    path = tmp_path / "same.custom"
    first_parser = ParserRegistration.legacy(_RecordingLegacyParser).resolve(config)
    second_parser = ParserRegistration.legacy(OtherLegacyParser).resolve(config)
    first = BatchFeatureRequest(path, "file:same.custom", "utf-8", first_parser, None, ())
    second = BatchFeatureRequest(path, "file:same.custom", "utf-8", second_parser, None, ())

    assert first.key != second.key


def test_unsupported_schema_marker_is_actionable(tmp_path: Path) -> None:
    class VersionedParser:
        id_generator: IdGenerator | None = None

        def parse(self, config: object, path: Path, uri: str, *args: object, **kwargs: object) -> object:
            return SimpleNamespace(
                gherkin_document=SimpleNamespace(schema_version="future"),
                filename=str(path),
                raw_data="source",
            )

    source = tmp_path / "versioned.custom"
    source.write_text("source", encoding="utf-8")
    adapter = LegacyParserAdapter(parser=VersionedParser(), config=object())

    with pytest.raises(ValueError, match="schema version") as error:
        adapter.parse(source, uri="file:versioned.custom")

    assert "VersionedParser" in str(error.value)
    assert str(source) in str(error.value)


def test_importing_legacy_protocol_does_not_require_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib
    import sys

    import pytest_cuke.compatibility.parser as legacy_parser_module

    monkeypatch.setitem(sys.modules, "messages", None)
    importlib.reload(legacy_parser_module)
