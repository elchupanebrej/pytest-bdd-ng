# Phase 15: cross-platform-test-suite-entrypoint-makefile-mingw-sh - Pattern Map

**Mapped:** 2026-05-23
**Files analyzed:** 3 new/modified files
**Analogs found:** 3 / 3

## Scope Note

`15-CONTEXT.md` and plans `15-01` / `15-02` scope this phase to `Makefile` and `DEVELOPMENT.rst`.
`15-SPEC.md` expands scope to tox-backed orchestration and may require `tox.ini` changes.
Planner must choose source of truth before execution. Pattern map includes both surfaces.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `Makefile` | config / route | request-response, batch, shell orchestration | `Makefile` | exact |
| `DEVELOPMENT.rst` | documentation | transform / human workflow | `DEVELOPMENT.rst` | exact |
| `tox.ini` | config | batch test matrix | `tox.ini` | exact |

## Pattern Assignments

### `Makefile` (config / route, request-response + batch shell orchestration)

**Analog:** `Makefile`

**Target declaration pattern** (lines 1-8):
```makefile
.PHONY: check-shell develop sync tox-list test test-all test-unit test-integration test-contract test-e2e \
	test-compat test-perf test-external test-external-subprocess-output test-external-xdist-html \
	test-external-xdist-message test-external-remote-local test-external-remote-ssh test-external-support \
	test-external-docker-build test-slow test-docker test-docker-linux test-docker-windows test-windows test-posix \
	env-check env-check-docker env-check-windows env-check-browser env-install env-install-docker \
	env-install-windows env-install-browser pre-commit coverage coveralls build dist-check release-check \
	clean compat-list compat-check validate-headings features-docs render-formatters local-pr-gate \
	messages-audit render-tox-reports render-tox-reports-run sync-message-schemas
```

**OS detection / guard pattern** (lines 10-14):
```makefile
UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(UNAME_S),Windows)
  $(error ERROR: make requires Git Bash on Windows. Run from Git Bash terminal.)
endif
```

**Platform routing pattern** (lines 16-25):
```makefile
ifeq ($(UNAME_S),Linux)
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix
  DOCKER_TARGETS := test-docker-windows test-external
else ifeq ($(UNAME_S),Darwin)
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix
  DOCKER_TARGETS := test-docker-linux test-docker-windows test-external
else
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix test-windows
  DOCKER_TARGETS := test-docker-linux test-external
endif
```

**Command variable pattern** (lines 27-38):
```makefile
UV_SYNC_EXTRAS := --extra test --extra testtypes --extra doc-gen --extra struct-bdd
PYTHON_FACTOR ?= 314
PYTEST_FACTOR ?= latest
FEATURES_ROOT ?= features
FEATURE_DOCS_OUTPUT ?= docs/features
MESSAGES_NDJSON ?= .tmp/messages.ndjson
FORMATTER_ARGS ?= --cucumber-summary
TOX_NDJSON_GLOB ?= .tox/*.messages.ndjson
TOX_HTML_REPORT_DIR ?= .tmp/tox-reports
PYTEST ?= uv run $(UV_SYNC_EXTRAS) python -m pytest
PYTEST_LOCAL_SELECTOR ?= not slow and not docker and not windows and not browser and not external
PYTEST_UNIT_IGNORE ?= --ignore=tests/cases/unit/unit/test_dead_code.py
```

**Full-run orchestration pattern** (lines 52-57):
```makefile
test-all: env-check
	@echo "=== Native targets ($(UNAME_S)) ==="
	@$(MAKE) --no-print-directory $(NATIVE_TARGETS)
	@echo "=== Docker targets ==="
	@-$(MAKE) --no-print-directory $(DOCKER_TARGETS)
	@-$(MAKE) --no-print-directory render-tox-reports-run
```

**Thin test target pattern** (lines 59-75):
```makefile
test-unit: env-check
	$(PYTEST) tests/cases/unit -m unit $(PYTEST_UNIT_IGNORE)

test-integration: env-check
	$(PYTEST) tests/cases/integration -m integration

test-contract: env-check
	$(PYTEST) tests/cases/contract -m contract

test-e2e: env-check
	$(PYTEST) tests/cases/e2e -m "e2e and not browser"

test-compat: env-check
	$(PYTEST) tests/cases/compat -m compat

test-perf: env-check
	$(PYTEST) tests/cases/perf -m perf
```

