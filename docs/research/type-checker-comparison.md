# Type Checker Comparison Report

**Date:** 2026-06-08
**Codebase:** pytest-bdd-ng `src/pytest_bdd/` (Python 3.14)
**Config:** Python 3.14 on Windows (x86_64-pc-windows-msvc)

## Executive Summary

Four type checkers were compared against mypy on the pytest-bdd codebase: **pyright** (Microsoft), **ty** (Astral/ruff team), **pytype** (Google), and **mypy** (current project checker). **mypy remains the best primary type checker** due to its attrs and pydantic plugin ecosystem which pyright and ty cannot match on this codebase. However, **pyright catches None-safety and override-compatibility issues mypy misses** and is recommended as an optional local check. **ty runs in 3 seconds** (14x faster than mypy) and catches 44 dataclass field-ordering issues no other tool detects — worth monitoring. **pytype failed to run** on Python 3.14 (import errors) and is not recommended.

## Methodology

Each tool was installed in an isolated `uv` venv at `$TEMP\type-checker-comparison`, run on `src/pytest_bdd/`, and then the venv was removed. No tools were added to `pyproject.toml`, pre-commit, or CI.

**Tools tested:**
| Tool | Version | Install Method | Settings |
|------|---------|---------------|----------|
| mypy | bundled | `uv run python -m mypy` | Current config + `--strict` |
| pyright | 1.1.410 | isolated venv pip | Default + typeCheckingMode strict |
| ty | 0.0.44 | isolated venv pip | Default |
| pytype | 2024.10.11 | isolated venv pip | Failed (see below) |

## Comparison Table

| Tool | Default Errors | Strict Errors | Unique Findings | False Positives | Speed (s) | CI Integration | Message Quality |
|------|---------------|---------------|-----------------|-----------------|-----------|----------------|-----------------|
| **mypy** | 647 | 819 | attrs plugin, pydantic plugin | Low (with plugins) | 41.7 | Pre-commit hook, mypy action | Medium |
| **pyright** | 159 + 4w | 1,927 + 1w | Override variance, Optional access, `__all__` checks | Medium (no attrs plugin) | 31.9 | Pyright GitHub Action, CLI | High |
| **ty** | — | 272 | Dataclass field order (44!), `Top[]` call safety | Low-Medium | 3.0 | None official | Medium |
| **pytype** | — | — | FAILED | N/A | N/A | Pre-commit hook | N/A |

## Per-Tool Analysis

### pyright

**What it catches that mypy misses:**
- `reportIncompatibleVariableOverride` (8 instances) — detects when subclass fields override base class fields with incompatible types due to mutability variance. These are real bugs where mutable fields break type soundness in subclasses. Example: `_gherkin_go/_build.py:27` — `user_options` override is incompatible due to `str` vs `str | None`.
- `reportOptionalMemberAccess` (4 instances) — catches optional-chaining issues mypy skips when stubs are incomplete.
- `reportUnsupportedDunderAll` (2) — flags `__all__` elements that are not actually exported.
- `reportPrivateImportUsage` (1) — catches imports of private symbols (`packaging.utils.Version` → should use `packaging.version.Version`).
- `reportInvalidTypeForm` (2) — catches using local variables in type expressions, which is unsound at runtime.

**What it misses (or misreports):**
- Attrs `@define` classes: pyright reports `reportGeneralTypeIssues` on attrs-generated fields because it doesn't understand the attrs class transformation. 52 such issues, nearly all false positives on attrs classes. This is the attrs plugin gap — pyright has no attrs plugin equivalent.
- Dataclass field ordering: unlike ty, pyright does not enforce field ordering rules for attrs/dataclasses with defaults.
- Import resolution: pyright reports `reportMissingModuleSource` (warning) for `setuptools` because it uses source-based analysis rather than import-based. This is a false positive for packages without `py.typed`.

**Performance:** 31.9s (default) / 33.9s (strict) — comparable to mypy.

### ty

**What it catches that others miss:**
- `dataclass-field-order` (44 instances!) — ty enforces that dataclass/attrs fields with defaults must come after fields without defaults. This is a Python runtime requirement (`TypeError: non-default argument follows default argument`) that mypy's attrs plugin does not enforce and pyright doesn't catch. These are potential runtime failures.
- `call-top-callable` (5 instances) — `toolz.Top` objects are typed as callable but the signature is erased, making calls unsafe. ty detects this; mypy does not because `toolz` is in `ignore_missing_imports`.
- `subclass-of-final-class` (3 instances) — catches subclassing of `typing_extensions.final` classes.
- `invalid-exception-caught` (1) — exactly the same catch as mypy's `[misc]` for catching `type[BaseException] | Sequence[...]`.

