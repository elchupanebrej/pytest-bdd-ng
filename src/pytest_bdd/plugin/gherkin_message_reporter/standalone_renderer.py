"""
Provide standalone renderer helpers.

Responsibility:
    Provide standalone renderer helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer` because
    it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _StandaloneRuntimeConfig: owns nested behavior below this boundary
    - _StandaloneReporterRuntime: owns nested behavior below this boundary
    - _StandaloneLiveFormatterService: owns nested behavior below this boundary
    - StandaloneCucumberFormatterRenderer: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `standalone_renderer`

State and side effects:
    mutates rootpath, config, requested_cucumber_formatters, formatter_catalog, renderer; depends on
    __future__.annotations, typing.TYPE_CHECKING, typing.cast, attrs.frozen,
    pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime.LiveFormatterService.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from attrs import frozen

from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import LiveFormatterService
from pytest_bdd.plugin.gherkin_message_reporter.session import (  # noqa: F401
    CucumberFormatterConfigurationError,
    CucumberFormatterRenderResult,
    CucumberFormatterRequest,
)
from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService
from pytest_bdd.util.cucumber_formatter_support.standalone import (
    resolve_standalone_formatter_catalog,
    resolve_standalone_formatter_requests,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
    from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog


@frozen
class _StandaloneRuntimeConfig:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneRuntimeConfig` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneRuntimeConfig` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `_StandaloneRuntimeConfig`

    State and side effects:
        mutates rootpath.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneRuntimeConfig` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    rootpath: Path


@frozen
class _StandaloneReporterRuntime:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneReporterRuntime` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneReporterRuntime` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - render_runtime_assets: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `_StandaloneReporterRuntime`

    State and side effects:
        mutates config, requested_cucumber_formatters, formatter_catalog, renderer.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneReporterRuntime` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    config: _StandaloneRuntimeConfig
    requested_cucumber_formatters: tuple[CucumberFormatterRequest, ...]
    formatter_catalog: FormatterPluginCatalog

    def __init__(
        self,
        *,
        config: _StandaloneRuntimeConfig,
        requested_cucumber_formatters: tuple[CucumberFormatterRequest, ...],
        formatter_catalog: FormatterPluginCatalog,
    ) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneReporterRuntime.__init__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneReporterRuntime.__init__` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - object.__setattr__: collaborator call used by this boundary

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
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "requested_cucumber_formatters", requested_cucumber_formatters)
        object.__setattr__(self, "formatter_catalog", formatter_catalog)

    def render_runtime_assets(
        self,
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneReporterRuntime.render_runtime_assets`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneReporterRuntime.render_runtime_assets`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - renderer: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `render_runtime_assets`
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `render_runtime_assets`
            - src/pytest_bdd/util/cucumber_formatter_support/base.py: imports or references `render_runtime_assets`
            - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `render_runtime_assets`

        State and side effects:
            mutates renderer.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneReporterRuntime.render_runtime_assets`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        renderer = cast(
            "Callable[[list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...]], dict[str, str]]",
            self.formatter_catalog.render_runtime_assets,
        )
        return renderer(formatter_requests)


class _StandaloneLiveFormatterService(LiveFormatterService):
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneLiveFormatterService` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneLiveFormatterService` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `_StandaloneLiveFormatterService`

    State and side effects:
        mutates self.reporter.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneLiveFormatterService` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    def __init__(self, reporter: _StandaloneReporterRuntime) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneLiveFormatterService.__init__`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneLiveFormatterService.__init__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary

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
            mutates self.reporter.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer._StandaloneLiveFormatterService.__init__`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        self.reporter = cast("GherkinMessageReporter", reporter)


@frozen
class StandaloneCucumberFormatterRenderer:
    """
    Represent standalone cucumber formatter renderer state.

    Responsibility:
        Represent standalone cucumber formatter renderer state. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer.StandaloneCucumberFormatterRenderer` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - discover: owns nested behavior below this boundary
        - resolve_requests: owns nested behavior below this boundary
        - render_from_messages_path: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references
          `StandaloneCucumberFormatterRenderer`

    State and side effects:
        mutates catalog, formatter_requests, runtime, live_formatter_service, envelopes.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer.StandaloneCucumberFormatterRenderer` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    catalog: FormatterPluginCatalog

    @classmethod
    def discover(
        cls,
        *,
        catalog: FormatterPluginCatalog | None = None,
    ) -> StandaloneCucumberFormatterRenderer:
        """
        Discover formatter plugins.

        Returns:
            Standalone renderer instance.

        Responsibility:
            Discover formatter plugins. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer.StandaloneCucumberFormatterRenderer.discover`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary
            - resolve_standalone_formatter_catalog: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
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
        return cls(catalog=resolve_standalone_formatter_catalog(catalog))

    def resolve_requests(
        self,
        *,
        rootpath: Path,
        formatter_option_values: dict[str, object],
    ) -> tuple[CucumberFormatterRequest, ...]:
        """
        Resolve formatter requests.

        Returns:
            Tuple of formatter requests.

        Responsibility:
            Resolve formatter requests. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer.StandaloneCucumberFormatterRenderer.resolve_requests`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - resolve_standalone_formatter_requests: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `resolve_requests`

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
            #arch-eval:locational_stability=3

        """
        return resolve_standalone_formatter_requests(
            rootpath=rootpath,
            formatter_option_values=formatter_option_values,
            catalog=self.catalog,
        )

    def render_from_messages_path(
        self,
        messages_path: Path,
        *,
        rootpath: Path,
        formatter_option_values: dict[str, object],
    ) -> CucumberFormatterRenderResult:
        """
        Render from messages path.

        Returns:
            Render result.

        Responsibility:
            Render from messages path. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer.StandaloneCucumberFormatterRenderer.render_from_messages_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.resolve_requests: collaborator call used by this boundary
            - _StandaloneReporterRuntime: collaborator call used by this boundary
            - _StandaloneRuntimeConfig: collaborator call used by this boundary
            - _StandaloneLiveFormatterService: collaborator call used by this boundary
            - TransportService.read_envelopes_from_path: collaborator call used by this boundary
            - live_formatter_service.run_requested_cucumber_formatters: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `render_from_messages_path`

        State and side effects:
            mutates formatter_requests, runtime, live_formatter_service, envelopes.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer.StandaloneCucumberFormatterRenderer.render_from_messages_path`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        formatter_requests = self.resolve_requests(
            rootpath=rootpath,
            formatter_option_values=formatter_option_values,
        )
        runtime = _StandaloneReporterRuntime(
            config=_StandaloneRuntimeConfig(rootpath=rootpath),
            requested_cucumber_formatters=formatter_requests,
            formatter_catalog=self.catalog,
        )
        live_formatter_service = _StandaloneLiveFormatterService(reporter=runtime)
        envelopes = TransportService.read_envelopes_from_path(messages_path)
        return live_formatter_service.run_requested_cucumber_formatters(envelopes)
