Feature: Installed compatibility matrix and migration audit
  A project can inspect its configured runtime matrix and measure feature migration
  through the canonical installed command without importing its test suite.

  Scenario: The configured matrix is JSON and the compatible filter removes excluded pairs
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has a compatibility matrix spanning supported and excluded pairs
    When I run command "cuke" with arguments "compatibility --list --json"
    Then the command should exit with code 0
    And the compatibility matrix JSON should include each configured factor pairing
    When I run command "pytest-cuke" with arguments "compatibility --list --json"
    Then the command should exit with code 0
    And the compatibility matrix JSON should include each configured factor pairing
    When I run command "cuke" with arguments "compatibility --compatible-only --json"
    Then the command should exit with code 0
    And the compatible-only matrix should contain no incompatible entries

  Scenario: A direct compatibility check distinguishes supported unsupported EOL and unavailable pairs
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    When I run command "cuke" with arguments "compatibility --python 3.14 --pytest latest --json"
    Then the command should exit with code 0
    And the compatibility pair should be compatible with reason "compatible"
    When I run command "cuke" with arguments "compatibility --python 3.9 --pytest 8.0 --json"
    Then the command should exit with a non-zero code
    And the compatibility pair should be compatible with reason "eol_python"
    And the compatibility pair should be unsupported by the project
    When I run command "cuke" with arguments "compatibility --python 3.10 --pytest 6.2 --json"
    Then the command should exit with a non-zero code
    And the compatibility pair should be incompatible with reason "eol_pytest"
    When I run command "cuke" with arguments "compatibility --python 3.14 --pytest 8.0 --json"
    Then the command should exit with a non-zero code
    And the compatibility pair should be incompatible with reason "python_not_supported_by_pytest"
    And the compatibility pair should be supported by the project
    When I run command "cuke" with arguments "compatibility --python 3.10 --pytest unknown --json"
    Then the command should exit with a non-zero code
    And the compatibility pair should be incompatible with reason "pytest_unavailable"
    When I run command "cuke" with arguments "compatibility --python unknown --pytest 8.0 --json"
    Then the command should exit with a non-zero code
    And the compatibility pair should be incompatible with reason "python_unavailable"

  Scenario: Tox expansion is deterministic and explicit INI and TOML inputs work outside the project directory
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has active TOML and alternate INI and TOML compatibility configurations
    When I run cuke compatibility tox expansion twice in the consumer project
    Then the tox expansion should be deterministic and include all supported factor combinations
    When I run cuke compatibility from outside the consumer with config "alternate.ini" and arguments "--expand-tox --json"
    Then the command should exit with code 0
    And the command JSON should include:
      """
      {"toxEnvNames": ["py312-pytest90-lin", "py312-pytest90-win"]}
      """
    When I run cuke compatibility from outside the consumer with config "alternate.toml" and arguments "--expand-tox --json"
    Then the command should exit with code 0
    And the command JSON should include:
      """
      {"toxEnvNames": ["py314-pytestlatest-mac"]}
      """
    And consumer file "malformed.toml" contains:
      """
      [tool.pytest-cuke.compatibility
      python-factors = ["3.10"]
      """
    When I run cuke compatibility from outside the consumer with config "malformed.toml" and arguments "--list --json"
    Then the command should exit with code 2
    And compatibility stderr should contain "invalid TOML configuration"
    And command diagnostics should be stderr-only

  Scenario: The active project audit counts autoload features without requiring wrapper files
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has a migration audit with one registration and one autoload-only feature scenario
    When I run command "cuke" with arguments "compatibility --audit-migration --json"
    Then the command should exit with code 0
    And the migration audit should report the configured identities and threshold
    And the autoload-only scenario should not require a mirror wrapper file

  Scenario: The migration audit follows a non-default active autoload feature root
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer uses a non-default autoload feature root for migration audit
    When I run command "cuke" with arguments "compatibility --audit-migration --json"
    Then the command should exit with code 0
    And the migration audit should count the active autoload feature without a wrapper

  Scenario: A non-string migration feature pattern is rejected cleanly in JSON mode
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has a non-string migration feature pattern
    When I run command "cuke" with arguments "compatibility --audit-migration --json"
    Then the command should exit with code 2
    And compatibility stderr should contain "feature-patterns entries must be strings"
    And command diagnostics should be stderr-only

  Scenario: An empty migration inventory is a valid complete audit
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has an empty migration audit inventory
    When I run command "cuke" with arguments "compatibility --audit-migration --json"
    Then the command should exit with code 0
    And the migration audit should report an empty inventory as complete
    When I run command "cuke" with arguments "compatibility --audit-migration --threshold-percent 101 --json"
    Then the command should exit with code 2
    And compatibility stderr should contain "threshold must be an integer from 0 to 100"
    And command diagnostics should be stderr-only
    When I run command "cuke" with arguments "compatibility --audit-migration --features-root missing-features --json"
    Then the command should exit with code 2
    And compatibility stderr should contain "invalid features root"
    And command diagnostics should be stderr-only

  Scenario: Duplicate normalized scenario registrations fail even when coverage meets its threshold
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has duplicate normalized migration scenario registrations
    When I run command "cuke" with arguments "compatibility --audit-migration --json"
    Then the command should exit with a non-zero code
    And the migration audit should report duplicate scenario registrations

  Scenario: One unmatched registration puts migration coverage below the configured threshold
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has one feature scenario and one unmatched registration with an eighty percent threshold
    When I run command "cuke" with arguments "compatibility --audit-migration --json"
    Then the command should exit with a non-zero code
    And the migration audit should report fifty percent coverage below threshold
