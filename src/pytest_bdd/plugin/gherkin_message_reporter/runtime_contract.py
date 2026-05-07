from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pytest_bdd.compatibility.pytest import Config, PytestPluginManager

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_bdd.model.message_extension import EventEnvelope
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRenderResult

QuietTerminalRestorer = Callable[[], None] | None
QuietTerminalReplacer = Callable[[Config], QuietTerminalRestorer]


@runtime_checkable
class ReporterLifecycleContract(Protocol):
    plugin_name: str

    def configure(
        self,
        *,
        pluginmanager: PytestPluginManager,
        quiet_terminal_replacer: QuietTerminalReplacer,
    ) -> None: ...

    def unconfigure(self, *, pluginmanager: PytestPluginManager) -> None: ...


@runtime_checkable
class FormatterRenderingContract(Protocol):
    def read_envelopes_from_path(self, messages_file_path: Path) -> list[EventEnvelope]: ...

    def render_requested_cucumber_formatters_from_path(
        self,
        messages_file_path: Path,
    ) -> CucumberFormatterRenderResult: ...
