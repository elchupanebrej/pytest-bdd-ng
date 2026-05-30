# Spike 003: Cross-platform Makefile with OS detection and target routing

# ── Platform detection ──────────────────────────────────────────────
UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")

ifeq ($(UNAME_S),Linux)
  PLATFORM := linux
else ifeq ($(UNAME_S),Darwin)
  PLATFORM := macos
else
  PLATFORM := windows
endif

# ── Windows-specific setup ─────────────────────────────────────────
ifeq ($(PLATFORM),windows)
  SHELL := C:/PROGRA~1/Git/bin/sh.exe
  export PATH := C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)
endif

# ── Per-platform test routing ──────────────────────────────────────
# Each platform runs: native suite + Docker suites for other platforms

ifeq ($(PLATFORM),linux)
  NATIVE_TARGETS := test-unit test-integration test-e2e test-compat test-perf test-slow test-posix
  DOCKER_TARGETS := test-docker-windows
else ifeq ($(PLATFORM),macos)
  NATIVE_TARGETS := test-unit test-integration test-e2e test-compat test-perf test-slow test-posix
  DOCKER_TARGETS := test-docker-linux test-docker-windows
else ifeq ($(PLATFORM),windows)
  NATIVE_TARGETS := test-unit test-integration test-e2e test-compat test-perf test-slow test-windows
  DOCKER_TARGETS := test-docker-linux
endif

# ── Diagnostic target ──────────────────────────────────────────────
.PHONY: platform-info
platform-info:
	@echo "=========================================="
	@echo " Platform Detection"
	@echo "=========================================="
	@echo "UNAME_S        = $(UNAME_S)"
	@echo "PLATFORM       = $(PLATFORM)"
	@echo "SHELL          = $(SHELL)"
	@echo "NATIVE_TARGETS = $(NATIVE_TARGETS)"
	@echo "DOCKER_TARGETS = $(DOCKER_TARGETS)"
	@echo "=========================================="
	@echo ""
	@echo "To run test-all on this platform:"
	@echo "  make $(NATIVE_TARGETS)"
	@echo "  make $(DOCKER_TARGETS)   # requires Docker"
	@echo "=========================================="

# ── Simulated test-all ─────────────────────────────────────────────
.PHONY: test-all
test-all:
	@echo "=== Running native targets ==="
	@for t in $(NATIVE_TARGETS); do \
		echo "  [$$t] would run here"; \
	done
	@echo "=== Running Docker targets ==="
	@for t in $(DOCKER_TARGETS); do \
		echo "  [$$t] would run here (if Docker available)"; \
	done
	@echo "=== test-all routing complete ==="
