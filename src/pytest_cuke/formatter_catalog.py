"""Resolve selected live formatter requests before pytest executes tests."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from attrs import evolve

from pytest_cuke.formatter_api import FormatterRequest

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config


def resolve_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return the selected formatter requests in stable order after preflight validation."""
    request_hook = getattr(config.hook, "pytest_cuke_formatter_requests", None)
    hook_results: list[Any] = request_hook(config=config) if request_hook is not None else []
    requests: list[FormatterRequest] = []
    for result in hook_results:
        if result is None:
            continue
        if isinstance(result, FormatterRequest):
            requests.append(result)
            continue
        if isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
            for request in result:
                if not isinstance(request, FormatterRequest):
                    raise pytest.UsageError(
                        "pytest_cuke_formatter_requests implementations must return FormatterRequest objects."
                    )
                requests.append(request)
            continue
        raise pytest.UsageError("pytest_cuke_formatter_requests implementations must return an iterable of requests.")

    if not requests:
        return ()

    root = Path(config.rootpath).resolve()
    normalized: list[FormatterRequest] = []
    names: set[str] = set()
    destinations: dict[str, FormatterRequest] = {}
    terminal_requests: list[FormatterRequest] = []

    for request in sorted(requests, key=lambda item: item.name):
        if request.name in names:
            raise pytest.UsageError(f"Duplicate live formatter request name {request.name!r}.")
        names.add(request.name)

        working_directory = request.working_directory
        if working_directory is None:
            working_directory = root
        elif not working_directory.is_absolute():
            working_directory = root / working_directory
        working_directory = working_directory.resolve(strict=False)
        if not working_directory.is_dir():
            raise pytest.UsageError(
                f"Live formatter {request.name!r} working directory does not exist: {working_directory}"
            )

        output_path = request.output_path
        if output_path is not None:
            if not output_path.is_absolute():
                output_path = root / output_path
            output_path = output_path.resolve(strict=False)
            if output_path.exists() and output_path.is_dir():
                raise pytest.UsageError(
                    f"Live formatter {request.name!r} output path is a directory: {output_path}"
                )
            if not output_path.parent.is_dir():
                raise pytest.UsageError(
                    f"Live formatter {request.name!r} output parent directory does not exist: {output_path.parent}"
                )
            destination_key = os.path.normcase(str(output_path))
            previous = destinations.get(destination_key)
            if previous is not None:
                raise pytest.UsageError(
                    f"Live formatters {previous.name!r} and {request.name!r} resolve to the same output path: "
                    f"{output_path}"
                )
            destinations[destination_key] = request
        else:
            terminal_requests.append(request)

        normalized.append(
            evolve(request, output_path=output_path, working_directory=working_directory),
        )

    if len(terminal_requests) > 1:
        names_text = ", ".join(repr(request.name) for request in terminal_requests)
        raise pytest.UsageError(f"Only one live formatter may write to the terminal; selected: {names_text}.")

    for request in normalized:
        _check_request_runtime(request)

    return tuple(normalized)


def _check_request_runtime(request: FormatterRequest) -> None:
    required_executables = dict.fromkeys((*request.required_executables, request.command[0]))
    for executable in required_executables:
        if shutil.which(executable) is None:
            raise pytest.UsageError(
                f"Live formatter {request.name!r} requires executable {executable!r}, but it was not found on PATH."
            )

    if not request.required_npm_packages:
        return

    node = shutil.which("node")
    if node is None:
        packages = ", ".join(request.required_npm_packages)
        raise pytest.UsageError(
            f"Live formatter {request.name!r} requires Node.js to load npm package(s): {packages}."
        )

    for package in request.required_npm_packages:
        try:
            completed = subprocess.run(  # noqa: S603 -- the fixed Node snippet imports a package selected by the plugin.
                [node, "--input-type=module", "-e", "await import(process.argv[1])", package],
                cwd=request.working_directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise pytest.UsageError(
                f"Live formatter {request.name!r} could not check npm package {package!r}: {error}"
            ) from error
        if completed.returncode != 0:
            detail = completed.stderr.strip().splitlines()
            suffix = f" ({detail[-1]})" if detail else ""
            raise pytest.UsageError(
                f"Live formatter {request.name!r} requires npm package {package!r}; install it in "
                f"{request.working_directory} with `npm install {package}`{suffix}."
            )


__all__ = ["resolve_formatter_requests"]
