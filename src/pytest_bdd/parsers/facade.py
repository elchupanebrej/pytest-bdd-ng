"""
Serves as the public API aggregation module for the pytest_bdd.parsers subpackage, explicitly re-exporting all public.

Responsibility:
    Serves as the public API aggregation module for the pytest_bdd.parsers subpackage, explicitly re-exporting all
    public parser types and helper functions from the internal parser modules: StepParser, StepParserProtocol,
    RegistryMode, ParserBuildValueError, _EXPECTED_PARSER_BUILD_ERRORS from base; cucumber_expression,
    _CucumberExpression, UNDEFINED_PARAMETER_TYPE_PATTERN from cucumber_expression; cucumber_regular_expression from
    cucumber_regex; heuristic, _build_parser_result from heuristic; parse, cfparse from parse_parser; re from re_parser;
    and string from string_parser. This module defines the canonical public API surface for step definition parsers that
    users access via `from pytest_bdd import parsers`.

Reason for existence:
    The parsers subpackage contains 8 module files (base, cucumber_expression, cucumber_regex, heuristic, parse_parser,
    re_parser, string_parser, plus the factory modules), each with internal implementation details that consumers should
    not need to navigate. This facade module aggregates all public symbols into a single import target, insulating
    consumers from internal module reorganization. Each import is annotated with a justification comment explaining the
    F401 suppression, making the public API intent explicit and reviewable. Without this facade, `from pytest_bdd import
    parsers` would fail to find the public parser classes because they're defined in subpackage modules.

Delegates:
    - pytest_bdd.parsers.base: Provides StepParser, StepParserProtocol, RegistryMode, ParserBuildValueError,
    _EXPECTED_PARSER_BUILD_ERRORS — the abstract infrastructure for all step parsers.
    - pytest_bdd.parsers.cucumber_expression: Provides cucumber_expression, _CucumberExpression,
    UNDEFINED_PARAMETER_TYPE_PATTERN — Cucumber expression and regex-based step parsers.
    - pytest_bdd.parsers.cucumber_regex: Provides cucumber_regular_expression — the Cucumber regular expression parser.
    - pytest_bdd.parsers.heuristic: Provides heuristic parser (auto-detection) and _build_parser_result.
    - pytest_bdd.parsers.parse_parser: Provides parse and cfparse — python-parse-based step parsers.
    - pytest_bdd.parsers.re_parser: Provides re — stdlib regex-based step parser.
    - pytest_bdd.parsers.string_parser: Provides string — exact-string-match step parser.

Cohesion:
    Every import in this module serves the purpose of exposing the parsers subpackage's public API. Imports are
    organized by source module and annotated with justification comments. No implementation logic exists.

Separation:
    - pytest_bdd.parsers (top-level module): Kept separate because that module wildcard-imports from this facade to
    provide the backward-compatible import path, while this facade enumerates the explicit API — implicit vs explicit
    API definition.
    - pytest_bdd.steps: Kept separate because steps owns step definition registration, while parsers owns step pattern
    matching — registration vs matching, different architectural layers.

Main consumers:
    - pytest_bdd.parsers (top-level): Wildcard-imports from this facade via `from pytest_bdd.parsers.facade import *`.
    - pytest_bdd.steps.manager: Imports StepParser, StepParserProtocol, and crawler_default for step definition
    registration and matching.
    - End-user test code via pytest_bdd.parsers: Users access parser classes like parsers.re(), parsers.parse(),
    parsers.cfparse() through the aggregated namespace.

State and side effects:
    None, keeps no persistent state. All imports are read-only namespace operations.

Invariants:
    - Every public parser class and its supporting infrastructure must be re-exported through this facade — no public
    parser type should require importing from a subpackage module directly.
    - Import justification comments must explain why each F401 suppression is acceptable.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from pytest_bdd.parsers.base import (  # noqa: F401  -- intentional re-export or import for public API facade
    _EXPECTED_PARSER_BUILD_ERRORS,
    ParserBuildValueError,
    RegistryMode,
    StepParser,
    StepParserProtocol,
)
from pytest_bdd.parsers.cucumber_expression import (  # noqa: F401  -- intentional re-export or import for public API facade
    UNDEFINED_PARAMETER_TYPE_PATTERN,
    _CucumberExpression,
    cucumber_expression,
)
from pytest_bdd.parsers.cucumber_regex import (  # noqa: F401  -- intentional re-export or import for public API facade
    cucumber_regular_expression,
)
from pytest_bdd.parsers.heuristic import (  # noqa: F401  -- intentional re-export; facade exposes full parsers public API
    _build_parser_result,
    heuristic,
)
from pytest_bdd.parsers.parse_parser import (  # noqa: F401  -- intentional re-export; facade exposes full parsers public API
    cfparse,
    parse,
)
from pytest_bdd.parsers.re_parser import (
    re,  # noqa: F401  -- intentional re-export; facade exposes full parsers public API
)
from pytest_bdd.parsers.string_parser import (
    string,  # noqa: F401  -- intentional re-export; facade exposes full parsers public API
)
