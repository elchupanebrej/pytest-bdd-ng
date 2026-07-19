# Phase 26: Test CLI scripts in a separate Cucumber Development flow - Research

**Researched:** 2026-06-22
**Domain:** Python CLI/script ATDD coverage through pytest-bdd-ng E2E feature docs
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
## Implementation Decisions

### CLI Invocation Strategy
- **D-01:** BDD scenarios will invoke the python interpreter directly for entrypoint scripts (e.g. using `python src/pytest_bdd/script/validate_feature_headings.py`).
- **D-02:** Non-entrypoint scripts (e.g. `scripts/arch.py`) will be invoked via python interpreter directly using relative paths from the repository root, with PYTHONPATH resolving to the repository root.
- **D-03:** Standard output and error output assertions in BDD scenarios will use substring/regex matching (e.g., `the renderer terminal output includes:` with tabular lines) to remain robust against minor output format updates.
- **D-04:** Scenarios must rely only on Python scripts for execution. The presence of any shell scripts (such as `scripts/run_messages_coverage_audit.sh`) will be reported/documented as an architectural gap/risk instead of running them directly in E2E tests.

### the agent's Discretion
- Whichever step names and file structures are cleanest for writing feature files and step mappings under `src/pytest_bdd_testing/step/development.py`.

### Deferred Ideas (OUT OF SCOPE)
- Resolving the `test_undefined_parameter_runtime.py` probe warning issue is documented as a known risk/limitation rather than being fixed in this phase.
</user_constraints>

## Summary

Phase 26 should keep the existing single Development feature space under `features/18 Development/`, the `src/pytest_bdd_testing/step/development.py` step module, and the explicit E2E loader at `src/pytest_bdd_testing/case/e2e/feature/test_18_development.py`; those artifacts already exist and the focused E2E target passed with 13 scenarios on 2026-06-22. [VERIFIED: codebase grep] [VERIFIED: focused pytest run]

Primary implementation pattern: feature files create isolated mock files in `testdir.tmpdir`, invoke Python CLIs through the shared harness `run <command>` step, assert exit codes through `the command exit code is N`, and assert output through regex-like substring table rows. [VERIFIED: codebase grep]

Primary planning caveat: requirement `P26-DEV-10` says to cover `scripts/run_messages_coverage_audit.sh` orchestration, but locked decision D-04 forbids direct shell-script execution in E2E and requires documenting the shell script as a BDD architectural gap. The existing `07 Messages Coverage Audit.feature.md` follows D-04 by checking file presence and logging the gap, so the planner should treat that as the correct scoped implementation unless the user reopens D-04. [CITED: .planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-CONTEXT.md] [VERIFIED: codebase grep]

**Primary recommendation:** Preserve the current plan shape, add no new packages, and make the phase gate `python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -q` plus `make lint`/`make custom-rules`; do not run shell audit orchestration from E2E unless D-04 changes. [VERIFIED: focused pytest run] [CITED: AGENTS.md]

## Project Constraints (from AGENTS.md)

