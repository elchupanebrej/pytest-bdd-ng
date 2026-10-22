"""Resolve formatter selections with the catalog shared by live and replay runs."""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from collections.abc import Iterable
from contextlib import suppress
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Any

from attrs import evolve

from pytest_cuke.cucumber_json import configured_cucumber_json_backend, configured_cucumber_json_output_path
from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config


class FormatterCatalogError(ValueError):
    """A selected formatter cannot be resolved or run in the current environment."""


_OUTPUT_PROBE_MAX_ATTEMPTS = 8
_NODE_PACKAGE_PREFLIGHT_SCRIPT = """
import { stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const resolved = import.meta.resolve(process.argv[1]);
if (!resolved.startsWith("file:")) {
  throw new Error(`npm package resolved to a non-file URL: ${resolved}`);
}

const entry = await stat(fileURLToPath(resolved));
if (!entry.isFile()) {
  throw new Error(`npm package entry is not a file: ${resolved}`);
}
""".strip()


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
        return resolve_formatter_catalog(
            requests,
            root=get_config_root_path(config),
            mode="Live",
            reserved_output_paths=_configured_live_output_paths(config),
        )
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
    reserved_output_paths: Iterable[tuple[str, Path]] = (),
) -> tuple[FormatterRequest, ...]:
    """Normalize requests and validate names, destinations, and selected runtimes."""
    if mode not in {"Live", "Replay"}:
        raise ValueError(f"unsupported formatter catalog mode: {mode!r}")
    resolved_root = Path(root).resolve()
    normalized: list[FormatterRequest] = []
    names: set[str] = set()
    destinations: dict[str, FormatterRequest] = {}
    reserved_destinations: dict[str, tuple[str, Path]] = {}
    normalized_reserved_outputs: list[tuple[str, Path]] = []
    terminal_requests: list[FormatterRequest] = []

    for name, path in reserved_output_paths:
        normalized_output_path = path if path.is_absolute() else resolved_root / path
        resolved_output_path = normalized_output_path.resolve(strict=False)
        destination_key = os.path.normcase(str(resolved_output_path))
        previous_reserved = reserved_destinations.get(destination_key)
        if previous_reserved is not None:
            previous_name, _ = previous_reserved
            raise FormatterCatalogError(
                f"{mode} output destinations {previous_name} and {name} resolve to the same output path: "
                f"{resolved_output_path}. Choose a distinct path for each report."
            )
        reserved_destinations[destination_key] = (name, resolved_output_path)
        normalized_reserved_outputs.append((name, resolved_output_path))

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
            destination_key = os.path.normcase(str(output_path))
            reserved_destination = reserved_destinations.get(destination_key)
            if reserved_destination is not None:
                reserved_name, _ = reserved_destination
                raise FormatterCatalogError(
                    f"{mode} formatter {_display_formatter_name(request.name)} and {reserved_name} "
                    f"resolve to the same output path: "
                    f"{output_path}. Choose a different destination for each report."
                )
            if output_path.exists() and output_path.is_dir():
                raise FormatterCatalogError(
                    f"{mode} formatter {request.name!r} output path is a directory: {output_path}"
                )
            if not output_path.parent.is_dir():
                raise FormatterCatalogError(
                    f"{mode} formatter {request.name!r} output parent directory does not exist: {output_path.parent}"
                )
            previous_request = destinations.get(destination_key)
            if previous_request is not None:
                formatter_names = f"{previous_request.name!r} and {request.name!r}"
                raise FormatterCatalogError(
                    f"{mode} formatters {formatter_names} resolve to the same output path: {output_path}"
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

    for name, output_path in normalized_reserved_outputs:
        _check_output_destination_writable(
            output_path,
            name=f"output {name}",
            mode=mode,
            directory_output=name == "--cuke-allure",
        )
    for request in normalized:
        if request.output_path is not None:
            _check_output_destination_writable(
                request.output_path,
                name=f"formatter {_display_formatter_name(request.name)} output",
                mode=mode,
            )

    for request in normalized:
        _check_request_runtime(request, mode=mode)

    return tuple(normalized)


def _display_formatter_name(name: str) -> str:
    """Show the public selector alongside a built-in formatter's internal name."""
    if name == "cucumber-json":
        return "'cucumber-json' (--cuke-json)"
    return repr(name)


def _configured_live_output_paths(config: Config) -> tuple[tuple[str, Path], ...]:
    """Resolve selected built-in report paths using each writer's path rules."""
    output_paths: list[tuple[str, Path]] = []
    cucumber_json_path = configured_cucumber_json_output_path(config)
    if cucumber_json_path is not None and configured_cucumber_json_backend(config) == "native":
        output_paths.append(("--cuke-json", cucumber_json_path))

    for option, label, expand in (
        ("cuke_messages_ndjson", "--cuke-messages-ndjson", False),
        ("cuke_html", "--cuke-html", False),
        ("cuke_allure", "--cuke-allure", True),
    ):
        output = _configured_output_option(config, option)
        if output is not None:
            output_paths.append((label, _canonical_output_path(output, expand=expand)))

    junitxml_path = getattr(getattr(config, "option", None), "xmlpath", None)
    if isinstance(junitxml_path, str) and junitxml_path:
        output_paths.append(("--junitxml", _canonical_output_path(junitxml_path, expand=True)))

    return tuple(output_paths)


def _configured_output_option(config: Config, name: str) -> str | None:
    """Read a plugin output option using its CLI-over-ini precedence."""
    option = getattr(getattr(config, "option", None), name, None)
    if isinstance(option, str):
        return option
    getini = getattr(config, "getini", None)
    ini_value = getini(name) if callable(getini) else None
    return ini_value if isinstance(ini_value, str) and ini_value else None


def _canonical_output_path(output: str, *, expand: bool) -> Path:
    if expand:
        output = os.path.expanduser(os.path.expandvars(output))
    return Path(output).resolve(strict=False)


def _check_output_destination_writable(
    output_path: Path,
    *,
    name: str,
    mode: str,
    directory_output: bool = False,
) -> None:
    """Probe output permissions without changing an existing report."""
    if directory_output and output_path.exists() and not output_path.is_dir():
        raise FormatterCatalogError(
            f"cannot initialize native Allure reporting: {name} path {output_path} already exists as a file"
        )
    if not directory_output and output_path.is_dir():
        raise FormatterCatalogError(f"{mode} {name} path is a directory: {output_path}")
    output_directory = output_path if directory_output and output_path.is_dir() else output_path.parent
    if not output_directory.is_dir():
        raise FormatterCatalogError(
            f"{mode} {name} parent directory does not exist: {output_directory}"
        )
    file_descriptor: int | None = None
    probe_path: Path | None = None
    try:
        probe_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        for _ in range(_OUTPUT_PROBE_MAX_ATTEMPTS):
            probe_path = output_directory / f".pytest-cuke-output-probe-{uuid.uuid4().hex}"
            try:
                file_descriptor = os.open(probe_path, probe_flags, 0o600)
            except FileExistsError:
                probe_path = None
                continue
            break
        if file_descriptor is None or probe_path is None:
            raise FileExistsError("could not reserve a unique output writability probe file")
        os.close(file_descriptor)
        file_descriptor = None
        probe_path.unlink()
        probe_path = None
    except OSError as error:
        if file_descriptor is not None:
            with suppress(OSError):
                os.close(file_descriptor)
        if probe_path is not None:
            with suppress(OSError):
                probe_path.unlink(missing_ok=True)
        raise FormatterCatalogError(
            f"{mode} {name} directory is not writable: {output_directory} "
            f"({type(error).__name__}: {error})"
        ) from error

    if not directory_output and output_path.is_file():
        file_descriptor = None
        try:
            file_descriptor = os.open(output_path, os.O_WRONLY | getattr(os, "O_BINARY", 0))
            os.close(file_descriptor)
            file_descriptor = None
        except OSError as error:
            if file_descriptor is not None:
                with suppress(OSError):
                    os.close(file_descriptor)
            raise FormatterCatalogError(
                f"{mode} {name} file is not writable: {output_path} ({type(error).__name__}: {error})"
            ) from error


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
            completed = subprocess.run(  # noqa: S603 -- Node resolves a package selected by formatter metadata.
                [node, "--input-type=module", "-e", _NODE_PACKAGE_PREFLIGHT_SCRIPT, package],
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
