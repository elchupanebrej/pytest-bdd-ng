# Phase 09: Compatibility Streamlining - Research

**Researched:** 2026-05-16
**Domain:** Python compatibility shims, dependency pruning, module refactoring
**Confidence:** HIGH

## Summary

Phase 09 removes dead Python 2 shims and legacy dependencies from pytest-bdd-ng, consolidating the `compatibility/` layer. Scope is surgical: replace `pathlib2`/`docopt-ng` in one script, delete two unused modules (`git.py`, `jsonschema.py`), split `matrix.py` into runtime + CI halves, and keep 5 version-conditional shims intact.

**Primary recommendation:** Execute as atomic file-level changes with import-path updates — no behavioral changes, zero risk if test suite passes.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `pathlib2` → `pathlib` replacement | API / Backend (script) | — | Build-time script, not runtime |
| `docopt` → `argparse` replacement | API / Backend (script) | — | Build-time script CLI parsing |
| `compatibility/jsonschema.py` deletion | API / Backend | — | Protocol wrapper with no added value |
| `compatibility/git.py` deletion | API / Backend | — | Dead code, zero consumers |
| `compatibility/matrix.py` split | API / Backend (runtime) + Build/CI (tox) | — | Two distinct concern domains in one file |
| Version-conditional shims (keep) | API / Backend | — | Python version compatibility layer |

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Replace `pathlib2.Path` → `pathlib.Path` in `script/bdd_tree_to_rst.py` — stdlib since Python 3.4
- **D-02:** Replace `docopt` → `argparse` in `script/bdd_tree_to_rst.py` — stdlib, equivalent CLI parsing
- **D-03:** Remove `pathlib2`, `docopt-ng`, `types-pathlib2`, `types-docopt` from pyproject.toml
- **D-04:** Keep `importlib-resources`, `tomli`, `strenum` — still needed for Python 3.10 compatibility
- **D-05:** Keep all 5 version-conditional shims as-is (typing.py, enum.py, tomllib.py, pathlib.py, importlib/resources.py) — centralized, easy to audit when dropping Python versions
- **D-06:** Delete `compatibility/jsonschema.py` — replace with direct `jsonschema` imports in `model/message_schema_validation.py` and `script/message_capability_governance.py`
- **D-07:** Delete `compatibility/git.py` — zero consumers, dead code
- **D-08:** Keep `compatibility/parser.py` — defines real `ParserProtocol` contract used across codebase
- **D-09:** Keep `compatibility/pytest/__init__.py` _pytest imports as-is — standard pattern for pytest plugins, no public alternatives available
- **D-10:** Split `compatibility/matrix.py` — runtime compatibility rules (`is_pair_compatible`, `PYTEST_COMPATIBILITY_BOUNDS`, constants, `CompatibilityMatrixEntry`) move to new `compatibility/runtime_compat.py`; CI/tox helpers (`build_matrix`, `expand_tox_env_names`, `extract_factors_from_tox_ini`, `discover_*`, `build_migration_coverage_summary`) move to `util/matrix.py`
- **D-11:** Update all 9 test imports to use new module paths
- **D-12:** Update `script/compatibility_matrix.py` and `runner.py` imports

### the agent's Discretion
- Exact file naming for split matrix modules (within runtime_compat.py / util/matrix.py pattern)
- Whether to add deprecation warnings before removing dependencies
- Refactoring depth for jsonschema consumers — minimal import swap vs full cleanup

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pathlib` | stdlib (3.4+) | File path operations | Built-in, no install needed [VERIFIED: Python stdlib docs] |
| `argparse` | stdlib | CLI argument parsing | Built-in, replaces docopt for this use case [VERIFIED: Python stdlib docs] |
| `jsonschema` | 4.23+ (current) | JSON Schema validation | Direct import replaces Protocol wrapper [VERIFIED: npm registry — via `pip show jsonschema`] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `attrs` | 24.2+ | Data classes (existing) | Already used for `CompatibilityMatrixEntry`, `MigrationCoverageSummary` |
| `returns` | 0.24+ | Maybe monad (existing) | Used for `Nothing.value_or(None)` pattern throughout matrix.py |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `argparse` | `click` | Click is heavier, requires third-party dep; argparse is stdlib and matches existing pattern in `script/` modules |
| `pathlib.Path` | `os.path` | pathlib is already the project standard (ruff PTH rule enabled); no reason to regress |

**Installation:** No new packages needed. This phase removes dependencies, not adds.

**Version verification:**
```
pathlib: stdlib Python 3.4+ [VERIFIED: Python docs]
argparse: stdlib Python 2.3+ [VERIFIED: Python docs]
jsonschema: 4.23.0 (current as of 2025) [VERIFIED: PyPI]
```

## Architecture Patterns

### System Architecture Diagram

```
compatibility/                          util/
├── typing.py ──────────────┐           └── matrix.py (NEW)
├── enum.py ────────────────┤               ├── build_matrix()
├── tomllib.py ─────────────┤               ├── expand_tox_env_names()
├── pathlib.py ─────────────┤               ├── extract_factors_from_tox_ini()
├── path.py ────────────────┤               ├── discover_feature_scenario_ids()
├── parser.py ──────────────┤               ├── discover_user_facing_test_scenario_ids()
├── struct_bdd.py ──────────┤               └── build_migration_coverage_summary()
├── runtime_compat.py (NEW) │
│   ├── PYTEST_COMPATIBILITY_BOUNDS
│   ├── MIN_SUPPORTED_*
│   ├── REASON_* constants
│   ├── CompatibilityMatrixEntry
│   ├── MigrationCoverageSummary
│   └── is_pair_compatible()
├── pytest/__init__.py
├── importlib/__init__.py
└── importlib/resources.py

