import json
from collections import Counter

import pytest

from pytest_cuke.compatibility.struct_bdd import STRUCT_BDD_INSTALLED

pytestmark = pytest.mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed")


@pytest.mark.parametrize(
    "suffix", [".bdd.yaml", ".bdd.yml", ".bdd", ".bdd.json", ".bdd.json5", ".bdd.hjson", ".bdd.hocon", ".bdd.toml"]
)
@pytest.mark.parametrize("duplicate", [False, True])
def test_joined_examples_execute_every_combination(pytester, suffix, duplicate):
    pytest.importorskip("pydantic")
    pytest.importorskip("yaml")
    pytester.makeini("[pytest]\ncuke_parser = python\n")
    second = "a" if duplicate else "d"
    document = {
        "Tags": ["TopTag"],
        "Name": "StepName",
        "Action": "Do first <Header1> <Header4>",
        "Examples": [{"Table": {"Parameters": ["Header1"], "Values": [["a"], [second]]}}],
        "Steps": [
            {
                "Step": {
                    "Action": "Do next",
                    "Examples": [{"Table": {"Parameters": ["Header4"], "Values": [["g"], ["j"]]}}],
                }
            }
        ],
    }
    if suffix == ".bdd.toml":
        content = f'''
Tags = ["TopTag"]
Name = "StepName"
Action = "Do first <Header1> <Header4>"
[[Examples]]
[Examples.Table]
Parameters = ["Header1"]
Values = [["a"], ["{second}"]]
[[Steps]]
[Steps.Step]
Action = "Do next"
[[Steps.Step.Examples]]
[Steps.Step.Examples.Table]
Parameters = ["Header4"]
Values = [["g"], ["j"]]
'''
    else:
        content = json.dumps(document)
    pytester.makefile(suffix, joined=content)
    pytester.makeconftest("""
from pytest_cuke import parsers, step
@step(parsers.parse("Do first {first} {second}"))
def first(first, second):
    pass
@step("Do next")
def next_step():
    pass
""")
    result = pytester.runpytest_subprocess(
        "--cuke-autoload", "--cuke-messages-ndjson=messages.ndjson", f"joined{suffix}", "-q"
    )
    result.assert_outcomes(passed=4)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    cases = [event["testCase"] for event in events if "testCase" in event]
    assert len(cases) == 4
    assert len({case["pickleId"] for case in cases}) == 4
    pickles = [event["pickle"] for event in events if "pickle" in event]
    expected = Counter(["Do first a g", "Do first a j", f"Do first {second} g", f"Do first {second} j"])
    assert Counter(pickle["steps"][0]["text"] for pickle in pickles) == expected
