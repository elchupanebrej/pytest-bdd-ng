# Contract Fixture: Xdist Consolidated Message Stream

## Scope

Defines the canonical NDJSON stream produced by `--messages-ndjson` when
pytest-bdd runs under `pytest-xdist`, including remote worker topologies where participants do not share a filesystem and communicate through execnet.

## Contract Goal

The final NDJSON output for a distributed run MUST behave like one logical
reporting stream:
- structural payloads appear once per logical run;
- execution payloads remain complete for every worker execution attempt
  transferred before worker shutdown or interruption;
- the resulting stream stays valid for current validators, governance tooling,
  and downstream report derivation;
- local and remote xdist execution does not require the controller to open
  worker-local report files or a reporter-managed side-channel socket.

## Input Model

The consolidation stage consumes:
- one controller participation context;
- zero or more worker chunk batches transferred as namespaced xdist channel
  events;
- one optional completion manifest per worker from `workeroutput`;
- per-envelope payload kind classification;
- canonical remap metadata for structural identifiers.

## Transport Preconditions

- Worker-to-controller transfers use execnet-serializable builtin payloads
  only.
- Worker-local files may exist as transient spool or crash buffers, but they
  are not part of the final consolidation contract.
- The controller must be able to finalize the stream from transferred chunk data plus completion manifests alone.

## Payload Classes

### Controller-Singular Payloads

These payloads appear exactly once in the final stream:
- `meta`
- `test_run_started`
- `test_run_finished`

Rules:
- Worker-local copies never become duplicate final output.
- The emitted payload must describe the logical run, not one worker fragment.

### Structural-Deduplicated Payloads

These payloads represent run-wide structure and appear at most once per semantic
identity:
- `source`
- `gherkin_document`
- `pickle`
- `step_definition`
- `parameter_type`
- `hook`
- `test_case`

Rules:
- Deduplication uses semantic identity and source anchors, not worker-local
  generated IDs, gateway mode, batch sequence numbers, or fragment paths.
- The controller assigns one canonical ID for each retained structural
  identity.
- Every reference from preserved runtime payloads is rewritten to canonical
  structural IDs before final emission.

### Execution-Preserved Payloads

These payloads represent real runtime behavior and are preserved for every
valid execution attempt:
- `test_run_hook_started`
- `test_run_hook_finished`
- `test_case_started`
- `test_step_started`
- `test_step_finished`
- `test_case_finished`
- `attachment`
- `external_attachment`
- `suggestion`
- `undefined_parameter_type`
- `parse_error`

Rules:
- Similar-looking runtime payloads are not deduplicated solely because they
  share scenario or step structure.
- Per-worker order is preserved across channel batches.
- Cross-worker merge order is deterministic for identical inputs.

## Identity and Reference Rules

- Structural payload identities MUST be stable across controller and worker
  participants.
- Worker-local structural IDs MUST NOT leak into the final stream if a
  canonical structural ID exists.
- Execution payloads MUST remain traceable to:
  - canonical run identity,
  - canonical structural scenario/test-case identity,
  - worker identity,
  - gateway mode,
  - attempt identity.
- Runtime payloads MUST NOT reference structural records discarded during deduplication.

## Ordering Rules

- The same set of transferred worker batches MUST produce the same final NDJSON order.
- Per-worker transfer order is preserved.
- Cross-worker merge order is determined by stable merge rules, not by
  wall-clock timing alone.
- Final output keeps lifecycle ordering valid for existing message validation.

## Failure Handling

- Missing or incomplete worker manifests MUST NOT silently drop known
  diagnostics.
- If a final stream can still be emitted, it MUST carry diagnostics that the
  run is partial.
- If canonical reference rewriting would leave orphaned runtime payloads with
  no deterministic recovery, consolidation MUST fail fast with explicit
  diagnostics instead of emitting an invalid stream.
- If a worker transfer stops after some batches were received, the received
  execution evidence remains eligible for consolidation and the interruption is
  recorded explicitly.
- If xdist/channel compatibility is unsupported before transfer starts, the
  reporter MUST fail fast before producing a misleading distributed stream.

## Compatibility Requirements

- The final consolidated stream MUST be accepted by current stream validation.
- The final consolidated stream MUST remain consumable by current governance and
  report-derivation tooling.
- Single-process runs MUST continue to produce equivalent output shape without
  entering the xdist-specific transport path.

## Validation Requirements

- Contract tests verify that duplicate structural payloads are suppressed while
  runtime payload counts remain complete.
- Transport tests verify that the controller finalizes from transferred worker
  channel events rather than worker-local filesystem reads.
- Docker acceptance tests verify that mixed worker outcomes survive consolidation across isolated containers.
- Acceptance coverage includes socket, proxy `via`, and SSH gateway topologies.
- GitHub CI must expose at least one Linux execution path that runs the new
  distributed-reporting validation coverage through repository-supported
  entrypoints.
- Governance and validation tests verify that the consolidated stream does not
  introduce duplicate lifecycle IDs or orphan references.
