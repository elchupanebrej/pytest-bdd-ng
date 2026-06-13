"""
`pytest_bdd_testing` is the test infrastructure package for the pytest-bdd-ng library,
owning Docker integration support, results parsing, compatibility shims, message governance
assertions, end-to-end test bootstrapping, contract boundary fixtures, and the entire
`case/` test-suite sub-tree. It serves as the single import root for all testing
utilities, fixtures, and test cases that verify the production library.

Responsibility:
    This root package provides the home for all pytest-bdd test tooling: Docker daemon
    detection and auto-start (`docker.py`), multi-node Docker cluster orchestration
    (`docker_cluster.py`), structured pytest result parsing (`pytest_results.py`),
    platform compatibility probing (`compatibility/`), Cucumber Messages governance
    assertion helpers (`messages/`), end-to-end test support (`e2e/`), Cucumber JSON
    formatter rendering and registry utilities (`cucumber_formatters/`), contract
    boundary documentation fixtures (`contract/fixtures/`), reusable pytest fixtures
    (`fixtures/`), Jinja2-based code-generation templates (`resources/templates/`),
    and Docker Compose asset stubs (`assets/`). The actual test functions themselves
    are organized under `case/`, separated into unit, integration, contract,
    end-to-end, performance, external, and compatibility sub-trees. Every sub-package
    under pytest_bdd_testing that is not the `case/` tree serves as shared test
    infrastructure consumed by multiple test modules; the root __init__.py itself
    carries no runtime logic beyond acting as the Python package marker and
    documenting this overall role.

Reason for existence:
    This package exists as a deliberate architectural separation from both the
    production library (under `src/pytest_bdd/`) and the original flat `tests/`
    directory. It consolidates all testing infrastructure — Docker orchestration,
    result parsing, assertion helpers, fixture factories, formatter registries, and
    the full test-case tree — under one importable package (`pytest_bdd_testing`).
    This allows test modules within `case/` to import shared utilities through
    regular Python dotted imports rather than relying on `sys.path` manipulation or
    fragile relative imports. Keeping the cases sub-tree (`case/`) nested under
    this package also ensures that test discovery, collection, and CI execution can
    target the single package root. The package is kept as a dedicated top-level
    `src/` package rather than living inside the library itself because test
    infrastructure has different dependency requirements (pytest, docker, subprocess)
    and is never shipped to end users of the library.

Delegates:
    - docker: Detects and starts Docker daemon (native or WSL2 Alpine), polls
      until ready, and provides `require_docker_daemon()` as a pytest skip-or-return
      fixture helper.
    - docker_cluster: Orchestrates multi-node Docker Compose clusters for
      distributed test scenarios, managing lifecycle and cleanup.
    - pytest_results: Parses structured pytest output (JSON, XML) into typed
      result objects for test assertion consumption.
    - compatibility: Platform and Python-version compatibility detection shims
      used by skipif-style test markers.
    - messages: Cucumber Messages governance assertion primitives
      (`assert_unique`, `assert_contains_all`, `assert_non_empty_text`) consumed
      by contract tests in `case/contract/messages/`.
    - e2e: End-to-end test support modules (docker_support, cucumber_formatter_support,
      test_e2e) that scaffold full-stack acceptance test execution.
    - cucumber_formatters: Formatter registry and rendering utilities for Cucumber
      JSON/pretty/progress formatter validation tests.
    - case: The actual test function tree (unit, integration, contract, e2e, perf,
      compat, external) — delegated entirely as a separate subtree so infrastructure
      modules remain test-agnostic.

Cohesion:
    The root __init__.py is empty of executable code but is highly cohesive as an
    architectural anchor: every sibling module and sub-package under this root serves
    the single purpose of testing the pytest-bdd-ng library. Docker modules test
    containerized scenarios, results parsing consumes pytest output, formatter
    modules validate rendering, and case/ exercises the full library. The root
    init does not mix unrelated concerns (no deployment, no documentation generation,
    no benchmarking) — those live in the project's `scripts/` directory.

Separation:
    - pytest_bdd: The production library under `src/pytest_bdd/`. Kept separate
      because test infrastructure must never ship to library consumers and has
      different dependency and import-time constraints (subprocess, docker, pytest
      internals).
    - tests/: The original flat test directory (if present). Separated because this
      package uses an explicit `src/` layout with dotted imports, while traditional
      `tests/` layouts rely on conftest.py and sys.path conventions.
    - scripts/: Project-level scripts for benchmarking, linting, and CI. Separated
      because those are build/CI tooling, not runtime test infrastructure.

Main consumers:
    - pytest_bdd_testing.case.*: Every test module under case/ imports from sibling
      infrastructure packages. For example, e2e tests use `pytest_bdd_testing.docker`,
      contract tests use `pytest_bdd_testing.messages`, and formatter tests use
      `pytest_bdd_testing.cucumber_formatters`.
    - CI/CD pipelines: Execute `pytest src/pytest_bdd_testing/` to run the full
      test suite, relying on the package boundary for collection scope.

State and side effects:
    The root __init__.py has no state. Sibling modules (`docker.py`, `docker_cluster.py`)
    interact with the host system via subprocess (docker CLI, WSL), environment variables,
    and file I/O. The `case/` subtree may write temp directories and pytest cache files
    during execution, but no persistent state is mutated at import time.

Invariants:
    - Must remain the single import root for all test infrastructure; no test module
      outside this package may import test utilities from each other's private paths.
    - Sibling infrastructure modules (docker, messages, etc.) must not import from
      `case/` — the dependency arrow points downward from case to infrastructure.
    - Must not grow import-time side effects that would couple the entire test suite
      to Docker availability or platform-specific behavior.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=N/A
    #arch-eval:cohesion=N/A
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=N/A
    #arch-eval:entity_fullness=N/A
    #arch-eval:locational_stability=3
"""
# init: package-marker
