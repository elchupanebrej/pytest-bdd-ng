# Phase 16: Move vulture dead-code gate from pytest to native pre-commit hook - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Move the existing vulture dead-code quality gate out of pytest and into the existing pre-commit/CI tooling path. This phase owns native vulture configuration, native pre-commit integration, whitelist migration, pytest dead-code test removal, and validation that the resulting pre-commit gate catches unknown dead code.

</domain>

<decisions>
## Implementation Decisions

### Whitelist Shape
- **D-01:** Use native `vulture_whitelist.py` only.
- **D-02:** Do not preserve the existing file/line/message allowlist as custom wrapper behavior.

### Stale False-Positive Cleanup
- **D-03:** Accept native vulture whitelist behavior for stale entries.
- **D-04:** Do not keep exact stale-entry enforcement from the current pytest parametrized test.

### CI Entrypoint
- **D-05:** Run vulture through the existing pre-commit path.
- **D-06:** Add the native `jendrikseipp/vulture` hook to `.pre-commit-config.yaml`; do not add a dedicated tox vulture environment unless planning finds the existing pre-commit env cannot run it.

### Test Removal Boundary
- **D-07:** Delete `tests/cases/unit/unit/test_dead_code.py` entirely.
- **D-08:** Do not replace it with a pytest config sanity test.

### the agent's Discretion
No discretionary areas. User selected explicit decisions for all discussed gray areas.

### Folded Todos
- **Vulture must be run not via pytest but as pre-commit hook** (`.planning/todos/pending/2026-05-20-vulture-must-be-run-not-via-pytest-but-as-pre-commit-hook.md`): This todo is fully in scope. It supplies the implementation direction: native vulture config plus whitelist first, native pre-commit hook, remove pytest-based dead-code test, CI through pre-commit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition
- `.planning/ROADMAP.md` — Phase 16 roadmap entry and dependency on Phase 15.
- `.planning/PROJECT.md` — Project constraints, tooling expectations, and stabilization scope.
- `.planning/STATE.md` — Current milestone state and pending todo context.

### Spike Findings
- `.planning/spikes/004-vulture-pre-commit-hook/README.md` — Validated feasibility and native-first recommendation.
- `.planning/spikes/MANIFEST.md` — Spike index showing Spike 004 as VALIDATED.

### Folded Todo
- `.planning/todos/pending/2026-05-20-vulture-must-be-run-not-via-pytest-but-as-pre-commit-hook.md` — Original task and updated native-vulture recommendation.

### Existing Tooling
- `.pre-commit-config.yaml` — Existing pre-commit hook structure and place to add native vulture hook.
- `pyproject.toml` — Existing dependency and tool configuration surface; add `[tool.vulture]` here.
- `tox.ini` — Existing `py{313,314}-pre-commit` env runs `pre-commit run --all-files`.
- `tests/cases/unit/unit/test_dead_code.py` — Current pytest-based vulture gate to remove and source for whitelist conversion.

### External Docs
- `https://pypi.org/pypi/vulture` — Vulture config, whitelist, `pyproject.toml`, and pre-commit integration docs.
- `https://pre-commit.com/` — Pre-commit hook configuration behavior.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.pre-commit-config.yaml`: Already has third-party hook sections plus a local hook section. Add native vulture as a new third-party repo entry.
- `pyproject.toml`: Existing central config file for pytest, ruff, mypy, packaging, dependencies. Add `[tool.vulture]`.
- `tests/cases/unit/unit/test_dead_code.py`: Source of current false-positive entries. Convert its `KNOWN_FALSE_POSITIVES` names into native whitelist code, then delete the file.

### Established Patterns
- Pre-commit is the project-standard gate for formatting, linting, YAML/TOML validation, docs generation, and heading validation.
- Tox pre-commit env already runs `pre-commit run --all-files`; CI should reuse that path.
- Tests are grouped semantically under `tests/cases/**`, but this gate should leave pytest because it is static analysis, not behavior testing.
- Project commands must use `uv`/tox/pre-commit consistently with existing tooling.

### Integration Points
- Add `jendrikseipp/vulture` repo entry in `.pre-commit-config.yaml`.
- Add `[tool.vulture]` in `pyproject.toml` with `paths = ["src/pytest_bdd", "vulture_whitelist.py"]` and `min_confidence = 80`.
- Add root-level `vulture_whitelist.py`.
- Remove `tests/cases/unit/unit/test_dead_code.py`.
- Verify through `pre-commit run vulture --all-files` and existing pre-commit tox env where practical.

</code_context>

<specifics>
## Specific Ideas

- Use native vulture config and whitelist over wrapper code.
- Wrapper script from `.planning/spikes/004-vulture-pre-commit-hook/` remains a fallback only; it is not preferred for production.
- Preserve current false-positive intent by converting the existing allowlist into native whitelist expressions, not by preserving file/line/message matching.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

### Reviewed Todos (not folded)
- `Improve library typing using best practices from awesome-python-typing`: weak match only through `pytest`; out of scope.
- `Integrate BDD/ATDD tests into development workflow and UAT phase`: weak match only through `phase`; out of scope.
- `Fix Makefile SHELL for cross-platform (Win/Mac/Linux)`: weak match only through `goal`; out of scope.

</deferred>

---

*Phase: 16-Move vulture dead-code gate from pytest to native pre-commit hook*
*Context gathered: 2026-05-25*
