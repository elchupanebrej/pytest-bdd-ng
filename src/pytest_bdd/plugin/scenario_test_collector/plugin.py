"""
Provide plugin helpers.

Responsibility:
    Provide plugin helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.scenario_test_collector.plugin` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _pytest_collect_file: owns nested behavior below this boundary
    - _pytest_pycollect_makemodule: owns nested behavior below this boundary
    - _ScenarioCollectionReadObserver: owns nested behavior below this boundary
    - _ScenarioLocatorProtocol: owns nested behavior below this boundary
    - _CollectionFixtureRequest: owns nested behavior below this boundary
    - _iter_resolved_feature_scenarios: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/exception.py: imports or references `plugin`
    - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `plugin`
    - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `plugin`
    - src/pytest_bdd/script/render_cucumber_formatters.py: imports or references `plugin`

State and side effects:
    mutates config, msg, gherkin_document, pickle, step_registry; depends on mimetypes, collections.abc.Collection,
    collections.abc.Iterator, collections.abc.Sequence, contextlib.suppress.

Invariants:
    - `pytest_bdd.plugin.scenario_test_collector.plugin` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises LookupError, pytest.UsageError; callers must treat these as boundary failures.

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

import mimetypes
from collections.abc import Collection, Iterator, Sequence
from contextlib import suppress
from functools import partial
from itertools import starmap
from operator import contains
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Protocol, cast
from unittest.mock import patch

import pytest
from attrs import define
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from cucumber_messages import (  # upstream library missing type stubs
    GherkinDocument,
    Pickle,
    Source,
)

from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector
from pytest_bdd.collector import Module as ModuleCollector
from pytest_bdd.collector_batch import FeatureBatchParser
from pytest_bdd.compatibility.pytest import (
    Collector,
    Config,
    FixtureRequest,
    Item,
    Mark,
    MarkDecorator,
    Metafunc,
)
from pytest_bdd.feature_locator import ScenarioLocatorBuilder
from pytest_bdd.mimetype import Mimetype, gherkin_suffixes, link_suffixes
from pytest_bdd.model.run import Run
from pytest_bdd.model.run_access import (
    require_feature_object,
    require_pickle_object,
    require_step_object,
    resolve_previous_step_object,
)
from pytest_bdd.model.scenario_collection import (
    PYTEST_BDD_MARK,
    PYTEST_BDD_SCENARIOS_MARK,
    FeatureAutoLoad,
)
from pytest_bdd.parser import (  # type: ignore[attr-defined]  # re-exported from compatibility module
    GherkinParser,
    MarkdownGherkinParser,
    ParserProtocol,
)
from pytest_bdd.plugin.scenario_test_collector._helpers import (
    _allow_empty_scenarios,
    _build_collection_step_registry,
    _build_pickle_param,
    _format_zero_match_step,
    _is_feature_autoload_item,
    _scenario_has_step_match,
)
from pytest_bdd.steps import (
    Definition,
    Matcher,
    Registry,
)
from pytest_bdd.util.toolz_extra import chain_map

if TYPE_CHECKING:
    from pytest_bdd.steps import StepRegistryProtocol


def _pytest_collect_file(parent: Collector, file_path: Path | str | None = None) -> Collector | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector.plugin._pytest_collect_file` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin._pytest_collect_file` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary
        - ScenarioTestCollector.is_enabled: collaborator call used by this boundary
        - hook.pytest_bdd_is_collectible: collaborator call used by this boundary
        - FeatureBatchParser.find_in_stash.value_or: collaborator call used by this boundary
        - FeatureBatchParser.find_in_stash: collaborator call used by this boundary
        - batch_parser.register: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `_pytest_collect_file`

    State and side effects:
        mutates file_path, config, hook, batch_parser.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin._pytest_collect_file` keeps its documented import path,
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
    if not ScenarioTestCollector.is_enabled(parent.session.config):
        return None
    if file_path is None:
        return None

    file_path = Path(file_path)
    config = parent.config
    hook = parent.config.hook

    if hook.pytest_bdd_is_collectible(config=config, path=Path(file_path)):
        batch_parser = FeatureBatchParser.find_in_stash(config.stash).value_or(None)
        if batch_parser is not None:
            batch_parser.register(Path(file_path))
        return FeatureFileCollector.build(parent=parent, file_path=file_path)  # type: ignore[return-value]  # FeatureFileCollector extends Module
    return None


def _pytest_pycollect_makemodule() -> Iterator[None]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector.plugin._pytest_pycollect_makemodule`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin._pytest_pycollect_makemodule` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - patch: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
          `_pytest_pycollect_makemodule`
        - src/pytest_bdd/plugin/struct_bdd/plugin.py: imports or references `_pytest_pycollect_makemodule`

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
    with patch("_pytest.python.Module", new=ModuleCollector):
        yield


@define(kw_only=True)
class _ScenarioCollectionReadObserver:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

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
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
          `_ScenarioCollectionReadObserver`

    State and side effects:
        mutates config.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    config: Config

    def on_source_loaded(self, gherkin_document: GherkinDocument, source: Source) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver.on_source_loaded` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver.on_source_loaded` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.config.hook.pytest_bdd_source_read: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `on_source_loaded`
            - src/pytest_bdd/scenario_locator/base.py: imports or references `on_source_loaded`

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
        self.config.hook.pytest_bdd_source_read(
            config=self.config,
            gherkin_document=gherkin_document,
            source=source,
        )

    def on_feature_loaded(self, gherkin_document: GherkinDocument) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver.on_feature_loaded` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver.on_feature_loaded` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.config.hook.pytest_bdd_feature_read: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `on_feature_loaded`
            - src/pytest_bdd/scenario_locator/base.py: imports or references `on_feature_loaded`

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
        self.config.hook.pytest_bdd_feature_read(config=self.config, gherkin_document=gherkin_document)

    def on_pickle_loaded(self, gherkin_document: GherkinDocument, pickle: Pickle) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver.on_pickle_loaded` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioCollectionReadObserver.on_pickle_loaded` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.config.hook.pytest_bdd_pickle_read: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `on_pickle_loaded`
            - src/pytest_bdd/scenario_locator/base.py: imports or references `on_pickle_loaded`

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
        self.config.hook.pytest_bdd_pickle_read(
            config=self.config,
            gherkin_document=gherkin_document,
            pickle=pickle,
        )


class _ScenarioLocatorProtocol(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioLocatorProtocol` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioLocatorProtocol` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - resolve: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `_ScenarioLocatorProtocol`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioLocatorProtocol` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    def resolve(
        self,
        config: Config,
        *,
        observer: _ScenarioCollectionReadObserver,
    ) -> Iterator[tuple[GherkinDocument, Pickle, Source]]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioLocatorProtocol.resolve` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin._ScenarioLocatorProtocol.resolve` because it keeps the
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


class _CollectionFixtureRequest:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest`
        owns documented class behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - getfixturevalue: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `_CollectionFixtureRequest`

    State and side effects:
        mutates self.parameter_type_registry, msg.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises LookupError; callers must treat these as boundary failures.

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

    def __init__(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest.__init__` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest.__init__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ParameterTypeRegistry: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.parameter_type_registry.

        Invariants:
            - `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest.__init__` keeps its documented
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
        self.parameter_type_registry = ParameterTypeRegistry()

    def getfixturevalue(self, name: str) -> object:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest.getfixturevalue` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest.getfixturevalue` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - LookupError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `getfixturevalue`
            - src/pytest_bdd/parsers/cucumber_expression.py: imports or references `getfixturevalue`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `getfixturevalue`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `getfixturevalue`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `getfixturevalue`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest.getfixturevalue` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises LookupError; callers must treat these as boundary failures.

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
        if name == "parameter_type_registry":
            return self.parameter_type_registry
        msg = f"Fixture {name!r} is not available during zero-match collection validation"
        raise LookupError(msg)


def _iter_resolved_feature_scenarios(
    config: Config,
    locators: Collection[_ScenarioLocatorProtocol],
) -> Iterator[tuple[GherkinDocument, Pickle, Source]]:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.scenario_test_collector.plugin._iter_resolved_feature_scenarios` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin._iter_resolved_feature_scenarios` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _ScenarioCollectionReadObserver: collaborator call used by this boundary
        - locator.resolve: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
          `_iter_resolved_feature_scenarios`

    State and side effects:
        mutates observer.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin._iter_resolved_feature_scenarios` keeps its documented
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
    observer = _ScenarioCollectionReadObserver(config=config)
    for locator in locators:
        yield from locator.resolve(config, observer=observer)


def _validate_zero_match_scenarios(config: Config, items: Sequence[Item]) -> None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.scenario_test_collector.plugin._validate_zero_match_scenarios` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin._validate_zero_match_scenarios` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - params.get: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - _allow_empty_scenarios: collaborator call used by this boundary
        - Run.from_stash: collaborator call used by this boundary
        - _is_feature_autoload_item: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
          `_validate_zero_match_scenarios`

    State and side effects:
        mutates allow_empty, failures, run, callspec, params.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin._validate_zero_match_scenarios` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises pytest.UsageError; callers must treat these as boundary failures.

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
    if getattr(config.option, "generate_missing", False) or getattr(config.option, "generate", False):
        return
    if getattr(config.option, "keyword", "") or getattr(config.option, "markexpr", ""):
        return
    # In mock-run mode, skip collection-time validation: missing/ambiguous steps are
    # reported as IDE diagnostic attachments at runtime in _verify_mock_run_bindings.
    if getattr(config.option, "mock_run", False):
        return

    allow_empty = _allow_empty_scenarios(config)
    failures: list[str] = []
    run = Run.from_stash(config.stash)
    for item in items:
        if _is_feature_autoload_item(item):
            continue

        callspec = getattr(item, "callspec", None)
        params = getattr(callspec, "params", {})
        gherkin_document = params.get("gherkin_document")
        pickle = params.get("pickle")
        feature_source = params.get("feature_source")
        if not isinstance(gherkin_document, GherkinDocument) or not isinstance(pickle, Pickle):
            continue

        step_registry = _build_collection_step_registry(config, getattr(item, "module", None))
        if pickle.steps and not _scenario_has_step_match(config, gherkin_document, pickle, step_registry):
            if allow_empty:
                item.add_marker(pytest.mark.skip(reason="No matching step definitions found"))  # type: ignore[attr-defined]  # pytest.mark module
                continue
            binding = run.ensure_feature_binding(
                gherkin_document=gherkin_document,
                source=feature_source if isinstance(feature_source, Source) else None,
            )
            failures.extend(_format_zero_match_step(binding, pickle, step) for step in pickle.steps)

    if failures:
        details = "\n".join(failures)
        msg = (
            "Scenarios with zero matched step definitions found:\n"
            f"{details}\n"
            "Use --allow-empty-scenarios to skip these scenarios instead."
        )
        raise pytest.UsageError(msg)


class _ModernTestCollector:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector.plugin._ModernTestCollector` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin._ModernTestCollector` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_pycollect_makemodule: owns nested behavior below this boundary
        - pytest_collect_file: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `_ModernTestCollector`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin._ModernTestCollector` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    @pytest.hookimpl(hookwrapper=True)
    def pytest_pycollect_makemodule(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        parent: Collector,  # noqa: ARG002 hookimpl
        module_path: Path,  # noqa: ARG002 hookimpl
    ) -> Iterator[None]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_test_collector.plugin._ModernTestCollector.pytest_pycollect_makemodule` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin._ModernTestCollector.pytest_pycollect_makemodule` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _pytest_pycollect_makemodule: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `pytest_pycollect_makemodule`

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
        yield from _pytest_pycollect_makemodule()

    @pytest.hookimpl
    def pytest_collect_file(self, parent: Collector, file_path: Path) -> Collector | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.scenario_test_collector.plugin._ModernTestCollector.pytest_collect_file` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin._ModernTestCollector.pytest_collect_file` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _pytest_collect_file: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `pytest_collect_file`

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
        # noqa: PLR6301 -- pytest hook, must be instance method
        return _pytest_collect_file(parent=parent, file_path=file_path)


class ScenarioTestCollector(_ModernTestCollector):
    """
    Collect scenario-backed pytest items from feature files.

    Responsibility:
        Collect scenario-backed pytest items from feature files. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_collection_modifyitems: owns nested behavior below this boundary
        - pytest_plugin_registered: owns nested behavior below this boundary
        - pytest_generate_tests: owns nested behavior below this boundary
        - pytest_bdd_convert_tag_to_marks: owns nested behavior below this boundary
        - pytest_bdd_match_step_definition_to_step: owns nested behavior below this boundary
        - pytest_bdd_get_mimetype: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `ScenarioTestCollector`

    State and side effects:
        mutates _, is_enabled, config, marks, mark_names.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector` keeps its documented import path,
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

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        config: Config,
        items: list[Item],
    ) -> None:
        """
        Reject collected scenarios where no step definitions match.

        Responsibility:
            Reject collected scenarios where no step definitions match. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_collection_modifyitems`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _validate_zero_match_scenarios: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `pytest_collection_modifyitems`

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
        _validate_zero_match_scenarios(config, items)

    @pytest.hookimpl(tryfirst=True)
    def pytest_plugin_registered(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        plugin: object,
        manager: object,  # noqa: ARG002 hookimpl
    ) -> None:
        """
        Handle plugin registered.

        Responsibility:
            Handle plugin registered. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_plugin_registered` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - hasattr: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - Registry.inject_registry_fixture: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `pytest_plugin_registered`

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
        if hasattr(plugin, "__file__") and isinstance(plugin, (type, ModuleType)):
            Registry.inject_registry_fixture(
                cast("StepRegistryProtocol", cast("object", plugin)),
            )

    @pytest.hookimpl
    def pytest_generate_tests(self, metafunc: Metafunc) -> None:  # noqa: PLR6301 -- pytest hook, must be instance method
        """
        Handle generate tests.

        Responsibility:
            Handle generate tests. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_generate_tests` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - filter: collaborator call used by this boundary
            - ScenarioLocatorBuilder: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - chain_map: collaborator call used by this boundary
            - _iter_resolved_feature_scenarios: collaborator call used by this boundary
            - metafunc.parametrize: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `pytest_generate_tests`

        State and side effects:
            mutates config, marks, mark_names, scenario_marks, locator_builder.

        Invariants:
            - `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_generate_tests` keeps its
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
        config = metafunc.config

        # build marker locators
        marks: Sequence[Mark] = metafunc.definition.own_markers
        mark_names = [mark.name for mark in marks]
        if PYTEST_BDD_MARK in mark_names:
            scenario_marks = filter(lambda mark: mark.name == PYTEST_BDD_SCENARIOS_MARK, marks)
            locator_builder = ScenarioLocatorBuilder(config=config)
            locators = cast(
                "Collection[_ScenarioLocatorProtocol]",
                chain_map(locator_builder.build_for_pytest_mark, scenario_marks),
            )
            feature_scenario_feature_source = _iter_resolved_feature_scenarios(config, locators)

            metafunc.parametrize(
                "gherkin_document, pickle, feature_source",
                starmap(
                    partial(_build_pickle_param, config=config),
                    feature_scenario_feature_source,
                ),
            )

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_convert_tag_to_marks(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        tag: str,
    ) -> Collection[Mark | MarkDecorator] | None:
        """
        Convert tag to pytest marks.

        Returns:
            Collection of marks or None.

        Responsibility:
            Convert tag to pytest marks. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_bdd_convert_tag_to_marks`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `pytest_bdd_convert_tag_to_marks`

        State and side effects:
            mutates _.

        Invariants:
            - `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_bdd_convert_tag_to_marks`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        _ = gherkin_document
        _ = pickle
        return [getattr(pytest.mark, tag)]

    @pytest.hookimpl
    def pytest_bdd_match_step_definition_to_step(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        request: FixtureRequest,
        run: Run,
    ) -> Definition:
        """
        Match step definition to step.

        Returns:
            Step definition.

        Responsibility:
            Match step definition to step. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_bdd_match_step_definition_to_step`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - request.getfixturevalue: collaborator call used by this boundary
            - require_feature_object: collaborator call used by this boundary
            - require_pickle_object: collaborator call used by this boundary
            - require_step_object: collaborator call used by this boundary
            - resolve_previous_step_object: collaborator call used by this boundary
            - step_matcher: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references
              `pytest_bdd_match_step_definition_to_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `pytest_bdd_match_step_definition_to_step`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
              `pytest_bdd_match_step_definition_to_step`
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `pytest_bdd_match_step_definition_to_step`

        State and side effects:
            mutates gherkin_document, pickle, step, previous_step, step_registry.

        Invariants:
            - `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_bdd_match_step_definition_to_step`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        gherkin_document = require_feature_object(run, hook_name="pytest_bdd_match_step_definition_to_step")
        pickle = require_pickle_object(run, hook_name="pytest_bdd_match_step_definition_to_step")
        step = require_step_object(run, hook_name="pytest_bdd_match_step_definition_to_step")
        previous_step = resolve_previous_step_object(run)
        step_registry: Registry = request.getfixturevalue("step_registry")
        step_matcher: Matcher = request.getfixturevalue("step_matcher")

        return step_matcher(request, gherkin_document, pickle, step, previous_step, step_registry)  # type: ignore[arg-type]  # dynamic runtime types from pytest hooks

    @pytest.hookimpl
    def pytest_bdd_get_mimetype(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        config: Config,  # noqa: ARG002 hookimpl
        path: Path,
    ) -> Mimetype | None:
        """
        Get mimetype for file path.

        Returns:
            Mimetype or None.

        Responsibility:
            Get mimetype for file path. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_bdd_get_mimetype` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - mimetypes.guess_type: collaborator call used by this boundary
            - Mimetype: collaborator call used by this boundary
            - any: collaborator call used by this boundary
            - map: collaborator call used by this boundary
            - partial: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `pytest_bdd_get_mimetype`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pytest_bdd_get_mimetype`

        State and side effects:
            mutates mimetype_string, _encoding, mimetype.

        Invariants:
            - `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_bdd_get_mimetype` keeps its
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
        mimetype_string, _encoding = mimetypes.guess_type(path)
        if mimetype_string is None:
            return None
        try:
            mimetype = Mimetype(mimetype_string)
        except ValueError:
            return None
        if mimetype is Mimetype.gherkin_plain:
            return mimetype
        if mimetype is Mimetype.markdown and any(map(partial(contains, gherkin_suffixes), path.suffixes)):
            return Mimetype.gherkin_markdown
        return None

    @pytest.hookimpl
    def pytest_bdd_get_parser(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        config: Config,  # noqa: ARG002 hookimpl
        mimetype: str,
    ) -> type[ParserProtocol] | None:
        """
        Get parser for mimetype.

        Returns:
            Parser class or None.

        Responsibility:
            Get parser for mimetype. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_bdd_get_parser` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - suppress: collaborator call used by this boundary
            - Mimetype: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `pytest_bdd_get_parser`
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pytest_bdd_get_parser`
            - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `pytest_bdd_get_parser`

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
        with suppress(KeyError, ValueError):
            return {
                Mimetype.gherkin_plain: GherkinParser,
                Mimetype.gherkin_markdown: MarkdownGherkinParser,
            }[Mimetype(mimetype)]
        return None

    @pytest.hookimpl
    def pytest_bdd_is_collectible(  # noqa: PLR6301 -- pytest hook, must be instance method
        self,
        config: Config,  # noqa: ARG002 hookimpl
        path: Path,
    ) -> bool | None:
        """
        Check if path is collectible.

        Returns:
            True if collectible, False or None otherwise.

        Responsibility:
            Check if path is collectible. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.pytest_bdd_is_collectible` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - any: collaborator call used by this boundary
            - map: collaborator call used by this boundary
            - partial: collaborator call used by this boundary
            - gherkin_suffixes.union: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `pytest_bdd_is_collectible`

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
            any(
                map(
                    partial(
                        contains,
                        gherkin_suffixes.union(link_suffixes),
                    ),
                    path.suffixes,
                ),
            )
            or None
        )

    @staticmethod
    def is_enabled(config: Config) -> bool:
        """
        Return True if the collector is enabled via CLI or INI config.

        Responsibility:
            Return True if the collector is enabled via CLI or INI config. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.is_enabled` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - config.getoption: collaborator call used by this boundary
            - config.getini: collaborator call used by this boundary
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `is_enabled`

        State and side effects:
            mutates is_enabled.

        Invariants:
            - `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollector.is_enabled` keeps its documented
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
        is_enabled = config.getoption(str(FeatureAutoLoad.Cli.DISABLE_OPTION))
        if is_enabled is None:
            is_enabled = not config.getini(str(FeatureAutoLoad.Ini.DISABLE_OPTION))
        return bool(is_enabled)


class ScenarioTestCollectorPlugin(ScenarioTestCollector):
    """
    Represent scenario test collector plugin state.

    Responsibility:
        Represent scenario test collector plugin state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollectorPlugin` because it keeps the nearest
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
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `ScenarioTestCollectorPlugin`
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references
          `ScenarioTestCollectorPlugin`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.plugin.ScenarioTestCollectorPlugin` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """
