"""
`pytest_bdd.cucumber_formatters.registry` — Test-fixture orchestration layer for cucumber formatter integration testing,
providing subprocess execution, output assertion, CLI-argument inspection, coverage suspension, telemetry capture, and
hook-proxy installation.

Responsibility:
    This module is the test-fixture orchestration layer for cucumber formatter integration testing. It owns the end-to-
    end machinery that runs pytest as a real subprocess with specific formatter CLI flags, suspends code-coverage
    instrumentation during subprocess execution to avoid measuring the subprocess itself, asserts whether pytest
    terminal reporter output was emitted or suppressed alongside formatter output, queries expected fake formatter
    output strings from the rendering module's output dictionary, normalizes fake-node capture telemetry into a
    structured format suitable for test assertions, installs a plugin-manager hook proxy that delegates cucumber
    formatter request and runtime-asset hook calls to discovered formatter plugins, and constructs a minimal in-testdir
    sample feature suite (one passing scenario, one failing scenario) with conftest step definitions. Every public
    function in this module is a test-support primitive that exercises or inspects the formatter subsystem from outside
    the pytest process boundary.

Reason for existence:
    This module is kept separate from `rendering` because it owns the "process orchestration and assertion" half of the
    formatter test stack, while `rendering` owns the "fake Node.js runtime filesystem materialization" half. The two
    halves have different dependency footprints: registry imports `subprocess`, `json`, and `contextlib` for subprocess
    execution and telemetry parsing, plus `pytest_bdd.util.cucumber_formatters` for CLI-flag inspection; rendering
    imports `shutil`, `stat`, and `pytest_bdd.plugin.gherkin_message_reporter.session` for filesystem scaffolding.
    Merging them would create a single module with ~900 lines covering two distinct operational domains (process
    management vs filesystem simulation) that have no shared control flow or state. The module is the authoritative
    source for the fake formatter output contract (`_FAKE_FORMATTER_OUTPUTS` is accessed here via a deferred import from
    rendering), for the terminal-fragment patterns that define "suppressed" vs "visible" pytest output, and for the
    subprocess environment-sanitization rules (PYTEST_BDD_FAKE_NODE_CAPTURE_DIR cleanup, NODE_PATH removal, PYTHONPATH
    injection).

Delegates:
    - `rendering._FAKE_FORMATTER_OUTPUTS`: Provides the dict of expected formatter output strings for each formatter
    name; accessed by `expected_formatter_output` via a deferred import to keep the module-level dependency on rendering
    lazy.
    - `pytest_bdd.util.cucumber_formatters.pytest_capture_already_configured`: Inspects CLI args to determine whether a
    capture mode is already explicitly set by the caller.
    - `pytest_bdd.util.cucumber_formatters.terminal_formatter_flags_requested`: Inspects CLI args to detect whether any
    terminal formatter flags (--cucumber-pretty, etc.) are present.
    - `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog`: Discovered at install time by
    `install_formatter_hook_registry` to resolve the set of registered formatter plugins; each plugin is iterated to
    collect formatter requests and runtime assets.
    - `_active_coverage_controller` / `_suspend_active_coverage`: Internal helpers that detect and temporarily stop the
    `coverage` library's active coverage measurement so that the subprocess's execution is not counted in coverage
    reports.
    - `json.loads` / `Path.read_text`: Used by `read_fake_node_captures` to deserialize captured JSON telemetry from the
    fake node capture directory.

Cohesion:
    All functions in this module revolve around a single concern: exercising the cucumber formatter subsystem and
    inspecting its behavior from test code. `run_pytest_via_real_entrypoint` is the main subprocess driver;
    `assert_pytest_terminal_reporter_suppressed` and `assert_pytest_terminal_reporter_visible` validate its output;
    `expected_formatter_output` and its line-oriented variants provide the oracle data;
    `requests_terminal_formatter_output` and `with_pytester_terminal_capture_disabled` are CLI-argument preprocessors
    consumed by the subprocess driver; `enable_fake_node_capture`, `read_fake_node_captures`, and
    `read_fake_formatter_telemetry` form a pipeline for capturing and normalizing fake-node telemetry;
    `install_formatter_hook_registry` wires a hook proxy for tests that exercise the hook lifecycle without a real
    subprocess; `build_sample_suite` creates the minimal testdir fixture consumed by nearly all formatter tests. The two
    internal helpers `_active_coverage_controller` and `_suspend_active_coverage` are only called by
    `run_pytest_via_real_entrypoint`.

Separation:
    - `rendering`: Kept separate because it owns filesystem-level fake runtime materialization (directory creation,
    template rendering, Windows .cmd shims, executable chmod) — operations that involve `shutil`, `stat`,
    `pytest_bdd.compatibility.importlib.resources.files`, and
    `pytest_bdd.plugin.gherkin_message_reporter.session.CucumberFormatterRequest`. Registry never touches these types or
    concerns.
    - `__init__`: Kept separate because it is a pure re-export facade with no logic; registry is one of the two backing
    modules it delegates to.

Main consumers:
    - `pytest_bdd_testing.cucumber_formatters.__init__`: Re-exports all 14 public symbols from this module as the
    canonical import surface.
    - `pytest_bdd_testing.cases.e2e.conftest`: Calls `install_fake_node`, `build_sample_suite`, and assertion functions
    to set up the e2e fixture environment.
    - `pytest_bdd_testing.cases.e2e.steps_formatters`: Uses `run_pytest_via_real_entrypoint` as a Gherkin step-
    definition primitive.
    - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters`: Uses the full suite of assertion functions and
    subprocess runner.
    - `pytest_bdd_testing.cases.contract.contract.test_cucumber_formatter_cli_contract`: Uses
    `install_formatter_hook_registry` for CLI contract tests.
    - `pytest_bdd_testing.cases.integration.hook.test_gherkin_reporter_context_lifecycle`: Uses
    `install_formatter_hook_registry` for hook lifecycle tests.

State and side effects:
    None, keeps no persistent state beyond three module-level constants (`_SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS`,
    `_VISIBLE_PYTEST_TERMINAL_FRAGMENTS`, `_REPO_ROOT`). The `run_pytest_via_real_entrypoint` function spawns a real
    subprocess that creates temporary files under `testdir.tmpdir` and writes to stdout/stderr;
    `enable_fake_node_capture` creates a directory under `tmp_path`; `install_formatter_hook_registry` mutates the
    passed-in `config` object by setting `config.pluginmanager.hook` to a `_HookProxy` instance. No network I/O, no
    pytest stash access.

Invariants:
    - `_SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS` defines the exact set of substrings that must NOT appear in output when a
    terminal formatter is active; if new terminal fragments are added upstream, this tuple must be updated.
    - `_VISIBLE_PYTEST_TERMINAL_FRAGMENTS` defines the exact set of substrings that MUST appear in output when no
    terminal formatter is active.
    - `_REPO_ROOT` is computed as `Path(__file__).resolve().parents[4]` and must resolve to the repository root; the
    parent count (4) is coupled to the directory depth of this file under `src/pytest_bdd_testing/tool/cucumber_formatter/`.
    - `run_pytest_via_real_entrypoint` strips all `PYTEST_*` environment variables (except `PYTEST_BDD_*`) from the
    subprocess environment to prevent test-session leakage.
    - `with_pytester_terminal_capture_disabled` must inject `--capture=no` only when a terminal formatter flag is
    present AND no explicit capture mode was already specified; otherwise the CLI args are returned unmodified.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import json
import os
import subprocess  # noqa: S404  # subprocess for formatter execution
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

    from _pytest.monkeypatch import MonkeyPatch

from pytest_bdd.util.cucumber_formatters import (
    pytest_capture_already_configured,
    terminal_formatter_flags_requested,
)

_SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS = (
    "test session starts",
    "platform ",
    "rootdir:",
    "collected ",
    "short test summary info",
    " passed in ",
)

_VISIBLE_PYTEST_TERMINAL_FRAGMENTS = (
    "test session starts",
    "platform ",
    "rootdir:",
    "collected ",
    "ERROR collecting ",
    "INTERNALERROR>",
)

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _active_coverage_controller() -> Any | None:
    """
    `registry._active_coverage_controller` — Returns the active Coverage controller instance if the coverage library is
    installed and currently measuring, otherwise None.

    Responsibility:
        Detects whether the `coverage` library is installed and currently active, and returns the active Coverage
        controller instance if one exists. This function is a defensive guard used exclusively by
        `_suspend_active_coverage` to safely stop and later restart coverage measurement when pytest is being invoked as
        a subprocess — without it, the subprocess's execution would be counted as part of the parent test's coverage,
        producing misleading metrics. The function handles three edge cases: coverage not installed (returns None),
        Coverage class not present (returns None), and `coverage.Coverage.current` not callable (returns None).

    Reason for existence:
        This function encapsulates the entire coverage-detection protocol so that `_suspend_active_coverage` and any
        future coverage-aware code can reuse the same detection logic. It localizes all knowledge about the `coverage`
        package's API surface (`coverage.Coverage.current()`) into a single, testable location. The function exists as a
        separate unit rather than being inlined into `_suspend_active_coverage` because the detection logic involves an
        import guard, attribute safety checks via `getattr`, and callable verification — three distinct concerns that
        would clutter the context manager's body.

    Delegates:
        - `import coverage`: Tries to import the optional `coverage` package at call time; if the import fails the
        function returns None immediately.
        - `getattr(coverage, "Coverage", None)`: Safely accesses the Coverage class attribute without assuming its existence.
        - `getattr(..., "current", None)`: Safely accesses the `current` classmethod on Coverage without assuming its existence.

    Cohesion:
        The function's entire logic is a single responsibility chain: try to get the active coverage controller,
        returning None at any failure point. No unrelated concerns are present.

    Separation:
        - `_suspend_active_coverage`: Kept separate because that function is a context manager that orchestrates the
        stop/restart lifecycle around a `yield` point; this function is the pure-detection helper it delegates to.

    Main consumers:
        - `_suspend_active_coverage`: Calls this function at entry to decide whether coverage suspension is necessary;
        receives either the controller instance or None.

    State and side effects:
        None, keeps no persistent state. The function reads `sys.modules` indirectly via `import coverage` but does not
        mutate it.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    try:
        import coverage
    except ImportError:
        return None
    current = getattr(getattr(coverage, "Coverage", None), "current", None)
    if not callable(current):
        return None
    return current()


