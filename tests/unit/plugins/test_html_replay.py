import io
import sys

from pytest_cuke import html_replay, html_replay_worker
from pytest_cuke.formatter_api import FormatterSelection


def test_html_replay_request_runs_the_worker_module(tmp_path):
    request = html_replay.replay_html_formatter_request(
        FormatterSelection(
            name="cucumber-html",
            destination=tmp_path / "report.html",
            working_directory=tmp_path,
        )
    )

    assert request.name == "cucumber-html"
    assert request.output_path == tmp_path / "report.html"
    assert request.command == (sys.executable, "-m", "pytest_cuke.html_replay_worker")
    assert request.required_npm_packages == ("@cucumber/html-formatter",)


def test_worker_joins_non_empty_stdin_lines(monkeypatch, capsys):
    monkeypatch.setattr(html_replay_worker, "render_cucumber_html", lambda messages: f"HTML:{messages}")
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"a":1}\n\n{"b":2}\n'))

    assert html_replay_worker.main() == 0
    assert capsys.readouterr().out == 'HTML:{"a":1},{"b":2}'


def test_worker_rejects_an_empty_stream(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n\n"))

    assert html_replay_worker.main() == 1
    assert "empty Messages stream" in capsys.readouterr().err
