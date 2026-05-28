.PHONY: check-shell develop sync tox-list test test-all test-platform-native test-platform-linux \
	test-platform-windows test-platform-macos test-unit test-integration test-contract test-e2e \
	test-compat test-perf test-external test-external-subprocess-output test-external-xdist-html \
	test-external-xdist-message test-external-remote-local test-external-remote-ssh test-external-support \
	test-external-docker-build test-slow test-docker test-docker-linux test-docker-windows test-windows test-posix \
	env-check env-check-tox env-check-powershell env-check-wsl2 env-check-docker env-check-docker-linux \
	env-check-docker-windows env-check-windows env-check-browser validate-test-all-backends env-install env-install-docker \
	env-install-windows env-install-browser pre-commit coverage coveralls build dist-check release-check \
	clean compat-list compat-check validate-headings features-docs render-formatters local-pr-gate \
	messages-audit render-tox-reports render-tox-reports-run sync-message-schemas \
	tox env-install-npm check-message-schemas validate-github-actions

UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(UNAME_S),Windows)
  $(error ERROR: make requires Git Bash on Windows. Run from Git Bash terminal.)
endif

IS_WINDOWS_HOST := $(if $(filter MINGW% MSYS% CYGWIN%,$(UNAME_S)),1,0)
WINDOWS_TOX_BACKEND_COMMAND ?=

ifneq (,$(filter MINGW% MSYS% CYGWIN%,$(UNAME_S)))
  DETECTED_SH := $(shell command -v sh.exe 2>/dev/null)
  ifeq ($(DETECTED_SH),)
    SHELL := C:/PROGRA~1/Git/bin/sh.exe
  else
    SHELL := $(DETECTED_SH)
  endif
  ifeq ($(shell command -v docker 2>/dev/null),)
    export PATH := C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)
  endif
endif

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
ifeq ($(GITHUB_ACTIONS),true)
  TOX ?= uvx --with tox-uv --with tox-gh-actions tox
else
  TOX ?= uvx --with tox-uv tox
endif
MAKE_COMMAND ?= make
TOX_LINUX_ENVS ?= py314-pytestlatest-coverage-lin,py314-pytestlatest-gherkinlatest-xdist-coverage-lin
TOX_WINDOWS_ENVS ?= py314-pytestlatest-coverage-win,py314-pytestlatest-gherkinlatest-xdist-coverage-win
TOX_MACOS_ENVS ?= py314-pytestlatest-coverage-mac,py314-pytestlatest-gherkinlatest-xdist-coverage-mac
WSL_LINUX_WORKDIR ?= /tmp/pytest-bdd-ng-wsl-linux-backend
WSL_LINUX_RSYNC_EXCLUDES ?= --delete-excluded --exclude=.git/ --exclude=.tox/ --exclude=.pytest_cache/ --exclude=.mypy_cache/ --exclude=.ruff_cache/ --exclude=.tmp/ --exclude=.venv/ --exclude=.venv-wsl/ --exclude=.win_venv/ --exclude=.windows_venv/ --exclude=.opencode/ --exclude=node_modules/ --exclude=htmlcov/ --exclude=__pycache__/ --exclude=.coverage --exclude=.coverage.* --exclude=coverage.json
TEST_ALL_ARGS ?=
TEST_NATIVE_ARGS ?=
TEST_LINUX_ARGS ?=
TEST_WINDOWS_ARGS ?=
TEST_MACOS_ARGS ?=
REPORT_ARGS ?=
FAIL_FAST ?= 0
ARTIFACT_MODE ?= collect
REPORT_MODE ?= render
export TEST_ALL_ARGS TEST_NATIVE_ARGS TEST_LINUX_ARGS TEST_WINDOWS_ARGS TEST_MACOS_ARGS REPORT_ARGS WINDOWS_TOX_BACKEND_COMMAND

ifeq ($(UNAME_S),Linux)
  TOX_NATIVE_ENVS ?= $(TOX_LINUX_ENVS)
