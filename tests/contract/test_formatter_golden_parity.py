"""Golden parity tests for cucumber formatter outputs."""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

import pytest

from pytest_bdd.script.render_cucumber_formatters import main
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog
from tests.support.cucumber_formatters import install_fake_node

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "cucumber_formatter_golden.json"
EXPECTED_FORMATTERS = {
    "json",
    "junit",
    "pretty",
    "progress",
    "progress-bar",
    "snippets",
    "summary",
    "usage",
    "usage-json",
}
CONSOLE_FORMATTERS = ("pretty", "progress", "progress-bar", "snippets", "summary", "usage")
FILE_FORMATTERS = ("json", "junit", "usage", "usage-json")
FAKE_FORMATTER_PACKAGES = ("@cucumber/cucumber", "@cucumber/junit-xml-formatter", "@cucumber/pretty-formatter")


def _messages_path(tmp_path: Path) -> Path:
    messages_path = tmp_path / "messages.ndjson"
    messages_path.write_text(
        textwrap.dedent(
            """\
            {"testRunStarted":{"id":"run-1","timestamp":{"seconds":0,"nanos":0}}}
            {"testRunFinished":{"success":false,"timestamp":{"seconds":0,"nanos":1},"testRunStartedId":"run-1","message":"done"}}
            """,
        ),
        encoding="utf-8",
    )
    return messages_path


def _normalize_output(value: str, tmp_path: Path) -> str:
    normalized = value.replace(str(tmp_path), "<TMP>")
    normalized = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", normalized)
    return re.sub(r"\b\d+(?:\.\d+)?s\b", "<DURATION>", normalized)


def _golden() -> dict[str, dict[str, str]]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_formatter_catalog_covers_all_golden_formatter_plugins() -> None:
    """Verify golden coverage includes every cucumber formatter plugin."""
    catalog_names = {plugin.formatter for plugin in FormatterPluginCatalog.discover().plugins}

    assert catalog_names == EXPECTED_FORMATTERS
    assert set(_golden()["stdout"]) | set(_golden()["file"]) == EXPECTED_FORMATTERS


@pytest.mark.parametrize("formatter_name", CONSOLE_FORMATTERS)
def test_console_formatter_output_matches_golden(
    formatter_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify terminal formatter output remains stable."""
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=FAKE_FORMATTER_PACKAGES)
    messages_path = _messages_path(tmp_path)
    plugin = FormatterPluginCatalog.discover().by_name()[formatter_name]

    assert main(["--messages-ndjson", str(messages_path), plugin.cli_flag]) == 0
    captured = capsys.readouterr()

    assert not captured.err
    assert _normalize_output(captured.out, tmp_path) == _golden()["stdout"][formatter_name]


@pytest.mark.parametrize("formatter_name", FILE_FORMATTERS)
def test_file_formatter_output_matches_golden(
    formatter_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify file formatter output remains stable."""
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=FAKE_FORMATTER_PACKAGES)
    messages_path = _messages_path(tmp_path)
    plugin = FormatterPluginCatalog.discover().by_name()[formatter_name]
    output_path = tmp_path / f"{formatter_name}.out"

    assert main(["--messages-ndjson", str(messages_path), plugin.cli_flag, str(output_path)]) == 0
    captured = capsys.readouterr()

    assert not captured.out
    assert not captured.err
    assert _normalize_output(output_path.read_text(encoding="utf-8"), tmp_path) == _golden()["file"][formatter_name]
