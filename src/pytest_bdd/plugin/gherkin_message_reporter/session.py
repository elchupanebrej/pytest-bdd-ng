from __future__ import annotations

import os
from collections.abc import Callable
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from attrs import frozen

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.plugin.cucumber_formatter_support.base import (
    FormatterRuntimeKind,
)
from pytest_bdd.plugin.cucumber_formatter_support.base import (
    load_formatter_adapter_support_template as _load_formatter_adapter_support_template,
)
from pytest_bdd.plugin.cucumber_formatter_support.base import (
    load_formatter_adapter_template as _load_formatter_adapter_template,
)

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config, PytestPluginManager


ResolveOutputPath = Callable[[str], Path]


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


@frozen
class CucumberFormatterRequest:
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


class CucumberFormatterConfigurationError(ValueError):
    """Raised when the requested cucumber formatter configuration is invalid."""

    @classmethod
    def duplicate_output_path(
        cls,
        *,
        formatter_labels: str,
        output_path: Path,
    ) -> CucumberFormatterConfigurationError:
        message = f"Multiple formatter outputs target the same path {output_path}: {formatter_labels}"
        return cls(message)

    @classmethod
    def missing_output_directory(
        cls,
        *,
        cli_flag: str,
        output_dir: Path,
    ) -> CucumberFormatterConfigurationError:
        message = f"Formatter output directory does not exist for {cli_flag}: {output_dir}"
        return cls(message)

    @classmethod
    def terminal_output_conflict(
        cls,
        *,
        formatter_labels: str,
    ) -> CucumberFormatterConfigurationError:
        message = f"Only one terminal-output formatter may be active per run: {formatter_labels}"
        return cls(message)


@frozen
class CucumberFormatterRenderResult:
    success: bool
    rendered_formatters: tuple[CucumberFormatterRequest, ...]
    missing_node: bool = False
    missing_packages: tuple[str, ...] = ()
    process_exit_code: int | None = None


@frozen
class NodePackageProvisionResult:
    env: dict[str, str]
    missing_packages: tuple[str, ...] = ()
    installed_packages: tuple[str, ...] = ()
    node_modules_roots: tuple[Path, ...] = ()
    missing_node: bool = False
    missing_npm: bool = False


def format_requested_cucumber_formatter_labels(
    formatter_requests: tuple[CucumberFormatterRequest, ...] | list[CucumberFormatterRequest],
) -> str:
    return ", ".join(request.cli_flag for request in formatter_requests)


def terminal_output_formatter_requests(
    formatter_requests: list[CucumberFormatterRequest],
) -> list[CucumberFormatterRequest]:
    return [request for request in formatter_requests if request.output_path is None]


def normalize_cucumber_formatter_output_key(output_path: Path) -> str:
    return os.path.normcase(str(output_path.resolve()))


def _read_template_asset(package: str, template_name: str) -> str:
    template = cast(Traversable, files(package).joinpath(template_name))
    return template.read_text(encoding="utf-8")


def _formatter_options_requested(config: Config) -> bool:
    option_values = cast(dict[str, object], getattr(getattr(config, "option", None), "__dict__", {}))
    return any(
        option_name.startswith("cucumber_")
        and option_name != "cucumber_html_path"
        and option_value not in (None, False)
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
    return cast(_FormatterRequestHook, hook)


def _require_formatter_runtime_assets_hook(pluginmanager: PytestPluginManager | None) -> _FormatterRuntimeAssetsHook:
    hook = _formatter_hook_proxy(pluginmanager)
    if hook is None or not hasattr(hook, "pytest_bdd_cucumber_formatter_runtime_assets"):
        msg = (
            "Cucumber formatter runtime assets are unavailable because the formatter runtime-assets hook registry "
            "was not configured."
        )
        raise RuntimeError(msg)
    return cast(_FormatterRuntimeAssetsHook, hook)


def resolve_requested_cucumber_formatters(
    config: Config,
    *,
    resolve_output_path: ResolveOutputPath,
) -> tuple[CucumberFormatterRequest, ...]:
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
            formatter_request
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
    return _read_template_asset(
        "pytest_bdd.plugin.gherkin_message_reporter.resources.templates",
        "live_formatter_bridge.mjs.j2",
    )


def load_formatter_adapter_support_template() -> str:
    loader = cast(Callable[[], str], _load_formatter_adapter_support_template)
    return loader()


def load_formatter_adapter_template(template_name: str) -> str:
    loader = cast(Callable[[str], str], _load_formatter_adapter_template)
    return loader(template_name)


def render_live_formatter_bridge() -> str:
    return load_live_formatter_bridge_template()


def render_live_formatter_runtime_assets(
    formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    *,
    pluginmanager: PytestPluginManager | None,
) -> dict[str, str]:
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