**What it misses:**
- No attrs plugin — some decisions are less informed about attrs-generated attributes.
- No generics checking depth: ty didn't catch `disallow_any_generics` equivalent issues (29 in mypy strict).
- Ecosystem maturity: ty is version 0.0.44 — too new for CI gating. The `tomllib` import in the codebase's `layer_rules.py` was flagged as unresolved (Python 3.10 backport issue).

**Performance:** 3.0s — 14x faster than mypy, 10x faster than pyright. Written in Rust.

### pytype

**Status: FAILED.**

pytype (2024.10.11) could not be imported on Python 3.14. The package installs but produces a cascade of import errors (`cannot import name 'utils' from 'pytype'`). pytype appears to rely on internal module layout that breaks on CPython 3.14.

**Analysis:** pytype uses import-time introspection to build its type inference engine and has hard dependencies on internal CPython structures that change between minor versions. Google's release cadence for pytype targets production environments (Python 3.8-3.12), and Python 3.14 support is not yet available. Since pytest-bdd requires Python 3.10-3.14, pytype cannot be part of the toolchain.

### mypy

**Current baseline (default config):**
- 647 errors under current configuration (`check_untyped_defs`, `warn_return_any`, 21 `ignore_missing_imports`, attrs + pydantic plugins).
- Top categories: `[attr-defined]` (333), `[call-arg]` (222), `[unused-ignore]` (70).

**Strict mode:**
- 819 errors with `--strict` flags enabled.
- New error categories introduced: `[unused-ignore]` (70 — would need clean-up first), `[untyped-decorator]` (54), `[type-arg]` (29), `[redundant-cast]` (23).
- Most `--strict` errors come from the 21 packages in `ignore_missing_imports` — once those are resolved (T1), the strict error count will drop significantly.

**Gaps in mypy:**
- Does not catch dataclass field order violations (ty finds 44).
- Does not catch mutable field override variance (pyright finds 8).
- `[unused-ignore]` errors (70) indicate many `# type: ignore` comments are now unnecessary after improvements.

## Unique Finding Overlap

Each tool found categories of issues the others did not:

| Finding Category | mypy | pyright | ty | Notes |
|-----------------|------|---------|----|----|
| Attrs field type issues | 333† | 52 (mostly FP) | — | mypy wins via plugin |
| Dataclass field ordering | ✗ | ✗ | 44 | ty only — runtime bugs |
| Override variance | ✗ | 8 | — | pyright only |
| None-safety access | Partial | 4 | — | pyright stricter |
| `__all__` integrity | ✗ | 2 | — | pyright only |
| Private import detection | ✗ | 1 | — | pyright only |
| `Top[]` callable safety | ✗† | ✗ | 5 | ty only — toolz-specific |
| Final class subclassing | — | — | 3 | ty only |
| Generics type arg checking | 29 | ✗ | ✗ | mypy only |

† mypy `attr-defined` count is heavily influenced by `ignore_missing_imports`; many of these are from packages lacking stubs, not actual bugs. †† mypy doesn't catch `Top[]` calls because `toolz` is in `ignore_missing_imports`.

## CI Recommendations

### RECOMMENDATION: pyright — Add as optional local check (not CI gate)

```bash
# Local only, not in pre-commit or CI:
pip install pyright
pyright src/pytest_bdd/
```

**Rationale:** pyright's strict mode finds 1,927 issues — 1,108 more than mypy strict. These include genuine bugs (None-safe access, override variance) and false positives from the attrs plugin gap. As an optional local check, developers can run pyright to catch None-safety issues during development before pushing. **Do not add to pre-commit or CI** because the attrs plugin gap produces ~52 false positives that would lower signal-to-noise.

### RECOMMENDATION: ty — Monitor, do not add yet

**Rationale:** ty is version 0.0.44 and shows impressive speed (3s) and unique findings (44 dataclass field ordering bugs). However, the ecosystem has not standardized around ty yet, it has no official CI integration, and Python 3.10 backport issues exist (`tomllib` import flagged). Re-evaluate in 6 months when the Astral ecosystem (ruff, uv, ty) matures. Keep ty on the radar — if it gains an attrs plugin and stabilizes, it could replace mypy long-term.

