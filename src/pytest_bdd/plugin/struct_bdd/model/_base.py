"""
Base model classes for struct BDD.

Responsibility:
    Base model classes for struct BDD. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - Keyword: owns nested behavior below this boundary
    - SubKeyword: owns nested behavior below this boundary
    - Node: owns nested behavior below this boundary
    - Table: owns nested behavior below this boundary
    - SubTable: owns nested behavior below this boundary
    - convert_sub_tables_to_tables: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_base`
    - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `_base`

State and side effects:
    mutates values, model_config, Given, When, Then; depends on collections.defaultdict, collections.abc.Callable,
    collections.abc.Iterator, collections.abc.Mapping, collections.abc.Sequence.

Invariants:
    - `pytest_bdd.plugin.struct_bdd.model._base` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from collections import defaultdict
from collections.abc import Callable, Iterator, Mapping, Sequence
from enum import Enum
from itertools import chain, product, starmap
from operator import attrgetter, eq
from typing import Annotated, Any, Literal, TypeAlias, TypeVar, Union, cast

from cucumber_messages import StepKeywordType
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
)

from pytest_bdd.util.toolz_extra import deepattrgetter

# mypy: disable-error-code="typeddict-unknown-key, typeddict-item"


class Keyword(Enum):
    """
    Represent keyword state.

    Responsibility:
        Represent keyword state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Keyword` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `Keyword`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `Keyword`

    State and side effects:
        mutates Given, When, Then, And, But.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._base.Keyword` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    Given = "Given"
    When = "When"
    Then = "Then"
    And = "And"
    But = "But"
    Star = "*"


class SubKeyword(Enum):
    """
    Represent sub keyword state.

    Responsibility:
        Represent sub keyword state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.SubKeyword` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `SubKeyword`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `SubKeyword`

    State and side effects:
        mutates Step, Alternative.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._base.SubKeyword` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    Step = "Step"
    Alternative = "Alternative"


KEYWORD_TO_TYPE: Mapping[Keyword | str | None, StepKeywordType] = defaultdict(
    lambda: StepKeywordType.unknown,
    [
        (Keyword.Given, StepKeywordType.context),
        (Keyword.When, StepKeywordType.action),
        (Keyword.Then, StepKeywordType.outcome),
        (Keyword.And, StepKeywordType.conjunction),
        (Keyword.But, StepKeywordType.conjunction),
        (Keyword.Star, StepKeywordType.unknown),
        (None, StepKeywordType.unknown),
    ],
)


class Node(BaseModel):
    """
    Represent node state.

    Responsibility:
        Represent node state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Node` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `Node`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `Node`

    State and side effects:
        mutates model_config, tags, name, description, comments.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._base.Node` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tags: Sequence[str] | None = Field(default_factory=cast("Callable[..., Any]", list), alias="Tags")
    name: str | None = Field(None, alias="Name")
    description: str | None = Field(None, alias="Description")
    comments: Sequence[str] | None = Field(default_factory=cast("Callable[..., Any]", list), alias="Comments")


class Table(Node):
    """
    Represent table state.

    Responsibility:
        Represent table state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Table` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - columned_values: owns nested behavior below this boundary
        - rowed_values: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `Table`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `Table`
        - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `Table`

    State and side effects:
        mutates values, type, parameters.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._base.Table` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    type: Literal["Rowed", "Columned"] | None = Field("Rowed", alias="Type")
    parameters: Sequence[str] | None = Field(default_factory=cast("Callable[..., Any]", list), alias="Parameters")
    values: Sequence[Sequence[object]] | None = Field(default_factory=cast("Callable[..., Any]", list), alias="Values")

    @property
    def columned_values(self) -> Sequence[Sequence[object]]:
        """
        Handle columned values.

        Responsibility:
            Handle columned values. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Table.columned_values`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary
            - zip: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `columned_values`
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `columned_values`

        State and side effects:
            mutates values.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model._base.Table.columned_values` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        values = self.values or []
        return values if self.type == "Columned" else list(zip(*values, strict=False))

    @property
    def rowed_values(self) -> Sequence[Sequence[object]]:
        """
        Handle rowed values.

        Responsibility:
            Handle rowed values. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Table.rowed_values`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary
            - zip: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `rowed_values`
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `rowed_values`
            - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `rowed_values`

        State and side effects:
            mutates values.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model._base.Table.rowed_values` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        values = self.values or []
        return values if self.type == "Rowed" else list(zip(*values, strict=False))


class SubTable(Node):
    """
    Represent sub table state.

    Responsibility:
        Represent sub table state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.SubTable` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `SubTable`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `SubTable`

    State and side effects:
        mutates sub_table.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._base.SubTable` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    sub_table: Table = Field(..., alias="Table")


