"""Provide plugin helpers for facade plugin."""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING

from attrs import define, field

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.plugin.allure_formatter.api_hooks import AllureFormatterApiHooks
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

logger = logging.getLogger(__name__)


@define(eq=False, hash=False)
class AllureFormatterPlugin:
    """
    Unified facade plugin for allure-formatter.

    Coordinates AllureFormatter and AllureFormatterApiHooks.
    """

    config: Config = field()
    output_dir: str = field()

    _listener: AllureFormatter | None = field(default=None, init=False)
    _api_hooks: AllureFormatterApiHooks | None = field(default=None, init=False)

    def start(self) -> None:
        """Start and register all coordinated sub-components."""
        from pytest_bdd.util.xdist import is_xdist_worker

        if is_xdist_worker(self.config):
            return  # Workers forward messages; controller consolidates and writes results.

        import allure_commons

        from pytest_bdd.plugin.allure_formatter.api_hooks import AllureFormatterApiHooks
        from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

        # 1. Register listener with pytest
        self._listener = AllureFormatter(config=self.config, output_dir=self.output_dir)
        self.config.pluginmanager.register(self._listener, "allure-formatter-listener")
        self._listener.start()

        # 2. Register api hooks with allure-commons
        self._api_hooks = AllureFormatterApiHooks(config=self.config)
        allure_commons.plugin_manager.register(self._api_hooks)

    def stop(self) -> None:
        """Unregister and clean up all coordinated sub-components."""
        import allure_commons

        if self._api_hooks is not None:
            with contextlib.suppress(ValueError, AssertionError):
                allure_commons.plugin_manager.unregister(self._api_hooks)
            self._api_hooks = None

        if self._listener is not None:
            with contextlib.suppress(ValueError, AssertionError):
                self.config.pluginmanager.unregister(self._listener)
            self._listener.stop()
            self._listener = None

    def pytest_bdd_enable_runtime_messages(self, config: Config) -> bool:
        """
        Enable producing runtime messages in live mode.

        Returns:
            bool: True if runtime messages should be enabled.

        """
        return getattr(config.option, "cucumber_messages_path", None) is None
