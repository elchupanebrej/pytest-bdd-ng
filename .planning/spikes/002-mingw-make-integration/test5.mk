# Test: SHELL with known-working internal bash + docker PATH
SHELL := /usr/bin/bash
export PATH := C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)

.PHONY: env-check env-check-docker
env-check:
	@command -v uv >/dev/null || { echo "ERROR: uv missing."; exit 1; }
	@echo "ENV CHECK PASSED"
env-check-docker:
	@command -v docker >/dev/null || { echo "ERROR: docker missing."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon unavailable."; exit 1; }
	@echo "DOCKER CHECK PASSED"