@contextmanager
def _suspend_active_coverage() -> Generator[None, None, None]:
    """
    `registry._suspend_active_coverage` — Context manager that temporarily stops any active coverage measurement for the
    duration of the with-block, then restarts it on exit.

    Responsibility:
        Provides a context manager that temporarily suspends any active coverage measurement for the duration of the
        `with` block, then restarts it on exit. This is essential for `run_pytest_via_real_entrypoint`, which spawns a
        real pytest subprocess — without suspension, the subprocess's execution would be recorded as covered lines in
        the parent test's coverage report, inflating metrics and causing flaky coverage data. The context manager
        handles the edge case where coverage is not installed (yields immediately with no-op), and catches any
        `CoverageWarning` emitted when restarting coverage after stop.

    Reason for existence:
        This context manager isolates the coverage-suspension protocol from the subprocess-invocation logic in
        `run_pytest_via_real_entrypoint`. The protocol involves three non-trivial steps: detecting the active
        controller, calling `controller.stop()`, and in the `finally` block, suppressing coverage warnings and calling
        `controller.start()`. Extracting this into a context manager makes the subprocess runner's code cleaner (a
        single `with _suspend_active_coverage():` line) and makes the coverage suspension behavior independently
        testable and reusable.

    Delegates:
        - `_active_coverage_controller`: Called at entry to detect whether a coverage controller exists; if None, the
        context manager yields immediately with no further action.
        - `sys.modules.get("coverage")`: Accesses the coverage module from sys.modules to retrieve the `CoverageWarning`
        exception class without re-importing.
        - `warnings.catch_warnings` / `warnings.filterwarnings("ignore", ...)`: Suppresses `CoverageWarning` during the
        `controller.start()` call in the `finally` block.

    Cohesion:
        The entire function is the stop-yield-restart lifecycle for coverage — a single, focused concern with no
        unrelated logic.

    Separation:
        - `_active_coverage_controller`: Kept separate because it is the pure-detection helper; this function is the
        lifecycle orchestrator that uses it.
        - `run_pytest_via_real_entrypoint`: Kept separate because that function owns subprocess invocation; this context
        manager is a reusable utility consumed by it.

    Main consumers:
        - `run_pytest_via_real_entrypoint`: Wraps the `subprocess.run` call in `with _suspend_active_coverage():` to
        prevent coverage pollution.

    State and side effects:
        Calls `controller.stop()` and `controller.start()` on the active coverage controller, which mutates the global
        coverage measurement state. The `finally` block guarantees restart even if the wrapped block raises. No
        file/network I/O, no pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    controller = _active_coverage_controller()
    if controller is None:
        yield
        return
    coverage_module = sys.modules.get("coverage")
    coverage_warning = getattr(getattr(coverage_module, "exceptions", None), "CoverageWarning", Warning)
    controller.stop()
    try:
        yield
    finally:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=coverage_warning)
            controller.start()


def expected_formatter_output(formatter_name: str) -> str:
    """
    `registry.expected_formatter_output` — Looks up the expected fake output string for a named cucumber formatter from
    the rendering module's output dictionary.

    Responsibility:
        Looks up the expected fake output string for a named cucumber formatter from the `_FAKE_FORMATTER_OUTPUTS`
        dictionary defined in the `rendering` module. This function is the authoritative accessor for the formatter-
        output oracle data — every test that asserts formatter stdout content goes through this function. It performs a
        deferred import of `rendering._FAKE_FORMATTER_OUTPUTS` to avoid a module-level circular dependency between
        registry and rendering (rendering does not import registry, but registry importing rendering at module level
        would be architecturally undesirable since registry is the "orchestration" half and rendering is the
        "simulation" half).

    Reason for existence:
        This function exists as a thin typed accessor rather than having test code directly import and index
        `_FAKE_FORMATTER_OUTPUTS` because it encapsulates the deferred import pattern and provides a single point where
        the oracle-data contract can be validated, logged, or changed. If the backing dictionary moves to a different
        module or changes format, only this function needs updating. The deferred import also ensures that `rendering`'s
        heavy imports (`shutil`, `stat`, `pytest_bdd.plugin.gherkin_message_reporter.session`) are not loaded until this
        function is actually called.

    Delegates:
        - `rendering._FAKE_FORMATTER_OUTPUTS`: The source-of-truth dictionary mapping formatter names (e.g., "summary",
        "progress", "pretty", "json", "junit") to their expected output strings; accessed via a deferred local import.

    Cohesion:
        This function is a pure data-accessor — a single expression returning one dictionary value. It is tightly
        cohesive with `expected_formatter_output_lines` and `expected_formatter_visible_line`, which compose on top of
        it.

    Separation:
        - `expected_formatter_output_lines`: Kept separate because it adds the `splitlines()` post-processing step; it
        delegates to this function.
        - `expected_formatter_visible_line`: Kept separate because it selects only the first line; it delegates to
        `expected_formatter_output_lines`.

    Main consumers:
        - `expected_formatter_output_lines`: Calls this function and splits the result into lines.
        - `assert_formatter_output_is_not_mixed_with_pytest_terminal`: Calls `expected_formatter_visible_line` (which
        transitively calls this function) to verify that the first line of expected formatter output appears in the
        captured subprocess output.

    State and side effects:
        None, keeps no persistent state. Pure function with no I/O beyond the deferred import of rendering (which
        imports are cached by Python after first call).

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    from pytest_bdd_testing.tool.cucumber_formatter.rendering import _FAKE_FORMATTER_OUTPUTS

    return _FAKE_FORMATTER_OUTPUTS[formatter_name]


