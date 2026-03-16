from __future__ import annotations

from attrs import frozen

from pytest_bdd.compatibility.importlib.metadata import entry_points
from pytest_bdd.plugin.cucumber_formatter_support.base import FormatterReporterPlugin

FORMATTER_PLUGIN_ENTRYPOINT_PREFIX = "pytest-bdd-cucumber-formatter-"


class UnknownFormatterPluginError(LookupError):
    def __init__(self, formatter_name: str, *, known_formatters: tuple[str, ...]) -> None:
        message = (
            f"Unknown cucumber formatter plugin {formatter_name!r}. Known formatters: {', '.join(known_formatters)}"
        )
        super().__init__(message)


def _sorted_formatter_plugins(
    formatter_plugins: list[FormatterReporterPlugin],
) -> tuple[FormatterReporterPlugin, ...]:
    return tuple(
        sorted(
            formatter_plugins,
            key=lambda plugin: (plugin.discovery_order, plugin.formatter, plugin.module_name),
        )
    )


def _discover_formatter_plugins_from_entrypoints() -> list[FormatterReporterPlugin]:
    formatter_plugins: list[FormatterReporterPlugin] = []
    for entrypoint in entry_points(group="pytest11"):
        if not entrypoint.name.startswith(FORMATTER_PLUGIN_ENTRYPOINT_PREFIX):
            continue
        plugin = entrypoint.load()
        if isinstance(plugin, FormatterReporterPlugin):
            formatter_plugins.append(plugin)
    return formatter_plugins


@frozen
class FormatterPluginCatalog:
    plugins: tuple[FormatterReporterPlugin, ...]

    @classmethod
    def discover(cls) -> FormatterPluginCatalog:
        formatter_plugins = _discover_formatter_plugins_from_entrypoints()
        if not formatter_plugins:
            message = (
                "No cucumber formatter plugins were discovered through pytest11 entry points. "
                "Standalone replay requires the explicit formatter catalog path."
            )
            raise RuntimeError(message)
        return cls(plugins=_sorted_formatter_plugins(formatter_plugins))

    def by_option_attr(self) -> dict[str, FormatterReporterPlugin]:
        return {plugin.option_attr: plugin for plugin in self.plugins}

    def by_name(self) -> dict[str, FormatterReporterPlugin]:
        return {plugin.formatter: plugin for plugin in self.plugins}

    def require_plugin(self, formatter_name: str) -> FormatterReporterPlugin:
        plugins_by_name = self.by_name()
        try:
            return plugins_by_name[formatter_name]
        except KeyError as exc:
            raise UnknownFormatterPluginError(
                formatter_name,
                known_formatters=tuple(sorted(plugins_by_name)),
            ) from exc

    def render_runtime_assets(self, formatter_requests) -> dict[str, str]:
        from pytest_bdd.plugin.gherkin_message_reporter.session import render_live_formatter_bridge

        assets = {"render_cucumber_formatters.js": render_live_formatter_bridge()}
        for formatter_request in formatter_requests:
            if formatter_request.runtime_kind.value != "module":
                continue
            rendered_assets = self.require_plugin(formatter_request.formatter).render_runtime_assets(
                formatter_request,
                tuple(formatter_requests),
            )
            if rendered_assets:
                assets.update(rendered_assets)
        return assets
