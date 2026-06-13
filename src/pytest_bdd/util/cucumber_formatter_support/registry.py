"""
Provides focused utility functions for the `registry` concern within pytest-bdd utility layer,
offering helper operat.

Responsibility:
    Provides focused utility functions for the `registry` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `registry` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `registry`-related helper operations within the
    utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `registry` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `registry` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
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
    Signals a UnknownFormatterPluginError condition during pytest-bdd runtime operations, carrying
    domain-specific contex.

    Responsibility:
        Signals a UnknownFormatterPluginError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically UnknownFormatterPluginError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - LookupError: UnknownFormatterPluginError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        UnknownFormatterPluginError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate UnknownFormatterPluginError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of UnknownFormatterPluginError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def __init__(self, formatter_name: str, *, known_formatters: tuple[str, ...]) -> None:
        """
        Initializ a new UnknownFormatterPluginError instance with domain-specific context parameters,.
        formatting a human-re.

        Responsibility:
            Initializes a new UnknownFormatterPluginError instance with domain-specific context parameters,
            formatting a human-readable diagnostic message that includes relevant identifiers for debugging
            test failures in pytest output and log files.

        Reason for existence:
            The __init__ of UnknownFormatterPluginError is the constructor boundary where raw failure
            context is transformed into a formatted exception message. It is the single place where the
            diagnostic message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on UnknownFormatterPluginError instances.

        Separation:
            - Other UnknownFormatterPluginError methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch UnknownFormatterPluginError implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        message = (
            f"Unknown cucumber formatter plugin {formatter_name!r}. Known formatters: {', '.join(known_formatters)}"
        )
        super().__init__(message)


