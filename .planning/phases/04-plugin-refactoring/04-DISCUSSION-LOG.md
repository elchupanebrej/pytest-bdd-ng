# Phase 4: Plugin Refactoring - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-05-13T09:02:47Z
**Phase:** 4-Plugin Refactoring
**Areas discussed:** Large-file split boundary, Cross-plugin boundary rule, Verification gate

---

## Large-file split boundary

| Question | Options | Selected |
|----------|---------|----------|
| Split depth? | Minimal under-400; responsibility modules; broader cleanup including `steps.py`; you decide | Responsibility modules |
| `live_formatter_runtime.py` split axis? | Transport/process/session/render; event-type modules; helper extraction | Transport/process/session/render |
| `message_validation.py` split axis? | Schema/load + protobuf mapping + validation API + error formatting; message type family; helper extraction | Schema/load + protobuf mapping + validation API + error formatting |
| Public import compatibility after splits? | No shims; temporary re-export shims; facade under 400 lines | No shims |

**User's choice:** B, A, A, A
**Notes:** User chose a deeper responsibility-based split with no private-path compatibility shims.

---

## Cross-plugin boundary rule

| Question | Options | Selected |
|----------|---------|----------|
| Enforcement strength? | Hard rule; risk-based; inventory only | Hard rule |
| Allowed communication path? | Pytest hooks only; hooks plus neutral utility modules; hooks plus typed service objects in `model/` | Hooks plus typed service objects in `model/` |
| Service object scope? | Stable contracts only; broad service layer; minimal adapters | Stable contracts only |
| External users importing plugin internals? | No guarantee + changelog note; deprecation warnings; aliases where easy | No guarantee + changelog note |

**User's choice:** A, C, A, A
**Notes:** Boundary is strict, but model-level typed contracts are allowed for stable cross-plugin data.

---

## Verification gate

| Question | Options | Selected |
|----------|---------|----------|
| Full-suite blockers from Phase 3? | Fix env blockers first; proceed with focused tests + document blockers; proceed with optional full suite | Fix env blockers first |
| Formatter equivalence check? | Golden before/after output; unit-level equivalence; manual smoke | Golden before/after output |
| Plugin structure verification? | Source contract test; static grep/check script; review | Source contract test |
| Boundary verification? | Test/script blocking plugin-internal imports; linter note; manual audit | Test/script blocking plugin-internal imports |

**User's choice:** A, A, A, A
**Notes:** Phase 4 must establish a real full-suite gate before refactor completion.

---

## the agent's Discretion

None.

## Deferred Ideas

None.
