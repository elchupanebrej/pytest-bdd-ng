"""
Hook specifications for the allure-cucumber plugin.

Defines AllureCucumberHookSpec with 5 hooks for cross-plugin communication.
All hook names are prefixed with ``pytest_`` so that PytestPluginManager
can discover the hookimpl implementations on registered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config


class AllureFormatterHookSpec:
    """
    Hook specifications for allure-formatter cross-plugin communication.

    Plugins implement these hooks to perform allure-formatter operations
    without direct callback wiring or config stash anti-patterns.
    """

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_consume_messages(self, config: Config) -> bool:  # noqa: PLR6301  -- pluggy hookspec keeps instance-method shape
        """
        Return True if a plugin wants to consume the NDJSON message stream.

        Implement this hook to opt-in to consuming the message output.
        The first plugin returning True wins.
        """
        return False

    @pytest.hookspec
    def pytest_allure_formatter_start_step(
        self,
        config: Config,
        uuid: str,
        title: str,
        params: dict | None = None,
    ) -> None:
        """Start a new step in the current test case."""

    @pytest.hookspec
    def pytest_allure_formatter_stop_step(
        self,
        config: Config,
        uuid: str,
        exc_type: type | None = None,
        exc_val: Exception | None = None,
        exc_tb: object | None = None,
    ) -> None:
        """Stop the current step."""

    @pytest.hookspec
    def pytest_allure_formatter_attach_data(
        self,
        config: Config,
        body: str | bytes,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach data to the current test case or step."""

    @pytest.hookspec
    def pytest_allure_formatter_attach_file(
        self,
        config: Config,
        source: str,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:
        """Attach a file to the current test case or step."""
