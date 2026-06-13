# How to Migrate from pytest-bdd (v1) to pytest-bdd-ng

## Problem

You are using the original ``pytest-bdd`` library (unmaintained, last release
was years ago) and want to migrate to ``pytest-bdd-ng`` — which provides
active maintenance, mypy ``--strict`` typing, a Go-based Gherkin parser,
Cucumber Messages protocol support, and a modular plugin architecture.

## Solution

Follow a systematic migration path: uninstall the old package, update
imports, fix fixture injection, migrate hooks, handle breaking CLI changes,
and then opt in to new features.

### 1. Why Migrate

| Feature | pytest-bdd v1 | pytest-bdd-ng |
|---------|---------------|---------------|
| Maintenance | Unmaintained | Active (2024+) |
| Type checking | No type hints | Full mypy ``--strict`` passes |
| Gherkin parsing | Python-only | Optional Go cgo parser (5-10x faster) |
| Reporting | Custom JSON | Cucumber Messages protocol (12+ formatters) |
| Plugin model | Monolithic | 18 modular plugins (core + extras) |
| Structured BDD | Not supported | YAML, JSON, TOML, HOCON, JSON5 |
| Test group ordering | Not supported | Semantic groups with xdist barriers |
| Python support | 2.7—3.9 | 3.10—3.14 |

### 2. Breaking Changes Checklist

#### Fixture Injection

**pytest-bdd v1** matched step argument names to fixture names
automatically:

```python
# pytest-bdd v1 — argument name "browser" auto-matched to fixture
@given("I am logged in")
def logged_in(browser):
    browser.visit("/login")
```

**pytest-bdd-ng** requires explicit fixture injection. Pass fixture names
through ``target_fixture`` or use test function arguments:

```python
# pytest-bdd-ng — explicit fixtures
@given("I am logged in")
def logged_in(browser):
    browser.visit("/login")


# In the test function, request the fixture explicitly:
@scenario("features/login.feature", "Login")
def test_login(browser):
    assert browser.title == "Dashboard"
```

#### Hook Signatures

**pytest-bdd v1** hooks used ``(feature, scenario)`` tuples:

```python
def pytest_bdd_before_scenario(request, feature, scenario):
    print(f"Scenario: {scenario.name}")
```

**pytest-bdd-ng** hooks use ``(request, run)`` with structured runtime
objects:

```python
def pytest_bdd_before_scenario(request, run):
    scenario_run = run.active_scenario_run
    print(f"Scenario: {scenario_run.name}")
```

Migration guide for all hooks:

| v1 Hook | v1 Signature | pytest-bdd-ng Hook | New Signature |
|---------|-------------|---------------------|---------------|
| ``pytest_bdd_before_scenario`` | ``(request, feature, scenario)`` | ``pytest_bdd_before_scenario`` | ``(request, run)`` |
| ``pytest_bdd_after_scenario`` | ``(request, feature, scenario)`` | ``pytest_bdd_after_scenario`` | ``(request, run)`` |
| ``pytest_bdd_before_step`` | ``(request, feature, scenario, step, step_func)`` | ``pytest_bdd_before_step`` | ``(request, run, ...)`` |
| ``pytest_bdd_after_step`` | ``(request, feature, scenario, step, step_func, step_func_args)`` | ``pytest_bdd_after_step`` | ``(request, run, ...)`` |

The full list of hooks is in ``src/pytest_bdd/plugin/pickle_runner/hook.py``
and includes additional hooks not present in v1:
``pytest_bdd_step_error``, ``pytest_bdd_step_func_lookup_error``,
``pytest_bdd_before_step_call``, ``pytest_bdd_get_step_caller``.

#### CLI Flags

| pytest-bdd v1 flag | pytest-bdd-ng flag | Notes |
|--------------------|-------------------|-------|
| ``--cucumberjson`` | ``--cucumber-json-formatter`` | Replaced by class-based plugin entrypoint |
| *(none)* | ``--cucumber-pretty`` | New: pretty terminal output |
| *(none)* | ``--cucumber-progress`` | New: progress bar |
| *(none)* | ``--cucumber-junit`` | New: JUnit XML output |
| *(none)* | ``--cucumber-usage`` | New: step usage stats |

#### Configuration (INI Options)

| pytest-bdd v1 option | pytest-bdd-ng option | Notes |
|----------------------|---------------------|-------|
| ``bdd_features_base_dir`` | ``bdd_features_base_dir`` | Unchanged |
| ``bdd_strict_gherkin`` | *(removed)* | Gherkin strict mode always enabled |
| *(none)* | ``bdd_allow_empty_scenarios`` | New: allow scenarios with no steps |
| *(none)* | ``test_group_order`` | New: semantic group ordering |
| *(none)* | ``test_group_default`` | New: default test group |
| *(none)* | ``test_group_paths`` | New: group-to-path mapping |

#### Step Parser Behavior

The heuristic parser in pytest-bdd-ng has a different priority order.
In v1, the first registered step definition that "looked like" a match
would win. In pytest-bdd-ng, priority is based on parser specificity:

1. String parsers (exact match)
2. Regex parsers (``re``)
3. Parse parsers (``parse``)
4. Cucumber expression parsers
5. Heuristic (falls through)

If you have overlapping step definitions that relied on registration order
in v1, they may match differently in pytest-bdd-ng. Run your test suite
and check for ``StepDefinitionNotFoundError`` messages.

