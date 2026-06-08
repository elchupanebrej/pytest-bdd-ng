# init: public-api  # init: no-check
"""
pytest-bdd-ng — BDD testing plugin for pytest.

pytest-bdd-ng brings Behavior-Driven Development to Python testing.
Users write Gherkin feature files (``.feature`` or ``.feature.md``),
define step implementations with ``@given``/``@when``/``@then``
decorators, and get full Cucumber-compatible reporting.

Public API exports (9 items):

- ``scenario``: Load and bind a single Gherkin scenario to a test function.
- ``scenarios``: Bulk-load scenarios from feature files and bind to test functions.
- ``given``: Define a Given step (precondition). Lazy-loaded from ``steps``.
- ``when``: Define a When step (action). Lazy-loaded from ``steps``.
- ``then``: Define a Then step (assertion). Lazy-loaded from ``steps``.
- ``step``: Define a liberal step matching any keyword. Lazy-loaded from ``steps``.
- ``not_implemented``: Mark intentional WIP step definitions. Lazy-loaded from ``steps``.
- ``tolerant``: Mark step definitions with tolerant failure policy. Lazy-loaded from ``steps``.
- ``FeaturePathType``: Enum controlling feature path resolution (PATH/URL/UNDEFINED).
- ``PytestBDDStepDefinitionWarning``: Warning for ambiguous step definitions.

For Sphinx autodoc::

    .. autofunction:: pytest_bdd.scenario
    .. autofunction:: pytest_bdd.scenarios
    .. autoclass:: pytest_bdd.FeaturePathType
    .. autofunction:: pytest_bdd.steps.given
    .. autofunction:: pytest_bdd.steps.when
    .. autofunction:: pytest_bdd.steps.then
    .. autofunction:: pytest_bdd.steps.step
    .. autofunction:: pytest_bdd.steps.not_implemented
    .. autofunction:: pytest_bdd.steps.tolerant
    .. autoclass:: pytest_bdd.PytestBDDStepDefinitionWarning

Note: ``given``, ``when``, ``then``, ``step``, ``not_implemented``, ``tolerant``, and
``PytestBDDStepDefinitionWarning`` are lazy-loaded via ``__getattr__``
(PEP 562) to avoid import overhead. Their docstrings are defined in
the source modules (``steps.py``, ``types/warning.py``).

Responsibility:
    pytest-bdd-ng — BDD testing plugin for pytest. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - __getattr__: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `pytest_bdd`

State and side effects:
    mutates msg; depends on __future__.annotations, typing.TYPE_CHECKING, pytest_bdd.scenario.FeaturePathType,
    pytest_bdd.scenario.scenario, pytest_bdd.scenario.scenarios.

Invariants:
    - `pytest_bdd` keeps its documented import path, ownership boundary, and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises AttributeError; callers must treat these as boundary failures.

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

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.scenario import FeaturePathType as FeaturePathType
from pytest_bdd.scenario import scenario as scenario
from pytest_bdd.scenario import scenarios as scenarios

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.steps import given as given
    from pytest_bdd.steps import not_implemented as not_implemented
    from pytest_bdd.steps import step as step
    from pytest_bdd.steps import then as then
    from pytest_bdd.steps import tolerant as tolerant
    from pytest_bdd.steps import when as when
    from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning as PytestBDDStepDefinitionWarning


def __getattr__(name: str) -> object:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.__getattr__` owns documented function behavior. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.__getattr__` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - get_distribution_version: collaborator call used by this boundary
        - AttributeError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `__getattr__`

    State and side effects:
        mutates msg; depends on pytest_bdd.steps.given, pytest_bdd.steps.not_implemented, pytest_bdd.steps.step,
        pytest_bdd.steps.then, pytest_bdd.steps.tolerant.

    Invariants:
        - `pytest_bdd.__getattr__` keeps its documented import path, ownership boundary, and observable behavior stable
          for callers.

    Failure semantics:
        Raises or re-raises AttributeError; callers must treat these as boundary failures.

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
    if name in {"given", "not_implemented", "step", "then", "tolerant", "when"}:
        from pytest_bdd.steps import (  # noqa: PLC0415 -- PEP 562 lazy loading
            given,
            not_implemented,
            step,
            then,
            tolerant,
            when,
        )

        return {
            "given": given,
            "not_implemented": not_implemented,
            "step": step,
            "then": then,
            "tolerant": tolerant,
            "when": when,
        }[name]
    if name == "PytestBDDStepDefinitionWarning":
        from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning  # noqa: PLC0415 -- PEP 562 lazy loading

        return PytestBDDStepDefinitionWarning
    if name == "__version__":
        from pytest_bdd.util.packaging import get_distribution_version  # noqa: PLC0415 -- PEP 562 lazy loading

        return str(get_distribution_version("pytest-bdd-ng"))
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
