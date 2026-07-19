# Final integration test: emulate real Makefile with Windows fix
ifdef OS
  SHELL := C:/PROGRA~1/Git/bin/sh.exe
  export PATH := C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)
endif

UV_SYNC_EXTRAS := --extra test --extra testtypes --extra doc-gen --extra struct-bdd
PYTHON_FACTOR ?= 314
PYTEST_FACTOR ?= latest
PYTEST ?= uv run python -m pytest
PYTEST_LOCAL_SELECTOR ?= not slow and not docker and not windows and not browser and not external

.PHONY: env-check env-check-docker env-install test-unit test

env-check:
	@command -v uv >/dev/null || { echo "ERROR: uv missing. Run make env-install."; exit 1; }
	@uv run python -c "import pytest" >/dev/null || { echo "ERROR: pytest environment missing. Run make env-install."; exit 1; }

env-check-docker:
	@command -v docker >/dev/null || { echo "ERROR: docker missing. Run make env-install-docker."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon unavailable. Start Docker, then retry."; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "ERROR: Docker Compose unavailable. Run make env-install-docker."; exit 1; }

env-install:
	uv sync $(UV_SYNC_EXTRAS)

test-unit: env-check
	$(PYTEST) tests/cases/unit -m unit -q

test: env-check
	$(PYTEST) tests/cases -m "$(PYTEST_LOCAL_SELECTOR)" -q
