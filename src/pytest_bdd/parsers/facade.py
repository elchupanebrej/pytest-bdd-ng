"""
Backward-compatible re-exports of all public step parsers.

Responsibility:
    Backward-compatible re-exports of all public step parsers. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers.facade` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - None, leaf-level implementation boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parsers.py: imports or references `facade`
    - src/pytest_bdd/parsers/__init__.py: imports or references `facade`

State and side effects:
    depends on __future__.annotations, pytest_bdd.parsers.base._EXPECTED_PARSER_BUILD_ERRORS,
    pytest_bdd.parsers.base.ParserBuildValueError, pytest_bdd.parsers.base.RegistryMode,
    pytest_bdd.parsers.base.StepParser.

Invariants:
    - `pytest_bdd.parsers.facade` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from pytest_bdd.parsers.base import (  # noqa: F401
    _EXPECTED_PARSER_BUILD_ERRORS,
    ParserBuildValueError,
    RegistryMode,
    StepParser,
    StepParserProtocol,
)
from pytest_bdd.parsers.cucumber_expression import (  # noqa: F401
    UNDEFINED_PARAMETER_TYPE_PATTERN,
    _CucumberExpression,
    cucumber_expression,
)
from pytest_bdd.parsers.cucumber_regex import (  # noqa: F401
    cucumber_regular_expression,
)
from pytest_bdd.parsers.heuristic import _build_parser_result, heuristic  # noqa: F401
from pytest_bdd.parsers.parse_parser import cfparse, parse  # noqa: F401
from pytest_bdd.parsers.re_parser import re  # noqa: F401
from pytest_bdd.parsers.string_parser import string  # noqa: F401
