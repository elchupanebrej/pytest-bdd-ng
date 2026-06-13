# Migration Guide: pytest-bdd to pytest-bdd-ng

For existing pytest-bdd users migrating to pytest-bdd-ng. Covers top 10 breaking changes with quick-reference before/after examples.

## 1. Step Decorator Imports

Step decorators (`@given`, `@when`, `@then`, `@step`) are lazy-loaded via `__getattr__`. Import path unchanged.

**Before (pytest-bdd):**
```python
from pytest_bdd import given, when, then
```

**After (pytest-bdd-ng):**
```python
from pytest_bdd import given, when, then  # Same import, lazy-loaded
```

## 2. target_fixture Replaces Implicit Given Fixtures

`@given` no longer auto-creates fixtures. Use `target_fixture` explicitly.

**Before:**
```python
@given("a user exists")
def user():
    return User()
```

**After:**
```python
from pytest_bdd import given, parsers


@given("a user exists", target_fixture="user")
def user():
    return User()
```

## 3. Parser Syntax: {var} Replaces <var>

Angle bracket template syntax replaced by curly braces with `parsers.parse()`.

**Before:**
```python
@given("user <name> exists")
def user(name): ...
```

**After:**
```python
@given(parsers.parse("user {name} exists"))
def user(name): ...
```

## 4. example_converters Moved to Step-Level Converters

`example_converters` on `@scenario` deprecated. Use `converters` on step decorators.

**Before:**
```python
@scenario("test.feature", "Example", example_converters={"count": int})
```

**After:**
```python
@given(parsers.parse("I have {count} items"), converters={"count": int})
def items(count): ...
```

## 5. Hook Signature Changes

Hooks now receive `(request, Run)` with cucumber_messages types instead of `(feature, scenario)` objects.

**Before:**
```python
def pytest_bdd_before_scenario(request, feature, scenario): ...
```

**After:**
```python
from pytest_bdd.model.scenario_run import Run


def pytest_bdd_before_scenario(request: pytest.FixtureRequest, run: Run): ...
```

## 6. Plugin Architecture: Class-Based Pattern

Plugins use class-based registration with entrypoint + hook.py instead of function-based.

**Before:**
```python
def pytest_configure(config):
    config.my_data = {}
```

**After:**
```python
class MyPlugin(StashBound):
    STASH_KEY = "my_plugin"

    def pytest_configure(self, config):
        self.initialize_in_stash(config)
```

## 7. StashBound Pattern for Config

pytest-bdd-ng uses `StashBound` base class for `pytest.config.stash` access.

**Before:**
```python
config._bdd_config = {"key": "value"}
```

**After:**
```python
class BddConfig(StashBound):
    STASH_KEY = "pytest_bdd_config"


config = BddConfig()
config.initialize_in_stash(pytest_config)
```

## 8. Cucumber Messages Integration

pytest-bdd-ng emits Cucumber Messages (NDJSON) for formatter integration.

**Before:** No message protocol support.

**After:**
```bash
pytest --cucumber-json-formatter=json  # Emits NDJSON messages
```

Messages available via `gherkin_message_reporter` plugin for live formatter bridges.

## 9. CLI Flag Changes

`--cucumberjson` removed. Use `--cucumber-json-formatter` via class-based plugin entrypoint.

**Before:**
```bash
pytest --cucumberjson=output.json
```

**After:**
```bash
pytest --cucumber-json-formatter=json --cucumber-json-file=output.json
```

## 156. Allure Plugin Removed

Dead Allure logger plugin removed. Use external `allure-pytest` plugin.

**Before:**
```bash
pip install allure-pytestdir=results
```

**After:**
```bash
pip install allure-pytest
pytest --alluredir=results  # Via external plugin
```

See [DEPRECATIONS.md](DEPRECATIONS.md) for full deprecation timeline.