else ifeq ($(UNAME_S),Darwin)
  TOX_NATIVE_ENVS ?= $(TOX_MACOS_ENVS)
else
  TOX_NATIVE_ENVS ?= $(TOX_WINDOWS_ENVS)
endif

develop:
	uv python install 3.14
	uv sync $(UV_SYNC_EXTRAS)

sync: develop

tox-list: env-check
	uvx --with tox-uv tox -l

test: env-check
	$(PYTEST) tests/cases -m "$(PYTEST_LOCAL_SELECTOR)"

test-all: validate-test-all-backends
	@set -e; \
	status=0; \
	echo "=== test-platform-native ($(UNAME_S)) ==="; \
	if [ "$(FAIL_FAST)" = "1" ]; then \
		$(MAKE_COMMAND) --no-print-directory test-platform-native || exit $$?; \
	else \
		$(MAKE_COMMAND) --no-print-directory test-platform-native || status=$$?; \
	fi; \
	echo "=== test-platform-linux ($(UNAME_S)) ==="; \
	if [ "$(FAIL_FAST)" = "1" ]; then \
		$(MAKE_COMMAND) --no-print-directory test-platform-linux || exit $$?; \
	else \
		$(MAKE_COMMAND) --no-print-directory test-platform-linux || status=$$?; \
	fi; \
	if [ "$(IS_WINDOWS_HOST)" != "1" ]; then \
		echo "=== test-platform-windows ($(UNAME_S)) ==="; \
		if [ "$(FAIL_FAST)" = "1" ]; then \
			$(MAKE_COMMAND) --no-print-directory test-platform-windows || exit $$?; \
		else \
			$(MAKE_COMMAND) --no-print-directory test-platform-windows || status=$$?; \
		fi; \
	fi; \
	echo "=== test-platform-macos ($(UNAME_S)) ==="; \
	if [ "$(FAIL_FAST)" = "1" ]; then \
		$(MAKE_COMMAND) --no-print-directory test-platform-macos || exit $$?; \
	else \
		$(MAKE_COMMAND) --no-print-directory test-platform-macos || status=$$?; \
	fi; \
	if [ "$(REPORT_MODE)" = "render" ]; then \
		$(MAKE_COMMAND) --no-print-directory render-tox-reports-run || status=$$?; \
	fi; \
	exit $$status

test-platform-native:
	@if [ "$(IS_WINDOWS_HOST)" = "1" ]; then \
		$(MAKE_COMMAND) --no-print-directory test-platform-windows TEST_WINDOWS_ARGS="$$TEST_NATIVE_ARGS"; \
	else \
		set -f; \
		$(MAKE_COMMAND) --no-print-directory env-check-tox; \
		$(TOX) run -e $(TOX_NATIVE_ENVS) -- $$TEST_ALL_ARGS $$TEST_NATIVE_ARGS; \
	fi