def expected_formatter_output_lines(formatter_name: str) -> list[str]:
    """
    `registry.expected_formatter_output_lines` — Returns the expected fake formatter output for a named formatter, split
    into individual lines.

    Responsibility:
        Returns the expected fake formatter output for a named formatter split into individual lines. This is a trivial
        composition on top of `expected_formatter_output` that adds `str.splitlines()`. It exists so that test
        assertions that need to inspect individual output lines (rather than the full string) have a direct, named API
        rather than repeating the `.splitlines()` call at every call site, which would couple test code to the string
        representation of the oracle data.

    Reason for existence:
        This function provides a line-oriented variant of the expected output oracle without requiring test code to know
        that the backing data is a single string. If the backing representation ever changed (e.g., to a pre-split
        list), only this function would need updating. It also serves as a semantic marker: when a test calls
        `expected_formatter_output_lines`, it signals intent to do per-line assertions, which aids readability and grep-
        ability of the test code.

    Delegates:
        - `expected_formatter_output`: Called to retrieve the raw expected output string, which is then split into lines.

    Cohesion:
        Single-line delegation function — fully cohesive with `expected_formatter_output` as its sole dependency.

    Separation:
        - `expected_formatter_output`: Kept separate because it is the raw-string accessor; this function is the line-
        oriented variant.
        - `expected_formatter_visible_line`: Kept separate because it selects only the first line; it delegates to this
        function.

    Main consumers:
        - `expected_formatter_visible_line`: Calls `expected_formatter_output_lines(formatter_name)[0]` to get the first line.
        - External test modules that need per-line oracle data for assertions.

    State and side effects:
        None, keeps no persistent state. Pure delegation function.

    Architecture score:
        #arch-eval:reason_for_existence=2
        #arch-eval:owned_responsibility=2
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    return expected_formatter_output(formatter_name).splitlines()


def expected_formatter_visible_line(formatter_name: str) -> str:
    """
    `registry.expected_formatter_visible_line` — Returns the first line of the expected formatter output for a given
    formatter name.

    Responsibility:
        Returns the first line of the expected formatter output for a given formatter name. This is the specific oracle
        value used by `assert_formatter_output_is_not_mixed_with_pytest_terminal` to verify that formatter output is
        present in the captured subprocess output — the assertion only checks that at least the first visible line
        appears, not the entire output. By isolating the "first line" selection into its own function, the assertion
        code stays clean and the selection logic is explicit.

    Reason for existence:
        This function exists as a semantic convenience: it names the concept of "the visible line that proves formatter
        output was produced." Without it, every call site that needs just the first line would write
        `expected_formatter_output_lines(formatter_name)[0]`, which is less descriptive and more brittle. If the
        "visible line" selection rule ever changes (e.g., to the second line, or a specific marker line), only this
        function needs updating.

    Delegates:
        - `expected_formatter_output_lines`: Called to get the full list of lines; this function returns index 0.

    Cohesion:
        Single-expression delegation function — fully cohesive with the expected-output accessor chain.

    Separation:
        - `expected_formatter_output_lines`: Kept separate because it provides the full line list; this function is the
        first-line selector.
        - `assert_formatter_output_is_not_mixed_with_pytest_terminal`: Kept separate because it is the assertion
        consumer; this function is the oracle provider.

    Main consumers:
        - `assert_formatter_output_is_not_mixed_with_pytest_terminal`: Uses this function's return value to check
        `assert expected_formatter_visible_line(formatter_name) in output`.

    State and side effects:
        None, keeps no persistent state. Pure delegation function.

    Architecture score:
        #arch-eval:reason_for_existence=2
        #arch-eval:owned_responsibility=2
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    return expected_formatter_output_lines(formatter_name)[0]


def assert_pytest_terminal_reporter_suppressed(output: str) -> None:
    """
    `registry.assert_pytest_terminal_reporter_suppressed` — Asserts that no known pytest terminal reporter fragments
    appear in the given output string.

    Responsibility:
        Asserts that none of the known pytest terminal reporter fragments (test session starts, platform, rootdir,
        collected count, short test summary info, passed-in duration) appear in the given output string. This is the
        primary assertion used to verify that cucumber terminal formatters have successfully suppressed the default
        pytest terminal reporter output. When a formatter like `--cucumber-pretty` is active, pytest's built-in terminal
        output should be absent — this function enforces that contract.

    Reason for existence:
        This function encapsulates the suppressed-fragment check as a named assertion with a descriptive error message.
        It exists as a separate function rather than being inlined into
        `assert_formatter_output_is_not_mixed_with_pytest_terminal` because "assert suppressed" and "assert visible" are
        complementary but independent assertions that are used in different test contexts — some tests only need one
        direction. The function also localizes the knowledge of which fragment strings constitute "pytest terminal
        output," which is defined in the module-level `_SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS` tuple.

    Delegates:
        - `_SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS`: The module-level tuple of substrings that must NOT appear in the
        output; iterated to build the `unexpected_fragments` list.

    Cohesion:
        This function performs a single assertion with a single failure mode — it is maximally cohesive.

    Separation:
        - `assert_pytest_terminal_reporter_visible`: Kept separate because it asserts the opposite condition (fragments
        MUST appear); the two functions share the same fragment-matching pattern but different failure semantics.
        - `assert_formatter_output_is_not_mixed_with_pytest_terminal`: Kept separate because it composes both
        assertions; this function is one half of that composed check.

    Main consumers:
        - `assert_formatter_output_is_not_mixed_with_pytest_terminal`: Calls this function after verifying that
        formatter output is present, ensuring terminal output is suppressed.
        - External test modules that independently verify suppression of pytest terminal output.

    State and side effects:
        None, keeps no persistent state. Pure assertion function — either returns None or raises AssertionError.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    unexpected_fragments = [fragment for fragment in _SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS if fragment in output]
    assert unexpected_fragments == [], (
        f"unexpected default pytest terminal reporter output was emitted: {unexpected_fragments!r}\n{output}"
    )


def assert_pytest_terminal_reporter_visible(output: str) -> None:
    """
    `registry.assert_pytest_terminal_reporter_visible` — Asserts that at least one known pytest terminal reporter
    fragment appears in the given output string.

    Responsibility:
        Asserts that at least one of the known pytest terminal reporter fragments (test session starts, platform,
        rootdir, collected count, ERROR collecting marker, INTERNALERROR marker) appears in the given output string.
        This is the assertion used in "baseline" or "no-formatter" test scenarios to verify that pytest's default
        terminal reporter is functioning correctly when no cucumber formatter is active — i.e., that the terminal output
        wasn't accidentally suppressed.

    Reason for existence:
        This function provides the positive counterpart to `assert_pytest_terminal_reporter_suppressed`. While that
        function checks for absence, this one checks for presence. They are maintained as separate functions because the
        fragment sets differ slightly (visible includes "ERROR collecting " and "INTERNALERROR>" markers that would be
        valid pytest terminal output in error scenarios but are not part of the suppressed set), and because combining
        both directions into one function with a boolean flag would be less readable at call sites.

    Delegates:
        - `_VISIBLE_PYTEST_TERMINAL_FRAGMENTS`: The module-level tuple of substrings that MUST appear in the output;
        iterated to build the `visible_fragments` list.

    Cohesion:
        This function performs a single assertion with a single failure mode — it is maximally cohesive.

    Separation:
        - `assert_pytest_terminal_reporter_suppressed`: Kept separate because it asserts the opposite condition with a
        slightly different fragment set; the two functions share the same fragment-matching pattern but serve different
        test scenarios.
        - `assert_formatter_output_is_not_mixed_with_pytest_terminal`: Kept separate; this function is not used by it
        (that function uses suppressed, not visible).

    Main consumers:
        - External test modules that need to verify pytest terminal reporter is functioning in baseline/no-formatter scenarios.

    State and side effects:
        None, keeps no persistent state. Pure assertion function — either returns None or raises AssertionError.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    visible_fragments = [fragment for fragment in _VISIBLE_PYTEST_TERMINAL_FRAGMENTS if fragment in output]
    assert visible_fragments, f"expected default pytest terminal reporter output, got:\n{output}"


