from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import string
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
from tests.testing_utils import data_table_to_dicts


@dataclass
class ConsumerProject:
    """An isolated installed-package consumer used by bootstrap contracts."""

    path: Path
    python: Path
    pytest: Path
    cuke: Path
    env: dict[str, str]
    pytest_result: subprocess.CompletedProcess[str] | None = None
    command_result: subprocess.CompletedProcess[str] | None = None


@fixture(scope="session")
def _pytest_cuke_artifacts(request, tmp_path_factory):
    project_root = Path(request.config.rootpath)
    artifact_dir = tmp_path_factory.mktemp("pytest-cuke-artifacts")
    build_source = artifact_dir.parent / "pytest-cuke-package-source"
    build_source.mkdir()
    for filename in ("pyproject.toml", "setup.cfg", "README.rst", "LICENSE.rst"):
        shutil.copy2(project_root / filename, build_source / filename)
    shutil.copytree(
        project_root / "src",
        build_source / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed-consumer contract requires uv to build distributions"
    result = subprocess.run(
        [uv_executable, "build", "--sdist", "--wheel", "--out-dir", str(artifact_dir), str(build_source)],
        cwd=build_source,
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
def install_pytest_cuke_consumer(distribution, _pytest_cuke_environments, tmp_path_factory):
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
    )


@given(
    re.compile(r'consumer file "(?P<relative_path>[^\"]+)" contains:'),
)
def write_consumer_file(relative_path, consumer: ConsumerProject, step):
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    file_path = consumer.path / destination
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(step.doc_string.content, encoding="utf-8")


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


@then(re.compile(r"the test outcome should have (?P<count>\d+) passed scenarios"))
def consumer_passed_scenarios(count, consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    expected_summary = rf"\b{re.escape(count)} passed BDD scenarios, 0 failed, 0 skipped\b"
    assert re.search(expected_summary, output), output


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
