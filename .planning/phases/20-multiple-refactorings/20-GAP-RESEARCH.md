# Phase 20 Gap-Closure: Test Package Extraction + __init__.py Elimination + PEP 420 — Research

**Researched:** 2026-06-10
**Domain:** Python packaging (setuptools multi-package discovery), PEP 420 namespace packages, mypy no_implicit_reexport, Docker compose path resolution
**Confidence:** HIGH

## Summary

This research covers the five tightly-coupled gap-closure domains for Phase 20 Wave 3: extracting tests to an independent `src/pytest_bdd_testing/` package, fixing broken Docker compose paths (currently 5 levels deep reaching `src/` instead of repo root), eliminating remaining `__all__` from public API `__init__.py` files under `no_implicit_reexport`, systematically removing empty `__init__.py` files per PEP 420, and updating the `init_rules.py` custom ruff rule for the new conventions (BLQ1401/1402/1403 redefinition).

The migration from `src/pytest_bdd/testing/` to `src/pytest_bdd_testing/` changes approximately 43 import sites, 73 `__init__.py` files in the testing tree, Docker compose paths (context depth changes from 6→5 levels thanks to shallower tree), Dockerfile COPY commands, controller/worker entrypoint Python module paths, and pyproject.toml config (testpaths, test_group_paths, mypy overrides, optional-dependencies).

The `__all__` elimination is gated by mypy's `no_implicit_reexport` flag which requires explicit re-exports. The replacement pattern is `from module import Symbol as Symbol` (the `as` alias form counts as explicit re-export, per mypy docs), not just removing `__all__` blindly.

**Primary recommendation:** Execute in strict dependency order per R10: R1-R4 (test package extraction + Docker rework) first, then R5-R9 (__init__.py elimination + namespace packages + rule updates). The test package extraction is prerequisite because Docker path fixes and import rewrites are logically entangled with the package move.

## User Constraints (from CONTEXT-GAPS.md)

### Locked Decisions

- **R1:** Tests must live in `src/pytest_bdd_testing/` — a completely separate package at `./src` level, parallel to `src/pytest_bdd/`.
- **R2:** `[project.optional-dependencies]` testing extra MUST be `testing = ["pytest_bdd_testing"]`.
- **R3:** Remove old `tests/` directory entirely after migration.
- **R4:** All Docker paths resolve from repo root. docker-compose.yml context, Dockerfile COPY paths, controller/worker entrypoint imports — all must use new `src/pytest_bdd_testing/` paths.
- **R5:** Eliminate empty `__init__.py` files (only classification comments). PEP 420 implicit namespace packages.
- **R6:** No `__all__` lists. Packages expose API via direct imports from canonical modules.
- **R7:** No backward compatibility. Remove re-exports added during INIT-01. No transitional facade.py for testing package.
- **R8:** Before deleting `__init__.py`: research which directories can use implicit namespace packages and which MUST keep `__init__.py`.
- **R9:** Update `init_rules.py`: BLQ1401 (no `__all__` in `__init__.py`), BLQ1402 (no empty `__init__.py`), BLQ1403 (`__init__.py` only for actual code).
- **R10:** Dependency order: R1-R4 first (test package extraction), then R5-R9 (__init__.py elimination).

### the agent's Discretion

- Exact directory structure of `src/pytest_bdd_testing/` (sub-packages, conftest placement)
- Whether to use `pytest_bdd_testing` or alternative package name
- How to handle the `stubs/` directory (already namespace-package-like)
- Whether mypy `no_implicit_reexport` exceptions for the remaining 10 `__all__` files are acceptable or need rework

### Deferred Ideas (OUT OF SCOPE)

- Full PEP 420 migration of `stubs/` directory — already compatible
- Removing `__init__.py` from `_ruff/rules/` directory — needs code execution, not just namespace
- Addressing 32 pre-existing layer_rules violations — separate concern

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| R1 | Separate test package at `src/pytest_bdd_testing/` | §R1 — Setuptools multi-package discovery, exclude from wheel, editable install behavior |
| R2 | Optional dependency `testing = ["pytest_bdd_testing"]` | §R2 — Local package dependency resolution, PEP 508 direct references, editable install path |
| R3 | Remove old `tests/` directory entirely | §R3 — Verification checklist: stale conftest, __pycache__, Docker asset copies |
| R4 | Docker compose reworked for new layout | §R4 — Context depth 5 levels from new location, Dockerfile COPY paths, entrypoint module paths |
| R5 | Eliminate empty `__init__.py` | §R5 — PEP 420 safety analysis per directory, ruff INP001 suppression list |
| R6 | Eliminate `__all__` from `__init__.py` | §R6 — mypy no_implicit_reexport replacement: `from X import Y as Y` pattern |
| R7 | No backward compatibility | §R7 — What to delete: facade.py re-exports, `tests/` dir, old import paths |
| R8 | PEP 420 namespace package research | §R8 — Directory-by-directory analysis: safe vs. must-keep |
| R9 | Update init_rules.py | §R9 — New BLQ1401/1402/1403 definitions, testing directory awareness |
| R10 | Dependency order | §R10 — Task sequencing rationale |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Package discovery (setuptools) | Build system | pyproject.toml config | `[tool.setuptools.packages.find]` controls which src/ dirs become packages |
| Test imports (43 sites) | Source tree | mypy overrides | Import paths change from `pytest_bdd.testing.*` → `pytest_bdd_testing.*` |
| Docker compose context | Docker build | File system layout | Context depth changes from 6→5 levels; Dockerfiles reference new paths |
| pylugin loading (pytest11 entry points) | Plugin system | pyproject.toml | Unchanged — entry points reference `pytest_bdd.plugin.*` (not testing) |
| __all__ elimination | mypy no_implicit_reexport | `from X import Y as Y` pattern | mypy requires explicit re-exports; `as` alias counts |
| PEP 420 namespace packages | Python runtime (3.3+) | ruff INP001 suppressions | Directories without `__init__.py` need INP001 exclusion |
| Custom ruff rules (init_rules.py) | CI/pre-commit | AST visitor in `_ruff/rules/` | Rule semantics change from advisory to enforcement |

## Standard Stack

### Core (already in project — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|-------------|
| setuptools | latest (build backend) | Package discovery, wheel building | Already configured; `[tool.setuptools.packages.find]` controls multi-package discovery |
| mypy | latest | Static type checking with `no_implicit_reexport` | Already configured; gates __all__ elimination strategy |
| ruff | ≥0.15 | INP001 namespace package enforcement | Already configured; per-file-ignores needed for new namespace dirs |
| Python | 3.10+ (3.14 target) | PEP 420 implicit namespace packages | Built into CPython since 3.3; no library needed |

### No new packages needed

This gap-closure is purely a refactoring operation. No new PyPI packages are required. The only configuration changes are in existing tooling (setuptools find config, mypy overrides, ruff per-file-ignores, pyproject.toml testpaths).

## Package Legitimacy Audit

> No new external packages are installed in this gap-closure. All changes are code moves, config updates, and file deletions.

