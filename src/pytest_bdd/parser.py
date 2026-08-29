from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from attr import attrib, attrs
from attrs import define, field

from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser
from gherkin.token_scanner import TokenScanner
from pytest_bdd.exceptions import FeatureConcreteParseError
from pytest_bdd.gherkin_builder import build_feature_from_dict
from pytest_bdd.markdown_token_matcher import MarkdownTokenMatcher
from pytest_bdd.model import Feature

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


@runtime_checkable
class ParserProtocol(Protocol):
    def parse(self, path: Path | str, uri: str | None = None, encoding: str = "utf-8", **kwargs: Any) -> Feature: ...
    def parse_text(self, content: str, uri: str | None = None, **kwargs: Any) -> Feature: ...


@define
class BaseParser:
    id_generator: Any = None

    def parse_text(self, content: str, uri: str | None = None, **kwargs: Any) -> Feature:
        raise NotImplementedError

    def parse(self, path: Path | str, uri: str | None = None, encoding: str = "utf-8", **kwargs: Any) -> Feature:
        p = Path(path)
        content = p.read_text(encoding=encoding)
        resolved_uri = uri or str(p.as_posix())
        feature = self.parse_text(content, uri=resolved_uri, **kwargs)
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
            )
        return feature

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
            return entry()
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
    def parse_text(
        self,
        content: str,
        uri: str | None = None,
        **kwargs: Any,
    ) -> Feature:
        parser = CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator))
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
    def parse_text(
        self,
        content: str,
        uri: str | None = None,
        **kwargs: Any,
    ) -> Feature:
        matcher = MarkdownTokenMatcher()
        scanner = TokenScanner(content)
        parser = CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator))
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
