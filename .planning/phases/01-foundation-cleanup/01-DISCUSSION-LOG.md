# Phase 1: Foundation Cleanup — Discussion Log

**Date:** 2026-05-12

## Areas Discussed

### Allure Plugin — Delete vs Re-implement

**Options presented:**
- Delete the entire allure_logger plugin + [allure] extra
- Re-implement the hook wiring to make it functional

**Selected:** Re-implement

**Clarification question:** The re-implementation scope is significant (wire up AllureLogger + PatchedAllureListener) — still Phase 1?

**Follow-up:** Defer to later phase — just remove dead code now, re-implement later.

**Decision:** Remove dead Allure entrypoint, plugin directory, [allure] extra, and associated test/ruff/mypy references. Re-implementation is a future effort.

---

### --cucumberjson Legacy Flag

**Options presented:**
- Add deprecation warning (original roadmap plan)
- Delete entirely — user stated: "don't warning, just delete"

**Selected:** Delete entirely

**Clarification question:** Breaking change risk for CI users — just delete, or emit error with hint?

**Follow-up:** Just delete — no transitional period.

**Decision:** Remove `--cucumberjson` from `pytest_addoption()`, no deprecation, no error hint. The `--cucumber-json` flag is the sole option going forward.

---

### DEPRECATIONS.md Format

**Options presented:**
- User to specify format
- Agent to determine format (user: "you have to find out format")

**Selected:** Agent's discretion

**Decision:** DEPRECATIONS.md is not created in this phase — no deprecations are introduced (everything is direct removal). Future phases that need deprecation paths will create it.

---

## Deferred Ideas

- Allure re-implementation — future phase after stabilization
- Other legacy CLI flag audit — Phase 11 (Audit & Prune)

## Summary

Phase 1 scope sharply narrowed: **removal only** — the dead Allure plugin and the legacy `--cucumberjson` flag are deleted without deprecation transitions. No DEPRECATIONS.md created since nothing is being deprecated. All re-implementation deferred.
