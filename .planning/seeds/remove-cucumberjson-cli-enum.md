---
title: Remove CucumberJson.Cli enum
trigger_condition: When dispatcher plugin renders legacy entrypoint config-reading obsolete
planted_date: 2026-05-19
---

`CucumberJson.Cli` in `src/pytest_bdd/plugin/cucumber_json/const.py` is dead code (removed CLI flag in Phase 01-02, D-10). The enum definition and test assertion in `test_cucumber_formatter_cli_contract.py:150` should be cleaned up once the dispatcher plugin removes the last reason to keep it.
