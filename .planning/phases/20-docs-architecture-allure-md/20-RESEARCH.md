# Phase 20: Allure-Cucumber Converter - Research

**Researched:** 2026-06-09
**Domain:** BDD test reporting / Cucumber Messages → Allure3 JSON conversion
**Confidence:** HIGH

## Summary

Phase 20 implements the Allure-Cucumber Converter defined in `docs/architecture/allure.md` — a schema-driven, standalone NDJSON-to-Allure-JSON converter that bridges the Cucumber Messages protocol with Allure3 reporting. Unlike existing pytest-bdd plugins that operate as runtime hooks during test execution, this converter is a **post-execution, file-in/file-out library** that works with NDJSON output from any cucumber runner (Python, Java, JS, etc.).

The architecture document defines 3 sequential sub-phases (JSONSchema extraction → allure-python-commons extension → converter mapping), plus 3 delivery artifacts (core library, CLI entry point, pytest plugin wrapper), and 2 layers of testing (schema validation + Playwright/Docker HTML validation). This is by far the largest and most complex phase in the v1 milestone, requiring new test dependencies (factoryboy, hypothesis), optional Docker/Playwright infrastructure, and a ~19th pytest11 plugin that follows the canonical 3-file pattern.

**Primary recommendation:** Break Phase 20 into 5 waves: (1) Schema Foundation — extract and commit canonical Allure3 JSONSchema, (2) Converter Core — implement NDJSON-to-Allure-JSON mapping, (3) Plugin + CLI Wrappers — canonical plugin + console_scripts, (4) Layer 1 Testing — schema validation with factoryboy/hypothesis, (5) Documentation + Final Verification. Wave 4 Layer 2 (Playwright/Docker HTML validation) should be deferred or made optional due to infrastructure complexity.

**Key risk:** The step hierarchy reconstruction (cucumber's flat `TestStepStarted/Finished` pairs → Allure's nested step tree) is the hardest mapping and the architecture doc explicitly calls this out. This mapping must handle interleaved hooks and background steps.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| NDJSON parsing (Cucumber Messages) | Converter Core | ExecutionMessageAdapter | Converter reads NDJSON files; adapter provides typed deserialization already |
| Allure JSON emission | Converter Core | — | Converter writes JSON directly against committed schema, not via allure-python-commons |
| Step hierarchy reconstruction | Converter Core | — | Flat cucumber events → nested Allure steps; purely algorithmic |
| Schema validation (Layer 1) | Testing | jsonschema (stdlib) | Validate converter output against committed schema; pure Python, no Docker |
| HTML validation (Layer 2) | Testing (optional) | Playwright + Docker | Containerized Allure3 → Playwright validates rendered HTML |
| pytest integration | Plugin Wrapper | entrypoint.py | Thin `pytest_sessionfinish` hook calling converter |
| CLI entry point | console_scripts | argparser | `allure-cucumber messages.ndjson --output allure-results/` |
| Schema extraction (Phase 1) | Research/Script | Schema comparison tooling | Read schemas from 5 implementations; commit canonical merged schema |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `cucumber-messages` | 32.2.0 (existing) | Cucumber Messages NDJSON parsing | Already in project deps; ExecutionMessageAdapter wraps it [VERIFIED: project pyproject.toml] |
| `jsonschema` | existing | Allure3 Events Schema validation | Already in project deps; used for Layer 1 testing [VERIFIED: project pyproject.toml] |
| `attrs` | existing | Data classes for converter model | Project convention; AGENTS.md mandates attrs over dataclasses [VERIFIED: project AGENTS.md] |
| `returns` | existing | Maybe type for optional values | Already used throughout model layer [VERIFIED: project pyproject.toml] |

### Supporting (Test)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `factoryboy` | [ASSUMED] latest | Generate varied NDJSON test fixtures | Layer 1 schema validation testing [ASSUMED] |
| `hypothesis` | [ASSUMED] latest | Property-based invariant testing | Layer 1: "any valid cucumber message NDJSON produces valid Allure JSON or documented error" [ASSUMED] |
| `playwright` | [ASSUMED] latest | Browser automation for Layer 2 | Layer 2 HTML validation (optional/deferred) — project already has `test-playwright` extra [ASSUMED] |
| `pydantic` | ≥2.0.3 (existing) | Schema/model validation | Already in deps; could model Allure JSON types [VERIFIED: project pyproject.toml] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom NDJSON parser | ExecutionMessageAdapter (existing) | Adapter already handles deserialization, namespacing, rewriting — no need to build |
| allure-python-commons for emission | Direct JSON emission against schema | Architecture doc explicitly says converter emits JSON directly; commons fork is for gap analysis only |
| Custom schema system | jsonschema + pydantic | jsonschema already in deps, pydantic for typed models |

**Installation additions needed:**
```bash
# For Layer 1 testing (should be added to test extra or new allure-converter extra):
pip install factoryboy hypothesis

# For Layer 2 testing (optional, in test-playwright extra already):
# playwright is already in test-playwright optional dependency
```

**Version verification:**
```bash
pip index versions cucumber-messages    # Currently installed: 32.2.0 [VERIFIED]
pip index versions jsonschema           # Already in project deps [VERIFIED: pyproject.toml]
pip index versions factory-boy          # NOT yet in deps [ASSUMED]
pip index versions hypothesis           # NOT yet in deps [ASSUMED]
```

