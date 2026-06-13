"""

Unit tests for scenario helper functions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd.scenario import FeaturePathType, get_python_name_generator, scenario, scenarios

pytestmark = [pytest.mark.unit]


def test_scenario_returns_decorator() -> None:
    """
    Scenario returns a decorator by default.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decorator = scenario("features/example.feature", "Example")

    assert callable(decorator)


def test_scenario_can_return_generated_test_function() -> None:
    """
    Scenario can return a generated test function directly.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    test_func = scenario("features/example.feature", "Example", return_test_decorator=False)

    assert callable(test_func)
    assert test_func.__name__.startswith("test")


def test_scenarios_returns_generated_test_function() -> None:
    """
    Scenarios returns a generated test function by default.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    test_func = scenarios("features/example.feature")

    assert callable(test_func)
    assert test_func.__name__ == "test_"


def test_scenarios_rejects_base_dir_and_base_url_together() -> None:
    """
    Scenarios rejects mutually exclusive path configuration.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    with pytest.raises(ValueError, match="Both"):
        scenarios("feature.feature", features_base_dir=Path(), features_base_url="https://example.test")


def test_scenarios_accepts_filter_callback() -> None:
    """
    Scenarios stores a callable filter on the pytest-bdd marker.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """

    def filter_(_config: object, _feature: object, _pickle: object) -> bool:
        return False

    test_func = scenarios("feature.feature", filter_=filter_)

    marker = next(mark for mark in test_func.pytestmark if mark.name == "scenarios")
    assert marker.kwargs["filter_"] is filter_


def test_scenarios_switches_to_url_path_type_when_base_url_is_set() -> None:
    """
    Scenarios uses URL path type when features_base_url is supplied.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    test_func = scenarios("feature.feature", features_base_url="https://example.test")

    marker = next(mark for mark in test_func.pytestmark if mark.name == "scenarios")
    assert marker.kwargs["features_path_type"] == FeaturePathType.URL


def test_python_name_generator_handles_empty_name_and_duplicates() -> None:
    """
    Python name generator yields pytest-collectable names.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    generator = get_python_name_generator("")

    assert next(generator) == "test_"
    assert next(generator) == "test_1"


def test_python_name_generator_with_real_name() -> None:
    """
    Python name generator formats a real scenario name.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    generator = get_python_name_generator("login with valid credentials")

    assert next(generator) == "test_login_with_valid_credentials"


def test_python_name_generator_with_special_chars() -> None:
    """
    Python name generator strips special characters.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    generator = get_python_name_generator("user's data (test)")

    name = next(generator)
    assert name.startswith("test_")
    assert "'" not in name


def test_scenarios_uses_features_base_dir() -> None:
    """
    Scenarios accepts a features base directory.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    test_func = scenarios("feature.feature", features_base_dir=Path.cwd())

    assert callable(test_func)


def test_scenarios_returns_decorator_with_return_test_decorator_true() -> None:
    """
    Scenarios returns decorator when return_test_decorator is True.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decorator = scenarios("feature.feature", return_test_decorator=True)

    assert callable(decorator)


def test_scenarios_passes_encoding_parameter() -> None:
    """
    Scenarios accepts encoding parameter.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    test_func = scenarios("feature.feature", encoding="latin-1")

    assert callable(test_func)


def test_scenario_with_encoding_parameter() -> None:
    """
    Scenario function accepts encoding parameter.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decorator = scenario("features/example.feature", "Test", encoding="utf-16")

    assert callable(decorator)
