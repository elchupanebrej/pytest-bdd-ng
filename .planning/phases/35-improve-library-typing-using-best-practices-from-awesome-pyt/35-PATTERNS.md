# Phase 35: Improve Library Typing Using Best Practices from Awesome-pyt - Pattern Map

**Mapped:** 2026-07-12
**Files analyzed:** 5
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pyproject.toml` | config | request-response | `pyproject.toml` (itself) | same-file / exact |
| `.pre-commit-config.yaml` | config | event-driven | `.pre-commit-config.yaml` (itself) | same-file / exact |
| `.github/workflows/lint.yml` | config | event-driven | `.github/workflows/lint.yml` (itself) | same-file / exact |
| `tox.ini` | config | request-response | `tox.ini` (itself) | same-file / exact |
| `src/pytest_bdd/compatibility/typing.py` | utility | request-response | `src/pytest_bdd/compatibility/typing.py` (itself) | same-file / exact |
| `src/pytest_bdd_toolchain/case/compat/test_consumer_typing.py` | test | file-I/O | `src/pytest_bdd_toolchain/case/unit/test_mypy_strict.py` — subprocess validation pattern; `src/pytest_bdd_toolchain/case/unit/test_stubs.py` — mypy runner & stubs checks | high |
| `src/pytest_bdd_toolchain/case/compat/typing/fixtures/` (valid & invalid example modules) | test (fixtures) | request-response | `src/pytest_bdd_toolchain/case/compat/test_public_api_exports.py` — public API import & call validations | partial |

---

## Pattern Assignments

### 1. `pyproject.toml` (config, request-response)
The main configuration file is updated to remove checker bypasses (excluding the toolchain test directories) and disable module-wide overrides. Mypy must check all packages cleanly, and Pyright rules/configuration are defined here.

**Analog:** `pyproject.toml` (existing mypy block, lines 265-292)

```toml
[tool.mypy]
check_untyped_defs = true
disallow_any_generics = true
disallow_incomplete_defs = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_decorators = true
disallow_untyped_defs = true
exclude = [
  "^src/pytest_bdd_toolchain/(case|step)/"
]
extra_checks = true
install_types = false
local_partial_types = true
mypy_path = "src, stubs"
no_implicit_reexport = true
packages = ["pytest_bdd", "pytest_bdd_toolchain"]
plugins = [
  "pydantic.mypy"
]
python_version = "3.14"
show_error_codes = true
strict_bytes = true
strict_equality = true
warn_redundant_casts = true
warn_return_any = true
warn_unused_configs = true
warn_unused_ignores = true
```

**Key conventions observed:**
* Strict settings are enabled globally.
* Excludes and `ignore_errors` overrides must be removed or narrowed down to line-level suppressions.
* Pyright configuration block can be added under `[tool.pyright]` matching standard packaging conventions.

---

### 2. `.pre-commit-config.yaml` (config, event-driven)
Integrates type-checking enforcement into local git workflow gates to prevent regression.

**Analog:** `.pre-commit-config.yaml` (existing mypy runner hook, lines 63-71)

```yaml
      - id: mypy
        name: mypy
        entry: >-
          uv run --python 3.14 --isolated --with mypy
          mypy --config-file pyproject.toml
        language: system
        types: [python]
        pass_filenames: false
        exclude: ^docs/
```

**Key conventions observed:**
* Hooks run within isolated `uv` context.
* `--config-file pyproject.toml` points to standard configurations.
* Entire repository checks are preferred to avoid partial analysis limitations (`pass_filenames: false`).

---

### 3. `.github/workflows/lint.yml` (config, event-driven)
The GitHub Actions workflow configuration is modified to block changes that introduce static typing errors or break public API typing contracts.

**Analog:** `.github/workflows/lint.yml` (existing lint jobs, lines 28-44)

```yaml
      - name: Install dependencies
        run: >-
          uv sync --extra test --extra testtypes
          --extra doc-gen --extra struct-bdd
      - name: Ruff check
        if: ${{ !env.ACT }}
        run: uv run ruff check src/ --extend-ignore EXE001,EXE002
      - name: Ruff format check
        if: ${{ !env.ACT }}
        run: uv run ruff format --check src/
      - name: Custom rules
        if: ${{ !env.ACT }}
        run: >-
          uv run python -m pytest
          src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py
          -q --no-header