## Package Legitimacy Audit

> **Required** whenever this phase installs external packages.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `factory-boy` | PyPI | [ASSUMED] 10+ yrs | [ASSUMED] 10M+/month | github.com/FactoryBoy/factory_boy | [ASSUMED] | Approved — well-established test fixture library |
| `hypothesis` | PyPI | [ASSUMED] 10+ yrs | [ASSUMED] 10M+/month | github.com/HypothesisWorks/hypothesis | [ASSUMED] | Approved — well-established property-based testing |
| `playwright` | PyPI | [ASSUMED] 5+ yrs | [ASSUMED] 5M+/month | github.com/microsoft/playwright-python | [ASSUMED] | Approved — already in project test-playwright extra |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*slopcheck was not available at research time — all packages above are tagged `[ASSUMED]` and the planner must gate each install behind a `checkpoint:human-verify` task.*

## Architecture Patterns

### System Architecture Diagram

```
┌──────────────────────┐     ┌──────────────────────────────┐     ┌──────────────────────┐
│  Cucumber Runner     │     │   Allure-Cucumber Converter   │     │   Allure3            │
│  (any lang/runtime)  │────▶│   (standalone, file-in/file-out)│────▶│   (report generator) │
│                      │     │                              │     │                      │
│  produces:           │     │  1. Read NDJSON               │     │   reads:              │
│  messages.ndjson     │     │  2. Parse via Adapter         │     │   allure-results/*.json│
└──────────────────────┘     │  3. Map events → Allure JSON  │     └──────────────────────┘
                              │  4. Reconstruct step tree     │
                              │  5. Emit to allure-results/   │
                              └──────────────────────────────┘
                                       │
                          ┌────────────┼────────────┐
                          │            │            │
                    ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │ Core Lib │ │   CLI    │ │  pytest  │
                    │ (converter│ │ (allure- │ │  plugin  │
                    │  package) │ │ cucumber)│ │ (wrapper)│
                    └──────────┘ └──────────┘ └──────────┘
```

### Data Flow (Converter Internal)

```
messages.ndjson
      │
      ▼
┌─────────────────────┐
│ Read NDJSON lines    │  ← Each line = cucumber_messages.Envelope (JSON)
│ (1 line = 1 envelope)│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ ExecutionMessageAdapter │  ← Existing: deserialize_dict() → ExecutionProjection
│ .deserialize_dict() │     ← Returns typed payload with kind introspection
└────────┬────────────┘
         │ [list of ExecutionProjection]
         ▼
┌─────────────────────┐
│ Event Collector      │  ← Group envelopes by testCaseStartedId → scenario
│ (build scenario map) │     Track TestCase/TestStep/Attachment ownership
└────────┬────────────┘
         │ [grouped event map]
         ▼
┌─────────────────────┐
│ Step Tree Builder    │  ← THE HARD PART: flat TestStepStarted/Finished pairs
│ (reconstruct         │     → nested Allure step hierarchy
│  hierarchy)          │     Must handle hooks, background steps interleaved
└────────┬────────────┘
         │ [hierarchical step tree per scenario]
         ▼
┌─────────────────────┐
│ Mapping Engine       │  ← Apply Cucumber → Allure mapping rules
│ (event → result JSON)│     - TestCaseStarted → TestResult
│                      │     - TestStep → TestStepResult
│                      │     - Attachment → Attachment
│                      │     - Unmappable → structured metadata
└────────┬────────────┘
         │ [Allure model objects]
         ▼
┌─────────────────────┐
│ JSON Serializer      │  ← Serialize to Allure result format
│ (emit to disk)       │     *-result.json, *-container.json, *-attachment.*
└────────┬────────────┘
         │
         ▼
allure-results/
├── abc123-result.json
├── def456-result.json
├── ghi789-container.json
└── ...
```

### Recommended Project Structure

```
src/pytest_bdd/plugin/allure_cucumber/
├── __init__.py                    # Package init
├── entrypoint.py                  # pytest11 registration
├── plugin.py                      # AllureCucumberPlugin (StashBound)
├── hook.py                        # Hook specification class
├── cli.py                         # console_scripts entry point (allure-cucumber)
└── converter/
    ├── __init__.py                # Public converter API
    ├── reader.py                  # NDJSON → ExecutionProjection stream
    ├── collector.py               # Group envelopes by testCase
    ├── step_tree.py               # Flat step pairs → nested hierarchy
    ├── mapper.py                  # Cucumber Messages → Allure model mapping
    ├── emitter.py                 # Allure model → JSON files on disk
    └── model.py                   # Allure result model types (attrs)
```

**Why this structure:**
- `converter/` subpackage keeps the core logic decoupled from pytest — callable from CLI, plugin, or standalone scripts
- `cli.py` at plugin level (not in converter) follows `render_cucumber_formatters` precedent — CLI entry points call into plugin infrastructure
- `entrypoint.py` + `plugin.py` + `hook.py` follows the canonical 3-file plugin pattern enforced by `test_plugin_structure_contract.py`
- `model.py` uses `attrs` (AGENTS.md mandate), stores Allure event types

