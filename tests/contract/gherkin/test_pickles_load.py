import json
from pathlib import Path

from pytest import mark, param

from pytest_cuke.model.message_types import Pickle, message_from_dict, message_to_dict

test_data = Path(__file__).parent.parent.parent.parent / "gherkin" / "testdata"


@mark.parametrize(
    "pickle_path",
    map(
        lambda file: param(file, id=file.name),  # type: ignore[no-any-return]
        (test_data / "good").glob("*.pickles.ndjson"),
    ),
)
def test_simple_load_pickle(pickle_path: Path):
    with pickle_path.open(mode="r") as pickle_file:
        for pickle_line in pickle_file:
            pickle_data = json.loads(pickle_line)["pickle"]
            pickle = message_from_dict(pickle_data, Pickle)
            assert isinstance(pickle, Pickle)

            dumped_pickle_data = message_to_dict(pickle)

            assert pickle_data == dumped_pickle_data
