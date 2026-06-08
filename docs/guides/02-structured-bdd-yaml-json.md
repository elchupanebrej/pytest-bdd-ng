# How to Use Structured BDD (YAML / JSON / TOML / HOCON)

## Problem

You want to write BDD scenarios in YAML, JSON, TOML, HOCON, or JSON5 instead
of Gherkin ``.feature`` files — for data-driven tests, integration with
existing YAML/JSON tooling, or because your team prefers structured formats
over plain-text Gherkin.

## Solution

Enable the **struct-bdd** plugin, create feature definitions in a supported
structured format, and let the plugin convert them to Gherkin internally.
Your ``@given`` / ``@when`` / ``@then`` decorators work unchanged.

### 1. Install the struct-bdd Extra

```bash
pip install pytest-bdd-ng[struct-bdd]
```

This pulls in ``hjson``, ``json5``, ``pyhocon``, ``PyYAML``, and the
``types-PyYAML`` stubs. On Python 3.10 it also brings ``tomli`` for TOML
support (Python 3.11+ uses stdlib ``tomllib``).

### 2. Write Scenarios in Structured Format

Create a file with the ``.struct.*`` suffix. The plugin recognizes:

| Extension | Format | Example filename |
|-----------|--------|------------------|
| ``.struct.yaml`` / ``.struct.yml`` / ``.struct.bdd`` | YAML | ``login.struct.yaml`` |
| ``.struct.json`` | JSON | ``login.struct.json`` |
| ``.struct.json5`` | JSON5 | ``login.struct.json5`` |
| ``.struct.hjson`` | HJSON | ``login.struct.hjson`` |
| ``.struct.hocon`` | HOCON | ``login.struct.hocon`` |
| ``.struct.toml`` | TOML | ``login.struct.toml`` |

**YAML example** — ``features/login.struct.yaml``:

```yaml
name: User Login
scenarios:
  - name: Successful login with valid credentials
    steps:
      - text: the user "alice" exists with password "secret"
        keyword: Given
      - text: the user logs in as "alice" with password "secret"
        keyword: When
      - text: the dashboard is displayed
        keyword: Then

  - name: Login fails with wrong password
    steps:
      - text: the user "bob" exists with password "correct"
        keyword: Given
      - text: the user logs in as "bob" with password "wrong"
        keyword: When
      - text: an error message "Invalid credentials" is shown
        keyword: Then

  - name: Login with empty credentials is rejected
    steps:
      - text: the login page is displayed
        keyword: Given
      - text: the user submits the login form with empty fields
        keyword: When
      - text: validation errors are shown for both fields
        keyword: Then
```

**TOML example** — ``features/login.struct.toml``:

```toml
name = "User Login"

[[scenarios]]
name = "Successful login with valid credentials"

[[scenarios.steps]]
text = 'the user "alice" exists with password "secret"'
keyword = "Given"
[[scenarios.steps]]
text = 'the user logs in as "alice" with password "secret"'
keyword = "When"
[[scenarios.steps]]
text = "the dashboard is displayed"
keyword = "Then"

[[scenarios]]
name = "Login fails with wrong password"

[[scenarios.steps]]
text = 'the user "bob" exists with password "correct"'
keyword = "Given"
[[scenarios.steps]]
text = 'the user logs in as "bob" with password "wrong"'
keyword = "When"
[[scenarios.steps]]
text = 'an error message "Invalid credentials" is shown'
keyword = "Then"
```

### 3. How the Plugin Maps to Gherkin Internally

The ``struct_bdd`` plugin implements three pytest hooks:

1. **``pytest_bdd_get_mimetype``** — detects structured files by extension
   and returns the appropriate ``Mimetype`` enum.
2. **``pytest_bdd_get_parser``** — provides a ``StructBDDParser`` factory
   configured for the detected format (YAML, JSON, etc.).
3. **``pytest_bdd_is_collectible``** — returns ``True`` for files with
   ``.struct.*`` suffixes so pytest can collect scenarios from them.