**Docker split / meta-target pattern** (lines 110-118):
```makefile
test-docker: env-check-docker
	@$(MAKE) --no-print-directory test-docker-linux
	@$(MAKE) --no-print-directory test-docker-windows

test-docker-linux: env-check-docker
	$(PYTEST) tests/cases -m "docker and not windows"

test-docker-windows: env-check-docker
	$(PYTEST) tests/cases -m "docker and windows"
```

**Exit-code-5 handling pattern** (lines 120-124):
```makefile
test-windows: env-check-windows
	$(PYTEST) tests/cases -m windows; EXIT=$$?; if [ $$EXIT -ne 0 ] && [ $$EXIT -ne 5 ]; then exit $$EXIT; fi

test-posix: env-check
	$(PYTEST) tests/cases -m posix; EXIT=$$?; if [ $$EXIT -ne 0 ] && [ $$EXIT -ne 5 ]; then exit $$EXIT; fi
```

**Validation / error handling pattern** (lines 126-143):
```makefile
check-shell:
	@true

env-check: check-shell
	@command -v uv >/dev/null || { echo "ERROR: uv missing. Run make env-install."; exit 1; }
	@uv run python -c "import pytest" >/dev/null || { echo "ERROR: pytest environment missing. Run make env-install."; exit 1; }

env-check-docker:
	@command -v docker >/dev/null || { echo "ERROR: docker missing. Run make env-install-docker."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon unavailable. Start Docker, then retry."; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "ERROR: Docker Compose unavailable. Run make env-install-docker."; exit 1; }

env-check-windows: env-check
	@if [ "$$(uname -s 2>/dev/null)" = "Linux" ]; then \
		command -v wsl.exe >/dev/null || { echo "ERROR: Windows bridge missing. Run make env-install-windows."; exit 1; }; \
	else \
		uv run python -c "import platform, sys; sys.exit(0 if platform.system() == 'Windows' else 1)" || { echo "ERROR: Windows target requires Windows host or WSL bridge."; exit 1; }; \
	fi
```

**Artifact rendering pattern** (lines 222-235):
```makefile
render-tox-reports: env-check render-tox-reports-run

render-tox-reports-run:
	@mkdir -p $(TOX_HTML_REPORT_DIR)
	@set -- $(TOX_NDJSON_GLOB); \
	if [ "$$1" = "$(TOX_NDJSON_GLOB)" ]; then \
		echo "ERROR: no tox NDJSON artifacts found. Run tox first."; \
		exit 1; \
	fi; \
	for ndjson in "$$@"; do \
		envname=$$(basename "$$ndjson" .messages.ndjson); \
		echo "Rendering $$envname -> $(TOX_HTML_REPORT_DIR)/$$envname.json"; \
		uv run render_cucumber_formatters --messages-ndjson "$$ndjson" --cucumber-json "$(TOX_HTML_REPORT_DIR)/$$envname.json"; \
	done
```

---

### `DEVELOPMENT.rst` (documentation, transform / human workflow)

**Analog:** `DEVELOPMENT.rst`

**Cross-platform section pattern** (lines 22-28):
```rst
Cross-Platform Setup
--------------------

The test suite supports cross-platform execution via Make. Each platform
requires specific tools. Use the table below to verify your environment.

.. list-table:: Cross-Platform Prerequisites
```

**Windows Git Bash warning pattern** (lines 48-52):
```rst
.. note::

   On Windows, all ``make`` commands must be run from Git Bash terminal.
   Running ``make`` from ``cmd.exe`` or PowerShell produces an error with
   instructions to switch to Git Bash.
```

**Canonical command pattern** (lines 54-62):
```rst
Canonical Make Commands
~~~~~~~~~~~~~~~~~~~~~~~

``make test``
  Default feasible test suite for the current machine (no surprise provisioning).

``make test-all``
  Full suite with cross-platform routing: native tests for your OS plus
  Docker-backed tests for non-native platforms (Docker unavailable is non-fatal).
```