### Pattern 1: Canonial 3-File Plugin Structure

**What:** Every pytest11 plugin must have `entrypoint.py`, `plugin.py`, `hook.py`

**Source:** `tests/cases/contract/contract/test_plugin_structure_contract.py` [VERIFIED]

**Example (from cucumber_json_formatter):**
```python
# entrypoint.py — minimal: instantiate plugin class
from .plugin import JsonFormatterPlugin
json_plugin = JsonFormatterPlugin()

# plugin.py — plugin class (may extend StashBound or FormatterReporterPlugin)
from pytest_bdd.util.cucumber_formatter_support.base import FormatterReporterPlugin

class JsonFormatterPlugin(FormatterReporterPlugin):
    output_mode = FormatterOutputMode.path
    def __init__(self):
        super().__init__(...)

# hook.py — canonical placeholder
"""
Hook specifications for the cucumber json formatter plugin.
This module is a canonical package-structure placeholder so source contracts can
require every pytest11 plugin package to provide an explicit hook surface.
"""
```

### Pattern 2: ExecutionMessageAdapter for NDJSON Parsing

**What:** Use `ExecutionMessageAdapter.deserialize_dict()` to parse NDJSON line dicts into typed `ExecutionProjection` objects with payload introspection.

**Source:** `src/pytest_bdd/model/execution_message_adapter.py` [VERIFIED]

**Example:**
```python
from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_extension import EventEnvelope, get_payload_kind

# Read NDJSON, parse each line:
with open("messages.ndjson") as f:
    for line in f:
        envelope_dict = json.loads(line)
        projection = ExecutionMessageAdapter.deserialize_dict(envelope_dict)
        # projection.payload_kind → "test_case_started", "test_step_finished", etc.
        # projection.payload → typed cucumber_messages object
        # projection.payload_id → string ID for cross-referencing
```

### Pattern 3: console_scripts Entry Point

**What:** CLI commands registered in `pyproject.toml` under `[project.scripts]`, pointing to a `main()` function.

**Source:** `pyproject.toml` lines 170-172 [VERIFIED]

**Example:**
```toml
[project.scripts]
allure-cucumber = "pytest_bdd.plugin.allure_cucumber.cli:main"
```

```python
# cli.py
import argparse
from pathlib import Path
from .converter import convert

def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert Cucumber Messages NDJSON to Allure results")
    parser.add_argument("messages_ndjson", type=Path, help="Path to messages.ndjson")
    parser.add_argument("--output", type=Path, default=Path("allure-results"),
                        help="Output directory for Allure result JSON files")
    args = parser.parse_args(argv)
    convert(args.messages_ndjson, args.output)
```

### Pattern 4: StashBound for Plugin Configuration

**What:** Plugin configuration stored in `pytest.config.stash` using `StashBound` base class.

**Source:** `src/pytest_bdd/model/stash_access.py`, `DEVELOPMENT.rst` lines 191-228 [VERIFIED]

**Example:**
```python
from attrs import define
from pytest_bdd.model.stash_access import StashBound

@define
class AllureCucumberConfig(StashBound):
    STASH_KEY = "allure-cucumber:config"
    output_dir: str = "allure-results"
    messages_path: str | None = None
```

### Pattern 5: attrs for Data Classes

**What:** Use `@define` from `attrs`, NOT stdlib `dataclass`.

**Source:** AGENTS.md line 92, DEVELOPMENT.rst lines 232-248 [VERIFIED]

### Anti-Patterns to Avoid

- **Importing from other plugins directly:** Cross-plugin communication must go through pytest hooks or shared model modules. The converter is in `allure_cucumber/converter/` (not a separate plugin).
- **Using `return None` in non-hook code:** Phase 2 quality gate. Use sentinels or `Maybe` from `returns`.
- **Using bare `except Exception:`:** Use specific exception types or `logger.warning(exc_info=True)` (STAB-03 compliance).
- **Using `dataclass` instead of `attrs`:** AGENTS.md mandates `attrs` for all data classes.
- **Making the converter a runtime hook:** Architecture doc explicitly states the converter is a post-execution file-in/file-out tool, not a pytest-bdd runtime hook. The pytest plugin wrapper is a thin integration layer.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| NDJSON parsing and cucumber message deserialization | Custom JSON + type checking | `ExecutionMessageAdapter.deserialize_dict()` | Already handles all cucumber-messages types, payload introspection, ID rewrites, namespacing |
| JSON Schema validation | Custom validation logic | `jsonschema` (already in deps) | Standard library, handles draft-07/2019-09/2020-12, produces structured errors |
| Cucumber message types/enums | Custom wrappers | `cucumber_messages` library + `message_extension.py` | Already imported, extended with pytest-bdd-specific types |
| JSON serialization of attrs objects | Manual dict conversion | `attrs.asdict()` + `cattrs` or manual | attrs built-in for simple cases; `cattrs` for structured un/structuring |
| CLI argument parsing | Manual sys.argv | `argparse` (stdlib) | Simple CLI; follow `render_cucumber_formatters` precedent |

