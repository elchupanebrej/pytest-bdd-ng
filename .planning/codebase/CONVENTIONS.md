---
last_mapped_commit: c59470a9bc50f5ae0f628a572832a5b614d862a7
mapped_at: 2026-05-12
focus: quality
---

# Coding Conventions

**Analysis Date:** 2026-05-12

## Naming Patterns

**Files:**
- Source modules: `snake_case.py` (e.g., `scenario_run.py`, `stash_access.py`, `collector_batch.py`).
- Test files: `test_*.py` (e.g., `test_steps.py`, `test_collector_batch.py`).
- Package `__init__.py` files: exist in every package directory; source `__init__.py` contains module-level docstrings only; `src/pytest_bdd/__init__.py` uses PEP 562 lazy loading for `given`, `step`, `then`, `when`.

**Functions:**
- Public functions: `snake_case` (e.g., `scenario()`, `scenarios()`, `get_python_name_generator()`).
- Private/internal functions: `_leading_underscore` (e.g., `_parse_feature_file()`, `_coerce_pytest_return_code()`, `_resolve_test_output_path()`).
- Test functions: `test_` prefix with descriptive name (e.g., `test_valid_gherkin_returns_document()`, `test_flush_is_idempotent()`).

**Variables:**
- Module-level constants: `UPPER_SNAKE_CASE` (e.g., `_REMOTE_XDIST_FIXTURE_DIR`, `_CUCUMBER_FORMATTER_REPORT_FEATURE_URI`).
- Instance variables: `snake_case` (e.g., `self.testdir`, `self.allure_report`).
- Unused variables: underscore-prefixed to satisfy the linter (`_` for truly unused; `_tag`, `_step` for descriptive but unused).

**Types:**
- Classes: `PascalCase` (e.g., `ScenarioFunction`, `FeatureBatchParser`, `StashAccess`, `LifecycleObjectRef`).
- Type aliases: `PascalCase` with suffix `T` (e.g., `ScenarioDecorator`, `ScenarioTest`, `ScenarioFilterT`, `ConverterT`).
- Exception classes: `PascalCase` with `Error` suffix (e.g., `PytestBDDStashLookupError`, `FeatureParseError`, `StepDefinitionNotFoundError`).
- Enum variants: `UPPER_SNAKE_CASE` (e.g., `HookPhase.before_scenario`, `RunStage.scenario_setup`).

## Code Style

**Formatting:**
- Tool: `ruff format` (equivalent to Black with `line-length = 120`).
- Indentation: spaces (4 spaces).
- Quotes: double quotes (`"`).
- Line endings: auto-detected.
- Magic trailing commas respected.
- Pre-commit hook: `ruff-format` auto-applied on `src/`, `tests/`, `docs/`.

**Linting:**
- Tool: `ruff check` with ~60 rule categories enabled (see `[tool.ruff.lint].select` in `pyproject.toml`).
- Key rule categories: `E`, `F` (pycodestyle, pyflakes), `I` (isort), `N` (pep8-naming), `ANN` (flake8-annotations), `D` (pydocstyle), `S` (bandit security), `SIM` (flake8-simplify), `UP` (pyupgrade), `PL` (pylint), `PT` (flake8-pytest-style), `Q` (flake8-quotes).
- Max complexity (McCabe): 10 (target: 6, per comment in config).
- Pre-commit hook: `ruff-check` with `--fix --exit-non-zero-on-fix`.
- Strict `mypy` configuration with `check_untyped_defs = true`, `show_error_codes = true`, `warn_return_any = true`.

**Per-file ignores in `pyproject.toml`:**
- `tests/*`: `ANN`, `D`, `S101` (asserts), `PLR0913` (too-many-args), and others relaxed for tests.
- `src/pytest_bdd/_gherkin_go/__init__.py`: `BLE001` (blind except for version logging), `RUF067` (API not just re-exports).
- Various `__init__.py`: `F401` (unused imports for re-export).

## Import Organization

**Order:** Follows `isort` sections:
1. `future` (`from __future__ import annotations` — used in **all** source files under `src/pytest_bdd/`)
2. `standard-library`
3. `third-party`
4. `first-party` (`pytest_bdd.*`)
5. `local-folder`

**Pattern:**
```python
# Standard library imports grouped together
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, cast

# Third-party imports
import pytest
from attrs import define, field
from cucumber_messages import GherkinDocument  # type:ignore[attr-defined]

# First-party imports
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.model.stash_access import StashBound
```

**Lazy imports** (inside functions/methods): used for heavy or optional dependencies via `# noqa: PLC0415`:
```python
def __getattr__(name: str) -> object:
    if name in {"given", "step", "then", "when"}:
        from pytest_bdd.steps import given, step, then, when  # noqa: PLC0415
```

**TYPE_CHECKING guards:** used for imports only needed for type annotations:
```python
if TYPE_CHECKING:
    from collections.abc import Generator
    from pytest_bdd.compatibility.pytest import Config
```

## Error Handling

**Patterns:**
- Custom exception hierarchy rooted in standard library exceptions (`Exception`, `ValueError`, `LookupError`, `TypeError`).
- Exception classes in `src/pytest_bdd/types/exception.py`:
  - `PytestBDDStashError` → `PytestBDDStashLookupError`, `PytestBDDStashAlreadyInitializedError`, `PytestBDDStashTypeMismatchError`
  - `FeatureParseError` → `FeatureConcreteParseError`
  - `ScenarioValidationError` → `ScenarioNotFoundError`, `ExamplesNotValidError`
  - `StepDefinitionNotFoundError`
  - `MessageSchemaValidationError`
