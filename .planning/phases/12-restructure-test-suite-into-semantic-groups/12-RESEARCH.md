# Phase 12: restructure-test-suite-into-semantic-groups - Research

**Researched:** 2026-05-19
**Domain:** pytest test-suite architecture, semantic grouping, Make/tox test orchestration
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
## Implementation Decisions

### Migration Slicing
- **D-01:** Use a big-bang migration for the test tree. Do not require a separate move-only commit before behavior/config edits.
- **D-02:** Planner may combine file moves, import updates, pytest config changes, Makefile changes, tox changes, and documentation edits when that keeps the migration coherent.
- **D-03:** Validation must still distinguish mechanical relocation from behavior changes in the plan and test strategy.

### Classification Edge Cases
- **D-04:** Use strict semantic classification. No mixed-purpose directories under `tests/cases/`.
- **D-05:** Ambiguous tests may be classified case-by-case by the agent based on purpose, not legacy path. Defaulting all ambiguous tests to `integration` is not locked.
- **D-06:** Canonical semantic groups are `unit`, `integration`, `contract`, `e2e`, `compat`, `perf`, and `external`.
- **D-07:** `messages`, formatter golden, docs/generation/scripts, Docker xdist, and long benchmark tests must be split according to the design doc's purpose-based mapping.

### Environment Target Policy
- **D-08:** Keep default `make test` feasible on the current machine without surprise provisioning; unavailable environment-specific tests are excluded from default selection.
- **D-09:** Explicit environment targets fail early with actionable setup errors when prerequisites are missing.
- **D-10:** `make test-all` should include feasible local, Docker, and platform bridge targets after validation; it should not fail solely because an unsupported/unavailable environment cannot run on the current host.
- **D-11:** Environment checks are read-only. Provisioning must be explicit through `env-install-*` targets.

### Helper-Code Extraction
- **D-12:** Shared active helpers move to internal `src/pytest_bdd/testing/` modules.
- **D-13:** `src/pytest_bdd/testing/` is internal project-owned test infrastructure, not documented as public user API.
- **D-14:** Local fixture code that only serves one semantic group may remain in that group's `conftest.py`.
- **D-15:** `tests/assets/` must contain passive fixtures, templates, golden files, Docker assets, and feature-document fixtures only.

### E2E Split Rule
- **D-16:** Split E2E collection per feature file where practical.
- **D-17:** Whole-directory E2E scenario loaders are forbidden after this phase.
- **D-18:** Each E2E module should bind only the feature file or files it owns so failures, selection, and ownership stay file-local.

### Makefile Contract
- **D-19:** Document only the new Makefile API. Old commands are not part of the user-facing contract.
- **D-20:** Remove old commands if they are unusable or misleading. Existing commands that naturally still work do not need documentation aliases.
- **D-21:** Tox remains the matrix engine; Make is the human entrypoint.

### the agent's Discretion
- Exact file-by-file classification for ambiguous tests, provided it follows strict purpose-based semantics.
- Exact implementation order inside the big-bang migration.
- Exact names and boundaries for internal helper modules under `src/pytest_bdd/testing/`, within the design doc's proposed module set.
- Exact validation command sequence, as long as it proves semantic group mapping, Makefile target shape, and representative old/new slice equivalence.

### Deferred Ideas (OUT OF SCOPE)
None - discussion stayed within phase scope.
</user_constraints>

## Summary

Phase 12 should be planned as one coordinated test-infrastructure migration: move collected tests under `tests/cases/{unit,integration,contract,e2e,compat,perf,external}`, move passive fixtures under `tests/assets/`, move shared active harness code into internal package modules under `src/pytest_bdd/testing/`, then update pytest config, Makefile, tox, docs, and path-dependent scripts together. [CITED: docs/superpowers/specs/2026-05-18-test-suite-restructure-design.md] [CITED: .planning/phases/12-restructure-test-suite-into-semantic-groups/12-CONTEXT.md]

