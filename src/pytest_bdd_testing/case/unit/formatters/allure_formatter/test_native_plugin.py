"""Unit and contract tests for pytest-native Allure BDD plugin."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.model.execution_message_adapter import ExecutionProjection
from pytest_bdd.plugin.allure_formatter.entrypoint import pytest_configure
from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

pytestmark = [pytest.mark.unit]


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock pytest Config."""
    config = MagicMock(spec=Config)
    config.option = MagicMock()
    config.option.allure_formatter_output_dir = None
    config.option.allure_formatter_output_dir = None
    config.option.allure_formatter_messages_in = None
    config.getini = MagicMock(return_value=None)
    config.pluginmanager = MagicMock()
    return config


def test_plugin_not_registered_by_default(mock_config: MagicMock) -> None:
    """Verify plugin is not registered if no allure options are provided."""
    pytest_configure(mock_config)
    mock_config.pluginmanager.register.assert_not_called()


def test_listener_registered_with_output_dir(mock_config: MagicMock) -> None:
    """Verify AllureFormatter is registered when output directory option is provided."""
    mock_config.option.allure_formatter_output_dir = "allure-results"
    # Configure get_plugin to return None (not already registered)
    mock_config.pluginmanager.get_plugin = MagicMock(return_value=None)
    with patch("allure_commons.plugin_manager") as mock_pm:
        with patch("allure_commons.logger.AllureFileLogger"):
            # Call early hook first (registers listener for import mode only)
            from pytest_bdd.plugin.allure_formatter.entrypoint import pytest_load_initial_conftests

            pytest_load_initial_conftests(mock_config, MagicMock(), ["--allure-formatter-output", "allure-results"])
            # Then call configure
            pytest_configure(mock_config)
    mock_config.pluginmanager.register.assert_called()
    registered_plugin = mock_config.pluginmanager.register.call_args[0][0]
    assert isinstance(registered_plugin, AllureFormatter)


def test_allure_formatter_plugin_facade_start_stop(mock_config: MagicMock) -> None:
    """Verify that AllureFormatterPlugin coordinates registration and cleanup."""

    from pytest_bdd.plugin.allure_formatter.plugin import AllureFormatterPlugin

    plugin = AllureFormatterPlugin(config=mock_config, output_dir="allure-results")

    with patch("allure_commons.plugin_manager") as mock_pm:
        with patch("allure_commons.logger.AllureFileLogger"):
            plugin.start()

            # Verify listener is registered in pytest
            mock_config.pluginmanager.register.assert_called()
            # Verify api hooks registered in allure-commons
            mock_pm.register.assert_called()

            plugin.stop()
            # Verify cleanup
            mock_config.pluginmanager.unregister.assert_called()
            mock_pm.unregister.assert_called()


def test_adapter_generates_allure_results(tmp_path: Path) -> None:
    """Verify that convert_to_allure_commons produces result JSONs and container."""
    output_dir = tmp_path / "allure-results"
    output_dir.mkdir()

    class DummyPayload:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def _make_proj(kind: str, **attrs: Any) -> MagicMock:
        proj = MagicMock(spec=ExecutionProjection)
        proj.payload_kind = MagicMock()
        proj.payload_kind.value = kind
        proj.payload = DummyPayload(**attrs)
        return proj

    ts1 = DummyPayload(id="ts1", pickle_step_id="ps1")
    tc1 = DummyPayload(id="tc1", pickle_id="p1", test_steps=[ts1])
    ps1 = DummyPayload(id="ps1", text="Given a step")

    # Create projections
    p_pickle = _make_proj("pickle", id="p1", name="Scenario 1", steps=[ps1])
    p_tc = _make_proj("test_case", id="tc1", pickle_id="p1", test_steps=[ts1])

    p_tcs = _make_proj("test_case_started", id="tcs1", test_case_id="tc1", timestamp=123457000000)
    p_tss = _make_proj("test_step_started", test_case_started_id="tcs1", test_step_id="ts1", timestamp=123457100000)

    ts_result = DummyPayload(status="passed")
    p_tsf = _make_proj(
        "test_step_finished",
        test_case_started_id="tcs1",
        test_step_id="ts1",
        test_step_result=ts_result,
        timestamp=123458100000,
    )
    p_tcf = _make_proj("test_case_finished", test_case_started_id="tcs1", timestamp=123458500000)

    projections = [p_pickle, p_tc, p_tcs, p_tss, p_tsf, p_tcf]

    from pytest_bdd.plugin.allure_formatter.adapter import convert_to_allure_commons

    convert_to_allure_commons(projections, output_dir)

    # Verify output files
    result_files = list(output_dir.glob("*-result.json"))
    container_files = list(output_dir.glob("*-container.json"))

    assert len(result_files) == 1
    assert len(container_files) == 1

    # Load result and assert structure
    with result_files[0].open(encoding="utf-8") as f:
        res_data = json.load(f)

    assert res_data["name"] == "Scenario 1"
    assert res_data["status"] == "passed"
    assert len(res_data["steps"]) == 1
    assert res_data["steps"][0]["name"] == "Given a step"
    assert res_data["steps"][0]["status"] == "passed"
