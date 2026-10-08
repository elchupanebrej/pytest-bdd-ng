Feature: Transactional generation of step definitions
  A consumer can generate only missing bindings without losing the step module it already owns.

  Scenario: Existing aliases and parser bindings are retained while only missing steps are generated
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has aliased parser bindings and two generation features
    When I run command "cuke" with arguments "generate steps --feature features/existing-bindings.feature --feature features/missing-hook.feature --target steps.py"
    Then the command should exit with code 0
    And the generated module should retain its existing aliases, parser binding, and user code
    And default generation should not create scenario wrapper files

  Scenario: Explicit scenario binding is added only when requested
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has an existing test module for explicit scenario binding
    When I run command "cuke" with arguments "generate steps --feature features/explicit-bindings.feature --target test_explicit_scenario.py --bind-scenarios"
    Then the command should exit with code 0
    And the chosen module should retain its user code and bind the selected scenario
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload test_explicit_scenario.py --color=no"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: An aliased existing scenario resolves relative to the configured feature directory
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has an aliased scenario binding that uses the configured feature directory
    And I remember the exact bytes of consumer file "test_aliased_scenario.py"
    When I run command "cuke" with arguments "generate steps --feature features/explicit-bindings.feature --target test_aliased_scenario.py --bind-scenarios"
    Then the command should exit with code 0
    And the existing aliased scenario binding should not be duplicated
    And consumer file "test_aliased_scenario.py" should match its remembered bytes
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload test_aliased_scenario.py --color=no"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: Relative scenario binding is reused without pytest configuration
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has no pytest configuration and an aliased relative scenario binding
    And I remember the exact bytes of consumer file "tests/test_bindings.py"
    When I run command "cuke" with arguments "generate steps --feature features/relative.feature --target tests/test_bindings.py --bind-scenarios"
    Then the command should exit with code 0
    And the existing relative scenario binding should not be duplicated
    And consumer file "tests/test_bindings.py" should match its remembered bytes

  Scenario: An existing absolute scenarios glob is not duplicated
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has an absolute scenarios glob binding for a generation feature
    And I remember the exact bytes of consumer file "steps.py"
    When I run command "cuke" with arguments "generate steps --feature features/absolute-glob.feature --target steps.py --bind-scenarios"
    Then the command should exit with code 0
    And the existing absolute scenarios glob binding should not be duplicated
    And consumer file "steps.py" should match its remembered bytes

  Scenario: A shallow scenarios glob does not cover a feature two directories deep
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has a shallow scenarios glob and a nested generation feature
    When I run command "cuke" with arguments "generate steps --feature features/area/nested/nested-scenario.feature --target steps.py --bind-scenarios"
    Then the command should exit with code 0
    And the nested feature should have an explicit generated scenario binding

  Scenario: Repeating a generation update leaves the module byte-identical
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has aliased parser bindings and two generation features
    When I run command "cuke" with arguments "generate steps --feature features/existing-bindings.feature --feature features/missing-hook.feature --target steps.py"
    Then the command should exit with code 0
    And I remember the exact bytes of consumer file "steps.py"
    When I run command "cuke" with arguments "generate steps --feature features/existing-bindings.feature --feature features/missing-hook.feature --target steps.py"
    Then the command should exit with code 0
    And consumer file "steps.py" should match its remembered bytes

  Scenario: Preview and print-only generation leave the target module unchanged
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has aliased parser bindings and two generation features
    And I remember the exact bytes of consumer file "steps.py"
    When I run command "cuke" with arguments "generate steps --feature features/existing-bindings.feature --feature features/missing-hook.feature --target steps.py --preview"
    Then the command should exit with code 0
    And the generator output should include the missing hook
    And the preview output should include the diff without pytest collection output
    And consumer file "steps.py" should match its remembered bytes
    When I run command "cuke" with arguments "generate steps --feature features/existing-bindings.feature --feature features/missing-hook.feature"
    Then the command should exit with code 0
    And the generator output should include the missing hook
    And consumer file "steps.py" should match its remembered bytes

  Scenario: A missing feature source leaves the target module byte-identical
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has a generation target and one valid feature
    And I remember the exact bytes of consumer file "steps.py"
    When I run command "cuke" with arguments "generate steps --feature features/missing.feature --target steps.py"
    Then the command should exit with a non-zero code
    And the generator error should identify "features/missing.feature"
    And consumer file "steps.py" should match its remembered bytes

  Scenario: An invalid target module is diagnosed without changing its bytes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has an invalid generation target and one valid feature
    And I remember the exact bytes of consumer file "steps.py"
    When I run command "cuke" with arguments "generate steps --feature features/valid.feature --target steps.py"
    Then the command should exit with a non-zero code
    And the generator error should identify the invalid target "steps.py"
    And consumer file "steps.py" should match its remembered bytes

  Scenario: A missing target path is reported and never created
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has a generation feature but no target module
    When I run command "cuke" with arguments "generate steps --feature features/missing-target.feature --target generated-steps.py"
    Then the command should exit with a non-zero code
    And the generator error should identify "generated-steps.py"
    And the consumer file "generated-steps.py" should not exist

  Scenario: Ambiguous existing step definitions fail with a remedy and preserve the target
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has two ambiguous bindings for one generation feature
    And I remember the exact bytes of consumer file "steps.py"
    When I run command "cuke" with arguments "generate steps --feature features/ambiguous-bindings.feature --target steps.py"
    Then the command should exit with a non-zero code
    And the generator should provide an actionable ambiguity error
    And consumer file "steps.py" should match its remembered bytes

  Scenario: A fixture setup failure during discovery returns non-zero and runs its finalizer
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has an autouse fixture that fails during generation inspection
    And I remember the exact bytes of consumer file "steps.py"
    When I run command "cuke" with arguments "generate steps --feature features/fixture-failure.feature --target steps.py"
    Then the command should exit with a non-zero code
    And the fixture setup failure should be reported and its cleanup finalizer should run
    And consumer file "steps.py" should match its remembered bytes

  Scenario: Formatter failure rolls back by default and keeps the attempted edit when requested
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has a generation target and one valid feature
    And the consumer PATH contains a formatter that fails
    And I remember the exact bytes of consumer file "steps.py"
    When I run command "cuke" with arguments "generate steps --feature features/valid.feature --target steps.py"
    Then the command should exit with a non-zero code
    And consumer file "steps.py" should match its remembered bytes
    When I run command "cuke" with arguments "generate steps --feature features/valid.feature --target steps.py --keep-on-error"
    Then the command should exit with a non-zero code
    And the target should retain the attempted generated definition after formatter failure

  Scenario: Escaped step text compiles, collects, and executes once after the stub is filled
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the consumer has aliased parser bindings and a multiline literal feature
    When I run command "cuke" with arguments "generate steps --feature features/existing-bindings.feature --feature features/missing-hook.feature --feature features/literal-generation.feature --target steps.py"
    Then the command should exit with code 0
    And the generated module should compile and preserve the exact escaped step text
    When I fill the generated step stubs to record their executions
    And I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --color=no"
    Then pytest should exit with code 0
    And the test outcome should have 3 passed scenarios
    And the generated literal step should have executed once with its original multiline payload
