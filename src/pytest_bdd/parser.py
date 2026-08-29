from __future__ import annotations

import json
import linecache
from contextlib import ExitStack
from functools import partial
from itertools import filterfalse
from operator import contains, itemgetter
from pathlib import Path
from shutil import which
from subprocess import CalledProcessError, check_output
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from attr import attrib, attrs
from attrs import define

from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser  # type: ignore[import]
from gherkin.pickles.compiler import Compiler as PicklesCompiler
from pytest_bdd.compatibility.importlib.resources import as_file, files
from pytest_bdd.compatibility.path import relpath
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.exceptions import FeatureConcreteParseError, FeatureParseError
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
        gherkin_document = Feature.load_gherkin_document(gherkin_document_raw_dict)
        pickles_data = PicklesCompiler(id_generator=self.id_generator).compile(gherkin_document_raw_dict)
        pickles = Feature.load_pickles(pickles_data)
        return Feature(  # type: ignore[call-arg]
            gherkin_document=gherkin_document,
            uri=gherkin_document.uri,
            pickles=pickles,
            filename=filename,
        )


@attrs
class GherkinParser(BaseParser):
    glob: Callable[..., Sequence[str | Path]] = attrib(
        default=lambda path: path.glob("*.feature") + path.glob("*.gherkin"), kw_only=True
    )

    def parse(
        self, config: Config | PytestBDDIdGeneratorHandler, path: Path, uri: str, *args: Any, **kwargs: Any
    ) -> tuple[Feature, str]:
        gherkin_parser = CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator))
        encoding = kwargs.pop("encoding", "utf-8")
        with path.open(mode="r", encoding=encoding) as feature_file:
            feature_file_data = feature_file.read()

        try:
            gherkin_document_raw_dict = gherkin_parser.parse(feature_file_data, *args, **kwargs)
        except CompositeParserException as e:
            raise FeatureConcreteParseError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e

        gherkin_document_raw_dict["uri"] = uri
        feature = self.build_feature(gherkin_document_raw_dict, filename=str(path.as_posix()))
        return feature, feature_file_data

    # TODO Move out of parser to loader component
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
        with ExitStack() as stack:
            feature_file, script_path = [
                stack.enter_context(path.open(mode="rb")),
                stack.enter_context(as_file(files("pytest_bdd").joinpath("markdown_parser.js"))),
            ]
            try:
                gherkin_document_raw_dict = json.loads(
                    check_output([which("node") or "", script_path], stdin=feature_file)  # noqa: S603
                )
            except CalledProcessError as e:
                raise FeatureParseError(f"Unable to parse {path}") from e
        gherkin_document_raw_dict["uri"] = uri
        feature = self.build_feature(gherkin_document_raw_dict, filename=str(path.as_posix()))
        return feature, path.read_text()
