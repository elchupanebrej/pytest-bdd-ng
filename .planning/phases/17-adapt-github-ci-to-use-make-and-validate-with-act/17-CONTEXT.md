# Phase 17: Adapt GitHub CI to use make and validate with act - Context

**Gathered:** 2026-05-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Adapt the main GitHub Actions workflow to reuse Makefile targets for project-specific commands, while keeping GitHub Actions responsible for runner/toolchain setup. This phase owns Makefile CI targets, workflow command replacement, npm formatter setup target, message schema check target, tox target behavior under `GITHUB_ACTIONS`, and local workflow validation through `act --validate`.

Out of scope: changing the CI matrix, changing test coverage policy, restructuring tox environments, changing package release semantics, or replacing GitHub Actions setup actions with Makefile-managed provisioning.

</domain>

<decisions>
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

### Folded Todos
- **Adapt GitHub CI to use make and validate with act** (`.planning/todos/pending/2026-05-27-adapt-github-ci-to-use-make.md`): This todo is Phase 17 scope. It supplies the implementation checklist: add Makefile targets, update `.github/workflows/main.yml`, use `astral-sh/setup-uv`, and validate through `act --validate`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition and Folded Todo
- `.planning/ROADMAP.md` — Phase 17 entry and dependency on Phase 16. Roadmap title is placeholder; this context locks the real phase scope.
- `.planning/todos/pending/2026-05-27-adapt-github-ci-to-use-make.md` — Original captured task and implementation checklist.
- `.planning/PROJECT.md` — Project constraints, tooling expectations, and core value.
- `.planning/REQUIREMENTS.md` — Requirement traceability and deferred testing concerns.

### Prior Phase Decisions
- `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-CONTEXT.md` — Makefile as cross-platform command API, explicit env-check targets, loud failure behavior.
- `.planning/phases/16-move-vulture-dead-code-gate-from-pytest-to-native-pre-commit/16-CONTEXT.md` — CI should reuse existing gate paths rather than duplicate tooling logic.

### Codebase Maps
- `.planning/codebase/STACK.md` — CI toolchain, uv/tox/npm/pandoc dependencies, GitHub Actions summary.
- `.planning/codebase/INTEGRATIONS.md` — Main workflow details, Codecov, PyPI build validation, message schema sync integration.
- `.planning/codebase/TESTING.md` — Test commands and tox usage.

### Source and Configuration
- `.github/workflows/main.yml` — Main workflow to update.
- `Makefile` — Existing command surface; add CI-oriented targets here.
- `tox.ini` — Tox environment mapping and tox-gh-actions behavior context.
- `pyproject.toml` — Project dependencies and tooling configuration.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Makefile` already centralizes tox, env-check, build, dist-check, schema sync, and platform test commands.
- `.github/workflows/main.yml` already has the correct matrix and setup sequence, but duplicates project command bodies.
- `dist-check` target already wraps build plus `twine check`.
- `sync-message-schemas` target already runs `pytest_bdd.script.sync_messages_contract_schemas`; `check-message-schemas` can wrap check mode rather than inventing a new script path.

### Established Patterns
- Makefile uses explicit `env-check*` and `env-install*` targets.
- Makefile targets should fail loudly with actionable error messages when required tools are absent.
- `uvx --with tox-uv tox` is the existing tox command surface.
- GitHub Actions setup actions should manage runner toolchains; Makefile should manage project commands.
- CI-only behavior should be guarded by `GITHUB_ACTIONS`, not by changing local defaults.

### Integration Points
- `.github/workflows/main.yml`: replace custom pip/npm/test/build command bodies with `make` calls after setup actions.
- `Makefile`: add `tox`, `env-install-npm`, `check-message-schemas`, and `validate-github-actions` to `.PHONY`.
- `Makefile`: adjust `TOX` construction under `GITHUB_ACTIONS=true` to include `tox-gh-actions`.
- `Makefile`: keep `dist-check` as the build validation command CI calls on Python 3.14.

</code_context>

<specifics>
## Specific Ideas

- Prefer `astral-sh/setup-uv` in workflow setup, then Makefile targets for commands.
- Replace schema check body with `make check-message-schemas` on Python 3.14 + Ubuntu only.
- Replace build/twine body with `make dist-check` on Python 3.14 only, preserving PyPI token environment if still required by existing workflow semantics.
- `validate-github-actions` should only validate workflow syntax; it should not try to run the full matrix locally.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

### Reviewed Todos (not folded)
- **Integrate BDD/ATDD tests into development workflow and UAT phase** — broad process change; not part of CI command deduplication.
- **Vulture must be run not via pytest but as pre-commit hook** — completed Phase 16 scope.
- **Fix Makefile SHELL for cross-platform (Win/Mac/Linux)** — completed Phase 15 scope; decisions carried forward only.

</deferred>

---

*Phase: 17-adapt-github-ci-to-use-make-and-validate-with-act*
*Context gathered: 2026-05-27*
