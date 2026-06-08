"""
Provide the base scenario locator types and mixin.

Responsibility:
    Provide the base scenario locator types and mixin. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.scenario_locator.base` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - ScenarioLocatorFeatureResolver: owns nested behavior below this boundary
    - ScenarioLocatorReadObserver: owns nested behavior below this boundary
    - ScenarioLocatorResolver: owns nested behavior below this boundary
    - ScenarioLocatorHookProtocol: owns nested behavior below this boundary
    - ScenarioLocatorFilterMixin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/scenario_locator/facade.py: imports or references `base`
    - src/pytest_bdd/script/message_capability_governance/schema.py: imports or references `base`

State and side effects:
    mutates binding, ScenarioLocatorFilterT, filter_, run; depends on __future__.annotations, collections.abc.Callable,
    collections.abc.Iterable, collections.abc.Iterator, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.scenario_locator.base` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import TYPE_CHECKING, Protocol, TypeAlias, runtime_checkable

from attrs import define, field
from cucumber_messages import GherkinDocument, Pickle, Source

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.model.run import Run
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import IdGenerator

if TYPE_CHECKING:
    from enum import Enum
    from pathlib import Path

    from pytest_bdd.compatibility.parser import ParsedFeature, ParserProtocol
    from pytest_bdd.mimetype import Mimetype
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding


@runtime_checkable
class ScenarioLocatorFeatureResolver(Protocol):
    """
    Register locator feature resolver.

    Responsibility:
        Register locator feature resolver. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.base.ScenarioLocatorFeatureResolver`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - resolve_features: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `ScenarioLocatorFeatureResolver`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.scenario_locator.base.ScenarioLocatorFeatureResolver` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    def resolve_features(
        self,
        config: Config | HasPytestStash,
    ) -> Iterable[tuple[ParsedFeature, Source]]:  # pragma: no cover
        """
        Resolve features.

        Responsibility:
            Resolve features. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorFeatureResolver.resolve_features` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `resolve_features`

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
            #arch-eval:locational_stability=3
        """
        ...


@runtime_checkable
class ScenarioLocatorReadObserver(Protocol):
    """
    Register locator read observer.

    Responsibility:
        Register locator read observer. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.base.ScenarioLocatorReadObserver` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - on_source_loaded: owns nested behavior below this boundary
        - on_feature_loaded: owns nested behavior below this boundary
        - on_pickle_loaded: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `ScenarioLocatorReadObserver`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.scenario_locator.base.ScenarioLocatorReadObserver` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    def on_source_loaded(self, gherkin_document: GherkinDocument, source: Source) -> None:  # pragma: no cover
        """
        Handle on source loaded.

        Responsibility:
            Handle on source loaded. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorReadObserver.on_source_loaded` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `on_source_loaded`

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
            #arch-eval:locational_stability=3
        """
        ...

    def on_feature_loaded(self, gherkin_document: GherkinDocument) -> None:  # pragma: no cover
        """
        Handle on feature loaded.

        Responsibility:
            Handle on feature loaded. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorReadObserver.on_feature_loaded` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `on_feature_loaded`

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
            #arch-eval:locational_stability=3
        """
        ...

    def on_pickle_loaded(self, gherkin_document: GherkinDocument, pickle: Pickle) -> None:  # pragma: no cover
        """
        Handle on pickle loaded.

        Responsibility:
            Handle on pickle loaded. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorReadObserver.on_pickle_loaded` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `on_pickle_loaded`

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
            #arch-eval:locational_stability=3
        """
        ...


@runtime_checkable
class ScenarioLocatorResolver(Protocol):
    """
    Register locator resolver.

    Responsibility:
        Register locator resolver. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.base.ScenarioLocatorResolver` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - resolve: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `ScenarioLocatorResolver`
        - src/pytest_bdd/scenario_locator/__init__.py: imports or references `ScenarioLocatorResolver`
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `ScenarioLocatorResolver`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.scenario_locator.base.ScenarioLocatorResolver` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def resolve(
        self,
        config: Config | HasPytestStash,
        *,
        observer: ScenarioLocatorReadObserver | None = None,
    ) -> Iterable[tuple[GherkinDocument, Pickle, Source]]:  # pragma: no cover
        """
        Resolve resolve.

        Responsibility:
            Resolve resolve. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.scenario_locator.base.ScenarioLocatorResolver.resolve`
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
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `resolve`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `resolve`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `resolve`
            - src/pytest_bdd/compatibility/path.py: imports or references `resolve`
            - src/pytest_bdd/feature_locator.py: imports or references `resolve`

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
        ...


class ScenarioLocatorHookProtocol(Protocol):
    """
    Register locator hook protocol.

    Responsibility:
        Register locator hook protocol. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.base.ScenarioLocatorHookProtocol` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_get_mimetype: owns nested behavior below this boundary
        - pytest_bdd_get_parser: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `ScenarioLocatorHookProtocol`
        - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `ScenarioLocatorHookProtocol`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.scenario_locator.base.ScenarioLocatorHookProtocol` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    def pytest_bdd_get_mimetype(self, *, config: Config, path: Path) -> Mimetype | str | Enum | None:
        """
        Handle bdd get mimetype.

        Responsibility:
            Handle bdd get mimetype. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorHookProtocol.pytest_bdd_get_mimetype` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `pytest_bdd_get_mimetype`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pytest_bdd_get_mimetype`

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
            #arch-eval:locational_stability=3
        """
        ...

    def pytest_bdd_get_parser(
        self,
        *,
        config: Config | HasPytestStash,
        mimetype: Mimetype,
    ) -> type[ParserProtocol] | None:
        """
        Handle bdd get parser.

        Responsibility:
            Handle bdd get parser. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorHookProtocol.pytest_bdd_get_parser` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `pytest_bdd_get_parser`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pytest_bdd_get_parser`
            - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `pytest_bdd_get_parser`

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
        ...