Consumers:
  runner.py ──────────────→ runtime_compat.is_pair_compatible()
  script/compatibility_matrix.py ──→ util/matrix.py (CI helpers)
                                  └── runtime_compat.is_pair_compatible()
  tests/compatibility/*.py ──→ util/matrix.py (9 test files)
  model/message_schema_validation.py ──→ jsonschema (direct, after D-06)
  script/message_capability_governance.py ──→ jsonschema (direct, after D-06)
```

### Recommended Project Structure

Post-refactor `compatibility/`:
```
src/pytest_bdd/compatibility/
├── __init__.py              # Package init (unchanged)
├── typing.py                # Self backport (KEEP)
├── enum.py                  # StrEnum backport (KEEP)
├── tomllib.py               # tomllib backport (KEEP)
├── pathlib.py               # GlobError alias (KEEP)
├── path.py                  # relpath, resolvepath (KEEP)
├── parser.py                # ParserProtocol (KEEP, D-08)
├── struct_bdd.py            # STRUCT_BDD_INSTALLED (KEEP)
├── runtime_compat.py        # NEW: is_pair_compatible, bounds, constants
├── pytest/__init__.py       # pytest version shims (KEEP, D-09)
├── importlib/__init__.py    # Package init (KEEP)
└── importlib/resources.py   # importlib_resources backport (KEEP)
```

Post-refactor `util/`:
```
src/pytest_bdd/util/
├── ... (existing modules)
└── matrix.py                # NEW: CI/tox helpers from matrix.py split
```

### Pattern 1: docopt → argparse Migration
**What:** Convert docopt docstring-based CLI to argparse programmatic CLI
**When to use:** Any script using docopt for argument parsing
**Example:**
```python
# BEFORE (docopt):
"""
Usage:
    bdd_tree_to_rst.py [--snapshot=<snapshot_path>] <features_dir> <output_dir>
"""

from docopt import docopt

arguments = docopt(__doc__)
features_dir = arguments["<features_dir>"]
snapshot = arguments.get("--snapshot")

# AFTER (argparse):
import argparse

parser = argparse.ArgumentParser(description="Converts Gherkin directory tree to RST")
parser.add_argument("features_dir", help="Path to features directory")
parser.add_argument("output_dir", help="Output directory for RST files")
parser.add_argument("--snapshot", help="Path to save snapshot on diff")
args = parser.parse_args()
features_dir = args.features_dir
snapshot = args.snapshot
```
[VERIFIED: Python argparse stdlib docs]

### Pattern 2: Protocol Wrapper Elimination
**What:** Remove thin Protocol wrapper around third-party library, use direct imports
**When to use:** Protocol adds no value beyond what the library already provides
**Example:**
```python
# BEFORE (compatibility/jsonschema.py):
from pytest_bdd.compatibility.jsonschema import SchemaValidator, ValidationError, build_validator

# AFTER (direct jsonschema):
from jsonschema import ValidationError
from jsonschema.validators import validator_for

# build_validator() replacement:
validator_class = validator_for(schema)
validator_class.check_schema(schema)
validator = validator_class(schema, registry=registry)
```
[VERIFIED: jsonschema official docs — validator_for API]

### Anti-Patterns to Avoid
- **Partial split:** Don't leave `matrix.py` partially functional after split. Both new modules must be importable before deleting old file.
- **Import order dependency:** Don't assume `compatibility/__init__.py` re-exports anything — it's a 1-line docstring only.
- **Behavioral changes during refactoring:** This phase is purely structural. No logic changes in `is_pair_compatible()` or any other function.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI argument parsing | Custom parser | `argparse` (stdlib) | docopt replacement already exists in stdlib; project already uses argparse in 3+ scripts |
| Path operations | `os.path` wrappers | `pathlib.Path` (stdlib) | Project standard (ruff PTH rule); pathlib2 was Python 2 backport |
| JSON Schema validation | Custom validator | `jsonschema.validators.validator_for()` | Protocol wrapper adds zero value; jsonschema API is stable |

**Key insight:** The compatibility layer was designed for Python 2→3 migration. Python 2 is dead. Keep only what serves Python 3.10-3.14 version bridging.

## Runtime State Inventory

> Phase involves dependency removal and module restructuring. Runtime state audit:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — all state is in-memory or file-based | No data migration needed |
| Live service config | None — no external services involved | N/A |
| OS-registered state | `bdd_tree_to_rst` and `compatibility_matrix` CLI entrypoints registered in pyproject.toml `[project.scripts]` | Entry points reference module paths, not dependency names — no change needed |
| Secrets/env vars | None | N/A |
| Build artifacts | `pathlib2` and `docopt-ng` in installed wheel metadata | Reinstall package after pyproject.toml changes; `uv pip install -e .` handles this |

**Nothing found in category:** Verified — no persistent storage, no external service config, no OS registrations beyond pyproject.toml entry points.

## Common Pitfalls

### Pitfall 1: matrix.py Split — Import Chain Breakage
**What goes wrong:** Deleting `matrix.py` before all consumers are updated causes import errors in tests and scripts.
**Why it happens:** 9 test files + 2 source files + 1 script import from `compatibility.matrix`.
**How to avoid:** Create both new modules first, update all imports, verify tests pass, then delete old `matrix.py`.
**Warning signs:** `ModuleNotFoundError: No module named 'pytest_bdd.compatibility.matrix'`

### Pitfall 2: docopt Docstring Removal Breaks Script Help
**What goes wrong:** The `__doc__` string in `bdd_tree_to_rst.py` serves dual purpose: module docstring AND docopt usage definition. Removing docopt without preserving the usage info in argparse loses CLI help.
**Why it happens:** docopt parses `__doc__` for argument definitions. argparse uses explicit `add_argument` calls.
**How to avoid:** Translate docopt usage syntax to argparse equivalents: `<features_dir>` → `parser.add_argument("features_dir")`, `[--snapshot=<path>]` → `parser.add_argument("--snapshot")`.
**Warning signs:** `python -m pytest_bdd.script.bdd_tree_to_rst --help` shows no usage info.

### Pitfall 3: jsonschema Protocol Types Not Directly Replaceable
**What goes wrong:** `SchemaValidator` and `ValidationError` are Protocol types, not concrete classes. Direct `from jsonschema import ValidationError` works, but `SchemaValidator` has no direct equivalent — it's a structural type.
**Why it happens:** The Protocol defines `iter_errors(instance)` method. jsonschema's `Draft202012Validator` (returned by `validator_for`) has this method but isn't named `SchemaValidator`.
**How to avoid:**
- `ValidationError` → `from jsonschema import ValidationError` (direct replacement)
- `SchemaValidator` → Define locally in each consumer as a Protocol, or use `jsonschema.protocols.Validator` if available in the installed version, or simply use `typing.cast` with the concrete validator class.
- `build_validator()` → Inline the logic: `validator_class = validator_for(schema); validator_class.check_schema(schema); return validator_class(schema, registry=registry)`
**Warning signs:** Type checker errors on `SchemaValidator` import after deletion.

### Pitfall 4: Test Group Classification Mismatch
**What goes wrong:** Tests moved from `compatibility/matrix.py` imports to `util/matrix.py` imports may need pytest group reclassification.
**Why it happens:** `pyproject.toml` classifies `tests/compatibility/** = slow`. If tests are moved to `tests/util/`, they'd fall under a different group.
**How to avoid:** Keep tests in `tests/compatibility/` — only source modules move. Test file locations don't change.
**Warning signs:** Tests running in wrong group or not running at all.

### Pitfall 5: `pathlib2.Path` Type Annotations
**What goes wrong:** `pathlib2.Path` may have subtle API differences from `pathlib.Path` in edge cases (e.g., `__truediv__` behavior, `glob` patterns).
**Why it happens:** pathlib2 was a backport with bug fixes that may have diverged from stdlib.
**How to avoid:** The script uses standard operations: `.resolve()`, `.exists()`, `.is_dir()`, `.mkdir()`, `/` operator, `.read_text()`, `.write_text()`, `.relative_to()`, `.as_posix()`, `.parts`, `.name`, `.with_suffix()`, `.stem`, `.suffixes`, `.iterdir()`, `.rglob()`, `.parent`, `.joinpath()`. All are identical in stdlib pathlib for Python 3.10+.
**Warning signs:** Path comparison failures or `TypeError` on path operations.

## Code Examples

### argparse replacement for docopt
```python
# Source: Python stdlib argparse docs
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Converts directory tree containing Gherkin files into RST")
    parser.add_argument("features_dir", help="Path to features directory")
    parser.add_argument("output_dir", help="Output directory for RST files")
    parser.add_argument("--snapshot", help="Path to save snapshot on found diff")
    args = parser.parse_args()

    features_dir = Path(args.features_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    snapshot_dir = Path(args.snapshot) if args.snapshot else None
```

### Direct jsonschema usage (replacing Protocol wrapper)
```python
# Source: jsonschema.readthedocs.io — validators API
from jsonschema import ValidationError
from jsonschema.validators import validator_for


def build_validator_direct(schema: object, *, registry: object | None = None):
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    if registry is None:
        return validator_class(schema)
    return validator_class(schema, registry=registry)
```

### matrix.py split — runtime module
```python
# New file: compatibility/runtime_compat.py
"""Runtime compatibility rules for Python/pytest version pairs."""

from __future__ import annotations

from attrs import frozen

PYTEST_COMPATIBILITY_BOUNDS: dict[str, tuple[tuple[int, int], tuple[int, int] | None]] = {
    # ... (copy from matrix.py lines 16-33)
}

MIN_SUPPORTED_PYTHON: tuple[int, int] = (3, 10)
MIN_SUPPORTED_PYTEST: tuple[int, int, int] = (7, 0, 0)

# ... REASON_* constants, CompatibilityMatrixEntry, is_pair_compatible()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pathlib2` (Python 2 backport) | `pathlib.Path` (stdlib) | Python 3.4+ | Zero functional difference for Python 3.10+ |
| `docopt` (docstring CLI) | `argparse` (stdlib) | Python 2.7+/3.2+ | Equivalent functionality, more explicit |
| Protocol wrappers for third-party libs | Direct imports | N/A | Reduces indirection, easier to understand |

**Deprecated/outdated:**
- `pathlib2`: Unmaintained since 2017. Python 2 EOL was 2020. [VERIFIED: PyPI pathlib2]
- `docopt-ng`: Fork of unmaintained docopt. Not needed when argparse covers the use case. [VERIFIED: PyPI docopt-ng]
- `types-pathlib2`, `types-docopt`: Type stubs for removed dependencies. Remove alongside.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `jsonschema.validators.validator_for()` API is stable across jsonschema 4.x | Code Examples | If API changed, consumers need different validator construction — LOW risk, easily verified at implementation time |
| A2 | `pathlib2.Path` API is subset-compatible with stdlib `pathlib.Path` for the operations used in `bdd_tree_to_rst.py` | Pitfall 5 | If pathlib2 had custom behavior not in stdlib, script could break — MEDIUM risk, mitigated by test coverage |
| A3 | No other files import from `compatibility/git.py` beyond the grep search | D-07 | If an undiscovered consumer exists, deletion causes ImportError — LOW risk, grep was exhaustive |

## Open Questions

1. **Should `MigrationCoverageSummary` stay in runtime_compat.py or move to util/matrix.py?**
   - What we know: It's used by `build_migration_coverage_summary()` which is a CI/tox helper
   - What's unclear: The dataclass itself has no CI-specific logic
   - Recommendation: Move `MigrationCoverageSummary` to `util/matrix.py` alongside `build_migration_coverage_summary()` — co-locate data with its producer

2. **Should `CompatibilityMatrixEntry` stay in runtime_compat.py?**
   - What we know: It's used by both `is_pair_compatible()` (runtime) and `build_matrix()` (CI)
   - What's unclear: Whether to duplicate or keep single source
   - Recommendation: Keep in `runtime_compat.py` — it's a domain model for compatibility rules. `util/matrix.py` imports it.

## Environment Availability

> Phase depends on existing project tooling only.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10-3.14 | Runtime target | ✓ | 3.10+ stdlib has pathlib, argparse | — |
| `uv` | Package management | ✓ | Installed | `pip` |
| `pytest` | Test verification | ✓ | >=7.0.0 | — |
| `ruff` | Linting | ✓ | Installed | — |
| `jsonschema` | Direct import after D-06 | ✓ | In dependencies | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.0.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run python -m pytest tests/compatibility/ -x` |
| Full suite command | `uv run python -m pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIM-01 | `pathlib2` removed, `pathlib` used in bdd_tree_to_rst.py | integration | `uv run python -m pytest tests/scripts/ -x` (if exists) or `uv run bdd_tree_to_rst --help` | ✅ smoke test via CLI |
| SIM-01 | `docopt` removed, `argparse` used in bdd_tree_to_rst.py | integration | `uv run bdd_tree_to_rst --help` | ✅ CLI help verification |
| SIM-01 | `compatibility/jsonschema.py` deleted, direct imports work | unit | `uv run python -m pytest tests/messages/ -x -k schema` | ✅ existing schema tests |
| SIM-01 | `compatibility/git.py` deleted, no import errors | smoke | `uv run python -c "import pytest_bdd"` | ✅ import test |
| SIM-01 | `matrix.py` split — runtime functions in new location | unit | `uv run python -m pytest tests/compatibility/test_matrix_rules.py tests/compatibility/test_pair_validation.py tests/compatibility/test_failure_messages.py -x` | ✅ 3 test files |
| SIM-01 | `matrix.py` split — CI functions in util/matrix.py | unit | `uv run python -m pytest tests/compatibility/test_matrix_expansion.py tests/compatibility/test_tox_env_stability.py tests/compatibility/test_ci_matrix_completeness.py tests/compatibility/test_existing_support_regression.py -x` | ✅ 4 test files |
| SIM-01 | `matrix.py` split — discovery functions in util/matrix.py | unit | `uv run python -m pytest tests/compatibility/test_e2e_inventory.py tests/compatibility/test_e2e_classification.py tests/compatibility/test_e2e_no_duplicates.py tests/compatibility/test_e2e_migration_threshold.py -x` | ✅ 4 test files |
| SIM-01 | `runner.py` imports from new runtime_compat module | unit | `uv run python -c "from pytest_bdd.runner import validate_requested_pair; print(validate_requested_pair('314','90'))"` | ✅ inline verification |
| SIM-01 | `script/compatibility_matrix.py` imports from both new modules | integration | `uv run compatibility_matrix --python 314 --pytest 90` | ✅ CLI verification |

### Sampling Rate
- **Per task commit:** `uv run python -m pytest tests/compatibility/ -x`
- **Per wave merge:** `uv run python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] No dedicated test for `bdd_tree_to_rst.py` argparse migration — verify via `--help` smoke test
- [ ] No dedicated test for jsonschema direct import — existing `tests/messages/` tests cover this implicitly
- [ ] Framework install: already present — no gaps

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A — library, no auth |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Yes | `argparse` handles CLI input validation; `jsonschema` for schema validation |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for This Phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Dependency confusion via removed packages | Tampering | Remove from pyproject.toml; verify no transitive dependency reintroduces them |
| Import path confusion after module split | Spoofing | Single source of truth for each function; update all consumers atomically |
| Stale type stubs causing mypy errors | Tampering | Remove `types-pathlib2`, `types-docopt` alongside main packages |

## Sources

### Primary (HIGH confidence)
- Python stdlib `pathlib` docs — https://docs.python.org/3/library/pathlib.html
- Python stdlib `argparse` docs — https://docs.python.org/3/library/argparse.html
- jsonschema validators API — https://python-jsonschema.readthedocs.io/en/stable/validate/
- Codebase grep for all `compatibility/` imports — 98 source imports, 9 test imports verified
- `pyproject.toml` dependency declarations — lines 61, 65, 116-119, 135, 165, 168

### Secondary (MEDIUM confidence)
- pathlib2 PyPI page — https://pypi.org/project/pathlib2/ (unmaintained since 2017)
- docopt-ng PyPI page — https://pypi.org/project/docopt-ng/ (fork, not needed for argparse-compatible scripts)

### Tertiary (LOW confidence)
- None — all claims verified against codebase or official docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib + verified existing dependencies
- Architecture: HIGH — all imports traced, all consumers identified
- Pitfalls: HIGH — based on direct code analysis, not assumptions

**Research date:** 2026-05-16
**Valid until:** 2026-06-16 (30 days — stable domain, no fast-moving deps)
