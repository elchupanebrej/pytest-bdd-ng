"""Unit tests for AllureFormatter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]


def test_init_creates_adapter() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")
    assert listener.adapter is not None
    assert listener.adapter.lifecycle is not None


def test_pytest_bdd_message_calls_adapter() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")
    message = MagicMock()

    with patch(
        "pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.deserialize",
    ) as mock_deserialize:
        mock_projection = MagicMock()
        mock_deserialize.return_value = mock_projection
        # Mock the route_envelope method by patching at the class level
        with patch.object(
            type(listener.adapter),
            "route_envelope",
            return_value=None,
        ):
            listener.pytest_bdd_message(config, message)
            mock_deserialize.assert_called_once_with(message, registry=listener._registry)


def test_pytest_bdd_message_handles_exception() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")
    message = MagicMock()

    with patch(
        "pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.deserialize",
    ) as mock_deserialize:
        mock_deserialize.side_effect = RuntimeError("deserialize failed")
        listener.pytest_bdd_message(config, message)
        # Should not raise - exception is caught and logged


def test_start_registers_file_logger() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")

    with patch("allure_commons.plugin_manager") as mock_pm:
        with patch("allure_commons.logger.AllureFileLogger") as mock_logger_cls:
            listener.start()
            mock_logger_cls.assert_called_once()
            mock_pm.register.assert_called_once()


def test_stop_unregisters_file_logger() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")
    listener._file_logger = MagicMock()

    with patch("allure_commons.plugin_manager") as mock_pm:
        listener.stop()
        mock_pm.unregister.assert_called_once()
        assert listener._file_logger is None


def test_stop_noop_when_no_file_logger() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")

    with patch("allure_commons.plugin_manager") as mock_pm:
        listener.stop()
        mock_pm.unregister.assert_not_called()


def test_pytest_allure_formatter_start_step_delegates_to_lifecycle() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")
    lifecycle = MagicMock()
    listener.adapter.lifecycle = lifecycle

    listener.pytest_allure_formatter_start_step(config=config, uuid="step-1", title="Given something")
    lifecycle.start_step.assert_called_once_with(uuid="step-1")


def test_pytest_allure_formatter_stop_step_delegates_to_lifecycle() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")
    lifecycle = MagicMock()
    listener.adapter.lifecycle = lifecycle

    listener.pytest_allure_formatter_stop_step(config=config, uuid="step-1")
    lifecycle.stop_step.assert_called_once_with("step-1")


def test_pytest_allure_formatter_attach_data_delegates_to_lifecycle() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")
    lifecycle = MagicMock()
    listener.adapter.lifecycle = lifecycle

    listener.pytest_allure_formatter_attach_data(
        config=config,
        body=b"content",
        name="screenshot.png",
        attachment_type="image/png",
        extension="png",
    )
    lifecycle.attach_data.assert_called_once()
    call_kwargs = lifecycle.attach_data.call_args[1]
    assert call_kwargs["body"] == b"content"
    assert call_kwargs["name"] == "screenshot.png"
    assert call_kwargs["attachment_type"] == "image/png"
    assert call_kwargs["extension"] == "png"


def test_pytest_allure_formatter_attach_file_delegates_to_lifecycle() -> None:
    from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

    config = MagicMock()
    listener = AllureFormatter(config=config, output_dir="test-results")
    lifecycle = MagicMock()
    listener.adapter.lifecycle = lifecycle

    listener.pytest_allure_formatter_attach_file(
        config=config,
        source="/path/to/file.png",
        name="file.png",
        attachment_type="image/png",
        extension="png",
    )
    lifecycle.attach_file.assert_called_once()
    call_kwargs = lifecycle.attach_file.call_args[1]
    assert call_kwargs["source"] == "/path/to/file.png"
    assert call_kwargs["name"] == "file.png"
    assert call_kwargs["attachment_type"] == "image/png"
    assert call_kwargs["extension"] == "png"
