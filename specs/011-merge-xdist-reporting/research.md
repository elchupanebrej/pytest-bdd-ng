# Phase 0 Research: Distributed Reporting Stream

## Decision 1: Use `pytest_xdist_getremotemodule` to install a project-local xdist remote-module adapter

- Decision: Integrate distributed reporting by returning a project-local remote module from `pytest_xdist_getremotemodule`, instead of creating a separate reporter-managed TCP transport.
- Rationale: `pytest-xdist` already creates each worker by calling `gateway.remote_exec(remote_module)` and exposes `pytest_xdist_getremotemodule()` as the intended extension point. That lets the feature ride on the same worker/controller channel for local and remote gateways without forking xdist permanently.
- Alternatives considered:
  - Keep the current TCP listener plus `workerinput` host/port metadata: rejected because it bypasses xdist network modes and breaks proxy and isolated-topology support.
  - Patch a vendored xdist fork: rejected because the clarified spec allows only a project-local compatibility adapter, not a permanent fork.

## Decision 2: Send reporting payloads as namespaced xdist events over the existing `execnet.Channel`

- Decision: Worker-side reporting batches will be emitted as namespaced xdist events on the existing `execnet.Channel`, using only execnet-serializable builtin payloads.
- Rationale: In xdist's remote module, `WorkerInteractor.sendevent()` already sends `(event_name, kwargs)` tuples over the channel, and execnet serializes builtin containers deterministically. Reusing that path preserves support for `popen`, `ssh`, `socket`, and proxy `via` gateways because all of them ultimately speak through the same channel abstraction.
- Alternatives considered:
  - Attach binary or custom Python objects directly to the channel: rejected because execnet documents builtin-type serialization only.
  - Delay transfer until `workeroutput` at session finish: rejected because interrupted workers would lose all earlier runtime evidence.

## Decision 3: Keep the controller as the only writer of the final NDJSON artifact

- Decision: The controller remains the sole owner of the final `--messages-ndjson` file, while workers only send runtime chunks and publish a terminal manifest.
- Rationale: One authoritative run-level stream is still required. Controller-only final emission keeps deduplication, canonical ID remapping, and stream validation in a single deterministic place and avoids any shared-filesystem requirement.
- Alternatives considered:
  - Let each worker write a shared final file: rejected because it assumes shared storage and introduces concurrent write ordering hazards.
  - Produce one file per worker and merge manually: rejected because the spec requires a single consolidated stream with no manual merge step.

## Decision 4: Preserve the current final-stream contract while replacing only the worker/controller transport

- Decision: The public `--messages-ndjson` consumer contract, schema validation, and governance tooling remain unchanged; only the internal worker/controller transport changes from path handoff or side-channel sockets to xdist channel events plus `workeroutput` manifest data.
- Rationale: Downstream consumers already depend on the NDJSON stream shape. The feature is transport-architectural, not a public output-format redesign.
- Alternatives considered:
  - Add a second remote-only report format: rejected because it fragments the reporting surface.
  - Make remote-safe behavior opt-in under a new CLI flag: rejected because the clarified feature changes the behavior expected from the existing reporter in xdist mode.

## Decision 5: Structural deduplication stays semantic and controller-owned

- Decision: Scenario, step, and other structural payloads will continue to be deduplicated by semantic identity and rewritten to controller-owned canonical IDs before final emission.
- Rationale: Moving onto the xdist channel changes transport origin, not payload meaning. Structural duplicates still arise across controller and workers, and runtime payloads still need canonical references after deduplication.
- Alternatives considered:
  - Treat all worker-origin payloads as distinct because they came from separate gateways: rejected because it reintroduces duplicate structural data.
  - Deduplicate by worker-local IDs only: rejected because worker-local ID spaces are not globally stable.

## Decision 6: Partial-worker behavior must be expressed as incremental chunks plus a terminal manifest

- Decision: Workers stream chunk events during execution and also publish a small completion manifest in `workeroutput`, allowing the controller to distinguish clean completion from interrupted transfer.
- Rationale: xdist already exposes `workeroutput` as the terminal worker-to-controller summary path. Combining it with incremental channel events keeps partial evidence from interrupted workers while still giving the controller an authoritative completion signal.
- Alternatives considered:
  - Channel events only: rejected because the controller would lack a deterministic success marker for healthy workers.
  - Manifest only: rejected because any worker crash would drop all earlier runtime output.

