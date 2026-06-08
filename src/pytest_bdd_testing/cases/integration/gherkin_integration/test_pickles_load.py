"""Provide test pickles load helpers."""

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
    """Verify simple load pickle."""
    with pickle_path.open(encoding="utf-8", mode="r") as pickle_file:
        for pickle_line in pickle_file:
            pickle_data = json.loads(pickle_line)["pickle"]
            pickle = message_converter.from_dict(pickle_data, Pickle)  # type: ignore[attr-defined] # migration to pydantic2
            assert isinstance(pickle, Pickle)

            dumped_pickle_data = message_converter.to_dict(pickle)

            assert pickle_data == dumped_pickle_data
