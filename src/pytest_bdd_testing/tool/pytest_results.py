"""
`pytest_bdd.pytest_results` owns documented module behavior.

Responsibility:
    Provides utility functions for handling subprocess/pytest test results in the testing
    infrastructure layer. Owns text coercion from captured output objects (coerce_captured_text),
    attachment of subprocess command results as BDD attachments with metadata
    (attach_command_result_outputs), quiet subprocess execution with stdout/stderr capture
    (run_quietly), combined output formatting (combined_result_output), boolean option coercion
    (_coerce_bool_option), and pytest run-mode resolution from ini option dicts
    (resolve_pytester_run_mode). All functions operate on generic object types rather than
    specific framework classes, making this module a bridge between pytest internals, subprocess
    results, and the BDD attachment mechanism.

Reason for existence:
    Testing pytest-bdd itself requires running pytest as a subprocess, capturing its output, and
    attaching diagnostic information to BDD reports. These operations are shared across multiple
    test modules (Docker cluster tests, pytester-based integration tests, message stream tests)
    but do not belong in the core pytest_bdd library because they are test-infrastructure
    concerns, not production features. The module consolidates five related result-processing
    utilities that share a common theme (handling the outputs of executed commands and test
    results) and a common set of imports (contextlib redirect, io.StringIO, typing generics).
    Keeping them here prevents each test module from inventing its own output-attachment or
    bool-coercion helper.

Delegates:
    - coerce_captured_text: Converts arbitrary captured output objects (None, str, objects with
      .str() or .lines attributes) to a plain string.
    - attach_command_result_outputs: Attaches a subprocess result's metadata, stdout, stderr,
      and harness outputs to a BDD report via a caller-supplied `attach` callable.
    - run_quietly: Executes a callable with redirected stdout/stderr, returning the result plus
      captured output strings.
    - combined_result_output: Merges stdout and stderr from a result object into a single string.
    - _coerce_bool_option: Parses a raw pytest option value into a bool using recognized
      true/false string sets; raises ValueError for ambiguous values.
    - resolve_pytester_run_mode: Determines whether pytest should run in "subprocess" or
      "inprocess" mode based on pytester option dict entries, rejecting conflicting settings.

Cohesion:
    All six functions operate on the shared concept of "process/test result output handling."
    coerce_captured_text is called by attach_command_result_outputs and combined_result_output.
    run_quietly produces the harness_outputs tuple consumed by attach_command_result_outputs.
    _coerce_bool_option is called by resolve_pytester_run_mode. No function performs unrelated
    I/O or state management. The module is a focused toolkit, not a grab-bag.

Separation:
    - pytest_bdd_testing.docker / pytest_bdd_testing.docker_cluster: These modules own Docker
      daemon detection and cluster orchestration; they may consume run_quietly or
      attach_command_result_outputs for result reporting but do not implement output processing
      themselves. Keeping result utilities separate prevents the Docker modules from coupling
      to BDD attachment APIs or pytest option-parsing details.
    - pytest_bdd.model.message_validation: Owns message-stream protocol validation;
      pytest_results has no message knowledge and does not import from the model layer.

Main consumers:
    - tests/.../conftest.py (Docker test fixtures): uses run_quietly to capture output when
      executing subprocess commands inside Docker containers, and attach_command_result_outputs
      to attach diagnostics to BDD reports.
    - tests/.../test_*.py (integration tests): uses resolve_pytester_run_mode to determine
      the correct pytester invocation mode from test configuration.

State and side effects:
    Module-level constants: _TRUE_VALUES and _FALSE_VALUES (frozensets of recognized boolean
    string representations). run_quietly writes to StringIO buffers (in-memory, no filesystem).
    attach_command_result_outputs calls the caller-supplied `attach` callable (typically a BDD
    framework attachment function). No pytest stash access. No environment variable reads/writes.
    No network I/O. No subprocess calls.

Invariants:
    - coerce_captured_text always returns a str, never None or bytes.
    - run_quietly always returns a 3-tuple of (result, stdout_str, stderr_str) where the
      string components are guaranteed to be str (StringIO.getvalue() returns str).
    - _coerce_bool_option raises ValueError for any input that is not a bool or recognized
      true/false string; it never silently returns an arbitrary value.
    - resolve_pytester_run_mode returns exactly "subprocess" or "inprocess"; it never
      returns None or any other string.

Failure semantics:
    _coerce_bool_option raises ValueError with the option name and raw value when the input
    is not a recognized truthy/falsy string. resolve_pytester_run_mode raises ValueError
    when both "subprocess" and "inprocess" options are present with conflicting truth values.
    No other function in this module raises exceptions.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING, ParamSpec, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

P = ParamSpec("P")
R = TypeVar("R")

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def coerce_captured_text(stream: object) -> str:
    r"""
    `pytest_bdd.pytest_results.coerce_captured_text` owns documented function behavior.

    Responsibility:
        Converts a captured output object from subprocess or pytest into a plain string,
        handling all common representations: None → "", str → identity, objects with a
        callable .str() method (pytest CaptureResult) → str(result.str()), objects with a
        .lines list attribute (pytest legacy capture) → "\n".join(lines), and any other
        object → str(stream). Always returns a str, never None or raises.

    Reason for existence:
        Subprocess results (subprocess.CompletedProcess) and pytest test reports store captured
        output in different shapes: sometimes a plain string, sometimes an object with .stdout
        returning a CaptureResult that has .str() and .lines attributes. This function is the
        single normalization point — callers pass in result.stdout or result.stderr without
        needing to know which capture backend produced it. It is extracted from
        attach_command_result_outputs and combined_result_output because both need the same
        coercion logic and inlining it would duplicate the isinstance/getattr chain.

    Delegates:
        - getattr: Retrieves .str and .lines attributes from the stream object for duck-typing.
        - callable: Checks whether .str is a callable method.
        - str: Fallback conversion for unrecognized types.

    Cohesion:
        The function handles exactly one concern: polymorphic text extraction from captured
        output objects. Every branch handles a different capture representation, all converging
        on the same return type (str). No unrelated logic.

    Separation:
        - attach_command_result_outputs: Uses coerce_captured_text to normalize stdout/stderr
          before attaching; separation keeps the attach function focused on BDD attachment
          mechanics.
        - combined_result_output: Also uses coerce_captured_text for the same normalization.

    Main consumers:
        - pytest_bdd_testing.pytest_results.attach_command_result_outputs: calls
          coerce_captured_text(getattr(result, "stdout", None)) and similarly for stderr.
        - pytest_bdd_testing.pytest_results.combined_result_output: calls
          coerce_captured_text for both stdout and stderr.

    State and side effects:
        None — pure function. No filesystem, environment, subprocess, or pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    if stream is None:
        return ""
    if isinstance(stream, str):
        return stream
    str_method = getattr(stream, "str", None)
    if callable(str_method):
        return str(str_method())
    lines = getattr(stream, "lines", None)
    if isinstance(lines, list):
        return "\n".join(lines)
    return str(stream)


