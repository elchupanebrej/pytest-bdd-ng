from __future__ import annotations

import mimetypes
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast, runtime_checkable

from attr import attrib, attrs
from attrs import define, evolve, field
from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser
from gherkin.token_scanner import TokenScanner

from pytest_cuke.compatibility.parser import LegacyParserAdapter
from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.external_examples import (
    attach_external_examples_sources,
    expand_external_examples,
    map_feature_source_lines,
    remap_parse_error,
)
from pytest_cuke.gherkin_builder import build_feature_from_dict
from pytest_cuke.markdown_token_matcher import MarkdownTokenMatcher
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.model import Feature
from pytest_cuke.parser_backend import parse_gherkin_document

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    class _GherkinParserProtocol(Protocol):
        def parse(self, token_scanner_or_str: Any, token_matcher: Any = None) -> Any: ...


def _new_gherkin_parser(id_generator: Any) -> _GherkinParserProtocol:
    """Adapt gherkin-official's untyped parser boundary to the runtime contract we use."""
    ast_builder = cast("Callable[..., Any]", AstBuilder)(id_generator=id_generator)
    parser_factory = cast("Callable[..., _GherkinParserProtocol]", CucumberIOBaseParser)
    return parser_factory(ast_builder=ast_builder)


@runtime_checkable
class ParserProtocol(Protocol):
    def parse(self, path: Path | str, uri: str | None = None, encoding: str = "utf-8", **kwargs: Any) -> Feature: ...
    def parse_text(self, content: str, uri: str | None = None, **kwargs: Any) -> Feature: ...


_PARSER_REGISTRATIONS_CONFIG_ATTRIBUTE = "_pytest_cuke_parser_registrations"


@define(frozen=True)
class ParserRegistration:
    """Explicitly declare how a parser provider implements the parser contract.

    Use :meth:`native` for the current path/URI/text -> ``Feature`` protocol and
    :meth:`legacy` for the historical config-aware ``ParsedFeature`` protocol.
    Classes and zero-argument factories are instantiated once per pytest config;
    parser instances are reused as provided. The per-config cache keeps class- and
    factory-created parsers isolated between independent pytest runs.
    """

    contract: str
    provider: Any

    @classmethod
    def native(cls, provider: Any) -> ParserRegistration:
        return cls("native", provider)

    @classmethod
    def legacy(cls, provider: Any) -> ParserRegistration:
        return cls("legacy", provider)

    def resolve(self, config: Any = None) -> ParserProtocol:
        if config is None:
            return self._build_parser(config)

        cache = _registration_cache(config)
        if cache is None:
            return self._build_parser(config)

        cache_key = (self.contract, id(self.provider))
        cached = cache.get(cache_key)
        if cached is not None and cached[0] is self.provider:
            return cached[1]

        parser = self._build_parser(config)
        cache[cache_key] = (self.provider, parser)
        return parser

    def _build_parser(self, config: Any) -> ParserProtocol:
        provider = self.provider
        if isinstance(provider, type):
            parser = provider()
        elif callable(getattr(provider, "parse", None)):
            parser = provider
        elif callable(provider):
            parser = provider()
        else:
            parser = provider

        if not callable(getattr(parser, "parse", None)):
            raise TypeError(
                f"ParserRegistration.{self.contract} provider {provider!r} did not produce an object with parse()."
            )
        if self.contract == "legacy":
            return cast("ParserProtocol", LegacyParserAdapter(parser=parser, config=config))
        if self.contract == "native":
            return cast("ParserProtocol", parser)
        raise ValueError(f"Unknown parser contract {self.contract!r}; use ParserRegistration.native() or .legacy().")


def _registration_cache(config: Any) -> dict[tuple[str, int], tuple[Any, ParserProtocol]] | None:
    cache = getattr(config, _PARSER_REGISTRATIONS_CONFIG_ATTRIBUTE, None)
    if cache is not None:
        return cast("dict[tuple[str, int], tuple[Any, ParserProtocol]]", cache)
    cache = {}
    try:
        config._pytest_cuke_parser_registrations = cache
    except (AttributeError, TypeError):
        return None
    return cache


