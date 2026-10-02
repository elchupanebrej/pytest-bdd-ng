from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import string
import sys
import tarfile
import venv
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from operator import attrgetter, itemgetter
from pathlib import Path
from typing import TYPE_CHECKING

from pytest import fixture

try:
    import pytest_httpserver

    HTTPServer = pytest_httpserver.HTTPServer
    pytest_plugins = ["pytest_httpserver.pytest_plugin"]
except ImportError:
    import pytest

    pytest_httpserver = None
    HTTPServer = None

    @fixture
    def httpserver():
        pytest.skip("pytest_httpserver is not installed")


from messages import Envelope  # type:ignore[attr-defined]
from pytest_cuke import given, step, then, when
from pytest_cuke.compatibility.pytest import assert_outcomes
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.utils import compose
from tests.support.testing_utils import data_table_to_dicts


@dataclass
class ConsumerProject:
    """An isolated installed-package consumer used by bootstrap contracts."""

    path: Path
    python: Path
    pytest: Path
    cuke: Path
    env: dict[str, str]
    artifact: Path
    pytest_result: subprocess.CompletedProcess[str] | None = None
    command_result: subprocess.CompletedProcess[str] | None = None
    validation_findings: list[dict[str, object]] | None = None


@fixture(scope="session")
def _pytest_cuke_artifacts(request, tmp_path_factory):
    project_root = Path(request.config.rootpath)
    artifact_dir = tmp_path_factory.mktemp("pytest-cuke-artifacts")
    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed-consumer contract requires uv to build distributions"
    result = subprocess.run(
        [uv_executable, "build", "--sdist", "--wheel", "--out-dir", str(artifact_dir), str(project_root)],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"could not build pytest-cuke artifacts:\n{result.stdout}\n{result.stderr}"
    sdists = list(artifact_dir.glob("pytest_cuke-*.tar.gz"))
    wheels = list(artifact_dir.glob("pytest_cuke-*.whl"))
    assert len(sdists) == 1, f"expected one sdist, found {sdists}"
    assert len(wheels) == 1, f"expected one wheel, found {wheels}"
    paths = {"wheel": wheels[0], "sdist": sdists[0]}
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    return {"paths": paths, "sha256": hashes}


@fixture(scope="session")
def _pytest_cuke_environments(_pytest_cuke_artifacts, tmp_path_factory):
    environment_root = tmp_path_factory.mktemp("pytest-cuke-venvs")
    consumer_interpreter = shutil.which("python3.10")
    assert consumer_interpreter, "the installed-consumer contract requires Python 3.10 or newer"
    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed-consumer contract requires uv to create isolated environments"
    environments = {}
    for distribution in ("wheel", "sdist"):
        artifact = _pytest_cuke_artifacts["paths"][distribution]
        environment_path = environment_root / distribution
        create_environment = subprocess.run(
            [uv_executable, "venv", "--python", consumer_interpreter, str(environment_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert create_environment.returncode == 0, (
            f"could not create {distribution} consumer environment:\n"
            f"{create_environment.stdout}\n{create_environment.stderr}"
        )
        python_path = environment_path / "bin" / "python"
        install = subprocess.run(
            [uv_executable, "pip", "install", "--python", str(python_path), str(artifact)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert install.returncode == 0, f"could not install {distribution}:\n{install.stdout}\n{install.stderr}"
        environments[distribution] = environment_path
    return environments


@given(
    re.compile(
        r"the pytest-cuke (?P<distribution>wheel|sdist) built from this checkout is installed in a fresh consumer project"
    ),
    target_fixture="consumer",
)
def install_pytest_cuke_consumer(distribution, _pytest_cuke_environments, _pytest_cuke_artifacts, tmp_path_factory):
    project_path = tmp_path_factory.mktemp("pytest-cuke-consumer")
    (project_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_features_dir = 'features'\ncuke_autoload = true\n",
        encoding="utf-8",
    )
    environment_path = _pytest_cuke_environments[distribution]
    binary_dir = environment_path / "bin"
    consumer_home = project_path / ".home"
    consumer_home.mkdir()
    environment = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTEST_CURRENT_TEST",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    ):
        environment.pop(name, None)
    environment.update(
        {
            "HOME": str(consumer_home),
            "PATH": f"{binary_dir}{os.pathsep}{os.defpath}",
            "PYTHONNOUSERSITE": "1",
        }
    )
    return ConsumerProject(
        path=project_path,
        python=binary_dir / "python",
        pytest=binary_dir / "pytest",
        cuke=binary_dir / "cuke",
        env=environment,
        artifact=_pytest_cuke_artifacts["paths"][distribution],
    )


@step(
    re.compile(r'consumer file "(?P<relative_path>[^\"]+)" contains:'),
)
def write_consumer_file(relative_path, consumer: ConsumerProject, step):
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    file_path = consumer.path / destination
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(step.doc_string.content, encoding="utf-8")


@step(re.compile(r'consumer file "(?P<relative_path>[^\"]+)" contains UTF-8 BOM and CRLF:'))
def write_consumer_file_with_bom_and_crlf(relative_path, consumer: ConsumerProject, step):
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    file_path = consumer.path / destination
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = step.doc_string.content.replace("\\t", "\t").replace("\r\n", "\n").replace("\r", "\n")
    file_path.write_bytes(b"\xef\xbb\xbf" + content.replace("\n", "\r\n").encode("utf-8"))


@step(re.compile(r'consumer empty file "(?P<relative_path>[^\"]+)" exists'))
def write_empty_consumer_file(relative_path, consumer: ConsumerProject):
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    file_path = consumer.path / destination
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"")


@step(re.compile(r'consumer file "(?P<relative_path>[^\"]+)" contains invalid UTF-8'))
def write_invalid_utf8_consumer_file(relative_path, consumer: ConsumerProject):
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    file_path = consumer.path / destination
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"name,tier\nAda,\xff\n")


@step(re.compile(r'consumer directory "(?P<relative_path>[^\"]+)" exists'))
def create_consumer_directory(relative_path, consumer: ConsumerProject):
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer directory paths must stay inside the consumer project")
    (consumer.path / destination).mkdir(parents=True, exist_ok=True)


@given("pytest configuration:")
def write_consumer_pytest_configuration(consumer: ConsumerProject, step):
    (consumer.path / "pyproject.toml").write_text(step.doc_string.content, encoding="utf-8")


@when(re.compile(r'I run installed pytest with arguments "(?P<arguments>[^\"]*)"'), target_fixture="pytest_run_result")
def run_consumer_pytest(arguments, consumer: ConsumerProject):
    result = subprocess.run(
        [str(consumer.pytest), *shlex.split(arguments)],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    consumer.pytest_result = result
    return result


@when(
    re.compile(r'I run pytest(?: in a subprocess)? with arguments "(?P<arguments>[^\"]*)"'),
    target_fixture="pytest_result",
)
def run_local_pytest_with_arguments(arguments, request, testdir, step):
    import os

    root = getattr(request.config, "rootpath", getattr(request.config, "rootdir", Path.cwd()))
    source_dir = str(Path(root) / "src")
    current_path = os.environ.get("PYTHONPATH", "")
    testdir.monkeypatch.setenv("PYTHONPATH", os.pathsep.join(filter(None, (source_dir, current_path))))
    cli_args = shlex.split(arguments)
    in_subprocess = "in a subprocess" in step.text
    runner = testdir.runpytest_subprocess if in_subprocess else testdir.runpytest_inprocess
    return runner(*cli_args)


@then(re.compile(r"pytest should exit with code (?P<exit_code>\d+)"))
def consumer_pytest_exit_status(exit_code: str, consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    assert result.returncode == int(exit_code), (
        f"pytest returned {result.returncode}:\n{result.stdout}\n{result.stderr}"
    )


@then("pytest should exit with a non-zero code")
def consumer_pytest_exit_nonzero(consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    assert result.returncode != 0, f"unexpected pytest success:\n{result.stdout}\n{result.stderr}"


@then("pytest output should explain the invalid feature directory")
def consumer_invalid_features_dir_message(consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    assert "feature directory must not be empty" in f"{result.stdout}\n{result.stderr}"


@then("pytest output should identify the invalid external Examples source")
def consumer_invalid_external_examples_source(consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert "External Examples source error" in output
    assert "row 2 has 1 columns; expected 2" in output
    assert str((consumer.path / "features/broken.feature").resolve()) in output
    assert str((consumer.path / "features/broken.csv").resolve()) in output
    for feature_name, source_name, diagnostic in (
        ("missing.feature", "missing.csv", "FileNotFoundError"),
        ("empty.feature", "empty.csv", "source is empty"),
        ("blank-header.feature", "blank-header.csv", "blank column"),
        ("invalid-encoding.feature", "invalid-encoding.csv", "UnicodeDecodeError"),
        ("unreadable.feature", "unreadable.csv", "IsADirectoryError"),
    ):
        assert diagnostic.lower() in output.lower(), output
        assert str((consumer.path / "features" / feature_name).resolve()) in output
        assert str((consumer.path / "features" / source_name).resolve()) in output


@then(re.compile(r"the test outcome should have (?P<count>\d+) passed scenarios"))
def consumer_passed_scenarios(count, consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    expected_summary = rf"\b{re.escape(count)} passed BDD scenarios, 0 failed, 0 skipped\b"
    assert re.search(expected_summary, output), output


@then("the installed distribution archive excludes harness and test assets")
def consumer_distribution_archive_is_runtime_only(consumer: ConsumerProject):
    if consumer.artifact.suffix == ".whl":
        with zipfile.ZipFile(consumer.artifact) as archive:
            members = archive.namelist()
    else:
        with tarfile.open(consumer.artifact, "r:gz") as archive:
            members = archive.getnames()

    forbidden_parts = {
        ".agents",
        ".github",
        ".planning",
        "docs",
        "examples",
        "features",
        "pytest_cuke_testing",
        "scripts",
        "tests",
    }
    leaked = [member for member in members if forbidden_parts.intersection(Path(member).parts)]
    assert not leaked, f"distribution archive contains non-runtime files: {leaked}"


@then("pytest terminal output should report 2 passed BDD scenarios")
def consumer_terminal_summary(consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    assert "2 passed BDD scenarios, 0 failed, 0 skipped" in f"{result.stdout}\n{result.stderr}"


@then(re.compile(r'consumer artifact "(?P<relative_path>[^\"]+)" should describe one feature with 2 passed scenarios'))
def consumer_cucumber_json_artifact(relative_path, consumer: ConsumerProject):
    report = json.loads((consumer.path / relative_path).read_text(encoding="utf-8"))
    assert len(report) == 1
    elements = report[0]["elements"]
    assert len(elements) == 2
    assert all(step["result"]["status"] == "passed" for scenario in elements for step in scenario["steps"])


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should be a valid Cucumber Messages stream for (?P<scenario_count>\d+) passed scenario and (?P<step_count>\d+) passed steps'
    )
)
def consumer_messages_artifact(relative_path, scenario_count, step_count, consumer: ConsumerProject):
    from messages import Envelope, TestCase, TestCaseFinished, TestCaseStarted, TestRunFinished, TestRunStarted
    from messages import TestStepFinished

    lines = (consumer.path / relative_path).read_text(encoding="utf-8").splitlines()
    envelopes = [Envelope.model_validate(json.loads(line)) for line in lines]
    messages = [
        message
        for envelope in envelopes
        for message in (
            envelope.test_case,
            envelope.test_case_started,
            envelope.pickle,
            envelope.test_case_finished,
            envelope.test_step_finished,
            envelope.test_run_started,
            envelope.test_run_finished,
        )
        if message is not None
    ]
    assert len([message for message in messages if isinstance(message, TestCase)]) == int(scenario_count)
    assert len([message for message in messages if isinstance(message, TestCaseStarted)]) == int(scenario_count)
    assert len([message for message in messages if isinstance(message, TestCaseFinished)]) == int(scenario_count)
    finished_steps = [message for message in messages if isinstance(message, TestStepFinished)]
    assert len(finished_steps) == int(step_count)
    assert all(message.test_step_result.status.value == "PASSED" for message in finished_steps)
    assert len([message for message in messages if isinstance(message, TestRunStarted)]) == 1
    run_finished = [message for message in messages if isinstance(message, TestRunFinished)]
    assert len(run_finished) == 1
    assert run_finished[0].success is True


@then("consumer reports should preserve external row identities, source URIs, Background steps, and outcomes")
def consumer_external_examples_reports(consumer: ConsumerProject):
    json_report = json.loads((consumer.path / "report.json").read_text(encoding="utf-8"))
    json_features = {Path(feature["uri"]).name: feature for feature in json_report}
    assert set(json_features) == {
        "users.feature",
        "inline-users.feature",
        "reported-users.feature",
        "markdown-users.feature.md",
    }

    def assert_json_rows(filename: str, row_values: set[str], expected_failed: set[str]) -> None:
        feature = json_features[filename]
        assert not feature["uri"].endswith(".csv")
        elements = feature["elements"]
        assert len(elements) == len(row_values)
        assert len({element["id"] for element in elements}) == len(row_values)
        seen_rows = set()
        for element in elements:
            step_names = [step["name"] for step in element["steps"]]
            assert step_names[0] in {
                "the lookup service is ready",
                "the user lookup service is ready",
                "the report session is open",
            }
            row_step = next(
                name for name in step_names if name.startswith("user row ") or name.startswith("the report row is ")
            )
            row_id = row_step.removeprefix("user row ").removeprefix("the report row is ").split()[0]
            seen_rows.add(row_id)
            step_statuses = {step["name"]: step["result"]["status"] for step in element["steps"]}
            assert step_statuses[step_names[0]] == "passed"
            result_step = next(
                name
                for name in step_names
                if name.startswith("looked up user ") or name.startswith("the report row result is ")
            )
            assert step_statuses[result_step] == ("failed" if row_id in expected_failed else "passed")
            source = element.get("external_examples_source")
            if filename in {"users.feature", "reported-users.feature", "markdown-users.feature.md"}:
                assert source is not None
                assert source["path"].endswith(
                    {
                        "users.feature": "users.csv",
                        "reported-users.feature": "report-users.csv",
                        "markdown-users.feature.md": "markdown-users.tab",
                    }[filename]
                )
                assert source["section_index"] == 1
                assert source["row_index"] in {1, 2}
                assert source["source_line"] == source["row_index"] + 1
                source_feature = consumer.path / "features" / filename
                marker_lines = [
                    line_number
                    for line_number, line in enumerate(source_feature.read_text(encoding="utf-8").splitlines(), start=1)
                    if "table:" in line
                ]
                assert source["marker_line"] in marker_lines
            else:
                assert source is None
        assert seen_rows == row_values

    assert_json_rows("users.feature", {"Ada", "Grace"}, set())
    assert_json_rows("inline-users.feature", {"Ada", "Grace"}, set())
    assert_json_rows("markdown-users.feature.md", {"Tina", "Maja"}, set())
    assert_json_rows("reported-users.feature", {"passed", "failed"}, {"failed"})

    def normalized_user_rows(filename: str) -> list[tuple[tuple[str, str], ...]]:
        return sorted(
            tuple((step["name"], step["result"]["status"]) for step in element["steps"])
            for element in json_features[filename]["elements"]
        )

    assert normalized_user_rows("users.feature") == normalized_user_rows("inline-users.feature")

    message_lines = (consumer.path / "messages.ndjson").read_text(encoding="utf-8").splitlines()
    envelopes = [json.loads(line) for line in message_lines]
    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    started = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    finished_steps = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    assert len(pickles) == len(cases) == len(started) == 8
    assert len({pickle["id"] for pickle in pickles}) == 8
    pickle_step_ids_all = [step["id"] for pickle in pickles for step in pickle["steps"]]
    assert len(pickle_step_ids_all) == len(set(pickle_step_ids_all))
    assert len(run_finished) == 1
    assert run_finished[0]["success"] is False

    from messages import Envelope

    for line in message_lines:
        Envelope.model_validate(json.loads(line))

    sources = [envelope["source"] for envelope in envelopes if "source" in envelope]
    assert {Path(source["uri"].removeprefix("file:")).name for source in sources} == {
        "users.feature",
        "inline-users.feature",
        "reported-users.feature",
        "markdown-users.feature.md",
    }
    source_by_name = {Path(source["uri"].removeprefix("file:")).name: source for source in sources}
    assert source_by_name["inline-users.feature"]["data"].find("Examples:") >= 0
    assert not any(source["uri"].endswith((".csv", ".tab")) for source in sources)

    documents = [envelope["gherkinDocument"] for envelope in envelopes if "gherkinDocument" in envelope]
    assert {Path(document["uri"].removeprefix("file:")).name for document in documents} == set(json_features)
    external_documents = {
        Path(document["uri"].removeprefix("file:")).name: document for document in documents if document.get("comments")
    }
    assert set(external_documents) == {"users.feature", "reported-users.feature", "markdown-users.feature.md"}
    for filename, document in external_documents.items():
        comment = document["comments"][0]
        expected_source_name = {
            "users.feature": "users.csv",
            "reported-users.feature": "report-users.csv",
            "markdown-users.feature.md": "markdown-users.tab",
        }[filename]
        assert comment["location"]["line"] > 0
        assert expected_source_name in comment["text"]
        feature_node = document["feature"]
        scenario_nodes = [child["scenario"] for child in feature_node["children"] if "scenario" in child]
        examples = [example for scenario in scenario_nodes for example in scenario["examples"]]
        assert examples
        for example in examples:
            assert example["tableHeader"]["location"]["line"] == 0
            assert all(row["location"]["line"] == 0 for row in example["tableBody"])

    document_ast_ids: dict[str, set[str]] = {}
    for document in documents:
        ast_node_ids: set[str] = set()
        for child in document["feature"]["children"]:
            scenario_node = child.get("scenario")
            if scenario_node is None:
                continue
            ast_node_ids.add(scenario_node["id"])
            for example in scenario_node["examples"]:
                ast_node_ids.add(example["id"])
                if header := example.get("tableHeader"):
                    ast_node_ids.add(header["id"])
                ast_node_ids.update(row["id"] for row in example["tableBody"])
        document_ast_ids[document["uri"]] = ast_node_ids

    case_pickle_ids = {case["id"]: case["pickleId"] for case in cases}
    pickle_step_ids = {pickle["id"]: [step["id"] for step in pickle["steps"]] for pickle in pickles}
    for case in cases:
        assert [test_step["pickleStepId"] for test_step in case["testSteps"]] == pickle_step_ids[case["pickleId"]]
    start_pickle_ids = {case_start["id"]: case_pickle_ids[case_start["testCaseId"]] for case_start in started}
    statuses_by_pickle: dict[str, list[str]] = defaultdict(list)
    for finished in finished_steps:
        statuses_by_pickle[start_pickle_ids[finished["testCaseStartedId"]]].append(
            finished["testStepResult"]["status"].lower()
        )

    found_report_rows = set()
    found_user_rows: dict[str, set[str]] = defaultdict(set)
    for pickle in pickles:
        filename = Path(pickle["uri"].removeprefix("file:")).name
        step_texts = [step["text"] for step in pickle["steps"]]
        assert filename in {
            "users.feature",
            "inline-users.feature",
            "reported-users.feature",
            "markdown-users.feature.md",
        }
        assert pickle["uri"].endswith(filename)
        assert not pickle["uri"].endswith(".csv") and not pickle["uri"].endswith(".tab")
        assert len(pickle["astNodeIds"]) == 2
        assert set(pickle["astNodeIds"]).issubset(document_ast_ids[pickle["uri"]])
        assert step_texts[0] in {
            "the lookup service is ready",
            "the report session is open",
        }
        assert statuses_by_pickle[pickle["id"]]
        assert len(statuses_by_pickle[pickle["id"]]) == len(pickle["steps"])
        if filename in {"users.feature", "inline-users.feature", "markdown-users.feature.md"}:
            assert all(status == "passed" for status in statuses_by_pickle[pickle["id"]])
            user_step = next(text for text in step_texts if text.startswith("user row "))
            found_user_rows[filename].add(user_step.removeprefix("user row ").split()[0])
            assert statuses_by_pickle[pickle["id"]][0] == "passed"
            if filename == "users.feature":
                assert "[external_examples:[section: 1, row:" in pickle["name"]
            if filename == "inline-users.feature":
                assert "[external_examples:" not in pickle["name"]
        else:
            identity_step = next(text for text in step_texts if text.startswith("the report row is "))
            identity = identity_step.removeprefix("the report row is ")
            found_report_rows.add(identity)
            expected_status = "failed" if identity == "failed" else "passed"
            assert expected_status in statuses_by_pickle[pickle["id"]]
    assert found_report_rows == {"passed", "failed"}
    assert found_user_rows == {
        "users.feature": {"Ada", "Grace"},
        "inline-users.feature": {"Ada", "Grace"},
        "markdown-users.feature.md": {"Tina", "Maja"},
    }


@then(re.compile(r'pytest help should not mention the legacy option "(?P<option>[a-z-]+)"'))
def consumer_help_rejects_legacy_options(option, consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    help_text = f"{result.stdout}\n{result.stderr}"
    assert f"--{option}" not in help_text
    assert "cucumber-" not in help_text
    assert "bdd-" not in help_text


@when(
    re.compile(r'I run command "(?P<command>pytest-cuke|cuke)" with arguments "(?P<arguments>[^\"]*)"'),
    target_fixture="command_run_result",
)
def run_consumer_command(command, arguments, consumer: ConsumerProject):
    executable = consumer.cuke if command == "cuke" else consumer.python.parent / command
    result = subprocess.run(
        [str(executable), *shlex.split(arguments)],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    consumer.command_result = result
    return result


@then(re.compile(r"the command should exit with code (?P<exit_code>\d+)"))
def consumer_command_exit_status(exit_code: str, consumer: ConsumerProject):
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    assert result.returncode == int(exit_code), (
        f"command returned {result.returncode}:\n{result.stdout}\n{result.stderr}"
    )


@then("the command should exit with a non-zero code")
def consumer_command_exit_nonzero(consumer: ConsumerProject):
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    assert result.returncode != 0, f"unexpected command success:\n{result.stdout}\n{result.stderr}"


@given(re.compile(r'consumer file "(?P<relative_path>[^\"]+)" has content:'))
def write_consumer_file_with_content(relative_path: str, consumer: ConsumerProject, step) -> None:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    target = consumer.path / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    content = step.doc_string.content.replace("{WHITESPACE_TITLE}", "   ")
    target.write_text(content, encoding="utf-8")


@given(re.compile(r'consumer file "(?P<relative_path>[^\"]+)" has invalid UTF-8 content'))
def write_consumer_file_with_invalid_utf8(relative_path: str, consumer: ConsumerProject) -> None:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    target = consumer.path / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"Feature: Invalid encoding\n\xff")


@then("the command JSON should include:")
def consumer_command_json_includes(consumer: ConsumerProject, step) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    actual = json.loads(result.stdout)
    expected = json.loads(step.doc_string.content)

    def assert_subset(expected_value: object, actual_value: object) -> None:
        if isinstance(expected_value, dict):
            assert isinstance(actual_value, dict)
            for key, value in expected_value.items():
                assert key in actual_value, f"JSON result has no {key!r}: {actual_value}"
                assert_subset(value, actual_value[key])
        elif isinstance(expected_value, list):
            assert isinstance(actual_value, list)
            assert len(actual_value) == len(expected_value), (expected_value, actual_value)
            for expected_item, actual_item in zip(expected_value, actual_value, strict=True):
                assert_subset(expected_item, actual_item)
        else:
            assert actual_value == expected_value, (expected_value, actual_value)

    assert_subset(expected, actual)


@then("the regular heading scan findings are stored")
def store_regular_heading_scan_findings(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    consumer.validation_findings = json.loads(result.stdout)["violations"]


@then("the advisory heading scan should preserve the regular findings")
def advisory_heading_scan_preserves_findings(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    assert consumer.validation_findings is not None, "the regular heading scan has not been stored"
    actual_findings = json.loads(result.stdout)["violations"]
    assert actual_findings == consumer.validation_findings


@then("the baseline audit should preserve identity fields")
def baseline_audit_preserves_identity_fields(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    payload = json.loads(result.stdout)
    assert payload["policy_id"] == "feature-heading-policy-v1"
    assert payload["run_id"].startswith("heading-scan-")
    assert payload["record_id"] == f"baseline-audit-{payload['run_id']}"


@then(re.compile(r'the command output should contain "(?P<expected>[^\"]+)"'))
def consumer_command_output_contains(expected: str, consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    assert expected.lower() in f"{result.stdout}\n{result.stderr}".lower()


@then(re.compile(r'pytest output should contain "(?P<expected>[^\"]+)"'))
def consumer_pytest_output_contains(expected: str, consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    assert expected.lower() in f"{result.stdout}\n{result.stderr}".lower()


@then(re.compile(r'the consumer file "(?P<relative_path>[^\"]+)" should (?P<state>exist|not exist)'))
def consumer_file_existence(relative_path: str, state: str, consumer: ConsumerProject) -> None:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    exists = (consumer.path / destination).exists()
    assert exists is (state == "exist"), f"consumer file {relative_path!r} exists={exists}"


@then("the command output should identify the installed pytest-cuke version")
def consumer_command_version_output(consumer: ConsumerProject):
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    assert result.returncode == 0
    assert re.search(r"pytest-cuke \d+\.\d+\.\d+", result.stdout)


@then("the command output should list the public subcommands")
def consumer_command_help_output(consumer: ConsumerProject):
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert all(path in output for path in ("validate <features-dir>", "generate steps", "convert allure"))


@then("the command help should show the required feature-directory argument")
def consumer_command_feature_directory_help(consumer: ConsumerProject):
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert "usage:" in output
    assert "features-dir" in output


@then("the command output should require a feature directory")
def consumer_command_requires_feature_directory(consumer: ConsumerProject):
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert "features-dir" in output
    assert "required" in output.lower()


@then("the unimplemented command should report that it is not implemented")
def consumer_unimplemented_command_output(consumer: ConsumerProject):
    result = consumer.command_result
    assert result is not None, "a standalone command has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}".lower()
    assert "not implemented" in output
    assert "validation passed" not in output
    assert "features are valid" not in output


if TYPE_CHECKING:  # pragma: no cover
    from pytest_cuke.compatibility.pytest import Testdir


@fixture
def httpserver_port(httpserver):
    return httpserver.port


@given(re.compile(r"File \"(?P<name>(\.|\w)+)(?P<extension>\.\w+)\" with (?P<extra_opts>.*|\s)content:"))
def write_file_with_extras(name, extension, testdir, step, request, extra_opts, tmp_path):
    content = step.doc_string.content
    is_fixture_templated = "fixture templated" in extra_opts
    if is_fixture_templated:
        template_fields = [field_name for _, field_name, _, _ in string.Formatter().parse(content) if field_name]

        format_options = dict(
            map(lambda fixture_name: (fixture_name, str(request.getfixturevalue(fixture_name))), template_fields)
        )
    file_data = str(content).format_map(format_options) if is_fixture_templated else content
    (Path(testdir.tmpdir.strpath) / f"{name}{extension}").write_text(file_data, encoding="utf-8")


@given(
    re.compile('File "(?P<name>\\w+)(?P<extension>\\.\\w+)" in the temporary path with content:'),
)
def write_file(name, extension, tmp_path: Path, step):
    content = step.doc_string.content
    (tmp_path / f"{name}{extension}").write_text(content)


@given(
    re.compile(r'Localserver endpoint "(?P<endpoint>.+)" responding content:'),
)
def test_feature_load_by_http_with_base_url(testdir, endpoint, httpserver: HTTPServer, step):
    httpserver.expect_request(endpoint).respond_with_data(
        step.doc_string.content,
        content_type=Mimetype.gherkin_plain.value,
    )
    yield


@given(re.compile("Set pytest.ini content to:"))
def _(testdir, step):
    content = step.doc_string.content
    testdir.makeini(content)


@step("run pytest", target_fixture="pytest_result")
def run_pytest(testdir: "Testdir", request, step):
    import os

    options_dict = data_table_to_dicts(step.data_table)
    is_sub = str(options_dict.get("subprocess", ["false"])[0]).lower() == "true"
    root = getattr(request.config, "rootpath", getattr(request.config, "rootdir", Path.cwd()))
    src_dir = str(Path(root) / "src")

    orig_pp = os.environ.get("PYTHONPATH", "")
    testdir.monkeypatch.setenv("PYTHONPATH", f"{src_dir}{os.pathsep}{orig_pp}" if orig_pp else src_dir)

    cli_args = list(options_dict.get("cli_args", []))
    if not is_sub:
        import sys

        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith("test_"):
                sys.modules.pop(mod_name, None)
        testrunner = testdir.runpytest_inprocess
    else:
        testrunner = testdir.runpytest_subprocess

    outcome = testrunner(*cli_args)

    yield outcome


@given("Install npm packages")
def _(testdir: "Testdir", step):
    options_dict = data_table_to_dicts(step.data_table)
    yield testdir.run(shutil.which("npm"), "install", "--silent", *options_dict.get("packages", []))


@step("pytest outcome must contain tests with statuses:")
def check_pytest_test_statuses(pytest_result, step):
    outcomes_kwargs = map(attrgetter("value"), step.data_table.rows[0].cells)
    outcomes_kwargs_values = map(compose(int, attrgetter("value")), step.data_table.rows[1].cells)
    outcome_result = dict(zip(outcomes_kwargs, outcomes_kwargs_values, strict=False))

    assert_outcomes(pytest_result, **outcome_result)


@step("pytest outcome must match lines:")
def check_pytest_stdout_lines(pytest_result, step):
    lines = list(map(compose(attrgetter("value"), itemgetter(0)), map(attrgetter("cells"), step.data_table.rows)))

    pytest_result.stdout.fnmatch_lines(lines)


@given(
    re.compile(r"Copy \"(?P<initial_path>(\w|\\|.)+)\" into \"(?P<final_path>(\w|\\|.)+)\""),
    converters={"initial_path": Path, "final_path": Path},
)
@given(
    re.compile(r"Copy path from \"(?P<initial_path>(\w|\\|.)+)\" to test path \"(?P<final_path>(\w|\\|.)+)\""),
    converters={"initial_path": Path, "final_path": Path},
)
def copy_file(testdir, request, initial_path: Path, final_path: Path):
    root = getattr(request.config, "rootpath", getattr(request.config, "rootdir", Path.cwd()))
    full_initial_path = (
        Path(root) / initial_path if (Path(root) / initial_path).exists() else Path(testdir.tmpdir) / initial_path
    )
    full_final_path = Path(testdir.tmpdir) / final_path
    if full_initial_path.is_file():
        full_final_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(full_initial_path, full_final_path)
    else:
        shutil.copytree(full_initial_path, full_final_path, dirs_exist_ok=True)


@then(
    re.compile(r"File \"(?P<file_path>(\w|\\|.)+)\" has \"(?P<line_count>(\w|\\|.)+)\" lines"),
    converters={"line_count": int, "file_path": Path},
)
def _(file_path: Path, line_count: int):
    with file_path.open("r") as fp:
        real_line_count = reduce(lambda _, last: last, map(itemgetter(0), enumerate(fp, start=1)), 0)  # type: ignore[no-any-return]
    assert line_count == real_line_count


@then(
    re.compile(r"File \"(?P<file_path>(\w|\\|.)+)\" is not empty"),
    converters={"file_path": Path},
)
def _(file_path: Path, testdir):
    assert (Path(str(testdir.tmpdir)) / file_path).stat().st_size != 0


@then(re.compile(r"Report \"(?P<file_path>(\w|\\|.)+)\" parsable into messages"), converters={"file_path": Path})
def _(file_path: Path):
    with file_path.open(mode="r") as ast_file:
        try:
            for raw_datum in ast_file:
                Envelope.model_validate(json.loads(raw_datum))
        except Exception as e:
            raise AssertionError from e


@given(re.compile(r'runtime source probe "(?P<name>[a-z][a-z0-9_]*)" contains:'))
def create_runtime_source_type_probe(name: str, request, step) -> None:
    project_root = Path(request.config.rootpath)
    source_root = project_root / "src" / "pytest_cuke"
    probe_path = source_root / f"_mypy_probe_{name}.py"
    if probe_path.exists():
        raise AssertionError(f"temporary runtime probe already exists: {probe_path}")
    probe_path.write_text(step.doc_string.content, encoding="utf-8")
    request.addfinalizer(lambda: probe_path.unlink(missing_ok=True))


@when("I run the authoritative runtime Mypy gate", target_fixture="typecheck_result")
def run_authoritative_runtime_mypy_gate(request):
    project_root = Path(request.config.rootpath)
    return subprocess.run(
        [sys.executable, str(project_root / "scripts" / "check_types.py")],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )


@when("I run the type-check adapter without Mypy installed", target_fixture="typecheck_result")
def run_typecheck_adapter_without_mypy(request, tmp_path):
    project_root = Path(request.config.rootpath)
    environment = tmp_path / "without-mypy"
    venv.EnvBuilder(with_pip=False).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return subprocess.run(
        [str(python), str(project_root / "scripts" / "check_types.py")],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )


@then(re.compile(r"the runtime type gate should fail with diagnostic \"(?P<code>[a-z-]+)\""))
def runtime_type_gate_has_expected_error(code: str, typecheck_result: subprocess.CompletedProcess[str]) -> None:
    output = f"{typecheck_result.stdout}\n{typecheck_result.stderr}"
    assert typecheck_result.returncode != 0, output
    assert f"[{code}]" in output, output


@then("the runtime type gate should pass with visible policy identity")
def runtime_type_gate_passes_with_policy_identity(typecheck_result: subprocess.CompletedProcess[str]) -> None:
    output = f"{typecheck_result.stdout}\n{typecheck_result.stderr}"
    assert typecheck_result.returncode == 0, output
    assert "MYPY_VERSION=2.3.1" in output, output
    assert "MYPY_CONFIG=" in output, output
    assert "MYPY_CONFIG_SHA256=" in output, output
    assert "MYPY_SCOPE=src/pytest_cuke" in output, output
    assert "MYPY_SCOPE_PY_FILES=" in output, output
    assert "MYPY_SCOPE_SHA256=" in output, output


@then("the type-check adapter should explain that Mypy is missing")
def typecheck_adapter_explains_missing_mypy(typecheck_result: subprocess.CompletedProcess[str]) -> None:
    output = f"{typecheck_result.stdout}\n{typecheck_result.stderr}"
    assert typecheck_result.returncode == 2, output
    assert "Mypy is not installed for this Python interpreter" in output, output
    assert "testtypes extra" in output, output
