---
quick_id: 260615-kzf
status: complete
date: 2026-06-15
---

# Summary: Inject architecture score templates into src/pytest_bdd_testing (excluding cases/)

## What was done

1. Added `--exclude` flag to `scripts/inject_responsibility_docstrings.py` to support directory exclusion
2. Ran the architecture injector on 47 Python files in `src/pytest_bdd_testing/` excluding `src/pytest_bdd_testing/cases/`

## Injection results

- **Files scanned:** 47
- **Docstrings added:** 32 (new entities without prior docstrings)
- **Docstrings updated:** 101 (existing docstrings enriched with responsibility contracts)
- **Errors:** 0

## Post-injection verification

- **Pylint score:** 9.66/10 (unchanged)
- **Architecture violations:** 0 (BLQ910-915 all pass)
- Pre-existing violations only: `BLQ1702` (noqa without explanation), `R1710` (inconsistent return)

## Files modified

All `.py` files in `src/pytest_bdd_testing/` (excluding `cases/`) now contain:
- Module-level responsibility docstrings with architecture scores
- Class-level responsibility docstrings with architecture scores
- Function/method-level responsibility docstrings with architecture scores

Each docstring includes the 9 `#arch-eval:` score criteria:
`reason_for_existence`, `owned_responsibility`, `delegation_boundary`, `cohesion`, `separation`, `consumer_clarity`, `state_invariants`, `entity_fullness`, `locational_stability`