Current suite has 162 test files and many path couplings: `pyproject.toml` maps legacy paths to `instant/fast/medium/slow/external`, `Makefile` runs `tox` for `test`, `tox.ini` hardcodes at least one `tests/messages/...` path, Docker assets reference `tests/e2e/fixtures/remote_xdist/...`, and helper imports target `tests.support.*`. [VERIFIED: codebase grep] Plan must include an inventory-driven rename/update wave, not only directory moves. [VERIFIED: codebase grep]

**Primary recommendation:** create a phase plan with Wave 0 classification/safety tests, Wave 1 tree/helper moves, Wave 2 config/Make/tox/docs rewrite, Wave 3 equivalence and environment validation. [VERIFIED: codebase grep] [CITED: docs/superpowers/specs/2026-05-18-test-suite-restructure-design.md]

## Project Constraints (from AGENTS.md)

- Documentation, specification, and planning artifacts must be English. [CITED: AGENTS.md]
- Follow `DEVELOPMENT.rst`; do not duplicate long guideline content in `AGENTS.md`. [CITED: AGENTS.md]
- Use `ruff`/pre-commit formatting and linting. [CITED: AGENTS.md]
- Maintain Python 3.10-3.14 support matrix. [CITED: AGENTS.md]
- Outside pytest hooks, avoid `return None`; use explicit values or deterministic exceptions. [CITED: AGENTS.md]
- Use `attrs` over stdlib `dataclass` in new/modified source. [CITED: AGENTS.md]
- Keep `tests/conftest.py` thin; shared group parsing, assignment, marker application, and xdist barrier logic belongs in `src/pytest_bdd/util/tests_group_ordering.py` in current code, despite context naming `test_group_ordering.py`. [VERIFIED: codebase grep]
- Group filtering uses normal pytest marker expressions such as `pytest -m <configured-group>`; do not hardcode non-group marker ignore lists. [CITED: AGENTS.md]
- For non-native platform test environments, run via Docker skill; Windows targets are exempt. [CITED: AGENTS.md]
- SpecKit is project source of truth for architecture/spec/task artifacts; GSD research/planning must not alter SpecKit `.specify/` artifacts or constitution. [CITED: AGENTS.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Semantic test classification | Test suite structure | pytest config | Directory owns meaning; config maps paths to group markers. [CITED: design doc] |
| Group marker/order resolution | pytest plugin hook layer | Test config | Existing hook adapter in `tests/conftest.py` delegates to source helper. [VERIFIED: codebase grep] |
| Human test API | Makefile | tox | Context locks Make as human entrypoint and tox as matrix engine. [CITED: CONTEXT.md] |
| Matrix execution | tox | Makefile | Current `tox.ini` owns Python/pytest/platform factors. [VERIFIED: codebase grep] |
| Active reusable harness code | `src/pytest_bdd/testing/` | group-local `conftest.py` | Context locks shared helpers into internal package, local fixtures may stay local. [CITED: CONTEXT.md] |
| Passive test data | `tests/assets/` | test modules | Design doc restricts assets to fixtures/templates/golden/Docker/feature docs. [CITED: design doc] |
| Environment validation/provisioning | Makefile targets | helper modules | Design separates read-only `env-check-*` from explicit `env-install-*`. [CITED: design doc] |

## Standard Stack

### Core

| Tool/Library | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| Python via `uv` | 3.14.4 local | Run tests and tools | Project uses `uv run` and Python 3.10-3.14 matrix. [VERIFIED: command output] [CITED: DEVELOPMENT.rst] |
| pytest | 9.0.3 local | Test runner, markers, `pytester` | Existing config enables `-p pytester`; pytest docs support registered custom markers and `-m` marker selection. [VERIFIED: command output] [CITED: https://docs.pytest.org/en/stable/how-to/mark.html] |
| tox | 4.54.0 local | Matrix engine | Current `tox.ini` uses tox 4 env factors; tox docs define `env_list`, `testenv`, and default tox runs. [VERIFIED: command output] [CITED: https://tox.wiki/en/4.40.0/tutorial/getting-started.html] |
| GNU Make | 4.3 local | Human command entrypoint | Context locks Make as documented API. [VERIFIED: command output] [CITED: CONTEXT.md] |
| pytest-bdd internal group helper | current repo | Path-to-group marker/order/barrier | Existing code already registers ini options and applies markers/order. [VERIFIED: codebase grep] |

### Supporting

| Tool/Library | Version | Purpose | When to Use |
|--------------|---------|---------|-------------|
| Docker / Docker Compose | not found on PATH | External Docker-backed tests | Use only behind `env-check-docker` / `test-docker`; missing locally means default targets must exclude Docker tests. [VERIFIED: command output] |
| Node/npm | Node 18.19.1, npm 11.6.2 | Cucumber formatter bridge and report rendering | Keep for formatter/browser/report tests that already require Node. [VERIFIED: command output] |
| WSL bridge | `wsl.exe` present | Windows bridge checks from WSL host | Use for explicit Windows bridge validation only. [VERIFIED: command output] |
| PowerShell | present | Windows bridge helper checks | Use only for explicit Windows/bridge targets. [VERIFIED: command output] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Path-based semantic grouping | Per-test manual markers only | Rejected by project pattern: current helper is path-driven and context says group filtering uses configured group names. [CITED: AGENTS.md] [VERIFIED: codebase grep] |
| Preserve `tests/support` | Keep test-only helper package | Rejected by design: shared active helpers move to `src/pytest_bdd/testing/`. [CITED: design doc] |
| Whole-suite e2e loader | `scenarios(".")` | Rejected by locked D-17; split per feature file. [CITED: CONTEXT.md] |

**Installation:** no new external packages recommended. [VERIFIED: codebase grep]

## Architecture Patterns

### System Architecture Diagram

```text
Developer command
  -> Makefile target
    -> env-check-* read-only gate
      -> selector construction (-m group/facet, path, tox env)
        -> tox env or uv pytest command
          -> pytest config [tool.pytest.ini_options]
            -> tests/conftest.py thin hook adapter
              -> src/pytest_bdd/util/tests_group_ordering.py
                -> item group marker + order marker + xdist barrier
                  -> collected tests under tests/cases/**
                    -> passive data from tests/assets/**
                    -> shared harness from src/pytest_bdd/testing/**
```

### Recommended Project Structure

```text
tests/
  cases/
    unit/
    integration/
    contract/
    e2e/
    compat/
    perf/
    external/
  assets/
    fixtures/
    templates/
    golden/
    docker/
    feature_docs/
src/pytest_bdd/testing/
  docker.py
  docker_cluster.py
  cucumber_formatters.py
  temp_paths.py
```

Source: design doc target tree. [CITED: docs/superpowers/specs/2026-05-18-test-suite-restructure-design.md]

### Pattern 1: Path-First Semantic Assignment

**What:** map `tests/cases/<group>/** = <group>` in `pyproject.toml` and let existing group helper apply pytest markers/order at collection time. [VERIFIED: codebase grep]

**When to use:** every collected test file. Do not rely on legacy folder names. [CITED: CONTEXT.md]

**Example:**

```toml
[tool.pytest.ini_options]
markers = [
  "unit: pure in-process module tests",
  "integration: local plugin, parser, runtime, pytester, and subprocess-light flows",
  "contract: golden files, boundary contracts, schema contracts, and formatter parity contracts",
  "e2e: full executable user workflows and feature-doc driven acceptance tests",
  "compat: Python, pytest, dependency, and platform compatibility checks",
  "perf: benchmarks and expensive performance probes",
  "external: Docker, browser, and host-platform harnesses or acceptance wrappers",
  "slow: intentionally slow tests",
  "docker: Docker-backed tests",
  "windows: Windows or Windows bridge behavior",
  "posix: POSIX host behavior",
  "browser: browser-backed tests",
]
test_group_default = "integration"
test_group_order = ["unit", "integration", "contract", "e2e", "compat", "perf", "external"]
test_group_paths = [
  "tests/cases/unit/** = unit",
  "tests/cases/integration/** = integration",
  "tests/cases/contract/** = contract",
  "tests/cases/e2e/** = e2e",
  "tests/cases/compat/** = compat",
  "tests/cases/perf/** = perf",
  "tests/cases/external/** = external",
]
testpaths = ["tests/cases"]
```

Source: design doc plus current config pattern. [CITED: design doc] [VERIFIED: codebase grep]

### Pattern 2: Thin `tests/conftest.py`

**What:** keep pytest hooks in `tests/conftest.py`, but logic in source helper. [CITED: AGENTS.md] [VERIFIED: codebase grep]

**When to use:** update imports only if helper module is renamed; avoid creating `tests/cases/conftest.py` with duplicate grouping logic. [CITED: AGENTS.md]

### Pattern 3: Internal Testing Package for Active Helpers

**What:** move reusable helper modules from `tests/support` to `src/pytest_bdd/testing`. [CITED: CONTEXT.md]

**When to use:** helpers imported by multiple semantic groups or needed by environment Make targets. [VERIFIED: codebase grep]

**Migration targets found:** `tests.support.cucumber_formatters`, `tests.support.docker`, `tests.support.docker_cluster`, `tests.support.pytest_results`. [VERIFIED: codebase grep]

### Anti-Patterns to Avoid

- **Mixed-purpose directories:** violates strict semantic classification. [CITED: CONTEXT.md]
- **Manual marker-only semantics:** drift-prone; project has path-driven group config. [VERIFIED: codebase grep]
- **Default target provisioning:** violates read-only env-check policy. [CITED: CONTEXT.md]
- **Keeping collected tests under `tests/assets/`:** assets must be passive. [CITED: CONTEXT.md]
- **Whole-directory e2e `scenarios(".")`:** forbidden after this phase. [CITED: CONTEXT.md]
- **Documenting old Make aliases as API:** context says document only new Makefile API. [CITED: CONTEXT.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Marker registration/selection | Custom CLI parser | pytest markers and `-m` expressions | pytest officially supports custom markers and marker selection. [CITED: https://docs.pytest.org/en/stable/how-to/mark.html] |
| Matrix orchestration | Shell loops over Python/pytest versions | tox env factors and `env_list` | tox 4 owns env setup/run semantics. [CITED: https://tox.wiki/en/4.40.0/tutorial/getting-started.html] |
| Group ordering/barrier | New test-local plugin | existing `src/pytest_bdd/util/tests_group_ordering.py` | Existing code already handles ini parsing, marker application, order marker, and barrier. [VERIFIED: codebase grep] |
| Environment readiness | Mutating checks inside test targets | `env-check-*` read-only targets | Context locks checks as read-only and provisioning as explicit. [CITED: CONTEXT.md] |

**Key insight:** main risk is stale path coupling, not algorithmic complexity. Plan must inventory and update every path reference, helper import, Docker fixture path, tox command, Make target, coverage/config rule, and doc command. [VERIFIED: codebase grep]

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None found; phase moves files/config only. No DB/datastore in project context. [CITED: AGENTS.md] | No data migration. |
| Live service config | GitHub workflow paths may exist but were not requested files; `tox.ini`, `Makefile`, `pyproject.toml` are in repo. [VERIFIED: codebase grep] | Planner should grep `.github/` before edits. |
| OS-registered state | None found. [VERIFIED: command output] | No OS registration migration. |
| Secrets/env vars | `tox.ini` and Docker helpers use env vars such as `PYTEST_REMOTE_MODE`; no secret key migration found. [VERIFIED: codebase grep] | Preserve env var names unless tied to moved paths. |
| Build artifacts | `.tox`, `.venv`, `build`, `dist`, `__pycache__` exist. [VERIFIED: codebase grep] | Do not edit generated artifacts; plan clean/regenerate if stale path failures occur. |

## Common Pitfalls

### Pitfall 1: Singular Helper Filename Mismatch

**What goes wrong:** planner follows context path `src/pytest_bdd/util/test_group_ordering.py`; actual file is `src/pytest_bdd/util/tests_group_ordering.py`. [VERIFIED: codebase grep]

**How to avoid:** use actual file unless intentionally renaming with imports/tests. [VERIFIED: codebase grep]

### Pitfall 2: Hidden Path Couplings

**What goes wrong:** pytest config passes but Docker/formatter/message scripts still reference old `tests/e2e/fixtures` or `tests/messages_coverage`. [VERIFIED: codebase grep]

**How to avoid:** plan mandatory `rg "tests/|tests\\\\|tests.support|scenarios\\("` audit before and after moves. [VERIFIED: codebase grep]

### Pitfall 3: Active Helpers Left Under Tests

**What goes wrong:** `tests/support` remains importable and becomes de facto API. [CITED: CONTEXT.md]

**How to avoid:** move active shared helpers to `src/pytest_bdd/testing/`; update patch targets in tests that mock helper internals. [VERIFIED: codebase grep]

### Pitfall 4: Default Make Target Too Expensive

**What goes wrong:** current `make test` runs full tox and could require unavailable Docker/platform/browser targets. [VERIFIED: codebase grep]

**How to avoid:** redefine `make test` as feasible current-machine suite; route Docker/browser/platform through explicit targets with `env-check-*`. [CITED: CONTEXT.md]

### Pitfall 5: E2E Split Breaks Shared Steps

**What goes wrong:** replacing `scenarios(".")` can orphan step definitions or collect too broad a feature set. [VERIFIED: codebase grep]

**How to avoid:** create one or more e2e modules that bind owned feature files; keep shared step fixtures where reused but avoid full-directory loader. [CITED: CONTEXT.md]

## Code Examples

### Existing Thin Adapter

```python
from pytest_bdd.util.tests_group_ordering import (
    apply_group_ordering,
    record_group_barrier_report,
    register_group_config_options,
    wait_for_group_barrier,
)

def pytest_addoption(parser):
    register_group_config_options(parser)

def pytest_collection_modifyitems(config, items):
    apply_group_ordering(config, items)
```

Source: current `tests/conftest.py`. [VERIFIED: codebase grep]

### Existing Group Helper Behavior

```python
def apply_group_ordering(config: pytest.Config, items: list[pytest.Item]) -> None:
    group_config = read_group_config(config)
    for index, group_name in enumerate(group_config.groups, start=1):
        config.addinivalue_line("markers", f"{group_name}: test group {index}")
    for item in items:
        assignment = resolve_group_assignment(item, group_config)
        apply_group_marker(item, assignment)
        apply_order_marker(item, assignment)
```

Source: current `src/pytest_bdd/util/tests_group_ordering.py`. [VERIFIED: codebase grep]

### Official Marker Registration Pattern

```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "env(name): mark test to run only on named environment"
    )
```

Source: pytest docs. [CITED: https://docs.pytest.org/en/stable/how-to/mark.html]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy speed-ish groups `instant/fast/medium/slow/external` | Semantic groups plus speed/environment facets | Phase 12 design, 2026-05-18 | Update `test_group_order`, `test_group_paths`, marker docs, Make targets. [CITED: design doc] |
| `tests/support` active helper modules | internal `src/pytest_bdd/testing/` | Phase 12 design, 2026-05-18 | Update imports and mock patch paths. [CITED: design doc] [VERIFIED: codebase grep] |
| `tests/e2e/test_e2e.py` whole directory loader | per-feature e2e modules | Phase 12 context, 2026-05-18 | Split ownership and selection. [CITED: CONTEXT.md] |
| `make test` = full tox + reports | feasible current-machine default | Phase 12 context, 2026-05-18 | Avoid surprise provisioning and unsupported env failure. [CITED: CONTEXT.md] |

**Deprecated/outdated:**
- `tests/support`: out of scope to keep. [CITED: design doc]
- `scenarios(".")` e2e loader: forbidden after phase. [CITED: CONTEXT.md]
- Old documented test commands in `DEVELOPMENT.rst`: must be rewritten to new Make API. [CITED: design doc]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `test_group_default = "integration"` is best fallback after migration. [ASSUMED] | Architecture Patterns | Unclassified tests could be mislabeled; planner should decide after classification inventory. |
| A2 | `tests.support.pytest_results` should move to `src/pytest_bdd/testing/pytest_results.py` even though design doc's proposed module list omits it. [ASSUMED] | Architecture Patterns | Helper may stay group-local if only e2e uses it; planner should classify by reuse. |
| A3 | GitHub workflow path references may need updates. [ASSUMED] | Runtime State Inventory | CI may fail if `.github/` has hardcoded old test paths. |

## Open Questions (RESOLVED)

1. **Should source helper filename be renamed from `tests_group_ordering.py` to `test_group_ordering.py`?**
   - What we know: AGENTS/context mention singular; current code uses plural. [VERIFIED: codebase grep]
   - Resolution: keep existing `src/pytest_bdd/util/tests_group_ordering.py` filename in Phase 12. Treat singular references as stale prose unless a later dedicated cleanup phase renames the module with import updates and compatibility rationale.
   - Plan impact: plans must reference the plural filename and must not add a rename task.

2. **How granular should E2E split be for 47 feature files?**
   - What we know: whole-directory loader forbidden; per-file split required where practical. [CITED: CONTEXT.md]
   - Resolution: create owned e2e modules per feature file where practical; when related feature files share one step/fixture boundary, one module may bind a small explicit list of `.feature`/`.feature.md` files.
   - Plan impact: every `scenarios(...)` call must name explicit feature file path(s); no directory target, `scenarios(".")`, or full-tree filter wrapper remains.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | all local commands | yes | 0.11.6 | none |
| Python via `uv` | tests/tools | yes | 3.14.4 | `uv python install 3.14` |
| pytest | validation | yes | 9.0.3 | project env sync |
| tox + tox-uv | matrix | yes | tox 4.54.0, tox-uv 1.35.2 | `uvx --with tox-uv tox` |
| GNU Make | human API | yes | 4.3 | direct `uv`/`tox` commands for debugging only |
| Docker | external/docker tests | no | - | exclude from default; explicit `env-check-docker` fails actionable |
| Docker Compose | external/docker tests | no | - | same as Docker |
| Node | formatter/browser/report tools | yes | 18.19.1 | env-check should fail if absent |
| npm | formatter/browser/report tools | yes | 11.6.2 | env-check should fail if absent |
| WSL bridge | Windows bridge targets | yes | `wsl.exe` present | skip unsupported bridge in `test-all` if validation fails |
| PowerShell | Windows bridge targets | yes | present | skip unsupported bridge in `test-all` if validation fails |

**Missing dependencies with no fallback:**
- None for planning/research. [VERIFIED: command output]

**Missing dependencies with fallback:**
- Docker/Docker Compose absent; default targets must exclude Docker tests and explicit Docker targets must fail early. [VERIFIED: command output] [CITED: CONTEXT.md]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 local, tox 4.54.0 local [VERIFIED: command output] |
| Config file | `pyproject.toml`, `tox.ini` [VERIFIED: codebase grep] |
| Quick run command | `uv run python -m pytest tests/cases/unit tests/cases/integration -q` [ASSUMED] |
| Full suite command | `make test-all` after Makefile rewrite [CITED: CONTEXT.md] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| TBD-01 | every collected test is under one semantic group path | unit/config | `uv run python -m pytest tests/cases/unit/test_test_suite_classification.py -q` | no - Wave 0 |
| TBD-02 | `tests/assets/` contains no collected tests | unit/config | `uv run python -m pytest tests/cases/unit/test_test_suite_classification.py -q` | no - Wave 0 |
| TBD-03 | Makefile exposes required targets and env checks are read-only | contract | `uv run python -m pytest tests/cases/contract/test_makefile_test_api.py -q` | no - Wave 0 |
| TBD-04 | representative old/new slices are equivalent | integration/smoke | `make test-unit && make test-integration && make test-contract` | no - after rewrite |
| TBD-05 | no whole-directory e2e loader remains | unit/static | `uv run python -m pytest tests/cases/unit/test_e2e_loader_shape.py -q` | no - Wave 0 |

### Sampling Rate

- **Per task commit:** nearest semantic slice, e.g. `make test-unit` or `make test-contract`. [ASSUMED]
- **Per wave merge:** `make test` plus targeted moved slice. [ASSUMED]
- **Phase gate:** `make test-all` and `uvx --with tox-uv tox -l`; Docker/platform targets validated according to local availability. [CITED: CONTEXT.md]

### Wave 0 Gaps

- [ ] `tests/cases/unit/test_test_suite_classification.py` - validates semantic path mapping and no tests under assets. [ASSUMED]
- [ ] `tests/cases/contract/test_makefile_test_api.py` - validates required Make targets and env-check/install split. [ASSUMED]
- [ ] `tests/cases/unit/test_e2e_loader_shape.py` - forbids `scenarios(".")` and broad feature-directory loaders. [ASSUMED]
- [ ] Update existing group helper tests after path change. [VERIFIED: codebase grep]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | no auth surface in test restructure. [VERIFIED: codebase grep] |
| V3 Session Management | no | no session surface in test restructure. [VERIFIED: codebase grep] |
| V4 Access Control | no | no app authorization surface. [VERIFIED: codebase grep] |
| V5 Input Validation | yes | validate Make/env command inputs and path mappings through tests, not shell string trust. [ASSUMED] |
| V6 Cryptography | no | no crypto surface. [VERIFIED: codebase grep] |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Accidental provisioning or mutation from default targets | Tampering | keep env checks read-only; put installs behind `env-install-*`. [CITED: CONTEXT.md] |
| Shell command injection in Make variables | Tampering | avoid interpolating untrusted vars into shell scripts; use fixed commands where possible. [ASSUMED] |
| Running Docker/browser tests without explicit user intent | Elevation/DoS | keep external tests behind explicit targets and validation gates. [CITED: CONTEXT.md] |

## Sources

### Primary (HIGH confidence)

- `docs/superpowers/specs/2026-05-18-test-suite-restructure-design.md` - target tree, groups, Make API, env behavior, migration safety.
- `.planning/phases/12-restructure-test-suite-into-semantic-groups/12-CONTEXT.md` - locked decisions.
- `AGENTS.md` - project constraints and test grouping rules.
- `DEVELOPMENT.rst` - current development/test workflow.
- `pyproject.toml`, `tox.ini`, `Makefile`, `tests/conftest.py`, `src/pytest_bdd/util/tests_group_ordering.py` - current implementation/config.
- pytest official docs: `https://docs.pytest.org/en/stable/how-to/mark.html` - marker registration and `-m` marker selection.
- tox official docs: `https://tox.wiki/en/4.40.0/tutorial/getting-started.html` - `env_list`, `testenv`, default tox run behavior.

### Secondary (MEDIUM confidence)

- `.planning/codebase/TESTING.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/STRUCTURE.md` - codebase maps dated 2026-05-12; useful but possibly stale.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified via local commands and official pytest/tox docs.
- Architecture: HIGH - locked by context/design doc and current code patterns.
- Pitfalls: HIGH - based on current grep evidence.
- File-by-file classification: MEDIUM - requires full planner inventory of 162 test files.

**Research date:** 2026-05-19
**Valid until:** 2026-06-18 for local architecture; re-check pytest/tox versions before implementation.
