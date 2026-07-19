# Spike 002: Test SHELL with short DOS path + Docker PATH
SHELL := C:/PROGRA~1/Git/bin/sh.exe
export PATH := C:/PROGRA~1/Git/bin:C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)

.PHONY: all
all:
	@echo "=== SHELL: $$SHELL ==="
	@echo "=== docker: $$(command -v docker 2>&1) ==="
	@echo "=== sh version: $$($(SHELL) --version 2>&1 | head -1) ==="
	@docker info >/dev/null 2>&1 && echo "DOCKER DAEMON: OK" || echo "DOCKER DAEMON: FAIL"
