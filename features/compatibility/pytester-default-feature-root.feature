Feature: Pytester child projects without a default feature directory
  Pytest-cuke autoload must not break plain pytest sessions in unrelated temporary projects.

  Scenario: A plain child test passes when the default feature directory is absent
    Given an isolated child project has one passing plain pytest test
    When I run pytest in the isolated child project with its default feature root
    Then the isolated child pytest session should pass its plain test

  Scenario: A missing feature directory in pytest.ini still reports an error
    Given an isolated child project has one passing plain pytest test
    When I run pytest in the isolated child project with a missing feature root in pytest.ini
    Then the isolated child pytest session should report the missing feature root

  Scenario: A missing feature directory from override-ini still reports an error
    Given an isolated child project has one passing plain pytest test
    When I run pytest in the isolated child project with a missing feature root from override-ini
    Then the isolated child pytest session should report the missing feature root
