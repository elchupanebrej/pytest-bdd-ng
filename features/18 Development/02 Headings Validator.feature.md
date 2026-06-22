# Feature: Headings Validator CLI
  Verify the validate_feature_headings.py pre-commit CLI tool detects empty feature and scenario headings.

## Scenario: Heading validation passes on clean feature document
  * Given Mock file "clean.feature.md" with content:

    ```gherkin
    # Feature: Clean feature
      Description of feature.

      ## Scenario: Clean scenario
        * Given clean steps
    ```
  * When run `python -m pytest_bdd.script.validate_feature_headings --root-path .`
  * Then the command exit code is 0

## Scenario: Heading validation fails on empty feature heading
  * Given Mock file "empty_feature.feature.md" with content:

    ```gherkin
    # Feature:
      Description of feature.
    ```
  * When run `python -m pytest_bdd.script.validate_feature_headings --root-path .`
  * Then the command exit code is 1
  * And the renderer terminal output includes:
    | Feature heading title is empty |