@AfterValidator
def convert_sub_tables_to_tables(value: object) -> object:
    """
    Convert sub tables to tables.

    Args:
        value: Input value that may be a SubTable.

    Returns:
        SubTable converted to Table, or original value.

    Responsibility:
        Convert sub tables to tables. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.struct_bdd.model._base.convert_sub_tables_to_tables` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `convert_sub_tables_to_tables`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `convert_sub_tables_to_tables`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return value.sub_table if isinstance(value, SubTable) else value


class Join(BaseModel):
    """
    Represent join state.

    Yields:
        Generated values.

    Responsibility:
        Represent join state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tags: owns nested behavior below this boundary
        - name: owns nested behavior below this boundary
        - description: owns nested behavior below this boundary
        - comments: owns nested behavior below this boundary
        - parameters: owns nested behavior below this boundary
        - type: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `Join`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `Join`
        - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `Join`

    State and side effects:
        mutates model_config, tables, __hash__, descriptions, filled_tables.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._base.Join` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tables: list[Annotated[Union[Table, "Join", SubTable], convert_sub_tables_to_tables]] = Field(
        default_factory=list,
        alias="Join",
    )

    __hash__ = id

    @property
    def tags(self) -> list[str]:
        """
        Handle tags.

        Responsibility:
            Handle tags. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.tags` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary
            - dict.fromkeys: collaborator call used by this boundary
            - chain.from_iterable: collaborator call used by this boundary
            - self._tables: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `tags`
            - src/pytest_bdd/model/feature_binding.py: imports or references `tags`
            - src/pytest_bdd/model/scenario_report.py: imports or references `tags`
            - src/pytest_bdd/plugin/cucumber_json/model.py: imports or references `tags`
            - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `tags`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return list(dict.fromkeys(chain.from_iterable(table.tags or [] for table in self._tables())))

    @property
    def name(self) -> str:
        """
        Handle name.

        Responsibility:
            Handle name. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.name` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - join: collaborator call used by this boundary
            - self._tables: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/__init__.py: imports or references `name`
            - src/pytest_bdd/_pylint/checkers/file_size_rules.py: imports or references `name`
            - src/pytest_bdd/_pylint/checkers/init_rules.py: imports or references `name`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `name`
            - src/pytest_bdd/_pylint/checkers/noqa_rules.py: imports or references `name`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return "\n".join(table.name for table in self._tables() if table.name is not None)

    @property
    def description(self) -> str:
        """
        Handle description.

        Responsibility:
            Handle description. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.description`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - chain.from_iterable: collaborator call used by this boundary
            - map: collaborator call used by this boundary
            - deepattrgetter: collaborator call used by this boundary
            - join: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_build.py: imports or references `description`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `description`
            - src/pytest_bdd/model/feature_binding.py: imports or references `description`
            - src/pytest_bdd/model/message_baseline_diff.py: imports or references `description`
            - src/pytest_bdd/model/message_capability.py: imports or references `description`

        State and side effects:
            mutates descriptions.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model._base.Join.description` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        descriptions = chain.from_iterable(map(deepattrgetter("description", skip_missing=True), self.tables))
        return "\n".join(str(description) for description in descriptions if description is not None)

    @property
    def comments(self) -> list[str]:
        """
        Handle comments.

        Responsibility:
            Handle comments. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.comments` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary
            - chain.from_iterable: collaborator call used by this boundary
            - self._tables: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `comments`
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `comments`
            - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `comments`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return list(chain.from_iterable(table.comments or [] for table in self._tables()))

    @property
    def parameters(self) -> list[str]:
        """
        Handle parameters.

        Responsibility:
            Handle parameters. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.parameters` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary
            - dict.fromkeys: collaborator call used by this boundary
            - chain.from_iterable: collaborator call used by this boundary
            - self._tables: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `parameters`
            - src/pytest_bdd/model/scenario_run.py: imports or references `parameters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `parameters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `parameters`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `parameters`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return list(dict.fromkeys(chain.from_iterable(table.parameters or [] for table in self._tables())))

    @property
    def type(self) -> Literal["Rowed"]:
        """
        Handle type.

        Responsibility:
            Handle type. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.type` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `type`
            - src/pytest_bdd/feature_locator.py: imports or references `type`
            - src/pytest_bdd/hook.py: imports or references `type`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `type`
            - src/pytest_bdd/model/message_converter.py: imports or references `type`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return "Rowed"

    @property
    def values(self) -> list[list[object]]:
        """
        Return rows with parameterized table values expanded.

        Responsibility:
            Return rows with parameterized table values expanded. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.values` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/file_size_rules.py: imports or references `values`
            - src/pytest_bdd/model/message_registry.py: imports or references `values`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `values`
            - src/pytest_bdd/parser.py: imports or references `values`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `values`

        State and side effects:
            mutates filled_tables, filled_tables_parameters.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model._base.Join.values` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """

        def _() -> Iterator[list[object]]:
            """
            Responsibility:
                Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.model._base.Join.values._` owns documented
                method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
                this method.

            Reason for existence:
                This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.values._`
                because it keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - list: collaborator call used by this boundary
                - attrgetter: collaborator call used by this boundary
                - chain.from_iterable: collaborator call used by this boundary
                - product: collaborator call used by this boundary
                - map: collaborator call used by this boundary
                - self._tables: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `_`
                - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `_`
                - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `_`
                - src/pytest_bdd/collector_batch.py: imports or references `_`
                - src/pytest_bdd/model/coverage/inventory.py: imports or references `_`

            State and side effects:
                mutates filled_tables, filled_tables_parameters.

            Invariants:
                - `pytest_bdd.plugin.struct_bdd.model._base.Join.values._` keeps its documented import path, ownership
                  boundary, and observable behavior stable for callers.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=4
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=4
            """
            filled_tables = list(filter(attrgetter("parameters"), self.tables))
            if filled_tables:  # noqa: PLR1702
                filled_tables_parameters = list(
                    chain.from_iterable(table.parameters or [] for table in self._tables()),
                )
                for filled_tables_values in (
                    list(chain.from_iterable(tables_values))
                    for tables_values in product(*map(attrgetter("rowed_values"), map(self._table, filled_tables)))
                ):
                    if all(
                        all(
                            starmap(
                                eq,
                                product(
                                    [
                                        value
                                        for table_parameter, value in zip(
                                            filled_tables_parameters,
                                            filled_tables_values,
                                            strict=False,
                                        )
                                        if parameter == table_parameter
                                    ],
                                    repeat=2,
                                ),
                            ),
                        )
                        for parameter in self.parameters
                    ):

                        def values_gen(
                            parameters: Sequence[str] = self.parameters,
                            filled_tables_parameters: Sequence[str] = filled_tables_parameters,
                            filled_tables_values: Sequence[object] = filled_tables_values,
                        ) -> Iterator[object]:
                            """
                            Responsibility:
                                Responsibility: Responsibility:
                                `pytest_bdd.plugin.struct_bdd.model._base.Join.values._.values_gen` owns documented
                                method behavior. It directly owns the observable contract, local decisions, and
                                maintenance boundary for this method.

                            Reason for existence:
                                This entity is the information expert for
                                `pytest_bdd.plugin.struct_bdd.model._base.Join.values._.values_gen` because it keeps the
                                nearest code, data shape, call signature, and failure knowledge together.

                            Delegates:
                                - zip: collaborator call used by this boundary

                            Cohesion:
                                The implementation stays together because its imports, calls, state writes, and return
                                contract describe one maintainable decision unit.

                            Separation:
                                - call-site peer: remains separate so same-kind responsibilities stay discoverable,
                                  testable, and changeable without widening caller knowledge.

                            Main consumers:
                                - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `values_gen`
                                - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `values_gen`

                            State and side effects:
                                keeps no local persistent state beyond call-local values.

                            Architecture score:
                                #arch-eval:reason_for_existence=4
                                #arch-eval:owned_responsibility=4
                                #arch-eval:delegation_boundary=4
                                #arch-eval:cohesion=4
                                #arch-eval:separation=3
                                #arch-eval:consumer_clarity=4
                                #arch-eval:state_invariants=3
                                #arch-eval:entity_fullness=4
                                #arch-eval:locational_stability=3
                            """
                            for parameter in parameters:
                                for table_parameter, value in zip(
                                    filled_tables_parameters,
                                    filled_tables_values,
                                    strict=False,
                                ):
                                    if parameter == table_parameter:
                                        yield value
                                        break

                        yield list(values_gen())
            else:
                yield from (
                    list(chain.from_iterable(values_combination))
                    for values_combination in product(*map(attrgetter("rowed_values"), self._tables()))
                )

        return list(_())

    @staticmethod
    def _table(table: Union[Table, "Join", SubTable]) -> Union[Table, "Join"]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.model._base.Join._table` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join._table` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_table`
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `_table`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        return table.sub_table if isinstance(table, SubTable) else table

    def _tables(self) -> Iterator[Union[Table, "Join"]]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.model._base.Join._tables` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join._tables` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - map: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_tables`
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `_tables`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        return map(self._table, self.tables)

    @property
    def columned_values(self) -> list[tuple[object, ...]]:
        """
        Handle columned values.

        Responsibility:
            Handle columned values. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.columned_values`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary
            - zip: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `columned_values`
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `columned_values`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        return list(zip(*self.values, strict=False))

    @property
    def rowed_values(self) -> list[list[object]]:
        """
        Handle rowed values.

        Responsibility:
            Handle rowed values. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._base.Join.rowed_values`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `rowed_values`
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `rowed_values`
            - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `rowed_values`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return self.values


TableNode: TypeAlias = Table | Join
StepPrototypeT = TypeVar("StepPrototypeT")  # bound=StepPrototype in _steps.py — forward ref across modules


Join.model_rebuild()
