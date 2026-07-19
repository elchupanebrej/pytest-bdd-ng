# Phase 15: cross-platform-test-suite-entrypoint-makefile-mingw-sh - Research

**Researched:** 2026-05-23
**Domain:** GNU Make cross-platform test orchestration, Git Bash/MinGW, Docker Desktop, tox/pytest routing
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Source for this subsection: `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md` [VERIFIED: codebase grep].

- **D-01:** Fail early with a clear error message when `make` is invoked from cmd.exe or PowerShell (not Git Bash) on Windows. Add a guard at the top of the Makefile that detects the absence of a bash-compatible shell and exits with actionable instructions ("ERROR: make requires Git Bash on Windows. Run from Git Bash terminal.").
- **Shell path:** Use `C:/PROGRA~1/Git/bin/sh.exe` (short DOS path — avoids space-in-path issues that break Make's SHELL resolution). Add Docker bin to PATH on Windows (`C:/PROGRA~1/Docker/Docker/resources/bin`).
- **OS detection:** Use `UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")`. Group MINGW*/MSYS*/CYGWIN* under the Windows filter. Route macOS via `Darwin`, Linux via `Linux`.
- **D-02:** Keep auto-attempt with `-` prefix in `test-all`. Docker targets are non-fatal when Docker is unavailable (matches Phase 12 D-08/D-10). Split `test-docker` into `test-docker-linux` (Alpine-based Python image) and `test-docker-windows` (Server Core-based Python image) with per-platform routing in `test-all`.
- **Docker image for Windows:** `python:3.14-windowsservercore-ltsc2022` — the only viable base image (Nano Server cannot run Python, no MSVC runtime).
- **D-03:** Silent pass, loud fail. `@` prefix on successful checks — no output on success. Clear ERROR message on failure with actionable fix instructions ("Run make env-install-docker"). Matches current convention and Phase 12 D-08 read-only environment check policy.
- **D-04:** Concise prerequisite table in DEVELOPMENT.rst listing OS, required tools (uv, Git Bash, Docker), verification command, and links to official install pages. Include canonical `make` commands. No full step-by-step walkthroughs — avoids duplicating upstream install guides that change over time.

### the agent's Discretion
Source for this subsection: `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md` [VERIFIED: codebase grep].

- Exact Makefile guard syntax and error message wording for unsupported shell detection
- Exact Docker target names and per-platform routing table structure
- env-check target internals (which tools to check, dependency ordering)
- DEVELOPMENT.rst section structure and prerequisite table format
- Whether to add a `test-docker` meta-target that dispatches to `test-docker-linux` or `test-docker-windows` based on platform
- Exact `uname` filter patterns for MinGW/MSYS/Cygwin variants

### Deferred Ideas (OUT OF SCOPE)
Source for this subsection: `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md` [VERIFIED: codebase grep].

- **"Integrate BDD/ATDD tests into development workflow and UAT phase"** — This is a workflow/process change, not a Makefile change. Belongs in its own phase or a quick task.
- **"No TestClasses are allowed in tests"** — Ruff rule enforcement, not Makefile-related. Belongs in a linting/quality phase.
</user_constraints>

## Summary

Phase 15 is Makefile/documentation orchestration work, not pytest runtime work [VERIFIED: `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md`]. Primary implementation surface is `Makefile` and `DEVELOPMENT.rst` [VERIFIED: `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md`]. Current workspace already contains Phase 15 edits and review fixes: `Makefile` has `UNAME_S`, PowerShell/cmd guard, Docker split targets, per-OS routing, and fixed exit-code-5 shell handling; `DEVELOPMENT.rst` already has `Cross-Platform Setup` [VERIFIED: `Makefile`; VERIFIED: `DEVELOPMENT.rst`; VERIFIED: `15-01-SUMMARY.md`; VERIFIED: `15-02-SUMMARY.md`; VERIFIED: `15-REVIEW-FIX.md`].

Critical planning risk: `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-SPEC.md` adds a broader tox-backed platform pipeline requirement that conflicts with the earlier `15-CONTEXT.md` scope and the user-provided success criteria [VERIFIED: `15-SPEC.md`; VERIFIED: `15-CONTEXT.md`]. Planner must choose source of truth before new implementation tasks: old Phase 15 means Makefile `pytest` target routing; newer SPEC means tox wrappers, WSL2, PowerShell launch, backend validation before work, per-target args, and fail-fast/artifact modes [VERIFIED: `15-SPEC.md`].

**Resolved planning rule:** `ROADMAP.md` Phase 15 success criteria plus `15-CONTEXT.md` govern this revision; finish/verify existing Makefile+docs. `15-SPEC.md` tox-orchestration expansion is deferred unless promoted to a later phase [VERIFIED: revision_context].

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| OS detection and route selection | Developer tooling / Makefile | Shell runtime | `uname -s` value enters Makefile parse-time logic and chooses target lists [CITED: https://www.gnu.org/s/make/manual/html_node/Choosing-the-Shell.html]. |
| Unsupported shell guard | Developer tooling / Makefile | Windows shell | PowerShell/cmd invocation lacks `uname`; current guard treats fallback `Windows` as unsupported shell [VERIFIED: `Makefile`; VERIFIED: `make test-all` from PowerShell]. |
| Native pytest/tox execution | Developer tooling / Makefile | Python test runner | Makefile is documented human API; tox remains matrix engine per Phase 12 [VERIFIED: `12-CONTEXT.md`; VERIFIED: `tox.ini`]. |
| Docker-backed non-native tests | Developer tooling / Makefile | Docker Desktop / Docker Engine | Makefile checks `docker`, daemon, Compose before Docker-backed targets [VERIFIED: `Makefile`; CITED: https://docs.docker.com/desktop/setup/install/windows-install/]. |
| Cross-platform docs | Documentation | Makefile | `DEVELOPMENT.rst` is project guideline source and must list prerequisites/commands [VERIFIED: `AGENTS.md`; VERIFIED: `DEVELOPMENT.rst`]. |

## Project Constraints (from AGENTS.md)

- Always prefix commands with `rtk` [VERIFIED: `AGENTS.md`].
- Development guidelines live in `DEVELOPMENT.rst`; do not duplicate long-lived project guidance in `AGENTS.md` [VERIFIED: `AGENTS.md`].
- Project is Python library/CLI tooling supporting Python 3.10-3.14 [VERIFIED: `AGENTS.md`].
- Core tools include `pytest>=7`, `tox>=4.2`, `pre-commit`, `ruff`, `mypy`, `packaging` [VERIFIED: `AGENTS.md`].
- Distributed/live-reporting stack includes `pytest-xdist>=3.8.0`, Docker/Compose, Node.js on PATH, `@cucumber/cucumber`, `@cucumber/pretty-formatter` [VERIFIED: `AGENTS.md`].
- For non-native platform test environments, run via Docker; Windows targets are exempt [VERIFIED: `AGENTS.md`].
- Makefile is project human test API from Phase 12; tox remains matrix engine [VERIFIED: `12-CONTEXT.md`].
- Documentation/planning artifacts must be English [VERIFIED: `AGENTS.md`].

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| GNU Make | 4.4.1 locally | Human test entrypoint and target router | GNU Make supports `SHELL`, parse-time variables, recursive `$(MAKE)`, and `-` ignored-error recipe prefix [VERIFIED: local `make --version`; CITED: https://www.gnu.org/s/make/manual/html_node/Choosing-the-Shell.html; CITED: https://www.gnu.org/s/make/manual/html_node/Errors.html]. |
| Git Bash / MinGW `sh.exe` | Git 2.53.0.windows.3 locally | Windows bash-compatible shell for Make recipes | Local Git install provides `C:/PROGRA~1/Git/bin/sh.exe`; Git Bash reports `MINGW64_NT-10.0-26200` via `uname -s` [VERIFIED: local probe]. |
| uv | 0.11.15 locally | Python environment runner | Existing Makefile uses `uv run` and `uv sync` for canonical test/development commands [VERIFIED: local `uv --version`; VERIFIED: `Makefile`; VERIFIED: `DEVELOPMENT.rst`]. |
| pytest | via project env | Test runner | Existing Makefile uses `uv run ... python -m pytest`; markers define unit/integration/e2e/docker/windows/posix routing [VERIFIED: `Makefile`; VERIFIED: `pyproject.toml`]. |
| tox | configured in `tox.ini` | Matrix engine | Phase 12 says tox remains matrix engine; `tox.ini` defines `lin`, `mac`, `win` platform factors and `{posargs}` [VERIFIED: `12-CONTEXT.md`; VERIFIED: `tox.ini`]. |
| Docker Desktop / Docker CLI | Docker 29.4.3 locally | Non-native/platform-backed test environments | Docker Desktop docs describe Windows/Linux container mode switching; Makefile checks CLI, daemon, Compose [VERIFIED: local `docker --version`; CITED: https://docs.docker.com/desktop/setup/install/windows-install/; VERIFIED: `Makefile`]. |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| ripgrep (`rg`) | 15.1.0 locally | `local-pr-gate` workflow checks | Keep explicit `command -v rg` guard before use [VERIFIED: local `rg --version`; VERIFIED: `Makefile`]. |
| PowerShell | Windows host shell | Native Windows tox launch if `15-SPEC.md` wins | SPEC requires PowerShell for Windows native tox from Git Bash [VERIFIED: `15-SPEC.md`]. |
| WSL2 / `wsl.exe` | not probed as available | Linux-from-Windows backend if `15-SPEC.md` wins | SPEC requires Linux tox from Windows via WSL2 [VERIFIED: `15-SPEC.md`]. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `uname -s` route detection | `ifdef OS` | `ifdef OS` only detects Windows family and misses macOS/Linux routing [VERIFIED: spike findings]. |
| `SHELL := C:/PROGRA~1/Git/bin/sh.exe` | Leave Git Bash shell intact | Context locked short path, but review found hardcoded path brittle; current code removed override after review fix [VERIFIED: `15-CONTEXT.md`; VERIFIED: `15-REVIEW.md`; VERIFIED: `15-REVIEW-FIX.md`; VERIFIED: `Makefile`]. |
| Direct pytest targets | tox-backed targets | Direct pytest matches old CONTEXT/success criteria; tox-backed wrappers match newer SPEC and Phase 12 tox-as-matrix rule [VERIFIED: `15-CONTEXT.md`; VERIFIED: `15-SPEC.md`; VERIFIED: `12-CONTEXT.md`]. |

**Installation:** No new package install required for old Phase 15 scope [VERIFIED: `15-CONTEXT.md`]. If SPEC scope wins, planner should use existing `tox` dependency, not add a new runner [VERIFIED: `tox.ini`; VERIFIED: `AGENTS.md`].

## Package Legitimacy Audit

No external packages recommended for installation in this research [VERIFIED: `15-CONTEXT.md`; VERIFIED: `15-SPEC.md`]. Package legitimacy gate not required [VERIFIED: no new packages].

## Architecture Patterns

### System Architecture Diagram

```text
Developer command
  |
  v
make parses Makefile
  |
  +--> UNAME_S := uname -s || echo Windows
  |      |
  |      +--> Windows fallback -> parse-time error for cmd.exe/PowerShell
  |      +--> Linux/Darwin/MINGW/MSYS/CYGWIN -> route target lists
  |
  v
env-check layer
  |
  +--> uv/Python checks
  +--> Docker checks for Docker-backed targets
  +--> Windows bridge checks for Windows target
  |
  v
test-all orchestration
  |
  +--> native targets (fatal)
  +--> Docker targets (non-fatal under old CONTEXT)
  +--> tox report rendering (non-fatal)
```

Diagram reflects current old-scope Makefile behavior [VERIFIED: `Makefile`].

### Recommended Project Structure

```text
Makefile                         # OS detection, env checks, target routing [VERIFIED]
DEVELOPMENT.rst                  # Cross-Platform Setup + Makefile API docs [VERIFIED]
tox.ini                          # Matrix engine if SPEC/tox expansion proceeds [VERIFIED]
pyproject.toml                   # pytest markers and test group paths [VERIFIED]
tests/cases/                     # semantic test groups routed by Makefile markers [VERIFIED]
```

### Pattern 1: Parse-Time Unsupported Shell Guard

**What:** Detect `uname` absence and fail before recipe execution [VERIFIED: `Makefile`].
**When to use:** Windows PowerShell/cmd invocation should stop with actionable message [VERIFIED: `15-CONTEXT.md`].
**Example:**

```makefile
# Source: current Makefile [VERIFIED: codebase grep]
UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(UNAME_S),Windows)
  $(error ERROR: make requires Git Bash on Windows. Run from Git Bash terminal.)
endif
```

### Pattern 2: MinGW/MSYS/Cygwin Grouping

**What:** Treat `MINGW%`, `MSYS%`, and `CYGWIN%` as Windows host family [VERIFIED: spike findings].
**When to use:** Route Windows-native tests and Linux Docker tests from Git Bash [VERIFIED: `15-CONTEXT.md`].
**Example:**

```makefile
# Source: spike findings [VERIFIED: .opencode/skills/spike-findings-pytest-bdd/references/cross-platform-testing.md]
ifneq ($(filter MINGW% MSYS% CYGWIN%,$(UNAME_S)),)
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix test-windows
  DOCKER_TARGETS := test-docker-linux test-external
endif
```

### Pattern 3: Non-Fatal Docker Subwork

**What:** Prefix Docker recursive make with `-` so unavailable Docker does not fail `test-all` under old CONTEXT [CITED: https://www.gnu.org/s/make/manual/html_node/Errors.html; VERIFIED: `12-CONTEXT.md`; VERIFIED: `15-CONTEXT.md`].
**When to use:** Docker-backed targets are optional in old Phase 15 success criteria [VERIFIED: `15-CONTEXT.md`].
**Example:**

```makefile
# Source: current Makefile [VERIFIED: codebase grep]
test-all: env-check
	@$(MAKE) --no-print-directory $(NATIVE_TARGETS)
	@-$(MAKE) --no-print-directory $(DOCKER_TARGETS)
	@-$(MAKE) --no-print-directory render-tox-reports-run
```

### Anti-Patterns to Avoid

- **Using `ifdef OS` for full routing:** Detects Windows presence only; does not distinguish Linux/macOS/MinGW variants [VERIFIED: spike findings].
- **Hardcoding Git/Docker short paths without fallback:** Review found custom installs/localized paths/8.3 collisions can break all recipes; current fix removed hardcoded `SHELL/PATH` block [VERIFIED: `15-REVIEW.md`; VERIFIED: `15-REVIEW-FIX.md`].
- **Putting Docker-dependent `test-external` in fatal native target list:** Review found this regresses Phase 12 D-10; current fix moved it to non-fatal Docker targets [VERIFIED: `15-REVIEW.md`; VERIFIED: `15-REVIEW-FIX.md`; VERIFIED: `Makefile`].
- **Bare `python` in Makefile checks:** Review fixed `env-check-windows` to use `uv run python` and depend on `env-check` [VERIFIED: `15-REVIEW-FIX.md`; VERIFIED: `Makefile`].

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OS detection | Custom Python/PowerShell detector | `uname -s` in Makefile | Locked by phase success criteria and available in Git Bash/POSIX shells [VERIFIED: `15-CONTEXT.md`; VERIFIED: local Git Bash probe]. |
| Error ignoring | Manual shell wrappers around every Docker target | GNU Make `-` recipe prefix | Official Make behavior ignores nonzero status for that recipe line [CITED: https://www.gnu.org/s/make/manual/html_node/Errors.html]. |
| Matrix execution | Ad hoc Python-version loops in Makefile | tox env factors | `tox.ini` already owns Python/pytest/platform factors [VERIFIED: `tox.ini`; VERIFIED: `12-CONTEXT.md`]. |
| Windows container base | Custom Nano Server Python image | Official Python Server Core image | Spike chose `python:3.14-windowsservercore-ltsc2022`; Microsoft docs show Nano Server has smaller API surface than Server Core [VERIFIED: spike findings; CITED: https://learn.microsoft.com/ar-sa/virtualization/windowscontainers/manage-containers/container-base-images]. |

**Key insight:** Makefile should orchestrate existing tools; pytest, tox, Docker, and shell should own their domains [VERIFIED: `12-CONTEXT.md`; VERIFIED: `15-CONTEXT.md`; VERIFIED: `tox.ini`].

## Common Pitfalls

### Pitfall 1: Spec/Context Scope Conflict

**What goes wrong:** Planner mixes old direct-pytest Makefile routing with newer tox-backed platform pipeline [VERIFIED: `15-CONTEXT.md`; VERIFIED: `15-SPEC.md`].
**Why it happens:** Existing artifacts were created in different workflow passes [VERIFIED: phase directory listing].
**How to avoid:** Add Wave 0 decision: old CONTEXT scope or newer SPEC scope [VERIFIED: codebase artifacts].
**Warning signs:** Plan mentions both "Docker non-fatal" and "missing required backend fails before subwork" without reconciling [VERIFIED: `15-CONTEXT.md`; VERIFIED: `15-SPEC.md`].

### Pitfall 2: Parse-Time `$(error)` Blocks Too Much

**What goes wrong:** Running `make` from PowerShell exits before even help/inspection targets [VERIFIED: local `make test-all` from PowerShell].
**Why it happens:** Guard is parse-time, before target selection [VERIFIED: `Makefile`].
**How to avoid:** This is acceptable for old D-01; if SPEC needs diagnostic targets from PowerShell, use target-scoped validation instead [VERIFIED: `15-CONTEXT.md`; ASSUMED].
**Warning signs:** PowerShell output includes Makefile parse error before any target recipe [VERIFIED: local probe].

### Pitfall 3: Hardcoded Windows Paths

**What goes wrong:** Git/Docker installed outside `C:\Program Files` or 8.3 names differ; Make shell or Docker lookup fails [VERIFIED: `15-REVIEW.md`].
**Why it happens:** Context locked short DOS paths, but review found environment variance [VERIFIED: `15-CONTEXT.md`; VERIFIED: `15-REVIEW.md`].
**How to avoid:** Prefer current reviewed fix: rely on Git Bash shell and `env-check-docker` PATH validation [VERIFIED: `15-REVIEW-FIX.md`; VERIFIED: `Makefile`].
**Warning signs:** `sh.exe: not found` or Docker missing despite Docker Desktop installed [VERIFIED: `15-REVIEW.md`].

### Pitfall 4: Windows Containers Mode

**What goes wrong:** Windows Docker target fails while Docker CLI works [CITED: https://docs.docker.com/desktop/setup/install/windows-install/].
**Why it happens:** Docker Desktop can switch between Linux and Windows container daemons on Windows [CITED: https://docs.docker.com/desktop/setup/install/windows-install/].
**How to avoid:** Document Windows containers mode requirement and fail with actionable `env-check-docker`/backend validation [CITED: https://docs.docker.com/desktop/setup/install/windows-install/; VERIFIED: `DEVELOPMENT.rst`].
**Warning signs:** Linux Docker targets work; Windows image pull/run fails [ASSUMED].

## Code Examples

### GNU Make Shell Choice

```makefile
# Source: GNU Make manual, adapted to project [CITED: https://www.gnu.org/s/make/manual/html_node/Choosing-the-Shell.html]
SHELL := /bin/sh
.SHELLFLAGS := -c
```

GNU Make takes recipe shell from `SHELL`; Windows/DOS shell behavior differs from POSIX and may use environment shell differently [CITED: https://www.gnu.org/s/make/manual/html_node/Choosing-the-Shell.html].

### Ignore Optional Docker Failures

```makefile
# Source: GNU Make manual + current Makefile [CITED: https://www.gnu.org/s/make/manual/html_node/Errors.html; VERIFIED: Makefile]
test-all: env-check
	@-$(MAKE) --no-print-directory $(DOCKER_TARGETS)
```

GNU Make `-` prefix causes Make to continue if that recipe line exits nonzero [CITED: https://www.gnu.org/s/make/manual/html_node/Errors.html].

### Preserve Pytest Exit Code 5

```makefile
# Source: current Makefile [VERIFIED: codebase grep]
test-posix: env-check
	$(PYTEST) tests/cases -m posix; EXIT=$$?; if [ $$EXIT -ne 0 ] && [ $$EXIT -ne 5 ]; then exit $$EXIT; fi
```

Current pattern treats "no tests collected" as non-fatal only for platform slices [VERIFIED: `Makefile`].

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single `test-docker` target | `test-docker-linux` and `test-docker-windows` | Phase 15 implementation summary, 2026-05-21 | Enables per-host routing [VERIFIED: `15-01-SUMMARY.md`; VERIFIED: `Makefile`]. |
| Docker `test-external` fatal in route list | `test-external` under non-fatal Docker targets | Review fix, 2026-05-21 | Restores Phase 12 feasible `test-all` policy [VERIFIED: `15-REVIEW-FIX.md`; VERIFIED: `12-CONTEXT.md`]. |
| Hardcoded `SHELL/PATH` short paths | No hardcoded Git/Docker path override | Review fix, 2026-05-21 | Avoids brittle Windows installs [VERIFIED: `15-REVIEW-FIX.md`; VERIFIED: `Makefile`]. |
| Direct pytest Make targets | Possible future tox-backed wrappers | 15-SPEC created 2026-05-23 | Scope expansion requires new plan decision [VERIFIED: `15-SPEC.md`]. |

**Deprecated/outdated:**
- `echo "Windows"` fallback: summary says quote characters broke `ifeq`; current uses `echo Windows` [VERIFIED: `15-01-SUMMARY.md`; VERIFIED: `Makefile`].
- `make test-docker` as docs-only target: current Makefile still has meta-target `test-docker`, but docs list split targets; review noted earlier mismatch was fixed [VERIFIED: `Makefile`; VERIFIED: `15-REVIEW-FIX.md`; VERIFIED: `DEVELOPMENT.rst`].

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Target-scoped validation may be preferable if SPEC needs diagnostic targets from PowerShell. | Common Pitfalls | Planner may over-constrain guard design. |
| A2 | Windows Docker image runtime failures commonly indicate daemon/container-mode mismatch. | Common Pitfalls | Error triage docs may be incomplete. |

## Resolved Questions

1. **Which source of truth governs planning: `15-CONTEXT.md` or `15-SPEC.md`?**
   - Resolution: `ROADMAP.md` Phase 15 success criteria plus `15-CONTEXT.md` locked decisions govern this planning revision [VERIFIED: `ROADMAP.md`; VERIFIED: `15-CONTEXT.md`; VERIFIED: revision_context].
   - Scope effect: `15-SPEC.md` tox-backed expansion is deferred unless explicitly promoted into a later phase or new planning pass [VERIFIED: `15-SPEC.md`; VERIFIED: revision_context].
   - Planner action: keep current Makefile/docs scope; do not silently merge tox-backed WSL2/PowerShell/fail-fast expansion into Phase 15.

2. **Should `test-docker` remain as meta-target?**
   - Resolution: Keep `test-docker` as compatibility/meta target per roadmap no-regression criterion and checker feedback [VERIFIED: `ROADMAP.md`; VERIFIED: revision_context].
   - Scope effect: split targets remain primary routing units; meta-target dispatches to `test-docker-linux` and `test-docker-windows`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| GNU Make | Makefile entrypoint | yes | 4.4.1 | none [VERIFIED: local probe]. |
| Git Bash `sh.exe` | Windows Make recipes | yes | Git 2.53.0.windows.3 | none for Windows old scope [VERIFIED: local probe]. |
| `uname` in PowerShell PATH | Unsupported-shell guard | no | — | fallback `echo Windows` triggers guard [VERIFIED: local probe; VERIFIED: `Makefile`]. |
| `uname` in Git Bash | OS detection | yes | reports `MINGW64_NT-10.0-26200` | none [VERIFIED: local probe]. |
| uv | env-check/test runner | yes | 0.11.15 | `make env-install` docs only [VERIFIED: local probe; VERIFIED: `Makefile`]. |
| Docker CLI | Docker targets | yes | 29.4.3 | Docker targets non-fatal under old CONTEXT [VERIFIED: local probe; VERIFIED: `15-CONTEXT.md`]. |
| Docker daemon | Docker targets | yes | desktop-linux context observed | Docker targets non-fatal under old CONTEXT [VERIFIED: local `docker info` partial output]. |
| ripgrep | local-pr-gate | yes | 15.1.0 | none; Makefile guard gives install link [VERIFIED: local probe; VERIFIED: `Makefile`]. |
| WSL2 / `wsl.exe` | Deferred SPEC Linux-from-Windows backend | not verified | — | none in current Phase 15 scope; required only if deferred SPEC expansion is promoted [VERIFIED: `15-SPEC.md`; VERIFIED: revision_context]. |

**Missing dependencies with no fallback:**
- WSL2 availability is unverified if SPEC/tox platform scope wins [VERIFIED: `15-SPEC.md`].

**Missing dependencies with fallback:**
- `uname` absent in PowerShell is expected and intentionally trips old-scope guard [VERIFIED: local probe; VERIFIED: `Makefile`].

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest via `uv run ... python -m pytest`; tox matrix in `tox.ini` [VERIFIED: `Makefile`; VERIFIED: `tox.ini`] |
| Config file | `pyproject.toml`, `tox.ini`, `.coveragerc` [VERIFIED: codebase grep] |
| Quick run command | `rtk powershell -NoProfile -Command "& 'C:/PROGRA~1/Git/bin/sh.exe' -lc 'cd /c/Users/bulky/Projects/pytest-bdd && make -n test-all'"` [VERIFIED: local probe] |
| Full suite command | `make test-all` from Git Bash; PowerShell intentionally blocked [VERIFIED: `Makefile`; VERIFIED: local probe] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| P15-01 | OS detection uses `uname -s`; Windows fallback guard fires | dry-run/smoke | `make test-all` from PowerShell should fail with Git Bash error | yes [VERIFIED] |
| P15-02 | MinGW/Git Bash routes as Windows family | dry-run/smoke | Git Bash `make -n test-all` shows `MINGW...`, includes `test-windows`, Docker Linux route | yes [VERIFIED] |
| P15-03 | Docker targets split and non-fatal in `test-all` | static/dry-run | `Select-String Makefile -Pattern 'test-docker-linux|test-docker-windows|@-'` | yes [VERIFIED] |
| P15-04 | `test-windows`/`test-posix` preserve exit code 5 only | static/dry-run | `Select-String Makefile -Pattern 'EXIT=\\$\\$\\?'` | yes [VERIFIED] |
| P15-05 | Cross-Platform Setup docs exist | static docs | `Select-String DEVELOPMENT.rst -Pattern 'Cross-Platform Setup'` | yes [VERIFIED] |

### Sampling Rate

- **Per task commit:** Git Bash `make -n test-all` plus PowerShell guard smoke [VERIFIED: local probe].
- **Per wave merge:** `uv run python -m pytest tests/cases/unit -m unit` and `uv run python -m pytest tests/cases/e2e -m "e2e and not browser"` [VERIFIED: `15-02-SUMMARY.md`].
- **Phase gate:** Git Bash `make -n test-all`, PowerShell guard, `pre-commit run --files Makefile DEVELOPMENT.rst`, and feasible unit/e2e smoke [VERIFIED: `15-02-SUMMARY.md`].

### Wave 0 Gaps

- [x] Source-of-truth checkpoint for `15-CONTEXT.md` vs `15-SPEC.md` resolved: `ROADMAP.md` + `15-CONTEXT.md` govern current revision; SPEC tox expansion deferred unless promoted [VERIFIED: revision_context].
- [x] SPEC tox-target validation tests/dry-runs not planned for current revision because SPEC expansion is deferred, not Phase 15 scope [VERIFIED: revision_context].

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No auth surface changed [VERIFIED: phase scope]. |
| V3 Session Management | no | No session surface changed [VERIFIED: phase scope]. |
| V4 Access Control | no | No access-control surface changed [VERIFIED: phase scope]. |
| V5 Input Validation | yes | Treat Make variables/args as shell inputs; quote variables and avoid eval-style dynamic shell construction [ASSUMED]. |
| V6 Cryptography | no | No crypto surface changed [VERIFIED: phase scope]. |

### Known Threat Patterns for Makefile Shell Orchestration

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Shell injection via user-supplied Make variables | Tampering/Elevation | Keep variables as arguments to known tools; avoid `eval`, untrusted command fragments, or unquoted path expansion [ASSUMED]. |
| PATH hijack for tools like `docker`, `uv`, `rg` | Spoofing/Tampering | Use `command -v` guards; document trusted shell; keep env checks before work [VERIFIED: `Makefile`; ASSUMED]. |
| Running from wrong Windows shell | Tampering/DoS | Parse-time Git Bash guard with actionable error [VERIFIED: `Makefile`; VERIFIED: local probe]. |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md` - locked decisions and scope [VERIFIED: codebase grep].
- `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-SPEC.md` - later tox-backed scope and conflict source [VERIFIED: codebase grep].
- `Makefile` - current implementation state [VERIFIED: codebase grep].
- `DEVELOPMENT.rst` - current docs state [VERIFIED: codebase grep].
- `tox.ini` - platform factors and `{posargs}` [VERIFIED: codebase grep].
- `pyproject.toml` - pytest markers/test groups [VERIFIED: codebase grep].
- GNU Make manual, Choosing the Shell - https://www.gnu.org/s/make/manual/html_node/Choosing-the-Shell.html [CITED].
- GNU Make manual, Errors in Recipes - https://www.gnu.org/s/make/manual/html_node/Errors.html [CITED].
- Docker Desktop Windows install docs - https://docs.docker.com/desktop/setup/install/windows-install/ [CITED].
- Microsoft Windows container version compatibility - https://learn.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility [CITED].
- Microsoft Windows container base images - https://learn.microsoft.com/ar-sa/virtualization/windowscontainers/manage-containers/container-base-images [CITED].

### Secondary (MEDIUM confidence)

- `.opencode/skills/spike-findings-pytest-bdd/references/cross-platform-testing.md` - local spike patterns [VERIFIED: codebase grep].
- `.opencode/skills/spike-findings-pytest-bdd/references/windows-docker-image.md` - local spike Docker image findings [VERIFIED: codebase grep].
- `15-REVIEW.md` and `15-REVIEW-FIX.md` - review/fix history [VERIFIED: codebase grep].

### Tertiary (LOW confidence)

- Assumptions A1-A2 in Assumptions Log [ASSUMED].

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified from local tools, Makefile, tox.ini, and official GNU/Docker/Microsoft docs.
- Architecture: MEDIUM - old scope is verified, but newer SPEC conflicts with old CONTEXT.
- Pitfalls: HIGH for reviewed issues, MEDIUM for Windows container runtime triage.

**Research date:** 2026-05-23
**Valid until:** 2026-06-22 for old Makefile scope; 2026-05-30 for Docker Desktop/Windows container specifics.
