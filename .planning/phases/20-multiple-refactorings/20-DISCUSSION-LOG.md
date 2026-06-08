# Phase 20: multiple-refactorings - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-08
**Phase:** 20-multiple-refactorings
**Areas discussed:** Task ordering and wave planning, Stub packaging strategy for T1, Custom ruff rule organization, Plugin core/extra split criteria

---

## Task Ordering and Wave Planning

| Option | Description | Selected |
|--------|-------------|----------|
| Typing (T0-T3) first | Mypy --strict is foundational but may touch every file creating merge conflicts | |
| Architecture (A1-A4) first | File splits and layer definition change import graphs; better to stabilize structure before types | ✓ |
| Interleaved waves | T0 + A2 + D2 as Wave 1, T1-T2 + A1 + D1 as Wave 2, T3 + A3-A4 + D0-D3 as Wave 3 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Gate: T0 blocks T1-T3 | Type checker comparison results may affect stub strategy | ✓ |
| Parallel: T0 and T1 can run together | Independent work; pyright recommendation doesn't change mypy--strict as primary gate | |

| Option | Description | Selected |
|--------|-------------|----------|
| A4 first — define layers, then audit/split | Layer boundaries tell A1 where split sub-modules belong and A2 which plugins violate layers | ✓ |
| A2+A1 first — audit/split, then define layers | File splits reveal unexpected dependencies; defining layers after dust settles is more accurate | |

| Option | Description | Selected |
|--------|-------------|----------|
| ADR writing gates architecture | Write ADR during architecture work as design doc before implementation | ✓ |
| ADRs after architecture settles | Write ADRs reflecting final state; cleaner narrative but loses decision-making context | |

**User's choice:** Architecture first; T0 gates T1-T3; A4 (layers) before A2+A1; ADRs as design documents during architecture.

---

## Stub Packaging Strategy for T1

| Option | Description | Selected |
|--------|-------------|----------|
| Ship stubs in wheel | Downstream users can run mypy without installing types-* packages | ✓ |
| Dev-only stubs | Smaller wheel; users run mypy via types-* from PyPI | |

| Option | Description | Selected |
|--------|-------------|----------|
| src/pytest_bdd/_stubs/<pkg>/ | Colocated with source; mypy_path picks them up naturally | |
| stubs/ at repo root | Standard typeshed-like layout; cleaner separation from source | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| One .pyi file per package | Simpler, fewer files; fails for packages needing submodule stubs | |
| Package directory with __init__.pyi | Allows sub-module stubs later; matches typeshed convention | ✓ |

**User's choice:** Ship stubs in wheel, at `stubs/` repo root, organized as package directories with `__init__.pyi`.

---

## Custom Ruff Rule Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Three separate files under _ruff/ | typing_rules.py, file_size_rules.py, layer_rules.py; matches existing pattern | ✓ |
| Single quality_rules.py extension | Add to existing quality_gates.py; less file churn but mixes concerns | |

| Option | Description | Selected |
|--------|-------------|----------|
| Lint rule: flag files >400 LOC | Simple rule; human planner proposes splits | |
| Lint rule + AST analysis | AST analysis counts distinct responsibility clusters; includes split proposals | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Configuration file (TOML/JSON) | Layer definitions in config; easy to update without code changes | ✓ |
| Hardcoded in rule source | Layer definitions in Python; simpler for single codebase | |

**User's choice:** Three separate files, AST analysis for file-size rule, TOML config for layer boundaries.

---

## Plugin Core/Extra Split Criteria (A2)

| Option | Description | Selected |
|--------|-------------|----------|
| Runtime-critical path only | Collection + execution only; reporting is extra | |
| Collection + Execution + Live Reporting | Add gherkin_message_reporter to core; formatters depend on it | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Thematic groups | formatters, struct-bdd, allure, code-gen; users install pip install pytest-bdd[formatters] | ✓ |
| One extra per plugin | Full granularity; 16+ extras in pyproject.toml | |
| Two-tier: core extras + full | Recommended group + full; middle ground | |

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-load when extra installed | pytest11 entry points register automatically; less friction | ✓ |
| Always require explicit -p | Prevents surprise plugin loading; adds friction | |

**User's choice:** Core = collection + execution + live reporting; thematic extras groups; auto-load when extra installed.

---

## the agent's Discretion

- Exact plan breakdown into numbered sub-plans
- Exact stub file content and which packages get types-* vs local stubs
- Exact ruff rule implementation details
- Exact TOML config schema for layer boundaries
- Exact pyproject.toml extras dependency lists
- ADR template and numbering
- How-to guide content beyond SPEC.md
- Object map scoring script implementation
- Sphinx autodoc page structure
- Go parser build system changes within setuptools constraint

## Responsibility Documentation Expansion

**Date:** 2026-06-12

User supplied a new phase wave scope: full responsibility documentation for every Python entity under `src/pytest_bdd/`.

Selected decisions:

- Preserve existing docstrings; append responsibility contracts when absent.
- Create missing docstrings with a normal summary plus responsibility contract.
- Cover modules, classes, functions, methods, async functions, and async methods.
- Responsibility contracts must describe direct ownership, reason for existence, delegates, cohesion, separation from actual same-kind peers when possible, source-derived consumers, and evidence-based scores.
- Add idempotent injector/check tooling with `--check`, `--write`, `--stub`, placeholder validation, and JSON report output.
- Expand object-map collection and add responsibility-zone analysis.
- Add Pylint gate for missing, placeholder, empty, and invalid responsibility contracts.
- Link generated responsibility documentation from architecture/API docs and DEVELOPMENT.rst.

## Deferred Ideas

None.
