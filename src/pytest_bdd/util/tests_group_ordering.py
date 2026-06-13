"""
Provides the test group ordering system used with pytest-xdist to schedule BDD feature tests in
configurable groups, .

Responsibility:
    Provides the test group ordering system used with pytest-xdist to schedule BDD feature tests in
    configurable groups, enabling controlled parallel execution order across distributed workers
    via marker assignment, barrier synchronization, and configuration parsing from pytest ini
    options.

Reason for existence:
    Test group ordering logic is complex enough to warrant its own module rather than being inlined
    into conftest.py. Separating config parsing, marker application, barrier logic, and the public
    facade into the tests_group_ordering sub-package keeps each concern independently testable.

Delegates:
    - `pytest_bdd.util.tests_group_ordering.facade`: provides the public API re-exports for group ordering

Cohesion:
    The module and its sub-package collaborate on the single workflow of assigning tests to ordered
    execution groups.

Separation:
    - `pytest_bdd.util.cucumber_formatters`: manages formatter CLI options while tests_group_ordering manages
    distributed test scheduling.

Main consumers:
    - `tests/conftest.py`: thin pytest adapter that delegates group ordering to this module

State and side effects:
    Reads pytest ini configuration via config.getini() but keeps no persistent state beyond the
    current invocation.

Invariants:
    - Group names are generic configuration values, not hardcoded project constants.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

from pytest_bdd.util.tests_group_ordering.facade import *  # noqa: F403  -- intentional re-export or import for public API facade
