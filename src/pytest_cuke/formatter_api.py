"""Public extension contracts for live and standalone Cucumber formatter plugins.

Third-party pytest plugins can return :class:`FormatterRequest` instances from
``pytest_cuke_formatter_requests``. The shared runtime owns validation,
process lifetime, Messages delivery, and output routing; formatter plugins own
selection and the command that consumes the Messages NDJSON stream on stdin.
"""

from __future__ import annotations

import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from threading import TIMEOUT_MAX
from typing import Protocol

from attrs import frozen


@frozen
class FormatterAsset:
    """A small runtime file materialized in a formatter's temporary asset directory."""

    path: str
    content: str | bytes

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("Formatter runtime asset path must be non-empty text")
        normalized = self.path.replace("\\", "/")
        asset_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(normalized)
        if (
            not normalized
            or not asset_path.parts
            or asset_path.is_absolute()
            or windows_path.is_absolute()
            or windows_path.drive
            or any(part in {"", ".", ".."} for part in asset_path.parts)
            or any(":" in part for part in asset_path.parts)
        ):
            raise ValueError(f"Formatter runtime asset path must be a safe relative path: {self.path!r}")
        if not isinstance(self.content, (str, bytes)):
            raise ValueError(f"Formatter runtime asset {self.path!r} content must be text or bytes")


@frozen
class FormatterSelection:
    """Describe one formatter selected by the standalone replay command."""

    name: str
    destination: Path | None
    working_directory: Path

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Formatter selection name must not be empty")
        if self.destination is not None and not isinstance(self.destination, Path):
            raise ValueError("Formatter selection destination must be a pathlib.Path or None")
        if not isinstance(self.working_directory, Path):
            raise ValueError("Formatter selection working_directory must be a pathlib.Path")


@frozen
class FormatterRequest:
    """Describe one selected formatter process.

    The child reads one JSON Cucumber Messages envelope per line from stdin,
    both during a live pytest run and when replaying a saved stream.
    It writes either terminal output (``output_path=None``) or a report to
    stdout (``output_path`` set). The runtime stages file output and replaces
    the destination only after a clean process exit.

    A terminal request may set ``bypass_capture`` to write directly to the
    original terminal stream while pytest captures test output. File requests
    cannot bypass capture.

    Command arguments may use ``{asset_dir}`` to refer to the temporary
    directory containing ``runtime_assets``.
    """

    name: str
    command: tuple[str, ...]
    output_path: Path | None = None
    working_directory: Path | None = None
    required_executables: tuple[str, ...] = ()
    required_npm_packages: tuple[str, ...] = ()
    timeout_seconds: float = 10.0
    runtime_assets: tuple[FormatterAsset, ...] = ()
    bypass_capture: bool = False

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Formatter request name must not be empty")
        if (
            not isinstance(self.command, tuple)
            or not self.command
            or any(not isinstance(argument, str) or not argument or "\x00" in argument for argument in self.command)
        ):
            raise ValueError(f"Formatter request {self.name!r} must provide a non-empty argv command")
        try:
            timeout_seconds = float(self.timeout_seconds)
        except (OverflowError, TypeError, ValueError):
            timeout_seconds = math.inf
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
            or timeout_seconds > TIMEOUT_MAX
        ):
            raise ValueError(
                f"Formatter request {self.name!r} timeout_seconds must be positive, finite, "
                f"and no greater than {TIMEOUT_MAX:g} seconds"
            )
        if not isinstance(self.required_executables, tuple) or any(
            not isinstance(executable, str) or not executable.strip() or "\x00" in executable
            for executable in self.required_executables
        ):
            raise ValueError(f"Formatter request {self.name!r} contains an invalid executable name")
        if not isinstance(self.required_npm_packages, tuple) or any(
            not isinstance(package, str) or not package.strip() or "\x00" in package
            for package in self.required_npm_packages
        ):
            raise ValueError(f"Formatter request {self.name!r} contains an invalid npm package name")
        if self.output_path is not None and not isinstance(self.output_path, Path):
            raise ValueError(f"Formatter request {self.name!r} output_path must be a pathlib.Path or None")
        if not isinstance(self.bypass_capture, bool):
            raise ValueError(f"Formatter request {self.name!r} bypass_capture must be a bool")
        if self.bypass_capture and self.output_path is not None:
            raise ValueError(f"Formatter request {self.name!r} can bypass capture only for terminal output")
        if self.working_directory is not None and not isinstance(self.working_directory, Path):
            raise ValueError(f"Formatter request {self.name!r} working_directory must be a pathlib.Path or None")
        if not isinstance(self.runtime_assets, tuple) or any(
            not isinstance(asset, FormatterAsset) for asset in self.runtime_assets
        ):
            raise ValueError(f"Formatter request {self.name!r} runtime_assets must be a tuple of FormatterAsset values")

        asset_paths = [
            os.path.normcase(str(PurePosixPath(asset.path.replace("\\", "/")))) for asset in self.runtime_assets
        ]
        if len(asset_paths) != len(set(asset_paths)):
            raise ValueError(f"Formatter request {self.name!r} contains duplicate runtime asset paths")
        if any("{asset_dir}" in argument for argument in self.command) and not self.runtime_assets:
            raise ValueError(f"Formatter request {self.name!r} uses {{asset_dir}} without runtime assets")


class FormatterRequestFactory(Protocol):
    """Factory loaded from the ``pytest_cuke.formatters`` entry-point group."""

    def __call__(self, selection: FormatterSelection, /) -> FormatterRequest: ...


__all__ = ["FormatterAsset", "FormatterRequest", "FormatterRequestFactory", "FormatterSelection"]
