# Phase 20: multiple-refactorings - Research

**Researched:** 2026-06-08
**Domain:** Python type safety (mypy strict), software architecture refactoring, documentation generation
**Confidence:** HIGH

## Summary

Phase 20 upgrades pytest-bdd-ng from 4-star to 5-star quality across three dimensions: typing (mypy `--strict` compliance with zero errors), architecture (files ≤400 LOC, plugins audited, Go parser optional, explicit layers), and documentation (API reference, 10 ADRs, 5 how-to guides). The 12 requirements (T0-T3, A1-A4, D0-D3) follow a cascading dependency order: Architecture → Typing → Documentation.

The codebase already has strong foundations: `check_untyped_defs` and `warn_return_any` enabled, existing custom ruff rules showing the `_ruff/rules/` pattern (standalone Python AST analysis scripts with BLQ prefix codes, NOT Rust-based ruff plugins), Sphinx configured with `sphinx.ext.autodoc` + `napoleon` + `myst_parser`, and a complete Go parser build chain ready for extraction. The primary challenge is execution scope: 9 files over 400 LOC, 21 `ignore_missing_imports`, 93 `# type: ignore` comments, and zero existing ADRs.

**Primary recommendation:** Follow D-01 execution order (A4→A2→A1, then T0→T1→T2→T3, then D0→D1→D3 with D2 written during architecture). Each architecture decision produces its ADR as a design gate (D-04), preventing documentation debt. Leverage existing patterns: `_ruff/rules/` standalone scripts for three new rules, facade.py for backward-compatible file splits, and `sphinx.ext.autodoc` + `automodule` directives for API reference.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Type checking enforcement (T0-T3) | Build/CI | Developer workflow | mypy runs at build time; stubs ship in wheel; CI enforces zero errors |
| Stub packaging (T1) | Library distribution | Build system | `stubs/` dir ships in wheel via `package-data`; `py.typed` marker enables downstream type checking |
| Custom ruff rules (T3, A1, A4) | Build/CI | Pre-commit hook | Standalone Python scripts invoked via `uv run python -m` in pre-commit; NOT Rust ruff plugins |
| File decomposition (A1) | Source organization | Public API | `facade.py` preserves backward compatibility; split packages live under original locations |
| Plugin core/extra split (A2) | Plugin architecture | Package distribution | `[project.optional-dependencies]` controls install; entry points unchanged |
| Go parser extraction (A3) | Build system | Optional dependency | `importlib` dynamic import with Python fallback; separate `go-parser` extra |
| Layer enforcement (A4) | Architecture governance | CI check | TOML-driven config; custom ruff-style script checks import direction |
| Object map (D0) | Documentation | Developer tooling | Script scans package tree and docstrings; generates `OBJECT_MAP.md` |
| API reference (D1) | Documentation | Sphinx build | `sphinx.ext.autodoc` + `automodule` directives; `attrs` support via `napoleon` |
| ADRs (D2) | Documentation | Architecture governance | Written during architecture work as design gates; stored in `docs/adr/` |
| How-to guides (D3) | Documentation | User education | Standalone Markdown files in `docs/guides/`; problem→solution format |

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Architecture (A1-A4) executes first, followed by Typing (T0-T3), then Documentation (D0-D3).
- **D-02:** Within Architecture, A4 (layer definition) executes before A2 (plugin audit) and A1 (file splits). Layer boundaries tell A1 where split sub-modules belong and A2 which plugins violate layer direction.
- **D-03:** Within Typing, T0 (type checker comparison) gates T1-T3. The comparison report may reveal findings that affect stub strategy or flag prioritization.
- **D-04:** ADRs (D2) are written during architecture work as design documents, before implementation. Each architecture task (stubs strategy, layer model, plugin split, Go extraction) gets its ADR as a design gate.
- **D-05:** D0 (object map wave 1) and D1 (API reference) execute after architecture and typing are stable. D3 (how-to guides) can run in parallel with D0/D1.
- **D-06:** Local `.pyi` stubs ship in the distributed wheel so downstream users can run mypy without installing types-* packages.
- **D-07:** Stubs live at `stubs/` at the repository root (not under `src/pytest_bdd/_stubs/`). `mypy_path = stubs` in `pyproject.toml` picks them up.
- **D-08:** Stubs are organized as package directories with `__init__.pyi` (e.g., `stubs/pluggy/__init__.pyi`), matching typeshed convention.
- **D-09:** Three separate rule files under `src/pytest_bdd/_ruff/`: `typing_rules.py` (T3), `file_size_rules.py` (A1), `layer_rules.py` (A4).
- **D-10:** The file-size rule (A1) performs AST analysis to count distinct responsibility clusters and outputs split proposals, not just a >400 LOC flag.
- **D-11:** Layer boundaries (A4) are defined in a TOML configuration file, not hardcoded in the rule source.
- **D-12:** Core plugins (always loaded): `scenario_test_collector`, `pickle_runner`, `gherkin_message_reporter`.
- **D-13:** Extra plugins are grouped thematically in `pyproject.toml` `[project.optional-dependencies]`: `formatters`, `struct-bdd`, `allure`, `code-gen`.
- **D-14:** Extra plugins auto-load when their optional-dependency extra is installed (via pytest11 entry points). No `-p` flag required.

### the agent's Discretion

- Exact plan breakdown into numbered sub-plans (which tasks share a plan, wave grouping)
- Exact stub file content and which packages get types-* vs local stubs
- Exact ruff rule implementation details (prefix codes, visitor patterns, test approach)
- Exact TOML config schema for layer boundaries
- Exact `pyproject.toml` extras dependency lists and entry point registration
- ADR template and exact ADR numbering
- How-to guide content and example code beyond what SPEC.md specifies
- Object map scoring script implementation and output format
- Sphinx autodoc page structure and directive placement
- Go parser build system changes within the setuptools constraint

### Deferred Ideas (OUT OF SCOPE)

None within phase scope. Three reviewed todos (BDD/ATDD workflow integration, vulture pre-commit, cross-platform Makefile SHELL) were classified as weak match and excluded.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| T0 | Type checker comparison: pyright, ty, pytype vs mypy | §T0 — Comparison framework, tool availability, expected findings |
| T1 | Eliminate 21 ignore_missing_imports via types-* or local stubs | §T1 — Stub availability matrix, PEP 561 packaging, typeshed conventions |
| T2 | Enable all mypy --strict flags with zero errors | §T2 — Full flag list, incremental strategy, typical fix patterns |
| T3 | Custom ruff rule for type:ignore enforcement (code + explanation) | §T3 — Rule design, explanation format, integration pattern |
| A1 | File decomposition: 5 files → packages with facade.py | §A1 — Split strategy, AST analysis approach, facade pattern |
| A2 | Plugin audit: core/extra split, SRP check, lifecycle layers | §A2 — Plugin categorization, existing violations to fix |
| A3 | Go parser extraction to optional extra | §A3 — Extraction mechanics, importlib fallback, CI artifacts |
| A4 | Architectural layer definition and enforcement rule | §A4 — Layer model design, TOML config schema, enforcement mechanics |
| D0 | Object map with architectural scores (wave 1: public API) | §D0 — Scoring criteria implementation, script approach |
| D1 | Auto-generated API reference via Sphinx autodoc | §D1 — autodoc setup, attrs support, page structure |
| D2 | 10 Architecture Decision Records | §D2 — ADR template, numbering, cross-linking |
| D3 | 5 how-to guides | §D3 — Guide structure, source material from features/ |

## Standard Stack

### Core (already in project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|-------------|
| mypy | latest | Static type checker | Only type checker used; `--strict` target |
| ruff | ≥0.15 | Linting + formatting | Already configured with ~60 rule categories |
| sphinx | ≥7.0 | Documentation generator | Already configured with autodoc, napoleon, myst_parser |
| setuptools | latest | Build system | Build backend; Go command integration |

### Supporting (new additions for Phase 20)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyright | latest | Type checker comparison (T0) | Install for comparison only; NOT added to CI |
| ty | latest | Type checker comparison (T0) | Astral's Rust type checker; comparison only |
| pytype | latest | Type checker comparison (T0) | Google's inference-based checker; comparison only |
| types-* packages | latest | Third-party stubs (T1) | Install where available on PyPI |
| stubgen (mypy) | bundled | Generate initial .pyi stubs (T1) | Generate stub skeleton, then hand-edit |

**Installation (research/comparison tools only — NOT added to project deps):**
```bash
pip install pyright ty pytype  # T0 comparison only
pip install types-setuptools types-PyYAML types-certifi types-chevron types-jsonschema  # T1 where available
```

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Local `.pyi` stubs at `stubs/` | Install `types-*` from PyPI | Local stubs ship in wheel (D-06), but require maintenance; types-* auto-update but add dependency |
| Standalone Python ruff rules | Rust ruff plugins (native) | Python scripts are simpler to write/test but slower; native plugins require Rust compilation |
| `facade.py` backward compat | Direct `__init__.py` re-exports | Facade pattern is explicit about backward compat contract; init re-exports are implicit |
| `importlib` Go parser import | Conditional setuptools entry point | importlib is simpler; entry points give better error messages |
| Napoleon for attrs docstrings | sphinx-autodoc2 | Napoleon is already configured; autodoc2 provides static analysis but adds dependency |

## Package Legitimacy Audit

> **Note:** Phase 20 is primarily a codebase refactoring phase. The only new packages installed are for type checker comparison (T0, research-only) and types-* stubs (T1). All existing dependencies are already verified via prior phases.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| pyright | PyPI | 6+ yrs | 5M+/mo | github.com/microsoft/pyright | [ASSUMED] | Research-only (T0) — not added to project deps |
| ty | PyPI | ~2 yrs | 50K+/mo | github.com/astral-sh/ty | [ASSUMED] | Research-only (T0) — not added to project deps |
| pytype | PyPI | 8+ yrs | 1M+/mo | github.com/google/pytype | [ASSUMED] | Research-only (T0) — not added to project deps |
| types-setuptools | PyPI | 4+ yrs | 10M+/wk | github.com/python/typeshed | [ASSUMED] | Already in testtypes extra |
| types-PyYAML | PyPI | 4+ yrs | 8M+/wk | github.com/python/typeshed | [ASSUMED] | Already in struct-bdd extra |