- Prefix shell commands with `rtk` when possible; initial `rtk read` attempts timed out under login shell startup, but `rtk 0.36.0` is available when `login=false` is used. [CITED: AGENTS.md] [VERIFIED: environment probe]
- Development guidance lives in `DEVELOPMENT.rst`; do not duplicate long-lived project guidance elsewhere when updating docs. [CITED: AGENTS.md]
- Use WSL2 where possible on Microsoft Windows. [CITED: AGENTS.md]
- Follow repository formatting and linting through `ruff` and pre-commit hooks. [CITED: AGENTS.md]
- Planning/specification/documentation artifacts must be written in English. [CITED: AGENTS.md]
- Outside pytest hooks, avoid `return None`; use explicit values or deterministic exceptions. [CITED: AGENTS.md]
- Use `attrs` instead of stdlib `dataclass` for new data-holding production code. [CITED: AGENTS.md]
- For new features, add acceptance tests under `features/` using ATDD/BDD patterns. [CITED: AGENTS.md]
- Keep test-group logic in `src/pytest_bdd/util/test_group_ordering.py`; do not add test-local grouping utility modules. [CITED: AGENTS.md]
- Group filtering uses configured pytest marker expressions; do not hardcode non-group markers into ignore lists. [CITED: AGENTS.md]
- Do not bypass pre-commit checks without explicit user permission. [CITED: AGENTS.md]
- If pre-commit fails on existing files, isolate and fix those failures in a separate dedicated commit before feature work. [CITED: AGENTS.md]
- Do not disable lint/pre-commit globally or exclude directories without explicit user permission and documented rationale. [CITED: AGENTS.md]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| P26-DEV-01 | Add a Development BDD feature space covering repository-specific scripts, CLIs, and pre-commit quality gates. | Seven files exist under `features/18 Development/`. [VERIFIED: codebase grep] |
| P26-DEV-02 | Add shared development step definitions for mock file setup, command execution in the test directory, exit-code checks, and stdout/stderr assertions. | `development.py` supplies mock files and exit/gap checks; `harness.py` supplies command execution and terminal-output assertions. [VERIFIED: codebase grep] |
| P26-DEV-03 | Register development steps in the E2E conftest and add an E2E loader for `features/18 Development/`. | E2E conftest imports `pytest_bdd_testing.step.development`; `test_18_development.py` loads all seven feature files. [VERIFIED: codebase grep] |
| P26-DEV-04 | Cover the `allure-cucumber` converter CLI with success and missing-input scenarios. | `01 Allure Converter CLI.feature.md` covers successful result/container generation and missing NDJSON. [VERIFIED: codebase grep] |
| P26-DEV-05 | Cover `validate_feature_headings.py` clean and failing heading validation scenarios. | `02 Headings Validator.feature.md` covers clean and empty feature-heading failure paths. [VERIFIED: codebase grep] |
| P26-DEV-06 | Cover `scripts/arch.py` responsibility injection, score collection, and gap analysis scenarios. | Existing feature covers injection and score collection; gap analysis is in SPEC/plan scope but not present as a distinct scenario in current feature text. [VERIFIED: codebase grep] |
| P26-DEV-07 | Cover the `compatibility_matrix` CLI compatibility, tox environment, and E2E migration-report scenarios. | Existing feature covers compatibility, incompatible pair, and tox env generation; E2E migration threshold reporting is in CLI but not present as a distinct current scenario. [VERIFIED: codebase grep] |
| P26-DEV-08 | Cover `sync_messages_contract_schemas.py` clean and drift scenarios. | Existing feature covers schema sync then check, plus drift detection on modified `Attachment.schema.json`. [VERIFIED: codebase grep] |
| P26-DEV-09 | Cover `render_cucumber_formatters` standalone NDJSON-to-summary rendering. | Existing feature creates NDJSON through pytest and renders summary output. [VERIFIED: codebase grep] |
| P26-DEV-10 | Cover `scripts/run_messages_coverage_audit.sh` governance report orchestration. | Locked D-04 overrides direct shell execution; current feature documents presence/gap only. Planner should preserve this unless user changes D-04. [CITED: 26-CONTEXT.md] [VERIFIED: codebase grep] |
| P26-DEV-11 | Update Phase 26 roadmap/planning artifacts with goals, success criteria, blockers, and verification commands. | ROADMAP/REQUIREMENTS already contain Phase 26 entries and `26-01-PLAN.md` exists. [VERIFIED: codebase grep] |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Development behavior specification | Feature docs | E2E loader | `features/18 Development/` owns human-readable executable behavior; loader only selects feature documents. [VERIFIED: codebase grep] |
| Isolated file setup | E2E step layer | pytester/testdir | `Mock file` and `Copy path` steps create test-local files without mutating repo/global state. [VERIFIED: codebase grep] |
| CLI invocation | E2E harness | Python CLI modules | `harness.py` normalizes `python` to `sys.executable`, sets `PYTHONPATH` to repo `src`, and runs with `cwd=testdir.tmpdir`. [VERIFIED: codebase grep] |
| CLI behavior | Script modules | Supporting package modules | Each CLI module owns argument parsing and exit semantics; BDD tests assert public process behavior. [VERIFIED: codebase grep] |
| Messages coverage audit shell gap | Feature docs | Development step layer | Locked D-04 puts shell execution out of E2E scope; feature documents the gap. [CITED: 26-CONTEXT.md] [VERIFIED: codebase grep] |

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| Python | 3.12.7 installed; project supports 3.10-3.14 | Runs CLIs and E2E tests | Existing runtime and AGENTS-supported matrix. [VERIFIED: environment probe] [CITED: AGENTS.md] |
| pytest | 8.3.4 installed; project declares `pytest>=7.0.0` | Test runner and pytester/testdir harness | Existing project test runner and configured testpath. [VERIFIED: environment probe] [VERIFIED: pyproject.toml] |
| pytest-bdd-ng internal API | local source | `scenarios()` loader and step decorators | Feature docs are executed through project’s own BDD runtime. [VERIFIED: codebase grep] |
| PyHamcrest | project test extra | Step assertions | Existing `development.py` and `harness.py` use `assert_that`, `equal_to`, and matchers. [VERIFIED: codebase grep] [VERIFIED: pyproject.toml] |
| uv | 0.11.16 installed | Environment and Makefile command runner | Makefile uses `uv run`/`uv sync` for test and lint entrypoints. [VERIFIED: environment probe] [VERIFIED: codebase grep] |

