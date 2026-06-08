"""
Provide warning helpers.

Responsibility:
    Provide warning helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.types.warning` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - PytestBDDStepDefinitionWarning: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/__init__.py: imports or references `warning`
    - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `warning`
    - src/pytest_bdd/_gherkin_go/_build.py: imports or references `warning`
    - src/pytest_bdd/collector_batch.py: imports or references `warning`
    - src/pytest_bdd/model/message_transport.py: imports or references `warning`

State and side effects:
    mutates __module__; depends on _pytest.warning_types.PytestWarning.

Invariants:
    - `pytest_bdd.types.warning` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from _pytest.warning_types import PytestWarning


class PytestBDDStepDefinitionWarning(PytestWarning):
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

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:5
    #arch-eval:score=why_not_split:5
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:5
    #arch-eval:score=module_location:5

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

    Responsibility:
        Warning emitted when multiple step definitions match the same Gherkin step. It directly owns the observable
        contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.warning.PytestBDDStepDefinitionWarning` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/__init__.py: imports or references `PytestBDDStepDefinitionWarning`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `PytestBDDStepDefinitionWarning`
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
          `PytestBDDStepDefinitionWarning`
        - src/pytest_bdd/steps/manager.py: imports or references `PytestBDDStepDefinitionWarning`
        - src/pytest_bdd/steps/matcher.py: imports or references `PytestBDDStepDefinitionWarning`

    State and side effects:
        mutates __module__.

    Invariants:
        - `pytest_bdd.types.warning.PytestBDDStepDefinitionWarning` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4

    """

    __module__ = "pytest_bdd"
