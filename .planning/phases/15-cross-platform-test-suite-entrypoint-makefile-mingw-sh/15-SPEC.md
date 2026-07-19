# Phase 15: Cross-Platform Test Suite Entrypoint — Specification

**Created:** 2026-05-23
**Ambiguity score:** 0.13 (gate: <= 0.20)
**Requirements:** 8 locked

## Goal

The Makefile becomes the single human entrypoint for the complete cross-platform test pipeline, while tox becomes the execution engine for native and non-native platform test environments with target-specific CLI option passthrough.

## Background

The repository already has a Makefile test API and a tox matrix. The Makefile currently contains platform routing and environment checks, but many test targets still invoke `uv run ... pytest` directly. `tox.ini` already defines platform factors such as `lin`, `mac`, and `win`, plus coverage, xdist, mypy, ruff, pre-commit, and reporter-related environments. The missing capability is a Makefile orchestration layer that delegates test execution through tox, validates all required native and non-native backends before work starts, and lets developers pass different CLI options to each sub-target from `test-all`.

## Requirements

1. **Makefile entrypoint**: `make test-all` must be the documented entrypoint for a full cross-platform test run.
   - Current: `test-all` orchestrates Make targets, but those targets mostly call `uv run python -m pytest` directly.
   - Target: `test-all` orchestrates named Make targets that execute tox environments for native and required non-native platform coverage.
   - Acceptance: A dry-run or equivalent inspection shows `test-all` invoking platform/debuggable sub-targets, and those sub-targets invoke tox rather than direct pytest for test execution.

2. **Thin test targets**: Makefile test targets must rely on tox for test execution.
   - Current: Targets such as `test-unit`, `test-integration`, `test-e2e`, `test-windows`, `test-posix`, and Docker targets directly invoke pytest through uv.
   - Target: Test targets are thin wrappers around tox env lists or tox labels/factors; direct pytest remains only where explicitly justified as non-tox utility work.
   - Acceptance: Reviewing Makefile shows cross-platform test targets call tox, and no full-suite/platform test target bypasses tox with direct pytest.

3. **Debuggable platform targets**: Makefile must expose explicit targets that show what platform scope is being run.
   - Current: Platform routing is hidden inside `NATIVE_TARGETS` and `DOCKER_TARGETS`, which makes it harder to debug full runs.
   - Target: Makefile exposes named targets such as native, Linux, Windows, and macOS platform scopes, or equivalent explicit targets, so a developer can run and inspect each scope independently.
   - Acceptance: `make -n` for the full run prints distinct named platform sub-targets, and each sub-target can be invoked independently.

4. **Target-specific option passthrough**: Each Makefile test target must accept its own CLI options and `test-all` must be able to pass different options to different sub-targets.
   - Current: `tox.ini` supports `{posargs}`, but Makefile does not provide a consistent per-target option interface from `test-all`.
   - Target: Every relevant Make target has a documented variable for its tox/pytest posargs, and `test-all` forwards each target's specific variable only to that target.
   - Acceptance: A command equivalent to `make test-all TEST_LINUX_ARGS="..." TEST_WINDOWS_ARGS="..."` passes the Linux options only to Linux tox work and Windows options only to Windows tox work.

5. **Validation before work**: Environment validation must run as a separate layer before any real test subwork starts.
   - Current: Some targets validate their own dependencies just before work starts; a partial run can begin before later backend validation fails.
   - Target: Full-run validation checks all required backends for the selected platform and mode before any tox test environment starts.
   - Acceptance: If a required backend such as WSL2, Docker, Docker Windows containers, or tox is unavailable, `test-all` exits from validation before starting any tox test work.

6. **Platform backend routing**: Required native and non-native platform backends must be routed per host OS.
   - Current: The Makefile routes native and Docker marker targets, but does not define the requested tox-backed platform backend policy.
   - Target: On Windows/Git Bash, native Windows tox runs through PowerShell and Linux tox runs through WSL2. On Linux, native Linux tox runs on the host and Windows tox runs in a Windows Docker container. On macOS, Linux and Windows tox runs execute through Docker containers.
   - Acceptance: Makefile routing and validation encode the three host policies above, and dry-runs show the expected backend command for each host family.

7. **Artifact mode and fail-fast mode**: Full runs must support both artifact-maximizing and fail-fast execution modes.
   - Current: Some Docker/report steps are non-fatal via `-`, but there is no explicit full-run mode contract.
   - Target: Default full run continues across independent subwork where possible to produce all available artifacts; an explicit fail-fast option stops after the first failed subwork.
   - Acceptance: Documentation and Makefile behavior show default continue/collect mode and an explicit `FAIL_FAST=1` or equivalent fail-fast mode.

8. **Tox platform correctness from Windows Git Bash**: Native Windows tests launched from Git Bash must run in a Windows shell context.
   - Current: Makefile recipes run under sh-style shell semantics.
   - Target: Windows native tox is invoked through PowerShell from Git Bash so process and shell behavior match the Windows platform under test. Python `sys.platform` remains expected to be `win32` when using Windows Python; the PowerShell requirement is for reliable native Windows command semantics.
   - Acceptance: Windows native target command uses PowerShell to launch tox, and Linux-from-Windows target uses WSL2.

