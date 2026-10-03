Feature: Historical custom feature parsers use an explicit adapter
  Parser extensions can retain their implemented legacy parsing behavior while
  pytest-cuke converts their result into the immutable native domain.

  Scenario: An installed extension parses its legacy feature during autoload
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has the runnable custom parser example
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-json=legacy-report.json --cuke-summary --color=no"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And the installed custom parser example should preserve its invocation inputs, source, and report identity

  Scenario: Explicit-file, directory, and autoload collection use the same legacy adapter
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has the runnable custom parser example
    When I compare custom parser collection through explicit file, directory, and autoload selection
    Then all three custom parser collection runs should pass the same scenario once
    And all three custom parser reports should identify the same normalized source

  Scenario: A legacy parser receives a custom encoding and normalized Unicode file path
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has the runnable custom parser example
    And consumer file "features/café.feature" contains text encoded as "latin-1":
      """gherkin
      Feature: Café with a legacy parser
        Scenario: Decode the feature source
      """
    And consumer file "test_legacy_encoding.py" contains:
      """python
      from pathlib import Path

      from parser_plugin import LEGACY_MIMETYPE
      from pytest_cuke import scenario


      @scenario(
          "café.feature",
          encoding="latin-1",
          features_base_dir="features",
          features_mimetype=LEGACY_MIMETYPE,
      )
      def test_legacy_parser_decodes_custom_encoding(feature):
          source = Path("features/café.feature")
          assert feature.name == "Café with a legacy parser"
          assert feature.source_content == source.read_text(encoding="latin-1")
          assert Path(feature.filename).resolve() == source.resolve()
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload test_legacy_encoding.py --cuke-summary --color=no"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And the custom encoding invocation should preserve the Unicode source path and URI

  Scenario: A missing optional codec does not prevent native Gherkin collection
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has a native Gherkin feature and a custom parser with an absent optional codec
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary --continue-on-collection-errors -vv --color=no"
    Then pytest should exit with a non-zero code
    And the native Gherkin scenario should pass while the optional codec error is actionable

  Scenario: Two pytest configs keep custom parser instances isolated in one process
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has the runnable custom parser example
    And the consumer has two independent pytest configs using the same legacy parser provider
    When I run both custom parser sessions in one consumer process
    Then each pytest config should receive its own legacy parser instance and registration

  Scenario: A malformed legacy result fails collection with parser and source guidance
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has the runnable custom parser example
    And the legacy parser is configured to return a malformed result
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary --continue-on-collection-errors -vv --color=no"
    Then pytest should exit with a non-zero code
    And the legacy parser collection error should name the parser, source, and adapter remedy

  Scenario: An internal TypeError raised by a legacy parser remains its original failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer has the runnable custom parser example
    And the legacy parser is configured to raise an internal TypeError
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary --continue-on-collection-errors -vv --color=no"
    Then pytest should exit with a non-zero code
    And the original legacy parser TypeError should be preserved