**Key insight:** The project already has a rich message handling infrastructure (`ExecutionMessageAdapter`, `message_converter`, `message_extension`, `message_registry`). Building a custom NDJSON parser would duplicate significant logic. The converter should be a thin mapping layer on top of this existing infrastructure.

## Runtime State Inventory

> Omitted — Phase 20 is a greenfield implementation with no existing runtime state to migrate. No stored data, live service config, OS-registered state, secrets, or build artifacts carry allure-related content (verified: `grep -r allure src/` returned zero results in production code).

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — verified by grep audit | N/A |
| Live service config | None | N/A |
| OS-registered state | None | N/A |
| Secrets/env vars | None | N/A |
| Build artifacts | None | N/A |

## Common Pitfalls

### Pitfall 1: Step Hierarchy Reconstruction

**What goes wrong:** Cucumber emits flat `TestStepStarted`/`TestStepFinished` event pairs. Allure3 expects explicitly nested step trees (`TestResult.steps[i].steps[j]`). Without proper reconstruction, all steps appear as siblings and the Allure report loses the BDD scenario structure (Given → When → Then grouping).

**Why it happens:** The cucumber messages protocol represents steps as a chronological flat stream, not a tree. Hooks, background steps, and regular steps are interleaved. The converter must track `testStepId` → parent relationships by examining the `pickle_step_id` references.

**How to avoid:** Build a stack-based tree builder. Track `testCaseStartedId` → `TestCase`, then for each `TestStepStarted`:
1. Push step onto the current branch's stack
2. When `TestStepFinished` arrives, pop from stack
3. Use `testStepId` parent references from the pickle to determine nesting

**Warning signs:** All steps at same depth in Allure report, background steps not grouped, hook steps appearing as regular steps.

### Pitfall 2: Unmappable Events — Silent Data Loss

**What goes wrong:** Some cucumber messages event types have no direct Allure3 analog (e.g., `parse_error`, `undefined_parameter_type`). Silently dropping these loses valuable debugging context.

**Why it happens:** The Allure3 event model is designed for test execution results, not for cucumber's full protocol surface area.

**How to avoid:** Encode unmappable events as structured attachments or metadata on the parent test result. Use `TestResult.attachments` with descriptive names. Never skip an event without explicit documentation of the mapping decision.

**Warning signs:** Declining to handle event types without documenting why, `pass` in mapping branches.

### Pitfall 3: Plugin Count Contract Mismatch

**What goes wrong:** `test_plugin_structure_contract.py` asserts `EXPECTED_PLUGIN_COUNT = 18`. Adding the 19th plugin without updating this constant breaks CI.

**Why it happens:** The contract test is an explicit gate; forgetting to bump the count is a common oversight when adding a new plugin.

**How to avoid:** Update `EXPECTED_PLUGIN_COUNT = 19` in the same wave that adds the `pytest11` entry point.

### Pitfall 4: Schema Extraction Scope Creep

**What goes wrong:** The architecture doc's "Phase 1: JSONSchema extraction and comparison" involves extracting schemas from 5 different implementations (allure-java, allure-js, allure-python, allure2, allure3). This could become a multi-week research project on its own, blocking all downstream work.

**Why it happens:** Each implementation has its own schema representation (Java annotations, TypeScript interfaces, Python attrs, JSON Schema files). Extracting, normalizing, comparing, and merging these is research-intensive.

**How to avoid:** Scope schema extraction to the canonical Allure3 reader source-of-truth (the TypeScript-based reader in allure3 repo). Use the other 4 implementations for comparison/gap analysis only. If the allure3 reader doesn't have an explicit JSONSchema file, extract one from the TypeScript types using a tool or manual transcription. The architecture doc says "Allure3 is the canonical target consumer" — prioritize its schema.

## Code Examples

Verified patterns from the project codebase:

### Reading Cucumber Messages NDJSON
```python
# Source: src/pytest_bdd/model/execution_message_adapter.py [VERIFIED]
# Pattern: deserialize_dict() for parsing NDJSON line dicts into typed projections

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter

envelope_dict = json.loads(line)  # one NDJSON line
projection = ExecutionMessageAdapter.deserialize_dict(envelope_dict)
# projection.payload_kind → e.g., "test_case_started"
# projection.payload → typed cucumber_messages.TestCaseStarted
# projection.payload_id → e.g., "abc-123"
```

### Serializing Envelopes to Dict
```python
# Source: src/pytest_bdd/model/execution_message_adapter.py [VERIFIED]
# Pattern: serialize_to_dict() for converting envelopes to JSON-compatible dicts

from pytest_bdd.model.message_serialization import MessageSerializationProfile

envelope_dict = ExecutionMessageAdapter.serialize_to_dict(
    envelope,
    profile=MessageSerializationProfile.extended,
)
```

### StashBound Plugin Config
```python
# Source: DEVELOPMENT.rst lines 208-228 [VERIFIED]
# Pattern: StashBound subclass for plugin configuration storage

from attrs import define
from pytest_bdd.model.stash_access import StashBound

@define
class AllureCucumberConfig(StashBound):
    STASH_KEY = "allure-cucumber:config"
    output_dir: str = "allure-results"

# In pytest_configure:
def pytest_configure(config):
    cfg = AllureCucumberConfig(output_dir="allure-results")
    cfg.initialize_in_stash(config.stash)
```

