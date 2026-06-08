"""
Provide model builder helpers.

Responsibility:
    Provide model builder helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model_builder` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - _ASTBuilder: owns nested behavior below this boundary
    - GherkinDocumentBuilder: owns nested behavior below this boundary
    - StepToFeatureASTBuilder: owns nested behavior below this boundary
    - ExampleASTBuilder: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `model_builder`

State and side effects:
    mutates model, previous_step_keyword_type, ModelT, comments, gherkin_document; depends on collections.abc.Iterable,
    collections.abc.Iterator, collections.abc.Sequence, operator.attrgetter, typing.Generic.

Invariants:
    - `pytest_bdd.plugin.struct_bdd.model_builder` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

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

from collections.abc import Iterable, Iterator, Sequence
from operator import attrgetter
from typing import Generic, TypeVar, cast

from attrs import define, field
from cucumber_messages import (  # type:ignore[attr-defined]  # upstream library missing type stubs
    Comment,
    DataTable,
    DocString,
    Examples,
    Feature,
    FeatureChild,
    GherkinDocument,
    Location,
    PickleStepType,
    Scenario,
    Step,
    StepKeywordType,
    TableCell,
    TableRow,
    Tag,
)

from .model import Join as StructJoin
from .model import StepPrototype as StructStep
from .model import Table as StructTable

ModelT = TypeVar("ModelT")


@define
class _ASTBuilder(Generic[ModelT]):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.model_builder._ASTBuilder` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model_builder._ASTBuilder` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - build: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_ASTBuilder`

    State and side effects:
        mutates model.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model_builder._ASTBuilder` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    model: ModelT

    def build(self, id_generator: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.struct_bdd.model_builder._ASTBuilder.build` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model_builder._ASTBuilder.build`
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
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `build`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `build`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `build`
            - src/pytest_bdd/steps/manager.py: imports or references `build`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Failure semantics:
            Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        # pragma: no cover
        raise NotImplementedError


@define
class GherkinDocumentBuilder(_ASTBuilder[StructStep]):
    """
    Represent gherkin document builder state.

    Responsibility:
        Represent gherkin document builder state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - build: owns nested behavior below this boundary
        - build_feature: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `GherkinDocumentBuilder`
        - src/pytest_bdd/plugin/struct_bdd/parser.py: imports or references `GherkinDocumentBuilder`

    State and side effects:
        mutates model, comments, gherkin_document, gherkin_document.uri.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    model: StructStep = field()

    def build(self, id_generator: object) -> GherkinDocument:
        """
        Build gherkin document.

        Returns:
            Gherkin document.

        Responsibility:
            Build gherkin document. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder.build` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - Comment: collaborator call used by this boundary
            - Location: collaborator call used by this boundary
            - enumerate: collaborator call used by this boundary
            - GherkinDocument: collaborator call used by this boundary
            - StepToFeatureASTBuilder.build: collaborator call used by this boundary
            - StepToFeatureASTBuilder: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `build`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `build`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `build`
            - src/pytest_bdd/steps/manager.py: imports or references `build`

        State and side effects:
            mutates comments.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder.build` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        comments = [
            Comment(
                location=Location(column=1, line=index + 1),
                text=comment,
            )
            for index, comment in enumerate(self.model.comments or [])
        ]
        return GherkinDocument(
            comments=comments,
            uri=None,
            feature=StepToFeatureASTBuilder(self.model).build(id_generator=id_generator),
        )

    def build_feature(self, filename: str, uri: str | None, id_generator: object) -> GherkinDocument:  # noqa: ARG002
        """
        Build feature with filename and URI.

        Returns:
            Gherkin document with feature.

        Responsibility:
            Build feature with filename and URI. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder.build_feature` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.build: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parser.py: imports or references `build_feature`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `build_feature`
            - src/pytest_bdd/plugin/struct_bdd/parser.py: imports or references `build_feature`

        State and side effects:
            mutates gherkin_document, gherkin_document.uri.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder.build_feature` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        gherkin_document = self.build(id_generator=id_generator)
        gherkin_document.uri = uri
        return gherkin_document


