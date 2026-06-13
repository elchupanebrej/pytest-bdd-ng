# Phase 17: Adapt GitHub CI to use make and validate with act - Pattern Map

**Mapped:** 2026-05-28
**Files analyzed:** 4 modified + 4 Makefile targets
**Analogs found:** 8 / 8

## File Classification

| New/Modified File or Target | Role | Data Flow | Closest Analog | Match Quality |
|-----------------------------|------|-----------|----------------|---------------|
| `Makefile` `TOX` construction | config | batch command-execution | `Makefile` lines 35-38 + `tox.ini` lines 114-121 | exact |
| `Makefile` `tox` target | config | batch command-execution | `Makefile` `tox-list`, `test-*` targets using `$(TOX)` | role-match |
| `Makefile` `env-install-npm` target | config | file-I/O provisioning | `Makefile` `env-install` / `env-install-browser` lines 313-325 | exact |
| `Makefile` `check-message-schemas` target | config | batch validation | `Makefile` `sync-message-schemas` lines 401-402 | exact |
| `Makefile` `validate-github-actions` target | config | batch validation | `Makefile` `env-check*` lines 242-248 | role-match |
| `.github/workflows/main.yml` | config | event-driven batch | existing `main.yml` setup + project-command steps lines 43-83 | exact |
| `tox.ini` | config | batch matrix-selection | existing `[gh-actions]` lines 114-121 | exact; likely read-only |
| `tests/cases/contract/generation/test_template_packaging.py` | test | file-I/O contract | same file lines 63-70 + `test_makefile_test_api.py` lines 62-90 | exact |

## Pattern Assignments

### `Makefile` `TOX` construction (config, batch command-execution)

**Analog:** `Makefile` variable block + `tox.ini` GitHub Actions mapping.

**Current variable pattern** (`Makefile` lines 35-38):
```make
PYTEST ?= uv run $(UV_SYNC_EXTRAS) python -m pytest
PYTEST_LOCAL_SELECTOR ?= not slow and not docker and not windows and not browser and not external
PYTEST_UNIT_IGNORE ?= --ignore=tests/cases/unit/unit/test_dead_code.py
TOX ?= uvx --with tox-uv tox
```

**Target pattern to copy:** keep `?=` override semantics. Replace single `TOX ?=` with an `ifeq ($(GITHUB_ACTIONS),true)` branch before first `$(TOX)` use.

```make
ifeq ($(GITHUB_ACTIONS),true)
  TOX ?= uvx --with tox-uv --with tox-gh-actions tox
else
  TOX ?= uvx --with tox-uv tox
endif
```

**Integration anchor:** `tox.ini` already maps GitHub matrix Python to tox factors (`tox.ini` lines 114-121):
```ini
[gh-actions]
python =
    3.10: py310
    3.11: py311
    3.12: py312
    3.13: py313
    3.14: py314
    pypy-3.11: pypy311
```

### `Makefile` `tox` target (config, batch command-execution)

**Analog:** existing `env-check-tox` and `$(TOX)` usage.

**Guard pattern** (`Makefile` lines 246-248):
```make
env-check-tox: check-shell
	@command -v uvx >/dev/null || { echo "ERROR: uvx missing. Run make env-install."; exit 1; }
	@$(TOX) --version >/dev/null || { echo "ERROR: tox unavailable. Run make env-install."; exit 1; }
```

**Target pattern to add:**
```make
tox: env-check-tox
	$(TOX)
```

**Planner note:** add `tox` to `.PHONY`. Existing `.PHONY` block starts at `Makefile` line 1 and already lists `tox-list`, but not `tox`.

### `Makefile` `env-install-npm` target (config, file-I/O provisioning)

**Analog:** explicit provisioning targets.

**Existing install target pattern** (`Makefile` lines 313-325):
```make
env-install:
	uv python install 3.14
	uv sync $(UV_SYNC_EXTRAS)

env-install-browser:
	uv sync $(UV_SYNC_EXTRAS) --extra test-playwright
	uv run python -m playwright install
```

**Workflow command body being moved** (`.github/workflows/main.yml` lines 58-62):
```yaml
- name: Install npm dependencies
  run: |
    npm install "@cucumber/html-formatter"
    npm install cucumber-html-reporter
    npm list
```

**Target pattern to add:**
```make
env-install-npm:
	npm install --no-save @cucumber/html-formatter cucumber-html-reporter
	npm list
```

**Planner note:** add `env-install-npm` to `.PHONY`. Keep this as provisioning target, not `env-check`.

### `Makefile` `check-message-schemas` target (config, batch validation)