The parser converts each scenario definition into a ``GherkinDocument``
object, and the pickle runner executes it identically to a Gherkin scenario.
Step definitions, hooks, and formatters are completely agnostic to the source
format.

### 4. File Naming and Discovery

- Files must have **two suffixes**: the ``.struct`` marker plus the format
  extension (e.g., ``.struct.yaml``, not just ``.yaml``).
- Files go in your features directory (default: ``features/``).
- You can mix structured files with plain ``.feature`` files in the same
  directory; both are collected automatically.

### 5. Using Step Definitions

The ``@given`` / ``@when`` / ``@then`` decorators work exactly as they do
with Gherkin ``.feature`` files:

```python
from pytest_bdd import given, when, then, parsers

@given(parsers.parse('the user "{username}" exists with password "{password}"'))
def user_exists(username, password):
    ...

@when(parsers.parse('the user logs in as "{username}" with password "{password}"'))
def user_logs_in(username, password):
    ...

@then("the dashboard is displayed")
def dashboard_displayed():
    ...
```

## Complete Example

Put ``features/calculator.struct.yaml``:

```yaml
name: Calculator
scenarios:
  - name: Add two numbers
    steps:
      - text: the calculator is reset
        keyword: Given
      - text: I enter 3
        keyword: When
      - text: I press add
        keyword: When
      - text: I enter 5
        keyword: When
      - text: I press equals
        keyword: When
      - text: the result is 8
        keyword: Then

  - name: Subtract two numbers
    steps:
      - text: the calculator is reset
        keyword: Given
      - text: I enter 10
        keyword: When
      - text: I press subtract
        keyword: When
      - text: I enter 4
        keyword: When
      - text: I press equals
        keyword: When
      - text: the result is 6
        keyword: Then
```

And ``tests/test_calculator.py``:

```python
from pytest_bdd import given, scenario, then, when

@scenario("features/calculator.struct.yaml", "Add two numbers")
def test_add():
    pass

@scenario("features/calculator.struct.yaml", "Subtract two numbers")
def test_subtract():
    pass

@given("the calculator is reset")
def calculator_reset():
    return {"value": 0, "operation": None}

@when("I enter 3")
def enter_3(calculator_reset):
    ...

@when("I press add")
def press_add(calculator_reset):
    calculator_reset["operation"] = "add"

@then("the result is 8")
def check_result_8(calculator_reset):
    assert calculator_reset["value"] == 8
```

## Common Mistakes

**YAML indentation errors.** YAML is indentation-sensitive. Using tabs
instead of spaces, inconsistent nesting, or mixing flow and block styles
causes parse failures. Symptoms: ``ScannerError`` or ``ParserError`` from
the ``yaml`` library. Fix: use only spaces and keep indentation consistent
(2 or 4 spaces). Run your YAML through a linter before committing.

**Missing required scenario fields.** Every scenario entry must have a
``name`` (string) and a ``steps`` array. Omitting either causes a
``KeyError`` during collection. The step array can be empty (resulting in an
empty scenario, which is allowed unless ``bdd_allow_empty_scenarios = false``
is set).

**Expecting all Gherkin features to work in structured format.** The
structured BDD plugin supports *scenarios and scenario outlines*, but
Gherkin features like ``Background``, ``Rule``, and ``Examples`` tables are
parsed differently in Gherkin than in structured formats. When using
structured BDD, embed precondition steps directly in each scenario instead
of using ``Background``.

**Using bare format extensions without ``.struct``.** Files named
``features/login.yaml`` (without the ``.struct`` marker) are NOT collected
by the struct-bdd plugin. Use ``features/login.struct.yaml`` instead. The
``.struct`` marker tells pytest-bdd to treat the file as structured BDD.

**Forgetting to install the extra.** Running ``pytest`` without having
``pytest-bdd-ng[struct-bdd]`` installed causes ``ImportError`` for ``hjson``,
``json5``, or ``pyhocon``. Install the extra before running tests:

```bash
pip install pytest-bdd-ng[struct-bdd]
```
