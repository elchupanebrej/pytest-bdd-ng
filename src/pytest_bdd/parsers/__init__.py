# init: public-api  # init: no-check
"""
Step parser implementations for pytest-bdd-ng.

Responsibility:
    Step parser implementations for pytest-bdd-ng. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - None, leaf-level implementation boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
      `parsers`
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `parsers`
    - src/pytest_bdd/steps/definition.py: imports or references `parsers`
    - src/pytest_bdd/steps/manager.py: imports or references `parsers`

State and side effects:
    depends on pytest_bdd.parsers.base._EXPECTED_PARSER_BUILD_ERRORS, pytest_bdd.parsers.base.ParserBuildValueError,
    pytest_bdd.parsers.base.RegistryMode, pytest_bdd.parsers.base.StepParserProtocol,
    pytest_bdd.parsers.cucumber_expression.UNDEFINED_PARAMETER_TYPE_PATTERN.

Invariants:
    - `pytest_bdd.parsers` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from pytest_bdd.parsers.base import (
    _EXPECTED_PARSER_BUILD_ERRORS as _EXPECTED_PARSER_BUILD_ERRORS,
)
from pytest_bdd.parsers.base import (
    ParserBuildValueError as ParserBuildValueError,
)
from pytest_bdd.parsers.base import (
    RegistryMode as RegistryMode,
)
from pytest_bdd.parsers.base import (
    StepParserProtocol as StepParserProtocol,
)
from pytest_bdd.parsers.cucumber_expression import (
    UNDEFINED_PARAMETER_TYPE_PATTERN as UNDEFINED_PARAMETER_TYPE_PATTERN,
)
from pytest_bdd.parsers.cucumber_expression import (
    _CucumberExpression as _CucumberExpression,
)
from pytest_bdd.parsers.facade import (
    StepParser as StepParser,
)
from pytest_bdd.parsers.facade import (
    cfparse as cfparse,
)
from pytest_bdd.parsers.facade import (
    cucumber_expression as cucumber_expression,
)
from pytest_bdd.parsers.facade import (
    cucumber_regular_expression as cucumber_regular_expression,
)
from pytest_bdd.parsers.facade import (
    heuristic as heuristic,
)
from pytest_bdd.parsers.facade import (
    parse as parse,
)
from pytest_bdd.parsers.facade import (
    re as re,
)
from pytest_bdd.parsers.facade import (
    string as string,
)
from pytest_bdd.parsers.heuristic import _build_parser_result as _build_parser_result