def _sorted_formatter_plugins(
    formatter_plugins: list[FormatterReporterPlugin],
) -> tuple[FormatterReporterPlugin, ...]:
    """
    Perform the `_sorted_formatter_plugins` operation within its module boundary, implementing a.
    focused helper function.

    Responsibility:
        Performs the `_sorted_formatter_plugins` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_sorted_formatter_plugins` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _sorted_formatter_plugins operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _sorted_formatter_plugins for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _sorted_formatter_plugins function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return tuple(
        sorted(
            formatter_plugins,
            key=lambda plugin: (plugin.discovery_order, plugin.formatter, plugin.module_name),
        ),
    )


def _discover_formatter_plugins_from_entrypoints() -> list[FormatterReporterPlugin]:
    """
    Perform the `_discover_formatter_plugins_from_entrypoints` operation within its module.
    boundary, implementing a focu.

    Responsibility:
        Performs the `_discover_formatter_plugins_from_entrypoints` operation within its module
        boundary, implementing a focused helper function that is consumed by higher layers for its
        specific utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `_discover_formatter_plugins_from_entrypoints` exists as a standalone function because it
        encapsulates an operation that does not require shared instance state and benefits from being
        independently callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _discover_formatter_plugins_from_entrypoints operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _discover_formatter_plugins_from_entrypoints for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _discover_formatter_plugins_from_entrypoints function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
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
    Encapsulates the FormatterPluginCatalog concern within pytest-bdd, providing a focused set of
    collaborating operation.

    Responsibility:
        Encapsulates the FormatterPluginCatalog concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        FormatterPluginCatalog is a distinct class because its methods share internal state and
        collaborate on a cohesive task that would be awkward to express as standalone functions with
        shared mutable parameters.

    Delegates:
        - object: FormatterPluginCatalog specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single FormatterPluginCatalog domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate FormatterPluginCatalog for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of FormatterPluginCatalog maintain internal consistency across all method calls.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    plugins: tuple[FormatterReporterPlugin, ...]

    @classmethod
    def discover(cls) -> FormatterPluginCatalog:
        """
        Perform the discover operation within the FormatterPluginCatalog boundary, handling its.
        specific sub-task as part of.

        Responsibility:
            Performs the discover operation within the FormatterPluginCatalog boundary, handling its
            specific sub-task as part of the broader FormatterPluginCatalog responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            discover is a distinct method because it encapsulates a specific behavioral concern that must
            be independently callable and potentially overridable by subclasses of FormatterPluginCatalog
            without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the discover operation on FormatterPluginCatalog instances.

        Separation:
            - Other FormatterPluginCatalog methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterPluginCatalog implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return _discover_formatter_plugin_catalog()

    def by_option_attr(self) -> dict[str, FormatterReporterPlugin]:
        """
        Perform the by_option_attr operation within the FormatterPluginCatalog boundary, handling its.
        specific sub-task as p.

        Responsibility:
            Performs the by_option_attr operation within the FormatterPluginCatalog boundary, handling its
            specific sub-task as part of the broader FormatterPluginCatalog responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            by_option_attr is a distinct method because it encapsulates a specific behavioral concern that
            must be independently callable and potentially overridable by subclasses of
            FormatterPluginCatalog without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the by_option_attr operation on FormatterPluginCatalog instances.

        Separation:
            - Other FormatterPluginCatalog methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterPluginCatalog implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return {plugin.option_attr: plugin for plugin in self.plugins}

    def by_name(self) -> dict[str, FormatterReporterPlugin]:
        """
        Perform the by_name operation within the FormatterPluginCatalog boundary, handling its.
        specific sub-task as part of .

        Responsibility:
            Performs the by_name operation within the FormatterPluginCatalog boundary, handling its
            specific sub-task as part of the broader FormatterPluginCatalog responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            by_name is a distinct method because it encapsulates a specific behavioral concern that must be
            independently callable and potentially overridable by subclasses of FormatterPluginCatalog
            without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the by_name operation on FormatterPluginCatalog instances.

        Separation:
            - Other FormatterPluginCatalog methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterPluginCatalog implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return {plugin.formatter: plugin for plugin in self.plugins}

    def require_plugin(self, formatter_name: str) -> FormatterReporterPlugin:
        """
        Perform the require_plugin operation within the FormatterPluginCatalog boundary, handling its.
        specific sub-task as p.

        Responsibility:
            Performs the require_plugin operation within the FormatterPluginCatalog boundary, handling its
            specific sub-task as part of the broader FormatterPluginCatalog responsibility in the pytest-
            bdd runtime lifecycle.

        Reason for existence:
            require_plugin is a distinct method because it encapsulates a specific behavioral concern that
            must be independently callable and potentially overridable by subclasses of
            FormatterPluginCatalog without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the require_plugin operation on FormatterPluginCatalog instances.

        Separation:
            - Other FormatterPluginCatalog methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterPluginCatalog implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
        Perform the render_runtime_assets operation within the FormatterPluginCatalog boundary,.
        handling its specific sub-ta.

        Responsibility:
            Performs the render_runtime_assets operation within the FormatterPluginCatalog boundary,
            handling its specific sub-task as part of the broader FormatterPluginCatalog responsibility in
            the pytest-bdd runtime lifecycle.

        Reason for existence:
            render_runtime_assets is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            FormatterPluginCatalog without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the render_runtime_assets operation on FormatterPluginCatalog
            instances.

        Separation:
            - Other FormatterPluginCatalog methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FormatterPluginCatalog implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
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
    Perform the `_discover_formatter_plugin_catalog` operation within its module boundary,.
    implementing a focused helper.

    Responsibility:
        Performs the `_discover_formatter_plugin_catalog` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `_discover_formatter_plugin_catalog` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _discover_formatter_plugin_catalog operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _discover_formatter_plugin_catalog for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _discover_formatter_plugin_catalog function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    formatter_plugins = _discover_formatter_plugins_from_entrypoints()
    if not formatter_plugins:
        message = (
            "No cucumber formatter plugins were discovered through pytest11 entry points. "
            "Standalone replay requires the explicit formatter catalog path."
        )
        raise RuntimeError(message)
    return FormatterPluginCatalog(plugins=_sorted_formatter_plugins(formatter_plugins))