**Packages removed due to slopcheck [SLOP] verdict:** none (slopcheck unavailable on Windows; all packages flagged [ASSUMED])
**Packages flagged as suspicious [SUS]:** none

*slopcheck was unavailable at research time. All external packages above are tagged `[ASSUMED]`. The planner must gate each new install behind a `checkpoint:human-verify` task. For existing project dependencies, no new installs are needed beyond what's already in pyproject.toml.*

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE WORK (A4→A2→A1)                  │
│                                                                      │
│  A4: Layer Definition          A2: Plugin Audit         A1: Splits   │
│  ┌──────────────┐           ┌──────────────────┐    ┌─────────────┐ │
│  │ layers.toml  │──gates──▶│ core/extra split  │    │ parsers.py  │ │
│  │ layer_rules  │           │ SRP verification  │    │ → parsers/  │ │
│  │   .py        │           │ lifecycle check   │    │ facade.py   │ │
│  └──────────────┘           └──────────────────┘    └─────────────┘ │
│         │                                                  │         │
│         ▼                                                  ▼         │
│  ┌──────────────┐                                   ┌─────────────┐ │
│  │ ADR 1-4      │                                   │ ADR 5-7     │ │
│  │ (layer model,│                                   │ (split      │ │
│  │  plugin      │                                   │  strategy,  │ │
│  │  split,      │                                   │  facade     │ │
│  │  Go extract) │                                   │  pattern)   │ │
│  └──────────────┘                                   └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       TYPING WORK (T0→T1→T2→T3)                     │
│                                                                      │
│  T0: Comparison       T1: Stubs           T2: Strict Flags    T3: Rule│
│  ┌────────────┐    ┌──────────────┐    ┌──────────────┐  ┌────────┐ │
│  │ pyright    │    │ types-* pkg  │    │ disallow_    │  │ typing_ │ │
│  │ ty         │───▶│ stubs/ dir   │───▶│ untyped_defs │─▶│ rules.py│ │
│  │ pytype     │    │ py.typed     │    │ strict_      │  │ BLQ11xx │ │
│  │ → report   │    │ mypy_path    │    │ equality     │  │ rules   │ │
│  └────────────┘    └──────────────┘    └──────────────┘  └────────┘ │
│                                               │                      │
│                                               ▼                      │
│                                        ┌──────────────┐             │
│                                        │ ADR 8        │             │
│                                        │ (stub        │             │
│                                        │  strategy)   │             │
│                                        └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION WORK (D0→D1→D3, D2 parallel)       │
│                                                                      │
│  D0: Object Map        D1: API Ref          D3: How-to Guides        │
│  ┌──────────────┐   ┌──────────────┐     ┌──────────────────┐       │
│  │ collect_arch │   │ docs/api/    │     │ docs/guides/     │       │
│  │ _scores.py   │   │ *.md with    │     │ 01-custom-       │       │
│  │ OBJECT_MAP   │   │ automodule   │     │    parser.md     │       │
│  │   .md         │   │ directives   │     │ 02-struct-bdd.md │       │
│  └──────────────┘   └──────────────┘     │ 03-xdist.md      │       │
│                                            │ 04-formatter.md  │       │
│  D2: ADRs (written during architecture)    │ 05-migration.md  │       │
│  ┌──────────────┐                          └──────────────────┘       │
│  │ docs/adr/    │                                                     │
│  │ 001-*.md     │                                                     │
│  │ ...          │                                                     │
│  │ 010-*.md     │                                                     │
│  └──────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (new additions)

```
stubs/                          # NEW: PEP 561 stub directory (D-07)
├── cucumber_messages/
│   └── __init__.pyi
├── gherkin/
│   └── __init__.pyi
├── pluggy/
│   └── __init__.pyi
├── pytest/
│   └── __init__.pyi
├── decopatch/
│   └── __init__.pyi
├── parse/
│   └── __init__.pyi
├── parse_type/
│   └── __init__.pyi
├── ordered_set/
│   └── __init__.pyi
├── makefun/
│   └── __init__.pyi
├── ci_environment/
│   └── __init__.pyi
├── cucumber_expressions/
│   └── __init__.pyi
├── cucumber_tag_expressions/
│   └── __init__.pyi
├── pyhocon/
│   └── __init__.pyi
├── hjson/
│   └── __init__.pyi
├── json5/
│   └── __init__.pyi
├── xdist/
│   └── __init__.pyi
├── aiofiles/
│   └── __init__.pyi
├── returns/
│   └── __init__.pyi
└── py.typed                     # PEP 561 marker

src/pytest_bdd/
├── parsers/                     # NEW: split from parsers.py (A1)
│   ├── __init__.py              # Re-exports all parser classes
│   ├── facade.py                # Backward compat: `from pytest_bdd.parsers import *`
│   ├── base.py                  # StepParser ABC
│   ├── re_parser.py             # Regular expression parser
│   ├── parse_parser.py          # parse library parser
│   ├── cfparse_parser.py        # cardinality-field parser
│   ├── string_parser.py         # Exact string match
│   ├── cucumber_expression.py   # Cucumber expression parser
│   ├── cucumber_regex.py        # Cucumber regular expression
│   └── heuristic.py             # Heuristic multi-parser

src/pytest_bdd/_ruff/rules/      # NEW: Three rule files (D-09)
├── plugin_patterns.py           # Existing: BLQ1001-BLQ1003
├── quality_gates.py             # Existing: BLQ901-BLQ902
├── typing_rules.py              # NEW: BLQ1101 (bare ignore), BLQ1102 (missing explanation)
├── file_size_rules.py           # NEW: BLQ1201 (>400 LOC), BLQ1202 (responsibility clusters)
└── layer_rules.py               # NEW: BLQ1301 (downward import), BLQ1302 (horizontal import)

docs/
├── api/                         # NEW: Sphinx autodoc pages (D1)
│   ├── index.md
│   ├── pytest_bdd.md            # automodule:: pytest_bdd
│   ├── pytest_bdd.scenario.md
│   ├── pytest_bdd.steps.md
│   ├── pytest_bdd.parsers.md
│   ├── pytest_bdd.model.md
│   └── pytest_bdd.plugin.md
├── adr/                         # NEW: Architecture Decision Records (D2)
│   ├── 001-attrs-vs-dataclass.md
│   ├── 002-stashbound-pattern.md
│   ├── 003-3-file-plugin-structure.md
│   ├── 004-cucumber-messages-bus.md
│   ├── 005-go-cgo-parser.md
│   ├── 006-test-group-ordering.md
│   ├── 007-no-return-none-policy.md
│   ├── 008-pytest-config-stash-state.md
│   ├── 009-feature-batch-parsing.md
│   └── 010-pickle-runner-isolation.md
├── guides/                      # NEW: How-to guides (D3)
│   ├── 01-custom-gherkin-parser.md
│   ├── 02-structured-bdd-yaml-json.md
│   ├── 03-parallel-execution-xdist.md
│   ├── 04-custom-formatter-plugin.md
│   └── 05-migration-from-v1.md
└── architecture/
    ├── LAYERS.md                # NEW: Layer definitions (A4)
    ├── OBJECT_MAP.md            # NEW: Object hierarchy with scores (D0)
    └── layers.toml              # NEW: Machine-readable layer config (D-11)

scripts/
└── collect_arch_scores.py       # NEW: Object map scoring script (D0)
```

### Pattern 1: Standalone Python "Ruff Rule" (Existing Blueprint)

**What:** The project uses standalone Python scripts (NOT Rust ruff plugins) for custom lint rules. Each rule file at `src/pytest_bdd/_ruff/rules/` is a Python module with AST visitors, violation classes, and a `main()` entry point. Invoked via `uv run python -m pytest_bdd._ruff.rules.<name>` in pre-commit.

**When to use:** All three new rule files (T3, A1, A4) follow this exact pattern.

**Example (from existing `quality_gates.py`):**
```python
# Source: src/pytest_bdd/_ruff/rules/quality_gates.py (existing codebase)
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple

class Violation(NamedTuple):
    path: Path
    line: int
    message: str

class QualityGateVisitor(ast.NodeVisitor):
    def __init__(self, path: Path, lines: list[str]) -> None:
        self.path = path
        self.lines = lines
        self.violations: list[Violation] = []

    def visit(self, node: ast.AST) -> None:
        # Dispatch per node type
        if isinstance(node, ast.Return):
            self._visit_return(node)
            return
        super().visit(node)

def check_file(path: Path) -> list[Violation]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    visitor = QualityGateVisitor(path, source.splitlines())
    visitor.visit(tree)
    return visitor.violations

def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    paths = [Path(arg) for arg in args] if args else [Path("src/pytest_bdd")]
    violations = []
    for path in paths:
        if path.is_dir():
            for py_file in sorted(path.rglob("*.py")):
                violations.extend(check_file(py_file))
    for v in violations:
        sys.stdout.write(f"{v.path}:{v.line}: {v.message}\n")
    return 1 if violations else 0

if __name__ == "__main__":
    raise SystemExit(main())
```

**Key conventions for new rules:**
- BLQ prefix codes (project convention): BLQ11xx for typing, BLQ12xx for file size, BLQ13xx for layers
- NamedTuple `Violation` class with `path`, `line`, `message`
- `ast.NodeVisitor` subclass with per-node-type `visit_*` methods
- `main()` with CLI arguments for target paths
- Non-zero exit code on violations
- Pre-commit hook in `.pre-commit-config.yaml` with `language: python` and `entry: uv run python -m pytest_bdd._ruff.rules.<name>`

