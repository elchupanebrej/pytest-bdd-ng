from __future__ import annotations

from unittest.mock import MagicMock

from pytest_cuke.cucumber_json import (
    LogBDDCucumberJSON,
    add_options,
    configure,
    unconfigure,
)


def test_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    add_options(parser)
    parser.getgroup.assert_called_once_with("cuke", "Cucumber JSON")
    assert group.addoption.call_count == 2
    output_args, output_kwargs = group.addoption.call_args_list[0]
    assert "--cuke-json" in output_args
    assert output_kwargs["dest"] == "cuke_json"
    assert output_kwargs["nargs"] == "?"
    assert output_kwargs["const"] == "cucumber.json"
    backend_args, backend_kwargs = group.addoption.call_args_list[1]
    assert "--cuke-json-backend" in backend_args
    assert backend_kwargs["dest"] == "cuke_json_backend"
    assert backend_kwargs["choices"] == ("cucumber", "native")


def test_configure_and_unconfigure() -> None:
    config = MagicMock()
    config.option.cuke_json = "report.json"
    config.option.cuke_json_backend = "native"
    del config.workerinput  # simulate master process

    configure(config)
    assert hasattr(config, "_bddcucumberjson")
    config.pluginmanager.register.assert_called_once()

    unconfigure(config)
    assert not hasattr(config, "_bddcucumberjson")
    config.pluginmanager.unregister.assert_called_once()


def test_configure_leaves_message_driven_json_to_shared_formatter_runtime() -> None:
    config = MagicMock()
    config.option.cuke_json = "report.json"
    config.option.cuke_json_backend = "cucumber"

    configure(config)

    assert "_bddcucumberjson" not in vars(config)
    config.pluginmanager.register.assert_not_called()


def test_log_bdd_cucumber_json_get_result() -> None:
    logger = LogBDDCucumberJSON("dummy.json")
    step = {"failed": False, "duration": 0.05}
    report = MagicMock()
    report.passed = True
    report.failed = False
    report.skipped = False

    res_passed = logger._get_result(step, report)
    assert res_passed["status"] == "passed"
    assert res_passed["duration"] == 50000000

    step_failed = {"failed": True, "duration": 0.01}
    report.passed = False
    report.failed = True
    report.longrepr = "AssertionError: failed"

    res_failed = logger._get_result(step_failed, report, error_message=True)
    assert res_failed["status"] == "failed"
    assert "AssertionError" in res_failed["error_message"]

    report.passed = True
    report.failed = False
    tolerated_step = {"failed": True, "status": "failed", "error_message": "body assertion", "duration": 0.01}
    tolerated_result = logger._get_result(tolerated_step, report)
    assert tolerated_result["status"] == "failed"
    assert tolerated_result["error_message"] == "body assertion"

    report.passed = False
    report.failed = False
    report.skipped = True
    res_skipped = logger._get_result(step, report)
    assert res_skipped["status"] == "skipped"


def test_log_bdd_cucumber_json_preserves_undefined_step_status() -> None:
    logger = LogBDDCucumberJSON("dummy.json")
    step = {
        "failed": True,
        "status": "undefined",
        "error_message": "Step definition is not found",
        "duration": 0.01,
    }
    report = MagicMock()
    report.passed = False
    report.failed = True
    report.skipped = False

    result = logger._get_result(step, report)

    assert result["status"] == "undefined"
    assert result["error_message"] == "Step definition is not found"
