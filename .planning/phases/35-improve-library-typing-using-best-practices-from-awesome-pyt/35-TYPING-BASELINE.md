# Phase 35 Strict Mypy Expanded Baseline

**Recorded:** 2026-07-12
**Purpose:** Preserve the no-bypass starting point before the source-remediation
batches. This is evidence, not an allowance for future errors.

## Command

```console
.venv/bin/mypy --config-file pyproject.toml
```

The command uses the repository's strict `[tool.mypy]` configuration after
removing the source-directory exclusion and all module-wide `ignore_errors`
overrides. It therefore discovers both `pytest_bdd` and
`pytest_bdd_toolchain`, including the toolchain paths that had been excluded.

## Result

**Exit status:** `1` (intentionally nonzero baseline)

```text
Found 2709 errors in 306 files (checked 738 source files)
```

The complete command output was 3,076 lines. Its error-code totals were:

| Errors | Code |
| ---: | --- |
| 1,075 | `no-untyped-def` |
| 573 | `attr-defined` |
| 347 | `arg-type` |
| 165 | `no-untyped-call` |
| 86 | `union-attr` |
| 76 | `syntax` |
| 61 | `type-arg` |
| 47 | `index` |
| 41 | `name-defined` |
| 40 | `untyped-decorator` |
| 36 | `var-annotated` |
| 30 | `misc` |
| 27 | `list-item` |
| 24 | `no-any-return` |
| 15 | `call-overload` |
| 14 | `operator` |
| 10 | `unused-ignore` |
| 10 | `dict-item` |
| 8 | `call-arg` |
| 7 | `import-not-found` |
| 7 | `assignment` |
| 3 | `comparison-overlap` |
| 2 | `return-value` |
| 1 each | `valid-type`, `type-var` |

## Dated Finding Summary

On 2026-07-12, the expanded strict configuration revealed 2,709 errors across
306 files. The largest work item is adding concrete annotations to the formerly
excluded toolchain code (`no-untyped-def`); dependency and framework boundary
typing accounts for a substantial second group (`attr-defined`, `arg-type`, and
`no-untyped-call`). The subsequent isolated remediation plans own their
individual evidence records. Plan 140 alone reconciles them into the canonical
inventory and runs the final clean full-source gate.

This baseline does not claim full-source cleanliness and does not modify the
canonical typing inventory.
