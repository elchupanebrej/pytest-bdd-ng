import linecache
from inspect import getfile, getsourcelines
from pathlib import Path
from typing import cast

from attrs import define
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    JavaMethod,
    JavaStackTraceElement,
    Location,
    ParseError,
    SourceReference,
)
from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser  # type: ignore[import]
from gherkin.token_matcher_markdown import GherkinInMarkdownTokenMatcher
from gherkin.token_scanner import TokenScanner

from pytest_bdd.compatibility.gherkin import GherkinDocument
from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.model.scenario_run import FeatureRuntimeBinding
from pytest_bdd.types.exception import FeatureConcreteParseError
from pytest_bdd.types.protocol import HasPytestStash

if STRUCT_BDD_INSTALLED:  # pragma: no cover
    from pytest_bdd.plugin.struct_bdd.parser import StructBDDParser  # noqa: F401


class BaseParser(ParserProtocol):
    @staticmethod
    def _build_parse_error_source(*, uri: str, line: int, column: int) -> SourceReference:
        source_kwargs = {
            "uri": uri,
            "location": Location(line=max(1, int(line)), column=max(1, int(column))),
        }
        with_suppress = (OSError, TypeError, ValueError)
        try:
            source_file = getfile(BaseParser)
            source_line = getsourcelines(BaseParser.emit_parse_error)[1]
        except with_suppress:
            source_file = None
            source_line = None

        if source_file is not None and source_line is not None:
            source_kwargs.update(
                {
                    "java_method": JavaMethod(
                        class_name=f"{BaseParser.__module__}.{BaseParser.__name__}",
                        method_name="emit_parse_error",
                        method_parameter_types=["message", "line", "column", "uri"],
                    ),
                    "java_stack_trace_element": JavaStackTraceElement(
                        class_name=f"{BaseParser.__module__}.{BaseParser.__name__}",
                        file_name=Path(source_file).name,
                        method_name="emit_parse_error",
                    ),
                }
            )
        return SourceReference(**source_kwargs)

    @staticmethod
    def emit_parse_error(config: Config | HasPytestStash, *, message: str, line: int, column: int, uri: str):
        hook_handler = getattr(config, "hook", None)
        emitter = getattr(hook_handler, "pytest_bdd_message", None) if hook_handler is not None else None
        if not callable(emitter):
            return
        try:
            emitter(
                config=config,
                message=Message(
                    parse_error=ParseError(
                        message=message,
                        source=BaseParser._build_parse_error_source(uri=uri, line=line, column=column),
                    )
                ),
            )
        except (AttributeError, TypeError, ValueError, RuntimeError):  # pragma: no cover
            return

    @staticmethod
    def normalize_gherkin_document_payload(gherkin_document_raw_dict: GherkinDocument) -> GherkinDocument:
        gherkin_document_raw_dict.setdefault("comments", [])

        def _normalize(node):
            if isinstance(node, dict):
                location = node.get("location")
                if isinstance(location, dict):
                    if "line" not in location:
                        location["line"] = 1
                    if "column" not in location:
                        location["column"] = 1
                for value in node.values():
                    _normalize(value)
            elif isinstance(node, list):
                for value in node:
                    _normalize(value)

        _normalize(gherkin_document_raw_dict)
        return gherkin_document_raw_dict

    @staticmethod
    def build_feature(gherkin_document_raw_dict) -> GherkinDocument:
        gherkin_document = FeatureRuntimeBinding.load_gherkin_document(gherkin_document_raw_dict)
        # TODO: here must adapter layer not just direct casting
        return cast(GherkinDocument, gherkin_document)


@define
class GherkinParser(BaseParser):
    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args,
        **kwargs,
    ) -> tuple[GherkinDocument, str]:
        gherkin_parser = CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator))
        encoding = kwargs.pop("encoding", "utf-8")
        feature_file_data = path.read_text(encoding=encoding)

        try:
            gherkin_document_raw_dict = cast(GherkinDocument, gherkin_parser.parse(feature_file_data, *args, **kwargs))
        except CompositeParserException as e:
            error_location = e.errors[0].location
            self.emit_parse_error(
                config,
                message=str(e.args[0]),
                line=int(error_location.get("line", 1)),
                column=int(error_location.get("column", 1)),
                uri=uri,
            )
            raise FeatureConcreteParseError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e

        gherkin_document_raw_dict["uri"] = uri  # type:ignore[]
        gherkin_document_raw_dict = self.normalize_gherkin_document_payload(gherkin_document_raw_dict)

        feature = self.build_feature(gherkin_document_raw_dict)
        feature._pytest_bdd_filename = str(path.as_posix())
        return feature, feature_file_data


@define
class MarkdownGherkinParser(BaseParser):
    def parse(
        self,
        config: Config | HasPytestStash,
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
            error_location = e.errors[0].location
            self.emit_parse_error(
                config,
                message=str(e.args[0]),
                line=int(error_location.get("line", 1)),
                column=int(error_location.get("column", 1)),
                uri=uri,
            )
            raise FeatureConcreteParseError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e

        gherkin_document_raw_dict["uri"] = uri
        # TODO create a defect for a gherkin parser repo
        gherkin_document_raw_dict["feature"].setdefault("keyword", "")
        gherkin_document_raw_dict = self.normalize_gherkin_document_payload(gherkin_document_raw_dict)

        feature = self.build_feature(gherkin_document_raw_dict)
        feature._pytest_bdd_filename = str(path.as_posix())
        return feature, feature_file_data