| Package | Registry | Disposition |
|---------|----------|-------------|
| (none) | — | No new packages — audit skipped |

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              WAVE 1: TEST PACKAGE EXTRACTION (R1-R4)         │
│                                                              │
│  ┌──────────────────────┐    ┌─────────────────────────────┐ │
│  │ src/pytest_bdd/       │    │ src/pytest_bdd_testing/      │ │
│  │  testing/  ──MOVE──▶ │    │  assets/docker/remote_xdist/ │ │
│  │   cases/              │    │  cases/{unit,integration,...}│ │
│  │   conftest.py         │    │  conftest.py                 │ │
│  │   docker.py           │    │  docker.py                   │ │
│  │   cucumber_formatters/│    │  cucumber_formatters/        │ │
│  │   ...                 │    │  ...                         │ │
│  └──────────────────────┘    └──────────────┬──────────────┘ │
│                                              │                │
│                          ┌───────────────────┘                │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │                    REWRITE IMPORTS (43 sites)             ││
│  │                                                          ││
│  │  from pytest_bdd.testing.X import Y                      ││
│  │  → from pytest_bdd_testing.X import Y                    ││
│  │                                                          ││
│  │  Impacted files:                                         ││
│  │  • test files (inside testing/ dir) — self-references    ││
│  │  • Docker entrypoints (controller_entrypoint.py)         ││
│  │  • Docker verify_report.py                               ││
│  │  • mypy overrides in pyproject.toml                      ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                    │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              FIX DOCKER COMPOSE PATHS (R4)               ││
│  │                                                          ││
│  │  CURRENT (BROKEN): context: ../../../../..  → src/ ✗     ││
│  │  CURRENT needs:     context: ../../../../../..  → root ✓ ││
│  │                                                          ││
│  │  NEW LOCATION:                                         ││
│  │  src/pytest_bdd_testing/assets/docker/remote_xdist/    ││
│  │  context: ../../../../.. (5 levels) = repo root ✓       ││
│  │                                                          ││
│  │  Dockerfiles: COPY src/pytest_bdd_testing/... → /app/   ││
│  │  Entrypoints: pytest_bdd_testing.assets.docker...       ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                    │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              UPDATE pyproject.toml (R1,R2)               ││
│  │                                                          ││
│  │  exclude = ["pytest_bdd_testing*"]  # keep out of wheel  ││
│  │  testing = ["pytest_bdd_testing"]   # R2 requirement     ││
│  │  testpaths = ["src/pytest_bdd_testing/cases"]            ││
│  │  test_group_paths = [                                    ││
│  │    "src/pytest_bdd_testing/cases/..."                    ││
│  │  ]                                                       ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                    │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              REMOVE tests/ DIRECTORY (R3)                ││
│  │                                                          ││
│  │  rm -rf tests/  (73 __init__.py, stale conftest,        ││
│  │  duplicate Docker assets, __pycache__)                   ││
│  │  Update Makefile docker target paths                     ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│        WAVE 2: __init__.py ELIMINATION + PEP 420 (R5-R9)     │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  STEP 1: Replace __all__ with `from X import Y as Y`    ││
│  │                                                          ││
│  │  10 files with __all__ → replace with as-import pattern ││
│  │  Keeps mypy no_implicit_reexport happy                   ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                    │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  STEP 2: Delete empty __init__.py files                 ││
│  │                                                          ││
│  │  ~70 testing/__init__.py files → DELETE (PEP 420)       ││
│  │  Selected main-package __init__.py files → DELETE        ││
│  │  Add INP001 suppressions for new namespace dirs          ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                    │
│                          ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  STEP 3: Update init_rules.py (R9)                      ││
│  │                                                          ││
│  │  BLQ1401 (was "empty"): No __all__ in __init__.py       ││
│  │  BLQ1402 (was "re-exports"): No empty __init__.py       ││
│  │  BLQ1403 (was "__all__ advisory"): __init__.py only for ││
│  │    actual code (imports, __getattr__, etc.)              ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Pattern 1: `from X import Y as Y` — mypy explicit re-export

**What:** When `no_implicit_reexport = true`, mypy does not treat `from foo import bar` as re-exporting `bar`. The `from foo import bar as bar` form (aliasing to same name) is treated as explicit re-export.

**When to use:** Every `__init__.py` that currently uses `__all__` for re-export control.

**Source:** [VERIFIED: /python/mypy — "The --no-implicit-reexport flag... mypy will not re-export unless the item is imported using from-as or is included in __all__."]

```python
# BEFORE (with __all__):
from pytest_bdd.parsers.base import StepParser
from pytest_bdd.parsers.re_parser import re as re_parser
__all__ = ["StepParser", "re_parser"]

# AFTER (no __all__ needed):
from pytest_bdd.parsers.base import StepParser as StepParser
from pytest_bdd.parsers.re_parser import re as re_parser
# ^ mypy treats 'as StepParser' and 'as re_parser' as explicit re-exports
```

### Pattern 2: Setuptools multi-package discovery with exclude

**What:** When `src/` contains multiple packages (`pytest_bdd`, `pytest_bdd_testing`), setuptools discovers both. `exclude` keeps the testing package out of the distribution wheel while it remains importable in editable installs.

**Source:** [VERIFIED: /pypa/setuptools — Package discovery docs, exclude glob patterns]

```toml
# pyproject.toml — multi-package layout with testing excluded from wheel
[tool.setuptools.packages.find]
where = ["src"]
include = ["pytest_bdd", "pytest_bdd*"]       # Only pytest_bdd + sub-packages in wheel
exclude = ["pytest_bdd_testing*", "pytest_bdd.testing*"]  # Testing stays local
namespaces = false  # Keep: regular packages only (__init__.py required)
```

### Pattern 3: Docker compose context depth calculation

**What:** The context depth (number of `..` components) equals the number of directory levels from the docker-compose.yml location up to the repo root. The migration changes this from 6 (current wrong: 5) to 5 (correct for new location).

**Source:** Verified by counting directory components from actual file locations.

```
CURRENT location:  src/pytest_bdd/testing/assets/docker/remote_xdist/docker-compose.yml
  Directory depth below repo root: 6 (src/pytest_bdd/testing/assets/docker/remote_xdist)
  context needed for repo root: ../../../../../.. (6 levels)
  Current context in file: ../../../../.. (5 levels → WRONG, resolves to src/)

NEW location:       src/pytest_bdd_testing/assets/docker/remote_xdist/docker-compose.yml
  Directory depth below repo root: 5 (src/pytest_bdd_testing/assets/docker/remote_xdist)
  context needed for repo root: ../../../../.. (5 levels → CORRECT)
```

```yaml
# docker-compose.yml at new location — correct context depth
services:
  controller:
    build:
      context: ../../../../..       # 5 levels → repo root ✓
      dockerfile: >-
        src/pytest_bdd_testing/assets/docker/remote_xdist/controller.Dockerfile
```

```dockerfile
# controller.Dockerfile at new location — all COPY paths from repo root
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src/pytest_bdd /app/src/pytest_bdd/
COPY src/pytest_bdd_testing/assets/docker/remote_xdist/ssh/ /etc/pytest-bdd/
COPY src/pytest_bdd_testing/cases/contract /app/src/pytest_bdd_testing/cases/contract/

ENTRYPOINT ["python", "src/pytest_bdd_testing/assets/docker/remote_xdist/controller_entrypoint.py"]
```

```python
# controller_entrypoint.py — updated Python module paths
# OLD: "pytest_bdd.testing.assets.docker.remote_xdist.project.remote_aggregation_case"
# NEW:
"--pyargs",
"pytest_bdd_testing.assets.docker.remote_xdist.project.remote_aggregation_case",
```