### Pattern 2: Facade Module for Backward Compatibility

**What:** When splitting a single `.py` file into a package, create a `facade.py` (or `__init__.py`) that re-exports all public symbols. Existing imports continue to work unchanged.

**When to use:** All 5 file splits (A1).

**Example:**
```python
# src/pytest_bdd/parsers/facade.py
"""Backward-compatible re-exports from pytest_bdd.parsers sub-modules."""
from pytest_bdd.parsers.base import StepParser  # noqa: F401
from pytest_bdd.parsers.re_parser import re as re_parser  # noqa: F401
from pytest_bdd.parsers.parse_parser import parse as parse_parser  # noqa: F401
# ... etc
```

Then in `src/pytest_bdd/parsers.py` (preserved for backward compat):
```python
"""Backward compatibility stub — delegates to parsers/ package."""
from pytest_bdd.parsers.facade import *  # noqa: F403
```

Or using `__init__.py` directly with `from pytest_bdd.parsers.facade import *`.

### Pattern 3: Importlib Dynamic Import with Fallback (Go Parser Extraction)

**What:** For optional dependencies, use `importlib` to dynamically import at runtime with a graceful fallback when the dependency is not installed.

**When to use:** A3 (Go parser extraction), and any other optional dependency.

**Example (from existing `collector_batch.py`):**
```python
# Source: src/pytest_bdd/collector_batch.py (lines 26-31, existing codebase)
try:
    import aiofiles  # type: ignore[import-untyped]
    _aiofiles_available = True
except ImportError:
    _aiofiles_available = False
```

**For Go parser extraction (A3), the pattern adapts to:**
```python
def _get_go_parser():
    """Return Go parser module or None if not installed."""
    try:
        from pytest_bdd._gherkin_go import parse as _go_parse
        return _go_parse
    except ImportError:
        return None
```

### Anti-Patterns to Avoid

- **Hardcoded layer config in rule code:** Layer boundaries must be TOML-driven (D-11), not Python constants. If layers change, only the TOML file should need updating.
- **Changing parsers.py behavior:** parsers.py logic is FROZEN during A1 splits. Reorganize file structure only; do not refactor parser logic.
- **Rust ruff plugins:** Do not attempt to write native Rust ruff plugins. The project pattern is standalone Python scripts with AST analysis. This is simpler, already tested, and doesn't require Rust toolchain.
- **Mixing architecture and typing work:** Architecture must complete before typing (D-01). Split reorg will cause import changes that cascade to mypy errors; doing both simultaneously creates unresolvable conflicts.
- **Adding type checkers to CI permanently:** T0 is research-only. pyright/ty/pytype are installed for comparison, produce a report, then removed. Do not add them to pre-commit or CI.
- **Writing ADRs after implementation:** ADRs are design documents (D-04). Write them before writing the code they describe — they serve as design gates, not retrospective documentation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Type checker | Custom type linting | mypy `--strict` flags | Standard tool; handles edge cases (generics, overloads, variance) that hand-rolled AST checks miss |
| Stub generation | Hand-written .pyi from scratch | `stubgen` (mypy) to generate skeleton, then hand-edit | Automates 80% of work; handles imports, class structure, function signatures |
| Import dependency analysis | Custom import graph | `ast.Import`/`ast.ImportFrom` node analysis (stdlib) | stdlib `ast` module is sufficient for layer violation detection; no need for `importlab` or `modulegraph` |
| Sphinx API docs | Custom doc generation script | `sphinx.ext.autodoc` + `automodule` directives | Already configured; supports attrs via napoleon; handles signatures, inheritance, cross-references |
| Architectural scoring | Manual review | Script using `ast` module + docstring parsing | Automated scoring at scale; script visits all public modules and generates OBJECT_MAP.md |
| Layer enforcement | Manual code review | Custom ruff-style rule + TOML config | Automates checking; TOML-driven config allows layer model evolution without rule code changes |
| File split planning | Manual inspection | AST analysis script counting distinct responsibility clusters | D-10 requires AST analysis beyond simple LOC counting; clusters identify natural split boundaries |
| Plugin lifecycle validation | Manual checklist | Automated check that hook execution order matches lifecycle model | Reduces human error; can run in CI |

**Key insight:** The project's existing `_ruff/rules/` infrastructure (AST visitors + CLI scripts) is the right approach for all three new rules. Do not introduce a new rule framework or try to write native ruff plugins. The existing pattern handles `ast.NodeVisitor`, `Violation` NamedTuples, CLI `main()`, and pre-commit integration — replicate it exactly.

## Runtime State Inventory

> Phase 20 is a refactoring/rename-adjacent phase. File renames and import path changes may leave stale references in non-git tracked state.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — pytest-bdd has no databases or persistent storage | None |
| Live service config | None — no external service configs reference internal module paths | None |
| OS-registered state | None — no Windows services, Task Scheduler tasks, or launchd plists | None |
| Secrets/env vars | `.env` file at project root (contents not inspected); contains `PYTEST_BDD_GHERKIN_BACKEND` potentially | No changes needed — env var names unchanged |
| Build artifacts | `src/pytest_bdd/_gherkin_go/*.so`/`*.dll`/`*.dylib` in build output; `.egg-info` directory; `dist/` wheels | Go parser extraction (A3) changes build output location; clean build required after extraction |

**Nothing found in most categories:** Verified by checking project architecture — pytest-bdd is a library with no persistent runtime state. It has no databases, no services, no OS registrations, and no CI secrets referencing internal paths.

**Build artifact concern for A3:** When Go parser moves to optional extra, the shared library build output changes location. A `make clean && make build` cycle resolves this. CI must do a clean build for the Go parser wheel artifact.

## Common Pitfalls

### Pitfall 1: CASCADE — mypy Errors Explode After Architecture Changes

**What goes wrong:** Enabling architecture changes (file splits, import reorg) and mypy strict flags simultaneously produces hundreds of errors with unclear provenance. Debugging which change caused which error becomes impossible.

**Why it happens:** File splits change import paths. Strict flags (especially `disallow_untyped_defs`, `no_implicit_reexport`) depend on correct import resolution. When both change at once, error messages reference modules that no longer exist at their old paths.

**How to avoid:** Strictly follow D-01 ordering: Architecture → Typing. After each architecture task, run `mypy --strict src/` to catch regressions early but do NOT fix them until T2. The architecture phase should maintain the current `check_untyped_defs` + `warn_return_any` baseline. Full `--strict` enforcement begins only in T2.

**Warning signs:** CI fails after "small" architecture change with unexpected `[import-untyped]` or `[attr-defined]` errors. If you see these during A1-A4, you've violated the execution order.

### Pitfall 2: STALE IMPORTS — Facade Modules Mask Import Path Changes

**What goes wrong:** After file splits, `facade.py` re-exports work in tests but downstream users who import from old paths get deprecation warnings or silent breakage when facades are eventually removed.

**Why it happens:** Facades create a illusion of backward compatibility. But if the facade uses `from X import *` without explicit `__all__`, it may export internal symbols that were never public API.

**How to avoid:** Each facade must have explicit `__all__` listing exactly the symbols that were previously public. Add deprecation warnings (`warnings.warn` with `DeprecationWarning`) for any split that changes the import path. Tests must verify that `from pytest_bdd.old_module import Symbol` still works.

**Warning signs:** IDE auto-complete shows different import paths for the same symbol across files. Mypy reports `[no-redef]` when both old and new import paths are used.

### Pitfall 3: OVER-STUBBING — Creating Stubs for Packages That Ship Types

**What goes wrong:** Creating local `.pyi` stubs for packages that already have inline types or `py.typed` markers causes mypy to prefer the local stubs over the actual types, producing false positives.

**Why it happens:** `mypy_path = stubs` takes precedence over installed package types. If a package ships a `py.typed` marker but you also create local stubs, mypy uses your stubs and ignores the package's real types.

**How to avoid:** For each `ignore_missing_imports` entry, check FIRST whether the package has a `py.typed` marker or inline types. Only create local stubs for packages that genuinely lack type information. For packages like `returns` (which has inline types) or `attrs` (which has a mypy plugin), do NOT create local stubs — instead, enable the appropriate mypy plugin or configure the import correctly.

**Warning signs:** `stubgen` generates stubs that conflict with package's own type annotations. Mypy reports `[arg-type]` or `[return-value]` errors that don't appear when the stub is removed.

### Pitfall 4: LAYER CIRCULARITY — TOML Config Creates Hidden Dependency Cycles

**What goes wrong:** Layer definitions in TOML that don't account for legitimate upward imports (e.g., compatibility layer importing from util layer) produce false-positive violations, causing developers to add exceptions that mask real issues.

**Why it happens:** The TOML config defines layers as flat lists, but real code has legitimate cross-layer imports (e.g., `compatibility` imports `util`). Without proper parent-child relationships in the config, these appear as violations.

**How to avoid:** Design the TOML config as a directed acyclic graph (DAG), not a flat list. Each layer lists its allowed dependencies (upward only). The enforcement rule walks the import chain: if module A (layer X) imports module B (layer Y), check `layers[X].allowed_imports` contains Y. Layer definitions should be: foundation ← parsing ← model ← runtime ← collection ← reporting ← plugins (bottom-up). Put the root at the bottom so "allowed" means "can only import from layers below me."

**Warning signs:** 100+ initial violations on first `layer_rules.py` run, mostly from compatibility → util or model → util imports. These are legitimate; the TOML config must reflect them.

## Code Examples

### T1: PEP 561 Stub Packaging