test-platform-linux:
	@if [ "$(UNAME_S)" = "Linux" ]; then \
		set -f; \
		$(MAKE_COMMAND) --no-print-directory env-check-tox; \
		$(TOX) run -e $(TOX_LINUX_ENVS) -- $$TEST_ALL_ARGS $$TEST_LINUX_ARGS; \
	elif printf '%s\n' "$(UNAME_S)" | grep -Eq '^(MINGW|MSYS|CYGWIN)'; then \
		if command -v wsl.exe >/dev/null 2>&1; then \
			$(MAKE_COMMAND) --no-print-directory env-check-wsl2; \
			WIN_PWD=$$(cygpath -w "$$PWD"); \
			POSIX_PWD=$$(cygpath -u "$$WIN_PWD"); \
			WSL_PWD=$$(printf '%s' "$$POSIX_PWD" | sed -E 's#^/([A-Za-z])/#/mnt/\L\1/#'); \
			wsl.exe sh -lc "set -e; mkdir -p \"$(WSL_LINUX_WORKDIR)\"; rsync -a --delete $(WSL_LINUX_RSYNC_EXCLUDES) \"$$WSL_PWD/\" \"$(WSL_LINUX_WORKDIR)/\"; cd \"$(WSL_LINUX_WORKDIR)\"; $(TOX) run -e $(TOX_LINUX_ENVS) -- $(TEST_ALL_ARGS) $(TEST_LINUX_ARGS); mkdir -p \"$$WSL_PWD/.tox\"; find .tox -maxdepth 1 -name '*.messages.ndjson' -exec cp {} \"$$WSL_PWD/.tox/\" \; 2>/dev/null || true"; \
		elif [ "$(FAIL_FAST)" = "1" ]; then \
			echo "ERROR: WSL2 unavailable. Run make env-install-windows."; exit 1; \
		else \
			echo "ERROR: WSL2 unavailable. Skipping Linux tox backend in ARTIFACT_MODE=$(ARTIFACT_MODE). Run make env-install-windows."; \
		fi; \
	else \
		if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
			docker run --rm -e TEST_ALL_ARGS -e TEST_LINUX_ARGS -v "$$PWD":/work -w /work python:3.14-slim sh -lc 'set -f; python -m pip install uv && $(TOX) run -e $(TOX_LINUX_ENVS) -- $$TEST_ALL_ARGS $$TEST_LINUX_ARGS'; \
		elif [ "$(FAIL_FAST)" = "1" ]; then \
			echo "ERROR: Docker unavailable for Linux tox backend. Run make env-install-docker."; exit 1; \
		else \
			echo "ERROR: Docker unavailable. Skipping Linux tox backend in ARTIFACT_MODE=$(ARTIFACT_MODE). Run make env-install-docker."; \
		fi; \
	fi

test-platform-windows:
	@if printf '%s\n' "$(UNAME_S)" | grep -Eq '^(MINGW|MSYS|CYGWIN)'; then \
		$(MAKE_COMMAND) --no-print-directory env-check-powershell; \
		powershell.exe -NoProfile -Command "Set-Location '$$(cygpath -w "$$PWD")'; $(TOX) run -e $(TOX_WINDOWS_ENVS) -- \$$env:TEST_ALL_ARGS \$$env:TEST_WINDOWS_ARGS"; \
	elif [ -n "$$WINDOWS_TOX_BACKEND_COMMAND" ]; then \
		eval "$$WINDOWS_TOX_BACKEND_COMMAND"; \
	elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
		$(MAKE_COMMAND) --no-print-directory env-check-docker-windows; \
		docker run --rm -e TEST_ALL_ARGS -e TEST_WINDOWS_ARGS -v "$$PWD":C:/work -w C:/work python:3.14-windowsservercore-ltsc2022 powershell -NoProfile -Command "python -m pip install uv; uvx --with tox-uv tox run -e $(TOX_WINDOWS_ENVS) -- \$$env:TEST_ALL_ARGS \$$env:TEST_WINDOWS_ARGS"; \
	elif [ "$(FAIL_FAST)" = "1" ]; then \
		echo "ERROR: Windows Docker or VM-like backend unavailable. Run make env-install-docker."; exit 1; \
	else \
		echo "ERROR: Windows Docker or VM-like backend unavailable. Skipping Windows tox backend in ARTIFACT_MODE=$(ARTIFACT_MODE). Run make env-install-docker."; \
	fi

test-platform-macos:
	@if [ "$(UNAME_S)" = "Darwin" ]; then \
		set -f; \
		$(MAKE_COMMAND) --no-print-directory env-check-tox; \
		$(TOX) run -e $(TOX_MACOS_ENVS) -- $$TEST_ALL_ARGS $$TEST_MACOS_ARGS; \
	elif [ "$(FAIL_FAST)" = "1" ]; then \
		echo "ERROR: macOS tox backend requires macOS host."; exit 1; \
	else \
		echo "ERROR: macOS tox backend requires macOS host. Skipping macOS tox backend in ARTIFACT_MODE=$(ARTIFACT_MODE)."; \
	fi

