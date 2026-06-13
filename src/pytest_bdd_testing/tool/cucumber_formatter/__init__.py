# init: allow  # init: no-check
"""
`pytest_bdd.cucumber_formatters` — Public re-export facade for cucumber formatter testing infrastructure, aggregating
assertion functions, subprocess runner, and fake-runtime installation from sibling submodules.

Responsibility:
    This package serves as the public re-export facade for cucumber formatter testing infrastructure. It gathers the
    core test utilities (fake node runtime installation, formatter output assertions, pytest subprocess execution,
    formatter hook registry installation, and formatter telemetry reading) from the two sibling modules `registry` and
    `rendering` and exposes them as a single flat import namespace for test modules. All 15 exported symbols are re-
    exported without any logic added, so the package boundary is purely organizational — downstream consumers never need
    to know which submodule owns which function. This package holds no implementation logic of its own; its sole job is
    to provide a stable, unified import surface for the test-fixture layer that supports cucumber formatter integration,
    e2e, contract, and compatibility test suites.

Reason for existence:
    This __init__.py exists to collapse the two-submodule split (registry vs rendering) into one consumer-facing
    namespace. Without it, every test file would need two separate import statements and would couple to the internal
    subdivision of test-support code. The registry module holds assertion functions, CLI-argument helpers, coverage-
    suspension utilities, and the hook-registry installer — test orchestration primitives. The rendering module owns the
    fake Node.js runtime materialization, template rendering, and Windows shim generation — filesystem/simulation
    primitives. The __init__.py bridges these two concerns so that test files import from a single
    `pytest_bdd_testing.cucumber_formatters` location, keeping the contract stable even if responsibilities are later
    rebalanced between registry and rendering. It is consumed by 12+ test files across e2e, integration, contract,
    compatibility, and external test suites.

Delegates:
    - `registry`: Provides formatter output assertion functions (`assert_pytest_terminal_reporter_suppressed`,
    `assert_pytest_terminal_reporter_visible`, `assert_formatter_output_is_not_mixed_with_pytest_terminal`), pytest
    subprocess execution (`run_pytest_via_real_entrypoint`), CLI-argument inspection
    (`requests_terminal_formatter_output`, `with_pytester_terminal_capture_disabled`), fake node capture management
    (`enable_fake_node_capture`, `read_fake_node_captures`), telemetry normalization (`read_fake_formatter_telemetry`),
    hook proxy installation (`install_formatter_hook_registry`), expected-output accessors (`expected_formatter_output`,
    `expected_formatter_output_lines`, `expected_formatter_visible_line`), and the sample testdir builder
    (`build_sample_suite`).
    - `rendering`: Provides fake Node.js runtime materialization (`materialize_fake_node_runtime`,
    `materialize_live_formatter_runtime`) and the top-level monkeypatch-based installer that wires the fake runtime onto
    PATH and environment (`install_fake_node`).

Cohesion:
    All 15 re-exported names share a single purpose: they are the complete toolkit needed to test cucumber formatter
    behavior in pytest-bdd without requiring a real Node.js installation. The registry functions cover the "test
    orchestration" side (assert, run, inspect, install hooks), while the rendering functions cover the "fake
    environment" side (materialize node shims, install on PATH). Together they form a coherent vertical slice for
    formatter testing that is used uniformly across integration, e2e, contract, and compatibility test suites. No
    function in this package serves a purpose unrelated to cucumber formatter testing.

Separation:
    - `registry`: Kept separate from the __init__.py to avoid making the facade module itself hundreds of lines long
    with implementation detail; the registry module owns all assertion logic, subprocess invocation, coverage
    suspension, and hook-proxy wiring, which are conceptually distinct from file-I/O-based runtime materialization in
    rendering.
    - `rendering`: Kept separate from the __init__.py because it owns filesystem-heavy operations (template loading,
    directory creation, Windows .cmd shim generation, fake JS file writing) that involve imports from
    `pytest_bdd.compatibility.importlib.resources`, `pytest_bdd.plugin.gherkin_message_reporter.session`, and
    `pytest_bdd.util.cucumber_formatter_support.registry` — dependencies that the assertion/test-orchestration module
    (registry) does not share.

Main consumers:
    - `pytest_bdd_testing.e2e.cucumber_formatter_support`: Re-exports `install_fake_node`,
    `materialize_fake_node_runtime`, and `run_pytest_via_real_entrypoint` for the e2e test support layer.
    - `pytest_bdd_testing.cases.e2e.conftest`: Imports `install_fake_node`, `build_sample_suite`, and assertion
    functions for e2e conftest setup.
    - `pytest_bdd_testing.cases.e2e.steps_formatters`: Imports `install_fake_node` and `run_pytest_via_real_entrypoint`
    as Gherkin step-definition primitives.
    - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters`: Imports the full suite (assertions, runner,
    installer, sample builder) for the core formatter integration test.
    - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters_feature`: Imports the suite for feature-level cucumber
    formatter tests.
    - `pytest_bdd_testing.cases.contract.contract.test_formatter_golden_parity`: Imports `install_fake_node` for golden-
    output parity testing.
    - `pytest_bdd_testing.cases.contract.contract.test_cucumber_formatter_cli_contract`: Imports
    `install_formatter_hook_registry` for CLI contract tests.
    - `pytest_bdd_testing.cases.contract.support.test_cucumber_formatters`: Imports both `registry` and `rendering`
    modules directly for unit-level contract tests.
    - `pytest_bdd_testing.cases.integration.hook.test_live_formatter_terminal_layout`: Imports
    `materialize_live_formatter_runtime` for live formatter terminal layout tests.
    - `pytest_bdd_testing.cases.integration.hook.test_gherkin_reporter_context_lifecycle`: Imports
    `install_formatter_hook_registry` for hook lifecycle tests.
    - `pytest_bdd_testing.cases.external.support.test_docker_wsl2`: Imports `materialize_fake_node_runtime` for
    Docker/WSL2 test support.
    - `pytest_bdd_testing.cases.external.e2e.test_xdist_remote_message_aggregation`: Imports the suite for xdist remote
    message aggregation tests.
    - `pytest_bdd_testing.cases.external.e2e.test_xdist_message_aggregation`: Imports the suite for xdist message
    aggregation tests.
    - `pytest_bdd_testing.cases.compat.compatibility.test_render_cucumber_formatters`: Imports
    `materialize_live_formatter_runtime` for compatibility tests.

State and side effects:
    None, keeps no persistent state. This __init__.py is a pure re-export module with no mutable state, no file I/O, no
    network access, and no pytest stash reads/writes. All side effects are confined to the imported submodules.

Invariants:
    - Every public name exported from this module is defined in either `registry` or `rendering`; no symbol is defined
    directly in this file.
    - The set of exported names may grow or shrink as submodule APIs evolve, but must remain a flat union of stable
    public symbols from the two submodules.
    - No test file should import from `pytest_bdd_testing.cucumber_formatters.registry` or `rendering` directly — this
    __init__.py is the canonical import surface.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from pytest_bdd_testing.assertion.formatter import (
    assert_formatter_output_is_not_mixed_with_pytest_terminal,
    assert_pytest_terminal_reporter_suppressed,
    assert_pytest_terminal_reporter_visible,
)
from pytest_bdd_testing.tool.cucumber_formatter.registry import (
    build_sample_suite,
    enable_fake_node_capture,
    expected_formatter_output,
    expected_formatter_output_lines,
    expected_formatter_visible_line,
    install_formatter_hook_registry,
    read_fake_formatter_telemetry,
    read_fake_node_captures,
    requests_terminal_formatter_output,
    run_pytest_via_real_entrypoint,
    with_pytester_terminal_capture_disabled,
)
from pytest_bdd_testing.tool.cucumber_formatter.rendering import (
    install_fake_node,
    materialize_fake_node_runtime,
    materialize_live_formatter_runtime,
)
