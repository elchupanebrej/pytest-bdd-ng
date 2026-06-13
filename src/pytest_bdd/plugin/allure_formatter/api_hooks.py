"""AllureFormatterApiHooks — implements allure_commons hooks via config.hook.xxx()."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from attrs import define, field

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config

logger = logging.getLogger(__name__)


@define(eq=False, hash=False)
class AllureFormatterApiHooks:
    """
    Implement allure_commons hooks for step and attach operations.

    Delegates to AllureFormatterHookSpec hooks via config.hook.xxx().
    Follows allure-pytest-bdd's AllurePytestBddApiHooks pattern (allure_api_listener.py:15).
    """

    config: Config = field()

    def start_step(self, uuid: str, title: str, params: dict | None = None) -> None:  # type: ignore[override]
        """Start a new step in the current test case."""
        self.config.hook.pytest_allure_formatter_start_step(config=self.config, uuid=uuid, title=title, params=params)

    def stop_step(
        self,
        uuid: str,
        exc_type: type | None = None,
        exc_val: Exception | None = None,
        exc_tb: object | None = None,
    ) -> None:  # type: ignore[override]
        """Stop the current step."""
        self.config.hook.pytest_allure_formatter_stop_step(
            config=self.config,
            uuid=uuid,
            exc_type=exc_type,
            exc_val=exc_val,
            exc_tb=exc_tb,
        )

    def attach_data(
        self,
        body: str | bytes,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:  # type: ignore[override]
        """Attach data to the current test case or step."""
        self.config.hook.pytest_allure_formatter_attach_data(
            config=self.config,
            body=body,
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )

    def attach_file(
        self,
        source: str,
        name: str,
        attachment_type: str | None = None,
        extension: str | None = None,
    ) -> None:  # type: ignore[override]
        """Attach a file to the current test case or step."""
        self.config.hook.pytest_allure_formatter_attach_file(
            config=self.config,
            source=source,
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )
