.PHONY: check-shell develop sync tox-list test test-all test-unit test-integration test-contract test-e2e \
	test-compat test-perf test-external test-slow test-docker-linux test-docker-windows test-windows test-posix \
	env-check env-check-docker env-check-windows env-check-browser env-install env-install-docker \
	env-install-windows env-install-browser pre-commit coverage coveralls build dist-check release-check \
	clean compat-list compat-check validate-headings features-docs render-formatters local-pr-gate \
	messages-audit render-tox-reports render-tox-reports-run sync-message-schemas

UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(UNAME_S),Windows)
  $(error ERROR: make requires Git Bash on Windows. Run from Git Bash terminal.)
endif

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

UV_SYNC_EXTRAS := --extra test --extra testtypes --extra doc-gen --extra struct-bdd
PYTHON_FACTOR ?= 314
PYTEST_FACTOR ?= latest
FEATURES_ROOT ?= features
FEATURE_DOCS_OUTPUT ?= docs/features
MESSAGES_NDJSON ?= .tmp/messages.ndjson
FORMATTER_ARGS ?= --cucumber-summary
TOX_NDJSON_GLOB ?= .tox/*.messages.ndjson
TOX_HTML_REPORT_DIR ?= .tmp/tox-reports
PYTEST ?= uv run python -m pytest
PYTEST_LOCAL_SELECTOR ?= not slow and not docker and not windows and not browser and not external
PYTEST_UNIT_IGNORE ?= --ignore=tests/cases/unit/unit/test_dead_code.py

develop:
	uv python install 3.14
	uv sync $(UV_SYNC_EXTRAS)

sync: develop

tox-list: env-check
	uvx --with tox-uv tox -l

test: env-check
	$(PYTEST) tests/cases -m "$(PYTEST_LOCAL_SELECTOR)"

test-all: env-check
	@echo "=== Native targets ($(UNAME_S)) ==="
	@$(MAKE) --no-print-directory $(NATIVE_TARGETS)
	@echo "=== Docker targets ==="
	@-$(MAKE) --no-print-directory $(DOCKER_TARGETS)
	@-$(MAKE) --no-print-directory render-tox-reports-run

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

test-external: env-check-docker
	$(PYTEST) tests/cases/external -m external

test-slow: env-check
	$(PYTEST) tests/cases -m "slow and not external and not docker"

test-docker-linux: env-check-docker
	$(PYTEST) tests/cases -m "docker and not windows"

test-docker-windows: env-check-docker
	$(PYTEST) tests/cases -m "docker and windows"

test-windows: env-check-windows
	$(PYTEST) tests/cases -m windows; EXIT=$$?; if [ $$EXIT -ne 0 ] && [ $$EXIT -ne 5 ]; then exit $$EXIT; fi

test-posix: env-check
	$(PYTEST) tests/cases -m posix; EXIT=$$?; if [ $$EXIT -ne 0 ] && [ $$EXIT -ne 5 ]; then exit $$EXIT; fi

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

clean:
	-rm -rf .venv ./dist $(TOX_HTML_REPORT_DIR) .tox/*.messages.ndjson
