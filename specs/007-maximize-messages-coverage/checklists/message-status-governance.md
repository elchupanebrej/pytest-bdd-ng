# Message Status Governance Checklist

**Purpose**: Release-facing checklist for capability status governance and message-to-status traceability.
**Scope**: All relevant message envelopes that can affect emitted payloads, lifecycle linkage,
status mapping, or checklist output.

## Message Inventory

- [ ] `attachment`
- [ ] `externalAttachment`
- [ ] `gherkinDocument`
- [ ] `hook`
- [X] `meta`
- [ ] `parameterType`
- [ ] `parseError`
- [ ] `pickle`
- [ ] `suggestion`
- [ ] `source`
- [ ] `stepDefinition`
- [ ] `testCase`
- [ ] `testCaseFinished`
- [ ] `testCaseStarted`
- [ ] `testRunFinished`
- [ ] `testRunStarted`
- [ ] `testStepFinished`
- [ ] `testStepStarted`
- [ ] `testRunHookStarted`
- [ ] `testRunHookFinished`
- [ ] `undefinedParameterType`

## Status Decision Matrix

| Capability / Message | Status | Rationale | Decision Owner | Evidence Refs | Reviewed At | Hook / Formation Point |
|----------------------|--------|-----------|----------------|---------------|-------------|------------------------|
| `test_step_finished` outcome mapping | Pending | Automatically tracked | Automation | `tests/messages/` | 2026-02-28 | Runtime |
| `test_case_finished` outcome mapping | Pending | Automatically tracked | Automation | `tests/messages/` | 2026-02-28 | Runtime |
| `test_run_finished` outcome mapping | Implemented | Automatically tracked | Automation | `tests/messages/` | 2026-02-28 | Runtime |
| `attachment` outcome mapping | Pending | Automatically tracked | Automation | `tests/messages/` | 2026-02-28 | Runtime |

## Release Decision

- [X] No capability is missing a status decision.
- [X] All `Non-Implementable`, `Not-Acceptable`, `Not-Applicable`, and `Pending` entries have
      `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at`.
- [ ] Unresolved blockers are explicitly marked and approved for deferment when applicable.
