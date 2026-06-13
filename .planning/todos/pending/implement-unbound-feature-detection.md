---
title: Implement Unbound Feature Detection
date: 2026-06-17
priority: medium
status: pending
---

# Implement Unbound Feature Detection

Add post-collection detection of `.feature.md` files in `features_base_dir` that
are not bound to any pytest collection. Report them as `pytest.skipped` items.

## Acceptance Criteria

- [ ] Recursive scan of `features_base_dir` for `.feature.md` files
- [ ] Compare against collected features after pytest collection
- [ ] Unbound features appear as `SKIPPED` in pytest output
- [ ] Skip reason clearly states the feature is not bound
- [ ] No regressions in existing e2e test behavior
