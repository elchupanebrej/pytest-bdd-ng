## User Constraints

- Phase 28 is the `pytest_bdd_toolchain` rename/extraction phase; `28-SPEC.md` and `28-CONTEXT.md` are authoritative. The old "implement all 24 feature specs" Phase 28 scope was deleted and must not guide planning. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Implement the rename as one atomic change rather than multiple GSD plans or staged checkpoint tasks. The phase is not done until the full `28-SPEC.md` validation passes. If validation exposes blockers, fix forward within the same plan instead of reverting at first failure. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- This is a clean break: no backward compatibility package, no deprecation warnings, no wrapper package, and `python -c "import pytest_bdd_testing"` must fail with `ImportError`. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md] [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-SPEC.md]
- Old-name references must be removed from active code, config, docs, features, root docs, current roadmap, current context, and current spec surfaces. Historical `.planning/phases/*` summaries and audit records may keep old-name references when they document past states. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Replace invalid test acceptance targets with `uv run python -m pytest src/pytest_bdd_toolchain/case -q --tb=short --no-header`. Scoped `rg` checks must avoid historical `.planning/phases/*` audit records. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Moved scripts must not inherit broad `scripts/*` ignores as a directory-level policy. Try to remove tool-module ignores and fix lint issues as best effort; if strict cleanup is too large, use narrow local `# noqa` comments with reasons. Do not add a directory-level `src/pytest_bdd_toolchain/tool/**` ignore fallback. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Each `pbt-* --help` command needs a proper help path that exits 0 and shows meaningful usage/help without running the tool's main side effects. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Remove the package discovery exclusion for the renamed toolchain package, remove the broad mypy exclusion for it, and update `testpaths`, `test_group_paths`, architecture config roots, quality gate commands, and script entrypoints to the new package path. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]

## Summary

Phase 28 is a high-blast-radius mechanical rename plus script packaging pass. The current test/tooling package lives at `src/pytest_bdd_testing/`, is explicitly excluded from setuptools discovery, is broadly excluded from mypy, and is referenced throughout pytest config, Ruff ignores, Pylint custom checkers, GitHub workflows, BDD feature docs, generated architecture docs, and active planning/codebase docs. [VERIFIED: pyproject.toml] [VERIFIED: .pre-commit-config.yaml] [VERIFIED: .github/workflows/tests.yml]

There are exactly 11 top-level development scripts in `scripts/`, matching the expected `pbt-*` entrypoint list from the phase context and rename spec. [VERIFIED: scripts/] [VERIFIED: docs/superpowers/specs/2026-06-24-rename-pytest-bdd-testing-to-toolchain.md]

The main implementation risk is not the directory rename itself; it is landing an internally consistent final state where imports, pytest plugin strings, Docker resource paths, generated docs, package data, command help behavior, and lint/type configs agree. A scoped active-surface scan, excluding historical phase artifacts and bytecode/cache files, currently finds old package/script references across active files. [VERIFIED: src/pytest_bdd_testing/] [VERIFIED: docs/architecture/OBJECT_MAP.md] [VERIFIED: features/18 Development/11 Tests.feature.md]

Note: this checkout has `README.md`, not `README.rst`, and no `CHANGES.rst` file was present during research. Treat `README.md` as the active root readme surface and do not create missing `.rst` files just to satisfy the file list. [VERIFIED: README.md]

## Architectural Responsibility Map