def assert_formatter_output_is_not_mixed_with_pytest_terminal(output: str, *, formatter_name: str) -> None:
    """
    `registry.assert_formatter_output_is_not_mixed_with_pytest_terminal` — Asserts that expected formatter output is
    present and that no pytest terminal reporter fragments appear in the given output.

    Responsibility:
        Performs a combined two-part assertion on subprocess output: first verifies that the expected formatter output's
        first visible line appears in the output (proving the formatter ran and produced output), then verifies that no
        pytest terminal reporter fragments are present (proving the formatter successfully suppressed pytest's default
        output). This is the primary output-validation assertion used in cucumber formatter integration tests — it
        confirms both that the formatter worked AND that it didn't leak pytest terminal output into the formatter
        stream.

    Reason for existence:
        This function composes the two lower-level assertions (`expected_formatter_visible_line` check and
        `assert_pytest_terminal_reporter_suppressed`) into a single named check that captures the full semantic
        contract: "formatter output present, pytest terminal output absent." Without this composition, every formatter
        test would need to write both assertions separately, which is repetitive and risks one being forgotten. The
        keyword-only `formatter_name` parameter ensures call sites are explicit about which formatter's oracle data to
        use.

    Delegates:
        - `expected_formatter_visible_line`: Called to get the first line of expected output for the named formatter;
        the result is checked with `assert ... in output`.
        - `assert_pytest_terminal_reporter_suppressed`: Called after the visible-line check to verify no pytest terminal
        fragments are present.

    Cohesion:
        This function composes two tightly related assertions into one semantic unit — both assertions validate the same
        `output` string against the same formatter, and they are always used together in formatter tests.

    Separation:
        - `assert_pytest_terminal_reporter_suppressed`: Kept separate because it can be used independently in tests that
        only care about suppression.
        - `run_pytest_via_real_entrypoint`: Kept separate because that function produces the output; this function validates it.

    Main consumers:
        - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters`: Calls this function for each formatter variant to
        validate subprocess output.

    State and side effects:
        None, keeps no persistent state. Pure assertion function — either returns None or raises AssertionError.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    assert expected_formatter_visible_line(formatter_name) in output, output
    assert_pytest_terminal_reporter_suppressed(output)


def run_pytest_via_real_entrypoint(
    testdir: Any,
    *cli_args: str,
    extra_env: dict[str, str] | None = None,
    preserve_fake_node: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    `registry.run_pytest_via_real_entrypoint` — Executes pytest as a real subprocess targeting files in a pytest testdir
    with sanitized environment, coverage suspension, and optional terminal-capture disabling.

    Responsibility:
        Executes pytest as a real subprocess via `subprocess.run` using the same Python interpreter that is running the
        current test session, targeting the test files inside a pytest `testdir` fixture. This function is the core
        subprocess driver for cucumber formatter integration testing — it constructs a sanitized environment (strips all
        `PYTEST_*` variables except `PYTEST_BDD_*`, injects `PYTHONPATH=src`, optionally removes fake-node
        PATH/NODE_PATH entries), appends `--capture=no` when a terminal formatter is active and no explicit capture mode
        was set, suspends active coverage during the subprocess run, and returns the `CompletedProcess` with captured
        stdout/stderr as text. The function supports two modes: default mode (cleans up fake node environment so the
        subprocess uses real Node.js if available) and `preserve_fake_node=True` mode (keeps fake node environment
        variables so the subprocess uses the fake node runtime).

    Reason for existence:
        This function is kept as a single, large, configurable subprocess driver rather than being split across multiple
        smaller functions because all of its logic serves one coherent goal: "produce a clean subprocess environment
        that mirrors real-world pytest invocation as closely as possible." The environment sanitization, PYTHONPATH
        injection, capture-mode injection, and coverage suspension are all interdependent — changing one often requires
        adjusting another — so co-locating them ensures consistency. The function exists in registry rather than
        rendering because it is the "orchestration" half of formatter testing: it runs pytest, while rendering provides
        the fake runtime that pytest may or may not use.

    Delegates:
        - `with_pytester_terminal_capture_disabled`: Called to optionally inject `--capture=no` into the CLI args when a
        terminal formatter flag is detected and no explicit capture mode is configured.
        - `_suspend_active_coverage`: Called as a context manager wrapping the `subprocess.run` call to prevent coverage
        pollution.
        - `subprocess.run`: The actual subprocess invocation using `[sys.executable, "-m", "pytest", *cli_args]`.

    Cohesion:
        All logic in this function serves the single purpose of constructing a correct subprocess invocation
        environment. Environment variable filtering, PATH manipulation, PYTHONPATH setup, and coverage suspension are
        all facets of "prepare a clean subprocess execution context."

    Separation:
        - `materialize_fake_node_runtime` / `install_fake_node` (in rendering): Kept separate because those functions
        create the fake runtime artifacts on disk; this function only reads/cleans the environment variables that point
        to them.
        - `build_sample_suite`: Kept separate because that function creates the test files inside testdir; this function
        runs pytest against them.

    Main consumers:
        - `pytest_bdd_testing.cases.e2e.steps_formatters`: Called as a Gherkin step-definition primitive to run pytest
        with formatter flags.
        - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters`: Called for each formatter variant test case.
        - `pytest_bdd_testing.cases.external.e2e.test_xdist_message_aggregation`: Called for xdist message aggregation tests.
        - `pytest_bdd_testing.cases.external.e2e.test_xdist_remote_message_aggregation`: Called for xdist remote message
        aggregation tests.
        - `pytest_bdd_testing.cases.compat.compatibility.test_render_cucumber_formatters`: Called for compatibility tests.

    State and side effects:
        Spawns a real subprocess that executes pytest, which creates temporary files under `testdir.tmpdir` and writes
        to stdout/stderr (captured in the returned `CompletedProcess`). Reads `os.environ` to build a sanitized copy.
        Modifies the copied environment dict (`env`) but never mutates the actual process environment. Suspends and
        restarts coverage measurement via `_suspend_active_coverage`. No network I/O, no pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=3
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    repo_root = _REPO_ROOT
    env = os.environ.copy()
    if not preserve_fake_node:
        capture_dir = env.pop("PYTEST_BDD_FAKE_NODE_CAPTURE_DIR", None)
        if capture_dir:
            fake_bin = Path(capture_dir).parent / "fake-node-bin"
            env["PATH"] = os.pathsep.join(
                p for p in env["PATH"].split(os.pathsep) if Path(p).resolve() != fake_bin.resolve()
            )
        env.pop("NODE_PATH", None)
        env.pop("FAKE_GLOBAL_NODE_MODULES_ROOT", None)
    for key in tuple(env):
        if key.startswith("PYTEST_") and not key.startswith("PYTEST_BDD_"):
            env.pop(key, None)
    src_path = str(repo_root / "src")
    env["PYTHONPATH"] = src_path
    if extra_env:
        env.update(extra_env)
    effective_cli_args = with_pytester_terminal_capture_disabled(*cli_args)
    with _suspend_active_coverage():
        return subprocess.run(  # noqa: S603  # trusted formatter commands
            [sys.executable, "-m", "pytest", *effective_cli_args],
            cwd=str(testdir.tmpdir),
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )


def requests_terminal_formatter_output(*cli_args: str) -> bool:
    """
    `registry.requests_terminal_formatter_output` — Returns True if any terminal formatter flags are present in the
    given pytest CLI arguments.

    Responsibility:
        Inspects the given pytest CLI arguments to determine whether any terminal formatter flags are present (e.g.,
        `--cucumber-pretty`, `--cucumber-summary`, `--cucumber-progress`, `--cucumber-progress-bar`, `--cucumber-usage`,
        `--cucumber-snippets`). This is a thin typed wrapper around `terminal_formatter_flags_requested` from
        `pytest_bdd.util.cucumber_formatters` that provides a stable, test-facing API name in the registry module's
        namespace.

    Reason for existence:
        This wrapper exists to keep the `pytest_bdd.util.cucumber_formatters` import localized to this module — test
        code that needs to check for terminal formatter flags imports from `registry` rather than from the utility layer
        directly. This maintains the facade pattern of the `cucumber_formatters` package and ensures that if the utility
        function's name or signature changes, only the wrapper needs updating.

    Delegates:
        - `pytest_bdd.util.cucumber_formatters.terminal_formatter_flags_requested`: The actual implementation that
        inspects CLI args for terminal formatter flags.

    Cohesion:
        Single-expression delegation function — fully cohesive with the CLI-argument inspection concern.

    Separation:
        - `with_pytester_terminal_capture_disabled`: Kept separate because it uses this function's result to decide
        whether to inject `--capture=no`; this function is the pure query, while that function is the command.

    Main consumers:
        - `with_pytester_terminal_capture_disabled`: Calls this function to decide whether capture-disabling is needed.

    State and side effects:
        None, keeps no persistent state. Pure delegation function.

    Architecture score:
        #arch-eval:reason_for_existence=2
        #arch-eval:owned_responsibility=2
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    return terminal_formatter_flags_requested(cli_args)