#### Plugin Loading

**pytest-bdd v1** loaded all functionality at startup. **pytest-bdd-ng**
splits plugins into core (always loaded) and extras (loaded when the
corresponding optional dependency is installed):

| Extra | Plugins | Install Command |
|-------|---------|-----------------|
| ``formatters`` | 10 formatter plugins | ``pip install pytest-bdd-ng[formatters]`` |
| ``struct-bdd`` | Structured BDD parser | ``pip install pytest-bdd-ng[struct-bdd]`` |
| ``allure`` | Allure logger | ``pip install pytest-bdd-ng[allure]`` |
| ``code-gen`` | Test code generator | ``pip install pytest-bdd-ng[code-gen]`` |

If you don't install the extra, the corresponding plugin does not load.
Check your CI pipeline for missing optional dependencies.

### 3. Migration Steps

Follow this sequence:

**a) Install pytest-bdd-ng and uninstall pytest-bdd:**

```bash
pip uninstall pytest-bdd
pip install pytest-bdd-ng
```

**b) Update imports** — the import path ``from pytest_bdd import ...`` is
unchanged:

```python
# Unchanged — works in both v1 and pytest-bdd-ng
from pytest_bdd import given, when, then, scenario, scenarios, parsers
```

**c) Update fixture injection** — review step definitions for fixture name
mismatches. The most common issue is step arguments that were accidentally
matched to fixtures by name in v1.

**d) Update hooks** — rename ``before_scenario`` / ``after_scenario`` to
``pytest_bdd_before_scenario`` / ``pytest_bdd_after_scenario``, and update
the signature from ``(request, feature, scenario)`` to ``(request, run)``.

**e) Run the test suite** — fix step matching errors, hook signature errors,
and import errors. Run with ``-v`` to see which steps fail to match.

**f) Enable new features** — once the suite passes, opt in to:

```bash
# Go parser (requires Go 1.21+ at build time)
pip install pytest-bdd-ng[go-parser]

# Structured BDD
pip install pytest-bdd-ng[struct-bdd]

# All formatters
pip install pytest-bdd-ng[formatters]
```

### 4. Before/After Comparison

**Before (pytest-bdd v1):**

```python
# tests/test_login.py
from pytest_bdd import given, scenario, then, when


@given("the login page is open")
def login_page_open(browser):  # 'browser' auto-matched to fixture
    browser.visit("/login")


@when('I enter "admin" and "secret"')
def enter_credentials(browser):
    browser.fill("username", "admin")
    browser.fill("password", "secret")
    browser.click("Login")


@then("I see the dashboard")
def see_dashboard(browser):
    assert "Dashboard" in browser.title


@scenario("features/login.feature", "Login with valid credentials")
def test_login():
    pass
```

**After (pytest-bdd-ng):**

```python
# tests/test_login.py
from pytest_bdd import given, parsers, scenario, then, when


@given("the login page is open")
def login_page_open(browser):
    browser.visit("/login")


@when(parsers.parse('I enter "{username}" and "{password}"'))
def enter_credentials(browser, username, password):
    browser.fill("username", username)
    browser.fill("password", password)
    browser.click("Login")


@then("I see the dashboard")
def see_dashboard(browser):
    assert "Dashboard" in browser.title


@scenario("features/login.feature", "Login with valid credentials")
def test_login(browser):
    assert browser.title == "Dashboard"
```

Key changes:
* ``parsers.parse()`` for parameterized steps (replaces ``<var>`` syntax).
* Test function now requests ``browser`` fixture explicitly in the
  ``@scenario`` decorated function.
* ``target_fixture`` is optional — use it only when a step needs to pass
  values to subsequent steps.

## Common Mistakes

**Forgetting to install extras.** Plugins silently fail to load when their
extra is not installed. If you see ``E   ModuleNotFoundError: No module
named 'pytest_bdd.plugin.cucumber_pretty'`` or similar, install:

```bash
pip install pytest-bdd-ng[formatters,struct-bdd]
```

**Assuming fixture injection works the same way.** In v1, every argument
to a step function was auto-matched to a fixture by name. In
pytest-bdd-ng, you must request fixtures explicitly in the test function
or use ``target_fixture``. If a step function argument is not a parsed
parameter and not an explicit fixture, it receives ``None``.

**Not updating CI configuration.** Your CI pipeline may have hardcoded
plugin names or CLI flags from v1. Check:

* ``pytest.ini`` / ``pyproject.toml`` for ``addopts`` containing old
  flags.
* GitHub Actions workflow files for ``--cucumberjson`` references.
* ``conftest.py`` for hook signature changes.

**Mixing old and new hook signatures.** If you have both
``pytest_bdd_before_scenario(request, feature, scenario)`` and
``pytest_bdd_before_scenario(request, run)`` in the same file, the old
signature causes a ``TypeError`` at runtime because pytest-bdd-ng passes
only two arguments.

**Not handling deprecation warnings.** pytest-bdd-ng emits
``DeprecationWarning`` for ``example_converters`` on ``@scenario`` and for
``<var>`` template syntax. Convert these to ``parsers.parse()`` with
``{var}`` syntax before they are removed in version 3.0:

```python
# Deprecated (v1 style)
@given("I have <count> items")
@scenario("...", example_converters={"count": int})

# Recommended (pytest-bdd-ng style)
@given(parsers.parse("I have {count} items"))
@scenario("...", converters={"count": int})
```
