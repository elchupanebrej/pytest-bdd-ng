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
    registry.add(
        ("validate",),
        "validate feature files",
        lambda arguments: 0,
        positionals=("features-dir",),
    )
    registry.add(("generate", "steps"), "generate step stubs", lambda arguments: 0)
    registry.add(("convert", "allure"), "convert Allure results", lambda arguments: 0)
    monkeypatch.setattr(cli, "_build_registry", lambda: registry)

    with pytest.raises(SystemExit) as error:
        cli.main(["--help"])

    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert "validate <features-dir>" in help_text
    assert "generate steps" in help_text
    assert "convert allure" in help_text
    assert "pytest_cuke.commands" in help_text

    with pytest.raises(SystemExit) as error:
        cli.main(["validate", "--help"])

    assert error.value.code == 0
    assert "features-dir" in capsys.readouterr().out


def test_generate_steps_help_exposes_transactional_update_modes(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        cli.main(["generate", "steps", "--help"])

    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert "--feature" in help_text
    assert "--target" in help_text
    assert "--preview" in help_text
    assert "--keep-on-error" in help_text
    assert "--bind-scenarios" in help_text


def test_command_dispatch_passes_trailing_arguments_to_extension(monkeypatch) -> None:
    received: list[str] = []
    registry = cli.CommandRegistry()
    registry.add(("report", "summary"), "summarize a report", lambda args: received.extend(args) or 7)
    monkeypatch.setattr(cli, "_build_registry", lambda: registry)

    assert cli.main(["report", "summary", "result.json", "--short"]) == 7
    assert received == ["result.json", "--short"]


def test_validate_requires_and_dispatches_a_features_directory(monkeypatch, capsys) -> None:
    received: list[str] = []

    def unimplemented_with_capture(arguments: list[str]) -> int:
        received.extend(arguments)
        return cli._unimplemented("validate")(arguments)

    registry = cli.CommandRegistry()
    registry.add(
        ("validate",),
        "validate feature files",
        unimplemented_with_capture,
        positionals=("features-dir",),
    )
    monkeypatch.setattr(cli, "_build_registry", lambda: registry)

    assert cli.main(["validate", "consumer-features"]) == 2
    assert received == ["consumer-features"]
    assert "not implemented" in capsys.readouterr().err

    with pytest.raises(SystemExit) as error:
        cli.main(["validate"])

    assert error.value.code == 2
    assert "features-dir" in capsys.readouterr().err

    with pytest.raises(SystemExit) as error:
        cli.main(["validate", "consumer-features", "extra"])

    assert error.value.code == 2
