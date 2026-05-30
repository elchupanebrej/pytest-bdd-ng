# Phase 15: Cross-platform test suite entrypoint (Makefile + MinGW sh) - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Add OS detection and cross-platform shell handling to the Makefile so `make test-all` works on Windows (MinGW/Git Bash), macOS, and Linux — routing native tests to the host platform and Docker-backed tests for non-native platforms, with env-check/install targets for prerequisite validation.

Scope is the Makefile and DEVELOPMENT.rst documentation. No changes to tox, pyproject.toml, CI workflows, or test code.
</domain>

<decisions>
## Implementation Decisions

### Shell / Platform Detection
- **D-01:** Fail early with a clear error message when `make` is invoked from cmd.exe or PowerShell (not Git Bash) on Windows. Add a guard at the top of the Makefile that detects the absence of a bash-compatible shell and exits with actionable instructions ("ERROR: make requires Git Bash on Windows. Run from Git Bash terminal.").
- **Shell path:** Use `C:/PROGRA~1/Git/bin/sh.exe` (short DOS path — avoids space-in-path issues that break Make's SHELL resolution). Add Docker bin to PATH on Windows (`C:/PROGRA~1/Docker/Docker/resources/bin`).
- **OS detection:** Use `UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")`. Group MINGW*/MSYS*/CYGWIN* under the Windows filter. Route macOS via `Darwin`, Linux via `Linux`.

### Docker Target Routing
- **D-02:** Keep auto-attempt with `-` prefix in `test-all`. Docker targets are non-fatal when Docker is unavailable (matches Phase 12 D-08/D-10). Split `test-docker` into `test-docker-linux` (Alpine-based Python image) and `test-docker-windows` (Server Core-based Python image) with per-platform routing in `test-all`.
- **Docker image for Windows:** `python:3.14-windowsservercore-ltsc2022` — the only viable base image (Nano Server cannot run Python, no MSVC runtime).

### env-check Behavior
- **D-03:** Silent pass, loud fail. `@` prefix on successful checks — no output on success. Clear ERROR message on failure with actionable fix instructions ("Run make env-install-docker"). Matches current convention and Phase 12 D-08 read-only environment check policy.

### Documentation
- **D-04:** Concise prerequisite table in DEVELOPMENT.rst listing OS, required tools (uv, Git Bash, Docker), verification command, and links to official install pages. Include canonical `make` commands. No full step-by-step walkthroughs — avoids duplicating upstream install guides that change over time.

### the agent's Discretion
- Exact Makefile guard syntax and error message wording for unsupported shell detection
- Exact Docker target names and per-platform routing table structure
- env-check target internals (which tools to check, dependency ordering)
- DEVELOPMENT.rst section structure and prerequisite table format
- Whether to add a `test-docker` meta-target that dispatches to `test-docker-linux` or `test-docker-windows` based on platform
- Exact `uname` filter patterns for MinGW/MSYS/Cygwin variants

### Folded Todos
- **"Fix Makefile SHELL for cross-platform (Win/Mac/Linux)"** — This todo IS Phase 15's scope. The spike findings provide the proven 2-line fix (SHELL + PATH on Windows, uname detection). Folded into implementation.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Spike Findings (Proven Patterns)
- `.opencode/skills/spike-findings-pytest-bdd/SKILL.md` — Feature areas index: cross-platform testing, Windows Docker image
- `.opencode/skills/spike-findings-pytest-bdd/references/cross-platform-testing.md` — Proven 2-line SHELL/PATH fix, uname detection, platform routing table, Docker target split. Includes anti-patterns (don't use `ifdef OS`, don't set `SHELL := sh`, don't use MSYS2 paths).
- `.opencode/skills/spike-findings-pytest-bdd/references/windows-docker-image.md` — Windows Server Core as the only viable base image, Dockerfile template, constraints (8 GB image, 30-60 min pull, Docker Desktop Windows containers mode).

### Roadmap and Requirements
- `.planning/ROADMAP.md` — Phase 15 entry: goal, success criteria, dependency on Phase 14
- `.planning/PROJECT.md` — Core value, constraints (ruff, attrs, StashBound, Python 3.10-3.14, pytest >=7.0.0)
- `.planning/REQUIREMENTS.md` — v1 testing requirements, traceability

### Prior Phase Decisions
- `.planning/phases/14-gap-closure/14-CONTEXT.md` — Phase 14 scope (immediate predecessor, testing-only phase)
- `.planning/phases/12-restructure-test-suite-into-semantic-groups/12-CONTEXT.md` — D-08 environment check policy (read-only, no surprise provisioning), D-09 early fail with actionable errors, D-10 test-all should not fail on unavailable environments, D-19 Makefile is the documented human API, D-21 tox stays as matrix engine

### Codebase Maps
- `.planning/codebase/STACK.md` — Tooling (uv, tox, pytest, Docker), platform requirements, environment variables
- `.planning/codebase/TESTING.md` — Test organization, run commands, test group ordering, markers
- `.planning/codebase/CONVENTIONS.md` — Naming, style, Makefile conventions

### Source and Configuration
- `Makefile` — Current state: 183 lines, no OS detection, no SHELL/PATH fix, single `test-docker` target, platform targets use posix `|| [ $$? -eq 5 ]` syntax
- `pyproject.toml` — Pytest markers (docker, windows, posix, slow, external), test_group_paths, test_group_order
- `DEVELOPMENT.rst` — Target for cross-platform setup documentation (D-04)

### Environment
- `.env` — Project-local environment configuration
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Current Makefile targets**: `env-check`, `env-check-docker`, `env-check-windows`, `env-install`, `env-install-docker` — extend these with platform-aware guards rather than replacing
- **`test-windows` target**: Existing Windows marker-based test selection (`tests/cases -m windows`) — keep the selector, fix the shell syntax for cross-platform compatibility
- **`test-posix` target**: Existing posix marker-based selection — same fix needed for `|| [ $$? -eq 5 ]` syntax
- **`test-docker` target**: Single target using `env-check-docker` + docker marker — split into linux/windows variants
- **`local-pr-gate` target**: Uses `rg` (ripgrep) in posix shell syntax — needs compatibility audit

### Established Patterns
- `@` prefix for silent commands, `-` prefix for non-fatal commands in Makefile
- `$(PYTEST)` variable for test runner command
- `$(MAKE)` for recursive make invocations
- `uv run python -m pytest` as the canonical test invocation
- Test markers: `docker`, `windows`, `posix`, `slow`, `external`, `browser`
- Read-only env-check targets, explicit env-install targets (Phase 12 D-08/D-11)

### Integration Points
- **Makefile line 33-37**: `test-all` — wire platform detection and routing here
- **Makefile line 63-64**: `test-docker` — split into `test-docker-linux` and `test-docker-windows`
- **Makefile line 66-67**: `test-windows` — fix `|| [ $$? -eq 5 ]` for non-posix shells
- **Makefile line 69-70**: `test-posix` — same fix
- **Makefile line 1-6**: `.PHONY` declarations — add new targets
- **Makefile line 76-79**: `env-check-docker` — may need platform-specific Docker checks
- **Makefile line 81-86**: `env-check-windows` — may need Git Bash detection guard
- **DEVELOPMENT.rst**: Add "Cross-Platform Setup" section with prerequisite table
</code_context>

<specifics>
## Specific Ideas

- The spike findings provide a near-complete implementation blueprint — the Makefile changes are primarily mechanical: add SHELL/PATH, add uname detection, add routing table, split `test-docker`, fix shell syntax in `test-windows`/`test-posix`.
- The unsupported shell guard should detect both cmd.exe and PowerShell by checking for a bash-compatible shell (not `uname` return value) — a user might have Git Bash installed but run `make` from the wrong terminal.
- Docker targets should remain commented or documented as "optional — run `make env-install-docker` first" rather than hidden.
- The `local-pr-gate` target's `rg` dependency is posix-specific — consider a companion Windows check or document the ripgrep requirement.
- DEVELOPMENT.rst prerequisite table should cover: Windows (Git Bash + Docker Desktop), macOS (Homebrew or uv), Linux (uv + Docker). Keep each row to one line.
</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
- **"Integrate BDD/ATDD tests into development workflow and UAT phase"** — This is a workflow/process change, not a Makefile change. Belongs in its own phase or a quick task.
- **"No TestClasses are allowed in tests"** — Ruff rule enforcement, not Makefile-related. Belongs in a linting/quality phase.

None of the other gray areas explored during discussion fell outside phase scope.
</deferred>

---

*Phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh*
*Context gathered: 2026-05-21*
