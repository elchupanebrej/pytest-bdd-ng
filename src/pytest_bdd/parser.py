from __future__ import annotations

import mimetypes
from functools import partial
from itertools import filterfalse
from operator import contains, itemgetter
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from attr import attrib, attrs
from attrs import define, field

from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser
from pytest_bdd.compatibility.path import relpath
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.exceptions import FeatureConcreteParseError
from pytest_bdd.gherkin_builder import build_feature_from_dict
from pytest_bdd.model import Feature

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.utils import PytestBDDIdGeneratorHandler

if STRUCT_BDD_INSTALLED:  # pragma: no cover
    from pytest_bdd.struct_bdd.parser import StructBDDParser

    assert StructBDDParser  # type: ignore[truthy-function]


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
    _parsers_by_key: dict[str, ParserProtocol | type[ParserProtocol]] = field(factory=dict)

    def register(self, key: str, parser: ParserProtocol | type[ParserProtocol]) -> None:
        self._parsers_by_key[key.lower()] = parser

    def get_parser(self, key: str) -> ParserProtocol | None:
        entry = self._parsers_by_key.get(key.lower())
        if entry is None:
            return None
        if isinstance(entry, type):
            return entry()
        return entry

    def get_parser_for_mimetype(self, mimetype: str) -> ParserProtocol | None:
        return self.get_parser(mimetype)

    def get_parser_for_path(self, path: Path | str) -> ParserProtocol | None:
        p = Path(path)
        name = p.name.lower()
        for key in self._parsers_by_key:
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

    def parse(
        self, config: Config | PytestBDDIdGeneratorHandler, path: Path, uri: str, *args: Any, **kwargs: Any
    ) -> tuple[Feature, str]:
        return self.build_feature({}, filename=str(path.as_posix())), ""

    def get_from_paths(self, config: Config, paths: Sequence[Path], **kwargs: Any) -> Sequence[Feature]:
        seen_names: set[Path] = set()
        features_content: list[tuple[Feature, str]] = []
        features_base_dir = kwargs.pop("features_base_dir", Path.cwd())
        if not features_base_dir.is_absolute():
            features_base_dir = Path.cwd() / features_base_dir

        for rel_path in map(Path, paths):
            path = rel_path if rel_path.is_absolute() else Path(features_base_dir) / rel_path
            file_paths = list(map(Path, self.glob(path))) if path.is_dir() else [Path(path)]
            features_content.extend(
                [
                    self.parse(config, p, "file:" + relpath(str(p), str(features_base_dir)), **kwargs)
                    for p in filterfalse(partial(contains, seen_names), file_paths)
                ]
            )
            for file_path in file_paths:
                if file_path not in seen_names:
                    seen_names.add(path)

        features = map(itemgetter(0), features_content)
        return sorted(features, key=lambda feature: feature.name or feature.filename)


@attrs
class MarkdownGherkinParser(BaseParser):
    glob: Callable[..., Sequence[str | Path]] = attrib(
        default=lambda path: path.glob("*.feature.md") + path.glob("*.gherkin.md"), kw_only=True
    )

    def parse(
        self, config: Config | PytestBDDIdGeneratorHandler, path: Path, uri: str, *args: Any, **kwargs: Any
    ) -> tuple[Feature, str]:
        return self.build_feature({}, filename=str(path.as_posix())), ""


default_parser_registry.register(".feature", GherkinParser)
default_parser_registry.register(".gherkin", GherkinParser)
default_parser_registry.register("text/x-gherkin", GherkinParser)


__all__ = [
    "BaseParser",
    "GherkinParser",
    "MarkdownGherkinParser",
    "ParserProtocol",
    "ParserRegistry",
    "default_parser_registry",
]