**Analog:** existing schema sync target.

**Current target** (`Makefile` lines 401-402):
```make
sync-message-schemas: env-check
	uv run python -m pytest_bdd.script.sync_messages_contract_schemas
```

**Workflow command body being moved** (`.github/workflows/main.yml` lines 66-70):
```yaml
- name: Generated messages schemas are up to date
  if: matrix.python-version == '3.14' && matrix.os == 'ubuntu-latest'
  run: |
    python -m pip install -e . GitPython
    python -m pytest_bdd.script.sync_messages_contract_schemas --check
```

**Target pattern to add:**
```make
check-message-schemas: env-check
	uv run python -m pytest_bdd.script.sync_messages_contract_schemas --check
```

**Planner note:** use existing `env-check`; no new script path.

### `Makefile` `validate-github-actions` target (config, batch validation)

**Analog:** loud actionable missing-tool checks.

**Existing error style** (`Makefile` lines 242-248):
```make
env-check: check-shell
	@command -v uv >/dev/null || { echo "ERROR: uv missing. Run make env-install."; exit 1; }
	@uv run python -c "import pytest" >/dev/null || { echo "ERROR: pytest environment missing. Run make env-install."; exit 1; }

env-check-tox: check-shell
	@command -v uvx >/dev/null || { echo "ERROR: uvx missing. Run make env-install."; exit 1; }
	@$(TOX) --version >/dev/null || { echo "ERROR: tox unavailable. Run make env-install."; exit 1; }
```

**Target pattern to add:**
```make
validate-github-actions: check-shell
	@command -v act >/dev/null || { echo "ERROR: act missing. Install act: https://nektosact.com/installation/"; exit 1; }
	act --validate
```

**Planner note:** phase verification must run `make validate-github-actions`.

### `.github/workflows/main.yml` (config, event-driven batch)

**Analog:** existing workflow shape. Preserve matrix, setup actions, conditions, Codecov, secrets env.

**Setup actions to keep visible** (`.github/workflows/main.yml` lines 43-52):
```yaml
- name: Set up Python ${{ matrix.python-version }}
  uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: "*"
- name: Install pandoc
  uses: r-lib/actions/setup-pandoc@v2
```

**Project command replacement anchors** (`.github/workflows/main.yml` lines 53-83):
```yaml
- name: Install PyPi dependencies
  run: |
    python -m pip install --upgrade pip
    pip install "tox>=4.2" "tox-gh-actions>=3.2" codecov
    pip install uv
- name: Install npm dependencies
  run: |
    npm install "@cucumber/html-formatter"
    npm install cucumber-html-reporter
    npm list
- name: Test with tox
  run: |
    uv run tox
- name: Generated messages schemas are up to date
  if: matrix.python-version == '3.14' && matrix.os == 'ubuntu-latest'
  run: |
    python -m pip install -e . GitPython
    python -m pytest_bdd.script.sync_messages_contract_schemas --check
- name: Gather codecov
  if: matrix.python-version == '3.14'
  run: |
    codecov
- name: Build checking
  if: "matrix.python-version == '3.14'"
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
  run: |
    python -m pip install --upgrade build twine
    python -m build
    twine check dist/*
```

**Target workflow pattern:**
```yaml
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

**Planner note:** keep `Gather codecov` condition and command unless intentionally adding a Makefile wrapper. `codecov` availability must remain; install path may stay workflow-level or become a dedicated setup dependency step. Do not hide checkout/Python/Node/pandoc/uv setup in Makefile.

### `tox.ini` (config, batch matrix-selection)

**Analog:** existing tox-gh-actions mapping. Likely no edit.

**Plugin requirement context** (`tox.ini` lines 1-5):
```ini
[tox]
requires =
    tox>=4.2
    tox-uv
env_list =
```

**Mapping to preserve** (`tox.ini` lines 114-121):
```ini
[gh-actions]
python =
    3.10: py310
    3.11: py311
    3.12: py312
    3.13: py313
    3.14: py314
    pypy-3.11: pypy311
