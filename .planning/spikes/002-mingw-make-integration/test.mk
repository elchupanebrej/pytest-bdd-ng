# Spike 002: Test MinGW make + docker integration on Windows
SHELL := C:/Program Files/Git/bin/sh.exe

# Docker bin must be on PATH for MinGW to find docker.exe
export PATH := C:/Program Files/Docker/Docker/resources/bin:$(PATH)

.PHONY: all env-check env-check-docker env-check-uv

all: env-check

env-check:
	@echo "=== SHELL check ==="
	@echo "SHELL=$$SHELL"
	@echo "SHELL version: $$($(SHELL) --version 2>&1 | head -1)"
	@echo ""
	@echo "=== PATH ==="
	@echo "$$PATH" | tr ':' '\n' | head -5
	@echo ""
	@echo "=== docker check ==="
	@command -v docker >/dev/null && echo "✓ docker found at $$(command -v docker)" || { echo "✗ docker NOT found on PATH"; exit 1; }
	@echo "=== uv check ==="
	@command -v uv >/dev/null && echo "✓ uv found at $$(command -v uv)" || { echo "✗ uv NOT found on PATH"; exit 1; }
	@echo "=== python check ==="
	@command -v python >/dev/null && echo "✓ python found" || command -v python3 >/dev/null && echo "✓ python3 found" || { echo "✗ python NOT found"; }
	@echo ""
	@echo "=== docker daemon ==="
	@docker info >/dev/null 2>&1 && echo "✓ docker daemon running" || { echo "✗ docker daemon NOT running"; exit 1; }
	@echo ""
	@echo "ALL CHECKS PASSED"
