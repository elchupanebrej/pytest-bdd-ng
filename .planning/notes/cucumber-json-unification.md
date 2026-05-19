---
title: Cucumber JSON unification decisions
date: 2026-05-19
context: Exploration session — unifying legacy and new cucumber JSON formatter config
---

## Decisions

**Engine selector:** `--cucumber-json-engine={builtin|cucumber-js}` (enum, defaults to `cucumber-js`)
- `builtin`: pure-Python legacy JSON generator, no external deps
- `cucumber-js`: delegates to Node.js cucumber-js via Cucumber Messages protocol

**Unified config surface:**
- One CLI flag `--cucumber-json <path>` and one INI key `cucumber_json_path` — same dest, same value source
- Central dispatcher plugin (`plugin/cucumber_json_dispatcher/`) owns both options, activates exactly one engine

**Architecture:**
- Dispatcher registers `--cucumber-json`, `cucumber_json_path`, `--cucumber-json-engine`
- For `cucumber-js` engine: dispatcher responds to `pytest_bdd_cucumber_formatter_request` hook
- For `builtin` engine: dispatcher instantiates legacy `LogBDDCucumberJSON` directly
- Existing `JsonFormatterPlugin` standalone entrypoint gets removed
- Legacy `cucumber_json/entrypoint.py` stripped down to factory only (no longer reads its own config)
