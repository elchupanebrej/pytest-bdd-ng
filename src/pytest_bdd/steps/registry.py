from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, cast, runtime_checkable

import pytest
from attrs import define, field
from ordered_set import OrderedSet
from typing_extensions import Protocol

from pytest_bdd.utils import setdefaultattr

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from pytest_bdd.steps.definition import Definition


@runtime_checkable
class StepProtocol(Protocol):
    __pytest_bdd_step_definitions__: set[Definition]


@runtime_checkable
class StepRegistryProtocol(Protocol):
    __pytest_bdd_step_registry__: Registry


@define
class Registry:
    namespace: StepRegistryProtocol | None = field(default=None)
    _definitions: OrderedSet[Definition] | None = field(default=None, alias="definitions")
    parent: Registry | None = field(default=None, init=False)

    @cached_property
    def registry(self) -> OrderedSet[Definition]:
        if self._definitions is not None:
            return self._definitions

        if self.namespace is None:
            return OrderedSet()

        step_containers: list[StepProtocol] = []
        for attr in dir(self.namespace):
            try:
                value = getattr(self.namespace, attr)
            except Exception:  # noqa: S112
                continue
            if isinstance(value, StepProtocol) and hasattr(value, "__pytest_bdd_step_definitions__"):
                step_containers.append(value)

        discovered_definitions: list[Definition] = []
        for step_container in step_containers:
            raw_definitions = getattr(step_container, "__pytest_bdd_step_definitions__", ())
            if isinstance(raw_definitions, set | list | tuple | OrderedSet):
                discovered_definitions.extend(raw_definitions)

        return OrderedSet(discovered_definitions)

    @classmethod
    def inject_registry_fixture(cls, namespace: StepRegistryProtocol) -> None:
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
        @pytest.fixture
        def step_registry(step_registry: Registry) -> Registry:
            self.parent = step_registry
            return self

        cast("StepRegistryProtocol", cast("object", step_registry)).__pytest_bdd_step_registry__ = self
        return cast("Callable[[Registry], Registry]", step_registry)

    def __iter__(self) -> Iterator[Definition]:
        return iter(self.registry)
