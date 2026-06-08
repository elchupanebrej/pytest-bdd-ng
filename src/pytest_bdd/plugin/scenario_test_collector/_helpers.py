"""
Helper functions extracted from plugin.py to reduce file size below 400 LOC.

Responsibility:
    Helper functions extracted from plugin.py to reduce file size below 400 LOC. It directly owns the observable
    contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.scenario_test_collector._helpers` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _build_pickle_param: owns nested behavior below this boundary
    - _allow_empty_scenarios: owns nested behavior below this boundary
    - _iter_collection_step_definitions: owns nested behavior below this boundary
    - _build_collection_step_registry: owns nested behavior below this boundary
    - _scenario_has_step_match: owns nested behavior below this boundary
    - _format_zero_match_step: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_helpers`

State and side effects:
    mutates previous_step, line, parent, binding, marks; depends on __future__.annotations, warnings,
    collections.abc.Iterator, typing.TYPE_CHECKING, typing.cast.

Invariants:
    - `pytest_bdd.plugin.scenario_test_collector._helpers` keeps its documented import path, ownership boundary, and
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
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from typing import TYPE_CHECKING, cast

from ordered_set import OrderedSet

from pytest_bdd.compatibility.pytest import (
    Config,
    FixtureRequest,
    Item,
)
from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
from pytest_bdd.model.run import Run
from pytest_bdd.model.scenario_collection import (
    EmptyScenarios,
)
from pytest_bdd.steps import (
    Definition,
    Matcher,
    Registry,
)
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument, Pickle, PickleStep, Source


def _build_pickle_param(
    gherkin_document: GherkinDocument,
    pickle: Pickle,
    feature_source: Source,
    config: Config,
) -> object:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector._helpers._build_pickle_param` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector._helpers._build_pickle_param` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - Run.from_stash.ensure_feature_binding: collaborator call used by this boundary
        - Run.from_stash: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - tag.name.lstrip: collaborator call used by this boundary
        - config.hook.pytest_bdd_convert_tag_to_marks: collaborator call used by this boundary
        - marks.extend: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_build_pickle_param`

    State and side effects:
        mutates binding, marks, tag_marks, table_rows_breadcrumb; depends on pytest.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector._helpers._build_pickle_param` keeps its documented import path,
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
    import pytest

    binding = Run.from_stash(config.stash).ensure_feature_binding(
        gherkin_document=gherkin_document,
        source=feature_source,
    )
    marks = []
    for tag in sorted(tag.name.lstrip("@") for tag in pickle.tags):
        tag_marks = config.hook.pytest_bdd_convert_tag_to_marks(
            gherkin_document=gherkin_document,
            pickle=pickle,
            tag=tag,
        )
        if tag_marks is not None:
            marks.extend(tag_marks)
    table_rows_breadcrumb = binding.pickle_table_rows_breadcrumb(pickle)
    return pytest.param(
        gherkin_document,
        pickle,
        feature_source,
        id=f"{binding.uri}-{binding.name}-{pickle.name}{table_rows_breadcrumb}",
        marks=marks,
    )


def _allow_empty_scenarios(config: Config) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector._helpers._allow_empty_scenarios` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector._helpers._allow_empty_scenarios` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - bool: collaborator call used by this boundary
        - config.getoption: collaborator call used by this boundary
        - config.getini: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_allow_empty_scenarios`

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
    return bool(
        config.getoption(str(EmptyScenarios.Cli.ALLOW_OPTION), default=False)
        or config.getini(str(EmptyScenarios.Ini.ALLOW_OPTION)),
    )


def _iter_collection_step_definitions(
    config: Config,
    module: object,
) -> Iterator[Definition]:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.scenario_test_collector._helpers._iter_collection_step_definitions` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector._helpers._iter_collection_step_definitions` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - config.pluginmanager.get_plugins: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - id: collaborator call used by this boundary
        - seen_registries.add: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
          `_iter_collection_step_definitions`

    State and side effects:
        mutates seen_registries, namespaces, registry, registry_id.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector._helpers._iter_collection_step_definitions` keeps its documented
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
    seen_registries: set[int] = set()
    namespaces = (module, *config.pluginmanager.get_plugins())
    for namespace in namespaces:
        registry = getattr(namespace, "_step_registry", None) or getattr(
            namespace,
            "__pytest_bdd_step_registry__",
            None,
        )
        if not isinstance(registry, Registry):
            continue
        registry_id = id(registry)
        if registry_id in seen_registries:
            continue
        seen_registries.add(registry_id)
        yield from registry


def _build_collection_step_registry(
    config: Config,
    module: object,
) -> Registry:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.scenario_test_collector._helpers._build_collection_step_registry` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector._helpers._build_collection_step_registry` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Registry: collaborator call used by this boundary
        - OrderedSet: collaborator call used by this boundary
        - _iter_collection_step_definitions: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references
          `_build_collection_step_registry`

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
    return Registry(definitions=OrderedSet(_iter_collection_step_definitions(config, module)))


def _scenario_has_step_match(
    config: Config,
    gherkin_document: GherkinDocument,
    pickle: Pickle,
    step_registry: Registry,
) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector._helpers._scenario_has_step_match`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector._helpers._scenario_has_step_match` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - _CollectionFixtureRequest: collaborator call used by this boundary
        - Matcher: collaborator call used by this boundary
        - warnings.catch_warnings: collaborator call used by this boundary
        - warnings.simplefilter: collaborator call used by this boundary
        - matcher: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_scenario_has_step_match`

    State and side effects:
        mutates previous_step, request, matcher, feature; depends on
        pytest_bdd.plugin.scenario_test_collector.plugin._CollectionFixtureRequest.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector._helpers._scenario_has_step_match` keeps its documented import
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
    from pytest_bdd.plugin.scenario_test_collector.plugin import _CollectionFixtureRequest

    request = cast("FixtureRequest", _CollectionFixtureRequest())
    matcher = Matcher(config)
    previous_step: PickleStep | None = None
    feature = gherkin_document.feature
    for step in pickle.steps:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", PytestBDDStepDefinitionWarning)
                matcher(request, feature, pickle, step, previous_step, step_registry)  # type: ignore[arg-type]  # feature from GherkinDocument, not Feature type
        except (LookupError, Matcher.MatchNotFoundError):
            previous_step = step
            continue
        return True
    return False


def _format_zero_match_step(
    binding: FeatureRuntimeBinding,
    pickle: Pickle,
    step: PickleStep,
) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector._helpers._format_zero_match_step`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector._helpers._format_zero_match_step` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - binding.step_line_number: collaborator call used by this boundary
        - binding.pickle_line_number: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_format_zero_match_step`

    State and side effects:
        mutates line.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector._helpers._format_zero_match_step` keeps its documented import path,
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
    line = binding.step_line_number(step)
    if line is None or line < 0:
        line = binding.pickle_line_number(pickle)
    return f'  File "{binding.filename}", line {line}: "{step.text}"'


def _is_feature_autoload_item(item: Item) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.scenario_test_collector._helpers._is_feature_autoload_item`
        owns documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector._helpers._is_feature_autoload_item` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `_is_feature_autoload_item`

    State and side effects:
        mutates parent; depends on pytest_bdd.collector.FeatureFileModule.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector._helpers._is_feature_autoload_item` keeps its documented import
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
    from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector

    parent = item.parent
    while parent is not None:
        if isinstance(parent, FeatureFileCollector):
            return True
        parent = parent.parent
    return False
