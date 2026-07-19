# Phase 11: Audit & Prune - Research

**Researched:** 2026-05-16
**Domain:** Python dead code detection, module splitting, CI matrix validation
**Confidence:** HIGH

## Summary

This phase targets zero dead code, unused imports, stale modules, and full CI matrix validation. Key finding: **ruff F401/F811/ERA001 already passes clean** — the primary lint gate is already satisfied. The real work is in vulture-detected dead code (270 findings at 60% confidence, 12 at 80%), large file splitting (3 files >750L), and CI matrix validation (~30 tox environments across Python 3.10-3.14 × pytest 7.0-9.x).

Three modules are confirmed dead: `feature_locator.py` (292L, zero imports), `runner.py:validate_requested_pair` (single unused function), `util/temp_root.py` (zero imports). Many vulture 60% findings are false positives — pytest hooks called dynamically, test-used methods, and re-export modules.

**Primary recommendation:** Remove confirmed dead modules first, split large files per CONTEXT.md decisions, validate CI matrix, document plugin justifications.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Keep decopatch as-is — functional, stable, low risk. Not worth rewrite during stabilization phase. Document health status in audit report.
- **D-02:** Split `steps.py` (803L) — separate StepDefinitionManager.Registry, StepDefinitionManager.Matcher, StepDefinitionManager.Definition into sub-modules
- **D-03:** Split `message_capability_governance.py` (751L) — separate governance logic into logical sub-modules
- **D-04:** Split `run.py` (630L) — further modularize runtime execution code (already split from scenario_run.py 1422L in earlier phase)
- **D-05:** Keep all 17 active plugins — audit each, document usage justification. Remove only truly dead/zero-consumer plugins. No removals based on assumed low usage.
- **D-06:** All 17 plugins confirmed active with entry points in pyproject.toml — none are dead code
- **D-07:** Full matrix validation required — all Python 3.10-3.14 × pytest 7.x-latest combinations (~20+ tox environments)
- **D-08:** CI matrix validation is a gate — phase fails if any combination in the matrix fails

### the agent's Discretion
- Exact sub-module naming and boundaries for large file splits
- Which specific plugins need usage documentation (all 17, but depth varies by complexity)
- Specific tox environment configuration for full matrix run

### Deferred Ideas (OUT OF SCOPE)
- decopatch replacement evaluation — future phase (keep as-is for now)
- parsers.py refactoring — FROZEN (tests only)

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Dead code detection | API / Tooling | — | Static analysis tools (ruff, vulture) operate on source |
| Unused import removal | API / Tooling | — | ruff F401 auto-fixable, vulture needs manual review |
| Commented-out code removal | API / Source | — | ERA001 rule enforcement |
| Large file splitting | API / Core Library | — | Internal module organization, backward compat via re-exports |
| Plugin audit | API / Plugin Layer | — | Entry point validation, consumer analysis |
| CI matrix validation | CI / Tooling | — | tox configuration, cross-platform execution |
| Decopatch health documentation | API / Dependency | — | Dependency audit, not replacement |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruff | 0.15.10 | Linting (F401/F811/ERA001) | Project standard, already configured, auto-fixable |
| vulture | 2.14+ (latest) | Dead code detection | Complements ruff — finds unused functions/classes ruff misses |
| tox | 4.2+ | CI matrix execution | Project standard, 30+ environments configured |
| tox-uv | latest | tox + uv integration | Already in tox.ini `requires` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| decopatch | 1.4.10 | Step decorator infrastructure | Keep as-is (D-01), document health |
| attrs | latest | Data classes | Project standard, all data classes use @define/@frozen |

**Installation:**
```bash
uv pip install vulture  # if not already in deps
```

**Version verification:**
```
ruff 0.15.10 — verified via `uv run python -m ruff --version`
vulture — installed via `uv pip install vulture`, no version pin in pyproject.toml
decopatch 1.4.10 — verified via `uv run python -c "import decopatch; print(decopatch.__version__)"`
tox 4.2+ — verified in tox.ini `requires`
```

## Architecture Patterns

### System Architecture Diagram