### Supporting
| Library/Tool | Version | Purpose | When to Use |
|--------------|---------|---------|-------------|
| `shlex`, `subprocess`, `sys`, `pathlib` | Python stdlib | Cross-platform process invocation and paths | Use existing harness behavior rather than custom command parsing. [VERIFIED: codebase grep] |
| Make | GNU Make 4.4.1 installed | Project quality gates | Run `make lint` and `make custom-rules` as phase gates. [VERIFIED: environment probe] [VERIFIED: codebase grep] |
| bash | 5.2.21 available | Shell audit script runtime outside E2E | Do not use from Phase 26 E2E under D-04; use only manual/CI maintenance context. [VERIFIED: environment probe] [CITED: 26-CONTEXT.md] |
| Node.js | v25.2.1 installed | Formatter bridge ecosystem support | Existing formatter tooling can depend on Node; Phase 26 summary renderer path passed without direct Node setup. [VERIFIED: environment probe] [VERIFIED: focused pytest run] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `python -m pytest_bdd.script.<module>` | Installed console scripts | Console scripts depend on install state; locked D-01 chooses interpreter/module invocation for deterministic local E2E. [CITED: 26-CONTEXT.md] |
| Existing `run <command>` harness step | New bespoke subprocess fixture | Bespoke runner would duplicate `PYTHONPATH`, `cwd`, attach-output, and shell normalization behavior. [VERIFIED: codebase grep] |
| Shell audit execution in BDD | Feature-level gap documentation | Direct execution would violate D-04 on Windows/native E2E; gap documentation satisfies locked scope. [CITED: 26-CONTEXT.md] |

**Installation:** No new external packages should be installed for this phase. [CITED: 26-SPEC.md] [VERIFIED: pyproject.toml]

```bash
# no package install required
python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -q
```

## Package Legitimacy Audit

No new external package installation is recommended for Phase 26, so the slopcheck/package legitimacy gate is not applicable. Existing dependencies are already declared in `pyproject.toml`. [CITED: 26-SPEC.md] [VERIFIED: pyproject.toml]

## Architecture Patterns

### System Architecture Diagram

```text
Feature file in features/18 Development/
  -> E2E loader test_18_development.py selects explicit feature documents
  -> E2E conftest imports shared step modules
  -> Step setup writes/copies files into testdir.tmpdir
  -> Harness run step executes Python command with cwd=testdir.tmpdir and PYTHONPATH=<repo>/src
  -> CLI module parses args and returns process exit code
  -> Step assertions verify exit code, files, and stdout/stderr fragments
  -> Focused pytest command reports Development flow status
```

### Recommended Project Structure