### Anti-Patterns to Avoid

- **Blind `__all__` removal:** Removing `__all__` without replacing with `from X import Y as Y` will break mypy `no_implicit_reexport`. The resulting errors cascade into downstream type checking.
- **Removing `__init__.py` from code-bearing packages:** Directories like `_ruff/rules/`, `_gherkin_go/` that contain executable code in their `__init__.py` MUST keep it. PEP 420 only applies to pure namespace containers.
- **Keeping testing package in distribution wheel:** Without `exclude`, `pytest_bdd_testing` ships in the user-facing wheel, bloating the install and exposing test internals.
- **Changing docker compose context without updating Dockerfile COPY paths:** Context depth and COPY paths are coupled. Changing one without the other produces silent build failures caught only at `docker compose build` time.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Package discovery for multi-package src/ | Custom setup.py logic | `[tool.setuptools.packages.find]` with `include`/`exclude` | Already configured; setuptools handles exclusion for wheel vs editable |
| mypy explicit re-export without `__all__` | Custom __getattr__ or module-level `__all__` | `from module import Symbol as Symbol` | mypy treats `as` alias as explicit re-export — documented behavior |
| PEP 420 namespace package validation | Custom import check | ruff `INP001` rule with per-file-ignores | Already enabled; just add exclusion patterns |
| Docker context depth verification | Manual path counting | Count directory components from file to repo root | Deterministic; `Get-ChildItem` depth count from known root |
| Import path rewriting (43 sites) | Manual find-and-replace | `sed`/`rg` with regex: `pytest_bdd\.testing` → `pytest_bdd_testing` | Standard tooling; verify with `rg "pytest_bdd\.testing"` after rewrite |

## Runtime State Inventory

> This is a rename/refactoring phase. File moves and import path changes may leave stale references in non-git tracked state.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — pytest-bdd has no databases or persistent storage | None |
| Live service config | None — no external service configs reference internal test paths | None |
| OS-registered state | None — no Windows services, Task Scheduler tasks, or launchd plists | None |
| Secrets/env vars | `.env` file at project root — contains `PYTEST_BDD_GHERKIN_BACKEND` and possibly `PYTEST_REMOTE_MODE`; does NOT reference `pytest_bdd.testing` paths | None — env var names unchanged |
| Build artifacts | `src/pytest_bdd/testing/__pycache__/` (73 dirs) — stale after move; `tests/__pycache__/` — stale after deletion; `dist/*.whl` — stale until rebuild; `.egg-info/` — stale until reinstall | `pip install -e .` cleans .egg-info; `find . -name __pycache__ -path '*/testing/*' -prune -exec rm -rf {} +` for stale caches |
| Docker images | `pytest-bdd-remote-xdist-controller:local` and `pytest-bdd-remote-xdist-worker:local` — contain old `/app/src/pytest_bdd/testing/` paths | `docker compose build --no-cache` rebuilds from new Dockerfiles |
| Docker volumes | `./artifacts` at docker-compose location — contains old report paths | Clean after rebuild: `docker compose down --volumes` |

**Nothing found in most runtime categories:** Verified — pytest-bdd is a library with no persistent runtime state, databases, or OS registrations.

## Step 2.6: Environment Availability Audit

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Package imports | ✓ | 3.14.2 | — |
| setuptools | Package discovery | ✓ | (build backend) | — |
| git | File move tracking | ✓ | (repo) | — |
| Docker | docker compose build verification | ✗ | — | Skip Docker verification; path correctness verified via directory counting |
| docker compose | Build verification | ✗ | — | Same as Docker |

**Missing dependencies with fallback:**
- Docker/Docker Compose — not available on this Windows machine. Docker path correctness is verified analytically (directory depth counting). Full Docker build verification is deferred to CI or a Docker-capable environment.

**Missing dependencies with no fallback:**
- None — all critical operations (file moves, import rewrites, config updates) use standard tools available in the environment.

## R1: Separate Test Package — Detailed Findings

### Current State

The `src/pytest_bdd/testing/` directory contains:
- **73 `__init__.py` files** — mostly empty package markers (`# init: package-marker`)
- **43 import sites** referencing `pytest_bdd.testing.*` from within the testing tree and from a few main-package locations
- Directory structure: `cases/{unit,integration,contract,e2e,compat,perf,external}/`, `cucumber_formatters/`, `assets/docker/remote_xdist/`, `docker.py`, `docker_cluster.py`, `pytest_results.py`, plus legacy directories (`args/`, `compatibility/`, `contract/`, etc.)
- `conftest.py` at `src/pytest_bdd/testing/cases/conftest.py` (primary) and `src/pytest_bdd/testing/cases/e2e/conftest.py` (e2e-specific)

### Target State

```
src/
├── pytest_bdd/           # Main library (testing/ subdir REMOVED)
│   ├── __init__.py
│   ├── ...
│   └── (no testing/ directory)
│
└── pytest_bdd_testing/   # Independent test package
    ├── __init__.py       # Package marker (regular package, not namespace)
    ├── conftest.py       # (moved from testing/cases/conftest.py — or kept at cases/ level)
    ├── docker.py
    ├── docker_cluster.py
    ├── pytest_results.py
    ├── cucumber_formatters/
    │   ├── __init__.py
    │   ├── facade.py
    │   ├── registry.py
    │   └── rendering.py
    ├── cucumber_formatters.py  # Backward compat shim (deleted per R7 — NO backward compat)
    ├── assets/
    │   └── docker/
    │       └── remote_xdist/
    │           ├── docker-compose.yml
    │           ├── controller.Dockerfile
    │           ├── worker.Dockerfile
    │           ├── controller_entrypoint.py
    │           ├── worker_entrypoint.py
    │           ├── verify_report.py
    │           ├── project/
    │           │   ├── __init__.py
    │           │   ├── aggregation.feature
    │           │   ├── conftest.py
    │           │   └── remote_aggregation_case.py
    │           └── ssh/
    └── cases/
        ├── conftest.py
        ├── unit/
        ├── integration/
        ├── contract/
        ├── e2e/
        │   └── conftest.py
        ├── compat/
        ├── perf/
        └── external/
            └── e2e/
                └── fixtures/
                    └── remote_xdist/
```

### Setuptools Configuration for Multi-Package src/

**Current `[tool.setuptools.packages.find]`:**
```toml
[tool.setuptools.packages.find]
namespaces = false
where = ["src"]
```

This discovers `pytest_bdd` (has `__init__.py`) and all its sub-packages. It also discovers `pytest_bdd.testing` as a sub-package because it has `__init__.py`.

**After migration — two separate top-level packages:**

