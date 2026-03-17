from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from attrs import define, field

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


@define(eq=False)
class ReporterServiceBase:
    plugin_suffix: ClassVar[str | None] = None
    reporter: GherkinMessageReporter = field()

    @property
    def plugin_name(self) -> str:
        plugin_suffix = type(self).plugin_suffix
        if plugin_suffix is None:
            message = f"{type(self).__name__} does not define plugin_suffix"
            raise ValueError(message)
        return f"{type(self.reporter).plugin_name}:{plugin_suffix}"
