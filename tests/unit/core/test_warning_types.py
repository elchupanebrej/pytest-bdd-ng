from __future__ import annotations

import pickle
import warnings

from pytest_cuke.warning_types import PytestBDDStepDefinitionWarning


def test_warning_hierarchy_and_emission() -> None:
    assert issubclass(PytestBDDStepDefinitionWarning, UserWarning)
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        warnings.warn("test warning", PytestBDDStepDefinitionWarning, stacklevel=1)
        assert len(recorded) == 1
        assert issubclass(recorded[0].category, PytestBDDStepDefinitionWarning)


def test_warning_round_trips_through_its_nested_module_path() -> None:
    warning = PytestBDDStepDefinitionWarning("duplicate step")

    serialized = pickle.dumps(warning)

    assert PytestBDDStepDefinitionWarning.__module__ == "pytest_cuke.warning_types"
    assert type(pickle.loads(serialized)) is PytestBDDStepDefinitionWarning