## Decision 7: Unsupported xdist/channel compatibility fails fast with a clear diagnostic

- Decision: The reporter will explicitly detect missing remote-module integration points or unsupported gateway/channel behavior and abort distributed reporting with a clear compatibility error rather than silently falling back.
- Rationale: The clarified spec forbids fallback to a side-channel transport and requires actionable diagnostics when the xdist version or topology cannot support the feature safely.
- Alternatives considered:
  - Silently disable distributed consolidation for unsupported cases: rejected because it hides missing report data.
  - Fall back to worker-local file reads or reporter-owned sockets: rejected because both violate the clarified transport requirement.

## Decision 8: Acceptance coverage must exercise every supported xdist remote gateway family

- Decision: The validation plan will cover local `popen`, remote `socket`, proxy `via`, and remote `ssh` execution topologies, with Docker-backed acceptance for the remote cases and explicit fail-fast coverage for unsupported combinations.
- Rationale: `pytest-xdist` documents remote socket workers and proxy routing via execnet gateways; the clarified spec extends that requirement to all officially supported remote gateway modes, not just direct local workers.
- Alternatives considered:
  - Keep only local `-n` coverage: rejected because it does not prove remote topology compatibility.
  - Cover only direct socket workers: rejected because it misses proxy-chain and SSH modes called out in the clarifications.

## Decision 9: GitHub CI should execute the new distributed-reporting coverage through repository-supported tox entrypoints

- Decision: The new distributed-reporting validation coverage will remain invocable through repository-supported `tox` environments, and at least one Linux GitHub Actions job will execute the remote gateway acceptance coverage through those same `tox` entrypoints.
- Rationale: `.github/workflows/main.yml` already installs `tox` and runs it in CI, while `tox.ini` already defines Linux-only remote acceptance environments for `socket`, `via`, and `ssh`. Keeping the CI path aligned with `tox` preserves one supported invocation model for local and GitHub runs.
- Alternatives considered:
  - Add workflow-only `pytest` commands that bypass `tox`: rejected because they create a second unsupported execution path.
  - Require every OS job to execute Docker-backed remote acceptance: rejected because the remote acceptance environments are Linux-scoped and do not need to block macOS or Windows matrix jobs.

## Decision 10: Prefer Python helpers for acceptance orchestration and verification, with bash limited to thin entrypoints

- Decision: New acceptance orchestration, verification, and fixture-helper logic will live in Python modules under `tests/` wherever practical, while shell scripts remain only as thin wrappers for container entrypoints that must launch shell-native processes such as `sshd` or `execnet.script.socketserver`.
- Rationale: The feature already benefits from Python-based orchestration and verification in `tests/e2e/test_xdist_remote_message_aggregation.py` and `tests/e2e/fixtures/remote_xdist/verify_report.py`. Python is easier to lint, exercise in CI, and evolve than multi-step bash glue, but shell remains appropriate for minimal container startup behavior.
- Alternatives considered:
  - Keep expanding bash for orchestration and verification: rejected because it duplicates control flow that is easier to test and maintain in Python.
  - Eliminate shell completely: rejected because container entrypoints still need straightforward process `exec` and SSH/socketserver setup behavior.

## References

- `pytest-xdist` hook definitions: https://raw.githubusercontent.com/pytest-dev/pytest-xdist/master/src/xdist/newhooks.py
- `pytest-xdist` worker manager internals: https://raw.githubusercontent.com/pytest-dev/pytest-xdist/master/src/xdist/workermanage.py
- `pytest-xdist` remote worker module: https://raw.githubusercontent.com/pytest-dev/pytest-xdist/master/src/xdist/remote.py
- `pytest-xdist` remote execution docs: https://pytest-xdist.readthedocs.io/en/stable/remote.html
- `pytest-xdist` internals overview: https://pytest-xdist.readthedocs.io/en/stable/how-it-works.html
- `execnet` channel and serialization basics: https://codespeak.net/execnet/basics.html
- Repository CI workflow: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.github/workflows/main.yml`
- Repository tox entrypoints: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tox.ini`
