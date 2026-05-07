from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.model.message_extension import EventEnvelope

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest


class GherkinMessageReporterHookSpec:
    @pytest.hookspec
    def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:
        """Implement cucumber message protocol https://github.com/cucumber/messages."""

    @pytest.hookspec
    def pytest_bdd_xdist_message_batch(self, config: Config, node: object, batch: dict[str, object]) -> None:
        """Record reporter-specific xdist batch events received on the controller side."""

    @pytest.hookspec
    def pytest_bdd_cucumber_formatter_request(
        self,
        config: Config,
        resolve_output_path: Callable[[str], Path],
    ) -> "CucumberFormatterRequest | None":
        """Build one formatter runtime request from the current pytest configuration."""

    @pytest.hookspec
    def pytest_bdd_cucumber_formatter_runtime_assets(
        self,
        formatter_request: "CucumberFormatterRequest",
        formatter_requests: tuple["CucumberFormatterRequest", ...],
    ) -> dict[str, str] | None:
        """Render formatter-specific runtime assets required by the live formatter bridge."""
