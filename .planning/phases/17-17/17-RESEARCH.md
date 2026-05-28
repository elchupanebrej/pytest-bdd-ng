# Phase 17: 17 - Research

**Researched:** 2026-05-27 [VERIFIED: gsd-sdk init.phase-op]
**Domain:** GitHub Actions, Makefile CI command API, tox/uv/npm workflow validation [VERIFIED: .planning/phases/17-17/17-CONTEXT.md]
**Confidence:** HIGH [VERIFIED: codebase + official docs]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

## Implementation Decisions

### CI Command Boundary
- **D-01:** Keep GitHub Actions setup steps visible in `.github/workflows/main.yml`: checkout, Python setup, Node setup, pandoc setup, and uv setup stay in the workflow.
- **D-02:** Move project-specific commands into Makefile targets. CI should call `make env-install-npm`, `make tox`, `make check-message-schemas`, and `make dist-check` instead of duplicating command bodies.
- **D-03:** Do not collapse the workflow into one opaque `make ci` target. The workflow should remain readable at the phase level while delegating command internals to Makefile.

### Tox Integration
- **D-04:** Add a `tox` target to `Makefile`.
- **D-05:** Use a `GITHUB_ACTIONS` conditional at tox command construction time so CI tox includes `tox-gh-actions`, while local `make tox` stays normal.
- **D-06:** CI should run `make tox`; the workflow should not keep a separate `pip install tox-gh-actions` step.

### Node and Message Schema Setup
- **D-07:** Add `env-install-npm` to `Makefile`.
- **D-08:** `env-install-npm` installs `@cucumber/html-formatter` and `cucumber-html-reporter`.
- **D-09:** Keep `actions/setup-node@v4` in the workflow because runner toolchain setup belongs to GitHub Actions.
- **D-10:** Add `check-message-schemas` as the Makefile target for the generated message schema sync check.

### Workflow Validation
- **D-11:** Add `validate-github-actions` target to `Makefile`.
- **D-12:** `validate-github-actions` runs `act --validate`.
- **D-13:** Target must fail clearly when `act` is missing, with an actionable install hint.
- **D-14:** Phase verification must run `make validate-github-actions`.

### the agent's Discretion

- Exact Makefile conditional syntax for `GITHUB_ACTIONS`.
- Exact target internals for `tox`, `env-install-npm`, `check-message-schemas`, and `validate-github-actions`, provided commands stay equivalent to decisions above.
- Exact workflow step names, provided setup remains visible and project commands call Makefile targets.

### Deferred Ideas (OUT OF SCOPE)

## Deferred Ideas

None — discussion stayed within phase scope.

### Reviewed Todos (not folded)
- **Integrate BDD/ATDD tests into development workflow and UAT phase** — broad process change; not part of CI command deduplication.
- **Vulture must be run not via pytest but as pre-commit hook** — completed Phase 16 scope.
- **Fix Makefile SHELL for cross-platform (Win/Mac/Linux)** — completed Phase 15 scope; decisions carried forward only.
</user_constraints>

## Summary

Use `Makefile` as project-command surface and keep `.github/workflows/main.yml` as runner/toolchain orchestration. Existing workflow already has checkout, Python, Node, pandoc, tox, npm, schema, Codecov, and build steps; Phase 17 should replace only command bodies with `make ...` calls while preserving matrix, setup actions, conditions, and secret env shape. [VERIFIED: .github/workflows/main.yml] [VERIFIED: .planning/phases/17-17/17-CONTEXT.md]

