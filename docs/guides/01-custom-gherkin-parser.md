# How to Write a Custom Gherkin Step Parser

## Problem

You want to use a custom step definition syntax — a domain-specific expression
language, a natural-language pattern, or a special matching algorithm — that
isn't covered by the seven built-in parsers (``re``, ``parse``, ``cfparse``,
``cucumber_expression``, ``cucumber_regex``, ``string``, ``heuristic``).

## Solution

Implement a subclass of ``StepParser`` (the abstract base class from
``pytest_bdd.parsers.base``) and pass it to the ``parser`` argument of
``@given`` / ``@when`` / ``@then``.

### 1. Understand the StepParser ABC

Every step parser must implement five members:

| Member | Kind | Purpose |
|--------|------|---------|
| ``type`` | class attribute | A ``StepDefinitionPatternType`` value describing the parser category. Use ``StepDefinitionPatternType.pytest_bdd_other_expression`` for custom parsers. |
| ``is_matching(request, name)`` | abstract method | Return ``True`` if this parser can handle the given step text. |
| ``parse_arguments(request, name, anonymous_group_names=None)`` | abstract method | Extract keyword arguments from the step text. Return a ``dict`` or ``None`` if parsing fails. |
| ``arguments`` | abstract property | Return a ``Collection[str]`` of argument names this parser expects. Must return an empty collection when not matched. |
| ``__str__()`` | abstract method | Return the parser's pattern as a human-readable string (used in error messages). |

### 2. Create a Custom Parser Class

```python
from __future__ import annotations

from collections.abc import Collection, Iterable
from typing import TYPE_CHECKING

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers.base import StepParser

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import FixtureRequest


class PrefixParser(StepParser):
    """Match steps that start with a fixed prefix string."""

    type = StepDefinitionPatternType.pytest_bdd_other_expression

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self._matched = False

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        return name.startswith(self.prefix)

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        if not name.startswith(self.prefix):
            return None
        remainder = name[len(self.prefix) :].strip()
        return {"text": remainder}

    @property
    def arguments(self) -> Collection[str]:
        return ("text",)

    def __str__(self) -> str:
        return self.prefix
```

### 3. Register the Parser with Step Decorators

```python
from pytest_bdd import given, when, then, parsers

my_parser = PrefixParser("[SETUP]")


@given(parsers.parse("the system is ready"))
def system_ready(): ...


@given("[SETUP] the database is initialized", parser=my_parser)
def database_initialized(text):
    print(f"Setup action: {text}")
```

You can also inject the parser at module level by overriding
``pytest_bdd_get_step_parser`` in a conftest, but the per-decorator
``parser=`` argument is the simplest approach for custom parsers.

### 4. Argument Extraction and Type Conversion

The ``parse_arguments`` method receives three inputs:

* ``request`` — the pytest ``FixtureRequest`` (use for fixture injection when
  building advanced parsers).
* ``name`` — the raw step text (e.g., ``"[SETUP] the database is initialized"``).
* ``anonymous_group_names`` — names for regex capture groups that lack named
  groups (optional; most custom parsers ignore this).

Return a ``dict[str, object]`` mapping argument names to their string values.
Type conversion (``int``, ``float``, ``bool``) happens separately — pytest-bdd
does not perform automatic coercion for custom parsers. If you need typed
arguments, call ``int(value)`` or ``float(value)`` inside ``parse_arguments``
and catch ``ValueError``.

## Complete Example

Here is a complete test file that runs with a custom parser:

```python
from collections.abc import Collection, Iterable

import pytest
from pytest_bdd import given, scenario, then, when
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers.base import StepParser


class StartsWithParser(StepParser):
    type = StepDefinitionPatternType.pytest_bdd_other_expression

    def __init__(self, expected: str) -> None:
        self.expected = expected

    def is_matching(self, request, name):
        return name.startswith(self.expected)

    def parse_arguments(self, request, name, anonymous_group_names=None):
        if not name.startswith(self.expected):
            return None
        return {"rest": name[len(self.expected) :].strip()}

    @property
    def arguments(self):
        return ("rest",)

    def __str__(self):
        return self.expected


GREET_PARSER = StartsWithParser("Greet")


@given("Greet Alice", parser=GREET_PARSER)
def greet_person(rest):
    return {"person": rest}


@when("they receive a welcome message")
def receive_welcome(greet_person):
    greet_person["message"] = f"Welcome, {greet_person['person']}!"


@then("the message should include their name")
def check_message(greet_person):
    assert greet_person["person"] in greet_person["message"]


@scenario("features/greet.feature", "A custom greeting")
def test_greet():
    pass
```

## Common Mistakes

**Not returning an empty tuple from ``arguments`` when there is no match.**
The ``arguments`` property is called even when ``is_matching`` returns
``False``, because pytest-bdd needs to know which fixture names the parser
*can potentially* produce. Always return ``()`` (or an empty ``tuple`` /
``list``) when the parser has no match. Returning ``None`` from
``arguments`` causes a ``TypeError``.

```python
# Wrong
@property
def arguments(self):
    if self._matched:
        return ("text",)
    return None  # TypeError during collection!


# Correct
@property
def arguments(self):
    return ("text",)  # Always returns a collection
```

**Forgetting to declare ``StepDefinitionPatternType``.** Set the ``type``
class attribute to ``StepDefinitionPatternType.pytest_bdd_other_expression``
so the Cucumber Messages protocol can correctly label the parser. Omitting
it produces an ``AttributeError`` at test collection time.

**Not testing with edge cases.** Your custom parser must handle:
* Empty step text (``""``)
* Unicode characters (``"Привет мир"``, ``"こんにちは"``)
* Steps containing characters that have special meaning in regex
  (``"[", "]", "(", ")", "{", "}"``) — custom parsers don't use regex, but
  users often copy-paste patterns that do
* Very long step texts (200+ characters)

**Assuming ``request`` is always available.** During collection, pytest may
call ``is_matching`` with a synthetic or partial request. Make your
``is_matching`` method robust against ``None`` request attributes, or guard
with ``if request is None`` early returns.