**Makefile API docs pattern** (lines 330-354):
```rst
Makefile Test API
~~~~~~~~~~~~~~~~~

Make is the human entrypoint for running tests. Tox remains the matrix engine.

.. code-block:: bash

   # Default suite: all feasible tests for current machine (no surprise provisioning)
   make test

   # Full suite: native + Docker-backed non-native routes where available
   make test-all

   # Core semantic groups
   make test-unit
   make test-integration
   make test-contract
   make test-e2e
   make test-compat
   make test-perf
   make test-external

   # Docker-backed tests (split by platform)
   make test-docker-linux
   make test-docker-windows
```

**Tox docs pattern** (lines 478-509):
```rst
Running Tests
-------------

Make is the recommended human entrypoint for running tests. Tox remains the
matrix engine for full Python/pytest version coverage.

To list the supported tox environments:

.. code-block:: bash

   uvx --with tox-uv tox -l

To run the full test suite and render one HTML report per pytest-based tox environment:

.. code-block:: bash

   make test

If you run tox directly, it will write one NDJSON artifact per pytest-based environment:

.. code-block:: bash

   uvx --with tox-uv tox

Render HTML reports from the collected tox NDJSON artifacts:

.. code-block:: bash

   make render-tox-reports

By default, tox writes NDJSON artifacts as ``.tox/<envname>.messages.ndjson`` and the
Makefile renders JSON reports to ``.tmp/tox-reports/<envname>.json``.
```

---

### `tox.ini` (config, batch test matrix)

**Analog:** `tox.ini`

**Matrix env list pattern** (lines 1-20):
```ini
[tox]
requires =
    tox>=4.2
    tox-uv
env_list =
    py314-pre-commit-lin
    py314-pytest{90, latest}-mypy
    py314-pytestlatest-playwright-report
    py314-pytestlatest-mypy-messages
    py314-pytestlatest-xdist-remote-{socket, via, ssh}-{lin, win}
    py314-pytest{90, 84, latest}-coverage-{lin, mac, win}
    py314-pytestlatest-gherkin{33, latest}-xdist-coverage-{lin, win, mac}
    py313-pytest{83, 82, 81, 80, latest}-coverage-{lin, mac, win}
    py312-pytest{74, 73, 72, 71, 70}-coverage-{lin, mac, win}
    pypy311-pytestlatest-coverage-{win, mac, lin}
    py{313, 312, 311, 310}-pytestlatest-mypy
    py{313, 312, 311, 310}-pytestlatest-coverage-lin
    py{py311, 313, 312, 311, 310}-pytestlatest-xdist-coverage-lin
    py{314, 313, 312, 311, 310}-ruff
distshare = {homedir}/.tox/distshare
```

**Default testenv / posargs pattern** (lines 22-56):
```ini
[testenv]
deps =
    .[build]
    .[doc-gen]
    .[struct-bdd]
    .[test]
    coverage: coverage
    gherkin33: gherkin-official~=33.0.0
    gherkinlatest: gherkin-official
    pytest70: pytest~=7.0.0
    pytest71: pytest~=7.1.0
    pytest72: pytest~=7.2.0
    pytest73: pytest~=7.3.0
    pytest74: pytest~=7.4.0
    pytest80: pytest~=8.0.0
    pytest81: pytest~=8.1.0
    pytest82: pytest~=8.2.0
    pytest83: pytest~=8.3.0
    pytest84: pytest~=8.4.0
    pytest90: pytest~=9.0.0
    pytestlatest: pytest
    xdist: pytest-xdist>=3.8
set_env =
    COLUMNS = 80
    GIT_PYTHON_GIT_EXECUTABLE = {env:GIT_PYTHON_GIT_EXECUTABLE:git}
    coverage: _PYTEST_CMD = coverage run --append -m pytest -m "not docker"
    pypy311: _PYTEST_CMD = pytest -m "not docker"
    win: _PYTEST_WINDOWS_ARGS = -p no:cacheprovider
    xdist: _PYTEST_MORE_ARGS = -n3 -rfsxX
commands =
    {env:_PYTEST_CMD:pytest} {env:_PYTEST_WINDOWS_ARGS:} {env:_PYTEST_MORE_ARGS:} --messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson {posargs:-vvl}
platform =
    lin: linux
    mac: darwin
    win: win32
```