def attach_command_result_outputs(
    attach: Callable[..., object],
    result: object,
    *,
    label: str,
    command: str | None = None,
    harness_outputs: tuple[str, str] = ("", ""),
) -> None:
    # Nested pytest/docker helper runs are harness diagnostics, not user-facing terminal
    # reporting. Keep them as attachments so the active cucumber formatter remains the
    # only writer to stdout/stderr during the outer test session.
    """
    `pytest_bdd.pytest_results.attach_command_result_outputs` owns documented function behavior.

    Responsibility:
        Attaches the stdout, stderr, return code, and optional harness outputs of a subprocess
        or test result object to a BDD report via a caller-supplied `attach` callable. Creates
        a metadata attachment with label, command, and return_code; then attaches stdout, stderr,
        harness stdout, and harness stderr as separate text/plain attachments, each named with a
        `{label}.{stream}.txt` convention. Uses coerce_captured_text to normalize output objects.
        All attachments use media_type "text/plain;charset=UTF-8".

    Reason for existence:
        When pytest-bdd tests run nested pytest or Docker commands as subprocesses, the output
        must be captured and attached to the BDD report for debugging without being printed to
        the outer test session's stdout/stderr (which would interfere with the active Cucumber
        formatter). This function standardizes the attachment pattern — metadata + stdout +
        stderr + harness streams — so that every test that runs a subprocess can produce
        consistent, searchable diagnostic attachments. The `attach` callable is injected rather
        than imported to avoid coupling this module to any specific BDD framework's attachment API.

    Delegates:
        - coerce_captured_text: Normalizes stdout/stderr objects to plain strings.
        - getattr: Retrieves returncode or ret from the result object.
        - attach (caller-supplied): The BDD framework's attachment function (e.g., pytest-bdd's
          scenario attachment mechanism).

    Cohesion:
        The function does one thing: serialize a command result into multiple attachments. The
        metadata, stdout, stderr, and harness output sections are all aspects of the same result
        object. No unrelated formatting or processing.

    Separation:
        - run_quietly: Produces the harness_outputs tuple that attach_command_result_outputs
          consumes; they work together but are separate because quiet execution and attachment
          are independent concerns.
        - coerce_captured_text: Handles output normalization; attach_command_result_outputs
          handles the attachment structure and naming.

    Main consumers:
        - tests/.../conftest.py (Docker test fixtures): calls attach_command_result_outputs
          after running subprocess commands inside Docker containers to attach diagnostic
          output to BDD scenario reports.
        - Any test that runs a subprocess and needs to attach its output to a BDD report.

    State and side effects:
        Calls the caller-supplied `attach` function multiple times (up to 5 calls per invocation
        for metadata, stdout, stderr, harness_stdout, harness_stderr). The side effects of
        `attach` depend on the caller's framework. No direct filesystem, environment, subprocess,
        or pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    metadata_lines = [f"label: {label}"]
    if command:
        metadata_lines.append(f"command: {command}")

    return_code = getattr(result, "returncode", getattr(result, "ret", None))
    if return_code is not None:
        metadata_lines.append(f"return_code: {return_code}")

    attach(
        "\n".join(metadata_lines) + "\n",
        media_type="text/plain;charset=UTF-8",
        file_name=f"{label}.meta.txt",
    )

    stdout = coerce_captured_text(getattr(result, "stdout", None))
    if stdout:
        attach(
            stdout,
            media_type="text/plain;charset=UTF-8",
            file_name=f"{label}.stdout.txt",
        )

    stderr = coerce_captured_text(getattr(result, "stderr", None))
    if stderr:
        attach(
            stderr,
            media_type="text/plain;charset=UTF-8",
            file_name=f"{label}.stderr.txt",
        )

    harness_stdout, harness_stderr = harness_outputs
    if harness_stdout:
        attach(
            harness_stdout,
            media_type="text/plain;charset=UTF-8",
            file_name=f"{label}.harness.stdout.txt",
        )

    if harness_stderr:
        attach(
            harness_stderr,
            media_type="text/plain;charset=UTF-8",
            file_name=f"{label}.harness.stderr.txt",
        )


def run_quietly(command: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs) -> tuple[R, str, str]:
    """
    `pytest_bdd.pytest_results.run_quietly` owns documented function behavior.

    Responsibility:
        Executes a callable with stdout and stderr redirected to StringIO buffers, capturing
        all console output that would normally go to the terminal. Returns a 3-tuple of
        (result: R, stdout: str, stderr: str) where result is the return value of the callable
        and the strings contain the captured output. Uses contextlib.redirect_stdout and
        redirect_stderr context managers. The callable receives *args and **kwargs forwarded
        from the function's variadic parameters via ParamSpec and TypeVar generics.

    Reason for existence:
        When pytest-bdd tests run nested pytest sessions (e.g., via pytester or subprocess),
        the inner session's output would pollute the outer session's console, breaking Cucumber
        formatter output. This function provides a clean capture mechanism: the inner command
        runs silently, and its output is returned as strings that can be attached to the BDD
        report or asserted on. The use of ParamSpec and TypeVar preserves the callable's full
        type signature through the wrapper. It is kept separate from attach_command_result_outputs
        because quiet execution and attachment are orthogonal — a caller may want to capture
        output without attaching it, or attach output from a non-quiet source.

    Delegates:
        - contextlib.redirect_stdout / redirect_stderr: Redirect sys.stdout and sys.stderr
          to StringIO buffers for the duration of the callable execution.
        - io.StringIO: In-memory text buffers for capturing output.

    Cohesion:
        The function has one responsibility: silently execute a callable and return its output.
        The stdout/stderr redirection and buffer retrieval are all part of this single capture
        pattern. No result parsing, attachment, or assertion logic.

    Separation:
        - attach_command_result_outputs: Consumes the harness_outputs tuple from run_quietly
          to attach harness diagnostic output. The split keeps capture mechanics separate
          from BDD attachment formatting.
        - subprocess.run (stdlib): run_quietly wraps Python callables; subprocess.run wraps
          external processes. They serve different use cases but both need output capture.

    Main consumers:
        - tests/.../conftest.py (Docker test fixtures): wraps Docker cluster setup/teardown
          code in run_quietly to prevent Docker Compose output from corrupting the Cucumber
          formatter display, then passes the captured output to attach_command_result_outputs.

    State and side effects:
        Modifies sys.stdout and sys.stderr temporarily via contextlib redirect managers. The
        StringIO buffers are ephemeral (created and discarded per call). No filesystem,
        environment, subprocess, or pytest stash access. The function itself is stateless
        between calls.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = command(*args, **kwargs)
    return result, stdout_buffer.getvalue(), stderr_buffer.getvalue()


