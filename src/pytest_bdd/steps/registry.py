"""Step definition registry with parent chain and fixture injection."""

from __future__ import annotations

from collections.abc import Callable, Iterator  # noqa: TC003
from typing import TYPE_CHECKING, cast

import pytest
from _pytest.fixtures import FixtureRequest  # noqa: TC002
from attrs import define, field
from ordered_set import OrderedSet
from typing_extensions import Protocol, runtime_checkable

from pytest_bdd.compatibility.pytest import FixtureLookupError
from pytest_bdd.util.toolz_extra import setdefaultattr

if TYPE_CHECKING:
    from pytest_bdd.steps.definition import Definition


@runtime_checkable
class StepProtocol(Protocol):
    """Protocol for callables carrying pytest-bdd step definitions."""

    __pytest_bdd_step_definitions__: set[Definition]


@runtime_checkable
class NamespaceStepRegistryProtocol(Protocol):
    """Protocol for objects carrying a namespace step registry."""

    _step_registry: Registry


@define
class Registry:
    """Collection of step definitions with optional parent registry."""

    @runtime_checkable
    class RegistryFixtureProtocol(Protocol):
        """Protocol for fixtures carrying an attached step registry."""

        __pytest_bdd_step_registry__: Registry

    registry: OrderedSet[Definition] = field(factory=OrderedSet)
    parent: Registry | None = field(default=None, init=False)

    @classmethod
    def inject_registry_fixture_and_register_steps(
        cls,
        namespace: NamespaceStepRegistryProtocol,
    ) -> None:
        """Inject registry fixture and register steps from namespace."""
        step_containers: list[StepProtocol] = [
            value for value in namespace.__dict__.values() if isinstance(value, StepProtocol)
        ]

        if not step_containers:
            return

        step_definition_registry = cast(
            "Registry",
            setdefaultattr(
                namespace,
                "_step_registry",
                value_factory=Registry,
            ),
        )
        setdefaultattr(namespace, "step_registry", step_definition_registry.fixture)
        step_definitions: list[Definition] = [
            step_definition
            for step_container in step_containers
            for step_definition in step_container.__pytest_bdd_step_definitions__
        ]
        step_definition_registry.registry.update(step_definitions)

        for fixture_name in (
            fixture_name
            for step_definition in step_definitions
            for fixture_name in step_definition.fixtures_mapped_from_step_definition
        ):

            def build_fixtures_mapped_from_step_definition(
                fixture_name: str = fixture_name,
            ) -> Callable[[FixtureRequest], object | None]:
                @pytest.fixture
                def fixtures_mapped_from_step_definition(request: FixtureRequest) -> object | None:
                    """
                    Map step definition fixture.

                    Returns:
                        Fixture value or None if not found.

                    """

                    def resolve_fixture_value() -> object | None:
                        try:
                            return request.getfixturevalue(fixture_name)
                        except FixtureLookupError:
                            return None

                    return resolve_fixture_value()

                return fixtures_mapped_from_step_definition

            setdefaultattr(namespace, fixture_name, build_fixtures_mapped_from_step_definition())

    @property
    def fixture(self) -> Callable[[Registry], Registry]:
        """Build the fixture that links a registry to its parent."""

        @pytest.fixture
        def step_registry(step_registry: Registry) -> Registry:
            self.parent = step_registry
            return self

        step_registry_typed = cast("Registry.RegistryFixtureProtocol", step_registry)
        step_registry_typed.__pytest_bdd_step_registry__ = self
        return step_registry

    def __iter__(self) -> Iterator[Definition]:
        """
        Iterate over registered step definitions.

        Returns:
            Iterator over step definitions.

        """
        return iter(self.registry)
