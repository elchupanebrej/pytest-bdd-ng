# Requirements Intel

Generated: 2026-06-20
Mode: merge
Ingest set: 4 documents

## Extracted Requirements

- P26-DEV-01: Add a Development BDD feature space covering repository-specific scripts, CLIs, and pre-commit quality gates.
- P26-DEV-02: Add shared development step definitions for mock file setup, command execution in the test directory, exit-code checks, and stdout/stderr assertions.
- P26-DEV-03: Register development steps in the E2E conftest and add an E2E loader for `features/18 Development/`.
- P26-DEV-04: Cover the `allure-cucumber` converter CLI with success and missing-input scenarios.
- P26-DEV-05: Cover `validate_feature_headings.py` clean and failing heading validation scenarios.
- P26-DEV-06: Cover `scripts/arch.py` responsibility injection, score collection, and gap analysis scenarios.
- P26-DEV-07: Cover the `compatibility_matrix` CLI compatibility, tox environment, and E2E migration-report scenarios.
- P26-DEV-08: Cover `sync_messages_contract_schemas.py` clean and drift scenarios.
- P26-DEV-09: Cover `render_cucumber_formatters` standalone NDJSON-to-summary rendering.
- P26-DEV-10: Cover `scripts/run_messages_coverage_audit.sh` governance report orchestration.
- P26-DEV-11: Update Phase 26 roadmap/planning artifacts with goals, success criteria, blockers, and verification commands.

## Completion Signals from Ingested Checklist

- All seven planned Development feature files are marked complete in `specs/026-dev-scripts-bdd/tasks.txt`.
