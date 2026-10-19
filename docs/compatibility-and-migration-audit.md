# Compatibility matrix and migration audit

The installed `cuke` and `pytest-cuke` commands share `cuke compatibility`.
The command reads the closest active `pyproject.toml` while walking up from
the current directory. Pass `--config PATH` to inspect another TOML project
configuration or a legacy tox INI file.

## Compatibility inspection

The project matrix is configured in `pyproject.toml`:

    [tool.pytest-cuke.compatibility]
    python-factors = ["3.11", "3.12", "3.13", "3.14", "3.15"]
    pytest-factors = ["7.4", "8.4", "9.0", "latest"]
    execution-targets = ["lin", "mac", "win"]
    tox-env-template = "py{python}-pytest{pytest}-coverage-{target}"
    compatibility-source = "pytest-official-policy-and-release-notes"

`python-factors` and `pytest-factors` accept dotted versions or tox-style
factors. `latest` is an explicit policy entry resolved through the minimum
supported Python floor in `pytest_cuke.compatibility.runtime_compat`; the
command does not query an installed pytest or infer runtime support from an
environment name. The configured release bounds reflect pytest's [Python
support policy](https://docs.pytest.org/en/stable/backwards-compatibility.html)
and release notes for when new Python versions gained support, including
[Python 3.12 in pytest 7.3](https://docs.pytest.org/en/7.4.x/changelog.html),
[Python 3.13 in pytest 8.2](https://docs.pytest.org/en/8.4.x/changelog.html),
and [Python 3.14 in pytest 8.4](https://docs.pytest.org/en/8.4.x/changelog.html).
Update those bounds deliberately when adding a pytest release line.
`tox-env-template` must include `{python}`, `{pytest}`, and either `{target}` or
`{platform}`. Expansion emits names only for pairs accepted by both upstream
compatibility bounds and the project's minimum supported Python/pytest versions.

Examples:

    cuke compatibility --list
    cuke compatibility --compatible-only --json
    cuke compatibility --python 3.12 --pytest latest --json
    cuke compatibility --expand-tox

The JSON matrix is an object with a stable `entries` array. Each entry reports
`pythonVersion`, `pytestVersion`, `isCompatible`, `isSupported`, `reasonCode`,
`executionTargets`, `compatibilitySource`, and optional `toxEnvName`.
`isCompatible` reports the selected upstream pytest policy. `isSupported`
reports whether both version factors meet the project's support floors. A pair
check succeeds only when both flags are true. Unsupported/EOL factors and
upstream-incompatible pairs retain distinct reason codes.

For a diagnostic against a legacy tox configuration, pass an explicit INI:

    [tox]
    env_list =
        py{312,313}-pytest{80,90}-coverage-{lin,win}

    [pytest-cuke-migration-audit]
    feature_patterns = **/*.feature, **/*.feature.md
    test_registration_patterns = **/*.py
    threshold_percent = 80

The INI reader expands tox brace factors, keeps only concrete configured
environments in `--expand-tox`, and supports the optional
`[pytest-cuke-compatibility]` keys `execution_targets` and
`compatibility_source`. INI input is diagnostic only; the active project default
is TOML.

## Migration audit

Configure an explicit inventory in the active `pyproject.toml`:

    [tool.pytest-cuke.migration-audit]
    feature-patterns = ["features/**/*.feature", "features/**/*.feature.md"]
    test-registration-patterns = ["tests/**/*.py"]
    threshold-percent = 80

The feature root defaults to `PROJECT/<cuke_features_dir>` from the active
`[tool.pytest.ini_options]` (or `PROJECT/features` when unset); the test root
defaults to `PROJECT/tests`. Configured patterns are applied beneath their
respective roots. A leading `features/` or `tests/` segment is removed, so the
default patterns work when the feature directory is customized. Root-relative
patterns such as `**/*.feature` also work. Override roots with `--features-root`
or `--tests-root`; the same configured patterns apply beneath those roots.
Missing default directories are treated as empty inventories, while an
explicitly supplied missing root or a path that is not a directory is an error.

Feature identities represent parsed scenario nodes and use the form
`relative/feature-path::normalized scenario title`. Paths are project-relative
when possible, use forward slashes, and are case-folded. Titles are Unicode
NFKC-normalized, case-folded, and have repeated whitespace collapsed. Scenario
outlines count as one identity per outline, not one per examples row.

Python registrations are discovered from literal `scenario(...)`,
`scenarios(...)`, or `pytest.mark.scenarios(...)` calls imported from
`pytest-cuke` or `pytest-bdd`. The audit reads Python ASTs and does not import or
execute test modules. Only static feature paths and static scenario titles can
be mapped; dynamic arguments are omitted. Registrations inside function bodies
are ignored, while top-level function and class-method decorators count.
Quoted examples, comments, and documentation strings are not registrations.

The denominator is the union of unique feature identities and unique Python
registration identities. Feature scenarios count even when autoload collects
them without mirror test files. Matching explicit wrappers do not increase the
denominator. Coverage is `feature identity count / union identity count`; a
valid empty inventory is 100%. `duplicatesInTests` counts repeated normalized
Python registration occurrences beyond the first for an identity. Duplicates
fail the audit even when coverage meets its threshold.

Run the audit and machine-readable equivalent:

    cuke compatibility --audit-migration
    cuke compatibility --audit-migration --threshold-percent 95 --json
    cuke compatibility --audit-migration --features-root docs/features --tests-root tests/e2e

An audit returns status 1 when coverage is below threshold or duplicate
registrations remain. Invalid thresholds, unreadable or malformed feature and
Python files, invalid explicit roots, and malformed config return actionable
diagnostics on stderr with status 2. JSON output is written to stdout without
diagnostic text.

## Supported environment inventory and acceptance

`config/env-matrix.yaml` is the source for the supported runtime, platform,
optional-capability and CI-cell inventory. Required runtime cells are CPython
3.11–3.15 on Linux, macOS and Windows, plus PyPy 3.12 and GraalPy 25.3 on Linux
x86_64. The required CPython 3.11/Linux cell is constrained to x86_64. CPython
3.11/Linux also runs latest pytest 7.4.x; CPython 3.12/Linux also runs latest
pytest 8.4.x. Every required tox environment installs the
package, runs the core suite and executes the standalone `examples/tutorial`
project. The inventory records upstream availability, installability, product
support, required CI, measured results and exclusions separately; unsupported
combinations include a source-backed reason. The checker compares those entries
with the resolved tox listing and GitHub Actions selectors. Optional Allure,
xdist, browser, native parser, formatter and documentation-generation lanes stay
separate from core runtime acceptance. An environment name alone does not
establish that a lane ran. The fast PR selector excludes
`slow`, `e2e`, `external`, `typecheck` and `doc_gen`; full runtime tox commands
exclude `e2e`, `external`, `typecheck` and `doc_gen`. The required
`py314-doc-gen` quality lane runs the documentation test with its optional
Python dependencies and Pandoc. Dedicated browser, native and remote jobs
install or verify their own prerequisites. xdist proof is reported as
`parallel`, separately from serial runtime proof.

Core runtime environments use tox's package installer directly; the GraalPy
cell keeps its bundled pip and does not install uv. Optional consumer and
formatter lanes install `uv>=0.8` where their isolated-consumer contracts need
it. Each coverage environment records its full Python and pytest versions, OS,
architecture, commit SHA, resolved tox command, selected/passed test counts,
outcome and workflow URLs. Full proof is valid only when every expected record
matches the requested commit SHA and passes.

Live formatter acceptance has dedicated Linux, macOS and Windows cells. The
portable Linux invocation is:

    tox run -e py313-live-formatters-acceptance-lin

The lane requires Node.js 22 with npm/npx and `uv>=0.8`. The workflow provisions
Node.js, installs uv, and verifies npx by running the Allure CLI. This Linux
invocation provides Linux evidence only. Proof runs each formatter environment's
local `.tox/<environment>/bin/uv` or `.tox/<environment>/Scripts/uv.exe`, records
the actual `uv --version` output and resolved executable path, and rejects
evidence that points to a uv outside that tox environment. Required CPython
3.11–3.15 cells on Linux, macOS and Windows run through the inventory-selected
full matrix; no CPython runtime platform cell is manual-only evidence.

Install the development and inventory tools, inspect resolved tox environments,
and validate the inventory from the repository root:

    python -m pip install -e ".[test,struct-bdd,env-matrix]"
    tox list --no-desc
    cuke compatibility --check-environments --inventory config/env-matrix.yaml --json

Probe a lane's declared prerequisites and real test carrier with
`--lane <lane-id>`. A missing requested tool or empty carrier selection fails
with a diagnostic and remedy:

    cuke compatibility --check-environments --inventory config/env-matrix.yaml --lane optional-dependency-probe --json
    cuke compatibility --check-environments --inventory config/env-matrix.yaml --lane browser-report --json

The full-runtime selector emits one row per tox environment without a second
hand-maintained cell list:

    python scripts/env_matrix.py --job full-matrix --split-tox-envs

For local exact-version reruns, CPython 3.15 uses the pinned interpreter on all
platforms, and the older pytest lines have dedicated Linux lanes:

    tox run -e py315-pytestlatest-coverage-lin,py315-pytestlatest-coverage-mac,py315-pytestlatest-coverage-win
    tox run -e py311-pytest74-coverage-lin,py312-pytest84-coverage-lin

For a full acceptance run, execute the inventory-selected jobs on a push or
workflow dispatch. The `full-supported-proof-<sha>` artifact contains the
aggregate summary, each environment's exact SHA, tox environment, installed
versions, resolved command, selected and passed test counts and result, and the
source evidence JSON and direct Actions job link from each matrix cell.
Aggregation fails if a cell is missing or duplicated, the SHA differs, the
actual interpreter or pytest version conflicts with the inventory/tox factor, a
declared environment fails, or a test lane selects no tests. Quality tool lanes
are recorded without pretending that a pytest test count applies to them.
Optional Allure conversion and xdist worker consolidation run in their own
inventory-selected matrix and aggregate group, separate from core runtime
claims. Remote socket, via, and SSH records also preserve the runtime, Python,
pytest, and pytest-xdist versions reported by both actual workers in complete
and interrupted runs.

`tox run` executes the complete declared tox environment list. Optional Allure
and xdist contracts can be rerun with their dedicated environments:

    tox run -e py313-pytest84-allure-coverage-lin
    tox run -e py314-pytestlatest-gherkin33-xdist-coverage-lin,py314-pytestlatest-gherkinlatest-xdist-coverage-lin

The historical Windows remote-worker lanes also remain manually runnable:

    tox run -e py314-pytestlatest-xdist-remote-socket-win,py314-pytestlatest-xdist-remote-via-win,py314-pytestlatest-xdist-remote-ssh-win

The remote xdist environments require a working Docker Engine and Compose;
the SSH mode also requires `ssh-keygen`. The browser-report environment requires
Node.js/npm/npx and Chromium with its system libraries. The native Go parser
environment requires Go and a C compiler; the Windows workflow installs MinGW
before running it. Each Linux and macOS proof cell records the output of
`go version` and `cc --version`. Each Windows cell records `go version` and
MinGW `gcc --version`. The aggregate keeps each resolved executable path and
full argv for both version commands and fails if either tool version or
command evidence is missing.
Missing prerequisites fail the selected lane with the required tool named in
the diagnostic.

The fast pull-request selector is only a Linux CPython 3.13 feedback run:

    python -m pytest -m "not e2e and not external and not slow and not typecheck and not doc_gen" -q

The fast selector excludes `slow`, `e2e`, `external`, `typecheck` and `doc_gen`.
The `py314-doc-gen` quality cell runs the optional documentation-generation
test with Pandoc on pull requests and full proof runs. Full runtime tox commands
exclude `e2e`, `external`, `typecheck` and `doc_gen`; dedicated browser, native
and remote jobs run their own contracts and prerequisites.
On push and manual workflow dispatch, the full runtime matrix, browser report,
live formatter acceptance, native parser, remote xdist and quality jobs upload
JSON evidence tied to the workflow's exact Git SHA. Each live formatter cell
uploads its own artifact, and the `aggregate-proof` job includes those outcomes.
Each record contains the tox environment, resolved command, selected test count
where applicable, actual Python/pytest, optional package and required system
tool versions, resolved system-tool executable paths and version-command argv,
including the formatter tox-local uv command, remote worker versions, selected
and passed test counts, and outcome. The
`aggregate-proof` job requires every
inventory environment, including the `serial`, `parallel`, `e2e`, `external`
and `quality` groups, and publishes `full-supported-proof-<sha>`. Missing,
duplicated, mismatched or failed cell
evidence, and test lanes with no selected tests, fail the aggregate. The
separate native-parser workflow remains available for pull requests and manual
dispatch; push proof is collected by the main workflow.