@define
class StepToFeatureASTBuilder(_ASTBuilder[StructStep]):
    """
    Represent step to feature astbuilder state.

    Yields:
        Generated values.

    Responsibility:
        Represent step to feature astbuilder state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - build: owns nested behavior below this boundary
        - _build_children: owns nested behavior below this boundary
        - _step_keyword: owns nested behavior below this boundary
        - _step_action: owns nested behavior below this boundary
        - _build_data_table: owns nested behavior below this boundary
        - _build_data_table_row: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `StepToFeatureASTBuilder`

    State and side effects:
        mutates previous_step_keyword_type, model, step_keyword_type, steps, rows.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    model: StructStep = field()

    def build(self, id_generator: object) -> Feature:
        """
        Build feature AST.

        Returns:
            Feature AST.

        Responsibility:
            Build feature AST. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder.build` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Feature: collaborator call used by this boundary
            - self._build_children: collaborator call used by this boundary
            - Location: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `build`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `build`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `build`
            - src/pytest_bdd/steps/manager.py: imports or references `build`

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
        return Feature(
            children=self._build_children(id_generator=id_generator),
            description=self.model.description or "",
            language="en",
            location=Location(column=1, line=1),
            tags=[],
            name=self.model.name or "",
            keyword="Feature",
        )

    def _build_children(self, id_generator: object) -> list[FeatureChild]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_build_children`

        State and side effects:
            mutates previous_step_keyword_type, step_keyword_type, steps.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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

        def _() -> Iterator[FeatureChild]:
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children._` owns documented
                method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
                this method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children._` because it keeps
                the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - next: collaborator call used by this boundary
                - Location: collaborator call used by this boundary
                - cast: collaborator call used by this boundary
                - self._step_action: collaborator call used by this boundary
                - filter: collaborator call used by this boundary
                - Step: collaborator call used by this boundary

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
                mutates previous_step_keyword_type, step_keyword_type, steps.

            Invariants:
                - `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children._` keeps its
                  documented import path, ownership boundary, and observable behavior stable for callers.

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
            for route in self.model.routes:
                if route.steps:

                    def steps_gen(steps: Iterable[StructStep]) -> Iterator[Step]:
                        """
                        Responsibility:
                            Responsibility: Responsibility:
                            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children._.steps_gen`
                            owns documented method behavior. It directly owns the observable contract, local decisions,
                            and maintenance boundary for this method.

                        Reason for existence:
                            This entity is the information expert for
                            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children._.steps_gen`
                            because it keeps the nearest code, data shape, call signature, and failure knowledge
                            together.

                        Delegates:
                            - Location: collaborator call used by this boundary
                            - Step: collaborator call used by this boundary
                            - next: collaborator call used by this boundary
                            - cast: collaborator call used by this boundary
                            - self._step_keyword: collaborator call used by this boundary
                            - self._step_action: collaborator call used by this boundary

                        Cohesion:
                            The implementation stays together because its imports, calls, state writes, and return
                            contract describe one maintainable decision unit.

                        Separation:
                            - call-site peer: remains separate so same-kind responsibilities stay discoverable,
                              testable, and changeable without widening caller knowledge.

                        Main consumers:
                            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `steps_gen`

                        State and side effects:
                            mutates previous_step_keyword_type, step_keyword_type.

                        Invariants:
                            - `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_children._.steps_gen`
                              keeps its documented import path, ownership boundary, and observable behavior stable for
                              callers.

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
                        previous_step_keyword_type = None
                        for step in steps:
                            step_keyword_type = (
                                previous_step_keyword_type
                                if step.keyword_type is StepKeywordType.conjunction
                                else step.keyword_type
                            )
                            yield Step(
                                id=next(cast("Iterator[str]", id_generator)),
                                keyword=self._step_keyword(step),
                                location=Location(column=1, line=1),
                                text=self._step_action(step),
                                keyword_type=(
                                    step_keyword_type.value
                                    if step_keyword_type is not None
                                    else StepKeywordType.unknown.value
                                ),
                                **self._build_data_table(step, id_generator),
                                **(
                                    {
                                        "doc_string": DocString(
                                            content=step.description,
                                            delimiter="\n",
                                            location=Location(column=1, line=1),
                                        ),
                                    }
                                    if step.description
                                    else {}
                                ),
                            )
                            previous_step_keyword_type = step_keyword_type

                    steps = [*steps_gen(filter(lambda step: self._step_action(step) is not None, route.steps))]

                    yield FeatureChild(
                        scenario=Scenario(
                            description=route.steps[0].description or "",
                            examples=(
                                [ExampleASTBuilder(route.example_table).build(id_generator=id_generator)]
                                if route.example_table.values
                                else []
                            ),
                            id=next(cast("Iterator[str]", id_generator)),
                            keyword="Scenario",
                            location=Location(column=1, line=1),
                            name=next(
                                filter(bool, map(attrgetter("name"), reversed(route.steps))),
                                "",
                            ),
                            tags=[
                                *(
                                    Tag(
                                        id=next(cast("Iterator[str]", id_generator)),
                                        location=Location(column=1, line=1),
                                        name=tag_name,
                                    )
                                    for tag_name in route.tags or []
                                ),
                            ],
                            steps=steps,
                        ),
                    )

        return list(_())

    @staticmethod
    def _step_keyword(step: StructStep) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._step_keyword` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._step_keyword` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py: imports or references `_step_keyword`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_step_keyword`

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
        return step.type if isinstance(step.type, str) else cast("PickleStepType", step.type).value

    @staticmethod
    def _step_action(step: StructStep) -> str | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._step_action` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._step_action` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_step_action`

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
        return cast("str | None", getattr(step, "action", None))

    @staticmethod
    def _build_data_table(step: StructStep, id_generator: object) -> dict[str, DataTable]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_data_table` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_data_table` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - StepToFeatureASTBuilder._build_data_table_row: collaborator call used by this boundary
            - StructJoin: collaborator call used by this boundary
            - DataTable: collaborator call used by this boundary
            - Location: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_build_data_table`

        State and side effects:
            mutates rows.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_data_table` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        rows = [
            row
            for row in (
                StepToFeatureASTBuilder._build_data_table_row(row_values, id_generator)
                for row_values in StructJoin(tables=step.data).rowed_values
            )
            if row is not None
        ]
        return (
            {
                "data_table": DataTable(
                    rows=rows,
                    location=Location(column=1, line=1),  # pydantic v1 compatibility in pydantic v2
                ),  # pydantic v1 compatibility in pydantic v2
            }
            if rows
            else {}
        )

    @staticmethod
    def _build_data_table_row(row_values: Sequence[object], id_generator: object) -> TableRow | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_data_table_row` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_data_table_row` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Location: collaborator call used by this boundary
            - TableCell: collaborator call used by this boundary
            - TableRow: collaborator call used by this boundary
            - next: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `_build_data_table_row`

        State and side effects:
            mutates cells.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model_builder.StepToFeatureASTBuilder._build_data_table_row` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        cells = [
            TableCell(
                location=Location(
                    column=1,
                    line=1,
                ),
                value=parameter,
            )
            for parameter in row_values
        ]
        return (
            TableRow(
                id=next(cast("Iterator[str]", id_generator)),
                location=Location(column=1, line=1),  # pydantic v1 compatibility in pydantic v2
                cells=cells,
            )  # pydantic v1 compatibility in pydantic v2
            if cells
            else None
        )


@define
class ExampleASTBuilder(_ASTBuilder[StructJoin | StructTable]):
    """
    Represent example astbuilder state.

    Responsibility:
        Represent example astbuilder state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model_builder.ExampleASTBuilder` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - build: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `ExampleASTBuilder`

    State and side effects:
        mutates model.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model_builder.ExampleASTBuilder` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    model: StructJoin | StructTable = field()

    def build(self, id_generator: object) -> Examples:
        """
        Build examples AST.

        Returns:
            Examples AST.

        Responsibility:
            Build examples AST. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model_builder.ExampleASTBuilder.build` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - Location: collaborator call used by this boundary
            - next: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - TableRow: collaborator call used by this boundary
            - TableCell: collaborator call used by this boundary
            - Examples: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `build`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `build`
            - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `build`
            - src/pytest_bdd/steps/manager.py: imports or references `build`

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
        return Examples(
            description=self.model.description,
            id=next(cast("Iterator[str]", id_generator)),
            keyword="Examples",
            location=Location(column=1, line=1),
            name=self.model.name,
            table_body=[
                *(
                    TableRow(
                        id=next(cast("Iterator[str]", id_generator)),
                        location=Location(column=1, line=1),
                        cells=[
                            *(
                                TableCell(
                                    location=Location(column=1, line=1),
                                    value=str(parameter),
                                )
                                for parameter in row_values
                            ),
                        ],
                    )
                    for row_values in self.model.rowed_values
                ),
            ],
            tags=[
                *(
                    Tag(
                        id=next(cast("Iterator[str]", id_generator)),
                        location=Location(column=1, line=1),
                        name=tag_name,
                    )
                    for tag_name in self.model.tags or []
                ),
            ],
            table_header=TableRow(
                id=next(cast("Iterator[str]", id_generator)),
                location=Location(column=1, line=1),
                cells=[
                    *(
                        TableCell(
                            location=Location(column=1, line=1),
                            value=parameter,
                        )
                        for parameter in self.model.parameters or []
                    ),
                ],
            ),
        )