test-unit: env-check
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- tests/cases/unit -m unit $(PYTEST_UNIT_IGNORE)

test-integration: env-check
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- tests/cases/integration -m integration

test-contract: env-check
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- tests/cases/contract -m contract

test-e2e: env-check
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- tests/cases/e2e -m "e2e and not browser"

test-compat: env-check
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- tests/cases/compat -m compat

test-perf: env-check
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- tests/cases/perf -m perf

test-external: env-check-docker
	@$(MAKE) --no-print-directory test-external-subprocess-output
	@$(MAKE) --no-print-directory test-external-xdist-html
	@$(MAKE) --no-print-directory test-external-xdist-message
	@$(MAKE) --no-print-directory test-external-docker-build
	@$(MAKE) --no-print-directory test-external-remote-local
	@$(MAKE) --no-print-directory test-external-remote-ssh
	@$(MAKE) --no-print-directory test-external-support

test-external-subprocess-output: env-check
	$(PYTEST) tests/cases/external/e2e/test_subprocess_output_attachments.py -m external

test-external-xdist-html: env-check
	$(PYTEST) tests/cases/external/e2e/test_xdist_html_reporting.py -m external

test-external-xdist-message: env-check
	$(PYTEST) tests/cases/external/e2e/test_xdist_message_aggregation.py -m external

test-external-docker-build: env-check-docker
	docker compose -f tests/assets/docker/remote_xdist/docker-compose.yml build

test-external-remote-local: env-check
	$(PYTEST) tests/cases/external/e2e/test_xdist_remote_message_aggregation.py -m external -k "socket or via"

test-external-remote-ssh: env-check-docker
	$(PYTEST) tests/cases/external/e2e/test_xdist_remote_message_aggregation.py -m external -k ssh

test-external-support: env-check
	$(PYTEST) tests/cases/external/support -m external

test-slow: env-check
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- tests/cases -m "slow and not external and not docker"

test-docker: env-check-docker
	@$(MAKE) --no-print-directory test-docker-linux
	@$(MAKE) --no-print-directory test-docker-windows

test-docker-linux: env-check-docker
	$(TOX) run -e $(TOX_LINUX_ENVS) -- tests/cases -m "docker and not windows"

test-docker-windows: env-check-docker
	$(TOX) run -e $(TOX_WINDOWS_ENVS) -- tests/cases -m "docker and windows"

test-windows: env-check-windows
	$(TOX) run -e $(TOX_WINDOWS_ENVS) -- tests/cases -m windows; EXIT=$$?; if [ $$EXIT -ne 0 ] && [ $$EXIT -ne 5 ]; then exit $$EXIT; fi

test-posix: env-check
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- tests/cases -m posix; EXIT=$$?; if [ $$EXIT -ne 0 ] && [ $$EXIT -ne 5 ]; then exit $$EXIT; fi

check-shell:
	@true

env-check: check-shell
	@command -v uv >/dev/null || { echo "ERROR: uv missing. Run make env-install."; exit 1; }
	@uv run python -c "import pytest" >/dev/null || { echo "ERROR: pytest environment missing. Run make env-install."; exit 1; }

env-check-tox: check-shell
	@command -v uvx >/dev/null || { echo "ERROR: uvx missing. Run make env-install."; exit 1; }
	@$(TOX) --version >/dev/null || { echo "ERROR: tox unavailable. Run make env-install."; exit 1; }

env-check-powershell: check-shell
	@command -v powershell.exe >/dev/null || { echo "ERROR: PowerShell bridge missing. Run from Git Bash on Windows or install PowerShell."; exit 1; }

env-check-wsl2: check-shell
	@command -v wsl.exe >/dev/null || { echo "ERROR: WSL2 missing. Run make env-install-windows."; exit 1; }
	@wsl.exe sh -lc 'command -v uvx >/dev/null' || { echo "ERROR: WSL2 tox backend missing uvx. Install uv in WSL2, then retry."; exit 1; }
	@wsl.exe sh -lc 'command -v rsync >/dev/null' || { echo "ERROR: WSL2 tox backend missing rsync. Install rsync in WSL2, then retry."; exit 1; }