ScenarioLocatorFilterT: TypeAlias = Callable[[Config | HasPytestStash, GherkinDocument, Pickle], bool]


@define
class ScenarioLocatorFilterMixin(ScenarioLocatorFeatureResolver, ScenarioLocatorResolver):
    """
    Register locator filter mixin.

    Yields:
        Generated values.

    Responsibility:
        Register locator filter mixin. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - filter_scenarios: owns nested behavior below this boundary
        - _bind_feature: owns nested behavior below this boundary
        - resolve: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `ScenarioLocatorFilterMixin`
        - src/pytest_bdd/scenario_locator/__init__.py: imports or references `ScenarioLocatorFilterMixin`
        - src/pytest_bdd/scenario_locator/facade.py: imports or references `ScenarioLocatorFilterMixin`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `ScenarioLocatorFilterMixin`
        - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `ScenarioLocatorFilterMixin`

    State and side effects:
        mutates binding, filter_, run.

    Invariants:
        - `pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    filter_: ScenarioLocatorFilterT | None = field(default=None, kw_only=True)

    def filter_scenarios(
        self,
        gherkin_document: GherkinDocument,
        pickles: Iterable[Pickle],
        config: Config | HasPytestStash,
    ) -> Iterable[tuple[GherkinDocument, Pickle]]:
        """
        Filter scenarios based on filter criteria.

        Args:
            gherkin_document: Parsed Gherkin document.
            pickles: List of pickle scenarios.
            config: Pytest config.

        Returns:
            Filtered tuples of (document, pickle).

        Responsibility:
            Filter scenarios based on filter criteria. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin.filter_scenarios` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.filter_: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `filter_scenarios`

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
        return (
            (gherkin_document, pickle)
            for pickle in pickles
            if self.filter_ is None or self.filter_(config, gherkin_document, pickle)
        )

    @staticmethod
    def _bind_feature(
        parsed: ParsedFeature,
        source: Source,
        config: Config | HasPytestStash,
    ) -> FeatureRuntimeBinding:
        """
        Bind a Gherkin document to the runtime.

        Args:
            parsed: Parsed feature with gherkin document, filename, and raw data.
            source: Feature source information.
            config: Pytest config.

        Returns:
            Feature runtime binding.

        Responsibility:
            Bind a Gherkin document to the runtime. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin._bind_feature` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Run.from_stash: collaborator call used by this boundary
            - run.ensure_feature_binding: collaborator call used by this boundary
            - binding.ensure_pickles: collaborator call used by this boundary
            - IdGenerator.from_stash: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/facade.py: imports or references `_bind_feature`

        State and side effects:
            mutates run, binding.

        Invariants:
            - `pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin._bind_feature` keeps its documented import
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
            #arch-eval:locational_stability=3

        """
        run = Run.from_stash(config.stash)
        binding = run.ensure_feature_binding(
            gherkin_document=parsed.gherkin_document,
            source=source,
            filename=parsed.filename,
        )
        binding.ensure_pickles(id_generator=IdGenerator.from_stash(config.stash))
        return binding

    def resolve(
        self,
        config: Config | HasPytestStash,
        *,
        observer: ScenarioLocatorReadObserver | None = None,
    ) -> Iterator[tuple[GherkinDocument, Pickle, Source]]:
        """
        Resolve resolve.

        Yields:
            Generated values.

        Responsibility:
            Resolve resolve. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin.resolve` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.resolve_features: collaborator call used by this boundary
            - self._bind_feature: collaborator call used by this boundary
            - observer.on_source_loaded: collaborator call used by this boundary
            - observer.on_feature_loaded: collaborator call used by this boundary
            - self.filter_scenarios: collaborator call used by this boundary
            - observer.on_pickle_loaded: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `resolve`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `resolve`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `resolve`
            - src/pytest_bdd/compatibility/path.py: imports or references `resolve`
            - src/pytest_bdd/feature_locator.py: imports or references `resolve`

        State and side effects:
            mutates binding.

        Invariants:
            - `pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin.resolve` keeps its documented import path,
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
            #arch-eval:locational_stability=4

        """
        for parsed, feature_source in self.resolve_features(config):
            binding = self._bind_feature(parsed, feature_source, config)
            if observer is not None:
                observer.on_source_loaded(parsed.gherkin_document, feature_source)
                observer.on_feature_loaded(parsed.gherkin_document)
            for _, pickle in self.filter_scenarios(parsed.gherkin_document, binding.pickles, config):
                if observer is not None:
                    observer.on_pickle_loaded(parsed.gherkin_document, pickle)
                yield parsed.gherkin_document, pickle, feature_source