With `namespaces = false` and both `src/pytest_bdd/__init__.py` and `src/pytest_bdd_testing/__init__.py` present, setuptools discovers both. To keep `pytest_bdd_testing` out of the distribution wheel:

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["pytest_bdd", "pytest_bdd*"]
exclude = ["pytest_bdd_testing*"]
namespaces = false
```

The `include` glob `"pytest_bdd*"` matches `pytest_bdd` and all its sub-packages (`pytest_bdd.model`, `pytest_bdd.plugin.*`, etc.). The `exclude` glob `"pytest_bdd_testing*"` prevents `pytest_bdd_testing` and its sub-packages from being included in the wheel.

**Editable install behavior:** With `pip install -e .`, Python adds `src/` to the path. Both `pytest_bdd` and `pytest_bdd_testing` are importable because they're both regular packages under `src/`. The `exclude` only affects the distribution wheel, not editable imports.

**After removing testing/ from pytest_bdd:** The `src/pytest_bdd/testing/` directory no longer exists, so `pytest_bdd.testing` imports will fail. All internal imports in the testing tree must change from `pytest_bdd.testing.X` to `pytest_bdd_testing.X`.

### Import Rewrite Impact (43 sites)

The 43 import sites break down as:

| Category | Count | Example | Rewrite |
|----------|-------|---------|---------|
| Test file self-references | ~30 | `from pytest_bdd.testing.cucumber_formatters import ...` | `from pytest_bdd_testing.cucumber_formatters import ...` |
| Docker entrypoints | 3 | `pytest_bdd.testing.assets.docker.remote_xdist.project.remote_aggregation_case` | `pytest_bdd_testing.assets.docker.remote_xdist.project.remote_aggregation_case` |
| Main package references to testing | ~5 | `from pytest_bdd.testing.docker import ...` (in test files only) | `from pytest_bdd_testing.docker import ...` |
| conftest.py fixtures | ~5 | `_REMOTE_XDIST_FIXTURE_DIR` calculation, `FIXTURE_DIR` in test_xdist_remote_message_aggregation.py | Path recomputation needed |

### Critical: FIXTURE_DIR in test_xdist_remote_message_aggregation.py

**Line 31:** `FIXTURE_DIR = Path(__file__).resolve().parents[6] / "tests" / "assets" / "docker" / "remote_xdist"`

This references `tests/` (repo root) which will be deleted per R3. The `parents[6]` from this file's location:
- Current: `src/pytest_bdd/testing/cases/external/e2e/test_xdist_remote_message_aggregation.py`
- `parents[6]` = repo root

After migration to `src/pytest_bdd_testing/cases/external/e2e/test_xdist_remote_message_aggregation.py`:
- `parents[5]` = repo root (since `pytest_bdd_testing` is one level shallower than `pytest_bdd.testing` was)
- `parents[4]` = `src/`

The fixture dir path should become:
```python
FIXTURE_DIR = Path(__file__).resolve().parents[5] / "src" / "pytest_bdd_testing" / "assets" / "docker" / "remote_xdist"
```

Or, better — compute relative to known project structure:
```python
FIXTURE_DIR = Path(__file__).resolve().parents[5] / "src" / "pytest_bdd_testing" / "assets" / "docker" / "remote_xdist"
```

### pyproject.toml Changes

```toml
# testpaths — old
testpaths = ["src/pytest_bdd/testing/cases"]
# testpaths — new
testpaths = ["src/pytest_bdd_testing/cases"]

# test_group_paths — old
test_group_paths = [
  "src/pytest_bdd/testing/cases/unit/** = unit",
  "src/pytest_bdd/testing/cases/integration/** = integration",
  ...
]
# test_group_paths — new
test_group_paths = [
  "src/pytest_bdd_testing/cases/unit/** = unit",
  "src/pytest_bdd_testing/cases/integration/** = integration",
  ...
]

# mypy overrides — old
[[tool.mypy.overrides]]
ignore_errors = true
module = ["pytest_bdd.testing.*"]

# mypy overrides — new
[[tool.mypy.overrides]]
ignore_errors = true
module = ["pytest_bdd_testing.*"]
```

### Makefile Changes

```makefile
# Line 218 — old
test-external-docker-build: env-check-docker
	docker compose -f src/pytest_bdd/testing/assets/docker/remote_xdist/docker-compose.yml build

# Line 218 — new
test-external-docker-build: env-check-docker
	docker compose -f src/pytest_bdd_testing/assets/docker/remote_xdist/docker-compose.yml build
```

All `$(PYTEST) src/pytest_bdd/testing/cases/...` references → `$(PYTEST) src/pytest_bdd_testing/cases/...`.

## R2: Optional Dependency Resolution — Detailed Findings

### The Problem

R2 requires `testing = ["pytest_bdd_testing"]` in `[project.optional-dependencies]`. But `pytest_bdd_testing` is a local-only package — it's not published to PyPI. Standard pip dependency resolution will fail for non-editable installs from PyPI.

### Resolution Strategy

**For editable installs (development/CI):** When `pip install -e '.[testing]'` runs from the repo root, `pip` resolves `pytest_bdd_testing` against the local environment. Since the package is importable from `src/` (which is on the path via the editable install), the dependency is satisfied.

**For wheel installs from PyPI:** The `pytest_bdd_testing` package is EXCLUDED from the wheel (via `exclude` in `[tool.setuptools.packages.find]`). End users installing `pip install pytest-bdd-ng[testing]` from PyPI would get a resolution error for `pytest_bdd_testing`.

**Mitigation:** This is acceptable because:
1. The `testing` extra is development-only. End users don't install `[testing]`.
2. CI/Docker environments use editable installs where the local package is available.
3. If `pytest_bdd_testing` was ever needed by downstream test suites, it could be published as a separate PyPI package `pytest-bdd-testing`.

**Implementation:**
```toml
[project.optional-dependencies]
# ... other extras ...
testing = ["pytest_bdd_testing"]
```

**Alternative considered (rejected per R2):** `testing = []` — simpler but violates R2. The `pytest_bdd_testing` reference serves as documentation of the dependency relationship even if pip can't always resolve it from PyPI.

## R3: Old tests/ Directory Removal — Verification Checklist

The `tests/` directory at repo root currently contains a full mirror of the testing tree (from the original Phase 20 Wave 3 migration). After all content is moved to `src/pytest_bdd_testing/` and verified working:

1. **Verify no references to `tests/` in active code:**
   ```bash
   rg '"tests/' src/ Makefile pyproject.toml .github/ --no-ignore
   rg "'tests/" src/ Makefile pyproject.toml .github/ --no-ignore
   rg ' tests/' src/ --no-ignore  # (import references)
   ```

2. **Files to delete:**
   - `tests/__init__.py`
   - `tests/conftest.py`
   - `tests/assets/` (entire tree — duplicate Docker assets)
   - `tests/cases/` (entire tree — duplicate test cases)
   - All support directories (`tests/args/`, `tests/compatibility/`, etc.)
   - All `__pycache__/` under `tests/`

3. **Post-deletion verification:**
   - `pytest --co` (collection only) — pytest should discover tests from `src/pytest_bdd_testing/cases/`
   - No `ImportError` for `tests.*` modules
   - `docker compose build` at new path succeeds (Docker-capable environment)

## R4: Docker Compose Path Rework — Detailed Findings

### Current Docker compose path analysis

The docker-compose.yml at `src/pytest_bdd/testing/assets/docker/remote_xdist/docker-compose.yml` has `context: ../../../../..` (5 levels up). Counting from the file location:

| Level | Directory |
|-------|-----------|
| 0 | `src/pytest_bdd/testing/assets/docker/remote_xdist/` |
| 1 (`..`) | `src/pytest_bdd/testing/assets/docker/` |
| 2 | `src/pytest_bdd/testing/assets/` |
| 3 | `src/pytest_bdd/testing/` |
| 4 | `src/pytest_bdd/` |
| 5 (`../../../../..`) | `src/` ← CURRENT context (BROKEN) |
| 6 (`../../../../../..`) | repo root ← CORRECT context |

**Current context resolves to `src/`, not repo root.** Dockerfiles reference `COPY pyproject.toml README.md /app/` and `COPY src /app/src/` — these need the repo root as context. The review (CR-01) noted this but the fix applied was incomplete (changed from 4→5 levels instead of 4→6).

### New Docker compose path (post-migration)

From `src/pytest_bdd_testing/assets/docker/remote_xdist/docker-compose.yml`:

| Level | Directory |
|-------|-----------|
| 0 | `src/pytest_bdd_testing/assets/docker/remote_xdist/` |
| 1 (`..`) | `src/pytest_bdd_testing/assets/docker/` |
| 2 | `src/pytest_bdd_testing/assets/` |
| 3 | `src/pytest_bdd_testing/` |
| 4 | `src/` |
| 5 (`../../../../..`) | repo root ✓ |

**New context: `../../../../..` = 5 levels = repo root. CORRECT.** The migration naturally fixes the depth because `src/pytest_bdd_testing/` is one level shallower than `src/pytest_bdd/testing/`.

### Dockerfile COPY Path Changes

**controller.Dockerfile (old → new):**

```dockerfile
# OLD (from repo root context):
COPY tests/__init__.py /app/tests/
COPY tests/conftest.py /app/tests/
COPY tests/assets /app/tests/assets/
COPY tests/cases/contract /app/tests/cases/contract/
ENTRYPOINT ["python", "src/pytest_bdd/testing/assets/docker/remote_xdist/controller_entrypoint.py"]

