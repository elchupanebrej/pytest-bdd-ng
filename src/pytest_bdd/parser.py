"""
Provide parser helpers.

Responsibility:
    Provide parser helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parser` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - BaseParser: owns nested behavior below this boundary
    - GherkinParser: owns nested behavior below this boundary
    - MarkdownGherkinParser: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `parser`
    - src/pytest_bdd/model/coverage/inventory.py: imports or references `parser`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `parser`
    - src/pytest_bdd/parsers/parse_parser.py: imports or references `parser`
    - src/pytest_bdd/plugin/code_generator/entrypoint.py: imports or references `parser`

State and side effects:
    mutates gherkin_document_raw_dict, source_file, source_line, gherkin_parser, encoding; depends on linecache,
    inspect.getfile, inspect.getsourcelines, pathlib.Path, typing.Any.

Invariants:
    - `pytest_bdd.parser` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Failure semantics:
    Raises or re-raises FeatureConcreteParseError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

import linecache
from inspect import getfile, getsourcelines
from pathlib import Path
from typing import Any, cast

from attrs import define
from cucumber_messages import (
    Envelope as Message,  # upstream library missing type stubs
)
from cucumber_messages import (  # type:ignore[attr-defined]  # upstream library missing type stubs
    GherkinDocument,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    ParseError,
    SourceReference,
)
from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser  # conditional gherkin import
from gherkin.token_matcher_markdown import GherkinInMarkdownTokenMatcher
from gherkin.token_scanner import TokenScanner

from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.model.feature_binding import FeatureRuntimeBinding  # pylint: disable=downward-import
from pytest_bdd.types.exception import FeatureConcreteParseError
from pytest_bdd.types.protocol import HasPytestStash

if STRUCT_BDD_INSTALLED:  # pragma: no cover
    from pytest_bdd.plugin.struct_bdd.parser import StructBDDParser  # noqa: F401 # pylint: disable=downward-import


class BaseParser(ParserProtocol):
    """
    Build feature documents and emit parse diagnostics.

    Responsibility:
        Build feature documents and emit parse diagnostics. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parser.BaseParser` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - _build_parse_error_source: owns nested behavior below this boundary
        - emit_parse_error: owns nested behavior below this boundary
        - normalize_gherkin_document_payload: owns nested behavior below this boundary
        - build_feature: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `BaseParser`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `BaseParser`

    State and side effects:
        mutates source_file, source_line, source_kwargs, with_suppress, hook_handler.

    Invariants:
        - `pytest_bdd.parser.BaseParser` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    @staticmethod
    def _build_parse_error_source(*, uri: str, line: int, column: int) -> SourceReference:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parser.BaseParser._build_parse_error_source` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parser.BaseParser._build_parse_error_source` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - max: collaborator call used by this boundary
            - int: collaborator call used by this boundary
            - Location: collaborator call used by this boundary
            - getfile: collaborator call used by this boundary
            - getsourcelines: collaborator call used by this boundary
            - source_kwargs.update: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `_build_parse_error_source`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_build_parse_error_source`

        State and side effects:
            mutates source_file, source_line, source_kwargs, with_suppress.

        Invariants:
            - `pytest_bdd.parser.BaseParser._build_parse_error_source` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
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
                },
            )
        return SourceReference(**source_kwargs)

    @staticmethod
    def emit_parse_error(config: Config | HasPytestStash, *, message: str, line: int, column: int, uri: str) -> None:
        """
        Handle emit parse error.

        Responsibility:
            Handle emit parse error. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parser.BaseParser.emit_parse_error` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - callable: collaborator call used by this boundary
            - emitter: collaborator call used by this boundary
            - Message: collaborator call used by this boundary
            - ParseError: collaborator call used by this boundary
            - BaseParser._build_parse_error_source: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `emit_parse_error`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `emit_parse_error`

        State and side effects:
            mutates hook_handler, emitter.

        Invariants:
            - `pytest_bdd.parser.BaseParser.emit_parse_error` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
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
                    ),
                ),
            )
        except (AttributeError, TypeError, ValueError, RuntimeError):  # pragma: no cover
            return

    @staticmethod
    def normalize_gherkin_document_payload(gherkin_document_raw_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize gherkin document payload.

        Returns:
            Normalized gherkin document dictionary.

        Responsibility:
            Normalize gherkin document payload. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parser.BaseParser.normalize_gherkin_document_payload`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _normalize: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references
              `normalize_gherkin_document_payload`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
              `normalize_gherkin_document_payload`

        State and side effects:
            mutates location.

        Invariants:
            - `pytest_bdd.parser.BaseParser.normalize_gherkin_document_payload` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        gherkin_document_raw_dict.setdefault("comments", [])

        def _normalize(node: object) -> None:
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.parser.BaseParser.normalize_gherkin_document_payload._normalize` owns documented method
                behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
                method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.parser.BaseParser.normalize_gherkin_document_payload._normalize` because it keeps the
                nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - isinstance: collaborator call used by this boundary
                - _normalize: collaborator call used by this boundary
                - node.get: collaborator call used by this boundary
                - node.values: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/collector_batch.py: imports or references `_normalize`
                - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `_normalize`
                - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_normalize`

            State and side effects:
                mutates location.

            Invariants:
                - `pytest_bdd.parser.BaseParser.normalize_gherkin_document_payload._normalize` keeps its documented
                  import path, ownership boundary, and observable behavior stable for callers.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=4
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=4
            """
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
    def build_feature(gherkin_document_raw_dict: dict[str, Any]) -> GherkinDocument:
        """
        Build feature from gherkin document dict.

        Returns:
            Built feature object.

        Responsibility:
            Build feature from gherkin document dict. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parser.BaseParser.build_feature` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - FeatureRuntimeBinding.load_gherkin_document: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `build_feature`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `build_feature`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `build_feature`
            - src/pytest_bdd/plugin/struct_bdd/parser.py: imports or references `build_feature`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return FeatureRuntimeBinding.load_gherkin_document(gherkin_document_raw_dict)


@define
class GherkinParser(BaseParser):
    """
    Handle gherkin parser.

    Raises:
        FeatureConcreteParseError: If the operation cannot be completed.

    Responsibility:
        Handle gherkin parser. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parser.GherkinParser` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - parse: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `GherkinParser`
        - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `GherkinParser`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `GherkinParser`

    State and side effects:
        mutates gherkin_document_raw_dict, gherkin_parser, encoding, feature_file_data, error_location.

    Invariants:
        - `pytest_bdd.parser.GherkinParser` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises FeatureConcreteParseError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4

    """

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args: object,  # noqa: ARG002 overload
        **kwargs: object,
    ) -> ParsedFeature:
        """
        Parse gherkin feature file.

        Returns:
            ParsedFeature with the document, filename, and raw data.

        Raises:
            FeatureConcreteParseError: If the operation cannot be completed.

        Responsibility:
            Parse gherkin feature file. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parser.GherkinParser.parse` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - int: collaborator call used by this boundary
            - error_location.get: collaborator call used by this boundary
            - CucumberIOBaseParser: collaborator call used by this boundary
            - AstBuilder: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse`
            - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `parse`
            - src/pytest_bdd/collector_batch.py: imports or references `parse`
            - src/pytest_bdd/hook.py: imports or references `parse`
            - src/pytest_bdd/parsers/__init__.py: imports or references `parse`

        State and side effects:
            mutates gherkin_document_raw_dict, gherkin_parser, encoding, feature_file_data, error_location.

        Invariants:
            - `pytest_bdd.parser.GherkinParser.parse` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises FeatureConcreteParseError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        gherkin_parser = CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator))
        encoding = cast("str", kwargs.pop("encoding", "utf-8"))
        feature_file_data = path.read_text(encoding=encoding)

        try:
            gherkin_document_raw_dict = cast("dict[str, Any]", gherkin_parser.parse(feature_file_data))
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
        gherkin_document_raw_dict = self.normalize_gherkin_document_payload(gherkin_document_raw_dict)

        feature = self.build_feature(gherkin_document_raw_dict)
        return ParsedFeature(
            gherkin_document=feature,
            filename=str(path.as_posix()),
            raw_data=feature_file_data,
        )


@define
class MarkdownGherkinParser(BaseParser):
    """
    Handle markdown gherkin parser.

    Raises:
        FeatureConcreteParseError: If the operation cannot be completed.

    Responsibility:
        Handle markdown gherkin parser. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parser.MarkdownGherkinParser` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parse: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `MarkdownGherkinParser`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `MarkdownGherkinParser`

    State and side effects:
        mutates gherkin_document_raw_dict, gherkin_parser, matcher, encoding, feature_file_data.

    Invariants:
        - `pytest_bdd.parser.MarkdownGherkinParser` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises FeatureConcreteParseError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3

    """

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args: object,  # noqa: ARG002 overload
        **kwargs: object,
    ) -> ParsedFeature:
        """
        Parse markdown gherkin feature file.

        Returns:
            ParsedFeature with the document, filename, and raw data.

        Raises:
            FeatureConcreteParseError: If the operation cannot be completed.

        Responsibility:
            Parse markdown gherkin feature file. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parser.MarkdownGherkinParser.parse` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - int: collaborator call used by this boundary
            - error_location.get: collaborator call used by this boundary
            - CucumberIOBaseParser: collaborator call used by this boundary
            - AstBuilder: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse`
            - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `parse`
            - src/pytest_bdd/collector_batch.py: imports or references `parse`
            - src/pytest_bdd/hook.py: imports or references `parse`
            - src/pytest_bdd/parsers/__init__.py: imports or references `parse`

        State and side effects:
            mutates gherkin_document_raw_dict, gherkin_parser, matcher, encoding, feature_file_data.

        Invariants:
            - `pytest_bdd.parser.MarkdownGherkinParser.parse` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises FeatureConcreteParseError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        gherkin_parser = CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator))
        matcher = GherkinInMarkdownTokenMatcher()
        encoding = cast("str", kwargs.pop("encoding", "utf-8"))
        feature_file_data = path.read_text(encoding=encoding)
        token_scanner = TokenScanner(feature_file_data)

        try:
            gherkin_document_raw_dict = cast("dict[str, Any]", gherkin_parser.parse(token_scanner, matcher))
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
        # TODO: create a defect for a gherkin parser repo
        gherkin_document_raw_dict["feature"].setdefault("keyword", "")
        gherkin_document_raw_dict = self.normalize_gherkin_document_payload(gherkin_document_raw_dict)

        feature = self.build_feature(gherkin_document_raw_dict)
        return ParsedFeature(
            gherkin_document=feature,
            filename=str(path.as_posix()),
            raw_data=feature_file_data,
        )
