"""pytest-bdd-ng — BDD testing plugin for pytest.

pytest-bdd-ng brings Behavior-Driven Development to Python testing.
Users write Gherkin feature files (``.feature`` or ``.feature.md``),
define step implementations with ``@given``/``@when``/``@then``
decorators, and get full Cucumber-compatible reporting.

Public API exports (8 items):

- ``scenario``: Load and bind a single Gherkin scenario to a test function.
- ``scenarios``: Bulk-load scenarios from feature files and bind to test functions.
- ``given``: Define a Given step (precondition). Lazy-loaded from ``steps``.
- ``when``: Define a When step (action). Lazy-loaded from ``steps``.
- ``then``: Define a Then step (assertion). Lazy-loaded from ``steps``.
- ``step``: Define a liberal step matching any keyword. Lazy-loaded from ``steps``.
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
    .. autoclass:: pytest_bdd.PytestBDDStepDefinitionWarning

Note: ``given``, ``when``, ``then``, ``step``, and
``PytestBDDStepDefinitionWarning`` are lazy-loaded via ``__getattr__``
(PEP 562) to avoid import overhead. Their docstrings are defined in
the source modules (``steps.py``, ``types/warning.py``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.scenario import FeaturePathType, scenario, scenarios

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.steps import given, step, then, when
    from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning

__all__ = [
    "FeaturePathType",
    "PytestBDDStepDefinitionWarning",
    "given",
    "scenario",
    "scenarios",
    "step",
    "then",
    "when",
]


def __getattr__(name: str) -> object:
    if name in {"given", "step", "then", "when"}:
        from pytest_bdd.steps import given, step, then, when  # noqa: PLC0415 -- PEP 562 lazy loading

        return {
            "given": given,
            "step": step,
            "then": then,
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
