"""
`project.remote_aggregation_case` owns documented module behavior.

Responsibility:
    A minimal pytest test module that serves as the test target for remote xdist message
    aggregation acceptance tests. Loads BDD scenarios from an aggregation.feature file via
    pytest_bdd.scenarios(), defines a single step (`@given("a passing step")` returning "ok"),
    and applies pytest markers (xdist, docker, slow) via pytestmark to ensure proper test
    grouping and xdist barrier behavior. This module is collected inside the Docker controller
    container by the controller entrypoint via `--pyargs`, and its execution produces the
    NDJSON message report that verify_report then validates.

Reason for existence:
    Remote xdist message aggregation testing requires a real pytest test module that exercises
    the full pytest-bdd pipeline (feature loading → step matching → scenario execution →
    message reporting) across distributed workers. This module provides that minimal test
    target with exactly enough complexity to verify multi-worker aggregation: a simple passing
    step that ensures scenarios complete successfully, and markers that ensure xdist distributes
    the tests across workers. It is kept as a separate module (not in the main test suite)
    because it must be collected inside the Docker container context, not on the host. The
    module is intentionally minimal — a single step definition and a scenarios() call — to
    keep the verification surface small and the test execution fast.

Delegates:
    - pytest_bdd.scenarios: Loads BDD scenarios from the aggregation.feature file in the same
      directory, generating test functions for each scenario.
    - pytest_bdd.given: Registers the "a passing step" step definition.
    - pytest.mark: The pytestmark list applies xdist, docker, and slow markers to all tests
      in this module, ensuring they are properly grouped for xdist distribution and skipped
      when Docker is unavailable.

Cohesion:
    All module contents serve the single purpose of being a valid, executable pytest-bdd test
    target for remote xdist testing. The step definition, scenario loader, and markers form a
    complete, self-contained test module. No unrelated imports or logic.

Separation:
    - conftest.py (sibling): Provides collection ignore rules to prevent duplicate feature file
      collection; this module focuses on test logic.
    - The host test suite: This module is explicitly not part of the host test suite; it is
      only collected inside Docker containers via --pyargs.
    - controller_entrypoint._build_pytest_cmd: References this module by its fully-qualified
      Python path for --pyargs collection.

Main consumers:
    - controller_entrypoint._build_pytest_cmd: Includes this module's fully-qualified path
      (`pytest_bdd_testing.assets.docker.remote_xdist.project.remote_aggregation_case`) in
      the pytest command for --pyargs collection.
    - pytest inside Docker controller container: Collects and executes this module's tests,
      producing the NDJSON report used by verify_report.

State and side effects:
    Module-level: pytestmark list applies xdist/docker/slow markers. scenarios() call at
    module level generates test functions (side effect at import time). The _pass step
    definition is registered in pytest-bdd's step registry (module-level side effect).
    No filesystem writes (scenarios reads aggregation.feature), no environment access, no
    subprocess calls, no pytest stash writes.

Invariants:
    - The aggregation.feature file must exist in the same directory as this module.
    - pytestmark includes pytest.mark.xdist, pytest.mark.docker, and pytest.mark.slow to
      ensure these tests are properly grouped and conditionally skipped.
    - The _pass step must always return a truthy value ("ok") to ensure scenarios complete
      successfully and produce passing message reports.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd import given, scenarios

pytestmark = [pytest.mark.xdist, pytest.mark.docker, pytest.mark.slow]

test_scenarios = scenarios(Path(__file__).with_name("aggregation.feature"))


@given("a passing step")
def _pass() -> str:
    """
    `remote_aggregation_case._pass` owns documented function behavior.

    Responsibility:
        A minimal pytest-bdd step definition registered via @given("a passing step") that
        always returns the string "ok". This step exists solely to satisfy the "Given a passing
        step" clause in the aggregation.feature scenarios, ensuring that all scenarios in the
        remote xdist acceptance test complete successfully (pass) rather than fail or remain
        undefined. The return value is irrelevant to the test outcome — pytest-bdd considers a
        step passed if it returns without raising an exception.

    Reason for existence:
        The aggregation.feature file contains scenarios like "Given a passing step" that need a
        corresponding step definition to execute. This function provides the absolute minimum
        implementation: a no-op that always succeeds. It is kept as a standalone function
        (rather than using a generic "pass" step from a shared fixture) because this test
        module is self-contained and collected via --pyargs inside a Docker container, where
        shared conftest fixtures from the host test suite are not available. The leading
        underscore naming (_pass) follows the pytest-bdd convention of prefixing step
        definition functions with _ when they are not meant to be called directly.

    Delegates:
        - pytest_bdd.given: The decorator that registers this function as the step definition
          for "a passing step" in pytest-bdd's step registry.

    Cohesion:
        The function does exactly one thing: return "ok". Its entire body is a single return
        statement. It serves the single purpose of satisfying a specific Gherkin step.

    Separation:
        - pytest_bdd.scenarios (module-level call): Loads the feature file scenarios that
          reference this step; the separation between step definitions and scenario loading
          follows standard pytest-bdd conventions.

    Main consumers:
        - pytest-bdd's step execution runtime: Calls this function when executing the "Given a
          passing step" clause in aggregation.feature scenarios during test execution inside
          the Docker controller container.

    State and side effects:
        None — pure function. Returns a constant string. No filesystem, environment, subprocess,
        or pytest stash access. The step registration side effect happens at decoration time
        (module import), not at call time.

    Architecture score:
        #arch-eval:reason_for_existence=2
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=1
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=5
    """
    return "ok"
