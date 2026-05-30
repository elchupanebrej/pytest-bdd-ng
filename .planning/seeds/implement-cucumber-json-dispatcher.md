---
title: Implement cucumber_json_dispatcher plugin
date: 2026-05-19
priority: medium
---

## Task

Create `src/pytest_bdd/plugin/cucumber_json_dispatcher/` as the central config dispatcher.

**Scope:**
- Register unified `--cucumber-json <path>` (CLI) and `cucumber_json_path` (INI)
- Register `--cucumber-json-engine={builtin|cucumber-js}` (default: `cucumber-js`)
- In `pytest_configure`: activate exactly one engine based on engine selector
- For `cucumber-js`: implement `pytest_bdd_cucumber_formatter_request` hook
- For `builtin`: instantiate and register `LogBDDCucumberJSON`
- Register as `pytest11` entrypoint in `pyproject.toml`

**Cleanup:**
- Remove standalone `pytest-bdd-cucumber-formatter-json` entrypoint
- Strip legacy `cucumber_json/entrypoint.py` to factory-only (no config reading)