def with_pytester_terminal_capture_disabled(*cli_args: str) -> tuple[str, ...]:
    """
    `registry.with_pytester_terminal_capture_disabled` — Conditionally injects --capture=no into CLI args when a
    terminal formatter is active and no explicit capture mode is configured.

    Responsibility:
        Conditionally injects `--capture=no` into the given pytest CLI arguments when all three conditions are met: (a)
        no explicit capture mode is already configured in the args, (b) a terminal formatter flag is detected, and (c)
        the caller didn't already pass `--capture=...`. This ensures that when pytest runs as a subprocess with a
        terminal formatter, the output capture machinery doesn't interfere with the formatter's own terminal output. If
        the conditions aren't met, the args are returned unmodified.

    Reason for existence:
        This function encapsulates the capture-mode injection logic in one place so that
        `run_pytest_via_real_entrypoint` doesn't need to understand the details of when and why capture should be
        disabled. It also prevents double-injection: by checking `pytest_capture_already_configured` first, it avoids
        adding `--capture=no` when the caller has already specified a capture mode, which would cause a pytest argument
        conflict.

    Delegates:
        - `pytest_bdd.util.cucumber_formatters.pytest_capture_already_configured`: Checks whether any `--capture=...`
        flag is already in the args.
        - `requests_terminal_formatter_output`: Checks whether terminal formatter flags are present.

    Cohesion:
        This function performs a single conditional transformation on CLI args — it is tightly focused on the capture-
        mode injection concern.

    Separation:
        - `requests_terminal_formatter_output`: Kept separate because it is the pure query; this function is the
        conditional command that uses it.
        - `run_pytest_via_real_entrypoint`: Kept separate because it is the consumer that passes CLI args through this
        function before subprocess invocation.

    Main consumers:
        - `run_pytest_via_real_entrypoint`: Calls `with_pytester_terminal_capture_disabled(*cli_args)` to get the
        effective CLI args for subprocess invocation.

    State and side effects:
        None, keeps no persistent state. Pure transformation function — returns a new tuple without mutating the input.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    if pytest_capture_already_configured(cli_args):
        return cli_args
    if not terminal_formatter_flags_requested(cli_args):
        return cli_args
    return ("--capture=no", *cli_args)


def enable_fake_node_capture(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """
    `registry.enable_fake_node_capture` — Creates a fake-node-captures directory under tmp_path and sets
    PYTEST_BDD_FAKE_NODE_CAPTURE_DIR via monkeypatch.

    Responsibility:
        Creates a `fake-node-captures` directory under the given `tmp_path` and sets the
        `PYTEST_BDD_FAKE_NODE_CAPTURE_DIR` environment variable to its path via `monkeypatch.setenv`. This directory is
        where the fake Node.js runtime writes JSON capture files recording details of each formatter invocation
        (formatter names used, message envelope counts, console writes, etc.). The function returns the created
        directory path so callers can later pass it to `read_fake_node_captures` or `read_fake_formatter_telemetry` for
        post-hoc analysis.

    Reason for existence:
        This function encapsulates the two-step setup (directory creation + env var injection) that is required before
        every test that needs to inspect fake-node telemetry. It exists as a named function rather than being inlined
        because the setup pattern is used across multiple test modules, and the semantic name `enable_fake_node_capture`
        clearly signals intent at call sites. It takes a `MonkeyPatch` to ensure the env var is cleaned up after the
        test, following pytest fixture best practices.

    Delegates:
        - `tmp_path.mkdir(exist_ok=True)`: Creates the capture directory on the filesystem.
        - `monkeypatch.setenv`: Sets `PYTEST_BDD_FAKE_NODE_CAPTURE_DIR` for the duration of the test.

    Cohesion:
        This function performs two tightly coupled operations (mkdir + setenv) that together form a single logical step:
        "enable capture." No unrelated concerns.

    Separation:
        - `read_fake_node_captures`: Kept separate because it reads the captures; this function sets up the directory
        where they are written.
        - `read_fake_formatter_telemetry`: Kept separate because it normalizes raw captures into structured telemetry;
        this function enables capture collection.
        - `install_fake_node` (in rendering): Kept separate because that function also sets
        `PYTEST_BDD_FAKE_NODE_CAPTURE_DIR` as part of the broader fake-node installation; this function is a lighter-
        weight alternative used when fake node is already installed.

    Main consumers:
        - External test modules that need to inspect fake-node telemetry after running pytest with formatters.

    State and side effects:
        Creates a directory on the filesystem under `tmp_path`. Mutates the process environment via `monkeypatch.setenv`
        (which is scoped to the test duration by pytest's monkeypatch fixture). No network I/O, no pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    capture_dir = tmp_path / "fake-node-captures"
    capture_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PYTEST_BDD_FAKE_NODE_CAPTURE_DIR", str(capture_dir))
    return capture_dir


def read_fake_node_captures(capture_dir: Path) -> list[dict[str, Any]]:
    """
    `registry.read_fake_node_captures` — Reads and parses all JSON capture files from a capture directory, sorted by
    filename.

    Responsibility:
        Reads all JSON files from the given capture directory (sorted by filename) and returns their parsed contents as
        a list of dictionaries. Each JSON file represents one fake-node formatter invocation's raw capture data as
        written by the fake node runtime's Python shim. This is the raw data accessor — for normalized/higher-level
        telemetry, use `read_fake_formatter_telemetry` which builds on top of this function.

    Reason for existence:
        This function encapsulates the JSON-file-reading protocol (glob, sort, parse) so that consumers of fake-node
        capture data don't need to know the file naming convention, the JSON encoding (UTF-8), or the sorting strategy.
        If the capture format changes from individual JSON files to a single NDJSON file, only this function needs
        updating.

    Delegates:
        - `capture_dir.glob("*.json")`: Finds all JSON capture files in the directory.
        - `json.loads`: Parses each file's text content into a Python dict.

    Cohesion:
        This function performs a single logical operation: "read and parse all capture files from a directory." No
        unrelated logic.

    Separation:
        - `enable_fake_node_capture`: Kept separate because it creates the capture directory; this function reads from it.
        - `read_fake_formatter_telemetry`: Kept separate because it normalizes the raw captures returned by this
        function into structured telemetry records.

    Main consumers:
        - `read_fake_formatter_telemetry`: Calls this function to get raw captures, then normalizes them.

    State and side effects:
        Reads files from the filesystem under `capture_dir`. No writes, no network I/O, no environment mutation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    return [json.loads(capture_path.read_text(encoding="utf-8")) for capture_path in sorted(capture_dir.glob("*.json"))]


def read_fake_formatter_telemetry(tmp_path: Path) -> list[dict[str, Any]]:
    """
    `registry.read_fake_formatter_telemetry` — Reads raw fake-node capture files and normalizes each into a structured
    telemetry record with standardized field names.

    Responsibility:
        Reads raw fake-node capture files from `tmp_path / "fake-node-captures"` and normalizes each capture into a
        structured telemetry record with standardized field names (`sourceMode`, `formatterNames`, `envelopeCount`,
        `emittedVisibleOutputDuringStream`, `consoleWriteCount`, `consoleFormatterNames`, optionally `messagesPath` and
        `workerIds`). The normalization bridges the gap between the raw capture dictionary written by the fake node
        runtime's Python shim (which uses arbitrary key names like `messagesPath`, `envelopeCount`,
        `emittedConsoleBeforeClose`) and the structured assertions that test code needs to make (checking formatter
        names, message counts, console output behavior).

    Reason for existence:
        This function exists as a dedicated normalization layer because the raw capture format is determined by the fake
        node runtime's internal logging, which may change independently of the test assertions. By normalizing here,
        test code can assert against stable field names (`sourceMode`, `formatterNames`, etc.) without coupling to the
        fake runtime's internal key naming. The function also resolves the capture directory path (`tmp_path / "fake-
        node-captures"`) so callers don't need to know the directory convention.

    Delegates:
        - `read_fake_node_captures`: Called to read the raw JSON capture files from the capture directory; returns a
        list of raw dicts that this function then normalizes.

    Cohesion:
        This function performs a single transformation: raw captures → normalized telemetry. Every line of code serves
        that transformation.

    Separation:
        - `read_fake_node_captures`: Kept separate because it is the raw-file reader; this function is the normalizer
        that uses it.
        - `enable_fake_node_capture`: Kept separate because it sets up the capture directory; this function reads and
        normalizes its contents.

    Main consumers:
        - External test modules that need structured telemetry data to assert formatter behavior (e.g., verifying that
        the correct formatter names were used, that envelope counts are non-zero, that console output was emitted during
        streaming).

    State and side effects:
        Reads files from the filesystem under `tmp_path / "fake-node-captures"`. No writes, no network I/O, no
        environment mutation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    telemetry: list[dict[str, Any]] = []
    for capture in read_fake_node_captures(tmp_path / "fake-node-captures"):
        source_mode = "messagesPath" if capture.get("messagesPath") else "stdin"
        normalized = {
            "sourceMode": source_mode,
            "formatterNames": capture.get("formatterNames", []),
            "envelopeCount": capture.get("envelopeCount", 0),
            "emittedVisibleOutputDuringStream": capture.get("emittedConsoleBeforeClose", False),
            "consoleWriteCount": capture.get("consoleWriteCount", 0),
            "consoleFormatterNames": capture.get("consoleFormatterNames", []),
        }
        messages_path = capture.get("messagesPath")
        if messages_path:
            normalized["messagesPath"] = messages_path
        worker_ids = capture.get("workerIds")
        if worker_ids:
            normalized["workerIds"] = worker_ids
        telemetry.append(normalized)
    return telemetry


