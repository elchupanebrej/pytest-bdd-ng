# Message Status Governance Checklist

**Purpose**: Release-facing checklist for capability status governance and message-to-status traceability.
**Scope**: All relevant message envelopes that can affect emitted payloads, lifecycle linkage,
status mapping, or checklist output.

## Message Inventory

- [ ] `meta`
- [ ] `source`
- [ ] `gherkin_document`
- [ ] `pickle`
- [ ] `step_definition`
- [ ] `parameter_type`
- [ ] `hook`
- [ ] `test_run_started`
- [ ] `test_case`
- [ ] `test_case_started`
- [ ] `test_step_started`
- [ ] `test_step_finished`
- [ ] `test_case_finished`
- [ ] `test_run_finished`
- [ ] `attachment`

## Status Decision Matrix

| Capability / Message | Status | Rationale | Decision Owner | Evidence Refs | Reviewed At | Hook / Formation Point |
|----------------------|--------|-----------|----------------|---------------|-------------|------------------------|
| `test_step_finished` outcome mapping | Pending |  |  |  |  | `pytest_bdd_after_step` / `pytest_bdd_step_error` |
| `test_case_finished` terminal status | Pending |  |  |  |  | `pytest_bdd_after_scenario` |
| `test_run_finished` release summary | Pending |  |  |  |  | `pytest_sessionfinish` |
| `attachment` governance metadata | Pending |  |  |  |  | `pytest_bdd_attach` |

## Release Decision

- [ ] No capability is missing a status decision.
- [ ] All `Non-Implementable`, `Not-Acceptable`, `Not-Applicable`, and `Pending` entries have
      `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at`.
- [ ] Unresolved blockers are explicitly marked and approved for deferment when applicable.
