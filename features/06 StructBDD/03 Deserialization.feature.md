# Feature: StructBDD deserialization and routing
  This feature documents how StructBDD YAML/JSON-like structures are
  deserialized into internal models and then expanded into executable routes.

## Scenario: Node, Table, and Step defaults deserialize safely
* Given File "test_deser_defaults.py" with content:

    ```python
    import pytest
    from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED

    pytestmark = [pytest.mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed")]

    from pytest_bdd.plugin.struct_bdd.model import Node, Step, Table


    def test_defaults():
        node = Node.model_validate({})
        assert node.tags == []
        assert node.name is None
        assert node.description is None
        assert node.comments == []

        table = Table.model_validate({})
        assert table.type == "Rowed"
        assert table.parameters == []
        assert table.values == []

        step = Step.model_validate({})
        routes = list(step.routes)
        assert len(routes) == 1
        assert routes[0].steps[0].action is None
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Joined examples build expanded tables and executable pickles
* Given File "test_deser_join.py" with content:

    ```python
    from textwrap import dedent

    import pytest
    from gherkin.pickles.compiler import Compiler
    from yaml import FullLoader
    from yaml import load as load_yaml

    from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED

    pytestmark = [pytest.mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed")]

    from pytest_bdd.model.message_converter import message_converter
    from pytest_bdd.plugin.struct_bdd.model import Step
    from pytest_bdd.plugin.struct_bdd.model_builder import GherkinDocumentBuilder
    from pytest_bdd.util.other import IdGenerator


    def test_joined_examples_expand():
        doc = dedent(
            """
        Tags:
          - TopTag
        Name: StepName
        Action: "Do first"
        Examples:
          - Table:
              Tags: [ExampleTag]
              Parameters: [Header1, Header2, Header3]
              Values:
                - [a, b, c]
                - [d, e, f]
        Steps:
          - Step:
              Action: "Do next"
              Tags: [StepTag]
              Examples:
                - Table:
                    Tags: [StepExampleTag]
                    Parameters: [Header4, Header5, Header6]
                    Values:
                      - [g, h, i]
                      - [j, k, l]
        """
        )
        step = Step.model_validate(load_yaml(doc, Loader=FullLoader))
        routes = list(step.routes)
        assert len(routes) == 1
        assert all(tag in routes[0].tags for tag in ["TopTag", "ExampleTag", "StepTag", "StepExampleTag"])
        assert len(routes[0].example_table.values) == 4

        document_ast = GherkinDocumentBuilder(step).build(id_generator=IdGenerator())
        document_ast.uri = "uri"
        pickles = Compiler().compile(message_converter.to_dict(document_ast))
        assert len(pickles) == 4
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Nested alternative steps deserialize without errors
* Given File "test_deser_nested.py" with content:

    ```python
    from textwrap import dedent

    import pytest
    from yaml import FullLoader
    from yaml import load as load_yaml

    from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED

    pytestmark = [pytest.mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed")]

    from pytest_bdd.plugin.struct_bdd.model import Step


    def test_nested_steps_are_valid():
        doc = dedent(
            """
        Steps:
          - Alternative:
              - Given: Do something
              - When: Do something
              - Then: Do something
          - Given: Do something
          - Step:
              Action: Do final thing
        """
        )
        step = Step.model_validate(load_yaml(doc, Loader=FullLoader))
        routes = list(step.routes)
        assert len(routes) == 3
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |
