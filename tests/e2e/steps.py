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
import time
import venv
import zipfile
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from functools import reduce
from operator import attrgetter, itemgetter
from pathlib import Path, PurePosixPath
from textwrap import dedent
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlsplit

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


def _consumer_binary_dir(environment_path: Path) -> Path:
    return environment_path / ("Scripts" if os.name == "nt" else "bin")


def _consumer_executable(binary_dir: Path, name: str) -> Path:
    return binary_dir / (f"{name}.exe" if os.name == "nt" else name)


@dataclass
class ConsumerProject:
    """An isolated installed-package consumer used by bootstrap contracts."""

    path: Path
    python: Path
    pytest: Path
    cuke: Path
    env: dict[str, str]
    artifact: Path
    mypy: Path | None = None
    pytest_result: subprocess.CompletedProcess[str] | None = None
    command_result: subprocess.CompletedProcess[str] | None = None
    typecheck_result: subprocess.CompletedProcess[str] | None = None
    native_parity_result: subprocess.CompletedProcess[str] | None = None
    validation_findings: list[dict[str, object]] | None = None
    struct_bdd_selection_runs: list[subprocess.CompletedProcess[str]] | None = None
    struct_bdd_parity_domain_result: subprocess.CompletedProcess[str] | None = None
    struct_bdd_parity_runs: list[subprocess.CompletedProcess[str]] | None = None
    custom_parser_selection_runs: list[subprocess.CompletedProcess[str]] | None = None
    custom_parser_selection_records: list[list[dict[str, object]]] | None = None
    custom_parser_selection_reports: list[dict[str, object]] | None = None
    custom_parser_session_result: subprocess.CompletedProcess[str] | None = None
    pytest_watchdog_expired: bool = False
    second_group_started_before_release: bool | None = None
    concurrent_group_results: list[subprocess.CompletedProcess[str]] | None = None
    concurrent_group_events: list[dict[str, object]] | None = None
    feature_source_session_results: list[subprocess.CompletedProcess[str]] | None = None
    feature_url_session_results: list[subprocess.CompletedProcess[str]] | None = None


def _validate_messages_envelope_compatibly(payload: Any) -> Envelope:
    """Validate a copied v24 message with the bundled v22 model."""
    assert isinstance(payload, dict), f"Cucumber Messages envelope must be an object, got {type(payload).__name__}"
    validation_payload = deepcopy(payload)

    def remove_v24_exception_traces(value: Any) -> None:
        if isinstance(value, dict):
            exception = value.get("exception")
            if isinstance(exception, dict) and "stackTrace" in exception:
                stack_trace = exception["stackTrace"]
                assert isinstance(stack_trace, str), exception
                exception.pop("stackTrace")
            for child in value.values():
                remove_v24_exception_traces(child)
        elif isinstance(value, list):
            for child in value:
                remove_v24_exception_traces(child)

    remove_v24_exception_traces(validation_payload)
    return Envelope.model_validate(validation_payload)


@dataclass
class LocalFeatureHTTPFixture:
    """Small local HTTP server for installed-consumer feature source contracts."""

    base_url: str
    responses: dict[str, tuple[int, str, str]]

    def respond(self, path: str, content: str, status: int, content_type: str) -> None:
        self.responses[path] = (status, content, content_type)


@fixture
def local_feature_http_server():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    responses: dict[str, tuple[int, str, str]] = {}

    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            status, content, content_type = responses.get(self.path, (404, "not found", "text/plain"))
            body = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    local_server = LocalFeatureHTTPFixture(f"http://127.0.0.1:{server.server_port}", responses)
    try:
        yield local_server
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


