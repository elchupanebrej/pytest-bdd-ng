import json


def test_ast_ids_are_unique_between_documents_and_all_pickle_refs_resolve(pytester):
    pytester.makeini(
        "[pytest]\ncuke_features_dir = features\ncuke_parser = python\n"
        "markers =\n    first: first source\n    second: second source\n"
    )
    root = pytester.path / "features"
    root.mkdir()
    for name in ("first", "second"):
        (root / f"{name}.feature").write_text(
            f"@{name}\nFeature: {name} source\n"
            "  Background: context\n    Given a context\n"
            f"  Scenario: {name} scenario\n    Given a value {name}\n"
        )
    pytester.makeconftest("""
from pytest_cuke import given, parsers

@given("a context")
def context():
    pass

@given(parsers.parse("a value {value}"))
def value(value):
    assert value in {"first", "second"}
""")
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(passed=2)
    assert result.ret == 0
    rows = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    documents = [row["gherkinDocument"] for row in rows if "gherkinDocument" in row]
    pickles = [row["pickle"] for row in rows if "pickle" in row]
    assert len(documents) == len(pickles) == 2
    sources = {}

    def remember(value, uri):
        if isinstance(value, dict):
            if "id" in value:
                assert value["id"] not in sources, f"duplicate AST id {value['id']} in {uri} and {sources}"
                sources[value["id"]] = uri
            for item in value.values():
                remember(item, uri)
        elif isinstance(value, list):
            for item in value:
                remember(item, uri)

    for document in documents:
        remember(document, document["uri"])
    for pickle in pickles:
        references = [*pickle["astNodeIds"], *(tag["astNodeId"] for tag in pickle["tags"])]
        references.extend(node for step in pickle["steps"] for node in step["astNodeIds"])
        assert references
        assert all(sources[node] == pickle["uri"] for node in references)
