Feature: Invocation-level feature source selection
  A pytest invocation can select local and remote feature roots, while command-line
  settings override configuration and explicit bindings keep their own source.

  Scenario: The command line selects a local feature root from a different working directory
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer directory "tools" exists
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the selected invocation feature root is executing")
      def selected_invocation_feature_root_is_executing():
          pass


      @given("the default feature root must not execute")
      def default_feature_root_must_not_execute():
          raise AssertionError("pytest ignored --cuke-features-dir")
      """
    And consumer file "features/default.feature" contains:
      """gherkin
      Feature: Default feature root
        Scenario: The default root is not selected
          Given the default feature root must not execute
      """
    And consumer file "selected-features/invocation.feature" contains:
      """gherkin
      Feature: Invocation feature root
        Scenario: The selected invocation feature root is executing
          Given the selected invocation feature root is executing
      """
    When I run installed pytest from consumer directory "tools" with arguments "--rootdir='{consumer_path}' '{consumer_path}' --cuke-autoload --cuke-parser=python --cuke-features-dir=selected-features --cuke-json=../invocation-source.json --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer artifact "invocation-source.json" should report feature URI "invocation.feature"

  Scenario: The command line overrides INI and an explicit binding keeps its own feature directory
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "ini-features"
      cuke_autoload = true
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the command-line feature root is selected")
      def command_line_feature_root_is_selected():
          pass


      @given("the explicit binding feature root is selected")
      def explicit_binding_feature_root_is_selected():
          pass


      @given("the INI feature root must not execute")
      def ini_feature_root_must_not_execute():
          raise AssertionError("pytest ignored --cuke-features-dir")
      """
    And consumer file "ini-features/ini.feature" contains:
      """gherkin
      Feature: INI feature root
        Scenario: The INI feature root is overridden
          Given the INI feature root must not execute
      """
    And consumer file "cli-features/cli.feature" contains:
      """gherkin
      Feature: Command-line feature root
        Scenario: The command-line feature root is selected
          Given the command-line feature root is selected
      """
    And consumer file "binding-features/binding.feature" contains:
      """gherkin
      Feature: Explicit binding feature root
        Scenario: The explicit binding feature root is selected
          Given the explicit binding feature root is selected
      """
    And consumer file "test_explicit_source.py" contains:
      """python
      from pytest_cuke import scenarios


      test_explicit_source = scenarios("binding.feature", features_base_dir="binding-features")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=cli-features --cuke-parser=python --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios

  Scenario Outline: A relative URL uses the configured prefix with or without a trailing slash
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the local HTTP fixture serves feature endpoint "/catalog/items.feature":
      """gherkin
      Feature: Relative HTTP feature
        Scenario: The URL base resolves the relative feature
          Given the relative HTTP feature was loaded
      """
    And the local HTTP fixture serves feature endpoint "/absolute.feature":
      """gherkin
      Feature: Absolute HTTP feature
        Scenario: An absolute URL bypasses the configured base prefix
          Given the absolute HTTP feature was loaded
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the relative HTTP feature was loaded")
      def relative_http_feature_was_loaded():
          pass


      @given("the absolute HTTP feature was loaded")
      def absolute_http_feature_was_loaded():
          pass
      """
    And consumer file "test_http_sources.py" contains:
      """python
      import os

      from pytest_cuke import scenarios
      from pytest_cuke.scenario import FeaturePathType


      http_base = os.environ["PYTEST_CUKE_TEST_HTTP_BASE_URL"]
      test_relative_http_feature = scenarios("items.feature", features_path_type=FeaturePathType.URL)
      test_absolute_http_feature = scenarios(
          f"{http_base}/absolute.feature",
          features_path_type=FeaturePathType.URL,
      )
      """
    When I run installed pytest with the local HTTP fixture URL base and arguments "--rootdir=. --cuke-no-autoload --cuke-features-base-url={local_http_base_url}<base_path> --cuke-parser=python --cuke-summary -q test_http_sources.py"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios

    Examples:
      | base_path  |
      | /catalog   |
      | /catalog/  |

  Scenario: A missing local feature root reports the selected path
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=missing-features"
    Then pytest should exit with a non-zero code
    And pytest output should include "missing-features"
    And pytest output should include "does not exist"

  Scenario: A malformed URL base produces a configuration diagnostic
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "test_url_binding.py" contains:
      """python
      from pytest_cuke import scenarios
      from pytest_cuke.scenario import FeaturePathType


      test_malformed_url_binding = scenarios("relative.feature", features_path_type=FeaturePathType.URL)
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-features-base-url=not-a-url --cuke-parser=python -q test_url_binding.py"
    Then pytest should exit with a non-zero code
    And pytest output should include "cuke_features_base_url"
    And pytest output should include "absolute HTTP(S)"

  Scenario: A relative URL binding without a URL base reports the required setting
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "test_url_without_base.py" contains:
      """python
      from pytest_cuke import scenarios
      from pytest_cuke.scenario import FeaturePathType


      test_url_without_base = scenarios("relative.feature", features_path_type=FeaturePathType.URL)
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python -q test_url_without_base.py"
    Then pytest should exit with a non-zero code
    And pytest output should include "--cuke-features-base-url"
    And pytest output should include "cuke_features_base_url"

  Scenario: An HTTP failure reports the selected source URL
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the local HTTP fixture returns status 404 for feature endpoint "/catalog/missing.feature"
    And consumer file "test_http_failure.py" contains:
      """python
      from pytest_cuke import scenarios
      from pytest_cuke.scenario import FeaturePathType


      test_missing_http_feature = scenarios("missing.feature", features_path_type=FeaturePathType.URL)
      """
    When I run installed pytest with the local HTTP fixture URL base and arguments "--rootdir=. --cuke-no-autoload --cuke-features-base-url={local_http_base_url}/catalog --cuke-parser=python -q test_http_failure.py"
    Then pytest should exit with a non-zero code
    And pytest output should identify the local HTTP source URL "/catalog/missing.feature"

  Scenario: A feature parse failure reports the source URL
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the local HTTP fixture serves feature endpoint "/catalog/broken.feature":
      """gherkin
      Feature: Broken HTTP feature
        Scenario: The malformed feature cannot be parsed
          Given an unfinished step
          Then
      """
    And consumer file "test_http_parse_failure.py" contains:
      """python
      from pytest_cuke import scenarios
      from pytest_cuke.scenario import FeaturePathType


      test_broken_http_feature = scenarios("broken.feature", features_path_type=FeaturePathType.URL)
      """
    When I run installed pytest with the local HTTP fixture URL base and arguments "--rootdir=. --cuke-no-autoload --cuke-features-base-url={local_http_base_url}/catalog --cuke-parser=python -q test_http_parse_failure.py"
    Then pytest should exit with a non-zero code
    And pytest output should identify the local HTTP source URL "/catalog/broken.feature"

  Scenario: An explicit URL path binding uses HTTP when a local feature root is configured
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the local HTTP fixture serves feature endpoint "/catalog/shared.feature":
      """gherkin
      Feature: URL-selected duplicate feature
        Scenario: The explicit URL path type selects the HTTP source
          Given the HTTP feature with a shared name was selected
      """
    And consumer file "features/shared.feature" contains:
      """gherkin
      Feature: Locally selected duplicate feature
        Scenario: The local duplicate must not be selected
          Given the local feature with a shared name must not be selected
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the HTTP feature with a shared name was selected")
      def http_feature_with_shared_name_was_selected():
          pass


      @given("the local feature with a shared name must not be selected")
      def local_feature_with_shared_name_must_not_be_selected():
          raise AssertionError("the relative URL binding selected the local feature root")
      """
    And consumer file "test_explicit_url_source.py" contains:
      """python
      from pytest_cuke import scenarios
      from pytest_cuke.scenario import FeaturePathType


      test_explicit_url_source = scenarios("shared.feature", features_path_type=FeaturePathType.URL)
      """
    When I run installed pytest with the local HTTP fixture URL base and arguments "--rootdir=. --cuke-no-autoload --cuke-features-dir=features --cuke-features-base-url={local_http_base_url}/catalog --cuke-parser=python --cuke-summary -q test_explicit_url_source.py"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: An explicit binding rejects simultaneous local and URL base settings
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "test_conflicting_source_bases.py" contains:
      """python
      from pytest_cuke import scenarios


      conflicting_sources = scenarios(
          "feature.feature",
          features_base_dir="features",
          features_base_url="http://127.0.0.1:9/features",
      )
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python -q test_conflicting_source_bases.py"
    Then pytest should exit with a non-zero code
    And pytest output should explain conflicting per-binding feature sources

  Scenario: Independent pytest sessions use their own selected local feature roots
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the first local feature root is selected")
      def first_local_feature_root_is_selected(pytestconfig):
          selected_root = pytestconfig.getoption("cuke_features_dir")
          assert selected_root.rstrip("/").endswith("first-features")


      @given("the second local feature root is selected")
      def second_local_feature_root_is_selected(pytestconfig):
          selected_root = pytestconfig.getoption("cuke_features_dir")
          assert selected_root.rstrip("/").endswith("second-features")
      """
    And consumer file "test_same_relative_feature.py" contains:
      """python
      from pytest_cuke import scenarios


      test_selected_local_feature = scenarios("selected/shared.feature")
      """
    And consumer file "first-features/selected/shared.feature" contains:
      """gherkin
      Feature: First local feature root
        Scenario: The first local root is selected
          Given the first local feature root is selected
      """
    And consumer file "second-features/selected/shared.feature" contains:
      """gherkin
      Feature: Second local feature root
        Scenario: The second local root is selected
          Given the second local feature root is selected
      """
    When I run installed pytest in two independent sessions with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-features-dir=first-features --cuke-summary -vv test_same_relative_feature.py" and then "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-features-dir=second-features --cuke-summary -vv test_same_relative_feature.py"
    Then both independent pytest sessions should execute exactly one selected root scenario

  Scenario: Independent pytest sessions keep distinct URL base settings
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the local HTTP fixture serves feature endpoint "/first/shared.feature":
      """gherkin
      Feature: First URL base
        Scenario: The first URL base is selected
          Given the first URL base source was selected
      """
    And the local HTTP fixture serves feature endpoint "/second/shared.feature":
      """gherkin
      Feature: Second URL base
        Scenario: The second URL base is selected
          Given the second URL base source was selected
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the first URL base source was selected")
      def first_url_base_source_was_selected(pytestconfig):
          base_url = pytestconfig.getoption("cuke_features_base_url")
          assert base_url.rstrip("/").endswith("/first")


      @given("the second URL base source was selected")
      def second_url_base_source_was_selected(pytestconfig):
          base_url = pytestconfig.getoption("cuke_features_base_url")
          assert base_url.rstrip("/").endswith("/second")
      """
    And consumer file "test_shared_url_source.py" contains:
      """python
      from pytest_cuke import scenarios
      from pytest_cuke.scenario import FeaturePathType


      test_shared_url_source = scenarios("shared.feature", features_path_type=FeaturePathType.URL)
      """
    When I run installed pytest in two independent URL-base sessions with the local HTTP fixture and arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-features-base-url={local_http_base_url}/first --cuke-summary -q test_shared_url_source.py" and then "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-features-base-url={local_http_base_url}/second --cuke-summary -q test_shared_url_source.py"
    Then both independent URL-base sessions should execute only their selected URL source