```text
features/18 Development/
├── 01 Allure Converter CLI.feature.md
├── 02 Headings Validator.feature.md
├── 03 Architecture Tooling.feature.md
├── 04 Compatibility Matrix.feature.md
├── 05 Messages Contract Schema Sync.feature.md
├── 06 Cucumber Formatter Renderer.feature.md
└── 07 Messages Coverage Audit.feature.md
src/pytest_bdd_testing/
├── step/development.py
├── step/harness.py
└── case/e2e/feature/test_18_development.py
```

### Pattern 1: Isolated Testdir Command Execution
**What:** Run commands from a temporary project directory while importing the repository source through `PYTHONPATH`. [VERIFIED: codebase grep]

**When to use:** Any Development feature scenario that executes a repository CLI against mock files. [VERIFIED: codebase grep]

**Example:**
```python
# Source: src/pytest_bdd_testing/step/harness.py
if command_args and command_args[0] == "python":
    command_args[0] = sys.executable
env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(repo_root / "src"), env.get("PYTHONPATH", "")]))
result = subprocess.run(command_args, check=False, capture_output=True, text=True, cwd=str(testdir.tmpdir), env=env)
```

### Pattern 2: Feature Files Assert Public CLI Behavior
**What:** Feature scenarios assert process-level contract: exit code, output fragments, and generated files. [VERIFIED: codebase grep]

**When to use:** Script/CLI coverage where internal function tests would overfit implementation details. [VERIFIED: cucumber-best-practices skill] [VERIFIED: codebase grep]

**Example:**
```gherkin
# Source: features/18 Development/06 Cucumber Formatter Renderer.feature.md
* When run `python -m pytest_bdd.script.render_cucumber_formatters --messages-ndjson messages.ndjson --cucumber-summary`
* Then the command exit code is 0
* And the renderer terminal output includes:
  | 1 scenario (1 passed) |
  | 1 step (1 passed) |
```

### Pattern 3: Shell Scripts Are Gap-Documented, Not E2E-Executed
**What:** If the development surface is shell-only, assert its presence and log the architectural gap. [CITED: 26-CONTEXT.md] [VERIFIED: codebase grep]

**When to use:** `scripts/run_messages_coverage_audit.sh` under D-04. [CITED: 26-CONTEXT.md]

**Example:**
```gherkin
# Source: features/18 Development/07 Messages Coverage Audit.feature.md
* Given the file "scripts/run_messages_coverage_audit.sh" exists
* Then its execution is reported as an architectural gap in BDD
```

### Anti-Patterns to Avoid
- **Invoking console scripts by installed name:** use `python -m ...` or direct `python scripts/arch.py` to avoid dependency on editable-install script state. [CITED: 26-CONTEXT.md]
- **Running shell scripts directly from Windows/native E2E:** violates D-04 and risks platform-specific failures. [CITED: 26-CONTEXT.md]
- **Exact full-output assertions:** use fragment/regex table assertions because D-03 requires robustness against minor output-format drift. [CITED: 26-CONTEXT.md]
- **Writing fixtures into the repository root during scenarios:** use `testdir.tmpdir` and `Copy path` for controlled local copies. [VERIFIED: codebase grep]
- **Replacing harness helpers with local one-off subprocess code:** duplicates established attach-output and env setup behavior. [VERIFIED: codebase grep]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Command execution | New subprocess wrapper in `development.py` | Existing `run <command>` step in `harness.py` | Already handles `sys.executable`, `PYTHONPATH`, `cwd`, capture, and attachment. [VERIFIED: codebase grep] |
| File fixture setup | Manual repo-root writes | `Mock file` and `Copy path` steps | Keeps scenarios isolated in pytester temp dirs. [VERIFIED: codebase grep] |
| Output matching | Full stdout/stderr snapshots | `the renderer terminal output includes:` | Locked D-03 requires substring/regex-style matching. [CITED: 26-CONTEXT.md] |
| Shell audit orchestration | Windows shell emulation inside E2E | Gap scenario under `07 Messages Coverage Audit` | Locked D-04 forbids direct shell-script execution. [CITED: 26-CONTEXT.md] |
| CLI coverage by internal functions only | Unit-only tests of parser/main helpers | BDD process-level scenarios | Phase objective is executable contributor-facing workflow coverage. [CITED: 26-SPEC.md] |

