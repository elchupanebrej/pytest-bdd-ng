from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast, runtime_checkable

from attr import attrib, attrs
from attrs import define, evolve, field
from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser
from gherkin.token_scanner import TokenScanner

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
    _parsers_by_key: dict[str, ParserProtocol | type[ParserProtocol] | Callable[[], ParserProtocol]] = field(
        factory=dict
    )

    def register(self, key: str, parser: ParserProtocol | type[ParserProtocol] | Callable[[], ParserProtocol]) -> None:
        self._parsers_by_key[key.lower()] = parser

    def get_parser(self, key: str) -> ParserProtocol | None:
        entry = self._parsers_by_key.get(key.lower())
        if entry is None:
            return None
        if isinstance(entry, type):
            return cast("ParserProtocol", entry())
        if callable(entry):
            return entry()
        return entry

    def get_parser_for_mimetype(self, mimetype: str) -> ParserProtocol | None:
        return self.get_parser(mimetype)

    def get_parser_for_path(self, path: Path | str) -> ParserProtocol | None:
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
        parser = _new_gherkin_parser(self.id_generator)
        try:
            raw_dict = parser.parse(content)
        except CompositeParserException as e:
            first_err = e.errors[0] if hasattr(e, "errors") and e.errors else None
            loc = getattr(first_err, "location", None) or {}
            line = loc.get("line", 0)
            line_text = ""
            lines = content.splitlines()
            if 1 <= line <= len(lines):
                line_text = lines[line - 1]
            raise FeatureConcreteParseError(
                str(e),
                line,
                line_text,
                uri or "",
            ) from e
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
        matcher = MarkdownTokenMatcher()
        scanner = cast("Callable[[str], Any]", TokenScanner)(content)
        parser = _new_gherkin_parser(self.id_generator)
        try:
            raw_dict = parser.parse(scanner, token_matcher=matcher)
        except CompositeParserException as e:
            first_err = e.errors[0] if hasattr(e, "errors") and e.errors else None
            loc = getattr(first_err, "location", None) or {}
            line = loc.get("line", 0)
            line_text = ""
            lines = content.splitlines()
            if 1 <= line <= len(lines):
                line_text = lines[line - 1]
            raise FeatureConcreteParseError(
                str(e),
                line,
                line_text,
                uri or "",
            ) from e
        return build_feature_from_dict(raw_dict, uri=uri or "")


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
    "ParserRegistry",
    "default_parser_registry",
]
