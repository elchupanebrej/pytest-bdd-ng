import logging
from unittest.mock import MagicMock

from pytest_cuke._native_go import _bridge


def test_go_parser_logs_version_once_on_first_parse(monkeypatch, caplog):
    library = MagicMock()
    version = MagicMock(return_value="v42.0.1")
    monkeypatch.setattr(_bridge, "_version_logged", False)
    monkeypatch.setattr(_bridge, "_load_library", lambda: library)
    monkeypatch.setattr(_bridge, "gherkin_go_version", version)
    monkeypatch.setattr(_bridge, "_call_and_free", lambda *_args: "{}")
    with caplog.at_level(logging.INFO, logger=_bridge.__name__):
        assert _bridge.gherkin_go_available()
        assert not caplog.records
        _bridge.parse_gherkin_document("Feature: first")
        _bridge.parse_gherkin_markdown("Feature: second")
    assert [record.getMessage() for record in caplog.records] == ["Go parser version: v42.0.1"]
    version.assert_called_once_with()


def test_version_lookup_failure_does_not_prevent_parsing(monkeypatch, caplog):
    library = MagicMock()
    monkeypatch.setattr(_bridge, "_version_logged", False)
    monkeypatch.setattr(_bridge, "_load_library", lambda: library)
    monkeypatch.setattr(_bridge, "gherkin_go_version", MagicMock(side_effect=RuntimeError("version unavailable")))
    monkeypatch.setattr(_bridge, "_call_and_free", lambda *_args: "{}")
    with caplog.at_level(logging.INFO, logger=_bridge.__name__):
        assert _bridge.parse_gherkin_document("Feature: example") == "{}"
    assert [record.getMessage() for record in caplog.records] == ["Go parser version: unknown"]
