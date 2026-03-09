# Data Model: Distributed Reporting Stream

## Entity: DistributedReportingRun

Purpose: Canonical aggregation root for one pytest execution that may include one controller and multiple xdist workers across local or remote gateways.

Fields:
- `run_id: str` (required, logical test-run identifier)
- `protocol_version: str` (required)
- `transport_mode: execnet_channel_events` (required)
- `controller_worker_id: str` (required, canonical controller identity such as `master`)
- `participants: dict[str, DistributedRunParticipant]`
- `structural_identity_index: dict[str, StructuralIdentity]`
- `id_remap_index: dict[tuple[str, str], CanonicalIdRemap]`
- `scenario_attempts: dict[str, ScenarioAttemptRecord]`
- `diagnostics: list[ConsolidationDiagnostic]`
- `status: collecting | consolidating | finalized | partial | failed`

Relationships:
- Owns many `DistributedRunParticipant` records.
- Owns one `XdistChannelAdapterCapability`.
- Owns many `WorkerChannelBatch` records through participants.
- Owns many `WorkerCompletionManifest` records through participants.
- Owns many `StructuralIdentity`, `CanonicalIdRemap`, `ScenarioAttemptRecord`, and `ConsolidationDiagnostic` records.

Validation rules:
- Exactly one final consolidated NDJSON stream is emitted for a finalized or partial run.
- `status=finalized` requires a valid final NDJSON artifact and no unresolved canonical-reference errors.
- `status=partial` requires at least one incomplete participant diagnostic and a still-valid final NDJSON stream.
- `status=failed` is used when xdist/channel compatibility cannot safely support the required transport.

State transitions:
- `collecting -> consolidating -> finalized`
- `collecting -> consolidating -> partial`
- `collecting -> failed`
- `consolidating -> failed`

## Entity: XdistChannelAdapterCapability

Purpose: Captures whether the active xdist session can host the project-local remote-module adapter and the namespaced reporting events required by this feature.

Fields:
- `xdist_version: str | None`
- `execnet_version: str | None`
- `remote_module_hook_available: bool`
- `channel_event_support: bool`
- `supported_gateway_modes: set[str]` (`popen`, `ssh`, `socket`, `via`)
- `diagnostic: str | None`
- `mode: compatible | incompatible`

Relationships:
- Belongs to one `DistributedReportingRun`.

Validation rules:
- `mode=compatible` requires `remote_module_hook_available=true` and `channel_event_support=true`.
- `mode=incompatible` requires a non-empty diagnostic and forces fail-fast behavior before distributed reporting starts.

## Entity: DistributedRunParticipant

Purpose: Controller or worker process contributing structural or runtime data to the logical run.

Fields:
- `participant_id: str` (required, unique within the run)
- `worker_id: str` (required, xdist worker or controller identifier)
- `role: controller | worker`
- `gateway_mode: popen | ssh | socket | via`
- `transport_state: awaiting | streaming | complete | interrupted | incompatible`
- `manifest_received: bool`
- `highest_batch_sequence: int | None`
- `received_envelope_count: int`

Relationships:
- Belongs to one `DistributedReportingRun`.
- Produces many `WorkerChannelBatch` records.
- Produces zero or one `WorkerCompletionManifest`.

Validation rules:
- `worker_id` is unique within one run.
- Only workers emit `WorkerChannelBatch` and `WorkerCompletionManifest` records.
- `transport_state=complete` requires a manifest with `complete=true`.

## Entity: WorkerChannelBatch

Purpose: Execnet-serializable reporting payload transferred from a worker to the controller as a namespaced xdist event.

Fields:
- `event_name: str` (required, namespaced event such as `pytest_bdd_message_chunk`)
- `worker_id: str` (required)
- `batch_sequence: int` (required, monotonic per worker)
- `envelopes: list[dict[str, object]]` (required, builtin-type payload dictionaries only)
- `is_terminal_batch: bool`
- `byte_count: int`

Relationships:
- Belongs to one `DistributedRunParticipant`.
- References one `DistributedReportingRun` through the participant.

Validation rules:
- `batch_sequence` is strictly increasing per worker.
- `event_name` is reserved to the reporter namespace and must not collide with built-in xdist event names.
- `envelopes` must be execnet-serializable builtin containers only.
- Per-batch envelope order is preserved during consolidation.

## Entity: WorkerCompletionManifest

Purpose: Terminal worker status published through `config.workeroutput` and received by the controller when xdist emits `workerfinished`.