def install_formatter_hook_registry(
    config: Any,
    *,
    catalog: Any = None,
) -> Any:
    """
    `registry.install_formatter_hook_registry` — Installs a _HookProxy onto config.pluginmanager.hook that delegates
    cucumber formatter hook calls to the discovered plugin catalog.

    Responsibility:
        Installs a `_HookProxy` instance as `config.pluginmanager.hook`, wiring the pytest plugin manager's hook-calling
        mechanism to the discovered formatter plugin catalog. The `_HookProxy` class provides two hook methods —
        `pytest_bdd_cucumber_formatter_request` (iterates all discovered plugins to collect formatter request dicts) and
        `pytest_bdd_cucumber_formatter_runtime_assets` (iterates all discovered plugins to collect rendered runtime
        assets) — which together simulate the hook calls that the real gherkin message reporter plugin makes during
        formatter initialization. If `config` has no `pluginmanager` attribute, a `SimpleNamespace` is created to hold
        the proxy. This function is used in tests that exercise the formatter hook lifecycle without spawning a real
        subprocess.

    Reason for existence:
        This function exists to provide a lightweight, in-process alternative to `run_pytest_via_real_entrypoint` for
        tests that only need to verify hook-calling behavior (which plugins are discovered, what formatter requests they
        produce, what runtime assets they render). It avoids the overhead of a subprocess invocation while still
        exercising the real `FormatterPluginCatalog.discover()` path. The `_HookProxy` is defined as a local class
        inside this function because it closes over the `resolved_catalog` variable, which keeps the hook proxy's
        dependency on the catalog explicit and prevents the class from being accidentally reused with a different
        catalog.

    Delegates:
        - `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.discover()`: Discovers all
        registered formatter plugins when `catalog` is None; if a catalog is passed explicitly, it is used directly.
        - `_HookProxy`: A locally-defined class that implements `pytest_bdd_cucumber_formatter_request` and
        `pytest_bdd_cucumber_formatter_runtime_assets` by iterating `resolved_catalog.plugins` and delegating to each
        plugin's corresponding method.

    Cohesion:
        The function's logic is a single pipeline: resolve catalog → create hook proxy → attach to pluginmanager →
        return pluginmanager. The `_HookProxy` class is defined inline because it is a closure over `resolved_catalog`
        and has no meaning outside this function.

    Separation:
        - `materialize_live_formatter_runtime` (in rendering): Kept separate because that function uses the real
        `FormatterPluginCatalog` to build runtime artifacts on disk; this function installs a hook proxy for in-process
        hook testing.
        - `run_pytest_via_real_entrypoint`: Kept separate because that function spawns a real subprocess; this function
        operates entirely in-process.

    Main consumers:
        - `pytest_bdd_testing.cases.integration.hook.test_gherkin_reporter_context_lifecycle`: Uses this function to
        install a hook proxy and test hook lifecycle behavior.
        - `pytest_bdd_testing.cases.contract.contract.test_cucumber_formatter_cli_contract`: Uses this function for CLI
        contract tests.

    State and side effects:
        Mutates the passed-in `config` object by setting `config.pluginmanager = SimpleNamespace()` (if not already
        present) and `config.pluginmanager.hook = _HookProxy()`. Imports `FormatterPluginCatalog` via a deferred import
        inside the function body. No file I/O, no network access, no environment mutation.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=3
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog

    resolved_catalog = FormatterPluginCatalog.discover() if catalog is None else catalog

    class _HookProxy:
        """
        `install_formatter_hook_registry._HookProxy` — Fake pytest plugin-manager hook proxy that broadcasts cucumber
        formatter hook calls to all plugins in the resolved FormatterPluginCatalog.

        Responsibility:
            Acts as a fake pytest plugin-manager hook proxy that delegates cucumber formatter hook calls to all plugins
            in the resolved `FormatterPluginCatalog`. It implements two hook methods:
            `pytest_bdd_cucumber_formatter_request` iterates every plugin to collect formatter request dictionaries
            (skipping plugins that return None), and `pytest_bdd_cucumber_formatter_runtime_assets` iterates every
            plugin to collect rendered runtime asset dictionaries (skipping plugins that return empty/falsy results).
            This proxy is installed onto `config.pluginmanager.hook` to simulate the real hook-calling mechanism that
            the gherkin message reporter plugin uses during formatter initialization.

        Reason for existence:
            This class is defined as a local class inside `install_formatter_hook_registry` because it closes over the
            `resolved_catalog` variable — each proxy instance is bound to a specific catalog, and defining it inline
            makes this binding explicit and prevents accidental reuse with a different catalog. The class exists as a
            named type rather than a pair of standalone functions because it represents the "hook proxy" concept as a
            cohesive object that can be attached to `config.pluginmanager.hook` as a single unit, matching the duck-
            typing interface expected by the real hook-calling code.

        Delegates:
            - `resolved_catalog.plugins`: The discovered list of formatter plugins; each plugin's
            `pytest_bdd_cucumber_formatter_request` and `pytest_bdd_cucumber_formatter_runtime_assets` methods are
            called in iteration order.

        Cohesion:
            Both methods follow the same pattern (iterate plugins, call the corresponding method, collect non-None/non-
            empty results) and serve the same purpose: simulating the hook broadcast that real pytest plugin
            infrastructure performs. The class has no unrelated methods or state.

        Separation:
            - `FormatterPluginCatalog`: Kept separate because it is the discovery mechanism; this class is the
            delegation proxy that broadcasts hook calls to discovered plugins.
            - `install_formatter_hook_registry`: Kept separate because it is the factory function that creates and
            installs this proxy; the class is a local implementation detail.

        Main consumers:
            - `install_formatter_hook_registry`: Instantiates `_HookProxy()` and assigns it to `config.pluginmanager.hook`.

        State and side effects:
            None, keeps no persistent state beyond the closure over `resolved_catalog`. The class methods are pure
            delegation — they read from the catalog and call plugin methods, but do not mutate the catalog, the plugins,
            or any external state.

        Invariants:
            - Both hook methods must iterate `resolved_catalog.plugins` in the same order to ensure deterministic
            behavior across calls.
            - `pytest_bdd_cucumber_formatter_request` skips plugins whose hook method returns None;
            `pytest_bdd_cucumber_formatter_runtime_assets` skips plugins whose hook method returns falsy — these
            filtering rules must remain consistent with the real plugin manager's behavior.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """

        def pytest_bdd_cucumber_formatter_request(
            self,
            *,
            config: Any,
            resolve_output_path: Any,
        ) -> list[dict[str, str]]:
            """
            `_HookProxy.pytest_bdd_cucumber_formatter_request` — Iterates all plugins in the catalog, collects formatter
            request dicts from each plugin's hook method, filtering out None results.

            Responsibility:
                Iterates over all plugins in the resolved `FormatterPluginCatalog`, calling each plugin's
                `pytest_bdd_cucumber_formatter_request` method with the given `config` and `resolve_output_path`, and
                collects non-None results into a list of formatter request dictionaries. This simulates the first-phase
                hook broadcast that the real gherkin message reporter plugin performs: asking every registered formatter
                plugin what formatter(s) it provides, what CLI flags it uses, and what output path it wants.

            Reason for existence:
                This method exists as the hook-proxy counterpart to the real `pytest_bdd_cucumber_formatter_request`
                hook. Without it, tests that exercise the hook lifecycle would need to manually iterate the plugin
                catalog themselves, duplicating the iteration-and-filter logic. The method also filters out None results
                (plugins that decline to provide a formatter request given the current config), matching the real plugin
                manager's behavior.

            Delegates:
                - `resolved_catalog.plugins`: The list of discovered formatter plugins; each plugin's
                `pytest_bdd_cucumber_formatter_request(config=..., resolve_output_path=...)` is called.
                - Each plugin's `pytest_bdd_cucumber_formatter_request` method: Produces the actual formatter request
                dict (or None if the plugin declines).

            Cohesion:
                Single responsibility: iterate plugins, collect formatter request dicts. No unrelated logic.

            Separation:
                - `pytest_bdd_cucumber_formatter_runtime_assets`: Kept separate because it handles the second-phase hook
                (runtime assets); this method handles the first-phase hook (formatter requests).
                - `install_formatter_hook_registry`: Kept separate because it is the factory function; this method is an
                instance method on the proxy it creates.

            Main consumers:
                - The gherkin message reporter plugin's hook-calling code (when running in-process tests that use
                `install_formatter_hook_registry`).

            State and side effects:
                None, keeps no persistent state. Pure delegation method — does not mutate the catalog, plugins, config,
                or any external state.

            Architecture score:
                #arch-eval:reason_for_existence=3
                #arch-eval:owned_responsibility=3
                #arch-eval:delegation_boundary=3
                #arch-eval:cohesion=4
                #arch-eval:separation=4
                #arch-eval:consumer_clarity=3
                #arch-eval:state_invariants=5
                #arch-eval:entity_fullness=2
                #arch-eval:locational_stability=4
            """
            requests: list[dict[str, str]] = []
            for plugin in resolved_catalog.plugins:
                request = plugin.pytest_bdd_cucumber_formatter_request(
                    config=config,
                    resolve_output_path=resolve_output_path,
                )
                if request is not None:
                    requests.append(request)  # type: ignore[arg-type]  # dynamic CucumberFormatterRequest
            return requests

        def pytest_bdd_cucumber_formatter_runtime_assets(
            self,
            *,
            formatter_request: Any,
            formatter_requests: Any,
        ) -> list[dict[str, str]]:
            """
            `_HookProxy.pytest_bdd_cucumber_formatter_runtime_assets` — Iterates all plugins in the catalog, collects
            rendered runtime asset dicts from each plugin's hook method, filtering out falsy results.

            Responsibility:
                Iterates over all plugins in the resolved `FormatterPluginCatalog`, calling each plugin's
                `pytest_bdd_cucumber_formatter_runtime_assets` method with the given `formatter_request` and
                `formatter_requests`, and collects non-empty results into a list of rendered runtime asset dictionaries.
                This simulates the second-phase hook broadcast where each formatter plugin is asked to produce its
                runtime artifacts (e.g., JavaScript modules, configuration files) needed to execute the formatter in a
                Node.js process.

            Reason for existence:
                This method exists as the hook-proxy counterpart to the real
                `pytest_bdd_cucumber_formatter_runtime_assets` hook. It centralizes the plugin-iteration logic so that
                tests exercising runtime-asset rendering don't need to manually walk the plugin catalog. The method
                filters out falsy results (plugins that have no runtime assets to contribute), matching the real plugin
                manager's behavior where plugins may decline to participate.

            Delegates:
                - `resolved_catalog.plugins`: The list of discovered formatter plugins; each plugin's
                `pytest_bdd_cucumber_formatter_runtime_assets(formatter_request=..., formatter_requests=...)` is called.
                - Each plugin's `pytest_bdd_cucumber_formatter_runtime_assets` method: Produces the rendered asset
                dictionaries (or falsy if the plugin has no assets).

            Cohesion:
                Single responsibility: iterate plugins, collect runtime asset dicts. No unrelated logic.

            Separation:
                - `pytest_bdd_cucumber_formatter_request`: Kept separate because it handles the first-phase hook
                (formatter requests); this method handles the second-phase hook (runtime assets).
                - `install_formatter_hook_registry`: Kept separate because it is the factory function; this method is an
                instance method on the proxy it creates.

            Main consumers:
                - The gherkin message reporter plugin's hook-calling code (when running in-process tests that use
                `install_formatter_hook_registry`).

            State and side effects:
                None, keeps no persistent state. Pure delegation method — does not mutate the catalog, plugins, or any external state.

            Architecture score:
                #arch-eval:reason_for_existence=3
                #arch-eval:owned_responsibility=3
                #arch-eval:delegation_boundary=3
                #arch-eval:cohesion=4
                #arch-eval:separation=4
                #arch-eval:consumer_clarity=3
                #arch-eval:state_invariants=5
                #arch-eval:entity_fullness=2
                #arch-eval:locational_stability=4
            """
            rendered_assets: list[dict[str, str]] = []
            for plugin in resolved_catalog.plugins:
                assets = plugin.pytest_bdd_cucumber_formatter_runtime_assets(
                    formatter_request=formatter_request,
                    formatter_requests=formatter_requests,
                )
                if assets:
                    rendered_assets.append(assets)
            return rendered_assets

    pluginmanager = getattr(config, "pluginmanager", None)
    if pluginmanager is None:
        pluginmanager = SimpleNamespace()
        config.pluginmanager = pluginmanager
    pluginmanager.hook = _HookProxy()
    return pluginmanager


