# Decisions Intel

Generated: 2026-06-20
Mode: merge
Ingest set: 4 documents

## Locked Decisions

None. No ADRs were included and no ingested document marks decisions as locked.

## Candidate Decisions

- Phase 26 should be the planning home for repository development-script ATDD/BDD coverage.
- Development-script coverage should live in a focused `features/18 Development/` feature directory.
- E2E support should use shared generic development steps for command execution, mock file creation, exit-code checks, and output checks.
- Coverage should prioritize user-facing CLIs and quality gates before lower-priority internal sync helpers.
- Existing implementation work under `features/18 Development/` and `src/pytest_bdd_testing/step/development.py` should be preserved during merge.

## Existing-Context Notes

- `.planning/ROADMAP.md` already contains a Phase 26 stub.
- `.planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/` exists but only contains `.gitkeep`.
- `.planning/REQUIREMENTS.md` was checked for unresolved merge conflict markers before destination-file updates.