def clear_parser_registrations(config: Any) -> None:
    """Drop parser instances after pytest finishes this config's collection/run."""
    with suppress(AttributeError):
        delattr(config, _PARSER_REGISTRATIONS_CONFIG_ATTRIBUTE)


@define
class BaseParser:
    supports_external_examples: ClassVar[bool] = False
    id_generator: Any = None

    def parse_text(self, content: str, uri: str | None = None, **kwargs: Any) -> Feature:
        raise NotImplementedError

    def parse(self, path: Path | str, uri: str | None = None, encoding: str = "utf-8", **kwargs: Any) -> Feature:
        p = Path(path)
        content = p.read_text(encoding=encoding)
        source_content = content
        external_examples = None
        if self.supports_external_examples:
            external_examples = expand_external_examples(content, p)
            content = external_examples.content
        resolved_uri = uri or str(p.as_posix())
        try:
            feature = self.parse_text(content, uri=resolved_uri, **kwargs)
        except FeatureConcreteParseError as error:
            if external_examples is not None:
                remap_parse_error(error, external_examples, source_content, resolved_uri)
            raise
        if external_examples is not None:
            feature = attach_external_examples_sources(feature, external_examples.bindings)
            feature = map_feature_source_lines(feature, external_examples.line_map)
        if feature.source_content is None:
            source_media_type = feature.source_media_type or self._source_media_type(p)
            feature = evolve(feature, source_content=source_content, source_media_type=source_media_type)
        if feature.filename is None:
            return Feature(
                name=feature.name,
                line=feature.line,
                tags=feature.tags,
                description=feature.description,
                background=feature.background,
                scenarios=feature.scenarios,
                rules=feature.rules,
                uri=feature.uri,
                id=feature.id,
                keyword=feature.keyword,
                language=feature.language,
                filename=str(p.as_posix()),
                source_content=feature.source_content,
                source_media_type=feature.source_media_type,
            )
        return feature

    def _source_media_type(self, path: Path) -> str:
        if path.name.lower().endswith((".md", ".markdown")):
            return Mimetype.markdown.value
        if self.supports_external_examples:
            return Mimetype.gherkin_plain.value
        kind = getattr(self, "kind", None)
        structured_media_type = getattr(Mimetype, f"struct_bdd_{kind}", None) if kind else None
        if structured_media_type is not None:
            return str(structured_media_type.value)
        return mimetypes.guess_type(path.name)[0] or Mimetype.gherkin_plain.value

    def build_feature(self, gherkin_document_raw_dict: Any, filename: str) -> Feature:
        return build_feature_from_dict(gherkin_document_raw_dict, filename=filename)


@define
class ParserRegistry:
    _parsers_by_key: dict[
        str, ParserProtocol | ParserRegistration | type[ParserProtocol] | Callable[[], ParserProtocol]
    ] = field(
        factory=dict
    )

    def register(
        self,
        key: str,
        parser: ParserProtocol | ParserRegistration | type[ParserProtocol] | Callable[[], ParserProtocol],
    ) -> None:
        self._parsers_by_key[key.lower()] = parser

    def get_parser(self, key: str) -> ParserProtocol | ParserRegistration | None:
        entry = self._parsers_by_key.get(key.lower())
        if entry is None:
            return None
        if isinstance(entry, ParserRegistration):
            return entry
        if isinstance(entry, type):
            return cast("ParserProtocol", entry())
        if callable(entry):
            return entry()
        return entry

    def get_parser_for_mimetype(self, mimetype: str) -> ParserProtocol | ParserRegistration | None:
        return self.get_parser(mimetype)

    def get_parser_for_path(self, path: Path | str) -> ParserProtocol | ParserRegistration | None:
        p = Path(path)
        name = p.name.lower()
        for key in sorted(self._parsers_by_key, key=len, reverse=True):
            if key.startswith(".") and name.endswith(key):
                return self.get_parser(key)
        suffix = p.suffix.lower()
        if suffix in self._parsers_by_key:
            return self.get_parser(suffix)
        guessed_type, _ = mimetypes.guess_type(str(p))
        if guessed_type and guessed_type.lower() in self._parsers_by_key:
            return self.get_parser(guessed_type)
        return None


