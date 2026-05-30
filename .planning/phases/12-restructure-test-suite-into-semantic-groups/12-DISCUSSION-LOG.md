# Phase 12: restructure-test-suite-into-semantic-groups - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-18
**Phase:** 12-restructure-test-suite-into-semantic-groups
**Areas discussed:** Migration slicing, Classification edge cases, Environment target policy, Helper-code extraction, E2E split rule, Makefile contract

---

## Migration Slicing

| Option | Description | Selected |
|--------|-------------|----------|
| Staged | Move one semantic group at time; easier review and rollback. | |
| Big-bang | Move all tests once; faster but high diff/noise risk. | yes |
| Hybrid | First create config/targets, then one large mechanical move. | |

**User's choice:** `big-bang`
**Notes:** User corrected typo `big0bang` as big-bang. Follow-up: do not require one mechanical move commit before behavior/config edits.

---

## Classification Edge Cases

| Option | Description | Selected |
|--------|-------------|----------|
| Strict | Classify by purpose from design doc, no mixed dirs. | yes |
| Legacy-compatible | Keep aliases/bridges for confusing old paths during transition. | |
| Agent decide | Planner classifies case-by-case. | |

**User's choice:** `strict`
**Notes:** Follow-up: agent may decide ambiguous test placement case-by-case; no forced default to `integration`.

---

## Environment Target Policy

| Option | Description | Selected |
|--------|-------------|----------|
| Fail explicit | Explicit env targets fail early if prereqs missing; default skips unavailable. | yes |
| Skip more | Skip missing envs even for explicit targets. | |
| Fail more | Fail any unavailable env in broad/full targets. | |

**User's choice:** `fail-explicit`
**Notes:** Follow-up: `make test-all` should include feasible env targets after checks, not fail solely because an unsupported/unavailable environment is absent.

---

## Helper-Code Extraction

| Option | Description | Selected |
|--------|-------------|----------|
| Library owned | Shared active helpers move to `src/pytest_bdd/testing/`. | yes |
| Test local | Keep most helper code in group `conftest.py`. | |
| Minimal | Move only Docker/formatter helpers first. | |

**User's choice:** `library-owned`
**Notes:** Follow-up: `src/pytest_bdd/testing/` is internal support only, not public-ish documented test API.

---

## E2E Split Rule

| Option | Description | Selected |
|--------|-------------|----------|
| Per feature file | One module binds one feature file where practical. | yes |
| Per topic | One module per feature topic directory. | |
| Agent decide | Split based on file count/step sharing. | |

**User's choice:** `per-feature-file`
**Notes:** Follow-up: forbid existing whole-directory collectors after phase.

---

## Makefile Contract

| Option | Description | Selected |
|--------|-------------|----------|
| New API only | Document new targets only. | yes |
| Aliases | Keep old/common commands as documented aliases. | |
| Transition | Temporary aliases with deprecation notes. | |

**User's choice:** `new-api-only`
**Notes:** Follow-up: remove old commands if unusable. Existing commands that naturally still work do not need documentation aliases.

---

## the agent's Discretion

- Exact file-by-file classification for ambiguous tests.
- Exact implementation order inside big-bang migration.
- Exact internal helper module boundaries under `src/pytest_bdd/testing/`.
- Exact validation command sequence.

## Deferred Ideas

None.
