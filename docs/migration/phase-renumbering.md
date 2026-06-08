# Phase Renumbering Map

## Summary

During development of the pytest-bdd-ng stabilization milestone, the phase numbering
shifted when **Phase 20 (multiple-refactorings)** was inserted at position 20. Three
pre-planned future phases (originally numbered 20–22) were renumbered to 21–23.

This document maps old→new phase numbers so that file names and any future commit
messages referencing the old numbering can be interpreted against the current ROADMAP.

**Important:** This mapping documents the numbering shift. Git history has NOT been
rewritten — phase-directory files in 21–23 still carry their original 20-\*, 21-\*,
22-\* prefixes. Use the table below to resolve references.

## Why Renumbering Happened

1. Phases 1–19 were planned and executed under their original numbers (no renumbering).
2. Phase 20 (multiple-refactorings) was added as a large refactoring phase, taking
   position 20 in the ROADMAP — a number already reserved by the pre-planned
   `codegen-step-binding-and-tolerant-steps` phase (originally Phase 20).
3. To accommodate the insertion, the three pre-planned phases shifted +1:
   - Old Phase 20 → New Phase 21
   - Old Phase 21 → New Phase 22
   - Old Phase 22 → New Phase 23
4. The `.planning/` files inside the shifted phase directories were NOT renamed
   (they retain their original `NN-*` prefixes) to avoid confusing git history
   for phases that have not yet been executed.

## Mapping Table

| Old Phase Number | New Phase Number | Phase Name |
|-----------------|-----------------|------------|
| 20              | 21              | codegen-step-binding-and-tolerant-steps |
| 21              | 22              | pdb-mcp-integration-for-agentic-debugging-and-producing-expl |
| 22              | 23              | test-step-binding-api |

**Phases 1–19:** No renumbering occurred. Phase numbers are identical old and new.

**Phase 20 (multiple-refactorings):** Inserted at position 20; did not exist in the
old numbering scheme.

## Interpreting Git History

### Commit Messages

Git commit messages rarely reference phase numbers explicitly. When they do:

- `(phase-20)` and `(20-NN)` refer to the CURRENT Phase 20 (multiple-refactorings).
  These are correct and require no mapping.
- `(phase-11)` refers to Phase 11 (audit-prune). Correct — no renumbering.
- No commits exist yet for phases 21–23 (they are future phases).

### Planning Directory Files

Files inside `.planning/phases/21-codegen-step-binding-and-tolerant-steps/` use
`20-*` naming (e.g., `20-01-PLAN.md`). These correspond to **Phase 21** in the
current ROADMAP.

Files inside `.planning/phases/22-pdb-mcp-integration-*/` use `21-*` naming.
These correspond to **Phase 22** in the current ROADMAP.

Files inside `.planning/phases/23-test-step-binding-api/` use `22-*` naming.
These correspond to **Phase 23** in the current ROADMAP.

### ROADMAP Status

As of 2026-06-09, the ROADMAP.md lists phases 1–20. Phases 21–23 exist as
pre-planned directories but are not yet in the active ROADMAP.

## Resolution Strategy

1. **Do NOT rewrite git history.** Rewriting history for unexecuted phases would
   create unnecessary churn and risk.
2. **When phases 21–23 are executed,** the planner/executor should use the NEW
   phase numbers (21, 22, 23) in commit messages, even if the planning files
   still carry their original prefixes.
3. **If file renaming is desired,** rename the `NN-*` files inside the shifted
   directories to match their current phase number. This is optional — the
   directory name already communicates the correct phase.

---

*Created: 2026-06-09*
*Phase: 20, Plan: 25*
