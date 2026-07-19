---
title: Unbound Feature Detection in E2E Runs
date: 2026-06-17
context: pytest-bdd-ng e2e hygiene
---

# Unbound Feature Detection

## Problem

`.feature.md` files in `features_base_dir` can exist on disk without being linked
into the pytest collection (no conftest.py or test module calls `scenarios(...)`).
These orphaned features silently disappear from test runs, confusing contributors.

## Design Decisions

- **Detection timing:** Post-collection scan, after pytest collection completes
- **Scope:** Recursive scan of `features_base_dir` (already configurable)
- **Reporting:** Individual `pytest.skipped` items in normal pytest output
- **Reason text:** `"Feature not bound to any test module"` (or similar)
- **Exclusions:** None — unbound features are always skipped

## Implementation Approach

1. Hook into pytest collection lifecycle (likely `pytest_collection_modifyitems`)
2. Scan `features_base_dir` for all `.feature.md` files
3. Compare against the set of features that pytest actually collected
4. For each unbound feature, inject a synthetic skipped item into the session

## Open Questions

- Which pytest hook is the right integration point?
- How to represent the synthetic skip item (class? function? direct item?)
- Should the feature filename or path appear in the skip reason?