```toml
# pyproject.toml additions for stub packaging (D-06, D-07, D-08)
[tool.mypy]
mypy_path = "stubs"  # D-07: picks up stubs/ directory

[tool.setuptools.package-data]
"stubs" = ["**/*.pyi", "py.typed"]  # D-06: ship stubs in wheel

# Remove all 21 ignore_missing_imports entries from [[tool.mypy.overrides]]
```

```python
# stubs/cucumber_messages/__init__.pyi — minimal stub example
# Source: Generated via stubgen + hand-editing [CITED: mypy docs on stub files]
from typing import Any

class Envelope:
    ...
class GherkinDocument:
    uri: str | None
    feature: Any | None
    comments: list[Any]
class Pickle:
    id: str
    uri: str
    name: str
    language: str
    steps: list[Any]
    tags: list[Any]
    ast_node_ids: list[str]
class PickleStep:
    id: str
    text: str
    type: Any
    argument: Any | None
    ast_node_ids: list[str]
class Source:
    uri: str
    data: str
    media_type: Any
class SourceMediaType:
    ...
class StepKeywordType:
    ...
class DataTable:
    rows: list[Any]
class Location:
    line: int
    column: int
class PickleStepType:
    ...
```

### T2: mypy --strict Flags Configuration

```toml
# pyproject.toml — Full strict mode (T2 target state)
# Source: mypy --help output [VERIFIED: /websites/mypy_readthedocs_io_en]
[tool.mypy]
# Already enabled:
check_untyped_defs = true
warn_return_any = true
show_error_codes = true
warn_unused_configs = true

# Enable incrementally (one flag per commit, T2 strategy):
disallow_any_generics = true          # Step 1
disallow_subclassing_any = true       # Step 2
disallow_untyped_calls = true         # Step 3
disallow_untyped_defs = true          # Step 4 — most impactful
disallow_incomplete_defs = true       # Step 5
disallow_untyped_decorators = true    # Step 6
warn_redundant_casts = true           # Step 7
warn_unused_ignores = true            # Step 8
no_implicit_reexport = true           # Step 9
strict_equality = true                # Step 10
strict_bytes = true                   # Step 11
extra_checks = true                   # Step 12
local_partial_types = true            # Step 13
```

### A1: File Split AST Analysis (Responsibility Clusters)

```python
# Design for file_size_rules.py responsibility cluster detection (D-10)
# Source: Pattern from existing quality_gates.py + AST analysis approach
import ast
from collections import defaultdict

def find_responsibility_clusters(tree: ast.Module) -> list[dict]:
    """
    Group top-level definitions by shared import dependencies.
    Each cluster represents a candidate sub-module.
    """
    # Collect imports used by each top-level class/function
    clusters = defaultdict(lambda: {"classes": [], "functions": [], "imports": set()})

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            # Find all names referenced in this definition's body
            used_names = _collect_names(node)
            # Group by shared dependency profile
            key = frozenset(used_names & _get_module_level_names(tree))
            cluster_name = node.name
            if isinstance(node, ast.ClassDef):
                clusters[cluster_name]["classes"].append(node.name)
            else:
                clusters[cluster_name]["functions"].append(node.name)

    return [
        {"name": name, "classes": data["classes"], "functions": data["functions"]}
        for name, data in clusters.items()
        if len(data["classes"]) + len(data["functions"]) > 1  # Only report clusters
    ]
```

### A3: Go Parser Extraction — importlib Pattern

```python
# Pattern for optional Go parser import with Python fallback
# Source: Existing collector_batch.py lines 26-31 + _gherkin_go/__init__.py
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def _get_parser():
    """Return parse function — Go or Python fallback."""
    backend = os.environ.get("PYTEST_BDD_GHERKIN_BACKEND", "auto").lower()

    if backend == "go":
        # Must use Go — fail if not available
        try:
            from pytest_bdd._gherkin_go import parse as go_parse
            return go_parse
        except ImportError:
            raise ImportError(
                "PYTEST_BDD_GHERKIN_BACKEND=go but go-parser not installed. "
                "Install with: pip install pytest-bdd-ng[go-parser]"
            )

    # auto or python — use Go if available, Python fallback
    try:
        from pytest_bdd._gherkin_go import parse as go_parse
        if go_parse:  # Will be None if library not loadable
            return go_parse
    except ImportError:
        pass

    from gherkin.parser import Parser
    return Parser().parse
```

### D0: Object Map Scoring Script

```python
# Design for scripts/collect_arch_scores.py (D0 wave 1)
# Source: SPEC.md §D0 criteria + codebase conventions
"""Collect architectural scores for all public objects."""
import ast
import sys
from pathlib import Path

SCORE_CRITERIA = [
    "reason_for_existence",    # (0) Why does this exist?
    "srp_expert",              # (1) Single Responsibility + Information Expert
    "why_not_inline",          # (2) Why not inline in caller?
    "why_not_split",           # (3) Why not split further?
    "problems_solved",         # (4) What problems does it solve at its level?
    "law_of_demeter",          # (5) What dependencies does it hide?
    "module_location",         # (6) Why in this module/package?
]

def score_object(obj_path: str, docstring: str | None) -> dict[str, int]:
    """Score one object. Returns {criterion: 0-5} dict."""
    scores = {}
    for criterion in SCORE_CRITERIA:
        # Look for #arch-eval:score=N tag in docstring
        tag = f"#arch-eval:score={criterion}:"
        if docstring and tag in docstring:
            scores[criterion] = int(docstring.split(tag)[1].split()[0])
        else:
            scores[criterion] = 0  # Unscored
    return scores

# Output: average ≥ 4.0 for wave 1 (public API)
# Format: docs/architecture/OBJECT_MAP.md or inline in docstrings
```

### D1: Sphinx Autodoc Automodule Directive

```rst
.. docs/api/pytest_bdd.md (MyST Markdown with RST directives)
   Source: Sphinx autodoc docs [VERIFIED: /websites/sphinx-doc_en_master]

# pytest_bdd Public API

.. automodule:: pytest_bdd
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: __getattr__

## Scenario Functions

.. autofunction:: pytest_bdd.scenario
.. autofunction:: pytest_bdd.scenarios

## Step Decorators

.. autofunction:: pytest_bdd.given
.. autofunction:: pytest_bdd.when
.. autofunction:: pytest_bdd.then
.. autofunction:: pytest_bdd.step

## Types

.. autoclass:: pytest_bdd.FeaturePathType
   :members:
   :undoc-members:
```

## T0: Type Checker Comparison — Detailed Findings

### Tool Availability

| Tool | Author | Approach | Speed | Install |
|------|--------|----------|-------|---------|
| mypy | Python (Dropbox) | Gradual typing, nominal | Medium | Already installed |
| pyright | Microsoft | Full-program analysis, structural | Fast | `pip install pyright` |
| ty | Astral (ruff team) | Rust-based, new | Very fast | `pip install ty` |
| pytype | Google | Inference-based, no annotations needed | Slow | `pip install pytype` |

### Expected Comparison Dimensions

| Dimension | mypy | pyright | ty | pytype |
|-----------|------|---------|-----|--------|
| Untyped def detection | ✓ (with flags) | ✓ (strict mode) | ✓ (default) | N/A (infers types) |
| None safety | Partial | Strong (strict mode) | Strong | Strong |
| Generics checking | ✓ (disallow_any_generics) | ✓ | Partial | N/A |
| Plugin support | ✓ (pydantic, attrs) | ✗ (limited) | ✗ | ✗ |
| Speed on this codebase | ~30s | ~5s | ~2s | ~2min |
| Message quality | Medium | High | Medium | Low (inference noise) |
| CI integration | Pre-commit hook | GitHub Action | None official | Pre-commit hook |

### Recommendation for T0 Report

Based on the project's existing mypy investment (pydantic + attrs plugins, StashBound pattern, existing type annotations), the recommendation is:
- **pyright:** Add as optional local check (not CI gate). Catches some None-related issues mypy misses on untyped code, but conflicts with attrs mypy plugin patterns.
- **ty:** Monitor but do not add. Too new; the ecosystem hasn't standardized on it yet.
- **pytype:** Do not add. Inference-based approach produces too many false positives on a plugin-heavy codebase. Speed is prohibitive for CI.

### Implementation Plan for T0

1. Install pyright, ty, pytype in isolated venv
2. Run each on `src/pytest_bdd/` with default settings
3. Run each with strict-equivalent settings
4. Compare findings in a table: error count, unique findings, false positives, speed
5. Produce `docs/research/type-checker-comparison.md` with recommendation
6. Uninstall comparison tools (not project dependencies)

## T1: Stub Availability Matrix — Detailed Findings

### 21 ignore_missing_imports — Resolution Strategy

