@xdist
@slow
Feature: pytest-xdist HTML reporting
  As a test automation engineer
  I want to run my test suite using pytest-xdist
  And generate a consolidated HTML report
  So that I can see the combined results from all workers
  And I do not need to add `-s` or `--capture=no` for reporting behavior

  Scenario: Generate consolidated HTML report from xdist run
    Given a test suite with multiple passing and failing scenarios
    When I run the test suite with pytest-xdist and request an HTML report
    Then a single HTML report is generated
    And the HTML report contains results from all executed scenarios