**Key insight:** Phase 26 is an ATDD harness phase, not a CLI refactor phase; planner tasks should wire feature-doc coverage around public process contracts and avoid reshaping the script implementations unless a scenario exposes a required failure. [CITED: 26-CONTEXT.md]

## Common Pitfalls

### Pitfall 1: P26-DEV-10 vs D-04 Scope Conflict
**What goes wrong:** Planner tries to execute `scripts/run_messages_coverage_audit.sh` because P26-DEV-10 says "cover orchestration." [CITED: 26-SPEC.md]
**Why it happens:** Requirement wording conflicts with locked D-04. [CITED: 26-CONTEXT.md]
**How to avoid:** Treat D-04 as higher-priority locked context and keep shell audit as a documented architectural gap. [CITED: 26-CONTEXT.md]
**Warning signs:** Feature invokes `bash scripts/run_messages_coverage_audit.sh` or assumes POSIX paths in E2E. [VERIFIED: codebase grep]

### Pitfall 2: Feature Claims Missing Current Scenarios
**What goes wrong:** Planner marks P26-DEV-06/P26-DEV-07 fully covered without noticing current features omit explicit `analyze-gaps` and E2E migration-threshold scenarios. [VERIFIED: codebase grep]
**Why it happens:** The existing plan says "gap analysis" and "E2E migration-report", but current feature text only covers a subset. [CITED: 26-01-PLAN.md] [VERIFIED: codebase grep]
**How to avoid:** Either add those scenarios in planning, or explicitly mark them scoped out/covered by lower-level tests if user accepts. [VERIFIED: codebase grep]
**Warning signs:** No `analyze-gaps` or `--report-e2e-migration-threshold` string in `features/18 Development/`. [VERIFIED: codebase grep]

### Pitfall 3: Schema Sync Test Can Hit Network/External Git
**What goes wrong:** `sync_messages_contract_schemas` fetches schema sources during sync/check paths, which can make BDD scenarios slower or environment-sensitive. [VERIFIED: codebase grep]
**Why it happens:** The CLI fetches Cucumber messages schemas into a temporary directory before comparing/copying. [VERIFIED: codebase grep]
**How to avoid:** Keep scenarios focused and allow enough runtime; do not multiply schema-sync scenarios beyond clean/drift coverage. [VERIFIED: focused pytest run]
**Warning signs:** Focused Development test slows significantly or fails on fetch/remote availability. [VERIFIED: focused pytest run]

### Pitfall 4: Warnings-As-Errors Can Break Logging/Gaps
**What goes wrong:** Warning-emitting probes or pytest plugin teardown warnings can fail collection because `filterwarnings = ["error"]`. [VERIFIED: pyproject.toml]
**Why it happens:** Project treats warnings as errors by default, and the messages coverage undefined-parameter probe is a known risk. [VERIFIED: pyproject.toml] [CITED: 26-SPEC.md]
**How to avoid:** Do not resolve the undefined-parameter probe in this phase; document it as deferred unless user reopens scope. [CITED: 26-CONTEXT.md]
**Warning signs:** `PluggyTeardownRaisedWarning`, collection-time fixture resolution failures, or exit code 4 in probe runs. [CITED: specs/026-dev-scripts-bdd/plan.md]

## Code Examples

### Development File Fixture
```python
# Source: src/pytest_bdd_testing/step/development.py
@given(parsers.parse('Mock file "{filename}" with content:'))
def mock_file_with_content(testdir: Testdir, filename: str, step: getattr) -> None:
    doc_string = getattr(step.argument, "doc_string", None) if getattr(step, "argument", None) else None
    content = doc_string.content if doc_string else ""
    target = Path(str(testdir.tmpdir)) / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
```

