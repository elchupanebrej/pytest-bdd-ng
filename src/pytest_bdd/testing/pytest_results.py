"""Provide pytest results helpers."""

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
    """
    Handle coerce captured text.

    Returns:
        Captured text as a plain string.

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
    """Handle attach command result outputs."""
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
    Run quietly.

    Returns:
        Command result, captured stdout, and captured stderr.

    """
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = command(*args, **kwargs)
    return result, stdout_buffer.getvalue(), stderr_buffer.getvalue()


def combined_result_output(result: object) -> str:
    """
    Handle combined result output.

    Returns:
        Combined stdout and stderr text.

    """
    stdout = coerce_captured_text(getattr(result, "stdout", None))
    stderr = coerce_captured_text(getattr(result, "stderr", None))
    return "\n".join(part for part in (stdout, stderr) if part)


def _coerce_bool_option(raw_value: object, *, option_name: str) -> bool:
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
    Resolve pytester run mode.

    Returns:
        Selected pytester run mode.

    Raises:
        ValueError: If the operation cannot be completed.

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