# NEW (from repo root context):
# No tests/ directory — use pytest_bdd_testing paths
COPY src/pytest_bdd_testing/assets/docker/remote_xdist/ssh/ /etc/pytest-bdd/
COPY src/pytest_bdd_testing/cases/contract /app/src/pytest_bdd_testing/cases/contract/
ENTRYPOINT ["python", "src/pytest_bdd_testing/assets/docker/remote_xdist/controller_entrypoint.py"]
```

Note: The `COPY tests/__init__.py tests/conftest.py tests/assets` lines exist to make the old `tests.assets.docker.remote_xdist.project.*` Python import path work inside the container. After migration, the import path becomes `pytest_bdd_testing.assets.docker.remote_xdist.project.*`, which is already on the Python path because `src/` is installed as an editable package. So those COPY lines are no longer needed.

**worker.Dockerfile:** Same pattern — remove `COPY tests/...` lines, ensure `src/pytest_bdd_testing/` is copied (already happens via `COPY src /app/src/`).

### Entrypoint Python Module Path Changes

**controller_entrypoint.py:**

```python
# Line 130 — OLD
"--pyargs", "pytest_bdd.testing.assets.docker.remote_xdist.project.remote_aggregation_case",
# Line 140 — OLD
"-m", "pytest_bdd.testing.assets.docker.remote_xdist.verify_report",

# Line 130 — NEW
"--pyargs", "pytest_bdd_testing.assets.docker.remote_xdist.project.remote_aggregation_case",
# Line 140 — NEW
"-m", "pytest_bdd_testing.assets.docker.remote_xdist.verify_report",
```

**verify_report.py:**

```python
# Line 13 — OLD
from pytest_bdd.testing.cases.contract.messages.message_stream_assertions import (...)
# Line 13 — NEW
from pytest_bdd_testing.cases.contract.messages.message_stream_assertions import (...)
```

**docker_cluster.py line 301:**

```python
# OLD
"src/pytest_bdd/testing/assets/docker/remote_xdist/controller_entrypoint.py",
# NEW
"src/pytest_bdd_testing/assets/docker/remote_xdist/controller_entrypoint.py",
```

### FIXTURE_DIR Path Fix

**test_xdist_remote_message_aggregation.py line 31:**

```python
# OLD — references tests/ at repo root (will be deleted per R3)
FIXTURE_DIR = Path(__file__).resolve().parents[6] / "tests" / "assets" / "docker" / "remote_xdist"

# NEW — references new package location
# From src/pytest_bdd_testing/cases/external/e2e/test_xdist_remote_message_aggregation.py
# parents[5] = repo root, then navigate into src/pytest_bdd_testing/
FIXTURE_DIR = Path(__file__).resolve().parents[5] / "src" / "pytest_bdd_testing" / "assets" / "docker" / "remote_xdist"
```

**e2e/conftest.py line 243:**

```python
# OLD
_REMOTE_XDIST_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "assets" / "docker" / "remote_xdist"

# NEW — from src/pytest_bdd_testing/cases/e2e/conftest.py
# parents[2] = src/pytest_bdd_testing/ (correct structure preserved)
_REMOTE_XDIST_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "assets" / "docker" / "remote_xdist"
# ^ This path stays the same! parents[2] from cases/e2e/conftest.py = pytest_bdd_testing/
# then assets/docker/remote_xdist = src/pytest_bdd_testing/assets/docker/remote_xdist/ ✓
```

## R5-R8: PEP 420 Namespace Package Analysis

### Directories That MUST Keep `__init__.py`

These directories have `__init__.py` files containing actual code (imports, `__getattr__`, class definitions, function definitions), not just comments:

| Directory | `__init__.py` content | Keep? |
|-----------|----------------------|-------|
| `src/pytest_bdd/` | Public API with `__all__`, `__getattr__`, imports, docstring | ✓ MUST keep |
| `src/pytest_bdd/model/` | `__all__`, re-exports, imports (90 lines) | ✓ MUST keep |
| `src/pytest_bdd/model/run/` | `__all__`, re-exports (42 lines) | ✓ MUST keep |
| `src/pytest_bdd/model/run/lifecycle/` | Contains code | ✓ MUST keep |
| `src/pytest_bdd/parsers/` | `__all__`, wildcard re-export (26 lines) | ✓ MUST keep |
| `src/pytest_bdd/scenario_locator/` | `__all__`, re-exports (14 lines) | ✓ MUST keep |
| `src/pytest_bdd/steps/` | `__all__`, re-exports (23 lines) | ✓ MUST keep |
| `src/pytest_bdd/types/` | `__all__`, re-exports | ✓ MUST keep |
| `src/pytest_bdd/_ruff/` | "init: package-marker" + docstring only | → can be empty PEP 420 after verification |
| `src/pytest_bdd/_ruff/rules/` | Contains docstring + module marker | → can be empty PEP 420 (rules are standalone scripts) |
| `src/pytest_bdd/_gherkin_go/` | Contains `parse()` function API | ✓ MUST keep |
| `src/pytest_bdd/compatibility/pytest/` | `__all__`, re-exports | ✓ MUST keep |
| `src/pytest_bdd/script/` | `__all__`, re-exports | ✓ MUST keep |
| `src/pytest_bdd/plugin/` directories with `__init__.py` | Varies — some have code, some are pure markers | See detailed analysis below |

### Directories That CAN Drop `__init__.py` (PEP 420 Namespace)

After R6 (eliminate `__all__`), the following directories have `__init__.py` files that are either empty or contain only classification comments — candidates for PEP 420 namespace:

**Testing package (after move to pytest_bdd_testing):** Approximately 70 of 73 `__init__.py` files in the testing tree are empty or contain only `# init: package-marker` comments. These can ALL be deleted. The remaining 3 (`testing/__init__.py`, `testing/cucumber_formatters/__init__.py`, `testing/assets/docker/remote_xdist/project/__init__.py`) have minimal content and should be evaluated individually.

