# Phase 12: restructure-test-suite-into-semantic-groups - Pattern Map

**Mapped:** 2026-05-19
**Files analyzed:** 14 file families
**Analogs found:** 14 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tests/cases/unit/**` | test | request-response | `tests/unit/test_group_ordering.py` | exact |
| `tests/cases/integration/**` | test | request-response | `tests/feature/test_steps.py`, `tests/hook/**` | role-match |
| `tests/cases/contract/**` | test | file-I/O/transform | `tests/contract/test_formatter_golden_parity.py` | exact |
| `tests/cases/e2e/**` | test | event-driven/request-response | `tests/e2e/test_cucumber_formatters_feature.py` | role-match |
| `tests/cases/compat/**` | test | transform/config | `tests/compatibility/test_existing_support_regression.py` | exact |
| `tests/cases/perf/**` | test | batch | `scripts/benchmark-before-after.ps1` and slow existing tests | partial |
| `tests/cases/external/**` | test | external/process I/O | `tests/e2e/test_xdist_remote_message_aggregation.py` | exact |
| `tests/assets/**` | fixture asset | file-I/O | `tests/e2e/fixtures/remote_xdist/**`, `tests/fixtures/**` | role-match |
| `src/pytest_bdd/testing/cucumber_formatters.py` | utility | process I/O/transform | `tests/support/cucumber_formatters.py` | exact |
| `src/pytest_bdd/testing/docker.py` | utility | external/process I/O | `tests/support/docker.py` | exact |
| `src/pytest_bdd/testing/docker_cluster.py` | utility | external/process I/O | `tests/support/docker_cluster.py` | exact |
| `pyproject.toml` | config | transform | `[tool.pytest.ini_options]` in `pyproject.toml` | exact |
| `Makefile` | config | batch/process I/O | current `Makefile` targets | role-match |
| `tox.ini` | config | batch/process I/O | current `tox.ini` env factors | exact |
| `DEVELOPMENT.rst` | docs | transform | current Testing Strategy section | exact |

## Pattern Assignments

### `tests/cases/**` semantic tree (test, request-response)

**Analog:** `tests/unit/test_group_ordering.py`

**Imports and fake object pattern** (lines 3-21):
```python
from pathlib import Path

import pytest
from attrs import frozen

from pytest_bdd.util.tests_group_ordering import (
    GroupAssignment,
    GroupConfig,
    GroupPathMapping,
    apply_group_ordering,
    apply_order_marker,
    read_group_config,
    register_group_config_options,
    resolve_group_assignment,
)

pytest_plugins = ("pytester",)
REPO_SRC = Path(__file__).parents[2] / "src"
```

**Pytester config contract pattern** (lines 421-452):
```python
pytester.makepyprojecttoml(
    """
    [tool.pytest.ini_options]
    addopts = "--order-scope=session"
    markers = [
      "first: first test group",
      "second: second test group",
      "order: execution ordering marker from pytest-order",
    ]
    test_group_order = ["first", "second"]
    test_group_default = "second"
    test_group_paths = [
      "test_first.py = first",
      "test_second.py = second",
    ]
    """,
)
pytester.makeconftest(
    f"""
    from pathlib import Path
    import sys
    import pytest

    sys.path.insert(0, {REPO_SRC.as_posix()!r})

    from pytest_bdd.util.tests_group_ordering import apply_group_ordering, register_group_config_options

    def pytest_addoption(parser):
        register_group_config_options(parser)

    def pytest_collection_modifyitems(config, items):
        apply_group_ordering(config, items)
```

**Planner note:** Wave 0 tests should copy this pytester style for `tests/cases/unit/test_test_suite_classification.py`. Assert every collected path under `tests/cases/<group>/` resolves to one canonical group. Assert no collected tests under `tests/assets/`.

### `tests/conftest.py` (hook adapter, request-response)

**Analog:** `tests/conftest.py`

**Thin adapter pattern** (lines 3-11, 16-48):
```python
import pytest

from pytest_bdd.util.temp_root import prefer_posix_temp_root
from pytest_bdd.util.tests_group_ordering import (
    apply_group_ordering,
    record_group_barrier_report,
    register_group_config_options,
    wait_for_group_barrier,
)

def pytest_addoption(parser):
    """Handle addoption."""
    register_group_config_options(parser)

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Handle collection modifyitems."""
    apply_group_ordering(config, items)

def pytest_runtest_setup(item):
    """Handle runtest setup."""
    wait_for_group_barrier(item)

def pytest_runtest_logreport(report):
    """Handle runtest logreport."""
    record_group_barrier_report(report)
```

**Planner note:** Keep grouping logic in `src/pytest_bdd/util/tests_group_ordering.py`. Do not add semantic grouping helpers under tests. Local `tests/cases/<group>/conftest.py` may hold group-local fixtures only.

### `src/pytest_bdd/util/tests_group_ordering.py` (utility, transform)

**Analog:** `src/pytest_bdd/util/tests_group_ordering.py`

**attrs config model pattern** (lines 14-24, 28-54):
```python
from attrs import frozen
from returns.maybe import Nothing

from pytest_bdd.compatibility.pytest import Mark, MarkDecorator
from pytest_bdd.compatibility.tomllib import loads as load_toml

@frozen
class GroupPathMapping:
    """Represent group path mapping state."""

    pattern: str
    group_name: str

@frozen
class GroupConfig:
    """Represent group config state."""

    groups: list[str]
    default: str
    paths: list[GroupPathMapping]
    rootpath: Path
```

**Config parse/apply pattern** (lines 92-141, 189-202):
```python
def register_group_config_options(parser: pytest.Parser) -> None:
    """Register group config options."""
    parser.addini("test_group_order", "Ordered pytest test group names; first group runs first.", type="args", default="")
    parser.addini("test_group_default", "Default pytest test group name for unresolved tests.", default="")
    parser.addini("test_group_paths", "Repo-relative path pattern to group mappings, formatted as 'pattern = group'.", type="linelist", default="")

def read_group_config(config: pytest.Config) -> GroupConfig:
    groups = _normalize_groups(_as_list(_get_ini_value(config, "test_group_order")))
    if not groups:
        warnings.warn("[test-groups] No test groups configured. Using fallback group 'default'.", stacklevel=2)
        groups = [_FALLBACK_GROUP]
    default = str(_get_ini_value(config, "test_group_default") or "")
    if default not in groups:
        warnings.warn(f"[test-groups] Default group '{default}' not found in groups. Using first group '{groups[0]}'.", stacklevel=2)
        default = groups[0]
    paths = _parse_path_mappings(_as_list(_get_ini_value(config, "test_group_paths")), groups)
    return GroupConfig(groups=groups, default=default, paths=paths, rootpath=Path(config.rootpath))

def apply_group_ordering(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Apply group ordering."""
    group_config = read_group_config(config)
    for index, group_name in enumerate(group_config.groups, start=1):
        config.addinivalue_line("markers", f"{group_name}: test group {index}")
```

**Planner note:** Update config data, not algorithm, unless Wave 0 exposes mismatch. Actual file is plural `tests_group_ordering.py`.

### `pyproject.toml` pytest config (config, transform)

**Analog:** `pyproject.toml`

**Current marker/path shape** (lines 232-271):
```toml
markers = [
  "deprecated: mark test testing deprecated API",
  "deficient: mark test with non-full coverage",
  "docker: mark tests that require Docker-backed environments",
  "instant: smallest in-process tests",
  "doc: documentation verification tests",
  "unit: fast in-memory unit tests for core modules",
  "fast: normal fast tests",
  "medium: moderate integration tests",
  "slow: expensive local tests",
  "external: tests requiring external services",
  "slow: mark tests that are intentionally excluded from short/default runs",
  "playwright: mark browser-backed acceptance tests",
  "surplus: mark test testing non-standard API",
  "technical_nonconvertible: mark technical regression tests that must remain in pytest suite",
  "xdist: mark tests that exercise pytest-xdist/distributed execution flows",
  "order: execution ordering marker from pytest-order"
]
test_group_default = "fast"
test_group_order = ["instant", "fast", "medium", "slow", "external"]
test_group_paths = [
  "tests/unit/** = instant",
  "tests/model/** = instant",
  ...
  "tests/e2e/** = external"
]
testpaths = ["tests"]
```

**Planner note:** Replace with canonical semantic groups from design: `unit`, `integration`, `contract`, `e2e`, `compat`, `perf`, `external`. Keep speed/environment as facets: `slow`, `docker`, `windows`, `posix`, `browser`. Set `testpaths = ["tests/cases"]`.

### `Makefile` test API (config, batch/process I/O)

**Analog:** `Makefile`

**Target/dependency pattern** (lines 1-30, 90-103):
```make
.PHONY: develop sync tox-list test quick-test pre-commit coverage coveralls build dist-check release-check \
	clean compat-list compat-check validate-headings features-docs render-formatters \
	local-pr-gate messages-audit render-tox-reports render-tox-reports-run sync-message-schemas

UV_SYNC_EXTRAS := --extra test --extra testtypes --extra doc-gen --extra struct-bdd
TEST_PATH ?= tests/

develop:
	uv python install 3.14
	uv sync $(UV_SYNC_EXTRAS)

test: develop
	uvx --with tox-uv tox
	$(MAKE) --no-print-directory render-tox-reports-run

quick-test: develop
	uv run pytest $(TEST_PATH) -x

render-tox-reports-run:
	@mkdir -p $(TOX_HTML_REPORT_DIR)
	@set -- $(TOX_NDJSON_GLOB); \
	if [ "$$1" = "$(TOX_NDJSON_GLOB)" ]; then \
		echo "ERROR: no tox NDJSON artifacts found. Run tox first."; \
		exit 1; \
	fi; \
```

**Planner note:** New human API must be documented Make targets only: `test`, `test-all`, `test-unit`, `test-integration`, `test-contract`, `test-e2e`, `test-compat`, `test-perf`, `test-external`, `test-slow`, `test-docker`, `test-windows`, `test-posix`, `env-check*`, `env-install*`. Keep read-only checks separate from provisioning.

### `tox.ini` matrix (config, batch/process I/O)

**Analog:** `tox.ini`

**Matrix factor pattern** (lines 1-20, 44-56, 73-88):
```ini
[tox]
requires =
    tox>=4.2
    tox-uv
env_list =
    py314-pre-commit-lin
    py314-pytest{90, latest}-mypy
    py314-pytestlatest-playwright-report
    py314-pytestlatest-xdist-remote-{socket, via, ssh}-{lin, win}
    py314-pytest{90, 84, latest}-coverage-{lin, mac, win}

[testenv]
set_env =
    COLUMNS = 80
    GIT_PYTHON_GIT_EXECUTABLE = {env:GIT_PYTHON_GIT_EXECUTABLE:git}
    coverage: _PYTEST_CMD = coverage run --append -m pytest -m "not docker"
    pypy311: _PYTEST_CMD = pytest -m "not docker"
    win: _PYTEST_WINDOWS_ARGS = -p no:cacheprovider
    xdist: _PYTEST_MORE_ARGS = -n3 -rfsxX
commands =
    {env:_PYTEST_CMD:pytest} {env:_PYTEST_WINDOWS_ARGS:} {env:_PYTEST_MORE_ARGS:} --messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson {posargs:-vvl}

[testenv:py314-pytestlatest-xdist-remote-{socket,via,ssh}-lin]
commands =
    python -m pytest -m docker -k {env:PYTEST_REMOTE_MODE:{envname}} --messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson -v
```

**Planner note:** Preserve tox as matrix engine. Update hardcoded moved paths, especially browser report path and Docker selectors. Keep `-m docker`/platform factors compatible with new semantic/environment markers.

### `src/pytest_bdd/testing/cucumber_formatters.py` (utility, process I/O/transform)

**Analog:** `tests/support/cucumber_formatters.py`

**Import and constant pattern** (lines 3-28, 29-72):
```python
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess  # noqa: S404
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest

from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog
from pytest_bdd.util.cucumber_formatters import pytest_capture_already_configured, terminal_formatter_flags_requested

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
```

**Error/coverage context pattern** (lines 75-100):
```python
def _active_coverage_controller() -> Any | None:
    try:
        import coverage
    except ImportError:
        return None
    current = getattr(getattr(coverage, "Coverage", None), "current", None)
    if not callable(current):
        return None
    return current()

@contextmanager
def _suspend_active_coverage():
    controller = _active_coverage_controller()
    if controller is None:
        yield
        return
    coverage_module = sys.modules.get("coverage")
    coverage_warning = getattr(getattr(coverage_module, "exceptions", None), "CoverageWarning", Warning)
    controller.stop()
```

**Planner note:** Move active helper and its templates into source package if shared. Update imports from `tests.support.cucumber_formatters` to `pytest_bdd.testing.cucumber_formatters`.

### `src/pytest_bdd/testing/docker.py` (utility, external/process I/O)

**Analog:** `tests/support/docker.py`

**Readiness/check pattern** (lines 21-56, 62-80, 111-140):
```python
def _resolve_tool_path(name: str) -> str | None:
    resolved = shutil.which(name)
    if resolved is not None:
        return resolved

    if os.name != "nt":
        return None
    ...
    for candidate in candidates:
        if _windows_tool_candidate_exists(candidate):
            return str(candidate)
    return None

def _alpine_wsl2_available() -> bool:
    """Detect if WSL2 Alpine dist exists by parsing ``wsl -l -v`` output."""
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        return False
    result = subprocess.run([wsl_bin, "-l", "-v"], check=False, capture_output=True)
    if result.returncode != 0:
        return False
    ...

def _wait_for_docker(backend: str, timeout: int = 60) -> bool:
    """Poll ``docker info`` (native) or ``wsl -d Alpine docker info`` (wsl2)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ...
        if result.returncode == 0:
            return True
        time.sleep(2)
    return False
```

**Planner note:** Current helper mutates in `_ensure_docker_cli_in_alpine`; split read-only env checks from explicit env-install targets. Keep `pytest.fail` only in test/harness paths, not generic check helpers unless test-target contract wants pytest failure.

### `src/pytest_bdd/testing/docker_cluster.py` (utility, external/process I/O)

**Analog:** `tests/support/docker_cluster.py`

**attrs + subprocess routing pattern** (lines 11-29, 54-100, 111-128):
```python
from attrs import define

from tests.support.docker import _resolve_tool_path

@define
class DockerTimeouts:
    """Represent docker timeouts state."""

    startup_poll: int = 60
    compose_up: int = 300
    compose_exec: int = 300

def _run_wsl_cmd(args: list[str], timeout: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        msg = "wsl executable not found"
        raise FileNotFoundError(msg)
    return subprocess.run([wsl_bin, "-d", "Alpine", "--", *command_args], check=False, capture_output=True, text=True, timeout=timeout, env=env)

class DockerClusterManager:
    def _run_docker_cmd(...):
        try:
            ...
        except subprocess.TimeoutExpired as err:
            msg = f"Docker operation '{op_name}' exceeded timeout ({timeout}s)"
            raise RuntimeError(msg) from err
```

**Planner note:** After move, internal import becomes `from pytest_bdd.testing.docker import _resolve_tool_path`. Keep explicit exceptions with messages.

### `tests/cases/e2e/**` split loaders (test, event-driven/request-response)

**Analog to replace:** `tests/e2e/test_e2e.py`

**Forbidden whole-directory loader** (lines 5-10, 24-40):
```python
from pytest_bdd import scenarios

_EXCLUDED_TAGS = {"allure", "docker", "slow", "xdist"}
_EXCLUDED_FEATURE_URI_FRAGMENTS = ("07 report/08 xdist remote network reporting.feature.md",)

def _exclude_default_bdd_features(config, feature, pickle):  # noqa: ARG001
    feature_uri = str(getattr(feature, "uri", "")).lower()
    ...
    return (... and tag_names.isdisjoint(_EXCLUDED_TAGS))

test = scenarios(".", filter_=_exclude_default_bdd_features)
```

**Analog to copy:** `tests/e2e/test_cucumber_formatters_feature.py`

**Owned feature-file loader** (lines 13-24):
```python
from pytest_bdd import given, parsers, scenarios, then, when
from tests.support.cucumber_formatters import (
    assert_pytest_terminal_reporter_suppressed,
    build_sample_suite,
    install_fake_node,
    read_fake_formatter_telemetry,
    requests_terminal_formatter_output,
    run_pytest_via_real_entrypoint,
)

test = scenarios("../tests/e2e/_cucumber_formatters.feature")
```

**Planner note:** Split `test_e2e.py` into per-feature or per-topic modules. Forbid `scenarios(".")`. Prefer `Path(__file__).with_name(...)` for moved feature assets.

### `tests/assets/**` passive files (fixture asset, file-I/O)

**Analog:** `tests/e2e/fixtures/remote_xdist/docker-compose.yml`

**Path-coupled Docker asset pattern** (lines 1-17, 25-47):
```yaml
services:
  controller:
    image: pytest-bdd-remote-xdist-controller:local
    build:
      context: ../../../..
      dockerfile: tests/e2e/fixtures/remote_xdist/controller.Dockerfile
    entrypoint: ["sleep", "infinity"]
    environment:
      PYTEST_REMOTE_MODE: ${PYTEST_REMOTE_MODE:-socket}
      REPORT_PATH: /artifacts/${REPORT_NAME}

  proxy:
    image: pytest-bdd-remote-xdist-worker:local
    build:
      context: ../../../..
      dockerfile: tests/e2e/fixtures/remote_xdist/worker.Dockerfile
```

**Planner note:** Move passive Docker files under `tests/assets/docker/remote_xdist`. Update `context`, `dockerfile`, Dockerfile `cp`, and entrypoint paths together.

### `tests/cases/contract/**` golden/contracts (test, file-I/O/transform)

**Analog:** `tests/contract/test_formatter_golden_parity.py`

**Golden fixture pattern** (lines 12-18, 54-63, 66-82):
```python
from pytest_bdd.script.render_cucumber_formatters import main
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog
from tests.support.cucumber_formatters import install_fake_node

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "cucumber_formatter_golden.json"

def _golden() -> dict[str, dict[str, str]]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

def test_formatter_catalog_covers_all_golden_formatter_plugins() -> None:
    catalog_names = {plugin.formatter for plugin in FormatterPluginCatalog.discover().plugins}
    assert catalog_names == EXPECTED_FORMATTERS
    assert set(_golden()["stdout"]) | set(_golden()["file"]) == EXPECTED_FORMATTERS

@pytest.mark.parametrize("formatter_name", CONSOLE_FORMATTERS)
def test_console_formatter_output_matches_golden(...):
    install_fake_node(monkeypatch, tmp_path, preinstalled_packages=FAKE_FORMATTER_PACKAGES)
    ...
    assert _normalize_output(captured.out, tmp_path) == _golden()["stdout"][formatter_name]
```

**Planner note:** Move golden JSON under `tests/assets/golden/`. Update `REPO_ROOT` parent depth if test path changes.

### `scripts/run_messages_coverage_audit.sh` (script, batch/file-I/O)

**Analog:** `scripts/run_messages_coverage_audit.sh`

**Path-coupled script pattern** (lines 9-18, 36-64):
```bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUDIT_DIR="${ROOT_DIR}/.tmp/messages-coverage-audit"
MESSAGES_FILE="${AUDIT_DIR}/messages-runtime.ndjson"

cd "${ROOT_DIR}"
export PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1

run_message_capture() {
  uv run --with pytest -m pytest \
    "$1" -q \
    -p no:pytest-bdd-gherkin-message-reporter \
    -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
    --messages-ndjson "${MESSAGES_FILE}"
}

run_message_capture tests/messages_coverage/test_mandatory_attachments.py
run_expected_failure_capture tests/messages_coverage/probes/test_failing_step_runtime.py
```

**Planner note:** Update moved message coverage paths. Keep `set -euo pipefail`.

### `DEVELOPMENT.rst` docs (docs, transform)

**Analog:** `DEVELOPMENT.rst`

**Current section to replace** (lines 193-226):
```rst
Testing Strategy
----------------

pytest-bdd-ng uses a four-tier testing approach:

Unit Tests (``tests/unit/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fast, isolated tests for core modules. Marked with ``@pytest.mark.unit``.
...

E2E/BDD Tests (``tests/e2e/`` + ``features/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Executable BDD specifications written as ``.feature.md`` files in ``features/NN Topic/``.
Step definitions live in ``tests/e2e/conftest.py``. The test entry point
``tests/e2e/test_e2e.py`` runs ``scenarios(".", ...)`` against the entire
``features/`` directory.
```

**Planner note:** Replace legacy path docs. Must mention semantic groups, speed/environment facets, Makefile API, read-only env checks, explicit provisioning, and no whole-directory E2E loaders.

## Shared Patterns

### Semantic Grouping
**Source:** `src/pytest_bdd/util/tests_group_ordering.py`, `pyproject.toml`
**Apply to:** `pyproject.toml`, Wave 0 classification tests, `tests/conftest.py`

Use path-driven group assignment. Do not hardcode non-group marker ignore lists. Canonical groups: `unit`, `integration`, `contract`, `e2e`, `compat`, `perf`, `external`.

### Thin Pytest Adapter
**Source:** `tests/conftest.py`
**Apply to:** `tests/conftest.py`, group-local conftests

Keep hook adapter thin. Source logic lives under `src/pytest_bdd/util/` or `src/pytest_bdd/testing/`.

### Active Helper Move
**Source:** `tests/support/cucumber_formatters.py`, `tests/support/docker.py`, `tests/support/docker_cluster.py`
**Apply to:** `src/pytest_bdd/testing/**`, imports in tests

Move reusable active helpers into `src/pytest_bdd/testing/`. Preserve `attrs`, explicit exceptions, `subprocess.run(..., check=False, capture_output=True, text=True)` patterns. Update patch targets in tests from `tests.support.*` to `pytest_bdd.testing.*`.

### Passive Asset Boundary
**Source:** `tests/e2e/fixtures/remote_xdist/**`, `tests/fixtures/**`
**Apply to:** `tests/assets/**`

Only passive data goes under `tests/assets/`: fixtures, templates, golden files, Docker assets, feature-document fixtures. No collected `test_*.py` files there.

### Make/Tox Contract
**Source:** `Makefile`, `tox.ini`
**Apply to:** Makefile targets, tox commands, docs

Make is human API. Tox remains matrix engine. Environment checks must be read-only; provisioning uses `env-install-*`.

### E2E Loader Shape
**Source:** `tests/e2e/test_cucumber_formatters_feature.py`
**Apply to:** `tests/cases/e2e/**`

Use file-owned `scenarios("specific.feature")` or `Path(__file__).with_name(...)`. Do not use `scenarios(".")`.

## No Analog Found

None. New structure has direct analogs in current tests, config, support helpers, or docs.

## Metadata

**Analog search scope:** `tests/`, `src/pytest_bdd/`, `pyproject.toml`, `tox.ini`, `Makefile`, `scripts/`, `docs/`
**Files scanned:** `rg` across source/config/docs plus targeted reads of 12 analog files
**Pattern extraction date:** 2026-05-19
