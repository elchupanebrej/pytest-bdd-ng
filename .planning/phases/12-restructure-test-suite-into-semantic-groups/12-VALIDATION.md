---
phase: 12
slug: restructure-test-suite-into-semantic-groups
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-19
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
| Estimated runtime | TBD after Make target split |

## Sampling Rate

- After every task commit: run the nearest semantic slice, such as `make test-unit`, `make test-integration`, or `make test-contract`.
- After every plan wave: run `make test` plus targeted moved slice.
- Before `$gsd-verify-work`: run `make test-all` and `uvx --with tox-uv tox -l`; Docker/platform targets follow local availability.
- Max feedback latency: keep quick slice under 60 seconds where possible.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-W0-01 | TBD | 0 | TBD-01/TBD-02 | T-12-01 | N/A | unit/config | `uv run python -m pytest tests/cases/unit/test_test_suite_classification.py -q` | no W0 | pending |
| 12-W0-02 | TBD | 0 | TBD-03 | T-12-02 | env checks remain read-only | contract | `uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | no W0 | pending |
| 12-W0-03 | TBD | 0 | TBD-05 | T-12-03 | N/A | unit/static | `uv run python -m pytest tests/cases/unit/test_e2e_loader_shape.py -q` | no W0 | pending |
| 12-MIG-01 | TBD | TBD | TBD-04 | T-12-04 | moved tests remain equivalent | integration/smoke | `make test-unit && make test-integration && make test-contract` | after rewrite | pending |

## Wave 0 Requirements

- [ ] `tests/cases/unit/test_test_suite_classification.py` - validates semantic path mapping and no tests under assets.
- [ ] `tests/cases/contract/test_makefile_test_api.py` - validates required Make targets and read-only env checks.
- [ ] `tests/cases/unit/test_e2e_loader_shape.py` - forbids `scenarios(".")` and broad feature-directory loaders.
- [ ] Update existing group helper tests after path change.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker/external target policy | TBD-03/TBD-04 | Docker absent locally; explicit target must fail actionable or be skipped intentionally | Run `make env-check-docker` and confirm failure is read-only and actionable when Docker is absent |

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all missing references identified by research.
- [x] No watch-mode flags.
- [x] Feedback latency target documented.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** pending
