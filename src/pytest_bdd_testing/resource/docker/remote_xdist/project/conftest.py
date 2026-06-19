"""
`pytest_bdd.assets.docker.remote_xdist.project.conftest` owns documented module behavior.

Responsibility:
    A pytest conftest for the Docker-container test project that sets `collect_ignore_glob =
    ["*.feature"]` to prevent pytest from collecting feature files during test discovery. This
    conftest exists because the remote_aggregation_case module uses pytest_bdd.scenarios() to
    load scenarios from aggregation.feature, and without this ignore rule, pytest would attempt
    to collect the .feature file directly in addition to the Python test module, causing
    duplicate test collection. The module also serves as documentation: it clarifies that this
    package is a test fixture project executed inside Docker containers, not part of the
    top-level pytest session.

Reason for existence:
    pytest-bdd's feature file collection can cause conflicts when a .feature file is both in
    the same directory as a test module that uses scenarios() and within pytest's default
    collection path. Without this conftest, the top-level test session (if it accidentally
    collects this directory) would see duplicate tests — once from the .feature file and once
    from the scenarios() call. The conftest is the standard pytest mechanism for per-directory
    configuration, and placing it here ensures the ignore rule applies only to this Docker test
    project, not to the entire repository.

Delegates:
    - (none): The module sets a single module-level variable (collect_ignore_glob) — no
      function calls, imports, or sub-entity delegation.

Cohesion:
    The module has a single responsibility: set collect_ignore_glob. The comment explaining
    the package's purpose supports this by documenting why the ignore rule exists. No unrelated
    configuration.

Separation:
    - remote_aggregation_case.py: The test module that uses scenarios() to load feature files;
      this conftest ensures those feature files are not double-collected.
    - The host test suite's conftest files: This conftest is scoped to the Docker test project
      directory and does not affect the host test suite's collection behavior.

Main consumers:
    - pytest collection inside Docker containers: When the controller runs `pytest --pyargs
      pytest_bdd_testing.resource.docker.remote_xdist.project.remote_aggregation_case`, this
      conftest is discovered as part of the package and applies the ignore rule.
    - pytest collection on the host (defensive): If this directory were to be collected by
      the host test session, this conftest would prevent duplicate feature file collection.

State and side effects:
    Sets collect_ignore_glob = ["*.feature"] at module level. This is read by pytest's
    collection mechanism at import time. No other state, no filesystem writes, no subprocess
    calls, no environment access, no pytest stash interaction.

Invariants:
    - collect_ignore_glob must include "*.feature" to prevent feature files in this directory
      from being collected as test items.
    - This conftest must remain in the `project/` directory (not the parent `remote_xdist/`
      directory) to scope the ignore rule only to this test project's feature files.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=1
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=1
    #arch-eval:locational_stability=5
"""

# This package is a test fixture project executed inside Docker containers /
# subprocesses by test_xdist_remote_message_aggregation.py.
# It must NOT be collected by the top-level pytest session.

collect_ignore_glob = ["*.feature"]