```
Source Code (211 files, 27972 lines)
  │
  ├── Dead Code Detection
  │   ├── ruff F401/F811/ERA001 → Already clean ✓
  │   └── vulture (60-100% confidence) → 270 findings, ~12 actionable at 80%+
  │
  ├── Large File Splitting
  │   ├── steps.py (971L) → Registry / Matcher / Definition sub-modules
  │   ├── script/message_capability_governance.py (853L) → governance sub-modules
  │   └── model/run.py (783L) → execution lifecycle sub-modules
  │
  ├── Plugin Audit (17 active)
  │   ├── Entry point validation → pyproject.toml [project.entry-points.pytest11]
  │   ├── Consumer analysis → grep + vulture cross-reference
  │   └── Usage justification → document per-plugin
  │
  ├── CI Matrix Validation
  │   ├── Python 3.10-3.14 × pytest 7.0-9.x → ~30 tox environments
  │   ├── Platforms: linux, mac, win (coverage envs)
  │   └── Gate: all matrix envs must pass
  │
  └── Metrics
      ├── Before: 211 files, 27972 lines
      └── After: reduced file count, reduced line count
```

### Recommended Project Structure (for large file splits)

```
src/pytest_bdd/
├── steps/                    # Split from steps.py (971L)
│   ├── __init__.py           # Re-export given/when/then/step
│   ├── registry.py           # Registry class, fixture injection
│   ├── matcher.py            # Matcher class, three-pass matching
│   ├── definition.py         # Definition class, wrapped function
│   └── decorators.py         # given/when/then/step decorator builders
├── script/
│   ├── message_capability_governance/  # Split from 853L file
│   │   ├── __init__.py
│   │   ├── schema.py         # Schema loading, validation
│   │   ├── capabilities.py   # Capability detection, inventory
│   │   ├── decisions.py      # Decision loading, validation
│   │   └── cli.py            # parse_args, main
│   └── ...
└── model/
    ├── run/                  # Split from run.py (783L)
    │   ├── __init__.py       # Re-export Run, RunStage, etc.
    │   ├── stages.py         # RunStage, RunStatus, HookPhase enums
    │   ├── lifecycle.py      # Run class, lifecycle methods
    │   └── refs.py           # LifecycleObjectRef, _*_ref helpers
```

### Pattern 1: Re-export for backward compatibility
**What:** Split large modules but maintain existing public API via `__init__.py` re-exports
**When to use:** Any module split where external consumers import from the original module path
**Example:**
```python
# src/pytest_bdd/steps/__init__.py
from __future__ import annotations
from pytest_bdd.steps.registry import Registry
from pytest_bdd.steps.matcher import Matcher
from pytest_bdd.steps.definition import Definition
from pytest_bdd.steps.decorators import given, when, then, step

__all__ = ["Registry", "Matcher", "Definition", "given", "when", "then", "step"]
```

### Pattern 2: Plugin consumer analysis
**What:** Verify each plugin has active consumers by checking entry points + test usage
**When to use:** Audit phase for plugin justification
**Example:**
```bash
# Check entry point exists
Select-String -Path pyproject.toml -Pattern "pytest11" -Context 0,20
# Check test coverage
Select-String -Path "tests/**/*.py" -Pattern "plugin_name" -List
```

### Anti-Patterns to Avoid
- **Blind vulture removal:** Many 60% confidence findings are false positives (pytest hooks called dynamically, test-used methods). Only remove at 80%+ confidence with manual verification.
- **Breaking public API:** Large file splits MUST maintain backward-compatible imports. External code imports `from pytest_bdd.steps import given` — this must still work.
- **Removing script modules without checking tests:** `script/` modules are used by tests even if not registered as CLI entry points.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dead code detection | Custom AST walker | vulture + ruff | vulture handles 270+ patterns, ruff handles F401/F811/ERA001 |
| Commented-out code detection | Regex scan | ruff ERA001 (eradicate) | Handles false positives, well-tested |
| CI matrix expansion | Manual env listing | tox `--listenvs` + `expand_tox_env_names()` | tox.ini already configured, helper exists |
| Plugin structure validation | Manual file checks | `pytest_bdd._ruff.rules.plugin_patterns` | Already implemented (BLQ1001-1003) |

**Key insight:** The project already has custom ruff rules (`_ruff/rules/`) for plugin pattern validation and quality gates. Leverage these rather than building new validation scripts.

## Runtime State Inventory

> Not a rename/refactor/migration phase — no runtime state to migrate.

## Common Pitfalls