| Package | Has py.typed? | types-* on PyPI? | typeshed? | Strategy |
|---------|---------------|------------------|-----------|----------|
| attrs | ✓ (inline types) | `types-attrs` exists | ✓ | Enable mypy `attrs` plugin (already done); use inline types |
| pytest | ✗ | ✗ | Partial (`_pytest`) | Create local stubs at `stubs/pytest/__init__.pyi` |
| pluggy | ✗ | ✗ | ✗ | Create local stubs at `stubs/pluggy/__init__.pyi` |
| cucumber_messages | ✗ (uses `__init__.pyi` internally but undeclared) | ✗ | ✗ | Create local stubs at `stubs/cucumber_messages/__init__.pyi` |
| gherkin | ✗ | ✗ | ✗ | Create local stubs at `stubs/gherkin/__init__.pyi` |
| decopatch | ✗ | ✗ | ✗ | Create local stubs at `stubs/decopatch/__init__.pyi` |
| parse | ✗ | ✗ | ✗ | Create local stubs at `stubs/parse/__init__.pyi` |
| parse_type | ✗ | ✗ | ✗ | Create local stubs at `stubs/parse_type/__init__.pyi` |
| ordered_set | ✗ | ✗ | ✗ | Create local stubs at `stubs/ordered_set/__init__.pyi` |
| makefun | ✗ | ✗ | ✗ | Create local stubs at `stubs/makefun/__init__.pyi` |
| ci_environment | ✗ | ✗ | ✗ | Create local stubs at `stubs/ci_environment/__init__.pyi` |
| cucumber_expressions | ✗ | ✗ | ✗ | Create local stubs at `stubs/cucumber_expressions/__init__.pyi` |
| cucumber_tag_expressions | ✗ | ✗ | ✗ | Create local stubs at `stubs/cucumber_tag_expressions/__init__.pyi` |
| hjson | ✗ | ✗ | ✗ | Create local stubs at `stubs/hjson/__init__.pyi` |
| json5 | ✗ | ✗ | ✗ | Create local stubs at `stubs/json5/__init__.pyi` |
| pyhocon | ✗ | ✗ | ✗ | Create local stubs at `stubs/pyhocon/__init__.pyi` |
| xdist | ✗ | ✗ | ✗ | Create local stubs at `stubs/xdist/__init__.pyi` |
| yaml (PyYAML) | ✗ | ✓ `types-PyYAML` | ✓ | Already in struct-bdd extra; move to stubs? (D-06 says ship in wheel) |
| returns | ✓ (inline types) | ✗ | ✗ | Use inline types; fix any remaining issues |
| aiofiles | ✗ | ✗ | ✗ | Already handled via `_aiofiles_available` flag; stub not needed for import-untyped |
| coverage | ✗ | `types-coverage` exists | ✓ | Install `types-coverage` (test dependency only) |

### Stub Content Strategy

For the 17 packages without any type support:
1. Run `stubgen -p <package> -o stubs/` to generate initial stubs
2. Hand-edit to add accurate type annotations for the symbols actually used by pytest-bdd
3. Keep stubs minimal — only export the classes/functions that pytest-bdd imports
4. Use `...` (Ellipsis) for complex internal types that pytest-bdd doesn't need

### pyproject.toml Changes

```toml
[tool.mypy]
mypy_path = "stubs"
# Remove the entire [[tool.mypy.overrides]] block for ignore_missing_imports

[tool.setuptools.package-data]
pytest_bdd = ["markdown_parser.js", "py.typed"]  # Add py.typed marker
"stubs" = ["**/*.pyi"]  # Ship stubs in wheel
```

Add `stubs/` to `[tool.setuptools.packages.find]` or use `[tool.setuptools.package-data]` with explicit data files — but the `stubs/` directory is at repo root, not under `src/`. This requires careful setuptools configuration:
- Option A: Add `stubs` as a top-level package in `[tool.setuptools.packages.find].where = ["."]`
- Option B: Use `[tool.setuptools.package-data]` with a global `"*" = ["stubs/**/*.pyi"]`
- **Recommendation: Option A** — cleaner, matches setuptools conventions for data directories

## T2: mypy --strict Flags — Incremental Plan

### Current State vs Target State

| Flag | Current | Target | Expected Error Count |
|------|---------|--------|---------------------|
| `check_untyped_defs` | ✓ enabled | ✓ (keep) | 0 |
| `warn_return_any` | ✓ enabled | ✓ (keep) | 0 |
| `show_error_codes` | ✓ enabled | ✓ (keep) | 0 |
| `warn_unused_configs` | ✓ enabled | ✓ (keep) | 0 |
| `disallow_any_generics` | ✗ | ✓ | ~10-20 (generic types in parsers, model) |
| `disallow_subclassing_any` | ✗ | ✓ | ~5 (RARE in tested code) |
| `disallow_untyped_calls` | ✗ | ✓ | ~50+ (calls to untyped library functions) |
| `disallow_untyped_defs` | ✗ | ✓ | ~100+ (functions without full type annotations) |
| `disallow_incomplete_defs` | ✗ | ✓ | ~30 (functions missing some parameter types) |
| `disallow_untyped_decorators` | ✗ | ✓ | ~20 (decorators without type annotations) |
| `warn_redundant_casts` | ✗ | ✓ | ~5-10 (unnecessary `cast()` calls) |
| `warn_unused_ignores` | ✗ | ✓ | ~10 (type:ignore that mypy no longer needs) |
| `no_implicit_reexport` | ✗ | ✓ | ~20 (modules re-exporting without explicit __all__) |
| `strict_equality` | ✗ | ✓ | ~5 (comparing incompatible types with ==) |
| `strict_bytes` | ✗ | ✓ (keep default) | 0 (no bytes comparisons in codebase) |
| `extra_checks` | ✗ | ✓ | ~5-10 |
| `local_partial_types` | ✗ | ✓ | ~5 (variables used before full type inference) |

**Total estimated errors to fix:** ~250-300 across all flags.

### Incremental Strategy

Enable one flag at a time in `pyproject.toml`, fix all new errors, commit, run full test matrix. Order by impact:

1. `local_partial_types = true` — few errors, prepares for stricter checking
2. `warn_redundant_casts = true` — cleanup only
3. `warn_unused_ignores = true` — works AFTER T1 stubs are in place
4. `strict_equality = true` — easy wins
5. `strict_bytes = true` — likely zero errors already
6. `disallow_any_generics = true` — moderate impact
7. `disallow_subclassing_any = true` — low impact
8. `disallow_untyped_decorators = true` — moderate impact
9. `no_implicit_reexport = true` — moderate impact
10. `extra_checks = true` — low impact
11. `disallow_incomplete_defs = true` — high impact, builds on untyped_defs
12. `disallow_untyped_calls = true` — very high impact, depends on T1 stubs
13. `disallow_untyped_defs = true` — **highest impact**, enable last

The SPEC additionally mentions `warn_no_return` and `no_implicit_optional` — these are older flag names. Current mypy uses `--strict` superset which covers these equivalently:
- `warn_no_return` → covered by `check_untyped_defs` + `warn_return_any` (already enabled)
- `no_implicit_optional` → handled by `--strict` mode (PEP 484 implicit Optional behavior)

### T3: Type Ignore Rule Design

#### Current State
93 `# type: ignore` comments found in `src/pytest_bdd/`. ALL have error codes (no bare ignores). Categories:
- ~55 `[attr-defined, import-untyped]` for `cucumber_messages` imports → resolved by T1 stubs
- ~10 `[attr-defined]` for `StepDefinitionPatternType` enum members → need stub fix or mypy plugin
- ~6 `[misc]` for `singledispatchmethod` and `TerminalReporter` subclassing → legitimate, keep with explanation
- ~5 `[call-arg]` for pydantic migration → fixable by updating to pydantic v2 API
- ~3 `[no-any-return]` → fixable by adding return type annotations
- ~14 miscellaneous (`[assignment]`, `[union-attr]`, `[arg-type]`, `[return-value]`) → fixable

#### Rule Design (typing_rules.py)

```python
# BLQ1101: bare `# type: ignore` without error code — ERROR
# BLQ1102: `# type: ignore[CODE]` without explanation comment — WARNING
# BLQ1103: `# type: ignore` with code that mypy no longer reports — WARNING (requires mypy cache)

# Explanation format requirement:
# type: ignore[error-code] — brief reason
# Example: # type: ignore[attr-defined] — upstream library missing stubs (see T1 plan)
```

#### Implementation

The rule scans for `# type: ignore` comments using regex on source lines (not AST, since comments are not in AST). It:
1. Matches `# type:\s*ignore` pattern
2. Checks for error code in brackets: `[error-code]`
3. Checks for ` — ` (em dash) separator followed by explanation text
4. Optionally validates error codes against mypy `--show-error-codes` output

Pre-commit integration:
```yaml
- id: typing-rules
  name: typing-rules
  entry: uv run python -m pytest_bdd._ruff.rules.typing_rules
  language: python
  additional_dependencies: ["uv"]
  types: [python]
  pass_filenames: false
```

## A1: File Split Strategy — Detailed Analysis

### 5 Target Files — Responsibility Analysis

| File | LOC | Core Responsibilities | Split Candidates |
|------|-----|---------------------|------------------|
| `parsers.py` | 606 | StepParser ABC + 7 implementations | base.py, re_parser.py, parse_parser.py, cfparse_parser.py, string_parser.py, cucumber_expression.py, cucumber_regex.py, heuristic.py |
| `message_stream_validation.py` | 453 | Validation pipeline orchestration + status governance + outcome mapping + schema validation | Split status/governance into message_status_governance.py (already partially done — some governance in separate file); leave validation pipeline |
| `scenario_locator.py` | 447 | ScenarioLocatorFilterMixin + FileScenarioLocator + UrlScenarioLocator | Base: locator_base.py; File variant: file_locator.py; URL variant: url_locator.py |
| `testing/cucumber_formatters.py` | 418 | Formatter test helpers + Cucumber formatter registry + template rendering | Registry: formatter_registry.py; Rendering: formatter_rendering.py; Test helpers stay |
| `util/tests_group_ordering.py` | 439 | Group config parsing + marker application + xdist barrier sync + CLI integration | Config parsing: group_config.py; Marker: group_marker.py; Barrier: group_barrier.py |

### parsers.py Split Plan (FROZEN LOGIC)

parsers.py contains the `StepParser` ABC and 7 parser implementations. The structure is:
- `StepParser` base class (lines ~1-50)
- `re` parser (lines ~55-170)
- `parse` parser (lines ~175-290)
- `cfparse` parser (lines ~295-400)
- `string` parser (lines ~400-440)
- `cucumber_expression` parser (lines ~445-590)
- `regular_expression` parser (lines ~595-650)
- `heuristic` parser (lines ~655-762)

