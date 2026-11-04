# Integration branch coverage, PDI, CI, and acceptance machinery

**Checked:** 2026-11-04
**Target:** `C:/Users/bulky/Projects/pytest-bdd-ng-integration-2026-10-29`
**Branch / head:** `integration/restore-parity-2026-10-29` / `dee40c1a898b960587128b476617c8d7a59c5617`
**Scope:** Read-only inventory of the integration worktree. This report records what exists, what can be reused, and where the repair has gaps. It does not change product code, configuration, CI, or policy.

## Finding

The integration branch already carries a substantial CI and acceptance system: a 40-cell environment inventory, a selector generator, a per-cell evidence writer, an exact-SHA proof aggregator, and a mature installed-consumer harness that builds a wheel and sdist with `uv` and installs them into isolated `uv venv` projects. Those are directly reusable.

Two pieces are materially weaker than the prior art they were restored from:

1. **Coverage is collected but not enforced or reported.** `.coveragerc` still declares `fail_under = 85`, but the integration tox configuration uses `coverage run --append` and contains no `coverage combine` or `coverage report` command. The prior rewrite branch had `--parallel-mode`, `coverage combine`, and `coverage-!xdist: coverage report`; the legacy default branch uploaded to Codecov. Both enforcement paths are absent here. The PyPy `<7.5` coverage pin that exists on `origin/default` is also absent.
2. **PDI is a static two-file contract.** `.pdi/contract.json` declares three supported capabilities but only supplies one runnable utility (`workspace.describe`). `validation.entrypoint` and `git.boundary` have no utility, schema, runner, or evidence artifact, and the contract's product name (`pytest-bdd-ng`) does not match the distribution name (`pytest-cuke`).

The environment evidence model is strong and precise: every record is tied to an exact 40/64-character SHA, a `(job, cell, tox_environment)` key, and a host preflight. There is no "profile" axis anywhere in the evidence model, and the only pinned historical revision is in `config/env-matrix.yaml` under `support_ledger.historical_reference`.

## 1. Coverage invocation and configuration

### `.coveragerc` (worktree root)

```ini
[run]
branch = true
source = pytest_cuke

[paths]
source =
    src/pytest_cuke
    .tox/*/lib/python*/site-packages/pytest_cuke
    .tox/*/Lib/site-packages/pytest_cuke

[report]
fail_under = 85
precision = 2
```

Observed properties:

- `.coveragerc:2-3` measures branch coverage for `pytest_cuke`.
- `.coveragerc:5-8` canonicalizes paths across `src/` and tox site-packages, which is necessary for combined runs.
- `.coveragerc:11-13` declares `fail_under = 85` and two-decimal precision.
- There is **no** `[run] parallel`, `[run] concurrency`, `[run] data_file`, `[report] show_missing`, or `[report] omit` section. The integration file is a trimmed version of `origin/default:.coveragerc`, which has `show_missing = true` and an omit list.

### `tox.ini` (worktree root)

- `tox.ini:4-30` lists the environments. Many are `...-coverage-...`; the coverage factor is applied only to those names.
- `tox.ini:39` installs `uv>=0.8` for every `coverage` environment.
- `tox.ini:42` installs `coverage>=7.4` for every `coverage` environment. There is no platform or implementation conditional.
- `tox.ini:59` is the only coverage invocation:

  ```ini
  coverage: _PYTEST_CMD = coverage run --append -m pytest
  ```

- `tox.ini:63` applies that command to the first tox command only:

  ```ini
  {env:_PYTEST_CMD:python -m pytest} {env:_PYTEST_MORE_ARGS:} {posargs:-m "not e2e and not external and not typecheck and not doc_gen" -q}
  ```

- `tox.ini:64-70` are subsequent plain `python -m pytest ...` commands (tutorial acceptance, PyPy acceptance, Allure, xdist message-worker, tutorial example). They do **not** use `_PYTEST_CMD`, so those runs are not measured.
- `tox.ini` contains **no** `coverage combine` and **no** `coverage report` command in any testenv.

### CI