```

**Key conventions observed:**
* Uses `uv run` to execute scripts in context.
* Guards jobs/steps using `if: ${{ !env.ACT }}` for local emulation.
* Pinned step actions and clean environment builds.

---

### 4. `tox.ini` (config, request-response)
Runs verification environments under different Python versions (minimum target 3.10 and platforms).

**Analog:** `tox.ini` (existing mypy target, lines 98-103)

```ini.
[testenv:py314-pytest{latest,90}-mypy]
deps =
    .[testtypes]
commands =
    python -m mypy --config-file pyproject.toml
```

**Key conventions observed:**
* Pinned dependency lists under `deps`.
* Direct subprocess command execution.

---

### 5. `src/pytest_bdd/compatibility/typing.py` (utility, request-response)
A central typing compatibility module designed to encapsulate all Python 3.10-3.14 differences and conditional imports.

**Analog:** `src/pytest_bdd/compatibility/typing.py` (entire file, lines 46-57)

```python
import sys
from typing import TypeAlias

__tracebackhide__ = True

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

__all__ = ["Self", "TypeAlias"]
```

**Key conventions observed:**
* Detects Python runtime via `sys.version_info`.
* Provides clean, unified imports to avoid scatters of `if sys.version_info` across domain code.
* Declares `__all__` to make re-exports clean and typed.

---

### 6. `src/pytest_bdd_toolchain/case/compat/test_consumer_typing.py` (test, file-I/O)
This new test executes `mypy` and `pyright` against consumer-facing typing fixture examples to verify correct type inference and error diagnostic rejection behavior.

**Analog:** `src/pytest_bdd_toolchain/case/unit/test_mypy_strict.py` (lines 56-67)

```python
    src_dir = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", src_dir],
        capture_output=True,
        text=True,
        timeout=180,
    )
    # mypy writes errors to stdout, not stderr
    last_line = result.stdout.strip().split("\n")[-1] if result.stdout else "(no output)"
    assert result.returncode == 0, (
        f"mypy --strict src/ exit code should be 0, got {result.returncode}.\nLast line: {last_line}"
    )
```

**Key conventions observed:**
* Uses `subprocess.run` with `sys.executable` to guarantee correct interpreter context.
* Captures stdout/stderr cleanly for diagnostics.
* Sets a safety `timeout=180`.

---

### 7. `src/pytest_bdd_toolchain/case/compat/typing/fixtures/` (test, request-response)
Fixtures that mock real consumer usage patterns of public APIs to assert typing correctness.

**Analog:** `src/pytest_bdd_toolchain/case/compat/test_public_api_exports.py` (lines 45-50)

```python
    importlib.import_module("pytest_bdd.scenario")

    from pytest_bdd.scenario import scenario

    assert not isinstance(scenario, ModuleType)
    assert callable(scenario)
```

**Key conventions observed:**
* Imports only public, documented API boundary components.
* Valid examples are fully typed with no ignores.
* Invalid examples check type checker diagnostics (e.g. invalid step decors or wrong type arguments).

---

## Shared Patterns

### A. Python Version Compatibility Guards
Version-gated features (e.g. `Self`, `TypeAlias`, and generic bounds) must only use conditional imports inside `src/pytest_bdd/compatibility/typing.py`:
```python
if sys.version_info >= (X, Y):
    from typing import Symbol
else:
    from typing_extensions import Symbol
```

### B. Subprocess Test Validation and Timeouts
All static analysis orchestration tests must use consistent subprocess execution constraints:
* Timeout limit of `180` seconds to avoid hanging CI tasks.
* Execution via `sys.executable -m <module>` to use the active virtual environment's dependencies.
* Clear error diagnostic outputs on assertion failures.

---

## No Analog Found

The following patterns have no close match in the existing codebase. The planner should use `35-TYPING-VALIDATION-RESEARCH.md` and PEP 561 / Pyright specification guidelines as the authoritative reference:

| Pattern | Reason |
|---------|--------|
| Pyright `--verifytypes` integration | First time the library is packaging and verifying type completeness of exported contracts in CI. |
| Negative typing assertions (invalid fixtures) | First time typing fixtures are specifically designed to fail type-checking with expected diagnostic categories. |

---

## Metadata

**Analog search scope:** `src/pytest_bdd/compatibility/`, `src/pytest_bdd_toolchain/case/unit/`, `src/pytest_bdd_toolchain/case/compat/`
**Research file:** `35-TYPING-VALIDATION-RESEARCH.md`
**Pattern mapping date:** 2026-07-12
