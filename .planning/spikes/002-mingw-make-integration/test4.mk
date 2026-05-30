# Test: SHELL + Git bin in PATH
SHELL := sh
export PATH := C:/PROGRA~1/Git/bin:C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)

.PHONY: env-check env-check-docker
env-check:
	@command -v uv >/dev/null || { echo "ERROR: uv missing."; exit 1; }
env-check-docker:
	@command -v docker >/dev/null || { echo "ERROR: docker missing."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon unavailable."; exit 1; }
	@echo "ALL DOCKER CHECKS PASSED"
