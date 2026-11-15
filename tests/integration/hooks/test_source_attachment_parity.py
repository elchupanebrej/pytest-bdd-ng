import json
import sys

import pytest
from pytest_cuke.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_cuke.formatter_api import FormatterRequest
from pytest_cuke.formatter_replay import replay_messages


@pytest.mark.parametrize(
    "filename,content,mimetype",
    [
        ("custom.story", "Feature: Custom\n  Scenario: Works\n    Given a working step\n", "application/x-custom"),
        ("worker.story", "Feature: Worker\n  Scenario: Works\n    Given a working step\n", "application/x-worker"),
        pytest.param(
            "structured.bdd.yaml",
            "Name: YAML\nAction: a working step\n",
            "application/x.struct_bdd+yaml",
            marks=pytest.mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed"),
        ),
        (
            "standard.feature",
            "Feature: Standard\n  Scenario: Works\n    Given a working step\n",
            "text/x.cucumber.gherkin+plain",
        ),
        (
            "recognized.story",
            "Feature: Recognized\n  Scenario: Works\n    Given a working step\n",
            "text/x.cucumber.gherkin+plain",
        ),
    ],
)
def test_source_content_survives_in_messages(pytester, filename, content, mimetype):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    (pytester.path / filename).write_text(content, encoding="utf-8")
    pytester.makeconftest("""
import pytest
from pathlib import Path
from attrs import evolve
from pytest_cuke import step
from pytest_cuke.parser import GherkinParser, ParserRegistration
class CustomParser(GherkinParser):
    pass
class PlainParser(GherkinParser):
    def parse_text(self, content, uri=None, **kwargs):
        return evolve(super().parse_text(content, uri=uri, **kwargs), source_content=content, source_media_type="text/x.cucumber.gherkin+plain")
@pytest.hookimpl(tryfirst=True)
def pytest_cuke_get_mimetype(config, path):
    if path.name == "recognized.story":
        return "application/x-recognized"
    if path.name == "worker.story":
        return "application/x-worker"
    if path.suffix == ".story":
        return "application/x-custom"
@pytest.hookimpl(tryfirst=True)
def pytest_cuke_get_parser(config, mimetype):
    if mimetype == "application/x-custom":
        return ParserRegistration.native(CustomParser)
    if mimetype == "application/x-recognized":
        return ParserRegistration.native(PlainParser)
    if mimetype == "application/x-worker":
        return ParserRegistration.native(GherkinParser)
@step("a working step")
def working():
    Path("step-executed").touch()
""")
    scenario_name = "YAML" if filename.endswith(".yaml") else "Works"
    pytester.makepyfile(
        test_scenarios=f"""
from pathlib import Path
from pytest_cuke import scenario
@scenario({filename!r}, {scenario_name!r}, features_base_dir=".")
def test_scenario():
    assert Path("step-executed").exists()
"""
    )
    batch_options = ("--cuke-batch-threshold=1",) if filename == "worker.story" else ()
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", *batch_options, "-q")
    result.assert_outcomes(passed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    if mimetype == "text/x.cucumber.gherkin+plain":
        sources = [event["source"] for event in events if "source" in event]
        assert len(sources) == 1 and sources[0]["data"] == content
        assert sources[0]["mediaType"] == mimetype
    else:
        attachments = [
            json.loads(event["attachment"]["body"])
            for event in events
            if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.source+json"
        ]
        assert len(attachments) == 1
        assert attachments[0]["data"] == content
        assert attachments[0]["mediaType"] == mimetype
        assert attachments[0]["uri"].endswith(filename)
        output = pytester.path / "formatter.ndjson"
        replay_messages(
            pytester.path / "messages.ndjson",
            (
                FormatterRequest(
                    name="probe",
                    command=(sys.executable, "-c", "import sys; sys.stdout.write(sys.stdin.read())"),
                    output_path=output,
                    working_directory=pytester.path,
                    timeout_seconds=5,
                ),
            ),
        )
        rendered = [json.loads(line) for line in output.read_text().splitlines()]
        assert not any(
            event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.source+json"
            for event in rendered
        )
        assert any("pickle" in event for event in rendered)
        if mimetype == "application/x.struct_bdd+yaml":
            pytest.importorskip("xdist")
            parallel = pytester.runpytest_subprocess("-n", "2", "--cuke-messages-ndjson=parallel.ndjson", "-q")
            parallel.assert_outcomes(passed=1)
            parallel_events = [
                json.loads(line) for line in (pytester.path / "parallel.ndjson").read_text().splitlines()
            ]
            parallel_sources = [
                json.loads(event["attachment"]["body"])
                for event in parallel_events
                if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.source+json"
            ]
            assert any(item["data"] == content and item["uri"].endswith(filename) for item in parallel_sources)
            parallel_output = pytester.path / "parallel-formatter.ndjson"
            replay_messages(
                pytester.path / "parallel.ndjson",
                (
                    FormatterRequest(
                        name="probe",
                        command=(sys.executable, "-c", "import sys; sys.stdout.write(sys.stdin.read())"),
                        output_path=parallel_output,
                        working_directory=pytester.path,
                        timeout_seconds=5,
                    ),
                ),
            )
            assert any("pickle" in json.loads(line) for line in parallel_output.read_text().splitlines())


def test_remote_custom_source_preserves_uri_mime_and_unicode(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makeconftest("""
import pytest
from pytest_cuke import given
from pytest_cuke.parser import GherkinParser, ParserRegistration
@pytest.hookimpl(tryfirst=True)
def pytest_cuke_get_parser(config, mimetype):
    if mimetype == "application/x-custom":
        return ParserRegistration.native(GherkinParser)
@given("a remote step")
def remote_step():
    pass
""")
    content = (
        "Feature: Unicode café\n  Scenario: Works\n    Given a remote step\n  Scenario: Ignored\n    Given no binding\n"
    )
    pytester.makepyfile(
        test_remote=f"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from pytest_cuke import scenario
CONTENT = {content!r}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = CONTENT.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/x-custom; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *args):
        pass
server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
Thread(target=server.serve_forever, daemon=True).start()
@scenario(f"http://127.0.0.1:{{server.server_port}}/remote.story", "Works", features_path_type="url", features_mimetype="application/x-custom")
def test_remote():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(passed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    sources = [
        json.loads(event["attachment"]["body"])
        for event in events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.source+json"
    ]
    assert len(sources) == 1
    assert sources[0]["uri"].startswith("http://127.0.0.1:") and sources[0]["uri"].endswith("/remote.story")
    assert sources[0]["mediaType"] == "application/x-custom"
    assert sources[0]["data"] == content
