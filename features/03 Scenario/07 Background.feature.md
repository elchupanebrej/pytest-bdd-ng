# Feature: Scenario background execution
  This feature documents two background guarantees:
  background steps run before scenario steps, and background doc strings are
  exposed to step functions with the expected content.

## Scenario: Background values are available and execute in order
* Given File "background.feature" with content:

    ```gherkin
    Feature: Background support
      Background:
        Given foo has a value "bar"
        And a background step with multiple lines:
          """
          one
          two
          """

      Scenario: Basic usage
        Then foo should have value "bar"

      Scenario: Background steps are executed first
        Given foo has no value "bar"
        And foo has a value "dummy"
        Then foo should have value "dummy"
        And foo should not have value "bar"
    ```

* And File "conftest.py" with content:

    ```python
    import pytest
    from pytest_bdd import given, then, parsers

    @pytest.fixture
    def foo():
      return {}

    @given(parsers.re(r"a background step .*"))
    def _multiline(step):
      assert step.argument.doc_string.content == "one\ntwo"

    @given('foo has a value "bar"')
    def _bar(foo):
      foo["bar"] = "bar"

    @given('foo has a value "dummy"')
    def _dummy(foo):
      foo["dummy"] = "dummy"

    @given('foo has no value "bar"')
    def _no_bar(foo):
      assert foo["bar"] == "bar"
      del foo["bar"]

    @then('foo should have value "bar"')
    def _then_bar(foo):
      assert foo["bar"] == "bar"

    @then('foo should have value "dummy"')
    def _then_dummy(foo):
      assert foo["dummy"] == "dummy"

    @then('foo should not have value "bar"')
    def _then_no_bar(foo):
      assert "bar" not in foo
    ```

* And File "test_background.py" with content:

    ```python
    from pytest_bdd import scenario

    @scenario("background.feature", "Basic usage")
    def test_background_basic():
      pass

    @scenario("background.feature", "Background steps are executed first")
    def test_background_order():
      pass
    ```

* When run pytest

    | cli_args | -k | test_background.py |
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 2      | 0      |