### Pitfall 1: Vulture False Positives on Pytest Hooks
**What goes wrong:** Removing pytest hook methods that vulture flags as "unused" because they are called dynamically by pytest's plugin system
**Why it happens:** Vulture uses static analysis — it cannot detect dynamic method invocation via pytest's hook calling mechanism
**How to avoid:** Never remove methods named `pytest_*` based on vulture alone. Verify by checking if the plugin's entry point is registered in pyproject.toml and if tests exercise the plugin.
**Warning signs:** vulture flags `pytest_configure`, `pytest_runtest_call`, etc. as unused — these are always false positives for registered plugins.

### Pitfall 2: Breaking Re-export Chains
**What goes wrong:** Splitting a module and forgetting to update `__init__.py` re-exports, causing import errors for consumers
**Why it happens:** The split creates new internal module paths but the public API path (`from pytest_bdd.steps import given`) still needs to resolve
**How to avoid:** Before splitting, catalog all external imports of the module. After splitting, verify each import path still resolves.
**Warning signs:** `ImportError` or `ModuleNotFoundError` after split; ruff F401 errors in new `__init__.py` files.

### Pitfall 3: tox Environment Explosion
**What goes wrong:** Running full CI matrix on local machine takes hours and may fail due to missing Python versions
**Why it happens:** tox.ini defines ~30 environments across 5 Python versions × 12 pytest versions × 3 platforms
**How to avoid:** Run matrix validation in CI, not locally. Locally, run `py{310,314}-ruff` and one coverage env as smoke test.
**Warning signs:** `InterpreterNotFound` for Python versions not installed locally.

### Pitfall 4: Over-pruning Script Modules
**What goes wrong:** Removing `script/` modules that are used by tests but not registered as CLI entry points
**Why it happens:** `sync_messages_contract_schemas.py` and `validate_feature_headings.py` are not in `[project.scripts]` but ARE imported by tests
**How to avoid:** Check both source imports AND test imports before removing any module
**Warning signs:** Test failures after module removal; `ModuleNotFoundError` in test files

### Pitfall 5: ruff ERA001 False Positives on Documentation
**What goes wrong:** ERA001 flags legitimate comments that look like code (e.g., `# skip reporting for non-bdd tests`)
**Why it happens:** eradicate uses heuristic detection — any comment containing Python keywords may be flagged
**How to avoid:** Review each ERA001 finding manually. Use `# noqa: ERA001` for legitimate comments that look like code.
**Warning signs:** ERA001 flags comments that describe behavior rather than commented-out code

## Code Examples

### ruff dead code check (already clean)
```bash
# Source: verified via `uv run python -m ruff check src/pytest_bdd/ --select F401,F811,ERA001`
# Result: "All checks passed!"
uv run python -m ruff check src/pytest_bdd/ --select F401,F811,ERA001
```

### vulture dead code scan
```bash
# High-confidence findings only (80%+)
uv run python -m vulture src/pytest_bdd/ --min-confidence 80

# All findings (requires manual triage)
uv run python -m vulture src/pytest_bdd/ --min-confidence 60
```

### tox matrix validation
```bash
# List all environments
uv run tox --listenvs

# Run full matrix (CI only)
uv run tox

# Run ruff gate only (local smoke)
uv run tox -e py314-ruff,py310-ruff

# Run single Python version across all pytest versions
uv run tox -e py314-pytest{70,71,72,73,74,80,81,82,83,84,90,latest}-coverage-lin
```