### E2E Loader
```python
# Source: src/pytest_bdd_testing/case/e2e/feature/test_18_development.py
pytestmark = [pytest.mark.e2e]

test = scenarios(
    "18 Development/01 Allure Converter CLI.feature.md",
    "18 Development/02 Headings Validator.feature.md",
    "18 Development/03 Architecture Tooling.feature.md",
    "18 Development/04 Compatibility Matrix.feature.md",
    "18 Development/05 Messages Contract Schema Sync.feature.md",
    "18 Development/06 Cucumber Formatter Renderer.feature.md",
    "18 Development/07 Messages Coverage Audit.feature.md",
)
```

### Step Registration
```python
# Source: src/pytest_bdd_testing/case/e2e/conftest.py
pytest.register_assert_rewrite("pytest_bdd_testing.step.development")
from pytest_bdd_testing.step.development import *  # noqa: F403, E402
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Script behavior covered indirectly or by ad hoc unit/CI checks | Executable Development feature space under `features/18 Development/` | Phase 26 artifacts present by 2026-06-22 | Contributor workflow contracts become runnable BDD specs. [VERIFIED: codebase grep] |
| Whole feature-tree E2E loading | Explicit per-domain E2E loader for Development files | Existing Phase 26 loader | Faster focused verification and clearer ownership. [VERIFIED: codebase grep] |
| Running shell orchestration directly | Document shell-only audit as gap under D-04 | Locked in 26-CONTEXT.md | Avoids Windows/native E2E fragility. [CITED: 26-CONTEXT.md] |

**Deprecated/outdated:**
- Planning references to legacy `tests/` paths in older codebase maps are stale for current test layout; current pytest testpath is `src/pytest_bdd_testing/case`. [VERIFIED: pyproject.toml] [CITED: .planning/codebase/TESTING.md]
- A loader shorthand `scenarios("18 Development")` appears in planning text, but current loader explicitly enumerates all seven feature files. [CITED: specs/026-dev-scripts-bdd/plan.md] [VERIFIED: codebase grep]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | No additional package install is required for Phase 26. | Standard Stack | Low; if a hidden CLI dependency is missing, planner needs an install/checkpoint task. This is supported by SPEC scope and current focused test pass. [CITED: 26-SPEC.md] [VERIFIED: focused pytest run] |

## Resolved Questions

No unresolved research questions remain after revision iteration 1.

1. **RESOLVED: P26-DEV-06 explicit `scripts/arch.py analyze-gaps` coverage**
   - Resolution: `26-02-PLAN.md` Task 1 adds the focused gap-analysis scenario and requires `python scripts/arch.py analyze-gaps` per D-02. [CITED: 26-02-PLAN.md]
   - Result: Score collection from 26-01 remains preserved, and the literal gap-analysis surface is covered by 26-02. [CITED: 26-01-PLAN.md] [CITED: 26-02-PLAN.md]

2. **RESOLVED: P26-DEV-07 explicit E2E migration-threshold coverage**
   - Resolution: `26-02-PLAN.md` Task 2 adds the focused `--report-e2e-migration-threshold` scenario and invokes `python -m pytest_bdd.script.compatibility_matrix ...` per D-01. [CITED: 26-02-PLAN.md]
   - Result: Compatibility and tox-environment coverage from 26-01 remains preserved, and the literal migration-threshold report surface is covered by 26-02. [CITED: 26-01-PLAN.md] [CITED: 26-02-PLAN.md]

3. **RESOLVED: P26-DEV-10 wording versus D-04**
   - Resolution: Locked D-04 controls implementation. Phase 26 preserves shell audit coverage as presence plus architectural-gap documentation, not direct shell execution. [CITED: 26-CONTEXT.md]
   - Result: `26-01-PLAN.md` Task 3 and `26-02-PLAN.md` Task 3 keep the D-04 boundary and add a no-bash/no-sh static gate for `scripts/run_messages_coverage_audit.sh`. [CITED: 26-01-PLAN.md] [CITED: 26-02-PLAN.md]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | CLI and E2E execution | yes | 3.12.7 | Use project-supported 3.10-3.14 via uv. [VERIFIED: environment probe] [CITED: AGENTS.md] |
| pytest | Focused E2E target | yes | 8.3.4 | `uv run python -m pytest ...` if shell `pytest` differs. [VERIFIED: environment probe] |
| uv | Makefile/env commands | yes | 0.11.16 | Direct `python -m pytest` for focused research run. [VERIFIED: environment probe] |
| Git | Commit/status/source control | yes | 2.53.0.windows.3 | none needed. [VERIFIED: environment probe] |
| Make | `make lint`, `make custom-rules` | yes | GNU Make 4.4.1 | Invoke underlying `uv run ruff...` and pytest custom-rules commands manually. [VERIFIED: environment probe] [VERIFIED: codebase grep] |
| bash | Shell audit script outside E2E | yes | 5.2.21 | Keep E2E gap-only per D-04. [VERIFIED: environment probe] [CITED: 26-CONTEXT.md] |
| Node.js | Formatter ecosystem support | yes | v25.2.1 | Existing fake-node helpers for specific formatter docs where needed. [VERIFIED: environment probe] [VERIFIED: codebase grep] |
| rtk | Token-filtered commands per AGENTS | yes | 0.36.0 | Use `login=false` or native commands if login startup hangs. [VERIFIED: environment probe] [CITED: AGENTS.md] |

**Missing dependencies with no fallback:** None found for research and focused E2E verification. [VERIFIED: environment probe]

**Missing dependencies with fallback:** None found. [VERIFIED: environment probe]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 installed; project declares `pytest>=7.0.0`. [VERIFIED: environment probe] [VERIFIED: pyproject.toml] |
| Config file | `pyproject.toml` under `[tool.pytest.ini_options]`. [VERIFIED: pyproject.toml] |
| Quick run command | `python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -q` [VERIFIED: focused pytest run] |
| Full suite command | `make lint` and `make custom-rules`; broader suite via `make test-e2e` if needed. [VERIFIED: codebase grep] |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| P26-DEV-01 | Development feature space exists | e2e | `python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -q` | yes [VERIFIED: focused pytest run] |
| P26-DEV-02 | Development steps support setup/execution/assertions | e2e | same quick command | yes [VERIFIED: codebase grep] |
| P26-DEV-03 | E2E conftest and loader register Development flow | e2e | same quick command | yes [VERIFIED: codebase grep] |
| P26-DEV-04 | Allure converter success/missing-input | e2e | same quick command | yes [VERIFIED: focused pytest run] |
| P26-DEV-05 | Heading validator clean/failure | e2e | same quick command | yes [VERIFIED: focused pytest run] |
| P26-DEV-06 | Architecture injection/score collection; gap-analysis question remains | e2e | same quick command | partial [VERIFIED: codebase grep] |
| P26-DEV-07 | Compatibility pairs/tox envs; E2E migration-report question remains | e2e | same quick command | partial [VERIFIED: codebase grep] |
| P26-DEV-08 | Schema sync clean/drift | e2e | same quick command | yes [VERIFIED: focused pytest run] |
| P26-DEV-09 | Formatter summary render | e2e | same quick command | yes [VERIFIED: focused pytest run] |
| P26-DEV-10 | Shell audit gap documented | e2e/documentation | same quick command | yes under D-04 [CITED: 26-CONTEXT.md] [VERIFIED: focused pytest run] |
| P26-DEV-11 | Planning artifacts updated | docs/static | `git status --short .planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow .planning/ROADMAP.md .planning/REQUIREMENTS.md` | yes [VERIFIED: codebase grep] |

### Sampling Rate
- **Per task commit:** `python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -q`. [VERIFIED: focused pytest run]
- **Per wave merge:** `make lint` and `make custom-rules`. [VERIFIED: codebase grep]
- **Phase gate:** Focused E2E green plus lint/custom-rules green before `$gsd-verify-work`. [CITED: 26-01-PLAN.md]

### Wave 0 Gaps
- `features/18 Development/03 Architecture Tooling.feature.md` may need an `analyze-gaps` scenario to satisfy P26-DEV-06 literally. [VERIFIED: codebase grep]
- `features/18 Development/04 Compatibility Matrix.feature.md` may need a `--report-e2e-migration-threshold` scenario to satisfy P26-DEV-07 literally. [VERIFIED: codebase grep]
- No missing test framework/config files found. [VERIFIED: pyproject.toml] [VERIFIED: codebase grep]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No auth/session surfaces in Phase 26 CLI test scope. [CITED: 26-SPEC.md] |
| V3 Session Management | no | No session state in Phase 26 scope. [CITED: 26-SPEC.md] |
| V4 Access Control | no | No access-control feature in Phase 26 scope. [CITED: 26-SPEC.md] |
| V5 Input Validation | yes | Exercise CLI argument/file validation through process-level BDD scenarios. [VERIFIED: codebase grep] |
| V6 Cryptography | no | No crypto feature in Phase 26 scope. [CITED: 26-SPEC.md] |

### Known Threat Patterns for Python CLI Test Harness

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Shell injection through command strings | Tampering | Use `shlex.split`, invoke Python modules directly, and avoid shell=True; current harness uses `subprocess.run(..., check=False, capture_output=True, text=True)` without shell for Python commands. [VERIFIED: codebase grep] |
| Repository mutation from scenarios | Tampering | Run in `testdir.tmpdir` and copy only needed paths. [VERIFIED: codebase grep] |
| Platform-specific shell behavior | Denial of Service | Do not execute shell-only audit script in native E2E under D-04. [CITED: 26-CONTEXT.md] |
| Fragile output snapshots | Reliability risk | Use output-fragment matching per D-03. [CITED: 26-CONTEXT.md] |

## Sources

### Primary (HIGH confidence)
- `AGENTS.md` - project constraints, tooling, BDD/ATDD rules, pre-commit rules. [CITED: AGENTS.md]
- `.planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-CONTEXT.md` - locked decisions and deferred shell/probe scope. [CITED: 26-CONTEXT.md]
- `.planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-SPEC.md` - locked requirements and known risk. [CITED: 26-SPEC.md]
- `.planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-01-PLAN.md` - existing implementation plan and verification commands. [CITED: 26-01-PLAN.md]
- `features/18 Development/*.feature.md` - current executable BDD coverage. [VERIFIED: codebase grep]
- `src/pytest_bdd_testing/step/development.py`, `src/pytest_bdd_testing/step/harness.py`, `src/pytest_bdd_testing/case/e2e/conftest.py`, `src/pytest_bdd_testing/case/e2e/feature/test_18_development.py` - current E2E harness implementation. [VERIFIED: codebase grep]
- `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml` - project scripts, dependencies, pytest groups, lint gates. [VERIFIED: codebase grep]
- Focused test run: `python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -q` -> `13 passed in 80.24s`. [VERIFIED: focused pytest run]

### Secondary (MEDIUM confidence)
- `specs/026-dev-scripts-bdd/development_script_exploration.md` - candidate analysis and original priorities. [CITED: specs/026-dev-scripts-bdd/development_script_exploration.md]
- `specs/026-dev-scripts-bdd/plan.md` - implementation proposal and known blocker details. [CITED: specs/026-dev-scripts-bdd/plan.md]
- `.planning/codebase/TESTING.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/STRUCTURE.md` - older codebase maps; useful but partially stale after test package migration. [CITED: .planning/codebase/TESTING.md]
- `cucumber-best-practices` skill - scenario design guidance used only as a style check, not as authoritative package documentation. [VERIFIED: cucumber-best-practices skill]

### Tertiary (LOW confidence)
- None. No web-only or training-only technical claims used. [VERIFIED: research process]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - existing project tools and installed versions were read from `pyproject.toml` and environment probes. [VERIFIED: pyproject.toml] [VERIFIED: environment probe]
- Architecture: HIGH - current feature, step, loader, and harness files were inspected and focused E2E passed. [VERIFIED: codebase grep] [VERIFIED: focused pytest run]
- Pitfalls: MEDIUM - shell/probe risks are documented in context/spec/plan, but exact future failure modes depend on whether D-04 is reopened. [CITED: 26-CONTEXT.md] [CITED: specs/026-dev-scripts-bdd/plan.md]

**Research date:** 2026-06-22
**Valid until:** 2026-07-22 for current repository structure; re-run research sooner if Phase 26 artifacts or D-04 change.
