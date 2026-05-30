# Feature: Rule support
  This feature documents support for `Rule` sections and verifies scenarios
  under nested rules are discovered and executed correctly, including examples
  table expansion in a nested rule.

## Scenario: Discover scenarios under rules and nested rules
* Given File "rule.feature" with content:

    ```gherkin
    Feature: Some rules
      Background:
        Given fb

      Rule: A
        Background:
          Given ab
        Example: Example A
          Given a

      Rule: B
        Example: Example B
          Given b

      Rule: C
        Example: Example CA
          Given c

        Rule: CB
          Example: CBA
            Given caa
          Example: CBB
            Given cab
          Example: CBC
            Given ca<key>
            Examples:
              | key |
              | c   |
              | d   |
              | e   |
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given, parsers

    @given(parsers.re(".+"))
    def _any_step():
      ...
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 8      | 0      |
