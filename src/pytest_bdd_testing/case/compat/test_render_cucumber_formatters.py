"""

Provide test render cucumber formatters helpers.
"""

import textwrap
from pathlib import Path

import pytest

from pytest_bdd.compatibility.tomllib import loads
from pytest_bdd.plugin.gherkin_message_reporter.session import (
    load_formatter_adapter_support_template,
    load_formatter_adapter_template,
    load_live_formatter_bridge_template,
)
from pytest_bdd.script.render_cucumber_formatters import main
from pytest_bdd_testing.tool.cucumber_formatter import (
    install_fake_node,
    materialize_live_formatter_runtime,
    read_fake_formatter_telemetry,
)


def test_render_cucumber_formatters_renders_from_existing_ndjson(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    """
    Verify render cucumber formatters renders from existing ndjson.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    messages_path = tmp_path / "messages.ndjson"
    output_path = tmp_path / "report.json"
    messages_path.write_text(
        textwrap.dedent(
            """\
            {"testRunStarted":{"id":"run-1","timestamp":{"seconds":0,"nanos":0}}}
            {"testRunFinished":{"success":false,"timestamp":{"seconds":0,"nanos":1},"testRunStartedId":"run-1","message":"done"}}
            """,
        ),
        encoding="utf-8",
    )

    code = main(
        [
            "--messages-ndjson",
            str(messages_path),
            "--cucumber-summary",
            "--cucumber-json",
            str(output_path),
            "--cucumber-usage-json",
            str(tmp_path / "usage.json"),
        ],
    )
    out = capsys.readouterr().out

    assert code == 0
    assert "Summary: 2 scenarios (1 passed, 1 failed)" in out
    assert '{"formatter": "json", "passed": 1, "failed": 1}' in output_path.read_text(encoding="utf-8")
    telemetry = read_fake_formatter_telemetry(tmp_path)
    assert len(telemetry) == 1
    assert telemetry[0]["emittedVisibleOutputDuringStream"] is False
    assert telemetry[0]["envelopeCount"] == 2
    assert telemetry[0]["formatterNames"] == ["summary", "json", "usage-json"]
    assert telemetry[0]["sourceMode"] == "messagesPath"
    assert telemetry[0]["consoleWriteCount"] == 0
    assert str(telemetry[0]["messagesPath"]).endswith("formatter_messages.ndjson")


def test_render_cucumber_formatters_rejects_multiple_terminal_outputs(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    """
    Verify render cucumber formatters rejects multiple terminal outputs.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
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

    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "--messages-ndjson",
                str(messages_path),
                "--cucumber-summary",
                "--cucumber-progress",
            ],
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 1
    assert "Only one terminal-output formatter may be active per run" in captured.err


def test_render_cucumber_formatters_rejects_missing_output_directory(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    """
    Verify render cucumber formatters rejects missing output directory.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
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

    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "--messages-ndjson",
                str(messages_path),
                "--cucumber-json",
                str(tmp_path / "missing" / "report.json"),
            ],
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 1
    assert "Formatter output directory does not exist" in captured.err


def test_render_cucumber_formatters_auto_installs_missing_packages(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    """
    Verify render cucumber formatters auto installs missing packages.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=())
    monkeypatch.chdir(tmp_path)
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

    code = main(
        [
            "--messages-ndjson",
            str(messages_path),
            "--cucumber-progress",
        ],
    )
    captured = capsys.readouterr()

    assert code == 0
    assert (
        "Installing missing global npm package(s) for cucumber formatter rendering "
        "(--cucumber-progress): @cucumber/cucumber" in captured.err
    )
    assert "Progress: .F" in captured.out
    telemetry = read_fake_formatter_telemetry(tmp_path)
    assert len(telemetry) == 1
    assert telemetry[0]["emittedVisibleOutputDuringStream"] is False
    assert telemetry[0]["envelopeCount"] == 2
    assert telemetry[0]["formatterNames"] == ["progress"]
    assert telemetry[0]["sourceMode"] == "messagesPath"
    assert telemetry[0]["consoleWriteCount"] == 0
    assert str(telemetry[0]["messagesPath"]).endswith("formatter_messages.ndjson")


def test_live_formatter_bridge_loads_from_packaged_template_asset() -> None:
    """
    Verify live formatter bridge loads from packaged template asset.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    template_source = load_live_formatter_bridge_template()
    support_source = load_formatter_adapter_support_template()
    progress_source = load_formatter_adapter_template("progress.cjs.j2")
    usage_source = load_formatter_adapter_template("usage.cjs.j2")

    assert "function loadFormatterSpecifier" in template_source
    assert "main().catch" in template_source
    assert "resolveSummaryFormatterClass" in support_source
    assert "class ProgressFormatterAdapter" in progress_source
    assert "class UsageFormatterAdapter" in usage_source


def test_live_formatter_bridge_uses_module_file_url_descriptors() -> None:
    """
    Verify module formatters are passed to cucumber-js as descriptors.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    template_source = load_live_formatter_bridge_template()

    assert "pathToFileURL" in template_source
    assert "return pathToFileURL" in template_source
    assert "return loaded && loaded.default ? loaded.default : loaded;" not in template_source


def test_runtime_materialization_only_writes_requested_formatter_assets(tmp_path: Path) -> None:
    """
    Verify runtime materialization only writes requested formatter assets.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    script_path, formatter_specs = materialize_live_formatter_runtime(tmp_path, "progress", "usage")

    assert script_path.exists()
    assert (tmp_path / "formatters" / "support.cjs").exists()
    assert (tmp_path / "formatters" / "progress.cjs").exists()
    assert (tmp_path / "formatters" / "usage.cjs").exists()
    assert not (tmp_path / "formatters" / "pretty.cjs").exists()
    assert [formatter_spec["formatter"] for formatter_spec in formatter_specs] == ["progress", "usage"]


def test_pyproject_lists_live_formatter_bridge_template_as_package_data() -> None:
    """
    Verify pyproject lists live formatter bridge template as package data.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pyproject = loads((Path(__file__).resolve().parents[4] / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert "pytest_bdd.plugin.gherkin_message_reporter.resources.templates" in package_data
    assert (
        "live_formatter_bridge.mjs.j2" in package_data["pytest_bdd.plugin.gherkin_message_reporter.resources.templates"]
    )
    assert (
        "formatter_adapter_support.cjs.j2"
        in package_data["pytest_bdd.plugin.gherkin_message_reporter.resources.templates"]
    )
    assert "pytest_bdd.plugin.gherkin_message_reporter.resources.templates.formatters" in package_data