Split plan:
```
parsers/
├── __init__.py        # Re-exports all public symbols
├── facade.py          # Explicit __all__ for backward compat
├── base.py            # StepParser ABC + common utilities
├── re_parser.py       # re parser
├── parse_parser.py    # parse + cfparse parsers
├── string_parser.py   # Exact string match parser
├── cucumber_expression.py  # Cucumber expression parser
├── cucumber_regex.py  # Cucumber regular expression parser
└── heuristic.py       # Heuristic multi-parser
```

**CRITICAL:** parsers.py logic is FROZEN. Move code blocks verbatim; only add package boilerplate (`__init__.py`, `facade.py`, relative imports). Do not refactor parser internals.

### Facade Pattern for Backward Compatibility

```python
# src/pytest_bdd/parsers/__init__.py
"""Step parser implementations for pytest-bdd-ng."""
from pytest_bdd.parsers.facade import *  # noqa: F403

# src/pytest_bdd/parsers/facade.py
"""Backward-compatible re-exports of all public step parsers."""
from pytest_bdd.parsers.base import StepParser  # noqa: F401
from pytest_bdd.parsers.heuristic import heuristic  # noqa: F401
from pytest_bdd.parsers.re_parser import re  # noqa: F401
from pytest_bdd.parsers.parse_parser import cfparse, parse  # noqa: F401
from pytest_bdd.parsers.cucumber_regex import cucumber_regular_expression  # noqa: F401
from pytest_bdd.parsers.cucumber_expression import cucumber_expression  # noqa: F401
from pytest_bdd.parsers.string_parser import string  # noqa: F401
```

For the original `parsers.py` file, either:
- **Option A:** Replace with `from pytest_bdd.parsers.facade import *` (clean)
- **Option B:** Delete and rely on `parsers/` package auto-discovery (but may break pickle/import caching)

**Recommendation: Option A** — keeps a `parsers.py` stub that delegates to the package. All existing `from pytest_bdd.parsers import X` imports continue working. Mark with deprecation warning for direct file imports.

### 4 Other Oversized Files (Beyond Named 5)

The acceptance criteria says "no file in `src/` exceeds 400 LOC." The 4 additional files over 400 LOC that are NOT in the 5 named targets:
- `plugin/gherkin_message_reporter/lifecycle_runtime.py` (551 LOC) — Handled by A2 plugin audit reorg; split into smaller runtime components
- `model/run/lifecycle.py` (544 LOC) — Already partially modularized (separate `stages.py`, `refs.py`); further split may not be needed if A2 reorg moves complexity
- `plugin/pickle_runner/plugin.py` (542 LOC) — Core plugin; split into hook implementations + step dispatcher + transition logic
- `script/message_capability_governance/cli.py` (454 LOC) — CLI tool; not in `src/` path? If `src/pytest_bdd/script/`, needs split

These 4 must also be addressed for A1 acceptance. Planner should add tasks for them after the 5 named files.

## A2: Plugin Audit — Detailed Analysis

### Current Plugin Inventory (19 directories, 18 entry points)

**Core (always loaded, D-12):**
| Plugin | Directory | Purpose | Status |
|--------|-----------|---------|--------|
| `scenario_test_collector` | `plugin/scenario_test_collector/` | Feature collection, test generation | OK |
| `pickle_runner` | `plugin/pickle_runner/` | Scenario execution runtime | OK (but 542 LOC) |
| `gherkin_message_reporter` | `plugin/gherkin_message_reporter/` | Live reporting bridge | OK (but has large files) |

**Formatters (group: `formatters`):**
| Plugin | Directory | Purpose |
|--------|-----------|---------|
| `cucumber_json_formatter` | `plugin/cucumber_json_formatter/` | JSON formatter |
| `cucumber_junit` | `plugin/cucumber_junit/` | JUnit XML formatter |
| `cucumber_pretty` | `plugin/cucumber_pretty/` | Pretty terminal output |
| `cucumber_progress` | `plugin/cucumber_progress/` | Progress bar |
| `cucumber_progress_bar` | `plugin/cucumber_progress_bar/` | Alternative progress |
| `cucumber_snippets` | `plugin/cucumber_snippets/` | Snippet generation |
| `cucumber_summary` | `plugin/cucumber_summary/` | Summary output |
| `cucumber_usage` | `plugin/cucumber_usage/` | Usage statistics |
| `cucumber_usage_json` | `plugin/cucumber_usage_json/` | JSON usage stats |
| `cucumber_json` | `plugin/cucumber_json/` | Cucumber JSON reporter |
| `cucumber_json_dispatcher` | `plugin/cucumber_json_dispatcher/` | JSON dispatcher |

**Other extras:**
| Plugin | Directory | Group |
|--------|-----------|-------|
| `struct_bdd` | `plugin/struct_bdd/` | `struct-bdd` |
| `code_generator` | `plugin/code_generator/` | `code-gen` |
| `gherkin_terminal_reporter` | `plugin/gherkin_terminal_reporter/` | `formatters` |
| `scenario_reporter` | `plugin/scenario_reporter/` | `formatters` |

### Known Violations to Fix

The SPEC notes: "core layers (model/, steps/, parser/) have compile-time dependencies on plugin implementations (pickle_runner, struct_bdd, gherkin_message_reporter)."

These are layer violations that A4 must detect and A2 must fix:
1. `model/` importing `pickle_runner` or `struct_bdd` symbols → must be resolved via hook/indirection
2. `steps/` importing `pickle_runner` symbols → must be resolved via hook/indirection
3. `parser/` importing `struct_bdd` symbols → must be resolved via hook/indirection

### pyproject.toml Optional Dependencies Structure

```toml
[project.optional-dependencies]
formatters = [
    # All 10 formatter plugins — auto-load when installed
]
struct-bdd = [
    "hjson", "json5", "pyhocon", "tomli", "PyYAML", "types-PyYAML"
]
allure = [
    "allure-python-commons"
]
code-gen = [
    # code_generator plugin
]
go-parser = [
    # Go parser — NEW for A3
]
```

Core plugins remain in main `[project.dependencies]` and their entry points stay in `[project.entry-points.pytest11]`. Extra plugin entry points ALSO stay in `[project.entry-points.pytest11]` — they auto-load when the extra is installed (D-14).

## A3: Go Parser Extraction — Implementation Mechanics

### Current Integration Point

`collector_batch.py` uses the Go parser via:
```python
# src/pytest_bdd/scenario_locator.py line ~179-181 (indirectly through parser.py)
# parser.py line 20: from gherkin.parser import Parser as CucumberIOBaseParser
# With go backend: from pytest_bdd._gherkin_go import parse
```

### Extraction Steps

1. **Move `_gherkin_go/` to separate package:** The 4 Python files (`__init__.py`, `_bridge.py`, `_build.py`, `_types.py`) and Go source (`gherkin_go/bridge/bridge.go`, `gherkin_go/go.mod`, `gherkin_go/vendor/`) move to an optional extra.

2. **Create `go-parser` extra in pyproject.toml:**
```toml
[project.optional-dependencies]
go-parser = [
    # Go runtime is NOT a Python dep — the shared lib is built separately
    # The extra only controls whether the Python bridge is installed
]
```

3. **Python fallback pattern in main package:**
```python
# Replace direct import in collector_batch.py/scenario_locator.py with:
def _resolve_parser(backend: str = "auto"):
    if backend == "go":
        try:
            from pytest_bdd._gherkin_go import parse
            return parse
        except ImportError:
            raise ImportError("go-parser extra not installed")
    # auto or python
    try:
        from pytest_bdd._gherkin_go import parse
        return parse
    except ImportError:
        from gherkin.parser import Parser
        return Parser().parse
```

4. **Setuptools build command:** The `BuildGoCommand` stays in the extra package. Only triggers when `go-parser` extra is installed AND Go toolchain is available.

5. **CI:** Build two wheels — one without Go (`pip install pytest-bdd`) and one with Go (`pip install pytest-bdd[go-parser]`). The Go parser wheel is a separate artifact.

6. **Benchmark verification:** Must confirm ≥2× speedup with Go parser (A3 acceptance criterion). Run the existing benchmark or create a simple parse-time measurement script.

### Package Data Changes

```toml
# Remove from main package data:
# "pytest_bdd._gherkin_go" = ["*.so", "*.dll", "*.dylib"]  # REMOVE

# Add to go-parser extra package data (if using setuptools extras plugin)
```

### Risk: Go v39 Compatibility

The current Go module uses `github.com/cucumber/gherkin/go/v28`. The SPEC allows bumping to v39 "if it doesn't break the cgo bridge." The bridge is minimal (113 lines of Go, 3 C exports). Risk assessment:
- **Low risk:** The bridge only calls `gherkin.ParseGherkinDocument()` and `json.Marshal()`. These APIs are stable across gherkin versions.
- **Skip condition:** If v39 changes the cgo-compatible function signatures or the JSON output format, skip the bump. v28 is acceptable.

## A4: Layer Definition — Detailed Model

### Proposed Layer Hierarchy (Bottom-Up)

