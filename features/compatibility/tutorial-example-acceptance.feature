@e2e
Feature: Tutorial example runs as an isolated pytest project
  The tutorial keeps its own pytest configuration, feature root, fixtures, and
  step definitions when invoked from the repository root by its Tox command.

  Scenario: The repository Tox invocation autoloads the tutorial scenario
    When I run the tutorial example with its repository Tox invocation
    Then the tutorial acceptance should pass one autoloaded scenario
