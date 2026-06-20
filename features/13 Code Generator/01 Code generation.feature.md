# Feature: Code generation
  Verify that code generation can gather missing artifacts, author target files, print scaffolds, and cooperate with runtime step policies.

## Scenario: Gather missing artifacts as NDJSON
* Given File "generation.feature" with content:

    ```gherkin
    Feature: Missing code generation

        Scenario: Bound scenario with a missing step
            Given I have a bar
            Then I have a custom bar

        Scenario: Unbound scenario
            Given I have a bar
    ```
* And File "test_existing.py" with content:

    ```python
    from pytest_bdd import given, scenario


    @given("I have a bar")
    def i_have_a_bar():
        return "bar"


    @scenario("generation.feature", "Bound scenario with a missing step")
    def test_bound():
        pass
    ```
* When run pytest

    | cli_args | --gather-missing-steps | generation.feature |
    |----------|------------------------|--------------------|

* Then pytest exits with code 100
* And pytest outcome must match lines:

    | *"scenario": "Unbound scenario"*"type": "missing_scenario_binding"*     |
    |-------------------------------------------------------------------------|
    | *"text": "I have a custom bar"*"type": "missing_step_definition"*       |

## Scenario: Bind a feature idempotently
* Given File "generation.feature" with content:

    ```gherkin
    Feature: Binding generation

        Scenario: Bound scenario with a missing step
            Given I have a bar
            Then I have a custom bar
    ```
* And File "test_generated.py" with content:

    ```python
    from pytest_bdd import scenarios


    scenarios("generation.feature")
    ```
* When run pytest

    | cli_args | --bind-feature | --target-file | test_generated.py | generation.feature |
    |----------|----------------|---------------|-------------------|--------------------|

* Then pytest exits with code 0
* And File "test_generated.py" contains "scenarios(" exactly 1 times
* And File "test_generated.py" contains the line "from pytest_bdd import scenarios"
* And File "test_generated.py" contains text:

    ```python
    scenarios("generation.feature")
    ```

## Scenario: Generate inert missing step skeletons
* Given File "generation.feature" with content:

    ```gherkin
    Feature: Missing step skeletons

        Scenario: Bound scenario with a missing step
            Given I have a bar
            Then I have a custom bar
    ```
* And File "test_existing.py" with content:

    ```python
    from pytest_bdd import given, scenario


    @given("I have a bar")
    def i_have_a_bar():
        return "bar"


    @scenario("generation.feature", "Bound scenario with a missing step")
    def test_bound():
        pass
    ```
* When run pytest

    | cli_args | --generate-missing-steps | --target-file | test_generated.py | generation.feature |
    |----------|--------------------------|---------------|-------------------|--------------------|

* Then pytest exits with code 100
* And File "test_generated.py" contains text:

    ```python
    from pytest_bdd import not_implemented, then


    @not_implemented
    @then("I have a custom bar")
    def _():
        raise NotImplementedError
    ```

## Scenario: Mock-run validates bindings without executing lifecycle code
* Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
* And File "probe.feature" with content:

    ```gherkin
    Feature: Mock run

        Scenario: Probe scenario
            Given a body probe
    ```
* And File "test_probe.py" with content:

    ```python
    from pathlib import Path

    from pytest_bdd import given, scenario


    @scenario("probe.feature", "Probe scenario")
    def test_probe():
        pass


    def pytest_bdd_before_scenario():
        Path("hook.txt").write_text("hook", encoding="utf-8")


    @given("a body probe")
    def body_probe():
        Path("body.txt").write_text("body", encoding="utf-8")
    ```
* When run pytest

    | cli_args | --mock-run |
    |----------|------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

* And File "hook.txt" does not exist
* And File "body.txt" does not exist

## Scenario: Mock-run emits IDE bootstrap messages without executing bodies
* Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
* And File "ide_bootstrap.feature" with content:

    ```gherkin
    Feature: IDE bootstrap

        Scenario: Bootstrap scenario
            Given a body probe
    ```
* And File "test_bootstrap.py" with content:

    ```python
    from pathlib import Path

    from pytest_bdd import given, scenario


    @scenario("ide_bootstrap.feature", "Bootstrap scenario")
    def test_bootstrap():
        pass


    def pytest_bdd_before_scenario(request, run):
        Path("hook.txt").write_text("hook", encoding="utf-8")


    @given("a body probe")
    def body_probe():
        Path("body.txt").write_text("body", encoding="utf-8")
    ```
