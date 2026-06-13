"""
Python-based Gherkin feature file parsers for plain-text and Markdown Gherkin formats.

Responsibility:
    Python-based Gherkin feature file parsers for plain-text and Markdown Gherkin formats. Defines BaseParser (abstract
    base with shared static methods for Cucumber Messages error reporting, Gherkin document normalization, and
    GherkinDocument construction), GherkinParser (parses plain .feature files using the gherkin library's
    CucumberIOBaseParser), and MarkdownGherkinParser (parses .feature.md files using GherkinInMarkdownTokenMatcher with
    a TokenScanner). Both concrete parsers implement the ParserProtocol interface and produce ParsedFeature results
    containing typed GherkinDocuments.

Reason for existence:
    This module is the information expert for "how to parse a single Gherkin feature file from disk into a typed parsed
    representation." It is placed in the parsing layer (order 2) as the synchronous, full-featured parsing path — as
    opposed to collector_batch.py which handles batch/parallel parsing with Go parser integration. The parsers here are
    used directly by the scenario locators (FileScenarioLocator, UrlScenarioLocator) when they need to parse individual
    feature files with full error reporting, URI annotation, and document normalization. The BaseParser class factors
    out shared behavior (error message emission via pytest-bdd hooks, default-value normalization, GherkinDocument
    construction via FeatureRuntimeBinding) that would otherwise be duplicated between GherkinParser and
    MarkdownGherkinParser.

Delegates:
    - gherkin.parser.Parser (CucumberIOBaseParser): The upstream Python Gherkin parser that produces raw dicts from
    Gherkin text.
    - gherkin.token_matcher_markdown.GherkinInMarkdownTokenMatcher: Matches Gherkin tokens within Markdown documents.
    - gherkin.token_scanner.TokenScanner: Tokenizes input text for the markdown token matcher.
    - gherkin.ast_builder.AstBuilder: Builds the Gherkin AST with the parser's ID generator.
    - BaseParser.normalize_gherkin_document_payload: Ensures default values for location fields and comments list.
    - BaseParser.build_feature: Constructs a typed GherkinDocument from a normalized dict via FeatureRuntimeBinding.
    - BaseParser.emit_parse_error: Sends a Cucumber Messages ParseError envelope through the pytest-bdd hook system.
    - BaseParser._build_parse_error_source: Constructs a SourceReference with Java-style stack trace metadata.
    - pytest_bdd.model.feature_binding.FeatureRuntimeBinding.load_gherkin_document: Deserializes and validates the
    GherkinDocument.
    - cucumber_messages: Provides typed message classes (GherkinDocument, ParseError, SourceReference, etc.).

Cohesion:
    All classes in this module are Gherkin parsers that share the same interface (ParserProtocol.parse()), the same
    output type (ParsedFeature), and the same error-reporting strategy (emit_parse_error → pytest_bdd_message hook). The
    BaseParser provides shared static methods used by both subclasses. The two concrete classes differ only in how they
    invoke the upstream parser (plain: parse(token_scanner=default); markdown: parse(token_scanner, matcher)). There are
    no unrelated utilities.

Separation:
    - pytest_bdd.collector_batch: Handles batch/parallel parsing with Go parser integration and caching. The batch
    parser does not use these classes — it uses _parse_feature_file which directly calls the Go parser or the raw
    CucumberIOBaseParser. The parsers here are the synchronous, single-file, full-featured path.
    - pytest_bdd.model.feature_binding.FeatureRuntimeBinding: Owns the GherkinDocument loading and validation.
    BaseParser.build_feature delegates to it.
    - pytest_bdd._gherkin_go: The Go ctypes parser backend. Not imported here — the batch parser uses it instead.

Main consumers:
    - pytest_bdd.scenario_locator.FileScenarioLocator / UrlScenarioLocator: Instantiate GherkinParser or
    MarkdownGherkinParser (or StructBDDParser if installed) to parse feature files during scenario discovery.
    - pytest_bdd.compatibility.parser.ParserProtocol: The protocol interface that these parsers implement, allowing
    locators to accept any parser type.

State and side effects:
    GherkinParser and MarkdownGherkinParser are attrs-defined classes with an id_generator field (inherited from
    ParserProtocol). Their parse() methods read feature files from disk (path.read_text()), call the upstream gherkin
    parser (CPU-bound), normalize the resulting dict (mutating default values), and construct a GherkinDocument
    (validation + deserialization). emit_parse_error sends messages through the pytest-bdd hook system (side effect on
    the reporting pipeline). The module conditionally imports StructBDDParser when the struct_bdd plugin is installed.

Invariants:
    - Every parse() call must annotate the raw dict with the file URI before normalization.
    - normalize_gherkin_document_payload must ensure every dict node has a "location" key with at least {"line": 1,
    "column": 1}.
    - MarkdownGherkinParser must additionally ensure the feature node has a "keyword" key (workaround for an upstream
    parser defect).
    - emit_parse_error must gracefully handle cases where the pytest_bdd_message hook is not registered (callable check
    + exception suppression).

Failure semantics:
    CompositeParserException from the upstream gherkin parser is caught in both parse() methods, reported via
    emit_parse_error, and re-raised as FeatureConcreteParseError with the error message, line number, source line text,
    and URI. This allows test frameworks to display the failing Gherkin line in error output. emit_parse_error itself
    suppresses AttributeError, TypeError, ValueError, and RuntimeError to gracefully handle missing or misconfigured
    hook handlers.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
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
    Abstract base class for Gherkin parsers providing shared static methods for error reporting and document construction.

    Responsibility:
        Abstract base class for Gherkin parsers providing shared static methods for error reporting and document
        construction. Defines four static methods: _build_parse_error_source (constructs Cucumber Messages
        SourceReference with Java-style stack trace metadata from the calling frame), emit_parse_error (sends ParseError
        messages through the pytest_bdd_message hook), normalize_gherkin_document_payload (recursively ensures default
        location fields and comments list), and build_feature (constructs a typed GherkinDocument from a normalized dict
        via FeatureRuntimeBinding.load_gherkin_document). Implements ParserProtocol but does not define the parse()
        method — that is left to concrete subclasses.

    Reason for existence:
        GherkinParser and MarkdownGherkinParser share significant behavior: error reporting via emit_parse_error,
        document normalization to fill in missing location/comment fields, and GherkinDocument construction via
        FeatureRuntimeBinding. Without BaseParser, this shared logic would be duplicated. The class is placed in
        parser.py rather than a separate base module because it is tightly coupled to the parsing concern — the source-
        location introspection in _build_parse_error_source uses getfile/getsourcelines against BaseParser itself to
        provide meaningful Java-style stack trace metadata in ParseError messages.

    Delegates:
        - _build_parse_error_source: Constructs the SourceReference for parse error messages with frame introspection.
        - emit_parse_error: Sends ParseError envelopes through the pytest-bdd hook system.
        - normalize_gherkin_document_payload: Normalizes the raw Gherkin dict before document construction.
        - build_feature: Constructs a GherkinDocument via FeatureRuntimeBinding.load_gherkin_document.

    Cohesion:
        All four static methods serve the single concern of "prepare a parsed Gherkin dict for downstream consumption
        with proper error handling." _build_parse_error_source and emit_parse_error handle the error path.
        normalize_gherkin_document_payload and build_feature handle the success path. There is no unrelated logic.

    Separation:
        - GherkinParser / MarkdownGherkinParser: Concrete subclasses that implement parse() using this base's shared methods.
        - pytest_bdd.model.feature_binding.FeatureRuntimeBinding: Owns GherkinDocument loading. BaseParser delegates to
        it but does not own the loading logic.
        - pytest_bdd.collector_batch._parse_feature_file: Bypasses this class entirely, using raw parser calls for performance.

    Main consumers:
        - GherkinParser.parse() and MarkdownGherkinParser.parse(): Call normalize_gherkin_document_payload,
        build_feature, and emit_parse_error.
        - Scenario locators: Use the concrete subclasses, not BaseParser directly.
        - External error-reporting tools: The parse error SourceReference points to BaseParser.emit_parse_error as the
        source method.

    State and side effects:
        _build_parse_error_source uses inspect.getfile/getsourcelines to introspect BaseParser's own source location —
        this is a read-only side effect on the filesystem (reading the source file for line info). emit_parse_error
        sends messages through pytest hooks (side effect on the reporting pipeline). normalize_gherkin_document_payload
        mutates the input dict in-place. build_feature delegates to FeatureRuntimeBinding.load_gherkin_document which
        performs validation.

    Invariants:
        - _build_parse_error_source must reference BaseParser.emit_parse_error as the source method for Java-style stack traces.
        - normalize_gherkin_document_payload must set default "comments": [] on the root dict.
        - The _normalize inner function in normalize_gherkin_document_payload must recursively handle both dict and list nodes.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
    """

    @staticmethod
    def _build_parse_error_source(*, uri: str, line: int, column: int) -> SourceReference:
        """
        Construct a Cucumber Messages SourceReference object for parse error reporting.

        Responsibility:
            Constructs a Cucumber Messages SourceReference object for parse error reporting. Creates a Location with the
            given line and column (clamped to minimum 1). Attempts to introspect BaseParser's own source code via
            inspect.getfile and inspect.getsourcelines to populate JavaMethod and JavaStackTraceElement metadata
            pointing to BaseParser.emit_parse_error. If introspection fails (OSError, TypeError, ValueError), the Java-
            style metadata is omitted. The resulting SourceReference links parse errors back to the parser source for
            debugging and CI integration.

        Reason for existence:
            Cucumber Messages parse errors carry source references that identify where the parsing error was detected.
            This method constructs those references with Java-style stack trace elements that point to emit_parse_error,
            providing a traceable path from the error message back through the parser code. The Java-style metadata
            (JavaMethod, JavaStackTraceElement) follows the cucumber-messages protocol which was designed for the Java
            Cucumber implementation.

        Delegates:
            - inspect.getfile(BaseParser): Gets the file containing BaseParser's source.
            - inspect.getsourcelines(BaseParser.emit_parse_error): Gets the source lines of emit_parse_error.
            - Location / JavaMethod / JavaStackTraceElement / SourceReference constructors: Build the nested message objects.

        Cohesion:
            Single-purpose: build a SourceReference for a parse error. Every line contributes to constructing the reference object.

        Separation:
            - emit_parse_error: Calls this method to build the source reference for the ParseError message it emits.

        Main consumers:
            - emit_parse_error: Called to build the source portion of ParseError envelopes.

        State and side effects:
            Reads BaseParser's source file from disk via inspect.getfile/getsourcelines (read-only I/O). No mutation.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
        Emit a Cucumber Messages ParseError envelope through the pytest-bdd_message hook.

        Responsibility:
            Emits a Cucumber Messages ParseError envelope through the pytest-bdd_message hook. Takes the error details
            (message, line, column, uri), builds a SourceReference via _build_parse_error_source, constructs a
            ParseError message, wraps it in a Message envelope, and sends it through config.hook.pytest_bdd_message. If
            the hook is not available (missing handler) or the emission fails (AttributeError, TypeError, ValueError,
            RuntimeError), silently returns. This method is the bridge between Gherkin parse failures and the
            reporting/formatter plugin layer.

        Reason for existence:
            Parse errors in Gherkin files need to be reported to the user in a structured way that formatter plugins
            (cucumber_json, cucumber_pretty, etc.) can consume. This method encapsulates the hook discovery and message
            construction so that concrete parser subclasses only need to call emit_parse_error(config, **error_details).
            The graceful degradation (silently returning when no hook is available) ensures that parse errors don't
            crash collection when formatter plugins are not installed.

        Delegates:
            - _build_parse_error_source: Constructs the SourceReference for the ParseError.
            - config.hook.pytest_bdd_message: The pytest hook that distributes messages to formatter plugins.
            - Message / ParseError constructors: Build the cucumber-messages protocol objects.

        Cohesion:
            Single-purpose: emit a parse error through the hook system. The try/except suppresses failures in the hook chain.

        Separation:
            - GherkinParser.parse() / MarkdownGherkinParser.parse(): Catch CompositeParserException and call this method
            before re-raising as FeatureConcreteParseError.
            - pytest_bdd.plugin.gherkin_message_reporter: The plugin that receives these messages and writes them to NDJSON/formats.

        Main consumers:
            - GherkinParser.parse(): Called when the upstream parser raises CompositeParserException.
            - MarkdownGherkinParser.parse(): Same usage pattern.

        State and side effects:
            Reads from config.hook (accesses pytest's hook relay). Calls hook.pytest_bdd_message which may trigger
            writer I/O, log output, or formatter state updates. The message emission is a fire-and-forget side effect —
            no return value is expected.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
        Normaliz a raw Gherkin document dict produced by the upstream parser to ensure all required fields have default val.

        Responsibility:
            Normalizes a raw Gherkin document dict produced by the upstream parser to ensure all required fields have
            default values. Sets a default empty "comments" list on the root dict if missing. Recursively walks all
            nested dicts and lists via the inner _normalize function, ensuring every dict node that has a "location" key
            also has "line" and "column" keys (defaulting to 1 if missing). This prevents downstream code from
            encountering KeyError when accessing assumed-always-present fields. Mutates the input dict in-place and
            returns it.

        Reason for existence:
            The upstream gherkin parser may omit certain optional fields from its output dict (e.g., "comments" when a
            feature has no comments, or "column" in some location objects). This inconsistency would force every
            consumer of Gherkin documents to defensively check for missing keys. This method centralizes the
            normalization, ensuring a consistent schema for all downstream code (build_feature, the batch parser,
            formatters).

        Delegates:
            - _normalize (inner function): Recursively walks the dict/list tree, filling in default location fields.

        Cohesion:
            Single-purpose: normalize a Gherkin dict to a consistent schema. The recursive walk handles arbitrary nesting depths.

        Separation:
            - build_feature: Consumes the normalized dict to construct a GherkinDocument.
            - pytest_bdd.collector_batch._documents_equivalent._normalize: A different normalization (stripping None and
            id fields for comparison), not filling defaults.

        Main consumers:
            - GherkinParser.parse() and MarkdownGherkinParser.parse(): Call this after the upstream parse and URI
            annotation, before build_feature.
            - Potentially any code that receives raw Gherkin dicts from the upstream parser.

        State and side effects:
            Mutates the input dict in-place (sets default "comments", fills missing "line"/"column" in nested dicts). No
            I/O, no external state modification.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        gherkin_document_raw_dict.setdefault("comments", [])

        def _normalize(node: object) -> None:
            """
            Recursively walks a nested dict/list structure representing a Gherkin AST node.

            Responsibility:
                Recursively walks a nested dict/list structure representing a Gherkin AST node. For each dict, if it
                contains a "location" key (also a dict), ensures that "line" and "column" keys exist within the location
                dict, defaulting to 1 if missing. Then recursively processes all values of the dict. For lists,
                recursively processes each element. Non-dict, non-list nodes are the recursion base case and are
                skipped.

            Reason for existence:
                The upstream Gherkin parser may produce location dicts with only one of "line" or "column" (or neither
                for some node types). This inner function ensures both fields are present so that downstream code can
                safely access location["line"] and location["column"] without KeyError. It is nested inside
                normalize_gherkin_document_payload because it is an implementation detail of the normalization strategy
                and is not reusable outside this context.

            Delegates:
                - Recursive calls to self for nested dicts and list values.

            Cohesion:
                Single-purpose: recursively fill default location fields. The isinstance checks handle the three node
                types (dict, list, other).

            Separation:
                - pytest_bdd.collector_batch._documents_equivalent._normalize: A different normalization (stripping
                fields for comparison), not filling defaults.

            Main consumers:
                - normalize_gherkin_document_payload: Called once at the root dict, then recursively by itself.

            State and side effects:
                Mutates nested dicts in-place (sets location["line"] and location["column"] defaults). No I/O.

            Architecture score:
                #arch-eval:reason_for_existence=3
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=5
                #arch-eval:cohesion=5
                #arch-eval:separation=5
                #arch-eval:consumer_clarity=3
                #arch-eval:state_invariants=5
                #arch-eval:entity_fullness=2
                #arch-eval:locational_stability=5
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
        Construct a typed GherkinDocument from a normalized raw dict by delegating to FeatureRuntimeBinding.load_gherkin_doc.

        Responsibility:
            Constructs a typed GherkinDocument from a normalized raw dict by delegating to
            FeatureRuntimeBinding.load_gherkin_document. This static method is the final step in the parse pipeline: raw
            text → upstream parse → normalize → build_feature → ParsedFeature. The load_gherkin_document call performs
            deserialization and validation, ensuring the resulting GherkinDocument is a valid cucumber-messages object.

        Reason for existence:
            The conversion from raw dict to typed GherkinDocument is non-trivial — it involves message validation, enum
            resolution, and nested object construction. This method encapsulates the delegation to FeatureRuntimeBinding
            so that concrete parser subclasses don't need to import or know about the model layer. It is a static method
            because the conversion is a pure function of the input dict.

        Delegates:
            - FeatureRuntimeBinding.load_gherkin_document: Validates and deserializes the dict into a GherkinDocument.

        Cohesion:
            Single-purpose: dict → GherkinDocument. One line of logic.

        Separation:
            - normalize_gherkin_document_payload: Prepares the dict for this method by filling defaults.
            - pytest_bdd.model.feature_binding.FeatureRuntimeBinding: Owns the loading/validation logic.

        Main consumers:
            - GherkinParser.parse() and MarkdownGherkinParser.parse(): Called as the final step before wrapping in ParsedFeature.

        State and side effects:
            None. The load_gherkin_document call is a pure function of its input (though it may perform internal
            validation/warnings).

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=5
        """
        return FeatureRuntimeBinding.load_gherkin_document(gherkin_document_raw_dict)


@define
class GherkinParser(BaseParser):
    """
    Parses plain-text Gherkin .feature files into ParsedFeature results.

    Responsibility:
        Parses plain-text Gherkin .feature files into ParsedFeature results. Implements the parse() method required by
        ParserProtocol: reads the file from disk, runs the upstream CucumberIOBaseParser (wrapping its AstBuilder),
        catches CompositeParserException for error reporting (via emit_parse_error) and re-raising as
        FeatureConcreteParseError, annotates the raw dict with the file URI, normalizes the dict via
        normalize_gherkin_document_payload, constructs a typed GherkinDocument via build_feature, and returns a
        ParsedFeature with the document, filename, and raw text. This is the standard parser for non-Markdown feature
        files.

    Reason for existence:
        This is the default Gherkin parser used by FileScenarioLocator and UrlScenarioLocator when no custom parser_type
        is specified. It handles the complete parse pipeline for plain Gherkin (not Markdown) files. It is an attrs-
        defined class (inheriting id_generator from ParserProtocol) so that instances can be configured with custom ID
        generators. It is separate from MarkdownGherkinParser because plain and markdown parsing require different token
        matchers and normalization workarounds.

    Delegates:
        - CucumberIOBaseParser: The upstream Python Gherkin parser.
        - AstBuilder: Builds the AST with id_generator.
        - path.read_text(): Reads the feature file from disk.
        - emit_parse_error: Reports parse errors through the pytest-bdd hook.
        - normalize_gherkin_document_payload: Normalizes the raw dict.
        - build_feature: Constructs the typed GherkinDocument.
        - linecache.getline: Retrieves the source line for FeatureConcreteParseError construction.

    Cohesion:
        The parse() method is a linear pipeline: read → parse → handle errors → annotate → normalize → build → return.
        Every step serves the single goal of "produce a ParsedFeature from a plain Gherkin file."

    Separation:
        - MarkdownGherkinParser: Handles Markdown Gherkin with TokenScanner and GherkinInMarkdownTokenMatcher, plus a
        markdown-specific keyword workaround.
        - pytest_bdd.collector_batch._parse_feature_file: Bypasses this class for performance, using raw parser calls directly.

    Main consumers:
        - pytest_bdd.scenario_locator.FileScenarioLocator / UrlScenarioLocator: Instantiate GherkinParser to parse
        feature files during scenario discovery. The parser_type parameter allows users to substitute alternative
        parsers.

    State and side effects:
        id_generator: a callable from ParserProtocol used by AstBuilder. parse() reads feature files from disk, calls
        the upstream parser (CPU-bound), mutates the raw dict (via normalize_gherkin_document_payload), and potentially
        emits parse error messages through hooks.

    Invariants:
        - The GherkinDocument must be annotated with the file URI before normalization.
        - CompositeParserException must be caught, reported via emit_parse_error, and re-raised as FeatureConcreteParseError.
        - The encoding parameter defaults to "utf-8" and is popped from kwargs.

    Failure semantics:
        CompositeParserException is caught, reported via emit_parse_error, and re-raised as
        FeatureConcreteParseError(message, line, source_line, uri). This provides structured error information for test
        reporters.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
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
        Pars a plain-text Gherkin .feature file into a ParsedFeature.

        Responsibility:
            Parses a plain-text Gherkin .feature file into a ParsedFeature. Creates a CucumberIOBaseParser with the
            instance's id_generator via AstBuilder, reads the file content with the specified encoding, invokes the
            parser to produce a raw dict, catches and transforms CompositeParserException into FeatureConcreteParseError
            (with hook emission), annotates the dict with the file URI, normalizes field defaults, constructs a typed
            GherkinDocument, and returns a ParsedFeature wrapping the document, filename, and raw text.

        Reason for existence:
            This is the core parsing method for plain Gherkin files. It implements the ParserProtocol interface used by
            scenario locators. The linear pipeline design (read → parse → handle errors → normalize → build → return)
            ensures each step has a clear responsibility and failures are handled at the appropriate level. The
            CompositeParserException → FeatureConcreteParseError translation provides user-friendly error messages with
            the exact Gherkin line that failed.

        Delegates:
            - CucumberIOBaseParser(ast_builder=AstBuilder(id_generator=self.id_generator)): Creates the upstream parser.
            - path.read_text(encoding=encoding): Reads the feature file.
            - gherkin_parser.parse(feature_file_data): Produces the raw dict.
            - emit_parse_error: Emits a ParseError message through hooks on failure.
            - linecache.getline: Retrieves the source line for error construction.
            - normalize_gherkin_document_payload: Normalizes field defaults.
            - build_feature: Constructs the typed GherkinDocument.
            - ParsedFeature constructor: Wraps the result.

        Cohesion:
            The method is a strict sequence of steps, each depending on the previous. No branching beyond error
            handling. Every line serves the parse → ParsedFeature goal.

        Separation:
            - MarkdownGherkinParser.parse: Differs in using TokenScanner and GherkinInMarkdownTokenMatcher.
            - BaseParser methods: The normalize, build, and emit steps are inherited from BaseParser.

        Main consumers:
            - Scenario locators (FileScenarioLocator, UrlScenarioLocator): Call parse() when discovering scenarios in feature files.

        State and side effects:
            Reads the feature file from disk. Creates and destroys a CucumberIOBaseParser instance. Mutates the raw dict
            (normalize step). May emit hook messages (error path). Constructs a GherkinDocument (validation).

        Failure semantics:
            CompositeParserException is caught, reported via emit_parse_error, and re-raised as
            FeatureConcreteParseError(e.args[0], line, source_line, uri). The source_line is retrieved via
            linecache.getline to show the user the exact failing Gherkin text.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
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
    Parses Markdown Gherkin .feature.md files into ParsedFeature results.

    Responsibility:
        Parses Markdown Gherkin .feature.md files into ParsedFeature results. Implements the parse() method with
        Markdown-specific token matching: creates a GherkinInMarkdownTokenMatcher and TokenScanner to parse Gherkin
        embedded within Markdown documents. Applies a workaround for an upstream parser defect by ensuring the feature
        node has a "keyword" key (defaulting to empty string). Otherwise follows the same pipeline as GherkinParser:
        read, parse, error handling, URI annotation, normalization, and GherkinDocument construction.

    Reason for existence:
        Gherkin-in-Markdown is a format where Gherkin scenarios are embedded in Markdown documents using fenced code
        blocks. The upstream gherkin library supports this via GherkinInMarkdownTokenMatcher + TokenScanner, which
        requires a different parsing path than plain Gherkin. This class encapsulates that difference while inheriting
        all shared behavior from BaseParser. It is separate from GherkinParser because the tokenizer/matcher setup and
        the keyword workaround are markdown-specific concerns.

    Delegates:
        - CucumberIOBaseParser: The upstream Python Gherkin parser.
        - GherkinInMarkdownTokenMatcher: Matches Gherkin tokens within Markdown.
        - TokenScanner: Tokenizes the input text for the markdown matcher.
        - AstBuilder: Builds the AST with id_generator.
        - path.read_text(): Reads the feature file.
        - emit_parse_error: Reports parse errors through hooks.
        - normalize_gherkin_document_payload: Normalizes the raw dict.
        - build_feature: Constructs the typed GherkinDocument.

    Cohesion:
        The parse() method follows the same linear pipeline as GherkinParser with two markdown-specific additions:
        TokenScanner + GherkinInMarkdownTokenMatcher for parsing, and the keyword default workaround. All logic serves
        the single goal of "produce a ParsedFeature from a Markdown Gherkin file."

    Separation:
        - GherkinParser: Handles plain Gherkin without TokenScanner/Matcher. The two classes share BaseParser but differ
        in their parse() implementation.
        - pytest_bdd.collector_batch._resolve_mimetype: Determines whether a file is markdown based on extension. The
        locators use this to choose between GherkinParser and MarkdownGherkinParser.

    Main consumers:
        - Scenario locators: Select MarkdownGherkinParser when the feature file has a .feature.md extension or the
        mimetype indicates markdown.

    State and side effects:
        Same as GherkinParser: reads files, parses, normalizes, constructs documents, may emit hook messages. The
        keyword workaround mutates the raw dict in-place ("feature" → "keyword" default).

    Invariants:
        - Must set a default "keyword" key on the feature node to work around an upstream gherkin parser defect.
        - Must use TokenScanner + GherkinInMarkdownTokenMatcher instead of the default token matcher.

    Failure semantics:
        Same as GherkinParser: CompositeParserException → emit_parse_error + FeatureConcreteParseError.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
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
        Pars a Markdown Gherkin .feature.md file into a ParsedFeature.

        Responsibility:
            Parses a Markdown Gherkin .feature.md file into a ParsedFeature. Creates a CucumberIOBaseParser with the
            instance's id_generator, a GherkinInMarkdownTokenMatcher for Markdown-aware token matching, and a
            TokenScanner for text tokenization. Reads the file, invokes the parser with the scanner and matcher, catches
            and transforms CompositeParserException into FeatureConcreteParseError (with hook emission), annotates the
            dict with the file URI, applies a markdown-specific workaround (setting default "keyword": "" on the feature
            node), normalizes field defaults, constructs a typed GherkinDocument, and returns a ParsedFeature.

        Reason for existence:
            Markdown Gherkin requires a fundamentally different parsing setup from plain Gherkin: the input must be
            tokenized by TokenScanner and matched by GherkinInMarkdownTokenMatcher. The parser.parse() call receives
            these as arguments instead of the raw text. Additionally, an upstream parser defect sometimes omits the
            "keyword" field from the feature node in markdown mode — the workaround ensures this key exists. This method
            encapsulates both differences.

        Delegates:
            - CucumberIOBaseParser: The upstream parser.
            - GherkinInMarkdownTokenMatcher: Markdown-aware token matcher.
            - TokenScanner: Input tokenizer.
            - AstBuilder: AST builder with id_generator.
            - path.read_text(): Reads the file.
            - gherkin_parser.parse(token_scanner, matcher): Produces the raw dict.
            - emit_parse_error: Emits parse error messages.
            - normalize_gherkin_document_payload: Normalizes defaults.
            - build_feature: Constructs GherkinDocument.

        Cohesion:
            The method follows the same pipeline as GherkinParser.parse() with two markdown-specific additions:
            TokenScanner+matcher setup, and the keyword workaround. All steps serve the parse → ParsedFeature goal.

        Separation:
            - GherkinParser.parse: Uses the default token matcher (implicit) instead of TokenScanner+GherkinInMarkdownTokenMatcher.

        Main consumers:
            - Scenario locators: Call parse() when the feature file mimetype indicates markdown.

        State and side effects:
            Reads the feature file from disk. Creates TokenScanner and parser instances. May emit hook messages on
            error. Mutates the raw dict (keyword workaround, normalization). Constructs GherkinDocument.

        Failure semantics:
            CompositeParserException is caught, reported via emit_parse_error, and re-raised as
            FeatureConcreteParseError(e.args[0], line, source_line, uri). The source_line comes from linecache.getline.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
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
        gherkin_document_raw_dict["feature"].setdefault("keyword", "")
        gherkin_document_raw_dict = self.normalize_gherkin_document_payload(gherkin_document_raw_dict)

        feature = self.build_feature(gherkin_document_raw_dict)
        return ParsedFeature(
            gherkin_document=feature,
            filename=str(path.as_posix()),
            raw_data=feature_file_data,
        )
