---
status: complete
quick_id: 260602-lhn
---

# Quick Task 260602-lhn Summary

## Completed

- Updated `FileScenarioLocator._resolved_feature_paths` in `src/pytest_bdd/scenario_locator.py` to wrap the yielded files from both directories and glob patterns with `sorted()`. This ensures a deterministic, stable, alphabetical resolution order when loading Gherkin/Markdown feature files.
- Commented out the unsupported `PLW0717` rule in `pyproject.toml` ignore list to resolve local ruff parsing errors.
- Verified that all unit tests in `tests/cases/unit/unit/test_scenario_locator.py` and `tests/cases/unit/unit/test_no_commented_code.py` pass.
- Recorded the quick task execution in `.planning/STATE.md`.
