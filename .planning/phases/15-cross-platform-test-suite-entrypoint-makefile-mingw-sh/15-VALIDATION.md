---
phase: 15
slug: cross-platform-test-suite-entrypoint-makefile-mingw-sh
status: partial
nyquist_compliant: false
wave_0_complete: true
created: 2026-05-23
updated: 2026-05-24
---

# Phase 15 - Validation Strategy

Scope: Makefile cross-platform entrypoint, tox-backed platform routing, backend validation, argument forwarding, report modes, and DEVELOPMENT.rst documentation.

Source of truth: `ROADMAP.md` Phase 15, `15-SPEC.md`, `15-CONTEXT.md`, `15-01-PLAN.md`, `15-02-PLAN.md`, `15-03-PLAN.md`, and `VERIFICATION.md`.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest contract tests plus Makefile dry-run/static checks |
| Config file | `pyproject.toml` |
| Quick run command | `rtk uv run python -m pytest tests/cases/contract/test_makefile_test_api.py tests/cases/contract/doc/test_development_rst.py -q` |
| Full suite command | `rtk make test-contract` |
| Estimated runtime | ~1s quick, tox-dependent full run |

## Sampling Rate

- After every Makefile/docs task commit: run the quick contract command.
- After every Phase 15 wave: run `rtk uv run pre-commit run --files Makefile DEVELOPMENT.rst tests/cases/contract/test_makefile_test_api.py tests/cases/contract/doc/test_development_rst.py`.
- Before `$gsd-verify-work`: run `rtk make -n test-all FAIL_FAST=1 REPORT_MODE=skip` from Git Bash plus the quick contract command.
- Max feedback latency: under 5s for the quick contract slice.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Test File | Status |
|---------|------|------|-------------|-----------|-------------------|-----------|--------|
| 15-01-01 | 01 | 1 | OS detection, Git Bash guard, Windows short-path shell/PATH behavior | contract/static | `rtk uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | `tests/cases/contract/test_makefile_test_api.py` | green |
| 15-01-02 | 01 | 1 | `test-docker` compatibility target and Linux/Windows split Docker targets | contract/static | `rtk uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | `tests/cases/contract/test_makefile_test_api.py` | green |
| 15-01-03 | 01 | 1 | Cross-platform exit code 5 handling for `test-windows` and `test-posix` | contract/static | `rtk uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | `tests/cases/contract/test_makefile_test_api.py` | green |
| 15-02-01 | 02 | 2 | Cross-Platform Setup and canonical Make command docs | contract/docs | `rtk uv run python -m pytest tests/cases/contract/doc/test_development_rst.py -q` | `tests/cases/contract/doc/test_development_rst.py` | green |
| 15-03-01 | 03 | 3 | `test-all` validates backends before platform subwork and delegates to named platform targets | contract/static | `rtk uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | `tests/cases/contract/test_makefile_test_api.py` | green |
| 15-03-02 | 03 | 3 | Platform targets are tox-backed and use matching tox env/arg variables | contract/static | `rtk uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | `tests/cases/contract/test_makefile_test_api.py` | green |
| 15-03-03 | 03 | 3 | PowerShell, WSL2, Docker Windows, and custom Windows backend routing patterns exist | contract/static | `rtk uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | `tests/cases/contract/test_makefile_test_api.py` | green |
| 15-03-04 | 03 | 3 | `FAIL_FAST`, `ARTIFACT_MODE`, `REPORT_MODE`, and `TEST_*_ARGS` are public Make inputs | contract/static | `rtk uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | `tests/cases/contract/test_makefile_test_api.py` | green |
| 15-03-05 | 03 | 3 | DEVELOPMENT.rst documents tox-backed routing, backend requirements, modes, and args | contract/docs | `rtk uv run python -m pytest tests/cases/contract/doc/test_development_rst.py -q` | `tests/cases/contract/doc/test_development_rst.py` | green |

## Wave 0 Requirements

Existing infrastructure covers this phase:

- `tests/cases/contract/test_makefile_test_api.py` - Makefile API and Phase 15 static contract tests.
- `tests/cases/contract/doc/test_development_rst.py` - DEVELOPMENT.rst documentation contract tests.
- `pyproject.toml` - pytest configuration.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real Windows full backend run | Phase 15 human UAT 1 | Requires Git Bash, PowerShell, WSL2, Docker Desktop state, and Windows tox execution on a real Windows host | From Git Bash on Windows, run `rtk make test-all` with WSL2 and Docker Desktop available. Confirm PowerShell Windows tox, WSL2 Linux tox, optional Docker/external work, and report rendering follow documented collect/fail-fast behavior. |
| Real Linux/macOS non-native backend run | Phase 15 human UAT 2 | Requires Linux/macOS hosts with Docker or equivalent Windows-capable backend | On Linux and macOS, run `rtk make test-all` with Docker or `WINDOWS_TOX_BACKEND_COMMAND` configured. Confirm native tox and non-native Windows/Linux backend routing match docs. |

## Validation Audit 2026-05-24

| Metric | Count |
|--------|-------|
| Gaps found | 6 |
| Resolved | 6 |
| Escalated | 2 |

Resolved gaps:

- Added automated Makefile contract coverage for Phase 15 platform targets and backend validation.
- Added automated Makefile contract coverage for tox env/arg isolation.
- Added automated Makefile contract coverage for backend routing patterns.
- Added automated Makefile contract coverage for mode/argument variables.
- Added automated guard that legacy `NATIVE_TARGETS`/`DOCKER_TARGETS` routing variables stay removed.
- Added automated DEVELOPMENT.rst contract coverage for Phase 15 docs.

Escalated to manual-only:

- Real Windows full backend execution.
- Real Linux/macOS non-native backend execution.

## Validation Sign-Off

- [x] All tasks have automated verification or explicit manual-only coverage.
- [x] Sampling continuity: no 3 consecutive tasks without automated verification.
- [x] Wave 0 covers all missing automated contract checks.
- [x] No watch-mode flags.
- [x] Feedback latency under 5s for quick contract slice.
- [ ] `nyquist_compliant: true` set in frontmatter.

**Approval:** partial 2026-05-24; blocked only on real cross-host manual backend UAT.
