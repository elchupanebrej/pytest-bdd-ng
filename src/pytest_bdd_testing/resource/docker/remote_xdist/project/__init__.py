"""
`pytest_bdd.assets.docker.remote_xdist.project` owns documented module behavior.

Responsibility:
    Serves as the Python package marker for the test project that runs inside Docker containers
    during remote xdist acceptance tests. This package contains a pytest conftest (with
    collection ignore rules) and the remote_aggregation_case test module that defines BDD
    step definitions and scenario loading for the aggregation.feature file. The __init__.py
    itself is empty — it exists solely to make the directory importable so that the controller
    entrypoint can collect tests via `--pyargs pytest_bdd_testing.assets.docker.remote_xdist.
    project.remote_aggregation_case`.

Reason for existence:
    The remote xdist controller runs pytest with `--pyargs` pointing to a fully-qualified
    Python module path. This requires the target module to live in a proper Python package
    (with __init__.py). This sub-package exists as a self-contained test project that can be
    collected independently of the host test suite. It is isolated from the parent
    pytest_bdd_testing package to prevent its tests from being accidentally collected by the
    host pytest session — the conftest.py's `collect_ignore_glob = ["*.feature"]` ensures
    that feature files in this package are not picked up during normal test discovery.

Delegates:
    - (none): This is a pure namespace-package marker with no executable code.

Cohesion:
    Contains only a docstring — no code, no imports, no state. Its purpose is purely
    structural: enabling Python package semantics for the directory. Cohesion is not
    meaningfully applicable to an empty namespace marker.

Separation:
    - pytest_bdd_testing.assets.docker.remote_xdist (parent package): Contains entrypoint
      scripts; this sub-package contains the actual test code executed inside containers.
    - pytest_bdd_testing (root testing package): Contains general testing utilities; this
      sub-package is a Docker-container-specific test project.

Main consumers:
    - controller_entrypoint._build_pytest_cmd: References this package via
      `--pyargs pytest_bdd_testing.assets.docker.remote_xdist.project.remote_aggregation_case`
      to collect and execute the remote aggregation test module inside the controller container.
    - pytest collection inside Docker containers: The package is imported when pytest runs
      with --pyargs in the container.

State and side effects:
    None — empty module with no code, no imports, no state, no side effects.

Invariants:
    - Must exist as a regular file (not a namespace package) to support --pyargs collection.
    - Must not contain any executable code that could interfere with test collection.
    - Its presence enables conftest.py to be discovered as a pytest plugin for this package.

Architecture score:
    #arch-eval:reason_for_existence=2
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=N/A
    #arch-eval:cohesion=N/A
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=N/A
    #arch-eval:entity_fullness=N/A
    #arch-eval:locational_stability=4
"""
