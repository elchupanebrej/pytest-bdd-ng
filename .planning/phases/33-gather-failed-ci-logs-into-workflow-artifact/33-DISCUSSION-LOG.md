# Phase 33: Gather Failed CI Logs into Workflow Artifact - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-10
**Phase:** 33-gather-failed-ci-logs-into-workflow-artifact
**Areas discussed:** Collector job scope, Log metadata

---

## Collector Job Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Both test and xdist-remote | `needs: [test, test-xdist-remote]` — one artifact captures all matrix failures | ✓ |
| Test matrix only | Stick to the spec. xdist-remote might need different handling and can be added later | |

**User's choice:** Both test and xdist-remote (Recommended)
**Notes:** The approved design spec originally scoped to `needs: test` only. User decided to broaden to both matrix jobs since xdist-remote (socket/via/ssh) failures are equally opaque and the collector cost is trivial. D-01 captures this override.

---

## Log Metadata

| Option | Description | Selected |
|--------|-------------|----------|
| Prepend metadata header | 3-line header (job name, run URL, timestamp) before raw log body — easier offline forensics | ✓ |
| Raw output only | Identical to what the Actions UI shows — cleanest for piping into grep/jq | |

**User's choice:** Prepend metadata header (Recommended)
**Notes:** Header includes human-readable job name, run URL, and ISO 8601 timestamp. The raw step output follows after a blank line. This makes offline investigation self-contained — no need to cross-reference artifact names to remember which run produced the logs. D-02 captures this override.

---

## the agent's Discretion

- Exact implementation of the metadata header formatting within the github-script body
- Whether the header uses `core.info` or is written directly into the log file content
- Any helper function extraction within the script for DRY log collection

## Deferred Ideas

None.

---

## Context Carried Forward

The approved design spec at `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md` was treated as the baseline — all spec-defined decisions (permissions, error handling, artifact naming, verification plan) carry forward unchanged. Only the two areas discussed above override the spec.
