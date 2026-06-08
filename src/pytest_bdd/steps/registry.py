"""
Step definition registry with parent chain and fixture injection.

Responsibility:
    Step definition registry with parent chain and fixture injection. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.steps.registry` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - StepProtocol: owns nested behavior below this boundary
    - StepRegistryProtocol: owns nested behavior below this boundary
    - Registry: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/execution_message_adapter.py: imports or references `registry`
    - src/pytest_bdd/model/message_registry.py: imports or references `registry`
    - src/pytest_bdd/model/message_schema_validation.py: imports or references `registry`
    - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `registry`
    - src/pytest_bdd/steps/__init__.py: imports or references `registry`

State and side effects:
    mutates __pytest_bdd_step_definitions__, __pytest_bdd_step_registry__, namespace, _definitions, parent; depends on
    __future__.annotations, collections.abc.Callable, collections.abc.Iterator, functools.cached_property,
    typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.steps.registry` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

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

from __future__ import annotations

from collections.abc import Callable, Iterator  # noqa: TC003
from functools import cached_property
from typing import TYPE_CHECKING, cast

import pytest
from attrs import define, field
from ordered_set import OrderedSet
from typing_extensions import Protocol, runtime_checkable

from pytest_bdd.util.toolz_extra import setdefaultattr

if TYPE_CHECKING:
    from pytest_bdd.steps.definition import Definition


@runtime_checkable
class StepProtocol(Protocol):
    """
    Protocol for callables carrying pytest-bdd step definitions.

    Responsibility:
        Protocol for callables carrying pytest-bdd step definitions. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.registry.StepProtocol` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/steps/__init__.py: imports or references `StepProtocol`
        - src/pytest_bdd/steps/manager.py: imports or references `StepProtocol`
        - src/pytest_bdd/steps/matcher.py: imports or references `StepProtocol`

    State and side effects:
        mutates __pytest_bdd_step_definitions__.

    Invariants:
        - `pytest_bdd.steps.registry.StepProtocol` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    __pytest_bdd_step_definitions__: set[Definition]


@runtime_checkable
class StepRegistryProtocol(Protocol):
    """
    Protocol for objects carrying a namespace step registry.

    Responsibility:
        Protocol for objects carrying a namespace step registry. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.registry.StepRegistryProtocol` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `StepRegistryProtocol`
        - src/pytest_bdd/steps/__init__.py: imports or references `StepRegistryProtocol`
        - src/pytest_bdd/steps/manager.py: imports or references `StepRegistryProtocol`
        - src/pytest_bdd/steps/matcher.py: imports or references `StepRegistryProtocol`

    State and side effects:
        mutates __pytest_bdd_step_registry__.

    Invariants:
        - `pytest_bdd.steps.registry.StepRegistryProtocol` keeps its documented import path, ownership boundary, and
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
        #arch-eval:locational_stability=4
    """

    __pytest_bdd_step_registry__: Registry


@define
class Registry:
    """
    Collection of step definitions with optional parent registry.

    Responsibility:
        Collection of step definitions with optional parent registry. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.registry.Registry` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - registry: owns nested behavior below this boundary
        - inject_registry_fixture: owns nested behavior below this boundary
        - fixture: owns nested behavior below this boundary
        - __iter__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `Registry`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `Registry`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Registry`
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `Registry`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `Registry`

    State and side effects:
        mutates namespace, _definitions, parent, step_containers, step_definition_registry.

    Invariants:
        - `pytest_bdd.steps.registry.Registry` keeps its documented import path, ownership boundary, and observable
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
        #arch-eval:locational_stability=4
    """

    namespace: StepRegistryProtocol | None = field(default=None)
    _definitions: OrderedSet[Definition] | None = field(default=None, alias="definitions")
    parent: Registry | None = field(default=None, init=False)

    @cached_property
    def registry(self) -> OrderedSet[Definition]:
        """
        Return the set of step definitions discovered from the namespace.

        Responsibility:
            Return the set of step definitions discovered from the namespace. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.registry.Registry.registry` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - OrderedSet: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - dir: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/execution_message_adapter.py: imports or references `registry`
            - src/pytest_bdd/model/message_registry.py: imports or references `registry`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `registry`
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `registry`
            - src/pytest_bdd/steps/__init__.py: imports or references `registry`

        State and side effects:
            mutates step_containers.

        Invariants:
            - `pytest_bdd.steps.registry.Registry.registry` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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
        if self._definitions is not None:
            return self._definitions

        if self.namespace is None:
            return OrderedSet()

        step_containers: list[StepProtocol] = [
            value
            for value in [getattr(self.namespace, attr) for attr in dir(self.namespace)]
            if isinstance(value, StepProtocol)
        ]

        return OrderedSet(
            [
                step_definition
                for step_container in step_containers
                for step_definition in step_container.__pytest_bdd_step_definitions__
            ],
        )

    @classmethod
    def inject_registry_fixture(
        cls,
        namespace: StepRegistryProtocol,
    ) -> None:
        """
        Inject registry fixture and register steps from namespace.

        Responsibility:
            Inject registry fixture and register steps from namespace. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.registry.Registry.inject_registry_fixture`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - setdefaultattr: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - Registry: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `inject_registry_fixture`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `inject_registry_fixture`
            - src/pytest_bdd/steps/__init__.py: imports or references `inject_registry_fixture`
            - src/pytest_bdd/steps/manager.py: imports or references `inject_registry_fixture`
            - src/pytest_bdd/steps/matcher.py: imports or references `inject_registry_fixture`

        State and side effects:
            mutates step_definition_registry.

        Invariants:
            - `pytest_bdd.steps.registry.Registry.inject_registry_fixture` keeps its documented import path, ownership
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
        step_definition_registry = cast(
            "Registry",
            setdefaultattr(
                namespace,
                "__pytest_bdd_step_registry__",
                value_factory=lambda: Registry(namespace),
            ),
        )
        setdefaultattr(namespace, "step_registry", step_definition_registry.fixture)

    @property
    def fixture(self) -> Callable[[Registry], Registry]:
        """
        Build the fixture that links a registry to its parent.

        Responsibility:
            Build the fixture that links a registry to its parent. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.registry.Registry.fixture` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - step_registry: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `fixture`
            - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `fixture`
            - src/pytest_bdd/steps/__init__.py: imports or references `fixture`
            - src/pytest_bdd/steps/manager.py: imports or references `fixture`
            - src/pytest_bdd/steps/matcher.py: imports or references `fixture`

        State and side effects:
            mutates self.parent, cast.__pytest_bdd_step_registry__.

        Invariants:
            - `pytest_bdd.steps.registry.Registry.fixture` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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

        @pytest.fixture
        def step_registry(step_registry: Registry) -> Registry:
            """
            Responsibility:
                Responsibility: Responsibility: `pytest_bdd.steps.registry.Registry.fixture.step_registry` owns
                documented method behavior. It directly owns the observable contract, local decisions, and maintenance
                boundary for this method.

            Reason for existence:
                This entity is the information expert for `pytest_bdd.steps.registry.Registry.fixture.step_registry`
                because it keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - None, leaf-level implementation boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
                  `step_registry`
                - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `step_registry`
                - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `step_registry`
                - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `step_registry`
                - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `step_registry`

            State and side effects:
                mutates self.parent.

            Invariants:
                - `pytest_bdd.steps.registry.Registry.fixture.step_registry` keeps its documented import path, ownership
                  boundary, and observable behavior stable for callers.

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
            self.parent = step_registry
            return self

        cast("StepRegistryProtocol", cast("object", step_registry)).__pytest_bdd_step_registry__ = self
        return cast("Callable[[Registry], Registry]", step_registry)

    def __iter__(self) -> Iterator[Definition]:
        """
        Iterate over registered step definitions.

        Returns:
            Iterator over step definitions.

        Responsibility:
            Iterate over registered step definitions. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.registry.Registry.__iter__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - iter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/steps/__init__.py: imports or references `__iter__`
            - src/pytest_bdd/steps/manager.py: imports or references `__iter__`
            - src/pytest_bdd/steps/matcher.py: imports or references `__iter__`

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
        return iter(self.registry)
