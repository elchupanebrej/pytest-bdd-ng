"""
Provide registry helpers.

Responsibility:
    Provide registry helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.cucumber_formatter_support.registry` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - UnknownFormatterPluginError: owns nested behavior below this boundary
    - _sorted_formatter_plugins: owns nested behavior below this boundary
    - _discover_formatter_plugins_from_entrypoints: owns nested behavior below this boundary
    - FormatterPluginCatalog: owns nested behavior below this boundary
    - _discover_formatter_plugin_catalog: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/execution_message_adapter.py: imports or references `registry`
    - src/pytest_bdd/model/message_registry.py: imports or references `registry`
    - src/pytest_bdd/model/message_schema_validation.py: imports or references `registry`
    - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references `registry`
    - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `registry`

State and side effects:
    mutates message, formatter_plugins, FORMATTER_PLUGIN_ENTRYPOINT_PREFIX, plugin, plugins; depends on
    __future__.annotations, functools.cache, typing.TYPE_CHECKING, attrs.frozen,
    pytest_bdd.compatibility.importlib.metadata.entry_points.

Invariants:
    - `pytest_bdd.util.cucumber_formatter_support.registry` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises UnknownFormatterPluginError, RuntimeError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from attrs import frozen

from pytest_bdd.compatibility.importlib.metadata import entry_points
from pytest_bdd.plugin.gherkin_message_reporter.session import render_live_formatter_bridge
from pytest_bdd.util.cucumber_formatter_support.base import FormatterReporterPlugin

if TYPE_CHECKING:
    from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest

FORMATTER_PLUGIN_ENTRYPOINT_PREFIX = "pytest-bdd-cucumber-formatter-"


class UnknownFormatterPluginError(LookupError):
    """
    Represent unknown formatter plugin error failures.

    Responsibility:
        Represent unknown formatter plugin error failures. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.registry.UnknownFormatterPluginError` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `UnknownFormatterPluginError`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `UnknownFormatterPluginError`
        - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references
          `UnknownFormatterPluginError`
        - src/pytest_bdd/util/cucumber_formatters.py: imports or references `UnknownFormatterPluginError`

    State and side effects:
        mutates message.

    Invariants:
        - `pytest_bdd.util.cucumber_formatter_support.registry.UnknownFormatterPluginError` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __init__(self, formatter_name: str, *, known_formatters: tuple[str, ...]) -> None:
        """
        Initialize the unknown formatter plugin error.

        Responsibility:
            Initialize the unknown formatter plugin error. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.registry.UnknownFormatterPluginError.__init__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - join: collaborator call used by this boundary
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates message.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.registry.UnknownFormatterPluginError.__init__` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        message = (
            f"Unknown cucumber formatter plugin {formatter_name!r}. Known formatters: {', '.join(known_formatters)}"
        )
        super().__init__(message)


def _sorted_formatter_plugins(
    formatter_plugins: list[FormatterReporterPlugin],
) -> tuple[FormatterReporterPlugin, ...]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.cucumber_formatter_support.registry._sorted_formatter_plugins`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.registry._sorted_formatter_plugins` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `_sorted_formatter_plugins`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `_sorted_formatter_plugins`
        - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references
          `_sorted_formatter_plugins`
        - src/pytest_bdd/util/cucumber_formatters.py: imports or references `_sorted_formatter_plugins`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    return tuple(
        sorted(
            formatter_plugins,
            key=lambda plugin: (plugin.discovery_order, plugin.formatter, plugin.module_name),
        ),
    )