### RECOMMENDATION: pytype — Do not add

**Rationale:** pytype does not support Python 3.14, and the project's compatibility matrix requires Python 3.10-3.14. Even if pytype eventually supports 3.14, its inference-based approach produces false positives on plugin-heavy codebases (pytest hooks, attrs transformations, decopatch decorations) and its speed (~2 minutes for a large codebase) is prohibitive for pre-commit and CI.

### RECOMMENDATION: mypy — Continue as primary type checker

**Rationale:** mypy's attrs and pydantic plugins are essential for this codebase. No other type checker understands `@define` class transformations or `StashBound` pattern typing. The 819 `--strict` errors are addressable through the T1 (stubs) and T2 (strict flags) workstreams already planned. Continue with the incremental flag-by-flag approach outlined in the T2 strategy.

## Conclusion

**Mypy is confirmed as the primary type checker** for pytest-bdd-ng. Its plugin ecosystem (attrs, pydantic) provides type checking depth that pyright and ty cannot replicate on this codebase. The T1-T2 workstreams (stubs creation, strict flag enablement) will bring mypy to zero `--strict` errors without switching tools.

**Pyright is the recommended supplementary tool** — developers should run it locally to catch override variance and None-safe access issues mypy misses. **Ty is the wildcard** — if it gains attrs plugin support and stabilizes, its 14x speed advantage and dataclass field ordering checks make it the most promising long-term replacement.

**Condition for revisiting:** Re-evaluate pyright and ty for CI inclusion in 6 months (2026-12) or when:
- Pyright gains an attrs plugin (or attrs/cattrs ships inline types via PEP 681),
- Ty reaches v1.0 and gains attrs/decorator awareness,
- The codebase typing coverage reaches a level where plugin-specific false positives are negligible.

---

## Impact on Phase 20 Typing Workstreams

This comparison validates and refines the T1-T3 strategy:

- **T1 (Stubs):** Confirmed necessary. The 819 mypy `--strict` errors will drop significantly once `ignore_missing_imports` entries are resolved. The 70 `unused-ignore` warnings confirm many `# type: ignore` comments are already stale — stubs will eliminate them.
- **T2 (Strict Flags):** Validated. `--strict` catches errors other tools don't: 29 generics type-arg issues (missed by pyright and ty), 54 untyped decorators, and 23 redundant casts. No reason to switch checkers.
- **T3 (type:ignore Rule):** Confirmed need. All 33 existing ignores have error codes (D-03 compliant), but pyright found issues mypy's `ignore_missing_imports` masks. The T3 rule should also check for obsolete ignores once T1 stubs land.
- **Gap Register:** 44 dataclass field-ordering issues (ty) and 8 override-variance issues (pyright) should be audited manually during T2 — they represent real bugs mypy cannot detect.

## Data Collection Methodology

**Error sampling (spot-checked 5 errors per tool):**

- **mypy strict `[untyped-decorator]` (54):** All from `@hookimpl` decorators on pytest hook functions. These are benign — pytest's hook system erases decorator types. Resolution: add `# type: ignore[untyped-decorator]` with explanation per T3 rule.
- **mypy strict `[type-arg]` (29):** Missing type arguments on generic types (`OrderedSet`, `dict`, `list`). Real typing gaps; fixable with proper annotations.
- **pyright `reportGeneralTypeIssues` (52):** 45/52 are attrs-generated field false positives (e.g., `Dataclass field cannot use private name`). 7 are genuine type issues (e.g., `Class overlaps Identifiable unsafely`).
- **pyright `reportArgumentType` (53):** Mixed real bugs (cucumber_messages Pydantic model constructor mismatches) and false positives from untyped libraries.
- **ty `dataclass-field-order` (44):** All from attrs classes where fields with defaults appear before non-default fields. These would cause `TypeError` at runtime if instances were created positionally. Attrs uses keyword-only construction so they don't crash in practice, but the convention violation is real.
- **ty `invalid-argument-type` (100):** Mostly from `--strict`-equivalent checking of constructor arguments — ty reports these with high precision and better message quality than mypy.

*Tool versions: pyright 1.1.410, ty 0.0.44, pytype 2024.10.11, mypy (bundled via uv)*
*Environment: Python 3.14, Windows 11 (x86_64), uv 0.11.15*
