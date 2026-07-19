# Constraints Intel

Generated: 2026-06-20
Mode: merge
Ingest set: 4 documents

## Implementation Constraints

- Use repository ATDD/BDD conventions: feature files under `features/`, E2E loaders under `src/pytest_bdd_testing/case/e2e/feature/`, and shared steps under `src/pytest_bdd_testing/step/`.
- Preserve xdist and existing E2E harness behavior.
- Use isolated temporary files/directories for CLI scenarios.
- Do not require global environment mutation for feature scenarios.
- `07 Messages Coverage Audit.feature.md` has a known blocker: the `undefined_parameter` runtime probe currently fails during collection with `step_matcher` fixture resolution / reporter teardown behavior.

## Verification Constraints

- Primary test target: `pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py`.
- Also run lint/custom-rule checks after implementation.
- Preserve unrelated dirty working-tree files.

## Merge Constraints

- Destination planning updates require `.planning/REQUIREMENTS.md` to remain free of merge conflict markers.
