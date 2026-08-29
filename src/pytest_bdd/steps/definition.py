from __future__ import annotations

from collections.abc import Collection, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

from attrs import define, field

import messages
from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.steps.types import (
    ConverterT,
    ParamsFixturesMapping,
    StepFunc,
    _resolve_callable_source_location,
)
from pytest_bdd.utils import IdGenerator, getitemdefault

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from pytest_bdd.compatibility.pytest import Config, FixtureRequest
    from pytest_bdd.model.step import Step, StepType
    from pytest_bdd.parsers.base import StepParser
    from pytest_bdd.types.protocol import HasPytestStash


@define(eq=False)
class Definition:
    func: StepFunc
    type_: str | StepType | None
    parser: StepParser
    anonymous_group_names: Iterable[str] | None
    converters: Mapping[str, ConverterT]
    params_fixtures_mapping: ParamsFixturesMapping
    param_defaults: Mapping[str, object]
    target_fixtures: Sequence[str]
    liberal: bool | None
    not_implemented: bool = False
    tolerant: bool = False
    id: str = field(init=False)
    __cache: dict[int, messages.StepDefinition] = field(factory=dict)

    @property
    def fixtures_mapped_from_step_definition(self) -> set[str]:
        known = set(self.parser.arguments) if self.anonymous_group_names is None else set(self.anonymous_group_names)
        fixtures = {*self.target_fixtures}
        if isinstance(self.params_fixtures_mapping, Mapping):
            fixtures.update(fn for fn in self.params_fixtures_mapping.values() if isinstance(fn, str))
            wildcard, conv = (
                getitemdefault(self.params_fixtures_mapping, ..., default=...),
                {p for p in self.params_fixtures_mapping if isinstance(p, str)},
            )
        elif isinstance(self.params_fixtures_mapping, Collection):
            conv, wildcard = set(), None
            fixtures.update(self.params_fixtures_mapping)
        else:
            conv, wildcard = set(), ... if bool(self.params_fixtures_mapping) else None
        if wildcard is ...:
            fixtures.update(known.difference(conv))
        return fixtures

    def as_message(self, config: Config | HasPytestStash) -> messages.StepDefinition:
        id_gen = IdGenerator.from_stash(config.stash)
        if id(id_gen) in self.__cache:
            return self.__cache[id(id_gen)]
        self.id = id_gen.get_next_id()
        pet = self.parser.type
        expr_type = pet if isinstance(pet, StepDefinitionPatternType) else StepDefinitionPatternType(str(pet))
        src_file, src_line = _resolve_callable_source_location(self.func)
        fn = str(self.func.__name__)
        msg = self.__cache[id(id_gen)] = messages.StepDefinition(
            id=self.id,
            pattern=messages.StepDefinitionPattern(source=str(self.parser), type=expr_type),
            source_reference=messages.SourceReference(
                uri=Path(resolvepath(src_file, getattr(config, "rootpath", Path.cwd()))).as_uri(),
                location=messages.Location(line=src_line, column=1),
                java_method=messages.JavaMethod(
                    class_name="pytest_bdd.steps.StepDefinition", method_name=fn, method_parameter_types=[]
                ),
                java_stack_trace_element=messages.JavaStackTraceElement(
                    class_name="pytest_bdd.steps.StepDefinition", file_name=Path(src_file).name, method_name=fn
                ),
            ),
        )
        return msg

    def get_parameters(self, request: FixtureRequest, step: Step | messages.PickleStep) -> dict[str, object]:
        step_text = getattr(step, "text", getattr(step, "name", ""))
        parsed = self.parser.parse_arguments(request, step_text, anonymous_group_names=self.anonymous_group_names) or {}
        return {**self.param_defaults, **{k: self.converters.get(k, lambda v: v)(v) for k, v in parsed.items()}}


StepDefinitionAlias: TypeAlias = Definition

__all__ = ["Definition", "StepDefinitionAlias"]
