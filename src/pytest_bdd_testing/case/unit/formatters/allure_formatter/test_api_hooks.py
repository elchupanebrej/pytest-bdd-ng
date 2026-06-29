"""Unit tests for AllureFormatterApiHooks."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytestmark = [pytest.mark.unit]


def test_start_step_delegates_to_hook() -> None:
    from pytest_bdd.plugin.allure_formatter.api_hooks import AllureFormatterApiHooks

    config = MagicMock()
    hooks = AllureFormatterApiHooks(config=config)
    hooks.start_step(uuid="step-1", title="Given something")

    config.hook.pytest_allure_formatter_start_step.assert_called_once_with(
        config=config,
        uuid="step-1",
        title="Given something",
        params=None,
    )


def test_stop_step_delegates_to_hook() -> None:
    from pytest_bdd.plugin.allure_formatter.api_hooks import AllureFormatterApiHooks

    config = MagicMock()
    hooks = AllureFormatterApiHooks(config=config)
    hooks.stop_step(uuid="step-1")

    config.hook.pytest_allure_formatter_stop_step.assert_called_once_with(
        config=config,
        uuid="step-1",
        exc_type=None,
        exc_val=None,
        exc_tb=None,
    )


def test_attach_data_delegates_to_hook() -> None:
    from pytest_bdd.plugin.allure_formatter.api_hooks import AllureFormatterApiHooks

    config = MagicMock()
    hooks = AllureFormatterApiHooks(config=config)
    hooks.attach_data(body=b"content", name="screenshot.png", attachment_type="image/png", extension="png")

    config.hook.pytest_allure_formatter_attach_data.assert_called_once_with(
        config=config,
        body=b"content",
        name="screenshot.png",
        attachment_type="image/png",
        extension="png",
    )


def test_attach_file_delegates_to_hook() -> None:
    from pytest_bdd.plugin.allure_formatter.api_hooks import AllureFormatterApiHooks

    config = MagicMock()
    hooks = AllureFormatterApiHooks(config=config)
    hooks.attach_file(source="/path/to/file.png", name="file.png", attachment_type="image/png", extension="png")

    config.hook.pytest_allure_formatter_attach_file.assert_called_once_with(
        config=config,
        source="/path/to/file.png",
        name="file.png",
        attachment_type="image/png",
        extension="png",
    )
