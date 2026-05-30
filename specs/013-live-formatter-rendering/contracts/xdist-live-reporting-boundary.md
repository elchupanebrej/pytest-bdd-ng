# Contract: Xdist Live Reporting Boundary

## Purpose

Define the boundary between distributed worker reporting and controller-owned
live formatter rendering.

## Participants

| Participant | Responsibility |
|-------------|----------------|
| Worker reporter | Emits execution envelopes locally and publishes incremental batches to the controller boundary. |
| Controller reporting authority | Receives local and remote envelopes through the message-stream orchestration plugin, owns live formatter execution, and maintains final consistency artifacts. |
| Live formatter session | Consumes the unified live envelope stream and renders console/file outputs according to formatter behavior. |
| Canonical message stream | Stores the final consolidated NDJSON artifact used for validation and compatibility replay. |

## Boundary Messages

| Message | Producer | Consumer | Required fields | Guarantee |
|---------|----------|----------|-----------------|-----------|
| `batch-publish` | Worker reporter | Controller reporting authority | `source_id`, `batch_sequence`, `envelopes[]` | Preserves order within `source_id`. |
| `source-complete` | Worker reporter | Controller reporting authority | `source_id`, `last_batch_sequence`, `transferred_envelope_count`, `interruption_reason?` | Declares whether a source completed cleanly. |
| `local-envelope` | Controller-local reporter flow | Controller reporting authority | `source_id`, `envelope` | Uses the same live-session contract as remote batches. |
| `session-close` | Controller reporting authority | Live formatter session | `session_id`, `run_status` | Stops new delivery and finalizes formatter cleanup. |

## Invariants

1. Exactly one controller/main authority renders live formatter output during a
   distributed run.
2. Worker authorities publish batches but do not render formatter output.
3. Message order must be preserved within each `source_id`.
4. Cross-source live interleaving follows controller arrival order; the system
   does not block live output on a reconstructed total global order.
5. Canonical NDJSON remains the final validation and replay artifact after live
   rendering has occurred.

## Failure Handling

1. Missing or interrupted source completion manifests must be surfaced as an
   actionable runtime/reporting error.
2. Delivery failure in one source must not authorize worker-local fallback
   rendering.
3. The controller may terminate the live formatter session as failed if the
   stream can no longer be trusted.

## Out of Scope

- Rendering directly from worker-local stdout during distributed runs
- Global cross-source reordering before any live formatter output appears
