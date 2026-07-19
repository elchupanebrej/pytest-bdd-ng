---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: "17"
subsystem: allure-formatter
tags: [mypy, typing, allure]
provides: [strict-mypy-clean Allure formatter slice]
affects: [35-140-PLAN.md]
completed: 2026-07-16
status: complete
---

# Phase 35 Plan 17: Allure Formatter Typing Summary

The five-module Allure formatter slice is strict-mypy clean. Local protocols type pytest's cleanup registration and Allure's dynamically exposed lifecycle and hook relay; hook parameters and registry writes now carry concrete types.

Focused mypy and Ruff passed. Focused Allure formatter tests passed with `18 passed, 85 skipped` using `/tmp` as pytest's base directory; the default `/dev/shm` cleanup path is permission-blocked in this environment. Pylint remains blocked by pre-existing BLQ architecture-documentation findings in the legacy modules and was not changed by this plan.
