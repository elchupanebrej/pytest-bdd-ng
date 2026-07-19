---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: "15"
subsystem: allure-formatter
tags: [mypy, typing, allure]
provides: [strict-mypy-clean Allure adapter slice]
affects: [35-140-PLAN.md]
completed: 2026-07-16
status: complete
---

# Phase 35 Plan 15: Allure Formatter Typing Summary

Focused mypy and Ruff passed. Focused Allure adapter and hook tests passed.

- Replaced dynamic plugin-hook access with a local callable boundary.
- Normalized Allure status, stage, and UUID values before sending them to the typed lifecycle API.
- Removed obsolete API-hook type ignores and made its parameter mapping concrete.

Targeted Pylint remains blocked by pre-existing documentation checks in unmodified Allure modules.
