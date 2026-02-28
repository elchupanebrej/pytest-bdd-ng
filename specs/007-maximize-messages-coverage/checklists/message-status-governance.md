# Message Status Governance Checklist

**Purpose**: Release-facing checklist for capability status governance and message-to-status traceability.
**Scope**: All relevant message envelopes that can affect emitted payloads, lifecycle linkage,
status mapping, or checklist output.

## Message Inventory

- [X] `meta`
- [X] `source`
- [X] `gherkin_document`
- [X] `pickle`
- [X] `step_definition`
- [X] `parameter_type`
- [X] `hook`
- [X] `test_run_started`
- [X] `test_case`
- [X] `test_case_started`
- [X] `test_step_started`
- [X] `test_step_finished`
- [X] `test_case_finished`
- [X] `test_run_finished`
- [X] `attachment`

## Status Decision Matrix

| Capability / Message | Status | Rationale | Decision Owner | Evidence Refs | Reviewed At | Hook / Formation Point |
|----------------------|--------|-----------|----------------|---------------|-------------|------------------------|
| `test_step_finished` outcome mapping | Implemented | Automatically tracks pass/fail/skip outcomes derived from test_step_result | Automation | `tests/messages/test_coverage.py` | 2026-02-28 | `pytest_bdd_after_step` / `pytest_bdd_step_error` |
| `test_case_finished` terminal status | Implemented | Evaluates and normalizes capability status block (Implemented, Not-Acceptable, etc.) | Automation | `tests/messages/test_coverage.py` | 2026-02-28 | `pytest_bdd_after_scenario` |
| `test_run_finished` release summary | Implemented | Summarizes total test run success strictly matching internal outcome fields | Automation | `tests/messages/test_coverage.py` | 2026-02-28 | `pytest_sessionfinish` |
| `attachment` governance metadata | Implemented | Generates governance report attached directly to test artifacts | Automation | `tests/messages/test_governance.py` | 2026-02-28 | `pytest_bdd_attach` |

## Release Decision

- [X] No capability is missing a status decision.
- [X] All `Non-Implementable`, `Not-Acceptable`, `Not-Applicable`, and `Pending` entries have
      `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at`.
- [X] Unresolved blockers are explicitly marked and approved for deferment when applicable.
