# Definitive test: SHELL with short DOS path to Git sh.exe
SHELL := C:/PROGRA~1/Git/bin/sh.exe
export PATH := C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)

.PHONY: env-check env-check-docker
env-check:
	@command -v uv >/dev/null || { echo "ERROR: uv missing. Run make env-install."; exit 1; }
	@uv run python -c "import pytest" >/dev/null || { echo "ERROR: pytest environment missing."; exit 1; }
	@echo "ENV CHECK PASSED"

env-check-docker:
	@command -v docker >/dev/null || { echo "ERROR: docker missing."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon unavailable."; exit 1; }
	@echo "DOCKER CHECK PASSED"