def combined_result_output(result: object) -> str:
    r"""
    `pytest_bdd.pytest_results.combined_result_output` owns documented function behavior.

    Responsibility:
        Merges the stdout and stderr of a result object into a single newline-joined string,
        omitting empty streams. Uses coerce_captured_text for normalization and getattr for
        attribute access on the result object. Returns a single string suitable for assertion
        messages or error reporting. If both stdout and stderr are empty/None, returns an
        empty string (from "\n".join([])).

    Reason for existence:
        When a subprocess command fails, test assertions often need to check that the combined
        output contains a specific error message. This function provides a one-call convenience
        over separately coercing stdout and stderr and joining them. It is separate from
        attach_command_result_outputs because attachments need streams separated (for
        organizational clarity), while error assertions need them combined (for grep-friendly
        searching).

    Delegates:
        - coerce_captured_text: Normalizes stdout and stderr to plain strings.
        - getattr: Retrieves stdout and stderr attributes from the result object.

    Cohesion:
        The function does exactly one string-combining operation with two inputs. Its brevity
        is proportional to its focused scope.

    Separation:
        - attach_command_result_outputs: Attaches streams separately for BDD reports;
          combined_result_output merges them for assertions. They serve different consumers
          but share coerce_captured_text.

    Main consumers:
        - Test assertion helpers that need to search combined subprocess output for expected
          strings (e.g., checking that `docker compose up` output contains an error message).

    State and side effects:
        None — pure function. No filesystem, environment, subprocess, or pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=2
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    stdout = coerce_captured_text(getattr(result, "stdout", None))
    stderr = coerce_captured_text(getattr(result, "stderr", None))
    return "\n".join(part for part in (stdout, stderr) if part)


def _coerce_bool_option(raw_value: object, *, option_name: str) -> bool:
    """
    `pytest_bdd.pytest_results._coerce_bool_option` owns documented function behavior.

    Responsibility:
        Converts a raw pytest option value (which may be a bool, string, or any object with a
        string representation) into a Python bool using recognized truthy/falsy value sets.
        Accepts bool passthrough, then normalizes via str().strip().lower() and checks against
        _TRUE_VALUES ({"1", "true", "yes", "on"}) and _FALSE_VALUES ({"0", "false", "no", "off"}).
        Raises ValueError with the option name and raw value if the input matches neither set.

    Reason for existence:
        Pytest pytester options arrive as lists of arbitrary objects (e.g., ["true"], ["1"]).
        This function provides a single, auditable truth table for boolean coercion, preventing
        each caller from inventing its own interpretation of what "true" means. The explicit
        ValueError with the option_name ensures that configuration errors (e.g., misspelled
        "ture" or "tru") fail loudly with a diagnostic message instead of silently defaulting
        to False. The frozenset module-level constants (_TRUE_VALUES, _FALSE_VALUES) make the
        accepted values immutable and importable.

    Delegates:
        - _TRUE_VALUES / _FALSE_VALUES (module-level frozensets): Define the recognized boolean
          string representations.

    Cohesion:
        The function does exactly one thing: parse a value into bool or raise. All logic
        (isinstance check, str normalization, set membership tests, error construction) serves
        that single purpose. No side effects or unrelated validation.

    Separation:
        - resolve_pytester_run_mode: The sole consumer; _coerce_bool_option is private (leading
          underscore) and exists only to support resolve_pytester_run_mode's option parsing.
          Keeping it separate makes the bool-coercion logic independently testable.

    Main consumers:
        - pytest_bdd_testing.pytest_results.resolve_pytester_run_mode: calls _coerce_bool_option
          to interpret the "subprocess" and "inprocess" option values from the pytester options dict.

    State and side effects:
        None — pure function. Reads _TRUE_VALUES and _FALSE_VALUES constants. No filesystem,
        environment, subprocess, or pytest stash access.

    Failure semantics:
        Raises ValueError(f"Invalid boolean value for {option_name!r}: {raw_value!r}") when the
        normalized value matches neither the true nor false sets. The caller
        (resolve_pytester_run_mode) propagates this to the test framework, which should treat it
        as a configuration error.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    if isinstance(raw_value, bool):
        return raw_value
    normalized = str(raw_value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    msg = f"Invalid boolean value for {option_name!r}: {raw_value!r}"
    raise ValueError(msg)


def resolve_pytester_run_mode(options_dict: dict[str, list[object]]) -> str:
    """
    `pytest_bdd.pytest_results.resolve_pytester_run_mode` owns documented function behavior.

    Responsibility:
        Determines whether pytest should run tests in "subprocess" or "inprocess" mode based
        on a pytester options dictionary (mapping option names to lists of raw values). Reads
        the "subprocess" and "inprocess" keys: if "subprocess" is True, adds "subprocess" to
        the mode set; if "inprocess" is True, adds "inprocess". Raises ValueError if both modes
        are requested simultaneously (conflicting options). Defaults to "subprocess" if neither
        option is present. Returns exactly "subprocess" or "inprocess".

    Reason for existence:
        Pytester (pytest's testdir fixture) can run tests either in the same process (inprocess)
        or in a subprocess. The test configuration may specify either or both options, and the
        boolean values are passed as list elements that need coercion. This function centralizes
        the option resolution logic — reading two keys, coercing their values, checking for
        conflicts, and providing a default — so that test fixtures don't each implement their
        own (potentially inconsistent) mode resolution. The explicit conflict detection (both
        modes True) prevents silently ambiguous configurations.

    Delegates:
        - _coerce_bool_option: Normalizes the raw option values ("true"/"1"/"yes"/"on" etc.)
          into Python bools with proper error messages.
        - dict.get: Accesses the options dictionary with default empty lists.

    Cohesion:
        The function handles one decision: "subprocess" or "inprocess"? All logic — option
        reading, coercion, conflict detection, defaulting — converges on that single output.
        No unrelated configuration parsing.

    Separation:
        - _coerce_bool_option: Handles the low-level string-to-bool conversion; this function
          handles the higher-level option resolution logic. The split keeps boolean parsing
          testable independently of the pytester dict structure.

    Main consumers:
        - tests/.../conftest.py (pytester-based test fixtures): calls resolve_pytester_run_mode
          to determine the correct run mode for testdir-based integration tests.

    State and side effects:
        None — pure function operating on the input dict. No filesystem, environment, subprocess,
        or pytest stash access.

    Failure semantics:
        Raises ValueError("Conflicting pytest invocation mode options: 'subprocess' and
        'inprocess'") when both options are present and evaluate to True. Also propagates
        ValueError from _coerce_bool_option if an option value is unrecognized.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    requested_modes: set[str] = set()

    if options_dict.get("subprocess"):
        requested_modes.add(
            "subprocess"
            if _coerce_bool_option(options_dict["subprocess"][0], option_name="subprocess")
            else "inprocess",
        )
    if options_dict.get("inprocess"):
        requested_modes.add(
            "inprocess" if _coerce_bool_option(options_dict["inprocess"][0], option_name="inprocess") else "subprocess",
        )

    if len(requested_modes) > 1:
        msg = "Conflicting pytest invocation mode options: 'subprocess' and 'inprocess'"
        raise ValueError(msg)
    if not requested_modes:
        return "subprocess"
    return requested_modes.pop()
