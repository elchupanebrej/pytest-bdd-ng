"""
`pytest_bdd.assets.docker.remote_xdist` owns documented module behavior.

Responsibility:
    Serves as the Python namespace package marker for Docker-based remote xdist acceptance test
    assets. This package contains entrypoint scripts (controller_entrypoint.py, worker_entrypoint.py),
    report verification logic (verify_report.py), and a sub-package `project/` that holds the
    actual pytest test module and conftest executed inside Docker containers. The package itself
    contains no executable code — it exists solely to make the directory importable as a Python
    package so that entrypoint scripts can be invoked via `python -m` and test modules can be
    collected via `--pyargs`.

Reason for existence:
    The Docker remote xdist test infrastructure requires Python modules that are both importable
    as packages (for `--pyargs` collection by pytest inside containers) and executable as scripts
    (for `docker compose exec controller python entrypoint.py`). This __init__.py makes the
    directory a proper package, enabling relative imports between sibling modules and allowing
    the controller entrypoint to reference the verify_report module and the project sub-package
    via fully-qualified import paths. It is kept as a separate package from the main
    pytest_bdd_testing namespace to isolate Docker-specific test assets from the general testing
    utilities in the parent package.

Delegates:
    - (none): This is a pure namespace-package marker; it delegates no work to sub-entities.

Cohesion:
    The module contains only a docstring — no code, no imports, no state. Its purpose is purely
    structural: making a directory tree importable. Cohesion is not applicable in the traditional
    sense for a namespace marker.

Separation:
    - pytest_bdd_testing (parent package): The parent package owns general test utilities
      (docker.py, docker_cluster.py, pytest_results.py); this sub-package owns the Docker-
      specific scripts and test modules that run inside containers. The separation prevents
      the general testing utilities from depending on Docker container-specific entrypoint logic.
    - pytest_bdd_testing.resource.docker.remote_xdist.project: The project sub-package contains
      the actual pytest test files; this __init__.py only marks the parent namespace.

Main consumers:
    - controller_entrypoint.py: The controller script runs inside the Docker controller container
      and imports from this package's sibling modules (verify_report) and sub-packages (project).
    - DockerClusterManager.run_in_controller: References
      `pytest_bdd_testing.resource.docker.remote_xdist.controller_entrypoint` as the script path
      for `docker compose exec`.
    - pytest collection inside Docker containers: Uses `--pyargs
      pytest_bdd_testing.resource.docker.remote_xdist.project.remote_aggregation_case` to collect
      the test module via Python import path.

State and side effects:
    None — empty module with no code, no imports, no state, no side effects.

Invariants:
    - Must exist as a regular Python file (not a namespace package) to support the `--pyargs`
      collection mode used by pytest inside Docker containers.
    - Must not contain any code that could trigger side effects at import time, since it is
      imported as a dependency of the project sub-package.

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