@fixture(scope="session")
def _pytest_cuke_artifacts(request, tmp_path_factory):
    project_root = Path(request.config.rootpath)
    artifact_dir = tmp_path_factory.mktemp("pytest-cuke-artifacts")
    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed-consumer contract requires uv to build distributions"
    build_environment = os.environ.copy()
    build_environment["PYTEST_CUKE_BUILD_GO"] = "off"
    result = subprocess.run(
        [uv_executable, "build", "--sdist", "--wheel", "--out-dir", str(artifact_dir), str(project_root)],
        cwd=project_root,
        env=build_environment,
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
    assert sys.version_info >= (3, 10), "the installed-consumer contract requires Python 3.10 or newer"
    consumer_interpreter = sys.executable
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
        python_path = _consumer_executable(_consumer_binary_dir(environment_path), "python")
        install = subprocess.run(
            [uv_executable, "pip", "install", "--python", str(python_path), str(artifact)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert install.returncode == 0, f"could not install {distribution}:\n{install.stdout}\n{install.stderr}"
        environments[distribution] = environment_path
    return environments


@fixture(scope="session")
def _pytest_cuke_typing_environments(_pytest_cuke_artifacts, tmp_path_factory):
    environment_root = tmp_path_factory.mktemp("pytest-cuke-typing-venvs")
    assert sys.version_info >= (3, 10), "the installed-consumer contract requires Python 3.10 or newer"
    consumer_interpreter = sys.executable
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
            f"could not create {distribution} typing consumer environment:\n"
            f"{create_environment.stdout}\n{create_environment.stderr}"
        )
        python_path = _consumer_executable(_consumer_binary_dir(environment_path), "python")
        install = subprocess.run(
            [uv_executable, "pip", "install", "--python", str(python_path), str(artifact), "mypy==2.3.1"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert install.returncode == 0, (
            f"could not install {distribution} and pinned Mypy:\n{install.stdout}\n{install.stderr}"
        )
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
    binary_dir = _consumer_binary_dir(environment_path)
    consumer_home = project_path / ".home"
    consumer_home.mkdir()
    environment = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "MYPYPATH",
        "MYPY_CONFIG_FILE_DIR",
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
    if os.name == "nt":
        environment["USERPROFILE"] = str(consumer_home)
    return ConsumerProject(
        path=project_path,
        python=_consumer_executable(binary_dir, "python"),
        pytest=_consumer_executable(binary_dir, "pytest"),
        cuke=_consumer_executable(binary_dir, "cuke"),
        env=environment,
        artifact=_pytest_cuke_artifacts["paths"][distribution],
    )


@given(
    re.compile(
        r"the pytest-cuke (?P<distribution>wheel|sdist) built from this checkout is installed with pinned Mypy in a fresh consumer project"
    ),
    target_fixture="consumer",
)
def install_pytest_cuke_typing_consumer(
    distribution, _pytest_cuke_typing_environments, _pytest_cuke_artifacts, tmp_path_factory
):
    project_path = tmp_path_factory.mktemp("pytest-cuke-typing-consumer")
    (project_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_features_dir = 'features'\ncuke_autoload = true\n",
        encoding="utf-8",
    )
    environment_path = _pytest_cuke_typing_environments[distribution]
    binary_dir = _consumer_binary_dir(environment_path)
    consumer_home = project_path / ".home"
    consumer_home.mkdir()
    environment = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "MYPYPATH",
        "MYPY_CONFIG_FILE_DIR",
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
    if os.name == "nt":
        environment["USERPROFILE"] = str(consumer_home)
    return ConsumerProject(
        path=project_path,
        python=_consumer_executable(binary_dir, "python"),
        pytest=_consumer_executable(binary_dir, "pytest"),
        cuke=_consumer_executable(binary_dir, "cuke"),
        env=environment,
        artifact=_pytest_cuke_artifacts["paths"][distribution],
        mypy=_consumer_executable(binary_dir, "mypy"),
    )


@given("a host-built native pytest-cuke wheel is installed when supplied", target_fixture="consumer")
def install_host_built_native_consumer(tmp_path_factory):
    native_wheel = os.environ.get("PYTEST_CUKE_NATIVE_WHEEL", "").strip()
    if not native_wheel:
        from pytest import skip

        skip(
            "provide PYTEST_CUKE_NATIVE_WHEEL with an actual wheel built for this host; "
            "native package loading cannot be accepted with a mocked library"
        )

    artifact = Path(native_wheel).expanduser().resolve()
    if artifact.suffix != ".whl" or not artifact.is_file():
        raise AssertionError(f"PYTEST_CUKE_NATIVE_WHEEL must name an existing wheel: {artifact}")

    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed-consumer contract requires uv to create isolated environments"
    assert sys.version_info >= (3, 10), "the installed-consumer contract requires Python 3.10 or newer"
    consumer_interpreter = sys.executable

    project_path = tmp_path_factory.mktemp("pytest-cuke-native-consumer")
    (project_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_features_dir = 'features'\ncuke_autoload = true\n",
        encoding="utf-8",
    )
    environment_path = tmp_path_factory.mktemp("pytest-cuke-native-venv")
    create_environment = subprocess.run(
        [uv_executable, "venv", "--python", consumer_interpreter, str(environment_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert create_environment.returncode == 0, (
        f"could not create native consumer environment:\n{create_environment.stdout}\n{create_environment.stderr}"
    )

    binary_dir = _consumer_binary_dir(environment_path)
    python_path = _consumer_executable(binary_dir, "python")
    install = subprocess.run(
        [uv_executable, "pip", "install", "--python", str(python_path), str(artifact)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, f"could not install native wheel:\n{install.stdout}\n{install.stderr}"

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
    if os.name == "nt":
        environment["USERPROFILE"] = str(consumer_home)
    return ConsumerProject(
        path=project_path,
        python=python_path,
        pytest=_consumer_executable(binary_dir, "pytest"),
        cuke=_consumer_executable(binary_dir, "cuke"),
        env=environment,
        artifact=artifact,
    )


@when("I run the native parser model parity test in the installed consumer")
def run_native_parser_model_parity_test(consumer: ConsumerProject) -> None:
    checkout_root = Path(__file__).resolve().parents[2]
    source_test = checkout_root / "tests" / "unit" / "parser" / "test_native_go_model_parity.py"
    consumer_test = consumer.path / "test_native_go_model_parity.py"
    shutil.copy2(source_test, consumer_test)
    try:
        consumer.native_parity_result = subprocess.run(
            [
                str(consumer.pytest),
                "-q",
                "-p",
                "no:cuke",
                "--rootdir",
                str(consumer.path),
                str(consumer_test),
            ],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        consumer_test.unlink(missing_ok=True)


@then("the installed native wheel preserves the Python Feature model")
def installed_native_wheel_preserves_model(consumer: ConsumerProject) -> None:
    result = consumer.native_parity_result
    assert result is not None, "the installed native parser parity test has not been run"
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, f"native parser model parity failed:\n{output}"
    assert re.search(r"\b3 passed\b", output), f"native parser model parity did not run:\n{output}"


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


def _consumer_artifact_path(relative_path: str, consumer: ConsumerProject) -> Path:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer artifact paths must stay inside the consumer project")
    project_root = consumer.path.resolve()
    artifact_path = (project_root / destination).resolve()
    try:
        artifact_path.relative_to(project_root)
    except ValueError as exc:
        raise ValueError("consumer artifact paths must stay inside the consumer project") from exc
    return artifact_path


@given("the installed consumer has no Allure Python adapters or Node on PATH")
def consumer_has_no_allure_runtime_dependencies(consumer: ConsumerProject) -> None:
    consumer.env["PATH"] = str(consumer.python.parent)
    assert shutil.which("node", path=consumer.env["PATH"]) is None
    assert shutil.which("allure", path=consumer.env["PATH"]) is None
    probe = subprocess.run(
        [
            str(consumer.python),
            "-c",
            "from importlib.metadata import PackageNotFoundError, distribution\n"
            "for name in ('allure-python-commons', 'allure-pytest'):\n"
            "    try:\n"
            "        distribution(name)\n"
            "    except PackageNotFoundError:\n"
            "        continue\n"
            "    raise SystemExit(f'unexpected Allure adapter installed: {name}')\n",
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, f"unexpected Allure runtime dependency: {probe.stdout}\n{probe.stderr}"


@when(re.compile(r'I remove consumer file "(?P<relative_path>[^\"]+)"'))
def remove_consumer_file(relative_path: str, consumer: ConsumerProject) -> None:
    target = _consumer_artifact_path(relative_path, consumer)
    if not target.is_file():
        raise ValueError(f"consumer file does not exist: {relative_path}")
    target.unlink()


@step(re.compile(r'consumer file "(?P<relative_path>[^\"]+)" contains UTF-8 BOM and CRLF:'))
def write_consumer_file_with_bom_and_crlf(relative_path, consumer: ConsumerProject, step):
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    file_path = consumer.path / destination
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = step.doc_string.content.replace("\\t", "\t").replace("\r\n", "\n").replace("\r", "\n")
    file_path.write_bytes(b"\xef\xbb\xbf" + content.replace("\n", "\r\n").encode("utf-8"))


@step(re.compile(r'consumer file "(?P<relative_path>[^\"]+)" contains text encoded as "(?P<encoding>[^\"]+)":'))
def write_consumer_file_with_encoding(relative_path, encoding, consumer: ConsumerProject, step):
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    file_path = consumer.path / destination
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(step.doc_string.content.encode(encoding))


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


@when(re.compile(r'I remove write permission from consumer directory "(?P<relative_path>[^\"]+)"'))
def remove_consumer_directory_write_permission(relative_path: str, consumer: ConsumerProject) -> None:
    from pytest import skip

    if os.name == "nt":
        skip("Windows does not enforce POSIX directory write permission bits")
    directory = _consumer_artifact_path(relative_path, consumer)
    if not directory.is_dir():
        raise ValueError(f"consumer directory does not exist: {relative_path}")
    directory.chmod(0o555)
    assert directory.stat().st_mode & 0o222 == 0, directory

    probe = directory / ".pytest-cuke-write-probe"
    try:
        probe.write_text("permission probe", encoding="utf-8")
    except PermissionError:
        return
    probe.unlink()
    directory.chmod(0o755)
    skip("the consumer filesystem does not enforce removed directory write permissions")


@when(re.compile(r'I restore write permission to consumer directory "(?P<relative_path>[^\"]+)"'))
def restore_consumer_directory_write_permission(relative_path: str, consumer: ConsumerProject) -> None:
    _consumer_artifact_path(relative_path, consumer).chmod(0o755)


@then(re.compile(r'consumer directory "(?P<relative_path>[^\"]+)" should remain empty'))
def consumer_directory_is_empty(relative_path: str, consumer: ConsumerProject) -> None:
    directory = _consumer_artifact_path(relative_path, consumer)
    assert directory.is_dir(), f"consumer directory does not exist: {relative_path}"
    contents = list(directory.iterdir())
    assert not contents, f"consumer directory should be empty: {contents!r}"


@given("pytest configuration:")
def write_consumer_pytest_configuration(consumer: ConsumerProject, step):
    (consumer.path / "pyproject.toml").write_text(step.doc_string.content, encoding="utf-8")


@given(re.compile(r'the local HTTP fixture serves feature endpoint "(?P<path>[^\"]+)":'))
def serve_local_http_feature_endpoint(path: str, local_feature_http_server: LocalFeatureHTTPFixture, step) -> None:
    local_feature_http_server.respond(
        path,
        step.doc_string.content,
        status=200,
        content_type=Mimetype.gherkin_plain.value,
    )


@given(re.compile(r'the local HTTP fixture returns status (?P<status>\d+) for feature endpoint "(?P<path>[^\"]+)"'))
def local_http_feature_endpoint_returns_status(
    path: str, status: str, local_feature_http_server: LocalFeatureHTTPFixture
) -> None:
    local_feature_http_server.respond(path, "not found", status=int(status), content_type="text/plain")


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
    re.compile(
        r'I run installed pytest from consumer directory "(?P<working_directory>[^\"]+)" '
        r'with arguments "(?P<arguments>[^\"]*)"'
    ),
    target_fixture="pytest_result",
)
def run_consumer_pytest_from_consumer_directory(working_directory, arguments, consumer: ConsumerProject):
    destination = Path(working_directory)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer working directories must stay inside the consumer project")
    cwd = consumer.path / destination
    if not cwd.is_dir():
        raise ValueError(f"consumer working directory does not exist: {cwd}")
    command = [
        str(consumer.pytest),
        *shlex.split(arguments.replace("{consumer_path}", str(consumer.path))),
    ]
    result = subprocess.run(
        command,
        cwd=cwd,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    consumer.pytest_result = result
    return result


@when(
    re.compile(
        r'I run installed pytest in two independent sessions with arguments "(?P<first_arguments>[^\"]*)" '
        r'and then "(?P<second_arguments>[^\"]*)"'
    ),
    target_fixture="pytest_results",
)
def run_consumer_pytest_in_two_independent_sessions(first_arguments, second_arguments, consumer: ConsumerProject):
    results = []
    for arguments in (first_arguments, second_arguments):
        result = subprocess.run(
            [str(consumer.pytest), *shlex.split(arguments)],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
        )
        results.append(result)
    consumer.feature_source_session_results = results
    consumer.pytest_result = results[-1]
    return results


@when(
    re.compile(
        r"I run installed pytest in two independent URL-base sessions with the local HTTP fixture and arguments "
        r'"(?P<first_arguments>[^\"]*)" and then "(?P<second_arguments>[^\"]*)"'
    ),
    target_fixture="pytest_results",
)
def run_consumer_pytest_in_two_independent_url_base_sessions(
    first_arguments: str,
    second_arguments: str,
    consumer: ConsumerProject,
    local_feature_http_server: LocalFeatureHTTPFixture,
):
    results = []
    for arguments in (first_arguments, second_arguments):
        command = [
            str(consumer.pytest),
            *shlex.split(arguments.replace("{local_http_base_url}", local_feature_http_server.base_url)),
        ]
        result = subprocess.run(
            command,
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
        )
        results.append(result)
    consumer.feature_url_session_results = results
    consumer.pytest_result = results[-1]
    return results


@when(
    re.compile(r'I run installed pytest with the local HTTP fixture URL base and arguments "(?P<arguments>[^\"]*)"'),
    target_fixture="pytest_result",
)
def run_consumer_pytest_with_local_http_fixture_url_base(
    arguments: str,
    consumer: ConsumerProject,
    local_feature_http_server: LocalFeatureHTTPFixture,
):
    http_base_url = local_feature_http_server.base_url
    environment = consumer.env.copy()
    environment["PYTEST_CUKE_TEST_HTTP_BASE_URL"] = http_base_url
    command = [
        str(consumer.pytest),
        *shlex.split(arguments.replace("{local_http_base_url}", http_base_url)),
    ]
    result = subprocess.run(
        command,
        cwd=consumer.path,
        env=environment,
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


@then("both independent pytest sessions should execute exactly one selected root scenario")
def independent_pytest_sessions_execute_selected_root_scenarios(consumer: ConsumerProject) -> None:
    results = consumer.feature_source_session_results
    assert results is not None and len(results) == 2, "the independent pytest sessions have not completed"
    expected_summary = re.compile(r"\b1 passed BDD scenarios, 0 failed, 0 skipped\b")
    scenario_names = ("The first local root is selected", "The second local root is selected")
    for index, result in enumerate(results, start=1):
        output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode == 0, f"independent pytest session {index} failed:\n{output}"
        assert expected_summary.search(output), (
            f"independent pytest session {index} did not run exactly one passing root scenario:\n{output}"
        )
        expected_name = scenario_names[index - 1]
        unexpected_name = scenario_names[1 - (index - 1)]
        assert expected_name in output, f"session {index} did not name its selected root scenario:\n{output}"
        assert unexpected_name not in output, f"session {index} also reported the other root scenario:\n{output}"


@then("both independent URL-base sessions should execute only their selected URL source")
def independent_pytest_sessions_execute_selected_url_sources(consumer: ConsumerProject) -> None:
    results = consumer.feature_url_session_results
    assert results is not None and len(results) == 2, "the independent URL-base sessions have not completed"
    expected_summary = re.compile(r"\b1 passed BDD scenarios, 0 failed, 0 skipped\b")
    for index, result in enumerate(results, start=1):
        output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode == 0, f"independent URL-base session {index} failed:\n{output}"
        assert expected_summary.search(output), (
            f"independent URL-base session {index} did not run exactly one passing source scenario:\n{output}"
        )


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
        ("unreadable.feature", "unreadable.csv", None),
    ):
        if diagnostic is None:
            assert any(error_name in output for error_name in ("IsADirectoryError", "PermissionError")), output
        else:
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
        "pytest_cuke_test_support",
        "test_support",
        "_test_support",
        "scripts",
        "tests",
    }
    leaked = [member for member in members if forbidden_parts.intersection(Path(member).parts)]
    assert not leaked, f"distribution archive contains non-runtime files: {leaked}"


@then("the installed archive publishes type metadata for both public facades")
def consumer_archive_publishes_public_type_metadata(consumer: ConsumerProject) -> None:
    if consumer.artifact.suffix == ".whl":
        with zipfile.ZipFile(consumer.artifact) as archive:
            members = archive.namelist()
    else:
        with tarfile.open(consumer.artifact, "r:gz") as archive:
            members = archive.getnames()

    normalized_members = {PurePosixPath(member).as_posix() for member in members}
    required_suffixes = (
        "pytest_cuke/py.typed",
        "pytest_cuke/__init__.py",
        "pytest_cuke/parsers/__init__.py",
    )
    missing = [
        suffix
        for suffix in required_suffixes
        if not any(member == suffix or member.endswith(f"/{suffix}") for member in normalized_members)
    ]
    assert not missing, f"installed {consumer.artifact.suffix} is missing public typed package files: {missing}"


@when(
    re.compile(r'I run pinned Mypy on consumer file "(?P<relative_path>[^"]+)"'),
    target_fixture="consumer_mypy_result",
)
def run_pinned_mypy_on_consumer_file(relative_path: str, consumer: ConsumerProject):
    if consumer.mypy is None:
        raise AssertionError("the consumer environment does not include the pinned Mypy checker")
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer type-check paths must stay inside the consumer project")
    result = subprocess.run(
        [
            str(consumer.mypy),
            "--strict",
            "--show-error-codes",
            "--no-error-summary",
            "--no-incremental",
            "--python-executable",
            str(consumer.python),
            str(consumer.path / destination),
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    consumer.typecheck_result = result
    return result


@then("pinned Mypy should accept the typed canonical facade example")
def consumer_mypy_accepts_public_facade_example(consumer: ConsumerProject) -> None:
    result = consumer.typecheck_result
    assert result is not None, "Mypy has not checked the installed consumer example"
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output


@then("pinned Mypy should reject the invalid scenario facade argument")
def consumer_mypy_rejects_invalid_scenario_facade_argument(consumer: ConsumerProject) -> None:
    result = consumer.typecheck_result
    assert result is not None, "Mypy has not checked the installed consumer example"
    output = f"{result.stdout}\n{result.stderr}"
    error_codes = re.findall(r"\[([a-z-]+)\]", output)
    assert result.returncode != 0, f"Mypy accepted an invalid public facade call:\n{output}"
    assert error_codes == ["arg-type"], f"Mypy reported unexpected diagnostics: {error_codes}\n{output}"
    assert 'Argument 1 to "scenario"' in output, output


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


@then(re.compile(r'consumer artifact "(?P<relative_path>[^"]+)" should report both explicitly bound scenarios'))
def consumer_explicit_bindings_json_artifact(relative_path: str, consumer: ConsumerProject) -> None:
    report = json.loads((consumer.path / relative_path).read_text(encoding="utf-8"))
    assert len(report) == 1, report
    scenarios = report[0]["elements"]
    assert {scenario["name"] for scenario in scenarios} == {
        "Bound with scenario",
        "Bound with scenarios",
    }, report
    assert all(step["result"]["status"] == "passed" for scenario in scenarios for step in scenario["steps"]), report


@then(re.compile(r'consumer artifact "(?P<relative_path>[^\"]+)" should report feature URI "(?P<expected_uri>[^\"]+)"'))
def consumer_cucumber_json_feature_uri(relative_path: str, expected_uri: str, consumer: ConsumerProject) -> None:
    report = json.loads((consumer.path / relative_path).read_text(encoding="utf-8"))
    assert len(report) == 1, report
    actual_uri = report[0].get("uri")
    assert actual_uri == expected_uri, f"expected feature URI {expected_uri!r}, got {actual_uri!r}"


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should be a valid Cucumber Messages stream for (?P<scenario_count>\d+) passed scenario and (?P<step_count>\d+) passed steps'
    )
)
def consumer_messages_artifact(relative_path, scenario_count, step_count, consumer: ConsumerProject):
    from messages import Envelope, TestCase, TestCaseFinished, TestCaseStarted, TestRunFinished, TestRunStarted
    from messages import TestStepFinished

    lines = (consumer.path / relative_path).read_text(encoding="utf-8").splitlines()
    envelopes = [_validate_messages_envelope_compatibly(json.loads(line)) for line in lines]
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


@then(
    re.compile(
        r'consumer Messages artifact "(?P<relative_path>[^"]+)" should preserve the failed step diagnostics '
        r"and attachment correlations"
    )
)
def consumer_messages_failure_attachment_correlations(relative_path: str, consumer: ConsumerProject) -> None:
    from base64 import b64decode

    from messages import ContentEncoding

    artifact_path = _consumer_artifact_path(relative_path, consumer)
    envelopes = []
    raw_payloads: list[dict[str, Any]] = []
    for line in artifact_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        assert isinstance(payload, dict), payload
        raw_payloads.append(payload)
        envelopes.append(_validate_messages_envelope_compatibly(payload))

    def payloads(kind: str) -> list[Any]:
        return [
            payload
            for envelope in envelopes
            if (payload := getattr(envelope, kind)) is not None
        ]

    def one(kind: str) -> Any:
        matches = payloads(kind)
        assert len(matches) == 1, f"expected one {kind} message, found {len(matches)}"
        return matches[0]

    def raw_one(kind: str) -> dict[str, Any]:
        matches = [payload[kind] for payload in raw_payloads if isinstance(payload.get(kind), dict)]
        assert len(matches) == 1, f"expected one raw {kind} message, found {len(matches)}"
        return matches[0]

    meta = raw_one("meta")
    assert meta.get("protocolVersion") == "24.0.0", meta
    pickle_message = one("pickle")
    test_case = one("test_case")
    case_started = one("test_case_started")
    case_finished = one("test_case_finished")
    run_finished = one("test_run_finished")
    assert test_case.pickle_id == pickle_message.id
    assert case_started.test_case_id == test_case.id
    assert case_finished.test_case_started_id == case_started.id
    assert run_finished.success is False
    assert len(test_case.test_steps) == 1, test_case
    test_step = test_case.test_steps[0]

    step_started = one("test_step_started")
    step_finished = one("test_step_finished")
    assert step_started.test_case_started_id == case_started.id
    assert step_started.test_step_id == test_step.id
    assert step_finished.test_case_started_id == case_started.id
    assert step_finished.test_step_id == test_step.id
    assert step_finished.test_step_result.status.value == "FAILED"
    assert step_finished.test_step_result.message == "failure sentinel"
    exception = step_finished.test_step_result.exception
    assert exception is not None
    assert exception.type == "AssertionError"
    assert exception.message == "failure sentinel"

    raw_step_finished = raw_one("testStepFinished")
    raw_result = raw_step_finished.get("testStepResult")
    assert isinstance(raw_result, dict), raw_step_finished
    assert raw_result.get("message") == "failure sentinel", raw_result
    raw_exception = raw_result.get("exception")
    assert isinstance(raw_exception, dict), raw_result
    assert raw_exception.get("type") == "AssertionError", raw_exception
    assert raw_exception.get("message") == "failure sentinel", raw_exception
    stack_trace = raw_exception.get("stackTrace")
    assert isinstance(stack_trace, str) and stack_trace.strip(), raw_exception
    assert "AssertionError: failure sentinel" in stack_trace, raw_exception

    attachments = payloads("attachment")
    assert len(attachments) == 2, attachments
    assert all(attachment.test_case_started_id == case_started.id for attachment in attachments), attachments
    assert all(attachment.test_step_id == test_step.id for attachment in attachments), attachments
    attachments_by_name = {attachment.file_name: attachment for attachment in attachments}
    assert len(attachments_by_name) == len(attachments), attachments
    assert set(attachments_by_name) == {"identity.txt", "binary.bin"}, attachments_by_name

    identity = attachments_by_name["identity.txt"]
    assert ContentEncoding(identity.content_encoding) == ContentEncoding.identity
    assert identity.media_type == "text/plain"
    assert identity.body == "identity evidence"

    binary = attachments_by_name["binary.bin"]
    assert ContentEncoding(binary.content_encoding) == ContentEncoding.base64
    assert binary.media_type == "application/octet-stream"
    assert b64decode(binary.body, validate=True) == b"\x00\xffbinary evidence"


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
        _validate_messages_envelope_compatibly(json.loads(line))

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


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^\"]+)" should contain one result for scenario '
        r'"(?P<scenario_name>[^\"]+)" with passed step "(?P<step_name>[^\"]+)" and one linked container'
    )
)
def consumer_allure_result_directory_has_one_passed_step(
    relative_path: str,
    scenario_name: str,
    step_name: str,
    consumer: ConsumerProject,
) -> None:
    directory = Path(relative_path)
    if directory.is_absolute() or ".." in directory.parts:
        raise ValueError("consumer artifact paths must stay inside the consumer project")
    result_directory = consumer.path / directory
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    assert isinstance(result.get("uuid"), str) and result["uuid"], result
    assert result.get("name") == scenario_name, result
    assert result.get("status") == "passed", result
    assert result.get("stage") == "finished", result
    assert isinstance(result.get("start"), int) and isinstance(result.get("stop"), int), result
    assert result["start"] <= result["stop"], result
    assert (result["start"], result["stop"]) == (1700000001000, 1700000003000), result
    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 1, result
    step_result = steps[0]
    assert isinstance(step_result, dict), step_result
    assert step_result.get("name") == step_name, step_result
    assert step_result.get("status") == "passed", step_result
    assert step_result.get("stage") == "finished", step_result
    assert isinstance(step_result.get("start"), int) and isinstance(step_result.get("stop"), int), step_result
    assert step_result["start"] <= step_result["stop"], step_result
    assert (step_result["start"], step_result["stop"]) == (1700000002000, 1700000002001), step_result

    container_files = sorted(result_directory.glob("*-container.json"))
    assert len(container_files) == 1, f"expected one Allure container file, found {container_files!r}"
    container = json.loads(container_files[0].read_text(encoding="utf-8"))
    assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
    container_uuid = container.get("uuid")
    assert isinstance(container_uuid, str) and container_uuid, container
    assert container_files[0].name == f"{container_uuid}-container.json", container
    children = container.get("children")
    assert isinstance(children, list) and result["uuid"] in children, container
    befores = container.get("befores")
    assert isinstance(befores, list) and len(befores) == 1, container
    before = befores[0]
    assert isinstance(before, dict), before
    assert before.get("name") == "Before setup", before
    assert before.get("status") == "passed", before
    assert before.get("stage") == "finished", before
    assert isinstance(before.get("start"), int) and isinstance(before.get("stop"), int), before
    assert before["start"] <= before["stop"], before
    assert (before["start"], before["stop"]) == (1700000001100, 1700000001200), before
    afters = container.get("afters")
    assert isinstance(afters, list) and len(afters) == 1, container
    after = afters[0]
    assert isinstance(after, dict), after
    assert after.get("name") == "After cleanup", after
    assert after.get("status") == "passed", after
    assert after.get("stage") == "finished", after
    assert isinstance(after.get("start"), int) and isinstance(after.get("stop"), int), after
    assert after["start"] <= after["stop"], after
    assert (after["start"], after["stop"]) == (1700000002100, 1700000002200), after


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^\"]+)" should emit two retry attempts for scenario '
        r'"(?P<scenario_name>[^\"]+)" with linked containers'
    )
)
def consumer_allure_retry_attempts(relative_path: str, scenario_name: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 2, f"expected two Allure retry results, found {result_files!r}"

    results_by_uuid: dict[str, dict[str, Any]] = {}
    for result_file in result_files:
        result = json.loads(result_file.read_text(encoding="utf-8"))
        assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
        result_uuid = result.get("uuid")
        assert isinstance(result_uuid, str) and result_uuid, result
        assert result_file.name == f"{result_uuid}-result.json", result
        assert result.get("name") == scenario_name, result
        assert result.get("stage") == "finished", result
        results_by_uuid[result_uuid] = result

    ordered_results = sorted(results_by_uuid.values(), key=lambda result: result.get("start", -1))
    assert [result.get("status") for result in ordered_results] == ["failed", "passed"], ordered_results
    assert [result.get("start") for result in ordered_results] == [1700000001000, 1700000004000], ordered_results
    assert [result.get("stop") for result in ordered_results] == [1700000003000, 1700000006000], ordered_results
    for result, expected_step_status in zip(ordered_results, ("failed", "passed"), strict=True):
        steps = result.get("steps")
        assert isinstance(steps, list) and len(steps) == 1, result
        assert isinstance(steps[0], dict), steps
        assert steps[0].get("name") == "the retryable operation", steps[0]
        assert steps[0].get("status") == expected_step_status, steps[0]

    container_files = sorted(result_directory.glob("*-container.json"))
    assert len(container_files) == len(results_by_uuid), container_files
    linked_results: list[str] = []
    for container_file in container_files:
        container = json.loads(container_file.read_text(encoding="utf-8"))
        assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
        container_uuid = container.get("uuid")
        assert isinstance(container_uuid, str) and container_uuid, container
        assert container_file.name == f"{container_uuid}-container.json", container
        children = container.get("children")
        assert isinstance(children, list) and len(children) == 1, container
        linked_results.append(children[0])
    assert len(linked_results) == len(set(linked_results)) == 2, linked_results
    assert set(linked_results) == set(results_by_uuid), {"results": results_by_uuid, "containers": linked_results}


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should map skipped, undefined, ambiguous, '
        r"pending, and unknown to their Allure statuses with scenario status broken"
    )
)
def consumer_allure_status_mappings(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    assert result_files[0].name == f"{result_uuid}-result.json", result
    assert result.get("name") == "Mixed outcome scenario", result
    assert result.get("status") == "broken", result
    assert result.get("stage") == "finished", result

    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 5, result
    assert all(isinstance(item, dict) for item in steps), steps
    assert [item.get("name") for item in steps] == [
        "the skipped operation",
        "the undefined operation",
        "the ambiguous operation",
        "the pending operation",
        "the unknown operation",
    ], steps
    assert [item.get("status") for item in steps] == ["skipped", "broken", "broken", "broken", "unknown"], steps
    assert all(item.get("stage") == "finished" for item in steps), steps

    container_files = sorted(result_directory.glob("*-container.json"))
    assert len(container_files) == 1, f"expected one Allure container file, found {container_files!r}"
    container = json.loads(container_files[0].read_text(encoding="utf-8"))
    assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
    container_uuid = container.get("uuid")
    assert isinstance(container_uuid, str) and container_uuid, container
    assert container_files[0].name == f"{container_uuid}-container.json", container
    assert container.get("children") == [result_uuid], container


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve deterministic '
        r'run-finished diagnostics from "(?P<messages_path>[^"]+)" and keep the scenario passed'
    )
)
def consumer_allure_run_finished_diagnostics(
    relative_path: str,
    messages_path: str,
    consumer: ConsumerProject,
) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    assert result_files[0].name == f"{result_uuid}-result.json", result
    assert result.get("name") == "Run diagnostic scenario", result
    assert result.get("status") == "passed", result
    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 1, result
    assert isinstance(steps[0], dict), steps[0]
    assert steps[0].get("name") == "the successful operation", steps[0]
    assert steps[0].get("status") == "passed", steps[0]

    references = result.get("attachments")
    assert isinstance(references, list) and len(references) == 1, result
    reference = references[0]
    assert isinstance(reference, dict), reference
    assert reference.get("name") == "Cucumber test run diagnostics", reference
    assert reference.get("type") == "application/json", reference
    source = reference.get("source")
    assert isinstance(source, str) and source, reference
    relative_source = PurePosixPath(source)
    assert (
        not relative_source.is_absolute()
        and ".." not in relative_source.parts
        and "\\" not in source
        and re.match(r"^[A-Za-z]:", source) is None
    ), reference
    attachment_path = result_directory.joinpath(*relative_source.parts).resolve()
    try:
        attachment_path.relative_to(result_directory.resolve())
    except ValueError as exc:
        raise AssertionError(f"attachment source escapes the Allure result directory: {source!r}") from exc
    assert attachment_path.is_file(), f"Allure run diagnostic attachment is missing: {source!r}"

    expected_diagnostics = {
        "success": False,
        "message": "run summary sentinel",
        "exception": {
            "type": "RuntimeError",
            "message": "run exception sentinel",
            "stackTrace": (
                "Traceback (most recent call last):\n"
                '  File "runner.py", line 42, in run\n'
                "RuntimeError: run exception sentinel"
            ),
        },
    }
    input_path = _consumer_artifact_path(messages_path, consumer)
    run_finished_payloads: list[dict[str, Any]] = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict) and isinstance(payload.get("testRunFinished"), dict):
            run_finished_payloads.append(payload["testRunFinished"])
    assert len(run_finished_payloads) == 1, run_finished_payloads
    assert run_finished_payloads[0].get("success") is False, run_finished_payloads[0]
    assert run_finished_payloads[0].get("message") == expected_diagnostics["message"], run_finished_payloads[0]
    assert run_finished_payloads[0].get("exception") == expected_diagnostics["exception"], run_finished_payloads[0]
    expected_bytes = (json.dumps(expected_diagnostics, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    actual_bytes = attachment_path.read_bytes()
    assert actual_bytes == expected_bytes, reference
    assert json.loads(actual_bytes) == expected_diagnostics, reference

    container_files = sorted(result_directory.glob("*-container.json"))
    assert len(container_files) == 1, f"expected one Allure container file, found {container_files!r}"
    container = json.loads(container_files[0].read_text(encoding="utf-8"))
    assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
    container_uuid = container.get("uuid")
    assert isinstance(container_uuid, str) and container_uuid, container
    assert container_files[0].name == f"{container_uuid}-container.json", container
    assert container.get("children") == [result_uuid], container


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve the success-only '
        r"run-finished JSON and keep the scenario passed"
    )
)
def consumer_allure_run_finished_success_only(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, result_files
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), result
    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    assert result_files[0].name == f"{result_uuid}-result.json", result
    assert result.get("name") == "Run status-only scenario", result
    assert result.get("status") == "passed", result
    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 1, result
    assert isinstance(steps[0], dict), steps
    assert steps[0].get("name") == "the successful operation", steps[0]
    assert steps[0].get("status") == "passed", steps[0]

    references = result.get("attachments")
    assert isinstance(references, list) and len(references) == 1, result
    reference = references[0]
    assert isinstance(reference, dict), reference
    assert reference.get("name") == "Cucumber test run diagnostics", reference
    assert reference.get("type") == "application/json", reference
    source = reference.get("source")
    assert isinstance(source, str) and source, reference
    relative_source = PurePosixPath(source)
    assert (
        not relative_source.is_absolute()
        and ".." not in relative_source.parts
        and "\\" not in source
        and re.match(r"^[A-Za-z]:", source) is None
    ), reference
    attachment_path = result_directory.joinpath(*relative_source.parts).resolve()
    try:
        attachment_path.relative_to(result_directory.resolve())
    except ValueError as exc:
        raise AssertionError(f"attachment source escapes the Allure result directory: {source!r}") from exc
    expected_diagnostics = {"success": False}
    expected_bytes = (json.dumps(expected_diagnostics, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    assert attachment_path.is_file(), attachment_path
    actual_bytes = attachment_path.read_bytes()
    assert actual_bytes == expected_bytes, reference
    assert json.loads(actual_bytes) == expected_diagnostics, reference

    containers = sorted(result_directory.glob("*-container.json"))
    assert len(containers) == 1, containers
    container = json.loads(containers[0].read_text(encoding="utf-8"))
    assert isinstance(container, dict), container
    container_uuid = container.get("uuid")
    assert isinstance(container_uuid, str) and container_uuid, container
    assert containers[0].name == f"{container_uuid}-container.json", container
    assert container.get("children") == [result_uuid], container


@when(
    re.compile(
        r'I generate an Allure 3 report from consumer result directory "(?P<results_path>[^"]+)" '
        r'into "(?P<report_path>[^"]+)"'
    ),
    target_fixture="allure3_render_result",
)
def generate_allure3_report(
    results_path: str,
    report_path: str,
    consumer: ConsumerProject,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    results_directory = _consumer_artifact_path(results_path, consumer)
    report_directory = _consumer_artifact_path(report_path, consumer)
    npx = shutil.which("npx")
    allure = shutil.which("allure")
    if npx:
        command = [npx, "--yes", "allure@3.20.0", "generate", str(results_directory), "-o", str(report_directory)]
    elif allure:
        version = subprocess.run([allure, "--version"], check=False, capture_output=True, text=True)
        version_output = f"{version.stdout}\n{version.stderr}"
        assert version.returncode == 0 and re.search(r"\b3\.", version_output), (
            f"Allure 3 is required to render this contract; installed CLI output was: {version_output}"
        )
        command = [allure, "generate", str(results_directory), "-o", str(report_directory)]
    else:
        from pytest import skip

        skip(
            "Allure 3 CLI is not installed; run the pinned consumer manually with "
            f"npx --yes allure@3.20.0 generate {results_directory} -o {report_directory}"
        )
    result = subprocess.run(
        command,
        cwd=consumer.path,
        env=os.environ.copy(),
        check=False,
        capture_output=True,
        text=True,
    )
    return result, report_directory


@then("the Allure 3 renderer should generate the report")
def allure3_report_was_generated(allure3_render_result: tuple[subprocess.CompletedProcess[str], Path]) -> None:
    result, report_directory = allure3_render_result
    assert result.returncode == 0, f"Allure 3 renderer failed:\n{result.stdout}\n{result.stderr}"
    rendered_html = sorted(path for path in report_directory.rglob("*.html") if path.is_file())
    assert rendered_html, f"Allure 3 did not render an HTML report under {report_directory}"
    assert any(path.stat().st_size > 0 for path in rendered_html), rendered_html


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should expose the raw event from '
        r'"(?P<messages_path>[^"]+)" as an application/json attachment'
    )
)
def consumer_allure_raw_extension_attachment(
    relative_path: str,
    messages_path: str,
    consumer: ConsumerProject,
) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"

    message_file = _consumer_artifact_path(messages_path, consumer)
    raw_extension_events: list[bytes] = []
    for raw_line in message_file.read_bytes().splitlines():
        payload = json.loads(raw_line)
        if isinstance(payload, dict) and "vendorAuditExtension" in payload:
            assert set(payload) == {"vendorAuditExtension"}, payload
            raw_extension_events.append(raw_line)
    assert len(raw_extension_events) == 1, raw_extension_events

    attachment_references: list[Any] = []

    def collect_attachments(value: Any) -> None:
        if isinstance(value, dict):
            attachments = value.get("attachments")
            if isinstance(attachments, list):
                attachment_references.extend(attachments)
            for nested_value in value.values():
                collect_attachments(nested_value)
        elif isinstance(value, list):
            for nested_value in value:
                collect_attachments(nested_value)

    collect_attachments(result)
    json_references = [
        reference
        for reference in attachment_references
        if isinstance(reference, dict) and reference.get("type") == "application/json"
    ]
    assert len(json_references) == 1, attachment_references

    reference = json_references[0]
    source = reference.get("source")
    assert isinstance(source, str) and source, reference
    relative_source = PurePosixPath(source)
    assert (
        not relative_source.is_absolute()
        and ".." not in relative_source.parts
        and "\\" not in source
        and re.match(r"^[A-Za-z]:", source) is None
    ), reference
    attachment_path = result_directory.joinpath(*relative_source.parts).resolve()
    try:
        attachment_path.relative_to(result_directory.resolve())
    except ValueError as exc:
        raise AssertionError(f"attachment source escapes the Allure result directory: {source!r}") from exc
    assert attachment_path.is_file(), f"Allure attachment file is missing: {source!r}"
    assert attachment_path.read_bytes() == raw_extension_events[0], reference


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^\"]+)" should preserve scenario '
        r'"(?P<scenario_name>[^\"]+)", tag "(?P<tag>[^\"]+)", and outline parameter '
        r'"(?P<parameter_name>[^\"]+)" value "(?P<parameter_value>[^\"]+)"'
    )
)
def consumer_allure_outline_result_metadata(
    relative_path: str,
    scenario_name: str,
    tag: str,
    parameter_name: str,
    parameter_value: str,
    consumer: ConsumerProject,
) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    assert result_files[0].name == f"{result_uuid}-result.json", result
    assert result.get("name") == scenario_name, result
    assert result.get("status") == "passed", result

    labels = result.get("labels")
    assert isinstance(labels, list), result
    tag_labels = [label for label in labels if isinstance(label, dict) and label.get("name") == "tag"]
    assert tag_labels == [{"name": "tag", "value": tag}], result

    parameters = result.get("parameters")
    assert isinstance(parameters, list), result
    outline_parameters = [
        parameter
        for parameter in parameters
        if isinstance(parameter, dict) and parameter.get("name") == parameter_name
    ]
    assert outline_parameters == [{"name": parameter_name, "value": parameter_value}], result

    container_files = sorted(result_directory.glob("*-container.json"))
    assert len(container_files) == 1, f"expected one Allure container file, found {container_files!r}"
    container = json.loads(container_files[0].read_text(encoding="utf-8"))
    assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
    container_uuid = container.get("uuid")
    assert isinstance(container_uuid, str) and container_uuid, container
    assert container_files[0].name == f"{container_uuid}-container.json", container
    assert container.get("children") == [result_uuid], container


@then(
    re.compile(
        r'consumer Allure result directories "(?P<first_path>[^"]+)" and "(?P<second_path>[^"]+)" '
        r"should be semantically equivalent"
    )
)
def consumer_allure_result_directories_semantically_equivalent(
    first_path: str,
    second_path: str,
    consumer: ConsumerProject,
) -> None:
    semantic_artifacts = []
    for relative_path in (first_path, second_path):
        result_directory = _consumer_artifact_path(relative_path, consumer)
        result_files = sorted(result_directory.glob("*-result.json"))
        assert len(result_files) == 1, f"expected one Allure result file in {relative_path!r}, found {result_files!r}"
        result = json.loads(result_files[0].read_text(encoding="utf-8"))
        assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
        result_uuid = result.get("uuid")
        assert isinstance(result_uuid, str) and result_uuid, result
        assert result_files[0].name == f"{result_uuid}-result.json", result

        container_files = sorted(result_directory.glob("*-container.json"))
        assert len(container_files) == 1, (
            f"expected one Allure container file in {relative_path!r}, found {container_files!r}"
        )
        container = json.loads(container_files[0].read_text(encoding="utf-8"))
        assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
        container_uuid = container.get("uuid")
        assert isinstance(container_uuid, str) and container_uuid, container
        assert container_files[0].name == f"{container_uuid}-container.json", container
        assert container.get("children") == [result_uuid], container

        semantic_result = dict(result)
        semantic_result.pop("uuid")
        semantic_container = dict(container)
        semantic_container.pop("uuid")
        semantic_container["children"] = ["<linked-result>"]
        semantic_artifacts.append((semantic_result, semantic_container))

    assert semantic_artifacts[0] == semantic_artifacts[1], {
        first_path: semantic_artifacts[0],
        second_path: semantic_artifacts[1],
    }


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve failed diagnostics, '
        r"portable attachments, and a linked container"
    )
)
def consumer_allure_failure_attachments_and_container(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    assert result.get("name") == "Fail after attaching evidence", result
    assert result.get("uuid") == result_files[0].name.removesuffix("-result.json"), result
    assert result.get("status") == "failed", result

    def assert_failure_details(item: dict[str, Any]) -> str:
        details = item.get("statusDetails")
        assert isinstance(details, dict), item
        assert details.get("message") == "failure sentinel", details
        trace = details.get("trace")
        assert isinstance(trace, str) and "AssertionError: failure sentinel" in trace, details
        return trace

    scenario_trace = assert_failure_details(result)
    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 1, result
    failed_step = steps[0]
    assert isinstance(failed_step, dict), failed_step
    assert failed_step.get("name") == "the operation attaches evidence and fails", failed_step
    assert failed_step.get("status") == "failed", failed_step
    step_trace = assert_failure_details(failed_step)
    assert scenario_trace == step_trace, {"scenario_trace": scenario_trace, "step_trace": step_trace}

    expected_files = {
        "identity.txt": ("text/plain", b"identity evidence"),
        "binary.bin": ("application/octet-stream", b"\x00\xffbinary evidence"),
    }
    references = failed_step.get("attachments")
    assert isinstance(references, list) and len(references) == len(expected_files), failed_step
    seen_names: set[str] = set()
    for reference in references:
        assert isinstance(reference, dict), reference
        name = reference.get("name")
        assert isinstance(name, str) and name in expected_files, reference
        assert name not in seen_names, references
        seen_names.add(name)
        media_type, expected_content = expected_files[name]
        assert reference.get("type") == media_type, reference
        source = reference.get("source")
        assert isinstance(source, str) and source, reference
        relative_source = PurePosixPath(source)
        assert (
            not relative_source.is_absolute()
            and ".." not in relative_source.parts
            and "\\" not in source
            and re.match(r"^[A-Za-z]:", source) is None
        ), reference
        attachment_path = result_directory.joinpath(*relative_source.parts).resolve()
        try:
            attachment_path.relative_to(result_directory.resolve())
        except ValueError as exc:
            raise AssertionError(f"attachment source escapes the Allure result directory: {source!r}") from exc
        assert attachment_path.is_file(), f"Allure attachment file is missing: {source!r}"
        assert attachment_path.read_bytes() == expected_content, reference
    assert seen_names == set(expected_files), references

    container_files = sorted(result_directory.glob("*-container.json"))
    assert len(container_files) == 1, f"expected one Allure container file, found {container_files!r}"
    container = json.loads(container_files[0].read_text(encoding="utf-8"))
    assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
    container_uuid = container.get("uuid")
    assert isinstance(container_uuid, str) and container_uuid, container
    assert container_files[0].name == f"{container_uuid}-container.json", container
    assert container.get("children") == [result["uuid"]], container


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should combine the exception and '
        r"step-result messages with a linked container"
    )
)
def consumer_allure_combined_failure_messages(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, result_files
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), result
    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    assert result_files[0].name == f"{result_uuid}-result.json", result
    assert result.get("name") == "Distinct failure messages", result
    assert result.get("status") == "failed", result
    expected_message = "exception detail\n\nstep result detail"
    result_details = result.get("statusDetails")
    assert isinstance(result_details, dict), result
    assert result_details.get("message") == expected_message, result_details

    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 1, result
    failed_step = steps[0]
    assert isinstance(failed_step, dict), steps
    assert failed_step.get("name") == "the operation reports separate failure details", failed_step
    assert failed_step.get("status") == "failed", failed_step
    step_details = failed_step.get("statusDetails")
    assert isinstance(step_details, dict), failed_step
    assert step_details.get("message") == expected_message, step_details

    containers = sorted(result_directory.glob("*-container.json"))
    assert len(containers) == 1, containers
    container = json.loads(containers[0].read_text(encoding="utf-8"))
    assert isinstance(container, dict), container
    container_uuid = container.get("uuid")
    assert isinstance(container_uuid, str) and container_uuid, container
    assert containers[0].name == f"{container_uuid}-container.json", container
    assert container.get("children") == [result_uuid], container


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should contain both scenarios with ordered '
        r"steps and linked containers"
    )
)
def consumer_allure_multiple_scenarios(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    expected_steps = {
        "Submit a book order": [
            "the cart contains a book",
            "the customer submits the order",
            "the order has an identifier",
        ],
        "Generate a customer report": [
            "a customer report is requested",
            "the report is generated",
            "the report is ready",
        ],
    }
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == len(expected_steps), f"unexpected Allure result files: {result_files!r}"
    results_by_uuid: dict[str, str] = {}
    for result_file in result_files:
        result = json.loads(result_file.read_text(encoding="utf-8"))
        assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
        result_uuid = result.get("uuid")
        assert isinstance(result_uuid, str) and result_uuid, result
        assert result_file.name == f"{result_uuid}-result.json", result
        scenario_name = result.get("name")
        assert scenario_name in expected_steps and scenario_name not in results_by_uuid.values(), result
        assert result.get("status") == "passed", result
        steps = result.get("steps")
        assert isinstance(steps, list), result
        step_names = [step.get("name") for step in steps if isinstance(step, dict)]
        assert step_names == expected_steps[scenario_name], result
        assert all(step.get("status") == "passed" for step in steps), result
        results_by_uuid[result_uuid] = scenario_name
    assert set(results_by_uuid.values()) == set(expected_steps), results_by_uuid

    container_files = sorted(result_directory.glob("*-container.json"))
    assert len(container_files) == len(results_by_uuid), f"unexpected Allure container files: {container_files!r}"
    linked_result_uuids: list[str] = []
    for container_file in container_files:
        container = json.loads(container_file.read_text(encoding="utf-8"))
        assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
        container_uuid = container.get("uuid")
        assert isinstance(container_uuid, str) and container_uuid, container
        assert container_file.name == f"{container_uuid}-container.json", container
        children = container.get("children")
        assert isinstance(children, list) and len(children) == 1, container
        linked_result_uuids.append(children[0])
    assert len(linked_result_uuids) == len(set(linked_result_uuids)), linked_result_uuids
    assert set(linked_result_uuids) == set(results_by_uuid), {
        "results": results_by_uuid,
        "containers": linked_result_uuids,
    }


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve the Background step before '
        r"scenario steps and a linked container"
    )
)
def consumer_allure_background_step_order(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, result_files
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), result
    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    assert result_files[0].name == f"{result_uuid}-result.json", result
    assert result.get("name") == "Save Ada's order", result
    assert result.get("status") == "passed", result
    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 3, result
    assert [step.get("name") for step in steps if isinstance(step, dict)] == [
        "the shop is open",
        "the customer is Ada",
        "the order is saved",
    ], steps
    assert all(isinstance(step, dict) and step.get("status") == "passed" for step in steps), steps

    containers = sorted(result_directory.glob("*-container.json"))
    assert len(containers) == 1, containers
    container = json.loads(containers[0].read_text(encoding="utf-8"))
    assert isinstance(container, dict), container
    container_uuid = container.get("uuid")
    assert isinstance(container_uuid, str) and container_uuid, container
    assert containers[0].name == f"{container_uuid}-container.json", container
    assert container.get("children") == [result_uuid], container


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve the scenario description, '
        r"tag, and structured step arguments"
    )
)
def consumer_allure_structured_step_arguments(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    assert result.get("name") == "Submit a profile payload and field table", result
    assert result.get("description") == "The request identifies its media type and keeps the field values.", result
    assert result.get("status") == "passed", result

    labels = result.get("labels")
    assert isinstance(labels, list), result
    tag_labels = [label for label in labels if isinstance(label, dict) and label.get("name") == "tag"]
    assert tag_labels == [{"name": "tag", "value": "@smoke"}], result

    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 2, result
    doc_string_step, data_table_step = steps
    assert isinstance(doc_string_step, dict), doc_string_step
    assert isinstance(data_table_step, dict), data_table_step
    assert [doc_string_step.get("name"), data_table_step.get("name")] == [
        "the JSON profile is accepted",
        "the profile fields are recorded",
    ], result
    assert all(step.get("status") == "passed" for step in steps), result

    doc_string_content = '{"customer": "Ada", "active": true}'
    doc_string_description = f"application/json\n\n{doc_string_content}"
    assert doc_string_step.get("description") == doc_string_description, doc_string_step
    assert doc_string_step.get("descriptionHtml") == doc_string_description, doc_string_step
    assert doc_string_step.get("parameters") == [
        {"name": "docString", "value": doc_string_content}
    ], doc_string_step

    data_table_markdown = "| field | value |\n| customer | Ada |\n| active | true |"
    assert data_table_step.get("description") == data_table_markdown, data_table_step
    assert data_table_step.get("descriptionHtml") == data_table_markdown, data_table_step
    assert data_table_step.get("parameters") == [
        {"name": "dataTable", "value": data_table_markdown}
    ], data_table_step


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
                _validate_messages_envelope_compatibly(json.loads(raw_datum))
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
    python = _consumer_executable(_consumer_binary_dir(environment), "python")
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


def _consumer_batch_output(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}"


def _write_simple_consumer_features(consumer: ConsumerProject, count: int) -> list[Path]:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index in range(count):
        path = feature_root / f"batch-sample-{index:04d}.feature"
        path.write_text(
            f"Feature: Batch sample {index}\n  Scenario: Batch scenario {index}\n",
            encoding="utf-8",
        )
        paths.append(path)
    return paths


def _run_consumer_batch_pytest(consumer: ConsumerProject, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(consumer.pytest), *arguments],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    consumer.pytest_result = result
    return result


def _consumer_batch_pass_count(result: subprocess.CompletedProcess[str]) -> int | None:
    match = re.search(r"\b(\d+) passed BDD scenarios, 0 failed, 0 skipped\b", _consumer_batch_output(result))
    return int(match.group(1)) if match else None


def _consumer_batch_node_ids(result: subprocess.CompletedProcess[str]) -> list[str]:
    node_ids: list[str] = []
    for line in _consumer_batch_output(result).splitlines():
        match = re.search(
            r"(?P<node>[^\s].*?\.(?:feature|gherkin)(?:\.md)?::.*?)(?:\s+(?:PASSED|FAILED|SKIPPED)\b|$)",
            line,
            flags=re.IGNORECASE,
        )
        if match:
            node_ids.append(match.group("node").strip())
    return node_ids


def _consumer_batch_fallback_reported(result: subprocess.CompletedProcess[str]) -> bool:
    output = _consumer_batch_output(result).lower()
    return "falling back" in output and any(word in output for word in ("serial", "sync", "synchronous"))


@fixture(scope="session")
def _pytest_cuke_group_wheel(request, tmp_path_factory) -> Path:
    project_root = Path(request.config.rootpath)
    artifact_dir = tmp_path_factory.mktemp("pytest-cuke-group-wheel")
    uv_executable = shutil.which("uv")
    assert uv_executable, "the test-group consumer contract requires uv to build the product wheel"
    build_environment = os.environ.copy()
    build_environment["PYTEST_CUKE_BUILD_GO"] = "off"
    result = subprocess.run(
        [uv_executable, "build", "--wheel", "--out-dir", str(artifact_dir), str(project_root)],
        cwd=project_root,
        env=build_environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"could not build the pytest-cuke wheel:\n{result.stdout}\n{result.stderr}"
    wheels = list(artifact_dir.glob("pytest_cuke-*.whl"))
    assert len(wheels) == 1, f"expected one pytest-cuke wheel, found {wheels}"
    return wheels[0]


@fixture(scope="session")
def _pytest_cuke_xdist_environment(_pytest_cuke_group_wheel: Path, tmp_path_factory):
    """Install the built wheel and xdist into an isolated external-consumer environment."""
    environment_path = tmp_path_factory.mktemp("pytest-cuke-group-venv")
    uv_executable = shutil.which("uv")
    assert uv_executable, "the test-group consumer contract requires uv to create an isolated environment"
    consumer_interpreter = sys.executable
    create_environment = subprocess.run(
        [uv_executable, "venv", "--python", consumer_interpreter, str(environment_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert create_environment.returncode == 0, (
        f"could not create the test-group consumer environment:\n"
        f"{create_environment.stdout}\n{create_environment.stderr}"
    )

    binary_dir = _consumer_binary_dir(environment_path)
    python_path = _consumer_executable(binary_dir, "python")
    install = subprocess.run(
        [
            uv_executable,
            "pip",
            "install",
            "--python",
            str(python_path),
            str(_pytest_cuke_group_wheel),
            "pytest-xdist",
            "pytest-order",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, (
        f"could not install the pytest-cuke wheel, pytest-xdist, and pytest-order:\n{install.stdout}\n{install.stderr}"
    )
    return environment_path


@given(
    "the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer",
    target_fixture="consumer",
)
def install_pytest_cuke_test_group_consumer(
    _pytest_cuke_xdist_environment, _pytest_cuke_group_wheel: Path, tmp_path_factory
):
    project_path = tmp_path_factory.mktemp("pytest-cuke-group-consumer")
    project_path.joinpath("pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_autoload = false\ntestpaths = ['tests']\n",
        encoding="utf-8",
    )
    project_path.joinpath("tests").mkdir()

    binary_dir = _consumer_binary_dir(_pytest_cuke_xdist_environment)
    consumer_home = project_path / ".home"
    consumer_home.mkdir()
    environment = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "MYPYPATH",
        "MYPY_CONFIG_FILE_DIR",
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
    if os.name == "nt":
        environment["USERPROFILE"] = str(consumer_home)
    return ConsumerProject(
        path=project_path,
        python=_consumer_executable(binary_dir, "python"),
        pytest=_consumer_executable(binary_dir, "pytest"),
        cuke=_consumer_executable(binary_dir, "cuke"),
        env=environment,
        artifact=_pytest_cuke_group_wheel,
    )


@given("the consumer records monotonic test start and terminal events")
def configure_consumer_test_group_event_recorder(consumer: ConsumerProject) -> None:
    event_support = consumer.path / "group_events.py"
    event_support.write_text(
        dedent(
            """\
            from __future__ import annotations

            import hashlib
            import json
            import os
            import time
            from pathlib import Path


            EVENT_DIRECTORY = Path(".pytest-cuke-group-events")


            def record_event(phase, *, nodeid, group, outcome=None, when=None):
                timestamp = time.monotonic_ns()
                worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
                record = {
                    "phase": phase,
                    "nodeid": nodeid,
                    "group": group,
                    "outcome": outcome,
                    "when": when,
                    "worker": worker,
                    "run_id": os.environ.get("PYTEST_CUKE_RUN_ID", "single"),
                    "timestamp_ns": timestamp,
                }
                token = hashlib.sha256(f"{phase}:{nodeid}:{worker}:{timestamp}".encode()).hexdigest()
                EVENT_DIRECTORY.mkdir(exist_ok=True)
                (EVENT_DIRECTORY / f"{phase}-{token}.json").write_text(json.dumps(record), encoding="utf-8")


            def record_start(nodeid, group):
                record_event("start", nodeid=nodeid, group=group)


            def signal(name):
                EVENT_DIRECTORY.mkdir(exist_ok=True)
                run_id = os.environ.get("PYTEST_CUKE_RUN_ID", "single")
                (EVENT_DIRECTORY / f"signal-{run_id}-{name}").write_text("ready", encoding="utf-8")


            def wait_for_signal(name, timeout=20):
                deadline = time.monotonic() + timeout
                run_id = os.environ.get("PYTEST_CUKE_RUN_ID", "single")
                signal_path = EVENT_DIRECTORY / f"signal-{run_id}-{name}"
                while not signal_path.exists():
                    if time.monotonic() >= deadline:
                        raise AssertionError(f"timed out waiting for event signal {name!r}")
                    time.sleep(0.01)
            """
        ),
        encoding="utf-8",
    )
    (consumer.path / "conftest.py").write_text(
        dedent(
            """\
            import pytest

            from group_events import record_event


            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                is_terminal_call = report.when == "call"
                is_terminal_setup = report.when == "setup" and report.outcome in {"failed", "skipped"}
                if not (is_terminal_call or is_terminal_setup):
                    return

                raw_groups = item.config.getini("cuke_test_group_order")
                groups = (
                    raw_groups.split()
                    if isinstance(raw_groups, str)
                    else [name for line in raw_groups for name in str(line).split()]
                )
                group_markers = {mark.name for mark in item.iter_markers() if mark.name in groups}
                group = next((name for name in reversed(groups) if name in group_markers), None)
                record_event(
                    "terminal",
                    nodeid=item.nodeid,
                    group=group,
                    outcome=report.outcome,
                    when=report.when,
                )
            """
        ),
        encoding="utf-8",
    )


@when(
    re.compile(
        r'I run installed pytest with a (?P<watchdog_seconds>\d+)-second watchdog and arguments "(?P<arguments>[^\"]*)"'
    ),
    target_fixture="pytest_result",
)
def run_consumer_pytest_with_watchdog(watchdog_seconds, arguments, consumer: ConsumerProject):
    command = [str(consumer.pytest), *shlex.split(arguments)]
    try:
        result = subprocess.run(
            command,
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=int(watchdog_seconds),
        )
    except subprocess.TimeoutExpired as error:
        consumer.pytest_watchdog_expired = True
        result = subprocess.CompletedProcess(
            command,
            124,
            error.stdout.decode() if isinstance(error.stdout, bytes) else error.stdout or "",
            error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr or "",
        )
    else:
        consumer.pytest_watchdog_expired = False
    consumer.pytest_result = result
    return result


@when("I run two independent consumer suites through their local xdist group barriers")
def run_independent_consumer_group_workflows(consumer: ConsumerProject) -> None:
    command = [
        str(consumer.pytest),
        "-c",
        "pytest.ini",
        "-n2",
        "--dist=loadfile",
        "--order-scope=session",
        "--cuke-no-autoload",
        "-q",
    ]
    event_directory = consumer.path / ".pytest-cuke-group-events"
    event_directory.mkdir(exist_ok=True)
    processes: dict[str, subprocess.Popen[str]] = {}
    output_paths: dict[str, Path] = {}

    def events_for(run_id: str) -> list[dict[str, object]]:
        records = _read_consumer_test_group_events(consumer) if event_directory.is_dir() else []
        return [event for event in records if event.get("run_id") == run_id]

    def wait_for_event(run_id: str, phase: str, group: str, deadline: float) -> None:
        while time.monotonic() < deadline:
            if any(event.get("phase") == phase and event.get("group") == group for event in events_for(run_id)):
                return
            finished = [name for name, process in processes.items() if process.poll() is not None]
            if finished:
                diagnostics = {
                    name: output_paths[name].read_text(encoding="utf-8")
                    for name in finished
                    if output_paths[name].is_file()
                }
                raise AssertionError(f"consumer run ended before {phase} for {run_id}/{group}: {diagnostics}")
            time.sleep(0.01)
        raise AssertionError(f"consumer run did not record {phase} for {run_id}/{group} before the watchdog")

    try:
        for run_id in ("first", "second"):
            output_path = consumer.path / f"group-run-{run_id}.log"
            output_paths[run_id] = output_path
            run_environment = consumer.env.copy()
            run_environment["PYTEST_CUKE_RUN_ID"] = run_id
            with output_path.open("w", encoding="utf-8") as output_file:
                processes[run_id] = subprocess.Popen(
                    command,
                    cwd=consumer.path,
                    env=run_environment,
                    stdout=output_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

        watchdog = time.monotonic() + 45
        wait_for_event("first", "start", "unit", watchdog)
        wait_for_event("second", "start", "unit", watchdog)

        (event_directory / "signal-first-release-unit").write_text("ready", encoding="utf-8")
        wait_for_event("first", "start", "integration", watchdog)
        second_started_integration_early = any(
            event.get("phase") == "start" and event.get("group") == "integration" for event in events_for("second")
        )
        consumer.second_group_started_before_release = second_started_integration_early

        (event_directory / "signal-second-release-unit").write_text("ready", encoding="utf-8")
        results: list[subprocess.CompletedProcess[str]] = []
        for run_id, process in processes.items():
            return_code = process.wait(timeout=max(1, int(watchdog - time.monotonic())))
            results.append(
                subprocess.CompletedProcess(
                    command,
                    return_code,
                    output_paths[run_id].read_text(encoding="utf-8"),
                    "",
                )
            )
        consumer.concurrent_group_results = results
        consumer.concurrent_group_events = _read_consumer_test_group_events(consumer)
    finally:
        for process in processes.values():
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


@then("both independent consumer runs should pass without sharing barrier state")
def independent_consumer_runs_use_isolated_barrier_state(consumer: ConsumerProject) -> None:
    results = consumer.concurrent_group_results
    assert results is not None and len(results) == 2, "the independent consumer runs have not completed"
    for index, result in enumerate(results, start=1):
        assert result.returncode == 0, f"consumer run {index} failed:\n{result.stdout}\n{result.stderr}"
    assert consumer.second_group_started_before_release is False, (
        "the second run entered its later group before that run's earlier group was released"
    )

    events = consumer.concurrent_group_events
    assert events is not None, "the independent consumer group events were not captured"
    for run_id in ("first", "second"):
        unit_terminals = [
            int(event["timestamp_ns"])
            for event in events
            if event.get("run_id") == run_id and event.get("phase") == "terminal" and event.get("group") == "unit"
        ]
        integration_starts = [
            int(event["timestamp_ns"])
            for event in events
            if event.get("run_id") == run_id and event.get("phase") == "start" and event.get("group") == "integration"
        ]
        assert unit_terminals and integration_starts, f"incomplete barrier events for run {run_id!r}: {events}"
        assert max(unit_terminals) < min(integration_starts), (
            f"run {run_id!r} began integration before all unit items settled"
        )


@then("the installed pytest run should finish before its watchdog")
def consumer_pytest_finished_before_watchdog(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    details = "" if result is None else f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert not consumer.pytest_watchdog_expired, f"installed pytest hung until the external watchdog{details}"


@then(re.compile(r'consumer start events should follow "(?P<expected>[^"]+)"'))
def consumer_start_events_follow_order(expected, consumer: ConsumerProject) -> None:
    events = _read_consumer_test_group_events(consumer)
    starts = sorted((event for event in events if event["phase"] == "start"), key=itemgetter("timestamp_ns"))
    actual = [str(event["nodeid"]).rsplit("::", 1)[-1] for event in starts]
    expected_names = [name.strip() for name in expected.split(",") if name.strip()]
    assert actual == expected_names, f"consumer start order was {actual}; expected {expected_names}"


@then(re.compile(r'every selected "(?P<earlier>[^\"]+)" test should settle before any "(?P<later>[^\"]+)" test starts'))
def consumer_test_groups_obey_terminal_barrier(earlier, later, consumer: ConsumerProject) -> None:
    events = _read_consumer_test_group_events(consumer)
    earlier_terminals = [
        event["timestamp_ns"] for event in events if event["phase"] == "terminal" and event["group"] == earlier
    ]
    later_starts = [event["timestamp_ns"] for event in events if event["phase"] == "start" and event["group"] == later]
    assert earlier_terminals, f"the consumer recorded no terminal events for group {earlier!r}"
    assert later_starts, f"the consumer recorded no start events for group {later!r}"
    assert max(earlier_terminals) < min(later_starts), (
        f"group {later!r} started before every selected {earlier!r} item settled: "
        f"latest terminal={max(earlier_terminals)}, earliest start={min(later_starts)}"
    )


@then(re.compile(r"consumer terminal outcomes should include (?P<outcomes>[a-z, ]+)"))
def consumer_terminal_outcomes_include(outcomes, consumer: ConsumerProject) -> None:
    events = _read_consumer_test_group_events(consumer)
    actual = {str(event["outcome"]) for event in events if event["phase"] == "terminal"}
    expected = {value.strip() for value in outcomes.split(",") if value.strip()}
    assert expected <= actual, f"terminal outcomes were {sorted(actual)}; expected at least {sorted(expected)}"


@then("the consumer should have no recorded test-group events")
def consumer_has_no_test_group_events(consumer: ConsumerProject) -> None:
    event_directory = consumer.path / ".pytest-cuke-group-events"
    records = list(event_directory.glob("*.json")) if event_directory.is_dir() else []
    assert not records, f"pytest unexpectedly recorded test-group events: {records}"


@then("the consumer should have no test-group barrier state root")
def consumer_has_no_test_group_barrier_state_root(consumer: ConsumerProject) -> None:
    state_root = consumer.path / ".pytest_cache" / "pytest-cuke-test-groups"
    assert not state_root.exists(), f"the default workflow created a test-group barrier state root: {state_root}"


@then(re.compile(r"at least (?P<count>two|four|\d+) xdist workers should have recorded group events"))
def consumer_group_events_show_multiple_workers(count: str, consumer: ConsumerProject) -> None:
    events = _read_consumer_test_group_events(consumer)
    workers = {str(event["worker"]) for event in events if event.get("worker") != "master"}
    required_workers = int(count) if count.isdecimal() else {"two": 2, "four": 4}[count]
    assert len(workers) >= required_workers, (
        f"expected events from at least {required_workers} xdist workers, got {sorted(workers)}"
    )


@then(re.compile(r'pytest output should include "(?P<expected>[^"]+)"'))
def consumer_pytest_output_includes(expected, consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert expected.casefold() in output.casefold(), f"pytest output did not include {expected!r}:\n{output}"


@then(re.compile(r'pytest output should not include "(?P<unexpected>[^"]+)"'))
def consumer_pytest_output_excludes(unexpected, consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert unexpected.casefold() not in output.casefold(), (
        f"pytest output unexpectedly included {unexpected!r}:\n{output}"
    )


@then("pytest output should explain conflicting per-binding feature sources")
def consumer_pytest_output_explains_conflicting_source_bases(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    expected = 'Both "features_base_dir" and "features_base_url" were specified'
    assert expected.casefold() in output.casefold(), f"pytest output did not explain the conflict:\n{output}"


@then(re.compile(r'pytest output should identify the local HTTP source URL "(?P<path>[^\"]+)"'))
def consumer_pytest_output_identifies_local_http_source_url(
    path: str,
    consumer: ConsumerProject,
    local_feature_http_server: LocalFeatureHTTPFixture,
) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    expected_url = f"{local_feature_http_server.base_url}{path}"
    output = f"{result.stdout}\n{result.stderr}"
    assert expected_url in output, f"pytest output did not identify {expected_url!r}:\n{output}"


def _read_consumer_test_group_events(consumer: ConsumerProject) -> list[dict[str, object]]:
    event_directory = consumer.path / ".pytest-cuke-group-events"
    assert event_directory.is_dir(), f"consumer test-group events were not recorded: {event_directory}"
    return [json.loads(path.read_text(encoding="utf-8")) for path in event_directory.glob("*.json") if path.is_file()]


def _normalized_cucumber_messages(consumer: ConsumerProject, relative_path: str) -> list[object]:
    report_path = consumer.path / relative_path
    assert report_path.is_file(), f"pytest did not create the Messages report: {report_path}"

    def normalize(value: object) -> object:
        if isinstance(value, dict):
            return {key: normalize(item) for key, item in value.items() if key not in {"timestamp", "duration"}}
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    lines = report_path.read_text(encoding="utf-8").splitlines()
    return [normalize(json.loads(line)) for line in lines if line.strip()]


@given(re.compile(r"I create (?P<count>\d+) simple consumer feature files?"))
def create_simple_consumer_features(count: str, consumer: ConsumerProject) -> None:
    _write_simple_consumer_features(consumer, int(count))


@given("the consumer cannot start spawn workers")
def prevent_consumer_spawn_pool_start(consumer: ConsumerProject) -> None:
    sitecustomize = consumer.path / "sitecustomize.py"
    sitecustomize.write_text(
        """import multiprocessing

_original_get_context = multiprocessing.get_context


class _UnavailableSpawnContext:
    def Pool(self, *args, **kwargs):
        raise RuntimeError("simulated spawn pool startup failure")


def _get_context(method=None):
    if method == "spawn":
        return _UnavailableSpawnContext()
    return _original_get_context(method)


multiprocessing.get_context = _get_context
""",
        encoding="utf-8",
    )
    consumer.env["PYTHONPATH"] = str(consumer.path)


@when("I compare serial and spawn collection of the installed consumer suite")
def compare_serial_and_spawn_collection(consumer: ConsumerProject) -> None:
    feature_count = len(list((consumer.path / "features").glob("*.feature")))
    assert feature_count > 0, "the consumer has no generated features to collect"
    optional_reader = subprocess.run(
        [
            str(consumer.python),
            "-c",
            "import importlib.util; raise SystemExit(importlib.util.find_spec('aiofiles') is not None)",
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert optional_reader.returncode == 0, (
        "the installed consumer unexpectedly has aiofiles; this scenario must exercise the sync-read fallback:\n"
        f"{optional_reader.stdout}\n{optional_reader.stderr}"
    )
    common_arguments = [
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-summary",
        "-vv",
        "--color=no",
        "--log-cli-level=WARNING",
    ]
    serial = _run_consumer_batch_pytest(
        consumer,
        [
            *common_arguments,
            f"--cuke-batch-threshold={feature_count + 1}",
            "--cuke-messages-ndjson=batch-serial.ndjson",
        ],
    )
    parallel = _run_consumer_batch_pytest(
        consumer,
        [
            *common_arguments,
            "--cuke-batch-threshold=1",
            "--cuke-messages-ndjson=batch-spawn.ndjson",
        ],
    )
    setattr(consumer, "batch_collection_runs", [serial, parallel])


@then("serial and spawn collection should have identical scenario identities, outcomes, and normalized messages")
def serial_and_spawn_collections_match(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "batch_collection_runs", None)
    assert runs is not None and len(runs) == 2, "serial and spawn collection runs have not completed"
    serial, spawn = runs
    serial_output = _consumer_batch_output(serial)
    spawn_output = _consumer_batch_output(spawn)
    assert serial.returncode == 0, f"serial collection failed:\n{serial_output}"
    assert spawn.returncode == 0, f"spawn collection failed:\n{spawn_output}"
    serial_ids = _consumer_batch_node_ids(serial)
    spawn_ids = _consumer_batch_node_ids(spawn)
    assert serial_ids, f"serial collection did not report scenario identities:\n{serial_output}"
    assert serial_ids == spawn_ids, (serial_ids, spawn_ids)
    assert not _consumer_batch_fallback_reported(spawn), spawn_output
    assert any("external-batch.feature" in node_id for node_id in serial_ids), serial_ids
    expected_count = len(serial_ids)
    assert _consumer_batch_pass_count(serial) == expected_count, serial_output
    assert _consumer_batch_pass_count(spawn) == expected_count, spawn_output
    serial_messages = _normalized_cucumber_messages(consumer, "batch-serial.ndjson")
    spawn_messages = _normalized_cucumber_messages(consumer, "batch-spawn.ndjson")
    assert serial_messages, "serial collection did not emit Cucumber Messages"
    assert serial_messages == spawn_messages


@when("I compare collection with and without a command-line threshold override")
def compare_cli_and_configured_batch_thresholds(consumer: ConsumerProject) -> None:
    common_arguments = [
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-summary",
        "--log-cli-level=WARNING",
    ]
    cli_override = _run_consumer_batch_pytest(consumer, [*common_arguments, "--cuke-batch-threshold=1"])
    configured_value = _run_consumer_batch_pytest(consumer, common_arguments)
    setattr(consumer, "batch_threshold_override_runs", [cli_override, configured_value])


@then("the command-line threshold should select parallel collection over configuration")
def cli_batch_threshold_overrides_configuration(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "batch_threshold_override_runs", None)
    assert runs is not None and len(runs) == 2, "the threshold comparison runs have not completed"
    cli_override, configured_value = runs
    cli_output = _consumer_batch_output(cli_override)
    config_output = _consumer_batch_output(configured_value)
    assert cli_override.returncode == 0, cli_output
    assert configured_value.returncode == 0, config_output
    assert _consumer_batch_fallback_reported(cli_override), cli_output
    assert not _consumer_batch_fallback_reported(configured_value), config_output


@then("both collection runs should pass every scenario")
def both_threshold_collection_runs_pass(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "batch_threshold_override_runs", None)
    assert runs is not None and len(runs) == 2, "the threshold comparison runs have not completed"
    for result in runs:
        output = _consumer_batch_output(result)
        assert _consumer_batch_pass_count(result) == 1, output


@when(re.compile(r"I compare collection at (?P<below>\d+), (?P<equal>\d+), and (?P<above>\d+) feature files"))
def compare_configured_batch_threshold_boundary(below: str, equal: str, above: str, consumer: ConsumerProject) -> None:
    common_arguments = [
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-summary",
        "--log-cli-level=WARNING",
    ]
    results: list[subprocess.CompletedProcess[str]] = []
    for count in (int(below), int(equal), int(above)):
        _write_simple_consumer_features(consumer, count)
        results.append(_run_consumer_batch_pytest(consumer, common_arguments))
    setattr(consumer, "batch_threshold_boundary_runs", results)


@then("collection should stay serial below the configured threshold and fall back at and above it")
def configured_batch_threshold_boundary_is_respected(consumer: ConsumerProject) -> None:
    results = getattr(consumer, "batch_threshold_boundary_runs", None)
    assert results is not None and len(results) == 3, "the threshold boundary runs have not completed"
    assert not _consumer_batch_fallback_reported(results[0]), _consumer_batch_output(results[0])
    assert _consumer_batch_fallback_reported(results[1]), _consumer_batch_output(results[1])
    assert _consumer_batch_fallback_reported(results[2]), _consumer_batch_output(results[2])


@then("all three collection runs should pass every scenario")
def all_configured_batch_threshold_runs_pass(consumer: ConsumerProject) -> None:
    results = getattr(consumer, "batch_threshold_boundary_runs", None)
    assert results is not None and len(results) == 3, "the threshold boundary runs have not completed"
    for count, result in zip((2, 3, 4), results, strict=True):
        output = _consumer_batch_output(result)
        assert result.returncode == 0, output
        assert _consumer_batch_pass_count(result) == count, output


@when("I compare collection immediately below and at the platform default threshold")
def compare_platform_default_batch_threshold(consumer: ConsumerProject) -> None:
    threshold = 50 if os.name == "posix" else 1000
    _write_simple_consumer_features(consumer, threshold - 1)
    common_arguments = [
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-summary",
        "--log-cli-level=WARNING",
    ]
    below = _run_consumer_batch_pytest(consumer, common_arguments)
    _write_simple_consumer_features(consumer, threshold)
    equal = _run_consumer_batch_pytest(consumer, common_arguments)
    setattr(consumer, "platform_default_threshold", threshold)
    setattr(consumer, "platform_default_threshold_runs", [below, equal])


@then("the platform default threshold should be 50 on POSIX and 1000 elsewhere")
def platform_batch_threshold_matches_documented_default(consumer: ConsumerProject) -> None:
    expected = 50 if os.name == "posix" else 1000
    actual = getattr(consumer, "platform_default_threshold", None)
    assert actual == expected, f"the host platform default should be {expected}, got {actual}"


@then("collection should stay serial below the default and fall back at the default")
def platform_default_batch_threshold_boundary_is_respected(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "platform_default_threshold_runs", None)
    assert runs is not None and len(runs) == 2, "the platform default threshold runs have not completed"
    below, equal = runs
    assert not _consumer_batch_fallback_reported(below), _consumer_batch_output(below)
    assert _consumer_batch_fallback_reported(equal), _consumer_batch_output(equal)


@then("both default-threshold collection runs should pass every scenario")
def platform_default_batch_threshold_runs_pass(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "platform_default_threshold_runs", None)
    threshold = getattr(consumer, "platform_default_threshold", None)
    assert runs is not None and len(runs) == 2 and isinstance(threshold, int), (
        "the platform default threshold runs have not completed"
    )
    for count, result in zip((threshold - 1, threshold), runs, strict=True):
        output = _consumer_batch_output(result)
        assert result.returncode == 0, output
        assert _consumer_batch_pass_count(result) == count, output


@when(re.compile(r'I run independent collection processes before and after replacing "(?P<relative_path>[^"]+)" with:'))
def run_independent_consumer_pytest_processes(relative_path: str, consumer: ConsumerProject, step) -> None:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    file_path = consumer.path / destination
    assert file_path.is_file(), f"the file to replace does not exist: {relative_path}"
    arguments = [
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-summary",
        "--cuke-batch-threshold=1",
        "-vv",
        "--color=no",
    ]
    first = _run_consumer_batch_pytest(consumer, arguments)
    file_path.write_text(step.doc_string.content, encoding="utf-8")
    second = _run_consumer_batch_pytest(consumer, arguments)
    setattr(consumer, "independent_batch_runs", [first, second])


@then("the later pytest process should collect the edited feature and pass its scenario")
def later_consumer_process_observes_feature_edit(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "independent_batch_runs", None)
    assert runs is not None and len(runs) == 2, "the independent pytest processes have not completed"
    first, second = runs
    first_output = _consumer_batch_output(first)
    second_output = _consumer_batch_output(second)
    assert first.returncode == 0, first_output
    assert second.returncode == 0, second_output
    assert _consumer_batch_pass_count(first) == 1, first_output
    assert _consumer_batch_pass_count(second) == 1, second_output
    assert "The first version is collected" in first_output, first_output
    assert "The first version is collected" not in second_output, second_output
    assert "The updated version is collected" in second_output, second_output


@then("pytest output should identify the feature and external source for each batch error")
def batch_collection_errors_keep_feature_and_source_paths(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = _consumer_batch_output(result)
    for relative_path in (
        "features/malformed.feature",
        "features/broken.feature",
        "features/broken.csv",
        "features/unreadable.feature",
        "features/unreadable.csv",
    ):
        assert str((consumer.path / relative_path).resolve()) in output, output
    for feature_name, source_name in (
        ("features/broken.feature", "features/broken.csv"),
        ("features/unreadable.feature", "features/unreadable.csv"),
    ):
        feature_path = (consumer.path / feature_name).resolve()
        source_path = (consumer.path / source_name).resolve()
        association = f"Referenced source: {source_path}; feature: {feature_path}"
        assert association in output, output
    assert "row 2 has 1 columns; expected 2" in output, output
    assert any(error_name in output for error_name in ("IsADirectoryError", "PermissionError")), output


_STRUCT_BDD_CONSUMER_FILES = (
    "contract.bdd",
    "contract.bdd.yaml",
    "contract.bdd.yml",
    "contract.bdd.hocon",
    "contract.bdd.json5",
    "contract.bdd.json",
    "contract.bdd.hjson",
    "contract.bdd.toml",
)
_STRUCT_BDD_CASE_VARIANT = "contract-uppercase.BDD.YAML"


def _struct_bdd_payload(relative_path: str) -> str:
    name = Path(relative_path).name
    scenario = f"Scenario for {name}"
    lowered_path = relative_path.lower()
    if lowered_path.endswith((".bdd", ".bdd.yaml", ".bdd.yml")):
        return f"Name: StructBDD {name}\nSteps:\n  - Step:\n      Name: {scenario}\n"
    if lowered_path.endswith(".bdd.hocon"):
        return f'Name = "StructBDD {name}"\nSteps = [{{ Step = {{ Name = "{scenario}" }} }}]\n'
    if lowered_path.endswith(".bdd.json5"):
        return f"{{ Name: 'StructBDD {name}', Steps: [{{ Step: {{ Name: '{scenario}' }} }}], }}\n"
    if lowered_path.endswith(".bdd.json"):
        return json.dumps({"Name": f"StructBDD {name}", "Steps": [{"Step": {"Name": scenario}}]}) + "\n"
    if lowered_path.endswith(".bdd.hjson"):
        return (
            "{\n"
            f'  Name: "StructBDD {name}"\n'
            "  Steps: [\n"
            "    {\n"
            "      Step: {\n"
            f'        Name: "{scenario}"\n'
            "      }\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )
    if lowered_path.endswith(".bdd.toml"):
        return f'Name = "StructBDD {name}"\n\n[[Steps]]\n[Steps.Step]\nName = "{scenario}"\n'
    raise ValueError(f"no StructBDD consumer payload is defined for {relative_path}")


def _struct_bdd_result_items(
    result: subprocess.CompletedProcess[str],
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    status_pattern = re.compile(r"\s+(?P<status>PASSED|FAILED|SKIPPED|ERROR)(?:\s+\[\s*\d+%\])?\s*$")
    for line in _consumer_batch_output(result).splitlines():
        match = status_pattern.search(line)
        if match and ".bdd" in line.lower():
            items.append((line[: match.start()].strip(), match.group("status")))
    return items


@given("the consumer installs the optional StructBDD loaders")
def install_optional_struct_bdd_loaders(consumer: ConsumerProject) -> None:
    uv_executable = shutil.which("uv")
    assert uv_executable, "installing optional StructBDD loaders requires uv"
    result = subprocess.run(
        [
            uv_executable,
            "pip",
            "install",
            "--python",
            str(consumer.python),
            "PyYAML",
            "hjson",
            "json5",
            "pyhocon",
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"could not install the StructBDD loaders:\n{result.stdout}\n{result.stderr}"


@given("the consumer has one runnable feature for every supported StructBDD suffix")
def create_all_struct_bdd_consumer_suffixes(consumer: ConsumerProject) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    for relative_path in _STRUCT_BDD_CONSUMER_FILES:
        (feature_root / relative_path).write_text(_struct_bdd_payload(relative_path), encoding="utf-8")

    # These are deliberately invalid as structured BDD documents. Autoload must
    # ignore data and unknown files rather than trying to parse them.
    for relative_path in ("ordinary.yaml", "ordinary.json", "unsupported.bdd.txt"):
        (feature_root / relative_path).write_text("not a feature: [", encoding="utf-8")


@given("the consumer also has an uppercase StructBDD suffix variant")
def create_uppercase_struct_bdd_suffix_variant(consumer: ConsumerProject) -> None:
    feature_path = consumer.path / "features" / _STRUCT_BDD_CASE_VARIANT
    feature_path.write_text(_struct_bdd_payload(_STRUCT_BDD_CASE_VARIANT), encoding="utf-8")


@when("I compare StructBDD autoload by directory and by explicit files")
def compare_struct_bdd_autoload_selection(consumer: ConsumerProject) -> None:
    common_arguments = [
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "--cuke-summary",
        "-vv",
        "--color=no",
    ]
    directory_run = _run_consumer_batch_pytest(consumer, [*common_arguments, "features"])
    explicit_run = _run_consumer_batch_pytest(
        consumer,
        [
            *common_arguments,
            *(f"features/{relative_path}" for relative_path in (*_STRUCT_BDD_CONSUMER_FILES, _STRUCT_BDD_CASE_VARIANT)),
        ],
    )
    consumer.struct_bdd_selection_runs = [directory_run, explicit_run]


@then("both StructBDD selections should collect all eight formats and the uppercase variant as passing scenarios")
def struct_bdd_autoload_selections_match(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "struct_bdd_selection_runs", None)
    assert runs is not None and len(runs) == 2, "the StructBDD selection runs have not completed"
    directory_run, explicit_run = runs
    for result in runs:
        output = _consumer_batch_output(result)
        assert result.returncode == 0, output
        items = _struct_bdd_result_items(result)
        expected_files = (*_STRUCT_BDD_CONSUMER_FILES, _STRUCT_BDD_CASE_VARIANT)
        assert len(items) == len(expected_files) == 9, output
        assert all(status == "PASSED" for _, status in items), output
        assert all(any(relative_path in node_id for node_id, _ in items) for relative_path in expected_files), (
            items,
            output,
        )

    directory_items = _struct_bdd_result_items(directory_run)
    explicit_items = _struct_bdd_result_items(explicit_run)
    assert dict(directory_items) == dict(explicit_items), (directory_items, explicit_items)


@then("ordinary YAML and JSON data files and unsupported suffixes should be ignored")
def struct_bdd_autoload_ignores_data_files(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "struct_bdd_selection_runs", None)
    assert runs is not None and len(runs) == 2, "the StructBDD selection runs have not completed"
    for result in runs:
        output = _consumer_batch_output(result)
        for relative_path in ("ordinary.yaml", "ordinary.json", "unsupported.bdd.txt"):
            assert relative_path not in output, output


@given("the consumer has one structured feature selected through overlapping locators")
def create_overlapping_struct_bdd_locators(consumer: ConsumerProject) -> None:
    (consumer.path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_features_dir = 'features'\ncuke_autoload = false\n",
        encoding="utf-8",
    )
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    feature_path = "features/overlap.bdd.yaml"
    (consumer.path / feature_path).write_text(
        "Name: Overlapping locators\nSteps:\n  - Step:\n      Name: One selected scenario\n",
        encoding="utf-8",
    )
    (consumer.path / "test_overlap.py").write_text(
        "from pytest_cuke import scenarios\n\n"
        "@scenarios('.', 'overlap.bdd.yaml', return_test_decorator=True)\n"
        "def test_overlapping_locators(scenario):\n"
        "    assert scenario.name == 'One selected scenario'\n",
        encoding="utf-8",
    )


@then("the overlapping locators should collect the structured scenario once")
def overlapping_struct_bdd_locators_are_deduplicated(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = _consumer_batch_output(result)
    items = []
    for line in output.splitlines():
        if "test_overlapping_locators[" in line:
            status = re.search(r"\b(PASSED|FAILED|SKIPPED|ERROR)(?:\s+\[\s*\d+%\])?\s*$", line)
            if status is None:
                continue
            assert status is not None
            items.append((line[: status.start()].strip(), status.group(1)))
    assert result.returncode == 0, output
    assert len(items) == 1, output
    assert items[0][1] == "PASSED", output


@given("the consumer has semantically equal Gherkin and YAML StructBDD features")
def create_struct_bdd_gherkin_parity_pair(consumer: ConsumerProject) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "parity.bdd.yaml").write_text(
        "Name: Shared report\n"
        "Steps:\n"
        "  - Step:\n"
        "      Name: Shared result\n"
        "      Steps:\n"
        "        - Given: the parity step passes\n",
        encoding="utf-8",
    )
    (feature_root / "parity.feature").write_text(
        "Feature: Shared report\n  Scenario: Shared result\n    Given the parity step passes\n",
        encoding="utf-8",
    )
    (consumer.path / "conftest.py").write_text(
        "from pytest_cuke import given\n\n@given('the parity step passes')\ndef parity_step():\n    pass\n",
        encoding="utf-8",
    )


@when("I compare their immutable feature models and scenario reports")
def compare_struct_bdd_gherkin_domains_and_reports(consumer: ConsumerProject) -> None:
    compare_domain_script = """
import sys
from pytest_cuke.parser import GherkinParser
from pytest_cuke.struct_bdd.parser import StructBDDParser

structured_path, gherkin_path = sys.argv[1:]
structured = StructBDDParser(kind="yaml").parse(structured_path, uri="parity.feature")
gherkin = GherkinParser().parse(gherkin_path, uri="parity.feature")

def normalize(feature):
    return {
        "name": feature.name,
        "description": feature.description,
        "tags": feature.tag_names,
        "scenarios": [
            {
                "name": scenario.name,
                "description": scenario.description,
                "keyword": scenario.keyword,
                "tags": scenario.tag_names,
                "steps": [
                    {
                        "keyword": step.keyword.strip(),
                        "name": step.name,
                        "doc_string": step.doc_string.content if step.doc_string else None,
                        "table": [
                            [cell.value for cell in row.cells]
                            for row in step.data_table.rows
                        ] if step.data_table else None,
                    }
                    for step in scenario.steps
                ],
            }
            for scenario in feature.scenarios
        ],
    }

assert normalize(structured) == normalize(gherkin), (normalize(structured), normalize(gherkin))
"""
    consumer.struct_bdd_parity_domain_result = subprocess.run(
        [
            str(consumer.python),
            "-c",
            compare_domain_script,
            "features/parity.bdd.yaml",
            "features/parity.feature",
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )

    common_arguments = ["--rootdir=.", "--cuke-summary", "-q", "--color=no"]
    consumer.struct_bdd_parity_runs = [
        _run_consumer_batch_pytest(
            consumer,
            [*common_arguments, "--cuke-json=parity-struct-bdd.json", "features/parity.bdd.yaml"],
        ),
        _run_consumer_batch_pytest(
            consumer,
            [*common_arguments, "--cuke-json=parity-gherkin.json", "features/parity.feature"],
        ),
    ]


@then("both formats should have matching normalized domains and Cucumber reports")
def struct_bdd_gherkin_domain_and_reports_match(consumer: ConsumerProject) -> None:
    domain_result = consumer.struct_bdd_parity_domain_result
    assert domain_result is not None, "the immutable feature model comparison has not run"
    assert domain_result.returncode == 0, f"{domain_result.stdout}\n{domain_result.stderr}"

    runs = consumer.struct_bdd_parity_runs
    assert runs is not None and len(runs) == 2, "the scenario report runs have not completed"
    for result in runs:
        output = _consumer_batch_output(result)
        assert result.returncode == 0, output
        assert "1 passed BDD scenarios, 0 failed, 0 skipped" in output, output

    def normalize_report(relative_path: str) -> dict[str, object]:
        report = json.loads((consumer.path / relative_path).read_text(encoding="utf-8"))
        assert len(report) == 1, report
        feature = report[0]
        return {
            "name": feature["name"],
            "tags": sorted(tag["name"].lstrip("@") for tag in feature["tags"]),
            "scenarios": [
                {
                    "name": scenario["name"],
                    "tags": sorted(tag["name"].lstrip("@") for tag in scenario["tags"]),
                    "steps": [
                        {
                            "keyword": step["keyword"].strip(),
                            "name": step["name"],
                            "status": step["result"]["status"],
                        }
                        for step in scenario["steps"]
                    ],
                }
                for scenario in feature["elements"]
            ],
        }

    assert normalize_report("parity-struct-bdd.json") == normalize_report("parity-gherkin.json")


@given("the consumer has a core Gherkin feature, malformed structured data, and an optional JSON5 feature")
def create_struct_bdd_loader_failure_fixtures(consumer: ConsumerProject) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "core.feature").write_text(
        "Feature: Core Gherkin stays available\n  Scenario: Core scenario passes without optional loaders\n",
        encoding="utf-8",
    )
    (feature_root / "malformed.bdd.json").write_text('{"Name": "Broken", "Steps": [', encoding="utf-8")
    (feature_root / "optional.bdd.json5").write_text(
        _struct_bdd_payload("optional.bdd.json5"),
        encoding="utf-8",
    )


@given("the consumer blocks the optional JSON5 loader")
def block_struct_bdd_json5_loader(consumer: ConsumerProject) -> None:
    (consumer.path / "sitecustomize.py").write_text(
        "import importlib\n"
        "_original_import_module = importlib.import_module\n\n"
        "def _without_json5(name, package=None):\n"
        "    if name == 'json5':\n"
        "        raise ModuleNotFoundError(\"No module named 'json5'\", name='json5')\n"
        "    return _original_import_module(name, package)\n\n"
        "importlib.import_module = _without_json5\n",
        encoding="utf-8",
    )
    consumer.env["PYTHONPATH"] = str(consumer.path)


@then("the StructBDD collection errors should identify both source files and the optional install extra")
def struct_bdd_collection_errors_are_attributed(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = _consumer_batch_output(result)
    assert "INTERNALERROR" not in output, output
    assert "Failed to parse structured BDD" in output, output
    for relative_path in ("features/malformed.bdd.json", "features/optional.bdd.json5"):
        assert str((consumer.path / relative_path).resolve()) in output, output
    assert "json5" in output.lower(), output
    assert "struct-bdd" in output.lower(), output


@then("the core Gherkin scenario should still pass")
def core_gherkin_passes_with_struct_bdd_collection_errors(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    items = []
    for line in _consumer_batch_output(result).splitlines():
        if "features/core.feature::" in line and re.search(r"\bPASSED(?:\s+\[\s*\d+%\])?\s*$", line):
            items.append(line.strip())
    assert len(items) == 1, _consumer_batch_output(result)


def _custom_parser_example_root() -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / "custom-parser-adapter"


def _copy_custom_parser_example(consumer: ConsumerProject) -> None:
    example_root = _custom_parser_example_root()
    assert example_root.is_dir(), f"the runnable custom parser example is missing: {example_root}"
    ignored_names = {"pyproject.toml", "requirements.txt", "readme.md", "readme.rst", ".gitignore"}
    ignored_parts = {".pytest_cache", "__pycache__", ".venv"}

    copied: list[Path] = []
    for source in sorted(example_root.rglob("*")):
        if not source.is_file() or ignored_names.intersection(part.lower() for part in source.parts):
            continue
        relative = source.relative_to(example_root)
        if ignored_parts.intersection(relative.parts):
            continue
        if source.suffix != ".py" and relative.parts[0] != "features":
            continue
        destination = consumer.path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(destination)

    assert any(path.name == "conftest.py" for path in copied), "the custom parser example has no conftest.py"
    feature_files = [path for path in copied if path.is_file() and path.suffix == ".feature"]
    assert len(feature_files) == 1, f"expected one legacy feature in the example, found {feature_files}"
    consumer.env["PYTEST_CUKE_INVOCATION_LOG"] = str(consumer.path / "parser-invocations.json")
    consumer.env.pop("PYTEST_CUKE_LEGACY_MODE", None)


@given("the consumer has the runnable custom parser example")
def copy_custom_parser_example_to_consumer(consumer: ConsumerProject) -> None:
    _copy_custom_parser_example(consumer)


def _custom_parser_feature_path(consumer: ConsumerProject) -> Path:
    feature_files = sorted((consumer.path / "features").rglob("*.feature"))
    assert len(feature_files) == 1, f"expected one custom parser feature, found {feature_files}"
    return feature_files[0]


def _custom_parser_invocation_records(consumer: ConsumerProject) -> list[dict[str, object]]:
    invocation_log = consumer.path / "parser-invocations.json"
    assert invocation_log.is_file(), f"the custom parser did not write its invocation log: {invocation_log}"
    records = json.loads(invocation_log.read_text(encoding="utf-8"))
    assert isinstance(records, list) and all(isinstance(record, dict) for record in records), records
    return records


def _custom_parser_report(consumer: ConsumerProject, relative_path: str) -> dict[str, object]:
    report_path = consumer.path / relative_path
    assert report_path.is_file(), f"pytest did not create the custom parser report: {report_path}"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert isinstance(report, list) and len(report) == 1, report
    feature_report = report[0]
    assert isinstance(feature_report, dict), feature_report
    return feature_report


def _custom_parser_source_name(uri: object) -> str:
    assert isinstance(uri, str), uri
    parsed_uri = urlsplit(uri)
    raw_path = parsed_uri.path if parsed_uri.scheme == "file" else uri
    return PurePosixPath(unquote(raw_path)).name


def _resolved_custom_parser_uri(uri: object, consumer: ConsumerProject, source_path: object | None = None) -> Path:
    assert isinstance(uri, str), uri
    parsed_uri = urlsplit(uri)
    raw_path = unquote(parsed_uri.path if parsed_uri.scheme == "file" else uri)
    uri_path = Path(raw_path)
    if uri_path.is_absolute():
        return uri_path.resolve()

    candidates = []
    if source_path is not None:
        resolved_source = _resolved_consumer_path(source_path, consumer)
        candidates.append(resolved_source.parent / uri_path)
    candidates.extend((consumer.path / "features" / uri_path, consumer.path / uri_path))
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _resolved_consumer_path(path_value: object, consumer: ConsumerProject) -> Path:
    path = Path(str(path_value))
    if not path.is_absolute():
        path = consumer.path / path
    return path.resolve()


@then("the installed custom parser example should preserve its invocation inputs, source, and report identity")
def installed_custom_parser_example_preserves_invocation_and_report(consumer: ConsumerProject) -> None:
    feature_path = _custom_parser_feature_path(consumer).resolve()
    records = _custom_parser_invocation_records(consumer)
    assert len(records) == 1, records
    record = records[0]
    assert set(record) >= {"path", "uri", "config_sentinel", "encoding", "id_sample"}, record
    assert _resolved_consumer_path(record["path"], consumer) == feature_path, record
    assert _custom_parser_source_name(record["uri"]) == feature_path.name, record
    assert record["config_sentinel"] is True, record
    assert record["encoding"] == "utf-8", record
    assert isinstance(record["id_sample"], str) and record["id_sample"], record

    feature_report = _custom_parser_report(consumer, "legacy-report.json")
    assert _resolved_custom_parser_uri(record["uri"], consumer, record["path"]) == _resolved_custom_parser_uri(
        feature_report.get("uri"), consumer
    ), (record, feature_report)
    assert _resolved_custom_parser_uri(feature_report.get("uri"), consumer, record["path"]) == feature_path, (
        feature_report
    )
    assert _custom_parser_source_name(feature_report.get("uri")) == feature_path.name, feature_report
    elements = feature_report.get("elements")
    assert isinstance(elements, list) and len(elements) == 1, feature_report
    scenario_report = elements[0]
    assert isinstance(scenario_report, dict), scenario_report
    assert scenario_report.get("id"), scenario_report
    steps = scenario_report.get("steps")
    assert isinstance(steps, list), scenario_report
    for step in steps:
        assert isinstance(step, dict), step
        step_result = step.get("result")
        assert isinstance(step_result, dict), step
        assert step_result.get("status") == "passed", step


@when("I compare custom parser collection through explicit file, directory, and autoload selection")
def compare_custom_parser_collection_modes(consumer: ConsumerProject) -> None:
    feature_path = _custom_parser_feature_path(consumer).relative_to(consumer.path).as_posix()
    selections = (
        (
            "explicit-file",
            ["--cuke-autoload", "--cuke-features-dir=features", feature_path],
        ),
        (
            "directory",
            ["--cuke-autoload", "--cuke-features-dir=features", "features"],
        ),
        (
            "autoload",
            ["--cuke-autoload", "--cuke-features-dir=features"],
        ),
    )
    runs: list[subprocess.CompletedProcess[str]] = []
    invocation_records: list[list[dict[str, object]]] = []
    feature_reports: list[dict[str, object]] = []
    for name, selection_arguments in selections:
        invocation_log = consumer.path / "parser-invocations.json"
        invocation_log.unlink(missing_ok=True)
        report_name = f"legacy-{name}.json"
        result = _run_consumer_batch_pytest(
            consumer,
            [
                "--rootdir=.",
                *selection_arguments,
                "--cuke-summary",
                f"--cuke-json={report_name}",
                "-vv",
                "--color=no",
            ],
        )
        runs.append(result)
        invocation_records.append(_custom_parser_invocation_records(consumer))
        feature_reports.append(_custom_parser_report(consumer, report_name))

    consumer.custom_parser_selection_runs = runs
    consumer.custom_parser_selection_records = invocation_records
    consumer.custom_parser_selection_reports = feature_reports


@then("all three custom parser collection runs should pass the same scenario once")
def all_custom_parser_collection_modes_pass(consumer: ConsumerProject) -> None:
    runs = consumer.custom_parser_selection_runs
    records = consumer.custom_parser_selection_records
    assert runs is not None and len(runs) == 3, "the custom parser selection runs have not completed"
    assert records is not None and len(records) == 3, "the custom parser invocation logs have not been captured"
    feature_path = _custom_parser_feature_path(consumer).resolve()
    for index, (result, invocation_records) in enumerate(zip(runs, records, strict=True)):
        output = _consumer_batch_output(result)
        assert result.returncode == 0, output
        assert _consumer_batch_pass_count(result) == 1, output
        assert len(invocation_records) == 1, (index, invocation_records, output)
        record = invocation_records[0]
        assert _resolved_consumer_path(record.get("path"), consumer) == feature_path, record
        assert _custom_parser_source_name(record.get("uri")) == feature_path.name, record
        assert record.get("encoding") == "utf-8", record
        assert isinstance(record.get("id_sample"), str) and record["id_sample"], record
        assert record.get("config_sentinel") is True, record


@then("all three custom parser reports should identify the same normalized source")
def custom_parser_selection_reports_match(consumer: ConsumerProject) -> None:
    reports = consumer.custom_parser_selection_reports
    assert reports is not None and len(reports) == 3, "the custom parser reports have not been captured"

    def normalize(report: dict[str, object]) -> dict[str, object]:
        elements = report.get("elements")
        assert isinstance(elements, list) and len(elements) == 1, report
        scenario_report = elements[0]
        assert isinstance(scenario_report, dict), scenario_report
        steps = scenario_report.get("steps")
        assert isinstance(steps, list), scenario_report
        normalized_steps = []
        for step in steps:
            assert isinstance(step, dict), step
            keyword = step.get("keyword", "")
            result = step.get("result")
            assert isinstance(keyword, str), step
            assert isinstance(result, dict), step
            normalized_steps.append((keyword.strip(), step.get("name"), result.get("status")))
        return {
            "source": _resolved_custom_parser_uri(report.get("uri"), consumer),
            "feature": report.get("name"),
            "scenario": scenario_report.get("name"),
            "steps": normalized_steps,
        }

    normalized = [normalize(report) for report in reports]
    assert normalized[1:] == normalized[:1] * 2, normalized


@then("the custom encoding invocation should preserve the Unicode source path and URI")
def custom_parser_encoding_and_unicode_path_are_preserved(consumer: ConsumerProject) -> None:
    feature_path = (consumer.path / "features" / "café.feature").resolve()
    records = _custom_parser_invocation_records(consumer)
    assert len(records) == 1, records
    record = records[0]
    assert _resolved_consumer_path(record.get("path"), consumer) == feature_path, record
    assert _resolved_custom_parser_uri(record.get("uri"), consumer, record.get("path")) == feature_path, record
    assert _custom_parser_source_name(record.get("uri")) == feature_path.name, record
    assert record.get("config_sentinel") is False, record
    assert record.get("encoding") == "latin-1", record
    assert isinstance(record.get("id_sample"), str) and record["id_sample"], record


@given("the consumer has a native Gherkin feature and a custom parser with an absent optional codec")
def create_consumer_optional_codec_contract(consumer: ConsumerProject) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "core.feature").write_text(
        "Feature: Native Gherkin stays available\n"
        "  Scenario: The native parser runs without the custom codec\n"
        "    Given the core parser step starts\n"
        "    Then the core parser step completes\n",
        encoding="utf-8",
    )
    (feature_root / "optional.legacy").write_text("The optional parser requests its codec.\n", encoding="utf-8")
    (consumer.path / "conftest.py").write_text(
        "from pytest_cuke import given, then\n"
        "\n"
        "pytest_plugins = ['optional_parser_plugin']\n"
        "\n"
        "@given('the core parser step starts', target_fixture='core_parser_started')\n"
        "def core_parser_starts():\n"
        "    return True\n"
        "\n"
        "@then('the core parser step completes')\n"
        "def core_parser_completes(core_parser_started):\n"
        "    assert core_parser_started is True\n",
        encoding="utf-8",
    )
    (consumer.path / "optional_parser_plugin.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "import importlib\n"
        "from pathlib import Path\n"
        "\n"
        "from pytest import hookimpl\n"
        "from pytest_cuke.parser import ParserRegistration\n"
        "\n"
        "OPTIONAL_MIMETYPE = 'application/x-optional-legacy-codec'\n"
        "MISSING_CODEC = 'pytest_cuke_optional_custom_codec'\n"
        "\n"
        "class OptionalCodecParser:\n"
        "    def parse(self, config, path: Path, uri: str, *args, **kwargs):\n"
        "        try:\n"
        "            importlib.import_module(MISSING_CODEC)\n"
        "        except ModuleNotFoundError as error:\n"
        "            if error.name != MISSING_CODEC:\n"
        "                raise\n"
        "            raise RuntimeError(\n"
        "                f'Optional custom codec is missing for {path}; '\n"
        "                'install consumer-parser-example[codec].'\n"
        "            ) from error\n"
        "        raise AssertionError('the optional codec unexpectedly exists')\n"
        "\n"
        "@hookimpl(tryfirst=True)\n"
        "def pytest_cuke_is_collectible(config, path: Path):\n"
        "    return True if path.name.casefold().endswith('.legacy') else None\n"
        "\n"
        "@hookimpl(tryfirst=True)\n"
        "def pytest_cuke_get_mimetype(config, path: Path):\n"
        "    return OPTIONAL_MIMETYPE if path.name.casefold().endswith('.legacy') else None\n"
        "\n"
        "@hookimpl(tryfirst=True)\n"
        "def pytest_cuke_get_parser(config, mimetype: str):\n"
        "    return ParserRegistration.legacy(OptionalCodecParser) if mimetype == OPTIONAL_MIMETYPE else None\n",
        encoding="utf-8",
    )


@then("the native Gherkin scenario should pass while the optional codec error is actionable")
def native_gherkin_survives_missing_optional_custom_codec(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = _consumer_batch_output(result)
    assert "INTERNALERROR" not in output, output
    assert "pytest_cuke_optional_custom_codec" in output, output
    assert "consumer-parser-example[codec]" in output, output
    assert str((consumer.path / "features" / "optional.legacy").resolve()) in output, output
    assert _consumer_batch_pass_count(result) == 1, output
    assert any(
        "features/core.feature::" in line and re.search(r"\bPASSED(?:\s+\[\s*\d+%\])?\s*$", line)
        for line in output.splitlines()
    ), output


@given("the consumer has two independent pytest configs using the same legacy parser provider")
def create_custom_parser_session_isolation_consumer(consumer: ConsumerProject) -> None:
    (consumer.path / "parser-invocations.json").unlink(missing_ok=True)
    (consumer.path / "parser-session-state.json").unlink(missing_ok=True)
    (consumer.path / "conftest.py").write_text("", encoding="utf-8")
    for name in ("first", "second"):
        feature_root = consumer.path / "features" / name
        feature_root.mkdir(parents=True, exist_ok=True)
        (feature_root / f"{name}.legacy").write_text(
            f"Feature: {name.title()} parser session\n  Scenario: This config gets its own parser\n",
            encoding="utf-8",
        )

    runner = dedent(
        """\
        from __future__ import annotations

        import json
        import os
        import sys
        from pathlib import Path

        import pytest
        from pytest import hookimpl

        from parser_plugin import LEGACY_MIMETYPE, LegacyFeatureParser
        from pytest_cuke.parser import ParserRegistration


        class SessionScopedLegacyParser(LegacyFeatureParser):
            def __init__(self):
                self.session_marker = None

            def parse(self, config, path, uri, *args, **kwargs):
                marker = config.getoption("custom_parser_session")
                if self.session_marker is None:
                    self.session_marker = marker
                elif self.session_marker != marker:
                    raise RuntimeError("legacy parser instance leaked across pytest configs")

                state_path = Path(os.environ["CUSTOM_PARSER_SESSION_LOG"])
                state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else []
                state.append({"config_marker": marker, "instance_marker": self.session_marker})
                state_path.write_text(json.dumps(state), encoding="utf-8")
                return super().parse(config, path, uri, *args, **kwargs)


        class SessionParserPlugin:
            def __init__(self):
                self.registration = ParserRegistration.legacy(SessionScopedLegacyParser)

            @hookimpl
            def pytest_addoption(self, parser):
                parser.addoption("--custom-parser-session", action="store")

            @hookimpl(tryfirst=True)
            def pytest_cuke_is_collectible(self, config, path):
                return True if path.name.casefold().endswith(".legacy") else None

            @hookimpl(tryfirst=True)
            def pytest_cuke_get_mimetype(self, config, path):
                return LEGACY_MIMETYPE if path.name.casefold().endswith(".legacy") else None

            @hookimpl(tryfirst=True)
            def pytest_cuke_get_parser(self, config, mimetype):
                return self.registration if mimetype == LEGACY_MIMETYPE else None


        exit_codes = []
        for marker in ("first", "second"):
            exit_code = pytest.main(
                [
                    "--rootdir=.",
                    "--cuke-autoload",
                    f"--cuke-features-dir=features/{marker}",
                    "--cuke-summary",
                    "--custom-parser-session",
                    marker,
                ],
                plugins=[SessionParserPlugin()],
            )
            exit_codes.append(int(exit_code))

        Path("session-results.json").write_text(json.dumps(exit_codes), encoding="utf-8")
        sys.exit(0 if exit_codes == [0, 0] else 1)
        """
    )
    (consumer.path / "run_parser_sessions.py").write_text(runner, encoding="utf-8")
    consumer.env["PYTEST_CUKE_INVOCATION_LOG"] = str(consumer.path / "parser-invocations.json")
    consumer.env["CUSTOM_PARSER_SESSION_LOG"] = str(consumer.path / "parser-session-state.json")


@when("I run both custom parser sessions in one consumer process")
def run_custom_parser_sessions_in_one_process(consumer: ConsumerProject) -> None:
    consumer.custom_parser_session_result = subprocess.run(
        [str(consumer.python), str(consumer.path / "run_parser_sessions.py")],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )


@then("each pytest config should receive its own legacy parser instance and registration")
def custom_parser_instances_are_scoped_to_pytest_config(consumer: ConsumerProject) -> None:
    result = consumer.custom_parser_session_result
    assert result is not None, "the in-process pytest sessions have not run"
    output = _consumer_batch_output(result)
    assert result.returncode == 0, output
    assert output.count("1 passed BDD scenarios, 0 failed, 0 skipped") == 2, output
    assert json.loads((consumer.path / "session-results.json").read_text(encoding="utf-8")) == [0, 0]

    state = json.loads((consumer.path / "parser-session-state.json").read_text(encoding="utf-8"))
    assert state == [
        {"config_marker": "first", "instance_marker": "first"},
        {"config_marker": "second", "instance_marker": "second"},
    ], state

    invocations = _custom_parser_invocation_records(consumer)
    assert len(invocations) == 2, invocations
    expected_sources = {
        (consumer.path / "features" / "first" / "first.legacy").resolve(),
        (consumer.path / "features" / "second" / "second.legacy").resolve(),
    }
    assert {_resolved_consumer_path(record.get("path"), consumer) for record in invocations} == expected_sources
    assert {
        _resolved_custom_parser_uri(record.get("uri"), consumer, record.get("path")) for record in invocations
    } == expected_sources
    assert all(record.get("config_sentinel") is True for record in invocations), invocations
    assert all(record.get("encoding") == "utf-8" for record in invocations), invocations
    assert all(isinstance(record.get("id_sample"), str) and record["id_sample"] for record in invocations), invocations


@given("the legacy parser is configured to return a malformed result")
def configure_custom_parser_malformed_result(consumer: ConsumerProject) -> None:
    consumer.env["PYTEST_CUKE_LEGACY_MODE"] = "malformed"


@given("the legacy parser is configured to raise an internal TypeError")
def configure_custom_parser_internal_type_error(consumer: ConsumerProject) -> None:
    consumer.env["PYTEST_CUKE_LEGACY_MODE"] = "type-error"


@then("the legacy parser collection error should name the parser, source, and adapter remedy")
def malformed_custom_parser_result_is_actionable(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = _consumer_batch_output(result)
    assert "INTERNALERROR" not in output, output
    assert "LegacyFeatureParser" in output, output
    assert str(_custom_parser_feature_path(consumer).resolve()) in output, output
    assert "ParserRegistration.legacy" in output, output


@then("the original legacy parser TypeError should be preserved")
def custom_parser_internal_type_error_is_preserved(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = _consumer_batch_output(result)
    assert "INTERNALERROR" not in output, output
    assert "TypeError: intentional legacy parser failure" in output, output
    assert "signature mismatch" not in output.lower(), output


_GENERATION_EXISTING_FEATURE = """Feature: Existing bindings are reused
  Scenario: The user-owned bindings still work
    Given the existing setup is available
    When I parse existing value \"café\"
    Then the original checks still hold
"""

_GENERATION_MISSING_FEATURE = """Feature: A missing binding is generated
  Scenario: The new hook is available
    Then the generated hook is now available
"""

_GENERATION_LITERAL_STEP = 'the message is "Привіт "світе" from C:\\qa\\tests'
_GENERATION_LITERAL_DOCSTRING = """first line: café
second line says \"keep this quoted\"
third line uses C:\\qa\\tests
"""
_GENERATION_LITERAL_FEATURE = f"""Feature: Escaped step text survives generation
  Scenario: The generated step accepts its original multiline payload
    Then {_GENERATION_LITERAL_STEP}
      \"\"\"
      first line: café
      second line says \"keep this quoted\"
      third line uses C:\\qa\\tests
      \"\"\"
"""


def _write_step_generation_consumer(consumer: ConsumerProject, *, include_literal: bool = False) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "existing-bindings.feature").write_text(_GENERATION_EXISTING_FEATURE, encoding="utf-8")
    (feature_root / "missing-hook.feature").write_text(_GENERATION_MISSING_FEATURE, encoding="utf-8")
    if include_literal:
        (feature_root / "literal-generation.feature").write_text(_GENERATION_LITERAL_FEATURE, encoding="utf-8")
    (consumer.path / "conftest.py").write_text('pytest_plugins = ["steps"]\n', encoding="utf-8")
    (consumer.path / "steps.py").write_text(
        """import json
from pathlib import Path

from pytest_cuke import given as setup, parsers, then as verify, when as parse_action

USER_NOTE = "keep this user-owned module code"


@setup("the existing setup is available", target_fixture="example_state")
def existing_setup():
    return {"note": USER_NOTE}


@parse_action(parsers.parse('I parse existing value "{value}"'), target_fixture="parsed_value")
def parse_existing_value(value):
    return value


@verify("the original checks still hold")
def original_checks_still_hold(example_state, parsed_value):
    assert example_state["note"] == USER_NOTE
    assert parsed_value == "café"
""",
        encoding="utf-8",
    )


@given("the consumer has aliased parser bindings and two generation features")
def consumer_with_aliased_parser_bindings_and_two_generation_features(consumer: ConsumerProject) -> None:
    _write_step_generation_consumer(consumer)


@given("the consumer has aliased parser bindings and a multiline literal feature")
def consumer_with_aliased_parser_bindings_and_literal_feature(consumer: ConsumerProject) -> None:
    _write_step_generation_consumer(consumer, include_literal=True)


@given("the consumer has an existing test module for explicit scenario binding")
def consumer_with_existing_test_module_for_scenario_binding(consumer: ConsumerProject) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "explicit-bindings.feature").write_text(_GENERATION_EXISTING_FEATURE, encoding="utf-8")
    (consumer.path / "test_explicit_scenario.py").write_text(
        """from pytest_cuke import given as setup, parsers, scenario, then as verify, when as parse_action

USER_NOTE = "keep this existing test module"


@setup("the existing setup is available", target_fixture="example_state")
def existing_setup():
    return {"note": USER_NOTE}


@parse_action(parsers.parse('I parse existing value "{value}"'), target_fixture="parsed_value")
def parse_existing_value(value):
    return value


@verify("the original checks still hold")
def original_checks_still_hold(example_state, parsed_value):
    assert example_state["note"] == USER_NOTE
    assert parsed_value == "café"
""",
        encoding="utf-8",
    )


@given("the consumer has a generation target and one valid feature")
def consumer_with_generation_target_and_valid_feature(consumer: ConsumerProject) -> None:
    (consumer.path / "features").mkdir(parents=True, exist_ok=True)
    (consumer.path / "features" / "valid.feature").write_text(
        "Feature: A valid generation source\n  Scenario: One missing definition\n    Then a new public binding is needed\n",
        encoding="utf-8",
    )
    (consumer.path / "steps.py").write_text('USER_NOTE = "preserve this target"\n', encoding="utf-8")


@given("the consumer has an invalid generation target and one valid feature")
def consumer_with_invalid_generation_target_and_valid_feature(consumer: ConsumerProject) -> None:
    (consumer.path / "features").mkdir(parents=True, exist_ok=True)
    (consumer.path / "features" / "valid.feature").write_text(
        "Feature: A valid generation source\n  Scenario: One missing definition\n    Then a new public binding is needed\n",
        encoding="utf-8",
    )
    (consumer.path / "steps.py").write_bytes(b'USER_NOTE = "preserve original bytes"\n\ndef invalid(:\n')


@given("the consumer PATH contains a formatter that fails")
def consumer_path_contains_failing_formatter(consumer: ConsumerProject) -> None:
    formatter_dir = consumer.path / ".test-bin"
    formatter_dir.mkdir(exist_ok=True)
    if os.name == "nt":
        formatter = formatter_dir / "ruff.cmd"
        formatter.write_text("@echo off\r\nexit /b 23\r\n", encoding="utf-8")
    else:
        formatter = formatter_dir / "ruff"
        formatter.write_text("#!/bin/sh\nexit 23\n", encoding="utf-8")
        formatter.chmod(0o755)
    consumer.env["PATH"] = f"{formatter_dir}{os.pathsep}{consumer.env['PATH']}"


@step(re.compile(r'I remember the exact bytes of consumer file "(?P<relative_path>[^\"]+)"'))
def remember_consumer_file_bytes(relative_path: str, consumer: ConsumerProject) -> None:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    target = consumer.path / destination
    assert target.is_file(), f"consumer file {relative_path!r} does not exist"
    snapshot_dir = consumer.path / ".generation-snapshots"
    snapshot_dir.mkdir(exist_ok=True)
    snapshot_name = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()
    (snapshot_dir / snapshot_name).write_bytes(target.read_bytes())


@then(re.compile(r'consumer file "(?P<relative_path>[^\"]+)" should match its remembered bytes'))
def consumer_file_matches_generation_snapshot(relative_path: str, consumer: ConsumerProject) -> None:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("consumer file paths must stay inside the consumer project")
    snapshot_name = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()
    snapshot = consumer.path / ".generation-snapshots" / snapshot_name
    assert snapshot.is_file(), f"no byte snapshot was saved for {relative_path!r}"
    actual = (consumer.path / destination).read_bytes()
    expected = snapshot.read_bytes()
    assert actual == expected, f"consumer file {relative_path!r} changed after the generation attempt"


@then("the generated module should retain its existing aliases, parser binding, and user code")
def generated_module_retains_existing_step_bindings(consumer: ConsumerProject) -> None:
    import ast

    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    compile(tree, str(target), "exec")
    assert 'USER_NOTE = "keep this user-owned module code"' in source
    facade_aliases = {
        (alias.name, alias.asname or alias.name)
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "pytest_cuke"
        for alias in node.names
    }
    assert {
        ("given", "setup"),
        ("parsers", "parsers"),
        ("then", "verify"),
        ("when", "parse_action"),
    }.issubset(facade_aliases)
    function_nodes = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {"existing_setup", "parse_existing_value", "original_checks_still_hold"}.issubset(function_nodes)
    setup_decorators = function_nodes["existing_setup"].decorator_list
    assert any(
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "setup"
        and decorator.args
        and isinstance(decorator.args[0], ast.Constant)
        and decorator.args[0].value == "the existing setup is available"
        for decorator in setup_decorators
    )
    parser_decorators = function_nodes["parse_existing_value"].decorator_list
    assert any(
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "parse_action"
        and decorator.args
        and isinstance(decorator.args[0], ast.Call)
        and isinstance(decorator.args[0].func, ast.Attribute)
        and decorator.args[0].func.attr == "parse"
        and decorator.args[0].args
        and isinstance(decorator.args[0].args[0], ast.Constant)
        and decorator.args[0].args[0].value == 'I parse existing value "{value}"'
        for decorator in parser_decorators
    )
    existing_then_decorators = function_nodes["original_checks_still_hold"].decorator_list
    assert any(
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "verify"
        and decorator.args
        and isinstance(decorator.args[0], ast.Constant)
        and decorator.args[0].value == "the original checks still hold"
        for decorator in existing_then_decorators
    )
    generated_definitions = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if any(
            isinstance(decorator, ast.Call)
            and decorator.args
            and isinstance(decorator.args[0], ast.Constant)
            and decorator.args[0].value == "the generated hook is now available"
            for decorator in node.decorator_list
        ):
            generated_definitions.append(node)
    assert len(generated_definitions) == 1
    assert (
        len(
            [
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "original_checks_still_hold"
            ]
        )
        == 1
    )


@then("default generation should not create scenario wrapper files")
def default_generation_does_not_create_scenario_wrappers(consumer: ConsumerProject) -> None:
    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    assert not list(consumer.path.rglob("test_*.py")), "default step generation created a mirror test wrapper"
    assert "@scenario(" not in source, source
    assert "@scenarios(" not in source, source


@then("the chosen module should retain its user code and bind the selected scenario")
def chosen_module_retains_user_code_and_binds_scenario(consumer: ConsumerProject) -> None:
    import ast

    target = consumer.path / "test_explicit_scenario.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    assert 'USER_NOTE = "keep this existing test module"' in source
    scenario_bindings = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if any(
            isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == "scenario"
            for decorator in node.decorator_list
        ):
            scenario_bindings.append(node)
    assert len(scenario_bindings) == 1, source


@then("the generator output should include the missing hook")
def generation_output_includes_missing_hook(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "step generation has not run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert "the generated hook is now available" in output, output


@then(re.compile(r'the generator error should identify "(?P<expected>[^\"]+)"'))
def generation_error_identifies_input(expected: str, consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "step generation has not run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert expected in output, output


@then(re.compile(r'the generator error should identify the invalid target "(?P<target>[^\"]+)"'))
def generation_error_identifies_invalid_target(target: str, consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "step generation has not run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert target in output, output
    assert any(marker in output.lower() for marker in ("invalid", "syntax", "parse")), output


@then("the target should retain the attempted generated definition after formatter failure")
def target_retains_attempted_generation_after_formatter_failure(consumer: ConsumerProject) -> None:
    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    assert 'USER_NOTE = "preserve this target"' in source
    assert "a new public binding is needed" in source
    compile(source, str(target), "exec")


@then("the generated module should compile and preserve the exact escaped step text")
def generated_module_compiles_and_preserves_literal_step(consumer: ConsumerProject) -> None:
    import ast

    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    compile(tree, str(target), "exec")
    matching_definitions = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not decorator.args:
                continue
            argument = decorator.args[0]
            if isinstance(argument, ast.Constant) and argument.value == _GENERATION_LITERAL_STEP:
                matching_definitions.append(node)
    assert len(matching_definitions) == 1, source


@when("I fill the generated step stubs to record their executions")
def fill_generated_step_stubs_to_record_executions(consumer: ConsumerProject) -> None:
    import ast

    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    expected_phrases = {"the generated hook is now available", _GENERATION_LITERAL_STEP}
    matching_definitions = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not decorator.args:
                continue
            argument = decorator.args[0]
            if isinstance(argument, ast.Constant) and argument.value in expected_phrases:
                matching_definitions.append(node)
                break
    names = {node.name for node in matching_definitions}
    assert len(names) == len(expected_phrases), f"not all generated stubs were found: {names}"

    lines = source.splitlines(keepends=True)
    for node in sorted(matching_definitions, key=lambda item: item.lineno, reverse=True):
        replacement = [
            f"def {node.name}(step):\n",
            '    event_path = Path("generated-step-events.json")\n',
            '    records = json.loads(event_path.read_text(encoding="utf-8")) if event_path.exists() else []\n',
            '    doc_string = getattr(step, "doc_string", None)\n',
            '    records.append({"text": step.text, "doc_string": None if doc_string is None else doc_string.content})\n',
            '    event_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")\n',
            "",
        ]
        lines[node.lineno - 1 : node.end_lineno] = replacement
    target.write_text("".join(lines), encoding="utf-8")
    compile(target.read_text(encoding="utf-8"), str(target), "exec")


@then("the generated literal step should have executed once with its original multiline payload")
def generated_literal_step_executed_once_with_multiline_payload(consumer: ConsumerProject) -> None:
    records = json.loads((consumer.path / "generated-step-events.json").read_text(encoding="utf-8"))
    matching = [record for record in records if record["text"] == _GENERATION_LITERAL_STEP]
    assert len(matching) == 1, records
    assert matching[0]["doc_string"].rstrip("\n") == _GENERATION_LITERAL_DOCSTRING.rstrip("\n"), records


@fixture(scope="session")
def _step_generation_consumer_wheel(request, tmp_path_factory):
    project_root = Path(request.config.rootpath)
    artifact_dir = tmp_path_factory.mktemp("pytest-cuke-step-generation-wheel")
    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed step-generation contract requires uv to build a wheel"
    build_environment = os.environ.copy()
    build_environment["PYTEST_CUKE_BUILD_GO"] = "off"
    build_result = subprocess.run(
        [uv_executable, "build", "--wheel", "--out-dir", str(artifact_dir), str(project_root)],
        cwd=project_root,
        env=build_environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert build_result.returncode == 0, (
        f"could not build the step-generation consumer wheel:\n{build_result.stdout}\n{build_result.stderr}"
    )
    wheels = list(artifact_dir.glob("pytest_cuke-*.whl"))
    assert len(wheels) == 1, f"expected one pytest-cuke wheel, found {wheels}"

    consumer_interpreter = sys.executable
    environment_path = tmp_path_factory.mktemp("pytest-cuke-step-generation-venv")
    create_environment = subprocess.run(
        [uv_executable, "venv", "--python", consumer_interpreter, str(environment_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert create_environment.returncode == 0, (
        f"could not create step-generation consumer environment:\n"
        f"{create_environment.stdout}\n{create_environment.stderr}"
    )
    binary_dir = _consumer_binary_dir(environment_path)
    python_path = _consumer_executable(binary_dir, "python")
    install = subprocess.run(
        [uv_executable, "pip", "install", "--python", str(python_path), str(wheels[0])],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, (
        f"could not install step-generation consumer wheel:\n{install.stdout}\n{install.stderr}"
    )
    return {"environment_path": environment_path, "wheel": wheels[0]}


@given(
    "the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project",
    target_fixture="consumer",
)
def install_step_generation_consumer(_step_generation_consumer_wheel, tmp_path_factory):
    project_path = tmp_path_factory.mktemp("pytest-cuke-step-generation-consumer")
    (project_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_features_dir = 'features'\ncuke_autoload = true\n",
        encoding="utf-8",
    )
    environment_path = _step_generation_consumer_wheel["environment_path"]
    binary_dir = _consumer_binary_dir(environment_path)
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
    if os.name == "nt":
        environment["USERPROFILE"] = str(consumer_home)
    return ConsumerProject(
        path=project_path,
        python=_consumer_executable(binary_dir, "python"),
        pytest=_consumer_executable(binary_dir, "pytest"),
        cuke=_consumer_executable(binary_dir, "cuke"),
        env=environment,
        artifact=_step_generation_consumer_wheel["wheel"],
    )


@given("the consumer has a generation feature but no target module")
def consumer_with_feature_but_missing_generation_target(consumer: ConsumerProject) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "missing-target.feature").write_text(
        "Feature: Missing target path\n  Scenario: Generate a missing step\n    Then a target would be useful\n",
        encoding="utf-8",
    )


@given("the consumer has two ambiguous bindings for one generation feature")
def consumer_with_ambiguous_bindings(consumer: ConsumerProject) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "ambiguous-bindings.feature").write_text(
        "Feature: Ambiguous bindings\n  Scenario: The step matches twice\n    Then the ambiguous value is ready\n",
        encoding="utf-8",
    )
    (consumer.path / "steps.py").write_text(
        """from pytest_cuke import parsers, then as verify

USER_NOTE = "preserve both ambiguous bindings"


@verify(parsers.parse("the ambiguous value is {value}"))
def first_ambiguous_binding(value):
    pass


@verify(parsers.parse("the ambiguous value is {value}"))
def second_ambiguous_binding(value):
    pass
""",
        encoding="utf-8",
    )


@given("the consumer has an autouse fixture that fails during generation inspection")
def consumer_with_failing_autouse_fixture(consumer: ConsumerProject) -> None:
    feature_root = consumer.path / "features"
    feature_root.mkdir(parents=True, exist_ok=True)
    (feature_root / "fixture-failure.feature").write_text(
        "Feature: Parser fixture setup failure\n  Scenario: The parser fixture fails\n    Then the fixture value is ready\n",
        encoding="utf-8",
    )
    (consumer.path / "steps.py").write_text(
        'USER_NOTE = "preserve this module when inspection fails"\n',
        encoding="utf-8",
    )
    (consumer.path / "conftest.py").write_text(
        """from pathlib import Path

from pytest import fixture


@fixture(autouse=True)
def fail_generation_inspection(request):
    request.addfinalizer(lambda: Path("fixture-cleanup.txt").write_text("cleaned", encoding="utf-8"))
    raise RuntimeError("intentional generation fixture setup failure")
""",
        encoding="utf-8",
    )


@then("the generator should provide an actionable ambiguity error")
def generation_reports_ambiguous_step_bindings(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "step generation has not run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert "ambiguous existing step definitions" in output.lower(), output
    assert "the ambiguous value is ready" in output, output
    assert "remove or narrow one matching parser" in output, output


@then("the fixture setup failure should be reported and its cleanup finalizer should run")
def parser_fixture_setup_failure_runs_finalizer(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "step generation has not run in this consumer"
    assert result.returncode != 0, f"fixture setup unexpectedly succeeded:\n{result.stdout}\n{result.stderr}"
    output = f"{result.stdout}\n{result.stderr}"
    assert "intentional generation fixture setup failure" in output, output
    cleanup = consumer.path / "fixture-cleanup.txt"
    assert cleanup.read_text(encoding="utf-8") == "cleaned", "pytest did not run the fixture finalizer"


@given("the consumer has an aliased scenario binding that uses the configured feature directory")
def consumer_with_aliased_scenario_binding_using_configured_feature_directory(consumer: ConsumerProject) -> None:
    _write_step_generation_consumer(consumer)
    feature_path = consumer.path / "features" / "explicit-bindings.feature"
    feature_path.write_text(
        "Feature: Explicit feature directory binding\n"
        "  Scenario: Existing scenario\n"
        "    Given the existing setup is available\n"
        '    When I parse existing value "café"\n'
        "    Then the original checks still hold\n",
        encoding="utf-8",
    )
    step_module = (consumer.path / "steps.py").read_text(encoding="utf-8")
    facade_import = "from pytest_cuke import given as setup, parsers, then as verify, when as parse_action"
    aliased_facade_import = (
        "from pytest_cuke import given as setup, parsers, scenario as bind_scenario, "
        "then as verify, when as parse_action"
    )
    assert facade_import in step_module
    test_module = step_module.replace(facade_import, aliased_facade_import, 1)
    test_module += """


@bind_scenario("explicit-bindings.feature", "Existing scenario")
def test_existing_scenario_binding():
    assert USER_NOTE == "keep this user-owned module code"
"""
    (consumer.path / "test_aliased_scenario.py").write_text(test_module, encoding="utf-8")


@then("the existing aliased scenario binding should not be duplicated")
def existing_aliased_scenario_binding_is_not_duplicated(consumer: ConsumerProject) -> None:
    import ast

    target = consumer.path / "test_aliased_scenario.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    bindings = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Name):
                continue
            if decorator.func.id in {"bind_scenario", "scenario"}:
                bindings.append((node, decorator))
    assert len(bindings) == 1, source
    _, binding = bindings[0]
    assert len(binding.args) >= 2
    assert isinstance(binding.args[0], ast.Constant) and binding.args[0].value == "explicit-bindings.feature"
    assert isinstance(binding.args[1], ast.Constant) and binding.args[1].value == "Existing scenario"


@then("the preview output should include the diff without pytest collection output")
def generation_preview_shows_diff_without_collection_output(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "step generation has not run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    lines = output.splitlines()
    assert any(line.startswith("--- ") for line in lines), output
    assert any(line.startswith("+++ ") for line in lines), output
    assert any(line.startswith("@@") for line in lines), output
    assert any(line.startswith("+") and "the generated hook is now available" in line for line in lines), output
    assert "test_cuke_generation_" not in output, output


@given("the consumer has an absolute scenarios glob binding for a generation feature")
def consumer_with_absolute_scenarios_glob_binding(consumer: ConsumerProject) -> None:
    _write_step_generation_consumer(consumer)
    feature_root = consumer.path / "features"
    (feature_root / "absolute-glob.feature").write_text(
        "Feature: Absolute scenarios glob binding\n"
        "  Scenario: The absolute glob already binds this feature\n"
        "    Given the existing setup is available\n"
        '    When I parse existing value "café"\n'
        "    Then the original checks still hold\n",
        encoding="utf-8",
    )
    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    facade_import = "from pytest_cuke import given as setup, parsers, then as verify, when as parse_action"
    scenarios_import = (
        "from pytest_cuke import given as setup, parsers, scenarios, then as verify, when as parse_action"
    )
    assert facade_import in source
    source = source.replace(facade_import, scenarios_import, 1)
    absolute_pattern = str((feature_root / "*.feature").resolve())
    source += f"""


@scenarios({absolute_pattern!r}, return_test_decorator=True)
def test_all_features_from_absolute_glob():
    pass
"""
    target.write_text(source, encoding="utf-8")


@then("the existing absolute scenarios glob binding should not be duplicated")
def existing_absolute_scenarios_glob_is_not_duplicated(consumer: ConsumerProject) -> None:
    import ast

    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    glob_bindings = []
    direct_scenario_bindings = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Name):
                continue
            if decorator.func.id == "scenarios":
                glob_bindings.append(decorator)
            elif decorator.func.id == "scenario":
                direct_scenario_bindings.append(decorator)
    assert len(glob_bindings) == 1, source
    assert not direct_scenario_bindings, source
    binding_path = glob_bindings[0].args[0]
    assert isinstance(binding_path, ast.Constant) and isinstance(binding_path.value, str), source
    expected_pattern = str((consumer.path / "features" / "*.feature").resolve())
    assert binding_path.value == expected_pattern, source
    assert Path(binding_path.value).is_absolute(), source


@given("the consumer has a shallow scenarios glob and a nested generation feature")
def consumer_with_shallow_scenarios_glob_and_nested_feature(consumer: ConsumerProject) -> None:
    _write_step_generation_consumer(consumer)
    nested_feature = consumer.path / "features" / "area" / "nested" / "nested-scenario.feature"
    nested_feature.parent.mkdir(parents=True, exist_ok=True)
    nested_feature.write_text(
        "Feature: Nested feature outside shallow glob\n"
        "  Scenario: Nested scenario\n"
        "    Given the existing setup is available\n"
        '    When I parse existing value "café"\n'
        "    Then the original checks still hold\n",
        encoding="utf-8",
    )
    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    facade_import = "from pytest_cuke import given as setup, parsers, then as verify, when as parse_action"
    scenarios_import = (
        "from pytest_cuke import given as setup, parsers, scenarios, then as verify, when as parse_action"
    )
    assert facade_import in source
    source = source.replace(facade_import, scenarios_import, 1)
    source += """


@scenarios("*/*.feature", filter_="Nested scenario", return_test_decorator=True)
def test_nested_scenario_glob():
    pass
"""
    target.write_text(source, encoding="utf-8")


@then("the nested feature should have an explicit generated scenario binding")
def nested_feature_has_generated_explicit_scenario_binding(consumer: ConsumerProject) -> None:
    import ast

    target = consumer.path / "steps.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    glob_bindings = []
    explicit_bindings = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Name):
                continue
            if decorator.func.id == "scenarios":
                glob_bindings.append(decorator)
            elif decorator.func.id == "scenario":
                explicit_bindings.append(decorator)

    assert len(glob_bindings) == 1, source
    glob_binding = glob_bindings[0]
    assert glob_binding.args and isinstance(glob_binding.args[0], ast.Constant)
    assert glob_binding.args[0].value == "*/*.feature", source
    filter_value = next(keyword.value for keyword in glob_binding.keywords if keyword.arg == "filter_")
    assert isinstance(filter_value, ast.Constant) and filter_value.value == "Nested scenario", source

    assert len(explicit_bindings) == 1, source
    explicit_binding = explicit_bindings[0]
    assert len(explicit_binding.args) >= 2
    path_literals = [node.value for node in ast.walk(explicit_binding.args[0]) if isinstance(node, ast.Constant)]
    assert "features/area/nested/nested-scenario.feature" in path_literals, source
    scenario_name = explicit_binding.args[1]
    assert isinstance(scenario_name, ast.Constant) and scenario_name.value == "Nested scenario", source


@given("the consumer has no pytest configuration and an aliased relative scenario binding")
def consumer_without_pytest_configuration_and_with_relative_scenario_binding(consumer: ConsumerProject) -> None:
    for name in ("pytest.ini", ".pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml"):
        (consumer.path / name).unlink(missing_ok=True)

    feature_path = consumer.path / "features" / "relative.feature"
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    feature_path.write_text(
        "Feature: Relative scenario binding\n"
        "  Scenario: Existing scenario\n"
        "    Given the existing setup is available\n"
        '    When I parse existing value "café"\n'
        "    Then the original checks still hold\n",
        encoding="utf-8",
    )

    target = consumer.path / "tests" / "test_bindings.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """from pytest_cuke import given as setup, parsers, scenario as bind_scenario, then as verify, when as parse_action

USER_NOTE = "preserve the existing relative binding module"


@setup("the existing setup is available", target_fixture="example_state")
def existing_setup():
    return {"note": USER_NOTE}


@parse_action(parsers.parse('I parse existing value "{value}"'), target_fixture="parsed_value")
def parse_existing_value(value):
    return value


@verify("the original checks still hold")
def original_checks_still_hold(example_state, parsed_value):
    assert example_state["note"] == USER_NOTE
    assert parsed_value == "café"


@bind_scenario('relative.feature', 'Existing scenario')
def test_existing_relative_binding():
    assert USER_NOTE == "preserve the existing relative binding module"
""",
        encoding="utf-8",
    )


@then("the existing relative scenario binding should not be duplicated")
def existing_relative_scenario_binding_is_not_duplicated(consumer: ConsumerProject) -> None:
    import ast

    target = consumer.path / "tests" / "test_bindings.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    bindings = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Name):
                continue
            if decorator.func.id in {"bind_scenario", "scenario"}:
                bindings.append(decorator)

    assert len(bindings) == 1, source
    binding = bindings[0]
    assert len(binding.args) >= 2
    assert isinstance(binding.args[0], ast.Constant) and binding.args[0].value == "relative.feature", source
    assert isinstance(binding.args[1], ast.Constant) and binding.args[1].value == "Existing scenario", source
    config_names = ("pytest.ini", ".pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml")
    assert not any((consumer.path / name).exists() for name in config_names)


def _write_compatibility_pyproject(
    consumer: ConsumerProject,
    *,
    python_factors: tuple[str, ...],
    pytest_factors: tuple[str, ...],
    execution_targets: tuple[str, ...],
    tox_env_template: str = "py{python}-pytest{pytest}-{target}",
) -> None:
    python_values = ", ".join(json.dumps(value) for value in python_factors)
    pytest_values = ", ".join(json.dumps(value) for value in pytest_factors)
    target_values = ", ".join(json.dumps(value) for value in execution_targets)
    (consumer.path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        'cuke_features_dir = "features"\n'
        "cuke_autoload = true\n\n"
        "[tool.pytest-cuke.compatibility]\n"
        f"python-factors = [{python_values}]\n"
        f"pytest-factors = [{pytest_values}]\n"
        f"execution-targets = [{target_values}]\n"
        f"tox-env-template = {json.dumps(tox_env_template)}\n",
        encoding="utf-8",
    )


def _write_migration_audit_configuration(
    consumer: ConsumerProject,
    *,
    threshold_percent: int,
    feature_patterns: tuple[str, ...] = ("features/**/*.feature",),
    test_registration_patterns: tuple[str, ...] = ("tests/**/*.py",),
) -> None:
    feature_values = ", ".join(json.dumps(value) for value in feature_patterns)
    test_values = ", ".join(json.dumps(value) for value in test_registration_patterns)
    (consumer.path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        'cuke_features_dir = "features"\n'
        "cuke_autoload = true\n\n"
        "[tool.pytest-cuke.migration-audit]\n"
        f"feature-patterns = [{feature_values}]\n"
        f"test-registration-patterns = [{test_values}]\n"
        f"threshold-percent = {threshold_percent}\n",
        encoding="utf-8",
    )


@given("the consumer has a compatibility matrix spanning supported and excluded pairs")
def consumer_with_configured_compatibility_matrix(consumer: ConsumerProject) -> None:
    _write_compatibility_pyproject(
        consumer,
        python_factors=("39", "310", "314"),
        pytest_factors=("62", "80", "latest"),
        execution_targets=("lin", "win"),
    )


@then("the compatibility matrix JSON should include each configured factor pairing")
def compatibility_matrix_contains_configured_factor_pairs(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "the compatibility matrix command has not run"
    payload = json.loads(result.stdout)
    entries = payload["entries"]
    assert len(entries) == 9, entries
    actual_pairs = {(entry["pythonVersion"], entry["pytestVersion"]) for entry in entries}
    assert actual_pairs == {
        (python, pytest) for python in ("3.9", "3.10", "3.14") for pytest in ("6.2", "8.0", "latest")
    }
    expected_fields = {
        "pythonVersion",
        "pytestVersion",
        "isCompatible",
        "isSupported",
        "reasonCode",
        "executionTargets",
        "compatibilitySource",
        "toxEnvName",
    }
    assert all(expected_fields <= entry.keys() for entry in entries), entries
    assert all(entry["executionTargets"] == ["lin", "win"] for entry in entries), entries
    assert {entry["reasonCode"] for entry in entries} >= {
        "compatible",
        "eol_python",
        "eol_pytest",
        "python_not_supported_by_pytest",
    }


@then("the compatible-only matrix should contain no incompatible entries")
def compatible_only_matrix_filters_incompatible_pairs(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "the compatible-only matrix command has not run"
    entries = json.loads(result.stdout)["entries"]
    assert entries, "the configured matrix should include compatible pairs"
    assert all(entry["isCompatible"] for entry in entries), entries


@then(
    re.compile(
        r'the compatibility pair should be (?P<compatibility>compatible|incompatible) with reason "(?P<reason>[^"]+)"'
    )
)
def compatibility_pair_reports_expected_reason(compatibility: str, reason: str, consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a compatibility pair command has not run"
    payload = json.loads(result.stdout)
    assert payload["isCompatible"] is (compatibility == "compatible"), payload
    assert payload["reasonCode"] == reason, payload


@then(re.compile(r"the compatibility pair should be (?P<support>supported|unsupported) by the project"))
def compatibility_pair_reports_project_support(support: str, consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a compatibility pair command has not run"
    payload = json.loads(result.stdout)
    assert payload["isSupported"] is (support == "supported"), payload


@given("the consumer has active TOML and alternate INI and TOML compatibility configurations")
def consumer_with_default_and_alternate_compatibility_configs(consumer: ConsumerProject) -> None:
    _write_compatibility_pyproject(
        consumer,
        python_factors=("310", "311"),
        pytest_factors=("80", "latest"),
        execution_targets=("lin", "win"),
    )
    (consumer.path / "alternate.ini").write_text(
        "[tox]\nenv_list =\n    py312-pytest90-lin\n    py312-pytest90-win\n",
        encoding="utf-8",
    )
    (consumer.path / "alternate.toml").write_text(
        "[tool.pytest-cuke.compatibility]\n"
        'python-factors = ["314"]\n'
        'pytest-factors = ["latest"]\n'
        'execution-targets = ["mac"]\n'
        'tox-env-template = "py{python}-pytest{pytest}-{target}"\n',
        encoding="utf-8",
    )


@when("I run cuke compatibility tox expansion twice in the consumer project")
def run_compatibility_tox_expansion_twice(consumer: ConsumerProject) -> None:
    command = [str(consumer.cuke), "compatibility", "--expand-tox", "--json"]
    runs = [
        subprocess.run(
            command,
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
        )
        for _ in range(2)
    ]
    consumer._compatibility_expansion_runs = runs
    consumer.command_result = runs[-1]


@then("the tox expansion should be deterministic and include all factor combinations")
def tox_expansion_is_deterministic_and_complete(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "_compatibility_expansion_runs", None)
    assert runs is not None and len(runs) == 2, "the repeated compatibility expansion has not run"
    assert all(run.returncode == 0 for run in runs), [(run.stdout, run.stderr) for run in runs]
    assert runs[0].stdout == runs[1].stdout, "repeated tox expansion changed its JSON output"
    names = json.loads(runs[-1].stdout)["toxEnvNames"]
    assert len(names) == 8 and len(set(names)) == 8, names
    assert set(names) == {
        f"py{python}-pytest{pytest}-{target}"
        for python in ("310", "311")
        for pytest in ("80", "latest")
        for target in ("lin", "win")
    }


@when(
    re.compile(
        r'I run cuke compatibility from outside the consumer with config "(?P<config>[^"]+)" '
        r'and arguments "(?P<arguments>[^"]*)"'
    )
)
def run_compatibility_from_outside_consumer(config: str, arguments: str, consumer: ConsumerProject) -> None:
    config_path = consumer.path / config
    result = subprocess.run(
        [str(consumer.cuke), "compatibility", *shlex.split(arguments), "--config", str(config_path)],
        cwd=consumer.path.parent,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    consumer.command_result = result


@given("the consumer has a migration audit with one registration and one autoload-only feature scenario")
def consumer_with_complete_autoload_migration_audit(consumer: ConsumerProject) -> None:
    _write_migration_audit_configuration(consumer, threshold_percent=50)
    feature = consumer.path / "features" / "accounts.feature"
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text(
        "Feature: Account management\n"
        "  Scenario: Create account\n"
        "    Given an account is ready\n"
        "  Scenario: Delete account\n"
        "    Given an account is ready\n",
        encoding="utf-8",
    )
    tests = consumer.path / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "test_account_bindings.py").write_text(
        "from pytest_cuke import scenario\n\n"
        '@scenario("./features/./accounts.feature", "Create account")\n'
        "def test_create_account():\n"
        "    pass\n\n"
        'DOCUMENTATION = \'@scenario("features/accounts.feature", "Delete account")\'\n\n'
        "def nested_example():\n"
        '    @scenario("features/accounts.feature", "Delete account")\n'
        "    def test_nested_registration():\n"
        "        pass\n",
        encoding="utf-8",
    )


@then("the migration audit should report the configured identities and threshold")
def migration_audit_reports_normalized_identities_and_threshold(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "the migration audit command has not run"
    payload = json.loads(result.stdout)
    assert payload["totalUserFacingScenarios"] == 2, payload
    assert payload["userFacingInFeatures"] == 2, payload
    assert payload["coveragePercent"] == 100.0, payload
    assert payload["thresholdPercent"] == 50, payload
    assert payload["thresholdMet"] is True, payload
    assert payload["duplicatesInTests"] == 0, payload
    assert payload["featureScenarioIds"] == [
        "features/accounts.feature::create account",
        "features/accounts.feature::delete account",
    ], payload
    assert payload["userFacingTestScenarioIds"] == ["features/accounts.feature::create account"], payload


@then("the autoload-only scenario should not require a mirror wrapper file")
def autoload_only_scenario_needs_no_mirror_wrapper(consumer: ConsumerProject) -> None:
    assert not (consumer.path / "tests" / "test_delete_account.py").exists()
    assert (consumer.path / "features" / "accounts.feature").is_file()


@given("the consumer uses a non-default autoload feature root for migration audit")
def consumer_with_non_default_autoload_feature_root(consumer: ConsumerProject) -> None:
    (consumer.path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ncuke_features_dir = "spec/features"\ncuke_autoload = true\n',
        encoding="utf-8",
    )
    feature = consumer.path / "spec" / "features" / "orders.feature"
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text(
        "Feature: Order management\n  Scenario: Submit order\n    Given an order is ready\n",
        encoding="utf-8",
    )


@then("the migration audit should count the active autoload feature without a wrapper")
def migration_audit_counts_active_autoload_feature_root(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "the migration audit command has not run"
    payload = json.loads(result.stdout)
    assert payload["totalUserFacingScenarios"] == 1, payload
    assert payload["userFacingInFeatures"] == 1, payload
    assert payload["coveragePercent"] == 100.0, payload
    assert payload["thresholdMet"] is True, payload
    assert payload["featureScenarioIds"] == ["spec/features/orders.feature::submit order"], payload
    assert payload["userFacingTestScenarioIds"] == [], payload
    assert not (consumer.path / "features" / "orders.feature").exists()
    assert not (consumer.path / "tests" / "test_orders.py").exists()


@given("the consumer has a non-string migration feature pattern")
def consumer_with_non_string_migration_feature_pattern(consumer: ConsumerProject) -> None:
    (consumer.path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        'cuke_features_dir = "features"\n'
        "cuke_autoload = true\n\n"
        "[tool.pytest-cuke.migration-audit]\n"
        "feature-patterns = [42]\n"
        'test-registration-patterns = ["tests/**/*.py"]\n'
        "threshold-percent = 80\n",
        encoding="utf-8",
    )


@given("the consumer has an empty migration audit inventory")
def consumer_with_empty_migration_inventory(consumer: ConsumerProject) -> None:
    _write_migration_audit_configuration(consumer, threshold_percent=80)


@then("the migration audit should report an empty inventory as complete")
def empty_migration_inventory_is_complete(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "the migration audit command has not run"
    payload = json.loads(result.stdout)
    assert payload["totalUserFacingScenarios"] == 0, payload
    assert payload["userFacingInFeatures"] == 0, payload
    assert payload["coveragePercent"] == 100.0, payload
    assert payload["thresholdMet"] is True, payload
    assert payload["duplicatesInTests"] == 0, payload


@given("the consumer has duplicate normalized migration scenario registrations")
def consumer_with_duplicate_normalized_migration_registrations(consumer: ConsumerProject) -> None:
    _write_migration_audit_configuration(consumer, threshold_percent=100)
    feature = consumer.path / "features" / "accounts.feature"
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text(
        "Feature: Account management\n  Scenario: Create account\n    Given an account is ready\n",
        encoding="utf-8",
    )
    tests = consumer.path / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "test_account_bindings.py").write_text(
        "from pytest_cuke import scenario\n\n"
        '@scenario("./features/./accounts.feature", "Create account")\n'
        "def test_create_account():\n"
        "    pass\n\n"
        '@scenario("features/accounts.feature", "Create account")\n'
        "def test_create_account_again():\n"
        "    pass\n",
        encoding="utf-8",
    )


@then("the migration audit should report duplicate scenario registrations")
def migration_audit_reports_duplicate_scenario_registrations(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "the migration audit command has not run"
    payload = json.loads(result.stdout)
    assert payload["duplicatesInTests"] > 0, payload
    assert payload["coveragePercent"] == 100.0, payload
    assert payload["thresholdMet"] is False, payload
    duplicate_ids = payload.get("duplicateScenarioIds")
    if duplicate_ids is not None:
        assert "features/accounts.feature::create account" in duplicate_ids, payload


@given("the consumer has one feature scenario and one unmatched registration with an eighty percent threshold")
def consumer_with_migration_coverage_below_threshold(consumer: ConsumerProject) -> None:
    _write_migration_audit_configuration(consumer, threshold_percent=80)
    feature = consumer.path / "features" / "accounts.feature"
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text(
        "Feature: Account management\n  Scenario: Create account\n    Given an account is ready\n",
        encoding="utf-8",
    )
    tests = consumer.path / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "test_account_bindings.py").write_text(
        "from pytest_cuke import scenario\n\n"
        '@scenario("features/accounts.feature", "Create account")\n'
        "def test_create_account():\n"
        "    pass\n\n"
        '@scenario("features/accounts.feature", "Delete account")\n'
        "def test_delete_account():\n"
        "    pass\n",
        encoding="utf-8",
    )


@then("the migration audit should report fifty percent coverage below threshold")
def migration_audit_reports_coverage_below_threshold(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "the migration audit command has not run"
    payload = json.loads(result.stdout)
    assert payload["totalUserFacingScenarios"] == 2, payload
    assert payload["userFacingInFeatures"] == 1, payload
    assert payload["coveragePercent"] == 50.0, payload
    assert payload["thresholdPercent"] == 80, payload
    assert payload["thresholdMet"] is False, payload
    assert payload["duplicatesInTests"] == 0, payload


@then(re.compile(r'compatibility stderr should contain "(?P<message>[^"]+)"'))
def compatibility_diagnostic_is_actionable(message: str, consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a compatibility command has not run"
    assert message in result.stderr, f"expected {message!r} in stderr:\n{result.stderr}"


@then("command diagnostics should be stderr-only")
def compatibility_diagnostics_are_stderr_only(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a compatibility command has not run"
    assert result.stdout == "", f"diagnostic output leaked to stdout:\n{result.stdout}"
    assert result.stderr.strip(), "expected an actionable diagnostic on stderr"


def _background_messages_artifact(relative_path: str, consumer: ConsumerProject) -> list[dict[str, object]]:
    artifact = consumer.path / relative_path
    lines = artifact.read_text(encoding="utf-8").splitlines()
    assert lines, f"Cucumber Messages artifact is empty: {artifact}"
    envelopes = [json.loads(line) for line in lines]
    for envelope in envelopes:
        _validate_messages_envelope_compatibly(envelope)
    return envelopes


def _assert_background_message_references(envelopes: list[dict[str, object]]) -> None:
    pickles = {pickle["id"]: pickle for envelope in envelopes if (pickle := envelope.get("pickle")) is not None}
    cases = {case["id"]: case for envelope in envelopes if (case := envelope.get("testCase")) is not None}
    starts = {
        started["id"]: started for envelope in envelopes if (started := envelope.get("testCaseStarted")) is not None
    }
    case_finishes = [finished for envelope in envelopes if (finished := envelope.get("testCaseFinished")) is not None]
    step_starts = [started for envelope in envelopes if (started := envelope.get("testStepStarted")) is not None]
    step_finishes = [finished for envelope in envelopes if (finished := envelope.get("testStepFinished")) is not None]
    run_finishes = [finished for envelope in envelopes if (finished := envelope.get("testRunFinished")) is not None]

    assert pickles, "the Messages stream has no expanded pickle records"
    assert len(cases) == len(pickles), (cases, pickles)
    assert len(starts) == len(cases), (starts, cases)
    assert len(case_finishes) == len(starts), (case_finishes, starts)
    assert {finished["testCaseStartedId"] for finished in case_finishes} == set(starts)
    assert len(run_finishes) == 1, run_finishes

    test_step_case_ids: dict[str, set[str]] = {}
    test_step_ids: list[str] = []
    for case in cases.values():
        pickle_id = case["pickleId"]
        assert pickle_id in pickles, f"test case references missing pickle {pickle_id!r}"
        pickle_step_ids = [step["id"] for step in pickles[pickle_id]["steps"]]
        test_steps = case["testSteps"]
        assert [step["pickleStepId"] for step in test_steps] == pickle_step_ids, (case, pickles[pickle_id])
        assert len({step["id"] for step in test_steps}) == len(test_steps), case
        for test_step in test_steps:
            test_step_ids.append(test_step["id"])
            test_step_case_ids.setdefault(test_step["id"], set()).add(case["id"])
    assert len(test_step_ids) == len(set(test_step_ids)), test_step_ids

    started_by_case = {started["testCaseId"]: started for started in starts.values()}
    assert len(started_by_case) == len(starts), started_by_case
    for event in step_starts:
        case_started = starts.get(event["testCaseStartedId"])
        assert case_started is not None, f"test step start references missing run {event!r}"
        case = cases[case_started["testCaseId"]]
        valid_test_step_ids = {step["id"] for step in case["testSteps"]}
        assert event["testStepId"] in valid_test_step_ids, (event, case)

    finished_references: list[tuple[str, str]] = []
    for event in step_finishes:
        case_started = starts.get(event["testCaseStartedId"])
        assert case_started is not None, f"test step finish references missing run {event!r}"
        case_id = case_started["testCaseId"]
        assert event["testStepId"] in test_step_case_ids, event
        assert case_id in test_step_case_ids[event["testStepId"]], (event, case_id)
        finished_references.append((event["testCaseStartedId"], event["testStepId"]))

    started_references = [(event["testCaseStartedId"], event["testStepId"]) for event in step_starts]
    assert len(finished_references) == len(set(finished_references)), finished_references
    assert set(finished_references) == set(started_references), (started_references, finished_references)


def _background_step_statuses(envelopes: list[dict[str, object]], pickle_id: str) -> list[tuple[str, str]]:
    pickle = next(envelope["pickle"] for envelope in envelopes if envelope.get("pickle", {}).get("id") == pickle_id)
    case = next(
        envelope["testCase"] for envelope in envelopes if envelope.get("testCase", {}).get("pickleId") == pickle_id
    )
    case_started = next(
        envelope["testCaseStarted"]
        for envelope in envelopes
        if envelope.get("testCaseStarted", {}).get("testCaseId") == case["id"]
    )
    finishes = {
        envelope["testStepFinished"]["testStepId"]: envelope["testStepFinished"]["testStepResult"]["status"]
        for envelope in envelopes
        if envelope.get("testStepFinished", {}).get("testCaseStartedId") == case_started["id"]
    }
    return [
        (pickle_step["text"], finishes[test_step["id"]])
        for pickle_step, test_step in zip(pickle["steps"], case["testSteps"], strict=True)
        if test_step["id"] in finishes
    ]


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should preserve the two-row feature Background step identities'
    )
)
def consumer_two_row_feature_background_messages(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _background_messages_artifact(relative_path, consumer)
    _assert_background_message_references(envelopes)

    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    starts = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    finishes = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    assert len(pickles) == len(cases) == len(starts) == 2
    assert len(finishes) == 6, finishes
    assert {finish["testStepResult"]["status"] for finish in finishes} == {"PASSED"}
    assert next(envelope["testRunFinished"]["success"] for envelope in envelopes if "testRunFinished" in envelope)

    expected_steps = {
        "I add 2 credits": ["the total starts at 10", "I add 2 credits", "the total is 12"],
        "I add 7 credits": ["the total starts at 10", "I add 7 credits", "the total is 17"],
    }
    actual_steps = {pickle["steps"][1]["text"]: [step["text"] for step in pickle["steps"]] for pickle in pickles}
    assert actual_steps == expected_steps, actual_steps
    assert len({step["id"] for pickle in pickles for step in pickle["steps"]}) == 6, pickles
    for pickle in pickles:
        statuses = _background_step_statuses(envelopes, pickle["id"])
        assert statuses == [(text, "PASSED") for text in expected_steps[pickle["steps"][1]["text"]]], statuses


@then(
    re.compile(
        r'consumer artifacts "(?P<messages_path>[^\"]+)" and "(?P<json_path>[^\"]+)" '
        r"should agree on both successful Background rows"
    )
)
def consumer_background_json_and_messages_agree(messages_path: str, json_path: str, consumer: ConsumerProject) -> None:
    envelopes = _background_messages_artifact(messages_path, consumer)
    _assert_background_message_references(envelopes)
    json_report = json.loads((consumer.path / json_path).read_text(encoding="utf-8"))
    assert len(json_report) == 1, json_report
    elements = json_report[0]["elements"]
    assert len(elements) == 2, elements

    json_rows: dict[str, list[tuple[str, str]]] = {}
    for element in elements:
        steps = [(step["name"], step["result"]["status"].lower()) for step in element["steps"]]
        action = next(name for name, _ in steps if name.startswith("I add "))
        assert action not in json_rows, json_rows
        json_rows[action] = steps

    messages_rows: dict[str, list[tuple[str, str]]] = {}
    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    for pickle in pickles:
        action = next(step["text"] for step in pickle["steps"] if step["text"].startswith("I add "))
        assert action not in messages_rows, messages_rows
        messages_rows[action] = [
            (name, status.lower()) for name, status in _background_step_statuses(envelopes, pickle["id"])
        ]
    assert messages_rows == json_rows, (messages_rows, json_rows)
    assert set(json_rows) == {"I add 2 credits", "I add 7 credits"}, json_rows
    assert all(status == "passed" for row in json_rows.values() for _, status in row), json_rows


@then(re.compile(r'consumer artifact "(?P<relative_path>[^\"]+)" should report both Background rows as passed'))
def consumer_background_json_rows_passed(relative_path: str, consumer: ConsumerProject) -> None:
    report = json.loads((consumer.path / relative_path).read_text(encoding="utf-8"))
    assert len(report) == 1, report
    elements = report[0]["elements"]
    assert len(elements) == 2, elements
    rows: dict[str, list[tuple[str, str]]] = {}
    for element in elements:
        steps = [(step["name"], step["result"]["status"].lower()) for step in element["steps"]]
        action = next(name for name, _ in steps if name.startswith("I add "))
        rows[action] = steps
    assert set(rows) == {"I add 2 credits", "I add 7 credits"}, rows
    assert rows == {
        "I add 2 credits": [
            ("the total starts at 10", "passed"),
            ("I add 2 credits", "passed"),
            ("the total is 12", "passed"),
        ],
        "I add 7 credits": [
            ("the total starts at 10", "passed"),
            ("I add 7 credits", "passed"),
            ("the total is 17", "passed"),
        ],
    }


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should preserve repeated feature and Rule Background step identities'
    )
)
def consumer_rule_background_message_identities(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _background_messages_artifact(relative_path, consumer)
    _assert_background_message_references(envelopes)
    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    finishes = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    assert len(pickles) == 2, pickles
    assert len(finishes) == 10, finishes
    assert {finish["testStepResult"]["status"] for finish in finishes} == {"PASSED"}

    rows = {}
    duplicate_ids = []
    for pickle in pickles:
        texts = [step["text"] for step in pickle["steps"]]
        action = next(text for text in texts if text.startswith("I add "))
        assert texts.count("the total starts at 10") == 3, texts
        assert len({step["id"] for step in pickle["steps"]}) == len(pickle["steps"]), pickle
        duplicate_ids.extend(step["id"] for step in pickle["steps"] if step["text"] == "the total starts at 10")
        statuses = _background_step_statuses(envelopes, pickle["id"])
        assert [status for _, status in statuses] == ["PASSED"] * 5, statuses
        rows[action] = [text for text, _ in statuses]
    assert set(rows) == {"I add 2 credits", "I add 7 credits"}, rows
    assert all(texts.count("the total starts at 10") == 3 for texts in rows.values()), rows
    assert len(duplicate_ids) == len(set(duplicate_ids)) == 6, duplicate_ids


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should close the Background lifecycle with statuses '
        r'"(?P<statuses>[a-z, ]+)" and an? (?P<run_result>successful|unsuccessful) run'
    )
)
def consumer_background_lifecycle_messages(
    relative_path: str, statuses: str, run_result: str, consumer: ConsumerProject
) -> None:
    envelopes = _background_messages_artifact(relative_path, consumer)
    _assert_background_message_references(envelopes)
    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    starts = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    finishes = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    assert len(pickles) == len(cases) == len(starts) == len(run_finished) == 1
    expected_statuses = [status.strip().upper() for status in statuses.split(",")]
    actual_statuses = [finish["testStepResult"]["status"] for finish in finishes]
    assert actual_statuses == expected_statuses, (actual_statuses, expected_statuses)
    assert bool(run_finished[0]["success"]) is (run_result == "successful"), run_finished
    assert len([envelope for envelope in envelopes if "testCaseFinished" in envelope]) == 1


@then(
    re.compile(r'consumer artifact "(?P<relative_path>[^\"]+)" should report the Background failure and skipped steps')
)
def consumer_background_failure_json(relative_path: str, consumer: ConsumerProject) -> None:
    report = json.loads((consumer.path / relative_path).read_text(encoding="utf-8"))
    assert len(report) == 1, report
    elements = report[0]["elements"]
    assert len(elements) == 1, elements
    statuses = [step["result"]["status"].lower() for step in elements[0]["steps"]]
    assert statuses == ["failed", "skipped", "skipped", "skipped"], statuses
    assert "passed" not in statuses, statuses


def _consumer_schema_directory(consumer: ConsumerProject, relative_path: str) -> Path:
    destination = Path(relative_path)
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("schema sync paths must stay inside the consumer project")
    return consumer.path / destination


def _schema_directory_snapshot(directory: Path) -> dict[str, object]:
    if not directory.exists():
        return {"exists": False, "entries": []}

    entries: list[dict[str, str]] = []
    for path in sorted(directory.rglob("*"), key=lambda item: item.relative_to(directory).as_posix()):
        relative_path = path.relative_to(directory).as_posix()
        if path.is_dir():
            entries.append({"path": relative_path, "kind": "directory"})
        elif path.is_file():
            entries.append(
                {
                    "path": relative_path,
                    "kind": "file",
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return {"exists": True, "entries": entries}


@when(re.compile(r'I snapshot consumer directory "(?P<relative_path>[^\"]+)" for schema sync'))
def snapshot_consumer_schema_directory(relative_path: str, consumer: ConsumerProject) -> None:
    directory = _consumer_schema_directory(consumer, relative_path)
    snapshot_path = consumer.path / ".schema-sync-snapshot.json"
    snapshot_path.write_text(
        json.dumps(_schema_directory_snapshot(directory), sort_keys=True),
        encoding="utf-8",
    )


@then(re.compile(r'consumer directory "(?P<relative_path>[^\"]+)" should match its schema sync snapshot'))
def consumer_schema_directory_matches_snapshot(relative_path: str, consumer: ConsumerProject) -> None:
    directory = _consumer_schema_directory(consumer, relative_path)
    snapshot_path = consumer.path / ".schema-sync-snapshot.json"
    expected = json.loads(snapshot_path.read_text(encoding="utf-8"))
    actual = _schema_directory_snapshot(directory)
    assert actual == expected, f"schema directory changed during a read-only or failed sync: {actual!r} != {expected!r}"


@given("a local schema sync fixture has sorted changed, missing, and extra entries")
def consumer_with_schema_sync_drift_fixture(consumer: ConsumerProject) -> None:
    source = consumer.path / "schema-fixture" / "jsonschema"
    source.mkdir(parents=True, exist_ok=True)
    envelope = {"$id": "Envelope.json", "type": "object"}
    (source / "Envelope.json").write_text(json.dumps(envelope, sort_keys=True), encoding="utf-8")
    for name in ("zeta", "gamma", "alpha", "beta"):
        schema = {"$id": f"{name}.json", "type": "object", "source": name}
        (source / f"{name}.json").write_text(json.dumps(schema, sort_keys=True), encoding="utf-8")

    destination = consumer.path / "schema-output"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "Envelope.schema.json").write_text(json.dumps(envelope, sort_keys=True), encoding="utf-8")
    for name in ("zeta", "alpha", "epsilon", "delta"):
        existing = {"$id": f"{name}.json", "type": "object", "source": "stale"}
        (destination / f"{name}.schema.json").write_text(json.dumps(existing, sort_keys=True), encoding="utf-8")


@then("schema sync output should name cuke-messages 0.1.0 and upstream tag v24.0.1")
def consumer_schema_sync_output_has_pinned_versions(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a schema sync command has not run"
    output = f"{result.stdout}\n{result.stderr}"
    assert "cuke-messages==0.1.0" in output, output
    assert "v24.0.1" in output, output


@then(re.compile(r'schema output "(?P<destination>[^\"]+)" should match source tree "(?P<source>[^\"]+)"'))
def consumer_schema_sync_output_matches_fixture(destination: str, source: str, consumer: ConsumerProject) -> None:
    source_root = _consumer_schema_directory(consumer, source) / "jsonschema"
    destination_root = _consumer_schema_directory(consumer, destination)
    expected: dict[str, object] = {}
    for path in source_root.glob("*.json"):
        if path.is_file():
            expected[f"{path.stem}.schema.json"] = json.loads(path.read_text(encoding="utf-8"))

    assert expected, f"the fixture has no JSON schemas: {source_root}"
    assert destination_root.is_dir(), f"schema sync did not create its output directory: {destination_root}"
    actual_paths = sorted(path.name for path in destination_root.iterdir())
    assert actual_paths == sorted(expected), actual_paths
    for name, expected_schema in expected.items():
        actual_schema = json.loads((destination_root / name).read_text(encoding="utf-8"))
        assert actual_schema == expected_schema, (name, actual_schema, expected_schema)


@then("schema sync output should list changed, missing, and extra files in sorted groups")
def consumer_schema_sync_output_lists_sorted_drift(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a schema sync check has not run"
    output = f"{result.stdout}\n{result.stderr}"
    lines = output.splitlines()
    expected = {
        "changed": ["alpha.schema.json", "zeta.schema.json"],
        "missing": ["beta.schema.json", "gamma.schema.json"],
        "extra": ["delta.schema.json", "epsilon.schema.json"],
    }
    groups: dict[str, list[str]] = {name: [] for name in expected}
    current_group: str | None = None
    heading_positions: list[int] = []
    schema_name = re.compile(r"[a-z0-9._-]+\.schema\.json", re.IGNORECASE)
    for line_number, line in enumerate(lines):
        heading = re.match(r"\s*(changed|missing|extra)\s*:\s*(.*)$", line, re.IGNORECASE)
        if heading is not None:
            current_group = heading.group(1).lower()
            heading_positions.append(line_number)
            groups[current_group].extend(name.lower() for name in schema_name.findall(heading.group(2)))
        elif current_group is not None:
            groups[current_group].extend(name.lower() for name in schema_name.findall(line))

    assert list(groups.values()) == list(expected.values()), (groups, expected, output)
    assert heading_positions == sorted(heading_positions) and len(heading_positions) == 3, (heading_positions, output)


@then(
    re.compile(
        r'consumer artifact "(?P<artifact>[^"]+)" should contain exactly one valid ParseError for feature '
        r'"(?P<feature>[^"]+)" at line (?P<line>\d+) column (?P<column>\d+)'
    )
)
def consumer_artifact_has_one_valid_parse_error(
    artifact: str,
    feature: str,
    line: str,
    column: str,
    consumer: ConsumerProject,
) -> None:
    from messages import Envelope

    artifact_path = Path(artifact)
    feature_path = Path(feature)
    if artifact_path.is_absolute() or ".." in artifact_path.parts:
        raise ValueError("consumer artifact paths must stay inside the consumer project")
    if feature_path.is_absolute() or ".." in feature_path.parts:
        raise ValueError("consumer feature paths must stay inside the consumer project")

    artifact_file = consumer.path / artifact_path
    raw_lines = artifact_file.read_text(encoding="utf-8").splitlines()
    assert raw_lines, f"consumer artifact {artifact!r} is empty"
    envelopes = [_validate_messages_envelope_compatibly(json.loads(raw_line)) for raw_line in raw_lines]
    parse_errors = [envelope.parse_error for envelope in envelopes if envelope.parse_error is not None]
    assert len(parse_errors) == 1, f"expected one ParseError envelope, got {len(parse_errors)}: {raw_lines!r}"
    assert all(envelope.pickle is None and envelope.test_case is None for envelope in envelopes), (
        "a parse failure must not fabricate a successful Pickle or TestCase"
    )

    parse_error = parse_errors[0]
    assert parse_error.message.strip(), "ParseError must explain the syntax failure"
    source = parse_error.source
    assert source is not None, "ParseError must include a SourceReference"
    assert source.uri, "ParseError source URI must be non-empty"
    expected_uri = f"file:{feature_path.name}"
    assert source.uri == expected_uri, f"expected ParseError source URI {expected_uri!r}, got {source.uri!r}"

    location = source.location
    assert location is not None, "ParseError must include a SourceReference location"
    assert location.line == int(line), f"expected parse error on line {line}, got {location.line}"
    assert location.column == int(column), f"expected one-based column {column}, got {location.column}"


@then("both message-reporting pytest sessions should fail with 3 BDD scenarios")
def both_consumer_message_sessions_fail_with_three_scenarios(consumer: ConsumerProject) -> None:
    results = consumer.feature_source_session_results
    assert results is not None and len(results) == 2, "both independent pytest sessions must have run"
    for session, result in enumerate(results, start=1):
        output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode != 0, f"message-reporting pytest session {session} unexpectedly passed:\n{output}"
        assert "0 passed BDD scenarios, 3 failed, 0 skipped" in output, output


def _consumer_message_envelopes(relative_path: str, consumer: ConsumerProject) -> list[Envelope]:
    artifact_path = Path(relative_path)
    if artifact_path.is_absolute() or ".." in artifact_path.parts:
        raise ValueError("consumer artifact paths must stay inside the consumer project")
    raw_lines = (consumer.path / artifact_path).read_text(encoding="utf-8").splitlines()
    assert raw_lines, f"consumer artifact {relative_path!r} is empty"
    return [_validate_messages_envelope_compatibly(json.loads(raw_line)) for raw_line in raw_lines]


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should contain (?P<count>\d+) schema-valid '
        r'UndefinedParameterType messages with expression "(?P<expression>[^"]+)" and name "(?P<name>[^"]+)"'
    )
)
def consumer_artifact_has_undefined_parameter_type_messages(
    relative_path: str,
    count: str,
    expression: str,
    name: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _consumer_message_envelopes(relative_path, consumer)
    messages = [envelope.undefined_parameter_type for envelope in envelopes if envelope.undefined_parameter_type]
    assert len(messages) == int(count), f"expected {count} UndefinedParameterType messages, got {len(messages)}"
    assert all(message.expression == expression for message in messages), messages
    assert all(message.name == name for message in messages), messages


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should report (?P<count>\d+) UNDEFINED steps, '
        r'(?P<scenario_count>\d+) failed scenarios, and an unsuccessful run'
    )
)
def consumer_artifact_has_undefined_steps_and_failed_scenarios(
    relative_path: str,
    count: str,
    scenario_count: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _consumer_message_envelopes(relative_path, consumer)
    steps = [envelope.test_step_finished for envelope in envelopes if envelope.test_step_finished is not None]
    assert len(steps) == int(count), f"expected {count} scenario step results, got {len(steps)}"
    statuses = [step.test_step_result.status.value for step in steps]
    assert all(status == "UNDEFINED" for status in statuses), statuses
    finished_cases = [envelope.test_case_finished for envelope in envelopes if envelope.test_case_finished is not None]
    assert len(finished_cases) == int(scenario_count), (
        f"expected {scenario_count} finished scenarios, got {len(finished_cases)}"
    )
    run_finishes = [envelope.test_run_finished for envelope in envelopes if envelope.test_run_finished is not None]
    assert len(run_finishes) == 1, f"expected one TestRunFinished event, got {len(run_finishes)}"
    assert run_finishes[0].success is False, run_finishes[0]


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should report one FAILED converter step and '
        r'two UNDEFINED unmatched steps'
    )
)
def consumer_artifact_reports_negative_control_step_statuses(
    relative_path: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _consumer_message_envelopes(relative_path, consumer)
    steps = [envelope.test_step_finished for envelope in envelopes if envelope.test_step_finished is not None]
    statuses = [step.test_step_result.status.value for step in steps]
    assert len(statuses) == 3, f"expected three negative-control step results, got {statuses}"
    assert statuses.count("FAILED") == 1, statuses
    assert statuses.count("UNDEFINED") == 2, statuses


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should contain (?P<chain_count>\d+) exception chains '
        r'and exactly (?P<cause_count>\d+) with UndefinedParameterTypeError'
    )
)
def consumer_artifact_has_expected_undefined_parameter_type_causes(
    relative_path: str,
    chain_count: str,
    cause_count: str,
    consumer: ConsumerProject,
) -> None:
    artifact_path = Path(relative_path)
    if artifact_path.is_absolute() or ".." in artifact_path.parts:
        raise ValueError("consumer artifact paths must stay inside the consumer project")
    raw_lines = (consumer.path / artifact_path).read_text(encoding="utf-8").splitlines()
    chains = [json.loads(raw_line) for raw_line in raw_lines]
    assert len(chains) == int(chain_count), f"expected {chain_count} captured exception chains, got {len(chains)}"
    cause_chains = [
        chain for chain in chains if any(entry.get("type") == "UndefinedParameterTypeError" for entry in chain)
    ]
    assert len(cause_chains) == int(cause_count), (
        f"expected exactly {cause_count} chains containing UndefinedParameterTypeError, got {len(cause_chains)}: "
        f"{chains!r}"
    )


@then(re.compile(r'consumer artifact "(?P<relative_path>[^"]+)" should contain no UndefinedParameterType messages'))
def consumer_artifact_has_no_undefined_parameter_type_messages(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _consumer_message_envelopes(relative_path, consumer)
    assert not any(envelope.undefined_parameter_type is not None for envelope in envelopes)


@then(
    re.compile(
        r'consumer runtime observation "(?P<observation_path>[^"]+)" should link to scenario '
        r'"(?P<scenario_name>[^"]+)" in Messages "(?P<messages_path>[^"]+)" and report "(?P<report_path>[^"]+)"'
    )
)
def consumer_runtime_observation_links_to_report_and_messages(
    observation_path: str,
    scenario_name: str,
    messages_path: str,
    report_path: str,
    consumer: ConsumerProject,
) -> None:
    observation_file = Path(observation_path)
    if observation_file.is_absolute() or ".." in observation_file.parts:
        raise ValueError("consumer runtime observation paths must stay inside the consumer project")
    observation = json.loads((consumer.path / observation_file).read_text(encoding="utf-8"))
    assert observation.get("scenario_name") == scenario_name, observation
    assert observation.get("hook_context_identity") == observation.get("step_context_identity"), observation
    assert observation.get("hook_scenario_run_identity") == observation.get("step_scenario_run_identity"), observation
    scenario_run_id = observation.get("scenario_run_id")
    assert isinstance(scenario_run_id, str) and scenario_run_id, observation
    test_case_started_id = observation.get("test_case_started_id")
    assert isinstance(test_case_started_id, str) and test_case_started_id, observation

    envelopes = _consumer_message_envelopes(messages_path, consumer)
    pickles = [envelope.pickle for envelope in envelopes if envelope.pickle is not None]
    scenario_pickles = [pickle for pickle in pickles if pickle.name == scenario_name]
    assert len(scenario_pickles) == 1, scenario_pickles
    pickle = scenario_pickles[0]
    test_cases = [envelope.test_case for envelope in envelopes if envelope.test_case is not None]
    scenario_cases = [case for case in test_cases if case.pickle_id == pickle.id]
    assert len(scenario_cases) == 1, scenario_cases
    test_case = scenario_cases[0]

    started = [
        envelope.test_case_started
        for envelope in envelopes
        if envelope.test_case_started is not None and envelope.test_case_started.test_case_id == test_case.id
    ]
    assert len(started) == 1, started
    assert started[0].id == test_case_started_id, (started[0], observation)
    finished = [
        envelope.test_case_finished
        for envelope in envelopes
        if envelope.test_case_finished is not None
        and envelope.test_case_finished.test_case_started_id == test_case_started_id
    ]
    assert len(finished) == 1, finished

    report_file = Path(report_path)
    if report_file.is_absolute() or ".." in report_file.parts:
        raise ValueError("consumer report paths must stay inside the consumer project")
    report = json.loads((consumer.path / report_file).read_text(encoding="utf-8"))
    reported_scenarios = [
        scenario
        for feature in report
        for scenario in feature.get("elements", [])
        if scenario.get("name") == scenario_name
    ]
    assert len(reported_scenarios) == 1, reported_scenarios
    assert all(step.get("result", {}).get("status") == "passed" for step in reported_scenarios[0]["steps"]), (
        reported_scenarios[0]
    )


def _consumer_runtime_snapshot(relative_path: str, consumer: ConsumerProject) -> dict[str, object]:
    artifact_path = Path(relative_path)
    if artifact_path.is_absolute() or ".." in artifact_path.parts:
        raise ValueError("consumer runtime snapshot paths must stay inside the consumer project")
    snapshot = json.loads((consumer.path / artifact_path).read_text(encoding="utf-8"))
    assert isinstance(snapshot, dict), f"consumer runtime snapshot must be an object, got {type(snapshot).__name__}"
    return snapshot


@then(
    re.compile(
        r'consumer runtime snapshot "(?P<relative_path>[^"]+)" should show no active BDD scenario'
    )
)
def consumer_runtime_snapshot_has_no_active_scenario(relative_path: str, consumer: ConsumerProject) -> None:
    snapshot = _consumer_runtime_snapshot(relative_path, consumer)
    assert snapshot == {
        "active_feature_binding": False,
        "active_scenario_run": False,
        "status": "inactive",
    }, snapshot


@then(
    re.compile(
        r'consumer runtime snapshot "(?P<relative_path>[^"]+)" should retain the failed scenario after clearing active refs'
    )
)
def consumer_runtime_snapshot_retains_teardown_failure(relative_path: str, consumer: ConsumerProject) -> None:
    snapshot = _consumer_runtime_snapshot(relative_path, consumer)
    assert snapshot["active_feature_binding"] is False, snapshot
    assert snapshot["active_scenario_run"] is False, snapshot
    assert snapshot["scenario_history_found"] is True, snapshot
    assert snapshot["scenario_status"] == "failed", snapshot
    assert snapshot["active_step"] is False, snapshot
    assert snapshot["exception_type"] == "RuntimeError", snapshot
    assert snapshot["exception_message"] == "runtime teardown failure sentinel", snapshot


@given("the installed consumer exposes tolerant steps and a continuation artifact")
def install_tolerant_step_consumer_definitions(consumer: ConsumerProject) -> None:
    (consumer.path / "conftest.py").write_text(
        '''import os
from pathlib import Path

import pytest
from pytest_cuke import parsers, then, when
from pytest_cuke.steps import tolerant


@tolerant
@when("the first tolerant operation raises an AssertionError")
def first_tolerant_operation():
    raise AssertionError("first tolerant assertion sentinel")


@when("the second tolerant operation raises a RuntimeError")
@tolerant
def second_tolerant_operation():
    raise RuntimeError("second tolerant runtime sentinel")


@tolerant
@when("a tolerant operation requests a skip")
def tolerant_operation_requests_skip():
    pytest.skip("tolerant skip sentinel")


@when("an ordinary operation raises a RuntimeError")
def ordinary_operation_raises():
    raise RuntimeError("ordinary runtime sentinel")


@then(parsers.parse('the continuation records "{labels}"'))
def record_continuation(labels):
    with Path("continuations.log").open("a", encoding="utf-8") as stream:
        stream.write("\\n".join(labels.split(",")) + "\\n")
    worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
    with Path(f"xdist-continuations-{worker}.log").open("a", encoding="utf-8") as stream:
        stream.write("\\n".join(labels.split(",")) + "\\n")


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    for item in items:
        if "A pytest marker overrides the conflicting Gherkin tag" in item.name:
            item.add_marker(pytest.mark.tolerant_status("ignored"))
        if "An invalid pytest marker falls through to the failed Gherkin tag" in item.name:
            item.add_marker(pytest.mark.tolerant_status("unknown"))
''',
        encoding="utf-8",
    )


@then(re.compile(r'consumer continuation artifact should list "(?P<labels>[^"]+)"'))
def consumer_continuation_artifact_has_expected_labels(labels: str, consumer: ConsumerProject) -> None:
    artifact = consumer.path / "continuations.log"
    actual = artifact.read_text(encoding="utf-8").splitlines()
    expected = labels.split(",")
    assert actual == expected, f"expected continuation lines {expected!r}, got {actual!r}"


@then(re.compile(r'consumer xdist continuation artifacts should show "(?P<label>[^"]+)" on (?P<count>\d+) workers'))
def consumer_xdist_tolerant_continuations(label: str, count: str, consumer: ConsumerProject) -> None:
    artifacts = sorted(consumer.path.glob("xdist-continuations-gw*.log"))
    assert len(artifacts) == int(count), f"expected {count} worker artifacts, found {artifacts!r}"
    actual = {artifact.name: artifact.read_text(encoding="utf-8").splitlines() for artifact in artifacts}
    expected = [label]
    assert all(lines == expected for lines in actual.values()), actual


def _tolerant_scenario_step_results(
    relative_path: str,
    scenario_name: str,
    consumer: ConsumerProject,
) -> tuple[list[tuple[str, dict[str, object]]], bool]:
    envelopes = _background_messages_artifact(relative_path, consumer)
    pickles = [
        envelope["pickle"]
        for envelope in envelopes
        if isinstance(envelope.get("pickle"), dict) and envelope["pickle"].get("name") == scenario_name
    ]
    assert len(pickles) == 1, f"expected one pickle for scenario {scenario_name!r}, got {pickles!r}"
    pickle = pickles[0]
    cases = [
        envelope["testCase"]
        for envelope in envelopes
        if isinstance(envelope.get("testCase"), dict) and envelope["testCase"].get("pickleId") == pickle["id"]
    ]
    assert len(cases) == 1, f"expected one test case for scenario {scenario_name!r}, got {cases!r}"
    test_case = cases[0]
    started = [
        envelope["testCaseStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testCaseStarted"), dict)
        and envelope["testCaseStarted"].get("testCaseId") == test_case["id"]
    ]
    assert len(started) == 1, f"expected one scenario attempt for {scenario_name!r}, got {started!r}"
    started_id = started[0]["id"]
    finishes = {
        finish["testStepId"]: finish["testStepResult"]
        for envelope in envelopes
        if isinstance((finish := envelope.get("testStepFinished")), dict)
        and finish.get("testCaseStartedId") == started_id
    }
    steps = [
        (pickle_step["text"], finishes[test_step["id"]])
        for pickle_step, test_step in zip(pickle["steps"], test_case["testSteps"], strict=True)
        if test_step["id"] in finishes
    ]
    run_finishes = [
        envelope["testRunFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunFinished"), dict)
    ]
    assert len(run_finishes) == 1, f"expected one TestRunFinished event, got {run_finishes!r}"
    return steps, bool(run_finishes[0].get("success"))


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should keep tolerant step statuses '
        r'"(?P<statuses>[A-Z, ]+)" and exception messages "(?P<messages>[^"]+)" for scenario '
        r'"(?P<scenario_name>[^"]+)" and TestRunFinished success "(?P<expected_run_success>true|false)"'
    )
)
def consumer_tolerant_step_messages(
    relative_path: str,
    statuses: str,
    messages: str,
    scenario_name: str,
    expected_run_success: str,
    consumer: ConsumerProject,
) -> None:
    steps, run_success = _tolerant_scenario_step_results(relative_path, scenario_name, consumer)
    expected_statuses = [status.strip() for status in statuses.split(",")]
    actual_statuses = [result.get("status") for _, result in steps]
    assert actual_statuses == expected_statuses, (actual_statuses, expected_statuses, steps)
    expected_messages = messages.split(",")
    failure_exceptions = []
    for _, result in steps:
        exception = result.get("exception")
        if result.get("status") == "FAILED" and isinstance(exception, dict):
            failure_exceptions.append(exception.get("message"))
    assert failure_exceptions == expected_messages, (failure_exceptions, expected_messages, steps)
    assert run_success is (expected_run_success == "true"), (run_success, expected_run_success)


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should report scenario "(?P<scenario_name>[^"]+)" '
        r'with step statuses "(?P<statuses>[a-z, ]+)" and error messages "(?P<messages>[^"]+)"'
    )
)
def consumer_tolerant_cucumber_json(
    relative_path: str,
    scenario_name: str,
    statuses: str,
    messages: str,
    consumer: ConsumerProject,
) -> None:
    report = json.loads((consumer.path / relative_path).read_text(encoding="utf-8"))
    scenarios = [
        scenario
        for feature in report
        for scenario in feature.get("elements", [])
        if scenario.get("name") == scenario_name
    ]
    assert len(scenarios) == 1, scenarios
    steps = scenarios[0]["steps"]
    actual_statuses = [step["result"]["status"] for step in steps]
    assert actual_statuses == [status.strip() for status in statuses.split(",")], (actual_statuses, steps)
    actual_messages = [
        step["result"]["error_message"]
        for step in steps
        if step["result"]["status"] == "failed" and step["result"].get("error_message")
    ]
    assert actual_messages == messages.split(","), (actual_messages, steps)


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should retain skip and undefined statuses under the ignored policy'
    )
)
def consumer_tolerant_skip_and_undefined_messages(relative_path: str, consumer: ConsumerProject) -> None:
    skip_steps, _ = _tolerant_scenario_step_results(
        relative_path,
        "A tolerant skip remains skipped under ignored policy",
        consumer,
    )
    undefined_steps, run_success = _tolerant_scenario_step_results(
        relative_path,
        "An undefined operation remains undefined under ignored policy",
        consumer,
    )
    assert [result.get("status") for _, result in skip_steps] == ["SKIPPED", "SKIPPED"], skip_steps
    assert [result.get("status") for _, result in undefined_steps] == ["UNDEFINED", "SKIPPED"], undefined_steps
    assert all(result.get("status") != "PASSED" for _, result in (*skip_steps, *undefined_steps))
    assert run_success is False
