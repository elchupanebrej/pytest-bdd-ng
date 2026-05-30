# Phase 16: move-vulture-dead-code-gate-from-pytest-to-native-pre-commit - Research

**Researched:** 2026-05-25
**Domain:** Python static analysis, vulture, pre-commit, pytest quality gates
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use native `vulture_whitelist.py` only.
- **D-02:** Do not preserve the existing file/line/message allowlist as custom wrapper behavior.
- **D-03:** Accept native vulture whitelist behavior for stale entries.
- **D-04:** Do not keep exact stale-entry enforcement from the current pytest parametrized test.
- **D-05:** Run vulture through the existing pre-commit path.
- **D-06:** Add the native `jendrikseipp/vulture` hook to `.pre-commit-config.yaml`; do not add a dedicated tox vulture environment unless planning finds the existing pre-commit env cannot run it.
- **D-07:** Delete `tests/cases/unit/unit/test_dead_code.py` entirely.
- **D-08:** Do not replace it with a pytest config sanity test.

### Folded Todo

- `Vulture must be run not via pytest but as pre-commit hook` is fully in scope.

</user_constraints>

## Summary

Phase 16 is tooling migration. The current dead-code gate lives in `tests/cases/unit/unit/test_dead_code.py`, invokes `python -m vulture src/pytest_bdd --min-confidence 80`, filters findings through `KNOWN_FALSE_POSITIVES`, and reruns vulture for every allowlisted finding. That makes static analysis look like pytest coverage and is slow/noisy.

Vulture's documented native path supports exactly this phase: configure command-line options in `[tool.vulture]`, include source paths and a whitelist file under `paths`, and add the native pre-commit hook from `https://github.com/jendrikseipp/vulture`. Vulture 2.16 is current on PyPI as of 2026-05-25. Vulture recommends whitelist files over `noqa`, `ignore_names`, or `ignore_decorators` when practical because the whitelist is Python syntax and is checked while scanning.

## Current State

| File | Current responsibility | Phase 16 action |
|------|------------------------|-----------------|
| `tests/cases/unit/unit/test_dead_code.py` | Pytest wrapper around vulture, parser, allowlist, stale allowlist checks | Delete |
| `.pre-commit-config.yaml` | Central pre-commit hook config | Add native vulture hook |
| `pyproject.toml` | Tool config and optional test dependencies | Add `[tool.vulture]`; remove vulture from pytest/test dependency surface if no longer needed |
| `tox.ini` | Generic testenv currently installs `vulture` | Remove vulture from generic testenv deps if pytest no longer uses it |
| `vulture_whitelist.py` | Not present | Add root-level native whitelist |
| `uv.lock` | Lockfile for project dependencies | Update only if dependency removal changes lock |

## Vulture Native Behavior

- `pyproject.toml` section: `[tool.vulture]`.
- Config keys match CLI flags with dashes converted to underscores, e.g. `min_confidence`.
- `paths` can include source directories and whitelist files.
- CLI args take precedence over `pyproject.toml`.
- Pre-commit integration uses:

```yaml
repos:
  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.16
    hooks:
      - id: vulture
```

- Exit codes: `0` means no dead code, `1` invalid input, `2` invalid command-line args, `3` dead code found.

## Whitelist Findings

Running `rtk uv run --extra test python -m vulture src/pytest_bdd --min-confidence 80 --make-whitelist` produced these native whitelist entries:

```python
fixturemanager
FunctionType
GherkinDocumentWithURI
AttrsInstance
Match
event
Traversable
fixturefunc
nextitem
module_path
manager
module_path
FunctionType
CodeType
FrameType
FunctionType
MethodType
TracebackType
```

Planner/executor should convert these into `vulture_whitelist.py`. Duplicate names may be collapsed if vulture still passes; keep duplicates only if needed to preserve behavior. Because the user chose native whitelist and native stale behavior, no file/line/message metadata is required.

## Recommended Implementation

Use one implementation plan:

1. Add `vulture_whitelist.py` at repository root from current vulture output.
2. Add `[tool.vulture]` to `pyproject.toml`:

```toml
[tool.vulture]
min_confidence = 80
paths = [
  "src/pytest_bdd",
  "vulture_whitelist.py"
]
```

3. Add native vulture hook to `.pre-commit-config.yaml` using `rev: v2.16`.
4. Remove `tests/cases/unit/unit/test_dead_code.py`.
5. Remove `vulture` from pytest/test dependency surfaces if it is no longer used outside the native hook (`pyproject.toml`, `tox.ini`; update `uv.lock` if needed).
6. Verify through `pre-commit run vulture --all-files`, the existing pre-commit path, and unit collection.

## Risks

| Risk | Mitigation |
|------|------------|
| Native whitelist suppresses by name rather than exact file/line/message | User selected native behavior; verify current vulture output is clean after migration |
| Removing `vulture` dependency changes `uv.lock` | Include lock update in plan if dependency is removed |
| Pre-commit hook creates isolated vulture env, so local direct `python -m vulture` may stop working | Accepted; CI path is pre-commit, not pytest/direct module invocation |
| `.pre-commit-config.yaml` hook ordering could run vulture before format fixes | Place vulture after ruff/format hooks to reduce false findings from auto-fix churn |

## Validation Architecture

| Requirement | Verification |
|-------------|--------------|
| Native hook runs | `rtk uv run pre-commit run vulture --all-files` exits 0 |
| Existing pre-commit env carries CI path | `rtk uv run pre-commit run --files .pre-commit-config.yaml pyproject.toml vulture_whitelist.py` exits 0 |
| Pytest gate removed | `rtk powershell -NoProfile -Command "if (Test-Path tests/cases/unit/unit/test_dead_code.py) { exit 1 }"` exits 0 |
| No lingering pytest-vulture refs | `rtk grep "test_dead_code|KNOWN_FALSE_POSITIVES|python -m vulture|\\\"vulture\\\"" tests pyproject.toml tox.ini` only shows intentional config/hook references |
| Unit collection unaffected | `rtk uv run --extra test python -m pytest tests/cases/unit -m unit -q` passes or shows unrelated baseline failures |

## Sources

- Phase context: `.planning/phases/16-move-vulture-dead-code-gate-from-pytest-to-native-pre-commit/16-CONTEXT.md`
- Spike finding: `.planning/spikes/004-vulture-pre-commit-hook/README.md`
- Folded todo: `.planning/todos/pending/2026-05-20-vulture-must-be-run-not-via-pytest-but-as-pre-commit-hook.md`
- Vulture docs: `https://pypi.org/project/vulture/`
- Pre-commit docs: `https://pre-commit.com/`

## Metadata

**Confidence breakdown:**
- Native vulture config and hook: HIGH.
- Dependency cleanup (`pyproject.toml`, `tox.ini`, `uv.lock`): MEDIUM, because executor must verify no remaining direct vulture invocation requires project dependency.
- Whitelist exact content: MEDIUM, because native whitelist is name-based and executor must run the hook after conversion.

**Research date:** 2026-05-25
**Valid until:** 2026-06-25 for vulture/pre-commit integration details.
