# Plan 15-01 Summary: Makefile Cross-Platform Guards

**Status:** Complete

## What was implemented

All 5 tasks executed on `Makefile`:

1. **OS detection + unsupported-shell guard + Windows SHELL/PATH fix** (lines 8-17)
   - `UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)` — detects OS at parse time
   - Parse-time `$(error ...)` guard fires when `UNAME_S` is literally `Windows` (running from cmd.exe/PowerShell), exiting with message "ERROR: make requires Git Bash on Windows. Run from Git Bash terminal."
   - For MINGW/MSYS/CYGWIN: `SHELL` set to short DOS path `C:/PROGRA~1/Git/bin/sh.exe` and Docker bin added to `PATH`
   - `check-shell` target added to `.PHONY` and wired as dependency of `env-check`

2. **Docker target split** (lines 86-90)
   - `test-docker` split into `test-docker-linux` (marker: `docker and not windows`) and `test-docker-windows` (marker: `docker and windows`)
   - Old single `test-docker` target removed from `.PHONY` and definitions

3. **Platform routing table + test-all rewrite** (lines 19-28, 55-60)
   - `NATIVE_TARGETS` and `DOCKER_TARGETS` set per OS (Linux, Darwin, MINGW/MSYS/CYGWIN)
   - `test-all` rewritten to use route variables with `@-` prefix on Docker targets (satisfies D-10: Docker unavailable is non-fatal)
   - `render-tox-reports-run` still at end with `@-` prefix

4. **Cross-platform shell syntax fix** (lines 92-96)
   - `test-windows` and `test-posix` old `|| [ $$? -eq 5 ]` syntax replaced with POSIX-compatible `EXIT=$$?; if [ $$EXIT -ne 0 ] && [ $$EXIT -ne 5 ]; then exit $$EXIT; fi`
   - Exit code 5 (no tests collected) silently accepted
   - Non-zero non-5 exit codes still cause target failure

5. **Dry-run validation**
   - `make -n` dry-runs confirmed all targets resolve correctly
   - `make --version` returns GNU Make 4.4.1
   - Guard verified: running `make` from PowerShell now correctly fails with "ERROR: make requires Git Bash on Windows"

## Verification

- Task 1 guard blocks: UNAME_S (6 refs), check-shell (3 refs), sh.exe path (1 ref) — all present
- Task 2 split Docker targets: test-docker-linux (4 refs), test-docker-windows (4 refs) — confirmed
- Task 3 routing table: NATIVE_TARGETS, DOCKER_TARGETS present with platform-specific assignments
- Task 4 syntax: zero remaining `[ $$? -eq 5 ]` patterns in Makefile
- Task 5 dry-run: all targets resolve, guard fires from PowerShell (intended behavior)

## Key decision: uname fallback quoting

The `echo "Windows"` fallback was corrected to `echo Windows` (without quotes). With quotes, `UNAME_S` contained `"Windows"` (with quote characters), so `ifeq ($(UNAME_S),Windows)` never matched. Fixed by removing quotes from the echo command.