* When run pytest

    | cli_args | --mock-run | --messages-ndjson | ide-bootstrap.ndjson |
    |----------|------------|-------------------|----------------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

* And File "hook.txt" does not exist
* And File "body.txt" does not exist
* And NDJSON report "ide-bootstrap.ndjson" contains attachment media type "application/vnd.pytest-bdd.launch+json"
* And NDJSON report "ide-bootstrap.ndjson" contains attachment media type "application/vnd.pytest-bdd.step-binding+json"

## Scenario: Mock-run emits missing-step diagnostics for code authoring
* Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
* And File "ide_missing.feature" with content:

    ```gherkin
    Feature: IDE missing step

        Scenario: Missing authoring
            Given this step is missing
    ```
* And File "test_missing_authoring.py" with content:

    ```python
    from pytest_bdd import given, scenario


    @scenario("ide_missing.feature", "Missing authoring")
    def test_missing_authoring():
        pass


    @given("other available step")
    def other_available_step():
        pass
    ```
* When run pytest

    | cli_args | --mock-run | --messages-ndjson | ide-missing.ndjson |
    |----------|------------|-------------------|--------------------|

* Then pytest exits with test failures
* And NDJSON report "ide-missing.ndjson" contains diagnostic "missing-step" with fields:

    | field                    | value                 |
    |--------------------------|-----------------------|
    | unmatchedStepText        | this step is missing  |
    | availableStepDefinitions | other available step  |

## Scenario: Mock-run reports duplicate source bindings
* Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
* And File "ide_duplicate.feature" with content:

    ```gherkin
    Feature: IDE duplicate binding

        Scenario: Duplicate source
            Given a shared step
    ```
* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given


    @given("a shared step")
    def shared_step():
        pass
    ```
* And File "test_duplicate_a.py" with content:

    ```python
    from pytest_bdd import scenario


    @scenario("ide_duplicate.feature", "Duplicate source")
    def test_duplicate_source():
        pass
    ```
* And File "test_duplicate_b.py" with content:

    ```python
    from pytest_bdd import scenario


    @scenario("ide_duplicate.feature", "Duplicate source")
    def test_duplicate_source():
        pass
    ```
* When run pytest

    | cli_args | --mock-run | --messages-ndjson | ide-duplicate.ndjson |
    |----------|------------|-------------------|----------------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 2      |

* And NDJSON report "ide-duplicate.ndjson" contains diagnostic "duplicate-bindings" with fields:

    | field    | value               |
    |----------|---------------------|
    | severity | warning             |
    | bindings | test_duplicate_a.py |
    | bindings | test_duplicate_b.py |

## Scenario: Not implemented steps can be treated as passed work in progress
* Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
* And File "wip.feature" with content:

    ```gherkin
    Feature: WIP steps

        Scenario: Pending step
            Given a pending step
    ```
* And File "test_wip.py" with content:

    ```python
    from pathlib import Path

    from pytest_bdd import given, not_implemented, scenario


    @scenario("wip.feature", "Pending step")
    def test_pending():
        pass


    @given("a pending step")
    @not_implemented
    def pending_step():
        Path("pending-body.txt").write_text("ran", encoding="utf-8")
        raise NotImplementedError
    ```
* When run pytest

    | cli_args | --wip-status | passed |
    |----------|--------------|--------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

* And File "pending-body.txt" does not exist

## Scenario: Tolerant ignored failures let scenarios continue
* Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
* And File "tolerant.feature" with content:

    ```gherkin
    Feature: Tolerant steps

        Scenario: Tolerant failure
            Given a tolerant step fails
            Then a later step runs
    ```
* And File "test_tolerant.py" with content:

    ```python
    from pathlib import Path

    from pytest_bdd import given, scenario, then, tolerant


    @scenario("tolerant.feature", "Tolerant failure")
    def test_tolerant_failure():
        pass


    @tolerant
    @given("a tolerant step fails")
    def tolerant_step():
        raise AssertionError("soft failure")


    @then("a later step runs")
    def later_step():
        Path("later.txt").write_text("ran", encoding="utf-8")
    ```
* When run pytest

    | cli_args | --tolerant-status | ignored |
    |----------|-------------------|---------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

* And File "later.txt" contains the line "ran"