### Plugin consumer analysis
```bash
# Check if a plugin module is imported anywhere
Select-String -Path "src/pytest_bdd/**/*.py","tests/**/*.py" -Pattern "from.*module_name|import.*module_name"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pylint for dead code | ruff + vulture | Project uses ruff exclusively | Faster, simpler config |
| Manual module splitting | Re-export pattern via `__init__.py` | Established in prior phases | Backward compat maintained |
| CI matrix manual testing | tox + tox-uv automation | tox.ini configured | 30+ envs automated |

**Deprecated/outdated:**
- `return None` in non-hook code: Replaced with `returns.maybe.Nothing` (Phase 2, STAB-02)
- Bare `except Exception:`: Replaced with specific exceptions + logging (Phase 2, STAB-03)
- Empty plugin directories (`cucumber_formatter_support`, `scenario_runner`): Removed in Phase 10

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | vulture 60% confidence findings are mostly false positives for pytest hooks | Common Pitfalls, Vulture analysis | May cause over-pruning if planner treats all findings equally |
| A2 | `feature_locator.py` (292L) is entirely dead code (zero imports in src or tests) | Dead code findings | If wrong, removal breaks unknown consumers |
| A3 | `util/temp_root.py` is dead code (zero imports) | Dead code findings | Same as A2 |
| A4 | tox matrix gate means ALL ~30 environments must pass, not just a subset | CI Matrix Validation | Phase may be blocked by flaky envs, not code issues |

## Open Questions

1. **Should `feature_locator.py` be removed or kept for future use?** (RESOLVED)
   - Decision: Remove — zero imports, 292 lines, no consumers. Plan 01 covers removal.

2. **Should `util/toolz_test.py` be moved to `tests/`?** (RESOLVED)
   - Decision: Keep in `src/` — testdir-based tests need it importable from installed package.

3. **CI matrix: which environments are expected to fail on Windows?** (RESOLVED)
   - Decision: Plan 05 validates CI matrix config; executor runs `tox --listenvs` to determine Windows-specific subset.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10 | CI matrix | ✗ (local) | — | CI only |
| Python 3.11 | CI matrix | ✗ (local) | — | CI only |
| Python 3.12 | CI matrix | ✗ (local) | — | CI only |
| Python 3.13 | CI matrix | ✗ (local) | — | CI only |
| Python 3.14 | CI matrix, ruff, pre-commit | ✓ | 3.14 | — |
| ruff | Lint gate | ✓ | 0.15.10 | — |
| vulture | Dead code detection | ✓ (installed this session) | latest | Manual review |
| tox | CI matrix | ✓ (via uv) | 4.2+ | — |
| tox-uv | tox + uv integration | ✓ | latest | — |

**Missing dependencies with no fallback:**
- Python 3.10-3.13 locally — CI matrix validation must run in CI, not locally

**Missing dependencies with fallback:**
- None — all tooling available locally for ruff/vulture checks

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x (latest), pytest 7.0-8.4 (matrix) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run python -m pytest tests/ -q -x` |
| Full suite command | `uv run tox` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIM-03 | No dead imports (F401/F811 clean) | lint | `uv run python -m ruff check src/pytest_bdd/ --select F401,F811` | ✅ Already passes |
| SIM-03 | No commented-out code (ERA001 clean) | lint | `uv run python -m ruff check src/pytest_bdd/ --select ERA001` | ✅ Already passes |
| SIM-03 | No dead code (vulture clean at 80%+) | static analysis | `uv run python -m vulture src/pytest_bdd/ --min-confidence 80` | ❌ 12 findings |
| SIM-03 | Plugin usage documented | manual | Review each of 17 plugins | ❌ Wave 0 |
| SIM-03 | CI matrix passes | integration | `uv run tox` | ✅ tox.ini configured |

### Sampling Rate
- **Per task commit:** `uv run python -m ruff check src/pytest_bdd/ --select F401,F811,ERA001`
- **Per wave merge:** `uv run python -m pytest tests/ -q -x`
- **Phase gate:** Full tox matrix green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_dead_code.py` — verifies no vulture findings at 80%+ confidence
- [ ] `tests/unit/test_no_commented_code.py` — verifies ERA001 clean
- [ ] Plugin justification documentation — one file per plugin or consolidated report

## Security Domain

> Not applicable — this phase is code quality/cleanup, no new security surface area.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | no | — |
| V6 Cryptography | no | — |

## Sources

### Primary (HIGH confidence)
- ruff 0.15.10 — verified via `uv run python -m ruff --version` and `ruff check --select F401,F811,ERA001`
- vulture — installed and run against codebase, 270 findings at 60%, 12 at 80%
- tox.ini — read directly from repository, 30+ environments defined
- pyproject.toml — read directly, 17 plugin entry points, 3 script entry points
- CONTEXT.md — read directly, 8 locked decisions

### Secondary (MEDIUM confidence)
- decopatch 1.4.10 — verified via import, last release 2022-03-01
- Large file line counts — verified via `Get-Content` and Python script
- Import analysis — verified via Select-String and Python AST parsing

### Tertiary (LOW confidence)
- vulture false positive rate for pytest hooks — based on pattern analysis, not official documentation
- CI matrix execution time — estimated based on environment count, not measured

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified via registry and direct execution
- Architecture: HIGH — codebase analysis, CONTEXT.md decisions
- Pitfalls: HIGH — observed in codebase (vulture false positives confirmed)
- Dead code findings: HIGH for 80%+ vulture, MEDIUM for 60% (requires manual triage)

**Research date:** 2026-05-16
**Valid until:** 30 days (stable codebase, slow-moving dependencies)
