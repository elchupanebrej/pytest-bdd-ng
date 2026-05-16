---
phase: 8
slug: bdd-acceptance-testing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-16
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=7.0.0 with pytester plugin |
| **Config file** | `pyproject.toml` under `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run python -m pytest tests/e2e/ -q -x` |
| **Full suite command** | `uv run python -m pytest tests/e2e/ -q` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run python -m pytest tests/e2e/ -q -x`
- **After every plan wave:** Run `uv run python -m pytest tests/e2e/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 8-01-01 | 01 | 1 | TEST-02 | T-8-01 / — | Go parser collection with Go available | BDD/e2e | `uv run python -m pytest tests/e2e/ -q` | ❌ W0 | ⬜ pending |
| 8-01-02 | 01 | 1 | TEST-02 | — | Tag expression complex boolean evaluation | BDD/e2e | `uv run python -m pytest tests/e2e/ -q` | ❌ W0 | ⬜ pending |
| 8-01-03 | 01 | 1 | TEST-02 | — | Heading validation policy enforcement | BDD/e2e | `uv run python -m pytest tests/e2e/ -q` | ❌ W0 | ⬜ pending |
| 8-01-04 | 01 | 1 | TEST-02 | — | Mimetype detection and routing | BDD/e2e | `uv run python -m pytest tests/e2e/ -q` | ❌ W0 | ⬜ pending |
| 8-01-05 | 01 | 1 | TEST-02 | — | StructBDD HOCON/TOML parsing | BDD/e2e | `uv run python -m pytest tests/e2e/ -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/e2e/steps_go_parser.py` — stubs for Go parser BDD scenarios
- [ ] `tests/e2e/steps_tag_expressions.py` — stubs for tag expression BDD scenarios
- [ ] `tests/e2e/steps_heading_validation.py` — stubs for heading validation BDD scenarios
- [ ] `tests/e2e/steps_mimetype.py` — stubs for mimetype BDD scenarios
- [ ] `tests/e2e/steps_formatters.py` — stubs for formatter BDD scenarios
- [ ] `tests/e2e/steps_code_generator.py` — stubs for code generator BDD scenarios
- [ ] `tests/e2e/steps_scenario_reporter.py` — stubs for scenario reporter BDD scenarios
- [ ] `tests/e2e/steps_compatibility.py` — stubs for compatibility layer BDD scenarios
- [ ] `tests/e2e/steps_batch_collection.py` — stubs for batch collection BDD scenarios

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Audit 47 existing feature files for consistency | TEST-02 | Qualitative review | Review each .feature.md for clarity, duplicate scenarios, standardized patterns |
| Generated docs in docs/features/ up to date | TEST-02 | Post-generation check | Run doc generation, verify output matches feature files |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
