# Contract Fixture: Xdist Worker and Controller Reporting Boundary

## Scope

Defines how pytest-bdd reporting data crosses the xdist worker/controller
boundary when execution runs through local or remote execnet gateways.

## Integration Point Contract

- The reporter integrates through `pytest_xdist_getremotemodule`.
- The returned project-local remote module must remain compatible with xdist's
  expected remote worker bootstrap contract:
  - receive `(workerinput, args, option_dict, change_sys_path)` from the
    controller channel;
  - run a `WorkerInteractor`-compatible event loop;
  - continue sending standard xdist events and `workerfinished`;
  - add reporter-specific namespaced events without colliding with built-in
    xdist event names.
- If this integration point is not available for the active xdist version or
  gateway topology, distributed reporting must fail fast with an explicit
  compatibility diagnostic.

## Worker Responsibilities

Workers MUST:
- emit reporting payloads into execnet-serializable chunk batches sent as
  namespaced xdist events on the existing `execnet.Channel`;
- preserve local runtime event order within each worker;
- include stable worker identity and gateway-mode context in reporter transport
  payloads;
- emit full execution evidence for each executed scenario attempt until
  completion or interruption;
- publish a final completion manifest through `config.workeroutput` before
  `workerfinished`;
- continue honoring standard xdist worker protocol behavior outside the
  reporter-specific event additions.

Workers MUST NOT:
- open or require a reporter-managed TCP listener;
- write directly to the final canonical `--messages-ndjson` artifact in xdist mode;
- require the controller to open worker-local-only files;
- depend on `rsync` for reporter transport;
- assume worker-local structural IDs are globally unique across the run;
- discard runtime events because a similar scenario or step was seen on another
  participant.

## Controller Responsibilities

The controller MUST:
- install the project-local remote module through the xdist hook layer;
- receive reporter chunk events through the same xdist/execnet channel callback
  path used for built-in worker events;
- collect completion manifests from `workeroutput` when `workerfinished`
  arrives;
- own the canonical structural identity table and structural ID remap table;
- deduplicate structural payloads before final emission;
- preserve all valid execution payloads received from workers;
- emit exactly one canonical final stream for the logical run;
- record explicit diagnostics when one or more workers are missing,
  interrupted, incompatible, or incomplete.

The controller MUST NOT:
- fabricate execution events that were never observed;
- rely on worker-local filesystem paths as the authoritative worker/controller
  handoff;
- rely on nondeterministic arrival timing as the sole merge-order rule;
- leave runtime payloads pointing to discarded structural IDs;
- fall back to a side-channel transport when the xdist-native path is
  unavailable.

## Boundary Data Contract

The worker-to-controller boundary must carry:
- logical run identity;
- worker identity;
- gateway mode;
- reporter event name in a dedicated namespace;
- per-worker batch sequence order;
- transferred envelope payloads in execnet-serializable builtin containers;
- completion state and interruption reason when known;
- enough structural data to derive semantic identities;
- enough runtime reference data to rewrite structural links to canonical IDs.

## Transport Rules

- Transport payloads must be serializable through execnet without custom object
  pickling.
- Worker-local disk may be used for transient buffering, but the controller
  cannot depend on direct access to that disk.
- Reporter traffic must stay on the xdist/execnet-managed communication path.
- `rsync` is not part of the reporter transport contract.
- A received completion manifest is authoritative for successful worker
  completion.
- An interrupted or missing manifest after partial chunk receipt results in a
  partial-stream diagnostic, not silent data loss.

## Gateway Compatibility Rules

- The boundary contract must work for xdist-supported `popen`, `ssh`, `socket`,
  and proxy `via` gateway topologies.
- Reporter transport must not assume direct worker reachability from the
  controller outside the existing xdist gateway route.
- Any unsupported xdist version or gateway/channel behavior must trigger
  fail-fast diagnostics before invalid reporting output is emitted.

## Structural Deduplication Rules

- Structural deduplication is controller-owned.
- Duplicate suppression decisions are based on semantic identity, not on
  worker, gateway, chunk, or arrival origin.
- The controller is responsible for producing canonical IDs for retained
  structural payloads.

## Runtime Preservation Rules

- Runtime envelopes are controller-merged, not controller-reconstructed.
- Execution attempts remain distinct across workers, retries, and repeated
  runs.
- Attachments and other runtime payloads stay attached to the canonicalized
  lifecycle chain after remapping.

## Partial-Run Rules

- If a worker transfer is interrupted after some batches were received, the
  controller may emit a partial final stream only when it also emits explicit
  diagnostics.
- Partial-stream diagnostics must identify the missing or incomplete participant when known.
- If no execution data from a worker was ever transferred, the controller still
  records the worker as missing, incompatible, or incomplete in diagnostics.

## Non-Xdist Compatibility

- When xdist is not active, the reporter continues in single-process mode
  without worker/controller split.
- Xdist-only hook registration remains conditional so non-xdist execution does
  not require optional hook contracts.

## Validation Requirements

- Unit tests verify chunk classification, completion manifest handling,
  canonical remap behavior, fail-fast compatibility checks, and duplicate
  suppression decisions.
- Integration tests verify controller-only final output ownership under local
  `-n` execution.
- Docker end-to-end tests verify remote worker aggregation across isolated
  socket, proxy `via`, and SSH gateway scenarios without shared filesystem
  assumptions.
- At least one Linux GitHub CI job must execute the new distributed-reporting
  coverage through repository-supported `tox` or equivalent repository-owned
  entrypoints rather than workflow-only ad hoc commands.
- Acceptance orchestration and verification helpers should be Python-based
  where practical; shell wrappers are reserved for thin container-entrypoint
  concerns such as starting `sshd` or `execnet.script.socketserver`.
- Regression tests verify non-xdist behavior remains unchanged.