```
Layer 0: FOUNDATION
  Modules: compatibility/, types/, const.py, mimetype.py, _ruff/
  Deps: stdlib only
  → No project-internal imports allowed

Layer 1: UTILITY
  Modules: util/ (all sub-modules)
  Deps: FOUNDATION
  → May import from FOUNDATION only

Layer 2: PARSING
  Modules: parser.py, parsers.py, collector_batch.py, _gherkin_go/
  Deps: FOUNDATION, UTILITY
  → May import from FOUNDATION, UTILITY; NOT from MODEL or above

Layer 3: MODEL
  Modules: model/ (all sub-modules)
  Deps: FOUNDATION, UTILITY
  → May import from FOUNDATION, UTILITY; NOT from PARSING, RUNTIME, or above
  → EXCEPTION: model/ may import gherkin for pickle compilation (upward to PARSING is acceptable for data types)

Layer 4: STEP DEFINITION
  Modules: steps/ (all sub-modules), hook.py
  Deps: FOUNDATION, UTILITY, PARSING, MODEL
  → May import from any lower layer

Layer 5: COLLECTION
  Modules: collector.py, feature_locator.py, scenario_locator.py, scenario.py
  Deps: FOUNDATION, UTILITY, PARSING, MODEL, STEP DEFINITION
  → May import from any lower layer

Layer 6: RUNTIME
  Modules: plugin/pickle_runner/, plugin/scenario_test_collector/
  Deps: FOUNDATION, UTILITY, PARSING, MODEL, STEP DEFINITION, COLLECTION
  → May import from any lower layer

Layer 7: REPORTING
  Modules: plugin/gherkin_message_reporter/, plugin/cucumber_*/, plugin/gherkin_terminal_reporter/, plugin/scenario_reporter/
  Deps: all lower layers
  → May import from any lower layer; NOT from other reporting plugins (cross-plugin = BLQ1002)

Layer 8: EXTRA PLUGINS
  Modules: plugin/struct_bdd/, plugin/code_generator/, plugin/allure_logger/
  Deps: all lower layers
  → May import from any lower layer; NOT from other extra plugins
```

### TOML Config Schema (D-11)

```toml
# docs/architecture/layers.toml
[layers.foundation]
order = 0
modules = [
    "pytest_bdd.compatibility",
    "pytest_bdd.types",
    "pytest_bdd.const",
    "pytest_bdd.mimetype",
    "pytest_bdd._ruff",
]
allowed_imports = []  # stdlib only
description = "No project-internal imports allowed"

[layers.utility]
order = 1
modules = ["pytest_bdd.util"]
allowed_imports = ["foundation"]
description = "Shared helpers; may import from foundation only"

[layers.parsing]
order = 2
modules = [
    "pytest_bdd.parser",
    "pytest_bdd.parsers",
    "pytest_bdd.collector_batch",
    "pytest_bdd._gherkin_go",
]
allowed_imports = ["foundation", "utility"]
description = "Gherkin parsing; may import from foundation and utility"

# ... etc for remaining layers
```

### Enforcement Rule (layer_rules.py)

The rule:
1. Reads `docs/architecture/layers.toml` at runtime
2. For each Python file, determines its layer by matching module prefix
3. For each `ast.Import`/`ast.ImportFrom` in the file, determines the imported module's layer
4. If imported module's layer is NOT in the current layer's `allowed_imports`, report BLQ1301 (downward import) or BLQ1302 (horizontal import within same layer across plugin boundaries)

### Expected Initial Violations

Based on the SPEC note about "core layers have compile-time dependencies on plugin implementations":
- `model/` importing from `pickle_runner`: ~3-5 violations → fixed via hook indirection in A2
- `steps/` importing from `pickle_runner`: ~2 violations → fixed via hook indirection in A2
- `parser/` importing from `struct_bdd`: ~1 violation → fixed via hook indirection in A2
- `compatibility/` importing from `util/`: legitimate (FOUNDATION → UTILITY is downward by strict ordering, but compatibility IS a special case) → TOML config must allow this

## D0: Object Map Implementation

### Scoring Script Design

`scripts/collect_arch_scores.py`:
1. Walks `src/pytest_bdd/` directory tree
2. For each `.py` file, parses AST to find top-level classes and functions
3. Reads docstrings for `#arch-eval:score=<criterion>=<N>` tags
4. Aggregates scores per object, module, and package
5. Outputs `docs/architecture/OBJECT_MAP.md` with summary table

### Wave 1 Scope (Phase Gate)

Wave 1 covers the public API surface:
- `pytest_bdd.__init__` (8 exports: scenario, scenarios, given, when, then, step, FeaturePathType, PytestBDDStepDefinitionWarning)
- `pytest_bdd.scenario` module
- `pytest_bdd.steps` module
- `pytest_bdd.parsers` module (StepParser ABC + 7 implementations)
- `pytest_bdd.hook` module
- `pytest_bdd.types` (public types only)

### Score Tag Format

```python
@define
class Run:
    """
    Session-scoped container for BDD test run state.

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:4
    #arch-eval:score=why_not_inline:5
    #arch-eval:score=why_not_split:4
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:4
    #arch-eval:score=module_location:5
    """
```

## D2: ADR Template and Numbering

### ADR Template

```markdown
# ADR-001: Use attrs over stdlib dataclasses

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

[What is the issue that we're seeing that is motivating this decision or change?]

## Decision

[What is the change that we're proposing and/or doing?]

## Consequences

[What becomes easier or more difficult to do because of this change?]

### Positive
- ...

### Negative
- ...

### Neutral
- ...
```

### 10 ADR Topics (from SPEC D2)

| # | Title | Covers |
|---|-------|--------|
| 001 | attrs vs dataclass | Project convention; why `@define` over `@dataclass` |
| 002 | StashBound pattern | pytest.config.stash access pattern; why not direct stash access |
| 003 | 3-file plugin structure | entrypoint.py + hook.py + plugin.py per plugin |
| 004 | Cucumber Messages as bus | Why NDJSON protocol; why not custom format |
| 005 | Go cgo parser | Build-time optional performance optimization |
| 006 | Test group ordering | Semantic test groups for CI optimization |
| 007 | No return None policy | Quality gate BLQ901; use Maybe/Result instead |
| 008 | pytest.config.stash runtime state | Session-scoped state management |
| 009 | Feature batch parsing | Lazy-batched async parsing for performance |
| 010 | Pickle runner isolation | Per-scenario state machine; isolation guarantees |

### Timeline: Written During Architecture (D-04)

| Architecture Task | ADR Written | Timing |
|-------------------|-------------|--------|
| A4 (layer definition) | ADR-001 (attrs), ADR-002 (StashBound), ADR-003 (plugin structure) | Before A4 implementation |
| A2 (plugin audit) | ADR-004 (Messages bus), ADR-007 (no return None) | Before A2 audit |
| A3 (Go extraction) | ADR-005 (Go parser) | Before A3 extraction |
| A1 (file splits) | ADR-006 (test grouping), ADR-008 (stash state), ADR-009 (batch parsing), ADR-010 (pickle runner) | Before A1 splits |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | All | ✓ | 3.14 (uv) | — |
| uv | Package management | ✓ | (present) | pip |
| mypy | T0-T2 typing | ✗ (not in current venv) | — | Install via `uv sync --extra testtypes` |
| ruff | Linting, formatting | ✓ | 0.15.15 (pre-commit) | — |
| Go 1.21+ | A3 Go parser build | ✗ (not checked) | — | Python fallback parser; Go parser build is optional |
| gcc/clang | A3 cgo compilation | ✗ (likely not on Windows) | — | Go parser skipped if C compiler unavailable |
| sphinx | D1 docs build | ✓ | ≥7.0 (in doc-gen extra) | — |
| Node.js | Formatter bridge | ✓ (pre-commit uses 22.0.0) | — | Not needed for phase 20 docs |
| Git | Source control | ✓ | — | — |

**Missing dependencies with no fallback:**
- `mypy` not in current venv — install with `uv sync --extra testtypes`
- Python packages `pyright`, `ty`, `pytype` for T0 comparison — install temporarily, remove after report

