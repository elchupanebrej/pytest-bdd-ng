"""Provide live formatter runtime coordinator."""

from __future__ import annotations

from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_node import LiveFormatterNodeMixin
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload import LiveFormatterPayloadMixin
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process import (
    LiveFormatterProcess,
    LiveFormatterProcessMixin,
)
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner import LiveFormatterRunnerMixin
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase


class LiveFormatterService(
    LiveFormatterRunnerMixin,
    LiveFormatterNodeMixin,
    LiveFormatterPayloadMixin,
    LiveFormatterProcessMixin,
    ReporterServiceBase,
):
    """Coordinate live formatter runtime behavior."""


__all__ = ["LiveFormatterProcess", "LiveFormatterService"]