Recommended tox command is a Makefile variable conditional: local `TOX ?= uvx --with tox-uv tox`, CI `TOX ?= uvx --with tox-uv --with tox-gh-actions tox`. `tox-gh-actions` official docs say it must be installed before tox runs, and if tox uses `requires`, plugin loading also needs `tox-gh-actions`; injecting with `uvx --with` satisfies install-before-run without a separate workflow step. [CITED: https://pypi.org/project/tox-gh-actions/3.4.0/] [VERIFIED: tox.ini]

**Primary recommendation:** Add explicit Makefile targets, set CI-only `TOX` via `GITHUB_ACTIONS=true`, update workflow project steps to `make ...`, then validate syntax with `make validate-github-actions`. [VERIFIED: .planning/phases/17-17/17-CONTEXT.md]

## Project Constraints (from AGENTS.md)

- Use `rtk` prefix for shell commands in agent work. [VERIFIED: AGENTS.md]
- Development guidelines live in `DEVELOPMENT.rst`; do not duplicate guideline content in AGENTS updates. [VERIFIED: AGENTS.md]
- Python library supports Python 3.10-3.14; keep compatibility aligned with pytest Python-version matrix. [VERIFIED: AGENTS.md] [VERIFIED: pyproject.toml]
- Follow ruff/pre-commit style. [VERIFIED: AGENTS.md]
- Documentation/spec/planning artifacts must be English. [VERIFIED: AGENTS.md]
- Outside pytest hooks, avoid returning `None`; use explicit values or deterministic exceptions. [VERIFIED: AGENTS.md]
- Use `attrs` over builtin `dataclass` for source-model code; Phase 17 should not add Python model code. [VERIFIED: AGENTS.md]
- Makefile cross-platform work must preserve Git Bash-on-Windows guard from Phase 15. [VERIFIED: Makefile] [VERIFIED: .planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md]
- CI should reuse existing gate paths rather than duplicate logic, matching Phase 16 direction. [VERIFIED: .planning/phases/16-move-vulture-dead-code-gate-from-pytest-to-native-pre-commit/16-CONTEXT.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Runner setup | GitHub Actions | Makefile | Checkout, Python, Node, pandoc, and uv setup are runner provisioning, locked to workflow. [VERIFIED: 17-CONTEXT.md] |
| Project command execution | Makefile | GitHub Actions | tox, npm package install, schema check, and dist check are project commands. [VERIFIED: 17-CONTEXT.md] |
| tox matrix selection | tox/tox-gh-actions | GitHub Actions | `[gh-actions]` maps Python factors; runner matrix supplies Python and OS. [VERIFIED: tox.ini] [CITED: https://pypi.org/project/tox-gh-actions/3.4.0/] |
| Workflow syntax validation | act CLI | Makefile | Target wraps `act --validate` and missing-tool check. [CITED: https://nektosact.com/usage/] |
| Coverage/build semantics | Existing workflow conditions | Makefile target internals | Codecov remains Python 3.14-only; `dist-check` wraps build plus twine check. [VERIFIED: .github/workflows/main.yml] [VERIFIED: Makefile] |

## Standard Stack

### Core

| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| `make` | GNU Make 4.4.1 local | Command API for local and CI project commands. [VERIFIED: local command] | Existing Makefile is established command surface. [VERIFIED: Makefile] |
| `uv` / `uvx` | 0.11.15 local; setup action installs uv in CI | Python tool/package runner. [VERIFIED: local command] | Official uv docs recommend `astral-sh/setup-uv` for GitHub Actions and show `uv run` command usage. [CITED: https://docs.astral.sh/uv/guides/integration/github/] |
| `tox` | latest registry 4.54.0; installed local 4.53.1 | Matrix test runner. [VERIFIED: pip index] | Existing `tox.ini` is project matrix source. [VERIFIED: tox.ini] |
| `tox-uv` | 1.35.2 | tox integration with uv, used by existing `TOX` variable. [VERIFIED: pip index] | Existing Makefile uses `uvx --with tox-uv tox`. [VERIFIED: Makefile] |
| `tox-gh-actions` | 3.5.0 | CI-only tox env selection for GitHub Actions. [VERIFIED: pip index] | Official docs require installing it before `tox` and configure via `[gh-actions]`. [CITED: https://pypi.org/project/tox-gh-actions/3.4.0/] |
| `act` | 0.2.88 local | Local GitHub Actions syntax validation. [VERIFIED: local command] | CLI help supports `--validate`; official docs describe workflow selection and local validation context. [VERIFIED: act --help] [CITED: https://nektosact.com/usage/] |

### Supporting

| Library/Tool | Version | Purpose | When to Use |
|--------------|---------|---------|-------------|
| `@cucumber/html-formatter` | 23.1.0 | HTML formatter npm dependency. [VERIFIED: npm registry] | Install in `env-install-npm`; package name is locked by CONTEXT but legitimacy remains human-checkpoint because Context7 unavailable and package docs not fetched. [ASSUMED] |
| `cucumber-html-reporter` | 7.2.0 | Alternate HTML reporter npm dependency. [VERIFIED: npm registry] | Install in `env-install-npm`; package name is locked by CONTEXT but legitimacy remains human-checkpoint. [ASSUMED] |
| `build` | 1.5.0 | Python dist build tool. [VERIFIED: pip index] | Already wrapped by `make build`. [VERIFIED: Makefile] |
| `twine` | 6.2.0 | Dist metadata check. [VERIFIED: pip index] | Already wrapped by `make dist-check`. [VERIFIED: Makefile] |
| `codecov` | 2.1.13 | Existing coverage upload command. [VERIFIED: pip index] | Keep workflow `codecov` step condition unchanged. [VERIFIED: .github/workflows/main.yml] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `uvx --with tox-uv --with tox-gh-actions tox` | Separate `pip install tox tox-gh-actions tox-uv` step | Separate step duplicates CI install logic and violates D-06. [VERIFIED: 17-CONTEXT.md] |
| `make validate-github-actions` | Direct `act --validate` in docs only | Direct command lacks missing-tool hint required by D-13. [VERIFIED: 17-CONTEXT.md] |
| `make ci` | Single opaque Makefile target | Explicitly out by D-03. [VERIFIED: 17-CONTEXT.md] |

**Installation:**
```bash
# Local tools, if missing. [ASSUMED: install channels vary by OS]
uv tool install act
uv tool install tox

# npm formatter dependencies inside Makefile target. [VERIFIED: 17-CONTEXT.md]
npm install --no-save @cucumber/html-formatter cucumber-html-reporter
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `tox` | PyPI | old/stable [VERIFIED: pip index] | not measured [ASSUMED] | tox-dev/tox [ASSUMED] | OK [VERIFIED: slopcheck] | Approved |
| `tox-uv` | PyPI | current [VERIFIED: pip index] | not measured [ASSUMED] | tox-dev/tox-uv [ASSUMED] | OK [VERIFIED: slopcheck] | Approved |
| `tox-gh-actions` | PyPI | latest 3.5.0 published by registry [VERIFIED: pip index] | not measured [ASSUMED] | ymyzk/tox-gh-actions [CITED: https://pypi.org/project/tox-gh-actions/3.4.0/] | OK [VERIFIED: slopcheck] | Approved |
| `build` | PyPI | current [VERIFIED: pip index] | not measured [ASSUMED] | pypa/build [ASSUMED] | OK [VERIFIED: slopcheck] | Existing approved |
| `twine` | PyPI | current [VERIFIED: pip index] | not measured [ASSUMED] | pypa/twine [ASSUMED] | OK [VERIFIED: slopcheck] | Existing approved |
| `codecov` | PyPI | current but legacy single available version [VERIFIED: pip index] | not measured [ASSUMED] | codecov/codecov-python [ASSUMED] | OK [VERIFIED: slopcheck] | Existing approved |
| `@cucumber/html-formatter` | npm | created 2020-01-10; modified 2026-04-13 [VERIFIED: npm registry] | not measured due RTK JSON filtering [ASSUMED] | github.com/cucumber/html-formatter [VERIFIED: npm registry] | PyPI SLOP only, wrong ecosystem [VERIFIED: slopcheck output] | Keep per D-08; planner should add human verify checkpoint |
| `cucumber-html-reporter` | npm | created 2016-06-26; modified 2024-10-01 [VERIFIED: npm registry] | not measured due RTK JSON filtering [ASSUMED] | github.com/gkushang/cucumber-html-reporter [VERIFIED: npm registry] | PyPI SLOP only, wrong ecosystem [VERIFIED: slopcheck output] | Keep per D-08; planner should add human verify checkpoint |

**Packages removed due to slopcheck [SLOP] verdict:** none; npm packages were incorrectly checked against PyPI by slopcheck and are locked by D-08. [VERIFIED: slopcheck output] [VERIFIED: 17-CONTEXT.md]
**Packages flagged as suspicious [SUS]:** `@cucumber/html-formatter`, `cucumber-html-reporter` need human verification before changing npm install semantics. [ASSUMED]

## Architecture Patterns

### System Architecture Diagram

```text
GitHub event
  -> matrix job (os, python-version)
  -> setup actions remain visible:
       checkout -> setup-python -> setup-node -> setup-pandoc -> setup-uv
  -> project commands:
       make env-install-npm
       make tox
          -> GITHUB_ACTIONS=true?
             yes -> uvx --with tox-uv --with tox-gh-actions tox
             no  -> uvx --with tox-uv tox
          -> tox.ini [gh-actions] maps Python factor
          -> tox platform factors gate OS-specific envs
       make check-message-schemas (3.14 + ubuntu only)
       codecov (3.14 only)
       make dist-check (3.14 only, keeps TWINE_* env)
```

### Recommended Project Structure

```text
Makefile                    # Add CI project-command targets. [VERIFIED: codebase]
.github/workflows/main.yml  # Keep setup actions; replace run bodies with make calls. [VERIFIED: codebase]
tox.ini                     # Keep existing [gh-actions] mapping. [VERIFIED: codebase]
tests/cases/contract/...    # Update workflow contract test if command text assertion changes. [VERIFIED: tests/cases/contract/generation/test_template_packaging.py]
```

### Pattern 1: CI-only tox plugin injection

**What:** Construct `TOX` differently when `GITHUB_ACTIONS=true`. [VERIFIED: 17-CONTEXT.md]
**When to use:** Only for `make tox`; do not change local tox defaults. [VERIFIED: 17-CONTEXT.md]

```make
# Source: tox-gh-actions docs + existing Makefile TOX variable.
ifeq ($(GITHUB_ACTIONS),true)
  TOX ?= uvx --with tox-uv --with tox-gh-actions tox
else
  TOX ?= uvx --with tox-uv tox
endif

tox: env-check-tox
	$(TOX)
```

**Implementation note:** Put CI override before first use of `$(TOX)`; use `?=` consistently so callers can still override `TOX`. [VERIFIED: Makefile]

### Pattern 2: Workflow setup stays declarative

**What:** Keep setup actions as separate steps, then call Makefile targets for project commands. [VERIFIED: 17-CONTEXT.md]

```yaml
# Source: uv GitHub Actions guide + Phase 17 decisions.
- name: Set up uv
  uses: astral-sh/setup-uv@v6

- name: Install npm dependencies
  run: make env-install-npm

- name: Test with tox
  run: make tox
```

**Version note:** Official uv docs show pinning `astral-sh/setup-uv` to a commit as best practice; using a version tag is simpler but weaker supply-chain control. [CITED: https://docs.astral.sh/uv/guides/integration/github/]

### Pattern 3: Clear missing-tool validation target

**What:** Fail before invoking `act` when missing, with install URL. [VERIFIED: 17-CONTEXT.md]

```make
validate-github-actions:
	@command -v act >/dev/null 2>&1 || { echo "ERROR: act missing. Install act: https://nektosact.com/installation/"; exit 1; }
	act --validate
```

**Local note:** On this machine, `act --help` lists `--validate` as "validate workflows". [VERIFIED: act --help]

### Anti-Patterns to Avoid

- **Hiding setup in Makefile:** setup actions must stay in workflow. [VERIFIED: 17-CONTEXT.md]
- **Installing `tox-gh-actions` in workflow:** use Makefile `TOX` command construction instead. [VERIFIED: 17-CONTEXT.md]
- **Changing matrix or Codecov gates:** out of scope. [VERIFIED: 17-CONTEXT.md]
- **Running full `act` matrix locally:** phase only requires syntax validation. [VERIFIED: 17-CONTEXT.md]
- **Using npm installs that dirty repo state locally:** prefer `npm install --no-save ...` unless planner intentionally wants package-lock. [ASSUMED]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| tox env selection in GitHub Actions | custom shell matrix parser | `tox-gh-actions` | Existing `tox.ini` has `[gh-actions]`; plugin handles Python factor mapping. [VERIFIED: tox.ini] [CITED: https://pypi.org/project/tox-gh-actions/3.4.0/] |
| uv installation in CI | curl/pip install uv script | `astral-sh/setup-uv` | Official uv docs recommend setup action and describe cache support. [CITED: https://docs.astral.sh/uv/guides/integration/github/] |
| workflow syntax validation | custom YAML parser | `act --validate` | `act` CLI exposes workflow validation. [VERIFIED: act --help] |
| Python package build checking | custom wheel/sdist inspection | `make dist-check` | Existing target wraps `build` and `twine check`. [VERIFIED: Makefile] |
| message schema drift check | new script path | `pytest_bdd.script.sync_messages_contract_schemas --check` via Makefile | Existing workflow/test expect this script. [VERIFIED: .github/workflows/main.yml] [VERIFIED: tests/cases/contract/generation/test_template_packaging.py] |

**Key insight:** This phase is command de-duplication, not CI redesign. Preserve workflow shape; centralize command bodies only. [VERIFIED: 17-CONTEXT.md]

## Common Pitfalls

### Pitfall 1: `TOX ?=` override order

**What goes wrong:** CI still runs without `tox-gh-actions`. [ASSUMED]
**Why it happens:** `TOX ?=` set once before conditional, then second `?=` does not override. [ASSUMED]
**How to avoid:** Use `ifeq` to choose one `TOX ?=` assignment, or use `TOX_CI_WITH` variable appended before assignment. [ASSUMED]
**Warning signs:** CI log says tox-gh-actions will not override envlist or runs unexpected env count. [CITED: https://pypi.org/project/tox-gh-actions/3.4.0/]

### Pitfall 2: OS matrix factor mismatch

**What goes wrong:** tox may skip platform-mismatched envs or run more envs than expected. [ASSUMED]
**Why it happens:** Existing `[gh-actions]` maps Python factor only; OS targeting is in tox env names and `platform` selectors. [VERIFIED: tox.ini]
**How to avoid:** Do not change matrix; observe first CI run. Add `[gh-actions:env]` only if planning explicitly expands scope. [ASSUMED]
**Warning signs:** tox output reports skipped `platform mismatch` envs or no envs selected. [ASSUMED]

### Pitfall 3: `uv run tox` versus `uvx --with tox-uv tox`

**What goes wrong:** CI may run a tox binary without required plugin set. [ASSUMED]
**Why it happens:** `uv run tox` uses project environment, while Makefile already standardizes on `uvx --with tox-uv tox`. [VERIFIED: Makefile] [VERIFIED: .github/workflows/main.yml]
**How to avoid:** CI calls `make tox`; Makefile owns exact `TOX`. [VERIFIED: 17-CONTEXT.md]
**Warning signs:** tox cannot import plugin or ignores `[gh-actions]`. [ASSUMED]

### Pitfall 4: npm target creates local artifacts

**What goes wrong:** local `make env-install-npm` creates `node_modules` or lockfiles. [ASSUMED]
**Why it happens:** Repo has no package.json/package-lock detected by PowerShell probe. [VERIFIED: local filesystem probe]
**How to avoid:** Prefer `npm install --no-save @cucumber/html-formatter cucumber-html-reporter`; keep `node_modules` ignored if already ignored. [ASSUMED]
**Warning signs:** `git status` shows package-lock/package.json after target. [ASSUMED]

### Pitfall 5: Codecov/build semantics drift

**What goes wrong:** Codecov or dist-check runs on wrong matrix rows. [ASSUMED]
**Why it happens:** Replacing steps can accidentally drop `if:` conditions or `TWINE_*` env. [VERIFIED: .github/workflows/main.yml]
**How to avoid:** Preserve `if: matrix.python-version == '3.14'` and build env block; only replace build commands with `make dist-check`. [VERIFIED: 17-CONTEXT.md]
**Warning signs:** Windows/macOS build check runs unexpectedly or PyPI token env removed. [ASSUMED]

## Code Examples

### Makefile target set

```make
# Source: existing Makefile patterns and Phase 17 locked decisions.
.PHONY: tox env-install-npm check-message-schemas validate-github-actions

ifeq ($(GITHUB_ACTIONS),true)
  TOX ?= uvx --with tox-uv --with tox-gh-actions tox
else
  TOX ?= uvx --with tox-uv tox
endif

tox: env-check-tox
	$(TOX)

env-install-npm:
	npm install --no-save @cucumber/html-formatter cucumber-html-reporter
	npm list

check-message-schemas: env-check
	uv run python -m pytest_bdd.script.sync_messages_contract_schemas --check

validate-github-actions:
	@command -v act >/dev/null 2>&1 || { echo "ERROR: act missing. Install act: https://nektosact.com/installation/"; exit 1; }
	act --validate
```

### Workflow command replacement

```yaml
# Source: existing main.yml and uv official docs.
- name: Set up uv
  uses: astral-sh/setup-uv@v6

- name: Install npm dependencies
  run: make env-install-npm

- name: Test with tox
  run: make tox

- name: Generated messages schemas are up to date
  if: matrix.python-version == '3.14' && matrix.os == 'ubuntu-latest'
  run: make check-message-schemas

- name: Build checking
  if: "matrix.python-version == '3.14'"
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
  run: make dist-check
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pip install uv` in CI | `astral-sh/setup-uv` action | uv docs current as of 2026-05-27 [CITED: https://docs.astral.sh/uv/guides/integration/github/] | Cleaner runner setup and optional uv cache. |
| Workflow duplicates project commands | Workflow calls Makefile project targets | Phase 17 locked decision [VERIFIED: 17-CONTEXT.md] | Less CI/local drift. |
| Direct `act --validate` by human memory | `make validate-github-actions` | Phase 17 locked decision [VERIFIED: 17-CONTEXT.md] | Repeatable validation with missing-tool hint. |

**Deprecated/outdated:**
- `pip install uv` inside workflow project dependency step is replaced by `astral-sh/setup-uv`. [CITED: https://docs.astral.sh/uv/guides/integration/github/] [VERIFIED: .github/workflows/main.yml]
- Separate workflow `pip install tox-gh-actions` step is replaced by CI-only `TOX` construction. [VERIFIED: 17-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `npm install --no-save` best preserves repo cleanliness without changing formatter availability. | Architecture Patterns / Pitfalls / Code Examples | CI formatter install may differ from existing workflow behavior. |
| A2 | Existing tox platform selectors are enough for OS matrix without adding `[gh-actions:env]`. | Common Pitfalls | CI may run too many/skipped envs. |
| A3 | npm package legitimacy should be human-verified because Context7 unavailable and slopcheck checked PyPI, not npm. | Package Legitimacy Audit | Planner may need checkpoint before npm target lands. |
| A4 | Codecov CLI command remains acceptable as existing semantics. | Standard Stack / Pitfalls | Codecov upload action might be preferred later, but out of scope. |

## Open Questions (RESOLVED)

1. **Pin `astral-sh/setup-uv` by tag or commit?**
   - What we know: uv official docs show commit-pinned example and call specific uv version pinning best practice. [CITED: https://docs.astral.sh/uv/guides/integration/github/]
   - RESOLVED: Use `astral-sh/setup-uv@v6`, following current workflow action tag style. Do not switch this phase to commit pinning; commit pin hardening is outside Phase 17 scope. [VERIFIED: 17-CONTEXT.md] [ASSUMED: project action pin policy]

2. **Should npm installs be `--no-save`?**
   - What we know: Existing workflow runs plain `npm install` commands; local repo has no package.json/package-lock found by probe. [VERIFIED: .github/workflows/main.yml] [VERIFIED: local filesystem probe]
   - RESOLVED: Use `npm install --no-save @cucumber/html-formatter cucumber-html-reporter` in `env-install-npm` to avoid repository package-file drift while preserving current ephemeral CI dependency semantics. [VERIFIED: 17-CONTEXT.md] [ASSUMED: no committed npm package files desired]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | Makefile tox/build/schema commands | yes | 0.11.15 local | `astral-sh/setup-uv` in CI [VERIFIED: local command] [CITED: https://docs.astral.sh/uv/guides/integration/github/] |
| `uvx` | Makefile `TOX` command | yes | 0.11.15 local | install uv [VERIFIED: local command] |
| `make` | all targets | yes | GNU Make 4.4.1 local | none [VERIFIED: local command] |
| `node` | npm formatter packages | yes | v25.2.1 local | setup-node in CI [VERIFIED: local command] [VERIFIED: .github/workflows/main.yml] |
| `npm` | `env-install-npm` | yes | 11.6.2 local | setup-node in CI [VERIFIED: local command] [VERIFIED: .github/workflows/main.yml] |
| `act` | `validate-github-actions` | yes | 0.2.88 local | fail with install hint if missing [VERIFIED: local command] |
| `ctx7` | docs lookup fallback | no | - | official docs via web [VERIFIED: local command] |
| graphify | graph context | disabled | - | codebase docs/context reads [VERIFIED: gsd-tools graphify status] |

**Missing dependencies with no fallback:**
- None for this machine; `act` is installed. [VERIFIED: local command]

**Missing dependencies with fallback:**
- `ctx7` CLI missing; official docs were fetched via web. [VERIFIED: local command] [CITED: https://docs.astral.sh/uv/guides/integration/github/]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest via tox/make [VERIFIED: pyproject.toml] [VERIFIED: tox.ini] |
| Config file | `pyproject.toml`, `tox.ini` [VERIFIED: codebase] |
| Quick run command | `make validate-github-actions` [VERIFIED: 17-CONTEXT.md] |
| Full suite command | `make tox` [VERIFIED: 17-CONTEXT.md] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| PH17-CI-01 | Workflow setup actions remain visible and project commands call Makefile targets. [VERIFIED: 17-CONTEXT.md] | contract/manual review | `make validate-github-actions` | no Wave 0 |
| PH17-CI-02 | CI tox uses `tox-gh-actions`; local tox does not. [VERIFIED: 17-CONTEXT.md] | Makefile smoke/manual | `GITHUB_ACTIONS=true make -n tox` and `make -n tox` | no Wave 0 |
| PH17-CI-03 | Message schema check calls existing sync script with `--check`. [VERIFIED: tests/cases/contract/generation/test_template_packaging.py] | contract | `uv run python -m pytest tests/cases/contract/generation/test_template_packaging.py -q` | yes |
| PH17-CI-04 | act validation target fails clearly when missing and runs `act --validate` when present. [VERIFIED: 17-CONTEXT.md] | smoke/manual | `make validate-github-actions` | no Wave 0 |

### Sampling Rate

- **Per task commit:** `make validate-github-actions` [VERIFIED: 17-CONTEXT.md]
- **Per wave merge:** `make validate-github-actions` plus `uv run python -m pytest tests/cases/contract/generation/test_template_packaging.py -q` [VERIFIED: local grep]
- **Phase gate:** `make validate-github-actions`; inspect `make -n tox` with and without `GITHUB_ACTIONS=true`. [ASSUMED]

### Wave 0 Gaps

- [ ] Add/update contract coverage for Makefile targets if planner wants automated target existence checks. [ASSUMED]
- [ ] Update `tests/cases/contract/generation/test_template_packaging.py` if workflow text assertion changes from direct script command to `make check-message-schemas`. [VERIFIED: tests/cases/contract/generation/test_template_packaging.py]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | no app auth in phase [VERIFIED: .planning/codebase/INTEGRATIONS.md] |
| V3 Session Management | no | no sessions in phase [VERIFIED: .planning/codebase/INTEGRATIONS.md] |
| V4 Access Control | no | no access-control code in phase [VERIFIED: .planning/codebase/INTEGRATIONS.md] |
| V5 Input Validation | yes | validate workflow YAML via `act --validate`; keep shell inputs static. [VERIFIED: act --help] |
| V6 Cryptography | yes, secrets handling only | preserve existing `TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}`; do not echo secrets. [VERIFIED: .github/workflows/main.yml] |

### Known Threat Patterns for GitHub Actions/Makefile

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret leakage in local `act` runs | Information Disclosure | `validate-github-actions` must run only `act --validate`, not full jobs needing secrets. [VERIFIED: 17-CONTEXT.md] [CITED: https://nektosact.com/usage/] |
| Supply-chain drift from unpinned action tags | Tampering | Prefer pinned action version/commit; at minimum use official `astral-sh/setup-uv`. [CITED: https://docs.astral.sh/uv/guides/integration/github/] |
| Shell injection through Make variables | Tampering | Keep target commands static; avoid interpolating untrusted event data. [ASSUMED] |
| npm package confusion | Tampering | Human-verify npm packages before changing install target; slopcheck was PyPI-only for scoped npm names. [VERIFIED: slopcheck output] |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/17-17/17-CONTEXT.md` - locked decisions, scope, folded todo. [VERIFIED: codebase read]
- `Makefile` - existing targets, `TOX`, `dist-check`, schema sync target. [VERIFIED: codebase read]
- `.github/workflows/main.yml` - current workflow matrix and command bodies. [VERIFIED: codebase read]
- `tox.ini` - env list, `[gh-actions]`, platform factors. [VERIFIED: codebase read]
- `pyproject.toml` - Python support, pytest config, package extras. [VERIFIED: codebase read]
- `tests/cases/contract/generation/test_template_packaging.py` - existing workflow contract assertion. [VERIFIED: codebase read]
- uv GitHub Actions docs - `astral-sh/setup-uv`, setup-python integration, caching. [CITED: https://docs.astral.sh/uv/guides/integration/github/]
- tox-gh-actions PyPI docs - usage, `[gh-actions]`, install-before-tox, tox `requires` note. [CITED: https://pypi.org/project/tox-gh-actions/3.4.0/]
- act docs and local help - workflow handling, secrets caution, `--validate` flag. [CITED: https://nektosact.com/usage/] [VERIFIED: act --help]

### Secondary (MEDIUM confidence)

- npm registry metadata for `@cucumber/html-formatter` and `cucumber-html-reporter`. [VERIFIED: npm registry]
- pip registry metadata for `tox`, `tox-uv`, `tox-gh-actions`, `codecov`, `build`, `twine`. [VERIFIED: pip index]
- slopcheck output for PyPI packages. [VERIFIED: slopcheck]

### Tertiary (LOW confidence)

- `npm install --no-save` recommendation for local cleanliness. [ASSUMED]
- OS-factor behavior under current tox-gh-actions mapping until first CI run observes it. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - core tools verified in codebase, registry, and official docs; npm legitimacy requires checkpoint. [VERIFIED: codebase + docs]
- Architecture: HIGH - phase decisions are locked and current workflow/Makefile are simple integration points. [VERIFIED: 17-CONTEXT.md]
- Pitfalls: MEDIUM - main risks are inferred from tox/Makefile behavior and need CI observation. [ASSUMED]

**Research date:** 2026-05-27 [VERIFIED: current date]
**Valid until:** 2026-06-03 for action/package versions; phase decisions remain valid until changed. [ASSUMED]