| Area | Current responsibility | Phase 28 target | Primary surfaces |
| --- | --- | --- | --- |
| Package rename | `src/pytest_bdd_testing/` owns test harness helpers, step definitions, resources, contracts, and test cases. [VERIFIED: src/pytest_bdd_testing/] | Rename to `src/pytest_bdd_toolchain/`; update all imports, pytest plugin strings, patch targets, Docker copy paths, docs, and config. | `src/pytest_bdd_testing/`, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/`, `features/`, `docs/` |
| Script entrypoints | 11 standalone files live in `scripts/`, with mixed CLI behavior and broad Ruff ignore. [VERIFIED: scripts/] [VERIFIED: pyproject.toml] | Move into `src/pytest_bdd_toolchain/tool/` and register all 11 `pbt-*` commands under `[project.scripts]`; remove `scripts/` if empty. | `scripts/*.py`, `src/pytest_bdd_toolchain/tool/`, `[project.scripts]` |
| Test package path migration | Pytest config, workflows, feature docs, and tests point at `src/pytest_bdd_testing/case`. [VERIFIED: pyproject.toml] [VERIFIED: .github/workflows/tests.yml] | Move to `src/pytest_bdd_toolchain/case`; update `testpaths`, `test_group_paths`, workflow report paths, E2E feature expectations, and acceptance commands. | `pyproject.toml`, `.github/workflows/tests.yml`, `features/18 Development/11 Tests.feature.md`, `docs/features/18 Development/11 Tests.feature.md` |
| Active-reference cleanup | Old-name/script references exist in source, docs, generated architecture docs, current planning/codebase docs, and workflow files. [VERIFIED: docs/architecture/OBJECT_MAP.md] [VERIFIED: .planning/ROADMAP.md] | Remove active references while preserving legitimate historical `.planning/phases/*` audit records. Generated docs may need regeneration or direct update depending on project convention. | `src/`, `docs/`, `features/`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/codebase/`, `.planning/intel/`, `.planning/todos/` |
| Validation | Existing acceptance examples include some stale or too-broad checks. [VERIFIED: docs/superpowers/specs/2026-06-24-rename-pytest-bdd-testing-to-toolchain.md] | Validate import break, import success, all entrypoint help paths, scoped pytest target, lint/type/package config, and scoped old-name absence excluding historical records. | `uv run python -m pytest`, `tox`, `uv run ruff`, `uv run mypy`, `uv run pylint`, scoped `rg` |

### Runtime State Inventory

| State category | Inventory | Phase 28 implications |
| --- | --- | --- |
| In-repo state | Source tree under `src/pytest_bdd_testing/`, script files under `scripts/`, package data templates, Docker assets, BDD feature files, generated docs, workflows, config, and planning docs. [VERIFIED: src/pytest_bdd_testing/] [VERIFIED: scripts/] | Rename/move must keep relative resource lookups correct. Dockerfiles and `Path(__file__)`/repository-root calculations are more fragile than plain imports. |
| Generated/cache state | `__pycache__` directories and `.pyc` files exist under `src/pytest_bdd_testing/`; generated architecture docs contain old paths and package names. [VERIFIED: src/pytest_bdd_testing/__pycache__/] [VERIFIED: docs/architecture/OBJECT_MAP.md] | Do not migrate bytecode. Exclude cache files from `rg`; delete stale cache directories if they would leave an importable old package artifact. Regenerate or update architecture docs so active docs do not keep stale names. |
| Config state | `pyproject.toml` controls project scripts, architecture roots, mypy exclude/packages, pytest paths/groups, quality gate command, Ruff per-file ignores, package data, and setuptools discovery exclusion. `.pre-commit-config.yaml` controls local Pylint path. [VERIFIED: pyproject.toml] [VERIFIED: .pre-commit-config.yaml] | Config must be updated in one pass before validation; otherwise pytest, Pylint, packaging, and entrypoints will disagree. |
| External/live service state | GitHub workflows call old test paths and script paths; Docker/Compose assets copy and execute old package paths inside containers; `tox` and Python-version matrix verification may depend on local interpreters. [VERIFIED: .github/workflows/tests.yml] [VERIFIED: .github/workflows/messages-baseline-drift.yml] [VERIFIED: src/pytest_bdd_testing/resource/docker/remote_xdist/controller.Dockerfile] | Workflow redesign is out of scope, but path references must be updated. Docker-backed tests may remain environment-gated; local validation should still catch stale paths by static scan. |
| Historical/audit state | `.planning/phases/*` contains past records that may mention `pytest_bdd_testing` and `scripts/`; `.planning/STATE.md` and older roadmap phase descriptions also include historical decisions. [VERIFIED: .planning/STATE.md] [VERIFIED: .planning/ROADMAP.md] | Do not use repository-wide old-name greps as a hard gate. Current planning surfaces should be updated where active, but historical phase records can remain unchanged. |

## Active Surfaces To Change

- Rename package directory: `src/pytest_bdd_testing/` -> `src/pytest_bdd_toolchain/`. Exclude/delete `__pycache__` and `.pyc` artifacts instead of moving them as meaningful source. [VERIFIED: src/pytest_bdd_testing/]
- Move all 11 scripts from `scripts/` to `src/pytest_bdd_toolchain/tool/`: `analyze_responsibility_zones.py`, `arch.py`, `collect_arch_scores.py`, `collect_test_scores.py`, `fill_arch_scores.py`, `fill_test_docstrings.py`, `fix_incomplete_scores.py`, `fix_long_lines.py`, `inject_responsibility_docstrings.py`, `inject_test_docstrings.py`, and `run_messages_coverage_audit.py`. [VERIFIED: scripts/]
- Add `src/pytest_bdd_toolchain/tool/__init__.py` with the repository's `__init__.py` classification convention. Current project guidance says `__init__.py` files are regulated by custom init rules. [VERIFIED: DEVELOPMENT.rst] [VERIFIED: src/pytest_bdd/_pylint/checkers/init_rules.py]
- Add 11 `[project.scripts]` entries in `pyproject.toml`: `pbt-arch`, `pbt-collect-arch-scores`, `pbt-collect-test-scores`, `pbt-fill-arch-scores`, `pbt-fill-test-docstrings`, `pbt-fix-incomplete-scores`, `pbt-fix-long-lines`, `pbt-inject-responsibility-docstrings`, `pbt-inject-test-docstrings`, `pbt-run-messages-coverage-audit`, `pbt-analyze-responsibility-zones`. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Update `pyproject.toml` sections: `[tool.architecture.*]`, `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.quality_gates]`, `[tool.ruff.lint.per-file-ignores]`, `[tool.setuptools.package-data]`, and `[tool.setuptools.packages.find]`. [VERIFIED: pyproject.toml]
- Remove setuptools exclusion `exclude = ["pytest_bdd_testing*"]` and replace package data key `"pytest_bdd_testing"` with `"pytest_bdd_toolchain"`. [VERIFIED: pyproject.toml]
- Replace `.pre-commit-config.yaml` Pylint target `src/pytest_bdd_testing/` with `src/pytest_bdd_toolchain/`. [VERIFIED: .pre-commit-config.yaml]
- Update `.github/workflows/lint.yml`, `.github/workflows/tests.yml`, and `.github/workflows/messages-baseline-drift.yml`; research found those workflow files contain old package/script paths. [VERIFIED: .github/workflows/lint.yml] [VERIFIED: .github/workflows/tests.yml] [VERIFIED: .github/workflows/messages-baseline-drift.yml]
- Update custom Pylint checkers under `src/pytest_bdd/_pylint/checkers/`: at minimum `responsibility_docs.py`, `test_responsibility_docs.py`, `quality_gates.py`, `file_size_rules.py`, `test_import_rules.py`, and `init_rules.py` contain old package/script assumptions. [VERIFIED: src/pytest_bdd/_pylint/checkers/]
- Update internal imports and string patch targets across the moved package. This includes `pytest_plugins` strings, `unittest.mock.patch("pytest_bdd_testing...")`, direct imports, Docker module invocations, and generated resource paths. [VERIFIED: src/pytest_bdd_testing/case/e2e/conftest.py] [VERIFIED: src/pytest_bdd_testing/case/external/test_docker_wsl2.py]
- Update Docker and remote-xdist assets containing package paths: Dockerfiles copy old `src/pytest_bdd_testing/...` locations and entrypoints invoke old module paths. [VERIFIED: src/pytest_bdd_testing/resource/docker/remote_xdist/controller.Dockerfile] [VERIFIED: src/pytest_bdd_testing/resource/docker/remote_xdist/worker.Dockerfile]
- Update active documentation: `AGENTS.md`, `DEVELOPMENT.rst`, `CONTRIBUTING.md`, `README.md`, `docs/TESTING.md`, `docs/test-template-guide.md`, `docs/messages-coverage-user-guide.md`, `docs/adr/011-make-to-act-migration.md`, `features/`, and generated `docs/features/`. [VERIFIED: AGENTS.md] [VERIFIED: DEVELOPMENT.rst] [VERIFIED: CONTRIBUTING.md] [VERIFIED: docs/TESTING.md]
- Update current planning/codebase docs outside historical phase archives: `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/codebase/`, `.planning/intel/`, and `.planning/todos/`. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: .planning/STATE.md] [VERIFIED: .planning/REQUIREMENTS.md]
- Update architecture generated docs if they remain committed active docs: `docs/architecture/OBJECT_MAP.md` and `docs/architecture/RESPONSIBILITY_GAPS.md` contain generator names, package paths, and old module names. [VERIFIED: docs/architecture/OBJECT_MAP.md] [VERIFIED: docs/architecture/RESPONSIBILITY_GAPS.md]

## Sequencing Hazards

- Do the package directory rename, internal import rewrite, and config path rewrite in the same local edit window. Running tests between only one of these steps will produce expected import and collection failures that are not useful.
- Move scripts before deleting `scripts/`, but do not leave duplicate script modules in both places. Duplicates will confuse reference scans and command documentation.
- Adjust moved script imports if they import sibling scripts by bare module name. `scripts/arch.py` currently imports modules such as `inject_responsibility_docstrings` and `collect_arch_scores` as bare imports; after moving into a package, prefer package-relative or fully qualified imports that work from console entrypoints. [VERIFIED: scripts/arch.py]
- `run_messages_coverage_audit.py` computes `root_dir = Path(__file__).resolve().parent.parent`, which points at the repository root only while the file is in `scripts/`. After moving to `src/pytest_bdd_toolchain/tool/`, this must be replaced with robust repo-root discovery or a package-aware path strategy. [VERIFIED: scripts/run_messages_coverage_audit.py]
- Several scripts have baked default roots using the old package name and sometimes `cases` instead of current `case`. Fix defaults while moving them. [VERIFIED: scripts/arch.py] [VERIFIED: scripts/collect_test_scores.py] [VERIFIED: scripts/fill_test_docstrings.py]
- Some generated docs and BDD docs encode expected workflow report paths such as `src/pytest_bdd_testing/case/unit`; failing to update those expectations will break development BDD acceptance even if Python imports work. [VERIFIED: features/18 Development/11 Tests.feature.md]
- Pylint custom checkers use old-name strings both in user-facing messages and rule logic. Treat these as code changes, not documentation-only replacements. [VERIFIED: src/pytest_bdd/_pylint/checkers/test_import_rules.py] [VERIFIED: src/pytest_bdd/_pylint/checkers/quality_gates.py]
- The current package is excluded from setuptools discovery. If the exclusion is merely renamed to `pytest_bdd_toolchain*`, the standalone package goal fails even though local editable tests may still pass. [VERIFIED: pyproject.toml]
- Removing mypy's broad package exclusion can expose many type errors in non-case toolchain code. Context says removal is required, but targeted exclusions for test code such as `case/` are acceptable if needed. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Do not globally disable lint or add a broad `src/pytest_bdd_toolchain/tool/**` Ruff ignore. If moved scripts need temporary suppressions, use local `# noqa` with explanations. [VERIFIED: AGENTS.md] [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Validate absence of old imports after deleting stale cache artifacts; otherwise `.pyc` paths under `src/pytest_bdd_testing/__pycache__/` can create noise and false confidence issues. [VERIFIED: src/pytest_bdd_testing/__pycache__/]

## Validation Strategy

Run validation after the atomic rename is complete.

### Import And Package Checks

```bash
uv run python -c "import pytest_bdd_toolchain"
uv run python -c "import pytest_bdd_testing"
```

The second command must fail with `ImportError`. Use an explicit shell assertion in automation:

```bash
if uv run python -c "import pytest_bdd_testing"; then
  echo "pytest_bdd_testing unexpectedly imports" >&2
  exit 1
fi
```

### Entrypoint Help Checks

```bash
uv run pbt-arch --help
uv run pbt-collect-arch-scores --help
uv run pbt-collect-test-scores --help
uv run pbt-fill-arch-scores --help
uv run pbt-fill-test-docstrings --help
uv run pbt-fix-incomplete-scores --help
uv run pbt-fix-long-lines --help
uv run pbt-inject-responsibility-docstrings --help
uv run pbt-inject-test-docstrings --help
uv run pbt-run-messages-coverage-audit --help
uv run pbt-analyze-responsibility-zones --help
```

These should exit 0 and show usage/help without mutating repository state. Add or adapt `argparse` in scripts that currently lack a real help path. `pbt-run-messages-coverage-audit --help` is especially important because the current script reads `sys.argv` directly and otherwise runs probes. [VERIFIED: scripts/run_messages_coverage_audit.py]

### Focused Test And Matrix Checks

```bash
uv run python -m pytest src/pytest_bdd_toolchain/case -q --tb=short --no-header
tox -e py310,py311,py312,py313,py314
```

If local Python interpreters are missing, document the exact missing interpreter and still run the available focused test target. Python 3.14 may be provisioned by `uv python install` when needed per project guidance. [VERIFIED: AGENTS.md]

### Lint, Type, And Packaging Checks

```bash
uv run ruff check src/pytest_bdd src/pytest_bdd_toolchain
uv run ruff format --check src/pytest_bdd src/pytest_bdd_toolchain
uv run mypy --config-file pyproject.toml
uv run pylint src/pytest_bdd/ src/pytest_bdd_toolchain/
uv build
```

Use `uv build` or equivalent packaging inspection to prove `pytest_bdd_toolchain` is included after removing the setuptools exclusion. [VERIFIED: pyproject.toml]

### Scoped Reference Checks

Avoid broad repository-wide greps. These checks intentionally exclude historical phase records and cache/bytecode:

```bash
rg -n "pytest_bdd_testing" \
  --glob '!*.pyc' \
  --glob '!**/__pycache__/**' \
  --glob '!.planning/phases/**' \
  AGENTS.md DEVELOPMENT.rst CONTRIBUTING.md README.md pyproject.toml .pre-commit-config.yaml \
  .github/workflows src scripts features docs \
  .planning/ROADMAP.md .planning/STATE.md .planning/REQUIREMENTS.md \
  .planning/codebase .planning/intel .planning/todos

rg -n "uv run python scripts|python scripts|scripts/" \
  --glob '!*.pyc' \
  --glob '!**/__pycache__/**' \
  --glob '!.planning/phases/**' \
  AGENTS.md DEVELOPMENT.rst CONTRIBUTING.md README.md pyproject.toml .pre-commit-config.yaml \
  .github/workflows src scripts features docs \
  .planning/ROADMAP.md .planning/STATE.md .planning/REQUIREMENTS.md \
  .planning/codebase .planning/intel .planning/todos
```

The second check may need a reviewed allowlist for non-development-script uses of the word `scripts/`, but `uv run python scripts/...`, `python scripts/...`, and old command documentation should be gone from active surfaces.

Also verify old and duplicate filesystem surfaces:

```bash
test ! -d src/pytest_bdd_testing
test ! -d scripts
find src -path '*/__pycache__/*' -name '*pytest_bdd_testing*' -print
```

## Lint And Type-Checking Implications

- The current `scripts/*` Ruff ignore is broad and procedural. Do not translate it into a permanent `src/pytest_bdd_toolchain/tool/**` ignore because Phase 28 explicitly forbids that fallback. [VERIFIED: pyproject.toml] [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- Expect moved scripts to trip annotation, subprocess, complexity, print, and docstring rules if the broad ignore is removed. Perform best-effort cleanup in tool modules that are easy to make compliant, especially adding `argparse` help paths and fixing root discovery.
- Keep existing broad ignores for `src/pytest_bdd_toolchain/case/**` and step-definition harness code if they remain justified as test fixture style; the no-directory-level-ignore constraint is specifically about the moved development tool modules. [VERIFIED: pyproject.toml] [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- If a tool module still needs a suppression, use a local `# noqa: RULE  # reason` comment. The repository has custom checks for bare `noqa` and missing explanations. [VERIFIED: AGENTS.md] [VERIFIED: src/pytest_bdd/_pylint/checkers/]
- Removing mypy's broad `^src/pytest_bdd_testing/` exclusion should not become a broad `^src/pytest_bdd_toolchain/` exclusion. If needed, target `case/` or specific legacy test-only modules and document the reason near the exclusion. [VERIFIED: pyproject.toml] [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]
- The project forbids disabling checks globally or excluding whole directories without explicit user permission. Do not solve moved-script lint failures by weakening global Ruff, mypy, or pre-commit policy. [VERIFIED: AGENTS.md]

## Common Pitfalls

- Leaving `pytest_bdd_testing` importable via stale directory, cache, editable install artifact, or compatibility shim.
- Updating Python imports but missing pytest plugin strings in `pytest_plugins = [...]`, patch targets, command strings, and Dockerfile `COPY`/`ENTRYPOINT` paths.
- Keeping `exclude = ["pytest_bdd_toolchain*"]` in setuptools, which would make local tests pass while distribution packaging fails.
- Moving `run_messages_coverage_audit.py` without fixing `Path(__file__).resolve().parent.parent`, causing it to resolve `src/pytest_bdd_toolchain` instead of the repository root.
- Registering `pbt-*` entrypoints that call modules with no real `--help` path; acceptance requires help to exit 0 without side effects.
- Treating `docs/features/` and `docs/architecture/` as ignorable history. They are committed active/generated docs and currently contain old active references.
- Using `rg pytest_bdd_testing .` as a final gate. It will fail on allowed historical records and cache unless scoped.
- Updating only `case` paths and missing incorrect legacy `cases` references in docs and some script defaults.
- Deleting `scripts/` before updating workflows and docs that still call `python scripts/...`.

## Planner Guidance

Plan this as one implementation plan with tightly ordered work packages inside it:

1. Prepare mechanical rename mapping and create a temporary checklist of old-name/script references using the scoped `rg` commands above.
2. Move `scripts/*.py` into `src/pytest_bdd_toolchain/tool/`, add package init, fix bare sibling imports, fix root discovery, and add proper `argparse` help paths where missing.
3. Rename `src/pytest_bdd_testing/` to `src/pytest_bdd_toolchain/`, excluding/removing cache artifacts.
4. Rewrite code imports, pytest plugin strings, patch targets, Docker resource paths, and test expected paths.
5. Update `pyproject.toml` and `.pre-commit-config.yaml` before running validation, with special attention to setuptools discovery and mypy exclusion removal.
6. Update workflows and active documentation/features/generated docs/current planning surfaces.
7. Run focused validation, fix forward, then run scoped reference checks and broader lint/type/package checks.

Prefer scripted mechanical replacement for package-name/path changes, followed by manual review of false positives and path-sensitive code. Do not split the final delivered state into a half-renamed package plus later cleanup; Phase 28's context requires an atomic coherent result. [VERIFIED: .planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md]

## Research Complete

Implementation research is complete. The phase is feasible as a single atomic rename/extraction, but the planner should treat script CLI hardening, root-path fixes, setuptools discovery, mypy exclusion removal, Docker path updates, generated-doc cleanup, and scoped reference validation as first-class tasks rather than incidental cleanup.
