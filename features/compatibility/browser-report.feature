@e2e
Feature: Review an Allure report in a real browser
  The browser acceptance lane generates HTML from a real pytest-cuke run,
  serves the report, and checks the visible report in Playwright Chromium.

  Scenario: Chromium shows a passed pytest-cuke scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs the pinned Allure pytest adapter
    And the consumer writes a real reportable pytest-cuke scenario
    When I run installed pytest with arguments "--cuke-autoload --cuke-features-dir=features --alluredir=allure-results -q"
    Then the consumer run should contain one passed Allure scenario result
    When I render the real Allure report and review it in Playwright Chromium
    Then Chromium should display the passed pytest-cuke scenario in the rendered report