default_parser_registry = ParserRegistry()


@define
class GherkinParser(BaseParser):
    supports_external_examples: ClassVar[bool] = True

    def parse_text(
        self,
        content: str,
        uri: str | None = None,
        **kwargs: Any,
    ) -> Feature:
        raw_dict = parse_gherkin_document(
            content,
            kwargs.get("parser_mode"),
            markdown=False,
            python_parser=lambda: _parse_python_document(content, uri, self.id_generator, markdown=False),
        )
        return build_feature_from_dict(raw_dict, uri=uri or "")


@attrs
class LegacyGherkinParser(BaseParser):
    glob: Callable[..., Sequence[str | Path]] = attrib(
        default=lambda path: path.glob("*.feature") + path.glob("*.gherkin"), kw_only=True
    )


@define
class MarkdownParser(BaseParser):
    supports_external_examples: ClassVar[bool] = True

    def parse_text(
        self,
        content: str,
        uri: str | None = None,
        **kwargs: Any,
    ) -> Feature:
        raw_dict = parse_gherkin_document(
            content,
            kwargs.get("parser_mode"),
            markdown=True,
            python_parser=lambda: _parse_python_document(content, uri, self.id_generator, markdown=True),
        )
        return build_feature_from_dict(raw_dict, uri=uri or "")


def _parse_python_document(
    content: str,
    uri: str | None,
    id_generator: Any,
    *,
    markdown: bool,
) -> dict[str, Any]:
    parser = _new_gherkin_parser(id_generator)
    if markdown:
        token_scanner = cast("Callable[[str], Any]", TokenScanner)(content)
        token_matcher: Any = MarkdownTokenMatcher()
        parser_input: Any = token_scanner
    else:
        token_matcher = None
        parser_input = content

    try:
        if markdown:
            raw_document = parser.parse(parser_input, token_matcher=token_matcher)
        else:
            raw_document = parser.parse(parser_input)
    except CompositeParserException as exc:
        first_error = exc.errors[0] if getattr(exc, "errors", None) else None
        location = getattr(first_error, "location", None) or {}
        line = location.get("line", 0)
        column = location.get("column", 1)
        if not isinstance(line, int):
            line = 0
        if not isinstance(column, int) or column < 1:
            column = 1
        lines = content.splitlines()
        line_text = lines[line - 1] if isinstance(line, int) and 1 <= line <= len(lines) else ""
        raise FeatureConcreteParseError(str(exc), line, line_text, uri or "", column=column) from exc
    if not isinstance(raw_document, dict):
        raise FeatureConcreteParseError("Gherkin parser returned an invalid document", 0, "", uri or "")
    return raw_document


# Aliases for backwards compatibility
MarkdownGherkinParser = MarkdownParser

default_parser_registry.register(".feature", GherkinParser)
default_parser_registry.register(".gherkin", GherkinParser)
default_parser_registry.register("text/x-gherkin", GherkinParser)
default_parser_registry.register(".feature.md", MarkdownParser)
default_parser_registry.register(".gherkin.md", MarkdownParser)
default_parser_registry.register(".md", MarkdownParser)
default_parser_registry.register("text/x-markdown", MarkdownParser)


__all__ = [
    "BaseParser",
    "GherkinParser",
    "LegacyGherkinParser",
    "MarkdownGherkinParser",
    "MarkdownParser",
    "ParserProtocol",
    "ParserRegistration",
    "ParserRegistry",
    "clear_parser_registrations",
    "default_parser_registry",
]
