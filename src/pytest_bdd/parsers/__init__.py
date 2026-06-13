"""
Public API facade for the Gherkin step-parsing subsystem.

Responsibility:
    Public API facade for the Gherkin step-parsing subsystem. Re-exports the StepParserProtocol, StepParser ABC,
    RegistryMode enum, ParserBuildValueError, all parser builder functions (parse, re, cfparse, cucumber_expression,
    cucumber_regular_expression, string, heuristic), and internal parser implementations (_CucumberExpression,
    UNDEFINED_PARAMETER_TYPE_PATTERN, _build_parser_result) so that consumers import from a single stable entry point
    rather than depending on internal parser module layout.

Reason for existence:
    This package is the information expert for step pattern parsing because it owns the abstract protocol every step
    parser must satisfy, the registry mechanism that allows parser backends to be registered and discovered lazily, and
    the facade that presents a unified public API. It is kept as a separate package (rather than being merged into steps
    or the top-level parser module) because the parser plugin system is an independently swappable concern that the
    step_definition layer depends on but should not own—parsers define how Gherkin step text is matched and
    parameterized, while steps define how matched parameters are dispatched to Python functions. The lazy module loading
    in base._load_parser_modules and the registry dispatch in base.StepParser.build ensure new parser backends can be
    added without modifying any consumer code.

Delegates:
    - base.py: Defines StepParserProtocol, StepParser ABC, RegistryMode, ParserBuildValueError, and the parser
    registration/dispatch infrastructure (register_parser, register_fallback_parser, _load_parser_modules,
    StepParser.build).
    - facade.py: Provides thin factory functions (parse, re, cfparse, cucumber_expression, cucumber_regular_expression,
    string, heuristic) that instantiate the appropriate parser classes, serving as the user-facing API.
    - cucumber_expression.py: Implements _CucumberExpression parser using the cucumber-expressions library with
    ParameterTypeRegistry integration.
    - cucumber_regex.py: Implements regular-expression-based Cucumber step matching.
    - re_parser.py: Implements Python re-based step parser.
    - parse_parser.py: Implements parse-format and cfparse parsers.
    - string_parser.py: Implements exact-string-match parser.
    - heuristic.py: Implements composite heuristic parser that tries multiple backends, also registered as the fallback
    parser.

Cohesion:
    All modules in this package share the same core concern: translating a Gherkin step text pattern (expressed as a
    string, regex, cucumber expression, or parse format) into a StepParserProtocol-compliant object that can test
    whether a given step name matches and extract named parameters. The __init__.py serves purely as a re-export facade;
    every module within the package implements exactly one parser backend or the shared base contracts. There is no
    unrelated utility logic mixed in.

Separation:
    - pytest_bdd.steps: The step_definition layer depends on this package for StepParser and parser factories, but
    parsers do not depend on steps—they only consume model types (StepDefinitionPatternType) and foundation types. This
    prevents parsers from being coupled to how step definitions are registered, matched, or executed.
    - pytest_bdd.parser: The higher-level Gherkin parser (parser.py) handles Gherkin document parsing (AST production
    from .feature files), while this package handles step-text pattern matching at the individual step level. They are
    separate concerns at different granularities.

Main consumers:
    - pytest_bdd.steps.definition: Definition stores a StepParser instance and delegates to parser.parse_arguments and
    parser.is_matching for step execution.
    - pytest_bdd.steps.manager: StepDefinitionManager.decorator_builder calls StepParser.build(step_parserlike) to
    construct a parser from the user-provided pattern.
    - pytest_bdd.steps.matcher: Matcher uses parser.is_matching to test each Definition against a PickleStep during
    runtime step dispatch.
    - pytest_bdd.plugin.scenario_test_collector: Uses parser types during test generation and step matching at
    collection time.

State and side effects:
    None, keeps no persistent state. The __init__.py is purely a re-export module. The underlying base module maintains
    module-level mutable state (_PARSER_REGISTRY, _FALLBACK_PARSER_BUILDER, _PARSER_MODULES_LOADED) but those are
    managed by base.py, not by this facade.

Invariants:
    - All parser classes exported via this module must satisfy both StepParserProtocol (runtime_checkable) and the
    StepParser ABC.
    - The facade must remain stable as the public API; internal parser module names (re_parser, parse_parser, etc.) are
    not part of the public contract.
    - Parser registry order in _PARSER_MODULES determines the dispatch priority in StepParser.build.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

__all__: list[str] = [
    "UNDEFINED_PARAMETER_TYPE_PATTERN",
    "_EXPECTED_PARSER_BUILD_ERRORS",
    "ParserBuildValueError",
    "RegistryMode",
    "StepParser",
    "StepParserProtocol",
    "_CucumberExpression",
    "_build_parser_result",
    "cfparse",
    "cucumber_expression",
    "cucumber_regular_expression",
    "heuristic",
    "parse",
    "re",
    "string",
]

from pytest_bdd.parsers.base import (
    _EXPECTED_PARSER_BUILD_ERRORS,
    ParserBuildValueError,
    RegistryMode,
    StepParserProtocol,
)
from pytest_bdd.parsers.cucumber_expression import (
    UNDEFINED_PARAMETER_TYPE_PATTERN,
    _CucumberExpression,
)
from pytest_bdd.parsers.facade import (
    StepParser,
    cfparse,
    cucumber_expression,
    cucumber_regular_expression,
    heuristic,
    parse,
    re,
    string,
)
from pytest_bdd.parsers.heuristic import _build_parser_result
