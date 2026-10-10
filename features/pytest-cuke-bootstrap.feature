Feature: Installed pytest-cuke product bootstrap
  A consumer installs the public package, discovers its pytest plugin, and uses
  the canonical pytest-cuke commands and configuration without harness imports.

  Scenario Outline: A built distribution exposes only the canonical root facade
    Given the pytest-cuke <distribution> built from this checkout is installed in a fresh consumer project
    And consumer file "test_public_api.py" contains:
      """python
      import importlib.metadata
      import importlib.util
      from pathlib import PurePosixPath

      import pytest_cuke
      from pytest_cuke import *
      from pytest_cuke.formatter_api import FormatterAsset, FormatterRequest, FormatterRequestFactory, FormatterSelection

      PUBLIC_NAMES = {"given", "when", "then", "step", "parsers", "scenario", "scenarios"}
      FORMATTER_NAMES = {"FormatterAsset", "FormatterRequest", "FormatterRequestFactory", "FormatterSelection"}


      def test_installed_public_facade():
          distribution = importlib.metadata.distribution("pytest-cuke")
          assert distribution.version
          assert set(pytest_cuke.__all__) == PUBLIC_NAMES
          assert {name for name in globals() if name in PUBLIC_NAMES} == PUBLIC_NAMES
          assert not any(hasattr(pytest_cuke, name) for name in FORMATTER_NAMES)
          assert all(
              value is not None
              for value in (FormatterAsset, FormatterRequest, FormatterRequestFactory, FormatterSelection)
          )
          assert all(callable(getattr(pytest_cuke, name)) for name in PUBLIC_NAMES - {"parsers"})
          assert all(hasattr(parsers, name) for name in ("parse", "re", "cfparse", "cuke_expressions"))
          assert all(not hasattr(pytest_cuke, name) for name in ("Feature", "Scenario", "Step", "Pickle", "Runner"))
          assert importlib.util.find_spec("pytest_bdd") is None
          assert importlib.util.find_spec("allure_pytest") is None
          assert all(importlib.util.find_spec(name) is None for name in ("yaml", "hjson", "json5", "pyhocon"))

          files = distribution.files or ()
          harness_assets = {".planning", ".agents", "pytest_cuke_testing", "tests", "features", "examples"}
          assert not any(harness_assets.intersection(PurePosixPath(str(path)).parts) for path in files)
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload test_public_api.py -q"
    Then pytest should exit with code 0
    And the installed distribution archive excludes harness and test assets

    Examples:
      | distribution     |
      | wheel            |
      | sdist            |

  Scenario: Plugin autoload runs a Background and a two-row Outline through the facade
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest import fixture
      from pytest_cuke import given, parsers, then, when


      @fixture
      def seed_value():
          return 40


      @given("the canonical pytest plugin is loaded once")
      def canonical_plugin_is_loaded_once(pytestconfig):
          plugins = [
              plugin
              for name, plugin in pytestconfig.pluginmanager.list_name_plugin()
              if name == "cuke"
          ]
          assert len(plugins) == 1
          assert plugins[0].__name__ == "pytest_cuke.plugin"


      @given("the shared pytest fixture is active")
      def shared_fixture_is_active(seed_value):
          assert seed_value == 40


      @when(parsers.parse("I add {amount:d} to the seed value"), target_fixture="total")
      def add_to_seed(seed_value, amount):
          return seed_value + amount


      @then(parsers.parse("the total is {expected:d}"))
      def check_total(total, expected):
          assert total == expected
      """
    And consumer file "features/fixture-outline.feature" contains:
      """gherkin
      Feature: Installed consumer scenarios
        Background:
          Given the canonical pytest plugin is loaded once
          Given the shared pytest fixture is active

        Scenario Outline: A parsed step can produce a target fixture
          When I add <amount> to the seed value
          Then the total is <expected>

          Examples:
            | amount | expected |
            | 2      | 42       |
            | 5      | 45       |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=features --cuke-autoload --cuke-json=report.json --cuke-progress"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And pytest terminal output should report 2 passed tests
    And consumer artifact "report.json" should describe one feature with 2 passed scenarios

  Scenario: NDJSON reports a no-Background scenario after plugin autoload
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, parsers, then


      @given(parsers.parse("the value is {value:d}"), target_fixture="number")
      def value_is(value):
          return value


      @then(parsers.parse("the result is {expected:d}"))
      def result_is(number, expected):
          assert number == expected
      """
    And consumer file "features/messages.feature" contains:
      """gherkin
      Feature: Messages output
        Scenario: The stream describes an executed scenario
          Given the value is 42
          Then the result is 42
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=features --cuke-autoload --cuke-messages-ndjson=messages.ndjson"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer artifact "messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 2 passed steps

  Scenario: Pytest reports invalid canonical option values
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir="
    Then pytest should exit with a non-zero code
    And pytest output should explain the invalid feature directory

  Scenario: A command-line feature directory overrides the canonical config value
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "configured-features"
      cuke_autoload = true
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the command-line feature was selected")
      def command_line_feature_selected():
          pass


      @given("the configuration-only feature was selected")
      def configuration_only_feature_selected():
          raise AssertionError("pytest ignored --cuke-features-dir")
      """
    And consumer file "configured-features/configured.feature" contains:
      """gherkin
      Feature: Configured feature directory
        Scenario: This feature must be overridden
          Given the configuration-only feature was selected
      """
    And consumer file "cli-features/selected.feature" contains:
      """gherkin
      Feature: Command-line feature directory
        Scenario: The CLI value takes precedence
          Given the command-line feature was selected
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=cli-features"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: External Examples load in autoload and explicit bindings and stay visible in reports
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, parsers, then


      @given("the lookup service is ready", target_fixture="lookup_ready")
      def lookup_service():
          return True


      @given(parsers.parse("user row {name} has tier {tier}"), target_fixture="user_record")
      def load_user(lookup_ready, name, tier):
          assert lookup_ready
          return {"name": name, "tier": tier}


      @then(parsers.parse("looked up user {name} has tier {tier}"))
      def check_user(user_record, name, tier):
          assert user_record == {"name": name, "tier": tier}


      @given("the report session is open", target_fixture="report_session")
      def report_session():
          return True


      @given(parsers.parse("the report row is {name}"), target_fixture="report_row")
      def load_report_row(report_session, name):
          assert report_session
          return name


      @then(parsers.parse("the report row result is {expected}"))
      def check_report_row(report_row, expected):
          assert report_row == expected
      """
    And consumer file "features/users.csv" contains:
      """csv
      name,tier
      Ada,gold
      Grace,silver
      """
    And consumer file "features/users.feature" contains:
      """gherkin
      Feature: External users
        Background:
          Given the lookup service is ready

        Scenario Outline: Look up a user from the external table
          Given user row <name> has tier <tier>
          Then looked up user <name> has tier <tier>

          Examples: | table: users.csv |
      """
    And consumer file "features/inline-users.feature" contains:
      """gherkin
      Feature: Inline users
        Background:
          Given the lookup service is ready

        Scenario Outline: Look up a user from the inline table
          Given user row <name> has tier <tier>
          Then looked up user <name> has tier <tier>

          Examples:
            | name  | tier   |
            | Ada   | gold   |
            | Grace | silver |
      """
    And consumer file "features/markdown-users.tab" contains UTF-8 BOM and CRLF:
      """tsv
      name	tier
      Tina	bronze
      Maja	copper
      """
    And consumer file "features/markdown-users.feature.md" contains:
      """markdown
      # Feature: External Markdown users
      ## Scenario Outline: Look up a Markdown user
          * Given the lookup service is ready
        * Given user row <name> has tier <tier>
        * Then looked up user <name> has tier <tier>
      ### Examples:
          | table: markdown-users.tab |
      """
    And consumer file "features/report-users.csv" contains:
      """csv
      name,expected
      passed,passed
      failed,expected-other
      """
    And consumer file "features/reported-users.feature" contains:
      """gherkin
      Feature: External rows in reports
        Background:
          Given the report session is open

        Scenario Outline: Report a row outcome
          Given the report row is <name>
          Then the report row result is <expected>

          Examples: <table:report-users.csv>
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-json=report.json --cuke-messages-ndjson=messages.ndjson --cuke-progress"
    Then pytest should exit with a non-zero code
    And consumer reports should preserve external row identities, source URIs, Background steps, and outcomes

    When consumer file "test_explicit_binding.py" contains:
      """python
      from pytest_cuke import scenario


      @scenario("users.feature")
      def test_explicit_users_binding():
          pass
      """
    And I run installed pytest with arguments "--rootdir=. --cuke-no-autoload"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios

    When consumer file "features/users.csv" contains:
      """csv
      name,tier
      Lin,platinum
      """
    And I run installed pytest with arguments "--rootdir=. --cuke-no-autoload"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: External CSV special values survive public step substitution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, parsers, then


      @given(parsers.re(r"payload is ?(?P<payload>(?s:.*))"), target_fixture="actual_payload")
      def capture_payload(payload):
          return payload


      @then(parsers.re(r"payload should equal ?(?P<expected>(?s:.*))"))
      def check_payload(actual_payload, expected):
          assert actual_payload == expected
      """
    And consumer file "features/special-values.csv" contains:
      """csv
      value,expected
      ,
      "comma, quote ""value""","comma, quote ""value"""
      "pipe | and back\slash","pipe | and back\slash"
      "first line
      second line","first line
      second line"
      """
    And consumer file "features/special-values.feature" contains:
      """gherkin
      Feature: External CSV special values
        Scenario Outline: Compare an external value
          Given payload is <value>
          Then payload should equal <expected>

          Examples: table: special-values.csv
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload"
    Then pytest should exit with code 0
    And the test outcome should have 4 passed scenarios

  Scenario: Invalid external CSV fails autoload collection with source diagnostics
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/broken.csv" contains:
      """csv
      name,tier
      Ada
      """
    And consumer empty file "features/empty.csv" exists
    And consumer file "features/blank-header.csv" contains:
      """csv
      name, ,tier
      Ada,gold
      """
    And consumer file "features/invalid-encoding.csv" contains invalid UTF-8
    And consumer directory "features/unreadable.csv" exists
    And consumer file "features/broken.feature" contains:
      """gherkin
      Feature: Invalid external examples
        Scenario Outline: Read an invalid source
          Given user row <name> has tier <tier>

          Examples: table: broken.csv
      """
    And consumer file "features/missing.feature" contains:
      """gherkin
      Feature: Missing external examples
        Scenario Outline: Read a missing source
          Given user row <name> has tier <tier>

          Examples: table: missing.csv
      """
    And consumer file "features/empty.feature" contains:
      """gherkin
      Feature: Empty external examples
        Scenario Outline: Read an empty source
          Given user row <name> has tier <tier>

          Examples: table: empty.csv
      """
    And consumer file "features/blank-header.feature" contains:
      """gherkin
      Feature: Blank header in external examples
        Scenario Outline: Read a source with a blank header
          Given user row <name> has tier <tier>

          Examples: table: blank-header.csv
      """
    And consumer file "features/invalid-encoding.feature" contains:
      """gherkin
      Feature: Invalid encoding in external examples
        Scenario Outline: Read a source with invalid UTF-8
          Given user row <name> has tier <tier>

          Examples: table: invalid-encoding.csv
      """
    And consumer file "features/unreadable.feature" contains:
      """gherkin
      Feature: Unreadable external examples
        Scenario Outline: Read an unreadable source
          Given user row <name> has tier <tier>

          Examples: table: unreadable.csv
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload"
    Then pytest should exit with a non-zero code
    And pytest output should identify the invalid external Examples source

  Scenario: Legacy pytest-bdd imports and option spellings are rejected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "test_legacy_import.py" contains:
      """python
      import importlib.util


      def test_legacy_package_is_not_installed():
          assert importlib.util.find_spec("pytest_bdd") is None
      """
    When I run installed pytest with arguments "--rootdir=. --help"
    Then pytest should exit with code 0
    And pytest help should not mention the legacy option "cucumber-json"
    And pytest help should not mention the legacy option "cucumber-html"
    And pytest help should not mention the legacy option "messages-ndjson"
    And pytest help should not mention the legacy option "disable-feature-autoload"
    And pytest help should not mention the legacy option "liberal-steps"
    And pytest help should not mention the legacy option "gherkin-terminal-reporter"
    And pytest help should not mention the legacy option "generate"
    And pytest help should not mention the legacy option "generate-missing"
    And pytest help should not mention the legacy option "feature"
    When I run installed pytest with arguments "--rootdir=. test_legacy_import.py -q"
    Then pytest should exit with code 0

  Scenario Outline: Both installed command names report the package version
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run command "<command>" with arguments "--version"
    Then the command should exit with code 0
    And the command output should identify the installed pytest-cuke version

    Examples:
      | command     |
      | pytest-cuke |
      | cuke        |

  Scenario: Standalone dispatchers expose validation and generation options
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run command "cuke" with arguments "--help"
    Then the command should exit with code 0
    And the command output should list the public subcommands
    When I run command "pytest-cuke" with arguments "--help"
    Then the command should exit with code 0
    And the command output should list the public subcommands
    When I run command "cuke" with arguments "validate --help"
    Then the command should exit with code 0
    And the command help should show the required feature-directory argument
    When I run command "cuke" with arguments "validate"
    Then the command should exit with a non-zero code
    And the command output should require a feature directory
    When I run command "cuke" with arguments "validate consumer-features"
    Then the command should exit with a non-zero code
    And the command output should contain "invalid feature root"
    When I run command "cuke" with arguments "generate steps --help"
    Then the command should exit with code 0
    And the command output should contain "--feature"
    And the command output should contain "--target"
    When I run command "cuke" with arguments "generate steps"
    Then the command should exit with a non-zero code
    And the command output should contain "--feature"
    When I run command "cuke" with arguments "convert allure missing.ndjson"
    Then the command should exit with a non-zero code
    And the command output should contain "cannot read input"

  Scenario: Heading validation scans parsed Gherkin and reports stable baseline data
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    # The consumer file step expands this marker to three spaces.
    And consumer file "features/empty.feature" has content:
      ```
      Feature: {WHITESPACE_TITLE}
        # Scenario: this comment is not a heading
        Background:
          Given a background step
        Scenario: {WHITESPACE_TITLE}
          Given a note:
            """
            Feature:
            Scenario:
            """
      Scenario: Quoted words in step text are not headings
        Given a quoted example contains "Feature:" and "Scenario:"
      ```
    And consumer file "features/nested.gherkin" has content:
      """
      Feature: Outline aliases and nested rules
        Rule:
          Scenario Template:
            Given a value <value>
            Examples:
              | value |
              | ready |
      """
    And consumer file "features/markdown.feature.md" has content:
      """
      # Feature:
      ## Scenario: Unicode café
      * Given this step is only parsed

      ```gherkin
      Feature:
        Scenario:
          Given fenced text must not be parsed
      ```
      """
    And consumer file "features/markdown.gherkin.md" has content:
      """
      # Feature: Valid markdown Gherkin
      ## Scenario:
      * Given this step is only parsed
      """
    When I run command "cuke" with arguments "validate features --include-pattern **/*.feature --include-pattern **/*.feature --include-pattern **/*.gherkin --include-pattern **/*.feature.md --include-pattern **/*.gherkin.md --json"
    Then the command should exit with a non-zero code
    And the command JSON should include:
      """
      {
        "documents_scanned": 4,
        "status": "fail",
        "violations": [
          {"path": "empty.feature", "line": 1, "heading_type": "feature", "code": "EMPTY_HEADING_TITLE", "raw_name": ""},
          {"path": "empty.feature", "line": 5, "heading_type": "scenario", "code": "EMPTY_HEADING_TITLE", "raw_name": ""},
          {"path": "markdown.feature.md", "line": 1, "heading_type": "feature", "code": "EMPTY_HEADING_TITLE", "raw_name": ""},
          {"path": "markdown.gherkin.md", "line": 2, "heading_type": "scenario", "code": "EMPTY_HEADING_TITLE", "raw_name": ""},
          {"path": "nested.gherkin", "line": 3, "heading_type": "scenario_outline", "code": "EMPTY_HEADING_TITLE", "raw_name": ""}
        ]
      }
      """
    And the regular heading scan findings are stored
    When I run command "cuke" with arguments "validate features --include-pattern **/*.feature --include-pattern **/*.feature --include-pattern **/*.gherkin --include-pattern **/*.feature.md --include-pattern **/*.gherkin.md --json --no-fail-on-violation"
    Then the command should exit with code 0
    And the advisory heading scan should preserve the regular findings
    When I run command "cuke" with arguments "validate features --include-pattern **/*.feature --include-pattern **/*.feature --include-pattern **/*.gherkin --include-pattern **/*.feature.md --include-pattern **/*.gherkin.md --json --baseline-audit"
    Then the command should exit with a non-zero code
    And the command JSON should include:
      """
      {
        "policy_id": "feature-heading-policy-v1",
        "violations_count": 5,
        "compliant": false
      }
      """
    And the baseline audit should preserve identity fields
    When I run command "cuke" with arguments "validate features --policy --json"
    Then the command should exit with code 0
    And the command JSON should include:
      """
      {
        "policy_id": "feature-heading-policy-v1",
        "enforced_heading_types": ["feature", "scenario", "scenario_outline"],
        "trim_whitespace": true,
        "empty_name_is_violation": true,
        "snippet_text_excluded": true
      }
      """
    Given consumer file "compliant/valid.feature" has content:
      """
      Feature: Checked baseline
        Scenario: A useful title
      """
    When I run command "cuke" with arguments "validate compliant --baseline-audit --json"
    Then the command should exit with code 0
    And the command JSON should include:
      """
      {
        "policy_id": "feature-heading-policy-v1",
        "violations_count": 0,
        "compliant": true
      }
      """
    And the baseline audit should preserve identity fields

  Scenario: Heading validation distinguishes invalid roots and syntax errors from empty discovery
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run command "cuke" with arguments "validate missing-features --json"
    Then the command should exit with a non-zero code
    And the command output should contain "invalid feature root"
    Given consumer directory "empty-discovery" exists
    When I run command "cuke" with arguments "validate empty-discovery --include-pattern **/*.feature --json"
    Then the command should exit with code 0
    And the command JSON should include:
      """
      {"documents_scanned": 0, "violations": [], "status": "pass"}
      """
    Given consumer file "features/broken.feature" has content:
      """
      Feature: Broken
        Scenario: broken syntax
          Given a step
          Invalid syntax without keyword
      """
    When I run command "cuke" with arguments "validate features --json"
    Then the command should exit with a non-zero code
    And the command output should contain "parse error"
    And the command output should contain "features/broken.feature"
    Given consumer file "io-error/invalid.feature" has invalid UTF-8 content
    When I run command "cuke" with arguments "validate io-error --json"
    Then the command should exit with a non-zero code
    And the command output should contain "io_error"
    And the command output should contain "io-error/invalid.feature"

  Scenario: Strict autoload rejects an empty parsed heading before a step can run
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/strict.feature" has content:
      """
      Feature: Strict title validation
        Scenario:
          Given record that the feature step ran
      """
    And consumer file "conftest.py" has content:
      """
      from pathlib import Path

      from pytest_cuke import given

      @given("record that the feature step ran")
      def record_feature_step():
          Path("step-ran.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=features --cuke-autoload --cuke-strict"
    Then pytest should exit with a non-zero code
    And pytest output should contain "EMPTY_HEADING_TITLE"
    And pytest output should contain "strict.feature:2"
    And the consumer file "step-ran.txt" should not exist

  Scenario: Non-strict autoload keeps heading policy opt-in
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/non-strict.feature" has content:
      """
      Feature: Non-strict title validation
        Scenario:
          Given record that the feature step ran
      """
    And consumer file "conftest.py" has content:
      """
      from pathlib import Path

      from pytest_cuke import given

      @given("record that the feature step ran")
      def record_feature_step():
          Path("step-ran.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=features --cuke-autoload"
    Then pytest should exit with code 0
    And the consumer file "step-ran.txt" should exist
