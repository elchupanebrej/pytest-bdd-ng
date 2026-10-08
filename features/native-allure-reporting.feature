Feature: Live native Allure reporting
  A pytest-cuke run can produce Allure results directly from its in-memory
  Cucumber Messages lifecycle, including when workers report through xdist.

  Scenario: Live reporting records a passed case step attachments and session hierarchy
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one live native Allure scenario with attachments
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results -q"
    Then the native Allure consumer should exit with code 0
    And native Allure results in "allure-results" should contain the passed scenario "Native live report scenario" and its steps
    And native Allure results should preserve their feature hierarchy and session container
    And native Allure results should contain the text, binary, and file attachments
    And the native report consumer should not write a Messages NDJSON file

  Scenario: The live native results can be rendered by the Allure CLI
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one live native Allure scenario with attachments
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results -q"
    Then the native Allure consumer should exit with code 0
    And native Allure results in "allure-results" should contain the passed scenario "Native live report scenario" and its steps
    When I generate an Allure 3 report from native results in "allure-results" into "allure-report"
    Then the native Allure 3 renderer should generate an HTML report

  Scenario: Native results preserve Gherkin descriptions outline identity and step arguments
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains a described native Allure outline with structured arguments
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure -q"
    Then the native Allure consumer should exit with code 0
    And native Allure results should preserve the full Gherkin field contract

  Scenario: xdist workers publish Allure results through the controller once
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains two native Allure scenarios with distinct nested steps and attachments
    And the consumer installs pytest-cuke with its Allure extra
    And the consumer installs pinned pytest-xdist
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results -n 2 -q"
    Then the native Allure consumer should exit with code 0
    And native Allure results should contain both controller scenarios exactly once
    And native Allure results should preserve each xdist case nested steps and attachments exactly once
    And the native Allure results should contain one shared session container for both scenarios

  Scenario: Native reporting coexists with the optional allure-pytest adapter
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one live native Allure scenario with attachments
    And the consumer installs pytest-cuke with its Allure extra
    And the consumer has allure-pytest available for its separate report
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=native-results --alluredir=adapter-results -q"
    Then the native Allure consumer should exit with code 0
    And native Allure results in "native-results" should contain the passed scenario "Native live report scenario" and its steps
    And the optional adapter results should contain one passed pytest item

  Scenario: Reporting stays disabled without Allure dependencies
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one native Allure scenario with attachments
    And the consumer has no Allure Python adapter dependencies
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features -q"
    Then the native Allure consumer should exit with code 0
    And the consumer should have no Allure results and no Allure Python adapter dependencies

  Scenario: Enabling native reporting without its extra gives installation guidance
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one native Allure scenario with attachments
    And the consumer has no Allure Python adapter dependencies
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure -q"
    Then pytest should report an actionable native Allure dependency error

  Scenario: A file blocking the native Allure output path gives an actionable error
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one native Allure scenario with attachments
    And the consumer output path "native-allure-output-file" is blocked by a regular file
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=native-allure-output-file -q"
    Then pytest should report an actionable native Allure output error for "native-allure-output-file"