```

**Planner note:** do not add `[gh-actions:env]` unless first CI run proves OS env selection broken. Phase scope says no matrix/tox restructuring.

### `tests/cases/contract/generation/test_template_packaging.py` (test, file-I/O contract)

**Analog:** workflow contract assertions reading workflow/pre-commit text.

**Existing contract** (`tests/cases/contract/generation/test_template_packaging.py` lines 63-70):
```python
def test_main_workflow_checks_generated_message_schemas_without_pre_commit() -> None:
    """Verify main workflow checks generated message schemas without pre commit."""
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "main.yml").read_text(encoding="utf-8")
    pre_commit_config = (PROJECT_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "Generated messages schemas are up to date" in workflow
    assert "pytest_bdd.script.sync_messages_contract_schemas --check" in workflow
    assert "sync_messages_contract_schemas" not in pre_commit_config
```

**Update pattern:** assertion may change from direct script text to Makefile target text.

```python
assert "Generated messages schemas are up to date" in workflow
assert "make check-message-schemas" in workflow
assert "sync_messages_contract_schemas" not in pre_commit_config
```

**Makefile contract analog** (`tests/cases/contract/test_makefile_test_api.py` lines 62-90):
```python
def _parse_targets(text: str) -> dict[str, dict[str, object]]:
    targets: dict[str, dict[str, object]] = {}
    current_targets: tuple[str, ...] = ()
    for line in text.splitlines():
        if line and not line.startswith(("\t", " ")) and ":" in line:
            target_part, dependency_part = line.split(":", maxsplit=1)
            current_targets = tuple(target.strip() for target in target_part.split() if target.strip())
            dependencies = tuple(dependency_part.strip().split())
            for target in current_targets:
                targets[target] = {"dependencies": dependencies, "commands": []}
        elif line.startswith("\t"):
            for target in current_targets:
                commands = targets[target]["commands"]
                assert isinstance(commands, list)
                commands.append(line.strip())
    return targets


def test_makefile_exposes_required_test_api_targets() -> None:
    """Verify Makefile contains the Phase 12 human test API."""
    targets = _parse_targets(_makefile_text())

    assert set(REQUIRED_TARGETS).issubset(targets)
```

**Planner note:** add focused contract checks for new Make targets only if desired. Minimal safe update is existing workflow schema assertion.

## Shared Patterns

### `.PHONY` Membership
**Source:** `Makefile` lines 1-7.
**Apply to:** all new Makefile targets.

Add: `tox`, `env-install-npm`, `check-message-schemas`, `validate-github-actions`.

### Read-Only Checks vs Provisioning
**Source:** `tests/cases/contract/test_makefile_test_api.py` lines 44-56 and 125-137.
**Apply to:** `env-check*`, `validate-github-actions`, `env-install-npm`.

`env-check*` targets must not run install/provision commands. `env-install-npm` may run `npm install` because it is explicit provisioning.

### Loud Missing Tool Failure
**Source:** `Makefile` lines 242-248.
**Apply to:** `validate-github-actions`.

Use `@command -v <tool> >/dev/null || { echo "ERROR: ..."; exit 1; }`.

### CI Secrets Preservation
**Source:** `.github/workflows/main.yml` lines 75-83.
**Apply to:** build step only.

Keep:
```yaml
env:
  TWINE_USERNAME: __token__
  TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

### Verification Commands
**Source:** Phase 17 context + existing contract tests.
**Apply to:** phase validation.

Run:
```bash
make validate-github-actions
GITHUB_ACTIONS=true make -n tox
make -n tox
uv run python -m pytest tests/cases/contract/generation/test_template_packaging.py -q
```

## No Analog Found

None. All planned files/targets have direct local analogs.

## Integration Points

| Point | Exact Change |
|-------|--------------|
| `Makefile` `.PHONY` | add `tox env-install-npm check-message-schemas validate-github-actions` |
| `Makefile` variable block | replace line 38 single `TOX ?=` with `GITHUB_ACTIONS` conditional |
| `Makefile` targets | add `tox`, `env-install-npm`, `check-message-schemas`, `validate-github-actions` |
| `.github/workflows/main.yml` setup | keep checkout, setup-python, setup-node, setup-pandoc; add `astral-sh/setup-uv@v6` |
| `.github/workflows/main.yml` commands | replace npm/tox/schema/build command bodies with `make ...` |
| `.github/workflows/main.yml` conditions | preserve schema Ubuntu+3.14, Codecov 3.14, build 3.14 |
| `tests/cases/contract/generation/test_template_packaging.py` | update workflow schema assertion to expect `make check-message-schemas` |
| `tox.ini` | no planned edit; preserve `[gh-actions]` mapping |

## Metadata

**Analog search scope:** `Makefile`, `.github/workflows/*.yml`, `.github/workflows/*.yaml`, `tox.ini`, `tests/cases/contract/**`, `.planning/phases/12*`, `.planning/phases/15*`, `.planning/codebase/**`
**Files scanned:** 60+ search hits, 7 direct file reads
**Pattern extraction date:** 2026-05-28
