# decopatch Health Status & CI Matrix Configuration

**Date:** 2026-05-16
**Phase:** 11-audit-prune
**Decisions:** D-01 (decopatch health), D-07/D-08 (CI matrix gates)

---

## decopatch Dependency Health

### Version Information

| Attribute | Value |
|-----------|-------|
| Version | 1.4.10 |
| Last PyPI release | 2022-03-01 |
| Last GitHub commit | 2024-06-01 |
| GitHub stars | ~25 |
| Source | https://github.com/smarie/python-decopatch |

### Usage in Project

- **Location:** `src/pytest_bdd/hook.py`
- **API used:** `decopatch.function_decorator`
- **Decorators built with decopatch:** `@given`, `@when`, `@then`, `@before_mark`, `@after_mark`, `@around_mark`
- **Purpose:** Enables flexible decorator signatures (with/without parentheses, with/without arguments) for step definition decorators

### Stability Assessment

- **Status:** Stable — no breaking changes expected
- **Activity:** Low-activity but functional library
- **Known CVEs:** None
- **Known issues:** None affecting this project
- **Risk level:** Low

### Decision: KEEP (per D-01)

**Rationale:**
- Functional and stable — no bugs or issues encountered
- Low risk — mature decorator library with well-understood behavior
- Not worth rewrite during stabilization phase — stdlib alternative would require re-implementing decorator introspection logic
- No viable drop-in replacement with equivalent flexibility
- Pin to current version to prevent unexpected changes

### Migration Notes (Future)

If decopatch becomes unmaintained or incompatible with future Python versions:
- Alternative: implement custom decorator using `functools.wraps` + signature inspection
- Effort: medium — requires careful handling of all decorator signature variants
- Risk: medium — decorator introspection is error-prone, regression testing required

---

## CI Matrix Configuration

### Tox Environment Summary

**Total environments:** 72 (via `tox --listenvs`)

### Python Version Coverage

| Python Version | Environments |
|----------------|-------------|
| 3.10 | 6 (mypy, coverage-lin, xdist, ruff) |
| 3.11 | 6 (mypy, coverage-lin, xdist, ruff) |
| 3.12 | 10 (mypy, coverage-lin/mac/win, xdist, ruff) |
| 3.13 | 17 (mypy, coverage-lin/mac/win, xdist-remote variants, ruff) |
| 3.14 | 27 (mypy, coverage-lin/mac/win, xdist-remote variants, gherkin33/gherkinlatest, ruff, pre-commit, playwright) |
| PyPy 3.11 | 4 (coverage-lin/mac/win, xdist) |

### pytest Version Coverage

| pytest Version | Python Versions Tested |
|----------------|----------------------|
| 7.0-7.4 | 3.12 |
| 8.0-8.4 | 3.13 |
| 9.0 | 3.14 |
| latest | 3.10, 3.11, 3.12, 3.13, 3.14, PyPy 3.11 |

### Platform Coverage

| Platform | Filter | Environments |
|----------|--------|-------------|
| Linux | `-lin` | ~24 |
| macOS | `-mac` | ~12 |
| Windows | `-win` | ~18 |

### Specialized Environments

| Category | Description |
|----------|-------------|
| `mypy` | Type checking (3.10-3.14) |
| `ruff` | Linting (3.10-3.14) |
| `pre-commit` | Pre-commit hooks (3.14) |
| `playwright-report` | Browser-based reporting (3.14) |
| `xdist-remote-*` | Remote execution via socket/SSH/via (3.13, 3.14) |
| `gherkin33` | gherkin-official>=33 compatibility (3.14) |
| `gherkinlatest` | Latest gherkin compatibility (3.14) |
| `coverage` | Test coverage with pytest-cov (3.10-3.14, PyPy) |

### CI Matrix Validation

- **tox --listenvs:** Exits 0, lists 72 environments
- **Python 3.10-3.14:** All versions covered
- **pytest 7.x-9.x:** All major versions covered
- **Platform filters:** lin, mac, win all present
- **Full matrix execution:** CI gate (per D-07, D-08), not a local task

### Notes

- Python 3.14 has the most environments (27) — primary development target
- Python 3.12-3.13 have full platform coverage (lin/mac/win)
- Python 3.10-3.11 have limited coverage (lin only for coverage, plus mypy/ruff)
- PyPy 3.11 included for alternative runtime coverage
- Remote xdist testing covers socket, SSH, and via transports on Linux and Windows
