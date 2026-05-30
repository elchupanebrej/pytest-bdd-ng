# Phase 09: Compatibility Streamlining - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove dead Python 2 shims and legacy dependencies; consolidate remaining compatibility layer.

**Requirement:** SIM-01 — "Streamline compatibility layer — remove dead shims, consolidate"

**Scope:**
1. Replace `pathlib2` and `docopt-ng` in `script/bdd_tree_to_rst.py` with stdlib equivalents, then remove both dependencies from pyproject.toml (including type stubs)
2. Delete unused `compatibility/git.py` (zero consumers)
3. Delete `compatibility/jsonschema.py` — replace Protocol wrapper with direct `jsonschema` imports in the 2 consumers
4. Split `compatibility/matrix.py` — move `is_pair_compatible()` and `PYTEST_COMPATIBILITY_BOUNDS` to a new runtime module; move tox/CI helpers (`build_matrix`, `expand_tox_env_names`, `extract_factors_from_tox_ini`, `discover_*`, `build_migration_coverage_summary`) to `util/`
5. Keep version-conditional shims as-is (typing.py, enum.py, tomllib.py, pathlib.py, importlib/resources.py)
6. Keep `compatibility/pytest/__init__.py` private imports as-is

**Exclusions:**
- Pattern unification across plugins → Phase 10
- Dead code audit and pruning → Phase 11
- `parsers.py` modifications — FROZEN (tests only)
- Python version support matrix changes — keep 3.10-3.14

</domain>

<decisions>
## Dependency Removal

- **D-01:** Replace `pathlib2.Path` → `pathlib.Path` in `script/bdd_tree_to_rst.py` — stdlib since Python 3.4
- **D-02:** Replace `docopt` → `argparse` in `script/bdd_tree_to_rst.py` — stdlib, equivalent CLI parsing
- **D-03:** Remove `pathlib2`, `docopt-ng`, `types-pathlib2`, `types-docopt` from pyproject.toml
- **D-04:** Keep `importlib-resources`, `tomli`, `strenum` — still needed for Python 3.10 compatibility

## Version Shim Strategy

- **D-05:** Keep all 5 version-conditional shims as-is (typing.py, enum.py, tomllib.py, pathlib.py, importlib/resources.py) — centralized, easy to audit when dropping Python versions

## Protocol Wrapper Simplification

- **D-06:** Delete `compatibility/jsonschema.py` — replace with direct `jsonschema` imports in `model/message_schema_validation.py` and `script/message_capability_governance.py`
- **D-07:** Delete `compatibility/git.py` — zero consumers, dead code
- **D-08:** Keep `compatibility/parser.py` — defines real `ParserProtocol` contract used across codebase

## pytest Private Imports

- **D-09:** Keep `compatibility/pytest/__init__.py` _pytest imports as-is — standard pattern for pytest plugins, no public alternatives available

## matrix.py Split

- **D-10:** Split `compatibility/matrix.py` — runtime compatibility rules (`is_pair_compatible`, `PYTEST_COMPATIBILITY_BOUNDS`, constants, `CompatibilityMatrixEntry`) move to new `compatibility/runtime_compat.py`; CI/tox helpers (`build_matrix`, `expand_tox_env_names`, `extract_factors_from_tox_ini`, `discover_*`, `build_migration_coverage_summary`) move to `util/matrix.py`
- **D-11:** Update all 9 test imports to use new module paths
- **D-12:** Update `script/compatibility_matrix.py` and `runner.py` imports

