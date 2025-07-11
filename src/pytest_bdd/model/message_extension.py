from dataclasses import dataclass
from enum import Enum

from cucumber_messages import *  # noqa: F403 This module patches the cucumber_messages module to extend it with pytest_bdd specific types
from cucumber_messages import StepDefinitionPattern as _BaseStepDefinitionPattern
from cucumber_messages import StepDefinitionPatternType as _BaseStepDefinitionPatternType

StepDefinitionPatternType = Enum(
    "StepDefinitionPatternType",
    dict(
        **{name: member.value for name, member in _BaseStepDefinitionPatternType.__members__.items()},
        pytest_bdd_heuristic_expression="PYTEST_BDD_HEURISTIC_EXPRESSION",
        pytest_bdd_string_expression="PYTEST_BDD_STRING_EXPRESSION",
        pytest_bdd_regular_expression="PYTEST_BDD_REGULAR_EXPRESSION",
        pytest_bdd_parse_expression="PYTEST_BDD_PARSE_EXPRESSION",
        pytest_bdd_cfparse_expression="PYTEST_BDD_CFPARSE_EXPRESSION",
        pytest_bdd_other_expression="PYTEST_BDD_OTHER_EXPRESSION",
    ),
)


@dataclass
class StepDefinitionPattern(_BaseStepDefinitionPattern):
    type: StepDefinitionPatternType
