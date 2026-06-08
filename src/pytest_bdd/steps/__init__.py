# init: public-api  # init: no-check
"""
Step definition management — re-exports from sub-modules.

Responsibility:
    Step definition management — re-exports from sub-modules. It directly owns the observable contract, local decisions,
    and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.steps` because it keeps the nearest code, data shape, call
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
    - src/pytest_bdd/__init__.py: imports or references `steps`
    - src/pytest_bdd/collector.py: imports or references `steps`
    - src/pytest_bdd/model/scenario_report.py: imports or references `steps`
    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `steps`
    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `steps`

State and side effects:
    depends on __future__.annotations, cucumber_messages.PickleStep, pytest_bdd.steps.decorators.given,
    pytest_bdd.steps.decorators.not_implemented, pytest_bdd.steps.decorators.step.

Invariants:
    - `pytest_bdd.steps` keeps its documented import path, ownership boundary, and observable behavior stable for
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

from __future__ import annotations

from cucumber_messages import (
    PickleStep as Step,  # upstream type stubs missing this attribute
)

from pytest_bdd.steps.decorators import given as given
from pytest_bdd.steps.decorators import not_implemented as not_implemented
from pytest_bdd.steps.decorators import step as step
from pytest_bdd.steps.decorators import then as then
from pytest_bdd.steps.decorators import tolerant as tolerant
from pytest_bdd.steps.decorators import when as when
from pytest_bdd.steps.definition import (
    ConverterT as ConverterT,
)
from pytest_bdd.steps.definition import (
    Definition as Definition,
)
from pytest_bdd.steps.definition import (
    ParamsFixturesMapping as ParamsFixturesMapping,
)
from pytest_bdd.steps.definition import (
    StepDecorator as StepDecorator,
)
from pytest_bdd.steps.definition import (
    StepFunc as StepFunc,
)
from pytest_bdd.steps.definition import (
    _resolve_callable_source_location as _resolve_callable_source_location,
)
from pytest_bdd.steps.manager import StepDefinitionManager as StepDefinitionManager
from pytest_bdd.steps.matcher import Matcher as Matcher
from pytest_bdd.steps.registry import Registry as Registry
from pytest_bdd.steps.registry import StepProtocol as StepProtocol
from pytest_bdd.steps.registry import StepRegistryProtocol as StepRegistryProtocol
