"""Text diagnostics from an installed extension matcher retain their parameter name."""

import json
import subprocess
import sys

import pytest

pytestmark = pytest.mark.contract


@pytest.mark.parametrize(
    "message,name",
    [
        ("Undefined parameter type 'unknownParameter'.", "unknownParameter"),
        ("Undefined parameter type {unknownParameter}.", "unknownParameter"),
        ("ordinary matcher failure", None),
    ],
)
def test_text_matcher_diagnostic(tmp_path, message, name):
    (tmp_path / "features").mkdir()
    (tmp_path / "features/probe.feature").write_text(
        "Feature: Extension matcher\n  Scenario: missing\n    Given value 10\n"
    )
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "conftest.py").write_text(
        "import pytest\nfrom pytest_cuke.steps import Matcher\n"
        "@pytest.hookimpl(tryfirst=True)\n"
        "def pytest_cuke_match_step_definition_to_step(request, run):\n"
        f"    raise Matcher.MatchNotFoundError({message!r})\n"
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "features/probe.feature",
            "--confcutdir=.",
            "-c",
            "pytest.ini",
            "--cuke-parser=python",
            "--cuke-messages-ndjson=messages.ndjson",
            "-q",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    events = [json.loads(line) for line in (tmp_path / "messages.ndjson").read_text().splitlines()]
    diagnostics = [e["undefinedParameterType"] for e in events if "undefinedParameterType" in e]
    assert diagnostics == ([{"expression": "value 10", "name": name}] if name else [])
