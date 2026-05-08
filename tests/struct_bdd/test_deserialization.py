"""Provide test deserialization helpers."""

from functools import partial
from operator import contains
from textwrap import dedent

import pytest
from cucumber_messages import StepKeywordType
from gherkin.pickles.compiler import Compiler
from yaml import FullLoader
from yaml import load as load_yaml

from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.model.message_converter import message_converter  # type:ignore[attr-defined]
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.pytest_extra import doesnt_raise

if STRUCT_BDD_INSTALLED:  # pragma: no cover
    from pytest_bdd.plugin.struct_bdd.model import Alternative, Join, Keyword, Node, Step, StepPrototype, Table
    from pytest_bdd.plugin.struct_bdd.model_builder import GherkinDocumentBuilder

pytestmark = [pytest.mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed")]


def test_node_containing_data_load():
    """Verify node containing data load."""
    node = Node.model_validate(
        {
            "Tags": ["Tag A", "Tag B"],
            "Name": "Node name",
            "Description": "Node description",
            "Comments": ["Comment A", "Comment B"],
        },
    )
    assert all(
        [
            "Tag A" in node.tags,
            "Tag B" in node.tags,
        ],
    )
    assert node.name == "Node name"
    assert node.description == "Node description"
    assert all(
        [
            "Comment A" in node.comments,
            "Comment B" in node.comments,
        ],
    )


def test_node_non_containing_data_load():
    """Verify node non containing data load."""
    node = Node.model_validate({})
    assert node.tags == []
    assert node.name is None
    assert node.description is None
    assert node.comments == []


def test_table_columned_containing_data_load():
    """Verify table columned containing data load."""
    table = Table.model_validate(
        {
            "Tags": ["Tag A", "Tag B"],
            "Name": "Table name",
            "Description": "Table description",
            "Comments": ["Comment A", "Comment B"],
            "Type": "Columned",
            "Parameters": ["Parameter A", "Parameter B"],
            "Values": [["Value A1", "Value A2"], ["Value B1", "Value B2"]],
        },
    )

    assert all(
        [
            "Tag A" in table.tags,
            "Tag B" in table.tags,
        ],
    )
    assert table.name == "Table name"
    assert table.description == "Table description"
    assert all(
        [
            "Comment A" in table.comments,
            "Comment B" in table.comments,
        ],
    )

    assert table.type == "Columned"
    assert table.parameters == ["Parameter A", "Parameter B"]
    assert table.values[0] == ["Value A1", "Value A2"]
    assert table.values[1] == ["Value B1", "Value B2"]
    assert table.columned_values == table.values


def test_table_rowed_containing_data_load():
    """Verify table rowed containing data load."""
    table = Table.model_validate(
        {
            "Type": "Rowed",
            "Parameters": ["Parameter A", "Parameter B"],
            "Values": [["Value A1", "Value A2"], ["Value B1", "Value B2"]],
        },
    )
    assert table.type == "Rowed"
    assert table.parameters == ["Parameter A", "Parameter B"]
    assert table.values[0] == ["Value A1", "Value A2"]
    assert table.values[1] == ["Value B1", "Value B2"]
    assert table.rowed_values == table.values


def test_table_non_containing_data_load():
    """Verify table non containing data load."""
    table = Table.model_validate({})

    assert table.tags == []
    assert table.name is None
    assert table.description is None
    assert table.comments == []

    assert table.type == "Rowed"
    assert table.parameters == []
    assert table.values == []


def test_join_load():
    """Verify join load."""
    raw_table_a = {
        "Tags": ["Tag A1", "Tag A2"],
        "Name": "Table A name",
        "Description": "Table A description",
        "Comments": ["Comment A1", "Comment A2"],
        "Type": "Columned",
        "Parameters": ["Parameter A1", "Parameter A2"],
        "Values": [["Value A11", "Value A12"], ["Value A21", "Value A22"]],
    }
    raw_table_b = {
        "Tags": ["Tag B1", "Tag B2"],
        "Name": "Table B name",
        "Description": "Table B description",
        "Comments": ["Comment B1", "Comment B2"],
        "Type": "Columned",
        "Parameters": ["Parameter B1", "Parameter B2"],
        "Values": [["Value B11", "Value B12"], ["Value B21", "Value B22"]],
    }

    join = Join.model_validate({"Join": [raw_table_a, raw_table_b]})
    assert join.tags == ["Tag A1", "Tag A2", "Tag B1", "Tag B2"]
    assert join.name == "\n".join([raw_table_a["Name"], raw_table_b["Name"]])
    assert join.description == "\n".join([raw_table_a["Description"], raw_table_b["Description"]])
    assert join.comments == ["Comment A1", "Comment A2", "Comment B1", "Comment B2"]
    assert join.parameters == [
        "Parameter A1",
        "Parameter A2",
        "Parameter B1",
        "Parameter B2",
    ]
    assert join.values == [
        ["Value A11", "Value A21", "Value B11", "Value B21"],
        ["Value A11", "Value A21", "Value B12", "Value B22"],
        ["Value A12", "Value A22", "Value B11", "Value B21"],
        ["Value A12", "Value A22", "Value B12", "Value B22"],
    ]
    assert join.columned_values == [
        ("Value A11", "Value A11", "Value A12", "Value A12"),
        ("Value A21", "Value A21", "Value A22", "Value A22"),
        ("Value B11", "Value B12", "Value B11", "Value B12"),
        ("Value B21", "Value B22", "Value B21", "Value B22"),
    ]


def test_step_prototype_non_containing_data_load():
    """Verify step prototype non containing data load."""
    step = StepPrototype.model_validate({})

    assert step.tags == []
    assert step.name is None
    assert step.description is None
    assert step.comments == []

    assert step.steps == []
    assert step.type == Keyword.Star
    assert step.data == []
    assert step.examples == []


def test_step_non_containing_data_load():
    """Verify step non containing data load."""
    step = Step.model_validate({})

    assert step.tags == []
    assert step.name is None
    assert step.description is None
    assert step.comments == []

    assert step.steps == []
    assert step.action is None
    assert step.type == Keyword.Star
    assert step.data == []
    assert step.examples == []

    routes = list(step.routes)
    assert len(routes) == 1
    route = routes[0]
    assert route.tags == []
    assert len(route.steps) == 1
    step = route.steps[0]
    assert step.action is None


def test_load_simplest_step_with_text_steps():
    """Verify load simplest step with text steps."""
    step: Step = Step().model_validate({"Steps": ["Do something"]})
    assert step.steps[0].type == Keyword.Star
    assert step.steps[0].keyword_type == StepKeywordType.unknown
    assert step.steps[0].action == "Do something"

    routes = list(step.routes)
    assert len(routes) == 1
    route = routes[0]
    assert route.tags == []
    assert route.steps[0].action is None
    assert route.steps[1] == step.steps[0]


def test_load_simplest_given():
    """Verify load simplest given."""
    step = Step.model_validate(
        {
            "Steps": [
                {"Given": "Do something"},
            ],
        },
    )
    assert step.steps[0].type == Keyword.Given
    assert step.steps[0].keyword_type == StepKeywordType.context
    assert step.steps[0].action == "Do something"

    routes = list(step.routes)
    assert len(routes) == 1
    route = routes[0]
    assert route.tags == []
    assert route.steps[0].action is None
    assert route.steps[1] == step.steps[0]


def test_load_actioned_step_with_text_steps():
    """Verify load actioned step with text steps."""
    step: Step = Step.model_validate({"Action": "First do", "Steps": ["Do something"]})
    assert step.steps[0].type == Keyword.Star
    assert step.steps[0].keyword_type == StepKeywordType.unknown
    assert step.steps[0].action == "Do something"

    routes = list(step.routes)
    assert len(routes) == 1
    route = routes[0]
    assert route.tags == []
    assert route.steps == [step, step.steps[0]]


def test_load_alternative_step_with_text_steps():
    """Verify load alternative step with text steps."""
    alternative_step: Alternative = Alternative.model_validate({"Alternative": ["Do something"]})

    routes = list(alternative_step.routes)
    assert len(routes) == 1
    route = routes[0]
    assert route.tags == []
    assert route.steps[0].action == "Do something"


def test_load_actioned_step_with_alternative_text_steps():
    """Verify load actioned step with alternative text steps."""
    step: Step = Step.model_validate(
        {
            "Action": "First do",
            "Steps": [
                {
                    "Alternative": [
                        "Do something",
                        "Do something else",
                    ],
                },
            ],
        },
    )

    routes = list(step.routes)
    oracle_routes_count = 2
    assert len(routes) == oracle_routes_count
    assert routes[0].steps == [step, step.steps[0].steps[0]]
    assert routes[1].steps == [step, step.steps[0].steps[1]]


def test_load_simplest_step_with_keyworded_steps():
    """Verify load simplest step with keyworded steps."""
    step: Step = Step.model_validate(
        {
            "Steps": [
                {"Given": "Given Do something"},
                {"When": "When Do something"},
                {"Then": "Then Do something"},
                {"And": "And Do something"},
                {"But": "But Do something"},
                {"*": "* Do something"},
                "Do something",
                {"Because": "Because Do something"},
                {"Step": {"Action": "Step Do something"}},
            ],
        },
    )

    routes = list(step.routes)
    assert len(routes) == 1


def test_load_step_with_single_simplest_steps():
    """Verify load step with single simplest steps."""
    with doesnt_raise(Exception):
        Step.model_validate({"Steps": [{"Step": {}}]})


def test_node_module_load_for_step():
    """Verify node module load for step."""
    with doesnt_raise(Exception):
        doc = dedent(
            # language=yaml
            """\
            Name: StepName
            Tags:
              - StepTag
              - StepTag
            Description: |
                Multiline

                Step description
            Comments:
              - Very nice comment
            Steps: []
            """,
        )

        data = load_yaml(doc, Loader=FullLoader)
        Step.model_validate(data)


def test_data_load():
    """Verify data load."""
    with doesnt_raise(Exception):
        doc = dedent(
            # language=yaml
            """\
            Name: StepName
            Data:
              - Table:
                  Tags:
                    - StepDataTableTag
                  Name: StepDataTableName
                  Description: StepDataTableDescription
                  Type: Columned
                  Parameters:
                    - StepDataTableParametersHeader1
                    - StepDataTableParametersHeader2
                  Values:
                    - [ a, b, c ]
                    - [ d, e, f ]
            Steps: []
            """,
        )

        data = load_yaml(doc, Loader=FullLoader)
        Step.model_validate(data)


def test_nested_sub_join_load():
    """Verify nested sub join load."""
    with doesnt_raise(Exception):
        doc = dedent(
            # language=yaml
            """
            Join:
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader1
                    - StepDataTableParametersHeader2
                  Values:
                    - [ a, b, c ]
                    - [ d, e, f ]
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader3
                    - StepDataTableParametersHeader4
                  Values: [ ]
            """,
        )

        data = load_yaml(doc, Loader=FullLoader)
        Join.model_validate(data)


def test_nested_data_load():
    """Verify nested data load."""
    with doesnt_raise(Exception):
        doc = dedent(
            # language=yaml
            """\
            Name: StepName
            Data:
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader1
                    - StepDataTableParametersHeader2
                  Values:
                    - [ a, b, c ]
                    - [ d, e, f ]
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader3
                    - StepDataTableParametersHeader4
                  Values: [ ]
              - Join:
                  - Table:
                      Parameters:
                        - StepDataTableParametersHeader1
                        - StepDataTableParametersHeader2
                      Values:
                        - [ a, b, c ]
                        - [ d, e, f ]
                  - Table:
                      Parameters:
                        - StepDataTableParametersHeader3
                        - StepDataTableParametersHeader4
                      Values: [ ]
            Steps: []
            """,
        )

        data = load_yaml(doc, Loader=FullLoader)
        Step.model_validate(data)


def test_nested_examples_load():
    """Verify nested examples load."""
    with doesnt_raise(Exception):
        doc = dedent(
            # language=yaml
            """\
            Name: StepName
            Examples:
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader1
                    - StepDataTableParametersHeader2
                  Values:
                    - [ a, b, c ]
                    - [ d, e, f ]
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader3
                    - StepDataTableParametersHeader4
                  Values: [ ]
              - Join:
                  - Table:
                      Parameters:
                        - StepDataTableParametersHeader1
                        - StepDataTableParametersHeader2
                      Values:
                        - [ a, b, c ]
                        - [ d, e, f ]
                  - Table:
                      Parameters:
                        - StepDataTableParametersHeader3
                        - StepDataTableParametersHeader4
                      Values: [ ]
            Steps: []
            """,
        )

        data = load_yaml(doc, Loader=FullLoader)
        Step.model_validate(data)


def test_tags_steps_examples_load():
    """Verify tags steps examples load."""
    doc = dedent(
        # language=yaml
        """\
        Tags:
          - TopTag
        Name: StepName
        Action: "Do first"
        Examples:
          - Table:
              Tags:
                - ExampleTag
              Parameters:
                [ Header1, Header2, Header3 ]
              Values:
                - [ a, b, c ]
                - [ d, e, f ]
        Steps:
          - Given: "Do next"
          - Step:
              Action: "Do something else"
              Tags:
                - StepTag
              Examples:
                  - Table:
                      Tags:
                        - StepExampleTag
                      Parameters:
                        [ Header4, Header5, Header6 ]
                      Values:
                        - [ g, h, i ]
                        - [ j, k, l ]
          - "Do last"
        """,
    )

    data = load_yaml(doc, Loader=FullLoader)
    step = Step.model_validate(data)
    routes = list(step.routes)

    assert len(routes) == 1
    route = routes[0]
    assert all(
        map(
            partial(contains, route.tags),
            ["TopTag", "ExampleTag", "StepTag", "StepExampleTag"],
        )
    )
    assert all(
        map(
            partial(contains, route.example_table.parameters),
            ["Header1", "Header2", "Header3", "Header4", "Header5", "Header6"],
        ),
    )
    oracle_route_example_table_length = 4
    assert len(route.example_table.values) == oracle_route_example_table_length

    document_ast = GherkinDocumentBuilder(step).build(id_generator=IdGenerator())
    document_ast.uri = "uri"

    pickles = Compiler().compile(message_converter.to_dict(document_ast))
    oracle_pickles_count = 4
    assert len(pickles) == oracle_pickles_count


def test_tags_steps_examples_load_complex():
    """Verify tags steps examples load complex."""
    doc = dedent(
        # language=yaml
        """\
        Tags:
          - TopTag
        Name: StepName
        Action: "Do first"
        Examples:
          - Join:
            - Table:
                Tags:
                  - ExampleTagA
                Parameters:
                  [ HeaderA, HeaderB, HeaderC ]
                Values:
                  - [ A1, B1, C1 ]
                  - [ A2, B2, C2 ]
            - Table:
                Tags:
                  - ExampleTagB
                Parameters:
                  [ HeaderD ]
                Values:
                  - [ D1 ]
                  - [ D2 ]
                  - [ D3 ]
          - Table:
              Tags:
                - ExampleTagC
              Parameters:
                [ HeaderK ]
              Values:
                - [ K1 ]
                - [ K2 ]
                - [ K3 ]
        Steps:
          - Alternative:
              - Step:
                  Action: "Do something else"
                  Tags:
                    - StepTagA
                  Examples:
                      - Join:
                          - Table:
                              Tags:
                                - StepExampleTagA
                              Parameters:
                                [ HeaderE, HeaderF ]
                              Values:
                                - [ E1, F1 ]
                                - [ E2, F2 ]
              - Step:
                  Action: "Do next"
                  Tags:
                    - StepTagB
                  Examples:
                      - Join:
                          - Table:
                              Type: Columned
                              Tags:
                                - StepExampleTagB
                              Parameters:
                                [ HeaderG, HeaderH ]
                              Values:
                                - [ G1, G2 ]
                                - [ H1, H2 ]
                          - Table:
                              Tags:
                                - StepExampleTagC
                              Parameters:
                                [ HeaderI, HeaderJ ]
                              Values:
                                - [ I1, J1 ]
                                - [ I2, J2 ]
        """,
    )

    data = load_yaml(doc, Loader=FullLoader)
    step = Step.model_validate(data)

    routes = list(step.routes)

    oracle_routes_count = 4
    assert len(routes) == oracle_routes_count

    oracle_route_example_table_lengths = (12, 6, 24, 12)
    assert all(
        len(route.example_table.values) == oracle_length
        for route, oracle_length in zip(routes, oracle_route_example_table_lengths, strict=False)
    )

    assert all(
        map(
            partial(contains, routes[0].tags),
            ["TopTag", "ExampleTagA", "ExampleTagB", "StepTagA", "StepExampleTagA"],
        ),
    )
    assert all(
        map(
            partial(contains, routes[0].example_table.parameters),
            ["HeaderC", "HeaderF", "HeaderA", "HeaderE", "HeaderB", "HeaderD"],
        ),
    )

    assert all(
        map(
            partial(contains, routes[1].tags),
            ["ExampleTagC", "StepExampleTagA", "StepTagA", "TopTag"],
        )
    )
    assert all(
        map(
            partial(contains, routes[1].example_table.parameters),
            routes[1].example_table.parameters,
        )
    )

    assert all(
        map(
            partial(contains, routes[2].tags),
            [
                "TopTag",
                "StepExampleTagB",
                "StepExampleTagC",
                "ExampleTagB",
                "StepTagB",
                "ExampleTagA",
            ],
        ),
    )
    assert all(
        map(
            partial(contains, routes[2].example_table.parameters),
            [
                "HeaderG",
                "HeaderC",
                "HeaderI",
                "HeaderA",
                "HeaderH",
                "HeaderB",
                "HeaderJ",
                "HeaderD",
            ],
        ),
    )

    assert all(
        map(
            partial(contains, routes[3].tags),
            ["TopTag", "StepExampleTagB", "StepExampleTagC", "ExampleTagC", "StepTagB"],
        ),
    )
    assert all(
        map(
            partial(contains, routes[3].example_table.parameters),
            ["HeaderG", "HeaderK", "HeaderI", "HeaderH", "HeaderJ"],
        ),
    )


def test_tags_steps_examples_joined_by_value_load():
    """Verify tags steps examples joined by value load."""
    doc = dedent(
        # language=yaml
        """\
        Tags:
          - TopTag
        Name: StepName
        Action: "Do first"
        Examples:
          - Join:
            - Table:
                Tags:
                  - ExampleTagA
                Parameters:
                  [ HeaderA, HeaderB ]
                Values:
                  - [ A1, B1]
                  - [ A2, B2]
            - Table:
                Tags:
                  - ExampleTagB
                Parameters:
                  [ HeaderB, HeaderC ]
                Values:
                  - [ B1, C1 ]
                  - [ B2, C2 ]
                  - [ B3, C3 ]
        Steps: []
        """,
    )

    data = load_yaml(doc, Loader=FullLoader)
    step = Step.model_validate(data)

    routes = list(step.routes)

    assert len(routes) == 1

    oracle_routes_example_table_length = 2
    assert len(routes[0].example_table.values) == oracle_routes_example_table_length


def test_load_nested_steps():
    """Verify load nested steps."""
    with doesnt_raise(Exception):
        doc = dedent(
            # language=yaml
            """\
            Steps:
              - Alternative:
                  - Given: Do something
                  - When: Do something
                  - Then: Do something
                  - And: Do something
                  - "*": Do something
              - Given: Do something
              - When: Do something
              - Then: Do something
              - And: Do something
              - "*": Do something
              - Step:
                  Action: Do something
            """,
        )

        data = load_yaml(doc, Loader=FullLoader)
        Step.model_validate(data)
