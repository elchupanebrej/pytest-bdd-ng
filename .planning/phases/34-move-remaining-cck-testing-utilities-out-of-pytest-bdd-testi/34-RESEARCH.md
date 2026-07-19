# Phase 34 Research: Move remaining CCK testing utilities out of pytest_bdd/testing

**Researched:** 2026-07-12
**Status:** Ready for planning

---

## Current State Analysis

### Source Module

[cck.py](file:///home/elchupanebrej/winhome/Projects/pytest-bdd/wsl-codex/src/pytest_bdd/testing/cck.py) — 553 lines, 18,819 bytes.

**Public API (`__all__`):**
| Export | Type | Description |
|--------|------|-------------|
| `CCK_RELEASE_TAG` | `str` constant | `"v29.2.2"` |
| `CCK_REPO` | `str` constant | `"cucumber/compatibility-kit"` |
| `CCK_SAMPLE_NAMES` | `list[str]` | 44 sample names (was 41 in spec, actually 41 entries in list) |
| `download_cck_sample` | function | Single sample download with gh→urllib fallback |
| `download_all_cck_samples` | function | Batch download all samples |
| `extract_scenario_names` | function | Parse pickle messages for scenario names |
| `extract_step_texts` | function | Parse pickle messages for step texts |
| `extract_expected_status` | function | Parse testStepFinished for overall status |
| `logger` | `Logger` | Module-level logger |

**Private functions:** `_download_via_gh_api`, `_download_via_urllib`

**Dependencies (imports):** Only stdlib — `base64`, `json`, `logging`, `subprocess`, `urllib.request`, `pathlib`. Zero internal project imports. No dependency on `pytest_bdd` internals.

**Internal note:** Uses `logger = logging.getLogger(__name__)` — after move, logger name will automatically change from `pytest_bdd.testing.cck` to `pytest_bdd_toolchain.case.contract.cck.cck`. This is a cosmetic change with no functional impact (only affects log output filtering).

### Source Directory

[testing/__init__.py](file:///home/elchupanebrej/winhome/Projects/pytest-bdd/wsl-codex/src/pytest_bdd/testing/__init__.py) — 49 lines, 1,496 bytes.

Contents: only docstring + `__tracebackhide__ = True` + `__all__ = []`. No code, no re-exports. Ready for deletion.

The `src/pytest_bdd/testing/` directory contains exactly:
- `__init__.py` (empty placeholder)
- `cck.py` (the file being moved)
- `__pycache__/` (auto-generated, ignored by git)

### Destination Directory

[case/contract/cck/](file:///home/elchupanebrej/winhome/Projects/pytest-bdd/wsl-codex/src/pytest_bdd_toolchain/case/contract/cck/) already contains:
- `__init__.py` — minimal, just `__all__ = []` (2 lines, 13 bytes)
- `conftest.py` — shared fixtures for CCK tests (187 lines)
- `test_cck_allure_conversion.py` — conversion contract tests (172 lines)
- `test_cck_allure_rendering.py` — rendering/UI contract tests (170 lines)

The `cck.py` file will be added alongside these files.

---

## Consumer Analysis — Exact Import Statements

### 1. [conftest.py](file:///home/elchupanebrej/winhome/Projects/pytest-bdd/wsl-codex/src/pytest_bdd_toolchain/case/contract/cck/conftest.py#L21-L26) (Line 21-26)

```python
from pytest_bdd.testing.cck import (
    CCK_RELEASE_TAG,
    download_all_cck_samples,
    extract_scenario_names,
    extract_step_texts,
)
```

**Change to:**
```python
from .cck import (
    CCK_RELEASE_TAG,
    download_all_cck_samples,
    extract_scenario_names,
    extract_step_texts,
)
```

### 2. [test_cck_allure_conversion.py](file:///home/elchupanebrej/winhome/Projects/pytest-bdd/wsl-codex/src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_conversion.py#L15) (Line 15)

```python
from pytest_bdd.testing.cck import CCK_SAMPLE_NAMES
```

**Change to:**
```python
from .cck import CCK_SAMPLE_NAMES
```

### 3. [test_cck_allure_rendering.py](file:///home/elchupanebrej/winhome/Projects/pytest-bdd/wsl-codex/src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_rendering.py#L14) (Line 14)

```python
from pytest_bdd.testing.cck import CCK_SAMPLE_NAMES, extract_scenario_names, extract_step_texts
```

**Change to:**
```python
from .cck import CCK_SAMPLE_NAMES, extract_scenario_names, extract_step_texts
```

### 4. [steps_cck_allure.py](file:///home/elchupanebrej/winhome/Projects/pytest-bdd/wsl-codex/src/pytest_bdd_toolchain/step/steps_cck_allure.py#L16) (Line 16)

```python
from pytest_bdd.testing.cck import download_cck_sample
```

**Change to:**
```python
from pytest_bdd_toolchain.case.contract.cck.cck import download_cck_sample
```

> [!NOTE]
> This file is in a different package subtree (`step/`), so it cannot use relative imports to `case/contract/cck/`. An absolute import is required.

---

## Reference Completeness Check

**All references to `pytest_bdd.testing` in the codebase (`src/` tree):**

| File | Line | Content | Action |
|------|------|---------|--------|
| `src/pytest_bdd/testing/__init__.py` | 15, 26 | Docstring references | Deleted with directory |
| `src/pytest_bdd/testing/cck.py` | 24 | Docstring reference to `__init__` | Moved + updated |
| `src/pytest_bdd_toolchain/case/contract/cck/conftest.py` | 21 | Import | Updated |
| `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_conversion.py` | 15 | Import | Updated |
| `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_rendering.py` | 14 | Import | Updated |
| `src/pytest_bdd_toolchain/step/steps_cck_allure.py` | 16 | Import | Updated |

**No references in:**
- `pyproject.toml` — zero occurrences of `pytest_bdd.testing` or `pytest_bdd/testing`
- `src/pytest_bdd/__init__.py` — does not import or re-export `testing`
- `.pre-commit-config.yaml` — no references
- Vulture whitelist files — no references
- `setup.cfg` — does not exist

---

## Technical Approach

### Plan: Single Plan (1 wave)

This is a pure file-move refactoring with no API changes, no new code, no new tests.

**Steps (order matters):**

1. **Copy** `src/pytest_bdd/testing/cck.py` → `src/pytest_bdd_toolchain/case/contract/cck/cck.py`
2. **Update docstring** in the copied `cck.py`:
   - Line 24: Change `pytest_bdd.testing.__init__` reference → remove or update to reflect new location
   - Line 28: Update "Main consumers" to reference `pytest_bdd_toolchain.case.contract.cck` modules
3. **Update 4 consumer imports** (exact changes listed above)
4. **Delete** `src/pytest_bdd/testing/cck.py`
5. **Delete** `src/pytest_bdd/testing/__init__.py`
6. **Delete** `src/pytest_bdd/testing/` directory (rmdir — should be empty after steps 4-5)
7. **Run linting and tests** to verify

### Docstring Updates in `cck.py` After Move

The `cck.py` docstring references need updating:

| Line | Current | Updated |
|------|---------|---------|
| 24 | `pytest_bdd.testing.__init__: Owns package-level exports...` | Remove this separation entry (no longer applies) |
| 28 | `tests/e2e/conftest.py: Imports CCK utilities...` | `pytest_bdd_toolchain.case.contract.cck.conftest: Shared CCK test fixtures` |

Similar "Main consumers" references appear in individual function docstrings (lines ~286, 348, 400, 458, 515) — all say `tests/e2e/conftest.py`, should say the actual consumers.

---

## Risks and Dependencies

| Risk | Severity | Mitigation |
|------|----------|------------|
| Missed import reference | Low | Exhaustive grep confirms exactly 4 consumer files, zero in pyproject/config |
| Logger name change | Negligible | `logging.getLogger(__name__)` auto-adapts; only affects log filter patterns (none configured) |
| `__pycache__` stale bytecode | Low | `git clean` or re-run; Python recompiles on import |
| Relative import in `steps_cck_allure.py` | N/A | File is in `step/` subtree, must use absolute import — verified approach |

**Dependencies:**
- Phase 33 (depends-on): Must be complete before starting — confirmed complete per STATE.md

---

## Validation Architecture

### Primary: Import Verification

```bash
python -c "from pytest_bdd_toolchain.case.contract.cck.cck import CCK_SAMPLE_NAMES, download_cck_sample, download_all_cck_samples, extract_scenario_names, extract_step_texts, extract_expected_status; print('OK')"
```

### Primary: Negative Import Check

```bash
python -c "from pytest_bdd.testing.cck import CCK_SAMPLE_NAMES" 2>&1 | grep -q "ModuleNotFoundError" && echo "PASS" || echo "FAIL"
```

### Primary: Run CCK Contract Tests

```bash
# Run only the CCK contract test files
python -m pytest src/pytest_bdd_toolchain/case/contract/cck/ -x --no-header -q -m "not docker and not browser"
```

This runs the conversion tests (`test_cck_allure_conversion.py`) which are the only CCK tests that don't require Docker/browser infrastructure. The parametrized tests import `CCK_SAMPLE_NAMES` and use the conftest fixtures — this validates the full import chain.

### Secondary: Lint Verification

```bash
# Ruff check the changed files
ruff check src/pytest_bdd_toolchain/case/contract/cck/ src/pytest_bdd_toolchain/step/steps_cck_allure.py
```

### Secondary: Full Pre-commit

```bash
pre-commit run --all-files
```

### Verification that source directory is fully removed

```bash
test ! -d src/pytest_bdd/testing && echo "PASS: testing/ directory removed" || echo "FAIL: testing/ directory still exists"
```

---

*Phase: 34-move-remaining-cck-testing-utilities-out-of-pytest-bdd-testi*
*Research completed: 2026-07-12*