env-check-docker:
	@command -v docker >/dev/null || { echo "ERROR: docker missing. Run make env-install-docker."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon unavailable. Start Docker, then retry."; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "ERROR: Docker Compose unavailable. Run make env-install-docker."; exit 1; }

env-check-docker-linux: env-check-docker
	@true

env-check-docker-windows: env-check-docker
	@if [ -n "$$WINDOWS_TOX_BACKEND_COMMAND" ]; then \
		true; \
	else \
		docker version --format '{{.Server.Os}}' 2>/dev/null | grep -qi windows || { echo "ERROR: Windows Docker backend unavailable. Switch Docker Desktop to Windows containers or set WINDOWS_TOX_BACKEND_COMMAND."; exit 1; }; \
		docker run --rm python:3.14-windowsservercore-ltsc2022 powershell -NoProfile -Command "python -m pip --version" >/dev/null || { echo "ERROR: Windows Docker Python backend unavailable."; exit 1; }; \
	fi

validate-test-all-backends: env-check-tox
	@if [ "$(FAIL_FAST)" = "1" ]; then \
		if printf '%s\n' "$(UNAME_S)" | grep -Eq '^(MINGW|MSYS|CYGWIN)'; then \
			$(MAKE_COMMAND) --no-print-directory env-check-powershell; \
			$(MAKE_COMMAND) --no-print-directory env-check-wsl2; \
			echo "ERROR: macOS tox backend requires macOS host."; exit 1; \
		elif [ "$(UNAME_S)" = "Linux" ]; then \
			$(MAKE_COMMAND) --no-print-directory env-check-docker-windows; \
			echo "ERROR: macOS tox backend requires macOS host."; exit 1; \
		elif [ "$(UNAME_S)" = "Darwin" ]; then \
			$(MAKE_COMMAND) --no-print-directory env-check-docker-linux; \
			$(MAKE_COMMAND) --no-print-directory env-check-docker-windows; \
		fi; \
	else \
		if printf '%s\n' "$(UNAME_S)" | grep -Eq '^(MINGW|MSYS|CYGWIN)'; then \
			$(MAKE_COMMAND) --no-print-directory env-check-powershell; \
			$(MAKE_COMMAND) --no-print-directory env-check-wsl2 || echo "ERROR: WSL2 unavailable. Linux tox backend will be skipped in ARTIFACT_MODE=$(ARTIFACT_MODE). Run make env-install-windows."; \
		elif [ "$(UNAME_S)" = "Linux" ]; then \
			$(MAKE_COMMAND) --no-print-directory env-check-docker-windows || echo "ERROR: Windows Docker backend unavailable. Windows tox backend will be skipped in ARTIFACT_MODE=$(ARTIFACT_MODE). Run make env-install-docker."; \
		elif [ "$(UNAME_S)" = "Darwin" ]; then \
			$(MAKE_COMMAND) --no-print-directory env-check-docker-linux || echo "ERROR: Linux Docker backend unavailable. Linux tox backend will be skipped in ARTIFACT_MODE=$(ARTIFACT_MODE). Run make env-install-docker."; \
			$(MAKE_COMMAND) --no-print-directory env-check-docker-windows || echo "ERROR: Windows Docker backend unavailable. Windows tox backend will be skipped in ARTIFACT_MODE=$(ARTIFACT_MODE). Run make env-install-docker."; \
		fi; \
		if ! command -v docker >/dev/null 2>&1; then \
			echo "ERROR: Docker unavailable. Non-native Docker tox backends will be skipped in ARTIFACT_MODE=$(ARTIFACT_MODE). Run make env-install-docker."; \
		fi; \
	fi

env-check-windows: env-check
	@if [ "$$(uname -s 2>/dev/null)" = "Linux" ]; then \
		command -v wsl.exe >/dev/null || { echo "ERROR: Windows bridge missing. Run make env-install-windows."; exit 1; }; \
	else \
		uv run python -c "import platform, sys; sys.exit(0 if platform.system() == 'Windows' else 1)" || { echo "ERROR: Windows target requires Windows host or WSL bridge."; exit 1; }; \
	fi

env-check-browser:
	@uv run python -c "import playwright" >/dev/null 2>&1 || { echo "ERROR: Playwright package missing. Run make env-install-browser."; exit 1; }
	@uv run python -m playwright --version >/dev/null 2>&1 || { echo "ERROR: Playwright CLI unavailable. Run make env-install-browser."; exit 1; }

env-install:
	uv python install 3.14
	uv sync $(UV_SYNC_EXTRAS)

env-install-docker:
	docker compose build

env-install-windows:
	@echo "Install or enable WSL2/Windows bridge support, then run make env-check-windows."

env-install-browser:
	uv sync $(UV_SYNC_EXTRAS) --extra test-playwright
	uv run python -m playwright install

compat-list: env-check
	uv run compatibility_matrix --list --compatible-only

compat-check: env-check
	uv run compatibility_matrix --python $(PYTHON_FACTOR) --pytest $(PYTEST_FACTOR)

pre-commit: env-check
	uvx pre-commit run --all-files

validate-headings: env-check
	uv run python -m pytest_bdd.script.validate_feature_headings --root-path $(FEATURES_ROOT)

features-docs: env-check
	uv run bdd_tree_to_rst $(FEATURES_ROOT) $(FEATURE_DOCS_OUTPUT)

render-formatters: env-check
	uv run render_cucumber_formatters --messages-ndjson $(MESSAGES_NDJSON) $(FORMATTER_ARGS)

coverage: env-check
	uv run coverage run --source=pytest_bdd -m pytest tests/cases
	uv run coverage report -m

coveralls: coverage
	uv run coveralls

build: env-check
	rm -rf ./dist
	uvx --with build python -m build

dist-check: build
	uvx --with twine twine check dist/*

release-check: dist-check

local-pr-gate: env-check
	@command -v rg >/dev/null 2>&1 || { echo "ERROR: ripgrep (rg) is required for local-pr-gate. Install: https://github.com/BurntSushi/ripgrep"; exit 1; }
	@echo "[1/4] pre-commit"
	uvx pre-commit run --all-files
	@echo "[2/4] e2e tests"
	uv run python -m pytest -q tests/cases/e2e
	@echo "[3/4] workflow matrix sanity"
	@if [ -f .github/workflows/tests.yml ]; then \
		echo "ERROR: legacy workflow .github/workflows/tests.yml exists"; \
		exit 1; \
	fi
	@if rg -n '"3\.9"|"pypy3\.9"' .github/workflows/*.yml; then \
		echo "ERROR: unsupported 3.9 matrix entries found in workflows"; \
		exit 1; \
	fi
	@echo "[4/4] dependency marker sanity"
	@if ! rg -n '"jq;platform_system!=\x27Windows\x27"' pyproject.toml >/dev/null; then \
		echo "ERROR: jq dependency marker for Windows exclusion is missing in pyproject.toml"; \
		exit 1; \
	fi
	@echo "local_pr_gate: PASS"

messages-audit: env-check
	bash scripts/run_messages_coverage_audit.sh

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

sync-message-schemas: env-check
	uv run python -m pytest_bdd.script.sync_messages_contract_schemas

tox: env-check-tox
	$(TOX)

env-install-npm:
	npm install --no-save @cucumber/html-formatter cucumber-html-reporter
	npm list

check-message-schemas: env-check
	uv run python -m pytest_bdd.script.sync_messages_contract_schemas --check

validate-github-actions: check-shell
	@command -v act >/dev/null || { echo "ERROR: act missing. Install act: https://nektosact.com/installation/"; exit 1; }
	act --validate

clean:
	-rm -rf .venv ./dist $(TOX_HTML_REPORT_DIR) .tox/*.messages.ndjson
