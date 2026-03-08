# Contract: Execution Message Adapter

## Scope

Defines the translation boundary between run-owned execution state and cucumber message envelopes used for reporting, replay, and governance.

## Allowed Inputs

Runtime source objects:
- `Run`
- `ScenarioRun`
- `FeatureRuntimeBinding`
- `GherkinDocument`
- `Source`
- `Pickle`
- `PickleStep`

Forbidden inputs:
- `src/pytest_bdd/model/gherkin_document/core.py::Feature`
- any compatibility wrapper that re-materializes feature metadata outside `Run`

## Responsibilities

`ExecutionMessageAdapter` MUST:
- serialize runtime lifecycle state to message payloads;
- deserialize message payloads into execution projections for validation and replay workflows;
- preserve deterministic IDs and cross-object reference links;
- operate without constructing or depending on a `Feature` adapter.

## Conversion Rules

1. Serialization:
- Must read correlation IDs from `Run.reporting_state`.
- Must derive feature-level metadata from the active `FeatureRuntimeBinding`.
- Must not create synthetic lifecycle IDs when state is missing.

2. Deserialization:
- Must resolve object IDs via `EnvelopeRegistry.identifiable`.
- Must expose projection objects that can resolve linked objects from the run-owned registry.
- Missing links produce deterministic diagnostics instead of fabricated objects.

3. Validation and reporting:
- Reporter transport receives adapter-normalized envelopes only.
- `message_validation.py` runs envelope projections through the adapter path before semantic checks.
- No adapter path may depend on `Feature` helper methods.

## Registry and ID Contract

- Canonical registry source: `Run.envelope_registry_from_pytest_stash(config)`.
- Canonical feature lookup source: `Run.feature_bindings_by_uri`.
- ID lookup key: stringified `Identifiable.id`.
- Transient optimization maps (for example `runtime_step_to_pickle_step_id`) are scenario-scoped only and are not canonical registry keys.

## Failure Handling

- Missing runtime context: deterministic warning/diagnostic and skip only context-dependent correlation fields.
- Missing feature binding: deterministic diagnostic; no fallback wrapper construction.
- Missing registry link: deterministic missing-reference diagnostic.
- Duplicate indexed IDs: deterministic overwrite behavior bound to insertion order.

## Validation Requirements

- Round-trip tests preserve IDs and reference relationships for runtime-required payloads.
- Reporter tests assert payload correlation uses run-owned feature bindings.
- Negative tests assert missing links and missing bindings do not trigger synthetic backfilling or `Feature` reconstruction.