def build_sample_suite(testdir: Any) -> None:
    """
    `pytest_bdd.cucumber_formatters.registry.build_sample_suite` — Creates a minimal test suite inside a pytest testdir
    with one passing and one failing scenario, conftest step definitions, and a test file using scenarios().

    Responsibility:
        Creates a minimal, self-contained test suite inside a pytest `testdir` fixture consisting of: a `pytest.ini`
        that disables feature autoload (preventing the collector from scanning for features outside the testdir), a
        `.feature` file with one passing scenario and one failing scenario, a `conftest.py` with two step definitions
        (`@given("a passing step")` that returns "ok" and `@given("a failing step")` that raises
        `RuntimeError("boom")`), and a `test_formatter_suite.py` that uses `scenarios("formatter_suite.feature")` to
        generate test functions. This is the standard test fixture used by virtually every cucumber formatter
        integration test — it provides a deterministic, two-scenario feature suite that exercises both the passing and
        failing code paths of every formatter.

    Reason for existence:
        This function centralizes the test-suite scaffolding so that every formatter test doesn't need to duplicate the
        same `testdir.makeini`, `testdir.makefile`, `testdir.makeconftest`, and `testdir.makepyfile` calls. If the
        sample suite structure ever needs to change (e.g., adding a scenario with undefined steps, or changing the
        failure exception type), only this function needs updating. The function exists in registry rather than
        rendering because it uses only `testdir` fixture methods (no filesystem I/O beyond what testdir provides) and
        because it is consumed alongside the assertion functions in the same test modules.

    Delegates:
        - `testdir.makeini`: Writes the `pytest.ini` configuration disabling feature autoload.
        - `testdir.makefile`: Creates the `.feature` file with the two scenarios.
        - `testdir.makeconftest`: Creates the `conftest.py` with step definitions.
        - `testdir.makepyfile`: Creates the `test_formatter_suite.py` that uses `scenarios()`.

    Cohesion:
        This function's entire body is a sequence of four testdir fixture calls that together produce a complete,
        runnable test suite. Every line contributes to building that single suite — no unrelated logic.

    Separation:
        - `run_pytest_via_real_entrypoint`: Kept separate because it runs pytest against the suite; this function builds
        the suite.
        - `materialize_fake_node_runtime` (in rendering): Kept separate because it creates fake Node.js runtime
        artifacts; this function creates pytest test files.

    Main consumers:
        - `pytest_bdd_testing.cases.e2e.conftest`: Calls `build_sample_suite` in the e2e conftest fixture setup.
        - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters`: Calls `build_sample_suite` before running
        formatter tests.
        - `pytest_bdd_testing.cases.e2e.e2e.test_cucumber_formatters_feature`: Calls `build_sample_suite` for feature-
        level formatter tests.
        - `pytest_bdd_testing.cases.external.e2e.test_xdist_message_aggregation`: Calls `build_sample_suite` for xdist tests.
        - `pytest_bdd_testing.cases.external.e2e.test_xdist_remote_message_aggregation`: Calls `build_sample_suite` for
        xdist remote tests.

    State and side effects:
        Creates files on disk under `testdir.tmpdir` via the testdir fixture methods. No network I/O, no environment
        mutation, no pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
    testdir.makeini(
        """\
        [pytest]
        disable_feature_autoload = true
        """,
    )
    testdir.makefile(
        ".feature",
        formatter_suite="""\
        Feature: formatter coverage

          Scenario: passing scenario
            Given a passing step

          Scenario: failing scenario
            Given a failing step
        """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given

        @given("a passing step")
        def _pass():
            return "ok"

        @given("a failing step")
        def _fail():
            raise RuntimeError("boom")
        """,
    )
    testdir.makepyfile(
        test_formatter_suite="""\
        from pytest_bdd import scenarios

        test_formatter_suite = scenarios("formatter_suite.feature")
        """,
    )
