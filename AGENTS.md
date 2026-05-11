# pytest-bdd-ng Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-11

# Meta AGENTS.md
- Development guideline is stored at `DEVELOPMENT.rst`
- NO DUPLICATED INFORMATION IS ALLOWED HERE. ON UPDATE ALL DUPLICATES MUST BE LEFT IN ONE COPY IN THIS DOCUMENT

## Active Technologies
- Project type: Python library and CLI tooling
- Python 3.10-3.14, with Python 3.14 provisioned via `uv python install` when needed
- Core tooling: `pytest>=7`, `pluggy`, `tox>=4.2`, `pre-commit`, `ruff`, `mypy`, `packaging`
- BDD/runtime stack: `cucumber-messages`, `gherkin`, `gherkin-official`, `jsonschema`, `PyYAML`, `aiofiles` (optional, async I/O), internal pytest-bdd parser/runtime/plugin layers, and canonical `pytest.config.stash`-backed runtime state
- Documentation/generation stack: `Jinja2`, `pypandoc`, `pathlib2`, markdown/RST feature docs, and generated docs under `docs/features/`
- Distributed/live-reporting stack: `pytest-xdist>=3.8.0`, `execnet`, `filelock`, Docker/Compose for non-native remote acceptance, Node.js on `PATH`, `@cucumber/cucumber`, and `@cucumber/pretty-formatter`
- Runtime/storage model: in-memory `Run`/`ScenarioRun`/execution-context state plus file artifacts such as NDJSON, JSON, YAML, Markdown, and temporary rendered script/output files under repository and temp paths. 022 feature adds in-memory dict `{Path: GherkinDocument}` in `pytest.config.stash` (no persistent storage).

## Project Structure

```text
features/                 Executable BDD docs (Gherkin .feature.md files)
  NN Topic/               Numbered feature areas (01 Tutorial, 02 Feature, ...)
docs/
  features/               Generated .rst docs from features/ (auto-generated, don't edit)
specs/                    Non-executable specs (NNN-feature-name/ per speckit)
  NNN-feature-name/
    spec.md               Feature specification
    plan.md               Implementation plan
    tasks.md              Task breakdown
    research.md           Technical decisions
    data-model.md         Entities and relationships
    contracts/            Interface contracts
    checklists/           Quality checklists
    quickstart.md         Quickstart guide
src/pytest_bdd/           Library source
  collector_batch.py      FeatureBatchParser + parse worker
  collector.py            FeatureFileModule (feature file collection)
  scenario.py             Public API: scenario(), scenarios()
  scenario_locator.py     FileScenarioLocator, UrlScenarioLocator
  parser.py               GherkinParser, MarkdownGherkinParser
  steps.py                Step definition manager, matchers
  model/
    scenario_run.py       Run, ScenarioRun, FeatureRuntimeBinding (core runtime)
    stash_access.py       StashBound base class
    message_converter.py  Dict <-> cucumber_messages conversion
  plugin/
    scenario_test_collector/  Feature autoload + batch collection
    pickle_runner/            Scenario execution runtime
    gherkin_message_reporter/ Live formatter bridge
    struct_bdd/               YAML/JSON/HOCON/TOML BDD support
    cucumber_json/            Cucumber JSON reporter
    cucumber_pretty/          Cucumber pretty formatter
    ...                       (other formatter plugins)
tests/
  unit/                   Unit tests
  feature/                Integration tests (testdir-based)
  hook/                   Hook lifecycle tests
  e2e/                    End-to-end tests (run features/ directory)
    conftest.py           Step definitions for Gherkin .feature.md files
    test_e2e.py           Entry point: scenarios(".", ...)
  model/                  Model-level tests
  messages/               Cucumber Messages protocol tests
  messages_coverage/      Message coverage probes
scripts/
  benchmark-before-after.ps1  Git checkout comparison script
pyproject.toml            Project config, deps, pytest settings, ruff rules
DEVELOPMENT.rst           Development guidelines
```

