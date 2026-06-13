"""

Provide test pickles load helpers.
"""

import json
from pathlib import Path

import pytest
from cucumber_messages import Pickle  # type:ignore[attr-defined] — upstream type stubs missing this attribute

from pytest_bdd.model.message_converter import message_converter

test_data = Path(__file__).parent.parent.parent / "gherkin" / "testdata"


@pytest.mark.parametrize(
    "pickle_path",
    (pytest.param(file, id=file.name) for file in (test_data / "good").glob("*.pickles.ndjson")),
)
def test_simple_load_pickle(pickle_path: Path):
    """
    Verify simple load pickle.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    with pickle_path.open(encoding="utf-8", mode="r") as pickle_file:
        for pickle_line in pickle_file:
            pickle_data = json.loads(pickle_line)["pickle"]
            pickle = message_converter.from_dict(pickle_data, Pickle)  # type: ignore[attr-defined] # migration to pydantic2
            assert isinstance(pickle, Pickle)

            dumped_pickle_data = message_converter.to_dict(pickle)

            assert pickle_data == dumped_pickle_data
