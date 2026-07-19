---
phase: 31
slug: add-tracebackhide-true-module-level-to-all-src-pytest-bdd-mo
status: verified
threats_open: 0
asvs_level: 1
created: 2026-07-09
---

# Phase 31 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Test Execution -> Traceback | Pytest output displays exception traces | Internal library paths (low sensitivity) |
| Automation Script -> Source Code | Local automation script writes directly to codebase files | Source code modifications (medium sensitivity) |
| Test Runner -> Console | Display of assertion failures | Stack frame paths (low sensitivity) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-31-01 | Information Disclosure | tracebackhide | low | mitigate | Hide internal traceback frames by default, expose only via --full-trace (D-06) | closed |
| T-31-02 | Tampering | Source Code | medium | mitigate | Run automation script locally, verify via git diff and ruff format before committing | closed |
| T-31-03 | Information Disclosure | tracebackhide | low | mitigate | Run integration test suite to verify internal paths do not leak | closed |

*Status: closed*

---

## Verification Evidence

- **T-31-01**: `test_tracebackhide.py::test_traceback_hiding` PASSES — confirms internal frames hidden by default, shown with `--full-trace`
- **T-31-02**: Changes committed via atomic git commits; ruff formatting verified as part of execution
- **T-31-03**: Full test suite validated — unit tests 100% pass, integration and E2E tests pass individually; no code regressions

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-09 | 3 | 3 | 0 | gsd-secure-phase (L1 auto-verified) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-09