Fields:
- `worker_id: str` (required)
- `complete: bool`
- `last_batch_sequence: int | None`
- `transferred_batch_count: int`
- `transferred_envelope_count: int`
- `interruption_reason: str | None`
- `gateway_mode: popen | ssh | socket | via`

Relationships:
- Belongs to one `DistributedRunParticipant`.

Validation rules:
- A worker emits at most one manifest per run.
- `complete=false` requires an `interruption_reason` or a matching controller diagnostic.
- `complete=true` requires `last_batch_sequence` to equal the participant's highest received batch sequence.

## Entity: StructuralIdentity

Purpose: Stable semantic identity for structural payloads that must appear only once in the final stream.

Fields:
- `identity_key: str` (required)
- `payload_kind: str` (required)
- `source_uri: str | None`
- `feature_uri: str | None`
- `scenario_anchor: str | None`
- `step_anchor: str | None`
- `hook_anchor: str | None`
- `canonical_id: str` (required)

Relationships:
- Belongs to one `DistributedReportingRun`.
- May be referenced by many `CanonicalIdRemap` records.

Validation rules:
- One semantic `identity_key` resolves to exactly one `canonical_id`.
- Structural identity never depends on worker ID, gateway mode, fragment path, or arrival time.

## Entity: CanonicalIdRemap

Purpose: Maps a worker-local structural ID to the canonical controller-owned ID retained in the final stream.

Fields:
- `worker_id: str` (required)
- `payload_kind: str` (required)
- `origin_id: str` (required)
- `canonical_id: str` (required)
- `identity_key: str` (required)

Relationships:
- Belongs to one `DistributedReportingRun`.
- References one `StructuralIdentity`.

Validation rules:
- Every worker-local structural ID maps to one canonical ID at most once.
- Runtime envelopes referencing remapped structural IDs must be rewritten before final NDJSON emission.

## Entity: ScenarioAttemptRecord

Purpose: Canonical record of one real runtime execution attempt preserved from distributed workers.

Fields:
- `scenario_attempt_id: str` (required)
- `worker_id: str` (required)
- `gateway_mode: popen | ssh | socket | via`
- `attempt_index: int` (required, `>= 0`)
- `test_case_id: str` (required, canonical structural reference)
- `test_case_started_id: str` (required)
- `step_ids: list[str]`
- `final_status: passed | failed | skipped | interrupted | unfinished`
- `sequence_bounds: tuple[int, int] | None`

Relationships:
- Belongs to one `DistributedReportingRun`.
- References one canonical structural test case.
- Owns many execution envelopes in the final stream.

Validation rules:
- Scenario attempts are never deduplicated merely because they point to the same scenario structure.
- `worker_id + attempt_index + canonical scenario anchor` remains sufficient for diagnostics and traceability.

## Entity: ConsolidatedEnvelope

Purpose: Envelope after controller-side classification, canonicalization, and ordering, ready for final NDJSON emission.

Fields:
- `payload_kind: str` (required)
- `payload_id: str | None`
- `classification: controller_singular | structural_deduplicated | execution_preserved`
- `worker_id: str | None`
- `gateway_mode: str | None`
- `sequence_in_worker: int | None`
- `canonical_refs: dict[str, str]`

Relationships:
- Originates from one `WorkerChannelBatch` or controller-local emission.
- Is emitted by one `DistributedReportingRun`.

Validation rules:
- Exactly one payload kind is present.
- `classification=structural_deduplicated` payloads must point only to canonical structural IDs.
- `classification=execution_preserved` payloads may remain per-attempt unique but must not reference discarded structural records.

## Entity: ConsolidationDiagnostic

Purpose: Structured signal describing duplicate suppression, partial worker transfer, unsupported compatibility, or invalid canonical references.

Fields:
- `code: duplicate_structural_payload | missing_worker_manifest | interrupted_worker_transfer | unsupported_xdist_channel | unresolved_runtime_reference | partial_stream`
- `severity: info | warning | error`
- `worker_id: str | None`
- `gateway_mode: str | None`
- `message: str` (required)
- `affected_ids: list[str]`

Relationships:
- Belongs to one `DistributedReportingRun`.

Validation rules:
- `code=unsupported_xdist_channel` is emitted only for fail-fast compatibility aborts.
- A partial run must emit at least one `partial_stream`, `missing_worker_manifest`, or `interrupted_worker_transfer` diagnostic.
- `severity=error` blocks final emission only when canonical references cannot be repaired deterministically.

## Modeling Note

- GitHub CI routing and Python-versus-bash helper choices are operational validation constraints only. They do not introduce additional runtime entities or change the controller-owned consolidation model described above.