### pytest11 Entry Point Registration
```python
# Source: pyproject.toml lines 91-109 [VERIFIED]
# Pattern: Module-level plugin instance in entrypoint.py

# pyproject.toml:
# [project.entry-points.pytest11]
# "pytest-bdd-allure-cucumber" = "pytest_bdd.plugin.allure_cucumber.entrypoint"

# entrypoint.py:
from .plugin import AllureCucumberPlugin
allure_cucumber_plugin = AllureCucumberPlugin()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| allure-python-commons for emission | Direct JSON emission against Allure3 schema | Architecture doc decision | Converter is library-independent; commons fork only for gap analysis |
| Runtime hook-based Allure integration | Post-execution file-in/file-out converter | Architecture doc decision | Works with any cucumber runner, not just pytest-bdd |
| Dead Allure logger plugin (Phase 1 removed) | New schema-driven converter | Phase 20 | Clean slate — no legacy allure code to migrate |
| Allure2 result format | Allure3 result format | Architecture doc targets Allure3 | Must verify Allure3 backward compat with Allure2 format |

**Deprecated/outdated:**
- **allure-python-commons `allure_commons.model2`**: The allure-python-commons library uses `attrs` v1 API (`attr.attrs` / `attr.attrib`) which is incompatible with modern `attrs` (v23+). The architecture doc says to vendor a copy and apply patches — this needs careful dependency isolation.
- **Allure2-specific schemas**: The architecture doc says Allure3 is the canonical target consumer. Allure2 schemas are extracted for comparison only.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `factoryboy` and `hypothesis` are the right test fixture/property-testing libraries for Layer 1 | Standard Stack | Low — both are well-established; alternatives exist (e.g., `pytest-factoryboy`, `pytest-subtests`) |
| A2 | Allure3 reader can consume Allure2-format result JSON files without modification | Architecture Patterns | Medium — if Allure3 requires a different format, the converter must target that format. The architecture doc calls out allure3 as canonical |
| A3 | The Allure3 TypeScript reader has extractable JSONSchema or TypeScript types that can be transcribed to JSON Schema | Common Pitfalls #4 | Medium — if the schema is only in code, manual transcription is needed; adds significant effort |
| A4 | `cucumber-messages` v32.2.0 includes all event types needed for the mapping (TestCaseStarted, TestStepStarted, Attachment, etc.) | Don't Hand-Roll | Low — these are core cucumber messages protocol types |
| A5 | The pytest plugin wrapper can be a thin `pytest_sessionfinish` hook that calls the converter | Architecture Patterns | Low — this is the simplest integration point; the converter is standalone |
| A6 | `EXPECTED_PLUGIN_COUNT` bump from 18 to 19 is the only contract test change needed | Common Pitfalls #3 | Low — verified that the test only checks count + structure |

## Open Questions (RESOLVED)

1. **Allure3 JSON Schema availability**
   - What we know: The allure3 repo (`/allure-framework/allure3`) has a reader package that parses result files. The schema may be expressed in TypeScript types rather than explicit JSON Schema files.
   - What's unclear: Whether a canonical JSON Schema file exists in the allure3 repo, or whether we need to extract/transcribe one from TypeScript types.
   - Recommendation: Research the allure3 reader package source during Wave 1. If no explicit schema exists, transcribe from TypeScript types in the reader package. Prioritize the allure3 source-of-truth over other implementations.
   - **RESOLVED:** Wave 1 (Plan 20-01) will research allure3 reader package. If no JSON Schema exists, transcribe from TypeScript types. Decision documented in 20-01-PLAN.md Task 1.

2. **Allure3 backward compatibility with Allure2 result format**
   - What we know: The allure-python-commons `model2.py` defines the Allure2 result format (`*-result.json`, `*-container.json`). The architecture doc says "Allure3 is the canonical target consumer."
   - What's unclear: Whether Allure3's reader accepts this exact format or requires a different format (e.g., single-line NDJSON).
   - Recommendation: Test during Wave 1 by generating a sample `*-result.json` in the current allure2 format and running `npx allure generate` against it. If Allure3 rejects it, examine the reader package to determine the expected format.
   - **RESOLVED:** Wave 1 (Plan 20-01) includes testing Allure3 reader against sample Allure2 format JSON. Deferred to Plan 20-01 Task 1 acceptance criteria.

3. **Scope of Schema Extraction (Phase 1 sub-phase)**
   - What we know: The architecture doc says extract schemas from "5 implementations: allure-java, allure-js, allure-python (producers) and allure2, allure3 (consumers)."
   - What's unclear: How deep the extraction and comparison should go. Full runtime capture from each implementation is expensive.
   - Recommendation: Prioritize allure3 (canonical consumer) and allure-python (closest producer). Extract schemas from the other 3 for gap identification only, not full coverage. See Common Pitfalls #4.
   - **RESOLVED:** Prioritize allure3 + allure-python only. Other implementations for gap identification. Documented in RESEARCH.md Common Pitfalls #4 and Plan 20-01 scope.

4. **factoryboy/hypothesis as test dependencies**
   - What we know: Neither is currently in the project's test extras. The architecture doc explicitly names them for Layer 1 testing.
   - What's unclear: Whether to add them to the existing `test` extra, create a new `allure-converter` extra, or make them dev-only.
   - Recommendation: Add to the `test` extra since they're general-purpose testing tools. If the user prefers isolation, a new `test-allure` extra would also work.
   - **RESOLVED:** Add to existing `test` extra in pyproject.toml. Gated behind human-verify checkpoint in Plan 20-04 Task 0.

5. **Layer 2 (Playwright + Docker) scope**
   - What we know: The architecture doc defines Layer 2 as "Feed Layer 1 outputs through containerized Allure3, Playwright validates rendered HTML report for content correctness."
   - What's unclear: Whether this should be implemented now or deferred as optional. The Docker/Playwright infrastructure adds significant complexity.
   - Recommendation: Defer Layer 2 to a follow-up phase or make it optional (gated behind `@pytest.mark.docker` and `@pytest.mark.browser` markers that already exist in the project). Layer 1 provides sufficient confidence for the converter's correctness.
   - **RESOLVED:** Layer 2 deferred out of Phase 20 scope. Not included in any plan.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Runtime | ✓ | 3.13 (dev env) | — |
| Node.js | Allure3 for Layer 2 testing | ✓ (assumed) | — | Skip Layer 2 tests |
| Docker | Layer 2 Allure3 container | ✓ (assumed) | — | Skip Layer 2 tests |
| playwright | Layer 2 browser testing | ✓ (in test-playwright extra) | — | Skip Layer 2 tests |

**Missing dependencies with no fallback:**
- `factoryboy`, `hypothesis` — need to be added to project dependencies before Layer 1 tests can run

**Missing dependencies with fallback:**
- Docker, Node.js, playwright — only needed for Layer 2 (deferrable)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/cases/contract/allure/ -x` |
| Full suite command | `uv run pytest tests/cases/ -m "not docker and not browser"` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-01 | NDJSON parsing produces typed ExecutionProjection stream | unit | `uv run pytest tests/cases/unit/allure/ -x` | ❌ Wave 0 |
| REQ-02 | Cucumber TestCaseStarted → Allure TestResult with correct UUID, labels, status | contract | `uv run pytest tests/cases/contract/allure/ -x` | ❌ Wave 0 |
| REQ-03 | Flat TestStep pairs reconstructed into nested step hierarchy | unit | `uv run pytest tests/cases/unit/allure/test_step_tree.py -x` | ❌ Wave 0 |
| REQ-04 | Unmappable events encoded as structured attachments (not dropped) | contract | `uv run pytest tests/cases/contract/allure/ -x` | ❌ Wave 0 |
| REQ-05 | Converter output validates against committed allure3-events.schema.json | contract | `uv run pytest tests/cases/contract/allure/test_schema_validation.py -x` | ❌ Wave 0 |
| REQ-06 | Plugin follows canonical 3-file structure (entrypoint + plugin + hook) | contract | `uv run pytest tests/cases/contract/contract/test_plugin_structure_contract.py -x` | ✅ existing |
| REQ-07 | CLI entry point `allure-cucumber` registered in pyproject.toml | contract | `uv run pytest tests/cases/contract/allure/test_cli.py -x` | ❌ Wave 0 |
| REQ-08 | pytest plugin wrapper calls converter at `pytest_sessionfinish` | integration | `uv run pytest tests/cases/integration/allure/test_plugin.py -x` | ❌ Wave 0 |
| REQ-09 | Property-based: any valid NDJSON produces valid Allure JSON or documented error (hypothesis) | contract | `uv run pytest tests/cases/contract/allure/test_hypothesis.py -x` | ❌ Wave 0 |
| REQ-10 | EXPECTED_PLUGIN_COUNT updated to 19 | contract | `uv run pytest tests/cases/contract/contract/test_plugin_structure_contract.py -x` | ✅ existing |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/cases/unit/allure/ -x --ff`
- **Per wave merge:** `uv run pytest tests/cases/contract/allure/ -x && uv run pytest tests/cases/contract/contract/test_plugin_structure_contract.py -x`
- **Phase gate:** Full feasible suite green (`make test`) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/cases/unit/allure/` — unit tests for converter internals (reader, collector, step_tree, mapper, emitter)
- [ ] `tests/cases/contract/allure/` — contract tests: schema validation, golden file parity
- [ ] `tests/cases/integration/allure/` — integration tests: plugin lifecycle, CLI execution
- [ ] `tests/cases/contract/allure/conftest.py` — shared fixtures: factoryboy factories, hypothesis strategies
- [ ] `factoryboy` and `hypothesis` install — `uv sync --extra test` (after deps added to pyproject.toml)
- [ ] Update `tests/cases/contract/contract/test_plugin_structure_contract.py` — `EXPECTED_PLUGIN_COUNT = 19`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no authentication involved |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | `jsonschema` for schema validation; `pydantic` for model validation; `ExecutionMessageAdapter` for NDJSON parsing |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for Python/NDJSON

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed NDJSON input (invalid JSON, missing fields) | Denial of Service | `json.loads` with try/except; `jsonschema.validate` with error collection; fail fast with structured error |
| Path traversal in `--output` CLI argument | Tampering | `Path.resolve()` + verify inside expected directory; `pathvalidate` library (already in deps) |
| Large NDJSON input exhausting memory | Denial of Service | Stream NDJSON line-by-line (not read all into memory); `ExecutionMessageAdapter` already supports this pattern |
| Injection via attachment content written to disk | Tampering | Sanitize attachment filenames; use UUID-based naming for output files |

