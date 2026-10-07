"""Resolve formatter selections with the catalog shared by live and replay runs."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterable
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Any

from attrs import evolve

from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config


class FormatterCatalogError(ValueError):
    """A selected formatter cannot be resolved or run in the current environment."""


def resolve_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Resolve live pytest hook requests through the shared formatter catalog."""
    import pytest  # noqa: PLC0415 -- standalone replay should not import pytest.

    from pytest_cuke.compatibility.pytest import get_config_root_path  # noqa: PLC0415

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

    try:
        return resolve_formatter_catalog(requests, root=get_config_root_path(config), mode="Live")
    except FormatterCatalogError as error:
        raise pytest.UsageError(str(error)) from error


def resolve_replay_formatter_requests(
    selections: Iterable[FormatterSelection],
    *,
    root: Path,
) -> tuple[FormatterRequest, ...]:
    """Load selected formatter factories and resolve them through the shared catalog."""
    selected = tuple(selections)
    if not selected:
        raise FormatterCatalogError("No replay formatter selected; provide at least one --formatter NAME=DESTINATION.")

    available = entry_points(group="pytest_cuke.formatters")
    by_name: dict[str, list[Any]] = {}
    for extension in available:
        by_name.setdefault(extension.name, []).append(extension)

    requests: list[FormatterRequest] = []
    for selection in selected:
        matches = by_name.get(selection.name, [])
        if not matches:
            names = ", ".join(sorted(by_name)) or "none installed"
            raise FormatterCatalogError(
                f"No replay formatter named {selection.name!r} is installed. Available formatters: {names}."
            )
        if len(matches) > 1:
            raise FormatterCatalogError(
                f"Replay formatter name {selection.name!r} is registered by more than one installed distribution."
            )

        try:
            factory = matches[0].load()
        except Exception as error:
            raise FormatterCatalogError(
                f"Could not load replay formatter {selection.name!r}: {type(error).__name__}: {error}"
            ) from error
        if not callable(factory):
            raise FormatterCatalogError(
                f"Replay formatter {selection.name!r} entry point must load a callable factory."
            )
        try:
            request = factory(selection)
        except Exception as error:
            raise FormatterCatalogError(
                f"Could not configure replay formatter {selection.name!r}: {type(error).__name__}: {error}"
            ) from error
        if not isinstance(request, FormatterRequest):
            raise FormatterCatalogError(f"Replay formatter {selection.name!r} factory must return a FormatterRequest.")
        if request.name != selection.name:
            raise FormatterCatalogError(
                f"Replay formatter {selection.name!r} factory returned a request named {request.name!r}."
            )
        requests.append(evolve(request, output_path=selection.destination))

    return resolve_formatter_catalog(requests, root=root, mode="Replay")


def resolve_formatter_catalog(
    requests: Iterable[FormatterRequest],
    *,
    root: Path,
    mode: str,
) -> tuple[FormatterRequest, ...]:
    """Normalize requests and validate names, destinations, and selected runtimes."""
    if mode not in {"Live", "Replay"}:
        raise ValueError(f"unsupported formatter catalog mode: {mode!r}")
    resolved_root = Path(root).resolve()
    normalized: list[FormatterRequest] = []
    names: set[str] = set()
    destinations: dict[str, FormatterRequest] = {}
    terminal_requests: list[FormatterRequest] = []

    for request in sorted(requests, key=lambda item: item.name):
        if request.name in names:
            raise FormatterCatalogError(f"Duplicate {mode.lower()} formatter request name {request.name!r}.")
        names.add(request.name)

        working_directory = request.working_directory
        if working_directory is None:
            working_directory = resolved_root
        elif not working_directory.is_absolute():
            working_directory = resolved_root / working_directory
        working_directory = working_directory.resolve(strict=False)
        if not working_directory.is_dir():
            raise FormatterCatalogError(
                f"{mode} formatter {request.name!r} working directory does not exist: {working_directory}"
            )

        output_path = request.output_path
        if output_path is not None:
            if not output_path.is_absolute():
                output_path = resolved_root / output_path
            output_path = output_path.resolve(strict=False)
            if output_path.exists() and output_path.is_dir():
                raise FormatterCatalogError(
                    f"{mode} formatter {request.name!r} output path is a directory: {output_path}"
                )
            if not output_path.parent.is_dir():
                raise FormatterCatalogError(
                    f"{mode} formatter {request.name!r} output parent directory does not exist: {output_path.parent}"
                )
            destination_key = os.path.normcase(str(output_path))
            previous = destinations.get(destination_key)
            if previous is not None:
                raise FormatterCatalogError(
                    f"{mode} formatters {previous.name!r} and {request.name!r} resolve to the same output path: "
                    f"{output_path}"
                )
            destinations[destination_key] = request
        else:
            terminal_requests.append(request)

        normalized.append(evolve(request, output_path=output_path, working_directory=working_directory))

    if len(terminal_requests) > 1:
        names_text = ", ".join(repr(request.name) for request in terminal_requests)
        raise FormatterCatalogError(
            f"Only one {mode.lower()} formatter may write to the terminal; selected: {names_text}."
        )

    for request in normalized:
        _check_request_runtime(request, mode=mode)

    return tuple(normalized)


def _check_request_runtime(request: FormatterRequest, *, mode: str) -> None:
    required_executables = dict.fromkeys((*request.required_executables, request.command[0]))
    for executable in required_executables:
        if shutil.which(executable) is None:
            raise FormatterCatalogError(
                f"{mode} formatter {request.name!r} requires executable {executable!r}, but it was not found on PATH."
            )

    if not request.required_npm_packages:
        return

    node = shutil.which("node")
    if node is None:
        packages = ", ".join(request.required_npm_packages)
        raise FormatterCatalogError(
            f"{mode} formatter {request.name!r} requires Node.js to load npm package(s): {packages}."
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
            raise FormatterCatalogError(
                f"{mode} formatter {request.name!r} could not check npm package {package!r}: {error}"
            ) from error
        if completed.returncode != 0:
            detail = completed.stderr.strip().splitlines()
            suffix = f" ({detail[-1]})" if detail else ""
            raise FormatterCatalogError(
                f"{mode} formatter {request.name!r} requires npm package {package!r}; install it in "
                f"{request.working_directory} with `npm install {package}`{suffix}."
            )


__all__ = [
    "FormatterCatalogError",
    "resolve_formatter_catalog",
    "resolve_formatter_requests",
    "resolve_replay_formatter_requests",
]
