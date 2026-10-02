from __future__ import annotations

import pytest

from pytest_cuke import cli


def test_command_registry_accepts_nested_commands_and_rejects_conflicts() -> None:
    registry = cli.CommandRegistry()
    registry.add(("report", "summary"), "summarize a report", lambda arguments: 0)

    with pytest.raises(ValueError, match="already registered"):
        registry.add(("report", "summary"), "duplicate summary", lambda arguments: 0)
    with pytest.raises(ValueError, match="children"):
        registry.add(("report",), "parent command", lambda arguments: 0)


def test_standalone_dispatcher_help_lists_reserved_commands(monkeypatch, capsys) -> None:
    registry = cli.CommandRegistry()
    registry.add(("validate", "features"), "validate feature files", lambda arguments: 0)
    registry.add(("generate", "steps"), "generate step stubs", lambda arguments: 0)
    registry.add(("convert", "allure"), "convert Allure results", lambda arguments: 0)
    monkeypatch.setattr(cli, "_build_registry", lambda: registry)

    with pytest.raises(SystemExit) as error:
        cli.main(["--help"])

    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert "validate features" in help_text
    assert "generate steps" in help_text
    assert "convert allure" in help_text
    assert "pytest_cuke.commands" in help_text


def test_command_dispatch_passes_trailing_arguments_to_extension(monkeypatch) -> None:
    received: list[str] = []
    registry = cli.CommandRegistry()
    registry.add(("report", "summary"), "summarize a report", lambda args: received.extend(args) or 7)
    monkeypatch.setattr(cli, "_build_registry", lambda: registry)

    assert cli.main(["report", "summary", "result.json", "--short"]) == 7
    assert received == ["result.json", "--short"]


def test_unimplemented_command_returns_failure_without_success_claim(capsys) -> None:
    registry = cli.CommandRegistry()
    registry.add(("validate", "features"), "validate feature files", cli._unimplemented("validate features"))
    parser = cli._parser_for(registry, "cuke")
    namespace = parser.parse_args(["validate", "features"])

    assert namespace._cuke_handler(namespace.arguments) == 2
    assert "not implemented" in capsys.readouterr().err