- Error messages use f-strings with descriptive context:
  ```python
  raise ValueError(msg)  # Pre-assigned message variable
  raise FeatureConcreteParseError(message, line_no, line, file)
  raise RuntimeError(f"`{cls.__name__}` is unavailable in config.stash.")
  ```
- `AttributeError`, `TypeError`, `ValueError`, `RuntimeError` caught in defensive code paths with `# pragma: no cover`.
- `contextlib.suppress` used for non-critical optional operations.
- Prefer `raise` with descriptive message over silent `None` returns (per AGENTS.md: "returning `None` is an antipattern; use explicit values or deterministic exceptions").

## Logging

**Framework:** Standard `logging` not widely used. The library uses:
- `warnings.warn` for user-facing diagnostics (e.g., `PytestBDDStepDefinitionWarning`).
- `print()` in test harness code for debug output.
- pytest's built-in `warnings` filter in `pyproject.toml` turns all warnings into errors (`filterwarnings = ["error"]`) with explicit ignores for `DeprecationWarning` and `ImportWarning`.

**Patterns:**
- Warning types defined in `src/pytest_bdd/types/warning.py`.
- Warnings issued via `warnings.warn()` with custom category.

## Comments

**When to Comment:**
- Every module has a top-level docstring: `"""Provide <module purpose> helpers."""`
- Every public function/class has a docstring with optional `Args:`, `Returns:`, `Raises:`, `Yields:` sections.
- Comments prefer full sentences with proper punctuation.
- `# language=gherkin` and `# language=python` inline comments on multi-line strings for IDE syntax highlighting in tests.

**JSDoc/TSDoc:** Not applicable (Python project).

**Ruff rules for comments:**
- `D` (pydocstyle) enforced on `src/` but suppressed on `tests/`.
- `ERA` (eradicate) to remove commented-out code.
- `TD` (flake8-todos) enabled; `TD002`/`TD003` ignored (missing author/link in TODOs).

## Function Design

**Size:** McCabe complexity target is 6 (current max set to 10). Functions are generally concise, though some integration functions in test code are longer.

**Parameters:**
- Type annotations required on all function signatures (enforced by `ANN` rules on source).
- `# noqa: PLR0913` used for functions with many parameters (e.g., `scenario()` has 12 parameters).
- `*` used to enforce keyword-only arguments:
  ```python
  def scenario(
      ...,
      *,
      return_test_decorator: Literal[True] = True,
  ) -> ScenarioDecorator: ...
  ```

**Return Values:**
- Type-annotated with `-> ReturnType`.
- Functions that return multiple types use `Union` (`|`) return types.
- Overloads used for conditional return types (`@overload` + `@overload` + actual implementation).

## Module Design

**Exports:**
- `__all__` is forbidden in all modules (including source modules, facade modules, compatibility helper modules, and `__init__.py` files) to ensure clean and predictable re-exports.
- Redundant import aliases (such as `from X import Y as Y` or `import Y as Y` where the alias name matches the imported name) are forbidden by custom lint rule `BLQ1404`. Imports must be clean without the duplicate `as` alias.
- To satisfy mypy strict type checking (`no_implicit_reexport = True` by default), facade and compatibility helper modules are exempted from strict checking by configuring `implicit_reexport = true` overrides under `[[tool.mypy.overrides]]` in `pyproject.toml` instead of using the redundant `as Y` pattern.
- Imports of test cases (any module or imported name starting with `test_` or containing `.test_`) must strictly reside under the `src/pytest_bdd_testing/cases/` package. Importing tests from any other path is forbidden and checked by custom lint rule `BLQ1601`.
- Lazy loading via `__getattr__` in `src/pytest_bdd/__init__.py` for `given`, `step`, `then`, `when`.

**Barrel Files:** `__init__.py` files in plugin packages typically contain only a docstring. The actual plugin code lives in `entrypoint.py` or `plugin.py`.

**attrs usage:** The project prefers `attrs` over builtin `dataclass`es (per AGENTS.md). Used for data-holding classes:
```python
from attrs import define, field

@define(slots=True)
class LifecycleObjectRef:
    kind: LifecycleKind
    object_id: str
    name: str | None = None
```

**`from __future__ import annotations`:** Present in every source file under `src/pytest_bdd/` (86 files). This enables forward reference support for type hints and PEP 604 `|` syntax.

## Naming for Testing

**Test fixtures:**
- `testdir` — the standard pytester fixture for writing integration tests that exercise full pytest runs.
- `tmp_path` — standard pytest tmp_path.
- Domain fixtures named descriptively: `allured_testdir`, `httpserver_port`, `remote_xdist_result`.

**Step definitions in tests:**
- `given()`, `when()`, `then()`, `step()` decorators from `pytest_bdd`.
- Steps use `re.compile(...)` or `parsers.parse(...)` for parameter matching.
- `target_fixture` parameter on steps that produce fixture values.
- Step functions named with descriptive verb phrases or `_` for anonymous steps.

**Test data patterns:**
- `testdir.makefile()`, `testdir.makeconftest()` for in-test file creation.
- Inline multi-line strings for feature files and conftest content.
- `textwrap.dedent()` for clean multi-line string formatting.
- Factory helper functions prefixed with `_` (e.g., `_build_gherkin_document()`, `_test_case()`).

---

*Convention analysis: 2026-05-12*
