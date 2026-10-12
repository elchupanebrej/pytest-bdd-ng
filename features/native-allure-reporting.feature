@e2e
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
    And native Allure timestamps should match the live Messages timestamps

  Scenario: Nested feature paths use POSIX separators in native Allure fullName
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one native Allure scenario in a nested feature directory
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results -q"
    Then the native Allure consumer should exit with code 0
    And native Allure fullName should preserve POSIX separators for scenario "Nested native feature path scenario"

  Scenario: Native reporting activates from cuke_allure ini configuration alone
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one native Allure scenario with attachments
    And the consumer configures native Allure output in cuke_allure ini
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "-q"
    Then the native Allure consumer should exit with code 0
    And native Allure results in "allure-results" should contain the passed scenario "Native live report scenario" and its steps
    And the native report consumer should not write a Messages NDJSON file

  Scenario: Native reporting works with allure-python-commons and no allure-pytest adapter
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one native Allure scenario without adapter API calls
    And the consumer installs allure-python-commons without allure-pytest
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results -q"
    Then the native Allure consumer should exit with code 0
    And native Allure results in "allure-results" should contain the passed scenario "Native live report scenario" with Gherkin steps only
    And the consumer should confirm allure-pytest is absent and allure-python-commons is present

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

  Scenario: xdist resolves native Allure structure when worker-local Messages IDs collide
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains two native Allure scenarios with colliding worker-local Messages IDs
    And the consumer installs pytest-cuke with its Allure extra
    And the consumer installs pinned pytest-xdist
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results -n 2 --dist=load -q"
    Then the native Allure consumer should exit with code 0
    And the two xdist workers should reuse a local Messages TestCase ID for different pickles
    And native Allure results should contain both controller scenarios exactly once
    And native Allure results should preserve each xdist case nested steps and attachments exactly once
    And the native Allure results should contain one shared session container for both scenarios

  Scenario: Duplicate worker batches are rejected before native Allure publication
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains two native Allure scenarios with distinct nested steps and attachments
    And the consumer installs pytest-cuke with its Allure extra
    And the consumer installs pinned pytest-xdist
    And the consumer replays its first controller-observed worker batch at controller session finish
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-parser=python --cuke-allure=allure-results -n 2 --dist=load -q"
    Then the native Allure consumer should exit nonzero
    And duplicate worker batches should be diagnosed without republishing to native Allure

  Scenario: Native reporting coexists with the optional allure-pytest adapter
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one native Allure scenario and one ordinary pytest test
    And the consumer installs pytest-cuke with its Allure extra
    And the consumer has allure-pytest available for its separate report
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=native-results --alluredir=adapter-results -q"
    Then the native Allure consumer should exit with code 0
    And native and adapter Allure results should contain the exact BDD and ordinary pytest cases

  Scenario: Native and adapter reporting reject the same output directory before tests run
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains one native Allure scenario and an ordinary pytest run marker
    And the consumer installs pytest-cuke with its Allure extra
    And the consumer has allure-pytest available for its separate report
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results --alluredir=allure-results -q"
    Then pytest should reject the overlapping Allure output paths before tests run

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

  Scenario: Live reporting preserves failed skipped and undefined outcomes with nested traceback
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains failed skipped and undefined native Allure scenarios
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results -q"
    Then the native Allure consumer should exit nonzero
    And native Allure results should preserve failed skipped and undefined cases with truthful details

  Scenario: Nested skip and error statuses agree in local and xdist runs
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains nested native Allure skip and error outcomes
    And the consumer installs pytest-cuke with its Allure extra
    And the consumer installs pinned pytest-xdist
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results-local -q"
    Then the native Allure consumer should exit nonzero
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-allure=allure-results-xdist -n 2 -q"
    Then the native Allure consumer should exit nonzero
    And native Allure results should preserve matching nested skip and error statuses in "allure-results-local" and "allure-results-xdist"

  Scenario: Live reporting preserves failed Background status and traceback
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains a native Allure scenario with a failing Gherkin Background
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-parser=python --cuke-allure=allure-results -q"
    Then the native Allure consumer should exit nonzero
    And native Allure results should preserve the failed Background diagnostic

  Scenario: Live reporting preserves a failing BEFORE_TEST_RUN hook fixture
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains a scenario and a failing native run hook "BEFORE_TEST_RUN" with sentinel "native before-run hook failure sentinel"
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-parser=python --cuke-allure=allure-results -q"
    Then the native Allure consumer should exit nonzero
    And the native Allure container should preserve the failed "BEFORE_TEST_RUN" fixture with sentinel "native before-run hook failure sentinel"

  Scenario: Live reporting preserves a failing AFTER_TEST_RUN hook fixture
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains a scenario and a failing native run hook "AFTER_TEST_RUN" with sentinel "native after-run hook failure sentinel"
    And the consumer installs pytest-cuke with its Allure extra
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-parser=python --cuke-allure=allure-results -q"
    Then the native Allure consumer should exit nonzero
    And the native Allure container should preserve the failed "AFTER_TEST_RUN" fixture with sentinel "native after-run hook failure sentinel"

  Scenario: xdist keeps an external tryfirst session-finish failure in the controller Allure container
    Given a fresh isolated pytest-cuke consumer is ready
    And the consumer contains a scenario and a failing native run hook "AFTER_TEST_RUN" with sentinel "xdist external tryfirst session-finish failure sentinel"
    And the consumer installs pytest-cuke with its Allure extra
    And the consumer installs pinned pytest-xdist
    When I run the native Allure consumer with arguments "--cuke-autoload --cuke-features-dir=features --cuke-parser=python --cuke-allure=allure-results -n 2 --dist=load -q"
    Then the native Allure consumer should exit nonzero
    And the controller-owned native Allure session container should preserve the failed "AFTER_TEST_RUN" fixture with sentinel "xdist external tryfirst session-finish failure sentinel"
