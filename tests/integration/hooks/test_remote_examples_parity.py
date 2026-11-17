import json
import base64
import shutil
import ssl
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest


@pytest.mark.parametrize("suffix,delimiter,absolute", [("csv", ",", False), ("tsv", "\t", True)])
def test_remote_examples_execute_each_row_and_retain_source(pytester, suffix, delimiter, absolute):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makeconftest("""
from pathlib import Path
from pytest_cuke import given, parsers
@given(parsers.parse("row {value}"))
def row(value):
    with Path("rows-executed.txt").open("a") as out:
        out.write(value + "\\n")
""")
    pytester.makepyfile(
        test_remote=f"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from pytest_cuke import scenario
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = FEATURE if self.path == "/features/example.feature" else TABLE
        body = data.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        pass
server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
base = f"http://127.0.0.1:{{server.server_port}}"
table_ref = base + "/features/rows.{suffix}" if {absolute!r} else "rows.{suffix}"
FEATURE = "Feature: Remote\\n  Scenario Outline: Rows\\n    Given row <value>\\n    Examples: table: " + table_ref + "\\n"
TABLE = "value{delimiter}other\\none{delimiter}1\\ntwo{delimiter}2\\n"
Thread(target=server.serve_forever, daemon=True).start()
@scenario(base + "/features/example.feature", "Rows", features_path_type="url")
def test_rows():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(passed=2)
    assert sorted((pytester.path / "rows-executed.txt").read_text().splitlines()) == ["one", "two"]
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    assert any("pickle" in event for event in events)
    sources = [
        json.loads(event["attachment"]["body"])["externalExamplesSource"]
        for event in events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-bdd.launch+json"
    ]
    assert sorted(source["sourceLine"] for source in sources) == [2, 3]
    assert sorted(source["rowIndex"] for source in sources) == [1, 2]
    assert all(source["path"].endswith(f"/features/rows.{suffix}") for source in sources)


@pytest.mark.parametrize("via_redirect,table_configured", [(False, True), (True, True), (True, False)])
def test_server_credentials_are_scoped_for_feature_and_external_table(
    pytester, monkeypatch, via_redirect, table_configured
):
    received = []
    table_origin = ""
    feature_origin = ""

    class TableHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            received.append(("table", self.headers.get("Authorization"), self.headers.get("X-Secret")))
            expected = "Bearer table-token" if table_configured else None
            self.send_response(200 if self.headers.get("Authorization") == expected else 403)
            self.end_headers()
            self.wfile.write(b"value\none\ntwo\n")

        def log_message(self, *_):
            pass

    class FeatureHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            received.append(("feature", self.headers.get("Authorization"), self.headers.get("X-Secret")))
            authorized = self.headers.get("Authorization") == "Bearer feature-token"
            authorized &= self.headers.get("X-Secret") == "feature-header"
            if self.path == "/redirect" and authorized:
                self.send_response(302)
                self.send_header("Location", table_origin + "/rows.csv")
                self.end_headers()
                return
            self.send_response(200 if authorized else 403)
            self.end_headers()
            feature = "Feature: Remote\n  Scenario Outline: Rows\n    Given row <value>\n    Examples: table: "
            reference = feature_origin + "/redirect" if via_redirect else table_origin + "/rows.csv"
            self.wfile.write((feature + reference + "\n").encode())

        def log_message(self, *_):
            pass

    table_server = ThreadingHTTPServer(("127.0.0.1", 0), TableHandler)
    feature_server = ThreadingHTTPServer(("127.0.0.1", 0), FeatureHandler)
    table_origin = f"http://127.0.0.1:{table_server.server_port}"
    feature_origin = f"http://127.0.0.1:{feature_server.server_port}"
    for server in (table_server, feature_server):
        Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("FEATURE_TOKEN", "feature-token")
    monkeypatch.setenv("FEATURE_HEADER", "feature-header")
    monkeypatch.setenv("TABLE_TOKEN", "table-token")
    rules = [
        {
            "origin": feature_origin,
            "bearer": {"env": "FEATURE_TOKEN"},
            "headers": {"X-Secret": {"env": "FEATURE_HEADER"}},
        },
    ]
    if table_configured:
        rules.append({"origin": table_origin, "bearer": {"env": "TABLE_TOKEN"}})
    pytester.makeini(
        "[pytest]\ncuke_parser = python\ncuke_autoload = false\ncuke_http_servers =\n"
        + "\n".join("    " + json.dumps(rule) for rule in rules)
    )
    pytester.makeconftest("""
from pytest_cuke import given, parsers
@given(parsers.parse("row {value}"))
def row(value):
    pass
""")
    pytester.makepyfile(
        test_remote=f"""
from pytest_cuke import scenario
@scenario({(feature_origin + "/example.feature")!r}, "Rows", features_path_type="url")
def test_rows():
    pass
"""
    )
    try:
        result = pytester.runpytest_subprocess("-q")
        result.assert_outcomes(passed=2)
        assert ("feature", "Bearer feature-token", "feature-header") in received
        assert ("table", "Bearer table-token" if table_configured else None, None) in received
        if via_redirect and table_configured:
            pytest.importorskip("xdist")
            received.clear()
            parallel = pytester.runpytest_subprocess("-n", "2", "-q")
            parallel.assert_outcomes(passed=2)
            assert any(source == "table" for source, _, _ in received)
            assert all(
                auth == "Bearer table-token" and header is None
                for source, auth, header in received
                if source == "table"
            )
    finally:
        for server in (feature_server, table_server):
            server.shutdown()
            server.server_close()


@pytest.mark.parametrize("use_cli,secure", [(False, False), (True, False), (False, True)])
def test_local_feature_can_load_basic_authenticated_remote_examples(pytester, monkeypatch, use_cli, secure):
    expected = "Basic " + base64.b64encode(b"reader:secret").decode()
    received = []

    class TableHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            received.append((self.headers.get("Authorization"), self.headers.get("X-Client")))
            self.send_response(200 if received[-1] == (expected, "pytest-cuke") else 403)
            self.end_headers()
            if self.path == "/example.feature":
                self.wfile.write(
                    b"Feature: HTTPS\n  Scenario Outline: Rows\n    Given row <value>\n    Examples: table: rows.csv\n"
                )
            else:
                self.wfile.write(b"value\none\ntwo\n")

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), TableHandler)
    if secure:
        openssl = shutil.which("openssl")
        if openssl is None:
            pytest.skip("openssl is required to create a test TLS certificate")
        key = pytester.path / "server.key"
        cert = pytester.path / "server.crt"
        subprocess.run(
            [
                openssl,
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-keyout",
                str(key),
                "-out",
                str(cert),
                "-subj",
                "/CN=127.0.0.1",
                "-addext",
                "subjectAltName=IP:127.0.0.1",
            ],
            check=True,
            capture_output=True,
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # Some interpreters (GraalPy) require string paths here.
        context.load_cert_chain(str(cert), str(key))
        server.socket = context.wrap_socket(server.socket, server_side=True)
        monkeypatch.setenv("SSL_CERT_FILE", str(cert))
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f"{'https' if secure else 'http'}://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("EXAMPLE_USER", "reader")
    monkeypatch.setenv("EXAMPLE_PASSWORD", "secret")
    rule = {
        "origin": origin,
        "basic": {"username": {"env": "EXAMPLE_USER"}, "password": {"env": "EXAMPLE_PASSWORD"}},
        "headers": {"X-Client": "pytest-cuke"},
    }
    ini_rule = {"origin": origin, "bearer": "incorrect"} if use_cli else rule
    pytester.makeini(
        "[pytest]\ncuke_parser = python\ncuke_autoload = false\ncuke_http_servers =\n    " + json.dumps(ini_rule)
    )
    (pytester.path / "local.feature").write_text(
        "Feature: Local\n  Scenario Outline: Rows\n    Given row <value>\n    Examples: table: "
        + origin
        + "/rows.csv\n"
    )
    pytester.makeconftest("""
from pytest_cuke import given, parsers
@given(parsers.parse("row {value}"))
def row(value):
    pass
""")
    if secure:
        pytester.makepyfile(
            test_local=f"""
from pytest_cuke import scenario
@scenario({(origin + "/example.feature")!r}, "Rows", features_path_type="url")
def test_rows():
    pass
"""
        )
    else:
        pytester.makepyfile(
            test_local="""
from pytest_cuke import scenario
@scenario("local.feature", "Rows", features_base_dir=".")
def test_rows():
    pass
"""
        )
    try:
        options = ("--cuke-http-server", json.dumps(rule)) if use_cli else ()
        result = pytester.runpytest_subprocess(*options, "-q")
        result.assert_outcomes(passed=2)
        assert received == [(expected, "pytest-cuke")] * (2 if secure else 1)
        assert "secret" not in result.stdout.str()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize("broken", ["missing", "empty", "malformed"])
def test_invalid_remote_table_reports_a_collection_error(pytester, broken):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/rows.csv":
                self.send_response(404 if broken == "missing" else 200)
                self.end_headers()
                if broken == "malformed":
                    self.wfile.write(b"name,value\nonly-one-column\n")
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"Feature: Remote\n  Scenario Outline: Rows\n    Given row <name>\n    Examples: table: rows.csv\n"
            )

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makepyfile(
        test_remote=f"""
from pytest_cuke import scenario
@scenario("http://127.0.0.1:{server.server_port}/example.feature", "Rows", features_path_type="url")
def test_rows():
    pass
"""
    )
    try:
        result = pytester.runpytest_subprocess("-q")
        assert result.ret != 0
        assert "External Examples source error" in result.stdout.str()
        assert "rows.csv" in result.stdout.str()
    finally:
        server.shutdown()
        server.server_close()


def test_relative_remote_table_resolves_against_redirected_feature_url(pytester):
    paths = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            paths.append(self.path)
            if self.path == "/shortcut":
                self.send_response(302)
                self.send_header("Location", "/nested/example.feature")
                self.end_headers()
            elif self.path == "/nested/example.feature":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    b"Feature: Remote\n  Scenario Outline: Rows\n    Given row <value>\n    Examples: table: rows.csv\n"
                )
            elif self.path == "/nested/rows.csv":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"value\none\ntwo\n")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makeconftest("""
from pytest_cuke import given, parsers
@given(parsers.parse("row {value}"))
def row(value):
    pass
""")
    pytester.makepyfile(
        test_remote=f"""
from pytest_cuke import scenario
@scenario("http://127.0.0.1:{server.server_port}/shortcut", "Rows", features_path_type="url", features_mimetype="text/x.cucumber.gherkin+plain")
def test_rows():
    pass
"""
    )
    try:
        result = pytester.runpytest_subprocess("-q")
        result.assert_outcomes(passed=2)
        assert "/nested/rows.csv" in paths
        assert "/rows.csv" not in paths
    finally:
        server.shutdown()
        server.server_close()
