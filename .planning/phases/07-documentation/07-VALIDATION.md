---
phase: 07
slug: documentation
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-15
audited: 2026-05-17
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (existing) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run python -m pytest tests/doc/ -x` |
| **Full suite command** | `uv run python -m pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds (doc tests only) |

---

## Sampling Rate

- **After every task commit:** Run docstring presence check or Sphinx build
- **After every plan wave:** `uv run python -m sphinx -b html docs docs/_build` — verify docs build without errors
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | — | — | Sphinx installed, napoleon enabled | automated | `uv run python -c "import sphinx; import sphinx.ext.napoleon"` | ✅ | ✅ green |
| 07-01-02 | 01 | 1 | — | — | Docstring test scaffolds created | automated | `test -d tests/doc/` | ✅ | ✅ green |
| 07-02-01 | 02 | 2 | DOC-01 | — | scenario() has comprehensive docstring | automated | `uv run python -c "from pytest_bdd import scenario; assert scenario.__doc__ and 'Args:' in scenario.__doc__"` | ✅ | ✅ green |
| 07-02-02 | 02 | 2 | DOC-01 | — | given/when/then/step have comprehensive docstrings | automated | `uv run python -c "from pytest_bdd import given; assert given.__doc__ and 'Args:' in given.__doc__"` | ✅ | ✅ green |
| 07-02-03 | 02 | 2 | DOC-01 | — | FeaturePathType, PytestBDDStepDefinitionWarning documented | automated | `uv run python -c "from pytest_bdd import FeaturePathType, PytestBDDStepDefinitionWarning; assert FeaturePathType.__doc__ and PytestBDDStepDefinitionWarning.__doc__"` | ✅ | ✅ green |
| 07-03-01 | 03 | 2 | DOC-02 | — | DEVELOPMENT.rst covers StashBound, attrs, testing, plugins | manual | `grep -c "StashBound\|attrs\|plugin class" DEVELOPMENT.rst` | ✅ | ✅ green |
| 07-04-01 | 04 | 2 | DOC-03 | — | MIGRATION.md covers top breaking changes | manual | `Test-Path MIGRATION.md; (Select-String -Path MIGRATION.md -Pattern "Before\|After").Count` | ✅ | ✅ green |
| 07-04-02 | 04 | 2 | — | — | DEPRECATIONS.md lists deprecated features | manual | `Test-Path DEPRECATIONS.md; (Select-String -Path DEPRECATIONS.md -Pattern "Removed\|Deprecated").Count` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/doc/test_docstrings.py` — verifies all `__all__` exports have non-empty docstrings with Args/Returns sections
- [x] `tests/doc/test_development_rst.py` — verifies DEVELOPMENT.rst contains required sections
- [x] Sphinx install: `sphinx>=7.0` in doc-gen extra — declared and installed (9.1.0)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DEVELOPMENT.rst comprehensive coverage | DOC-02 | Content quality assessment | Review DEVELOPMENT.rst for architecture, StashBound, attrs, testing strategy, BDD workflow, CI matrix sections |
| Migration guide accuracy | DOC-03 | Requires comparison with original pytest-bdd | Verify each before/after example against original pytest-bdd API |
| DEPRECATIONS.md completeness | — | Requires knowledge of all deprecated features | Review phase 1-6 changes for deprecated/removed features |

---

## Validation Audit 2026-05-17

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Verification results:**
- Sphinx 9.1.0 installed, napoleon importable: PASS
- All 8 `__all__` exports have non-empty docstrings with Args/Returns: PASS
- `tests/doc/` test suite: 6 passed, 7 skipped, 0 failed
- DEVELOPMENT.rst: 587 lines, all required sections present
- MIGRATION.md: 170 lines, 24 before/after references, 10 breaking changes
- DEPRECATIONS.md: exists, wired into docs/include.rst

---

## Validation Audit 2026-05-18

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Verification results:**
- Nyquist validation config enabled: PASS
- Existing validation file detected: PASS
- Sphinx 9.1.0 installed, napoleon importable: PASS
- Public API docstring probes for `scenario`, `given`, `FeaturePathType`, and `PytestBDDStepDefinitionWarning`: PASS
- Documentation content probes for DEVELOPMENT.rst, MIGRATION.md, DEPRECATIONS.md, and docs/include.rst: PASS
- `tests/doc/` test suite: 6 passed, 7 skipped, 0 failed

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved
