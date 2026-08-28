from __future__ import annotations

import warnings

from pytest_bdd.warning_types import PytestBDDStepDefinitionWarning


def test_warning_hierarchy_and_emission() -> None:
    assert issubclass(PytestBDDStepDefinitionWarning, UserWarning)
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        warnings.warn("test warning", PytestBDDStepDefinitionWarning, stacklevel=1)
        assert len(recorded) == 1
        assert issubclass(recorded[0].category, PytestBDDStepDefinitionWarning)
