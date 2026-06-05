"""Provide session helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.model.cucumber_formatter_contract import (
    CucumberFormatterRenderResult,
    CucumberFormatterRequest,
    FormatterRuntimeKind,
    NodePackageProvisionResult,
    ResolveOutputPath,
)
from pytest_bdd.util.cucumber_formatter_support.base import (
    load_formatter_adapter_support_template as _load_formatter_adapter_support_template,
)
from pytest_bdd.util.cucumber_formatter_support.base import (
    load_formatter_adapter_template as _load_formatter_adapter_template,
)

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable

    from pytest_bdd.compatibility.pytest import Config, PytestPluginManager

# Re-export contract types for backward compatibility within the same plugin package.
__all__ = [
    "CucumberFormatterConfigurationError",
    "CucumberFormatterRenderResult",
    "CucumberFormatterRequest",
    "FormatterRuntimeKind",
    "NodePackageProvisionResult",
    "ResolveOutputPath",
]


class _FormatterRequestHook(Protocol):
    def pytest_bdd_cucumber_formatter_request(
        self,
        *,
        config: Config,
        resolve_output_path: ResolveOutputPath,
    ) -> tuple[CucumberFormatterRequest, ...]: ...


class _FormatterRuntimeAssetsHook(Protocol):
    def pytest_bdd_cucumber_formatter_runtime_assets(
        self,
        *,
        formatter_request: CucumberFormatterRequest,
        formatter_requests: tuple[CucumberFormatterRequest, ...],
    ) -> tuple[dict[str, str] | None, ...]: ...


class CucumberFormatterConfigurationError(ValueError):
    """Raised when the requested cucumber formatter configuration is invalid."""

    @classmethod
    def duplicate_output_path(
        cls,
        *,
        formatter_labels: str,
        output_path: Path,
    ) -> CucumberFormatterConfigurationError:
        """
        Create error for duplicate output path.

        Returns:
            Configuration error.

        """
        message = f"Multiple formatter outputs target the same path {output_path}: {formatter_labels}"
        return cls(message)

    @classmethod
    def missing_output_directory(
        cls,
        *,
        cli_flag: str,
        output_dir: Path,
    ) -> CucumberFormatterConfigurationError:
        """
        Create error for missing output directory.

        Returns:
            Configuration error.

        """
        message = f"Formatter output directory does not exist for {cli_flag}: {output_dir}"
        return cls(message)

    @classmethod
    def terminal_output_conflict(
        cls,
        *,
        formatter_labels: str,
    ) -> CucumberFormatterConfigurationError:
        """
        Create error for terminal output conflict.

        Returns:
            Configuration error.

        """
        message = f"Only one terminal-output formatter may be active per run: {formatter_labels}"
        return cls(message)


def format_requested_cucumber_formatter_labels(
    formatter_requests: tuple[CucumberFormatterRequest, ...] | list[CucumberFormatterRequest],
) -> str:
    """
    Format requested cucumber formatter labels.

    Returns:
        Comma-separated formatter labels.

    """
    return ", ".join(request.cli_flag for request in formatter_requests)


def terminal_output_formatter_requests(
    formatter_requests: list[CucumberFormatterRequest],
) -> list[CucumberFormatterRequest]:
    """
    Filter terminal output formatter requests.

    Returns:
        List of terminal output formatter requests.

    """
    return [request for request in formatter_requests if request.output_path is None]


def normalize_cucumber_formatter_output_key(output_path: Path) -> str:
    """
    Normalize cucumber formatter output key.

    Returns:
        Normalized output path string.

    """
    return os.path.normcase(str(output_path.resolve()))


def _read_template_asset(package: str, template_name: str) -> str:
    template = cast("Traversable", files(package).joinpath(template_name))
    return template.read_text(encoding="utf-8")


def _formatter_options_requested(config: Config) -> bool:
    option_values = cast("dict[str, object]", getattr(getattr(config, "option", None), "__dict__", {}))
    return any(
        option_name.startswith("cucumber_")
        and option_name != "cucumber_html_path"
        and option_value not in {None, False}
        for option_name, option_value in option_values.items()
    )


def _formatter_hook_proxy(pluginmanager: PytestPluginManager | None) -> object | None:
    return getattr(pluginmanager, "hook", None)


def _resolve_formatter_request_hook(config: Config) -> _FormatterRequestHook | None:
    hook = _formatter_hook_proxy(getattr(config, "pluginmanager", None))
    if hook is None or not hasattr(hook, "pytest_bdd_cucumber_formatter_request"):
        if _formatter_options_requested(config):
            msg = (
                "Cucumber formatter plugins are unavailable because the formatter request hook registry "
                "was not configured."
            )
            raise RuntimeError(msg)
        return None
    return cast("_FormatterRequestHook", hook)


def _require_formatter_runtime_assets_hook(pluginmanager: PytestPluginManager | None) -> _FormatterRuntimeAssetsHook:
    hook = _formatter_hook_proxy(pluginmanager)
    if hook is None or not hasattr(hook, "pytest_bdd_cucumber_formatter_runtime_assets"):
        msg = (
            "Cucumber formatter runtime assets are unavailable because the formatter runtime-assets hook registry "
            "was not configured."
        )
        raise RuntimeError(msg)
    return cast("_FormatterRuntimeAssetsHook", hook)


def resolve_requested_cucumber_formatters(
    config: Config,
    *,
    resolve_output_path: ResolveOutputPath,
) -> tuple[CucumberFormatterRequest, ...]:
    """
    Resolve requested cucumber formatters.

    Returns:
        Tuple of cucumber formatter requests.

    """
    requested_formatters: list[CucumberFormatterRequest] = []
    formatter_request_hook = _resolve_formatter_request_hook(config)
    if formatter_request_hook is not None:
        requested_formatters.extend(
            formatter_request
            for formatter_request in formatter_request_hook.pytest_bdd_cucumber_formatter_request(
                config=config,
                resolve_output_path=resolve_output_path,
            )
            if formatter_request is not None
        )
    requested_formatters = _order_requested_cucumber_formatters(requested_formatters)
    validate_requested_cucumber_formatters(requested_formatters)
    return tuple(requested_formatters)


def _order_requested_cucumber_formatters(
    requested_formatters: list[CucumberFormatterRequest],
) -> list[CucumberFormatterRequest]:
    return sorted(
        requested_formatters,
        key=lambda formatter_request: (
            formatter_request.discovery_order,
            formatter_request.formatter,
            formatter_request.plugin_module,
        ),
    )


def validate_requested_cucumber_formatters(
    formatter_requests: list[CucumberFormatterRequest],
) -> None:
    """
    Validate requested cucumber formatters.

    Raises:
        terminal_output_conflict: If the operation cannot be completed.
        duplicate_output_path: If the operation cannot be completed.
        missing_output_directory: If the operation cannot be completed.

    """
    terminal_requests = terminal_output_formatter_requests(formatter_requests)
    if len(terminal_requests) > 1:
        raise CucumberFormatterConfigurationError.terminal_output_conflict(
            formatter_labels=format_requested_cucumber_formatter_labels(terminal_requests),
        )

    requests_by_output_key: dict[str, list[CucumberFormatterRequest]] = {}
    for formatter_request in formatter_requests:
        output_path = formatter_request.output_path
        if output_path is None:
            continue
        if not output_path.parent.exists():
            raise CucumberFormatterConfigurationError.missing_output_directory(
                cli_flag=formatter_request.cli_flag,
                output_dir=output_path.parent,
            )
        requests_by_output_key.setdefault(normalize_cucumber_formatter_output_key(output_path), []).append(
            formatter_request,
        )

    duplicate_requests = next(
        (request_group for request_group in requests_by_output_key.values() if len(request_group) > 1),
        None,
    )
    if duplicate_requests is not None:
        duplicate_output_path = duplicate_requests[0].output_path or Path("<terminal>")
        raise CucumberFormatterConfigurationError.duplicate_output_path(
            output_path=duplicate_output_path,
            formatter_labels=format_requested_cucumber_formatter_labels(duplicate_requests),
        )


def load_live_formatter_bridge_template() -> str:
    """
    Load live formatter bridge template.

    Returns:
        Template content.

    """
    return _read_template_asset(
        "pytest_bdd.plugin.gherkin_message_reporter.resources.templates",
        "live_formatter_bridge.mjs.j2",
    )


def load_formatter_adapter_support_template() -> str:
    """
    Load formatter adapter support template.

    Returns:
        Template content.

    """
    return cast("str", _load_formatter_adapter_support_template())


def load_formatter_adapter_template(template_name: str) -> str:
    """
    Load formatter adapter template.

    Returns:
        Template content.

    """
    return cast("str", _load_formatter_adapter_template(template_name))


def render_live_formatter_bridge() -> str:
    """
    Render live formatter bridge.

    Returns:
        Rendered bridge.

    """
    return load_live_formatter_bridge_template()


def render_live_formatter_runtime_assets(
    formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    *,
    pluginmanager: PytestPluginManager | None,
) -> dict[str, str]:
    """
    Render live formatter runtime assets.

    Returns:
        Runtime assets dictionary.

    """
    """Render live formatter runtime assets."""
    assets = {"render_cucumber_formatters.js": render_live_formatter_bridge()}
    module_requests = [
        formatter_request
        for formatter_request in formatter_requests
        if formatter_request.runtime_kind == FormatterRuntimeKind.module
    ]
    if not module_requests:
        return assets

    runtime_assets_hook = _require_formatter_runtime_assets_hook(pluginmanager)
    for formatter_request in module_requests:
        for rendered_assets in runtime_assets_hook.pytest_bdd_cucumber_formatter_runtime_assets(
            formatter_request=formatter_request,
            formatter_requests=tuple(formatter_requests),
        ):
            if rendered_assets:
                assets.update(rendered_assets)
    return assets
