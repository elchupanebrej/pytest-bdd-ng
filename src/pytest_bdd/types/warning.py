"""Provide warning helpers."""

import pytest


class PytestBDDStepDefinitionWarning(pytest.PytestWarning):
    """
    Warning emitted when multiple step definitions match the same Gherkin step.

    This warning is triggered during scenario execution when the step
    matcher finds more than one registered step definition that matches
    a single Gherkin step. The first match is used for execution, and
    all alternative matches are logged in the warning message.

    This typically indicates ambiguous step patterns in the test suite
    — two or more ``@given``, ``@when``, ``@then``, or ``@step``
    decorators with overlapping patterns. Resolve by refining step
    patterns to eliminate ambiguity, or by using more specific parsers.

    This class inherits from ``pytest.PytestWarning`` and can be
    filtered or suppressed using pytest's ``filterwarnings``
    configuration.

    Args:
        message: Description of the ambiguous step definitions found.
            Typically includes the list of alternative step definitions
            that matched the same Gherkin step.

    Example:
        Suppressing the warning in pytest.ini::

            [pytest]
            filterwarnings =
                ignore:Alternative step definitions:pytest_bdd.PytestBDDStepDefinitionWarning

        Or via command line::

            pytest -W "ignore::pytest_bdd.PytestBDDStepDefinitionWarning"

    Returns:
        A ``PytestBDDStepDefinitionWarning`` instance containing the
        description of ambiguous step definitions.

    """

    __module__ = "pytest_bdd"