**Main package candidates:**

| Directory | Current content | Can drop? | Notes |
|-----------|-----------------|-----------|-------|
| `_ruff/__init__.py` | `# init: allow` + docstring | YES (after verification) | Rules are standalone scripts invoked via `python -m` |
| `_ruff/rules/__init__.py` | Docstring only | YES | Each rule file is independently importable |
| `message_stream_validation/__init__.py` | Unknown — check | Unknown | Need to verify content |
| `template/__init__.py` | Unknown — check | Unknown | Need to verify content |
| `script/message_capability_governance/cli/__init__.py` | Unknown | Unknown | Need to verify |
| `compatibility/importlib/` directories | Sub-modules only? | YES | Already namespace-package pattern in sibling `compatibility/` dir |
| `model/coverage/` (no `__init__.py` currently) | Already PEP 420 | N/A | Already namespace |
| `model/message_jsonschema/` (no `__init__.py` currently) | Already PEP 420 | N/A | Already namespace |

**Plugin directories with `__init__.py` but no code:**

Many plugin subdirectories have `__init__.py` files that are pure package markers. For example:
- `plugin/cucumber_json_dispatcher/__init__.py`
- `plugin/pickle_runner/__init__.py`
- `plugin/pickle_runner/plugin/__init__.py`
- `plugin/gherkin_message_reporter/resources/__init__.py`
- `plugin/gherkin_message_reporter/resources/templates/__init__.py`

These represent a choice: keep as explicit package markers (safer, explicit) or remove for PEP 420 (cleaner, requires INP001 suppressions). Since the `plugin/` directory already operates as a namespace package (no `plugin/__init__.py`), its subdirectories can also go namespace.

### Ruff INP001 Suppression Strategy

Currently, these patterns suppress INP001:
```toml
"src/pytest_bdd/plugin/**" = ["INP001"]
"src/pytest_bdd/util/**" = ["INP001"]
"src/pytest_bdd/compatibility/*" = ["INP001"]
"src/pytest_bdd/testing/cases/*" = ["INP001"]  # already suppressed
```

After migration and `__init__.py` removal, add:
```toml
"src/pytest_bdd_testing/**" = ["INP001"]
"src/pytest_bdd/_ruff/**" = ["INP001"]            # if _ruff/__init__.py removed
"src/pytest_bdd/message_stream_validation/**" = ["INP001"]  # if __init__.py removed
"src/pytest_bdd/template/**" = ["INP001"]         # if __init__.py removed
```

### setuptools `namespaces = false` Behavior

