# Phase 11: Audit & Prune - Discussion Log

**Date:** 2026-05-16
**Mode:** Default (interactive)

## Discussion Summary

### Decopatch fate
**Options presented:**
- Replace with makefun-only (Recommended)
- Keep as-is
- Replace with stdlib functools.wraps
- You decide

**User selected:** Keep as-is

**Notes:** decopatch 1.4.10 (last release 2022-03-01) is functional and stable. Not worth rewrite effort during stabilization phase. Document health status in audit report.

### Large file evaluation
**Options presented:**
- Split the big 3 (Recommended) — steps.py, message_capability_governance.py, run.py
- Split only if clearly separable
- Leave as-is, justify in report

**User selected:** Split the big 3 (Recommended)

**Notes:** steps.py (803L) → Registry/Matcher/Definition sub-modules. message_capability_governance.py (751L) → capability detection/status governance/checklist generation. run.py (630L) → execution lifecycle stages.

### Underused plugin audit
**Options presented:**
- Keep all, document usage (Recommended)
- Aggressive prune + consolidate
- Deprecate first, remove later

**User selected:** Keep all, document usage (Recommended)

**Notes:** All 17 plugins confirmed active with entry points. Audit each, document why kept. Remove only truly dead/zero-consumer plugins.

### CI matrix validation scope
**Options presented:**
- Full matrix (all combos)
- Representative subset (Recommended)
- Current tox config only

**User selected:** Full matrix (all combos)

**Notes:** All Python 3.10-3.14 × pytest 7.x-latest combinations (~20+ tox environments). CI matrix validation is a gate — phase fails if any combination fails.

## Deferred Ideas

- decopatch replacement → future phase
- parsers.py refactoring → FROZEN

## the agent's Discretion Items

- Exact sub-module naming and boundaries for large file splits
- Which specific plugins need usage documentation depth
- Specific tox environment configuration for full matrix run

---

*Phase: 11-Audit & Prune*
*Discussion completed: 2026-05-16*