**Specialized Docker/xdist env pattern** (lines 73-88):
```ini
[testenv:py314-pytestlatest-xdist-remote-{socket,via,ssh}-lin]
set_env =
    socket: PYTEST_REMOTE_MODE = socket
    ssh: PYTEST_REMOTE_MODE = ssh
    via: PYTEST_REMOTE_MODE = via
commands =
    python -m pytest -m docker -k {env:PYTEST_REMOTE_MODE:{envname}} --messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson -v

[testenv:py314-pytestlatest-xdist-remote-{socket,via,ssh}-win]
set_env =
    socket: PYTEST_REMOTE_MODE = socket
    ssh: PYTEST_REMOTE_MODE = ssh
    via: PYTEST_REMOTE_MODE = via
commands =
    python -m pytest {env:_PYTEST_WINDOWS_ARGS:} -m docker -k {env:PYTEST_REMOTE_MODE:{envname}} --messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson -v
platform = win: win32
```

**Lint env pattern** (lines 90-111):
```ini
[testenv:py{313,314}-pre-commit]
skip_install = true
deps =
    pre-commit
commands =
    pre-commit run --all-files

[testenv:py{310,311,312,313,314}-pytest{latest,70,71,72,73,74,80,81,82,83,84,90}-mypy]
deps =
    .[testtypes]
commands =
    python -m mypy --config-file pyproject.toml

[testenv:py{310,311,312,313,314}-ruff]
deps =
    .[testtypes]
    ruff
commands =
    ruff check src tests docs
    ruff format --check src tests docs
allowlist_externals =
    ruff
```

## Shared Patterns

### Environment Checks

**Source:** `Makefile` lines 129-143
**Apply to:** `Makefile` preflight targets, backend validation targets
```makefile
env-check: check-shell
	@command -v uv >/dev/null || { echo "ERROR: uv missing. Run make env-install."; exit 1; }
	@uv run python -c "import pytest" >/dev/null || { echo "ERROR: pytest environment missing. Run make env-install."; exit 1; }

env-check-docker:
	@command -v docker >/dev/null || { echo "ERROR: docker missing. Run make env-install-docker."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon unavailable. Start Docker, then retry."; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "ERROR: Docker Compose unavailable. Run make env-install-docker."; exit 1; }
```

### Optional Subwork

**Source:** `Makefile` lines 52-57
**Apply to:** Docker/report/artifact collection targets under old CONTEXT scope
```makefile
test-all: env-check
	@echo "=== Native targets ($(UNAME_S)) ==="
	@$(MAKE) --no-print-directory $(NATIVE_TARGETS)
	@echo "=== Docker targets ==="
	@-$(MAKE) --no-print-directory $(DOCKER_TARGETS)
	@-$(MAKE) --no-print-directory render-tox-reports-run
```

### Marker / Group Names

**Source:** `pyproject.toml` lines 235-258
**Apply to:** Makefile marker selectors and tox posargs. Do not invent hardcoded marker ignore lists.
```toml
markers = [
  "unit: pure in-process module tests",
  "integration: local plugin, parser, runtime, pytester, and subprocess-light flows",
  "contract: golden files, boundary contracts, schema contracts, and formatter parity contracts",
  "e2e: full executable user workflows and feature-doc driven acceptance tests",
]
test_group_default = "integration"
test_group_order = ["unit", "integration", "contract", "e2e", "compat", "perf", "external"]
test_group_paths = [
  "tests/cases/unit/** = unit",
  "tests/cases/integration/** = integration",
  "tests/cases/contract/** = contract",
  "tests/cases/e2e/** = e2e",
]
```

### Tox Artifact Contract

**Source:** `tox.ini` lines 51-52 and `Makefile` lines 222-235
**Apply to:** Any tox-backed Makefile target and report rendering
```ini
commands =
    {env:_PYTEST_CMD:pytest} {env:_PYTEST_WINDOWS_ARGS:} {env:_PYTEST_MORE_ARGS:} --messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson {posargs:-vvl}
```

```makefile
TOX_NDJSON_GLOB ?= .tox/*.messages.ndjson
TOX_HTML_REPORT_DIR ?= .tmp/tox-reports
```

## No Analog Found

None. All likely modified files have direct analogs in the current codebase.

## Metadata

**Analog search scope:** root config/docs (`Makefile`, `DEVELOPMENT.rst`, `tox.ini`, `pyproject.toml`); project skills dirs checked: `.codex/skills`, `.agents/skills`, `.opencode/skills` (none found by `rtk find`).
**Files scanned:** 4 analog/reference files plus 5 phase artifacts.
**Pattern extraction date:** 2026-05-23
