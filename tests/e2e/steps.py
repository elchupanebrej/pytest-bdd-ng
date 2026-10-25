from __future__ import annotations

import errno
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
import tomllib
import venv
import zipfile
from collections import Counter, defaultdict
from contextlib import suppress
from dataclasses import dataclass
from functools import reduce
from operator import attrgetter, itemgetter
from pathlib import Path, PurePosixPath
from textwrap import dedent, indent
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlsplit

import pytest
from packaging.version import Version
from pytest import fixture

try:
    import pytest_httpserver

    HTTPServer = pytest_httpserver.HTTPServer
except ImportError:
    pytest_httpserver = None
    HTTPServer = None

    @fixture
    def httpserver():
        pytest.fail(
            "HTTP BDD acceptance requires pytest-httpserver. Install pytest-cuke[test] "
            "or run `python -m pip install -e '.[test]'` from the checkout.",
            pytrace=False,
        )


from pytest_cuke import given, step, then, when
from pytest_cuke.compatibility.pytest import assert_outcomes
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.model.message_types import Envelope, message_from_dict
from pytest_cuke.model.message_validation import validate_envelope
from pytest_cuke.utils import compose
from tests.support.testing_utils import data_table_to_dicts, mask_npm_package_from_node_resolution


def _consumer_binary_dir(environment_path: Path) -> Path:
    return environment_path / ("Scripts" if os.name == "nt" else "bin")


def _consumer_executable(binary_dir: Path, name: str) -> Path:
    return binary_dir / (f"{name}.exe" if os.name == "nt" else name)


def _consumer_path(binary_dir: Path, *, include_node: bool = False) -> str:
    path_entries = [str(binary_dir)]
    if include_node:
        node = shutil.which("node")
        if node is not None:
            path_entries.append(str(Path(node).parent))
            npm = shutil.which("npm")
            if npm is not None:
                path_entries.append(str(Path(npm).parent))
    path_entries.extend(os.defpath.split(os.pathsep))
    return os.pathsep.join(dict.fromkeys(path_entries))


def _consumer_environment() -> dict[str, str]:
    """Copy the host environment without carrying outer tox or xdist state."""
    environment = os.environ.copy()
    for name in (
        "TOX_ENV_DIR",
        "PYTEST_XDIST_WORKER",
        "PYTEST_XDIST_WORKER_COUNT",
        "PYTEST_XDIST_TESTRUNUID",
    ):
        environment.pop(name, None)
    return environment


def _split_consumer_arguments(arguments: str) -> list[str]:
    """Split BDD CLI arguments without treating Windows path separators as escapes."""
    lexer = shlex.shlex(arguments, posix=True)
    lexer.whitespace_split = True
    if os.name == "nt":
        lexer.escape = ""
    return list(lexer)


def _normalized_path_text(value: str) -> str:
    """Normalize host-specific separators before comparing diagnostic paths."""
    return value.replace("\\", "/")


_DEBUG_MCP_PYPY_WINDOWS_SKIP_REASON = (
    "Debug MCP is unsupported for PyPy on Windows: MCP SDK v1.x requires pywin32>=310 on Windows "
    "for Python <3.14, and published pywin32 wheels target CPython only."
    "Debug MCP is unsupported for PyPy on Windows because MCP SDK v1.x requires pywin32>=310 for Python <3.14, "
    "and published pywin32 wheels target CPython only. PyPy is excluded from the core runtime inventory."
)


def _debug_mcp_capability_skip_reason(implementation: str, sys_platform: str) -> str | None:
    """Return the upstream-compatibility exclusion for PyPy on Windows."""
    if implementation.casefold() == "pypy" and sys_platform.casefold() == "win32":
        return _DEBUG_MCP_PYPY_WINDOWS_SKIP_REASON
    return None


def _require_debug_mcp_capability(implementation: str, sys_platform: str) -> None:
    reason = _debug_mcp_capability_skip_reason(implementation, sys_platform)
    if reason is not None:
        pytest.skip(reason)


def _consumer_python_implementation_and_platform(consumer: ConsumerProject) -> tuple[str, str]:
    probe = (
        "import json, platform, sys; "
        "print(json.dumps({'implementation': platform.python_implementation(), 'platform': sys.platform}))"
    )
    result = subprocess.run(
        [str(consumer.python), "-c", probe],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, (
        "could not identify the installed consumer runtime before installing Debug MCP: "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    try:
        runtime = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(f"invalid installed consumer runtime probe: {result.stdout!r}") from error
    assert isinstance(runtime, dict), runtime
    implementation = runtime.get("implementation")
    sys_platform = runtime.get("platform")
    assert isinstance(implementation, str) and implementation, runtime
    assert isinstance(sys_platform, str) and sys_platform, runtime
    return implementation, sys_platform


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
    socket_gateway_addresses: list[str] | None = None
    socket_gateway_processes: list[Any] | None = None
    socket_gateway_remote_roots: list[Path] | None = None
    socket_gateway_log_paths: list[Path] | None = None
    socket_gateway_filesystem_isolated: bool = False


@fixture(scope="session")
def _pytest_cuke_cucumber_json_runtime(tmp_path_factory):
    """Install the pinned Node formatter runtime above all isolated consumers."""
    node = shutil.which("node")
    npm = shutil.which("npm")
    if node is None or npm is None:
        return None

    runtime_root = tmp_path_factory.getbasetemp()
    package_json = {
        "name": "pytest-cuke-e2e-consumer-runtime",
        "private": True,
        "type": "module",
        "dependencies": {"@cucumber/cucumber": "13.3.0"},
    }
    (runtime_root / "package.json").write_text(json.dumps(package_json, indent=2) + "\n", encoding="utf-8")

    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join(
        dict.fromkeys((str(Path(node).parent), str(Path(npm).parent), *os.defpath.split(os.pathsep)))
    )
    environment.pop("NODE_PATH", None)
    install = subprocess.run(
        [npm, "install", "--no-audit", "--no-fund"],
        cwd=runtime_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    assert install.returncode == 0, (
        f"could not install pinned @cucumber/cucumber@13.3.0 for installed consumers:\n"
        f"{install.stdout}\n{install.stderr}"
    )
    metadata = runtime_root / "node_modules" / "@cucumber" / "cucumber" / "package.json"
    installed_version = json.loads(metadata.read_text(encoding="utf-8")).get("version")
    assert installed_version == "13.3.0", installed_version
    return runtime_root


def _validate_messages_envelope_compatibly(payload: Any) -> Envelope:
    """Convert and validate one Cucumber Messages wire envelope."""
    assert isinstance(payload, dict), f"Cucumber Messages envelope must be an object, got {type(payload).__name__}"
    envelope = message_from_dict(payload)
    diagnostics = validate_envelope(envelope)
    assert not diagnostics, f"invalid Cucumber Messages envelope: {diagnostics!r}; payload={payload!r}"
    return envelope


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
    assert sys.version_info >= (3, 11), "the installed-consumer contract requires Python 3.11 or newer"
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
    assert sys.version_info >= (3, 11), "the installed-consumer contract requires Python 3.11 or newer"
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
def install_pytest_cuke_consumer(
    distribution,
    _pytest_cuke_environments,
    _pytest_cuke_artifacts,
    _pytest_cuke_cucumber_json_runtime,
    tmp_path_factory,
):
    project_path = tmp_path_factory.mktemp("pytest-cuke-consumer")
    (project_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ncuke_features_dir = 'features'\ncuke_autoload = true\n",
        encoding="utf-8",
    )
    environment_path = _pytest_cuke_environments[distribution]
    binary_dir = _consumer_binary_dir(environment_path)
    consumer_home = project_path / ".home"
    consumer_home.mkdir()
    environment = _consumer_environment()
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
            "PATH": _consumer_path(binary_dir, include_node=True),
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


@given("the consumer installs pytest-cuke with its Allure extra in an isolated environment")
def install_pytest_cuke_allure_extra_in_isolated_environment(consumer: ConsumerProject) -> None:
    """Install the Allure extra without changing shared base consumer environments."""
    _install_pytest_cuke_extra_in_isolated_environment(consumer, "allure")


@given("the consumer installs pytest-cuke with its StructBDD extra in an isolated environment")
def install_pytest_cuke_struct_bdd_extra_in_isolated_environment(consumer: ConsumerProject) -> None:
    """Install the complete structured BDD capability without changing shared base environments."""
    _install_pytest_cuke_extra_in_isolated_environment(consumer, "struct-bdd")


@given("the consumer installs pytest-cuke with its Cucumber JSON extra in an isolated environment")
def install_pytest_cuke_cucumber_json_extra_in_isolated_environment(consumer: ConsumerProject) -> None:
    """Install native Cucumber JSON support without changing shared base consumer environments."""
    _install_pytest_cuke_extra_in_isolated_environment(consumer, "cucumber-json")


def _install_pytest_cuke_extra_in_isolated_environment(consumer: ConsumerProject, extra: str) -> None:
    uv_executable = shutil.which("uv")
    assert uv_executable, f"the {extra} consumer contract requires uv to create an isolated environment"
    environment_path = consumer.path / f".venv-{extra}"
    create_environment = subprocess.run(
        [uv_executable, "venv", "--python", sys.executable, str(environment_path)],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert create_environment.returncode == 0, (
        f"could not create {extra} consumer environment:\n{create_environment.stdout}\n{create_environment.stderr}"
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
            f"pytest-cuke[{extra}] @ {consumer.artifact.resolve().as_uri()}",
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, (
        f"could not install pytest-cuke with its {extra} extra:\n{install.stdout}\n{install.stderr}"
    )
    consumer.python = python_path
    consumer.pytest = _consumer_executable(binary_dir, "pytest")
    consumer.cuke = _consumer_executable(binary_dir, "cuke")
    consumer.env["PATH"] = _consumer_path(binary_dir, include_node=False)


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
    environment = _consumer_environment()
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
    assert sys.version_info >= (3, 11), "the installed-consumer contract requires Python 3.11 or newer"
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
    environment = _consumer_environment()
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


def _repository_file_path(relative_path: str) -> Path:
    source = Path(relative_path)
    if (
        source.is_absolute()
        or ".." in source.parts
        or "\\" in relative_path
        or re.match(r"^[A-Za-z]:", relative_path) is not None
    ):
        raise ValueError("repository source paths must stay inside the product checkout")
    repository_root = Path(__file__).resolve().parents[2]
    source_path = (repository_root / source).resolve()
    try:
        source_path.relative_to(repository_root)
    except ValueError as exc:
        raise ValueError("repository source paths must stay inside the product checkout") from exc
    if not source_path.is_file():
        raise ValueError(f"repository source file does not exist: {relative_path}")
    return source_path


@given(
    re.compile(
        r'repository file "(?P<source_path>[^\"]+)" is copied to consumer file "(?P<destination_path>[^\"]+)"'
    )
)
def copy_repository_file_to_consumer(source_path: str, destination_path: str, consumer: ConsumerProject) -> None:
    source = _repository_file_path(source_path)
    if "\\" in destination_path or re.match(r"^[A-Za-z]:", destination_path) is not None:
        raise ValueError("consumer artifact paths must stay inside the consumer project")
    destination = _consumer_artifact_path(destination_path, consumer)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination = _consumer_artifact_path(destination_path, consumer)
    shutil.copy2(source, destination)


def _consumer_allure_attachment_file(result_directory: Path, reference: dict[str, Any]) -> Path:
    source = reference.get("source")
    assert isinstance(source, str) and source, reference
    relative_source = PurePosixPath(source)
    assert (
        not relative_source.is_absolute()
        and ".." not in relative_source.parts
        and "\\" not in source
        and relative_source.as_posix() == source
        and re.match(r"^[A-Za-z]:", source) is None
    ), reference
    attachment_path = result_directory.joinpath(*relative_source.parts).resolve()
    try:
        attachment_path.relative_to(result_directory.resolve())
    except ValueError as exc:
        raise AssertionError(f"attachment source escapes the Allure result directory: {source!r}") from exc
    assert attachment_path.is_file(), f"Allure attachment file is missing: {source!r}"
    return attachment_path


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


@given(re.compile(r'consumer temporary directory "(?P<relative_path>[^\"]+)" is configured as TMPDIR'))
def configure_consumer_tmpdir(relative_path: str, consumer: ConsumerProject) -> None:
    temporary_directory = _consumer_artifact_path(relative_path, consumer)
    temporary_directory.mkdir(parents=True, exist_ok=True)
    assert not any(temporary_directory.iterdir()), f"consumer TMPDIR must start empty: {temporary_directory}"
    temporary_path = str(temporary_directory)
    consumer.env.update({"TMPDIR": temporary_path, "TMP": temporary_path, "TEMP": temporary_path})


@then(
    re.compile(
        r'consumer temporary directory "(?P<relative_path>[^\"]+)" should have no worker-owned Messages stream files'
    )
)
def consumer_tmpdir_has_no_worker_messages_files(relative_path: str, consumer: ConsumerProject) -> None:
    temporary_directory = _consumer_artifact_path(relative_path, consumer)
    assert temporary_directory.is_dir(), f"consumer TMPDIR is missing: {temporary_directory}"
    worker_streams = sorted(
        path for path in temporary_directory.glob("tmp*") if path.is_file() and path.suffix != ".lock"
    )
    assert not worker_streams, f"worker-owned temporary Messages streams remain: {worker_streams!r}"


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
    arguments = arguments.replace(
        "{mcp_nonlocal_host}", str(getattr(consumer, "_mcp_nonlocal_host", "{mcp_nonlocal_host}"))
    )
    result = subprocess.run(
        [str(consumer.pytest), *_split_consumer_arguments(arguments)],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
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
        *_split_consumer_arguments(arguments.replace("{consumer_path}", str(consumer.path))),
    ]
    result = subprocess.run(
        command,
        cwd=cwd,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    consumer.pytest_result = result
    return result


@when("I check shared Cucumber runtime resolution from a sibling consumer directory")
def check_shared_cucumber_runtime_resolution_from_sibling(consumer: ConsumerProject) -> None:
    node = shutil.which("node", path=consumer.env.get("PATH"))
    if node is None:
        import pytest

        pytest.skip("the shared Cucumber runtime resolution contract requires Node.js")

    sibling_path = consumer.path.parent / "pytest-cuke-cucumber-runtime-sibling"
    sibling_path.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            node,
            "--input-type=module",
            "-e",
            "console.log(import.meta.resolve(process.argv[1]))",
            "@cucumber/cucumber",
        ],
        cwd=sibling_path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    consumer._cucumber_runtime_sibling_result = result
    consumer._cucumber_runtime_sibling_path = sibling_path


@then("the sibling consumer should resolve the shared Cucumber runtime from the temporary root")
def sibling_consumer_resolves_shared_cucumber_runtime(consumer: ConsumerProject) -> None:
    result = getattr(consumer, "_cucumber_runtime_sibling_result", None)
    assert isinstance(result, subprocess.CompletedProcess), "the sibling consumer resolution check has not run"
    assert result.returncode == 0, f"Node could not resolve @cucumber/cucumber from a sibling consumer:\n{result.stderr}"
    resolved_url = unquote(result.stdout.strip()).replace("\\", "/")
    expected_package_root = str((consumer.path.parent / "node_modules" / "@cucumber" / "cucumber").resolve())
    expected_package_root = expected_package_root.replace("\\", "/")
    assert expected_package_root in resolved_url, (expected_package_root, resolved_url)


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
            [str(consumer.pytest), *_split_consumer_arguments(arguments)],
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
            *_split_consumer_arguments(arguments.replace("{local_http_base_url}", local_feature_http_server.base_url)),
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
        *_split_consumer_arguments(arguments.replace("{local_http_base_url}", http_base_url)),
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
    root = getattr(request.config, "rootpath", getattr(request.config, "rootdir", Path.cwd()))
    source_dir = str(Path(root) / "src")
    test_root = Path(str(testdir.tmpdir))
    cli_args = _split_consumer_arguments(arguments)
    project_root_argument = next(
        (
            argument.partition("=")[2]
            for argument in cli_args
            if argument.startswith("--rootdir=")
        ),
        None,
    )
    if project_root_argument is None and "--rootdir" in cli_args:
        rootdir_index = cli_args.index("--rootdir")
        if rootdir_index + 1 < len(cli_args):
            project_root_argument = cli_args[rootdir_index + 1]

    python_paths = [str(test_root)]
    if project_root_argument is not None:
        project_root = Path(project_root_argument)
        if not project_root.is_absolute():
            project_root = test_root / project_root
        if project_root.is_dir():
            python_paths.insert(0, str(project_root))
    current_path = os.environ.get("PYTHONPATH", "")
    testdir.monkeypatch.setenv(
        "PYTHONPATH",
        os.pathsep.join(filter(None, (*python_paths, source_dir, current_path))),
    )
    in_subprocess = "in a subprocess" in step.text or os.name == "nt"
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
    expected_summary = re.compile(r"\b1 passed\b")
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
    expected_summary = re.compile(r"\b1 passed\b")
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


@then("pytest output should identify the invalid external Examples row and both paths")
def consumer_invalid_external_examples_row(consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert "External Examples source error" in output
    assert "row 2 has 1 columns; expected 2" in output
    assert str((consumer.path / "features/broken.feature").resolve()) in output
    assert str((consumer.path / "features/broken.csv").resolve()) in output


@then(re.compile(r"the test outcome should have (?P<count>\d+) passed scenarios"))
def consumer_passed_scenarios(count, consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    expected_summary = rf"\b{re.escape(count)} passed\b"
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


@then("pytest terminal output should report 2 passed tests")
def consumer_terminal_summary(consumer: ConsumerProject):
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    assert re.search(r"\b2 passed\b", f"{result.stdout}\n{result.stderr}")


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
    from pytest_cuke.model.message_types import TestCase, TestCaseFinished, TestCaseStarted, TestRunFinished
    from pytest_cuke.model.message_types import TestRunStarted, TestStepFinished

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
        r'the structured YAML source is omitted from Cucumber Messages in artifact "(?P<relative_path>[^"]+)"'
    )
)
def structured_yaml_source_is_omitted_from_messages(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = [
        json.loads(line)
        for line in (consumer.path / relative_path).read_text(encoding="utf-8").splitlines()
    ]
    assert not any("source" in envelope for envelope in envelopes), envelopes


@then(
    re.compile(
        r'every Pickle step in artifact "(?P<relative_path>[^"]+)" refers to a Gherkin AST step'
    )
)
def pickle_steps_reference_gherkin_ast_steps(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = [
        json.loads(line)
        for line in (consumer.path / relative_path).read_text(encoding="utf-8").splitlines()
    ]
    gherkin_documents = [envelope["gherkinDocument"] for envelope in envelopes if "gherkinDocument" in envelope]
    pickle_steps = [
        step
        for envelope in envelopes
        if "pickle" in envelope
        for step in envelope["pickle"].get("steps", [])
    ]

    def collect_step_ids(node: object) -> set[str]:
        identifiers: set[str] = set()
        if isinstance(node, dict):
            steps = node.get("steps")
            if isinstance(steps, list):
                identifiers.update(
                    step["id"]
                    for step in steps
                    if isinstance(step, dict) and isinstance(step.get("id"), str) and step["id"]
                )
            for value in node.values():
                identifiers.update(collect_step_ids(value))
        elif isinstance(node, list):
            for value in node:
                identifiers.update(collect_step_ids(value))
        return identifiers

    gherkin_step_ids = set().union(*(collect_step_ids(document) for document in gherkin_documents))
    assert gherkin_documents, envelopes
    assert pickle_steps, envelopes
    for pickle_step in pickle_steps:
        ast_node_ids = pickle_step.get("astNodeIds")
        assert isinstance(ast_node_ids, list) and ast_node_ids, pickle_step
        assert set(ast_node_ids).issubset(gherkin_step_ids), (pickle_step, gherkin_step_ids)


def _local_xdist_messages_artifact(
    relative_path: str,
    consumer: ConsumerProject,
    *,
    expect_partial: bool = False,
) -> list[dict[str, Any]]:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    assert artifact_path.is_file(), f"local xdist Messages artifact was not written: {artifact_path}"
    envelopes: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(artifact_path.read_text(encoding="utf-8").splitlines(), start=1):
        assert raw_line.strip(), f"local xdist Messages artifact has a blank line at {line_number}"
        envelope = json.loads(raw_line)
        assert isinstance(envelope, dict), f"local xdist Messages line {line_number} is not an object: {envelope!r}"
        payload_keys = [key for key, value in envelope.items() if value is not None]
        assert len(payload_keys) == 1, f"local xdist Messages line {line_number} is not one payload: {envelope!r}"
        _validate_messages_envelope_compatibly(envelope)
        envelopes.append(envelope)
    assert envelopes, f"local xdist Messages artifact is empty: {artifact_path}"
    if not expect_partial:
        from pytest_cuke.model.message_stream_validation import MessageStreamValidator

        validator = MessageStreamValidator()
        for envelope in envelopes:
            validator.accept(message_from_dict(envelope))
        diagnostics = validator.finish()
        assert not diagnostics, f"local xdist Messages artifact has stream diagnostics: {diagnostics!r}"
    return envelopes


def _message_identifier_graph(value: object) -> tuple[list[str], list[str]]:
    object_ids: list[str] = []
    references: list[str] = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key == "workerId":
                    continue
                if key == "id":
                    assert isinstance(nested, str) and nested, (key, nested)
                    object_ids.append(nested)
                elif key.endswith(("Id", "Ids", "_id", "_ids")):
                    identifiers = nested if isinstance(nested, list) else [nested]
                    for identifier in identifiers:
                        assert isinstance(identifier, str) and identifier, (key, identifier)
                        references.append(identifier)
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(value)
    return object_ids, references


def _assert_local_xdist_messages_graph(
    envelopes: list[dict[str, Any]],
    observations: list[dict[str, str]] | None,
) -> None:
    expected_cases = [
        "worker case standalone completes",
        "worker case alpha completes",
        "worker case beta completes",
        "worker case alpha completes",
    ]
    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    started = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    case_finished = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    step_started = [envelope["testStepStarted"] for envelope in envelopes if "testStepStarted" in envelope]
    step_finished = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]

    assert len([envelope for envelope in envelopes if "meta" in envelope]) == 1, envelopes
    assert len([envelope for envelope in envelopes if "source" in envelope]) == 1, envelopes
    assert len([envelope for envelope in envelopes if "gherkinDocument" in envelope]) == 1, envelopes
    assert len(pickles) == len(cases) == 4
    assert len(started) == len(case_finished) == 4
    assert len(step_started) == len(step_finished) == 4
    assert len(run_started) == len(run_finished) == 1
    assert run_finished[0].get("success") is True, run_finished[0]
    assert envelopes[-1].get("testRunFinished") == run_finished[0], "testRunFinished must close the merged stream"
    if observations is not None:
        assert len(observations) == 4, observations
        assert Counter(observation["case"] for observation in observations) == Counter(
            ["standalone", "alpha", "beta", "alpha"]
        ), observations
        observed_workers = {observation["worker_id"] for observation in observations}
    else:
        observed_workers = {attempt.get("workerId") for attempt in started}
        assert all(isinstance(worker_id, str) and worker_id for worker_id in observed_workers), started
    assert len(observed_workers) == 2, observations

    pickle_step_texts = [pickle["steps"][0]["text"] for pickle in pickles]
    assert len(pickle_step_texts) == 4, pickle_step_texts
    assert Counter(pickle_step_texts) == Counter(expected_cases), pickle_step_texts

    pickles_by_id = {pickle["id"]: pickle for pickle in pickles}
    cases_by_id = {case["id"]: case for case in cases}
    starts_by_id = {attempt["id"]: attempt for attempt in started}
    assert len(pickles_by_id) == len(pickles), pickles
    assert len(cases_by_id) == len(cases), cases
    assert len(starts_by_id) == len(started), started
    assert {case["pickleId"] for case in cases} == set(pickles_by_id), cases
    assert {finish["testCaseStartedId"] for finish in case_finished} == set(starts_by_id), case_finished
    assert len(case_finished) == len({finish["testCaseStartedId"] for finish in case_finished}), case_finished

    started_case_names: list[str] = []
    for attempt in started:
        case = cases_by_id[attempt["testCaseId"]]
        pickle = pickles_by_id[case["pickleId"]]
        case_step_text = pickle["steps"][0]["text"]
        assert case_step_text in expected_cases, case_step_text
        assert attempt.get("workerId") in observed_workers, (attempt, observed_workers)
        assert attempt["attempt"] == 0, attempt
        started_case_names.append(case_step_text)
        pickle_step_ids = [step["id"] for step in pickle["steps"]]
        case_steps = case["testSteps"]
        assert [step["pickleStepId"] for step in case_steps] == pickle_step_ids, (case, pickle)
        assert len(case_steps) == 1, case
    assert Counter(started_case_names) == Counter(expected_cases), started_case_names

    valid_steps_by_case_id = {
        case["id"]: {step["id"] for step in case["testSteps"]}
        for case in cases
    }
    started_references = [
        (event["testCaseStartedId"], event["testStepId"])
        for event in step_started
    ]
    finished_references = [
        (event["testCaseStartedId"], event["testStepId"])
        for event in step_finished
    ]
    assert len(started_references) == len(set(started_references)) == 4, step_started
    assert len(finished_references) == len(set(finished_references)) == 4, step_finished
    assert set(started_references) == set(finished_references), (step_started, step_finished)
    for event in [*step_started, *step_finished]:
        attempt = starts_by_id.get(event["testCaseStartedId"])
        assert attempt is not None, f"step event references a missing attempt: {event!r}"
        case_id = attempt["testCaseId"]
        assert event["testStepId"] in valid_steps_by_case_id[case_id], (event, case_id)
    assert all(event["testStepResult"]["status"] == "PASSED" for event in step_finished), step_finished

    object_ids, references = _message_identifier_graph(envelopes)
    assert len(object_ids) == len(set(object_ids)), f"worker-scoped Messages IDs were not namespaced: {object_ids}"
    namespace_prefixes = {f"{worker_id}:" for worker_id in observed_workers} | {"master:"}
    identifiers = [*object_ids, *references]
    assert all(identifier.startswith(tuple(namespace_prefixes)) for identifier in identifiers), identifiers
    assert set(references) <= set(object_ids), f"Messages references point to missing nested or envelope IDs: {set(references) - set(object_ids)}"


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should be one complete local xdist Messages stream '
        r"for the four selected rows"
    )
)
def consumer_local_xdist_messages_stream(relative_path: str, consumer: ConsumerProject) -> None:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    envelopes = _local_xdist_messages_artifact(relative_path, consumer)
    observation_directory = artifact_path.with_name(f"{artifact_path.name}.worker-observations")
    assert observation_directory.is_dir(), f"xdist worker observations are missing: {observation_directory}"
    observations: list[dict[str, str]] = []
    for observation_path in observation_directory.glob("*.json"):
        observation = json.loads(observation_path.read_text(encoding="utf-8"))
        assert isinstance(observation, dict), observation
        case_token = observation.get("case")
        worker_id = observation.get("worker_id")
        assert isinstance(case_token, str) and case_token, observation
        assert isinstance(worker_id, str) and worker_id and worker_id != "master", observation
        observations.append({"case": case_token, "worker_id": worker_id})
    _assert_local_xdist_messages_graph(envelopes, observations)
    shutil.rmtree(observation_directory)


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should be one complete subprocess gateway Messages stream '
        r"for the four selected rows"
    )
)
def consumer_subprocess_gateway_messages_stream(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _local_xdist_messages_artifact(relative_path, consumer)
    _assert_local_xdist_messages_graph(envelopes, observations=None)


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should contain incomplete live worker batches'
    )
)
def consumer_local_xdist_live_batches(relative_path: str, consumer: ConsumerProject) -> None:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    assert artifact_path.is_file(), f"live xdist batch artifact was not written: {artifact_path}"
    raw_batches = artifact_path.read_text(encoding="utf-8").splitlines()
    assert raw_batches, f"live xdist batch artifact is empty: {artifact_path}"
    batches: list[dict[str, Any]] = []
    for line_number, raw_batch in enumerate(raw_batches, start=1):
        assert raw_batch.strip(), f"live xdist batch artifact has a blank line at {line_number}"
        batch = json.loads(raw_batch)
        assert isinstance(batch, dict), batch
        assert batch.get("complete") is False, f"live worker batches must remain explicitly incomplete: {batch!r}"
        worker_id = batch.get("worker_id")
        sequence = batch.get("sequence")
        envelopes = batch.get("envelopes")
        assert isinstance(worker_id, str) and worker_id and worker_id != "master", batch
        assert isinstance(sequence, int) and not isinstance(sequence, bool) and sequence >= 0, batch
        assert isinstance(envelopes, list) and envelopes, batch
        for envelope in envelopes:
            _validate_messages_envelope_compatibly(envelope)
        batches.append(batch)

    worker_sequences: dict[str, list[int]] = defaultdict(list)
    for batch in batches:
        worker_sequences[batch["worker_id"]].append(batch["sequence"])
        for envelope in batch["envelopes"]:
            object_ids, references = _message_identifier_graph(envelope)
            prefix = f"{batch['worker_id']}:"
            assert all(identifier.startswith(prefix) for identifier in [*object_ids, *references]), batch

    assert len(worker_sequences) >= 2, f"live transport should expose at least two workers: {worker_sequences}"
    for worker_id, sequences in worker_sequences.items():
        assert len(sequences) == len(set(sequences)), (worker_id, sequences)
        assert sorted(sequences) == list(range(len(sequences))), (worker_id, sequences)


@then(
    re.compile(
        r'consumer artifact "(?P<manifest_path>[^\"]+)" should report complete manifests matching '
        r'"(?P<batches_path>[^\"]+)"(?P<expected_test_failure> despite the expected test failure)?'
    )
)
def consumer_local_xdist_manifests_match_batches(
    manifest_path: str,
    batches_path: str,
    consumer: ConsumerProject,
    expected_test_failure: str | None = None,
) -> None:
    from pytest_cuke.model.message_consolidation import namespace_envelope_ids

    manifest_artifact = _consumer_artifact_path(manifest_path, consumer)
    batch_artifact = _consumer_artifact_path(batches_path, consumer)
    assert manifest_artifact.is_file(), f"worker manifest artifact was not written: {manifest_artifact}"
    assert batch_artifact.is_file(), f"live batch artifact was not written: {batch_artifact}"
    records = [json.loads(line) for line in manifest_artifact.read_text(encoding="utf-8").splitlines() if line]
    batches = [json.loads(line) for line in batch_artifact.read_text(encoding="utf-8").splitlines() if line]
    assert records, f"worker manifest artifact is empty: {manifest_artifact}"
    assert len(records) == 2, records

    observed_batches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for batch in batches:
        observed_batches[batch["worker_id"]].append(batch)
    seen_workers: set[str] = set()
    for record in records:
        worker_id = record.get("worker_id")
        transport = record.get("transport")
        assert isinstance(worker_id, str) and worker_id, record
        assert worker_id not in seen_workers, f"worker published more than one completion record: {record!r}"
        seen_workers.add(worker_id)
        assert record.get("error") is None, record
        allowed_exit_statuses = (None, 0, 1) if expected_test_failure else (None, 0)
        assert record.get("exitstatus") in allowed_exit_statuses, record
        assert isinstance(transport, dict), record
        manifest = transport.get("manifest")
        tail_batch = transport.get("tail_batch")
        assert isinstance(manifest, dict), record
        assert manifest.get("complete") is True, record
        assert manifest.get("worker_id") == worker_id, record
        worker_batches = observed_batches.pop(worker_id, [])
        if isinstance(tail_batch, dict):
            tail_batch_worker_id = tail_batch.get("worker_id")
            tail_sequence = tail_batch.get("sequence")
            assert tail_batch_worker_id == worker_id, (record, tail_batch)
            assert isinstance(tail_sequence, int) and not isinstance(tail_sequence, bool), tail_batch
            matching_batches = [batch for batch in worker_batches if batch.get("sequence") == tail_sequence]
            if matching_batches:
                assert len(matching_batches) == 1, (record, matching_batches)
                live_batch = matching_batches[0]
                assert live_batch.get("worker_id") == tail_batch_worker_id, (live_batch, tail_batch)
                tail_envelopes = tail_batch.get("envelopes")
                assert isinstance(tail_envelopes, list), tail_batch
                namespaced_tail_envelopes = [
                    namespace_envelope_ids(envelope, worker_id=worker_id) for envelope in tail_envelopes
                ]
                assert live_batch.get("envelopes") == namespaced_tail_envelopes, (live_batch, tail_batch)
            else:
                worker_batches.append(tail_batch)
        sequences = sorted(batch.get("sequence") for batch in worker_batches)
        envelope_count = sum(len(batch.get("envelopes", [])) for batch in worker_batches)
        assert sequences == list(range(manifest["batch_count"])), (record, sequences)
        assert manifest.get("batch_count") == len(worker_batches), (record, len(worker_batches))
        assert manifest.get("envelope_count") == envelope_count, (record, envelope_count)
        assert manifest.get("last_sequence") == (sequences[-1] if sequences else None), (record, sequences)
    assert not observed_batches, f"live batches have no corresponding worker manifest: {observed_batches}"
    assert len(seen_workers) == 2, seen_workers
    manifest_artifact.unlink()


@given("the installed consumer pins pytest-xdist below 4 for socket rsync staging")
def pin_consumer_xdist_below_four_for_socket_rsync(consumer: ConsumerProject) -> None:
    uv_executable = shutil.which("uv")
    assert uv_executable, "socket gateway consumer setup requires uv to pin pytest-xdist"
    result = subprocess.run(
        [uv_executable, "pip", "install", "--python", str(consumer.python), "pytest-xdist<4"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"could not install xdist with rsync support:\n{result.stdout}\n{result.stderr}"


@given("a test-managed isolated localhost execnet socket gateway is listening")
def start_isolated_localhost_execnet_socket_gateway(
    consumer: ConsumerProject,
    request,
) -> None:
    _start_execnet_socket_gateways(consumer, request, filesystem_isolated=False)


@given("a test-managed filesystem-isolated localhost execnet socket gateway is listening")
def start_filesystem_isolated_localhost_execnet_socket_gateway(
    consumer: ConsumerProject,
    request,
) -> None:
    import pytest

    if sys.platform != "linux":
        pytest.skip("@external filesystem-isolation gateway acceptance requires Linux bubblewrap")
    bubblewrap = shutil.which("bwrap")
    if bubblewrap is None:
        pytest.skip("@external filesystem-isolation gateway acceptance requires bubblewrap; remote parity is unverified")
    _start_execnet_socket_gateways(
        consumer,
        request,
        filesystem_isolated=True,
        bubblewrap=bubblewrap,
    )


def _start_execnet_socket_gateways(
    consumer: ConsumerProject,
    request,
    *,
    filesystem_isolated: bool,
    bubblewrap: str | None = None,
) -> None:
    import socket
    import tempfile

    addresses: list[str] = []
    processes: list[Any] = []
    remote_roots: list[Path] = []
    log_paths: list[Path] = []
    consumer.socket_gateway_addresses = addresses
    consumer.socket_gateway_processes = processes
    consumer.socket_gateway_remote_roots = remote_roots
    consumer.socket_gateway_log_paths = log_paths
    consumer.socket_gateway_filesystem_isolated = filesystem_isolated

    def stop_gateway() -> None:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        for remote_root in remote_roots:
            shutil.rmtree(remote_root, ignore_errors=True)

    request.addfinalizer(stop_gateway)

    server_environment = consumer.env.copy()
    server_environment["PYTHONUNBUFFERED"] = "1"
    if filesystem_isolated:
        assert bubblewrap is not None
        server_environment["HOME"] = "/tmp"
        server_environment["TMPDIR"] = "/tmp"
        server_environment["PATH"] = "/opt/pytest-cuke-remote/bin:/usr/bin:/bin"
        server_environment["VIRTUAL_ENV"] = "/opt/pytest-cuke-remote"
        server_environment["PYTEST_CUKE_HIDDEN_CONSUMER_ROOT"] = str(consumer.path.resolve())
    for gateway_index in range(2):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            host, port = listener.getsockname()
        address = f"{host}:{port}"
        remote_root = Path(tempfile.mkdtemp(prefix=f"pytest-cuke-execnet-remote-{gateway_index}-"))
        log_path = remote_root / "socketserver.log"
        addresses.append(address)
        remote_roots.append(remote_root)
        log_paths.append(log_path)
        log_stream = log_path.open("w", encoding="utf-8")
        server_command = [str(consumer.python), "-m", "execnet.script.socketserver", address]
        server_cwd = remote_root
        if filesystem_isolated:
            checkout_root = Path(__file__).resolve().parents[2]
            remote_venv = Path(consumer.python).parent.parent
            server_command = [
                bubblewrap,
                "--unshare-user",
                "--unshare-pid",
                "--unshare-ipc",
                "--unshare-uts",
                "--die-with-parent",
                "--ro-bind",
                "/",
                "/",
                "--proc",
                "/proc",
                "--dev",
                "/dev",
                "--tmpfs",
                "/opt",
                "--dir",
                "/opt/pytest-cuke-remote",
                "--ro-bind",
                str(remote_venv),
                "/opt/pytest-cuke-remote",
                "--tmpfs",
                "/tmp",
                "--tmpfs",
                "/mnt",
                "--tmpfs",
                str(checkout_root),
                "--chdir",
                "/tmp",
                "/opt/pytest-cuke-remote/bin/python",
                "-m",
                "execnet.script.socketserver",
                address,
            ]
            server_cwd = Path("/")
        try:
            process = subprocess.Popen(
                server_command,
                cwd=server_cwd,
                env=server_environment,
                stdin=subprocess.DEVNULL,
                stdout=log_stream,
                stderr=subprocess.STDOUT,
            )
        finally:
            log_stream.close()
        processes.append(process)

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            if log_path.is_file() and "Entering Accept loop" in log_path.read_text(
                encoding="utf-8", errors="replace"
            ):
                break
            time.sleep(0.05)
        server_output = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
        assert process.poll() is None and "Entering Accept loop" in server_output, (
            f"test-managed execnet socket gateway {gateway_index} did not start:\n{server_output}"
        )
        assert consumer.path.resolve() not in remote_root.resolve().parents, (
            "localhost socket servers must run outside the consumer project tree"
        )


@when(
    re.compile(
        r'I run installed pytest through two localhost execnet socket gateways with arguments "(?P<arguments>[^\"]*)"'
    ),
    target_fixture="pytest_run_result",
)
def run_installed_pytest_through_localhost_socket_gateways(arguments: str, consumer: ConsumerProject):
    addresses = consumer.socket_gateway_addresses
    assert addresses and len(addresses) == 2, "two test-managed localhost socket gateways have not started"
    pytest_arguments = _split_consumer_arguments(arguments)
    rewritten_arguments: list[str] = []
    for argument in pytest_arguments:
        if argument == "--rootdir=.":
            rewritten_arguments.extend(("--rootdir", str(consumer.path.resolve())))
        elif argument == "features" or argument.startswith("features/"):
            rewritten_arguments.append(str(consumer.path / argument))
        else:
            rewritten_arguments.append(argument)
    command = [
        str(consumer.pytest),
        *rewritten_arguments,
        *(f"--tx=socket={address}" for address in addresses),
    ]
    conftest_path = consumer.path / "conftest.py"
    conftest = conftest_path.read_text(encoding="utf-8") if conftest_path.is_file() else ""
    nodeid_normalizer = "# pytest-cuke test-managed socket nodeid normalization"
    if nodeid_normalizer not in conftest:
        conftest_path.write_text(
            conftest
            + "\n\n"
            + nodeid_normalizer
            + "\n"
            + dedent(
                r'''
                import re as _pytest_cuke_socket_re

                _pytest_cuke_socket_remote_nodeid = _pytest_cuke_socket_re.compile(
                    r"file:.+?/pyexecnetcache/(pytest-cuke-group-consumer[^/]+)/features/socket-worker-cases\.feature-"
                )

                def pytest_collection_modifyitems(items):
                    for item in items:
                        normalized = item.nodeid.replace("\\", "/")
                        item._nodeid = _pytest_cuke_socket_remote_nodeid.sub(
                            r"file:\1/features/socket-worker-cases.feature-", normalized
                        )
                '''
            ),
            encoding="utf-8",
        )
    try:
        result = subprocess.run(
            command,
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
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
    if result.returncode != 0:
        remote_roots = consumer.socket_gateway_remote_roots or []
        remote_diagnostics = []
        for index, root in enumerate(remote_roots):
            entries = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
            log_path = root / "socketserver.log"
            server_log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
            remote_diagnostics.append(
                f"socket gateway {index} root files={entries!r}; server log={server_log!r}"
            )
        result.stdout = f"{result.stdout}\n" + "\n".join(remote_diagnostics)
    consumer.pytest_result = result
    return result


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should be one complete localhost socket gateway Messages stream '
        r"for the four selected rows"
    )
)
def consumer_localhost_socket_gateway_messages_stream(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _local_xdist_messages_artifact(relative_path, consumer)
    _assert_local_xdist_messages_graph(envelopes, observations=None)


@then("consumer artifact \"isolated.ndjson\" should be a complete filesystem-isolated gateway Messages stream")
def consumer_filesystem_isolated_gateway_messages_stream(consumer: ConsumerProject) -> None:
    from pytest_cuke.model.message_stream_validation import MessageStreamValidator

    envelopes = _local_xdist_messages_artifact("isolated.ndjson", consumer)
    validator = MessageStreamValidator()
    for envelope in envelopes:
        validator.accept(message_from_dict(envelope))
    diagnostics = validator.finish()
    assert not diagnostics, f"filesystem-isolated gateway stream has structural or reference errors: {diagnostics!r}"

    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    started = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    finished = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]

    assert len(pickles) == len(cases) == len(started) == len(finished) == 2, envelopes
    assert len(run_finished) == 1 and run_finished[0].get("success") is True, run_finished
    assert envelopes[-1].get("testRunFinished") == run_finished[0], "the isolated gateway stream must be finalized"
    pickles_by_id = {pickle["id"]: pickle for pickle in pickles}
    cases_by_id = {case["id"]: case for case in cases}
    assert {pickles_by_id[cases_by_id[attempt["testCaseId"]]["pickleId"]]["name"] for attempt in started} == {
        "First worker case",
        "Second worker case",
    }
    assert len({attempt.get("workerId") for attempt in started}) == 2, started

    object_ids, references = _message_identifier_graph(envelopes)
    assert len(object_ids) == len(set(object_ids)), f"isolated worker IDs were not namespaced: {object_ids}"
    assert set(references) <= set(object_ids), (
        f"isolated worker references point to missing IDs: {set(references) - set(object_ids)}"
    )


@then("the socket consumer should have no worker-shared observation artifacts")
def consumer_socket_gateway_has_no_shared_observations(consumer: ConsumerProject) -> None:
    observation_paths = sorted(consumer.path.rglob("*.worker-observations"))
    assert not observation_paths, f"socket worker observations unexpectedly used shared consumer paths: {observation_paths}"
    remote_roots = consumer.socket_gateway_remote_roots
    assert remote_roots and len(remote_roots) == 2, "the isolated socket server roots are unavailable"
    assert all(root.is_dir() for root in remote_roots), remote_roots
    remote_observations = sorted(path for root in remote_roots for path in root.rglob("*.worker-observations"))
    assert not remote_observations, f"socket worker observations were created in the isolated server root: {remote_observations}"


@then("pytest output should report one passed, one failed, and one skipped test")
def consumer_mixed_xdist_outcomes(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert re.search(r"\b1 passed\b", output), output
    assert re.search(r"\b1 failed\b", output), output
    assert re.search(r"\b1 skipped\b", output), output
    assert "expected worker case failure" in output, output


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should contain the complete mixed local xdist Messages stream'
    )
)
def consumer_mixed_xdist_messages_stream(relative_path: str, consumer: ConsumerProject) -> None:
    from pytest_cuke.model.message_stream_validation import MessageStreamValidator

    envelopes = _local_xdist_messages_artifact(relative_path, consumer)
    validator = MessageStreamValidator()
    for envelope in envelopes:
        validator.accept(message_from_dict(envelope))
    diagnostics = validator.finish()
    assert not diagnostics, f"the mixed outcome stream has structural or reference errors: {diagnostics!r}"

    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    started = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    case_finished = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    step_started = [envelope["testStepStarted"] for envelope in envelopes if "testStepStarted" in envelope]
    step_finished = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]

    assert len(pickles) == len(cases) == len(started) == len(case_finished) == 3
    assert len(step_started) == len(step_finished) == 3
    assert len(run_started) == len(run_finished) == 1
    assert run_finished[0].get("success") is False, run_finished[0]
    assert envelopes[-1].get("testRunFinished") == run_finished[0], "testRunFinished must close the merged stream"

    expected_names = {"mixed worker case passed completes", "mixed worker case failed completes", "mixed worker case skipped completes"}
    pickles_by_id = {pickle["id"]: pickle for pickle in pickles}
    cases_by_id = {case["id"]: case for case in cases}
    starts_by_id = {attempt["id"]: attempt for attempt in started}
    finishes_by_attempt = {finish["testCaseStartedId"]: finish for finish in case_finished}
    assert len(pickles_by_id) == len(cases_by_id) == len(starts_by_id) == 3
    assert set(finishes_by_attempt) == set(starts_by_id), case_finished
    assert len(finishes_by_attempt) == 3, case_finished
    assert {case["pickleId"] for case in cases} == set(pickles_by_id), cases

    attempts_by_name: dict[str, dict[str, Any]] = {}
    for attempt in started:
        case = cases_by_id[attempt["testCaseId"]]
        pickle = pickles_by_id[case["pickleId"]]
        name = pickle["steps"][0]["text"]
        assert name in expected_names, (name, pickle)
        assert name not in attempts_by_name, f"selected row was started more than once: {name!r}"
        assert attempt.get("attempt") == 0, attempt
        assert isinstance(attempt.get("workerId"), str) and attempt["workerId"].startswith("gw"), attempt
        assert len(case["testSteps"]) == 1, case
        attempts_by_name[name] = attempt
    assert set(attempts_by_name) == expected_names, attempts_by_name

    statuses_by_name: dict[str, str] = {}
    for name, attempt in attempts_by_name.items():
        assert attempt["id"] in finishes_by_attempt, (name, attempt)
        matching_steps = [
            event
            for event in step_finished
            if event["testCaseStartedId"] == attempt["id"]
        ]
        assert len(matching_steps) == 1, matching_steps
        step_status = matching_steps[0]["testStepResult"]["status"]
        statuses_by_name[name] = step_status
    assert statuses_by_name == {
        "mixed worker case passed completes": "PASSED",
        "mixed worker case failed completes": "FAILED",
        "mixed worker case skipped completes": "SKIPPED",
    }, statuses_by_name

    object_ids, references = _message_identifier_graph(envelopes)
    assert len(object_ids) == len(set(object_ids)), f"worker-scoped Messages IDs were not namespaced: {object_ids}"
    assert set(references) <= set(object_ids), (
        f"Messages references point to missing nested or envelope IDs: {set(references) - set(object_ids)}"
    )


@then("pytest output should report the crashed xdist worker and partial Messages diagnostics")
def consumer_crashed_xdist_worker_diagnostics(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    assert not consumer.pytest_watchdog_expired, f"the xdist crash run exceeded its watchdog:\n{result.stdout}\n{result.stderr}"
    output = f"{result.stdout}\n{result.stderr}"
    for code in ("interrupted_worker_transfer", "missing_worker_manifest", "partial_stream"):
        assert code in output, f"missing {code!r} diagnostic from the controlled worker crash:\n{output}"


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should contain the flushed partial local xdist Messages stream'
    )
)
def consumer_crashed_xdist_partial_stream(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _local_xdist_messages_artifact(relative_path, consumer, expect_partial=True)
    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    case_finished = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    assert len(run_started) == len(run_finished) == 1, envelopes
    assert run_finished[0].get("success") is False, run_finished[0]
    assert envelopes[-1].get("testRunFinished") == run_finished[0], "the partial stream must flush its terminal message"
    assert case_finished, f"the survivor worker's completed case was not flushed: {envelopes!r}"


@then(re.compile(r'consumer artifact "(?P<relative_path>[^\"]+)" should record the crashed worker'))
def consumer_crashed_xdist_worker_record(relative_path: str, consumer: ConsumerProject) -> None:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    assert artifact_path.is_file(), f"worker shutdown probe artifact was not written: {artifact_path}"
    records = [json.loads(line) for line in artifact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(records) == 2, records
    crashed = [record for record in records if record.get("error")]
    assert len(crashed) == 1, records
    crashed_record = crashed[0]
    assert crashed_record.get("worker_id") in {"gw0", "gw1"}, crashed_record
    transport = crashed_record.get("transport")
    assert not isinstance(transport, dict) or not isinstance(transport.get("manifest"), dict), crashed_record
    survivor_records = [record for record in records if record is not crashed_record]
    assert len(survivor_records) == 1, records
    survivor_transport = survivor_records[0].get("transport")
    assert isinstance(survivor_transport, dict), survivor_records[0]
    survivor_manifest = survivor_transport.get("manifest")
    assert isinstance(survivor_manifest, dict) and survivor_manifest.get("complete") is True, survivor_records[0]


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^\"]+)" should contain the accepted stream after a publisher failure'
    )
)
def consumer_batch_publisher_failure_stream(relative_path: str, consumer: ConsumerProject) -> None:
    from pytest_cuke.model.message_stream_validation import MessageStreamValidator

    envelopes = _local_xdist_messages_artifact(relative_path, consumer)
    validator = MessageStreamValidator()
    for envelope in envelopes:
        validator.accept(message_from_dict(envelope))
    diagnostics = validator.finish()
    assert not diagnostics, f"the accepted stream should remain structurally valid: {diagnostics!r}"

    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    started = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    finished = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]

    assert len(pickles) == len(cases) == len(started) == len(finished) == 2, envelopes
    assert len(run_started) == len(run_finished) == 1, envelopes
    assert run_finished[0].get("success") is False, run_finished[0]
    assert envelopes[-1].get("testRunFinished") == run_finished[0], "the failed-publisher stream must be finalized"


def _normalized_local_xdist_messages(envelopes: list[dict[str, Any]]) -> list[object]:
    identifiers: dict[str, str] = {}
    json_attachment_media_types = {
        "application/vnd.pytest-bdd.launch+json",
        "application/vnd.pytest-bdd.step-binding+json",
        "application/vnd.pytest-bdd.diagnostic+json",
    }

    def normalize(value: object, field_name: str | None = None) -> object:
        if field_name in {"timestamp", "duration", "workerId"}:
            return None
        if isinstance(value, dict):
            media_type = value.get("mediaType")
            normalized_values: dict[str, object] = {}
            for key, item in value.items():
                if key in {"timestamp", "duration", "workerId"}:
                    continue
                if (
                    key == "body"
                    and isinstance(media_type, str)
                    and media_type in json_attachment_media_types
                    and isinstance(item, str)
                ):
                    try:
                        body = json.loads(item)
                    except json.JSONDecodeError:
                        normalized = item
                    else:
                        normalized_body = normalize(body)
                        normalized = json.dumps(
                            normalized_body,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                else:
                    normalized = normalize(item, key)
                if normalized is not None:
                    normalized_values[key] = normalized
            return normalized_values
        if isinstance(value, list):
            if isinstance(field_name, str) and (
                field_name == "id" or field_name.endswith(("Id", "Ids", "_id", "_ids"))
            ):
                return [normalize_identifier(item) for item in value]
            return [normalize(item) for item in value]
        if isinstance(value, str) and (
            field_name == "id"
            or (isinstance(field_name, str) and field_name.endswith(("Id", "Ids", "_id", "_ids")))
        ):
            return normalize_identifier(value)
        return value

    def normalize_identifier(value: object) -> object:
        if not isinstance(value, str):
            return normalize(value)
        if value not in identifiers:
            identifiers[value] = f"message-id-{len(identifiers) + 1}"
        return identifiers[value]

    return [normalize(envelope) for envelope in envelopes]


@then(
    re.compile(
        r'consumer artifacts "(?P<first_path>[^\"]+)" and "(?P<second_path>[^\"]+)" '
        r"should have identical normalized local xdist output"
    )
)
def consumer_local_xdist_messages_are_deterministic(
    first_path: str,
    second_path: str,
    consumer: ConsumerProject,
) -> None:
    first = _local_xdist_messages_artifact(first_path, consumer)
    second = _local_xdist_messages_artifact(second_path, consumer)
    first_normalized = _normalized_local_xdist_messages(first)
    second_normalized = _normalized_local_xdist_messages(second)
    assert first_normalized == second_normalized, (
        "equivalent local xdist runs should produce the same normalized Cucumber Messages stream"
    )


@then("the installed consumer should have no leftover local Messages worker fragments")
def consumer_has_no_local_xdist_message_fragments(consumer: ConsumerProject) -> None:
    root = consumer.path.resolve()
    leftover_paths: list[str] = []
    worker_terms = ("worker-fragment", "worker-manifest", "message-worker", "worker-message")
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix().casefold()
        if any(term in relative for term in worker_terms):
            leftover_paths.append(relative)
    assert not leftover_paths, f"local Messages worker fragments or manifests were left behind: {leftover_paths}"


@then(
    re.compile(
        r'consumer Messages artifact "(?P<relative_path>[^"]+)" should preserve the failed step diagnostics '
        r"and attachment correlations"
    )
)
def consumer_messages_failure_attachment_correlations(relative_path: str, consumer: ConsumerProject) -> None:
    from base64 import b64decode

    from pytest_cuke.model.message_types import ContentEncoding

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
    assert meta.get("protocolVersion") == "28.0.0", meta
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
    user_attachments = [attachment for attachment in attachments if attachment.test_case_started_id is not None]
    metadata_attachments = [attachment for attachment in attachments if attachment.test_case_started_id is None]
    assert len(user_attachments) == 2, user_attachments
    assert len(metadata_attachments) == 2, metadata_attachments
    assert len(user_attachments) + len(metadata_attachments) == len(attachments), attachments
    assert all(attachment.test_case_started_id == case_started.id for attachment in user_attachments), user_attachments
    assert all(attachment.test_step_id == test_step.id for attachment in user_attachments), user_attachments
    attachments_by_name = {attachment.file_name: attachment for attachment in user_attachments}
    assert len(attachments_by_name) == len(user_attachments), user_attachments
    assert set(attachments_by_name) == {"identity.txt", "binary.bin"}, attachments_by_name

    metadata_by_type = {attachment.media_type: attachment for attachment in metadata_attachments}
    assert len(metadata_by_type) == len(metadata_attachments), metadata_attachments
    assert set(metadata_by_type) == {_IDE_LAUNCH_MEDIA_TYPE, _IDE_STEP_BINDING_MEDIA_TYPE}, metadata_by_type
    launch_metadata = json.loads(metadata_by_type[_IDE_LAUNCH_MEDIA_TYPE].body)
    assert launch_metadata.get("testCaseId") == test_case.id, launch_metadata
    assert launch_metadata.get("pickleId") == pickle_message.id, launch_metadata
    step_metadata = json.loads(metadata_by_type[_IDE_STEP_BINDING_MEDIA_TYPE].body)
    assert step_metadata.get("testCaseId") == test_case.id, step_metadata
    assert step_metadata.get("pickleStepId") == test_step.pickle_step_id, step_metadata

    identity = attachments_by_name["identity.txt"]
    assert identity.content_encoding is ContentEncoding.identity
    assert identity.media_type == "text/plain"
    assert identity.body == "identity evidence"

    binary = attachments_by_name["binary.bin"]
    assert binary.content_encoding is ContentEncoding.base64
    assert binary.media_type == "application/octet-stream"
    assert b64decode(binary.body, validate=True) == b"\x00\xffbinary evidence"


@then(
    re.compile(
        r'consumer Messages artifact "(?P<relative_path>[^"]+)" should preserve the failed Background step '
        r'diagnostic and step order'
    )
)
def consumer_messages_failed_background_step(relative_path: str, consumer: ConsumerProject) -> None:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    envelopes = [
        json.loads(line)
        for line in artifact_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert all(isinstance(envelope, dict) for envelope in envelopes), envelopes

    meta = [envelope["meta"] for envelope in envelopes if isinstance(envelope.get("meta"), dict)]
    assert len(meta) == 1 and meta[0].get("protocolVersion") == "28.0.0", meta

    pickles = [envelope["pickle"] for envelope in envelopes if isinstance(envelope.get("pickle"), dict)]
    test_cases = [envelope["testCase"] for envelope in envelopes if isinstance(envelope.get("testCase"), dict)]
    assert len(pickles) == len(test_cases) == 1, (pickles, test_cases)
    pickle_steps = pickles[0].get("steps")
    test_steps = test_cases[0].get("testSteps")
    assert isinstance(pickle_steps, list) and len(pickle_steps) == 4, pickle_steps
    assert isinstance(test_steps, list) and len(test_steps) == len(pickle_steps), test_steps
    expected_step_texts = [
        "the shop is open",
        "the inventory reconciliation fails",
        "the customer is Ada",
        "the order is saved",
    ]
    assert [step.get("text") for step in pickle_steps if isinstance(step, dict)] == expected_step_texts, pickle_steps
    pickle_step_ids = [step.get("id") for step in pickle_steps if isinstance(step, dict)]
    assert all(isinstance(step_id, str) and step_id for step_id in pickle_step_ids), pickle_steps
    assert [step.get("pickleStepId") for step in test_steps if isinstance(step, dict)] == pickle_step_ids, test_steps

    case_started = [
        envelope["testCaseStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testCaseStarted"), dict)
    ]
    case_finished = [
        envelope["testCaseFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testCaseFinished"), dict)
    ]
    run_finished = [
        envelope["testRunFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunFinished"), dict)
    ]
    assert len(case_started) == len(case_finished) == len(run_finished) == 1, (
        case_started,
        case_finished,
        run_finished,
    )
    attempt_id = case_started[0].get("id")
    assert isinstance(attempt_id, str) and attempt_id, case_started[0]
    assert case_finished[0].get("testCaseStartedId") == attempt_id, case_finished[0]
    assert run_finished[0].get("success") is False, run_finished[0]

    failed_pickle_step_id = pickle_step_ids[1]
    failed_test_step = next(
        test_step
        for test_step in test_steps
        if isinstance(test_step, dict) and test_step.get("pickleStepId") == failed_pickle_step_id
    )
    failed_step_id = failed_test_step.get("id")
    assert isinstance(failed_step_id, str) and failed_step_id, failed_test_step
    started_events = [
        envelope["testStepStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testStepStarted"), dict)
        and envelope["testStepStarted"].get("testStepId") == failed_step_id
    ]
    finished_events = [
        envelope["testStepFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testStepFinished"), dict)
        and envelope["testStepFinished"].get("testStepId") == failed_step_id
    ]
    assert len(started_events) == len(finished_events) == 1, (started_events, finished_events)
    assert started_events[0].get("testCaseStartedId") == attempt_id, started_events[0]
    assert finished_events[0].get("testCaseStartedId") == attempt_id, finished_events[0]
    result = finished_events[0].get("testStepResult")
    assert isinstance(result, dict) and result.get("status") == "FAILED", finished_events[0]
    assert result.get("message") == "background failure sentinel", result
    exception = result.get("exception")
    assert isinstance(exception, dict), result
    assert exception.get("type") == "AssertionError", exception
    assert exception.get("message") == "background failure sentinel", exception
    trace = exception.get("stackTrace")
    assert isinstance(trace, str) and "AssertionError: background failure sentinel" in trace, exception


@then("consumer reports should preserve external row identities, source URIs, Background steps, and outcomes")
def consumer_external_examples_reports(consumer: ConsumerProject):
    json_report = json.loads((consumer.path / "report.json").read_text(encoding="utf-8"))
    json_features = {Path(feature["uri"].removeprefix("file:")).name: feature for feature in json_report}
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
            "the user lookup service is ready",
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
        [str(executable), *_split_consumer_arguments(arguments)],
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
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve Cucumber run-hook fixtures '
        r'and attachment evidence'
    )
)
def consumer_allure_run_hook_fixtures(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    assert result.get("name") == "Run-hook scenario", result
    assert result.get("status") == "passed", result
    assert result.get("stage") == "finished", result
    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 1, result
    assert isinstance(steps[0], dict), steps
    assert steps[0].get("name") == "the saved step", steps[0]
    assert steps[0].get("status") == "passed", steps[0]
    assert steps[0].get("stage") == "finished", steps[0]

    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    containers = _assert_allure_container_result_links(result_directory, {result_uuid})
    container = _assert_allure_shared_run_hook_container(containers, {result_uuid})

    befores = container.get("befores")
    assert isinstance(befores, list) and len(befores) == 1, container
    before = befores[0]
    assert isinstance(before, dict), before
    assert before.get("name") == "Prepare reporting endpoint", before
    assert before.get("status") == "passed", before
    assert before.get("stage") == "finished", before
    assert (before.get("start"), before.get("stop")) == (1700000000100, 1700000000200), before

    afters = container.get("afters")
    assert isinstance(afters, list) and len(afters) == 1, container
    after = afters[0]
    assert isinstance(after, dict), after
    assert after.get("name") == "Flush audit log", after
    assert after.get("status") == "failed", after
    assert after.get("stage") == "finished", after
    assert (after.get("start"), after.get("stop")) == (1700000000700, 1700000000900), after
    status_details = after.get("statusDetails")
    assert isinstance(status_details, dict), after
    assert status_details.get("message") == "after run hook failure sentinel", status_details
    assert status_details.get("trace") == (
        "RuntimeError: after run hook failure sentinel\n  at conftest.py:20"
    ), status_details

    attachments = after.get("attachments")
    assert isinstance(attachments, list) and len(attachments) == 2, after
    expected_attachments = {
        "after-run.log": ("text/plain", b"after run hook attachment bytes"),
        "after-run.bin": ("application/octet-stream", b"\x00\xff"),
    }
    seen_attachments: set[str] = set()
    for attachment in attachments:
        assert isinstance(attachment, dict), attachment
        name = attachment.get("name")
        assert isinstance(name, str) and name in expected_attachments, attachment
        assert name not in seen_attachments, attachments
        seen_attachments.add(name)
        media_type, expected_bytes = expected_attachments[name]
        assert attachment.get("type") == media_type, attachment
        attachment_path = _consumer_allure_attachment_file(result_directory, attachment)
        assert attachment_path.read_bytes() == expected_bytes, attachment
    assert seen_attachments == set(expected_attachments), attachments


def _assert_allure_attachment_sources(value: Any, result_directory: Path) -> None:
    if isinstance(value, dict):
        attachments = value.get("attachments")
        if attachments is not None:
            assert isinstance(attachments, list), attachments
            for attachment in attachments:
                assert isinstance(attachment, dict), attachment
                for field in ("name", "source", "type"):
                    assert isinstance(attachment.get(field), str) and attachment[field], attachment
                assert _consumer_allure_attachment_file(result_directory, attachment).is_file(), attachment
        for key, nested_value in value.items():
            if key != "attachments":
                _assert_allure_attachment_sources(nested_value, result_directory)
    elif isinstance(value, list):
        for nested_value in value:
            _assert_allure_attachment_sources(nested_value, result_directory)


def _assert_allure_container_result_links(
    result_directory: Path,
    result_ids: set[str],
) -> list[dict[str, Any]]:
    container_files = sorted(result_directory.glob("*-container.json"))
    assert container_files, f"expected Allure container files in {result_directory}"
    linked_ids: list[str] = []
    containers: list[dict[str, Any]] = []
    for container_file in container_files:
        container = json.loads(container_file.read_text(encoding="utf-8"))
        assert isinstance(container, dict), f"Allure container must be a JSON object, got {type(container).__name__}"
        container_uuid = container.get("uuid")
        assert isinstance(container_uuid, str) and container_uuid, container
        children = container.get("children")
        assert isinstance(children, list) and children, container
        assert all(isinstance(child, str) and child for child in children), container
        assert len(children) == len(set(children)), container
        unknown_ids = set(children) - result_ids
        assert not unknown_ids, {"container": container, "unknown_result_ids": unknown_ids}
        linked_ids.extend(children)
        containers.append(container)

    assert set(linked_ids) == result_ids, {"linked_result_ids": linked_ids, "expected_result_ids": result_ids}
    return containers


def _assert_allure_shared_run_hook_container(
    containers: list[dict[str, Any]],
    result_ids: set[str],
) -> dict[str, Any]:
    fixture_containers = [
        container
        for container in containers
        if container.get("befores") or container.get("afters")
    ]
    assert len(fixture_containers) == 1, fixture_containers
    shared_container = fixture_containers[0]
    assert set(shared_container.get("children", [])) == result_ids, shared_container
    return shared_container


@then(
    re.compile(
        r'consumer Messages artifact "(?P<relative_path>[^"]+)" should preserve pytest-generated v28 run hooks '
        r"around one passed scenario"
    )
)
def consumer_messages_pytest_generated_run_hooks(relative_path: str, consumer: ConsumerProject) -> None:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    envelopes = [
        json.loads(line)
        for line in artifact_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert all(isinstance(envelope, dict) for envelope in envelopes), envelopes

    metas = [envelope["meta"] for envelope in envelopes if isinstance(envelope.get("meta"), dict)]
    assert len(metas) == 1 and metas[0].get("protocolVersion") == "28.0.0", metas

    run_started_events = [
        envelope["testRunStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunStarted"), dict)
    ]
    run_finished_events = [
        envelope["testRunFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunFinished"), dict)
    ]
    assert len(run_started_events) == len(run_finished_events) == 1, (
        run_started_events,
        run_finished_events,
    )
    run_id = run_started_events[0].get("id")
    assert isinstance(run_id, str) and run_id, run_started_events[0]
    assert run_finished_events[0].get("testRunStartedId") == run_id, run_finished_events[0]
    assert run_finished_events[0].get("success") is True, run_finished_events[0]

    hook_definitions = {
        hook.get("type"): hook
        for envelope in envelopes
        if isinstance((hook := envelope.get("hook")), dict)
        and hook.get("type") in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}
    }
    assert set(hook_definitions) == {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}, hook_definitions
    expected_names = {
        "BEFORE_TEST_RUN": "pytest session start",
        "AFTER_TEST_RUN": "pytest session finish",
    }
    for hook_type, hook in hook_definitions.items():
        assert hook.get("name") == expected_names[hook_type], hook
        assert isinstance(hook.get("id"), str) and hook["id"], hook
        assert hook.get("sourceReference") == {
            "uri": "pytest-cuke:runtime",
            "location": {"line": 1},
        }, hook

    run_hook_starts: dict[str, dict[str, Any]] = {}
    run_hook_start_positions: dict[str, int] = {}
    for index, envelope in enumerate(envelopes):
        started = envelope.get("testRunHookStarted")
        if not isinstance(started, dict):
            continue
        hook_type = next(
            (
                kind
                for kind, hook in hook_definitions.items()
                if hook.get("id") == started.get("hookId")
            ),
            None,
        )
        assert hook_type is not None, started
        assert hook_type not in run_hook_starts, (hook_type, run_hook_starts, started)
        assert started.get("testRunStartedId") == run_id, started
        assert isinstance(started.get("id"), str) and started["id"], started
        run_hook_starts[hook_type] = started
        run_hook_start_positions[hook_type] = index
    assert set(run_hook_starts) == {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}, run_hook_starts

    run_hook_finishes: dict[str, dict[str, Any]] = {}
    run_hook_finish_positions: dict[str, int] = {}
    for index, envelope in enumerate(envelopes):
        finished = envelope.get("testRunHookFinished")
        if not isinstance(finished, dict):
            continue
        started_id = finished.get("testRunHookStartedId")
        hook_type = next(
            (kind for kind, started in run_hook_starts.items() if started.get("id") == started_id),
            None,
        )
        assert hook_type is not None and hook_type not in run_hook_finishes, finished
        result = finished.get("result")
        assert isinstance(result, dict) and result.get("status") == "PASSED", finished
        run_hook_finishes[hook_type] = finished
        run_hook_finish_positions[hook_type] = index
    assert set(run_hook_finishes) == {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}, run_hook_finishes

    case_starts = [
        (index, envelope["testCaseStarted"])
        for index, envelope in enumerate(envelopes)
        if isinstance(envelope.get("testCaseStarted"), dict)
    ]
    case_finishes = [
        (index, envelope["testCaseFinished"])
        for index, envelope in enumerate(envelopes)
        if isinstance(envelope.get("testCaseFinished"), dict)
    ]
    assert len(case_starts) == len(case_finishes) == 1, (case_starts, case_finishes)
    case_start_index, case_started = case_starts[0]
    case_finish_index, case_finished = case_finishes[0]
    assert case_finished.get("testCaseStartedId") == case_started.get("id"), case_finished
    assert case_finished.get("willBeRetried") is False, case_finished

    pickle_messages = [envelope["pickle"] for envelope in envelopes if isinstance(envelope.get("pickle"), dict)]
    test_case_messages = [
        envelope["testCase"]
        for envelope in envelopes
        if isinstance(envelope.get("testCase"), dict)
    ]
    assert len(pickle_messages) == len(test_case_messages) == 1, (pickle_messages, test_case_messages)
    assert pickle_messages[0].get("name") == "Session hook scenario", pickle_messages[0]
    assert test_case_messages[0].get("pickleId") == pickle_messages[0].get("id"), test_case_messages[0]

    step_starts = [
        (index, envelope["testStepStarted"])
        for index, envelope in enumerate(envelopes)
        if isinstance(envelope.get("testStepStarted"), dict)
    ]
    step_finishes = [
        (index, envelope["testStepFinished"])
        for index, envelope in enumerate(envelopes)
        if isinstance(envelope.get("testStepFinished"), dict)
    ]
    assert len(step_starts) == len(step_finishes) == 1, (step_starts, step_finishes)
    step_start_index, step_started = step_starts[0]
    step_finish_index, step_finished = step_finishes[0]
    assert step_started.get("testCaseStartedId") == case_started.get("id"), step_started
    assert step_finished.get("testCaseStartedId") == case_started.get("id"), step_finished
    assert step_started.get("testStepId") == step_finished.get("testStepId"), (step_started, step_finished)
    step_result = step_finished.get("testStepResult")
    assert isinstance(step_result, dict) and step_result.get("status") == "PASSED", step_finished

    run_start_index = next(index for index, envelope in enumerate(envelopes) if "testRunStarted" in envelope)
    run_finish_index = next(index for index, envelope in enumerate(envelopes) if "testRunFinished" in envelope)
    before_start = run_hook_start_positions["BEFORE_TEST_RUN"]
    before_finish = run_hook_finish_positions["BEFORE_TEST_RUN"]
    after_start = run_hook_start_positions["AFTER_TEST_RUN"]
    after_finish = run_hook_finish_positions["AFTER_TEST_RUN"]
    assert (
        run_start_index
        < before_start
        < before_finish
        < case_start_index
        < step_start_index
        < step_finish_index
        < case_finish_index
        < after_start
        < after_finish
        < run_finish_index
    ), {
        "positions": {
            "run_start": run_start_index,
            "before_start": before_start,
            "before_finish": before_finish,
            "case_start": case_start_index,
            "step_start": step_start_index,
            "step_finish": step_finish_index,
            "case_finish": case_finish_index,
            "after_start": after_start,
            "after_finish": after_finish,
            "run_finish": run_finish_index,
        }
    }


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve pytest session run-hook fixtures'
    )
)
def consumer_allure_pytest_session_run_hook_fixtures(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), result
    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    assert result.get("name") == "Session hook scenario", result
    assert result.get("status") == "passed", result
    assert result.get("stage") == "finished", result
    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 1, result
    assert isinstance(steps[0], dict), steps
    assert steps[0].get("name") in {
        "the pytest session hook scenario passes",
        "Given the pytest session hook scenario passes",
    }, steps[0]
    assert steps[0].get("status") == "passed", steps[0]

    containers = _assert_allure_container_result_links(result_directory, {result_uuid})
    shared_container = _assert_allure_shared_run_hook_container(containers, {result_uuid})
    expected_fixtures = {
        "befores": "pytest session start",
        "afters": "pytest session finish",
    }
    for fixture_group_name, fixture_name in expected_fixtures.items():
        fixtures = shared_container.get(fixture_group_name)
        assert isinstance(fixtures, list) and len(fixtures) == 1, shared_container
        fixture = fixtures[0]
        assert isinstance(fixture, dict), fixture
        assert fixture.get("name") == fixture_name, fixture
        assert fixture.get("status") == "passed", fixture
        assert fixture.get("stage") == "finished", fixture
        assert type(fixture.get("start")) is int and type(fixture.get("stop")) is int, fixture
        assert fixture["start"] <= fixture["stop"], fixture


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should satisfy the result and container required-field '
        r'contract'
    )
)
def consumer_allure_result_and_container_field_contract(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert result_files, f"expected Allure result files in {result_directory}"

    # AllureFileLogger chooses independent filename prefixes; UUID fields link results and containers.
    result_ids: set[str] = set()
    for result_file in result_files:
        result = json.loads(result_file.read_text(encoding="utf-8"))
        assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
        for field in ("uuid", "name", "fullName", "testCaseId", "historyId", "stage"):
            assert isinstance(result.get(field), str) and result[field], result
        assert result.get("status") in {"passed", "failed", "broken", "skipped", "unknown"}, result
        for field in ("steps", "labels", "parameters"):
            assert isinstance(result.get(field), list), result
        for field in ("start", "stop"):
            assert type(result.get(field)) is int, result
        assert result["start"] <= result["stop"], result
        result_ids.add(result["uuid"])
        _assert_allure_attachment_sources(result, result_directory)

    containers = _assert_allure_container_result_links(result_directory, result_ids)
    _assert_allure_shared_run_hook_container(containers, result_ids)
    for container in containers:
        for field in ("befores", "afters"):
            fixtures = container.get(field, [])
            assert isinstance(fixtures, list), container
            for fixture_result in fixtures:
                assert isinstance(fixture_result, dict), fixture_result
                for fixture_field in ("name", "stage"):
                    assert (
                        isinstance(fixture_result.get(fixture_field), str) and fixture_result[fixture_field]
                    ), fixture_result
                assert fixture_result.get("status") in {"passed", "failed", "broken", "skipped", "unknown"}, (
                    fixture_result
                )
                for fixture_field in ("start", "stop"):
                    assert type(fixture_result.get(fixture_field)) is int, fixture_result
                assert fixture_result["start"] <= fixture_result["stop"], fixture_result
        _assert_allure_attachment_sources(container, result_directory)


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

    _assert_allure_container_result_links(result_directory, {result_uuid})


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
    attachment_path = _consumer_allure_attachment_file(result_directory, reference)

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

    _assert_allure_container_result_links(result_directory, {result_uuid})


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
    attachment_path = _consumer_allure_attachment_file(result_directory, reference)
    expected_diagnostics = {"success": False}
    expected_bytes = (json.dumps(expected_diagnostics, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
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


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^\"]+)" should preserve run-level fallback '
        r'attachment "(?P<attachment_name>[^\"]+)" of type "(?P<media_type>[^\"]+)" with bytes '
        r'"(?P<body>[^\"]+)"'
    )
)
def consumer_allure_run_level_fallback_attachment(
    relative_path: str,
    attachment_name: str,
    media_type: str,
    body: str,
    consumer: ConsumerProject,
) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    assert result.get("name") == "Run fallback scenario", result

    references = result.get("attachments")
    assert isinstance(references, list) and len(references) == 1, result
    reference = references[0]
    assert isinstance(reference, dict), reference
    assert reference.get("name") == attachment_name, reference
    assert reference.get("type") == media_type, reference
    attachment_path = _consumer_allure_attachment_file(result_directory, reference)
    source = reference["source"]
    relative_source = PurePosixPath(source)
    assert (
        not relative_source.is_absolute()
        and len(relative_source.parts) >= 2
        and relative_source.parts[0] == "attachments"
    ), reference
    assert attachment_path.read_bytes() == body.encode("utf-8"), reference


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^\"]+)" should preserve JSON attachment '
        r'"(?P<file_name>[^\"]+)" for testCaseId "(?P<case_id>[^\"]+)" as an unmapped fallback from '
        r'"(?P<messages_path>[^\"]+)"'
    )
)
def consumer_allure_unmapped_case_fallback_attachment(
    relative_path: str,
    file_name: str,
    case_id: str,
    messages_path: str,
    consumer: ConsumerProject,
) -> None:
    media_type = "application/vnd.pytest-bdd.launch+json"
    messages_file = _consumer_artifact_path(messages_path, consumer)
    matching_messages: list[dict[str, Any]] = []
    test_case_ids: set[str] = set()
    for line in messages_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        assert isinstance(payload, dict), payload
        test_case = payload.get("testCase")
        if isinstance(test_case, dict) and isinstance(test_case.get("id"), str):
            test_case_ids.add(test_case["id"])
        attachment = payload.get("attachment")
        if isinstance(attachment, dict) and attachment.get("fileName") == file_name:
            matching_messages.append(attachment)

    assert len(test_case_ids) == 1, test_case_ids
    assert len(matching_messages) == 1, matching_messages
    input_attachment = matching_messages[0]
    assert input_attachment.get("testCaseStartedId") is None, input_attachment
    assert input_attachment.get("mediaType") == media_type, input_attachment
    assert input_attachment.get("contentEncoding") == "IDENTITY", input_attachment
    body = input_attachment.get("body")
    assert isinstance(body, str), input_attachment
    body_payload = json.loads(body)
    assert isinstance(body_payload, dict), body_payload
    assert body_payload.get("testCaseId") == case_id, body_payload

    result_directory = _consumer_artifact_path(relative_path, consumer)
    assert result_directory.is_dir(), f"Allure output directory was not created: {result_directory}"
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, f"expected one Allure result file, found {result_files!r}"
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
    assert result.get("name") == "Known scenario", result
    assert result.get("status") == "passed", result
    assert isinstance(result.get("testCaseId"), str) and result["testCaseId"], result

    references = result.get("attachments")
    assert isinstance(references, list) and len(references) == 1, result
    reference = references[0]
    assert isinstance(reference, dict), reference
    assert reference.get("name") == f"Cucumber unmapped testCaseId '{case_id}' fallback: {file_name}", reference
    assert reference.get("type") == media_type, reference
    attachment_path = _consumer_allure_attachment_file(result_directory, reference)
    source = reference["source"]
    relative_source = PurePosixPath(source)
    assert (
        not relative_source.is_absolute()
        and len(relative_source.parts) >= 2
        and relative_source.parts[0] == "attachments"
    ), reference
    actual_bytes = attachment_path.read_bytes()
    assert actual_bytes == body.encode("utf-8"), reference
    actual_payload = json.loads(actual_bytes)
    assert isinstance(actual_payload, dict), actual_payload
    assert actual_payload.get("testCaseId") == case_id, actual_payload


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
    attachment_path = _consumer_allure_attachment_file(result_directory, reference)
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

    containers = _assert_allure_container_result_links(result_directory, {result_uuid})
    _assert_allure_shared_run_hook_container(containers, {result_uuid})


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
    internal_attachment_types = {_IDE_LAUNCH_MEDIA_TYPE, _IDE_STEP_BINDING_MEDIA_TYPE}
    runtime_hierarchy_labels = {"feature", "parentSuite", "rule", "scenario", "suite"}

    def normalized(value: Any) -> Any:
        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                if key in {"uuid", "titlePath"}:
                    continue
                if key == "labels" and isinstance(item, list):
                    result[key] = [
                        normalized(label)
                        for label in item
                        if not (isinstance(label, dict) and label.get("name") in runtime_hierarchy_labels)
                    ]
                    continue
                if key == "parameters" and isinstance(item, list):
                    result[key] = [
                        normalized(parameter)
                        for parameter in item
                        if not (isinstance(parameter, dict) and parameter.get("name") == "pickleId")
                    ]
                    continue
                if key == "name" and isinstance(item, str):
                    result[key] = re.sub(r"^(?:Given|When|Then|And|But|\*)\s+", "", item)
                    continue
                if key == "attachments" and isinstance(item, list):
                    references: list[Any] = []
                    for reference in item:
                        if (
                            isinstance(reference, dict)
                            and reference.get("type") in internal_attachment_types
                        ):
                            references.append({"type": reference["type"]})
                        else:
                            references.append(normalized(reference))
                    result[key] = references
                else:
                    result[key] = normalized(item)
            return result
        if isinstance(value, list):
            return [normalized(item) for item in value]
        return value

    semantic_artifacts = []
    for relative_path in (first_path, second_path):
        result_directory = _consumer_artifact_path(relative_path, consumer)
        result_files = sorted(result_directory.glob("*-result.json"))
        assert len(result_files) == 1, f"expected one Allure result file in {relative_path!r}, found {result_files!r}"
        result = json.loads(result_files[0].read_text(encoding="utf-8"))
        assert isinstance(result, dict), f"Allure result must be a JSON object, got {type(result).__name__}"
        result_uuid = result.get("uuid")
        assert isinstance(result_uuid, str) and result_uuid, result

        result_ids = {result_uuid}
        containers = _assert_allure_container_result_links(result_directory, result_ids)
        _assert_allure_shared_run_hook_container(containers, result_ids)

        semantic_result = normalized(result)
        semantic_containers = []
        for container in containers:
            semantic_container = normalized(container)
            for field in ("name", "start", "stop"):
                semantic_container.pop(field, None)
            semantic_container.setdefault("befores", [])
            semantic_container.setdefault("afters", [])
            children = container["children"]
            semantic_container["children"] = ["<linked-result>" for _ in children]
            semantic_containers.append(semantic_container)
        semantic_containers.sort(key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
        semantic_artifacts.append((semantic_result, semantic_containers))

    assert semantic_artifacts[0] == semantic_artifacts[1], {
        first_path: semantic_artifacts[0],
        second_path: semantic_artifacts[1],
    }


@then(
    re.compile(
        r'consumer Allure result directories "(?P<first_path>[^\"]+)" and "(?P<second_path>[^\"]+)" '
        r'should preserve no-attempt Messages extensions for their scenarios from "(?P<messages_path>[^\"]+)"'
    )
)
def consumer_allure_no_attempt_message_extensions(
    first_path: str,
    second_path: str,
    messages_path: str,
    consumer: ConsumerProject,
) -> None:
    from collections import Counter

    @dataclass(frozen=True)
    class ScenarioIdentity:
        feature_file: str
        scenario_name: str

    extension_types = {_IDE_LAUNCH_MEDIA_TYPE, _IDE_STEP_BINDING_MEDIA_TYPE}
    messages_file = _consumer_artifact_path(messages_path, consumer)
    envelopes = [
        json.loads(line)
        for line in messages_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    pickle_scenarios = {
        pickle["id"]: ScenarioIdentity(
            feature_file=PurePosixPath(pickle["uri"].replace("\\", "/")).name,
            scenario_name=re.sub(r"\[table_rows:\[line: \d+\]\]$", "", pickle["name"]),
        )
        for envelope in envelopes
        if isinstance((pickle := envelope.get("pickle")), dict)
        and isinstance(pickle.get("id"), str)
        and isinstance(pickle.get("name"), str)
        and isinstance(pickle.get("uri"), str)
    }
    scenario_identity_by_case = {
        test_case["id"]: pickle_scenarios[test_case["pickleId"]]
        for envelope in envelopes
        if isinstance((test_case := envelope.get("testCase")), dict)
        and isinstance(test_case.get("id"), str)
        and isinstance(test_case.get("pickleId"), str)
        and test_case["pickleId"] in pickle_scenarios
    }
    case_ids_by_scenario: dict[ScenarioIdentity, set[str]] = defaultdict(set)
    for case_id, scenario_identity in scenario_identity_by_case.items():
        case_ids_by_scenario[scenario_identity].add(case_id)

    def semantic_payload(payload: dict[str, Any]) -> str:
        stable_payload = {key: value for key, value in payload.items() if key != "testCaseId"}
        return json.dumps(stable_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    expected_by_scenario: dict[ScenarioIdentity, Counter[tuple[str, str, str]]] = defaultdict(Counter)
    for envelope in envelopes:
        attachment = envelope.get("attachment")
        if not isinstance(attachment, dict) or attachment.get("testCaseStartedId") is not None:
            continue
        media_type = attachment.get("mediaType")
        if media_type not in extension_types:
            continue
        body = attachment.get("body")
        assert isinstance(body, str), attachment
        payload = json.loads(body)
        assert isinstance(payload, dict), payload
        case_id = payload.get("testCaseId")
        assert isinstance(case_id, str) and case_id in scenario_identity_by_case, payload
        scenario_identity = scenario_identity_by_case[case_id]
        expected_by_scenario[scenario_identity][(media_type, case_id, semantic_payload(payload))] += 1

    assert expected_by_scenario, f"no no-attempt pytest-cuke extension attachments were found in {messages_path!r}"
    for scenario_identity, expected in expected_by_scenario.items():
        assert {media_type for media_type, _case_id, _payload in expected} == extension_types, {
            scenario_identity: expected
        }

    for relative_path in (first_path, second_path):
        result_directory = _consumer_artifact_path(relative_path, consumer)
        result_files = sorted(result_directory.glob("*-result.json"))
        assert len(result_files) == len(expected_by_scenario), (relative_path, result_files, expected_by_scenario)
        actual_by_scenario: dict[ScenarioIdentity, Counter[tuple[str, str, str]]] = defaultdict(Counter)

        for result_file in result_files:
            result = json.loads(result_file.read_text(encoding="utf-8"))
            assert isinstance(result, dict), result
            full_name = result.get("fullName")
            assert isinstance(full_name, str), result
            matching_scenarios = [
                identity
                for identity in expected_by_scenario
                if full_name.endswith(f"{identity.feature_file}:{identity.scenario_name}")
            ]
            assert len(matching_scenarios) == 1, (relative_path, result, expected_by_scenario)
            scenario_identity = matching_scenarios[0]
            result_case_id = result.get("testCaseId")
            assert isinstance(result_case_id, str) and result_case_id, result
            assert scenario_identity not in actual_by_scenario, (relative_path, result)

            attachment_references: list[Any] = []

            def collect_attachments(value: Any, references: list[Any]) -> None:
                if isinstance(value, dict):
                    nested_references = value.get("attachments")
                    if isinstance(nested_references, list):
                        references.extend(nested_references)
                    for nested_value in value.values():
                        collect_attachments(nested_value, references)
                elif isinstance(value, list):
                    for nested_value in value:
                        collect_attachments(nested_value, references)

            collect_attachments(result, attachment_references)
            for reference in attachment_references:
                if not isinstance(reference, dict) or reference.get("type") not in extension_types:
                    continue
                attachment_path = _consumer_allure_attachment_file(result_directory, reference)
                payload = json.loads(attachment_path.read_text(encoding="utf-8"))
                assert isinstance(payload, dict), payload
                message_case_id = payload.get("testCaseId")
                assert message_case_id in case_ids_by_scenario[scenario_identity], (
                    relative_path,
                    result,
                    reference,
                    payload,
                )
                actual_by_scenario[scenario_identity][
                    (reference["type"], message_case_id, semantic_payload(payload))
                ] += 1

        assert dict(actual_by_scenario) == dict(expected_by_scenario), {
            relative_path: dict(actual_by_scenario),
            messages_path: dict(expected_by_scenario),
        }


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve failed diagnostics, '
        r"portable attachments, and linked containers"
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
        attachment_path = _consumer_allure_attachment_file(result_directory, reference)
        assert attachment_path.read_bytes() == expected_content, reference
    assert seen_names == set(expected_files), references

    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    containers = _assert_allure_container_result_links(result_directory, {result_uuid})
    _assert_allure_shared_run_hook_container(containers, {result_uuid})


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

    result_ids = set(results_by_uuid)
    containers = _assert_allure_container_result_links(result_directory, result_ids)
    shared_container = _assert_allure_shared_run_hook_container(containers, result_ids)
    assert set(shared_container["children"]) == result_ids, shared_container


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve the Background step before '
        r"scenario steps and linked containers"
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

    containers = _assert_allure_container_result_links(result_directory, {result_uuid})
    _assert_allure_shared_run_hook_container(containers, {result_uuid})


@then(
    re.compile(
        r'consumer Allure result directory "(?P<relative_path>[^"]+)" should preserve the failed Background step '
        r'diagnostic, order, and linked containers'
    )
)
def consumer_allure_failed_background_step(relative_path: str, consumer: ConsumerProject) -> None:
    result_directory = _consumer_artifact_path(relative_path, consumer)
    result_files = sorted(result_directory.glob("*-result.json"))
    assert len(result_files) == 1, result_files
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert isinstance(result, dict), result
    result_uuid = result.get("uuid")
    assert isinstance(result_uuid, str) and result_uuid, result
    assert result_files[0].name == f"{result_uuid}-result.json", result
    assert result.get("name") == "Save Ada's order", result
    assert result.get("status") == "failed", result
    assert result.get("stage") == "finished", result
    result_details = result.get("statusDetails")
    assert isinstance(result_details, dict), result
    assert result_details.get("message") == "background failure sentinel", result_details
    result_trace = result_details.get("trace")
    assert isinstance(result_trace, str) and "AssertionError: background failure sentinel" in result_trace, result_details

    steps = result.get("steps")
    assert isinstance(steps, list) and len(steps) == 4, result
    assert all(isinstance(step, dict) for step in steps), steps
    assert [step.get("name") for step in steps] == [
        "the shop is open",
        "the inventory reconciliation fails",
        "the customer is Ada",
        "the order is saved",
    ], steps
    assert steps[0].get("status") == "passed", steps[0]
    failed_background_step = steps[1]
    assert failed_background_step.get("status") == "failed", failed_background_step
    step_details = failed_background_step.get("statusDetails")
    assert isinstance(step_details, dict), failed_background_step
    assert step_details.get("message") == "background failure sentinel", step_details
    step_trace = step_details.get("trace")
    assert isinstance(step_trace, str) and "AssertionError: background failure sentinel" in step_trace, step_details
    assert all(step.get("status") != "passed" for step in steps[2:]), steps

    containers = _assert_allure_container_result_links(result_directory, {result_uuid})
    _assert_allure_shared_run_hook_container(containers, {result_uuid})


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


@then(
    re.compile(
        r'the capability report should cover IDs from consumer files '
        r'"(?P<mandatory_path>[^"]+)" and "(?P<runtime_required_path>[^"]+)"'
    )
)
def consumer_capability_report_covers_policy_ids(
    mandatory_path: str,
    runtime_required_path: str,
    consumer: ConsumerProject,
) -> None:
    result = consumer.command_result
    assert result is not None, "a capability report command has not been run"
    report = json.loads(result.stdout)
    assert isinstance(report, dict), report

    def ids_from_consumer_file(relative_path: str) -> set[str]:
        scope_file = _consumer_artifact_path(relative_path, consumer)
        assert scope_file.is_file(), f"capability scope file is missing: {relative_path}"
        return {
            line.strip()
            for line in scope_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

    mandatory_ids = ids_from_consumer_file(mandatory_path)
    runtime_required_ids = ids_from_consumer_file(runtime_required_path)
    assert mandatory_ids, f"mandatory capability scope is empty: {mandatory_path}"
    assert runtime_required_ids, f"runtime-required capability scope is empty: {runtime_required_path}"
    scope = report.get("scope")
    assert isinstance(scope, dict), report
    reported_mandatory = scope.get("mandatory_capability_ids")
    reported_runtime_required = scope.get("runtime_required_capability_ids")
    assert isinstance(reported_mandatory, list), scope
    assert isinstance(reported_runtime_required, list), scope
    assert mandatory_ids <= set(reported_mandatory), (mandatory_ids, reported_mandatory)
    assert runtime_required_ids <= set(reported_runtime_required), (runtime_required_ids, reported_runtime_required)

    capabilities = report.get("capabilities")
    assert isinstance(capabilities, list), report
    rows_by_id = {
        row["capability_id"]: row
        for row in capabilities
        if isinstance(row, dict) and isinstance(row.get("capability_id"), str)
    }
    expected_ids = mandatory_ids | runtime_required_ids
    assert expected_ids <= rows_by_id.keys(), (expected_ids - rows_by_id.keys())

    observations = report.get("observations")
    assert isinstance(observations, dict), report
    observed_ids = observations.get("capability_ids")
    assert isinstance(observed_ids, list), observations
    assert runtime_required_ids <= set(observed_ids), (runtime_required_ids, observed_ids)
    for capability_id in mandatory_ids:
        assert rows_by_id[capability_id].get("mandatory") is True, rows_by_id[capability_id]
        assert rows_by_id[capability_id].get("status") == "Implemented", rows_by_id[capability_id]
    for capability_id in runtime_required_ids:
        assert rows_by_id[capability_id].get("runtime_required") is True, rows_by_id[capability_id]
        assert rows_by_id[capability_id].get("observed_runtime") is True, rows_by_id[capability_id]

    decisions = report.get("decisions")
    assert isinstance(decisions, list), report
    decision_ids = {
        decision.get("capability_id")
        for decision in decisions
        if isinstance(decision, dict) and isinstance(decision.get("capability_id"), str)
    }
    assert mandatory_ids <= decision_ids, (mandatory_ids - decision_ids, decisions)


@then(
    re.compile(
        r'the report should show the v28 non-runtime classification for "(?P<capability_id>[^"]+)" '
        r"and actionable unresolved IDs"
    )
)
def consumer_capability_report_shows_non_runtime_classification_and_gaps(
    capability_id: str,
    consumer: ConsumerProject,
) -> None:
    result = consumer.command_result
    assert result is not None, "a capability report command has not been run"
    report = json.loads(result.stdout)
    assert isinstance(report, dict), report
    assert report.get("baseline_release") == "28.0.0", report

    observations = report.get("observations")
    assert isinstance(observations, dict), report
    assert observations.get("source_kind") == "runtime", observations

    gates = report.get("gates")
    assert isinstance(gates, dict), report
    assert gates.get("passed") is False, gates
    failures = gates.get("failures")
    assert isinstance(failures, list), gates
    failure_prefix = "require-non-runtime-classified: missing explicit classifications for: "
    matching_failures = [
        failure for failure in failures if isinstance(failure, str) and failure.startswith(failure_prefix)
    ]
    assert len(matching_failures) == 1, failures
    missing_ids = matching_failures[0][len(failure_prefix) :].split(", ")
    assert missing_ids and all(missing_ids), matching_failures[0]
    assert missing_ids == sorted(set(missing_ids)), missing_ids
    assert capability_id not in missing_ids, missing_ids

    capabilities = report.get("capabilities")
    assert isinstance(capabilities, list), report
    rows_by_id = {
        row["capability_id"]: row
        for row in capabilities
        if isinstance(row, dict) and isinstance(row.get("capability_id"), str)
    }
    assert capability_id in rows_by_id, capabilities
    classified_row = rows_by_id[capability_id]
    assert classified_row.get("status") == "Not-Applicable", classified_row
    assert classified_row.get("runtime_required") is False, classified_row
    assert classified_row.get("observed_runtime") is False, classified_row
    rationale = classified_row.get("comment")
    assert isinstance(rationale, str) and "testRunHookStartedId" in rationale, classified_row

    decisions = report.get("decisions")
    assert isinstance(decisions, list), report
    matching_decisions = [
        decision
        for decision in decisions
        if isinstance(decision, dict) and decision.get("capability_id") == capability_id
    ]
    assert matching_decisions == [
        {
            "capability_id": capability_id,
            "comment": rationale,
            "release_target": "28.0.0",
            "status": "Not-Applicable",
        }
    ], matching_decisions

    runtime_scope = report.get("scope")
    assert isinstance(runtime_scope, dict), report
    runtime_required_ids = runtime_scope.get("runtime_required_capability_ids")
    assert isinstance(runtime_required_ids, list), runtime_scope
    assert capability_id not in runtime_required_ids, runtime_required_ids
    summary = report.get("summary")
    assert isinstance(summary, dict), report
    assert summary.get("non_runtime_classified", 0) >= 1, summary

    for missing_id in missing_ids:
        row = rows_by_id.get(missing_id)
        assert row is not None, (missing_id, rows_by_id.keys())
        assert row.get("relevance") == "relevant", row
        assert row.get("runtime_required") is False, row
        assert row.get("observed_runtime") is False, row
        assert row.get("status") == "Pending", row


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


@then("the Markdown capability report should list observations and decisions in stable order")
def consumer_markdown_capability_report_is_stably_ordered(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a standalone capability report command has not been run"
    lines = result.stdout.splitlines()

    def section_lines(title: str, next_title: str) -> list[str]:
        try:
            start = lines.index(title) + 1
            end = lines.index(next_title, start)
        except ValueError as error:
            raise AssertionError(f"Markdown capability report is missing {title!r} or {next_title!r}: {result.stdout}") from error
        return lines[start:end]

    observed_lines = section_lines("## Observed fields", "## Decisions")
    observed_ids = [match.group(1) for line in observed_lines if (match := re.fullmatch(r"- `([^`]+)`", line))]
    assert observed_ids == sorted(set(observed_ids)), observed_ids

    decision_lines = section_lines("## Decisions", "## Gate result")
    decision_ids = [
        match.group(1)
        for line in decision_lines
        if (match := re.match(r"\| `([^`]+)` \|", line))
    ]
    assert decision_ids == sorted(set(decision_ids)), decision_ids


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
    try:
        exists = (consumer.path / destination).exists()
    except OSError as error:
        if error.errno != errno.ENAMETOOLONG and getattr(error, "winerror", None) != 206:
            raise
        exists = False
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
    if not is_sub and os.name != "nt":
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


@then("pytest outcome must contain tests with statuses:")
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
    re.compile(r"Copy \"(?P<initial_path>[^\"]+)\" into \"(?P<final_path>[^\"]+)\""),
    converters={"initial_path": Path, "final_path": Path},
)
@given(
    re.compile(r"Copy path from \"(?P<initial_path>[^\"]+)\" to test path \"(?P<final_path>[^\"]+)\""),
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


@then(
    re.compile(
        r'Messages report file "(?P<file_path>[^"]+)" contains one complete successful run with one scenario and one passed step'
    ),
    converters={"file_path": Path},
)
def _(file_path: Path, testdir) -> None:
    from pytest_cuke.model.message_types import GherkinDocument, Meta, Pickle, Source
    from pytest_cuke.model.message_types import TestCase, TestCaseFinished, TestCaseStarted, TestRunFinished
    from pytest_cuke.model.message_types import TestRunStarted, TestStepFinished, TestStepStarted

    artifact_path = Path(str(testdir.tmpdir)) / file_path
    assert artifact_path.is_file(), f"Messages report was not written: {artifact_path}"

    payload_types = (
        ("meta", Meta),
        ("source", Source),
        ("gherkin_document", GherkinDocument),
        ("pickle", Pickle),
        ("test_case", TestCase),
        ("test_run_started", TestRunStarted),
        ("test_run_finished", TestRunFinished),
        ("test_case_started", TestCaseStarted),
        ("test_case_finished", TestCaseFinished),
        ("test_step_started", TestStepStarted),
        ("test_step_finished", TestStepFinished),
    )
    payloads = {name: [] for name, _ in payload_types}
    positions = {name: [] for name, _ in payload_types}
    line_count = 0

    with artifact_path.open(mode="r", encoding="utf-8") as report:
        for position, raw_line in enumerate(report):
            line_count = position + 1
            assert raw_line.strip(), f"Messages report has a blank line at {position + 1}"
            envelope = _validate_messages_envelope_compatibly(json.loads(raw_line))
            for name, _ in payload_types:
                payload = getattr(envelope, name)
                if payload is not None:
                    payloads[name].append(payload)
                    positions[name].append(position)

    for name, payload_type in payload_types:
        assert len(payloads[name]) == 1, f"expected one {name} envelope, got {len(payloads[name])}"
        assert isinstance(payloads[name][0], payload_type), payloads[name][0]

    meta = payloads["meta"][0]
    source = payloads["source"][0]
    gherkin_document = payloads["gherkin_document"][0]
    pickle = payloads["pickle"][0]
    test_case = payloads["test_case"][0]
    run_finished = payloads["test_run_finished"][0]
    case_started = payloads["test_case_started"][0]
    case_finished = payloads["test_case_finished"][0]
    step_started = payloads["test_step_started"][0]
    step_finished = payloads["test_step_finished"][0]

    assert meta.protocol_version and source.uri
    assert gherkin_document.feature is not None
    assert len(pickle.steps) == 1, pickle.steps
    assert len(test_case.test_steps) == 1, test_case.test_steps
    test_step = test_case.test_steps[0]
    assert test_case.pickle_id == pickle.id
    assert test_step.pickle_step_id == pickle.steps[0].id
    assert case_started.test_case_id == test_case.id
    assert case_finished.test_case_started_id == case_started.id
    assert step_started.test_case_started_id == case_started.id
    assert step_finished.test_case_started_id == case_started.id
    assert step_started.test_step_id == test_step.id
    assert step_finished.test_step_id == test_step.id
    assert step_finished.test_step_result.status.value == "PASSED"
    assert case_finished.will_be_retried is False
    assert run_finished.success is True
    assert (
        positions["test_run_started"][0]
        < positions["test_case_started"][0]
        < positions["test_step_started"][0]
        < positions["test_step_finished"][0]
        < positions["test_case_finished"][0]
        < positions["test_run_finished"][0]
    )
    assert positions["test_run_finished"][0] == line_count - 1, "test_run_finished must terminate the stream"


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
def runtime_type_gate_passes_with_policy_identity(
    request: Any,
    typecheck_result: subprocess.CompletedProcess[str],
) -> None:
    output = f"{typecheck_result.stdout}\n{typecheck_result.stderr}"
    assert typecheck_result.returncode == 0, output
    config = tomllib.loads((Path(request.config.rootpath) / "pyproject.toml").read_text(encoding="utf-8"))
    checker_version = config["tool"]["pytest-cuke"]["typecheck"]["checker_version"]
    assert f"MYPY_VERSION={checker_version}" in output, output
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
    match = re.search(r"\b(\d+) passed\b", _consumer_batch_output(result))
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
            "pytest-xdist<4",
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
    environment = _consumer_environment()
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


@given("the installed consumer registers the run-aware lifecycle extension plugin")
def install_run_aware_lifecycle_extension(consumer: ConsumerProject) -> None:
    (consumer.path / "conftest.py").write_text(
        dedent(
            '''\
            pytest_plugins = ["run_aware_plugin"]

            from pytest_cuke import given, parsers, then, when


            def _record_body(label):
                with open("run-aware-body-effects.log", "a", encoding="utf-8") as stream:
                    stream.write(label + "\\n")


            @given(parsers.parse('the first run-aware step records "{label}"'))
            def first_run_aware_step(label):
                _record_body(label)
                return label


            @when(parsers.parse('the next run-aware step records "{label}"'))
            def next_run_aware_step(label):
                _record_body(label)
                return label


            @when(parsers.parse('the custom caller step records "{label}"'), target_fixture="custom_middle")
            def custom_caller_step(label):
                _record_body(label)
                return label


            @when(parsers.parse('the run-aware body raises "{message}"'))
            def run_aware_body_raises(message):
                _record_body("body-before-error")
                raise AssertionError(message)


            @when(parsers.parse('a replaceable run-aware step receives "{label}"'))
            def replaceable_run_aware_step(label):
                _record_body("original-replaceable-body")
                return label


            @when("the observer hook raises")
            def observer_hook_raises():
                _record_body("hook-body-must-not-run")


            @then(parsers.parse('the last run-aware step records "{label}"'))
            def last_run_aware_step(label, custom_middle):
                if label == "custom-end":
                    assert custom_middle == "custom-middle"
                else:
                    assert custom_middle is None
                with open("run-aware-target-fixtures.log", "a", encoding="utf-8") as stream:
                    stream.write(f"{label}={custom_middle!r}\\n")
                _record_body(label)
                return label


            def pytest_collection_modifyitems(items):
                items.sort(key=lambda item: "pytest_cuke_scenario" not in [
                    marker.name for marker in item.iter_markers()
                ])
            '''
        ),
        encoding="utf-8",
    )
    (consumer.path / "run_aware_plugin.py").write_text(
        dedent(
            '''\
            from __future__ import annotations

            import json
            import os
            from pathlib import Path
            from typing import Any

            from pytest import hookimpl


            _sequence = 0
            _replacement_payload = {}


            def _step_name(value: Any) -> str | None:
                if value is None:
                    return None
                step = getattr(value, "step", value)
                return getattr(step, "name", getattr(step, "text", None))


            def _step_index(run, step):
                scenario = run.scenario
                if scenario is None or step is None:
                    return None
                return next(
                    (index for index, candidate in enumerate(scenario.steps) if candidate == step),
                    None,
                )


            def _record(event, run, *, request=None, step=None, previous_step=None,
                        step_func=None, step_func_args=None, step_definition=None,
                        exception=None, selection=None):
                global _sequence
                _sequence += 1
                current = run.step
                previous = run.previous_step
                definition_func = getattr(step_definition, "func", None)
                row = {
                    "sequence": _sequence,
                    "event": event,
                    "run_id": run.run_id,
                    "run_identity": id(run),
                    "worker_id": run.worker_id,
                    "request_nodeid": request.node.nodeid if request is not None else None,
                    "feature_name": getattr(run.feature, "name", None),
                    "scenario_name": getattr(run.scenario, "name", None),
                    "stage": run.stage,
                    "hook_phase": run.hook_phase,
                    "status": run.status,
                    "transition_index": run.transition_index,
                    "step_name": _step_name(step),
                    "previous_step_name": _step_name(previous_step) or _step_name(run.previous_step),
                    "context_step_name": _step_name(run.step),
                    "context_previous_step_name": _step_name(run.previous_step),
                    "current_step_index": _step_index(run, current),
                    "previous_step_index": _step_index(run, previous),
                    "scenario_status": run.status,
                    "step_func": getattr(step_func, "__name__", None),
                    "step_func_identity": id(step_func) if step_func is not None else None,
                    "step_func_args": step_func_args,
                    "step_definition_func": getattr(definition_func, "__name__", None),
                    "step_definition_identity": id(step_definition) if step_definition is not None else None,
                    "step_definition_func_identity": id(definition_func) if definition_func is not None else None,
                    "exception_type": type(exception).__name__ if exception is not None else None,
                    "exception_message": str(exception) if exception is not None else None,
                    "selection": selection,
                }
                worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
                with Path(f"run-aware-{worker}.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, sort_keys=True, default=repr) + "\\n")


            @hookimpl
            def pytest_cuke_before_scenario(request, run):
                _record("before_scenario", run, request=request)


            @hookimpl
            def pytest_cuke_run_scenario(request, run):
                _record("run_scenario", run, request=request)


            @hookimpl
            def pytest_cuke_after_scenario(run):
                _record("after_scenario", run)


            @hookimpl
            def pytest_cuke_before_step(request, run, step_func):
                step = run.step
                _record("before_step", run, request=request, step=step, step_func=step_func)
                if _step_name(step) == "the observer hook raises":
                    raise RuntimeError("observer hook failure sentinel")


            @hookimpl
            def pytest_cuke_before_step_call(run, step_func, step_func_args, step_definition):
                _record("before_step_call", run, step=run.step, step_func=step_func,
                        step_func_args=step_func_args, step_definition=step_definition)
                if _step_name(run.step) == 'a replaceable run-aware step receives "callable payload sentinel"':
                    def replacement_callable(label):
                        actual_kwargs = {"label": label}
                        _record("replacement_callable", run, step=run.step,
                                step_func=replacement_callable, step_func_args=actual_kwargs,
                                step_definition=step_definition)
                        raise RuntimeError("replacement callable failure sentinel")

                    step_definition.func = replacement_callable
                    _replacement_payload.update(
                        definition=step_definition,
                        callable=replacement_callable,
                        kwargs=step_func_args,
                    )
                    _record("replacement_installed", run, step=run.step,
                            step_func=replacement_callable, step_func_args=step_func_args,
                            step_definition=step_definition)


            @hookimpl
            def pytest_cuke_after_step(run):
                _record("after_step", run, step=run.step)


            @hookimpl
            def pytest_cuke_step_error(
                request, run, step_func, step_func_args, exception, step_definition, tolerated
            ):
                selection = "tolerated" if tolerated else "ordinary"
                if _step_name(run.step) == 'a replaceable run-aware step receives "callable payload sentinel"':
                    assert step_definition is _replacement_payload["definition"]
                    assert step_func is step_definition.func is _replacement_payload["callable"]
                    assert isinstance(step_func_args, dict)
                    assert step_func_args is _replacement_payload["kwargs"]
                    assert step_func_args == {"label": "callable payload sentinel"}
                    assert isinstance(exception, RuntimeError)
                    assert str(exception) == "replacement callable failure sentinel"
                    selection = "replacement_payload_matches"
                _record("step_error", run, request=request, step=run.step, step_func=step_func,
                        step_func_args=step_func_args, step_definition=step_definition,
                        exception=exception, selection=selection)


            @hookimpl
            def pytest_cuke_step_func_lookup_error(request, run, exception):
                _record("lookup_error", run, request=request, step=run.step, exception=exception)


            @hookimpl
            def pytest_cuke_match_step_definition_to_step(request, run):
                use_custom = (
                    getattr(run.scenario, "name", None) == "Custom dispatcher invokes run-step and caller"
                    and (_step_name(run.step) or "").startswith("the custom caller step records ")
                )
                step_definition = None
                if use_custom:
                    step_registry = request.getfixturevalue("step_registry")
                    matches = []
                    while step_registry is not None:
                        matches.extend(
                            definition
                            for definition in step_registry
                            if definition.func.__name__ == "custom_caller_step"
                        )
                        step_registry = step_registry.parent
                    assert len(matches) == 1, matches
                    step_definition = matches[0]
                _record("matcher", run, request=request, step=run.step, previous_step=run.previous_step,
                        step_definition=step_definition,
                        selection="custom" if use_custom else "default_fallback")
                return step_definition


            @hookimpl
            def pytest_cuke_get_step_caller(request, run, step_func, step_func_args, step_definition):
                step = run.step
                use_custom = (_step_name(step) or "").startswith("the custom caller step records ")
                if use_custom:
                    assert isinstance(step_func_args, dict)
                    assert step_func_args == {"label": "custom-middle"}
                if _step_name(step) == 'a replaceable run-aware step receives "callable payload sentinel"':
                    assert step_func is step_definition.func is _replacement_payload["callable"]
                    assert step_func_args is _replacement_payload["kwargs"]
                _record("caller", run, request=request, step=step, step_func=step_func,
                        step_func_args=step_func_args, step_definition=step_definition,
                        selection="custom" if use_custom else "default_fallback")
                if use_custom:
                    return lambda: step_func(**step_func_args)
                return None


            @hookimpl
            def pytest_cuke_get_step_dispatcher(request, run):
                use_custom = getattr(run.scenario, "name", None) == (
                    "Custom dispatcher invokes run-step and caller"
                )
                _record("dispatcher", run, request=request,
                        selection="custom" if use_custom else "default_fallback")
                if not use_custom:
                    return None

                def dispatch(left_steps):
                    while left_steps:
                        step = left_steps.popleft()
                        run.start_step(step)
                        request.config.hook.pytest_cuke_run_step(request=request, run=run)

                return dispatch
            '''
        ),
        encoding="utf-8",
    )


def _run_aware_consumer_rows(relative_path: str, consumer: ConsumerProject) -> list[dict[str, Any]]:
    artifact = _consumer_artifact_path(relative_path, consumer)
    assert artifact.is_file(), f"run-aware hook artifact {relative_path!r} does not exist"
    rows = [json.loads(line) for line in artifact.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert all(isinstance(row, dict) for row in rows), rows
    return rows


@given(re.compile(r'the staged E2E example "(?P<relative_path>[^"]+)" is copied to the installed consumer'))
def install_staged_e2e_example_in_consumer(relative_path: str, testdir: Any, consumer: ConsumerProject) -> None:
    source = Path(str(testdir.tmpdir)) / relative_path
    if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
        raise ValueError("staged E2E example paths must stay inside the test directory")
    assert source.is_dir(), f"the staged E2E example directory does not exist: {source}"
    destination = consumer.path / Path(relative_path).name
    shutil.copytree(source, destination, dirs_exist_ok=True)


@then(re.compile(r'consumer run-aware hook artifact "(?P<relative_path>[^"]+)" should show successful run transitions'))
def consumer_run_aware_successful_lifecycle(relative_path: str, consumer: ConsumerProject) -> None:
    rows = _run_aware_consumer_rows(relative_path, consumer)
    scenarios = {
        "Default dispatcher and caller fallbacks": ("default_fallback", ["alpha", "beta", "omega"]),
        "Custom dispatcher invokes run-step and caller": ("custom", ["custom-start", "custom-middle", "custom-end"]),
    }
    assert {row["scenario_name"] for row in rows} == set(scenarios), rows
    assert len({row["run_id"] for row in rows}) == 1, rows
    assert len({row["run_identity"] for row in rows}) == 1, rows

    for scenario_name, (dispatcher_selection, expected_labels) in scenarios.items():
        scenario_rows = [row for row in rows if row["scenario_name"] == scenario_name]
        events = [row["event"] for row in scenario_rows]
        assert events[0] == "before_scenario", scenario_rows
        assert (
            events.index("before_scenario") < events.index("dispatcher") < events.index("after_scenario")
        ), scenario_rows
        assert (
            events.index("before_scenario") < events.index("run_scenario") < events.index("after_scenario")
        ), scenario_rows
        assert events[-1] == "after_scenario", scenario_rows
        assert all(row["feature_name"] == "Run-aware lifecycle consumer" for row in scenario_rows)
        assert all(
            row["request_nodeid"]
            for row in scenario_rows
            if row["event"] in {"before_scenario", "run_scenario"}
        ), scenario_rows

        before_scenario = next(row for row in scenario_rows if row["event"] == "before_scenario")
        after_scenario = scenario_rows[-1]
        assert (before_scenario["stage"], before_scenario["hook_phase"], before_scenario["status"]) == (
            "setup",
            "pytest_cuke_before_scenario",
            "running",
        ), before_scenario
        assert (after_scenario["stage"], after_scenario["hook_phase"], after_scenario["status"]) == (
            "finished",
            "pytest_cuke_after_scenario",
            "passed",
        ), after_scenario
        assert after_scenario["request_nodeid"] is None, after_scenario

        dispatchers = [row for row in scenario_rows if row["event"] == "dispatcher"]
        assert len(dispatchers) == 1 and dispatchers[0]["selection"] == dispatcher_selection, dispatchers
        matcher_rows = [row for row in scenario_rows if row["event"] == "matcher"]
        caller_rows = [row for row in scenario_rows if row["event"] == "caller"]
        assert len(matcher_rows) == 3, matcher_rows
        if dispatcher_selection == "custom":
            selected_matchers = [row for row in matcher_rows if row["selection"] == "custom"]
            assert len(selected_matchers) == 1, matcher_rows
            selected_matcher = selected_matchers[0]
            assert selected_matcher["step_name"] == 'the custom caller step records "custom-middle"', (
                selected_matcher
            )
            assert selected_matcher["step_definition_func"] == "custom_caller_step", selected_matcher
            assert all(
                row["selection"] == ("custom" if row is selected_matcher else "default_fallback")
                for row in matcher_rows
            ), matcher_rows
        else:
            assert all(row["selection"] == "default_fallback" for row in matcher_rows)
        assert len(caller_rows) == 3, caller_rows
        if dispatcher_selection == "custom":
            assert [row["selection"] for row in caller_rows].count("custom") == 1, caller_rows
            custom_caller = next(row for row in caller_rows if row["selection"] == "custom")
            assert isinstance(custom_caller["step_func_args"], dict), custom_caller
            assert custom_caller["step_func_args"] == {"label": "custom-middle"}, custom_caller
        else:
            assert all(row["selection"] == "default_fallback" for row in caller_rows), caller_rows

        step_rows = [row for row in scenario_rows if row["event"] == "before_step"]
        call_rows = [row for row in scenario_rows if row["event"] == "before_step_call"]
        after_step_rows = [row for row in scenario_rows if row["event"] == "after_step"]
        assert len(step_rows) == len(call_rows) == len(after_step_rows) == 3, scenario_rows
        assert [row["current_step_index"] for row in step_rows] == [0, 1, 2], step_rows
        assert [row["current_step_index"] for row in call_rows] == [0, 1, 2], call_rows
        assert [row["current_step_index"] for row in after_step_rows] == [0, 1, 2], after_step_rows
        assert [row["step_func_args"]["label"] for row in call_rows] == expected_labels, call_rows
        assert all(row["step_func"] == row["step_definition_func"] for row in call_rows), call_rows
        target_fixture_value = "custom-middle" if dispatcher_selection == "custom" else None
        assert call_rows[-1]["step_func_args"]["custom_middle"] == target_fixture_value, call_rows[-1]
        assert all(row["request_nodeid"] is None for row in call_rows + after_step_rows), scenario_rows
        assert all(
            row["stage"] == "step-running"
            and row["hook_phase"] == "pytest_cuke_step_call"
            for row in call_rows
        ), call_rows
        assert all(
            row["stage"] == "step-running"
            and row["hook_phase"] == "pytest_cuke_after_step"
            for row in after_step_rows
        ), after_step_rows

        for index, row in enumerate(step_rows):
            expected_previous = None if index == 0 else step_rows[index - 1]["step_name"]
            assert row["context_step_name"] == row["step_name"], row
            assert (
                row["previous_step_name"]
                == row["context_previous_step_name"]
                == expected_previous
            ), row
            assert (row["stage"], row["hook_phase"], row["status"]) == (
                "step-running",
                "pytest_cuke_before_step",
                "running",
            ), row

            matching_events = [
                item["event"]
                for item in scenario_rows
                if item["step_name"] == row["step_name"]
                or item["context_step_name"] == row["step_name"]
            ]
            assert matching_events.index("matcher") < matching_events.index("before_step")
            assert matching_events.index("before_step") < matching_events.index("before_step_call")
            assert matching_events.index("before_step_call") < matching_events.index("caller")
            assert matching_events.index("caller") < matching_events.index("after_step")

        transition_indexes = [row["transition_index"] for row in scenario_rows]
        assert transition_indexes == sorted(transition_indexes), scenario_rows

    body_effects = _consumer_artifact_path("run-aware-body-effects.log", consumer).read_text(
        encoding="utf-8"
    ).splitlines()
    assert body_effects == [
        "alpha",
        "beta",
        "omega",
        "custom-start",
        "custom-middle",
        "custom-end",
    ], body_effects

    target_fixture_effects = _consumer_artifact_path("run-aware-target-fixtures.log", consumer).read_text(
        encoding="utf-8"
    ).splitlines()
    assert target_fixture_effects == ["omega=None", "custom-end='custom-middle'"], target_fixture_effects


@then(
    re.compile(
        r'consumer run-aware example artifact "(?P<relative_path>[^"]+)" should show all scenarios, lifecycle context, and the attachment'
    )
)
def consumer_run_aware_example_observations(relative_path: str, consumer: ConsumerProject) -> None:
    rows = _run_aware_consumer_rows(relative_path, consumer)
    scenarios = {
        "First scenario starts without a previous step": (
            [
                'the first hook step records "first-start"',
                'the next hook step records "first-middle"',
                'the final hook step records "first-end"',
            ],
            ["first-start", "first-middle", "first-end"],
        ),
        "Second scenario also starts without a previous step": (
            [
                'the first hook step records "second-start"',
                'the next hook step records "second-middle"',
                'the final hook step records "second-end"',
            ],
            ["second-start", "second-middle", "second-end"],
        ),
        "Attachment hooks receive the active run": (["the example attaches a report"], [None]),
    }
    assert {row["scenario_name"] for row in rows} == set(scenarios), rows
    assert all(row["feature_name"] == "Run-aware lifecycle hooks" for row in rows), rows
    assert len({row["run_id"] for row in rows}) == 1, rows

    for scenario_name, (expected_step_names, expected_labels) in scenarios.items():
        scenario_rows = [row for row in rows if row["scenario_name"] == scenario_name]
        assert scenario_rows[0]["event"] == "before_scenario", scenario_rows
        assert scenario_rows[-1]["event"] == "after_scenario", scenario_rows
        before_scenario = scenario_rows[0]
        after_scenario = scenario_rows[-1]
        assert (before_scenario["stage"], before_scenario["hook_phase"], before_scenario["status"]) == (
            "setup",
            "pytest_cuke_before_scenario",
            "running",
        ), before_scenario
        assert (after_scenario["stage"], after_scenario["hook_phase"], after_scenario["status"]) == (
            "finished",
            "pytest_cuke_after_scenario",
            "passed",
        ), after_scenario
        assert len([row for row in scenario_rows if row["event"] == "dispatcher_fallback"]) == 1, scenario_rows
        assert len([row for row in scenario_rows if row["event"] == "matcher_fallback"]) == len(
            expected_step_names
        ), scenario_rows
        assert len([row for row in scenario_rows if row["event"] == "caller_fallback"]) == len(
            expected_step_names
        ), scenario_rows

        steps = [row for row in scenario_rows if row["event"] == "before_step"]
        calls = [row for row in scenario_rows if row["event"] == "before_step_call"]
        after_steps = [row for row in scenario_rows if row["event"] == "after_step"]
        assert [row["step_name"] for row in steps] == expected_step_names, steps
        assert [row["step_name"] for row in calls] == expected_step_names, calls
        assert [row["current_step_index"] for row in steps] == list(range(len(expected_step_names))), steps
        for row, expected_label in zip(calls, expected_labels, strict=True):
            if expected_label is None:
                assert row["step_func_args"] == {"attach": "add_attachment"}, row
            else:
                assert row["step_func_args"]["label"] == expected_label, row
        assert all(row["step_func"] == row["step_definition_func"] for row in calls), calls
        assert [row["step_name"] for row in after_steps] == expected_step_names, after_steps

        for index, row in enumerate(steps):
            expected_previous = None if index == 0 else expected_step_names[index - 1]
            assert row["previous_step_name"] == expected_previous, row
            assert (row["stage"], row["hook_phase"], row["status"]) == (
                "step-running",
                "pytest_cuke_before_step",
                "running",
            ), row
        assert all(row["stage"] == "step-running" for row in calls + after_steps), scenario_rows
        assert [row["transition_index"] for row in scenario_rows] == sorted(
            row["transition_index"] for row in scenario_rows
        ), scenario_rows

    attachments = [row for row in rows if row["event"] == "attachment"]
    assert len(attachments) == 1, attachments
    attachment = attachments[0]
    assert attachment["scenario_name"] == "Attachment hooks receive the active run", attachment
    assert attachment["step_name"] == "the example attaches a report", attachment
    assert attachment["previous_step_name"] is None, attachment
    assert (attachment["stage"], attachment["status"]) == ("step-running", "running"), attachment
    assert attachment["hook_phase"], attachment
    assert attachment["attachment"] == "run-aware attachment sentinel", attachment
    assert attachment["media_type"] == "text/plain", attachment
    assert attachment["file_name"] == "run-aware-report.txt", attachment
    assert attachment["request_nodeid"], attachment


@then(
    re.compile(
        r'consumer run-aware hook artifact "(?P<relative_path>[^"]+)" should distinguish failures and cleanup'
    )
)
def consumer_run_aware_failure_cleanup(relative_path: str, consumer: ConsumerProject) -> None:
    rows = _run_aware_consumer_rows(relative_path, consumer)
    failure_expectations = {
        "Body failure remains a step error": ("step_error", "AssertionError", "body failure sentinel", "failed"),
        "Replacement callable failure preserves hook payload": (
            "step_error",
            "RuntimeError",
            "replacement callable failure sentinel",
            "failed",
        ),
        "Lookup failure remains a lookup error": (
            "lookup_error",
            "StepDefinitionNotFoundError",
            "Step definition is not found",
            "undefined",
        ),
        "Hook failure is cleaned up": (
            "step_error",
            "RuntimeError",
            "observer hook failure sentinel",
            "failed",
        ),
    }
    for scenario_name, (event, error_type, error_message, status) in failure_expectations.items():
        scenario_rows = [row for row in rows if row["scenario_name"] == scenario_name]
        error_rows = [row for row in scenario_rows if row["event"] == event]
        assert len(error_rows) == 1, (scenario_name, scenario_rows)
        error = error_rows[0]
        assert error["exception_type"] == error_type, error
        assert error_message in error["exception_message"], error
        assert error["status"] == status, error
        expected_error_phase = (
            "pytest_cuke_step_func_lookup_error" if event == "lookup_error" else "pytest_cuke_step_error"
        )
        assert error["stage"] == "step-running" and error["hook_phase"] == expected_error_phase, error
        assert not [row for row in scenario_rows if row["event"] == "after_step"], scenario_rows
        finish_rows = [row for row in scenario_rows if row["event"] == "after_scenario"]
        assert len(finish_rows) == 1, scenario_rows
        finish = finish_rows[0]
        assert finish["stage"] == "finished" and finish["hook_phase"] == "pytest_cuke_after_scenario", finish
        assert finish["status"] == status and finish["scenario_status"] == status, finish

    replacement_rows = [
        row
        for row in rows
        if row["scenario_name"] == "Replacement callable failure preserves hook payload"
    ]
    installed = next(row for row in replacement_rows if row["event"] == "replacement_installed")
    invoked = next(row for row in replacement_rows if row["event"] == "replacement_callable")
    replacement_error = next(row for row in replacement_rows if row["event"] == "step_error")
    assert installed["step_func"] == installed["step_definition_func"] == "replacement_callable", installed
    assert invoked["step_func_args"] == {"label": "callable payload sentinel"}, invoked
    assert replacement_error["selection"] == "replacement_payload_matches", replacement_error
    assert replacement_error["step_func"] == replacement_error["step_definition_func"] == "replacement_callable", (
        replacement_error
    )
    assert replacement_error["step_func_identity"] == installed["step_func_identity"], replacement_error
    assert replacement_error["step_func_identity"] == replacement_error["step_definition_func_identity"], (
        replacement_error
    )
    assert replacement_error["step_definition_identity"] == installed["step_definition_identity"], (
        replacement_error
    )
    assert replacement_error["step_func_args"] == {"label": "callable payload sentinel"}, replacement_error
    assert replacement_error["exception_message"] == "replacement callable failure sentinel", replacement_error
    assert not [row for row in replacement_rows if row["event"] == "after_step"], replacement_rows

    body_rows = [row for row in rows if row["scenario_name"] == "Body failure remains a step error"]
    lookup_rows = [row for row in rows if row["scenario_name"] == "Lookup failure remains a lookup error"]
    assert not [row for row in body_rows if row["event"] == "lookup_error"], body_rows
    assert not [row for row in lookup_rows if row["event"] == "step_error"], lookup_rows

    fresh_rows = [row for row in rows if row["scenario_name"] == "Fresh scenario starts without prior steps"]
    fresh_first_step = next(row for row in fresh_rows if row["event"] == "before_step")
    assert fresh_first_step["current_step_index"] == 0, fresh_first_step
    assert fresh_first_step["previous_step_name"] is None, fresh_first_step
    assert fresh_first_step["context_previous_step_name"] is None, fresh_first_step
    fresh_finish = next(row for row in fresh_rows if row["event"] == "after_scenario")
    assert fresh_finish["status"] == "passed" and fresh_finish["stage"] == "finished", fresh_finish

    cleanup = json.loads(_consumer_artifact_path("run-aware-cleanup.json", consumer).read_text(encoding="utf-8"))
    assert cleanup == {
        "active_feature": False,
        "active_scenario": False,
        "feature": None,
        "scenario": None,
        "step": None,
        "previous_step": None,
        "stage": "inactive",
        "hook_phase": "inactive",
        "status": "inactive",
    }, cleanup
    body_effects = _consumer_artifact_path("run-aware-body-effects.log", consumer).read_text(
        encoding="utf-8"
    ).splitlines()
    assert "hook-body-must-not-run" not in body_effects, body_effects


@then("consumer run-aware observations should isolate two pytest.main sessions")
def consumer_run_aware_pytest_main_isolation(consumer: ConsumerProject) -> None:
    rows = _run_aware_consumer_rows("run-aware-master.jsonl", consumer)
    expected = {
        "First pytest.main session starts clean",
        "Second pytest.main session starts clean",
    }
    starts = [row for row in rows if row["event"] == "before_scenario"]
    assert {row["scenario_name"] for row in starts} == expected, starts
    assert len({row["run_id"] for row in starts}) == 2, starts
    assert len({row["run_identity"] for row in starts}) == 2, starts
    for row in starts:
        assert row["stage"] == "setup" and row["status"] == "running", row
        assert row["current_step_index"] is None and row["previous_step_name"] is None, row
    assert all(row["worker_id"] == "master" for row in rows), rows


@then("consumer run-aware xdist artifacts should show isolated contexts on two workers")
def consumer_run_aware_xdist_isolation(consumer: ConsumerProject) -> None:
    artifacts = sorted(consumer.path.glob("run-aware-gw*.jsonl"))
    assert len(artifacts) == 2, artifacts
    worker_run_ids: set[str] = set()
    expected_scenarios = {"First xdist worker scenario", "Second xdist worker scenario"}
    for artifact in artifacts:
        rows = _run_aware_consumer_rows(artifact.name, consumer)
        assert {row["scenario_name"] for row in rows} == expected_scenarios, rows
        assert all(row["worker_id"] == artifact.stem.removeprefix("run-aware-") for row in rows), rows
        first_steps = [row for row in rows if row["event"] == "before_step"]
        assert len(first_steps) == 2, first_steps
        assert all(
            row["current_step_index"] == 0 and row["previous_step_name"] is None for row in first_steps
        ), first_steps
        run_ids = {row["run_id"] for row in rows}
        assert len(run_ids) == 1, rows
        assert len({row["run_identity"] for row in rows}) == 1, rows
        worker_run_ids.update(run_ids)
    assert len(worker_run_ids) == 2, worker_run_ids


@given("the consumer records monotonic test start and terminal events")
def configure_consumer_test_group_event_recorder(consumer: ConsumerProject) -> None:
    event_support = consumer.path / "group_events.py"
    event_support.write_text(
        dedent(
            """\
            from __future__ import annotations

            import hashlib
            import itertools
            import json
            import os
            import tempfile
            import time
            from pathlib import Path


            EVENT_DIRECTORY = Path(".pytest-cuke-group-events")
            EVENT_SEQUENCE = itertools.count()


            def record_event(
                phase,
                *,
                nodeid,
                group,
                outcome=None,
                when=None,
                resolved_group=None,
                assignment_source=None,
                assignment_ordinal=None,
                collection_position=None,
            ):
                sequence = next(EVENT_SEQUENCE)
                timestamp = time.monotonic_ns()
                worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
                run_id = os.environ.get("PYTEST_CUKE_RUN_ID", "single")
                record = {
                    "phase": phase,
                    "nodeid": nodeid,
                    "group": group,
                    "outcome": outcome,
                    "when": when,
                    "resolved_group": resolved_group,
                    "assignment_source": assignment_source,
                    "assignment_ordinal": assignment_ordinal,
                    "collection_position": collection_position,
                    "sequence": sequence,
                    "worker": worker,
                    "run_id": run_id,
                    "timestamp_ns": timestamp,
                }
                token = hashlib.sha256(f"{phase}:{nodeid}:{worker}:{run_id}:{sequence}".encode()).hexdigest()
                EVENT_DIRECTORY.mkdir(exist_ok=True)
                event_path = EVENT_DIRECTORY / f"{phase}-{token}.json"
                temporary_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        dir=EVENT_DIRECTORY,
                        prefix=f".{event_path.name}.",
                        suffix=".tmp",
                        delete=False,
                    ) as temporary_file:
                        temporary_file.write(json.dumps(record))
                        temporary_path = Path(temporary_file.name)
                    os.replace(temporary_path, event_path)
                finally:
                    if temporary_path is not None:
                        try:
                            temporary_path.unlink()
                        except FileNotFoundError:
                            pass


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


            @pytest.hookimpl(hookwrapper=True, tryfirst=True)
            def pytest_collection_finish(session):
                yield
                test_group_plugin = session.config.pluginmanager.get_plugin("pytest_cuke_test_groups")
                assignments = getattr(test_group_plugin, "assignments", {})
                for position, item in enumerate(session.items):
                    assignment = assignments.get(item.nodeid)
                    record_event(
                        "collection",
                        nodeid=item.nodeid,
                        group=getattr(assignment, "group", None),
                        resolved_group=getattr(assignment, "group", None),
                        assignment_source=getattr(getattr(assignment, "source", None), "value", None),
                        assignment_ordinal=getattr(assignment, "ordinal", None),
                        collection_position=position,
                    )


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
                test_group_plugin = item.config.pluginmanager.get_plugin("pytest_cuke_test_groups")
                assignment = (
                    getattr(test_group_plugin, "assignments", {}).get(item.nodeid)
                    if test_group_plugin is not None
                    else None
                )
                record_event(
                    "terminal",
                    nodeid=item.nodeid,
                    group=group,
                    resolved_group=getattr(assignment, "group", None),
                    assignment_source=getattr(getattr(assignment, "source", None), "value", None),
                    assignment_ordinal=getattr(assignment, "ordinal", None),
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
    command = [str(consumer.pytest), *_split_consumer_arguments(arguments)]
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
    starts = [event for event in events if event["phase"] == "start"]
    workers = {str(event.get("worker", "master")) for event in starts}
    order_key = "sequence" if len(workers) <= 1 else "timestamp_ns"
    starts.sort(key=lambda event: event[order_key])
    actual = [str(event["nodeid"]).rsplit("::", 1)[-1] for event in starts]
    expected_names = [name.strip() for name in expected.split(",") if name.strip()]
    collection = sorted(
        (event for event in events if event["phase"] == "collection"),
        key=lambda event: event["collection_position"],
    )
    collection_details = [
        {
            "position": event["collection_position"],
            "nodeid": str(event["nodeid"]).rsplit("::", 1)[-1],
            "group": event.get("resolved_group"),
            "source": event.get("assignment_source"),
            "ordinal": event.get("assignment_ordinal"),
        }
        for event in collection
    ]
    assert actual == expected_names, (
        f"consumer start order was {actual}; expected {expected_names}; "
        f"final collection assignments: {collection_details}"
    )


@then(re.compile(r'consumer collection events should follow "(?P<expected>[^"]+)"'))
def consumer_collection_events_follow_order(expected, consumer: ConsumerProject) -> None:
    events = _read_consumer_test_group_events(consumer)
    collection = sorted(
        (event for event in events if event["phase"] == "collection"),
        key=lambda event: event["collection_position"],
    )
    actual = [str(event["nodeid"]).rsplit("::", 1)[-1] for event in collection]
    expected_names = [name.strip() for name in expected.split(",") if name.strip()]
    details = [
        {
            "position": event["collection_position"],
            "nodeid": str(event["nodeid"]).rsplit("::", 1)[-1],
            "group": event.get("resolved_group"),
            "source": event.get("assignment_source"),
            "ordinal": event.get("assignment_ordinal"),
        }
        for event in collection
    ]
    assert actual == expected_names, (
        f"consumer final collection order was {actual}; expected {expected_names}; "
        f"collection assignments: {details}"
    )


@then(re.compile(r'consumer collection assignments should include "(?P<expected>[^"]+)"'))
def consumer_collection_assignments_include(expected, consumer: ConsumerProject) -> None:
    events = _read_consumer_test_group_events(consumer)
    collection = [event for event in events if event["phase"] == "collection"]
    actual = {
        str(event["nodeid"]).rsplit("::", 1)[-1]: {
            "group": event.get("resolved_group"),
            "source": event.get("assignment_source"),
            "ordinal": event.get("assignment_ordinal"),
        }
        for event in collection
    }
    expected_assignments = {}
    for value in expected.split(","):
        name, separator, assignment_text = value.partition("=")
        group, source_separator, source_and_ordinal = assignment_text.partition(":")
        source, ordinal_separator, ordinal = source_and_ordinal.partition(":")
        assert (
            separator
            and name.strip()
            and group.strip()
            and source_separator
            and source.strip()
            and ordinal_separator
            and ordinal.strip().isdecimal()
        ), f"invalid expected collection assignment {value!r}"
        expected_assignments[name.strip()] = {
            "group": group.strip(),
            "source": source.strip(),
            "ordinal": int(ordinal),
        }

    actual_assignments = {name: actual.get(name) for name in expected_assignments}
    assert actual_assignments == expected_assignments, (
        f"consumer collection assignments were {actual_assignments}; expected {expected_assignments}; "
        f"all assignments: {actual}"
    )


@then(re.compile(r'consumer resolved groups should include "(?P<expected>[^"]+)"'))
def consumer_resolved_groups_include(expected, consumer: ConsumerProject) -> None:
    events = _read_consumer_test_group_events(consumer)
    terminals = [event for event in events if event["phase"] == "terminal"]
    actual = {
        str(event["nodeid"]).rsplit("::", 1)[-1]: {
            "group": event.get("resolved_group"),
            "source": event.get("assignment_source"),
        }
        for event in terminals
    }
    expected_assignments = {}
    for item in expected.split(","):
        name, separator, group = item.partition("=")
        assert separator and name.strip() and group.strip(), f"invalid expected group assignment {item!r}"
        expected_assignments[name.strip()] = group.strip()

    actual_assignments = {name: actual.get(name, {}).get("group") for name in expected_assignments}
    assert actual_assignments == expected_assignments, (
        f"consumer resolved test groups were {actual_assignments}; expected {expected_assignments}; "
        f"assignment details: {actual}"
    )


@then(re.compile(r'every selected "(?P<earlier>[^\"]+)" test should settle before any "(?P<later>[^\"]+)" test starts'))
def consumer_test_groups_obey_terminal_barrier(earlier, later, consumer: ConsumerProject) -> None:
    events = _read_consumer_test_group_events(consumer)
    earlier_terminals = [
        event["timestamp_ns"] for event in events if event["phase"] == "terminal" and event["group"] == earlier
    ]
    later_starts = [event["timestamp_ns"] for event in events if event["phase"] == "start" and event["group"] == later]
    assert earlier_terminals, f"the consumer recorded no terminal events for group {earlier!r}"
    assert later_starts, f"the consumer recorded no start events for group {later!r}"
    assert max(earlier_terminals) <= min(later_starts), (
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
    workers = {
        str(event["worker"])
        for event in events
        if event.get("phase") in {"start", "terminal"} and event.get("worker") != "master"
    }
    required_workers = int(count) if count.isdecimal() else {"two": 2, "four": 4}[count]
    assert len(workers) >= required_workers, (
        f"expected events from at least {required_workers} xdist workers, got {sorted(workers)}"
    )


@then(re.compile(r'pytest output should include "(?P<expected>[^"]+)"'))
def consumer_pytest_output_includes(expected, consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    normalized_output = re.sub(r"\s+", " ", output).casefold()
    normalized_expected = re.sub(r"\s+", " ", expected).casefold()
    assert normalized_expected in normalized_output, f"pytest output did not include {expected!r}:\n{output}"


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
    envelopes = [json.loads(line) for line in report_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    run_started = next(
        (envelope["testRunStarted"] for envelope in envelopes if isinstance(envelope.get("testRunStarted"), dict)),
        None,
    )
    run_started_id = run_started.get("id") if isinstance(run_started, dict) else None
    run_namespace, separator, counter = (
        run_started_id.rpartition("-") if isinstance(run_started_id, str) else ("", "", "")
    )
    if not separator or not counter.isdecimal():
        run_namespace = ""

    def normalize(value: object, field_name: str | None = None) -> object:
        if isinstance(value, dict):
            media_type = value.get("mediaType")
            normalized: dict[str, object] = {}
            for key, item in value.items():
                if key in {"timestamp", "duration"}:
                    continue
                if (
                    key == "body"
                    and isinstance(media_type, str)
                    and media_type.endswith("+json")
                    and isinstance(item, str)
                ):
                    try:
                        attachment_payload = json.loads(item)
                    except json.JSONDecodeError:
                        normalized[key] = item
                    else:
                        normalized[key] = json.dumps(
                            normalize(attachment_payload),
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                else:
                    normalized[key] = normalize(item, key)
            return normalized
        if isinstance(value, list):
            return [normalize(item, field_name) for item in value]
        if (
            isinstance(value, str)
            and run_namespace
            and field_name is not None
            and (field_name == "id" or field_name.endswith("Id") or field_name.endswith("Ids"))
            and value.startswith(f"{run_namespace}-")
        ):
            return f"<run>{value[len(run_namespace):]}"
        return value

    return [normalize(envelope) for envelope in envelopes]


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


@given("the consumer installs pytest-cuke with its StructBDD extra")
def install_pytest_cuke_struct_bdd_extra_in_consumer_environment(consumer: ConsumerProject) -> None:
    _install_pytest_cuke_extra_in_isolated_environment(consumer, "struct-bdd")


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

    common_arguments = ["--rootdir=.", "-q", "--color=no"]
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
        assert re.search(r"\b1 passed\b", output), output

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
    assert len(re.findall(r"\b1 passed\b", output)) == 2, output
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
    environment = _consumer_environment()
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
        python_factors=("311", "312"),
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


@then("the tox expansion should be deterministic and include all supported factor combinations")
def tox_expansion_is_deterministic_and_complete(consumer: ConsumerProject) -> None:
    runs = getattr(consumer, "_compatibility_expansion_runs", None)
    assert runs is not None and len(runs) == 2, "the repeated compatibility expansion has not run"
    assert all(run.returncode == 0 for run in runs), [(run.stdout, run.stderr) for run in runs]
    assert runs[0].stdout == runs[1].stdout, "repeated tox expansion changed its JSON output"
    names = json.loads(runs[-1].stdout)["toxEnvNames"]
    assert len(names) == 8 and len(set(names)) == 8, names
    assert set(names) == {
        f"py{python}-pytest{pytest}-{target}"
        for python in ("311", "312")
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
        [str(consumer.cuke), "compatibility", *_split_consumer_arguments(arguments), "--config", str(config_path)],
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


@then("schema sync output should name cucumber-messages 28.0.0 and upstream tag v28.0.0")
def consumer_schema_sync_output_has_pinned_versions(consumer: ConsumerProject) -> None:
    result = consumer.command_result
    assert result is not None, "a schema sync command has not run"
    output = f"{result.stdout}\n{result.stderr}"
    assert "cucumber-messages==28.0.0" in output, output
    assert "v28.0.0" in output, output


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
        assert re.search(r"\b3 failed\b", output), output


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
    serialized_labels = "\\n".join(labels.split(",")) + "\\n"
    with Path("continuations.log").open("a", encoding="utf-8") as stream:
        stream.write(serialized_labels)
    worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
    with Path(f"xdist-continuations-{worker}.log").open("a", encoding="utf-8") as stream:
        stream.write(serialized_labels)


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


@given("the installed consumer exposes two duplicate tolerant step definitions")
def add_duplicate_tolerant_step_definitions(consumer: ConsumerProject) -> None:
    conftest_path = consumer.path / "conftest.py"
    conftest = conftest_path.read_text(encoding="utf-8")
    assert "from pytest_cuke.steps import tolerant" in conftest, conftest
    assert "def record_continuation(labels):" in conftest, conftest
    conftest_path.write_text(
        conftest
        + dedent(
            """\

            @tolerant
            @when("the ambiguous tolerant operation matches two definitions")
            def first_ambiguous_tolerant_operation():
                record_continuation("first")


            @when("the ambiguous tolerant operation matches two definitions")
            @tolerant
            def second_ambiguous_tolerant_operation():
                record_continuation("second")
            """
        ),
        encoding="utf-8",
    )


@given("the installed consumer exposes a tolerant step that requests a missing fixture")
def add_tolerant_missing_fixture_step(consumer: ConsumerProject) -> None:
    conftest_path = consumer.path / "conftest.py"
    conftest = conftest_path.read_text(encoding="utf-8")
    assert "from pytest_cuke.steps import tolerant" in conftest, conftest
    conftest_path.write_text(
        conftest
        + dedent(
            """\

            @tolerant
            @when("the tolerant operation requests a missing fixture")
            def tolerant_step_with_missing_fixture(tolerant_missing_fixture):
                Path("missing-fixture-step-body.log").write_text("ran", encoding="utf-8")
            """
        ),
        encoding="utf-8",
    )


@given("the installed consumer declares a real target fixture for a failing tolerant step")
def add_tolerant_target_fixture_consumer(consumer: ConsumerProject) -> None:
    conftest_path = consumer.path / "conftest.py"
    conftest = conftest_path.read_text(encoding="utf-8")
    assert "from pytest_cuke.steps import tolerant" in conftest, conftest
    assert "from pytest_cuke import parsers, then, when" in conftest, conftest
    conftest_path.write_text(
        conftest
        + dedent(
            """\

            @pytest.fixture
            def tolerant_target_value():
                return "fixture-provided-target"


            @tolerant
            @when(
                "the tolerant setup raises before returning its target fixture",
                target_fixture="tolerant_target_value",
            )
            def tolerant_setup_raises_before_target_return():
                raise AssertionError("tolerant target failure sentinel")


            @then("the later step consumes the real target fixture")
            def consume_real_tolerant_target_fixture(tolerant_target_value):
                assert tolerant_target_value == "fixture-provided-target"
                record_continuation(tolerant_target_value)
            """
        ),
        encoding="utf-8",
    )


@given("the consumer stages the checked-in tolerant steps example")
def stage_checked_in_tolerant_steps_example(consumer: ConsumerProject) -> None:
    example_root = Path(__file__).resolve().parents[2] / "examples" / "tolerant-steps"
    relative_files = (
        Path("readme.md"),
        Path("pyproject.toml"),
        Path("requirements.txt"),
        Path("conftest.py"),
        Path(".gitignore"),
        Path("features/tolerant-steps.feature"),
    )
    missing = [str(relative_path) for relative_path in relative_files if not (example_root / relative_path).is_file()]
    assert not missing, f"the runnable tolerant steps example is missing files: {missing!r}"
    for relative_path in relative_files:
        destination = consumer.path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(example_root / relative_path, destination)


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


@then(
    re.compile(
        r'consumer xdist WIP side-effect artifacts should show "(?P<effects>[^"]+)" '
        r'on (?P<count>\d+) workers'
    )
)
def consumer_xdist_wip_side_effects(effects: str, count: str, consumer: ConsumerProject) -> None:
    artifacts = sorted(consumer.path.glob("wip-effects-gw*.log"))
    assert len(artifacts) == int(count), f"expected {count} worker artifacts, found {artifacts!r}"
    actual = {artifact.name: artifact.read_text(encoding="utf-8").splitlines() for artifact in artifacts}
    expected = effects.split(",")
    assert all(lines == expected for lines in actual.values()), (expected, actual)


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
        r'with step statuses "(?P<statuses>[a-z, ]+)" and error messages "(?P<messages>[^"]*)"'
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
    expected_messages = messages.split(",") if messages else []
    assert actual_messages == expected_messages, (actual_messages, expected_messages, steps)


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


@then(
    re.compile(
        r'consumer artifacts "(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" should report strict '
        r'tolerant fixture lookup "(?P<fixture_name>[^"]+)" for scenario "(?P<scenario_name>[^"]+)"'
    )
)
def consumer_tolerant_fixture_lookup_failure(
    messages_path: str,
    json_path: str,
    fixture_name: str,
    scenario_name: str,
    consumer: ConsumerProject,
) -> None:
    message_steps, run_success = _tolerant_scenario_step_results(messages_path, scenario_name, consumer)
    assert [result.get("status") for _, result in message_steps] == ["FAILED", "SKIPPED"], message_steps
    lookup_exception = message_steps[0][1].get("exception")
    assert isinstance(lookup_exception, dict), message_steps
    assert lookup_exception.get("type") == "FixtureLookupError", lookup_exception
    assert fixture_name in str(lookup_exception.get("message")), lookup_exception
    assert message_steps[1][1].get("exception") is None, message_steps
    assert run_success is False

    report = json.loads((consumer.path / json_path).read_text(encoding="utf-8"))
    scenarios = [
        scenario
        for feature in report
        for scenario in feature.get("elements", [])
        if scenario.get("name") == scenario_name
    ]
    assert len(scenarios) == 1, scenarios
    json_steps = scenarios[0]["steps"]
    assert [step["result"]["status"] for step in json_steps] == ["failed", "skipped"], json_steps
    assert fixture_name in json_steps[0]["result"].get("error_message", ""), json_steps
    assert not json_steps[1]["result"].get("error_message"), json_steps


@given("the installed consumer exposes not-implemented steps and policy probes")
def install_not_implemented_step_consumer_definitions(consumer: ConsumerProject) -> None:
    (consumer.path / "conftest.py").write_text(
        '''from pathlib import Path

import os
import pytest
import pytest_cuke
from pytest_cuke import parsers, then, when
from pytest_cuke.steps import not_implemented


assert not hasattr(pytest_cuke, "not_implemented"), "not_implemented must stay in pytest_cuke.steps"


def _record_effect(value):
    with Path("wip-effects.log").open("a", encoding="utf-8") as stream:
        stream.write(value + "\\n")
    worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
    if worker != "master":
        with Path(f"wip-effects-{worker}.log").open("a", encoding="utf-8") as stream:
            stream.write(value + "\\n")


def _record_continuation(value):
    with Path("continuations.log").open("a", encoding="utf-8") as stream:
        stream.write(value + "\\n")
    worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
    with Path(f"xdist-continuations-{worker}.log").open("a", encoding="utf-8") as stream:
        stream.write(value + "\\n")


@pytest.hookimpl
def pytest_cuke_before_step(request, run, step_func):
    step = run.step
    if step is not None and "not-implemented" in step.name:
        _record_effect("before-step")


@pytest.hookimpl
def pytest_cuke_before_step_call(
    request, run, step_func, step_func_args, step_definition
):
    step = run.step
    if step is not None and "not-implemented" in step.name:
        _record_effect("before-call")


@not_implemented
@when(parsers.parse('the first not-implemented parameter step requests fixture injection for "{label}"'))
def first_parameter_step(label, wip_fixture_that_is_not_defined):
    _record_effect("body:first:" + label)


@when(parsers.parse('the second not-implemented parameter step requests fixture injection for "{label}"'))
@not_implemented
def second_parameter_step(label, wip_fixture_that_is_not_defined):
    _record_effect("body:second:" + label)


@when(parsers.parse('a not-implemented outline step for "{row}" requests fixture injection'))
@not_implemented
def outline_parameter_step(row, wip_fixture_that_is_not_defined):
    _record_effect("body:outline:" + row)


@not_implemented
@when(parsers.parse('a not-implemented body raises "{message}"'))
def not_implemented_body_raises(message):
    _record_effect("body:raise")
    raise RuntimeError(message)


@not_implemented
@when("a not-implemented body succeeds")
def not_implemented_body_succeeds():
    _record_effect("body:success")


@not_implemented
@when("the not-implemented setup creates its target", target_fixture="wip_created_target")
def not_implemented_target_setup():
    _record_effect("body:target")
    return "a value that must not be fabricated"


@then(parsers.parse('a later step records "{label}"'))
def record_wip_continuation(label):
    _record_continuation(label)


@then("the later step confirms the WIP target is None")
def confirm_wip_target_is_none(wip_created_target):
    assert wip_created_target is None
    Path("target-observation.log").write_text("None\\n", encoding="utf-8")
    _record_continuation("target-is-none")


@when("an ordinary operation raises under WIP policy")
def ordinary_wip_policy_operation():
    _record_effect("body:ordinary")
    raise RuntimeError("ordinary WIP exception sentinel")


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    for item in items:
        if "A marker overrides its tag and the failed global policy" in item.name:
            item.add_marker(pytest.mark.wip_status(" PASSED "))
        if "An invalid marker falls through to the failed tag" in item.name:
            item.add_marker(pytest.mark.wip_status(" UNKNOWN "))
''',
        encoding="utf-8",
    )


def _wip_scenario_step_results(
    relative_path: str,
    scenario_name: str,
    consumer: ConsumerProject,
) -> tuple[list[tuple[str, dict[str, object]]], bool]:
    envelopes = _background_messages_artifact(relative_path, consumer)
    _assert_background_message_references(envelopes)
    pickles = [
        envelope["pickle"]
        for envelope in envelopes
        if isinstance(envelope.get("pickle"), dict) and envelope["pickle"].get("name") == scenario_name
    ]
    assert len(pickles) == 1, f"expected one pickle for WIP scenario {scenario_name!r}, got {pickles!r}"
    pickle = pickles[0]
    cases = [
        envelope["testCase"]
        for envelope in envelopes
        if isinstance(envelope.get("testCase"), dict) and envelope["testCase"].get("pickleId") == pickle["id"]
    ]
    assert len(cases) == 1, f"expected one test case for WIP scenario {scenario_name!r}, got {cases!r}"
    test_case = cases[0]
    starts = [
        envelope["testCaseStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testCaseStarted"), dict)
        and envelope["testCaseStarted"].get("testCaseId") == test_case["id"]
    ]
    assert len(starts) == 1, f"expected one started attempt for WIP scenario {scenario_name!r}, got {starts!r}"
    started_id = starts[0]["id"]
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
        r'consumer artifacts "(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" should agree for WIP scenario '
        r'"(?P<scenario_name>[^"]+)" with step statuses "(?P<statuses>[a-z, ]+)" and exception messages '
        r'"(?P<messages>[^"]*)" and run success "(?P<run_success>true|false)"'
    )
)
def consumer_wip_messages_and_json_agree(
    messages_path: str,
    json_path: str,
    scenario_name: str,
    statuses: str,
    messages: str,
    run_success: str,
    consumer: ConsumerProject,
) -> None:
    steps, actual_run_success = _wip_scenario_step_results(messages_path, scenario_name, consumer)
    expected_messages_statuses = [status.strip().upper() for status in statuses.split(",")]
    actual_message_statuses = [result.get("status") for _, result in steps]
    assert actual_message_statuses == expected_messages_statuses, (actual_message_statuses, expected_messages_statuses)
    actual_messages = [
        result["exception"].get("message")
        for _, result in steps
        if result.get("status") == "FAILED" and isinstance(result.get("exception"), dict)
    ]
    expected_messages = messages.split(",") if messages else []
    assert actual_messages == expected_messages, (actual_messages, expected_messages)
    assert actual_run_success is (run_success == "true"), (actual_run_success, run_success)

    report = json.loads(_consumer_artifact_path(json_path, consumer).read_text(encoding="utf-8"))
    scenarios = [
        element
        for feature in report
        for element in feature.get("elements", [])
        if element.get("name") == scenario_name
    ]
    assert len(scenarios) == 1, scenarios
    json_steps = scenarios[0]["steps"]
    json_statuses = [step["result"]["status"] for step in json_steps]
    expected_json_statuses = [status.strip() for status in statuses.split(",")]
    assert json_statuses == expected_json_statuses, (json_statuses, expected_json_statuses)
    json_messages = [
        step["result"]["error_message"]
        for step in json_steps
        if step["result"]["status"] == "failed" and step["result"].get("error_message")
    ]
    assert json_messages == expected_messages, (json_messages, expected_messages)


@then(
    re.compile(
        r'consumer Messages artifact "(?P<relative_path>[^"]+)" should report WIP scenario '
        r'"(?P<scenario_name>[^"]+)" with step statuses "(?P<statuses>[A-Z, ]+)" and exception messages '
        r'"(?P<messages>[^"]*)"'
    )
)
def consumer_wip_scenario_messages(
    relative_path: str,
    scenario_name: str,
    statuses: str,
    messages: str,
    consumer: ConsumerProject,
) -> None:
    steps, _ = _wip_scenario_step_results(relative_path, scenario_name, consumer)
    expected_statuses = [status.strip() for status in statuses.split(",")]
    actual_statuses = [result.get("status") for _, result in steps]
    assert actual_statuses == expected_statuses, (actual_statuses, expected_statuses, steps)
    actual_messages = [
        result["exception"].get("message")
        for _, result in steps
        if result.get("status") == "FAILED" and isinstance(result.get("exception"), dict)
    ]
    expected_messages = messages.split(",") if messages else []
    assert actual_messages == expected_messages, (actual_messages, expected_messages, steps)


@then(re.compile(r'consumer WIP side-effect artifact should list "(?P<effects>[^"]+)"'))
def consumer_wip_side_effects(effects: str, consumer: ConsumerProject) -> None:
    actual = _consumer_artifact_path("wip-effects.log", consumer).read_text(encoding="utf-8").splitlines()
    expected = effects.split(",")
    assert actual == expected, f"expected WIP side effects {expected!r}, got {actual!r}"


@when(
    re.compile(
        r'I run installed pytest twice in one process with arguments "(?P<first_arguments>[^"]*)" and then '
        r'"(?P<second_arguments>[^"]*)"'
    )
)
def run_consumer_pytest_twice_in_one_process(
    first_arguments: str,
    second_arguments: str,
    consumer: ConsumerProject,
) -> None:
    runner = consumer.path / "run_wip_sessions.py"
    runner.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "import pytest\n"
        "separator = sys.argv.index('--pytest-cuke-next-session')\n"
        "first = pytest.main(sys.argv[1:separator])\n"
        "second = pytest.main(sys.argv[separator + 1:])\n"
        "Path('repeat-session-exits.txt').write_text(f'{int(first)},{int(second)}\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            str(consumer.python),
            str(runner),
            *_split_consumer_arguments(first_arguments),
            "--pytest-cuke-next-session",
            *_split_consumer_arguments(second_arguments),
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    consumer.pytest_result = result


@then(re.compile(r'consumer repeated pytest sessions should exit with codes "(?P<codes>[0-9,]+)"'))
def consumer_repeated_pytest_sessions_exit(codes: str, consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "repeated pytest sessions have not been run"
    assert result.returncode == 0, f"the session runner failed:\n{result.stdout}\n{result.stderr}"
    actual = _consumer_artifact_path("repeat-session-exits.txt", consumer).read_text(encoding="utf-8").strip()
    assert actual == codes, f"expected repeated pytest exit codes {codes!r}, got {actual!r}"


@then(
    re.compile(
        r'consumer artifact "(?P<messages_path>[^"]+)" should contain 2 coherent passed WIP outline attempts '
        r'matching "(?P<json_path>[^"]+)"'
    )
)
def consumer_wip_outline_messages_match_json(
    messages_path: str,
    json_path: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _background_messages_artifact(messages_path, consumer)
    _assert_background_message_references(envelopes)
    pickles = [
        envelope["pickle"]
        for envelope in envelopes
        if isinstance(envelope.get("pickle"), dict)
        and any("not-implemented outline step" in step["text"] for step in envelope["pickle"]["steps"])
    ]
    assert len(pickles) == 2, pickles
    cases = {
        envelope["testCase"]["pickleId"]: envelope["testCase"]
        for envelope in envelopes
        if isinstance(envelope.get("testCase"), dict)
    }
    starts = {
        envelope["testCaseStarted"]["testCaseId"]: envelope["testCaseStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testCaseStarted"), dict)
    }
    assert len(cases) == len(starts) == 2, (cases, starts)
    assert len([envelope for envelope in envelopes if isinstance(envelope.get("testCaseFinished"), dict)]) == 2
    finished_steps = {
        (finish["testCaseStartedId"], finish["testStepId"]): finish["testStepResult"]
        for envelope in envelopes
        if isinstance((finish := envelope.get("testStepFinished")), dict)
    }
    message_rows: dict[tuple[str, ...], tuple[str, ...]] = {}
    for pickle in pickles:
        case = cases[pickle["id"]]
        started = starts[case["id"]]
        texts = tuple(step["text"] for step in pickle["steps"])
        statuses = tuple(
            finished_steps[(started["id"], test_step["id"])]["status"]
            for test_step in case["testSteps"]
        )
        assert statuses == ("PASSED",) * len(texts), (texts, statuses)
        assert texts not in message_rows, message_rows
        message_rows[texts] = statuses

    run_finishes = [
        envelope["testRunFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunFinished"), dict)
    ]
    assert len(run_finishes) == 1 and run_finishes[0].get("success") is True, run_finishes

    report = json.loads(_consumer_artifact_path(json_path, consumer).read_text(encoding="utf-8"))
    elements = [element for feature in report for element in feature.get("elements", [])]
    assert len(elements) == 2, elements
    json_rows = {
        tuple(step["name"] for step in element["steps"]): tuple(
            step["result"]["status"].upper() for step in element["steps"]
        )
        for element in elements
    }
    assert len(json_rows) == 2, json_rows
    assert message_rows == json_rows, (message_rows, json_rows)


_IDE_LAUNCH_MEDIA_TYPE = "application/vnd.pytest-bdd.launch+json"
_IDE_STEP_BINDING_MEDIA_TYPE = "application/vnd.pytest-bdd.step-binding+json"
_IDE_DIAGNOSTIC_MEDIA_TYPE = "application/vnd.pytest-bdd.diagnostic+json"
_IDE_VENDOR_MEDIA_TYPES = frozenset(
    {
        _IDE_LAUNCH_MEDIA_TYPE,
        _IDE_STEP_BINDING_MEDIA_TYPE,
        _IDE_DIAGNOSTIC_MEDIA_TYPE,
    }
)


def _ide_binding_envelopes(relative_path: str, consumer: ConsumerProject) -> list[dict[str, object]]:
    artifact = _consumer_artifact_path(relative_path, consumer)
    lines = artifact.read_text(encoding="utf-8").splitlines()
    envelopes = [json.loads(line) for line in lines if line.strip()]
    assert all(isinstance(envelope, dict) for envelope in envelopes), envelopes
    return envelopes


def _ide_binding_payloads(
    envelopes: list[dict[str, object]], media_type: str
) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for envelope in envelopes:
        attachment = envelope.get("attachment")
        if not isinstance(attachment, dict) or attachment.get("mediaType") != media_type:
            continue
        body = attachment.get("body")
        assert isinstance(body, str), attachment
        payload = json.loads(body)
        assert isinstance(payload, dict), payload
        payloads.append(payload)
    return payloads


def _ide_assert_media_type_policy(envelopes: list[dict[str, object]]) -> None:
    """Keep one stable, unversioned vendor media-type policy in every run mode."""
    found_media_types: set[str] = set()
    for envelope in envelopes:
        attachment = envelope.get("attachment")
        if not isinstance(attachment, dict):
            continue
        media_type = attachment.get("mediaType")
        if not isinstance(media_type, str) or not media_type.startswith("application/vnd.pytest-bdd."):
            continue

        assert media_type in _IDE_VENDOR_MEDIA_TYPES, attachment
        assert media_type.endswith("+json"), attachment
        body = attachment.get("body")
        assert isinstance(body, str), attachment
        payload = json.loads(body)
        assert isinstance(payload, dict), (media_type, payload)
        found_media_types.add(media_type)

    assert found_media_types == _IDE_VENDOR_MEDIA_TYPES, found_media_types


def _ide_source_path(uri: object, consumer: ConsumerProject) -> Path:
    assert isinstance(uri, str) and uri, f"source URI must be a non-empty string, got {uri!r}"
    parsed = urlsplit(uri)
    if parsed.scheme == "file":
        from urllib.request import url2pathname

        path_text = url2pathname(unquote(parsed.path))
        if parsed.netloc and parsed.netloc != "localhost":
            path_text = f"//{parsed.netloc}{path_text}"
        elif os.name == "nt" and re.match(r"^/[A-Za-z]:", path_text):
            path_text = path_text[1:]
        path = Path(path_text)
    else:
        assert not parsed.scheme, f"source URI must be a file URI or consumer-relative path: {uri!r}"
        path = Path(unquote(uri))
        if not path.is_absolute():
            path = consumer.path / path
    resolved = path.resolve()
    assert resolved.is_file(), f"source URI {uri!r} did not resolve to a file: {resolved}"
    return resolved


def _ide_assert_source_identity(
    identity: object,
    consumer: ConsumerProject,
    *,
    suffix: str | None = None,
) -> tuple[Path, int]:
    assert isinstance(identity, dict), f"source identity must be an object, got {identity!r}"
    line = identity.get("line")
    assert type(line) is int and line > 0, identity
    source_path = _ide_source_path(identity.get("uri"), consumer)
    source_lines = source_path.read_text(encoding="utf-8").splitlines()
    assert line <= len(source_lines), f"source line {line} is outside {source_path}"
    if suffix is not None:
        assert source_path.name.endswith(suffix), (source_path, suffix)
    return source_path, line


def _ide_assert_file_source_reference(
    reference: object,
    consumer: ConsumerProject,
    *,
    suffix: str | None = None,
) -> tuple[Path, int]:
    assert isinstance(reference, dict), f"source reference must be an object, got {reference!r}"
    uri = reference.get("uri")
    assert isinstance(uri, str) and urlsplit(uri).scheme == "file", reference
    return _ide_assert_source_identity(reference, consumer, suffix=suffix)


def _ide_nested_source_references(value: object) -> list[dict[str, object]]:
    references: list[dict[str, object]] = []
    if isinstance(value, dict):
        if isinstance(value.get("uri"), str) and "line" in value:
            references.append(value)
        for child in value.values():
            references.extend(_ide_nested_source_references(child))
    elif isinstance(value, list):
        for child in value:
            references.extend(_ide_nested_source_references(child))
    return references


def _ide_collected_nodeids(consumer: ConsumerProject) -> set[str]:
    path = _consumer_artifact_path("collected-nodeids.txt", consumer)
    return {line for line in path.read_text(encoding="utf-8").splitlines() if line}


def _ide_case_records(
    envelopes: list[dict[str, object]],
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    test_cases = {
        case["id"]: case
        for envelope in envelopes
        if isinstance((case := envelope.get("testCase")), dict) and isinstance(case.get("id"), str)
    }
    pickles = {
        pickle["id"]: pickle
        for envelope in envelopes
        if isinstance((pickle := envelope.get("pickle")), dict) and isinstance(pickle.get("id"), str)
    }
    return test_cases, pickles


def _ide_case_step_results(
    envelopes: list[dict[str, object]], test_case: dict[str, object]
) -> dict[str, str]:
    case_id = test_case.get("id")
    case_steps = test_case.get("testSteps")
    assert isinstance(case_id, str) and isinstance(case_steps, list), test_case
    starts_by_id = {
        start["id"]: start
        for envelope in envelopes
        if isinstance((start := envelope.get("testCaseStarted")), dict)
        and start.get("testCaseId") == case_id
        and isinstance(start.get("id"), str)
    }
    test_step_ids = {step.get("id") for step in case_steps if isinstance(step, dict)}
    results: dict[str, str] = {}
    for envelope in envelopes:
        finish = envelope.get("testStepFinished")
        if not isinstance(finish, dict):
            continue
        if finish.get("testCaseStartedId") not in starts_by_id or finish.get("testStepId") not in test_step_ids:
            continue
        result = finish.get("testStepResult")
        assert isinstance(result, dict) and isinstance(result.get("status"), str), finish
        results[finish["testStepId"]] = result["status"]
    return results


@given("the consumer project root includes a Unicode character")
def consumer_project_root_includes_unicode(consumer: ConsumerProject) -> None:
    old_path = consumer.path
    unicode_path = old_path.with_name(f"{old_path.name}-café")
    assert not unicode_path.exists(), unicode_path
    old_path.rename(unicode_path)
    consumer.path = unicode_path
    consumer.env["HOME"] = str(unicode_path / ".home")
    if os.name == "nt":
        consumer.env["USERPROFILE"] = str(unicode_path / ".home")


@when(
    re.compile(
        r'I run installed pytest with an absolute consumer feature root and Messages file "(?P<relative_path>[^"]+)"'
    )
)
def run_consumer_pytest_with_absolute_feature_root(relative_path: str, consumer: ConsumerProject) -> None:
    output_path = _consumer_artifact_path(relative_path, consumer)
    result = subprocess.run(
        [
            str(consumer.pytest),
            "--rootdir=.",
            "--cuke-autoload",
            "--cuke-parser=python",
            f"--cuke-features-dir={consumer.path / 'features'}",
            f"--cuke-messages-ndjson={output_path}",
            "-q",
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    consumer.pytest_result = result


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should report the five parser bindings with real source identities'
    )
)
def consumer_ide_parser_bindings_have_real_sources(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(launches) == 1, launches
    launch = launches[0]
    case_id = launch.get("testCaseId")
    pickle_id = launch.get("pickleId")
    nodeid = launch.get("nodeid")
    assert isinstance(case_id, str) and case_id, launch
    assert isinstance(pickle_id, str) and pickle_id, launch
    assert isinstance(nodeid, str) and nodeid in _ide_collected_nodeids(consumer), launch
    feature_path, _ = _ide_assert_source_identity(launch.get("sourceIdentity"), consumer, suffix=".feature")
    assert feature_path == (consumer.path / "features/parser-bindings.feature").resolve(), feature_path

    test_cases, pickles = _ide_case_records(envelopes)
    test_case = test_cases[case_id]
    assert test_case.get("pickleId") == pickle_id, (launch, test_case)
    pickle = pickles[pickle_id]
    steps = pickle.get("steps")
    assert isinstance(steps, list), pickle
    step_text_by_id = {step["id"]: step["text"] for step in steps if isinstance(step, dict)}
    expected_arguments = {
        "the literal binding is selected": [],
        "I parse the name Alice": [("name", "Alice")],
        "I cfparse the name Bohdan": [("name", "Bohdan")],
        "I match the regex name Ira": [("name", "Ira")],
        "I match the expression name Olena": [("name", "Olena")],
        "all five parser bindings ran": [],
    }
    matches = [
        payload
        for payload in _ide_binding_payloads(envelopes, _IDE_STEP_BINDING_MEDIA_TYPE)
        if payload.get("testCaseId") == case_id
    ]
    assert len(matches) == len(expected_arguments), matches
    actual_arguments: dict[str, list[tuple[str, object]]] = {}
    step_definition_ids: set[str] = set()
    for match in matches:
        step_id = match.get("pickleStepId")
        definition_id = match.get("stepDefinitionId")
        assert isinstance(step_id, str) and step_id in step_text_by_id, match
        assert isinstance(definition_id, str) and definition_id, match
        arguments = match.get("matchArguments")
        assert isinstance(arguments, list), match
        actual_arguments[step_text_by_id[step_id]] = [
            (argument.get("name"), argument.get("value"))
            for argument in arguments
            if isinstance(argument, dict)
        ]
        reference_path, _ = _ide_assert_file_source_reference(
            match.get("sourceReference"), consumer, suffix="conftest.py"
        )
        assert reference_path == (consumer.path / "conftest.py").resolve(), reference_path
        step_definition_ids.add(definition_id)
    assert actual_arguments == expected_arguments, (actual_arguments, expected_arguments)
    assert len(step_definition_ids) == len(expected_arguments), step_definition_ids


@then(re.compile(r'consumer artifact "(?P<relative_path>[^"]+)" should report the missing step and both ambiguous candidates'))
def consumer_ide_missing_and_ambiguous_diagnostics(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    _ide_assert_media_type_policy(envelopes)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(launches) == 2, launches
    nodeids = _ide_collected_nodeids(consumer)
    launches_by_case = {launch.get("testCaseId"): launch for launch in launches}
    assert len(launches_by_case) == 2 and None not in launches_by_case, launches
    assert all(launch.get("nodeid") in nodeids for launch in launches), launches

    diagnostics = _ide_binding_payloads(envelopes, _IDE_DIAGNOSTIC_MEDIA_TYPE)
    missing = [diagnostic for diagnostic in diagnostics if diagnostic.get("kind") == "missing-step"]
    ambiguous = [diagnostic for diagnostic in diagnostics if diagnostic.get("kind") == "ambiguous-step"]
    assert len(missing) == len(ambiguous) == 1, diagnostics
    missing_diagnostic = missing[0]
    ambiguous_diagnostic = ambiguous[0]
    assert missing_diagnostic.get("severity") == ambiguous_diagnostic.get("severity") == "warning"
    assert missing_diagnostic.get("unmatchedStepText") == "the unique missing phrase is needle-73", missing_diagnostic
    missing_case_id = missing_diagnostic.get("testCaseId")
    missing_step_id = missing_diagnostic.get("pickleStepId")
    assert missing_case_id in launches_by_case and isinstance(missing_step_id, str), missing_diagnostic
    available = missing_diagnostic.get("availableStepDefinitions")
    assert isinstance(available, list) and available, missing_diagnostic
    available_references = _ide_nested_source_references(available)
    assert available_references, available
    resolved_available = [
        _ide_assert_file_source_reference(reference, consumer)[0]
        for reference in available_references
    ]
    assert (consumer.path / "conftest.py").resolve() in resolved_available, resolved_available

    candidates = ambiguous_diagnostic.get("candidates")
    assert isinstance(candidates, list) and len(candidates) == 2, ambiguous_diagnostic
    candidate_ids: list[str] = []
    candidate_lines: list[int] = []
    for candidate in candidates:
        assert isinstance(candidate, dict), candidate
        assert candidate.get("pattern") == "the ambiguous operation is selected", candidate
        definition_id = candidate.get("stepDefinitionId")
        assert isinstance(definition_id, str) and definition_id, candidate
        candidate_ids.append(definition_id)
        path, line = _ide_assert_file_source_reference(candidate.get("sourceReference"), consumer, suffix="conftest.py")
        assert path == (consumer.path / "conftest.py").resolve(), path
        candidate_lines.append(line)
    assert len(set(candidate_ids)) == 2, candidate_ids
    assert len(set(candidate_lines)) == 2, candidate_lines
    ambiguous_case_id = ambiguous_diagnostic.get("testCaseId")
    ambiguous_step_id = ambiguous_diagnostic.get("pickleStepId")
    assert ambiguous_case_id in launches_by_case and isinstance(ambiguous_step_id, str), ambiguous_diagnostic

    test_cases, pickles = _ide_case_records(envelopes)
    missing_case = test_cases[missing_case_id]
    missing_pickle = pickles[missing_case["pickleId"]]
    missing_step_texts = {
        step["id"]: step["text"] for step in missing_pickle["steps"] if isinstance(step, dict)
    }
    assert missing_step_texts[missing_step_id] == missing_diagnostic["unmatchedStepText"], missing_diagnostic
    missing_test_step = next(
        step for step in missing_case["testSteps"] if isinstance(step, dict) and step.get("pickleStepId") == missing_step_id
    )
    missing_statuses = _ide_case_step_results(envelopes, missing_case)
    assert missing_statuses.get(missing_test_step["id"]) == "UNDEFINED", missing_statuses
    failure_reports_path = _consumer_artifact_path("failure-reports.ndjson", consumer)
    failure_reports = [
        json.loads(line)
        for line in failure_reports_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(failure_reports) == 1, failure_reports
    assert failure_reports[0].get("exceptionType") == "StepDefinitionNotFoundError", failure_reports
    failure_message = failure_reports[0].get("message")
    assert isinstance(failure_message, str), failure_reports
    for expected_fragment in (
        'Step definition is not found: "the unique missing phrase is needle-73".',
        'Step keyword: "Given".',
        'scenario "An unmatched step still fails naturally"',
    ):
        assert expected_fragment in failure_message, failure_reports

    ambiguous_case = test_cases[ambiguous_case_id]
    ambiguous_pickle = pickles[ambiguous_case["pickleId"]]
    ambiguous_step_texts = {
        step["id"]: step["text"] for step in ambiguous_pickle["steps"] if isinstance(step, dict)
    }
    ambiguous_step_match = next(
        match
        for match in _ide_binding_payloads(envelopes, _IDE_STEP_BINDING_MEDIA_TYPE)
        if match.get("testCaseId") == ambiguous_case_id and match.get("pickleStepId") == ambiguous_step_id
    )
    assert ambiguous_step_texts[ambiguous_step_id] == "the ambiguous operation is selected", ambiguous_step_match
    assert ambiguous_step_match.get("stepDefinitionId") == candidate_ids[0], ambiguous_step_match
    ambiguous_test_step = next(
        step
        for step in ambiguous_case["testSteps"]
        if isinstance(step, dict) and step.get("pickleStepId") == ambiguous_step_id
    )
    ambiguous_statuses = _ide_case_step_results(envelopes, ambiguous_case)
    assert ambiguous_statuses.get(ambiguous_test_step["id"]) == "PASSED", ambiguous_statuses


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should link mock-run launches to bound and missing source identities'
    )
)
def consumer_ide_mock_run_source_identities(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    _ide_assert_media_type_policy(envelopes)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(launches) == 2, launches

    nodeids = _ide_collected_nodeids(consumer)
    test_cases, pickles = _ide_case_records(envelopes)
    launch_by_case: dict[str, tuple[dict[str, object], dict[str, object], dict[str, object]]] = {}
    feature_path = (consumer.path / "features/mock-run-messages.feature").resolve()
    for launch in launches:
        case_id = launch.get("testCaseId")
        pickle_id = launch.get("pickleId")
        nodeid = launch.get("nodeid")
        assert isinstance(case_id, str) and case_id, launch
        assert isinstance(pickle_id, str) and pickle_id, launch
        assert isinstance(nodeid, str) and nodeid in nodeids, launch
        test_case = test_cases[case_id]
        pickle = pickles[pickle_id]
        assert test_case.get("pickleId") == pickle_id, (launch, test_case)
        source_path, source_line = _ide_assert_source_identity(launch.get("sourceIdentity"), consumer)
        assert source_path == feature_path, (launch, source_path)
        source_text = source_path.read_text(encoding="utf-8").splitlines()[source_line - 1]
        assert source_text.strip().startswith("Scenario:"), (source_line, source_text)
        assert case_id not in launch_by_case, launches
        launch_by_case[case_id] = (launch, test_case, pickle)

    case_by_first_step: dict[str, str] = {}
    for case_id, (_launch, _test_case, pickle) in launch_by_case.items():
        steps = pickle.get("steps")
        assert isinstance(steps, list) and steps, pickle
        first_text = steps[0].get("text") if isinstance(steps[0], dict) else None
        assert isinstance(first_text, str), pickle
        case_by_first_step[first_text] = case_id
    bound_step_text = "the IDE mock-run match is available"
    missing_step_texts = {
        "the first missing IDE message step is absent",
        "the second missing IDE message step is absent",
    }
    bound_case_id = case_by_first_step[bound_step_text]
    missing_case_id = next(
        case_id for first_text, case_id in case_by_first_step.items() if first_text in missing_step_texts
    )
    assert bound_case_id != missing_case_id, case_by_first_step
    missing_case_steps = launch_by_case[missing_case_id][2].get("steps")
    assert isinstance(missing_case_steps, list), launch_by_case[missing_case_id][2]
    missing_text_by_step_id = {
        step["id"]: step["text"]
        for step in missing_case_steps
        if isinstance(step, dict) and isinstance(step.get("id"), str) and isinstance(step.get("text"), str)
    }
    assert set(missing_text_by_step_id.values()) == missing_step_texts, missing_text_by_step_id

    matches = _ide_binding_payloads(envelopes, _IDE_STEP_BINDING_MEDIA_TYPE)
    assert len(matches) == 1, matches
    match = matches[0]
    assert match.get("testCaseId") == bound_case_id, match
    bound_steps = launch_by_case[bound_case_id][2].get("steps")
    assert isinstance(bound_steps, list) and len(bound_steps) == 1, bound_steps
    bound_step_id = bound_steps[0].get("id")
    assert isinstance(bound_step_id, str) and match.get("pickleStepId") == bound_step_id, match
    assert isinstance(match.get("stepDefinitionId"), str) and match["stepDefinitionId"], match
    assert match.get("matchArguments") == [], match
    definition_path, _ = _ide_assert_file_source_reference(match.get("sourceReference"), consumer, suffix="conftest.py")
    assert definition_path == (consumer.path / "conftest.py").resolve(), definition_path

    diagnostics = _ide_binding_payloads(envelopes, _IDE_DIAGNOSTIC_MEDIA_TYPE)
    missing_diagnostics = [diagnostic for diagnostic in diagnostics if diagnostic.get("kind") == "missing-step"]
    assert len(diagnostics) == len(missing_diagnostics) == 2, diagnostics
    reported_texts: set[str] = set()
    feature_lines = feature_path.read_text(encoding="utf-8").splitlines()
    for diagnostic in missing_diagnostics:
        assert diagnostic.get("severity") == "warning", diagnostic
        assert diagnostic.get("testCaseId") == missing_case_id, diagnostic
        step_id = diagnostic.get("pickleStepId")
        unmatched_text = diagnostic.get("unmatchedStepText")
        assert isinstance(step_id, str) and missing_text_by_step_id.get(step_id) == unmatched_text, diagnostic
        assert isinstance(unmatched_text, str) and unmatched_text in missing_step_texts, diagnostic
        reported_texts.add(unmatched_text)
        source_lines = [
            index
            for index, line in enumerate(feature_lines, start=1)
            if unmatched_text in line
        ]
        assert len(source_lines) == 1 and source_lines[0] > 0, (unmatched_text, source_lines)
        available = diagnostic.get("availableStepDefinitions")
        assert isinstance(available, list) and available, diagnostic
        references = _ide_nested_source_references(available)
        assert references, available
        available_paths = [
            _ide_assert_file_source_reference(reference, consumer)[0]
            for reference in references
        ]
        assert (consumer.path / "conftest.py").resolve() in available_paths, available_paths
    assert reported_texts == missing_step_texts, (reported_texts, missing_diagnostics)


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should report unbound and duplicate scenario bindings with real node and case IDs'
    )
)
def consumer_ide_collection_binding_diagnostics(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(launches) == 2, launches
    nodeids = _ide_collected_nodeids(consumer)
    launch_by_case = {
        launch.get("testCaseId"): launch
        for launch in launches
        if isinstance(launch.get("testCaseId"), str)
    }
    assert len(launch_by_case) == 2, launches
    assert all(launch.get("nodeid") in nodeids for launch in launches), launches
    diagnostics = _ide_binding_payloads(envelopes, _IDE_DIAGNOSTIC_MEDIA_TYPE)
    unbound = [diagnostic for diagnostic in diagnostics if diagnostic.get("kind") == "unbound-scenario"]
    duplicates = [diagnostic for diagnostic in diagnostics if diagnostic.get("kind") == "duplicate-bindings"]
    assert len(unbound) == len(duplicates) == 1, diagnostics
    assert unbound[0].get("severity") == duplicates[0].get("severity") == "warning"
    unbound_path, unbound_line = _ide_assert_source_identity(
        unbound[0].get("sourceIdentity"), consumer, suffix="collection-bindings.feature"
    )
    duplicate_path, duplicate_line = _ide_assert_source_identity(
        duplicates[0].get("sourceIdentity"), consumer, suffix="collection-bindings.feature"
    )
    assert unbound_path == duplicate_path == (consumer.path / "features/collection-bindings.feature").resolve()
    assert unbound_line != duplicate_line, (unbound_line, duplicate_line)

    bindings = duplicates[0].get("bindings")
    assert isinstance(bindings, list) and len(bindings) == 2, duplicates[0]
    binding_nodeids: set[str] = set()
    binding_case_ids: set[str] = set()
    for binding in bindings:
        assert isinstance(binding, dict), binding
        nodeid = binding.get("nodeid")
        case_id = binding.get("testCaseId")
        assert isinstance(nodeid, str) and nodeid in nodeids, binding
        assert "test_first_collection_binding" in nodeid or "test_second_collection_binding" in nodeid, nodeid
        assert isinstance(case_id, str) and case_id in launch_by_case, binding
        assert launch_by_case[case_id].get("nodeid") == nodeid, (binding, launch_by_case[case_id])
        binding_nodeids.add(nodeid)
        binding_case_ids.add(case_id)
    assert len(binding_nodeids) == len(binding_case_ids) == 2, bindings


@then(re.compile(r'consumer artifact "(?P<relative_path>[^"]+)" should report distinct source lines for both outline rows'))
def consumer_ide_outline_row_identities(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(launches) == 3, launches
    test_cases, pickles = _ide_case_records(envelopes)
    rows: dict[str, tuple[dict[str, object], dict[str, object], Path, int]] = {}
    for launch in launches:
        case_id = launch.get("testCaseId")
        pickle_id = launch.get("pickleId")
        nodeid = launch.get("nodeid")
        assert isinstance(case_id, str) and isinstance(pickle_id, str) and isinstance(nodeid, str), launch
        test_case = test_cases[case_id]
        pickle = pickles[pickle_id]
        step_texts = [step.get("text") for step in pickle.get("steps", []) if isinstance(step, dict)]
        matching_row = next((value for value in ("11", "22", "33") if f"the source row is {value}" in step_texts), None)
        assert matching_row is not None, (launch, step_texts)
        assert matching_row not in rows, rows
        source_path, source_line = _ide_assert_source_identity(launch.get("sourceIdentity"), consumer)
        assert source_path.name.endswith(("outline-rows.feature", "narrative-cafe.feature.md")), source_path
        assert nodeid in _ide_collected_nodeids(consumer), launch
        tags = pickle.get("tags", [])
        assert isinstance(tags, list), pickle
        tag_names = {
            tag["name"].removeprefix("@")
            for tag in tags
            if isinstance(tag, dict) and isinstance(tag.get("name"), str)
        }
        if matching_row == "11":
            assert "north-row" in tag_names and "south-row" not in tag_names, (matching_row, tag_names)
        elif matching_row == "22":
            assert "south-row" in tag_names and "north-row" not in tag_names, (matching_row, tag_names)
        else:
            assert not {"north-row", "south-row"}.intersection(tag_names), (matching_row, tag_names)
        rows[matching_row] = (test_case, pickle, source_path, source_line)

    assert set(rows) == {"11", "22", "33"}, rows
    outline_rows = [rows[value] for value in ("11", "22")]
    assert all(row[2] == (consumer.path / "features/outline-rows.feature").resolve() for row in outline_rows)
    assert outline_rows[0][1]["id"] != outline_rows[1][1]["id"], outline_rows
    assert outline_rows[0][0]["id"] != outline_rows[1][0]["id"], outline_rows
    assert outline_rows[0][3] != outline_rows[1][3], outline_rows
    assert outline_rows[0][1]["id"] != rows["33"][1]["id"], rows
    assert rows["33"][2] == (consumer.path / "features/narrative/narrative-cafe.feature.md").resolve(), rows
    assert "café" in str(rows["33"][2].resolve()), rows["33"]

    matches = _ide_binding_payloads(envelopes, _IDE_STEP_BINDING_MEDIA_TYPE)
    assert len(matches) == 3, matches
    case_to_arguments = {
        match["testCaseId"]: match.get("matchArguments")
        for match in matches
        if isinstance(match.get("testCaseId"), str)
    }
    for value, (test_case, pickle, _source_path, _source_line) in rows.items():
        step = pickle["steps"][0]
        test_step = test_case["testSteps"][0]
        assert step["text"] == f"the source row is {value}", step
        assert case_to_arguments[test_case["id"]] == [{"name": "value", "value": int(value)}], case_to_arguments
        assert test_step.get("pickleStepId") == step["id"], test_step
        match = next(item for item in matches if item.get("testCaseId") == test_case["id"])
        _ide_assert_file_source_reference(match.get("sourceReference"), consumer, suffix="conftest.py")


@then(re.compile(r'consumer artifact "(?P<relative_path>[^"]+)" should contain only the current narrative source identity'))
def consumer_ide_current_narrative_identity(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(launches) == 1, launches
    launch = launches[0]
    test_cases, pickles = _ide_case_records(envelopes)
    case_id = launch.get("testCaseId")
    pickle_id = launch.get("pickleId")
    assert isinstance(case_id, str) and isinstance(pickle_id, str), launch
    assert case_id in test_cases and pickle_id in pickles, launch
    assert test_cases[case_id].get("pickleId") == pickle_id, launch
    source_path, _ = _ide_assert_source_identity(launch.get("sourceIdentity"), consumer, suffix="narrative-cafe.feature.md")
    assert source_path == (consumer.path / "features/narrative/narrative-cafe.feature.md").resolve()
    pickle_texts = [step.get("text") for step in pickles[pickle_id].get("steps", []) if isinstance(step, dict)]
    assert pickle_texts == ["the source row is 33"], pickle_texts
    nodeid = launch.get("nodeid")
    assert isinstance(nodeid, str) and nodeid in _ide_collected_nodeids(consumer), launch
    matches = [
        match
        for match in _ide_binding_payloads(envelopes, _IDE_STEP_BINDING_MEDIA_TYPE)
        if match.get("testCaseId") == case_id
    ]
    assert len(matches) == 1 and matches[0].get("matchArguments") == [{"name": "value", "value": 33}], matches
    _ide_assert_file_source_reference(matches[0].get("sourceReference"), consumer, suffix="conftest.py")
    assert not any(
        diagnostic.get("kind") == "duplicate-bindings"
        for diagnostic in _ide_binding_payloads(envelopes, _IDE_DIAGNOSTIC_MEDIA_TYPE)
    ), envelopes


@then(re.compile(r'consumer artifact "(?P<relative_path>[^"]+)" should keep both worker source identities separate'))
def consumer_ide_xdist_source_identities(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(launches) == 2, launches
    test_cases, _ = _ide_case_records(envelopes)
    pickle_messages = [
        pickle
        for envelope in envelopes
        if isinstance((pickle := envelope.get("pickle")), dict)
    ]
    seen_sources: dict[str, dict[str, object]] = {}
    for launch in launches:
        case_id = launch.get("testCaseId")
        pickle_id = launch.get("pickleId")
        nodeid = launch.get("nodeid")
        assert isinstance(case_id, str) and isinstance(pickle_id, str) and isinstance(nodeid, str), launch
        source_path, _ = _ide_assert_source_identity(launch.get("sourceIdentity"), consumer)
        assert source_path.name in {"north-source.feature", "south-source.feature"}, source_path
        assert source_path.name not in seen_sources, seen_sources
        case = test_cases[case_id]
        expected_value = "north" if source_path.name == "north-source.feature" else "south"
        expected_name = "The north source is collected" if expected_value == "north" else "The south source is collected"
        assert case.get("pickleId") == pickle_id, (launch, case)
        matching_pickles = [
            pickle
            for pickle in pickle_messages
            if pickle.get("id") == pickle_id and pickle.get("name") == expected_name
        ]
        assert matching_pickles, (launch, pickle_messages)
        assert case.get("testSteps"), case
        assert all(
            isinstance(pickle.get("steps"), list)
            and pickle["steps"][0].get("text") == f"the worker source is {expected_value}"
            for pickle in matching_pickles
        ), (source_path, matching_pickles)
        assert source_path.name.split("-")[0] in nodeid, nodeid
        seen_sources[source_path.name] = launch
    assert set(seen_sources) == {"north-source.feature", "south-source.feature"}, seen_sources
    assert len({launch["testCaseId"] for launch in launches}) == 2, launches

    matches = _ide_binding_payloads(envelopes, _IDE_STEP_BINDING_MEDIA_TYPE)
    assert len(matches) == 2, matches
    matched_cases = {match.get("testCaseId"): match for match in matches}
    assert set(matched_cases) == {launch.get("testCaseId") for launch in launches}, (matched_cases, launches)
    for source_name, launch in ((name, payload) for name, payload in seen_sources.items()):
        match = matched_cases[launch["testCaseId"]]
        expected_value = "north" if source_name == "north-source.feature" else "south"
        assert match.get("matchArguments") == [{"name": "value", "value": expected_value}], match
        _ide_assert_file_source_reference(match.get("sourceReference"), consumer, suffix="conftest.py")


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should preserve mock-run background and row binding arguments'
    )
)
def consumer_ide_mock_run_outline_arguments(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    matches = _ide_binding_payloads(envelopes, _IDE_STEP_BINDING_MEDIA_TYPE)
    diagnostics = _ide_binding_payloads(envelopes, _IDE_DIAGNOSTIC_MEDIA_TYPE)
    assert len(launches) == 2 and len(matches) == 10, (launches, matches)
    assert all(diagnostic.get("kind") == "unbound-scenario" for diagnostic in diagnostics), diagnostics
    assert not any(diagnostic.get("kind") == "missing-step" for diagnostic in diagnostics), diagnostics

    test_cases, pickles = _ide_case_records(envelopes)
    assert len(test_cases) == 2 and len(pickles) >= 2, (test_cases, pickles)
    nodeids = _ide_collected_nodeids(consumer)
    expected_rows = {
        "amber": {
            "action": "expand",
            "outcome": "expanded",
            "steps": [
                "the feature background opens the account",
                "the rule background prepares the ledger",
                "the selected account is amber",
                "I request expand for account amber",
                "the validation outcome is expanded for account amber",
            ],
            "arguments": [
                [],
                [],
                [{"name": "account", "value": "amber"}],
                [{"name": "action", "value": "expand"}, {"name": "account", "value": "amber"}],
                [{"name": "outcome", "value": "expanded"}, {"name": "account", "value": "amber"}],
            ],
        },
        "birch": {
            "action": "focus",
            "outcome": "focused",
            "steps": [
                "the feature background opens the account",
                "the rule background prepares the ledger",
                "the selected account is birch",
                "I request focus for account birch",
                "the validation outcome is focused for account birch",
            ],
            "arguments": [
                [],
                [],
                [{"name": "account", "value": "birch"}],
                [{"name": "action", "value": "focus"}, {"name": "account", "value": "birch"}],
                [{"name": "outcome", "value": "focused"}, {"name": "account", "value": "birch"}],
            ],
        },
    }
    rows_by_account: dict[str, tuple[dict[str, object], dict[str, object], dict[str, object], int]] = {}
    bindings_by_case: dict[str, list[dict[str, object]]] = {}
    for match in matches:
        case_id = match.get("testCaseId")
        assert isinstance(case_id, str), match
        bindings_by_case.setdefault(case_id, []).append(match)

    feature_path = (consumer.path / "features/explicit-mock-run.feature").resolve()
    excluded_scenarios = {
        "The keyword filter excludes this missing binding",
        "The marker filter excludes this missing binding",
    }
    reported_excluded_scenarios: set[str] = set()
    for diagnostic in diagnostics:
        source_path, source_line = _ide_assert_source_identity(
            diagnostic.get("sourceIdentity"), consumer, suffix="explicit-mock-run.feature"
        )
        assert source_path == feature_path, diagnostic
        source_text = source_path.read_text(encoding="utf-8").splitlines()[source_line - 1]
        scenario_name = source_text.strip().removeprefix("Scenario:").strip()
        assert scenario_name in excluded_scenarios, (diagnostic, source_text)
        reported_excluded_scenarios.add(scenario_name)
    assert reported_excluded_scenarios == excluded_scenarios, (reported_excluded_scenarios, diagnostics)
    for launch in launches:
        case_id = launch.get("testCaseId")
        pickle_id = launch.get("pickleId")
        nodeid = launch.get("nodeid")
        assert isinstance(case_id, str) and isinstance(pickle_id, str) and isinstance(nodeid, str), launch
        assert nodeid in nodeids and "test_selected_outline_validation" in nodeid, launch
        assert case_id in test_cases and pickle_id in pickles, launch
        test_case = test_cases[case_id]
        pickle = pickles[pickle_id]
        assert test_case.get("pickleId") == pickle_id, (launch, test_case)

        source_identity = launch.get("sourceIdentity")
        source_path, source_line = _ide_assert_source_identity(source_identity, consumer)
        assert source_path == feature_path, (source_path, feature_path)
        assert isinstance(source_identity, dict), source_identity
        assert _ide_source_path(source_identity.get("scenarioUri"), consumer) == feature_path, source_identity
        row_id = source_identity.get("rowId")
        assert isinstance(row_id, str) and row_id, source_identity
        assert source_identity.get("rowLine") == source_line, source_identity
        source_fields = [field.strip() for field in feature_path.read_text(encoding="utf-8").splitlines()[source_line - 1].strip().strip("|").split("|")]
        assert len(source_fields) == 3, (source_line, source_fields)
        account, action, outcome = source_fields
        assert account in expected_rows and expected_rows[account]["action"] == action, (source_line, source_fields)
        assert expected_rows[account]["outcome"] == outcome, (source_line, source_fields)
        assert account not in rows_by_account, rows_by_account

        pickle_steps = pickle.get("steps")
        raw_case_steps = test_case.get("testSteps")
        expected = expected_rows[account]
        assert isinstance(pickle_steps, list) and isinstance(raw_case_steps, list), (pickle, test_case)
        case_steps = [
            step
            for step in raw_case_steps
            if isinstance(step, dict) and isinstance(step.get("pickleStepId"), str)
        ]
        assert [step.get("text") for step in pickle_steps if isinstance(step, dict)] == expected["steps"], pickle_steps
        assert len(case_steps) == len(pickle_steps) == 5, (raw_case_steps, pickle_steps)
        ast_node_ids = pickle.get("astNodeIds")
        assert isinstance(ast_node_ids, list) and row_id in ast_node_ids, (row_id, ast_node_ids)

        case_bindings = bindings_by_case.get(case_id, [])
        assert len(case_bindings) == 5, (case_id, case_bindings)
        matches_by_step = {match.get("pickleStepId"): match for match in case_bindings}
        assert len(matches_by_step) == 5, case_bindings
        for pickle_step, test_step, expected_arguments in zip(pickle_steps, case_steps, expected["arguments"], strict=True):
            assert isinstance(pickle_step, dict) and isinstance(test_step, dict), (pickle_step, test_step)
            step_id = pickle_step.get("id")
            assert isinstance(step_id, str) and test_step.get("pickleStepId") == step_id, (pickle_step, test_step)
            match = matches_by_step.get(step_id)
            assert isinstance(match, dict), (step_id, case_bindings)
            assert isinstance(match.get("stepDefinitionId"), str) and match["stepDefinitionId"], match
            assert match.get("matchArguments") == expected_arguments, (pickle_step, match, expected_arguments)
            definition_path, _ = _ide_assert_file_source_reference(
                match.get("sourceReference"), consumer, suffix="conftest.py"
            )
            assert definition_path == (consumer.path / "conftest.py").resolve(), definition_path

        rows_by_account[account] = (launch, test_case, pickle, source_line)

    assert set(rows_by_account) == set(expected_rows), rows_by_account
    amber = rows_by_account["amber"]
    birch = rows_by_account["birch"]
    assert amber[0].get("testCaseId") != birch[0].get("testCaseId"), (amber, birch)
    assert amber[0].get("pickleId") != birch[0].get("pickleId"), (amber, birch)
    assert amber[1].get("id") != birch[1].get("id"), (amber, birch)
    assert amber[2].get("id") != birch[2].get("id"), (amber, birch)
    assert amber[3] != birch[3], (amber, birch)
    assert amber[2].get("astNodeIds") != birch[2].get("astNodeIds"), (amber, birch)


@then(
    re.compile(
        r'consumer artifacts "(?P<first_path>[^"]+)" and "(?P<second_path>[^"]+)" '
        r'should preserve mock-run session and worker identities'
    )
)
def consumer_ide_mock_run_sessions_and_workers_are_isolated(
    first_path: str,
    second_path: str,
    consumer: ConsumerProject,
) -> None:
    first_envelopes = _ide_binding_envelopes(first_path, consumer)
    second_envelopes = _ide_binding_envelopes(second_path, consumer)
    first_launches = _ide_binding_payloads(first_envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    second_launches = _ide_binding_payloads(second_envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(first_launches) == 1 and len(second_launches) == 2, (first_launches, second_launches)
    first_run_ids = [
        run["id"]
        for envelope in first_envelopes
        if isinstance((run := envelope.get("testRunStarted")), dict) and isinstance(run.get("id"), str)
    ]
    second_run_ids = [
        run["id"]
        for envelope in second_envelopes
        if isinstance((run := envelope.get("testRunStarted")), dict) and isinstance(run.get("id"), str)
    ]
    assert len(first_run_ids) == len(second_run_ids) == 1, (first_run_ids, second_run_ids)
    assert first_run_ids[0] != second_run_ids[0], (first_run_ids, second_run_ids)

    first_launch = first_launches[0]
    first_case_id = first_launch.get("testCaseId")
    first_pickle_id = first_launch.get("pickleId")
    assert isinstance(first_case_id, str) and isinstance(first_pickle_id, str), first_launch
    first_source, _ = _ide_assert_source_identity(
        first_launch.get("sourceIdentity"), consumer, suffix="north-source.feature"
    )
    assert first_source == (consumer.path / "features/first-session/north-source.feature").resolve(), first_source
    first_test_cases, first_pickles = _ide_case_records(first_envelopes)
    assert first_case_id in first_test_cases and first_pickle_id in first_pickles, first_launch
    assert first_test_cases[first_case_id].get("pickleId") == first_pickle_id, first_launch
    first_steps = first_pickles[first_pickle_id].get("steps")
    assert isinstance(first_steps, list) and [step.get("text") for step in first_steps] == [
        "the worker source is north"
    ], first_steps

    observations = []
    for worker_id in ("main", "gw0", "gw1"):
        observation_path = _consumer_artifact_path(f"worker-nodeids-{worker_id}.ndjson", consumer)
        assert observation_path.is_file(), f"worker {worker_id} did not write its observation file"
        observations.extend(
            json.loads(line)
            for line in observation_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    assert len(observations) == 3, observations
    observations_by_nodeid = {entry.get("nodeid"): entry.get("worker") for entry in observations}
    assert len(observations_by_nodeid) == 3, observations
    first_nodes = [nodeid for nodeid in observations_by_nodeid if "first-session/north-source.feature" in nodeid]
    second_nodes = [nodeid for nodeid in observations_by_nodeid if "second-session/" in nodeid]
    assert len(first_nodes) == 1 and len(second_nodes) == 2, observations
    assert observations_by_nodeid[first_nodes[0]] == "main", observations
    assert {observations_by_nodeid[nodeid] for nodeid in second_nodes} == {"gw0", "gw1"}, observations

    second_test_cases, second_pickles = _ide_case_records(second_envelopes)
    second_case_ids: set[str] = set()
    second_pickle_ids: set[str] = set()
    second_source_values: dict[Path, str] = {}
    second_case_values: dict[str, str] = {}
    expected_source_values = {
        (consumer.path / "features/second-session/north-source.feature").resolve(): "north",
        (consumer.path / "features/second-session/south-source.feature").resolve(): "south",
    }
    for launch in second_launches:
        case_id = launch.get("testCaseId")
        pickle_id = launch.get("pickleId")
        nodeid = launch.get("nodeid")
        assert isinstance(case_id, str) and isinstance(pickle_id, str) and isinstance(nodeid, str), launch
        assert nodeid in second_nodes and nodeid in observations_by_nodeid, launch
        worker_id = observations_by_nodeid[nodeid]
        assert isinstance(worker_id, str) and worker_id in {"gw0", "gw1"}, (launch, worker_id)
        assert case_id.startswith(f"{worker_id}:"), (worker_id, launch)
        assert case_id in second_test_cases and pickle_id in second_pickles, launch
        assert second_test_cases[case_id].get("pickleId") == pickle_id, launch
        second_source, _ = _ide_assert_source_identity(launch.get("sourceIdentity"), consumer)
        assert second_source in expected_source_values, (launch, second_source)
        expected_value = expected_source_values[second_source]
        expected_nodeid_prefix = f"features/second-session/{expected_value}-source.feature::"
        assert nodeid.startswith(expected_nodeid_prefix), (launch, expected_nodeid_prefix)
        second_source_values[second_source] = expected_value
        second_case_values[case_id] = expected_value

        pickle = second_pickles[pickle_id]
        pickle_steps = pickle.get("steps")
        assert pickle.get("uri") == f"file:{expected_value}-source.feature", (launch, pickle)
        assert pickle.get("name") == f"The {expected_value} source is collected", (launch, pickle)
        assert isinstance(pickle_steps, list) and [step.get("text") for step in pickle_steps] == [
            f"the worker source is {expected_value}"
        ], (launch, pickle_steps)
        second_case_ids.add(case_id)
        second_pickle_ids.add(pickle_id)

    assert len(second_case_ids) == len(second_pickle_ids) == 2, second_launches
    assert second_source_values == expected_source_values, (second_source_values, expected_source_values)
    assert first_case_id not in second_case_ids and first_pickle_id not in second_pickle_ids, (
        first_launch,
        second_launches,
    )
    second_matches = _ide_binding_payloads(second_envelopes, _IDE_STEP_BINDING_MEDIA_TYPE)
    assert len(second_matches) == 2, second_matches
    for match in second_matches:
        case_id = match.get("testCaseId")
        step_id = match.get("pickleStepId")
        assert isinstance(case_id, str) and case_id in second_case_ids, match
        expected_value = second_case_values[case_id]
        worker_id = next(
            observations_by_nodeid[launch["nodeid"]]
            for launch in second_launches
            if launch.get("testCaseId") == case_id
        )
        assert isinstance(worker_id, str) and worker_id in {"gw0", "gw1"}, (match, worker_id)
        assert isinstance(step_id, str), match
        launch = next(item for item in second_launches if item.get("testCaseId") == case_id)
        pickle_id = launch.get("pickleId")
        pickle_steps = second_pickles[pickle_id].get("steps") if isinstance(pickle_id, str) else None
        matching_steps = [
            step
            for step in pickle_steps or []
            if isinstance(step, dict) and step.get("id") == step_id
        ]
        assert len(matching_steps) == 1, (match, pickle_steps)
        assert match.get("matchArguments") == [{"name": "value", "value": expected_value}], match
        definition_path, _ = _ide_assert_file_source_reference(
            match.get("sourceReference"), consumer, suffix="conftest.py"
        )
        assert definition_path == (consumer.path / "conftest.py").resolve(), definition_path


@then(
    re.compile(
        r'consumer artifact "(?P<relative_path>[^"]+)" should contain one complete duplicate binding diagnostic '
        r'for both worker modules'
    )
)
def consumer_ide_split_worker_duplicate_bindings(relative_path: str, consumer: ConsumerProject) -> None:
    envelopes = _ide_binding_envelopes(relative_path, consumer)
    launches = _ide_binding_payloads(envelopes, _IDE_LAUNCH_MEDIA_TYPE)
    assert len(launches) == 2, launches

    launches_by_nodeid: dict[str, dict[str, object]] = {}
    for launch in launches:
        nodeid = launch.get("nodeid")
        case_id = launch.get("testCaseId")
        assert isinstance(nodeid, str) and nodeid, launch
        assert isinstance(case_id, str) and case_id, launch
        assert nodeid not in launches_by_nodeid, launches
        source_path, _ = _ide_assert_source_identity(
            launch.get("sourceIdentity"), consumer, suffix="split-worker-bindings.feature"
        )
        assert source_path == (consumer.path / "features/split-worker-bindings.feature").resolve(), source_path
        launches_by_nodeid[nodeid] = launch

    assert len({launch.get("testCaseId") for launch in launches}) == 2, launches
    assert {"test_north_duplicate_binding.py", "test_south_duplicate_binding.py"} == {
        next(name for name in ("test_north_duplicate_binding.py", "test_south_duplicate_binding.py") if name in nodeid)
        for nodeid in launches_by_nodeid
    }, launches_by_nodeid

    worker_pairs = []
    for worker_id in ("gw0", "gw1"):
        worker_path = _consumer_artifact_path(f"worker-nodeids-{worker_id}.txt", consumer)
        assert worker_path.is_file(), f"worker {worker_id} did not write its nodeid observation"
        worker_pairs.extend(
            tuple(line.split("\t", maxsplit=1))
            for line in worker_path.read_text(encoding="utf-8").splitlines()
        )
    assert len(worker_pairs) == 2 and all(len(pair) == 2 for pair in worker_pairs), worker_pairs
    workers_by_nodeid = {nodeid: worker for nodeid, worker in worker_pairs}
    assert set(workers_by_nodeid) == set(launches_by_nodeid), (workers_by_nodeid, launches_by_nodeid)
    assert len(set(workers_by_nodeid.values())) == 2, workers_by_nodeid

    diagnostics = [
        diagnostic
        for diagnostic in _ide_binding_payloads(envelopes, _IDE_DIAGNOSTIC_MEDIA_TYPE)
        if diagnostic.get("kind") == "duplicate-bindings"
    ]
    assert len(diagnostics) == 1, diagnostics
    diagnostic = diagnostics[0]
    assert diagnostic.get("severity") == "warning", diagnostic
    source_path, _ = _ide_assert_source_identity(
        diagnostic.get("sourceIdentity"), consumer, suffix="split-worker-bindings.feature"
    )
    assert source_path == (consumer.path / "features/split-worker-bindings.feature").resolve(), diagnostic

    bindings = diagnostic.get("bindings")
    assert isinstance(bindings, list) and len(bindings) == 2, diagnostic
    actual_pairs: set[tuple[str, str]] = set()
    for binding in bindings:
        assert isinstance(binding, dict), binding
        nodeid = binding.get("nodeid")
        case_id = binding.get("testCaseId")
        assert isinstance(nodeid, str) and nodeid in launches_by_nodeid, binding
        assert isinstance(case_id, str) and case_id, binding
        launch = launches_by_nodeid[nodeid]
        assert launch.get("testCaseId") == case_id, (binding, launch)
        actual_pairs.add((nodeid, case_id))
    expected_pairs = {
        (nodeid, launch["testCaseId"])
        for nodeid, launch in launches_by_nodeid.items()
        if isinstance(launch.get("testCaseId"), str)
    }
    assert actual_pairs == expected_pairs, (actual_pairs, expected_pairs)


@then(re.compile(r'consumer marker artifact "(?P<relative_path>[^"]+)" should contain the normal BDD execution markers'))
def consumer_mock_run_normal_execution_markers(relative_path: str, consumer: ConsumerProject) -> None:
    marker_path = _consumer_artifact_path(relative_path, consumer)
    assert marker_path.is_file(), f"consumer execution marker artifact does not exist: {marker_path}"
    actual = marker_path.read_text(encoding="utf-8").splitlines()
    expected = [
        "after-scenario",
        "after-step",
        "before-scenario",
        "before-step",
        "before-step-call",
        "run-scenario",
        "step-body",
        "test-function-body",
    ]
    assert sorted(actual) == sorted(expected), (actual, expected)


@then(
    re.compile(
        r'consumer marker artifact "(?P<relative_path>[^"]+)" should contain only (?P<count>\d+) '
        r'instances? of the pytest test-function body marker'
    )
)
def consumer_mock_run_only_test_function_markers(relative_path: str, count: str, consumer: ConsumerProject) -> None:
    marker_path = _consumer_artifact_path(relative_path, consumer)
    assert marker_path.is_file(), f"the ordinary pytest function body did not run: {marker_path}"
    actual = marker_path.read_text(encoding="utf-8").splitlines()
    expected = ["test-function-body"] * int(count)
    assert actual == expected, (actual, expected)


@then(
    re.compile(
        r'collection should reject consumer feature "(?P<feature_path>[^"]+)", scenario "(?P<scenario_name>[^"]+)", '
        r'and step "(?P<step_text>[^"]+)" before files "(?P<hook_path>[^"]+)" and "(?P<body_path>[^"]+)" are created'
    )
)
def consumer_all_unmatched_collection_usage_error(
    feature_path: str,
    scenario_name: str,
    step_text: str,
    hook_path: str,
    body_path: str,
    consumer: ConsumerProject,
) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    normalized_output = _normalized_path_text(output)
    expected_source = _consumer_artifact_path(feature_path, consumer)
    normalized_source = expected_source.as_posix()
    source_references = (normalized_source, feature_path, f"file:{expected_source.name}", expected_source.name)
    feature_lines = expected_source.read_text(encoding="utf-8").splitlines()
    scenario_lines = [
        line_number
        for line_number, line in enumerate(feature_lines, start=1)
        if line.strip() == f"Scenario: {scenario_name}"
    ]
    assert len(scenario_lines) == 1, (scenario_name, scenario_lines, feature_lines)
    scenario_line = scenario_lines[0]
    step_line_numbers: list[int] = []
    for line_number, line in enumerate(feature_lines[scenario_line:], start=scenario_line + 1):
        stripped = line.strip()
        if stripped.startswith(("Scenario:", "Scenario Outline:", "Rule:", "Feature:")):
            break
        if re.match(r"^(?:Given|When|Then|And|But|\*)\s+", stripped):
            step_line_numbers.append(line_number)
    expected_line_references = [
        f"{normalized_source}:{line_number}:" for line_number in (scenario_line, *step_line_numbers)
    ]
    checks = {
        f"pytest UsageError exit code 4; got {result.returncode}": result.returncode == 4,
        "pytest emitted its UsageError summary": bool(re.search(r"(?im)^ERROR:", output))
        or "UsageError" in output,
        f"output identifies source {feature_path!r}": any(
            source_reference in normalized_output for source_reference in source_references
        ),
        f"output identifies exact scenario and step lines {expected_line_references!r}": all(
            reference in normalized_output for reference in expected_line_references
        ),
        f"output identifies scenario {scenario_name!r}": scenario_name in output,
        f"output identifies unmatched step {step_text!r}": step_text in output,
        f"runtime hook file {hook_path!r} was not created": not _consumer_artifact_path(hook_path, consumer).exists(),
        f"test body file {body_path!r} was not created": not _consumer_artifact_path(body_path, consumer).exists(),
    }
    failures = [message for message, passed in checks.items() if not passed]
    assert not failures, f"all-unmatched collection guard checks failed: {failures}\npytest output:\n{output}"


@then(
    re.compile(
        r'pytest should skip all-unmatched scenario "(?P<scenario_name>[^"]+)" with a meaningful reason '
        r'from feature "(?P<feature_path>[^"]+)" before files "(?P<hook_path>[^"]+)" '
        r'and "(?P<body_path>[^"]+)" are created'
    )
)
def consumer_all_unmatched_skip_has_reason(
    scenario_name: str, feature_path: str, hook_path: str, body_path: str, consumer: ConsumerProject
) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    normalized_output = _normalized_path_text(output)
    has_skip = bool(re.search(r"\bskip(?:ped|s)?\b", output, re.IGNORECASE))
    has_meaningful_reason = bool(
        re.search(r"unmatch|no (?:matching |bound )?steps?|step definitions?|empty scenario", output, re.IGNORECASE)
    )
    feature_source = _consumer_artifact_path(feature_path, consumer)
    feature_lines = feature_source.read_text(encoding="utf-8").splitlines()
    scenario_lines = [
        line_number
        for line_number, line in enumerate(feature_lines, start=1)
        if line.strip() == f"Scenario: {scenario_name}"
    ]
    assert len(scenario_lines) == 1, (scenario_name, scenario_lines, feature_lines)
    normalized_feature_source = feature_source.as_posix()
    scenario_location = f"{normalized_feature_source}:{scenario_lines[0]}"
    checks = {
        f"pytest exited successfully; got {result.returncode}": result.returncode == 0,
        "pytest reports the selected scenario as skipped": has_skip,
        "pytest includes an informative no-binding reason": has_meaningful_reason,
        f"pytest skip reason identifies source location {scenario_location!r}": scenario_location in normalized_output,
        f"pytest output identifies scenario {scenario_name!r}": scenario_name in output,
        f"pytest output identifies feature source {feature_path!r}": any(
            _normalized_path_text(source) in normalized_output
            for source in (normalized_feature_source, feature_path, feature_source.name)
        ),
        f"runtime hook file {hook_path!r} was not created": not _consumer_artifact_path(hook_path, consumer).exists(),
        f"test body file {body_path!r} was not created": not _consumer_artifact_path(body_path, consumer).exists(),
    }
    failures = [message for message, passed in checks.items() if not passed]
    assert not failures, f"all-unmatched skip checks failed: {failures}\npytest output:\n{output}"


@then(
    re.compile(
        r'pytest output should identify source "(?P<reported_path>[^"]+)" at the line containing '
        r'"(?P<source_text>[^"]+)" in consumer feature "(?P<feature_path>[^"]+)"'
    )
)
def consumer_pytest_output_identifies_source_line(
    reported_path: str, source_text: str, feature_path: str, consumer: ConsumerProject
) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    source_path = _consumer_artifact_path(feature_path, consumer)
    source_lines = source_path.read_text(encoding="utf-8").splitlines()
    line_numbers = [
        line_number
        for line_number, line in enumerate(source_lines, start=1)
        if line.strip() == source_text
    ]
    assert len(line_numbers) == 1, (source_text, line_numbers, source_lines)
    expected_reference = f"{reported_path}:{line_numbers[0]}"
    output = f"{result.stdout}\n{result.stderr}"
    assert expected_reference in output, (
        f"pytest output did not identify source location {expected_reference!r}:\n{output}"
    )


@then("pytest output should report exactly 2 deselected items")
def consumer_pytest_reports_two_deselected_items(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}"
    assert re.search(r"\b2 deselected\b", output), output


@then(re.compile(r'consumer marker file "(?P<relative_path>[^"]+)" should contain lines "(?P<lines>[^"]+)"'))
def consumer_marker_file_contains_lines(relative_path: str, lines: str, consumer: ConsumerProject) -> None:
    marker_path = _consumer_artifact_path(relative_path, consumer)
    actual = marker_path.read_text(encoding="utf-8").splitlines()
    expected = [line.strip() for line in lines.split(",")]
    assert actual == expected, (actual, expected)


@given("the installed consumer exposes a debugger failure BDD probe")
def install_debugger_failure_probe(consumer: ConsumerProject) -> None:
    (consumer.path / "conftest.py").write_text(
        dedent(
            '''\
            import json
            import re
            from pathlib import Path

            from pytest_cuke import given, then, when

            def pytest_configure(config):
                config.addinivalue_line(
                    "markers",
                    "mcp-debug-probe: marker for the Debug MCP installed-consumer probe",
                )

            def pytest_cuke_debug_mcp_artifact_created(
                nodeid, pytest_phase, bdd_metadata, json_path, markdown_path, status, summary
            ):
                observation = {
                    "nodeid": nodeid,
                    "pytest_phase": pytest_phase,
                    "bdd_metadata": bdd_metadata,
                    "json_path": str(json_path),
                    "markdown_path": str(markdown_path),
                    "status": status,
                    "summary": summary,
                }
                Path("debug-mcp-artifact-hook.json").write_text(
                    json.dumps(observation, ensure_ascii=False, sort_keys=True), encoding="utf-8"
                )

            @given("the debugger probe records its setup completion")
            def record_probe_setup():
                Path("probe-setup.log").write_text("setup completed\\n", encoding="utf-8")

            @when(re.compile(r'the debugger probe raises "(?P<message>[^"]+)"'))
            def raise_probe_failure(message):
                raise RuntimeError(message)

            @then("the debugger probe continuation should not run")
            def record_probe_continuation():
                Path("probe-continuation.log").write_text("unexpected\\n", encoding="utf-8")
            '''
        ),
        encoding="utf-8",
    )
    (consumer.path / "features").mkdir(exist_ok=True)
    (consumer.path / "features" / "debug-mcp-probe.feature").write_text(
        dedent(
            '''\
            Feature: MCP failure inspection probe
              @mcp-debug-probe
              Scenario Outline: The client can inspect the failing BDD step for <probe_id>
                Given the debugger probe records its setup completion
                When the debugger probe raises "<message>"
                Then the debugger probe continuation should not run

                Examples:
                  | probe_id       | message                       |
                  | outline-row-17 | debug MCP failure sentinel |
            '''
        ),
        encoding="utf-8",
    )


@given("the installed consumer exposes an ordinary passing pytest test")
def install_ordinary_passing_pytest_test(consumer: ConsumerProject) -> None:
    tests = consumer.path / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "test_ordinary_pass.py").write_text(
        dedent(
            '''\
            from pathlib import Path

            def test_ordinary_pytest_run_passes():
                Path("ordinary-run.marker").write_text("passed\\n", encoding="utf-8")
            '''
        ),
        encoding="utf-8",
    )


def _write_plain_pytest_failure(consumer: ConsumerProject, *, phase: str, delayed: bool = False) -> None:
    assert phase in {"call", "setup", "teardown"}, phase
    source = """
        import time

        def test_plain_pytest_failure():
            time.sleep(1.25)
            raise RuntimeError("debug MCP timeout sentinel")
    """ if delayed else None
    if source is None and phase == "call":
        source = '''\
            def test_plain_pytest_failure():
                raise RuntimeError("debug MCP call failure sentinel")
        '''
    elif source is None and phase == "setup":
        source = '''\
            import pytest

            @pytest.fixture(autouse=True)
            def fail_during_setup():
                raise RuntimeError("debug MCP setup failure sentinel")

            def test_plain_pytest_failure():
                raise AssertionError("setup failure should prevent the test body")
        '''
    elif source is None and phase == "teardown":
        source = '''\
            import pytest

            @pytest.fixture(autouse=True)
            def fail_during_teardown():
                yield
                raise RuntimeError("debug MCP teardown failure sentinel")

            def test_plain_pytest_failure():
                pass
        '''
    (consumer.path / "features").mkdir(exist_ok=True)
    (consumer.path / "test_plain_pytest_failure.py").write_text(dedent(source), encoding="utf-8")
    consumer._mcp_expected_plain_phase = phase
    consumer._mcp_expected_plain_message = (
        "debug MCP timeout sentinel" if delayed else f"debug MCP {phase} failure sentinel"
    )


@given("the installed consumer has a trailing pytest test that waits after release")
def install_trailing_debug_mcp_test(consumer: ConsumerProject) -> None:
    (consumer.path / "test_z_after_debug_mcp_failure.py").write_text(
        dedent(
            '''\
            import time

            def test_wait_after_debug_mcp_failure_release():
                time.sleep(2.0)
            '''
        ),
        encoding="utf-8",
    )


@given("the installed consumer exposes a plain pytest call failure")
def install_plain_pytest_call_failure(consumer: ConsumerProject) -> None:
    _write_plain_pytest_failure(consumer, phase="call")


@given("the installed consumer records Debug MCP artifact hook calls")
def install_plain_debug_mcp_artifact_hook(consumer: ConsumerProject) -> None:
    (consumer.path / "conftest.py").write_text(
        dedent(
            '''\
            import json
            from pathlib import Path

            def pytest_cuke_debug_mcp_artifact_created(
                nodeid, pytest_phase, bdd_metadata, json_path, markdown_path, status, summary
            ):
                observation = {
                    "nodeid": nodeid,
                    "pytest_phase": pytest_phase,
                    "bdd_metadata": bdd_metadata,
                    "json_path": str(json_path),
                    "markdown_path": str(markdown_path),
                    "status": status,
                    "summary": summary,
                }
                Path("debug-mcp-artifact-hook.json").write_text(
                    json.dumps(observation, ensure_ascii=False, sort_keys=True), encoding="utf-8"
                )
            '''
        ),
        encoding="utf-8",
    )


@given(re.compile(r'the installed consumer exposes a plain pytest failure during "(?P<phase>setup|teardown)"'))
def install_plain_pytest_phase_failure(phase: str, consumer: ConsumerProject) -> None:
    _write_plain_pytest_failure(consumer, phase=phase)


@given("the installed consumer exposes a delayed plain pytest failure")
def install_delayed_plain_pytest_failure(consumer: ConsumerProject) -> None:
    _write_plain_pytest_failure(consumer, phase="call", delayed=True)


@given("the installed consumer exposes two ordered debugger failures")
def install_two_ordered_debugger_failures(consumer: ConsumerProject) -> None:
    install_debugger_failure_probe(consumer)
    feature_path = consumer.path / "features" / "debug-mcp-probe.feature"
    feature = feature_path.read_text(encoding="utf-8")
    first_row = "| outline-row-17 | debug MCP failure sentinel |"
    assert feature.count(first_row) == 1, feature
    feature = feature.replace(
        first_row,
        f"{first_row}\n                  | outline-row-18 | debug MCP failure sentinel |",
    )
    feature_path.write_text(feature, encoding="utf-8")


@given("the installed consumer has a file blocking its configured artifact directory")
def install_debug_mcp_artifact_path_blocker(consumer: ConsumerProject) -> None:
    blocker = consumer.path / "occupied-root"
    blocker.write_text("this file prevents creation of occupied-root/child\n", encoding="utf-8")
    assert blocker.is_file(), blocker


@given("the installed consumer has a small mcp-pdb debug target")
def install_debug_mcp_debug_target(consumer: ConsumerProject) -> None:
    (consumer.path / "debug-mcp-debugger-target.py").write_text(
        dedent(
            '''\
            from pathlib import Path

            Path("debugger-continuation-completed.txt").write_text("continued\\n", encoding="utf-8")
            '''
        ),
        encoding="utf-8",
    )


@given("the consumer has a startup guard for MCP imports and child processes")
def install_mcp_startup_guard(consumer: ConsumerProject) -> None:
    guard_directory = consumer.path / "startup-guard"
    guard_directory.mkdir(exist_ok=True)
    (guard_directory / "sitecustomize.py").write_text(
        dedent(
            '''\
            import atexit
            import builtins
            import os
            import signal
            import subprocess
            from pathlib import Path

            observation = Path(os.environ["CUKE_MCP_GUARD"])

            def record(value):
                observation.parent.mkdir(parents=True, exist_ok=True)
                with observation.open("a", encoding="utf-8") as stream:
                    stream.write(value + "\\n")

            original_import = builtins.__import__

            def observed_import(name, *args, **kwargs):
                if name == "mcp" or name.startswith("mcp.") or name == "mcp_pdb":
                    record("import:" + name)
                return original_import(name, *args, **kwargs)

            builtins.__import__ = observed_import
            original_popen = subprocess.Popen

            class ObservedPopen(original_popen):
                def __init__(self, *args, **kwargs):
                    command = args[0] if args else kwargs.get("args", "unknown")
                    command_text = repr(command).lower()
                    is_debugger_backend = "pytest_cuke.debug_mcp.backend" in command_text
                    if (
                        os.name == "nt"
                        and os.environ.get("CUKE_MCP_GRACEFUL_CTRL_BREAK") == "1"
                        and is_debugger_backend
                    ):
                        kwargs = dict(kwargs)
                        kwargs["creationflags"] = (
                            kwargs.get("creationflags", 0) | subprocess.CREATE_NEW_PROCESS_GROUP
                        )
                        child_env = kwargs.get("env")
                        child_env = dict(os.environ if child_env is None else child_env)
                        child_env["CUKE_MCP_ROLE"] = "backend"
                        kwargs["env"] = child_env
                    super().__init__(*args, **kwargs)
                    self._cuke_mcp_debugger_backend = is_debugger_backend
                    observed_commands = ("mcp-pdb", "mcp_pdb", "pytest_cuke.debug_mcp.backend")
                    if any(command_name in command_text for command_name in observed_commands):
                        record(f"child:{self.pid}:{repr(command)}")
                        atexit.register(lambda child=self: record(f"child-status:{child.pid}:{child.poll()}"))
                    if is_debugger_backend:
                        record(f"backend-process-group:{self.pid}:{kwargs.get('creationflags', 0)}")

                def terminate(self):
                    if getattr(self, "_cuke_mcp_debugger_backend", False):
                        record(f"backend-cleanup:{self.pid}")
                    return super().terminate()

            subprocess.Popen = ObservedPopen

            if os.name == "nt" and os.environ.get("CUKE_MCP_GRACEFUL_CTRL_BREAK") == "1":
                role = os.environ.get("CUKE_MCP_ROLE")
                if role in {"consumer", "backend"}:
                    def handle_ctrl_break(signum, frame):
                        record(f"signal:SIGBREAK:{role}:{os.getpid()}")
                        if role == "consumer":
                            signal.default_int_handler(signum, frame)

                    signal.signal(signal.SIGBREAK, handle_ctrl_break)
                    record(f"signal-handler-ready:{role}:{os.getpid()}")
            '''
        ),
        encoding="utf-8",
    )
    consumer.env["PYTHONPATH"] = str(guard_directory)
    consumer.env["CUKE_MCP_GUARD"] = str(consumer.path / "mcp-startup-observations.log")


@given("the consumer holds an available loopback port open")
def reserve_debug_mcp_port(consumer: ConsumerProject) -> None:
    import socket

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    consumer._mcp_occupied_socket = listener
    consumer._mcp_occupied_port = listener.getsockname()[1]


@given("the installed consumer has no optional Debug MCP dependencies")
def uninstall_debug_mcp_extra(consumer: ConsumerProject) -> None:
    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed-consumer contract requires uv to manage optional packages"
    uninstall = subprocess.run(
        [
            uv_executable,
            "pip",
            "uninstall",
            "--python",
            str(consumer.python),
            "mcp",
            "mcp-pdb",
            "uvicorn",
            "pydantic",
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert uninstall.returncode == 0, f"could not remove optional Debug MCP packages:\n{uninstall.stdout}\n{uninstall.stderr}"
    check = subprocess.run(
        [
            str(consumer.python),
            "-c",
            "import importlib.util, sys; sys.exit(1 if any(importlib.util.find_spec(name) for name in ('mcp', 'mcp_pdb', 'uvicorn', 'pydantic')) else 0)",
        ],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert check.returncode == 0, f"optional Debug MCP dependencies remain importable:\n{check.stdout}\n{check.stderr}"


@given("the consumer has a bindable non-loopback address for MCP")
def choose_debug_mcp_nonlocal_host(consumer: ConsumerProject) -> None:
    import ipaddress
    import socket

    import pytest

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 9))
        address = probe.getsockname()[0]
    except OSError as error:
        pytest.skip(f"non-loopback host warning cannot be exercised without an outbound interface: {error}")
    finally:
        probe.close()
    parsed = ipaddress.ip_address(address)
    if parsed.is_loopback or parsed.is_unspecified:
        pytest.skip(f"no non-loopback source address is available: {address}")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((address, 0))
    except OSError as error:
        pytest.skip(f"non-loopback source address cannot be bound: {error}")
    finally:
        listener.close()
    consumer._mcp_nonlocal_host = address


@given("installed pytest starts in an isolated signal process group")
def configure_consumer_pytest_signal_group(consumer: ConsumerProject) -> None:
    consumer._mcp_signal_process_group = True
    if os.name == "nt":
        consumer.env["CUKE_MCP_GRACEFUL_CTRL_BREAK"] = "1"
        consumer.env["CUKE_MCP_ROLE"] = "consumer"


@given("the installed consumer has the optional debug MCP extra installed")
def install_debug_mcp_extra(consumer: ConsumerProject) -> None:
    implementation, sys_platform = _consumer_python_implementation_and_platform(consumer)
    _require_debug_mcp_capability(implementation, sys_platform)
    if implementation.casefold() != "cpython":
        pytest.skip("Debug MCP extra installation acceptance targets CPython")

    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed-consumer contract requires uv to install the optional MCP extra"
    install = subprocess.run(
        [uv_executable, "pip", "install", "--python", str(consumer.python), f"{consumer.artifact}[debug-mcp]"],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert install.returncode == 0, (
        "could not install the optional debug-mcp consumer extra:\n"
        f"{install.stdout}\n{install.stderr}"
    )


@then("the Debug MCP install guard should exclude only PyPy on Windows")
def debug_mcp_install_guard_excludes_only_pypy_windows() -> None:
    with pytest.raises(pytest.skip.Exception) as outcome:
        _require_debug_mcp_capability("PyPy", "win32")
    assert str(outcome.value) == _DEBUG_MCP_PYPY_WINDOWS_SKIP_REASON
    _require_debug_mcp_capability("PyPy", "linux")
    _require_debug_mcp_capability("CPython", "win32")
    _require_debug_mcp_capability("CPython", "linux")


@then("the installed debug MCP extra should be importable on CPython 3.11 or newer and resolve a supported MCP SDK version")
def installed_debug_mcp_extra_is_supported_cpython(consumer: ConsumerProject) -> None:
    probe = (
        "import importlib, json, platform, sys\n"
        "from importlib.metadata import version\n"
        "for module in ('cryptography', 'mcp', 'mcp_pdb.main', 'uvicorn'):\n"
        "    importlib.import_module(module)\n"
        "import cryptography\n"
        "print(json.dumps({\n"
        "    'implementation': platform.python_implementation(),\n"
        "    'python': list(sys.version_info[:2]),\n"
        "    'cryptography': cryptography.__version__,\n"
        "    'mcp': version('mcp'),\n"
        "}))\n"
    )
    result = subprocess.run(
        [str(consumer.python), "-c", probe],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        "the installed debug-mcp dependencies could not be imported:\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    resolved = json.loads(result.stdout)
    assert isinstance(resolved, dict), f"invalid runtime probe output: {result.stdout!r}"
    assert isinstance(resolved.get("cryptography"), str), f"missing cryptography version: {resolved!r}"
    assert isinstance(resolved.get("mcp"), str), f"missing mcp version: {resolved!r}"
    assert resolved.get("implementation") == "CPython", resolved
    assert resolved.get("python", [0, 0]) >= [3, 11], resolved
    mcp_version = Version(resolved["mcp"])
    assert Version("1.24") <= mcp_version < Version("2"), (
        f"the Debug MCP SDK requires mcp>=1.24,<2, but resolved {mcp_version}:\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@when(re.compile(r'I start installed pytest for MCP inspection with arguments "(?P<arguments>[^"]*)"'))
def start_consumer_pytest_for_mcp_inspection(arguments: str, consumer: ConsumerProject) -> None:
    cli_arguments = _split_consumer_arguments(arguments)
    # Keep pytest's cache and the discovery record anchored to this consumer project.
    consumer_root = consumer.path.resolve()
    rootdir_argument = f"--rootdir={consumer_root}"
    for index, argument in enumerate(cli_arguments):
        if argument.startswith("--rootdir="):
            cli_arguments[index] = rootdir_argument
            break
    else:
        cli_arguments.insert(0, rootdir_argument)
    occupied_port = getattr(consumer, "_mcp_occupied_port", None)
    if occupied_port is not None:
        cli_arguments = [argument.replace("{mcp_occupied_port}", str(occupied_port)) for argument in cli_arguments]
    nonlocal_host = getattr(consumer, "_mcp_nonlocal_host", None)
    if nonlocal_host is not None:
        cli_arguments = [argument.replace("{mcp_nonlocal_host}", str(nonlocal_host)) for argument in cli_arguments]
    command = [str(consumer.pytest), *cli_arguments]
    output_path = consumer.path / "mcp-pytest-output.log"
    process_group_options: dict[str, object] = {}
    if getattr(consumer, "_mcp_signal_process_group", False):
        if os.name == "nt":
            process_group_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            process_group_options["start_new_session"] = True
    with output_path.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(
            command,
            cwd=consumer.path,
            env=consumer.env,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            **process_group_options,
        )
    if os.name == "nt" and getattr(consumer, "_mcp_signal_process_group", False):
        guard_path = consumer.path / "mcp-startup-observations.log"
        creationflags = int(process_group_options.get("creationflags", 0))
        with guard_path.open("a", encoding="utf-8") as guard:
            guard.write(f"outer-process-group:{process.pid}:{creationflags}\n")
    setattr(consumer, "_mcp_pytest_process", process)
    setattr(consumer, "_mcp_pytest_command", command)
    setattr(consumer, "_mcp_pytest_output_path", output_path)
    consumer.pytest_result = None


@when("no external MCP client connects before the held failure times out")
def wait_for_mcp_failure_timeout_without_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    initial = _mcp_read_discovery_record(consumer, timeout=15)
    assert initial.get("status") == "holding_failure", initial
    failure = initial.get("active_failure")
    assert isinstance(failure, dict), initial
    assert failure.get("error_message") == "debug MCP timeout sentinel", failure
    held_at = time.monotonic()
    try:
        return_code = process.wait(timeout=7)
    except subprocess.TimeoutExpired as error:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        raise AssertionError(f"the no-client Debug MCP hold exceeded its bounded timeout:\n{output}") from error
    elapsed = time.monotonic() - held_at
    output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
    assert return_code != 0, f"the timeout release changed a failed test into a passing pytest run:\n{output}"
    assert 2.4 <= elapsed <= 7, f"hold lasted {elapsed:.3f}s after discovery first showed the failure:\n{output}"
    final_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
    final_record = json.loads(final_path.read_text(encoding="utf-8"))
    assert final_record.get("status") == "closed", final_record
    assert final_record.get("active_failure") is None, final_record
    last_release = final_record.get("last_release")
    assert isinstance(last_release, dict), final_record
    assert last_release.get("session_id") == initial.get("session_id"), (last_release, initial)
    assert last_release.get("sequence") == failure.get("sequence"), (last_release, failure)
    assert last_release.get("reason") == "timeout", final_record
    endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
    assert endpoints == [None, None], final_record
    consumer._mcp_initial_discovery = initial
    consumer._mcp_final_record = final_record
    consumer._mcp_timeout_elapsed = elapsed
    consumer._mcp_advertised_endpoints_after_finish = endpoints


@then('the MCP timeout observation should prove release from the current hold with reason "timeout"')
def consumer_mcp_timeout_observation(consumer: ConsumerProject) -> None:
    initial = getattr(consumer, "_mcp_initial_discovery", None)
    final_record = getattr(consumer, "_mcp_final_record", None)
    elapsed = getattr(consumer, "_mcp_timeout_elapsed", None)
    assert isinstance(initial, dict) and isinstance(final_record, dict), (initial, final_record)
    assert isinstance(elapsed, float) and 2.4 <= elapsed <= 7, elapsed
    assert final_record.get("last_release", {}).get("reason") == "timeout", final_record
    assert final_record.get("active_failure") is None, final_record


@then("the selected MCP launch should fail before advertising an endpoint or keeping a child alive")
def consumer_debug_mcp_startup_failure_has_no_advertised_endpoint_or_child(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    try:
        return_code = process.wait(timeout=25)
    except subprocess.TimeoutExpired as error:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        raise AssertionError(f"selected Debug MCP startup did not fail promptly:\n{output}") from error
    output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
    assert return_code != 0, f"selected Debug MCP startup unexpectedly succeeded:\n{output}"
    guard_path = consumer.path / "mcp-startup-observations.log"
    guard_output = guard_path.read_text(encoding="utf-8") if guard_path.is_file() else ""
    child_pids = re.findall(r"^child:(\d+):", guard_output, re.MULTILINE)
    statuses = {
        pid: status
        for pid, status in re.findall(r"^child-status:(\d+):([^\n]+)$", guard_output, re.MULTILINE)
    }
    occupied_socket = getattr(consumer, "_mcp_occupied_socket", None)
    try:
        if occupied_socket is None:
            assert "pydantic" in output.lower(), output
            assert "pytest-cuke[debug-mcp]" in output.lower(), output
            assert not child_pids, guard_output
        else:
            assert "debugger server exited during startup" in output.lower(), output
            assert child_pids, guard_output
            assert all(pid in statuses and statuses[pid] != "None" for pid in child_pids), (
                child_pids,
                statuses,
                guard_output,
            )
        record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        if record_path.is_file():
            record = json.loads(record_path.read_text(encoding="utf-8"))
            assert record.get("debugger_endpoint") is None and record.get("inspection_endpoint") is None, record
            assert record.get("active_failure") is None, record
            assert record.get("status") in {"closed", "waiting"}, record
    finally:
        if occupied_socket is not None:
            occupied_socket.close()


@then("pytest output should announce the Debug MCP session, endpoints, and held failure")
def consumer_pytest_output_announces_debug_mcp_session(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    discovery = getattr(consumer, "_mcp_initial_discovery", None)
    assert result is not None and isinstance(discovery, dict), (result, discovery)
    output = f"{result.stdout}\n{result.stderr}"
    assert f"Debug MCP session: {discovery['session_id']} (waiting)" in output, output
    assert f"Debug MCP debugger: {discovery['debugger_endpoint']}" in output, output
    assert f"Debug MCP inspection: {discovery['inspection_endpoint']}" in output, output
    discovery_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
    assert f"Debug MCP discovery: {discovery_path}" in output, output
    failure = discovery.get("active_failure")
    assert isinstance(failure, dict), discovery
    announcement = (
        f"Debug MCP holding failure #{failure['sequence']} (call) at {failure['nodeid']}: "
        "RuntimeError: debug MCP failure sentinel"
    )
    assert announcement in output, output


def _debug_mcp_sdk_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def jsonable(value):
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, dict):
                return {str(key): jsonable(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [jsonable(item) for item in value]
            if hasattr(value, "model_dump"):
                return jsonable(value.model_dump(mode="json"))
            return str(value)

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return jsonable(structured)
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        def tool_snapshot(result):
            return {
                "is_error": bool(getattr(result, "isError", False)),
                "payload": tool_payload(result),
                "content": [
                    {"type": getattr(block, "type", None), "text": getattr(block, "text", None)}
                    for block in getattr(result, "content", [])
                ],
            }

        async def main(endpoint, output_path):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = {tool.name for tool in tools.tools}
                    required = {"inspect_failure", "heartbeat", "release_failure"}
                    assert required <= names, f"missing MCP inspection tools: {required - names}"

                    inspected_result = await session.call_tool("inspect_failure", {})
                    assert not getattr(inspected_result, "isError", False), inspected_result
                    inspected = tool_snapshot(inspected_result)
                    failure = inspected["payload"].get("active_failure")
                    assert isinstance(failure, dict), inspected
                    session_id = inspected["payload"].get("session_id")
                    status = inspected["payload"].get("status")
                    sequence = failure.get("sequence")
                    assert isinstance(session_id, str) and session_id, inspected
                    assert isinstance(status, str) and status, inspected
                    assert isinstance(sequence, int) and sequence > 0, inspected

                    heartbeat_result = await session.call_tool(
                        "heartbeat", {"session_id": session_id, "sequence": sequence}
                    )
                    assert not getattr(heartbeat_result, "isError", False), heartbeat_result
                    heartbeat = tool_snapshot(heartbeat_result)

                    # Refresh the lease before it expires, then inspect after the first lease deadline.
                    await asyncio.sleep(6.1)
                    refresh_result = await session.call_tool(
                        "heartbeat", {"session_id": session_id, "sequence": sequence}
                    )
                    assert not getattr(refresh_result, "isError", False), refresh_result
                    refresh = tool_snapshot(refresh_result)
                    assert refresh["payload"].get("session_id") == session_id, refresh
                    assert refresh["payload"].get("sequence") == sequence, refresh
                    await asyncio.sleep(4.2)
                    after_heartbeat_result = await session.call_tool("inspect_failure", {})
                    assert not getattr(after_heartbeat_result, "isError", False), after_heartbeat_result
                    after_heartbeat = tool_snapshot(after_heartbeat_result)
                    active_after_heartbeat = after_heartbeat["payload"].get("active_failure")
                    assert isinstance(active_after_heartbeat, dict), after_heartbeat
                    assert active_after_heartbeat.get("sequence") == sequence, after_heartbeat
                    assert after_heartbeat["payload"].get("status") == status, after_heartbeat

                    release_result = await session.call_tool(
                        "release_failure", {"session_id": session_id, "sequence": sequence}
                    )
                    assert not getattr(release_result, "isError", False), release_result
                    release = tool_snapshot(release_result)
                    assert release["payload"].get("released") is True, release

                    Path(output_path).write_text(
                        json.dumps(
                            {
                                "endpoint": endpoint,
                                "tools": sorted(names),
                                "inspection": inspected["payload"],
                                "heartbeat": heartbeat["payload"],
                                "heartbeat_refresh": refresh["payload"],
                                "after_heartbeat": after_heartbeat["payload"],
                                "release": release["payload"],
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2]))
        '''
    )


def _debug_mcp_artifact_sdk_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def jsonable(value):
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, dict):
                return {str(key): jsonable(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [jsonable(item) for item in value]
            if hasattr(value, "model_dump"):
                return jsonable(value.model_dump(mode="json"))
            return str(value)

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return jsonable(structured)
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        async def main(endpoint, output_path, artifact_root):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = {tool.name for tool in tools.tools}
                    required = {"inspect_failure", "submit_artifact", "release_failure"}
                    assert required <= names, f"missing MCP artifact tools: {required - names}"

                    inspection_result = await session.call_tool("inspect_failure", {})
                    inspection = tool_payload(inspection_result)
                    failure = inspection.get("active_failure")
                    assert isinstance(failure, dict), inspection
                    session_id = inspection.get("session_id")
                    sequence = failure.get("sequence")
                    assert isinstance(session_id, str) and session_id, inspection
                    assert isinstance(sequence, int) and sequence > 0, inspection
                    context = failure.get("bdd_context")
                    assert isinstance(context, dict), failure

                    active_bdd_metadata = {
                        "feature_path": context.get("feature_path"),
                        "feature_name": context.get("feature_name"),
                        "scenario_name": context.get("scenario_name"),
                        "step_keyword": context.get("step_keyword"),
                        "step_text": context.get("step_text"),
                        "tags": context.get("tags", []),
                        "example_row": context.get("outline_row", {}),
                    }
                    tampered_bdd_metadata = {
                        "feature_path": "file:forged-feature.feature",
                        "feature_name": "Forged feature",
                        "scenario_name": "Forged scenario",
                        "step_keyword": "Then",
                        "step_text": "the submitted metadata is untrusted",
                        "tags": ["forged-tag"],
                        "example_row": {"probe_id": "forged-row", "message": "forged-message"},
                    }
                    artifact = {
                        "artifact_id": "outline-row-17-investigation",
                        "nodeid": failure["nodeid"],
                        "pytest_phase": failure["phase"],
                        "status": "needs_followup",
                        "summary": "The held outline row failed in its When step.",
                        "inspected_commands": ["inspect_failure", "heartbeat"],
                        "evidence": ["The failure message matches the expected debugger probe sentinel."],
                        "suspected_cause": "The probe deliberately raises its configured sentinel exception.",
                        "next_action": "Review the outline row and its failure context.",
                        "bdd_metadata": tampered_bdd_metadata,
                    }

                    missing_required_artifact = {**artifact}
                    del missing_required_artifact["summary"]
                    invalid_artifacts = {
                        "wrong_json_type": "artifact must be a JSON object",
                        "wrong_phase": {**artifact, "pytest_phase": "not-a-phase"},
                        "wrong_status": {**artifact, "status": "approved"},
                        "extra_key": {**artifact, "unexpected_field": "must be rejected"},
                        "missing_required": missing_required_artifact,
                    }
                    invalid_submissions = {}
                    for case_name, invalid_artifact in invalid_artifacts.items():
                        invalid_result = await session.call_tool(
                            "submit_artifact",
                            {
                                "session_id": session_id,
                                "sequence": sequence,
                                "artifact": invalid_artifact,
                            },
                        )
                        invalid_payload = tool_payload(invalid_result)
                        assert invalid_payload.get("ok") is False, (case_name, invalid_payload)
                        assert invalid_payload.get("error") == "validation_error", (case_name, invalid_payload)
                        assert invalid_payload.get("details"), (case_name, invalid_payload)
                        assert "json_path" not in invalid_payload, (case_name, invalid_payload)
                        assert "markdown_path" not in invalid_payload, (case_name, invalid_payload)
                        invalid_submissions[case_name] = invalid_payload

                    mismatched_artifacts = {
                        "wrong_nodeid": {**artifact, "nodeid": f"{failure['nodeid']}::other-test"},
                        "wrong_allowed_phase": {
                            **artifact,
                            "pytest_phase": "setup" if failure["phase"] != "setup" else "teardown",
                        },
                    }
                    mismatch_submissions = {}
                    root = Path(artifact_root)
                    for case_name, mismatched_artifact in mismatched_artifacts.items():
                        mismatch_payload = tool_payload(
                            await session.call_tool(
                                "submit_artifact",
                                {
                                    "session_id": session_id,
                                    "sequence": sequence,
                                    "artifact": mismatched_artifact,
                                },
                            )
                        )
                        assert mismatch_payload.get("ok") is False, (case_name, mismatch_payload)
                        assert mismatch_payload.get("error") == "failure_mismatch", (case_name, mismatch_payload)
                        assert mismatch_payload.get("details"), (case_name, mismatch_payload)
                        assert "json_path" not in mismatch_payload, (case_name, mismatch_payload)
                        assert "markdown_path" not in mismatch_payload, (case_name, mismatch_payload)
                        assert "artifact_status" not in mismatch_payload, (case_name, mismatch_payload)

                        after_mismatch = tool_payload(await session.call_tool("inspect_failure", {}))
                        assert after_mismatch.get("session_id") == session_id, after_mismatch
                        assert after_mismatch.get("active_failure") == failure, (after_mismatch, failure)
                        assert not root.exists() or not list(root.iterdir()), (
                            case_name,
                            root,
                            list(root.iterdir()) if root.exists() else [],
                        )
                        root_entries = sorted(path.name for path in root.iterdir()) if root.exists() else []
                        mismatch_submissions[case_name] = {
                            "response": mismatch_payload,
                            "active_after": after_mismatch.get("active_failure"),
                            "artifact_root_entries_after": root_entries,
                        }

                    valid_result = await session.call_tool(
                        "submit_artifact",
                        {"session_id": session_id, "sequence": sequence, "artifact": artifact},
                    )
                    valid_payload = tool_payload(valid_result)
                    assert valid_payload.get("artifact_id") == artifact["artifact_id"], valid_payload
                    assert isinstance(valid_payload.get("json_path"), str), valid_payload
                    assert isinstance(valid_payload.get("markdown_path"), str), valid_payload

                    release_result = await session.call_tool(
                        "release_failure", {"session_id": session_id, "sequence": sequence}
                    )
                    release = tool_payload(release_result)
                    assert release.get("released") is True, release
                    assert release.get("artifact_status") == "written", release

                    Path(output_path).write_text(
                        json.dumps(
                            {
                                "endpoint": endpoint,
                                "tools": sorted(names),
                                "inspection": inspection,
                                "invalid_submissions": invalid_submissions,
                                "mismatch_submissions": mismatch_submissions,
                                "active_bdd_metadata": active_bdd_metadata,
                                "valid_submission": valid_payload,
                                "submitted_artifact": artifact,
                                "release": release,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
        '''
    )


def _debug_mcp_plain_artifact_sdk_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def jsonable(value):
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, dict):
                return {str(key): jsonable(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [jsonable(item) for item in value]
            if hasattr(value, "model_dump"):
                return jsonable(value.model_dump(mode="json"))
            return str(value)

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return jsonable(structured)
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        async def main(endpoint, output_path, artifact_root):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = {tool.name for tool in tools.tools}
                    required = {"inspect_failure", "submit_artifact", "release_failure"}
                    assert required <= names, f"missing MCP artifact tools: {required - names}"

                    inspection = tool_payload(await session.call_tool("inspect_failure", {}))
                    failure = inspection.get("active_failure")
                    session_id = inspection.get("session_id")
                    assert isinstance(failure, dict), inspection
                    assert failure.get("bdd_context") is None, failure
                    assert isinstance(session_id, str) and session_id, inspection
                    sequence = failure.get("sequence")
                    assert isinstance(sequence, int) and sequence > 0, failure
                    artifact = {
                        "artifact_id": "plain-pytest-investigation",
                        "nodeid": failure["nodeid"],
                        "pytest_phase": failure["phase"],
                        "status": "investigated",
                        "summary": "The plain pytest failure was inspected without BDD context.",
                        "inspected_commands": ["inspect_failure"],
                        "evidence": ["The active failure is an ordinary pytest call failure."],
                        "suspected_cause": "The test deliberately raises its configured sentinel exception.",
                        "next_action": "Review the plain pytest failure and its traceback.",
                    }

                    submission = tool_payload(
                        await session.call_tool(
                            "submit_artifact",
                            {"session_id": session_id, "sequence": sequence, "artifact": artifact},
                        )
                    )
                    assert submission.get("ok") is True, submission
                    assert submission.get("artifact_id") == artifact["artifact_id"], submission
                    assert isinstance(submission.get("json_path"), str), submission
                    assert isinstance(submission.get("markdown_path"), str), submission
                    configured_root = Path(artifact_root).resolve()
                    assert Path(submission["json_path"]).resolve().is_relative_to(configured_root), submission
                    assert Path(submission["markdown_path"]).resolve().is_relative_to(configured_root), submission

                    release = tool_payload(
                        await session.call_tool(
                            "release_failure", {"session_id": session_id, "sequence": sequence}
                        )
                    )
                    assert release.get("released") is True, release
                    assert release.get("artifact_status") == "written", release

                    Path(output_path).write_text(
                        json.dumps(
                            {
                                "endpoint": endpoint,
                                "tools": sorted(names),
                                "inspection": inspection,
                                "submitted_artifact": artifact,
                                "valid_submission": submission,
                                "release": release,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
        '''
    )


def _debug_mcp_filesystem_failure_sdk_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        async def main(endpoint, output_path):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = {tool.name for tool in tools.tools}
                    required = {"inspect_failure", "submit_artifact", "release_failure"}
                    assert required <= names, f"missing MCP artifact tools: {required - names}"

                    inspection = tool_payload(await session.call_tool("inspect_failure", {}))
                    failure = inspection.get("active_failure")
                    session_id = inspection.get("session_id")
                    assert isinstance(failure, dict), inspection
                    assert isinstance(session_id, str) and session_id, inspection
                    sequence = failure.get("sequence")
                    assert isinstance(sequence, int) and sequence > 0, failure
                    context = failure.get("bdd_context")
                    assert isinstance(context, dict), failure
                    artifact = {
                        "artifact_id": "filesystem-blocked-investigation",
                        "nodeid": failure["nodeid"],
                        "pytest_phase": failure["phase"],
                        "status": "investigated",
                        "summary": "The held failure was inspected before artifact storage failed.",
                        "inspected_commands": ["inspect_failure"],
                        "evidence": ["The external MCP client submits a schema-valid investigation report."],
                        "suspected_cause": "The configured artifact parent is an occupied regular file.",
                        "next_action": "Fix the artifact directory and submit the report again.",
                        "bdd_metadata": {
                            "feature_path": context.get("feature_path"),
                            "feature_name": context.get("feature_name"),
                            "scenario_name": context.get("scenario_name"),
                            "step_keyword": context.get("step_keyword"),
                            "step_text": context.get("step_text"),
                            "tags": context.get("tags", []),
                            "example_row": context.get("outline_row", {}),
                        },
                    }

                    failed_submission = tool_payload(
                        await session.call_tool(
                            "submit_artifact",
                            {"session_id": session_id, "sequence": sequence, "artifact": artifact},
                        )
                    )
                    assert failed_submission.get("ok") is False, failed_submission
                    assert failed_submission.get("error") == "filesystem_error", failed_submission
                    assert failed_submission.get("details"), failed_submission
                    assert "json_path" not in failed_submission, failed_submission
                    assert "markdown_path" not in failed_submission, failed_submission

                    after_failure = tool_payload(await session.call_tool("inspect_failure", {}))
                    active_after_failure = after_failure.get("active_failure")
                    assert isinstance(active_after_failure, dict), after_failure
                    assert after_failure.get("session_id") == session_id, after_failure
                    assert active_after_failure.get("sequence") == sequence, after_failure
                    assert active_after_failure.get("nodeid") == failure.get("nodeid"), after_failure
                    assert active_after_failure.get("phase") == failure.get("phase"), after_failure

                    release = tool_payload(
                        await session.call_tool(
                            "release_failure", {"session_id": session_id, "sequence": sequence}
                        )
                    )
                    assert release.get("released") is True, release
                    assert release.get("artifact_status") == "missing", release

                    Path(output_path).write_text(
                        json.dumps(
                            {
                                "endpoint": endpoint,
                                "tools": sorted(names),
                                "inspection": inspection,
                                "artifact": artifact,
                                "failed_submission": failed_submission,
                                "after_failure": after_failure,
                                "release": release,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2]))
        '''
    )


def _debug_mcp_stale_artifact_sdk_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        def artifact_for(failure, artifact_id):
            context = failure.get("bdd_context")
            assert isinstance(context, dict), failure
            return {
                "artifact_id": artifact_id,
                "nodeid": failure["nodeid"],
                "pytest_phase": failure["phase"],
                "status": "investigated",
                "summary": "The client inspected this held outline-row failure.",
                "inspected_commands": ["inspect_failure"],
                "evidence": ["The failure is associated with the selected outline row."],
                "suspected_cause": "The BDD probe deliberately raises its sentinel exception.",
                "next_action": "Review the held outline row before continuing.",
                "bdd_metadata": {
                    "feature_path": context.get("feature_path"),
                    "feature_name": context.get("feature_name"),
                    "scenario_name": context.get("scenario_name"),
                    "step_keyword": context.get("step_keyword"),
                    "step_text": context.get("step_text"),
                    "tags": context.get("tags", []),
                    "example_row": context.get("outline_row", {}),
                },
            }

        async def main(endpoint, output_path):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = {tool.name for tool in tools.tools}
                    required = {"inspect_failure", "submit_artifact", "release_failure"}
                    assert required <= names, f"missing MCP artifact tools: {required - names}"

                    first_inspection = tool_payload(await session.call_tool("inspect_failure", {}))
                    first_failure = first_inspection.get("active_failure")
                    session_id = first_inspection.get("session_id")
                    assert isinstance(first_failure, dict), first_inspection
                    assert isinstance(session_id, str) and session_id, first_inspection
                    first_sequence = first_failure.get("sequence")
                    assert isinstance(first_sequence, int) and first_sequence > 0, first_failure
                    assert first_failure.get("bdd_context", {}).get("outline_row", {}).get("probe_id") == "outline-row-17", first_failure

                    first_artifact = artifact_for(first_failure, "first-row-investigation")
                    first_submission = tool_payload(
                        await session.call_tool(
                            "submit_artifact",
                            {"session_id": session_id, "sequence": first_sequence, "artifact": first_artifact},
                        )
                    )
                    assert first_submission.get("artifact_id") == first_artifact["artifact_id"], first_submission
                    first_release = tool_payload(
                        await session.call_tool(
                            "release_failure", {"session_id": session_id, "sequence": first_sequence}
                        )
                    )
                    assert first_release.get("released") is True, first_release
                    assert first_release.get("artifact_status") == "written", first_release

                    loop = asyncio.get_running_loop()
                    deadline = loop.time() + 25
                    second_inspection = None
                    second_failure = None
                    while loop.time() < deadline:
                        payload = tool_payload(await session.call_tool("inspect_failure", {}))
                        candidate = payload.get("active_failure")
                        if isinstance(candidate, dict) and candidate.get("sequence", 0) > first_sequence:
                            second_inspection = payload
                            second_failure = candidate
                            break
                        await asyncio.sleep(0.1)
                    assert isinstance(second_inspection, dict), "pytest did not hold the next ordered failure"
                    assert isinstance(second_failure, dict), second_inspection
                    assert second_inspection.get("session_id") == session_id, second_inspection
                    second_sequence = second_failure.get("sequence")
                    assert isinstance(second_sequence, int) and second_sequence > first_sequence, second_failure
                    assert second_failure.get("bdd_context", {}).get("outline_row", {}).get("probe_id") == "outline-row-18", second_failure

                    stale_artifact = artifact_for(second_failure, "stale-sequence-must-not-write")
                    stale_submission = tool_payload(
                        await session.call_tool(
                            "submit_artifact",
                            {"session_id": session_id, "sequence": first_sequence, "artifact": stale_artifact},
                        )
                    )
                    assert stale_submission.get("ok") is False, stale_submission
                    assert stale_submission.get("error") == "failure_unavailable", stale_submission
                    assert stale_submission.get("details"), stale_submission
                    assert "json_path" not in stale_submission, stale_submission
                    assert "markdown_path" not in stale_submission, stale_submission

                    after_stale = tool_payload(await session.call_tool("inspect_failure", {}))
                    active_after_stale = after_stale.get("active_failure")
                    assert isinstance(active_after_stale, dict), after_stale
                    assert active_after_stale.get("sequence") == second_sequence, after_stale
                    assert active_after_stale.get("nodeid") == second_failure.get("nodeid"), after_stale

                    second_release = tool_payload(
                        await session.call_tool(
                            "release_failure", {"session_id": session_id, "sequence": second_sequence}
                        )
                    )
                    assert second_release.get("released") is True, second_release
                    assert second_release.get("artifact_status") == "missing", second_release

                    Path(output_path).write_text(
                        json.dumps(
                            {
                                "tools": sorted(names),
                                "first_failure": first_failure,
                                "first_submission": first_submission,
                                "first_release": first_release,
                                "second_failure": second_failure,
                                "stale_submission": stale_submission,
                                "after_stale": after_stale,
                                "second_release": second_release,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2]))
        '''
    )


def _debug_mcp_external_client_timeout_message(
    consumer: ConsumerProject,
    stage_path: Path,
    error: subprocess.TimeoutExpired,
    client_name: str,
) -> str:
    stage = (
        stage_path.read_text(encoding="utf-8", errors="replace")
        if stage_path.is_file()
        else "no client stage was recorded"
    )
    output_path = getattr(consumer, "_mcp_pytest_output_path", None)
    pytest_output = (
        output_path.read_text(encoding="utf-8", errors="replace")
        if isinstance(output_path, Path) and output_path.exists()
        else ""
    )

    def captured_output(value: str | bytes | None) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value if isinstance(value, str) else ""

    return (
        f"{client_name} timed out after {error.timeout}s at last client stage {stage.strip()!r}\n"
        f"pytest output ({output_path}):\n{pytest_output}\n"
        f"client output captured before timeout:\n{captured_output(error.stdout)}\n"
        f"client stderr captured before timeout:\n{captured_output(error.stderr)}"
    )


def _terminate_debug_mcp_external_client(process: subprocess.Popen[str]) -> None:
    """Stop a timed-out client process tree and reap its root process."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        with suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                close_fds=True,
                timeout=5,
            )
    else:
        import signal

        with suppress(OSError):
            os.killpg(process.pid, signal.SIGKILL)
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _run_debug_mcp_external_client(
    consumer: ConsumerProject,
    command: list[str],
    *,
    client_name: str,
    timeout: float,
    stage_path: Path,
    log_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Run an SDK client with file-backed stdio and bounded process-tree cleanup.

    The client gets no PIPE-backed stdout or stderr descriptors to inherit. Its
    output is written to one diagnostic file, unrelated descriptors are closed,
    and the client process is waited before that file is read.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    process_options: dict[str, object] = {}
    if os.name == "nt":
        process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        process_options["start_new_session"] = True

    timeout_error: subprocess.TimeoutExpired | None = None
    return_code: int | None = None
    with log_path.open("w", encoding="utf-8", errors="replace") as output:
        process = subprocess.Popen(
            command,
            cwd=consumer.path,
            env=consumer.env,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            close_fds=True,
            **process_options,
        )
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            timeout_error = error
            _terminate_debug_mcp_external_client(process)
        finally:
            output.flush()

    client_output = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    if timeout_error is not None:
        diagnostic_timeout = subprocess.TimeoutExpired(
            command,
            timeout,
            output=client_output,
            stderr="",
        )
        raise AssertionError(
            _debug_mcp_external_client_timeout_message(
                consumer,
                stage_path,
                diagnostic_timeout,
                client_name,
            )
            + f"\nclient output log: {log_path}"
        ) from timeout_error

    assert return_code is not None, "the external MCP client process was not waited"
    return subprocess.CompletedProcess(command, return_code, client_output, "")


def _debug_mcp_debugger_continuation_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def mark(stage_path, stage):
            Path(stage_path).write_text(stage + "\\n", encoding="utf-8")
            print(f"client stage: {stage}", flush=True)

        class BoundedClientSession(ClientSession):
            def __init__(self, read_stream, write_stream, stage_path, label):
                super().__init__(read_stream, write_stream)
                self._stage_path = stage_path
                self._label = label

            async def _bounded(self, operation, awaitable):
                stage = f"{self._label} {operation}"
                mark(self._stage_path, stage)
                # mcp-pdb may spend 9 seconds polling continue, then fetch location context.
                timeout = 20 if self._label == "debugger" and operation == "call_tool send_pdb_command" else 10
                try:
                    return await asyncio.wait_for(awaitable, timeout=timeout)
                except asyncio.TimeoutError as error:
                    raise TimeoutError(f"{stage} timed out after {timeout} seconds") from error

            async def initialize(self, *args, **kwargs):
                return await self._bounded("initialize", super().initialize(*args, **kwargs))

            async def list_tools(self, *args, **kwargs):
                return await self._bounded("list_tools", super().list_tools(*args, **kwargs))

            async def call_tool(self, *args, **kwargs):
                tool_name = args[0] if args else kwargs.get("name", "unknown")
                return await self._bounded(
                    f"call_tool {tool_name}",
                    super().call_tool(*args, **kwargs),
                )

        def tool_text(result):
            assert not getattr(result, "isError", False), result
            texts = [
                block.text
                for block in getattr(result, "content", [])
                if isinstance(getattr(block, "text", None), str)
            ]
            assert texts, f"MCP debugger tool returned no text: {result!r}"
            return "\\n".join(texts)

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP inspection tool did not return structured JSON: {result!r}")

        async def inspect(endpoint, stage_path):
            mark(stage_path, "inspection connect")
            async with streamable_http_client(endpoint) as (read_stream, write_stream, _session_id):
                async with BoundedClientSession(read_stream, write_stream, stage_path, "inspection") as session:
                    await session.initialize()
                    result = await session.call_tool("inspect_failure", {})
                    assert not getattr(result, "isError", False), result
                    payload = tool_payload(result)
                    mark(stage_path, "inspection ClientSession context exit")
                mark(stage_path, "inspection HTTP client context exit")
            return payload

        async def main(debugger_endpoint, inspection_endpoint, target_path, output_path, stage_path):
            mark(stage_path, "read initial inspection")
            active_before = await inspect(inspection_endpoint, stage_path)
            failure = active_before.get("active_failure")
            session_id = active_before.get("session_id")
            assert isinstance(failure, dict), active_before
            sequence = failure.get("sequence")
            assert isinstance(session_id, str) and session_id, active_before
            assert isinstance(sequence, int) and sequence > 0, active_before

            mark(stage_path, "debugger connect")
            async with streamable_http_client(debugger_endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _session_id,
            ):
                async with BoundedClientSession(read_stream, write_stream, stage_path, "debugger") as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = {tool.name for tool in tools.tools}
                    required = {"start_debug", "send_pdb_command"}
                    assert required <= names, f"missing mcp-pdb debugger tools: {required - names}"

                    start_result = await session.call_tool("start_debug", {"file_path": target_path})
                    start_text = tool_text(start_result)
                    assert "Debugging session started" in start_text, start_text

                    continue_result = await session.call_tool("send_pdb_command", {"command": "continue"})
                    continue_text = tool_text(continue_result)
                    assert "Command output" in continue_text or "session" in continue_text.lower(), continue_text
                    mark(stage_path, "debugger ClientSession context exit")
                mark(stage_path, "debugger HTTP client context exit")

            mark(stage_path, "write debugger observation")
            Path(output_path).write_text(
                json.dumps(
                    {
                        "debugger_endpoint": debugger_endpoint,
                        "inspection_endpoint": inspection_endpoint,
                        "tools": sorted(names),
                        "active_before": active_before,
                        "start_response": start_text,
                        "continue_response": continue_text,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        asyncio.run(main(*sys.argv[1:]))
        '''
    )


def _mcp_read_discovery_record(consumer: ConsumerProject, timeout: float = 45) -> dict[str, object]:
    record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
    process = getattr(consumer, "_mcp_pytest_process")
    deadline = time.monotonic() + timeout
    latest_error = "discovery file has not been published"
    while time.monotonic() < deadline:
        if record_path.is_file():
            try:
                payload = json.loads(record_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict) and isinstance(payload.get("active_failure"), dict):
                    return payload
                latest_error = f"discovery record has no active failure yet: {payload!r}"
            except (OSError, json.JSONDecodeError) as error:
                latest_error = repr(error)
        if process.poll() is not None:
            break
        time.sleep(0.1)
    output_path = getattr(consumer, "_mcp_pytest_output_path")
    output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    raise AssertionError(
        f"installed pytest did not publish an active MCP failure ({latest_error}) before the watchdog;\n"
        f"pytest output:\n{output}"
    )


def _mcp_endpoint_port(endpoint: object) -> tuple[str, int]:
    assert isinstance(endpoint, str), f"MCP endpoint must be a URL, got {endpoint!r}"
    parsed = urlsplit(endpoint)
    assert parsed.scheme == "http" and parsed.hostname and parsed.port, endpoint
    assert parsed.path == "/mcp", endpoint
    return parsed.hostname, parsed.port


def _debug_mcp_lease_expiry_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        import time
        from pathlib import Path
        from urllib.parse import urlsplit

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        async def main(endpoint, output_path):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    inspected_result = await session.call_tool("inspect_failure", {})
                    assert not getattr(inspected_result, "isError", False), inspected_result
                    inspected = tool_payload(inspected_result)
                    failure = inspected.get("active_failure")
                    assert isinstance(failure, dict), inspected
                    session_id = inspected.get("session_id")
                    sequence = failure.get("sequence")
                    assert isinstance(session_id, str) and session_id, inspected
                    assert isinstance(sequence, int) and sequence > 0, failure

                    heartbeat_result = await session.call_tool(
                        "heartbeat", {"session_id": session_id, "sequence": sequence}
                    )
                    assert not getattr(heartbeat_result, "isError", False), heartbeat_result
                    heartbeat = tool_payload(heartbeat_result)
                    assert heartbeat.get("session_id") == session_id, heartbeat
                    assert heartbeat.get("sequence") == sequence, heartbeat
                    Path(output_path).write_text(
                        json.dumps(
                            {
                                "inspection": inspected,
                                "heartbeat": heartbeat,
                                "heartbeat_at": time.monotonic(),
                            },
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2]))
        '''
    )


@when("an external MCP client heartbeats once and stops renewing the lease")
def run_external_debug_mcp_lease_expiry_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    client_path = consumer.path / "debug-mcp-lease-client.py"
    result_path = consumer.path / "debug-mcp-lease-client-result.json"
    try:
        discovery = _mcp_read_discovery_record(consumer)
        assert discovery.get("status") == "holding_failure", discovery
        failure = discovery.get("active_failure")
        assert isinstance(failure, dict), discovery
        assert failure.get("phase") == "call", failure
        assert failure.get("error_message") == consumer._mcp_expected_plain_message, failure
        endpoint = discovery.get("inspection_endpoint")
        _mcp_endpoint_port(endpoint)
        consumer._mcp_initial_discovery = discovery

        client_path.write_text(_debug_mcp_lease_expiry_client_script(), encoding="utf-8")
        client_result = subprocess.run(
            [str(consumer.python), str(client_path), str(endpoint), str(result_path)],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        consumer._mcp_lease_client_result = client_result
        assert client_result.returncode == 0, (
            f"external MCP lease client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        inspected = observation.get("inspection")
        heartbeat = observation.get("heartbeat")
        assert isinstance(inspected, dict) and isinstance(heartbeat, dict), observation
        assert inspected.get("session_id") == discovery.get("session_id"), (inspected, discovery)
        assert inspected.get("active_failure") == failure, (inspected, failure)
        assert heartbeat.get("session_id") == discovery.get("session_id"), observation
        assert heartbeat.get("sequence") == failure.get("sequence"), observation
        heartbeat_at = observation.get("heartbeat_at")
        assert isinstance(heartbeat_at, (int, float)), observation
        consumer._mcp_lease_client_observation = observation

        try:
            return_code = process.wait(timeout=12)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("pytest did not resume after the external MCP heartbeat lease expired") from error
        elapsed = time.monotonic() - heartbeat_at
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"lease expiry changed the failed pytest outcome to success:\n{output}"
        assert 1.8 <= elapsed <= 12, f"pytest resumed {elapsed:.3f}s after the heartbeat:\n{output}"

        final_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = json.loads(final_path.read_text(encoding="utf-8"))
        assert final_record.get("status") == "closed", final_record
        assert final_record.get("active_failure") is None, final_record
        release = final_record.get("last_release")
        assert isinstance(release, dict), final_record
        assert release.get("session_id") == discovery.get("session_id"), (release, discovery)
        assert release.get("sequence") == failure.get("sequence"), (release, failure)
        assert release.get("reason") == "lease_expired", final_record
        endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
        assert endpoints == [None, None], final_record
        consumer._mcp_final_record = final_record
        consumer._mcp_lease_elapsed = elapsed
        consumer._mcp_advertised_endpoints_after_finish = endpoints
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


@then('the MCP lease observation should prove bounded release from the current hold with reason "lease_expired"')
def consumer_mcp_lease_expiry_observation(consumer: ConsumerProject) -> None:
    discovery = getattr(consumer, "_mcp_initial_discovery", None)
    observation = getattr(consumer, "_mcp_lease_client_observation", None)
    final_record = getattr(consumer, "_mcp_final_record", None)
    elapsed = getattr(consumer, "_mcp_lease_elapsed", None)
    assert isinstance(discovery, dict) and isinstance(observation, dict), (discovery, observation)
    assert isinstance(final_record, dict), final_record
    assert isinstance(elapsed, float) and 1.8 <= elapsed <= 12, elapsed
    failure = discovery.get("active_failure")
    heartbeat = observation.get("heartbeat")
    release = final_record.get("last_release")
    assert isinstance(failure, dict) and isinstance(heartbeat, dict) and isinstance(release, dict)
    assert heartbeat.get("sequence") == failure.get("sequence"), (heartbeat, failure)
    assert release.get("sequence") == failure.get("sequence"), (release, failure)
    assert release.get("reason") == "lease_expired", release
    assert final_record.get("active_failure") is None, final_record


def _debug_mcp_repeated_release_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        def error_snapshot(result):
            return {
                "is_error": bool(getattr(result, "isError", False)),
                "messages": [
                    getattr(block, "text", "")
                    for block in getattr(result, "content", [])
                    if isinstance(getattr(block, "text", None), str)
                ],
            }

        async def main(endpoint, output_path):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    inspected_result = await session.call_tool("inspect_failure", {})
                    assert not getattr(inspected_result, "isError", False), inspected_result
                    inspected = tool_payload(inspected_result)
                    failure = inspected.get("active_failure")
                    session_id = inspected.get("session_id")
                    assert isinstance(failure, dict) and isinstance(session_id, str), inspected
                    sequence = failure.get("sequence")
                    assert isinstance(sequence, int) and sequence > 0, failure

                    release_result = await session.call_tool(
                        "release_failure", {"session_id": session_id, "sequence": sequence}
                    )
                    assert not getattr(release_result, "isError", False), release_result
                    release = tool_payload(release_result)
                    assert release.get("released") is True, release

                    repeated_release_result = await session.call_tool(
                        "release_failure", {"session_id": session_id, "sequence": sequence}
                    )
                    repeated_release = error_snapshot(repeated_release_result)
                    assert repeated_release["is_error"], repeated_release
                    assert any(
                        "there is no active failure matching this Debug MCP session and sequence" in message
                        for message in repeated_release["messages"]
                    ), repeated_release
                    Path(output_path).write_text(
                        json.dumps(
                            {
                                "inspection": inspected,
                                "release": release,
                                "repeated_release": repeated_release,
                            },
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2]))
        '''
    )


@when("an external MCP client releases the held failure and retries release")
def run_external_debug_mcp_repeated_release_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    client_path = consumer.path / "debug-mcp-repeated-release-client.py"
    result_path = consumer.path / "debug-mcp-repeated-release-client-result.json"
    try:
        discovery = _mcp_read_discovery_record(consumer)
        assert discovery.get("status") == "holding_failure", discovery
        failure = discovery.get("active_failure")
        assert isinstance(failure, dict), discovery
        endpoint = discovery.get("inspection_endpoint")
        _mcp_endpoint_port(endpoint)
        consumer._mcp_initial_discovery = discovery

        client_path.write_text(_debug_mcp_repeated_release_client_script(), encoding="utf-8")
        client_result = subprocess.run(
            [str(consumer.python), str(client_path), str(endpoint), str(result_path)],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        consumer._mcp_repeated_release_client_result = client_result
        assert client_result.returncode == 0, (
            f"external MCP repeated-release client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert observation.get("inspection", {}).get("active_failure") == failure, observation
        assert observation.get("release", {}).get("released") is True, observation
        consumer._mcp_repeated_release_observation = observation

        try:
            return_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("pytest did not resume after the external release") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"release changed the failed pytest outcome to success:\n{output}"
        final_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = json.loads(final_path.read_text(encoding="utf-8"))
        assert final_record.get("status") == "closed", final_record
        assert final_record.get("active_failure") is None, final_record
        release = final_record.get("last_release")
        assert isinstance(release, dict), final_record
        assert release.get("reason") == "explicit", final_record
        assert release.get("session_id") == discovery.get("session_id"), (release, discovery)
        assert release.get("sequence") == failure.get("sequence"), (release, failure)
        endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
        assert endpoints == [None, None], final_record
        consumer._mcp_final_record = final_record
        consumer._mcp_advertised_endpoints_after_finish = endpoints
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


@then("the MCP repeated-release observation should report the controlled unavailable-failure error")
def consumer_mcp_repeated_release_observation(consumer: ConsumerProject) -> None:
    discovery = getattr(consumer, "_mcp_initial_discovery", None)
    observation = getattr(consumer, "_mcp_repeated_release_observation", None)
    final_record = getattr(consumer, "_mcp_final_record", None)
    assert isinstance(discovery, dict) and isinstance(observation, dict), (discovery, observation)
    assert isinstance(final_record, dict), final_record
    failure = discovery.get("active_failure")
    release = observation.get("release")
    repeated_release = observation.get("repeated_release")
    assert isinstance(failure, dict) and isinstance(release, dict) and isinstance(repeated_release, dict), observation
    assert release.get("sequence") == failure.get("sequence"), (release, failure)
    assert repeated_release.get("is_error") is True, repeated_release
    assert any(
        "there is no active failure matching this Debug MCP session and sequence" in message
        for message in repeated_release.get("messages", [])
    ), repeated_release
    assert final_record.get("last_release", {}).get("reason") == "explicit", final_record


def _debug_mcp_plain_failure_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        async def main(endpoint, output_path):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    inspected_result = await session.call_tool("inspect_failure", {})
                    assert not getattr(inspected_result, "isError", False), inspected_result
                    inspected = tool_payload(inspected_result)
                    failure = inspected.get("active_failure")
                    assert isinstance(failure, dict), inspected
                    session_id = inspected.get("session_id")
                    sequence = failure.get("sequence")
                    assert isinstance(session_id, str) and session_id, inspected
                    assert isinstance(sequence, int) and sequence > 0, failure
                    release_result = await session.call_tool(
                        "release_failure", {"session_id": session_id, "sequence": sequence}
                    )
                    assert not getattr(release_result, "isError", False), release_result
                    release = tool_payload(release_result)
                    assert release.get("released") is True, release
                    Path(output_path).write_text(
                        json.dumps({"inspection": inspected, "release": release}, indent=2),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2]))
        '''
    )


@when("an external MCP client inspects and releases the held plain pytest failure")
def run_external_debug_mcp_plain_failure_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    client_path = consumer.path / "debug-mcp-plain-client.py"
    result_path = consumer.path / "debug-mcp-plain-client-result.json"
    try:
        discovery = _mcp_read_discovery_record(consumer)
        assert discovery.get("status") == "holding_failure", discovery
        failure = discovery.get("active_failure")
        assert isinstance(failure, dict), discovery
        assert failure.get("phase") == consumer._mcp_expected_plain_phase, failure
        assert failure.get("error_message") == consumer._mcp_expected_plain_message, failure
        assert failure.get("bdd_context") is None, failure
        endpoint = discovery.get("inspection_endpoint")
        _mcp_endpoint_port(endpoint)
        consumer._mcp_initial_discovery = discovery

        client_path.write_text(_debug_mcp_plain_failure_client_script(), encoding="utf-8")
        client_result = subprocess.run(
            [str(consumer.python), str(client_path), str(endpoint), str(result_path)],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        consumer._mcp_plain_client_result = client_result
        assert client_result.returncode == 0, (
            f"external MCP plain-failure client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        inspected = observation.get("inspection")
        inspected_failure = inspected.get("active_failure") if isinstance(inspected, dict) else None
        assert inspected_failure == failure, (inspected_failure, failure)
        assert inspected.get("session_id") == discovery.get("session_id"), (inspected, discovery)
        assert observation.get("release", {}).get("sequence") == failure.get("sequence"), observation
        consumer._mcp_plain_client_observation = observation

        return_code = process.wait(timeout=15)
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"releasing a failed plain pytest report changed pytest to success:\n{output}"
        final_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = json.loads(final_path.read_text(encoding="utf-8"))
        assert final_record.get("status") == "closed", final_record
        assert final_record.get("active_failure") is None, final_record
        assert final_record.get("last_release", {}).get("reason") == "explicit", final_record
        endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
        assert endpoints == [None, None], final_record
        consumer._mcp_final_record = final_record
        consumer._mcp_advertised_endpoints_after_finish = endpoints
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


@then(re.compile(r'the plain pytest MCP observation should show a "(?P<phase>call|setup|teardown)" failure with null BDD context'))
def consumer_plain_pytest_mcp_observation_has_null_bdd_context(phase: str, consumer: ConsumerProject) -> None:
    discovery = getattr(consumer, "_mcp_initial_discovery", None)
    observation = getattr(consumer, "_mcp_plain_client_observation", None)
    assert isinstance(discovery, dict) and isinstance(observation, dict), (discovery, observation)
    failure = discovery.get("active_failure")
    inspected = observation.get("inspection")
    assert isinstance(inspected, dict), observation
    inspected_failure = inspected.get("active_failure") if isinstance(inspected, dict) else None
    assert isinstance(failure, dict) and isinstance(inspected_failure, dict), observation
    assert failure == inspected_failure, (failure, inspected_failure)
    assert failure.get("phase") == phase == consumer._mcp_expected_plain_phase, failure
    assert failure.get("error_type") == "RuntimeError", failure
    assert failure.get("error_message") == consumer._mcp_expected_plain_message, failure
    assert failure.get("bdd_context") is None, failure
    assert str(failure.get("nodeid", "")).endswith("test_plain_pytest_failure.py::test_plain_pytest_failure"), failure


def _debug_mcp_stale_operations_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        def error_snapshot(result):
            return {
                "is_error": bool(getattr(result, "isError", False)),
                "content": [getattr(block, "text", "") for block in getattr(result, "content", [])],
            }

        async def main(endpoint, output_path):
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    first = tool_payload(await session.call_tool("inspect_failure", {}))
                    first_failure = first.get("active_failure")
                    session_id = first.get("session_id")
                    assert isinstance(first_failure, dict), first
                    assert isinstance(session_id, str) and session_id, first
                    first_sequence = first_failure.get("sequence")
                    assert isinstance(first_sequence, int), first_failure
                    first_release = tool_payload(
                        await session.call_tool(
                            "release_failure", {"session_id": session_id, "sequence": first_sequence}
                        )
                    )
                    assert first_release.get("released") is True, first_release

                    loop = asyncio.get_running_loop()
                    deadline = loop.time() + 25
                    second = None
                    second_failure = None
                    while loop.time() < deadline:
                        candidate = tool_payload(await session.call_tool("inspect_failure", {}))
                        active = candidate.get("active_failure")
                        if isinstance(active, dict) and active.get("sequence", 0) > first_sequence:
                            second = candidate
                            second_failure = active
                            break
                        await asyncio.sleep(0.1)
                    assert isinstance(second, dict) and isinstance(second_failure, dict), (
                        "pytest did not hold the next ordered failure"
                    )
                    assert second.get("session_id") == session_id, second
                    second_sequence = second_failure.get("sequence")
                    assert isinstance(second_sequence, int) and second_sequence > first_sequence, second_failure

                    stale_session = error_snapshot(
                        await session.call_tool(
                            "heartbeat", {"session_id": "stale-session-id", "sequence": second_sequence}
                        )
                    )
                    stale_sequence = error_snapshot(
                        await session.call_tool(
                            "release_failure", {"session_id": session_id, "sequence": first_sequence}
                        )
                    )
                    assert stale_session["is_error"], stale_session
                    assert stale_sequence["is_error"], stale_sequence
                    after_stale = tool_payload(await session.call_tool("inspect_failure", {}))
                    assert after_stale.get("active_failure") == second_failure, (after_stale, second_failure)

                    release_second = tool_payload(
                        await session.call_tool(
                            "release_failure", {"session_id": session_id, "sequence": second_sequence}
                        )
                    )
                    assert release_second.get("released") is True, release_second
                    Path(output_path).write_text(
                        json.dumps(
                            {
                                "first_failure": first_failure,
                                "second_failure": second_failure,
                                "stale_session": stale_session,
                                "stale_sequence": stale_sequence,
                                "after_stale": after_stale,
                                "release_second": release_second,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )

        asyncio.run(main(sys.argv[1], sys.argv[2]))
        '''
    )


@when("an external MCP client submits stale session and sequence operations while the next failure is held")
def run_external_debug_mcp_stale_operations_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    client_path = consumer.path / "debug-mcp-stale-operations-client.py"
    result_path = consumer.path / "debug-mcp-stale-operations-result.json"
    try:
        discovery = _mcp_read_discovery_record(consumer)
        assert discovery.get("status") == "holding_failure", discovery
        endpoint = discovery.get("inspection_endpoint")
        _mcp_endpoint_port(endpoint)
        consumer._mcp_initial_discovery = discovery
        client_path.write_text(_debug_mcp_stale_operations_client_script(), encoding="utf-8")
        client_result = subprocess.run(
            [str(consumer.python), str(client_path), str(endpoint), str(result_path)],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
        consumer._mcp_stale_operations_client_result = client_result
        assert client_result.returncode == 0, (
            f"external MCP stale-operation client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        consumer._mcp_stale_operations_observation = observation
        return_code = process.wait(timeout=15)
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"stale operations and valid release changed pytest to success:\n{output}"
        final_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = json.loads(final_path.read_text(encoding="utf-8"))
        assert final_record.get("status") == "closed", final_record
        assert final_record.get("active_failure") is None, final_record
        assert final_record.get("last_release", {}).get("sequence") == observation["second_failure"]["sequence"], final_record
        assert final_record.get("last_release", {}).get("reason") == "explicit", final_record
        consumer._mcp_final_record = final_record
        consumer._mcp_advertised_endpoints_after_finish = [
            final_record.get("debugger_endpoint"),
            final_record.get("inspection_endpoint"),
        ]
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


@then("the MCP stale-operation observation should show client errors and preserve the next failure")
def consumer_mcp_stale_operations_preserve_next_failure(consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_stale_operations_observation", None)
    assert isinstance(observation, dict), observation
    first = observation.get("first_failure")
    second = observation.get("second_failure")
    stale_session = observation.get("stale_session")
    stale_sequence = observation.get("stale_sequence")
    after_stale = observation.get("after_stale")
    assert isinstance(first, dict) and isinstance(second, dict), observation
    assert isinstance(stale_session, dict) and isinstance(stale_sequence, dict), observation
    for error in (stale_session, stale_sequence):
        assert error.get("is_error") is True, error
        text = " ".join(str(part) for part in error.get("content", []))
        assert "there is no active failure matching this Debug MCP session and sequence" in text, error
    assert first.get("sequence", 0) < second.get("sequence", 0), observation
    assert first.get("nodeid") != second.get("nodeid"), observation
    assert isinstance(after_stale, dict), observation
    assert after_stale.get("active_failure") == second, observation
    release = observation.get("release_second")
    assert isinstance(release, dict) and release.get("released") is True, observation


def _assert_debug_mcp_failure_context(
    failure: object, consumer: ConsumerProject | None = None
) -> dict[str, object]:
    assert isinstance(failure, dict), failure
    assert failure.get("phase") == "call", failure
    assert failure.get("error_type") == "RuntimeError", failure
    assert failure.get("error_message") == "debug MCP failure sentinel", failure
    assert isinstance(failure.get("nodeid"), str) and failure["nodeid"], failure
    assert isinstance(failure.get("sequence"), int) and failure["sequence"] > 0, failure
    context = failure.get("bdd_context")
    assert isinstance(context, dict), failure
    assert context.get("feature_name") == "MCP failure inspection probe", context
    scenario_name = context.get("scenario_name")
    assert isinstance(scenario_name, str), context
    assert scenario_name.startswith("The client can inspect the failing BDD step for <probe_id>"), context
    assert "[table_rows:[line:" in scenario_name, context
    assert context.get("step_keyword") == "When", context
    assert context.get("step_text") == 'the debugger probe raises "debug MCP failure sentinel"', context
    feature_path = context.get("feature_path")
    assert isinstance(feature_path, str) and feature_path, context
    if consumer is not None:
        path_value = feature_path.removeprefix("file:")
        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = consumer.path / candidate
        expected_path = (consumer.path / "features" / "debug-mcp-probe.feature").resolve()
        assert candidate.resolve() == expected_path, (feature_path, expected_path)
    tags = context.get("tags")
    assert isinstance(tags, list) and any(str(tag).lstrip("@") == "mcp-debug-probe" for tag in tags), context
    outline_row = context.get("outline_row")
    outline_row_json = json.dumps(outline_row, ensure_ascii=False)
    assert "outline-row-17" in outline_row_json and "debug MCP failure sentinel" in outline_row_json, context
    breadcrumb = context.get("breadcrumb")
    assert isinstance(breadcrumb, dict), context
    assert breadcrumb.get("feature_name") == "MCP failure inspection probe", context
    assert breadcrumb.get("scenario_name") == scenario_name, context
    breadcrumb_row = breadcrumb.get("outline_row")
    breadcrumb_row_json = json.dumps(breadcrumb_row, ensure_ascii=False)
    assert "outline-row-17" in breadcrumb_row_json and "debug MCP failure sentinel" in breadcrumb_row_json, context
    breadcrumb_step = breadcrumb.get("step")
    assert isinstance(breadcrumb_step, dict), context
    assert breadcrumb_step.get("keyword") == "When", context
    assert breadcrumb_step.get("text") == 'the debugger probe raises "debug MCP failure sentinel"', context
    return context


@when("an external MCP client inspects the advertised failure, heartbeats, and releases it")
def run_external_debug_mcp_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = getattr(consumer, "_mcp_pytest_command")
    output_path = getattr(consumer, "_mcp_pytest_output_path")
    client_path = consumer.path / "debug-mcp-client.py"
    result_path = consumer.path / "debug-mcp-client-result.json"
    client_result: subprocess.CompletedProcess[str] | None = None
    try:
        client_path.write_text(_debug_mcp_sdk_client_script(), encoding="utf-8")
        discovery = _mcp_read_discovery_record(consumer)
        inspection_endpoint = discovery.get("inspection_endpoint")
        debugger_endpoint = discovery.get("debugger_endpoint")
        inspection_host, inspection_port = _mcp_endpoint_port(inspection_endpoint)
        debugger_host, debugger_port = _mcp_endpoint_port(debugger_endpoint)
        assert inspection_host == debugger_host == "127.0.0.1", discovery
        assert inspection_endpoint != debugger_endpoint, discovery
        assert isinstance(discovery.get("session_id"), str) and discovery["session_id"], discovery
        assert isinstance(discovery.get("status"), str) and discovery["status"], discovery
        assert discovery.get("status") == "holding_failure", discovery
        _assert_debug_mcp_failure_context(discovery.get("active_failure"), consumer)
        setattr(consumer, "_mcp_initial_discovery", discovery)

        client_result = subprocess.run(
            [str(consumer.python), str(client_path), str(inspection_endpoint), str(result_path)],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=25,
        )
        setattr(consumer, "_mcp_client_result", client_result)
        assert client_result.returncode == 0, (
            f"external MCP SDK client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        assert result_path.is_file(), f"MCP client did not write its observation: {client_result.stdout}"
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert observation.get("endpoint") == inspection_endpoint, observation
        assert {"inspect_failure", "heartbeat", "release_failure"} <= set(observation.get("tools", [])), observation
        inspected = observation.get("inspection")
        assert isinstance(inspected, dict), observation
        assert inspected.get("session_id") == discovery["session_id"], observation
        assert inspected.get("status") == discovery["status"], observation
        client_failure = _assert_debug_mcp_failure_context(inspected.get("active_failure"), consumer)
        assert client_failure == discovery["active_failure"]["bdd_context"], (client_failure, discovery)
        assert isinstance(observation.get("heartbeat"), dict) and observation["heartbeat"], observation
        assert observation.get("after_heartbeat", {}).get("active_failure", {}).get("sequence") == discovery[
            "active_failure"
        ]["sequence"], observation
        assert observation.get("release", {}).get("released") is True, observation
        setattr(consumer, "_mcp_client_observation", observation)

        try:
            return_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("installed pytest did not resume after the external release") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"release changed the failed pytest outcome to success:\n{output}"
        assert f"Debug MCP session: {discovery['session_id']} (waiting)" in output, output
        assert f"Debug MCP debugger: {debugger_endpoint}" in output, output
        assert f"Debug MCP inspection: {inspection_endpoint}" in output, output
        discovery_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        assert f"Debug MCP discovery: {discovery_path}" in output, output
        active_failure = discovery.get("active_failure")
        assert isinstance(active_failure, dict), discovery
        expected_hold_announcement = (
            f"Debug MCP holding failure #{active_failure['sequence']} (call) at {active_failure['nodeid']}: "
            "RuntimeError: debug MCP failure sentinel"
        )
        assert expected_hold_announcement in output, output
        final_record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = (
            json.loads(final_record_path.read_text(encoding="utf-8")) if final_record_path.is_file() else None
        )
        setattr(consumer, "_mcp_final_record", final_record)
        endpoints = []
        if isinstance(final_record, dict):
            assert final_record.get("status") == "closed", final_record
            assert final_record.get("active_failure") is None, final_record
            endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
            assert endpoints == [None, None], final_record
        setattr(consumer, "_mcp_advertised_endpoints_after_finish", endpoints)
        for host, port in ((debugger_host, debugger_port), (inspection_host, inspection_port)):
            import socket

            try:
                connection = socket.create_connection((host, port), timeout=0.25)
            except OSError:
                continue
            connection.close()
            raise AssertionError(f"MCP endpoint {host}:{port} remained open after pytest finished")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if client_result is not None:
            setattr(consumer, "_mcp_client_result", client_result)


@when(
    re.compile(
        r'an external MCP client rejects mismatched artifacts and submits an investigation artifact under "(?P<artifact_root>[^"]+)"'
    )
)
def run_external_debug_mcp_artifact_client(artifact_root: str, consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    client_path = consumer.path / "debug-mcp-artifact-client.py"
    result_path = consumer.path / "debug-mcp-artifact-client-result.json"
    client_result: subprocess.CompletedProcess[str] | None = None
    try:
        _consumer_artifact_path(artifact_root, consumer)
        client_path.write_text(_debug_mcp_artifact_sdk_client_script(), encoding="utf-8")
        discovery = _mcp_read_discovery_record(consumer)
        inspection_endpoint = discovery.get("inspection_endpoint")
        _mcp_endpoint_port(inspection_endpoint)
        _assert_debug_mcp_failure_context(discovery.get("active_failure"), consumer)
        consumer._mcp_artifact_initial_discovery = discovery

        client_result = subprocess.run(
            [
                str(consumer.python),
                str(client_path),
                str(inspection_endpoint),
                str(result_path),
                artifact_root,
            ],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=25,
        )
        consumer._mcp_artifact_client_result = client_result
        assert client_result.returncode == 0, (
            f"external MCP artifact client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        assert result_path.is_file(), f"MCP artifact client did not write its observation: {client_result.stdout}"
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert observation.get("endpoint") == inspection_endpoint, observation
        assert {"inspect_failure", "submit_artifact", "release_failure"} <= set(observation.get("tools", [])), observation
        inspection = observation.get("inspection")
        assert isinstance(inspection, dict), observation
        assert inspection.get("session_id") == discovery.get("session_id"), observation
        client_failure = inspection.get("active_failure")
        assert client_failure == discovery.get("active_failure"), (client_failure, discovery)
        _assert_debug_mcp_failure_context(client_failure, consumer)
        consumer._mcp_artifact_observation = observation

        try:
            return_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("installed pytest did not resume after the artifact client released the failure") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"artifact submission changed the failed pytest outcome to success:\n{output}"

        final_record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = (
            json.loads(final_record_path.read_text(encoding="utf-8")) if final_record_path.is_file() else None
        )
        consumer._mcp_final_record = final_record
        endpoints = []
        if isinstance(final_record, dict):
            assert final_record.get("status") == "closed", final_record
            assert final_record.get("active_failure") is None, final_record
            endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
            assert endpoints == [None, None], final_record
        consumer._mcp_advertised_endpoints_after_finish = endpoints
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if client_result is not None:
            consumer._mcp_artifact_client_result = client_result


@when(
    re.compile(
        r'an external MCP client submits an artifact for the held plain pytest failure under "(?P<artifact_root>[^"]+)"'
    )
)
def run_external_debug_mcp_plain_artifact_client(artifact_root: str, consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    client_path = consumer.path / "debug-mcp-plain-artifact-client.py"
    result_path = consumer.path / "debug-mcp-plain-artifact-client-result.json"
    client_result: subprocess.CompletedProcess[str] | None = None
    try:
        _consumer_artifact_path(artifact_root, consumer)
        client_path.write_text(_debug_mcp_plain_artifact_sdk_client_script(), encoding="utf-8")
        discovery = _mcp_read_discovery_record(consumer)
        endpoint = discovery.get("inspection_endpoint")
        _mcp_endpoint_port(endpoint)
        failure = discovery.get("active_failure")
        assert isinstance(failure, dict), discovery
        assert failure.get("bdd_context") is None, failure
        consumer._mcp_artifact_initial_discovery = discovery

        client_result = subprocess.run(
            [str(consumer.python), str(client_path), str(endpoint), str(result_path), artifact_root],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=25,
        )
        consumer._mcp_artifact_client_result = client_result
        assert client_result.returncode == 0, (
            f"external plain-failure MCP artifact client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        assert result_path.is_file(), f"plain-failure MCP artifact client did not write its observation: {client_result.stdout}"
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert observation.get("endpoint") == endpoint, observation
        assert {"inspect_failure", "submit_artifact", "release_failure"} <= set(observation.get("tools", [])), observation
        inspection = observation.get("inspection")
        assert isinstance(inspection, dict), observation
        assert inspection.get("session_id") == discovery.get("session_id"), observation
        assert inspection.get("active_failure") == failure, (inspection, failure)
        assert inspection["active_failure"].get("bdd_context") is None, inspection
        consumer._mcp_artifact_observation = observation

        try:
            return_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("installed pytest did not resume after plain-failure artifact release") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"plain-failure artifact submission changed pytest to success:\n{output}"

        final_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = json.loads(final_path.read_text(encoding="utf-8"))
        consumer._mcp_final_record = final_record
        assert final_record.get("status") == "closed", final_record
        assert final_record.get("active_failure") is None, final_record
        assert final_record.get("last_release", {}).get("sequence") == failure.get("sequence"), final_record
        assert final_record.get("last_release", {}).get("artifact_status") == "written", final_record
        endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
        assert endpoints == [None, None], final_record
        consumer._mcp_advertised_endpoints_after_finish = endpoints
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if client_result is not None:
            consumer._mcp_artifact_client_result = client_result


@when("an external MCP client submits an artifact and releases the held failure after the write fails")
def run_external_debug_mcp_filesystem_failure_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    client_path = consumer.path / "debug-mcp-filesystem-failure-client.py"
    result_path = consumer.path / "debug-mcp-filesystem-failure-client-result.json"
    client_result: subprocess.CompletedProcess[str] | None = None
    try:
        client_path.write_text(_debug_mcp_filesystem_failure_sdk_client_script(), encoding="utf-8")
        discovery = _mcp_read_discovery_record(consumer)
        endpoint = discovery.get("inspection_endpoint")
        _mcp_endpoint_port(endpoint)
        _assert_debug_mcp_failure_context(discovery.get("active_failure"), consumer)
        consumer._mcp_filesystem_artifact_initial_discovery = discovery

        client_result = subprocess.run(
            [str(consumer.python), str(client_path), str(endpoint), str(result_path)],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=25,
        )
        consumer._mcp_filesystem_artifact_client_result = client_result
        assert client_result.returncode == 0, (
            f"external MCP filesystem-failure client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        assert result_path.is_file(), f"MCP filesystem-failure client did not write its observation: {client_result.stdout}"
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert observation.get("endpoint") == endpoint, observation
        assert {"inspect_failure", "submit_artifact", "release_failure"} <= set(observation.get("tools", [])), observation
        consumer._mcp_filesystem_artifact_observation = observation

        try:
            return_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("installed pytest did not resume after the filesystem-error release") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"filesystem failure and release changed pytest's failed outcome to success:\n{output}"

        final_record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = (
            json.loads(final_record_path.read_text(encoding="utf-8")) if final_record_path.is_file() else None
        )
        consumer._mcp_final_record = final_record
        endpoints = []
        if isinstance(final_record, dict):
            assert final_record.get("status") == "closed", final_record
            assert final_record.get("active_failure") is None, final_record
            endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
            assert endpoints == [None, None], final_record
        consumer._mcp_advertised_endpoints_after_finish = endpoints
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if client_result is not None:
            consumer._mcp_filesystem_artifact_client_result = client_result


@when("an external MCP client tries the first failure sequence after the next failure is held")
def run_external_debug_mcp_stale_artifact_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    client_path = consumer.path / "debug-mcp-stale-artifact-client.py"
    result_path = consumer.path / "debug-mcp-stale-artifact-client-result.json"
    client_result: subprocess.CompletedProcess[str] | None = None
    try:
        client_path.write_text(_debug_mcp_stale_artifact_sdk_client_script(), encoding="utf-8")
        discovery = _mcp_read_discovery_record(consumer)
        endpoint = discovery.get("inspection_endpoint")
        _mcp_endpoint_port(endpoint)
        consumer._mcp_stale_artifact_initial_discovery = discovery

        client_result = subprocess.run(
            [str(consumer.python), str(client_path), str(endpoint), str(result_path)],
            cwd=consumer.path,
            env=consumer.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
        consumer._mcp_stale_artifact_client_result = client_result
        assert client_result.returncode == 0, (
            f"external MCP stale-artifact client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        assert result_path.is_file(), f"MCP stale-artifact client did not write its observation: {client_result.stdout}"
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert {"inspect_failure", "submit_artifact", "release_failure"} <= set(observation.get("tools", [])), observation
        consumer._mcp_stale_artifact_observation = observation

        try:
            return_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("installed pytest did not resume after release of its second held failure") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"releasing the ordered failures changed pytest's failed outcome to success:\n{output}"

        final_record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = (
            json.loads(final_record_path.read_text(encoding="utf-8")) if final_record_path.is_file() else None
        )
        consumer._mcp_final_record = final_record
        endpoints = []
        if isinstance(final_record, dict):
            assert final_record.get("status") == "closed", final_record
            assert final_record.get("active_failure") is None, final_record
            endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
            assert endpoints == [None, None], final_record
        consumer._mcp_advertised_endpoints_after_finish = endpoints
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if client_result is not None:
            consumer._mcp_stale_artifact_client_result = client_result


@when("an external MCP client continues a session through the advertised debugger endpoint")
def run_debugger_mcp_continuation_client(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = getattr(consumer, "_mcp_pytest_command")
    output_path = getattr(consumer, "_mcp_pytest_output_path")
    client_path = consumer.path / "debug-mcp-continuation-client.py"
    result_path = consumer.path / "debug-mcp-continuation-client-result.json"
    stage_path = consumer.path / "debug-mcp-continuation-client-stage.txt"
    target_path = consumer.path / "debug-mcp-debugger-target.py"
    completion_path = consumer.path / "debugger-continuation-completed.txt"
    client_result: subprocess.CompletedProcess[str] | None = None
    try:
        assert target_path.is_file(), target_path
        client_path.write_text(_debug_mcp_debugger_continuation_client_script(), encoding="utf-8")
        stage_path.unlink(missing_ok=True)
        discovery = _mcp_read_discovery_record(consumer)
        inspection_endpoint = discovery.get("inspection_endpoint")
        debugger_endpoint = discovery.get("debugger_endpoint")
        inspection_host, _inspection_port = _mcp_endpoint_port(inspection_endpoint)
        debugger_host, _debugger_port = _mcp_endpoint_port(debugger_endpoint)
        assert inspection_host == debugger_host == "127.0.0.1", discovery
        assert isinstance(discovery.get("session_id"), str) and discovery["session_id"], discovery
        initial_failure = discovery.get("active_failure")
        assert isinstance(initial_failure, dict), discovery
        _assert_debug_mcp_failure_context(initial_failure, consumer)
        setattr(consumer, "_mcp_initial_discovery", discovery)

        client_result = _run_debug_mcp_external_client(
            consumer,
            [
                str(consumer.python),
                str(client_path),
                str(debugger_endpoint),
                str(inspection_endpoint),
                str(target_path),
                str(result_path),
                str(stage_path),
            ],
            client_name="external debugger MCP client",
            timeout=60,
            stage_path=stage_path,
            log_path=consumer.path / "debug-mcp-continuation-client.log",
        )
        setattr(consumer, "_mcp_debugger_client_result", client_result)
        assert client_result.returncode == 0, (
            f"external debugger MCP client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        assert result_path.is_file(), f"debugger MCP client did not write its observation: {client_result.stdout}"
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert observation.get("debugger_endpoint") == debugger_endpoint, observation
        assert observation.get("inspection_endpoint") == inspection_endpoint, observation
        assert {"start_debug", "send_pdb_command"} <= set(observation.get("tools", [])), observation
        before = observation.get("active_before")
        assert isinstance(before, dict), observation
        assert before.get("session_id") == discovery["session_id"], observation
        failure = before.get("active_failure")
        assert isinstance(failure, dict), observation
        assert failure == initial_failure, (failure, initial_failure)
        assert completion_path.read_text(encoding="utf-8") == "continued\n", (
            "the advertised mcp-pdb continue command did not run the debug target"
        )
        setattr(consumer, "_mcp_debugger_continuation_observation", observation)

        try:
            return_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("installed pytest did not resume after debugger continuation") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"debugger continuation changed the failed pytest outcome to success:\n{output}"

        final_record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
        final_record = (
            json.loads(final_record_path.read_text(encoding="utf-8")) if final_record_path.is_file() else None
        )
        setattr(consumer, "_mcp_final_record", final_record)
        assert isinstance(final_record, dict), "pytest did not retain the final Debug MCP discovery record"
        assert final_record.get("status") == "closed", final_record
        assert final_record.get("active_failure") is None, final_record
        last_release = final_record.get("last_release")
        assert isinstance(last_release, dict), final_record
        assert last_release.get("session_id") == before.get("session_id"), (last_release, before)
        assert last_release.get("sequence") == failure.get("sequence"), (last_release, failure)
        assert last_release.get("reason") == "debugger_continuation", final_record
        endpoints = [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
        assert endpoints == [None, None], final_record
        setattr(consumer, "_mcp_advertised_endpoints_after_finish", endpoints)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if client_result is not None:
            setattr(consumer, "_mcp_debugger_client_result", client_result)


@then("debugger continuation should release the exact advertised failure")
def consumer_debugger_continuation_releases_exact_failure(consumer: ConsumerProject) -> None:
    discovery = getattr(consumer, "_mcp_initial_discovery", None)
    final_record = getattr(consumer, "_mcp_final_record", None)
    observation = getattr(consumer, "_mcp_debugger_continuation_observation", None)
    assert isinstance(discovery, dict), discovery
    assert isinstance(final_record, dict), final_record
    assert isinstance(observation, dict), observation
    initial_failure = discovery.get("active_failure")
    before = observation.get("active_before")
    assert isinstance(initial_failure, dict) and isinstance(before, dict), observation
    inspected_failure = before.get("active_failure")
    last_release = final_record.get("last_release")
    assert isinstance(inspected_failure, dict) and isinstance(last_release, dict), final_record
    assert before.get("session_id") == discovery.get("session_id") == last_release.get("session_id"), final_record
    assert inspected_failure == initial_failure, (inspected_failure, initial_failure)
    assert inspected_failure.get("sequence") == last_release.get("sequence"), (
        inspected_failure,
        last_release,
    )
    assert last_release.get("reason") == "debugger_continuation", final_record


@then("the consumer should report no MCP backend import or child process")
def consumer_reports_no_mcp_startup(consumer: ConsumerProject) -> None:
    marker = consumer.path / "mcp-startup-observations.log"
    assert not marker.exists(), marker.read_text(encoding="utf-8") if marker.exists() else ""
    assert not (consumer.path / "probe-continuation.log").exists()


@then("the MCP client observation should confirm the advertised endpoint and BDD failure context")
def consumer_mcp_client_observation_confirms_context(consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_client_observation", None)
    assert isinstance(observation, dict), observation
    discovery = getattr(consumer, "_mcp_initial_discovery", None)
    assert isinstance(discovery, dict), discovery
    assert observation["endpoint"] == discovery["inspection_endpoint"]
    failure = observation["inspection"]["active_failure"]
    _assert_debug_mcp_failure_context(failure, consumer)
    assert isinstance(observation.get("heartbeat"), dict) and observation["heartbeat"]
    assert observation.get("after_heartbeat", {}).get("active_failure", {}).get("sequence") == failure[
        "sequence"
    ], observation
    assert observation["release"].get("released") is True


@then("the MCP artifact observation should confirm strict validation, failure binding, BDD metadata, and written release status")
def consumer_mcp_artifact_observation_confirms_contract(consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_artifact_observation", None)
    assert isinstance(observation, dict), observation
    invalid_submissions = observation.get("invalid_submissions")
    assert isinstance(invalid_submissions, dict), observation
    assert set(invalid_submissions) == {
        "wrong_json_type",
        "wrong_phase",
        "wrong_status",
        "extra_key",
        "missing_required",
    }, invalid_submissions
    for case_name, invalid in invalid_submissions.items():
        assert isinstance(invalid, dict), (case_name, invalid)
        assert invalid.get("ok") is False, (case_name, invalid)
        assert invalid.get("error") == "validation_error", (case_name, invalid)
        assert invalid.get("details"), (case_name, invalid)
        assert "json_path" not in invalid and "markdown_path" not in invalid, (case_name, invalid)

    mismatch_submissions = observation.get("mismatch_submissions")
    assert isinstance(mismatch_submissions, dict), observation
    assert set(mismatch_submissions) == {"wrong_nodeid", "wrong_allowed_phase"}, mismatch_submissions
    inspection = observation.get("inspection")
    assert isinstance(inspection, dict), observation
    failure = inspection.get("active_failure")
    assert isinstance(failure, dict), inspection
    for case_name, mismatch in mismatch_submissions.items():
        assert isinstance(mismatch, dict), (case_name, mismatch)
        response = mismatch.get("response")
        assert isinstance(response, dict), (case_name, mismatch)
        assert response.get("ok") is False, (case_name, response)
        assert response.get("error") == "failure_mismatch", (case_name, response)
        assert response.get("details"), (case_name, response)
        assert not {"json_path", "markdown_path", "artifact_status"}.intersection(response), (case_name, response)
        assert mismatch.get("active_after") == failure, (case_name, mismatch, failure)
        assert mismatch.get("artifact_root_entries_after") == [], (case_name, mismatch)

    submitted = observation.get("submitted_artifact")
    valid = observation.get("valid_submission")
    assert isinstance(submitted, dict), observation
    assert isinstance(valid, dict), observation
    assert valid.get("artifact_id") == submitted.get("artifact_id"), valid
    assert valid.get("json_path") and valid.get("markdown_path"), valid

    metadata = submitted.get("bdd_metadata")
    assert isinstance(metadata, dict), submitted
    assert metadata.get("feature_name") == "Forged feature", metadata
    assert metadata.get("example_row", {}).get("probe_id") == "forged-row", metadata
    active_bdd_metadata = observation.get("active_bdd_metadata")
    assert isinstance(active_bdd_metadata, dict), observation
    context = failure.get("bdd_context")
    assert isinstance(context, dict), failure
    assert active_bdd_metadata == {
        "feature_path": context.get("feature_path"),
        "feature_name": context.get("feature_name"),
        "scenario_name": context.get("scenario_name"),
        "step_keyword": context.get("step_keyword"),
        "step_text": context.get("step_text"),
        "tags": context.get("tags", []),
        "example_row": context.get("outline_row") or {},
    }, (active_bdd_metadata, context)
    assert active_bdd_metadata.get("feature_name") == "MCP failure inspection probe", active_bdd_metadata
    assert active_bdd_metadata.get("scenario_name", "").startswith(
        "The client can inspect the failing BDD step for <probe_id>"
    ), active_bdd_metadata
    assert active_bdd_metadata.get("step_keyword") == "When", active_bdd_metadata
    assert active_bdd_metadata.get("step_text") == 'the debugger probe raises "debug MCP failure sentinel"', (
        active_bdd_metadata
    )
    assert active_bdd_metadata.get("example_row", {}).get("probe_id") == "outline-row-17", active_bdd_metadata

    release = observation.get("release")
    assert isinstance(release, dict), observation
    assert release.get("released") is True, release
    assert release.get("artifact_status") == "written", release


@then("the plain failure artifact observation should confirm null BDD context, default metadata, and written release status")
def consumer_mcp_plain_artifact_observation_confirms_contract(consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_artifact_observation", None)
    assert isinstance(observation, dict), observation
    inspection = observation.get("inspection")
    submitted = observation.get("submitted_artifact")
    result = observation.get("valid_submission")
    release = observation.get("release")
    assert isinstance(inspection, dict), observation
    failure = inspection.get("active_failure")
    assert isinstance(failure, dict), inspection
    assert failure.get("bdd_context") is None, failure
    assert isinstance(submitted, dict), observation
    assert "bdd_metadata" not in submitted, submitted
    assert isinstance(result, dict) and result.get("ok") is True, observation
    assert result.get("artifact_id") == submitted.get("artifact_id"), result
    assert result.get("json_path") and result.get("markdown_path"), result
    assert isinstance(release, dict) and release.get("released") is True, observation
    assert release.get("artifact_status") == "written", release
    pytest_result = consumer.pytest_result
    assert pytest_result is not None and pytest_result.returncode != 0, pytest_result


def _resolve_debug_mcp_artifact_path(value: object, artifact_root: Path) -> Path:
    assert isinstance(value, str) and value, value
    candidate = Path(value)
    assert candidate.is_absolute(), f"Debug MCP artifact path must be absolute: {candidate}"
    resolved = candidate.resolve()
    resolved_root = artifact_root.resolve()
    assert resolved.is_relative_to(resolved_root), f"Debug MCP artifact escaped its configured root: {resolved}"
    return resolved


def _expected_debug_mcp_artifact_bdd_metadata(failure: dict[str, Any]) -> dict[str, Any]:
    context = failure.get("bdd_context")
    if context is None:
        return {
            "feature_path": None,
            "feature_name": None,
            "scenario_name": None,
            "step_keyword": None,
            "step_text": None,
            "tags": [],
            "example_row": {},
        }
    assert isinstance(context, dict), failure
    return {
        "feature_path": context.get("feature_path"),
        "feature_name": context.get("feature_name"),
        "scenario_name": context.get("scenario_name"),
        "step_keyword": context.get("step_keyword"),
        "step_text": context.get("step_text"),
        "tags": context.get("tags", []),
        "example_row": context.get("outline_row") or {},
    }


@then(
    re.compile(
        r'the consumer MCP artifact files should contain the submitted JSON and Markdown pair under "(?P<artifact_root>[^"]+)"'
    )
)
def consumer_mcp_artifact_files_contain_pair(artifact_root: str, consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_artifact_observation", None)
    assert isinstance(observation, dict), observation
    submitted = observation.get("submitted_artifact")
    result = observation.get("valid_submission")
    inspection = observation.get("inspection")
    assert isinstance(submitted, dict) and isinstance(result, dict) and isinstance(inspection, dict), observation
    failure = inspection.get("active_failure")
    assert isinstance(failure, dict), inspection

    artifact_root_path = _consumer_artifact_path(artifact_root, consumer)
    json_path = _resolve_debug_mcp_artifact_path(result.get("json_path"), artifact_root_path)
    markdown_path = _resolve_debug_mcp_artifact_path(result.get("markdown_path"), artifact_root_path)
    assert json_path.is_file(), f"Debug MCP JSON artifact was not written: {json_path}"
    assert markdown_path.is_file(), f"Debug MCP Markdown artifact was not written: {markdown_path}"
    assert json_path.suffix == ".json", json_path
    assert markdown_path.suffix in {".md", ".markdown"}, markdown_path
    assert json_path.stem == markdown_path.stem, (json_path, markdown_path)

    document = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(document, dict), document
    saved_artifact = document
    for field in (
        "artifact_id",
        "nodeid",
        "pytest_phase",
        "status",
        "summary",
        "inspected_commands",
        "evidence",
        "suspected_cause",
        "next_action",
    ):
        assert saved_artifact.get(field) == submitted.get(field), (field, saved_artifact, submitted)
    observation = getattr(consumer, "_mcp_artifact_observation", None)
    assert isinstance(observation, dict), observation
    expected_bdd_metadata = _expected_debug_mcp_artifact_bdd_metadata(failure)
    assert saved_artifact.get("bdd_metadata") == expected_bdd_metadata, (saved_artifact, expected_bdd_metadata)
    saved_metadata = saved_artifact.get("bdd_metadata")
    assert isinstance(saved_metadata, dict), saved_artifact

    markdown = markdown_path.read_text(encoding="utf-8")
    assert submitted["artifact_id"] in markdown, markdown
    assert submitted["summary"] in markdown, markdown
    if failure.get("bdd_context") is None:
        assert "## BDD context" not in markdown, markdown
    else:
        assert saved_metadata.get("example_row", {}).get("probe_id") == "outline-row-17", saved_metadata
        assert "outline-row-17" in markdown, markdown
        assert 'the debugger probe raises "debug MCP failure sentinel"' in markdown, markdown
        assert "Forged feature" not in markdown, markdown


@then(
    re.compile(
        r'the consumer artifact hook should report the active BDD failure and saved paths under "(?P<artifact_root>[^"]+)"'
    )
)
def consumer_mcp_artifact_hook_matches_files(artifact_root: str, consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_artifact_observation", None)
    discovery = getattr(consumer, "_mcp_artifact_initial_discovery", None)
    assert isinstance(observation, dict), observation
    assert isinstance(discovery, dict), discovery
    submitted = observation.get("submitted_artifact")
    result = observation.get("valid_submission")
    assert isinstance(submitted, dict) and isinstance(result, dict), observation

    hook_path = consumer.path / "debug-mcp-artifact-hook.json"
    assert hook_path.is_file(), f"pytest_cuke_debug_mcp_artifact_created was not called: {hook_path}"
    hook = json.loads(hook_path.read_text(encoding="utf-8"))
    failure = discovery.get("active_failure")
    assert isinstance(failure, dict), discovery
    assert hook.get("nodeid") == failure.get("nodeid"), hook
    assert hook.get("pytest_phase") == failure.get("phase") == "call", hook
    assert hook.get("bdd_metadata") == _expected_debug_mcp_artifact_bdd_metadata(failure), hook
    assert hook.get("bdd_metadata") != submitted.get("bdd_metadata"), hook
    artifact_root_path = _consumer_artifact_path(artifact_root, consumer)
    assert _resolve_debug_mcp_artifact_path(hook.get("json_path"), artifact_root_path) == _resolve_debug_mcp_artifact_path(
        result.get("json_path"), artifact_root_path
    ), hook
    assert _resolve_debug_mcp_artifact_path(hook.get("markdown_path"), artifact_root_path) == _resolve_debug_mcp_artifact_path(
        result.get("markdown_path"), artifact_root_path
    ), hook
    assert hook.get("status") == submitted.get("status"), hook
    assert hook.get("summary") == submitted.get("summary"), hook


@then("the MCP artifact client observation should show the stale sequence did not affect the next failure")
def consumer_mcp_stale_artifact_observation_confirms_isolation(consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_stale_artifact_observation", None)
    assert isinstance(observation, dict), observation
    first = observation.get("first_failure")
    second = observation.get("second_failure")
    stale = observation.get("stale_submission")
    after_stale = observation.get("after_stale")
    assert isinstance(first, dict) and isinstance(second, dict), observation
    assert isinstance(stale, dict) and isinstance(after_stale, dict), observation
    assert first.get("sequence", 0) < second.get("sequence", 0), (first, second)
    assert first.get("nodeid") != second.get("nodeid"), (first, second)
    assert first.get("bdd_context", {}).get("outline_row", {}).get("probe_id") == "outline-row-17", first
    assert second.get("bdd_context", {}).get("outline_row", {}).get("probe_id") == "outline-row-18", second
    assert stale.get("ok") is False, stale
    assert stale.get("error") == "failure_unavailable", stale
    assert stale.get("details"), stale
    assert "json_path" not in stale and "markdown_path" not in stale, stale
    active_after_stale = after_stale.get("active_failure")
    assert isinstance(active_after_stale, dict), after_stale
    assert active_after_stale.get("sequence") == second.get("sequence"), after_stale
    assert active_after_stale.get("nodeid") == second.get("nodeid"), after_stale
    assert active_after_stale.get("bdd_context", {}).get("outline_row", {}).get("probe_id") == "outline-row-18", after_stale

    first_release = observation.get("first_release")
    second_release = observation.get("second_release")
    assert isinstance(first_release, dict) and isinstance(second_release, dict), observation
    assert first_release.get("released") is True, first_release
    assert first_release.get("artifact_status") == "written", first_release
    assert second_release.get("released") is True, second_release
    assert second_release.get("artifact_status") == "missing", second_release


@then("the MCP filesystem error observation should show the failure remained held until release")
def consumer_mcp_filesystem_error_preserves_held_failure(consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_filesystem_artifact_observation", None)
    discovery = getattr(consumer, "_mcp_filesystem_artifact_initial_discovery", None)
    assert isinstance(observation, dict), observation
    assert isinstance(discovery, dict), discovery
    failure = observation.get("inspection", {}).get("active_failure")
    after_failure = observation.get("after_failure", {}).get("active_failure")
    artifact = observation.get("artifact")
    error = observation.get("failed_submission")
    release = observation.get("release")
    assert isinstance(failure, dict) and isinstance(after_failure, dict), observation
    assert isinstance(artifact, dict) and isinstance(error, dict) and isinstance(release, dict), observation
    assert observation.get("inspection", {}).get("session_id") == discovery.get("session_id"), observation
    assert failure.get("sequence") == discovery.get("active_failure", {}).get("sequence"), observation
    assert after_failure.get("sequence") == failure.get("sequence"), (failure, after_failure)
    assert after_failure.get("nodeid") == failure.get("nodeid"), (failure, after_failure)
    assert after_failure.get("phase") == failure.get("phase") == "call", (failure, after_failure)
    assert error.get("ok") is False, error
    assert error.get("error") == "filesystem_error", error
    assert error.get("details"), error
    assert "json_path" not in error and "markdown_path" not in error, error
    assert release.get("released") is True, release
    assert release.get("artifact_status") == "missing", release

    blocker = consumer.path / "occupied-root"
    assert blocker.is_file(), blocker
    assert not (blocker / "child").exists(), "artifact sink created a child beneath a regular file"
    assert not (consumer.path / "debug-mcp-artifact-hook.json").exists(), (
        "artifact-created hook ran despite the failed filesystem write"
    )


@then("the MCP discovery record should no longer advertise a live endpoint")
def consumer_mcp_discovery_has_no_live_endpoint(consumer: ConsumerProject) -> None:
    endpoints = getattr(consumer, "_mcp_advertised_endpoints_after_finish", None)
    assert isinstance(endpoints, list), endpoints
    assert not any(endpoints), f"discovery record still advertises endpoints after pytest exited: {endpoints}"


@then("installed pytest help should describe the Debug MCP options and defaults")
def consumer_pytest_help_documents_debug_mcp_defaults(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None, "installed pytest help has not been captured"
    assert result.returncode == 0, f"pytest --help failed:\n{result.stdout}\n{result.stderr}"
    output = re.sub(r"\s+", " ", f"{result.stdout}\n{result.stderr}").casefold()
    for option in (
        "--cuke-mcp-on-fail",
        "--cuke-mcp-timeout",
        "--cuke-mcp-lease",
        "--cuke-mcp-host",
        "--cuke-mcp-port",
        "default: 30 seconds",
        "default: 10 seconds",
        "default: 127.0.0.1",
        "default: auto",
    ):
        assert option.casefold() in output, f"pytest --help did not include {option!r}:\n{result.stdout}\n{result.stderr}"


@when("the harness interrupts only the active pytest consumer process")
def interrupt_active_debug_mcp_consumer_process(consumer: ConsumerProject) -> None:
    import signal

    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    discovery = _mcp_read_discovery_record(consumer, timeout=20)
    assert discovery.get("status") == "holding_failure", discovery
    failure = discovery.get("active_failure")
    assert isinstance(failure, dict), discovery
    consumer._mcp_initial_discovery = discovery

    guard_path = consumer.path / "mcp-startup-observations.log"
    if os.name == "nt":
        ready_deadline = time.monotonic() + 15
        while time.monotonic() < ready_deadline:
            guard_output = guard_path.read_text(encoding="utf-8") if guard_path.is_file() else ""
            ready_events = set(
                re.findall(r"^signal-handler-ready:(consumer|backend):(\d+)$", guard_output, re.MULTILINE)
            )
            outer_groups = re.findall(r"^outer-process-group:(\d+):(\d+)$", guard_output, re.MULTILINE)
            backend_groups = re.findall(r"^backend-process-group:(\d+):(\d+)$", guard_output, re.MULTILINE)
            has_consumer_handler = ("consumer", str(process.pid)) in ready_events
            has_backend_handler = any(role == "backend" for role, _pid in ready_events)
            if has_consumer_handler and has_backend_handler and outer_groups and backend_groups:
                break
            if process.poll() is not None:
                output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
                raise AssertionError(
                    f"pytest exited before consumer/backend Ctrl+Break handlers were ready:\n{guard_output}\n{output}"
                )
            time.sleep(0.05)
        else:
            raise AssertionError(
                "consumer/backend Ctrl+Break handlers did not become ready within 15 seconds:\n"
                f"{guard_output}"
            )

    interrupt = signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT
    process.send_signal(interrupt)
    try:
        return_code = process.wait(timeout=15)
    except subprocess.TimeoutExpired as error:
        process.kill()
        process.wait(timeout=3)
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        raise AssertionError(f"interrupted pytest did not close within 15 seconds:\n{output}") from error
    output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
    consumer._mcp_interrupted_failure = failure
    final_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
    final_record: object | None = None
    cleanup_deadline = time.monotonic() + 5
    while time.monotonic() < cleanup_deadline:
        try:
            payload = json.loads(final_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            final_record = payload
            if payload.get("status") == "closed" and payload.get("active_failure") is None:
                break
        time.sleep(0.05)
    consumer._mcp_final_record = final_record
    consumer._mcp_advertised_endpoints_after_finish = (
        [final_record.get("debugger_endpoint"), final_record.get("inspection_endpoint")]
        if isinstance(final_record, dict)
        else None
    )
    guard_output = guard_path.read_text(encoding="utf-8") if guard_path.is_file() else ""
    consumer._mcp_interrupted_pid = str(process.pid)
    consumer._mcp_interrupted_guard_lines = guard_output.splitlines()
    consumer._mcp_interrupted_signal_events = re.findall(
        r"^signal:SIGBREAK:(consumer|backend):(\d+)$", guard_output, re.MULTILINE
    )
    consumer._mcp_interrupted_handler_ready_events = re.findall(
        r"^signal-handler-ready:(consumer|backend):(\d+)$", guard_output, re.MULTILINE
    )
    consumer._mcp_interrupted_outer_process_groups = re.findall(
        r"^outer-process-group:(\d+):(\d+)$", guard_output, re.MULTILINE
    )
    consumer._mcp_interrupted_backend_process_groups = re.findall(
        r"^backend-process-group:(\d+):(\d+)$", guard_output, re.MULTILINE
    )
    consumer._mcp_interrupted_backend_cleanups = re.findall(
        r"^backend-cleanup:(\d+)$", guard_output, re.MULTILINE
    )
    consumer._mcp_interrupted_child_pids = re.findall(r"^child:(\d+):", guard_output, re.MULTILINE)
    consumer._mcp_interrupted_child_statuses = {
        pid: status
        for pid, status in re.findall(r"^child-status:(\d+):([^\n]+)$", guard_output, re.MULTILINE)
    }


@then("the interrupted pytest process should finish with failure and close its debugger child")
def consumer_interrupted_debug_mcp_process_is_closed(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    failure = getattr(consumer, "_mcp_interrupted_failure", None)
    final_record = getattr(consumer, "_mcp_final_record", None)
    child_pids = getattr(consumer, "_mcp_interrupted_child_pids", None)
    child_statuses = getattr(consumer, "_mcp_interrupted_child_statuses", None)
    assert result is not None and result.returncode != 0, result
    assert isinstance(failure, dict), failure
    assert isinstance(final_record, dict), final_record
    assert final_record.get("status") == "closed", final_record
    assert final_record.get("active_failure") is None, final_record
    assert final_record.get("last_release", {}).get("sequence") == failure.get("sequence"), final_record
    assert final_record.get("last_release", {}).get("reason") == "shutdown", final_record
    assert isinstance(child_pids, list) and child_pids, child_pids
    assert isinstance(child_statuses, dict), child_statuses
    assert all(pid in child_statuses and child_statuses[pid] != "None" for pid in child_pids), (
        child_pids,
        child_statuses,
    )
    if os.name == "nt":
        consumer_pid = getattr(consumer, "_mcp_interrupted_pid", None)
        ready_events = getattr(consumer, "_mcp_interrupted_handler_ready_events", None)
        signals = getattr(consumer, "_mcp_interrupted_signal_events", None)
        outer_groups = getattr(consumer, "_mcp_interrupted_outer_process_groups", None)
        backend_groups = getattr(consumer, "_mcp_interrupted_backend_process_groups", None)
        backend_cleanups = getattr(consumer, "_mcp_interrupted_backend_cleanups", None)
        guard_lines = getattr(consumer, "_mcp_interrupted_guard_lines", None)
        assert isinstance(consumer_pid, str) and consumer_pid, consumer_pid
        assert isinstance(ready_events, list), ready_events
        assert ("consumer", consumer_pid) in ready_events, ready_events
        assert isinstance(outer_groups, list) and len(outer_groups) == 1, outer_groups
        outer_pid, outer_flags_text = outer_groups[0]
        outer_flags = int(outer_flags_text)
        assert outer_pid == consumer_pid, outer_groups
        assert outer_flags & subprocess.CREATE_NEW_PROCESS_GROUP, outer_groups
        console_isolation_flags = (
            subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        )
        assert (outer_flags & console_isolation_flags) == 0, outer_groups
        assert isinstance(backend_groups, list) and len(backend_groups) == 1, backend_groups
        backend_pid, backend_flags_text = backend_groups[0]
        backend_flags = int(backend_flags_text)
        assert backend_pid != consumer_pid, (consumer_pid, backend_groups)
        assert backend_flags & subprocess.CREATE_NEW_PROCESS_GROUP, backend_groups
        assert (backend_flags & console_isolation_flags) == 0, backend_groups
        assert ("backend", backend_pid) in ready_events, ready_events
        assert isinstance(signals, list) and signals == [("consumer", consumer_pid)], signals
        assert isinstance(backend_cleanups, list) and backend_cleanups == [backend_pid], backend_cleanups
        assert isinstance(guard_lines, list), guard_lines
        consumer_signal = f"signal:SIGBREAK:consumer:{consumer_pid}"
        backend_cleanup = f"backend-cleanup:{backend_pid}"
        assert consumer_signal in guard_lines and backend_cleanup in guard_lines, guard_lines
        assert guard_lines.index(consumer_signal) < guard_lines.index(backend_cleanup), guard_lines
        assert not any(
            line.startswith("signal:SIGBREAK:backend:")
            for line in guard_lines[: guard_lines.index(backend_cleanup)]
        ), guard_lines


@then(re.compile(r'consumer artifact "(?P<relative_path>[^"]+)" should retain the failed debugger BDD scenario'))
def consumer_debug_mcp_json_report_retains_failure(relative_path: str, consumer: ConsumerProject) -> None:
    report_path = _consumer_artifact_path(relative_path, consumer)
    assert report_path.is_file(), f"Cucumber JSON report was not written: {report_path}"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    scenarios = [
        scenario
        for feature in report
        for scenario in feature.get("elements", [])
        if isinstance(scenario.get("name"), str)
        and scenario["name"].startswith("The client can inspect the failing BDD step for <probe_id>")
        and isinstance(scenario.get("id"), str)
        and "[table_rows:[line:" in scenario["id"]
    ]
    assert len(scenarios) == 1, scenarios
    statuses = [step.get("result", {}).get("status") for step in scenarios[0].get("steps", [])]
    assert statuses == ["passed", "failed", "skipped"], statuses
    report_text = json.dumps(scenarios[0], ensure_ascii=False)
    assert "debug MCP failure sentinel" in report_text, scenarios[0]


@then(re.compile(r'consumer artifact "(?P<relative_path>[^"]+)" should retain the debugger failure evidence'))
def consumer_debug_mcp_messages_retain_failure(relative_path: str, consumer: ConsumerProject) -> None:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    assert artifact_path.is_file(), f"Messages artifact was not written: {artifact_path}"
    artifact_text = artifact_path.read_text(encoding="utf-8")
    assert artifact_text.strip(), f"Messages artifact is empty: {artifact_path}"
    assert "debug MCP failure sentinel" in artifact_text, artifact_text
    assert "testCaseFinished" in artifact_text, artifact_text


@given("the installed consumer has pytest-xdist installed")
def install_pytest_xdist_consumer(consumer: ConsumerProject) -> None:
    uv_executable = shutil.which("uv")
    assert uv_executable, "the installed-consumer contract requires uv to install pytest-xdist"
    install = subprocess.run(
        [uv_executable, "pip", "install", "--python", str(consumer.python), "pytest-xdist"],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert install.returncode == 0, f"could not install pytest-xdist:\n{install.stdout}\n{install.stderr}"


@given("the installed consumer exposes two concurrent xdist debugger failures")
def install_concurrent_xdist_debugger_failures(consumer: ConsumerProject) -> None:
    (consumer.path / "conftest.py").write_text(
        dedent(
            '''\
            import json
            import os
            import re
            import time
            from pathlib import Path

            import pytest
            from pytest_cuke import given, when

            @pytest.hookimpl(tryfirst=True)
            def pytest_cuke_message_batch(config, batch):
                del config
                messages = []
                for envelope in batch.get("envelopes", []):
                    if not isinstance(envelope, dict):
                        continue
                    payloads = [
                        (kind, payload)
                        for kind, payload in envelope.items()
                        if kind != "meta" and isinstance(payload, dict)
                    ]
                    if not payloads:
                        continue
                    kind, payload = payloads[0]
                    message = {"payload_kind": kind}
                    if kind == "stepDefinition":
                        message["step_definition_id"] = payload.get("id")
                    elif kind == "testCase":
                        test_steps = payload.get("testSteps", [])
                        message["test_case_step_definition_ids"] = [
                            test_step.get("stepDefinitionIds", [])
                            for test_step in test_steps
                            if isinstance(test_step, dict)
                        ]
                    messages.append(message)
                record = {
                    "worker_id": batch.get("worker_id"),
                    "sequence": batch.get("sequence"),
                    "messages": messages,
                }
                with Path("worker-message-batches.jsonl").open("a", encoding="utf-8") as trace:
                    trace.write(json.dumps(record, ensure_ascii=False) + "\\n")
                    trace.flush()

            def pytest_configure(config):
                config.addinivalue_line(
                    "markers",
                    "mcp-xdist-probe: marker for the Debug MCP xdist installed-consumer probe",
                )

            @given("the xdist worker registers its BDD failure context")
            def register_xdist_worker_context():
                worker_id = os.environ.get("PYTEST_XDIST_WORKER")
                if not worker_id:
                    raise RuntimeError("the concurrent Debug MCP probe requires a pytest-xdist worker")
                rendezvous = Path("xdist-worker-rendezvous")
                rendezvous.mkdir(exist_ok=True)
                (rendezvous / f"{worker_id}.json").write_text(
                    json.dumps({"worker_id": worker_id}), encoding="utf-8"
                )

            @when(re.compile(r'it reaches the shared xdist rendezvous and raises "(?P<message>[^"]+)"'))
            def raise_after_xdist_rendezvous(message):
                worker_id = os.environ.get("PYTEST_XDIST_WORKER")
                rendezvous = Path("xdist-worker-rendezvous")
                if message.endswith("bravo"):
                    gate = rendezvous / "release-bravo"
                    deadline = time.monotonic() + 90
                    while not gate.is_file() and time.monotonic() < deadline:
                        time.sleep(0.05)
                    if not gate.is_file():
                        raise RuntimeError("the xdist worker waiting for the discovery check was not released")
                else:
                    deadline = time.monotonic() + 30
                    while len(list(rendezvous.glob("*.json"))) < 2 and time.monotonic() < deadline:
                        time.sleep(0.05)
                    workers = sorted(path.stem for path in rendezvous.glob("*.json"))
                    if len(workers) != 2 or worker_id not in workers:
                        raise RuntimeError(
                            f"xdist workers did not rendezvous before the deadline: {workers!r}"
                        )
                raise RuntimeError(f"{message} on {worker_id}")

            @given(re.compile(r'the worker waits for fresh xdist discovery as "(?P<label>[^"]+)"'))
            def wait_for_fresh_xdist_discovery(label):
                worker_id = os.environ.get("PYTEST_XDIST_WORKER")
                if not worker_id:
                    raise RuntimeError("the fresh-session probe requires a pytest-xdist worker")
                rendezvous = Path("fresh-xdist-rendezvous")
                rendezvous.mkdir(exist_ok=True)
                (rendezvous / f"{worker_id}-{label}.json").write_text(
                    json.dumps({"worker_id": worker_id, "label": label}), encoding="utf-8"
                )
                release = rendezvous / "release"
                deadline = time.monotonic() + 60
                while not release.is_file() and time.monotonic() < deadline:
                    time.sleep(0.05)
                if not release.is_file():
                    raise RuntimeError("the fresh-session discovery check did not release the xdist worker")
            '''
        ),
        encoding="utf-8",
    )
    feature_directory = consumer.path / "features"
    feature_directory.mkdir(exist_ok=True)
    (feature_directory / "debug-mcp-xdist-probe-alpha.feature").write_text(
        dedent(
            '''\
            Feature: Concurrent Debug MCP worker inspection
              @mcp-xdist-probe
              Scenario Outline: The worker retains BDD context for <probe_id>
                Given the xdist worker registers its BDD failure context
                When it reaches the shared xdist rendezvous and raises "<message>"

                Examples:
                  | probe_id     | message                          |
                  | worker-alpha | debug MCP xdist failure alpha   |
                  | worker-charlie | debug MCP xdist failure charlie |
            '''
        ),
        encoding="utf-8",
    )
    (feature_directory / "debug-mcp-xdist-probe-bravo.feature").write_text(
        dedent(
            '''\
            Feature: Concurrent Debug MCP worker inspection
              @mcp-xdist-probe
              Scenario Outline: The worker retains BDD context for <probe_id>
                Given the xdist worker registers its BDD failure context
                When it reaches the shared xdist rendezvous and raises "<message>"

                Examples:
                  | probe_id     | message                         |
                  | worker-bravo | debug MCP xdist failure bravo   |
            '''
        ),
        encoding="utf-8",
    )
    fresh_feature_directory = consumer.path / "fresh-session-features"
    fresh_feature_directory.mkdir(exist_ok=True)
    (fresh_feature_directory / "fresh-session.feature").write_text(
        dedent(
            '''\
            Feature: Fresh Debug MCP xdist session
              Scenario Outline: Worker waits for current session discovery as <label>
                Given the worker waits for fresh xdist discovery as "<label>"

                Examples:
                  | label       |
                  | worker-alpha |
                  | worker-bravo |
            '''
        ),
        encoding="utf-8",
    )


@given("the installed consumer exposes an identical failure on each xdist worker")
def install_identical_xdist_debugger_failures(consumer: ConsumerProject) -> None:
    (consumer.path / "conftest.py").write_text(
        dedent(
            '''\
            import os
            import time
            from pathlib import Path

            from pytest_cuke import given, when

            @given("each xdist worker joins the shared failure rendezvous")
            def join_duplicate_failure_rendezvous():
                worker_id = os.environ.get("PYTEST_XDIST_WORKER")
                if not worker_id:
                    raise RuntimeError("the duplicate failure probe requires a pytest-xdist worker")
                rendezvous = Path("xdist-duplicate-rendezvous")
                rendezvous.mkdir(exist_ok=True)
                (rendezvous / f"{worker_id}.ready").write_text(worker_id, encoding="utf-8")
                deadline = time.monotonic() + 30
                while len(list(rendezvous.glob("*.ready"))) < 2 and time.monotonic() < deadline:
                    time.sleep(0.05)
                workers = sorted(path.stem for path in rendezvous.glob("*.ready"))
                if len(workers) != 2 or worker_id not in workers:
                    raise RuntimeError(f"xdist workers did not reach the same failure: {workers!r}")

            @when("each xdist worker raises the same held failure")
            def raise_duplicate_xdist_failure():
                raise RuntimeError("identical Debug MCP xdist failure")
            '''
        ),
        encoding="utf-8",
    )
    feature_directory = consumer.path / "features"
    feature_directory.mkdir(exist_ok=True)
    (feature_directory / "identical-worker-failure.feature").write_text(
        dedent(
            '''\
            Feature: Identical Debug MCP worker failures
              Scenario: The identical failure is held on each xdist worker
                Given each xdist worker joins the shared failure rendezvous
                When each xdist worker raises the same held failure
            '''
        ),
        encoding="utf-8",
    )


@when("I release the waiting xdist worker after observing one held failure")
def release_waiting_xdist_worker_after_observation(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the xdist MCP pytest process has not been started"
    index_path = _mcp_xdist_workers_path(consumer)
    deadline = time.monotonic() + 90
    latest_index: object = "xdist root discovery file has not been published"
    while time.monotonic() < deadline:
        try:
            latest_index = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            latest_index = repr(error)
        if isinstance(latest_index, dict):
            workers = latest_index.get("workers")
            if isinstance(workers, list) and len(workers) == 2:
                holding = [
                    worker
                    for worker in workers
                    if isinstance(worker, dict)
                    and worker.get("status") == "holding_failure"
                    and isinstance(worker.get("active_failure"), dict)
                ]
                waiting = [
                    worker
                    for worker in workers
                    if isinstance(worker, dict)
                    and worker.get("status") == "waiting"
                    and worker.get("active_failure") is None
                ]
                if (
                    latest_index.get("status") == "holding_failure"
                    and len(holding) == len(waiting) == 1
                ):
                    consumer._mcp_xdist_single_hold_index = latest_index
                    rendezvous = consumer.path / "xdist-worker-rendezvous"
                    rendezvous.mkdir(exist_ok=True)
                    (rendezvous / "release-bravo").write_text("release", encoding="utf-8")
                    return
        if process.poll() is not None:
            break
        time.sleep(0.05)
    output_path = consumer._mcp_pytest_output_path
    output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    raise AssertionError(
        f"xdist discovery never showed one held worker and one waiting worker ({latest_index!r});\n"
        f"pytest output:\n{output}"
    )


@then("xdist discovery should record one held worker while its peer waits")
def consumer_xdist_discovery_records_single_hold(consumer: ConsumerProject) -> None:
    index = getattr(consumer, "_mcp_xdist_single_hold_index", None)
    assert isinstance(index, dict), index
    assert index.get("status") == "holding_failure", index
    workers = index.get("workers")
    assert isinstance(workers, list) and len(workers) == 2, index
    holding = [
        worker
        for worker in workers
        if isinstance(worker, dict)
        and worker.get("status") == "holding_failure"
        and isinstance(worker.get("active_failure"), dict)
    ]
    waiting = [
        worker
        for worker in workers
        if isinstance(worker, dict)
        and worker.get("status") == "waiting"
        and worker.get("active_failure") is None
    ]
    assert len(holding) == len(waiting) == 1, workers
    for worker in [*holding, *waiting]:
        assert isinstance(worker.get("debugger_endpoint"), str), worker
        assert isinstance(worker.get("inspection_endpoint"), str), worker


def _mcp_xdist_workers_path(consumer: ConsumerProject) -> Path:
    return consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "workers.json"


def _read_mcp_xdist_worker_index(consumer: ConsumerProject, timeout: float = 50) -> dict[str, object]:
    index_path = _mcp_xdist_workers_path(consumer)
    process = consumer._mcp_pytest_process
    deadline = time.monotonic() + timeout
    latest_error = "xdist root discovery file has not been published"
    while time.monotonic() < deadline:
        if index_path.is_file():
            try:
                payload = json.loads(index_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    workers = payload.get("workers")
                    active = [
                        worker
                        for worker in workers
                        if isinstance(worker, dict) and isinstance(worker.get("active_failure"), dict)
                    ] if isinstance(workers, list) else []
                    if len(active) >= 2:
                        return payload
                    latest_error = f"xdist root discovery has fewer than two active failures: {payload!r}"
            except (OSError, json.JSONDecodeError) as error:
                latest_error = repr(error)
        if process.poll() is not None:
            break
        time.sleep(0.1)
    output_path = consumer._mcp_pytest_output_path
    output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    raise AssertionError(
        f"installed pytest did not advertise two active xdist worker failures ({latest_error}) before the watchdog;\n"
        f"pytest output:\n{output}"
    )


def _assert_mcp_xdist_worker_index(index: object) -> list[dict[str, object]]:
    assert isinstance(index, dict), index
    shared_session_id = index.get("session_id")
    assert isinstance(shared_session_id, str) and shared_session_id, index
    assert index.get("status") == "holding_failure", index
    assert "debugger_endpoint" not in index and "inspection_endpoint" not in index, index
    workers = index.get("workers")
    assert isinstance(workers, list) and len(workers) == 2, index
    assert all(isinstance(worker, dict) for worker in workers), workers
    typed_workers = [worker for worker in workers if isinstance(worker, dict)]
    worker_ids = [worker.get("worker_id") for worker in typed_workers]
    assert all(isinstance(worker_id, str) and worker_id for worker_id in worker_ids), typed_workers
    assert worker_ids == sorted(worker_ids) and len(set(worker_ids)) == 2, worker_ids
    session_ids = [worker.get("session_id") for worker in typed_workers]
    assert all(isinstance(session_id, str) and session_id for session_id in session_ids), typed_workers
    assert len(set(session_ids)) == 2, typed_workers
    identities: set[tuple[str, int]] = set()
    nodeids: set[str] = set()
    inspection_endpoints: set[str] = set()
    endpoints: set[str] = set()
    probe_ids: set[str] = set()
    for worker in typed_workers:
        assert worker.get("status") == "holding_failure", worker
        debugger_endpoint = worker.get("debugger_endpoint")
        inspection_endpoint = worker.get("inspection_endpoint")
        assert isinstance(debugger_endpoint, str), worker
        assert isinstance(inspection_endpoint, str), worker
        assert debugger_endpoint != inspection_endpoint, worker
        _mcp_endpoint_port(debugger_endpoint)
        _mcp_endpoint_port(inspection_endpoint)
        endpoints.update((debugger_endpoint, inspection_endpoint))
        inspection_endpoints.add(inspection_endpoint)

        failure = worker.get("active_failure")
        assert isinstance(failure, dict), worker
        sequence = failure.get("sequence")
        session_id = worker.get("session_id")
        assert isinstance(sequence, int) and sequence > 0, failure
        assert isinstance(session_id, str), worker
        identities.add((session_id, sequence))
        nodeid = failure.get("nodeid")
        assert isinstance(nodeid, str) and nodeid, failure
        nodeids.add(nodeid)
        assert failure.get("phase") == "call", failure
        assert failure.get("error_type") == "RuntimeError", failure
        assert isinstance(failure.get("error_message"), str) and failure["error_message"], failure

        context = failure.get("bdd_context")
        assert isinstance(context, dict), failure
        assert context.get("feature_name") == "Concurrent Debug MCP worker inspection", context
        assert context.get("step_keyword") == "When", context
        assert isinstance(context.get("scenario_name"), str) and "<probe_id>" in context["scenario_name"], context
        assert context.get("step_text") in {
            "it reaches the shared xdist rendezvous and raises \"debug MCP xdist failure alpha\"",
            "it reaches the shared xdist rendezvous and raises \"debug MCP xdist failure bravo\"",
        }, context
        feature_path = context.get("feature_path")
        assert isinstance(feature_path, str) and Path(feature_path).name in {
            "debug-mcp-xdist-probe-alpha.feature",
            "debug-mcp-xdist-probe-bravo.feature",
        }, context
        tags = context.get("tags")
        assert isinstance(tags, list) and "mcp-xdist-probe" in {str(tag).lstrip("@") for tag in tags}, context
        row = context.get("outline_row")
        assert isinstance(row, dict), context
        probe_id = row.get("probe_id")
        assert isinstance(probe_id, str) and probe_id in {"worker-alpha", "worker-bravo"}, context
        probe_ids.add(probe_id)
    assert len(identities) == len(nodeids) == len(inspection_endpoints) == 2, typed_workers
    assert len(endpoints) == 4, typed_workers
    assert probe_ids == {"worker-alpha", "worker-bravo"}, typed_workers
    return typed_workers


def _debug_mcp_xdist_worker_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        import time
        from pathlib import Path
        from urllib.parse import urlsplit

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def mark(stage_path, stage):
            Path(stage_path).write_text(stage + "\\n", encoding="utf-8")
            print(f"client stage: {stage}", flush=True)

        class BoundedClientSession(ClientSession):
            def __init__(self, read_stream, write_stream, stage_path, label):
                super().__init__(read_stream, write_stream)
                self._stage_path = stage_path
                self._label = label

            async def _bounded(self, operation, awaitable):
                stage = f"{self._label} {operation}"
                mark(self._stage_path, stage)
                try:
                    return await asyncio.wait_for(awaitable, timeout=10)
                except asyncio.TimeoutError as error:
                    raise TimeoutError(f"{stage} timed out after 10 seconds") from error

            async def initialize(self, *args, **kwargs):
                return await self._bounded("initialize", super().initialize(*args, **kwargs))

            async def list_tools(self, *args, **kwargs):
                return await self._bounded("list_tools", super().list_tools(*args, **kwargs))

            async def call_tool(self, *args, **kwargs):
                tool_name = args[0] if args else kwargs.get("name", "unknown")
                return await self._bounded(
                    f"call_tool {tool_name}",
                    super().call_tool(*args, **kwargs),
                )

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        def read_index(path):
            return json.loads(Path(path).read_text(encoding="utf-8"))

        def checked_endpoint(record, key):
            endpoint = record.get(key)
            assert isinstance(endpoint, str) and endpoint, (
                f"worker {record.get('worker_id')} has no {key}: {record!r}"
            )
            parsed = urlsplit(endpoint)
            assert parsed.scheme == "http" and parsed.hostname and parsed.port and parsed.path == "/mcp", (
                f"worker {record.get('worker_id')} has an invalid {key}: {endpoint!r}; record={record!r}"
            )
            return endpoint

        async def call_worker(record, tool_name, arguments, stage_path):
            endpoint = checked_endpoint(record, "inspection_endpoint")
            worker_id = record["worker_id"]
            mark(stage_path, f"{worker_id} inspection connect")
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with BoundedClientSession(
                    read_stream, write_stream, stage_path, f"{worker_id} inspection"
                ) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    names = {tool.name for tool in listed.tools}
                    assert {"inspect_failure", "heartbeat", "release_failure", "submit_artifact"} <= names, (
                        record,
                        names,
                    )
                    result = await session.call_tool(tool_name, arguments)
                    assert not getattr(result, "isError", False), result
                    return tool_payload(result)

        async def inspect_debugger_endpoint(record, stage_path):
            endpoint = checked_endpoint(record, "debugger_endpoint")
            mark(stage_path, f"{record['worker_id']} debugger connect")
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with BoundedClientSession(
                    read_stream, write_stream, stage_path, f"{record['worker_id']} debugger"
                ) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    names = sorted(tool.name for tool in listed.tools)
                    required = {"start_debug", "send_pdb_command"}
                    assert required <= set(names), (record, names)
                    return {"endpoint": endpoint, "tools": names}

        async def main(index_path, output_path, artifact_root, stage_path):
            mark(stage_path, "read xdist worker index")
            index = read_index(index_path)
            records = sorted(index["workers"], key=lambda worker: worker["worker_id"])
            assert len(records) == 2, index
            inspections = {}
            for record in records:
                inspected = await call_worker(record, "inspect_failure", {}, stage_path)
                failure = inspected.get("active_failure")
                assert isinstance(failure, dict), inspected
                assert inspected.get("session_id") == record.get("session_id"), (inspected, record)
                assert failure == record.get("active_failure"), (failure, record)
                debugger = await inspect_debugger_endpoint(record, stage_path)
                inspections[record["worker_id"]] = {
                    "endpoint": record["inspection_endpoint"],
                    "tools": ["inspect_failure", "heartbeat", "release_failure", "submit_artifact"],
                    "inspection": inspected,
                    "debugger": debugger,
                }

            target = next(
                record
                for record in records
                if record["active_failure"]["bdd_context"]["outline_row"]["probe_id"] == "worker-alpha"
            )
            remaining = next(record for record in records if record["worker_id"] != target["worker_id"])
            target_failure = target["active_failure"]
            remaining_failure = remaining["active_failure"]
            target_sequence = target_failure["sequence"]
            remaining_sequence = remaining_failure["sequence"]
            context = target_failure.get("bdd_context")
            assert isinstance(context, dict), target_failure
            submitted_artifact = {
                "artifact_id": f"{target['worker_id']}-failure-{target_sequence}-investigation",
                "nodeid": target_failure["nodeid"],
                "pytest_phase": target_failure["phase"],
                "status": "investigated",
                "summary": f"The held failure from {target['worker_id']} was investigated.",
                "inspected_commands": ["inspect_failure", "heartbeat"],
                "evidence": ["The MCP inspection endpoint returned this worker's held failure."],
                "suspected_cause": "The worker probe deliberately raises its configured sentinel exception.",
                "next_action": "Review the failure associated with this worker and sequence.",
                "bdd_metadata": {
                    "feature_path": context.get("feature_path"),
                    "feature_name": context.get("feature_name"),
                    "scenario_name": context.get("scenario_name"),
                    "step_keyword": context.get("step_keyword"),
                    "step_text": context.get("step_text"),
                    "tags": context.get("tags", []),
                    "example_row": context.get("outline_row", {}),
                },
            }
            artifact_submission = await call_worker(
                target,
                "submit_artifact",
                {
                    "session_id": target["session_id"],
                    "sequence": target_sequence,
                    "artifact": submitted_artifact,
                },
                stage_path,
            )
            assert artifact_submission.get("ok") is True, artifact_submission
            assert artifact_submission.get("artifact_id") == submitted_artifact["artifact_id"], artifact_submission
            root = Path(artifact_root).resolve()
            for path_key in ("json_path", "markdown_path"):
                path = Path(artifact_submission[path_key]).resolve()
                assert path.is_relative_to(root), (path, root, artifact_submission)
                assert path.is_file(), path
            saved = json.loads(Path(artifact_submission["json_path"]).read_text(encoding="utf-8"))
            assert saved.get("artifact_id") == submitted_artifact["artifact_id"], saved
            assert saved.get("nodeid") == target_failure.get("nodeid"), (saved, target_failure)
            assert saved.get("pytest_phase") == target_failure.get("phase"), (saved, target_failure)
            assert saved.get("bdd_metadata") == submitted_artifact["bdd_metadata"], (saved, submitted_artifact)

            first_heartbeat = await call_worker(
                target,
                "heartbeat",
                {"session_id": target["session_id"], "sequence": target_sequence},
                stage_path,
            )
            assert first_heartbeat.get("session_id") == target["session_id"], first_heartbeat
            assert first_heartbeat.get("sequence") == target_sequence, first_heartbeat
            assert first_heartbeat.get("lease_seconds", 0) >= 30, first_heartbeat
            remaining_after_heartbeat = await call_worker(remaining, "inspect_failure", {}, stage_path)
            assert remaining_after_heartbeat.get("session_id") == remaining["session_id"], remaining_after_heartbeat
            assert remaining_after_heartbeat.get("active_failure") == remaining_failure, remaining_after_heartbeat

            first_release = await call_worker(
                target,
                "release_failure",
                {"session_id": target["session_id"], "sequence": target_sequence},
                stage_path,
            )
            assert first_release.get("released") is True, first_release
            assert first_release.get("session_id") == target["session_id"], first_release
            assert first_release.get("sequence") == target_sequence, first_release
            assert first_release.get("artifact_status") == "written", first_release

            mark(stage_path, "wait for released worker follow-up failure")
            deadline = time.monotonic() + 15
            isolated_index = None
            while time.monotonic() < deadline:
                isolated_index = read_index(index_path)
                current = {
                    worker["worker_id"]: worker for worker in isolated_index.get("workers", [])
                }
                current_target = current.get(target["worker_id"])
                current_remaining = current.get(remaining["worker_id"])
                target_failure = current_target.get("active_failure") if isinstance(current_target, dict) else None
                target_sequence_after_release = (
                    target_failure.get("sequence") if isinstance(target_failure, dict) else None
                )
                target_released_or_advanced = target_failure is None or (
                    isinstance(target_sequence_after_release, int) and target_sequence_after_release > target_sequence
                )
                if (
                    isinstance(current_target, dict)
                    and target_released_or_advanced
                    and isinstance(current_remaining, dict)
                    and current_remaining.get("active_failure") == remaining_failure
                ):
                    break
                await asyncio.sleep(0.05)
            else:
                raise AssertionError(
                    f"releasing {target['worker_id']} did not leave its peer unchanged: {isolated_index!r}"
                )

            remaining_after_release = await call_worker(remaining, "inspect_failure", {}, stage_path)
            assert remaining_after_release.get("session_id") == remaining["session_id"], remaining_after_release
            assert remaining_after_release.get("active_failure") == remaining_failure, remaining_after_release

            await call_worker(
                remaining,
                "heartbeat",
                {"session_id": remaining["session_id"], "sequence": remaining_sequence},
                stage_path,
            )
            last_peer_heartbeat = time.monotonic()
            followup_deadline = time.monotonic() + 15
            followup_index = None
            followup_failure = None
            while time.monotonic() < followup_deadline:
                followup_index = read_index(index_path)
                current = {
                    worker["worker_id"]: worker for worker in followup_index.get("workers", [])
                }
                current_target = current.get(target["worker_id"])
                current_remaining = current.get(remaining["worker_id"])
                if isinstance(current_target, dict):
                    candidate = current_target.get("active_failure")
                    if isinstance(candidate, dict) and candidate.get("sequence", 0) > target_sequence:
                        followup_failure = candidate
                        break
                if isinstance(current_remaining, dict) and current_remaining.get("active_failure") != remaining_failure:
                    raise AssertionError(
                        f"the other worker changed before the follow-up failure started: {followup_index!r}"
                    )
                if time.monotonic() - last_peer_heartbeat >= 5:
                    await call_worker(
                        remaining,
                        "heartbeat",
                        {"session_id": remaining["session_id"], "sequence": remaining_sequence},
                        stage_path,
                    )
                    last_peer_heartbeat = time.monotonic()
                await asyncio.sleep(0.1)
            if not isinstance(followup_failure, dict):
                raise AssertionError(f"the released worker did not hold its next failure: {followup_index!r}")
            assert followup_failure.get("sequence", 0) > target_sequence, followup_failure
            assert followup_index["status"] == "holding_failure", followup_index
            followup_workers = {
                worker["worker_id"]: worker for worker in followup_index.get("workers", [])
            }
            assert followup_workers[remaining["worker_id"]].get("active_failure") == remaining_failure

            followup_sequence = followup_failure["sequence"]
            followup_heartbeat = await call_worker(
                target,
                "heartbeat",
                {"session_id": target["session_id"], "sequence": followup_sequence},
                stage_path,
            )
            assert followup_heartbeat.get("session_id") == target["session_id"], followup_heartbeat
            assert followup_heartbeat.get("sequence") == followup_sequence, followup_heartbeat
            assert followup_heartbeat.get("lease_seconds", 0) >= 30, followup_heartbeat

            mark(stage_path, "wait for follow-up worker lease expiry")
            last_peer_heartbeat = time.monotonic()
            timeout_deadline = time.monotonic() + 45
            timeout_index = None
            while time.monotonic() < timeout_deadline:
                timeout_index = read_index(index_path)
                current = {worker["worker_id"]: worker for worker in timeout_index.get("workers", [])}
                current_target = current.get(target["worker_id"])
                current_remaining = current.get(remaining["worker_id"])
                target_release = current_target.get("last_release") if isinstance(current_target, dict) else None
                if (
                    isinstance(current_target, dict)
                    and current_target.get("active_failure") is None
                    and isinstance(target_release, dict)
                    and target_release.get("sequence") == followup_failure.get("sequence")
                    and target_release.get("reason") == "lease_expired"
                    and isinstance(current_remaining, dict)
                    and current_remaining.get("active_failure") == remaining_failure
                    and timeout_index.get("status") == "holding_failure"
                ):
                    break
                if time.monotonic() - last_peer_heartbeat >= 5:
                    await call_worker(
                        remaining,
                        "heartbeat",
                        {"session_id": remaining["session_id"], "sequence": remaining_sequence},
                        stage_path,
                    )
                    last_peer_heartbeat = time.monotonic()
                await asyncio.sleep(0.1)
            else:
                raise AssertionError(f"one worker's lease did not expire independently: {timeout_index!r}")
            remaining_after_timeout = await call_worker(remaining, "inspect_failure", {}, stage_path)
            assert remaining_after_timeout.get("session_id") == remaining["session_id"], remaining_after_timeout
            assert remaining_after_timeout.get("active_failure") == remaining_failure, remaining_after_timeout

            second_release = await call_worker(
                remaining,
                "release_failure",
                {"session_id": remaining["session_id"], "sequence": remaining_sequence},
                stage_path,
            )
            assert second_release.get("released") is True, second_release
            assert second_release.get("session_id") == remaining["session_id"], second_release
            assert second_release.get("sequence") == remaining_sequence, second_release
            assert second_release.get("artifact_status") == "missing", second_release

            mark(stage_path, "write xdist worker observation")
            Path(output_path).write_text(
                json.dumps(
                    {
                        "root_session_id": index.get("session_id"),
                        "initial_index": index,
                        "inspections": inspections,
                        "target_worker_id": target["worker_id"],
                        "remaining_worker_id": remaining["worker_id"],
                        "submitted_artifact": submitted_artifact,
                        "artifact_submission": artifact_submission,
                        "first_heartbeat": first_heartbeat,
                        "remaining_after_heartbeat": remaining_after_heartbeat,
                        "first_release": first_release,
                        "isolated_index": isolated_index,
                        "remaining_after_release": remaining_after_release,
                        "followup_index": followup_index,
                        "followup_failure": followup_failure,
                        "followup_heartbeat": followup_heartbeat,
                        "timeout_index": timeout_index,
                        "remaining_after_timeout": remaining_after_timeout,
                        "second_release": second_release,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
        '''
    )


def _debug_mcp_xdist_duplicate_artifact_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path
        from urllib.parse import urlsplit

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def mark(stage_path, stage):
            Path(stage_path).write_text(stage + "\\n", encoding="utf-8")
            print(f"client stage: {stage}", flush=True)

        def checked_endpoint(record):
            endpoint = record.get("inspection_endpoint")
            assert isinstance(endpoint, str) and endpoint, (
                f"worker {record.get('worker_id')} has no inspection_endpoint: {record!r}"
            )
            parsed = urlsplit(endpoint)
            assert parsed.scheme == "http" and parsed.hostname and parsed.port and parsed.path == "/mcp", (
                f"worker {record.get('worker_id')} has an invalid inspection_endpoint: "
                f"{endpoint!r}; record={record!r}"
            )
            return endpoint

        class BoundedClientSession(ClientSession):
            def __init__(self, read_stream, write_stream, stage_path, label):
                super().__init__(read_stream, write_stream)
                self._stage_path = stage_path
                self._label = label

            async def _bounded(self, operation, awaitable):
                stage = f"{self._label} {operation}"
                mark(self._stage_path, stage)
                try:
                    return await asyncio.wait_for(awaitable, timeout=10)
                except asyncio.TimeoutError as error:
                    raise TimeoutError(f"{stage} timed out after 10 seconds") from error

            async def initialize(self, *args, **kwargs):
                return await self._bounded("initialize", super().initialize(*args, **kwargs))

            async def list_tools(self, *args, **kwargs):
                return await self._bounded("list_tools", super().list_tools(*args, **kwargs))

            async def call_tool(self, *args, **kwargs):
                tool_name = args[0] if args else kwargs.get("name", "unknown")
                return await self._bounded(
                    f"call_tool {tool_name}",
                    super().call_tool(*args, **kwargs),
                )

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        async def call_worker(record, tool_name, arguments, stage_path):
            endpoint = checked_endpoint(record)
            mark(stage_path, f"{record['worker_id']} inspection connect")
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with BoundedClientSession(
                    read_stream, write_stream, stage_path, f"{record['worker_id']} inspection"
                ) as session:
                    await session.initialize()
                    names = {tool.name for tool in (await session.list_tools()).tools}
                    required = {"inspect_failure", "submit_artifact", "release_failure"}
                    assert required <= names, (record, names)
                    result = await session.call_tool(tool_name, arguments)
                    return tool_payload(result)

        async def main(snapshot_path, output_path, stage_path):
            mark(stage_path, "read duplicate-worker index")
            index = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
            records = sorted(index.get("workers", []), key=lambda worker: worker["worker_id"])
            assert len(records) == 2, index
            observations = {}
            submitted_artifacts = {}
            submissions = {}
            releases = {}

            try:
                for record in records:
                    worker_id = record["worker_id"]
                    try:
                        inspection = await call_worker(record, "inspect_failure", {}, stage_path)
                        observations[worker_id] = inspection
                        failure = inspection.get("active_failure")
                        if not isinstance(failure, dict):
                            submissions[worker_id] = {"client_error": f"no active failure: {inspection!r}"}
                            continue
                        context = failure.get("bdd_context")
                        if not isinstance(context, dict):
                            submissions[worker_id] = {"client_error": f"no BDD context: {failure!r}"}
                            continue
                        artifact = {
                            "artifact_id": f"{worker_id}-identical-failure-investigation",
                            "nodeid": failure.get("nodeid"),
                            "pytest_phase": failure.get("phase"),
                            "status": "investigated",
                            "summary": f"The identical held failure on {worker_id} was investigated.",
                            "inspected_commands": ["inspect_failure"],
                            "evidence": ["An external MCP client inspected this worker's active failure."],
                            "suspected_cause": "Both xdist workers execute the same pytest item and nodeid.",
                            "next_action": "Keep this report attached to the matching worker failure.",
                            "bdd_metadata": {
                                "feature_path": context.get("feature_path"),
                                "feature_name": context.get("feature_name"),
                                "scenario_name": context.get("scenario_name"),
                                "step_keyword": context.get("step_keyword"),
                                "step_text": context.get("step_text"),
                                "tags": context.get("tags", []),
                                "example_row": context.get("outline_row") or {},
                            },
                        }
                        submitted_artifacts[worker_id] = artifact
                        failure_session_id = inspection.get("session_id")
                        sequence = failure.get("sequence")
                        try:
                            submissions[worker_id] = await call_worker(
                                record,
                                "submit_artifact",
                                {
                                    "session_id": failure_session_id,
                                    "sequence": sequence,
                                    "artifact": artifact,
                                },
                                stage_path,
                            )
                        except Exception as error:
                            submissions[worker_id] = {"client_error": repr(error)}
                    except Exception as error:
                        observations.setdefault(worker_id, {"client_error": repr(error)})
            finally:
                for record in records:
                    worker_id = record["worker_id"]
                    failure = record.get("active_failure")
                    try:
                        if not isinstance(failure, dict):
                            inspected = observations.get(worker_id, {}).get("active_failure")
                            failure = inspected if isinstance(inspected, dict) else None
                        if not isinstance(failure, dict):
                            releases[worker_id] = {"client_error": "no active failure sequence to release"}
                            continue
                        releases[worker_id] = await call_worker(
                            record,
                            "release_failure",
                            {
                                "session_id": record.get("session_id"),
                                "sequence": failure.get("sequence"),
                            },
                            stage_path,
                        )
                    except Exception as error:
                        releases[worker_id] = {"client_error": repr(error)}

            mark(stage_path, "write duplicate-worker observation")
            Path(output_path).write_text(
                json.dumps(
                    {
                        "root_session_id": index.get("session_id"),
                        "initial_index": index,
                        "observations": observations,
                        "submitted_artifacts": submitted_artifacts,
                        "submissions": submissions,
                        "releases": releases,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
        '''
    )


def _debug_mcp_xdist_fresh_worker_client_script() -> str:
    return dedent(
        '''\
        import asyncio
        import json
        import sys
        from pathlib import Path
        from urllib.parse import urlsplit

        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        def mark(stage_path, stage):
            Path(stage_path).write_text(stage + "\\n", encoding="utf-8")
            print(f"client stage: {stage}", flush=True)

        def checked_endpoint(record, key):
            endpoint = record.get(key)
            assert isinstance(endpoint, str) and endpoint, (
                f"worker {record.get('worker_id')} has no {key}: {record!r}"
            )
            parsed = urlsplit(endpoint)
            assert parsed.scheme == "http" and parsed.hostname and parsed.port and parsed.path == "/mcp", (
                f"worker {record.get('worker_id')} has an invalid {key}: {endpoint!r}; record={record!r}"
            )
            return endpoint

        class BoundedClientSession(ClientSession):
            def __init__(self, read_stream, write_stream, stage_path, label):
                super().__init__(read_stream, write_stream)
                self._stage_path = stage_path
                self._label = label

            async def _bounded(self, operation, awaitable):
                stage = f"{self._label} {operation}"
                mark(self._stage_path, stage)
                try:
                    return await asyncio.wait_for(awaitable, timeout=10)
                except asyncio.TimeoutError as error:
                    raise TimeoutError(f"{stage} timed out after 10 seconds") from error

            async def initialize(self, *args, **kwargs):
                return await self._bounded("initialize", super().initialize(*args, **kwargs))

            async def list_tools(self, *args, **kwargs):
                return await self._bounded("list_tools", super().list_tools(*args, **kwargs))

            async def call_tool(self, *args, **kwargs):
                tool_name = args[0] if args else kwargs.get("name", "unknown")
                return await self._bounded(
                    f"call_tool {tool_name}",
                    super().call_tool(*args, **kwargs),
                )

        def tool_payload(result):
            structured = getattr(result, "structuredContent", None)
            if isinstance(structured, dict):
                return structured
            for block in getattr(result, "content", []):
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        return payload
            raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")

        async def inspect_worker(record, stage_path):
            worker_id = record["worker_id"]
            endpoint = checked_endpoint(record, "inspection_endpoint")
            mark(stage_path, f"{worker_id} inspection connect")
            async with streamable_http_client(endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with BoundedClientSession(
                    read_stream, write_stream, stage_path, f"{worker_id} inspection"
                ) as session:
                    mark(stage_path, f"{worker_id} inspection initialize")
                    await session.initialize()
                    mark(stage_path, f"{worker_id} inspection list_tools")
                    names = {tool.name for tool in (await session.list_tools()).tools}
                    assert {"inspect_failure", "heartbeat", "release_failure"} <= names, (record, names)
                    mark(stage_path, f"{worker_id} inspection inspect_failure")
                    inspection = tool_payload(await session.call_tool("inspect_failure", {}))
                    assert inspection.get("session_id") == record.get("session_id"), (inspection, record)
                    assert inspection.get("active_failure") is None, inspection
                    mark(stage_path, f"{worker_id} inspection ClientSession context exit")
                mark(stage_path, f"{worker_id} inspection HTTP client context exit")

            debugger_endpoint = checked_endpoint(record, "debugger_endpoint")
            mark(stage_path, f"{worker_id} debugger connect")
            async with streamable_http_client(debugger_endpoint, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with BoundedClientSession(
                    read_stream, write_stream, stage_path, f"{worker_id} debugger"
                ) as session:
                    mark(stage_path, f"{worker_id} debugger initialize")
                    await session.initialize()
                    mark(stage_path, f"{worker_id} debugger list_tools")
                    debugger_tools = sorted(tool.name for tool in (await session.list_tools()).tools)
                    assert {"start_debug", "send_pdb_command"} <= set(debugger_tools), (record, debugger_tools)
                    mark(stage_path, f"{worker_id} debugger ClientSession context exit")
                mark(stage_path, f"{worker_id} debugger HTTP client context exit")

            return {
                "worker_id": record["worker_id"],
                "session_id": inspection["session_id"],
                "inspection_endpoint": endpoint,
                "active_failure": inspection.get("active_failure"),
                "debugger_endpoint": debugger_endpoint,
                "debugger_tools": debugger_tools,
            }

        async def main(index_path, output_path, stage_path):
            mark(stage_path, "read fresh worker index")
            index = json.loads(Path(index_path).read_text(encoding="utf-8"))
            workers = sorted(index.get("workers", []), key=lambda worker: worker["worker_id"])
            assert len(workers) == 2, index
            observations = [await inspect_worker(record, stage_path) for record in workers]
            mark(stage_path, "write fresh worker observation")
            Path(output_path).write_text(
                json.dumps({"session_id": index.get("session_id"), "workers": observations}, indent=2),
                encoding="utf-8",
            )

        asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
        '''
    )


@when("external MCP clients inspect both advertised xdist worker endpoints, heartbeat, and release them independently")
def run_external_mcp_xdist_worker_clients(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the xdist MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    index_path = _mcp_xdist_workers_path(consumer)
    client_path = consumer.path / "debug-mcp-xdist-worker-client.py"
    result_path = consumer.path / "debug-mcp-xdist-worker-client-result.json"
    stage_path = consumer.path / "debug-mcp-xdist-worker-client-stage.txt"
    log_path = consumer.path / "debug-mcp-xdist-worker-client.log"
    client_result: subprocess.CompletedProcess[str] | None = None
    try:
        initial_index = _read_mcp_xdist_worker_index(consumer)
        initial_workers = _assert_mcp_xdist_worker_index(initial_index)
        consumer._mcp_xdist_initial_index = initial_index
        consumer._mcp_xdist_initial_workers = initial_workers
        client_path.write_text(_debug_mcp_xdist_worker_client_script(), encoding="utf-8")
        stage_path.unlink(missing_ok=True)
        artifact_root = _consumer_artifact_path("xdist-artifacts", consumer)
        client_result = _run_debug_mcp_external_client(
            consumer,
            [
                str(consumer.python),
                str(client_path),
                str(index_path),
                str(result_path),
                str(artifact_root),
                str(stage_path),
            ],
            client_name="xdist worker MCP clients",
            timeout=90,
            stage_path=stage_path,
            log_path=log_path,
        )
        consumer._mcp_xdist_client_result = client_result
        assert client_result.returncode == 0, (
            f"external xdist MCP clients failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        assert result_path.is_file(), f"xdist MCP client did not write its observation: {client_result.stdout}"
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert isinstance(observation, dict), observation
        consumer._mcp_xdist_client_observation = observation

        try:
            return_code = process.wait(timeout=30)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("installed pytest did not finish after both xdist worker failures were released") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"releasing both xdist failures changed pytest's failed outcomes to success:\n{output}"
        final_index_path = _mcp_xdist_workers_path(consumer)
        assert final_index_path.is_file(), f"pytest did not retain the final xdist worker index: {final_index_path}"
        consumer._mcp_xdist_final_index = json.loads(final_index_path.read_text(encoding="utf-8"))
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if client_result is not None:
            consumer._mcp_xdist_client_result = client_result


@when("an external MCP client submits a structured artifact to each identical worker failure")
def submit_artifacts_to_identical_xdist_failures(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the duplicate xdist MCP pytest process has not been started"
    command = consumer._mcp_pytest_command
    output_path = consumer._mcp_pytest_output_path
    index_path = _mcp_xdist_workers_path(consumer)
    client_path = consumer.path / "debug-mcp-xdist-duplicate-artifact-client.py"
    result_path = consumer.path / "debug-mcp-xdist-duplicate-artifact-client-result.json"
    stage_path = consumer.path / "debug-mcp-xdist-duplicate-artifact-client-stage.txt"
    log_path = consumer.path / "debug-mcp-xdist-duplicate-artifact-client.log"
    client_result: subprocess.CompletedProcess[str] | None = None
    try:
        deadline = time.monotonic() + 60
        initial_index: dict[str, object] | None = None
        latest: object = "xdist root discovery has not been published"
        while time.monotonic() < deadline:
            try:
                payload = json.loads(index_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                latest = repr(error)
                payload = None
            if isinstance(payload, dict):
                latest = payload
                records = payload.get("workers")
                active = [
                    record
                    for record in records
                    if isinstance(record, dict)
                    and record.get("status") == "holding_failure"
                    and isinstance(record.get("active_failure"), dict)
                    and isinstance(record.get("debugger_endpoint"), str)
                    and bool(record["debugger_endpoint"])
                    and isinstance(record.get("inspection_endpoint"), str)
                    and bool(record["inspection_endpoint"])
                ] if isinstance(records, list) else []
                if (
                    payload.get("status") == "holding_failure"
                    and isinstance(records, list)
                    and len(records) == 2
                    and len(active) == 2
                ):
                    initial_index = payload
                    break
            if process.poll() is not None:
                break
            time.sleep(0.05)
        assert isinstance(initial_index, dict), (
            f"xdist did not hold both identical worker failures ({latest!r}) before the watchdog;\n"
            f"pytest output:\n{output_path.read_text(encoding='utf-8') if output_path.exists() else ''}"
        )
        records = initial_index.get("workers")
        assert isinstance(records, list) and len(records) == 2, initial_index
        workers = sorted(
            (record for record in records if isinstance(record, dict)),
            key=lambda record: record.get("worker_id", ""),
        )
        assert len(workers) == 2, initial_index
        for worker in workers:
            debugger_endpoint = worker.get("debugger_endpoint")
            inspection_endpoint = worker.get("inspection_endpoint")
            assert isinstance(debugger_endpoint, str) and debugger_endpoint, worker
            assert isinstance(inspection_endpoint, str) and inspection_endpoint, worker
            _mcp_endpoint_port(debugger_endpoint)
            _mcp_endpoint_port(inspection_endpoint)
        failures = [record.get("active_failure") for record in workers]
        assert all(isinstance(failure, dict) for failure in failures), initial_index
        consumer._mcp_xdist_duplicate_initial_index = initial_index
        consumer._mcp_xdist_duplicate_initial_workers = workers

        client_path.write_text(_debug_mcp_xdist_duplicate_artifact_client_script(), encoding="utf-8")
        snapshot_path = consumer.path / "debug-mcp-xdist-duplicate-artifact-index.json"
        snapshot_path.write_text(json.dumps(initial_index, ensure_ascii=False, indent=2), encoding="utf-8")
        stage_path.unlink(missing_ok=True)
        client_result = _run_debug_mcp_external_client(
            consumer,
            [str(consumer.python), str(client_path), str(snapshot_path), str(result_path), str(stage_path)],
            client_name="duplicate-worker MCP client",
            timeout=60,
            stage_path=stage_path,
            log_path=log_path,
        )
        consumer._mcp_xdist_duplicate_client_result = client_result
        assert client_result.returncode == 0, (
            f"external duplicate-worker MCP client failed ({client_result.returncode}):\n"
            f"{client_result.stdout}\n{client_result.stderr}"
        )
        assert result_path.is_file(), f"duplicate-worker client did not write its observation: {client_result.stdout}"
        observation = json.loads(result_path.read_text(encoding="utf-8"))
        assert isinstance(observation, dict), observation
        consumer._mcp_xdist_duplicate_client_observation = observation

        try:
            return_code = process.wait(timeout=30)
        except subprocess.TimeoutExpired as error:
            raise AssertionError("identical xdist failures did not finish after both worker releases") from error
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        consumer.pytest_result = subprocess.CompletedProcess(command, return_code, output, "")
        assert return_code != 0, f"releasing the identical xdist failures changed pytest's failed outcome to success:\n{output}"
        final_index_path = _mcp_xdist_workers_path(consumer)
        assert final_index_path.is_file(), f"pytest did not retain the final xdist worker index: {final_index_path}"
        consumer._mcp_xdist_duplicate_final_index = json.loads(final_index_path.read_text(encoding="utf-8"))
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if client_result is not None:
            consumer._mcp_xdist_duplicate_client_result = client_result


@then("both workers should retain the same failure identity in distinct sessions")
def consumer_xdist_duplicate_failures_have_distinct_sessions(consumer: ConsumerProject) -> None:
    initial_index = getattr(consumer, "_mcp_xdist_duplicate_initial_index", None)
    observation = getattr(consumer, "_mcp_xdist_duplicate_client_observation", None)
    assert isinstance(initial_index, dict), initial_index
    assert isinstance(observation, dict), observation
    records = initial_index.get("workers")
    assert isinstance(records, list) and len(records) == 2, initial_index
    workers = sorted(
        (record for record in records if isinstance(record, dict)),
        key=lambda record: record.get("worker_id", ""),
    )
    assert len(workers) == 2, initial_index
    assert workers[0].get("worker_id") != workers[1].get("worker_id"), workers
    assert workers[0].get("session_id") != workers[1].get("session_id"), workers
    failures = [worker.get("active_failure") for worker in workers]
    assert all(isinstance(failure, dict) for failure in failures), workers
    first, second = failures
    for field in ("nodeid", "phase", "sequence", "bdd_context"):
        assert first.get(field) == second.get(field), (field, first, second)
    assert first.get("phase") == "call", failures
    assert first.get("error_message") == second.get("error_message") == "identical Debug MCP xdist failure", failures
    context = first.get("bdd_context")
    assert isinstance(context, dict), first
    assert context.get("feature_name") == "Identical Debug MCP worker failures", context
    assert context.get("scenario_name") == "The identical failure is held on each xdist worker", context

    inspected = observation.get("observations")
    assert isinstance(inspected, dict), observation
    for worker in workers:
        worker_id = worker.get("worker_id")
        response = inspected.get(worker_id)
        assert isinstance(response, dict), (worker_id, inspected)
        assert response.get("session_id") == worker.get("session_id"), (response, worker)
        assert response.get("active_failure") == worker.get("active_failure"), (response, worker)


@then("both duplicate worker services should close while preserving the pytest failure")
def consumer_xdist_duplicate_workers_close_after_failure(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    initial_index = getattr(consumer, "_mcp_xdist_duplicate_initial_index", None)
    final_index = getattr(consumer, "_mcp_xdist_duplicate_final_index", None)
    observation = getattr(consumer, "_mcp_xdist_duplicate_client_observation", None)
    assert result is not None and result.returncode != 0, result
    assert isinstance(initial_index, dict), initial_index
    assert isinstance(final_index, dict), final_index
    assert isinstance(observation, dict), observation
    assert final_index.get("session_id") == initial_index.get("session_id"), (final_index, initial_index)
    assert final_index.get("status") == "closed", final_index
    initial_workers = initial_index.get("workers")
    final_workers = final_index.get("workers")
    assert isinstance(initial_workers, list) and len(initial_workers) == 2, initial_index
    assert isinstance(final_workers, list) and len(final_workers) == 2, final_index
    initial_by_id = {worker.get("worker_id"): worker for worker in initial_workers if isinstance(worker, dict)}
    final_by_id = {worker.get("worker_id"): worker for worker in final_workers if isinstance(worker, dict)}
    assert set(initial_by_id) == set(final_by_id), (initial_by_id, final_by_id)
    releases = observation.get("releases")
    assert isinstance(releases, dict), observation
    for worker_id in initial_by_id:
        final = final_by_id[worker_id]
        assert final.get("status") == "closed", final
        assert final.get("active_failure") is None, final
        assert final.get("debugger_endpoint") is None, final
        assert final.get("inspection_endpoint") is None, final
        release = releases.get(worker_id)
        assert isinstance(release, dict) and release.get("released") is True, (worker_id, release)
        worker_record_path = (
            consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "workers" / f"{worker_id}.json"
        )
        assert worker_record_path.is_file(), worker_record_path
        worker_record = json.loads(worker_record_path.read_text(encoding="utf-8"))
        assert worker_record.get("status") == "closed", worker_record
        assert worker_record.get("active_failure") is None, worker_record


@then("identical worker failures should produce separate artifact paths and written release status")
def consumer_xdist_duplicate_artifacts_keep_worker_paths(consumer: ConsumerProject) -> None:
    initial_index = getattr(consumer, "_mcp_xdist_duplicate_initial_index", None)
    observation = getattr(consumer, "_mcp_xdist_duplicate_client_observation", None)
    assert isinstance(initial_index, dict), initial_index
    assert isinstance(observation, dict), observation
    initial_workers = initial_index.get("workers")
    assert isinstance(initial_workers, list) and len(initial_workers) == 2, initial_index
    workers = {worker.get("worker_id"): worker for worker in initial_workers if isinstance(worker, dict)}
    assert len(workers) == 2, initial_workers
    submissions = observation.get("submissions")
    submitted_artifacts = observation.get("submitted_artifacts")
    releases = observation.get("releases")
    assert isinstance(submissions, dict) and isinstance(submitted_artifacts, dict), observation
    assert isinstance(releases, dict), observation
    assert set(submissions) == set(submitted_artifacts) == set(releases) == set(workers), observation

    root = consumer.path / "collision-artifacts"
    json_paths: list[Path] = []
    markdown_paths: list[Path] = []
    for worker_id, worker in workers.items():
        failure = worker.get("active_failure")
        submitted = submitted_artifacts[worker_id]
        submission = submissions[worker_id]
        release = releases[worker_id]
        assert isinstance(failure, dict), worker
        assert isinstance(submitted, dict), submitted
        assert isinstance(submission, dict), submission
        assert submission.get("ok") is True, (worker_id, submission)
        assert submission.get("artifact_id") == submitted.get("artifact_id"), (submission, submitted)
        assert submitted.get("nodeid") == failure.get("nodeid"), (submitted, failure)
        assert submitted.get("pytest_phase") == failure.get("phase") == "call", (submitted, failure)
        assert submitted.get("bdd_metadata") == _expected_debug_mcp_artifact_bdd_metadata(failure), (
            submitted,
            failure,
        )
        json_path = _resolve_debug_mcp_artifact_path(submission.get("json_path"), root)
        markdown_path = _resolve_debug_mcp_artifact_path(submission.get("markdown_path"), root)
        assert json_path.is_file(), json_path
        assert markdown_path.is_file(), markdown_path
        assert json_path.parent.name == worker.get("session_id"), (json_path, worker)
        assert json_path.parent.parent.name == worker_id, (json_path, worker_id)
        assert json_path.suffix == ".json" and markdown_path.suffix == ".md", (json_path, markdown_path)
        assert json_path.stem == markdown_path.stem, (json_path, markdown_path)
        document = json.loads(json_path.read_text(encoding="utf-8"))
        assert document.get("artifact_id") == submitted.get("artifact_id"), document
        assert document.get("nodeid") == failure.get("nodeid"), (document, failure)
        assert document.get("pytest_phase") == failure.get("phase"), (document, failure)
        assert document.get("bdd_metadata") == submitted.get("bdd_metadata"), (document, submitted)
        assert submitted.get("artifact_id") in markdown_path.read_text(encoding="utf-8"), markdown_path
        assert release.get("released") is True, release
        assert release.get("artifact_status") == "written", (worker_id, release)
        json_paths.append(json_path)
        markdown_paths.append(markdown_path)

    assert len(set(json_paths)) == len(set(markdown_paths)) == 2, (json_paths, markdown_paths)
    assert sorted(root.rglob("*.json")) == sorted(json_paths), list(root.rglob("*"))
    assert sorted(root.rglob("*.md")) == sorted(markdown_paths), list(root.rglob("*"))


@then("xdist root discovery should show both distinct worker failures")
def consumer_xdist_discovery_shows_distinct_worker_failures(consumer: ConsumerProject) -> None:
    index = getattr(consumer, "_mcp_xdist_initial_index", None)
    records = _assert_mcp_xdist_worker_index(index)
    observation = getattr(consumer, "_mcp_xdist_client_observation", None)
    assert isinstance(observation, dict), observation
    inspections = observation.get("inspections")
    assert isinstance(inspections, dict), observation
    assert set(inspections) == {record["worker_id"] for record in records}, inspections
    for record in records:
        worker_id = record["worker_id"]
        result = inspections.get(worker_id)
        assert isinstance(result, dict), (worker_id, inspections)
        assert result.get("endpoint") == record.get("inspection_endpoint"), result
        assert {"inspect_failure", "heartbeat", "release_failure", "submit_artifact"} <= set(
            result.get("tools", [])
        ), result
        debugger = result.get("debugger")
        assert isinstance(debugger, dict), result
        assert debugger.get("endpoint") == record.get("debugger_endpoint"), (debugger, record)
        assert {"start_debug", "send_pdb_command"} <= set(debugger.get("tools", [])), debugger
        inspection = result.get("inspection")
        assert isinstance(inspection, dict), result
        assert inspection.get("session_id") == record.get("session_id"), (inspection, record)
        assert inspection.get("status") == record.get("status"), (inspection, record)
        assert inspection.get("active_failure") == record.get("active_failure"), (inspection, record)


@then("heartbeating, releasing, and timing out one worker should leave its peer isolated")
def consumer_xdist_release_isolated_to_one_worker(consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_xdist_client_observation", None)
    initial_index = getattr(consumer, "_mcp_xdist_initial_index", None)
    assert isinstance(observation, dict), observation
    initial_workers = _assert_mcp_xdist_worker_index(initial_index)
    target_worker_id = observation.get("target_worker_id")
    remaining_worker_id = observation.get("remaining_worker_id")
    assert target_worker_id != remaining_worker_id, observation
    workers_by_id = {worker["worker_id"]: worker for worker in initial_workers}
    target = workers_by_id.get(target_worker_id)
    remaining = workers_by_id.get(remaining_worker_id)
    assert isinstance(target, dict) and isinstance(remaining, dict), observation

    first_release = observation.get("first_release")
    first_heartbeat = observation.get("first_heartbeat")
    second_release = observation.get("second_release")
    remaining_after_heartbeat = observation.get("remaining_after_heartbeat")
    isolated_index = observation.get("isolated_index")
    remaining_after_release = observation.get("remaining_after_release")
    followup_index = observation.get("followup_index")
    followup_failure = observation.get("followup_failure")
    timeout_index = observation.get("timeout_index")
    remaining_after_timeout = observation.get("remaining_after_timeout")
    assert isinstance(first_heartbeat, dict), observation
    assert isinstance(remaining_after_heartbeat, dict), observation
    assert isinstance(first_release, dict) and isinstance(second_release, dict), observation
    assert isinstance(isolated_index, dict) and isinstance(remaining_after_release, dict), observation
    assert isinstance(followup_index, dict) and isinstance(followup_failure, dict), observation
    assert isinstance(timeout_index, dict) and isinstance(remaining_after_timeout, dict), observation
    target_failure = target.get("active_failure")
    remaining_failure = remaining.get("active_failure")
    assert isinstance(target_failure, dict) and isinstance(remaining_failure, dict), observation
    assert first_heartbeat.get("session_id") == target.get("session_id"), first_heartbeat
    assert first_heartbeat.get("sequence") == target_failure.get("sequence"), first_heartbeat
    assert first_heartbeat.get("lease_seconds", 0) > 0, first_heartbeat
    assert remaining_after_heartbeat.get("session_id") == remaining.get("session_id"), remaining_after_heartbeat
    assert remaining_after_heartbeat.get("active_failure") == remaining_failure, remaining_after_heartbeat
    assert first_release.get("released") is True, first_release
    assert first_release.get("session_id") == target.get("session_id"), first_release
    assert first_release.get("sequence") == target_failure.get("sequence"), first_release
    assert first_release.get("artifact_status") == "written", first_release
    assert second_release.get("released") is True, second_release
    assert second_release.get("session_id") == remaining.get("session_id"), second_release
    assert second_release.get("sequence") == remaining_failure.get("sequence"), second_release
    assert second_release.get("artifact_status") == "missing", second_release
    isolated_workers = isolated_index.get("workers")
    assert isinstance(isolated_workers, list), isolated_index
    isolated_by_id = {worker.get("worker_id"): worker for worker in isolated_workers if isinstance(worker, dict)}
    target_after = isolated_by_id.get(target_worker_id)
    remaining_after = isolated_by_id.get(remaining_worker_id)
    assert isinstance(target_after, dict) and isinstance(remaining_after, dict), isolated_index
    target_failure_after_release = target_after.get("active_failure")
    assert target_failure_after_release is None or (
        isinstance(target_failure_after_release, dict)
        and isinstance(target_failure_after_release.get("sequence"), int)
        and target_failure_after_release["sequence"] > target_failure["sequence"]
    ), target_after
    if target_failure_after_release is None:
        assert target_after.get("last_release", {}).get("sequence") == target_failure.get("sequence"), target_after
    assert remaining_after.get("active_failure") == remaining_failure, (remaining_after, remaining_failure)
    assert remaining_after_release.get("session_id") == remaining.get("session_id"), remaining_after_release
    assert remaining_after_release.get("active_failure") == remaining_failure, remaining_after_release

    followup_workers = {
        worker.get("worker_id"): worker
        for worker in followup_index.get("workers", [])
        if isinstance(worker, dict)
    }
    target_followup = followup_workers.get(target_worker_id)
    remaining_followup = followup_workers.get(remaining_worker_id)
    assert isinstance(target_followup, dict) and isinstance(remaining_followup, dict), followup_index
    assert followup_index.get("status") == "holding_failure", followup_index
    assert target_followup.get("session_id") == target.get("session_id"), target_followup
    assert followup_failure.get("sequence", 0) > target_failure.get("sequence", 0), followup_failure
    assert target_followup.get("active_failure") == followup_failure, target_followup
    assert remaining_followup.get("active_failure") == remaining_failure, remaining_followup

    timeout_workers = {
        worker.get("worker_id"): worker
        for worker in timeout_index.get("workers", [])
        if isinstance(worker, dict)
    }
    target_after_timeout = timeout_workers.get(target_worker_id)
    remaining_after_timeout_index = timeout_workers.get(remaining_worker_id)
    assert isinstance(target_after_timeout, dict), timeout_index
    assert isinstance(remaining_after_timeout_index, dict), timeout_index
    assert timeout_index.get("status") == "holding_failure", timeout_index
    assert target_after_timeout.get("active_failure") is None, target_after_timeout
    timeout_release = target_after_timeout.get("last_release")
    assert isinstance(timeout_release, dict), target_after_timeout
    assert timeout_release.get("sequence") == followup_failure.get("sequence"), timeout_release
    assert timeout_release.get("reason") == "lease_expired", timeout_release
    assert remaining_after_timeout_index.get("active_failure") == remaining_failure
    assert remaining_after_timeout.get("session_id") == remaining.get("session_id"), remaining_after_timeout
    assert remaining_after_timeout.get("active_failure") == remaining_failure, remaining_after_timeout


@then("the written worker artifact should match its failure while the peer release remains missing")
def consumer_xdist_artifact_is_bound_to_one_worker(consumer: ConsumerProject) -> None:
    observation = getattr(consumer, "_mcp_xdist_client_observation", None)
    initial_index = getattr(consumer, "_mcp_xdist_initial_index", None)
    assert isinstance(observation, dict), observation
    workers = _assert_mcp_xdist_worker_index(initial_index)
    workers_by_id = {worker["worker_id"]: worker for worker in workers}
    target_worker_id = observation.get("target_worker_id")
    remaining_worker_id = observation.get("remaining_worker_id")
    target = workers_by_id.get(target_worker_id)
    remaining = workers_by_id.get(remaining_worker_id)
    assert isinstance(target, dict) and isinstance(remaining, dict), observation
    target_failure = target.get("active_failure")
    remaining_failure = remaining.get("active_failure")
    assert isinstance(target_failure, dict) and isinstance(remaining_failure, dict), observation

    submitted = observation.get("submitted_artifact")
    submission = observation.get("artifact_submission")
    assert isinstance(submitted, dict) and isinstance(submission, dict), observation
    assert submission.get("ok") is True, submission
    assert submission.get("artifact_id") == submitted.get("artifact_id"), submission
    assert submitted.get("nodeid") == target_failure.get("nodeid"), (submitted, target_failure)
    assert submitted.get("pytest_phase") == target_failure.get("phase") == "call", (submitted, target_failure)
    assert submitted.get("bdd_metadata", {}).get("example_row") == target_failure.get("bdd_context", {}).get(
        "outline_row"
    ), (submitted, target_failure)

    root = consumer.path / "xdist-artifacts"
    json_path = _resolve_debug_mcp_artifact_path(submission.get("json_path"), root)
    markdown_path = _resolve_debug_mcp_artifact_path(submission.get("markdown_path"), root)
    assert json_path.is_file(), json_path
    assert markdown_path.is_file(), markdown_path
    assert json_path.suffix == ".json" and markdown_path.suffix == ".md", (json_path, markdown_path)
    assert json_path.stem == markdown_path.stem, (json_path, markdown_path)
    assert json_path.name.startswith(f"failure-{target_failure['sequence']:04d}-"), (json_path, target_failure)
    assert json_path.parent.name == target.get("session_id"), (json_path, target)
    assert json_path.parent.parent.name == target.get("worker_id"), (json_path, target)
    assert sorted(root.rglob("*.json")) == [json_path], list(root.rglob("*"))
    assert sorted(root.rglob("*.md")) == [markdown_path], list(root.rglob("*"))

    document = json.loads(json_path.read_text(encoding="utf-8"))
    assert document.get("artifact_id") == submitted.get("artifact_id"), document
    assert document.get("nodeid") == target_failure.get("nodeid"), (document, target_failure)
    assert document.get("pytest_phase") == target_failure.get("phase"), (document, target_failure)
    assert document.get("bdd_metadata") == submitted.get("bdd_metadata"), (document, submitted)
    context = target_failure.get("bdd_context")
    assert isinstance(context, dict), target_failure
    assert document["bdd_metadata"].get("scenario_name") == context.get("scenario_name"), (document, context)
    assert document["bdd_metadata"].get("example_row") == context.get("outline_row"), (document, context)
    assert submitted["artifact_id"] in markdown_path.read_text(encoding="utf-8")

    assert observation.get("first_release", {}).get("artifact_status") == "written", observation
    assert observation.get("second_release", {}).get("artifact_status") == "missing", observation
    assert target_failure.get("sequence") == remaining_failure.get("sequence") == 1, observation
    assert target.get("session_id") != remaining.get("session_id"), observation


@then("pytest should report both initial failures and the third follow-up failure, then close every worker service")
def consumer_xdist_keeps_failures_and_closes_worker_services(consumer: ConsumerProject) -> None:
    result = consumer.pytest_result
    assert result is not None and result.returncode != 0, result
    report_path = consumer.path / "report.json"
    worker_index_path = _mcp_xdist_workers_path(consumer)
    worker_directory = worker_index_path.parent / "workers"
    worker_record_paths = sorted(str(path.relative_to(consumer.path)) for path in worker_directory.glob("*.json"))
    assert report_path.is_file(), (
        f"Cucumber JSON report was not written: {report_path}\n"
        f"child pytest exit code: {result.returncode}\n"
        f"child pytest combined stdout/stderr:\n{result.stdout}\n"
        f"xdist worker index: {worker_index_path} (exists={worker_index_path.is_file()})\n"
        f"xdist worker records: {worker_record_paths}"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    scenarios = [
        scenario
        for feature in report
        if feature.get("name") == "Concurrent Debug MCP worker inspection"
        for scenario in feature.get("elements", [])
        if isinstance(scenario.get("name"), str) and scenario["name"].startswith("The worker retains BDD context")
    ]
    assert len(scenarios) == 3, scenarios
    messages = set()
    for scenario in scenarios:
        statuses = [step.get("result", {}).get("status") for step in scenario.get("steps", [])]
        assert statuses == ["passed", "failed"], (scenario, statuses)
        scenario_text = json.dumps(scenario, ensure_ascii=False)
        for message in (
            "debug MCP xdist failure alpha",
            "debug MCP xdist failure bravo",
            "debug MCP xdist failure charlie",
        ):
            if message in scenario_text:
                messages.add(message)
    assert messages == {
        "debug MCP xdist failure alpha",
        "debug MCP xdist failure bravo",
        "debug MCP xdist failure charlie",
    }, scenarios

    initial_index = getattr(consumer, "_mcp_xdist_initial_index", None)
    initial_workers = _assert_mcp_xdist_worker_index(initial_index)
    observation = getattr(consumer, "_mcp_xdist_client_observation", None)
    assert isinstance(observation, dict), observation
    timed_out_worker_id = observation.get("target_worker_id")
    timeout_failure = observation.get("followup_failure")
    assert isinstance(timeout_failure, dict), observation
    final_index = getattr(consumer, "_mcp_xdist_final_index", None)
    assert isinstance(final_index, dict), final_index
    assert final_index.get("status") == "closed", final_index
    assert final_index.get("session_id") == initial_index.get("session_id"), (final_index, initial_index)
    final_workers = final_index.get("workers")
    assert isinstance(final_workers, list) and len(final_workers) == 2, final_index
    final_by_id = {worker.get("worker_id"): worker for worker in final_workers if isinstance(worker, dict)}
    assert set(final_by_id) == {worker.get("worker_id") for worker in initial_workers}, final_index
    old_endpoints: list[str] = []
    for initial in initial_workers:
        worker_id = initial.get("worker_id")
        final = final_by_id.get(worker_id)
        assert isinstance(final, dict), (worker_id, final_index)
        assert final.get("status") == "closed", final
        assert final.get("active_failure") is None, final
        assert final.get("debugger_endpoint") is None, final
        assert final.get("inspection_endpoint") is None, final
        initial_failure = initial.get("active_failure")
        release = final.get("last_release")
        assert isinstance(initial_failure, dict) and isinstance(release, dict), (initial, final)
        assert release.get("session_id") == initial.get("session_id"), (initial, final)
        if worker_id == timed_out_worker_id:
            assert release.get("sequence") == timeout_failure.get("sequence"), (initial, final)
            assert release.get("reason") == "lease_expired", final
        else:
            assert release.get("sequence") == initial_failure.get("sequence"), (initial, final)
            assert release.get("reason") == "explicit", final
        debugger_endpoint = initial.get("debugger_endpoint")
        inspection_endpoint = initial.get("inspection_endpoint")
        assert isinstance(debugger_endpoint, str) and isinstance(inspection_endpoint, str), initial
        old_endpoints.extend((debugger_endpoint, inspection_endpoint))

        worker_record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "workers" / f"{worker_id}.json"
        assert worker_record_path.is_file(), f"worker discovery record was not retained: {worker_record_path}"
        worker_record = json.loads(worker_record_path.read_text(encoding="utf-8"))
        assert worker_record.get("worker_id") == worker_id, worker_record
        assert worker_record.get("status") == "closed", worker_record
        assert worker_record.get("active_failure") is None, worker_record
        assert worker_record.get("debugger_endpoint") is None, worker_record
        assert worker_record.get("inspection_endpoint") is None, worker_record

    import socket

    for endpoint in old_endpoints:
        host, port = _mcp_endpoint_port(endpoint)
        try:
            connection = socket.create_connection((host, port), timeout=0.25)
        except OSError:
            continue
        connection.close()
        raise AssertionError(f"xdist worker MCP endpoint {host}:{port} remained open after pytest finished")


@when("I release the fresh-session workers after observing current discovery")
def release_fresh_xdist_session_workers(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    assert isinstance(process, subprocess.Popen), "the second xdist pytest process has not been started"
    old_index = getattr(consumer, "_mcp_xdist_initial_index", None)
    old_workers = _assert_mcp_xdist_worker_index(old_index)
    assert isinstance(old_index, dict), old_index
    old_session_id = old_index.get("session_id")
    old_sessions = {worker["session_id"] for worker in old_workers}
    old_endpoints = {
        endpoint
        for worker in old_workers
        for endpoint in (worker.get("debugger_endpoint"), worker.get("inspection_endpoint"))
        if isinstance(endpoint, str)
    }
    index_path = _mcp_xdist_workers_path(consumer)
    rendezvous = consumer.path / "fresh-xdist-rendezvous"
    release_path = rendezvous / "release"
    deadline = time.monotonic() + 75
    current_index: dict[str, object] | None = None
    latest: object = "second-session xdist index has not been published"
    while time.monotonic() < deadline:
        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            latest = repr(error)
            payload = None
        if isinstance(payload, dict):
            latest = payload
            root_session_id = payload.get("session_id")
            workers = payload.get("workers")
            if root_session_id != old_session_id and isinstance(workers, list) and len(workers) == 2:
                typed_workers = [worker for worker in workers if isinstance(worker, dict)]
                worker_ids = [worker.get("worker_id") for worker in typed_workers]
                ready = (
                    len(typed_workers) == 2
                    and worker_ids == sorted(worker_ids)
                    and len(set(worker_ids)) == 2
                    and payload.get("status") == "waiting"
                    and all(
                        worker.get("status") == "waiting"
                        and worker.get("active_failure") is None
                        and isinstance(worker.get("session_id"), str)
                        and worker.get("session_id") not in old_sessions
                        and isinstance(worker.get("debugger_endpoint"), str)
                        and isinstance(worker.get("inspection_endpoint"), str)
                        for worker in typed_workers
                    )
                )
                current_endpoints = {
                    endpoint
                    for worker in typed_workers
                    for endpoint in (worker.get("debugger_endpoint"), worker.get("inspection_endpoint"))
                    if isinstance(endpoint, str)
                }
                if ready and len(current_endpoints) == 4:
                    worker_record_matches = True
                    for worker in typed_workers:
                        worker_record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "workers" / (
                            f"{worker['worker_id']}.json"
                        )
                        try:
                            worker_record = json.loads(worker_record_path.read_text(encoding="utf-8"))
                        except (OSError, json.JSONDecodeError):
                            worker_record_matches = False
                            break
                        if (
                            worker_record.get("root_session_id") != root_session_id
                            or worker_record.get("session_id") != worker.get("session_id")
                            or worker_record.get("debugger_endpoint") != worker.get("debugger_endpoint")
                            or worker_record.get("inspection_endpoint") != worker.get("inspection_endpoint")
                            or worker_record.get("status") != "waiting"
                        ):
                            worker_record_matches = False
                            break
                    try:
                        marker_records = [
                            json.loads(path.read_text(encoding="utf-8"))
                            for path in rendezvous.glob("*.json")
                        ] if rendezvous.is_dir() else []
                    except (OSError, json.JSONDecodeError):
                        marker_records = []
                    marker_workers = {record.get("worker_id") for record in marker_records}
                    if worker_record_matches and marker_workers == set(worker_ids):
                        client_path = consumer.path / "debug-mcp-xdist-fresh-session-client.py"
                        client_result_path = consumer.path / "debug-mcp-xdist-fresh-session-client-result.json"
                        client_stage_path = consumer.path / "debug-mcp-xdist-fresh-session-client-stage.txt"
                        client_log_path = consumer.path / "debug-mcp-xdist-fresh-session-client.log"
                        client_path.write_text(_debug_mcp_xdist_fresh_worker_client_script(), encoding="utf-8")
                        client_stage_path.unlink(missing_ok=True)
                        client_result = _run_debug_mcp_external_client(
                            consumer,
                            [
                                str(consumer.python),
                                str(client_path),
                                str(index_path),
                                str(client_result_path),
                                str(client_stage_path),
                            ],
                            client_name="fresh-session MCP endpoint clients",
                            timeout=60,
                            stage_path=client_stage_path,
                            log_path=client_log_path,
                        )
                        assert client_result.returncode == 0, (
                            f"fresh-session MCP endpoint clients failed ({client_result.returncode}):\n"
                            f"{client_result.stdout}\n{client_result.stderr}"
                        )
                        assert client_result_path.is_file(), client_result.stdout
                        client_observation = json.loads(client_result_path.read_text(encoding="utf-8"))
                        assert client_observation.get("session_id") == root_session_id, client_observation
                        observations_by_id = {
                            record.get("worker_id"): record
                            for record in client_observation.get("workers", [])
                            if isinstance(record, dict)
                        }
                        assert set(observations_by_id) == set(worker_ids), client_observation
                        for worker in typed_workers:
                            endpoint_observation = observations_by_id.get(worker.get("worker_id"))
                            assert isinstance(endpoint_observation, dict), client_observation
                            assert endpoint_observation.get("session_id") == worker.get("session_id"), (
                                endpoint_observation,
                                worker,
                            )
                            assert endpoint_observation.get("inspection_endpoint") == worker.get(
                                "inspection_endpoint"
                            ), (endpoint_observation, worker)
                            assert endpoint_observation.get("debugger_endpoint") == worker.get("debugger_endpoint"), (
                                endpoint_observation,
                                worker,
                            )
                            assert endpoint_observation.get("active_failure") is None, endpoint_observation
                        current_index = payload
                        break
        if process.poll() is not None:
            break
        time.sleep(0.05)

    if current_index is None:
        output_path = consumer._mcp_pytest_output_path
        output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        raise AssertionError(
            "the second xdist session did not publish two fresh waiting workers before the watchdog; "
            f"latest discovery: {latest!r}\npytest output:\n{output}"
        )

    fresh_workers = current_index.get("workers")
    assert isinstance(fresh_workers, list), current_index
    endpoints = {
        endpoint
        for worker in fresh_workers
        if isinstance(worker, dict)
        for endpoint in (worker.get("debugger_endpoint"), worker.get("inspection_endpoint"))
        if isinstance(endpoint, str)
    }
    assert len(endpoints) == 4 and not endpoints.intersection(old_endpoints), (endpoints, old_endpoints)
    release_path.write_text("release fresh xdist session\n", encoding="utf-8")
    consumer._mcp_xdist_restart_observation = {
        "old_session_id": old_session_id,
        "old_worker_sessions": sorted(old_sessions),
        "old_endpoints": sorted(old_endpoints),
        "fresh_index": current_index,
        "fresh_endpoints": sorted(endpoints),
        "fresh_endpoint_observation": client_observation,
        "rendezvous_workers": sorted(marker_workers),
    }


@then("the new xdist session should replace previous worker discovery and pass its probes")
def consumer_fresh_xdist_session_replaces_previous_discovery(consumer: ConsumerProject) -> None:
    process = getattr(consumer, "_mcp_pytest_process", None)
    observation = getattr(consumer, "_mcp_xdist_restart_observation", None)
    assert isinstance(process, subprocess.Popen), process
    assert isinstance(observation, dict), observation
    try:
        return_code = process.wait(timeout=30)
    except subprocess.TimeoutExpired as error:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        raise AssertionError("the second installed xdist pytest session did not finish after worker release") from error
    output_path = consumer._mcp_pytest_output_path
    output = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    consumer.pytest_result = subprocess.CompletedProcess(consumer._mcp_pytest_command, return_code, output, "")
    assert return_code == 0, f"the fresh xdist session did not pass after worker release:\n{output}"
    assert re.search(r"\b2 passed\b", output), output

    fresh_index = observation.get("fresh_index")
    assert isinstance(fresh_index, dict), observation
    old_session_id = observation.get("old_session_id")
    old_worker_sessions = set(observation.get("old_worker_sessions", []))
    fresh_session_id = fresh_index.get("session_id")
    assert isinstance(fresh_session_id, str) and fresh_session_id != old_session_id, observation
    workers = fresh_index.get("workers")
    assert isinstance(workers, list) and len(workers) == 2, fresh_index
    worker_ids = [worker.get("worker_id") for worker in workers if isinstance(worker, dict)]
    assert worker_ids == sorted(worker_ids) and len(set(worker_ids)) == 2, workers
    assert set(observation.get("rendezvous_workers", [])) == set(worker_ids), observation
    fresh_sessions = set()
    for worker in workers:
        assert isinstance(worker, dict), workers
        assert worker.get("status") == "waiting", worker
        assert worker.get("active_failure") is None, worker
        assert worker.get("session_id") not in old_worker_sessions, worker
        assert isinstance(worker.get("debugger_endpoint"), str), worker
        assert isinstance(worker.get("inspection_endpoint"), str), worker
        fresh_sessions.add(worker.get("session_id"))
    assert len(fresh_sessions) == 2, workers

    final_path = _mcp_xdist_workers_path(consumer)
    final_index = json.loads(final_path.read_text(encoding="utf-8"))
    assert final_index.get("session_id") == fresh_session_id, final_index
    assert final_index.get("status") == "closed", final_index
    final_workers = final_index.get("workers")
    assert isinstance(final_workers, list) and len(final_workers) == 2, final_index
    assert [worker.get("worker_id") for worker in final_workers] == worker_ids, final_workers
    for worker in final_workers:
        assert worker.get("status") == "closed", worker
        assert worker.get("active_failure") is None, worker
        assert worker.get("debugger_endpoint") is None, worker
        assert worker.get("inspection_endpoint") is None, worker
        worker_record_path = consumer.path / ".pytest_cache" / "cuke" / "debug-mcp" / "workers" / (
            f"{worker['worker_id']}.json"
        )
        worker_record = json.loads(worker_record_path.read_text(encoding="utf-8"))
        assert worker_record.get("root_session_id") == fresh_session_id, worker_record
        assert worker_record.get("session_id") == worker.get("session_id"), (worker_record, worker)
        assert worker_record.get("status") == "closed", worker_record
        assert worker_record.get("debugger_endpoint") is None, worker_record
        assert worker_record.get("inspection_endpoint") is None, worker_record
    observation["final_index"] = final_index


# Cucumber Messages reporting-spine acceptance helpers (#293).
def _install_consumer_reporting_spine_probe(event_kind: str, consumer: ConsumerProject) -> None:
    invalid_envelope_source = {
        "multi-payload": (
            "invalid = Envelope(\n"
            "    test_run_started=TestRunStarted(timestamp=Timestamp(seconds=123, nanos=456)),\n"
            "    test_run_finished=TestRunFinished(\n"
            "        success=True, timestamp=Timestamp(seconds=124, nanos=0)\n"
            "    ),\n"
            ")"
        ),
        "schema-invalid": (
            "invalid = Envelope(\n"
            "    test_run_started=TestRunStarted(timestamp=Timestamp(seconds=1700000000, nanos=0))\n"
            ")\n"
            'invalid.test_run_started.timestamp.seconds = "invalid"'
        ),
    }.get(event_kind)

    extension_injectors = {
        "duplicate-lifecycle-id": '''\
        @pytest.hookimpl(hookwrapper=True, trylast=True)
        def pytest_runtest_call(item):
            yield
            if not _accepted_case_starts:
                raise AssertionError("the canonical test_case_started event was not observed")
            item.config.hook.pytest_cuke_message(
                config=item.config,
                message=Envelope(test_case_started=_accepted_case_starts[-1]),
            )
        ''',
        "orphan-reference": '''\
        @pytest.hookimpl(trylast=True)
        def pytest_runtest_setup(item):
            item.config.hook.pytest_cuke_message(
                config=item.config,
                message=Envelope(
                    attachment=Attachment(
                        body="reporting-spine-orphan-attachment",
                        content_encoding=AttachmentContentEncoding.identity,
                        media_type="text/plain",
                        test_case_started_id="reporting-spine-unknown-attempt",
                    )
                ),
            )
        ''',
        "out-of-order-lifecycle": '''\
        class _AfterMessageStreamFinalizes:
            @pytest.hookimpl(hookwrapper=True, tryfirst=True)
            def pytest_sessionfinish(self, session, exitstatus):
                outcome = yield
                del outcome, exitstatus
                config = session.config
                if _run_started_id is None or _after_run_hook_id is None:
                    raise AssertionError("the canonical AFTER_TEST_RUN hook was not observed")

                message_plugin = config.pluginmanager.get_plugin("pytest_cuke_messages")
                if message_plugin is None:
                    raise AssertionError("the Cucumber Messages plugin was not registered")
                diagnostic_start = len(message_plugin.message_diagnostics)
                config.hook.pytest_cuke_message(
                    config=config,
                    message=Envelope(
                        test_run_hook_started=TestRunHookStarted(
                            id="reporting-spine-duplicate-after-hook-start",
                            test_run_started_id=_run_started_id,
                            hook_id=_after_run_hook_id,
                            timestamp=Timestamp(seconds=1700000001, nanos=0),
                        )
                    ),
                )
                late_diagnostics = message_plugin.message_diagnostics[diagnostic_start:]
                payloads = [message_diagnostic_to_dict(diagnostic) for diagnostic in late_diagnostics]
                Path("out-of-order-diagnostics.json").write_text(json.dumps(payloads), encoding="utf-8")
                if len(payloads) != 1 or payloads[0].get("code") != "OUT_OF_ORDER_LIFECYCLE":
                    raise AssertionError(f"expected one late out-of-order diagnostic, got {payloads!r}")
                session.exitstatus = pytest.ExitCode.TESTS_FAILED


        def pytest_sessionstart(session):
            session.config.pluginmanager.register(
                _AfterMessageStreamFinalizes(),
                name="reporting_spine_after_message_stream_finalizes",
            )
        ''',
    }
    if event_kind not in {"multi-payload", "schema-invalid", *extension_injectors}:
        raise ValueError(f"unsupported reporting-spine event kind: {event_kind}")

    if invalid_envelope_source is not None:
        injection = f'''\
        @pytest.hookimpl(trylast=True)
        def pytest_runtest_setup(item):
            global _submitted_reporting_spine_probe
            if _submitted_reporting_spine_probe:
                return
            _submitted_reporting_spine_probe = True

{indent(dedent(invalid_envelope_source).strip(), "            ")}
            for envelope in (
                _attachment("reporting-spine-before"),
                invalid,
                _attachment("reporting-spine-after"),
            ):
                item.config.hook.pytest_cuke_message(config=item.config, message=envelope)
        '''
    else:
        injection = extension_injectors[event_kind]

    runtime_definitions = dedent(
        '''\
        @given("the reporting spine probe passes")
        def reporting_spine_probe_passes():
            pass
        '''
    ).strip()
    template = dedent(
        '''\
        import json
        from pathlib import Path

        import pytest
        from cucumber_messages import (
            Attachment,
            AttachmentContentEncoding,
            Envelope,
            TestRunFinished,
            TestRunHookStarted,
            TestRunStarted,
            Timestamp,
            message_converter,
        )
        from pytest_cuke import given
        from pytest_cuke.model.message_validation import message_diagnostic_to_dict


        def _attachment(body):
            return Envelope(
                attachment=Attachment(
                    body=body,
                    content_encoding=AttachmentContentEncoding.identity,
                    media_type="text/plain",
                )
            )


        _submitted_reporting_spine_probe = False
        _accepted_case_starts = []
        _run_started_id = None
        _after_run_hook_id = None


        def pytest_cuke_message_validated(config, message):
            global _accepted_case_starts, _after_run_hook_id, _run_started_id, _submitted_reporting_spine_probe
            payload = message_converter.to_dict(message)
            if message.test_case_started is not None:
                _accepted_case_starts.append(message.test_case_started)
            if message.test_run_started is not None:
                _run_started_id = message.test_run_started.id
            if message.hook is not None and message.hook.type is not None:
                if message.hook.type.value == "AFTER_TEST_RUN":
                    _after_run_hook_id = message.hook.id
            with Path("validated-messages.ndjson").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, ensure_ascii=False))
                stream.write("\\n")


        __RUNTIME_DEFINITIONS__


        __INJECTION__
        '''
    )
    source = template.replace("__RUNTIME_DEFINITIONS__", runtime_definitions).replace(
        "__INJECTION__", dedent(injection).strip()
    )
    (consumer.path / "conftest.py").write_text(source, encoding="utf-8")


@given('an installed consumer extension submits a "multi-payload" envelope through pytest_cuke_message')
def install_consumer_reporting_spine_multi_payload_probe(consumer: ConsumerProject) -> None:
    _install_consumer_reporting_spine_probe("multi-payload", consumer)


@given('an installed consumer extension submits a "schema-invalid" envelope through pytest_cuke_message')
def install_consumer_reporting_spine_schema_invalid_probe(consumer: ConsumerProject) -> None:
    _install_consumer_reporting_spine_probe("schema-invalid", consumer)


@given('an installed consumer extension submits a "duplicate-lifecycle-id" envelope through pytest_cuke_message')
def install_consumer_reporting_spine_duplicate_id_probe(consumer: ConsumerProject) -> None:
    _install_consumer_reporting_spine_probe("duplicate-lifecycle-id", consumer)


@given('an installed consumer extension submits an "orphan-reference" envelope through pytest_cuke_message')
def install_consumer_reporting_spine_orphan_reference_probe(consumer: ConsumerProject) -> None:
    _install_consumer_reporting_spine_probe("orphan-reference", consumer)


@given('an installed consumer extension submits an "out-of-order-lifecycle" envelope through pytest_cuke_message')
def install_consumer_reporting_spine_out_of_order_probe(consumer: ConsumerProject) -> None:
    _install_consumer_reporting_spine_probe("out-of-order-lifecycle", consumer)


@given(
    re.compile(
        r'the consumer installs reporting-spine probe "(?P<probe>runtime-outcomes|passing-session|teardown-failure)"'
    )
)
def install_consumer_reporting_spine_runtime_probe(probe: str, consumer: ConsumerProject) -> None:
    runtime_definitions = dedent(
        '''\
        @given("the reporting spine step passes")
        def reporting_spine_step_passes():
            pass


        @given("the reporting spine step fails")
        def reporting_spine_step_fails():
            pytest.fail("reporting spine failure sentinel")


        @given("the reporting spine step skips")
        def reporting_spine_step_skips():
            pytest.skip("reporting spine skip sentinel")
        '''
    ).strip()
    if probe == "passing-session":
        runtime_definitions = dedent(
            '''\
            @given("the reporting spine step passes")
            def reporting_spine_step_passes():
                pass
            '''
        ).strip()
    elif probe == "teardown-failure":
        runtime_definitions = dedent(
            '''\
            @pytest.fixture
            def reporting_spine_teardown_failure():
                yield
                raise RuntimeError("reporting spine teardown failure sentinel")


            @given("the reporting spine step passes before pytest teardown")
            def reporting_spine_step_passes_before_teardown(reporting_spine_teardown_failure):
                pass
            '''
        ).strip()

    template = dedent(
        '''\
        import json
        from pathlib import Path

        import pytest
        from cucumber_messages import message_converter
        from pytest_cuke import given


        def pytest_cuke_message_validated(config, message):
            payload = message_converter.to_dict(message)
            output_path = getattr(config.option, "cuke_messages_ndjson", None)
            if isinstance(output_path, str) and output_path:
                output = Path(output_path)
                observer_path = output.with_name(f"{output.stem}.validated.ndjson")
            else:
                observer_path = Path("validated-messages.ndjson")
            with observer_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, ensure_ascii=False))
                stream.write("\\n")


        __RUNTIME_DEFINITIONS__
        '''
    )
    source = template.replace("__RUNTIME_DEFINITIONS__", runtime_definitions)
    (consumer.path / "conftest.py").write_text(source, encoding="utf-8")


@then(
    re.compile(
        r'the consumer should report one structured message diagnostic "(?P<code>INVALID_PAYLOAD_SHAPE|'
        r'SCHEMA_VALIDATION_ERROR|DUPLICATE_LIFECYCLE_ID|ORPHAN_REFERENCE|OUT_OF_ORDER_LIFECYCLE)"'
        r'(?: at position (?P<position>\d+))? with payload kind "(?P<payload_kind>[^"]+)"'
    )
)
def consumer_reports_message_diagnostic(
    code: str,
    position: str | None,
    payload_kind: str,
    consumer: ConsumerProject,
) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    prefix = "PYTEST_CUKE_MESSAGE_DIAGNOSTIC="
    output = result.stdout + result.stderr
    diagnostic_lines = [line[len(prefix) :] for line in output.splitlines() if line.startswith(prefix)]
    assert len(diagnostic_lines) == 1, (
        f"expected one structured pytest-cuke message diagnostic, got {diagnostic_lines!r}:\n{output}"
    )

    diagnostic_text = diagnostic_lines[0]
    diagnostic = json.loads(diagnostic_text)
    assert isinstance(diagnostic, dict), diagnostic
    assert json.dumps(diagnostic, ensure_ascii=False, separators=(",", ":")) == diagnostic_text, diagnostic_text
    expected_payload_kind = None if payload_kind == "null" else payload_kind
    assert diagnostic.get("code") == code, diagnostic
    assert diagnostic.get("severity") == "error", diagnostic
    actual_position = diagnostic.get("position")
    assert isinstance(actual_position, int) and actual_position >= 0, diagnostic
    if position is not None:
        assert actual_position == int(position), diagnostic
    assert diagnostic.get("payload_kind") == expected_payload_kind, diagnostic
    assert isinstance(diagnostic.get("message"), str) and diagnostic["message"].strip(), diagnostic

    if code == "INVALID_PAYLOAD_SHAPE":
        assert "payload" in diagnostic["message"].casefold(), diagnostic
    elif code == "SCHEMA_VALIDATION_ERROR":
        assert diagnostic.get("instance_path") == "/testRunStarted/timestamp/seconds", diagnostic


@then(
    re.compile(
        r'the late lifecycle probe should capture one structured message diagnostic "(?P<code>OUT_OF_ORDER_LIFECYCLE)" '
        r'with payload kind "(?P<payload_kind>test_run_hook_started)"'
    )
)
def consumer_captures_late_message_diagnostic(code: str, payload_kind: str, consumer: ConsumerProject) -> None:
    diagnostic_path = consumer.path / "out-of-order-diagnostics.json"
    assert diagnostic_path.is_file(), f"late lifecycle probe did not write diagnostics: {diagnostic_path}"
    diagnostics = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    assert isinstance(diagnostics, list) and len(diagnostics) == 1, diagnostics
    diagnostic = diagnostics[0]
    assert isinstance(diagnostic, dict), diagnostic
    assert diagnostic.get("code") == code, diagnostic
    assert diagnostic.get("severity") == "error", diagnostic
    assert diagnostic.get("payload_kind") == payload_kind, diagnostic
    assert isinstance(diagnostic.get("position"), int) and diagnostic["position"] >= 0, diagnostic
    message = diagnostic.get("message")
    assert isinstance(message, str) and any(
        expected_phrase in message
        for expected_phrase in (
            "Cannot accept an envelope after stream validation has finished",
            "test_run_hook_started appeared while another run hook was active",
        )
    ), diagnostic


@then(
    re.compile(
        r'consumer Messages artifact "(?P<relative_path>[^"]+)" should retain the valid terminal reporting spine '
        r'around the rejected "(?P<event_kind>multi-payload|schema-invalid|duplicate-lifecycle-id|'
        r'orphan-reference|out-of-order-lifecycle)" event'
    )
)
def consumer_messages_artifact_retains_reporting_spine(
    relative_path: str,
    event_kind: str,
    consumer: ConsumerProject,
) -> None:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    assert artifact_path.is_file(), f"Messages artifact was not written: {artifact_path}"
    raw_lines = [line for line in artifact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert raw_lines, f"Messages artifact is empty: {artifact_path}"

    raw_envelopes: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(raw_lines, start=1):
        payload = json.loads(raw_line)
        assert isinstance(payload, dict), f"line {line_number} is not an envelope object: {payload!r}"
        payload_keys = [key for key, value in payload.items() if value is not None]
        assert len(payload_keys) == 1, f"line {line_number} is not a single-payload envelope: {payload!r}"
        _validate_messages_envelope_compatibly(payload)
        raw_envelopes.append(payload)

    observer_path = _consumer_artifact_path("validated-messages.ndjson", consumer)
    assert observer_path.is_file(), f"validated-message observer did not receive accepted events: {observer_path}"
    observer_envelopes: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(observer_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        assert isinstance(payload, dict), f"observer line {line_number} is not an envelope object: {payload!r}"
        payload_keys = [key for key, value in payload.items() if value is not None]
        assert len(payload_keys) == 1, f"observer line {line_number} is not a single-payload envelope: {payload!r}"
        _validate_messages_envelope_compatibly(payload)
        observer_envelopes.append(payload)

    def ordered_event_ids(envelopes: list[dict[str, Any]]) -> list[tuple[str, object]]:
        identities: list[tuple[str, object]] = []
        for envelope in envelopes:
            kind = next(key for key, value in envelope.items() if value is not None)
            event = envelope[kind]
            assert isinstance(event, dict), (kind, event)
            known_ids = tuple(
                (name, event[name])
                for name in ("id", "testCaseStartedId", "testCaseId", "testStepId")
                if name in event
            )
            serialized_event = known_ids or json.dumps(event, ensure_ascii=False, sort_keys=True)
            identities.append((kind, serialized_event))
        return identities

    sink_event_ids = ordered_event_ids(raw_envelopes)
    observer_event_ids = ordered_event_ids(observer_envelopes)
    assert observer_event_ids == sink_event_ids, (
        "the validated-message observer and configured NDJSON sink must receive the same ordered accepted events: "
        f"observer={observer_event_ids!r}, sink={sink_event_ids!r}"
    )
    assert observer_envelopes == raw_envelopes, (
        "both sinks must receive the identical accepted envelopes, including payload values: "
        f"observer={observer_envelopes!r}, sink={raw_envelopes!r}"
    )

    run_started = [envelope["testRunStarted"] for envelope in raw_envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in raw_envelopes if "testRunFinished" in envelope]
    attachments = [envelope["attachment"] for envelope in raw_envelopes if "attachment" in envelope]
    assert len(run_started) == 1, f"expected one testRunStarted message, got {run_started!r}"
    assert len(run_finished) == 1, f"expected one terminal testRunFinished message, got {run_finished!r}"
    assert run_finished[0]["success"] is False, run_finished[0]
    if event_kind == "out-of-order-lifecycle":
        rejected_hook_id = "reporting-spine-duplicate-after-hook-start"
        assert not any(
            envelope.get("testRunHookStarted", {}).get("id") == rejected_hook_id for envelope in raw_envelopes
        ), raw_envelopes
    assert raw_envelopes[-1].get("testRunFinished") == run_finished[0], "testRunFinished must close the stream"

    marker_bodies = [attachment.get("body") for attachment in attachments]
    if event_kind in {"multi-payload", "schema-invalid"}:
        assert marker_bodies.count("reporting-spine-before") == 1, marker_bodies
        assert marker_bodies.count("reporting-spine-after") == 1, marker_bodies
        run_started_index = next(index for index, envelope in enumerate(raw_envelopes) if "testRunStarted" in envelope)
        before_index = next(
            index
            for index, envelope in enumerate(raw_envelopes)
            if envelope.get("attachment", {}).get("body") == "reporting-spine-before"
        )
        after_index = next(
            index
            for index, envelope in enumerate(raw_envelopes)
            if envelope.get("attachment", {}).get("body") == "reporting-spine-after"
        )
        finished_index = next(index for index, envelope in enumerate(raw_envelopes) if "testRunFinished" in envelope)
        assert run_started_index < before_index < after_index < finished_index, raw_envelopes
    elif event_kind == "duplicate-lifecycle-id":
        started = [envelope["testCaseStarted"] for envelope in raw_envelopes if "testCaseStarted" in envelope]
        assert len(started) == 1, f"the duplicate attempt ID must be rejected before either sink: {started!r}"
    elif event_kind == "orphan-reference":
        assert "reporting-spine-orphan-attachment" not in marker_bodies, marker_bodies

    for sink_name, envelopes in (
        ("configured NDJSON sink", raw_envelopes),
        ("validated-message observer", observer_envelopes),
    ):
        if event_kind == "multi-payload":
            assert not any(
                envelope.get("testRunStarted", {}).get("timestamp", {}).get("seconds") == 123
                or envelope.get("testRunFinished", {}).get("timestamp", {}).get("seconds") == 124
                for envelope in envelopes
            ), f"the rejected multi-payload event leaked into the {sink_name}"
        elif event_kind == "schema-invalid":
            assert not any(
                envelope.get("testRunStarted", {}).get("timestamp", {}).get("seconds") == "invalid"
                for envelope in envelopes
            ), f"the rejected schema-invalid payload leaked into the {sink_name}"
        elif event_kind == "orphan-reference":
            assert not any(
                envelope.get("attachment", {}).get("body") == "reporting-spine-orphan-attachment"
                for envelope in envelopes
            ), f"the rejected orphan attachment leaked into the {sink_name}"


def _reporting_spine_artifact(relative_path: str, consumer: ConsumerProject) -> list[dict[str, Any]]:
    artifact_path = _consumer_artifact_path(relative_path, consumer)
    assert artifact_path.is_file(), f"Messages artifact was not written: {artifact_path}"
    envelopes: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(artifact_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        assert isinstance(payload, dict), f"line {line_number} is not an envelope object: {payload!r}"
        payload_keys = [key for key, value in payload.items() if value is not None]
        assert len(payload_keys) == 1, f"line {line_number} is not a single-payload envelope: {payload!r}"
        _validate_messages_envelope_compatibly(payload)
        envelopes.append(payload)
    assert envelopes, f"Messages artifact is empty: {artifact_path}"
    return envelopes


def _reporting_spine_hook_failure_evidence(result: dict[str, Any]) -> str:
    exception = result.get("exception")
    evidence = (
        result.get("message"),
        exception.get("message") if isinstance(exception, dict) else None,
        exception.get("stackTrace") if isinstance(exception, dict) else None,
    )
    return " ".join(value for value in evidence if isinstance(value, str))


def _reporting_spine_event_ids(envelopes: list[dict[str, Any]]) -> list[tuple[str, object]]:
    identities: list[tuple[str, object]] = []
    for envelope in envelopes:
        kind = next(key for key, value in envelope.items() if value is not None)
        event = envelope[kind]
        assert isinstance(event, dict), (kind, event)
        event_ids = tuple(
            (name, event[name])
            for name in ("id", "testCaseStartedId", "testCaseId", "testStepId")
            if name in event
        )
        identities.append((kind, event_ids or json.dumps(event, ensure_ascii=False, sort_keys=True)))
    return identities


def _assert_reporting_spine_fanout(
    messages_path: str,
    observer_path: str,
    consumer: ConsumerProject,
) -> list[dict[str, Any]]:
    messages = _reporting_spine_artifact(messages_path, consumer)
    observed = _reporting_spine_artifact(observer_path, consumer)
    message_ids = _reporting_spine_event_ids(messages)
    observed_ids = _reporting_spine_event_ids(observed)
    assert observed_ids == message_ids, (
        "the validated extension sink and configured NDJSON sink must receive the same event IDs in the same order: "
        f"observer={observed_ids!r}, ndjson={message_ids!r}"
    )
    assert observed == messages, (
        "the validated extension sink and configured NDJSON sink must receive identical accepted envelopes: "
        f"observer={observed!r}, ndjson={messages!r}"
    )
    return messages



@then(
    re.compile(
        r'consumer Messages artifact "(?P<relative_path>[^"]+)" should report a failed root AFTER_TEST_RUN hook with '
        r'sentinel "(?P<failure_sentinel>[^"]+)", a passed worker step, and an unsuccessful root run'
    )
)
def consumer_xdist_stream_reports_failed_root_after_run_hook(
    relative_path: str,
    failure_sentinel: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _reporting_spine_artifact(relative_path, consumer)

    run_starts = [
        envelope["testRunStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunStarted"), dict)
    ]
    run_start_ids = [started.get("id") for started in run_starts]
    assert run_start_ids and all(isinstance(run_id, str) and run_id for run_id in run_start_ids), run_starts
    assert len(run_start_ids) == len(set(run_start_ids)), run_start_ids
    assert any(run_id.startswith("master:") for run_id in run_start_ids), run_start_ids

    run_finishes = [
        envelope["testRunFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunFinished"), dict)
    ]
    assert run_finishes, f"no terminal Messages outcomes were emitted for xdist: {envelopes!r}"
    finished_run_ids = []
    for finish in run_finishes:
        assert finish.get("success") is False, finish
        run_id = finish.get("testRunStartedId")
        assert isinstance(run_id, str) and run_id in set(run_start_ids), finish
        finished_run_ids.append(run_id)
    assert len(finished_run_ids) == len(set(finished_run_ids)), finished_run_ids
    assert set(finished_run_ids) == set(run_start_ids), (run_start_ids, run_finishes)
    master_run_finishes = [
        finish for finish in run_finishes if str(finish.get("testRunStartedId", "")).startswith("master:")
    ]
    assert len(master_run_finishes) == 1, master_run_finishes
    assert envelopes[-1].get("testRunFinished") == master_run_finishes[0], "the root terminal event must close the stream"

    after_hook_ids = {
        hook["id"]
        for envelope in envelopes
        if isinstance((hook := envelope.get("hook")), dict)
        and hook.get("type") == "AFTER_TEST_RUN"
        and isinstance(hook.get("id"), str)
    }
    assert after_hook_ids, f"no AFTER_TEST_RUN hook definition was emitted: {envelopes!r}"
    after_hook_starts = [
        started
        for envelope in envelopes
        if isinstance((started := envelope.get("testRunHookStarted")), dict)
        and started.get("hookId") in after_hook_ids
    ]
    assert after_hook_starts, f"no AFTER_TEST_RUN hook was started in the xdist stream: {envelopes!r}"
    after_hook_start_ids = [started.get("id") for started in after_hook_starts]
    assert all(isinstance(start_id, str) and start_id for start_id in after_hook_start_ids), after_hook_starts
    assert len(after_hook_start_ids) == len(set(after_hook_start_ids)), after_hook_starts
    assert all(started.get("testRunStartedId") in set(run_start_ids) for started in after_hook_starts), (
        run_start_ids,
        after_hook_starts,
    )
    started_run_ids = {started.get("testRunStartedId") for started in after_hook_starts}
    assert started_run_ids == set(run_start_ids), (started_run_ids, run_start_ids, after_hook_starts)
    after_hook_starts_by_id = {started["id"]: started for started in after_hook_starts}

    after_hook_finishes = [
        finished
        for envelope in envelopes
        if isinstance((finished := envelope.get("testRunHookFinished")), dict)
        and finished.get("testRunHookStartedId") in after_hook_start_ids
    ]
    assert after_hook_finishes, f"no AFTER_TEST_RUN hook was finished in the xdist stream: {envelopes!r}"
    finished_after_hook_ids = [finish.get("testRunHookStartedId") for finish in after_hook_finishes]
    assert len(finished_after_hook_ids) == len(set(finished_after_hook_ids)), after_hook_finishes
    assert set(finished_after_hook_ids) == set(after_hook_start_ids), (after_hook_starts, after_hook_finishes)
    failed_after_hook_run_ids: set[str] = set()
    for finish in after_hook_finishes:
        result = finish.get("result")
        if not isinstance(result, dict) or result.get("status") != "FAILED":
            continue
        if failure_sentinel in _reporting_spine_hook_failure_evidence(result):
            started = after_hook_starts_by_id[finish["testRunHookStartedId"]]
            run_id = started.get("testRunStartedId")
            assert isinstance(run_id, str) and run_id, (started, finish)
            failed_after_hook_run_ids.add(run_id)
    assert failed_after_hook_run_ids == set(run_start_ids), (
        f"every root/worker test run must have a failed AFTER_TEST_RUN hook containing {failure_sentinel!r}",
        run_start_ids,
        failed_after_hook_run_ids,
        after_hook_finishes,
    )

    pickles_by_id = {
        pickle["id"]: pickle
        for envelope in envelopes
        if isinstance((pickle := envelope.get("pickle")), dict)
        and isinstance(pickle.get("id"), str)
    }
    cases_by_id = {
        case["id"]: case
        for envelope in envelopes
        if isinstance((case := envelope.get("testCase")), dict)
        and isinstance(case.get("id"), str)
    }
    assert pickles_by_id and cases_by_id, (pickles_by_id, cases_by_id)
    attempts_by_id = {
        attempt["id"]: attempt
        for envelope in envelopes
        if isinstance((attempt := envelope.get("testCaseStarted")), dict)
        and isinstance(attempt.get("id"), str)
    }
    assert attempts_by_id, f"no xdist scenario attempts were emitted: {envelopes!r}"
    assert len(attempts_by_id) == sum(
        isinstance(envelope.get("testCaseStarted"), dict) for envelope in envelopes
    ), attempts_by_id
    worker_ids: set[str] = set()
    for attempt in attempts_by_id.values():
        case_id = attempt.get("testCaseId")
        assert case_id in cases_by_id, attempt
        worker_id = attempt.get("workerId")
        assert isinstance(worker_id, str) and worker_id and worker_id != "master", attempt
        assert attempt["id"].startswith(f"{worker_id}:"), attempt
        worker_ids.add(worker_id)
        test_case = cases_by_id[case_id]
        pickle = pickles_by_id.get(test_case.get("pickleId"))
        assert isinstance(pickle, dict), test_case
        pickle_step_ids = {
            step.get("id"): step.get("text")
            for step in pickle.get("steps", [])
            if isinstance(step, dict) and isinstance(step.get("id"), str)
        }
        test_case_steps = test_case.get("testSteps")
        assert isinstance(test_case_steps, list), test_case
        assert all(
            isinstance(step, dict) and step.get("pickleStepId") in pickle_step_ids
            for step in test_case_steps
        ), (test_case, pickle)

    case_finish_attempt_ids = [
        finish.get("testCaseStartedId")
        for envelope in envelopes
        if isinstance((finish := envelope.get("testCaseFinished")), dict)
    ]
    assert case_finish_attempt_ids and set(case_finish_attempt_ids) == set(attempts_by_id), (
        case_finish_attempt_ids,
        attempts_by_id,
    )
    assert len(case_finish_attempt_ids) == len(set(case_finish_attempt_ids)), case_finish_attempt_ids

    step_starts = [
        step
        for envelope in envelopes
        if isinstance((step := envelope.get("testStepStarted")), dict)
    ]
    step_finishes = [
        step
        for envelope in envelopes
        if isinstance((step := envelope.get("testStepFinished")), dict)
    ]
    step_start_pairs = [(step.get("testCaseStartedId"), step.get("testStepId")) for step in step_starts]
    step_finish_pairs = [(step.get("testCaseStartedId"), step.get("testStepId")) for step in step_finishes]
    assert step_start_pairs and set(step_start_pairs) == set(step_finish_pairs), (step_starts, step_finishes)
    assert len(step_start_pairs) == len(set(step_start_pairs)), step_starts
    passed_scenario_steps = []
    for step in step_finishes:
        attempt_id = step.get("testCaseStartedId")
        attempt = attempts_by_id.get(attempt_id)
        assert isinstance(attempt, dict), step
        test_case = cases_by_id[attempt["testCaseId"]]
        case_steps = {
            case_step["id"]: case_step["pickleStepId"]
            for case_step in test_case["testSteps"]
        }
        pickle = pickles_by_id[test_case["pickleId"]]
        pickle_steps = {
            pickle_step.get("id"): pickle_step.get("text")
            for pickle_step in pickle["steps"]
            if isinstance(pickle_step, dict)
        }
        result = step.get("testStepResult")
        if (
            isinstance(result, dict)
            and result.get("status") == "PASSED"
            and pickle_steps.get(case_steps.get(step.get("testStepId")))
            == "the xdist reporting spine step passes"
        ):
            passed_scenario_steps.append(step)
    assert passed_scenario_steps and worker_ids, (passed_scenario_steps, worker_ids)
    assert any(run_id.startswith("master:") for run_id in failed_after_hook_run_ids), failed_after_hook_run_ids


@then(
    re.compile(
        r'consumer output and Messages artifact "(?P<relative_path>[^"]+)" should exclude xdist diagnostics '
        r'"(?P<diagnostics>[a-z_,]+)"'
    )
)
def consumer_xdist_reporting_has_no_manifest_diagnostics(
    relative_path: str,
    diagnostics: str,
    consumer: ConsumerProject,
) -> None:
    result = consumer.pytest_result
    assert result is not None, "pytest has not been run in this consumer"
    output = f"{result.stdout}\n{result.stderr}".casefold()
    envelopes = _reporting_spine_artifact(relative_path, consumer)
    artifact = json.dumps(envelopes, ensure_ascii=False, sort_keys=True).casefold()
    codes = [code.strip().casefold() for code in diagnostics.split(",") if code.strip()]
    assert codes, diagnostics
    for code in codes:
        assert code not in output, f"pytest output unexpectedly reported {code!r}:\n{output}"
        assert code not in artifact, f"Messages artifact unexpectedly reported {code!r}:\n{artifact}"


@then(
    re.compile(
        r'consumer reporting-spine artifacts "(?P<messages_path>[^"]+)" and "(?P<observer_path>[^"]+)" '
        r'should preserve outcome terminal events with protocol "(?P<protocol_version>[0-9.]+)"'
    )
)
def consumer_reporting_spine_preserves_outcomes(
    messages_path: str,
    observer_path: str,
    protocol_version: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _assert_reporting_spine_fanout(messages_path, observer_path, consumer)
    meta = [envelope["meta"] for envelope in envelopes if isinstance(envelope.get("meta"), dict)]
    assert len(meta) == 1, meta
    assert meta[0].get("protocolVersion") == protocol_version, meta[0]

    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finished = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    assert len(run_started) == 1, run_started
    assert len(run_finished) == 1, run_finished
    assert run_finished[0].get("success") is False, run_finished[0]
    assert envelopes[-1].get("testRunFinished") == run_finished[0], "the terminal event must close the stream"

    pickles_by_name = {
        pickle["name"]: pickle
        for envelope in envelopes
        if isinstance((pickle := envelope.get("pickle")), dict)
    }
    expected_statuses = {
        "A reporting spine step passes": "PASSED",
        "A reporting spine step fails": "FAILED",
        "A reporting spine step skips": "SKIPPED",
        "An undefined reporting spine step stays undefined": "UNDEFINED",
    }
    assert set(pickles_by_name) == set(expected_statuses), pickles_by_name
    cases_by_pickle = {
        test_case["pickleId"]: test_case
        for envelope in envelopes
        if isinstance((test_case := envelope.get("testCase")), dict)
    }
    pickle_events = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    case_events = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    assert len(pickle_events) == len(case_events) == len(expected_statuses), (pickle_events, case_events)
    started_by_case = {
        started["testCaseId"]: started
        for envelope in envelopes
        if isinstance((started := envelope.get("testCaseStarted")), dict)
    }
    start_events = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    case_finishes = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    assert (
        len(cases_by_pickle)
        == len(started_by_case)
        == len(start_events)
        == len(case_finishes)
        == len(expected_statuses)
    )

    for scenario_name, expected_status in expected_statuses.items():
        pickle = pickles_by_name[scenario_name]
        test_case = cases_by_pickle[pickle["id"]]
        attempt = started_by_case[test_case["id"]]
        step_finishes = [
            envelope["testStepFinished"]
            for envelope in envelopes
            if isinstance(envelope.get("testStepFinished"), dict)
            and envelope["testStepFinished"].get("testCaseStartedId") == attempt["id"]
        ]
        assert len(step_finishes) == 1, (scenario_name, step_finishes)
        actual_status = step_finishes[0]["testStepResult"].get("status")
        assert actual_status == expected_status, (scenario_name, actual_status, step_finishes)
        linked_finishes = [
            finish
            for finish in case_finishes
            if finish.get("testCaseStartedId") == attempt["id"]
        ]
        assert len(linked_finishes) == 1, (scenario_name, linked_finishes)


@then(
    re.compile(
        r'consumer reporting-spine artifacts "(?P<messages_path>[^"]+)" and "(?P<observer_path>[^"]+)" '
        r'should keep the passed step and failed run after teardown failure'
    )
)
def consumer_reporting_spine_preserves_teardown_failure(
    messages_path: str,
    observer_path: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _assert_reporting_spine_fanout(messages_path, observer_path, consumer)
    meta = [envelope["meta"] for envelope in envelopes if isinstance(envelope.get("meta"), dict)]
    run_starts = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    run_finishes = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    starts = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    case_finishes = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    step_finishes = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    assert len(meta) == len(run_starts) == len(run_finishes) == len(cases) == len(starts) == 1
    assert len(case_finishes) == len(step_finishes) == 1
    assert meta[0].get("protocolVersion") == "28.0.0", meta[0]
    assert cases[0].get("pickleId") == next(envelope["pickle"]["id"] for envelope in envelopes if "pickle" in envelope)
    assert starts[0].get("testCaseId") == cases[0].get("id")
    assert step_finishes[0].get("testStepResult", {}).get("status") == "PASSED", step_finishes[0]
    assert step_finishes[0].get("testCaseStartedId") == starts[0].get("id")
    assert case_finishes[0].get("testCaseStartedId") == starts[0].get("id")
    assert run_finishes[0].get("success") is False, run_finishes[0]
    assert envelopes[-1].get("testRunFinished") == run_finishes[0], "the terminal event must close the stream"


@then(
    re.compile(
        r'consumer Messages artifact "(?P<messages_path>[^"]+)" should record the failed terminal run and '
        r"AFTER_TEST_RUN diagnostic after an external tryfirst session-finish failure"
    )
)
def consumer_messages_external_session_finish_failure(
    messages_path: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _reporting_spine_artifact(messages_path, consumer)

    metas = [envelope["meta"] for envelope in envelopes if isinstance(envelope.get("meta"), dict)]
    assert len(metas) == 1 and metas[0].get("protocolVersion") == "28.0.0", metas
    run_starts = [
        envelope["testRunStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunStarted"), dict)
    ]
    run_finishes = [
        envelope["testRunFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunFinished"), dict)
    ]
    assert len(run_starts) == len(run_finishes) == 1, (run_starts, run_finishes)
    run_id = run_starts[0].get("id")
    assert isinstance(run_id, str) and run_id, run_starts[0]
    terminal_event = run_finishes[0]
    assert terminal_event.get("testRunStartedId") == run_id, terminal_event
    assert terminal_event.get("success") is False, terminal_event
    assert envelopes[-1].get("testRunFinished") == terminal_event, "the terminal event must close the stream"

    after_hooks = [
        envelope["hook"]
        for envelope in envelopes
        if isinstance(envelope.get("hook"), dict)
        and envelope["hook"].get("type") == "AFTER_TEST_RUN"
    ]
    assert len(after_hooks) == 1, after_hooks
    after_hook_id = after_hooks[0].get("id")
    assert isinstance(after_hook_id, str) and after_hook_id, after_hooks[0]
    after_hook_starts = [
        envelope["testRunHookStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunHookStarted"), dict)
        and envelope["testRunHookStarted"].get("hookId") == after_hook_id
    ]
    assert len(after_hook_starts) == 1, after_hook_starts
    after_hook_started_id = after_hook_starts[0].get("id")
    assert isinstance(after_hook_started_id, str) and after_hook_started_id, after_hook_starts[0]
    assert after_hook_starts[0].get("testRunStartedId") == run_id, after_hook_starts[0]
    after_hook_finishes = [
        envelope["testRunHookFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testRunHookFinished"), dict)
        and envelope["testRunHookFinished"].get("testRunHookStartedId") == after_hook_started_id
    ]
    assert len(after_hook_finishes) == 1, after_hook_finishes
    after_hook_result = after_hook_finishes[0].get("result")
    assert isinstance(after_hook_result, dict), after_hook_finishes[0]
    assert after_hook_result.get("status") == "FAILED", after_hook_result
    failure_evidence = _reporting_spine_hook_failure_evidence(after_hook_result)
    assert "external tryfirst pytest_sessionfinish failure sentinel" in failure_evidence, (
        after_hook_result,
        failure_evidence,
    )

    pickles = [envelope["pickle"] for envelope in envelopes if isinstance(envelope.get("pickle"), dict)]
    test_cases = [envelope["testCase"] for envelope in envelopes if isinstance(envelope.get("testCase"), dict)]
    case_starts = [
        envelope["testCaseStarted"]
        for envelope in envelopes
        if isinstance(envelope.get("testCaseStarted"), dict)
    ]
    case_finishes = [
        envelope["testCaseFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testCaseFinished"), dict)
    ]
    step_finishes = [
        envelope["testStepFinished"]
        for envelope in envelopes
        if isinstance(envelope.get("testStepFinished"), dict)
    ]
    assert len(pickles) == len(test_cases) == len(case_starts) == len(case_finishes) == 1, (
        pickles,
        test_cases,
        case_starts,
        case_finishes,
    )
    assert len(step_finishes) == 1, step_finishes
    assert pickles[0].get("name") == "The step passes before session finish fails", pickles[0]
    assert test_cases[0].get("pickleId") == pickles[0].get("id"), test_cases[0]
    assert case_starts[0].get("testCaseId") == test_cases[0].get("id"), case_starts[0]
    attempt_id = case_starts[0].get("id")
    assert isinstance(attempt_id, str) and attempt_id, case_starts[0]
    assert case_finishes[0].get("testCaseStartedId") == attempt_id, case_finishes[0]
    assert step_finishes[0].get("testCaseStartedId") == attempt_id, step_finishes[0]
    step_result = step_finishes[0].get("testStepResult")
    assert isinstance(step_result, dict) and step_result.get("status") == "PASSED", step_finishes[0]


@then(
    re.compile(
        r'consumer reporting-spine sessions "(?P<first_messages>[^"]+)" and "(?P<second_messages>[^"]+)" '
        r'should have isolated validated sinks and lifecycle IDs'
    )
)
def consumer_reporting_spine_sessions_are_isolated(
    first_messages: str,
    second_messages: str,
    consumer: ConsumerProject,
) -> None:
    first_path = PurePosixPath(first_messages)
    second_path = PurePosixPath(second_messages)
    first_observer = str(first_path.with_name(f"{first_path.stem}.validated.ndjson"))
    second_observer = str(second_path.with_name(f"{second_path.stem}.validated.ndjson"))
    first = _assert_reporting_spine_fanout(first_messages, first_observer, consumer)
    second = _assert_reporting_spine_fanout(second_messages, second_observer, consumer)

    for name, envelopes in (("first", first), ("second", second)):
        metas = [envelope["meta"] for envelope in envelopes if isinstance(envelope.get("meta"), dict)]
        starts = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
        cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
        case_finishes = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
        run_starts = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
        run_finishes = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
        counts = (len(metas), len(starts), len(cases), len(case_finishes), len(run_starts), len(run_finishes))
        assert counts == (1, 1, 1, 1, 1, 1), (
            name,
            metas,
            starts,
            cases,
            case_finishes,
            run_starts,
            run_finishes,
        )
        assert metas[0].get("protocolVersion") == "28.0.0", metas[0]
        assert cases[0].get("pickleId") == next(
            envelope["pickle"]["id"] for envelope in envelopes if "pickle" in envelope
        ), (name, cases[0])
        assert starts[0].get("testCaseId") == cases[0].get("id"), (name, starts[0], cases[0])
        assert case_finishes[0].get("testCaseStartedId") == starts[0].get("id"), (name, case_finishes[0])
        assert run_finishes[0].get("success") is True, (name, run_finishes[0])
        assert envelopes[-1].get("testRunFinished") == run_finishes[0], (name, envelopes[-1])

    first_attempt_id = next(
        envelope["testCaseStarted"]["id"] for envelope in first if "testCaseStarted" in envelope
    )
    second_attempt_id = next(
        envelope["testCaseStarted"]["id"] for envelope in second if "testCaseStarted" in envelope
    )
    first_case_id = next(envelope["testCase"]["id"] for envelope in first if "testCase" in envelope)
    second_case_id = next(envelope["testCase"]["id"] for envelope in second if "testCase" in envelope)
    assert first_attempt_id != second_attempt_id, (first_attempt_id, second_attempt_id)
    assert first_case_id != second_case_id, (first_case_id, second_case_id)


@given(
    re.compile(
        r'the consumer installs reporting-spine run-hook probe "(?P<probe>failing-after-hook)"'
    )
)
def install_consumer_reporting_spine_run_hook_probe(probe: str, consumer: ConsumerProject) -> None:
    if probe != "failing-after-hook":
        raise ValueError(f"unsupported reporting-spine run-hook probe: {probe}")

    template = dedent(
        '''\
        import json
        from pathlib import Path

        import pytest
        from cucumber_messages import Attachment, AttachmentContentEncoding, Envelope, message_converter
        from pytest_cuke import given


        _hook_types = {}
        _run_hook_started_ids = {}


        def pytest_cuke_message_validated(config, message):
            if message.hook is not None and message.hook.type is not None:
                _hook_types[message.hook.id] = message.hook.type.value
            if message.test_run_hook_started is not None:
                started = message.test_run_hook_started
                hook_type = _hook_types.get(started.hook_id)
                if hook_type is not None:
                    _run_hook_started_ids[hook_type] = started.id

            payload = message_converter.to_dict(message)
            output_path = getattr(config.option, "cuke_messages_ndjson", None)
            if isinstance(output_path, str) and output_path:
                output = Path(output_path)
                observer_path = output.with_name(f"{output.stem}.validated.ndjson")
            else:
                observer_path = Path("validated-messages.ndjson")
            with observer_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, ensure_ascii=False))
                stream.write("\\n")


        def _attach_to_run_hook(config, hook_type):
            started_id = _run_hook_started_ids.get(hook_type)
            if not started_id:
                raise AssertionError(f"no started {hook_type} run hook was observed")
            attachment_name = hook_type.casefold().replace("_", "-")
            config.hook.pytest_cuke_message(
                config=config,
                message=Envelope(
                    attachment=Attachment(
                        body=f"reporting-spine-{attachment_name}-attachment",
                        content_encoding=AttachmentContentEncoding.identity,
                        media_type="text/plain",
                        test_run_hook_started_id=started_id,
                    )
                ),
            )


        @given("the reporting spine run-hook step passes")
        def reporting_spine_run_hook_step_passes():
            pass


        @pytest.hookimpl(hookwrapper=True, trylast=True)
        def pytest_sessionstart(session):
            yield
            _attach_to_run_hook(session.config, "BEFORE_TEST_RUN")


        @pytest.hookimpl(hookwrapper=True, trylast=True)
        def pytest_sessionfinish(session, exitstatus):
            outcome = yield
            _attach_to_run_hook(session.config, "AFTER_TEST_RUN")
            outcome.force_exception(RuntimeError("reporting spine after-session hook sentinel"))
        '''
    )
    (consumer.path / "conftest.py").write_text(template, encoding="utf-8")


@then(
    re.compile(
        r'consumer reporting-spine artifacts "(?P<messages_path>[^"]+)" and "(?P<observer_path>[^"]+)" '
        r'should preserve the ordered before and failed after run-hook lifecycle for protocol "(?P<protocol_version>[0-9.]+)"'
    )
)
def consumer_reporting_spine_preserves_run_hook_lifecycle(
    messages_path: str,
    observer_path: str,
    protocol_version: str,
    consumer: ConsumerProject,
) -> None:
    envelopes = _assert_reporting_spine_fanout(messages_path, observer_path, consumer)
    meta = [envelope["meta"] for envelope in envelopes if isinstance(envelope.get("meta"), dict)]
    assert len(meta) == 1 and meta[0].get("protocolVersion") == protocol_version, meta

    def events(kind: str) -> list[dict[str, Any]]:
        found = [envelope[kind] for envelope in envelopes if isinstance(envelope.get(kind), dict)]
        assert found, f"expected {kind} events in the reporting-spine stream"
        return found

    run_started = events("testRunStarted")
    run_finished = events("testRunFinished")
    assert len(run_started) == len(run_finished) == 1, (run_started, run_finished)
    run_id = run_started[0].get("id")
    assert isinstance(run_id, str) and run_id, run_started[0]
    assert run_finished[0].get("testRunStartedId") == run_id, run_finished[0]
    assert run_finished[0].get("success") is False, run_finished[0]
    assert envelopes[-1].get("testRunFinished") == run_finished[0], "testRunFinished must close the stream"

    hooks = {
        hook.get("type"): hook
        for envelope in envelopes
        if isinstance((hook := envelope.get("hook")), dict)
        and hook.get("type") in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}
    }
    assert set(hooks) == {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}, hooks
    hook_definition_indexes = {
        hook_type: next(
            index
            for index, envelope in enumerate(envelopes)
            if envelope.get("hook", {}).get("id") == hook["id"]
        )
        for hook_type, hook in hooks.items()
    }
    for hook_type, hook in hooks.items():
        source_reference = hook.get("sourceReference")
        assert isinstance(source_reference, dict), (hook_type, hook)
        assert isinstance(source_reference.get("uri"), str) and source_reference["uri"], source_reference
        location = source_reference.get("location")
        assert isinstance(location, dict) and isinstance(location.get("line"), int) and location["line"] > 0, (
            hook_type,
            source_reference,
        )

    started_events = events("testRunHookStarted")
    finished_events = events("testRunHookFinished")
    starts_by_type: dict[str, dict[str, Any]] = {}
    start_indexes: dict[str, int] = {}
    for index, envelope in enumerate(envelopes):
        started = envelope.get("testRunHookStarted")
        if not isinstance(started, dict):
            continue
        hook = next(
            (definition for definition in hooks.values() if definition.get("id") == started.get("hookId")), None
        )
        assert hook is not None, started
        hook_type = hook["type"]
        assert hook_type not in starts_by_type, (hook_type, starts_by_type, started)
        assert started.get("testRunStartedId") == run_id, started
        assert isinstance(started.get("id"), str) and started["id"], started
        starts_by_type[hook_type] = started
        start_indexes[hook_type] = index
        assert hook_definition_indexes[hook_type] < index, (hook_type, hook_definition_indexes[hook_type], index)
    assert set(starts_by_type) == {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}, started_events

    finishes_by_start: dict[str, dict[str, Any]] = {}
    finish_indexes: dict[str, int] = {}
    for index, envelope in enumerate(envelopes):
        finished = envelope.get("testRunHookFinished")
        if not isinstance(finished, dict):
            continue
        started_id = finished.get("testRunHookStartedId")
        assert started_id in {event.get("id") for event in starts_by_type.values()}, finished
        assert started_id not in finishes_by_start, (started_id, finished)
        finishes_by_start[started_id] = finished
        finish_indexes[started_id] = index
    assert len(finished_events) == len(finishes_by_start) == 2, finished_events

    attachments = [
        (index, envelope["attachment"])
        for index, envelope in enumerate(envelopes)
        if isinstance(envelope.get("attachment"), dict)
        and envelope["attachment"].get("body") in {
            "reporting-spine-before-test-run-attachment",
            "reporting-spine-after-test-run-attachment",
        }
    ]
    assert len(attachments) == 2, attachments
    attachment_indexes: dict[str, int] = {}
    for index, attachment in attachments:
        hook_type = "BEFORE_TEST_RUN" if "before" in attachment["body"] else "AFTER_TEST_RUN"
        started = starts_by_type[hook_type]
        assert attachment.get("testRunHookStartedId") == started["id"], (hook_type, attachment, started)
        attachment_indexes[hook_type] = index

    statuses: dict[str, str] = {}
    for hook_type, started in starts_by_type.items():
        finished = finishes_by_start[started["id"]]
        result = finished.get("result")
        assert isinstance(result, dict), (hook_type, finished)
        statuses[hook_type] = result.get("status")
        assert finish_indexes[finished["testRunHookStartedId"]] > start_indexes[hook_type]
        assert (
            start_indexes[hook_type]
            < attachment_indexes[hook_type]
            < finish_indexes[finished["testRunHookStartedId"]]
        )
    assert statuses == {"BEFORE_TEST_RUN": "PASSED", "AFTER_TEST_RUN": "FAILED"}, statuses

    failed_result = finishes_by_start[starts_by_type["AFTER_TEST_RUN"]["id"]]["result"]
    exception = failed_result.get("exception")
    failure_evidence = "\n".join(
        value
        for value in (
            failed_result.get("message"),
            exception.get("message") if isinstance(exception, dict) else None,
        )
        if isinstance(value, str)
    )
    assert "reporting spine after-session hook sentinel" in failure_evidence, failed_result

    scenario_starts = [
        index for index, envelope in enumerate(envelopes) if isinstance(envelope.get("testCaseStarted"), dict)
    ]
    scenario_finishes = [
        index for index, envelope in enumerate(envelopes) if isinstance(envelope.get("testCaseFinished"), dict)
    ]
    assert len(scenario_starts) == len(scenario_finishes) == 1, (scenario_starts, scenario_finishes)
    before_start = start_indexes["BEFORE_TEST_RUN"]
    after_start = start_indexes["AFTER_TEST_RUN"]
    before_finish = finish_indexes[starts_by_type["BEFORE_TEST_RUN"]["id"]]
    after_finish = finish_indexes[starts_by_type["AFTER_TEST_RUN"]["id"]]
    assert (
        envelopes.index(next(envelope for envelope in envelopes if "testRunStarted" in envelope))
        < before_start
        < before_finish
        < scenario_starts[0]
        < scenario_finishes[0]
        < after_start
        < after_finish
        < envelopes.index(next(envelope for envelope in envelopes if "testRunFinished" in envelope))
    )


@when("I run the tutorial example as its own pytest project", target_fixture="tutorial_pytest_result")
def run_tutorial_example_as_own_pytest_project() -> subprocess.CompletedProcess[str]:
    repository_root = Path(__file__).resolve().parents[2]
    tutorial_root = repository_root / "examples" / "tutorial"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        "pyproject.toml",
        "--rootdir=.",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        "-q",
        ".",
    ]
    return subprocess.run(
        command,
        cwd=tutorial_root,
        env=_consumer_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )


@then("the tutorial acceptance should pass one autoloaded scenario")
def tutorial_acceptance_passes_one_autoloaded_scenario(
    tutorial_pytest_result: subprocess.CompletedProcess[str],
) -> None:
    output = tutorial_pytest_result.stdout + tutorial_pytest_result.stderr
    assert tutorial_pytest_result.returncode == 0, (
        f"tutorial pytest exited with {tutorial_pytest_result.returncode}\n"
        f"command output:\n{output}"
    )
    assert re.search(r"(?m)^1 passed(?:,|\s|$)", output), output
