import linecache
from pathlib import Path
from typing import Union, cast

from attr import attrs
from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser  # type: ignore[import]
from gherkin.pickles.compiler import Compiler as PicklesCompiler
from gherkin.token_matcher_markdown import GherkinInMarkdownTokenMatcher
from gherkin.token_scanner import TokenScanner

from pytest_bdd.compatibility.gherkin import GherkinDocument
from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.model.gherkin_document import Feature
from pytest_bdd.types.exception import FeatureConcreteParseError
from pytest_bdd.types.protocol import HasPytestBDDIdGenerator

if STRUCT_BDD_INSTALLED:  # pragma: no cover
    from pytest_bdd.plugin.struct_bdd.parser import StructBDDParser  # noqa: F401


class BaseParser(ParserProtocol):
    def build_feature(self, gherkin_document_raw_dict, filename: str) -> Feature:
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
    def parse(
        self,
        config: Union[Config, HasPytestBDDIdGenerator],  # noqa: ARG002 overload
        path: Path,
        uri: str,
        *args,
        **kwargs,
    ) -> tuple[Feature, str]:
        gherkin_parser = CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator))
        encoding = kwargs.pop("encoding", "utf-8")
        feature_file_data = path.read_text(encoding=encoding)

        try:
            gherkin_document_raw_dict = cast(GherkinDocument, gherkin_parser.parse(feature_file_data, *args, **kwargs))
        except CompositeParserException as e:
            raise FeatureConcreteParseError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e

        gherkin_document_raw_dict["uri"] = uri  # type:ignore[]

        feature = self.build_feature(
            gherkin_document_raw_dict,
            filename=str(path.as_posix()),
        )
        return feature, feature_file_data


@attrs
class MarkdownGherkinParser(BaseParser):
    def parse(
        self,
        config: Union[Config, HasPytestBDDIdGenerator],  # noqa: ARG002 overload
        path: Path,
        uri: str,
        *args,  # noqa: ARG002 overload
        **kwargs,
    ):
        gherkin_parser = CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator))
        matcher = GherkinInMarkdownTokenMatcher()
        encoding = kwargs.pop("encoding", "utf-8")
        feature_file_data = path.read_text(encoding=encoding)
        token_scanner = TokenScanner(feature_file_data)

        try:
            gherkin_document_raw_dict = cast(GherkinDocument, gherkin_parser.parse(token_scanner, matcher))
        except CompositeParserException as e:
            raise FeatureConcreteParseError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e

        gherkin_document_raw_dict["uri"] = uri
        # TODO create a defect for a gherkin parser repo
        gherkin_document_raw_dict["feature"].setdefault("keyword", "")

        feature = self.build_feature(
            gherkin_document_raw_dict,
            filename=str(path.as_posix()),
        )
        return feature, feature_file_data
