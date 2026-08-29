from __future__ import annotations

from unittest.mock import MagicMock

from pytest_bdd.cucumber_json import (
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
    parser.getgroup.assert_called_once_with("bdd", "Cucumber JSON")
    group.addoption.assert_called_once()
    args, kwargs = group.addoption.call_args
    assert "--cucumberjson" in args
    assert "--cucumber-json" in args
    assert kwargs["dest"] == "cucumber_json_path"


def test_configure_and_unconfigure() -> None:
    config = MagicMock()
    config.option.cucumber_json_path = "report.json"
    del config.workerinput  # simulate master process

    configure(config)
    assert hasattr(config, "_bddcucumberjson")
    config.pluginmanager.register.assert_called_once()

    unconfigure(config)
    assert not hasattr(config, "_bddcucumberjson")
    config.pluginmanager.unregister.assert_called_once()


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

    report.passed = False
    report.failed = False
    report.skipped = True
    res_skipped = logger._get_result(step, report)
    assert res_skipped["status"] == "skipped"