## the agent's Discretion
- Exact file naming for split matrix modules (within runtime_compat.py / util/matrix.py pattern)
- Whether to add deprecation warnings before removing dependencies
- Refactoring depth for jsonschema consumers — minimal import swap vs full cleanup

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/ROADMAP.md` — Phase 9 goal: "Remove dead Python 2 shims and legacy dependencies; consolidate remaining compatibility layer"
- `.planning/REQUIREMENTS.md` — SIM-01: "Streamline compatibility layer — remove dead shims, consolidate"
- `.planning/PROJECT.md` — Core value, constraints (Python 3.10-3.14, pytest >=7.0.0)
- `.planning/phases/08-bdd-acceptance-testing/08-CONTEXT.md` — Prior phase decisions, compatibility layer references

### Source Code — Dependencies to Remove
- `src/pytest_bdd/script/bdd_tree_to_rst.py` — Uses `pathlib2.Path` (line 28) and `docopt` (line 26)
- `pyproject.toml` — Lines 61, 65, 116, 119, 135, 165, 168 (dependency declarations)

### Source Code — Compatibility Layer (12 modules)
- `src/pytest_bdd/compatibility/__init__.py` — Package init (1 line)
- `src/pytest_bdd/compatibility/typing.py` — `Self` backport (14 lines)
- `src/pytest_bdd/compatibility/enum.py` — `StrEnum` backport (10 lines)
- `src/pytest_bdd/compatibility/tomllib.py` — `tomllib` backport (10 lines)
- `src/pytest_bdd/compatibility/pathlib.py` — `GlobError` type alias (5 lines)
- `src/pytest_bdd/compatibility/path.py` — `relpath`, `resolvepath` helpers (45 lines)
- `src/pytest_bdd/compatibility/parser.py` — `ParsedFeature`, `ParserProtocol` (39 lines)
- `src/pytest_bdd/compatibility/struct_bdd.py` — `STRUCT_BDD_INSTALLED` check (5 lines)
- `src/pytest_bdd/compatibility/jsonschema.py` — Protocol wrapper (42 lines) — DELETE
- `src/pytest_bdd/compatibility/git.py` — Protocol wrapper (62 lines) — DELETE (zero consumers)
- `src/pytest_bdd/compatibility/matrix.py` — Compatibility matrix (352 lines) — SPLIT
- `src/pytest_bdd/compatibility/pytest/__init__.py` — pytest version shims (172 lines)
- `src/pytest_bdd/compatibility/importlib/__init__.py` — Package init (1 line)
- `src/pytest_bdd/compatibility/importlib/resources.py` — `importlib_resources` backport (8 lines)
- `src/pytest_bdd/compatibility/importlib/metadata.py` — stdlib re-exports (31 lines)

### Source Code — matrix.py Consumers
- `src/pytest_bdd/runner.py` — `is_pair_compatible()` (runtime)
- `src/pytest_bdd/script/compatibility_matrix.py` — matrix generation (build)
- `src/pytest_bdd/model/message_schema_validation.py` — jsonschema imports (2 consumers)
- `src/pytest_bdd/script/message_capability_governance.py` — jsonschema imports (2 consumers)
- `tests/compatibility/` — 9 test files importing matrix.py functions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `compatibility/pytest/__init__.py` — Centralized pytest version detection (`PYTEST8`, `PYTEST81`, `PYTEST83`), used across codebase
- `compatibility/path.py` — `relpath()` handles Windows cross-drive edge cases, used by scenario_locator

### Established Patterns
- Version-conditional imports use `if sys.version_info >= (3, X): stdlib else: backport` pattern
- Protocol wrappers define interface contracts while deferring to third-party implementations
- `compatibility/` modules are thin — most are < 50 lines, only matrix.py is substantial (352 lines)

### Integration Points
- `runner.py` calls `is_pair_compatible()` for runtime version checks — must remain importable from compatibility/
- `script/compatibility_matrix.py` generates CI matrix reports — can move to util/
- 9 test files in `tests/compatibility/` test matrix.py functions — imports must be updated after split

</code_context>

<specifics>
## Specific Ideas

- `pathlib2.Path` in bdd_tree_to_rst.py is used for file operations — direct replacement with `pathlib.Path` should be zero-diff
- `docopt` docstring format in bdd_tree_to_rst.py maps cleanly to `argparse` with `description` and `add_argument`
- `jsonschema.py` `build_validator()` is a thin wrapper around `jsonschema.validators.validator_for()` — consumers can call directly
- `git.py` is completely unused — safe to delete without migration
- `matrix.py` split boundary: `is_pair_compatible()` + `PYTEST_COMPATIBILITY_BOUNDS` + constants + `CompatibilityMatrixEntry` stay runtime; tox env generation and discovery functions move to util

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-Compatibility Streamlining*
*Context gathered: 2026-05-16*