- `.github/workflows/main.yml` has no coverage report, coverage upload, or coverage artifact step. Its jobs run tox through `scripts/run_env_matrix_cell.py` and upload `evidence-*.json` only.
- `scripts/run_env_matrix_cell.py` measures test counts and outcomes, not coverage percentage. See `selected_tests` / `passed_tests` at `scripts/run_env_matrix_cell.py:371-373`, `:432-433`, and `:522-531`.
- `scripts/aggregate_env_evidence.py` validates outcomes but has no coverage field in its expected record. See the required-field checks at `scripts/aggregate_env_evidence.py:392-758`.

### Prior art to reuse

`origin/rewrite-from-2.3.1:tox.ini` had the working pattern:

```ini
# lines 20-22
# xdist lanes are not coverage-gated: raw `coverage run` does not measure xdist
# workers (#208), and the sequential twins already enforce fail_under on the
# same code.

set_env =
    coverage: _PYTEST_CMD = coverage run --parallel-mode -m pytest   # line 46

commands =
    {env:_PYTEST_CMD:pytest} {env:_PYTEST_MORE_ARGS:} ...            # line 50
    coverage: coverage combine                                      # line 51
    coverage-!xdist: coverage report                                # line 52
```

Relevant history:

- `e642c486` — "fix(coverage): canonicalize paths via parallel data + combine (#231)".
- `3b779831` — "ci(coverage): enforce src-only fail_under=85 in tox coverage lanes".
- `origin/default:859d32bc` — "Restrict coverage version to <7.5 on PyPy to prevent TypeError on union annotations". The default tox pins `coverage<7.5` for PyPy (default `tox.ini` dependency block) while the integration branch pins only `coverage>=7.4`.
- `origin/default:.github/workflows/main.yml:68-69` uploads coverage with `codecov/codecov-action@v4`; the integration branch has no equivalent.

### Gaps in coverage