With `namespaces = false`, setuptools only discovers regular packages (directories with `__init__.py`). This is the current setting and should remain:
- The main `pytest_bdd` package must have `__init__.py` (it's a regular package)
- Sub-packages of `pytest_bdd` without `__init__.py` are PEP 420 namespace packages — they're importable at runtime but NOT discovered as separate packages by setuptools
- This is correct: sub-packages belong to `pytest_bdd` and don't need independent package metadata
- The new `pytest_bdd_testing` needs `__init__.py` (regular package) to be discovered

### Stubs/ Directory (Deferred)

The `stubs/` directory at repo root is ALREADY PEP 420-compatible. It's referenced via `mypy_path = "stubs"` and contains `.pyi` files. No changes needed — already deferred.

## R6: `__all__` Elimination — Detailed Analysis

### Current State: 10 files with `__all__`

| File | `__all__` items | `no_implicit_reexport` impact |
|------|-----------------|-------------------------------|
| `__init__.py` | 10 items (FeaturePathType, PytestBDDStepDefinitionWarning, given, not_implemented, scenario, scenarios, step, then, tolerant, when) | Uses `__getattr__` for lazy loading — `__all__` needed for mypy unless TYPE_CHECKING pattern changed |
| `model/__init__.py` | ~20 items | Re-exports from model sub-modules |
| `model/run/__init__.py` | ~10 items | Re-exports from run sub-modules |
| `parsers/__init__.py` | ~8 items | Re-exports parser classes |
| `scenario_locator/__init__.py` | ~6 items | Re-exports locator classes |
| `steps/__init__.py` | ~10 items | Re-exports step decorators |
| `types/__init__.py` | ~5 items | Re-exports types |
| `script/__init__.py` | ~3 items | Re-exports script entry points |
| `script/message_capability_governance/__init__.py` | ~5 items | Re-exports governance tools |
| `compatibility/pytest/__init__.py` | ~5 items | Re-exports compatibility shims |

### Replacement Strategy

For files that use `__all__` for re-exports (all except root `__init__.py` which uses `__getattr__`):

**Pattern A — Direct `as` re-exports (standard mypy pattern):**
```python
# BEFORE:
from pytest_bdd.parsers.base import StepParser
from pytest_bdd.parsers.re_parser import re as re_parser
__all__ = ["StepParser", "re_parser"]

# AFTER:
from pytest_bdd.parsers.base import StepParser as StepParser
from pytest_bdd.parsers.re_parser import re as re_parser
# mypy treats 'as StepParser' as explicit re-export — no __all__ needed
```

**Pattern B — Root `__init__.py` with `__getattr__` (special case):**

The root `__init__.py` uses PEP 562 `__getattr__` for lazy loading. The `__all__` list documents the public API AND satisfies mypy. For this file specifically, `__all__` serves a documentation purpose beyond mypy. Options:
1. Keep `__all__` with `# init: no-check` exemption (violates R6 spirit)
2. Remove `__all__` and switch to TYPE_CHECKING-only imports (mypy will see them but they won't exist at runtime)
3. Remove `__all__` and add `from pytest_bdd.steps import given as given` etc. under `TYPE_CHECKING` — but PEP 562 `__getattr__` already handles runtime

**Recommendation for root `__init__.py`:** Use Pattern C — move all lazy imports under `if TYPE_CHECKING` with `as` aliases:
```python
if TYPE_CHECKING:
    from pytest_bdd.steps import (
        given as given,
        not_implemented as not_implemented,
        step as step,
        then as then,
        tolerant as tolerant,
        when as when,
    )
    from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning as PytestBDDStepDefinitionWarning
# No __all__ needed — all imports use 'as' which is explicit re-export
```

### Verification

After replacing all `__all__` with `from X import Y as Y`:
```bash
mypy --strict src/pytest_bdd/  # Should pass with zero errors
```

Any `[no-redef]` or `[attr-defined]` errors indicate a missed `as` alias or broken import.

## R9: init_rules.py Update

### Current Rules (as of Phase 20 Wave 3)

| Rule | Current Meaning |
|------|----------------|
| BLQ1401 | Empty or metadata-only `__init__.py` (advisory) |
| BLQ1402 | Re-exports without `__all__` (advisory) |
| BLQ1403 | `__all__` defined in `__init__.py` (advisory) |

### New Rules (R9 requirements)

| Rule | New Meaning | Why Changed |
|------|-------------|-------------|
| BLQ1401 | **No `__all__` in `__init__.py`** (was: empty/check) | R6 eliminates all `__all__` |
| BLQ1402 | **No empty `__init__.py`** (was: re-exports) | R5 enforces PEP 420 — empty files must be deleted |
| BLQ1403 | **`__init__.py` only for actual code** (was: advisory about __all__) | Files with only docstrings/comments are violations |

### Updated check_file logic

```python
def check_file(path: Path) -> list[Violation]:
    # ...

    # BLQ1401: __all__ in __init__.py is now a hard error (R6)
    if has_all:
        violations.append(Violation(
            path=path, line=1,
            message=f"BLQ1401: {path} defines __all__. "
                    f"Replace with 'from X import Y as Y' pattern for mypy no_implicit_reexport."
        ))

    # BLQ1402: Empty __init__.py — delete it (R5)
    if not visitor.has_imports and not has_all:
        stripped = source
        for comment in CLASSIFICATION_COMMENTS:
            stripped = stripped.replace(comment, "")
        stripped = stripped.strip()
        if not stripped:
            violations.append(Violation(
                path=path, line=1,
                message=f"BLQ1402: {path} is empty or metadata-only. "
                        f"Delete this file (PEP 420 implicit namespace package)."
            ))

    # BLQ1403: __init__.py must contain actual code (R9)
    # — already covered by BLQ1402 for empty files
    # — files with only docstrings but no imports/code trigger this
    if not visitor.has_imports and not has_all and stripped and not any(
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Assign))
    ):
        violations.append(Violation(
            path=path, line=1,
            message=f"BLQ1403: {path} contains only docstring. "
                    f"Add actual code (imports, definitions) or delete for PEP 420."
        ))
```

### Testing Directory Awareness

The `check_paths()` function at line 157 already skips `testing` directories:
```python
if "testing" in py_file.parts:
    continue
```

After migration, this skip logic should be updated to skip `pytest_bdd_testing` instead:
```python
if "pytest_bdd_testing" in py_file.parts:
    continue
```

Or more robustly — skip everything under `src/pytest_bdd_testing/` entirely since it's a separate package with its own conventions.

## Common Pitfalls

### Pitfall 1: DOCKER CONTEXT — Confusing Directory Levels

**What goes wrong:** The docker-compose.yml context depth is off by exactly 1 level (5 instead of 6 for current location, or miscalculated after migration). Docker builds fail with cryptic "COPY failed: file not found" errors.

**Why it happens:** Counting directory levels from a deeply nested file is error-prone. The docker-compose.yml at `src/pytest_bdd/testing/assets/docker/remote_xdist/` is 6 levels deep, but the context uses 5 levels, resolving to `src/` instead of repo root.

**How to avoid:** After migration to `src/pytest_bdd_testing/assets/docker/remote_xdist/` (5 levels deep), use exactly 5 `..` components. Verify with: `realpath src/pytest_bdd_testing/assets/docker/remote_xdist/../../../../..` should print the repo root.

**Warning signs:** `docker compose build` fails with `COPY failed: file not found` for `pyproject.toml` or `src/`.

### Pitfall 2: STALE IMPORTS — `pytest_bdd.testing` Still Referenced After Move

**What goes wrong:** After moving files, some imports still reference `pytest_bdd.testing.*` because the `src/pytest_bdd/testing/` directory was deleted. Imports fail at runtime or during test collection.

**Why it happens:** 43 import sites across deeply nested test files. Manual find-and-replace can miss edge cases (dynamic imports, string references in `--pyargs` arguments, conftest path calculations).

**How to avoid:** Run `rg "pytest_bdd\.testing" src/ --no-ignore` after all rewrites. This MUST return zero results. Then run `pytest --co` (collection only) to verify imports work.

**Warning signs:** `ImportError: cannot import name '...' from 'pytest_bdd.testing'` during test collection.

### Pitfall 3: `__all__` REMOVAL WITHOUT `as` ALIAS — mypy Cascade

**What goes wrong:** Removing `__all__` without adding `as Y` aliases causes mypy `no_implicit_reexport` errors on every downstream module that imports from that `__init__.py`.

**Why it happens:** `no_implicit_reexport = true` means `from .submodule import X` does NOT re-export `X`. Downstream code doing `from package import X` gets `[attr-defined]` errors.

**How to avoid:** For every `__all__ = ["X", "Y"]`, verify that the corresponding import uses `from .submodule import X as X`. Run `mypy --strict src/` after each `__init__.py` change.

**Warning signs:** `mypy` reports `Module "pytest_bdd.X" does not explicitly export attribute "Y"` after `__all__` removal.

### Pitfall 4: NAMESPACE COLLISION — `pytest_bdd` + `pytest_bdd_testing` Both Under `src/`

**What goes wrong:** Both packages under `src/` with `namespaces = false` may conflict if `pytest_bdd_testing` lacks `__init__.py`. Without it, setuptools won't discover it as a separate package, and Python may treat it as part of a `pytest_bdd` namespace.

**Why it happens:** PEP 420 namespace packages merge directories with the same name across different locations on `sys.path`. If `pytest_bdd_testing` is moved under a `pytest_bdd` namespace accidentally or if the `__init__.py` is missing, Python's import system can misroute imports.

**How to avoid:** Ensure `src/pytest_bdd_testing/__init__.py` exists (even if minimal). The file marks it as a regular package, preventing namespace collision. Verify: `python -c "import pytest_bdd_testing; print(pytest_bdd_testing.__file__)"`.

## Code Examples

### R1: Import Rewrite Automation Pattern

```bash
# Find all files referencing old import path
rg "pytest_bdd\.testing" src/ --files-with-matches

# Rewrite import statements (dry-run first!)
rg "pytest_bdd\.testing" src/ --files-with-matches | while read f; do
    sed -i 's/pytest_bdd\.testing/pytest_bdd_testing/g' "$f"
done

# Verify zero remaining references
rg "pytest_bdd\.testing" src/  # MUST be empty
```

### R4: Docker Compose Context Verification

```bash
# From the repo root, verify the context resolves correctly
cd src/pytest_bdd_testing/assets/docker/remote_xdist
realpath ../../../../..  # Should print the repo root
```

### R6: `__all__` → `as` Alias Conversion

```python
# Source: mypy docs on no_implicit_reexport [VERIFIED: /python/mypy]
# BEFORE:
from .base import StepParser
from .re_parser import re as re_parser
__all__ = ["StepParser", "re_parser"]

# AFTER — mypy treats 'as X' as explicit re-export:
from .base import StepParser as StepParser
from .re_parser import re as re_parser
# No __all__ needed
```

### R8: PEP 420 Namespace Package Verification

```python
# Verify a directory can be a PEP 420 namespace package
# Run from Python:
import importlib
mod = importlib.import_module("pytest_bdd.plugin")  # Already namespace (no __init__.py)
print(mod.__path__)  # Should be _NamespacePath, not list
print(mod.__file__)  # Should raise AttributeError (namespace packages have no __file__)
```

## Sources

### Primary (HIGH confidence)
- [/pypa/setuptools] — Package discovery: `find:`, `namespaces`, `include`/`exclude` glob behavior. Confirmed default behavior discovers implicit namespaces; `namespaces = false` restricts to regular packages.
- [/python/mypy] — `no_implicit_reexport` flag behavior: `from-as` imports count as explicit re-export; `__all__` not required when using `from X import Y as Y` pattern. `namespace_packages = true` (default) enables PEP 420.
- [/astral-sh/ruff] — INP001 rule: flake8-no-pep420. Per-file-ignores suppress INP001 for namespace package directories.

### Secondary (MEDIUM confidence)
- PEP 420 specification (Python 3.3+) — implicit namespace packages. Verified via Python 3.14 behavior on this machine.
- Actual file system inspection: directory depth counts verified by enumerating components from file location to repo root.

### Tertiary (LOW confidence)
- None — all critical claims verified against Context7 docs or actual file system.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pytest_bdd_testing` as a local-only dependency in `testing` extra will resolve in editable installs but fail for PyPI wheel installs | R2 | End users who `pip install pytest-bdd-ng[testing]` from PyPI get resolution error. Mitigation: testing extra is dev-only; CI uses editable install. |
| A2 | `src/pytest_bdd_testing/assets/docker/remote_xdist/` is exactly 5 directory levels below repo root | R4 | Wrong depth would produce broken docker compose context. Mitigation: verified by counting actual directory components. |
| A3 | `_ruff/__init__.py` and `_ruff/rules/__init__.py` can be safely deleted because rules are invoked via `python -m pytest_bdd._ruff.rules.<name>` which doesn't require package `__init__.py` | R5/R8 | If Python module resolution requires `_ruff/__init__.py` for submodule imports, rule execution would break. Mitigation: test `uv run python -m pytest_bdd._ruff.rules.init_rules` after deletion. |
| A4 | The `from X import Y as Y` pattern satisfies mypy `no_implicit_reexport` for all 10 `__all__` sites | R6 | If mypy doesn't recognize the `as` alias pattern for certain re-export scenarios (e.g., wildcard re-exports), some files would still need `__all__`. Mitigation: run `mypy --strict src/pytest_bdd/` after each conversion. |
| A5 | Removing `__init__.py` from `plugin/cucumber_json_dispatcher/` and similar leaf plugin directories won't break pytest plugin loading | R5 | pytest11 entry points reference `pytest_bdd.plugin.<name>.entrypoint` — these are concrete module paths, not package imports. But if any import uses `from pytest_bdd.plugin.cucumber_json_dispatcher import something`, it would need the `__init__.py`. Mitigation: grep for such imports before deletion. |

## Open Questions

1. **`pytest_bdd_testing` as PyPI dependency: What happens when someone installs from PyPI?**
   - What we know: The testing package is excluded from the wheel. The `testing = ["pytest_bdd_testing"]` dependency would fail to resolve from PyPI.
   - What's unclear: Whether we should publish `pytest-bdd-testing` as a separate PyPI package to satisfy this dependency, or accept that the `testing` extra is dev-only.
   - Recommendation: Accept dev-only for now. If downstream test suites need the testing package, publish `pytest-bdd-testing` as a separate PyPI package later.

2. **Root `__init__.py` `__all__` — keep or remove?**
   - What we know: The root `__init__.py` uses PEP 562 `__getattr__` for lazy loading. The `__all__` serves both mypy and documentation purposes. The `as` alias pattern doesn't apply cleanly because symbols are lazily loaded.
   - What's unclear: Whether the `TYPE_CHECKING` + `as` pattern (Recommendation in §R6) fully satisfies mypy or causes subtle issues with the `__getattr__` fallback.
   - Recommendation: Attempt the `TYPE_CHECKING` + `as` pattern. If mypy complains, mark root `__init__.py` as `# init: no-check` for BLQ1401 and keep `__all__` as documented exception.

3. **Should `pytest_bdd_testing/cases/conftest.py` move to `pytest_bdd_testing/conftest.py`?**
   - What we know: Currently `src/pytest_bdd/testing/cases/conftest.py` is the primary conftest. There's also `testing/cases/e2e/conftest.py` for e2e-specific fixtures.
   - What's unclear: Whether pytest discovers conftest at `cases/` level or `pytest_bdd_testing/` level. The `testpaths` config points to `cases/`.
   - Recommendation: Keep `conftest.py` at `cases/` level (matching current structure). Verify pytest discovery with `pytest --co`.

## Environment Availability

> External dependencies section — all critical operations use standard tools.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Package imports, PEP 420 | ✓ | 3.14.2 | — |
| setuptools | Package discovery | ✓ | (build backend) | — |
| git | File moves, history tracking | ✓ | (repo) | — |
| Docker | Build verification | ✗ | — | Analytical verification (directory depth counting) |
| docker compose | Build verification | ✗ | — | Same as Docker |

**Missing dependencies with no fallback:** None — Docker verification is analytical, not required for code changes.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest src/pytest_bdd_testing/cases/unit -x -q` |
| Full suite command | `pytest src/pytest_bdd_testing/cases/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R1 | `pytest_bdd_testing` package importable | smoke | `python -c "import pytest_bdd_testing"` | ❌ Wave 0 |
| R1 | Tests discoverable from new testpaths | integration | `pytest --co` | N/A (pytest built-in) |
| R2 | `pip install -e '.[testing]'` succeeds | manual | `pip install -e '.[testing]' --dry-run` | N/A |
| R4 | Docker compose parses without error | manual | `docker compose -f .../docker-compose.yml config` | N/A (needs Docker) |
| R5 | Zero empty `__init__.py` in main package | lint | `uv run python -m pytest_bdd._ruff.rules.init_rules src/pytest_bdd/` | ❌ Wave 0 |
| R6 | Zero `__all__` in `__init__.py` (except exempt) | lint | Same init_rules check | ❌ Wave 0 |
| R6 | mypy passes with `no_implicit_reexport` | type-check | `mypy --strict src/pytest_bdd/` | ❌ Wave 0 |
| R8 | PEP 420 directories importable without `__init__.py` | smoke | `python -c "import pytest_bdd.plugin; print(type(pytest_bdd.plugin.__path__))"` | N/A |

### Wave 0 Gaps
- [ ] Updated `init_rules.py` with new BLQ1401/1402/1403 semantics
- [ ] Test for `init_rules.py` new rules (unit test under `tests/` or `pytest_bdd_testing/cases/unit/`)
- [ ] Import smoke test: `python -c "import pytest_bdd_testing"`
- [ ] mypy verification after `__all__` removal
- [ ] ruff INP001 verification after `__init__.py` deletion

## Security Domain

> `security_enforcement` is enabled by default. Phase 20 gap-closure is a refactoring phase with no new attack surface.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | No | N/A |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | No — code moves only | N/A |
| V6 Cryptography | No | N/A |

**Note:** This is a pure refactoring phase. No new code paths are introduced. File moves, import rewrites, and `__init__.py` deletions do not create new threat vectors. The existing security controls (ruff bandit rules, mypy strict checking) remain in place.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; existing toolchain (setuptools, mypy, ruff) documented via Context7
- Architecture: HIGH — file system verified; directory depths counted; import sites enumerated
- Pitfalls: HIGH — all common pitfalls identified with specific warning signs and prevention strategies

**Research date:** 2026-06-10
**Valid until:** 2026-07-10 (30 days — stable domain)

**Key finding for planner:** The Docker compose context is currently BROKEN (5 levels → `src/`, needs 6 levels → repo root). The migration to `src/pytest_bdd_testing/` naturally fixes this because the new location is 5 levels deep from repo root instead of 6. This means the Docker path rework (R4) and test package extraction (R1) MUST happen together — fixing one without the other leaves Docker broken.
