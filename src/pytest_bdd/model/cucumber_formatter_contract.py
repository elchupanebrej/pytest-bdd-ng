"""
Provide stable cucumber formatter contract types.

These are narrow data-only value types shared across formatter plugins.
No plugin runtime behavior lives here — only frozen request/result descriptors
and the type aliases that accompany them.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from attrs import frozen

from pytest_bdd.compatibility.enum import StrEnum

ResolveOutputPath = Callable[[str], Path]


class FormatterRuntimeKind(StrEnum):
    """Represent formatter runtime kind state."""

    builtin = "builtin"
    module = "module"


@frozen
class CucumberFormatterRequest:
    """Represent cucumber formatter request state."""

    option_attr: str
    cli_flag: str
    formatter: str
    package_name: str
    output_path: Path | None
    plugin_module: str
    runtime_kind: FormatterRuntimeKind
    runtime_specifier: str | None = None
    runtime_module_path: str | None = None
    runtime_export_name: str | None = None
    runtime_template_name: str | None = None
    discovery_order: int = 0


@frozen
class CucumberFormatterRenderResult:
    """Represent cucumber formatter render result state."""

    success: bool
    rendered_formatters: tuple[CucumberFormatterRequest, ...]
    missing_node: bool = False
    missing_packages: tuple[str, ...] = ()
    process_exit_code: int | None = None


@frozen
class NodePackageProvisionResult:
    """Represent node package provision result state."""

    env: dict[str, str]
    missing_packages: tuple[str, ...] = ()
    installed_packages: tuple[str, ...] = ()
    node_modules_roots: tuple[Path, ...] = ()
    missing_node: bool = False
    missing_npm: bool = False
