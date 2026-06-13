"""
Serves as a public API facade and re-export module that imports and re-exposes all step parser classes (cucumber_expr.

Responsibility:
    Serves as a public API facade and re-export module that imports and re-exposes all step parser classes
    (cucumber_expression, cucumber_regular_expression, parse, cfparse, re, string, heuristic) and their supporting
    infrastructure (StepParser, StepParserProtocol, RegistryMode, ParserBuildValueError, _EXPECTED_PARSER_BUILD_ERRORS,
    UNDEFINED_PARAMETER_TYPE_PATTERN) from the pytest_bdd.parsers subpackage through a single wildcard import from
    pytest_bdd.parsers.facade. This module is the canonical public entry point for end-user step parser imports such as
    `from pytest_bdd import parsers`.

Reason for existence:
    Provides a stable, short import path (pytest_bdd.parsers) for the parser API while keeping the actual
    implementations organized in subpackage modules (facade.py, base.py, cucumber_expression.py, cucumber_regex.py,
    parse_parser.py, re_parser.py, string_parser.py, heuristic.py). This follows the facade pattern used throughout
    pytest-bdd where top-level package modules re-export from deeper subpackages, insulating consumers from internal
    package reorganization. When a new parser type is added, only facade.py needs to add the re-export — consumers
    importing from pytest_bdd.parsers automatically gain access. This module contains zero implementation logic; all
    behavior delegates entirely to the subpackage.

Delegates:
    - pytest_bdd.parsers.facade: All public API symbols are imported via wildcard from this module, which in turn
    aggregates re-exports from base, cucumber_expression, cucumber_regex, heuristic, parse_parser, re_parser, and
    string_parser.

Cohesion:
    Perfect cohesion in the facade sense: the single responsibility is re-exporting the parsers public API. There is no
    code beyond the wildcard import, so there is no risk of internal cohesion conflict.

Separation:
    - pytest_bdd.parsers.facade: Kept separate because facade.py owns the explicit list of re-exports with justification
    comments for each import, while parsers.py is a thin wildcard wrapper — facade.py is the "source of truth" for what
    constitutes the public API, and parsers.py is the backward-compatible entry point.
    - pytest_bdd.steps: Kept separate because steps owns step definition registration and matching logic, while parsers
    owns the pluggable parser implementations that steps uses — they are in different architectural layers
    (step_definition vs parsing).

Main consumers:
    - End-user test code: `from pytest_bdd import parsers` then `parsers.re(r"...")`, `parsers.parse("...")`, etc.
    - pytest_bdd.steps.definition: Imports StepParser and StepParserProtocol from the parsers package for step
    definition registration and type checking.

State and side effects:
    None, keeps no persistent state. The wildcard import executes at module load time but has no side effects beyond
    populating the module namespace.

Invariants:
    - The wildcard import (`from pytest_bdd.parsers.facade import *`) must be the only executable line in the module
    beyond the docstring and noqa comment.
    - Every public parser class and supporting type must be accessible through pytest_bdd.parsers without additional
    imports.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=2
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=1
    #arch-eval:locational_stability=5
"""

from pytest_bdd.parsers.facade import *  # noqa: F403  -- intentional re-export or import for public API facade
