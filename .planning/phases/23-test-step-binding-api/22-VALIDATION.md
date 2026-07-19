# Phase 22: Test/Step binding API - Validation Plan

**Created:** 2026-06-05
**Status:** Nyquist compliant
**Source:** Phase 22 SPEC, CONTEXT, RESEARCH, and PLAN artifacts
**Last audited:** 2026-06-06

## Validation Goal

Prove `--mock-run --messages-ndjson` is a reliable IDE bootstrap contract for launch mapping, exact step bindings, scoped diagnostics, and source binding cardinality while preserving mock-run no-execution guarantees.

## Requirement Coverage

| Requirement | Validation | Status |
|-------------|------------|--------|
| P22-01 | `tests/cases/integration/messages/test_ide_binding_contract.py::test_ide_bootstrap_messages_and_probes` runs `pytest --mock-run --messages-ndjson report.ndjson`, asserts Source, GherkinDocument, Pickle, StepDefinition, TestCase, launch attachment payloads, and verifies hook/body probe files are absent. | COVERED |
| P22-02 | `tests/cases/integration/messages/test_ide_binding_contract.py::test_runnable_launch_mapping` parses launch attachments and runs `pytest <nodeid>` for a simple scenario, proving the nodeid selects exactly one item. | COVERED |
| P22-03 | `tests/cases/integration/messages/test_ide_binding_contract.py::test_examples_row_launch_mapping` asserts each Examples row has a distinct launch payload and each nodeid runs only that row. | COVERED |
| P22-04 | `tests/cases/integration/messages/test_ide_binding_diagnostics.py::test_binding_cardinality_diagnostics` covers zero, one, and multiple source Feature/Scenario hookups, with warnings only for zero and multiple. | COVERED |
| P22-05 | `tests/cases/integration/messages/test_ide_binding_diagnostics.py::test_binding_cardinality_diagnostics` binds the same source scenario from two pytest modules, asserts one source-level warning, and preserves both runnable handles. | COVERED |
| P22-06 | `tests/cases/integration/messages/test_ide_binding_contract.py::test_launch_metadata_isolation` proves launch metadata uses Attachment JSON, not tags or marks, and does not alter `-m`, tag expressions, or tag hooks. | COVERED |
| P22-07 | `tests/cases/integration/messages/test_ide_step_bindings.py::test_matched_step_bindings` covers string, parse, regex, and cfparse-style patterns, resolving each PickleStep to expected StepDefinition sourceReference and match arguments. | COVERED |
| P22-08 | `tests/cases/integration/messages/test_ide_step_bindings.py::test_missing_step_diagnostics` and `test_ambiguous_step_diagnostics` assert scoped available definitions and candidate definitions are emitted as diagnostic attachments. | COVERED |
| TEST-02 | `features/13 Code Generator/01 Code generation.feature.md` and `tests/cases/e2e/steps_code_generator.py` document and execute mock-run IDE bootstrap, missing-step/codegen-adjacent diagnostics, and duplicate source binding warnings. | COVERED |

## Test Infrastructure

| Layer | Files | Command |
|-------|-------|---------|
| Integration message contract | `tests/cases/integration/messages/test_ide_binding_contract.py`, `tests/cases/integration/messages/test_ide_binding_diagnostics.py`, `tests/cases/integration/messages/test_ide_step_bindings.py` | `rtk proxy uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py tests/cases/integration/messages/test_ide_binding_diagnostics.py tests/cases/integration/messages/test_ide_step_bindings.py tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_step_matching_ambiguous.py -q` |
| Feature-level ATDD | `features/13 Code Generator/01 Code generation.feature.md`, `tests/cases/e2e/steps_code_generator.py` | `rtk proxy uv run pytest tests/cases/e2e/e2e/test_feature_058_code_generator.py -q -k "IDE or duplicate"` |
| Docs contract | `docs/features/`, feature ordering contract | `rtk proxy uv run pytest tests/cases/contract/doc tests/cases/contract/contract/test_feature_doc_ordering_contract.py -q` |

## Per-Task Map

| Task | Requirements | Automated Coverage | Status |
|------|--------------|--------------------|--------|
| 22-01 | P22-01, P22-02, P22-03, P22-04, P22-05, P22-06, P22-07, P22-08 | Contract tests under `tests/cases/integration/messages/` plus mock-run probe regression in `tests/cases/integration/feature/test_mock_run.py`. | COVERED |
| 22-02 | P22-02, P22-03, P22-04, P22-05, P22-06 | Launch and cardinality tests in `test_ide_binding_contract.py` and `test_ide_binding_diagnostics.py`. | COVERED |
| 22-03 | P22-01, P22-07, P22-08 | Step binding, missing-step, ambiguous-step, mock-run, and ambiguous matching tests. | COVERED |
| 22-04 | P22-01, P22-02, P22-03, P22-04, P22-05, P22-06, P22-07, P22-08, TEST-02 | Feature-level ATDD slice and docs contract tests. | COVERED |

## Manual-Only

None. All Phase 22 requirements have automated verification.

## Execution Gates

1. Plan 22-01 creates failing contract tests and `22-HOOK-TAXONOMY.md`.
2. Plan 22-02 makes launch and cardinality tests pass.
3. Plan 22-03 makes matched, missing, and ambiguous step binding tests pass.
4. Plan 22-04 adds feature-level ATDD and runs final targeted verification.

## Automated Commands

```powershell
rtk proxy uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py tests/cases/integration/messages/test_ide_binding_diagnostics.py tests/cases/integration/messages/test_ide_step_bindings.py tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_step_matching_ambiguous.py -q
rtk proxy uv run pytest tests/cases/e2e/e2e/test_feature_058_code_generator.py -q -k "IDE or duplicate"
rtk proxy uv run pytest tests/cases/contract/doc tests/cases/contract/contract/test_feature_doc_ordering_contract.py -q
```

## Nyquist Checks

- Contract boundary: tests observe NDJSON payloads, not private helper return values.
- Negative space: tests prove hook/body probe files are not created during mock-run.
- Row specificity: Examples rows are validated by executing returned nodeids, not by string shape alone.
- Scope correctness: missing/ambiguous diagnostics are validated against the request-local step registry universe.
- Isolation: attachment carrier is validated against user tag/mark behavior.

## Exit Criteria

Phase 22 is execution-complete only when all targeted integration tests and feature-level ATDD gates pass without xfail/skip markers added for Phase 22 behavior.

## Validation Audit 2026-06-06

| Metric | Count |
|--------|-------|
| Requirements audited | 9 |
| Covered | 9 |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Verified commands:

```powershell
rtk proxy uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py tests/cases/integration/messages/test_ide_binding_diagnostics.py tests/cases/integration/messages/test_ide_step_bindings.py tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_step_matching_ambiguous.py -q
rtk proxy uv run pytest tests/cases/e2e/e2e/test_feature_058_code_generator.py -q -k "IDE or duplicate"
rtk proxy uv run pytest tests/cases/contract/doc tests/cases/contract/contract/test_feature_doc_ordering_contract.py -q
```

Results: 17 integration tests passed, 3 feature-level ATDD tests passed, and 26 docs contract tests passed. No manual-only validation remains.