## Boundaries

**In scope:**
- Makefile orchestration targets for full, native, Linux, Windows, and macOS/platform-equivalent test scopes.
- Tox-backed execution for cross-platform test targets.
- Per-target CLI option passthrough from `test-all` to sub-targets.
- Preflight validation targets for tox, WSL2, Docker Linux containers, Docker Windows containers, and PowerShell-backed Windows native execution.
- Explicit continue-for-artifacts and fail-fast modes.
- Documentation updates describing the Makefile entrypoint, target variables, validation layer, and platform backend routing.

**Out of scope:**
- Rewriting pytest test logic or markers — this phase changes orchestration, not test semantics.
- Redesigning the tox matrix from scratch — existing tox environments remain the source execution units unless small additions are required to expose platform scopes.
- Changing CI provider workflow semantics — local Makefile entrypoint is the phase focus.
- Provisioning WSL2, Docker Desktop, Windows containers, or VM images automatically — validation must be read-only and actionable.
- Making non-native platform tests silently optional in full mode — missing required backends fail validation unless a separately documented opt-out mode is added.

## Constraints

- Makefile remains the human-facing entrypoint everywhere.
- Tox is the execution engine for test environments.
- Windows host entrypoint is Git Bash, but native Windows tox must be launched through PowerShell.
- Linux-from-Windows requires WSL2.
- Non-native Linux and Windows execution requires Docker or equivalent VM-like isolation.
- Validation must finish before test execution begins for selected full-run scope.
- Target option variables must be independent so `test-all` can pass different options to different sub-targets.

## Acceptance Criteria

- [ ] `make test-all` runs named platform/debuggable sub-targets rather than opaque direct pytest calls.
- [ ] Full-run and platform test targets invoke tox for test execution.
- [ ] `make test-all` can pass different CLI options to different sub-targets in one command.
- [ ] Validation for all required selected backends completes before any tox test work begins.
- [ ] Windows/Git Bash native Windows tox is launched via PowerShell.
- [ ] Windows/Git Bash Linux tox is launched via WSL2.
- [ ] Linux host routes Windows platform tox through Windows Docker container or an equivalent VM-like backend.
- [ ] macOS host routes Linux and Windows platform tox through Docker containers or equivalent VM-like backends.
- [ ] Default full run attempts independent subwork to collect available artifacts after failures.
- [ ] Explicit fail-fast mode stops after the first failed subwork.
- [ ] Documentation describes platform prerequisites, validation targets, full-run behavior, fail-fast behavior, and per-target option variables.

## Ambiguity Report

| Dimension           | Score | Min   | Status | Notes |
|---------------------|-------|-------|--------|-------|
| Goal Clarity        | 0.93  | 0.75  | ✓      | Makefile entrypoint and tox execution engine are locked. |
| Boundary Clarity    | 0.84  | 0.70  | ✓      | Scope limited to orchestration, validation, passthrough, docs. |
| Constraint Clarity  | 0.86  | 0.65  | ✓      | Host/backend routing and PowerShell/WSL2/Docker requirements are explicit. |
| Acceptance Criteria | 0.84  | 0.70  | ✓      | Pass/fail checks cover routing, validation, passthrough, and modes. |
| **Ambiguity**       | 0.13  | <=0.20| ✓      | Gate passed after round 2. |

Status: ✓ = met minimum, ⚠ = below minimum (planner treats as assumption)

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|-------|-------------|------------------|-----------------|
| 1 | Researcher | Should `test-all` run every tox env across required platform backends or only curated groups? | `test-all` must cover the complete required tox-backed platform pipeline. |
| 1 | Researcher | How should CLI options pass through? | Each target must have its own options; `test-all` must forward different options to different targets. |
| 1 | Researcher | What happens when non-native backend validation fails? | Separate validation layer runs before real work; failed validation prevents subwork from starting. |
| 1 | Researcher | How should failures affect artifact collection? | Default mode should collect all possible artifacts; explicit fail-fast mode stops at first failure. |
| 2 | Simplifier | Should targets become thinner and rely on tox? | Yes; test targets should be thin wrappers around tox. |
| 2 | Boundary Keeper | Should explicit platform targets exist? | Yes; targets must make it possible to debug and understand what ran. |
| 2 | Failure Analyst | How should native Windows run from Git Bash? | Invoke PowerShell for native Windows tox; use WSL2 for Linux tox from Windows. |
| 2 | Failure Analyst | Does Git Bash make Python report the wrong platform? | Not if Windows Python runs; `sys.platform` remains `win32`. PowerShell remains required for native Windows shell semantics. |

---

*Phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh*
*Spec created: 2026-05-23*
*Next step: $gsd-discuss-phase 15 — implementation decisions (how to build what's specified above)*
