---
quick_id: 260602-lhn
slug: seems-file-locator-doesn-t-preserve-file
status: complete
---

# Quick Task 260602-lhn: Seems file locator doesn't preserve file order

## Must Haves

- Ensure `FileScenarioLocator._resolved_feature_paths` returns resolved paths in a deterministic, sorted order (for each directory/glob).
- Verify the change with tests, ensuring `test_file_locator_directory_expands_files` passes and the build remains green.
- Record the quick task execution in `STATE.md`.
- Generate completion summary file `260602-lhn-SUMMARY.md`.

## Tasks

| # | Action | Verify | Done |
|---|--------|--------|------|
| 1 | Sort the resolved feature paths in `FileScenarioLocator._resolved_feature_paths` using `sorted()`. | Code in `src/pytest_bdd/scenario_locator.py` is updated. | yes |
| 2 | Run unit tests to verify the fix and check for any regressions. | `pytest tests/cases/unit/unit/test_scenario_locator.py` passes successfully. | yes |
| 3 | Update `STATE.md` with the new quick task. | `STATE.md` contains the quick task table entry. | yes |
| 4 | Write summary file and mark task complete. | `260602-lhn-SUMMARY.md` exists and status is complete. | yes |