def _discover_formatter_plugins_from_entrypoints() -> list[FormatterReporterPlugin]:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.util.cucumber_formatter_support.registry._discover_formatter_plugins_from_entrypoints` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.registry._discover_formatter_plugins_from_entrypoints` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - entry_points: collaborator call used by this boundary
        - entrypoint.name.startswith: collaborator call used by this boundary
        - entrypoint.load: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - formatter_plugins.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `_discover_formatter_plugins_from_entrypoints`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references
          `_discover_formatter_plugins_from_entrypoints`
        - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references
          `_discover_formatter_plugins_from_entrypoints`
        - src/pytest_bdd/util/cucumber_formatters.py: imports or references
          `_discover_formatter_plugins_from_entrypoints`

    State and side effects:
        mutates formatter_plugins, plugin.

    Invariants:
        - `pytest_bdd.util.cucumber_formatter_support.registry._discover_formatter_plugins_from_entrypoints` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
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
    """
    Represent formatter plugin catalog state.

    Raises:
        UnknownFormatterPluginError: If the operation cannot be completed.

    Responsibility:
        Represent formatter plugin catalog state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - discover: owns nested behavior below this boundary
        - by_option_attr: owns nested behavior below this boundary
        - by_name: owns nested behavior below this boundary
        - require_plugin: owns nested behavior below this boundary
        - render_runtime_assets: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `FormatterPluginCatalog`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `FormatterPluginCatalog`
        - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references `FormatterPluginCatalog`
        - src/pytest_bdd/util/cucumber_formatters.py: imports or references `FormatterPluginCatalog`

    State and side effects:
        mutates plugins, plugins_by_name, assets, rendered_assets.

    Invariants:
        - `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises UnknownFormatterPluginError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """

    plugins: tuple[FormatterReporterPlugin, ...]

    @classmethod
    def discover(cls) -> FormatterPluginCatalog:
        """
        Discover formatter plugins.

        Returns:
            Formatter plugin catalog.

        Responsibility:
            Discover formatter plugins. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.discover` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _discover_formatter_plugin_catalog: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references `discover`
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `discover`
            - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references `discover`
            - src/pytest_bdd/util/cucumber_formatters.py: imports or references `discover`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return _discover_formatter_plugin_catalog()

    def by_option_attr(self) -> dict[str, FormatterReporterPlugin]:
        """
        Get plugins by option attribute.

        Returns:
            Dictionary mapping option attributes to plugins.

        Responsibility:
            Get plugins by option attribute. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.by_option_attr` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `by_option_attr`
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `by_option_attr`
            - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references `by_option_attr`
            - src/pytest_bdd/util/cucumber_formatters.py: imports or references `by_option_attr`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

        """
        return {plugin.option_attr: plugin for plugin in self.plugins}

    def by_name(self) -> dict[str, FormatterReporterPlugin]:
        """
        Get plugins by name.

        Returns:
            Dictionary mapping formatter names to plugins.

        Responsibility:
            Get plugins by name. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.by_name` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references `by_name`
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `by_name`
            - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references `by_name`
            - src/pytest_bdd/util/cucumber_formatters.py: imports or references `by_name`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

        """
        return {plugin.formatter: plugin for plugin in self.plugins}

    def require_plugin(self, formatter_name: str) -> FormatterReporterPlugin:
        """
        Require a plugin by formatter name.

        Returns:
            Formatter reporter plugin.

        Raises:
            UnknownFormatterPluginError: If the operation cannot be completed.

        Responsibility:
            Require a plugin by formatter name. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.require_plugin` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.by_name: collaborator call used by this boundary
            - UnknownFormatterPluginError: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `require_plugin`
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `require_plugin`
            - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references `require_plugin`
            - src/pytest_bdd/util/cucumber_formatters.py: imports or references `require_plugin`

        State and side effects:
            mutates plugins_by_name.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.require_plugin` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises UnknownFormatterPluginError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        plugins_by_name = self.by_name()
        try:
            return plugins_by_name[formatter_name]
        except KeyError as exc:
            raise UnknownFormatterPluginError(
                formatter_name,
                known_formatters=tuple(sorted(plugins_by_name)),
            ) from exc

    def render_runtime_assets(self, formatter_requests: tuple[CucumberFormatterRequest, ...]) -> dict[str, str]:
        """
        Render runtime assets.

        Returns:
            Rendered runtime assets dictionary.

        Responsibility:
            Render runtime assets. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.render_runtime_assets` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - render_live_formatter_bridge: collaborator call used by this boundary
            - self.require_plugin.render_runtime_assets: collaborator call used by this boundary
            - self.require_plugin: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - assets.update: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `render_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `render_runtime_assets`
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `render_runtime_assets`
            - src/pytest_bdd/util/cucumber_formatter_support/base.py: imports or references `render_runtime_assets`
            - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references
              `render_runtime_assets`

        State and side effects:
            mutates assets, rendered_assets.

        Invariants:
            - `pytest_bdd.util.cucumber_formatter_support.registry.FormatterPluginCatalog.render_runtime_assets` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
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


@cache
def _discover_formatter_plugin_catalog() -> FormatterPluginCatalog:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.util.cucumber_formatter_support.registry._discover_formatter_plugin_catalog` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.cucumber_formatter_support.registry._discover_formatter_plugin_catalog` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _discover_formatter_plugins_from_entrypoints: collaborator call used by this boundary
        - RuntimeError: collaborator call used by this boundary
        - FormatterPluginCatalog: collaborator call used by this boundary
        - _sorted_formatter_plugins: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `_discover_formatter_plugin_catalog`
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references
          `_discover_formatter_plugin_catalog`
        - src/pytest_bdd/util/cucumber_formatter_support/standalone.py: imports or references
          `_discover_formatter_plugin_catalog`
        - src/pytest_bdd/util/cucumber_formatters.py: imports or references `_discover_formatter_plugin_catalog`

    State and side effects:
        mutates formatter_plugins, message.

    Invariants:
        - `pytest_bdd.util.cucumber_formatter_support.registry._discover_formatter_plugin_catalog` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    formatter_plugins = _discover_formatter_plugins_from_entrypoints()
    if not formatter_plugins:
        message = (
            "No cucumber formatter plugins were discovered through pytest11 entry points. "
            "Standalone replay requires the explicit formatter catalog path."
        )
        raise RuntimeError(message)
    return FormatterPluginCatalog(plugins=_sorted_formatter_plugins(formatter_plugins))