## Implementation Wave Recommendation

Phase 20 is the most complex phase in the v1 milestone. Breaking it into 5 waves prevents analysis paralysis and enables incremental delivery. Each wave produces a testable, committable increment.

### Wave 1: Schema Foundation (Plan 01)
**Goal:** Extract, compare, and commit the canonical Allure3 Events JSONSchema.

**Scope:**
- Research Allure3 reader package for existing schema/TypeScript types
- Extract schema from allure-python-commons `model2.py` (Allure2 format)
- Compare with Allure3 reader expectations
- Create `docs/allure3-events.schema.json` as the committed canonical schema
- Test: `jsonschema` can validate sample Allure result JSON against the schema

**Key decisions resolved:**
- Does Allure3 accept Allure2-format result JSON? (Open Question #2)
- Does the allure3 repo have an extractable schema? (Open Question #1)
- What format should the converter target?

**Risks:** Schema extraction scope creep (Pitfall #4). Mitigation: prioritize allure3 + allure-python only.

**Estimated complexity:** MEDIUM — primarily research with tool-assisted extraction.

### Wave 2: Converter Core (Plan 02)
**Goal:** Implement the Cucumber Messages → Allure3 JSON mapping.

**Scope:**
- Create `converter/` subpackage with `reader.py`, `collector.py`, `step_tree.py`, `mapper.py`, `emitter.py`, `model.py`
- Implement NDJSON reading via `ExecutionMessageAdapter.deserialize_dict()`
- Implement event grouping by testCase
- Implement step hierarchy reconstruction (HARD — Pitfall #1)
- Implement mapping engine with documented mapping table
- Implement JSON emitter producing `*-result.json`, `*-container.json`, `*-attachment.*`
- Handle unmappable events as structured attachments (Pitfall #2)

**Key decisions resolved:**
- Step tree reconstruction algorithm
- Mapping for each cucumber message event type
- Output file naming convention

**Risks:** Step hierarchy bugs (Pitfall #1). Mitigation: extensive unit tests for step tree builder with known fixture NDJSON.

**Estimated complexity:** HIGH — the step tree reconstruction is algorithmically challenging.

### Wave 3: Plugin + CLI Wrappers (Plan 03)
**Goal:** Deliver the 3 artifacts: core library (already done in Wave 2), CLI, and pytest plugin.

**Scope:**
- Create `allure_cucumber/` plugin directory with canonical 3-file structure
- Create `cli.py` with argparse-based `allure-cucumber` CLI
- Register `allure-cucumber` in `pyproject.toml` `[project.scripts]`
- Register `pytest-bdd-allure-cucumber` in `pyproject.toml` `[project.entry-points.pytest11]`
- Implement thin `pytest_sessionfinish` hook calling converter
- Update `EXPECTED_PLUGIN_COUNT = 19` in contract test
- No allure extra or optional dependency — converter is always available

**Key decisions resolved:**
- CLI argument design
- Plugin configuration options (output dir, messages path)
- Whether to auto-detect NDJSON from gherkin_message_reporter

**Risks:** Plugin count contract mismatch (Pitfall #3). Mitigation: update count in same commit.

**Estimated complexity:** LOW-MEDIUM — mechanical work following established patterns.

### Wave 4: Layer 1 Testing (Plan 04)
**Goal:** Comprehensive schema validation and property-based testing.

**Scope:**
- Add `factoryboy` and `hypothesis` to test dependencies
- Create factoryboy factories for cucumber message envelopes
- Create hypothesis strategies for valid NDJSON streams
- Schema validation tests: any converter output validates against `allure3-events.schema.json`
- Property-based tests: "any valid cucumber message NDJSON produces valid Allure JSON or documented error"
- Contract tests for plugin structure, CLI interface, and golden output
- Update all test files to follow semantic group markers

**Key decisions resolved:**
- Dependency placement (test extra or new extra) — Open Question #4
- Coverage targets for converter modules

**Risks:** hypothesis edge case generation may find unexpected mapping issues. Mitigation: start with known-scenario tests before enabling hypothesis.

**Estimated complexity:** MEDIUM — test infrastructure setup plus comprehensive test writing.

### Wave 5: Documentation + Final Verification (Plan 05)
**Goal:** Documentation, CI integration, and full verification.

**Scope:**
- Update DEVELOPMENT.rst with Allure-Cucumber Converter section
- Create or update architecture documentation cross-links
- Add BDD feature test in `features/` for the Allure converter (project ATDD practice)
- Run full test suite: `make test`
- Run CI-compatible suite: `make test-all`
- Verify no regressions in existing tests
- Update `docs/architecture/allure.md` with implementation notes (if applicable)

**Key decisions resolved:**
- Whether Layer 2 (Playwright/Docker) is in scope — Open Question #5

**Risks:** Low — verification and documentation only.

**Estimated complexity:** LOW — verification, documentation, and cleanup.

### Deferred / Optional: Layer 2 (HTML Validation)
- Playwright + Docker-based HTML report validation
- Requires containerized Allure3 instance
- Gated behind `@pytest.mark.docker` and `@pytest.mark.browser` (existing markers)
- Not in Phase 20 scope unless explicitly requested

## Dependencies and Risks

### External Dependencies
| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| `cucumber-messages` 32.2.0 | Runtime | ✓ Already in deps | Core input format parsing |
| `jsonschema` | Runtime | ✓ Already in deps | Layer 1 validation |
| `attrs` | Runtime | ✓ Already in deps | Data classes per project convention |
| `returns` | Runtime | ✓ Already in deps | Maybe type for optional values |
| `pydantic` ≥2.0.3 | Runtime | ✓ Already in deps | Optional: type validation for Allure models |
| `factoryboy` | Test | ✗ Need to add | Layer 1 fixture generation |
| `hypothesis` | Test | ✗ Need to add | Layer 1 property-based testing |
| `playwright` | Test | ✓ In test-playwright extra | Layer 2 only (deferred) |

### Internal Dependencies
| Capability | Source | Status |
|------------|--------|--------|
| ExecutionMessageAdapter | `model/execution_message_adapter.py` | ✓ Reusable — deserialize_dict for NDJSON parsing |
| message_converter | `model/message_converter.py` | ✓ Reusable — envelope_to_dict, envelope_from_dict |
| message_extension | `model/message_extension.py` | ✓ Reusable — EventEnvelope, PayloadKind, get_payload_kind |
| StashBound | `model/stash_access.py` | ✓ Reusable — Plugin config pattern |
| Test semantic groups | `tests/cases/{unit,contract,integration}` | ✓ Follow pattern |

### Key Risks

1. **Step hierarchy reconstruction complexity (HIGH):** The flat-to-nested step tree mapping is the hardest algorithmic challenge. The cucumber messages protocol has no explicit parent-child step relationships — the converter must infer hierarchy from pickle data and chronological event ordering. Mitigation: spike the step tree builder in Wave 2 before committing to the full converter design.

2. **Allure3 format uncertainty (MEDIUM):** It's unclear whether Allure3's reader accepts Allure2-format JSON result files or requires a different format. If a new format is required, the emitter must target it. Mitigation: resolve this in Wave 1 (Schema Foundation) before any emitter code is written. Test with `npx allure generate` against sample output.

3. **Schema extraction scope creep (MEDIUM):** Researching 5 implementations for schema extraction could balloon into weeks of work. Mitigation: prioritize allure3 (canonical consumer) + allure-python (producer for Python ecosystem). Use other 3 for gap identification only.

4. **Test dependency proliferation (LOW):** Adding `factoryboy` and `hypothesis` as full dependencies may be controversial. Mitigation: add to `test` extra which already has 15+ dependencies. These are standard testing tools.

5. **Contract test friction (LOW):** The `test_plugin_structure_contract.py` expects exactly 18 plugins. Forgetting to bump `EXPECTED_PLUGIN_COUNT` to 19 breaks CI. Mitigation: update in the same wave as plugin registration.

## Sources

### Primary (HIGH confidence)
- `docs/architecture/allure.md` — Phase 20 specification document [VERIFIED]
- `src/pytest_bdd/model/execution_message_adapter.py` — NDJSON parsing infrastructure [VERIFIED]
- `src/pytest_bdd/model/message_converter.py` — Cucumber message serialization [VERIFIED]
- `src/pytest_bdd/model/message_extension.py` — EventEnvelope, PayloadKind types [VERIFIED]
- `src/pytest_bdd/model/stash_access.py` — StashBound plugin config pattern [VERIFIED]
- `tests/cases/contract/contract/test_plugin_structure_contract.py` — Plugin structure contract [VERIFIED]
- `pyproject.toml` — Dependencies, entry points, scripts [VERIFIED]
- `DEVELOPMENT.rst` — Plugin development lifecycle and patterns [VERIFIED]
- `AGENTS.md` — Code conventions (attrs, StashBound, no return None) [VERIFIED]
- `/allure-framework/allure-python` (GitHub) — Allure2 result model (`model2.py`, `mapping.py`) [VERIFIED: official repo]
- `/allure-framework/allure3` (Context7) — Allure3 reader and CLI documentation [VERIFIED: Context7]

### Secondary (MEDIUM confidence)
- Allure3 reader package documentation (Context7) — Reader format expectations [CITED: Context7]
- Allure3 CLI `npx allure generate` — Confirmed can generate from results directory [CITED: Context7]

### Tertiary (LOW confidence)
- `factoryboy` and `hypothesis` as test dependencies — Named in architecture doc but not verified against specific versions or compatibility [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All core deps already in project; only test deps need addition
- Architecture: HIGH — Architecture doc is comprehensive; existing codebase patterns well-understood
- Pitfalls: MEDIUM — Step hierarchy reconstruction risk is real; Allure3 format uncertainty needs resolution

**Research date:** 2026-06-09
**Valid until:** 2026-07-09 (30 days — schema extraction findings may need refresh as allure3 evolves)
