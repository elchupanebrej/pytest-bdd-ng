---
phase: 12
slug: restructure-test-suite-into-semantic-groups
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-19
validated: 2026-05-19
---

# Phase 12 - Validation Strategy

Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 local, tox 4.54.0 local |
| Config file | `pyproject.toml`, `tox.ini`, `Makefile` |
| Quick run command | `uv run python -m pytest tests/cases/unit tests/cases/integration -q` |
| Full suite command | `make test-all` |
| Estimated runtime | ~10 min (unit: 32s, integration: 262s, contract: 243s, e2e: 79s, compat: 3s, perf: 9s, slow: 99s) |

## Sampling Rate

- After every task commit: run the nearest semantic slice, such as `make test-unit`, `make test-integration`, or `make test-contract`.
- After every plan wave: run `make test` plus targeted moved slice.
- Before `$gsd-verify-work`: run `make test-all` and `uvx --with tox-uv tox -l`; Docker/platform targets follow local availability.
- Max feedback latency: keep quick slice under 60 seconds where possible.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-W0-01 | 12-01 | 0 | P12-01/P12-05 | T-12-01 | N/A | unit/config | `uv run python -m pytest tests/cases/unit/test_test_suite_classification.py -q` | no W0 | pass |
| 12-W0-02 | 12-01 | 0 | P12-02/P12-03 | T-12-02 | env checks remain read-only | contract | `uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | no W0 | pass |
| 12-W0-03 | 12-01 | 0 | P12-05 | T-12-03 | N/A | unit/static | `uv run python -m pytest tests/cases/unit/test_e2e_loader_shape.py -q` | no W0 | pass |
| 12-MIG-01 | 12-02/12-03/12-04 | 1/2/3 | P12-01/P12-04/P12-06/P12-07 | T-12-04 | moved tests remain equivalent | integration/smoke | `make test-unit && make test-integration && make test-contract` | after rewrite | pass |

## Wave 0 Requirements

- [x] `tests/cases/unit/test_test_suite_classification.py` - validates semantic path mapping and no tests under assets.
- [x] `tests/cases/contract/test_makefile_test_api.py` - validates required Make targets and read-only env checks.
- [x] `tests/cases/unit/test_e2e_loader_shape.py` - forbids `scenarios(".")` and broad feature-directory loaders.
- [x] Update existing group helper tests after path change.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker/external target policy | P12-03/P12-07 | Docker absent locally; explicit target must fail actionable or be skipped intentionally | Run `make env-check-docker` and confirm failure is read-only and actionable when Docker is absent |

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all missing references identified by research.
- [x] No watch-mode flags.
- [x] Feedback latency target documented.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** ✅ validated by Plan 12-06 — all Wave 0 guards pass, semantic slices pass, tox -l resolves, stale import audit clean, Docker/external targets correctly gated behind env-check failures per D-10.