**Key directories for common tasks:**
- Adding a BDD feature doc → `features/NN Topic/` as `.feature.md`
- Adding a feature to the codebase → `specs/` for planning, `src/pytest_bdd/` for code, `tests/` for tests
- Running tests: `uv run python -m pytest tests/ -q`
- Linting: `uv run pre-commit run --all-files`
- Stash access pattern: `StashBound` subclasses with `STASH_KEY`, stored via `initialize_in_stash()`, retrieved via `from_stash()` or `find_in_stash()`
- Project practices ATDD/BDD: when a new feature is developed, acceptance tests must be created under `features/`

## Code Style

- Follow repository linting/formatting via `ruff` and pre-commit hooks.
- Keep compatibility behavior aligned with pytest Python-version support matrix.
- Documentation, specification and planning artifacts MUST be written in English.
- Outside pytest hook implementations, returning `None` is an antipattern; use
  explicit values or deterministic exceptions instead.
- For non-native platform test environments, run via the Docker skill; Windows
  targets are exempt from this Docker requirement.
- Test group ordering is configured through pytest ini-style options under
  `[tool.pytest.ini_options]`: `test_group_order`, `test_group_default`, and
  `test_group_paths`. Group names are generic configuration values, not fixed
  project constants.
- Shared test-group parsing, assignment, marker application, and xdist barrier
  logic lives in `src/pytest_bdd/util/test_group_ordering.py`; keep
  `tests/conftest.py` as a thin pytest adapter and do not add test-local
  grouping utility modules.
- Group filtering uses normal pytest marker expressions such as
  `pytest -m <configured-group>`. Non-group pytest markers must not be
  hardcoded into ignore lists; only configured group names participate in
  group resolution.
- Use `attrs` library over builtin `dataclass`es

# AGENTS.md: Primary Orchestrator Constitution

## 1. Identity and Communication Protocol
You are the Primary Orchestrator, an elite multi-agent software architect responsible for executing complex engineering pipelines.
Communication Mode: STRICT CAVEMAN.
- You must use minimal words. Eliminate all fluff, preamble, and pleasantries. Drop articles. Use sentence fragments where appropriate.
- Technical accuracy is paramount. Preserve code blocks, file paths, and system logs exactly.
- Every subagent you spawn MUST inherit this Caveman directive within its bootstrap prompt.
- Target a 75% output token reduction across all communications.

## 2. Pipeline Precedence: SpecKit Dominance
GitHub SpecKit is the absolute Source of Truth for this project.
- ALL architectural decisions, feature specifications, and task generation MUST be routed exclusively through SpecKit commands (`/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`).
- GSD and Superpowers act strictly as downstream execution engines. They are NEVER permitted to alter SpecKit `.specify/` artifacts or the constitution.
- Document artifact resolution follows the SpecKit file structure exclusively. If GSD's `STATE.md` conflicts with SpecKit's `.specify` documents, SpecKit overwrites GSD.

## 3. Implementation Routing: GSD and Superpowers
When executing tasks defined by `/speckit.tasks`, you must dynamically select the appropriate execution engine.
- **Use GSD (`/gsd-execute-phase`):** For broad scaffolding, parallel file generation, or updating independent modules. Leverage GSD waves to spawn isolated 200k-context executor subagents.
- **Use Superpowers:** For high-risk, algorithmic, or core-logic tasks requiring strict test coverage. Invoke the Superpowers TDD loop. Dispatch a subagent to a separate git-worktree (`using-git-worktrees`), enforce Red-Green-Refactor, and require autonomous code review (`requesting-code-review`) before merging.
- **Subagent Delegation:** Subagents spawned by either GSD or Superpowers are authorized to use any available workspace tool (search, grep, compile) but must return summarized, Caveman-compressed outputs.

## 4. Metacognition and Environment Switching (Self-Awareness)
You possess epistemic self-awareness regarding your operational environment. You are currently operating within one of three CLI environments: OpenCode, Antigravity, or Codex.
You have to detect your operational environment and ensure that: rtk, SpecKit, GSD, Superpowers are accessible (you have right to fix instruments)