**Missing dependencies with fallback:**
- Go 1.21+ — A3 extraction builds Go parser as optional; Python fallback handles absence
- C compiler — Go parser build skips gracefully when C compiler unavailable

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥7.0.0 (project's own framework) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run python -m pytest tests/cases/unit -m unit -q` |
| Full suite command | `uv run python -m pytest tests/cases -m "not slow and not docker and not browser"` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| T0 | Type checker comparison report | manual (report output) | N/A — comparison is research | ❌ Wave 0 |
| T1 | Zero ignore_missing_imports after stubs | integration | `uv run python -m mypy --strict src/pytest_bdd` | ❌ Wave 0 (CI gate) |
| T2 | mypy --strict exits 0 | integration | `uv run python -m mypy --strict src/pytest_bdd` | ❌ Wave 0 (CI gate) |
| T3 | typing rule flags bare ignores | unit | `uv run python -m pytest_bdd._ruff.rules.typing_rules src/pytest_bdd` | ❌ Wave 0 |
| A1 | No file exceeds 400 LOC | integration | `uv run python -m pytest_bdd._ruff.rules.file_size_rules src/pytest_bdd` | ❌ Wave 0 |
| A2 | Plugin SRP, lifecycle, core/extra split | unit (plugin check) | `uv run python -m pytest_bdd._ruff.rules.plugin_patterns src/pytest_bdd/plugin` | ✅ (BLQ1001-1003) |
| A3 | Go parser optional; benchmark ≥2× | perf | Benchmark script (new) | ❌ Wave 0 |
| A4 | Zero layer violations | integration | `uv run python -m pytest_bdd._ruff.rules.layer_rules src/pytest_bdd` | ❌ Wave 0 |
| D0 | Object map average ≥ 4.0 | unit (script) | `uv run python scripts/collect_arch_scores.py` | ❌ Wave 0 |
| D1 | make docs builds without warnings | smoke | `make docs` | ❌ Wave 0 |
| D2 | 10 ADRs at docs/adr/ | manual (file check) | `ls docs/adr/*.md | wc -l` | ❌ Wave 0 |
| D3 | 5 guide files at docs/guides/ | manual (file check) | `ls docs/guides/*.md | wc -l` | ❌ Wave 0 |

### Wave 0 Gaps

- [ ] `tests/cases/unit/test_typing_rules.py` — covers T3 rule unit tests
- [ ] `tests/cases/unit/test_file_size_rules.py` — covers A1 rule unit tests
- [ ] `tests/cases/unit/test_layer_rules.py` — covers A4 rule unit tests
- [ ] `tests/cases/unit/test_collect_arch_scores.py` — covers D0 script unit tests
- [ ] `docs/architecture/layers.toml` — layer config for A4 and test fixture
- [ ] `scripts/collect_arch_scores.py` — D0 scoring script
- [ ] Benchmark script for Go parser (A3)
- [ ] Type checker comparison report template (T0)
- [ ] Custom ruff rule test fixtures (per-rule test patterns matching existing `plugin_patterns.py` tests)
- [ ] Framework install: `uv sync --extra testtypes` (for mypy in CI)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A — library, no auth |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Yes (minimal) | T3 type:ignore rule enforces code quality; parsers already use schema validation |
| V6 Cryptography | No | N/A — no cryptographic operations |

### Known Threat Patterns for refactoring phases

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Stale import paths after file splits | Denial of Service (broken imports) | facade.py pattern; full test suite after each split |
| Type confusion after removing ignore_missing_imports | Tampering | mypy --strict gate; CI prevents merge of untyped code |
| Go parser extraction breaking production parsing | Denial of Service | Python fallback parser always available; CI tests both backends |
| Layer enforcement false positives masking real violations | Information Disclosure | TOML-driven config allows tuning; manual review of initial violation list |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| check_untyped_defs only | mypy --strict (15+ flags) | Phase 20 | Catches 10× more type errors; requires full type annotation coverage |
| ignore_missing_imports for 21 packages | Local stubs + types-* packages | Phase 20 | Downstream users can run mypy on code importing pytest-bdd |
| Single-file parsers.py (606 LOC) | parsers/ package with 8 sub-modules | Phase 20 | Better code navigation; each parser independently testable |
| All plugins bundled | core/extra split with [optional-dependencies] | Phase 20 | Smaller install; users only install formatters/allure/struct-bdd when needed |
| Go parser bundled in main package | optional go-parser extra with Python fallback | Phase 20 | pip install pytest-bdd works without Go toolchain |
| No formal architecture documentation | LAYERS.md + OBJECT_MAP.md + 10 ADRs | Phase 20 | New contributors understand architecture in <2 minutes |
| Manual type:ignore enforcement | Custom ruff rule (BLQ11xx) | Phase 20 | All ignores require explanation; bare ignores blocked |
| Custom ruff rules as scripts | (unchanged — same pattern for new rules) | N/A | Proven approach; extends cleanly to 3 new rule files |

**Deprecated/outdated:**
- `ignore_missing_imports = true` for 21 packages: Removed after T1 stubs are in place
- Single-file modules exceeding 400 LOC: Split into sub-packages with facade.py (A1)
- Core-to-plugin compile-time dependencies: Resolved via hook indirection (A2, A4)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | pyright, ty, pytype are installable and runnable on this codebase (T0) | T0 | Low — all are standard pip packages; worst case: some don't work on Windows |
| A2 | 17 of 21 ignore_missing_imports packages have no types-* on PyPI and need local stubs | T1 | Medium — some packages may have added py.typed since last check; re-verify each before creating stubs |
| A3 | 5 named files (parsers, scenario_locator, message_stream_validation, cucumber_formatters, tests_group_ordering) can be split without breaking tests | A1 | Medium — hidden import dependencies may surface; facade.py must be exhaustive |
| A4 | The existing `_ruff/rules/` standalone Python script pattern is correct for all three new rules | T3, A1, A4 | Low — this is the established project convention; confirmed by existing `plugin_patterns.py` and `quality_gates.py` |
| A5 | Core-to-plugin compile-time dependencies (model→pickle_runner, steps→pickle_runner, parser→struct_bdd) can be resolved via hook indirection | A2, A4 | High — these dependencies may be deep architectural coupling that requires significant refactoring; the A2 audit must confirm feasibility before implementation |
| A6 | Go parser extraction via importlib fallback will maintain ≥2× speedup benchmark | A3 | Low — the benchmark compares parse speed, not import speed; importlib overhead is negligible vs parsing time |
| A7 | Sphinx autodoc can generate docs for attrs classes via napoleon extension | D1 | Low — napoleon is already configured and handles attrs `@define` classes correctly |
| A8 | slopcheck unavailable on Windows; all external packages tagged [ASSUMED] | Package Legitimacy | Low — pyright/ty/pytype are well-known Microsoft/Astral/Google projects; types-* packages are from python/typeshed |
| A9 | The 4 remaining oversized files (>400 LOC not in the 5 named targets) can be addressed in A1 scope | A1 | Medium — these files may have different complexity profiles; the planner should add tasks for them |

## Open Questions (RESOLVED)

1. **Core-to-plugin dependency resolution feasibility (A2/A4 boundary)**
   - What we know: SPEC says "core layers (model/, steps/, parser/) have compile-time dependencies on plugin implementations (pickle_runner, struct_bdd, gherkin_message_reporter)"
   - What's unclear: Whether these can be resolved via hook indirection without breaking runtime behavior. Some may be legitimate (e.g., model importing gherkin_message_reporter for message types)
   - Recommendation: A2 audit must produce a violation report listing each import, its justification, and the fix strategy (hook, move to util, or TOML exception). Planner should include a "feasibility gate" task before implementing fixes.

2. **stubs/ directory in setuptools package data**
   - What we know: `stubs/` is at repo root, NOT under `src/`. setuptools `[tool.setuptools.packages.find]` uses `where = ["src"]` so `stubs/` is outside.
   - What's unclear: How to include `stubs/` in the built wheel while keeping `src/` layout. Options: (a) add `stubs` as a top-level package, (b) use MANIFEST.in, (c) use `[tool.setuptools.package-data]` with wildcard path
   - Recommendation: Use approach (a) — add `"stubs"` to `[tool.setuptools.packages.find].where` by listing both `["src", "."]` or explicitly adding `stubs` via `[tool.setuptools.packages]` directive. Planner should research exact setuptools syntax.

3. **ADR-004 (Cucumber Messages) content scope**
   - What we know: 10 ADR topics are locked per SPEC. ADR-004 is "Cucumber Messages as bus."
   - What's unclear: Whether this ADR should cover the full protocol choice (NDJSON, envelope structure, extension points) or just the bus topology. The codebase has extensive message governance (message_capability, message_status_governance, message_stream_validation) that could be separate ADRs.
   - Recommendation: ADR-004 covers the bus decision (why Cucumber Messages protocol). Message governance details go in architecture documentation (LAYERS.md), not a separate ADR.

4. **mypy strict flag `warn_unreachable` inclusion**
   - What we know: SPEC mentions "all mypy --strict flags." The `--strict` flag from current mypy includes `--warn-unreachable` by default in recent versions.
   - What's unclear: Whether `warn_unreachable` is included in the phase scope or optional. The SPEC says "all `--strict` flags enabled" which implies yes.
   - Recommendation: Include `warn_unreachable` as part of T2. It's a low-error-count flag (mostly dead code detection) and improves code quality.

5. **py.typed marker placement**
   - What we know: PEP 561 requires a `py.typed` marker file in the package directory for mypy to recognize inline types. pytest-bdd currently lacks this marker.
   - What's unclear: Whether to place `py.typed` in `src/pytest_bdd/` (enabling downstream mypy to check imports of pytest-bdd) or also in `stubs/` (redundant since stubs are for OTHER packages).
   - Recommendation: Place `py.typed` in `src/pytest_bdd/` only. The `stubs/` directory contains stubs for OTHER packages; its consumers use `mypy_path` to find them. `py.typed` in `src/pytest_bdd/` signals that the pytest-bdd package itself has inline type annotations.

## Sources

### Primary (HIGH confidence)
- [Context7: /websites/mypy_readthedocs_io_en] — mypy --strict flags list, PEP 561 stub packaging, stubgen usage
- [Context7: /python/mypy] — Creating stubs, MYPYPATH, py.typed marker, installed packages
- [Context7: /astral-sh/ruff] — Custom lint rules, AST visitor pattern, rule naming conventions
- [Context7: /websites/sphinx-doc_en_master] — autodoc setup, automodule directives, autofunction/autoclass usage
- [Project source: src/pytest_bdd/_ruff/rules/plugin_patterns.py] — Existing custom rule blueprint (BLQ1001-BLQ1003)
- [Project source: src/pytest_bdd/_ruff/rules/quality_gates.py] — Second rule file confirming pattern (BLQ901-BLQ902)
- [Project source: pyproject.toml] — Current mypy config, 21 ignore_missing_imports, ruff rules, entry points
- [Project source: _gherkin_go/] — Go parser bridge, build system, integration point
- [Project source: docs/conf.py] — Sphinx config with autodoc, napoleon, myst_parser already configured
- [Project source: .pre-commit-config.yaml] — Pre-commit hook structure for new rules

### Secondary (MEDIUM confidence)
- [STACK.md] — Technology stack and dependency categorization
- [ARCHITECTURE.md] — Layer structure, data flow, plugin architecture
- [CONVENTIONS.md] — Code style, import patterns, attrs usage, from __future__ import annotations
- [Makefile] — Project command boundary; build and test targets
- [Grep: type:ignore] — 93 verified type:ignore comments with error codes

### Tertiary (LOW confidence)
- [ASSUMED] pyright, ty, pytype availability and behavior on this specific codebase
- [ASSUMED] Exact error counts per mypy strict flag (estimated 250-300 total)
- [ASSUMED] 17 packages without any type support (verified via pip index; may change)
- [ASSUMED] Go v39 compatibility with existing cgo bridge (untested)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools are project-established (mypy, ruff, sphinx, setuptools); new tools are well-known (pyright, pytype)
- Architecture: HIGH — codebase extensively mapped; existing patterns (ruff rules, plugin structure, parser organization) provide clear blueprints
- Pitfalls: MEDIUM — identified pitfalls are common in multi-dimensional refactoring phases; some are speculative (over-stubbing, stale imports) but grounded in ecosystem experience

**Research date:** 2026-06-08
**Valid until:** 2026-07-08 (30 days — stable tools; stubs and types-* availability may change)