- No command runs `coverage report`, so `fail_under = 85` is inert.
- No command runs `coverage combine`, so `--append` is used instead of parallel data files and path canonicalization.
- xdist environments are coverage-labelled, but `.coveragerc` has no `concurrency`/`parallel` configuration. The rewrite branch explicitly documented that raw `coverage run` does not measure xdist workers (#208). The integration branch has no equivalent gate or documented exclusion.
- Only tox command index 0 is wrapped in coverage; the e2e/acceptance commands in the same environment are not measured.
- No CI artifact or aggregate proof contains a coverage number.
- The PyPy coverage pin from `origin/default` is not carried forward.

## 2. Environment matrix and CI selectors

### Inventory shape

`config/env-matrix.yaml` (2,912 lines) has these top-level sections:

| Line | Section | Contents |
|---|---|---|
| 1 | `schema_version` | `1` |
| 2 | `project` | requirement floors, tox/workflow paths, evidence fields, aggregate groups, fast-PR selector |
| 22 | `runtime_policy` | `required_cells`, runtime evidence fields, upstream sources |
| 441 | `runtime_inventory` | runtime availability/support ledger |
| 512 | `support_ledger` | historical reference and historical capability exclusions |
| 1295 | `workflow_cells` | 40 concrete CI matrix cells |
| 1721 | `lanes` | 58 lanes: 49 required, 6 optional, 3 unsupported |
| 2912 | `capability_exclusions` | empty list |

`workflow_cells` job distribution (line 1295 block):

- `full-matrix`: 17
- `optional-integrations`: 9
- `quality`: 4
- `live-formatters-acceptance`: 3
- `native-go-parser`: 3
- `remote`: 3
- `browser-report`: 1

Each cell declares `id`, `job`, `runtime`, `python`, `platform`, `architecture`, `runner`, `setup_python_input`, `expected_interpreter`, and `tox_envs`. `lanes` additionally declare `status`, `capability`, `workflow_selector`, `command`, `prerequisites`, and `expected_carrier`.

### Selector script

`scripts/env_matrix.py`:

- `load_cells()` at `:14-40` reads `workflow_cells` with PyYAML and validates `tox_envs`, `id`, `runner`, `python`, `platform`.
- `split_cell_environments()` at `:43-61` expands one cell into one row per tox environment and rejects unknown cell ids.
- `main()` at `:64-122` supports:
  - `--job` (required)
  - `--split-cells CELL_ID...` (only for `full-matrix`; enforced at `:102-103`)
  - `--split-tox-envs`
  - `--inventory` (default `config/env-matrix.yaml`)
  - `--github-output` (writes `cells=<json>` to `GITHUB_OUTPUT`)

Observed behavior on the host: running `python3 scripts/env_matrix.py --job full-matrix --split-tox-envs` fails with

```text
env-matrix: PyYAML is required; install `pytest-cuke[env-matrix]`.
```

That is expected; the script does not vendor YAML. CI installs `PyYAML==6.0.3` before calling it (`.github/workflows/main.yml:28-29`, `:97-98`, `:140-141`, etc.).

### Workflow selection

`.github/workflows/main.yml`:

- `matrix-select` job at `:13-50` calls `env_matrix.py` seven times, once per job (`full-matrix`, `optional-integrations`, `remote`, `browser-report`, `live-formatters-acceptance`, `native-go-parser`, `quality`) and exports job outputs.
- Matrix jobs consume `fromJSON(needs.matrix-select.outputs.<name>)`:
  - `live-formatters-acceptance` at `:80-117`
  - `full-matrix` at `:119-166`
  - `optional-integrations` at `:168-211`
  - `remote` at `:213-248`
  - `browser-report` at `:250-295`
  - `native-go-parser` at `:297-337`
  - `quality` at `:339-371`
- Each job exports the job URL through `.github/actions/export-job-url/action.yml`, which sets `PYTEST_CUKE_JOB_URL` after finding the exact job display name.
- `aggregate-proof` at `:373-396` downloads `env-evidence-*` artifacts and runs:
  ```text
  python scripts/aggregate_env_evidence.py --input-dir artifacts \
    --inventory config/env-matrix.yaml --sha "${{ github.sha }}" \
    --output artifacts/full-proof-summary.json
  ```
- `.github/workflows/native-go-parser.yml:11-24` repeats the same `env_matrix.py --job native-go-parser` selection on pull requests, then `:26-61` runs the native parser cell and uploads a separate proof artifact.

### Gaps in CI/inventory

- No `profile` axis exists in cells, lanes, or evidence. A "profile" would have to be introduced if the repair needs to distinguish, for example, build profile or runtime profile.
- `--split-cells` is restricted to `full-matrix`; other jobs are emitted as whole cells.
- The native parser selector exists twice: once inside the main workflow and once in `native-go-parser.yml`. They read the same inventory but have separate artifact names and separate CI runs.

## 3. PDI contract, utilities, and schemas

### Files

- `.pdi/contract.json`
- `.pdi/schemas/workspace-describe.json`

### Contract

`contract_schema` is `"1.0"`. Product is:

```json
"product": {"name": "pytest-bdd-ng", "version": "2.3.1"}
```

Capabilities:

| Capability | Version | Status | Utility present |
|---|---|---|---|
| `workspace.describe` | 1.2 | supported | yes |
| `validation.entrypoint` | 1.0 | supported | no |
| `git.boundary` | 1.0 | supported | no |

Only one utility is declared:

```json
{
  "name": "workspace.describe",
  "command": ["python3", "-c", "import json, subprocess, sys\n..."],
  "schema": ".pdi/schemas/workspace-describe.json",
  "acceptance": "passed"
}
```

The command runs `git rev-parse --show-toplevel` and `git status --porcelain`, then prints `{"root": ..., "clean": ...}`. `evidence` is two static booleans: `product_acceptance: true`, `compatibility_fixture: true`.

### Schema

`.pdi/schemas/workspace-describe.json` is a JSON Schema 2020-12 object requiring `root` (string) and `clean` (boolean), with `additionalProperties: false`.

### Observed behavior

Run from the integration worktree with the Windows Git shim on `PATH`:

```text
{"root": "C:/Users/bulky/Projects/pytest-bdd-ng-integration-2026-10-29", "clean": true}
```

Portability caveat: the command resolves bare `git` from `PATH`. Under WSL2 without the shim, the Linux `git` cannot read this worktree because `.git` points at `C:/Users/bulky/Projects/pytest-bdd-ng/.git/worktrees/...`. The utility itself is fine; its dependency on the caller's `PATH` is the caveat.

### Prior art

- `origin/rewrite-from-2.3.1` introduced the contract in `779f6c7a` ("feat(pdi): add Product Development Interface contract (refs #143, #150, #151)").
- `origin/pdi/portable-workspace-describe` contains commit `48baf719` / `65138850` ("fix(pdi): use portable python3 for workspace.describe utility"), which replaced a hard-coded Linuxbrew interpreter path with `python3`.

### Gaps in PDI

- `validation.entrypoint` and `git.boundary` have no utility command, no schema, no acceptance artifact, and no implementation reference.
- `"acceptance": "passed"` is static text with no timestamp, SHA, environment, or artifact link.
- `evidence.product_acceptance` and `evidence.compatibility_fixture` are static booleans; they are not derived from CI evidence or the environment proof.
- The contract's `product.name` is `pytest-bdd-ng`, while `pyproject.toml:79` declares `name = "pytest-cuke"`. Versions agree (`2.3.1` in both).
- There is no `revision`, `commit`, `profile`, or `schema` field at contract level.
- No script or test in the worktree reads `.pdi/contract.json`; a repository-wide search finds only the contract and schema themselves.

## 4. Acceptance machinery

### Wheel/sdist build fixture

`tests/e2e/steps.py:288-311` — session-scoped `_pytest_cuke_artifacts`:

- Requires `uv` on `PATH`.
- Builds with `uv build --sdist --wheel --out-dir <tmp> <project_root>`.
- Sets `PYTEST_CUKE_BUILD_GO=off`.
- Asserts exactly one `pytest_cuke-*.tar.gz` and one `pytest_cuke-*.whl`.
- Returns artifact paths and SHA-256 hashes.

### venv fixtures

`tests/e2e/steps.py`:

- `_pytest_cuke_environments` at `:314-344`: creates one `uv venv --python sys.executable` per distribution (`wheel`, `sdist`) and installs the built artifact with `uv pip install`.
- `_pytest_cuke_typing_environments` at `:347-379`: same, plus `mypy==2.3.1`.
- `_install_pytest_cuke_extra_in_isolated_environment` at `:453-492`: creates a per-extra `.venv-<extra>` and installs `pytest-cuke[extra] @ <artifact URI>`.

### Installed-consumer fixtures and steps

- `ConsumerProject` dataclass at `:157-190`: stores project path, python/pytest/cuke executables, environment, artifact, optional mypy, and subprocess result slots.
- `_consumer_binary_dir`, `_consumer_executable`, `_consumer_path`, `_consumer_environment` at `:58-89`: platform-aware executable lookup; strips `TOX_ENV_DIR` and xdist worker variables; builds a constrained `PATH`.
- Install steps:
  - `install_pytest_cuke_consumer` at `:382-432` (`Given the pytest-cuke <wheel|sdist> built from this checkout is installed in a fresh consumer project`).
  - `install_pytest_cuke_typing_consumer` at `:495-542`.
  - `install_host_built_native_consumer` at `:545-619` (requires `PYTEST_CUKE_NATIVE_WHEEL`).
  - Extra installers at `:435-451` (Allure, StructBDD, Cucumber JSON).
- Execution steps:
  - `run_consumer_pytest` at `:901-917` (`When I run installed pytest with arguments "..."`).
  - `run_consumer_pytest_from_consumer_directory` at `:920-949`.
  - Two-session and HTTP-fixture variants at `:1001-1060`.
  - `run_consumer_command` at `:2726`.
  - Watchdog variant at `:5817`.
- Consumer file/artifact assertions are spread through `tests/e2e/steps.py` and `tests/e2e/runtime_steps.py`.

### Features that use the harness

A repository search finds **48 feature files** containing "built from this checkout is installed", including:

- `features/installed-explicit-bindings.feature`
- `features/installed-consumer-typing.feature`
- `features/compatibility/environment-inventory.feature` (26 uses)
- `features/compatibility/environment-proof-aggregation.feature`
- `features/compatibility/environment-policy-ledger.feature`
- `features/compatibility/pypy-runtime-acceptance.feature`
- `features/allure-message-conversion.feature` (22 uses)
- `features/pytest-cuke-bootstrap.feature` (15 uses)
- `features/feature-source-selection.feature` (15 uses)
- `features/live-cucumber-*.feature`
- `features/native-go-parser/optional-native-go-parser.feature`

`tests/conftest.py:7` enables the `pytester` plugin, and `tests/e2e/development_steps.py:33-58` provides a generic subprocess runner for CLI tests. `tests/e2e/runtime_steps.py:58` probes the consumer interpreter directly.

### Environment/proof acceptance

- `tests/e2e/environment_inventory_steps.py` (4,252 lines) loads `config/env-matrix.yaml`, runs `cuke compatibility --check-environments --inventory config/env-matrix.yaml --json`, checks tox listing and CI selection proof, and validates runtime policy.
- `tests/e2e/environment_proof_aggregation_steps.py` (2,967 lines) synthesizes evidence artifacts and runs `scripts/aggregate_env_evidence.py` via subprocess (`:1125-1135`).
- `tests/e2e/environment_policy_ledger_steps.py` (579 lines) checks the pinned historical baseline and retired cells.
- `tests/unit/compatibility/test_environment_matrix.py` (558 lines) unit-tests runtime policy, exclusions, and optional-integration policy.

### Native parser acceptance

`scripts/test_native_go_parser.py:11-69`:

1. Builds a pure sdist with `PYTEST_CUKE_BUILD_GO=off`.
2. Builds a native wheel from that sdist with `PYTEST_CUKE_BUILD_GO=required` using `pip wheel --no-deps`.
3. Runs `features/native-go-parser/optional-native-go-parser.feature` with `PYTEST_CUKE_NATIVE_WHEEL` pointing at the wheel.

The tox lane `native-go-parser` (`tox.ini:36-49` region, env at `~:160-170`) and both workflows call this script or the same feature.

### Gaps in acceptance

- The installed-consumer harness requires `uv`, network access to install dependencies, and `npm` for the Cucumber JSON runtime (`tests/e2e/steps.py:193-233`). There is no offline/short smoke subset.
- The wheel is rebuilt once per pytest session, not reused across separate acceptance lanes.
- The harness records test outcomes and artifact JSON, but no coverage measurement and no PDI/contract identity.
- The default pytest selector excludes `e2e` (`tox.ini:63`), so the attestation features only run in the dedicated `-m e2e` commands or dedicated lanes. There is no single command that runs the whole acceptance surface.

## 5. Environment evidence and revision/profile identity

### Evidence writer

`scripts/run_env_matrix_cell.py:275-533` writes one JSON document per CI cell.

Top-level shape (`:338-349` initially, `:522-531` final):

```json
{
  "schema_version": 1,
  "git_sha": "<full SHA>",
  "job": "<workflow job>",
  "cell": "<cell id>",
  "outcome": "passed|failed",
  "preflight": {
    "expected_interpreter": "3.14.*",
    "runtime": "CPython",
    "python": "3.14.x",
    "platform_name": "linux|darwin|win32",
    "architecture": "x86_64|aarch64|...",
    "platform": "<platform.platform()>"
  },
  "environments": [ ... ]
}
```

Each `environments[]` record (`:425-448`, extended at `:459-520`) has:

- `git_sha`, `job`, `cell`, `group`, `tox_environment`
- `command` (`[tox, "run", "--result-json", ..., "-e", env]`)
- `selected_tests`, `passed_tests`
- `system_tool_versions`, `system_tool_commands`
- `outcome`, `returncode`
- `platform`, `platform_name`, `os_name`, `os_release`, `architecture`
- `job_url`, `run_url`
- `result_json`
- `runtime`, `python`, `pytest`, `optional_versions`
- `tox_result` (full tox result JSON) or `tox_result_error`
- `acceptance_commands` for full-matrix pytest envs
- `remote_worker_runs` for remote jobs
- diagnostic fields such as `missing_optional_packages`, `missing_system_tools`, `runtime_evidence_error`

Preflight validation (`:121-153`) compares the selected cell's `runtime`, `expected_interpreter`, `platform`, and `architecture` against the live interpreter and fails before tox runs if they mismatch. The preflight is written into the evidence.

### Evidence identity checks

`scripts/aggregate_env_evidence.py`:

- `_inventory_environments()` at `:106-173` derives the expected `(job, cell, tox_environment)` set and validates the job ledger and aggregate groups.
- `collect_evidence()` at `:392-758` requires:
  - exact `payload.git_sha == expected_sha` (`:424-425`);
  - exact per-environment SHA (`:441-442`);
  - header job/cell agreement (`:439-440`);
  - no unrequested or duplicate environment (`:443-459`);
  - passing payload and record outcomes (`:462-471`);
  - runtime, Python, interpreter, platform, architecture agreement (`:472-505`);
  - valid workflow job and run URLs that identify the same run (`:506-516`);
  - resolved tox command, result path, and successful tox result entry (`:517-529`);
  - actual optional dependency versions and required system tool versions/commands (`:530-605`);
  - tox result interpreter/version/package agreement (`:606-652`);
  - pytest factor agreement (`:653-691`);
  - at least one selected and one passed test for test groups (`:695-703`).
- `main()` at `:761-782` requires a full 40- or 64-character hex SHA.

Workflow-link identity is `(hostname, repository path, run id)` in `_workflow_link_identity()` at `:62-91`. The job URL is populated by `.github/actions/export-job-url/action.yml`; the run URL is assembled from `GITHUB_SERVER_URL`, `GITHUB_REPOSITORY`, and `GITHUB_RUN_ID` in `scripts/run_env_matrix_cell.py:166-173`.

### Revision identity

- Per-run revision is `git_sha` from `--sha` / `GITHUB_SHA` (`scripts/run_env_matrix_cell.py:285`, `:342`).
- The only historical revision pin is `config/env-matrix.yaml:516`:
  ```yaml
  support_ledger:
    historical_reference:
      repository: elchupanebrej/pytest-bdd-ng
      revision: fb5f16f11f3f66fce97a5eeb5f5a862ab71949ce
      tox_file: tox.ini
      workflow_file: .github/workflows/main.yml
  ```
  It is used by the policy ledger, not by per-run environment evidence.

### Profile identity

There is **no profile identity** in the integration worktree. Searches across `config/`, `scripts/`, `.pdi/`, `.github/`, and `tests/e2e/environment_*` find no `profile` field. The closest concepts are:

- the `(job, cell, tox_environment)` key;
- the `group` label (`serial`, `parallel`, `e2e`, `external`, `quality`, `optional`) from `scripts/environment_evidence.py:128-140`;
- the distribution choice (`wheel` vs `sdist`) in the installed-consumer harness, which is not recorded in environment evidence.

If the repair needs a profile identity, it must be introduced explicitly; it cannot be recovered from the current records.

### Gaps in evidence

- Coverage is absent from every evidence record and from the aggregate proof.
- PDI acceptance is absent from every evidence record.
- No build/profile identity (for example, wheel vs sdist) is recorded alongside environment evidence.
- The aggregate proof is intentionally strict about SHA and identity; any repair must preserve that strictness when adding new fields.

## 6. Reuse map and concrete gaps

### Reuse directly

| Need | Prior art | Location |
|---|---|---|
| CI matrix selection | `scripts/env_matrix.py` + `workflow_cells` | `config/env-matrix.yaml:1295`, `scripts/env_matrix.py:14-122` |
| Per-cell runtime preflight | `_verify_selected_runtime`, `_observed_runtime` | `scripts/run_env_matrix_cell.py:111-153` |
| Evidence writer | `run_env_matrix_cell.py main` | `scripts/run_env_matrix_cell.py:275-533` |
| Exact-SHA proof gate | `collect_evidence` | `scripts/aggregate_env_evidence.py:392-758` |
| Job URL capture | composite action | `.github/actions/export-job-url/action.yml` |
| Wheel + sdist build | `_pytest_cuke_artifacts` | `tests/e2e/steps.py:288-311` |
| Isolated venv install | `_pytest_cuke_environments`, `_pytest_cuke_typing_environments` | `tests/e2e/steps.py:314-379` |
| Installed consumer project | `ConsumerProject`, install steps | `tests/e2e/steps.py:157-619` |
| Subprocess acceptance | `run_consumer_pytest`, `run_consumer_command` | `tests/e2e/steps.py:901-949`, `:2726` |
| Native sdist/wheel test | `scripts/test_native_go_parser.py` | `scripts/test_native_go_parser.py:11-69` |
| Coverage enforcement | `--parallel-mode`, `combine`, `report`, xdist exclusion | `origin/rewrite-from-2.3.1:tox.ini:46-52`, `:20-22` |
| PyPy coverage pin | `coverage<7.5` on PyPy | `origin/default:tox.ini` dependency block; commit `859d32bc` |
| Coverage upload | Codecov action | `origin/default:.github/workflows/main.yml:68-69` |
| PDI contract shape | contract + JSON Schema + portable utility | `.pdi/contract.json`, `.pdi/schemas/workspace-describe.json`, `origin/pdi/portable-workspace-describe` |

### Gaps the repair must close

1. **Coverage enforcement.** `fail_under = 85` is currently unreachable because no `coverage report` runs. Restore a report command and decide which lane(s) own the gate.
2. **Coverage data merging.** `--append` replaced `--parallel-mode` + `coverage combine`; the latter is the prior art for path canonicalization and per-environment isolation.
3. **xdist measurement.** The integration config labels xdist lanes as coverage lanes but does not configure concurrency. Either measure workers or carry the rewrite branch's explicit xdist exclusion rationale.
4. **Second and later tox commands.** The e2e/acceptance commands in each coverage environment are not wrapped by `_PYTEST_CMD`.
5. **PyPy coverage compatibility.** Carry the `coverage<7.5` pin from `origin/default` or verify a newer coverage version on PyPy 3.12.
6. **Coverage evidence.** No evidence record or aggregate proof contains a coverage number or artifact path.
7. **PDI completeness.** `validation.entrypoint` and `git.boundary` need utilities, schemas, runner, and real acceptance evidence, or their status must change.
8. **PDI identity.** Reconcile `product.name` (`pytest-bdd-ng`) with `pyproject.toml:79` (`pytest-cuke`), and replace static `"passed"`/`true` values with linked, reproducible evidence.
9. **Profile identity.** No profile axis exists. If the repair needs one, add it to the contract/evidence schema deliberately.
10. **Single acceptance entrypoint.** Acceptance is spread across 48 installed-consumer features plus dedicated e2e lanes; there is no short, documented command that exercises the full acceptance surface.

## Commands observed

```text
# PDI utility (from the integration worktree, Windows Git shim on PATH)
python3 -c 'import json, subprocess, sys
r_root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=".")
r_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=".")
print(json.dumps({"root": r_root.stdout.strip(), "clean": r_status.stdout.strip() == ""}))'
# -> {"root": "C:/Users/bulky/Projects/pytest-bdd-ng-integration-2026-10-29", "clean": true}

# Environment selector (host lacks PyYAML)
python3 scripts/env_matrix.py --job full-matrix --split-tox-envs
# -> env-matrix: PyYAML is required; install `pytest-cuke[env-matrix]`.
```

No acceptance suite was run; the inventory above is from source and short read-only commands.

## Sources

- Integration worktree, branch `integration/restore-parity-2026-10-29`, head `dee40c1a898b960587128b476617c8d7a59c5617`.
- `origin/rewrite-from-2.3.1` — coverage `--parallel-mode` / `combine` / `report` pattern; commits `e642c486`, `3b779831`, `1aba0500`.
- `origin/default` at `859d32bc` — `.coveragerc`, tox PyPy coverage pin, Codecov upload.
- `origin/pdi/portable-workspace-describe` — PDI contract portability commit `48baf719` / `65138850`.
- Product issue #335 (this research request).
