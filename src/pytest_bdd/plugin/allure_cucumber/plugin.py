"""Provide plugin helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from attrs import define, field

from pytest_bdd.compatibility.pytest import TerminalReporter
from pytest_bdd.plugin.allure_cucumber.converter import convert

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config

logger = logging.getLogger(__name__)


@define(eq=False, hash=False)
class AllureCucumberPlugin:
    """Represent allure cucumber plugin state."""

    config: Config = field()
    output_dir: str = "allure-results"
    messages_path: str | None = None
    plugin_name: str = "pytest-bdd-allure-cucumber"

    def pytest_sessionfinish(self) -> None:
        """Handle sessionfinish — call converter."""
        output_path = Path(os.path.expandvars(self.output_dir)).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        messages_path = self._resolve_messages_path()
        if messages_path is None:
            logger.warning("No messages NDJSON path found, skipping allure conversion")
            return

        try:
            convert(messages_path, output_path)
        except (OSError, ValueError) as exc:
            logger.warning("Allure conversion failed: %s", exc, exc_info=True)

    def pytest_terminal_summary(self, terminalreporter: object) -> None:
        """Write terminal summary."""
        if isinstance(terminalreporter, TerminalReporter):
            terminalreporter.write_sep("-", f"generated allure results: {self.output_dir}")

    def _resolve_messages_path(self) -> Path | None:
        """
        Resolve the messages NDJSON path.

        Returns:
            Path to messages NDJSON file, or None if not found.

        """
        if self.messages_path is not None:
            path = Path(self.messages_path)
            if path.is_absolute():
                return path
            return Path.cwd().resolve() / path

        default_path = Path.cwd().resolve() / "allure-results" / "messages.ndjson"
        if default_path.exists():
            return default_path

        return None
