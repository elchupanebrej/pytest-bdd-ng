@e2e
Feature: Tutorial example runs as an isolated pytest project
  The tutorial keeps its own pytest configuration, feature root, fixtures, and
  step definitions when invoked from the product repository root.

  Scenario: Autoload discovers the tutorial scenario from its project root
    When I run the tutorial example as its own pytest project
    Then the tutorial acceptance should pass one autoloaded scenario
