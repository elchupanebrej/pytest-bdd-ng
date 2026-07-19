# Phase 28: Extract pytest_bdd_toolchain - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-25
**Phase:** 28-Extract pytest_bdd_toolchain
**Areas discussed:** Phase identity and roadmap alignment, Migration granularity, Validation target correction, Tool package and lint policy

---

## Phase Identity And Roadmap Alignment

| Option | Description | Selected |
|--------|-------------|----------|
| 28-SPEC.md overrides ROADMAP for this phase | Treat SPEC as newer authoritative scope while leaving ROADMAP stale | |
| ROADMAP remains authoritative | Keep old 24-spec Phase 28 scope | |
| Split the rename into a new phase | Preserve old Phase 28 and move rename elsewhere | |
| Other | Update ROADMAP so Phase 28 is the rename/extraction phase | ✓ |

**User's choice:** ROADMAP must be updated. Phase 28 is the `pytest_bdd_toolchain` rename/extraction phase.
**Notes:** User chose to delete the obsolete 24-spec scope, match the Phase 28 ROADMAP entry to `28-SPEC.md`, and update ROADMAP immediately.

---

## Migration Granularity

| Option | Description | Selected |
|--------|-------------|----------|
| One plan with staged tasks and checkpoints | One GSD plan with internal checkpoints | |
| Multiple separate plans | More review control, more GSD bookkeeping | |
| One atomic change | Broad rename lands as a single implementation change | ✓ |
| Other | Freeform | |

**User's choice:** One atomic change.
**Notes:** Full `28-SPEC.md` validation is still required before done. Commit shape is planner discretion. If validation exposes blockers, fix forward within the same plan.

---

## Validation Target Correction

| Option | Description | Selected |
|--------|-------------|----------|
| Active code/config/docs only | Remove old-name refs from active surfaces; historical phase records may remain | ✓ |
| Entire repository | Rewrite all history and planning audit records too | |
| Source tree only | Clean source but leave docs/config/planning inconsistent | |
| Other | Freeform | |

**User's choice:** Active code/config/docs and current planning surfaces only.
**Notes:** Replace invalid `pytest src/pytest_bdd_testing/` acceptance target with `uv run python -m pytest src/pytest_bdd_toolchain/case -q --tb=short --no-header`. Use scoped `rg` checks rather than broad repository grep. Rename the phase directory now to match the new scope.

---

## Tool Package And Lint Policy

| Option | Description | Selected |
|--------|-------------|----------|
| Keep focused tool-specific ignores only | Preserve practical CLI ignores only | |
| Keep current broad scripts/* ignores | Fast migration, weak quality bar for package modules | |
| Remove all ignores and fix everything | Strongest quality target, may expand scope | ✓ |
| Other | Freeform | |

**User's choice:** Remove ignores and fix lint issues as best effort.
**Notes:** This is not a hard blocker if cleanup grows too large. Directory-level ignore fallback is not approved; use narrow local `# noqa` comments with reasons if needed. Each `pbt-* --help` command must expose a real help path and exit 0 without main side effects.

---

## the agent's Discretion

- Planner may choose exact mechanical rename approach.
- Planner may choose final commit shape as long as the final delivered state is coherent.

## Deferred Ideas

None.
