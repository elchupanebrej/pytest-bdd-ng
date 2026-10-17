@e2e
Feature: Tutorial example runs as an isolated pytest project
  The tutorial keeps its own pytest configuration, feature root, fixtures, and
  step definitions when invoked from its project root.

  Scenario: Autoload discovers the tutorial scenario from the tutorial directory
    When I run the tutorial example as its own pytest project
    Then the tutorial acceptance should pass one autoloaded scenario
