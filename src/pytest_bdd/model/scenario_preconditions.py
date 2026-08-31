"""
Resolve and order scenario preconditions during pytest collection.

Responsibility:
    Resolves scenario-to-scenario precondition declarations, validates that referenced scenarios were collected, and
    produces a deterministic topological ordering for the pytest collection hook.

Reason for existence:
    Scenario preconditions are collection-time graph semantics rather than step execution behavior. Centralizing URI
    normalization, declaration parsing, cycle detection, and ordering keeps the collector thin and gives users clear
    errors before any scenario runs.

Delegates:
    - `pathlib.Path`: Canonicalizes local feature paths for cross-feature references.
    - `pytest_bdd.plugin.scenario_test_collector`: Supplies collected items and applies the resulting order.
    - pytest item metadata: Provides pickle tags and feature sources for graph construction.

Cohesion:
    All entities in this module support one dependency-graph pipeline: identify scenario keys, parse edges, validate
    targets, detect cycles, and topologically order items. The graph is rebuilt per collection invocation.

Separation:
    - Scenario execution remains in the pickle runner; this module only determines collection order and errors.
    - Cucumber Messages reporting remains in reporting adapters; precondition scenarios use the normal message path.
    - pytest hook integration remains in the collector plugin; this module exposes pure graph operations.

Main consumers:
    - `ScenarioTestCollector.pytest_collection_modifyitems`: Applies ordering and translates graph errors to usage errors.
    - Unit tests and future tooling: Parse and validate precondition declarations independently of pytest execution.

State and side effects:
    Parsing and graph helpers are stateless. Ordering returns a new item list and does not mutate global registries,
    making the behavior safe when pytest-xdist collects independently in multiple workers.

Invariants:
    - Every declared target must resolve to a collected scenario key.
    - A dependency cycle is rejected with a readable chain before ordering completes.
    - Non-BDD item positions remain stable while BDD scenario slots receive topologically ordered items.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

# The graph helper entities remain intentionally small; this module doc records their shared architectural boundary.
# pylint: disable=missing-responsibility-doc,missing-architecture-score,no-return-none

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from attrs import define

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from pytest_bdd.compatibility.pytest import Item


_PRECONDITION_PATTERN = re.compile(r"^@?precondition(?:\((?P<parenthesized>.*)\)|=(?P<assigned>.*))$")


@define(frozen=True, slots=True)
class ScenarioKey:
    """Identify one collected scenario by canonical feature URI and name."""

    uri: str
    name: str

    def display(self) -> str:
        """Return a concise human-readable scenario reference."""
        return f"{self.uri}: {self.name}"


@define(frozen=True, slots=True)
class ScenarioPrecondition:
    """Represent a resolved edge from a scenario to its setup scenario."""

    key: ScenarioKey
    target: ScenarioKey


class ScenarioPreconditionError(ValueError):
    """Base error for invalid scenario precondition declarations."""


class MissingScenarioPreconditionError(ScenarioPreconditionError):
    """Report a precondition that is not part of the current collection."""


class ScenarioPreconditionCycleError(ScenarioPreconditionError):
    """Report a cycle in the scenario precondition graph."""


def _canonical_uri(uri: str) -> str:
    """Normalize local feature paths while preserving non-file URIs."""
    if uri.startswith("file:"):
        uri = uri.removeprefix("file:")
    if "://" in uri:
        return uri
    return str(Path(uri).expanduser().resolve())


def _source_uri(source: object, pickle: object) -> str:
    """Read a feature URI from a Cucumber Source or pickle-like object."""
    source_uri = getattr(source, "uri", None) or getattr(pickle, "uri", None)
    return _canonical_uri(str(source_uri or "<unknown-feature>"))


def _split_reference(reference: str) -> tuple[str, str]:
    """Split ``feature: scenario`` without mistaking a Windows drive for the separator."""
    reference = reference.strip().strip("\"'")
    match = re.search(r":\s+", reference)
    if match is not None:
        return reference[: match.start()].strip(), reference[match.end() :].strip()
    if ":" in reference and not re.match(r"^[A-Za-z]:[\\/]", reference):
        feature, name = reference.rsplit(":", 1)
        return feature.strip(), name.strip()
    return "", reference


def parse_precondition_tag(tag_name: str, *, source_uri: str, scenario_name: str) -> ScenarioPrecondition | None:
    """
    Parse one precondition tag into a canonical dependency edge.

    Tags without the ``precondition`` shape are ignored. A target without a
    feature component refers to another scenario in the current feature.
    """
    match = _PRECONDITION_PATTERN.fullmatch(tag_name.strip())
    if match is None:
        return None

    reference = (match.group("parenthesized") or match.group("assigned") or "").strip()
    feature_part, target_name = _split_reference(reference)
    if not target_name:
        message = f"Precondition tag {tag_name!r} does not name a scenario"
        raise ScenarioPreconditionError(message)

    current_uri = _canonical_uri(source_uri)
    if feature_part:
        feature_path = Path(feature_part).expanduser()
        if not feature_path.is_absolute() and "://" not in feature_part:
            feature_path = Path(current_uri).parent / feature_path
        target_uri = _canonical_uri(str(feature_path))
    else:
        target_uri = current_uri

    return ScenarioPrecondition(
        key=ScenarioKey(uri=current_uri, name=scenario_name),
        target=ScenarioKey(uri=target_uri, name=target_name),
    )


def _item_data(item: Item) -> tuple[object, object, object] | None:
    """Return the Gherkin objects attached to a parametrized BDD item."""
    callspec = getattr(item, "callspec", None)
    params = getattr(callspec, "params", None)
    if not isinstance(params, dict):
        return None
    pickle = params.get("pickle")
    if pickle is None:
        return None
    return params.get("gherkin_document"), pickle, params.get("feature_source")


def _tag_names(pickle: object) -> Iterable[str]:
    """Yield string tag names from a Cucumber pickle."""
    for tag in getattr(pickle, "tags", ()) or ():
        name = getattr(tag, "name", None)
        if isinstance(name, str):
            yield name


def _find_cycle(dependencies: dict[ScenarioKey, set[ScenarioKey]]) -> tuple[ScenarioKey, ...] | None:
    """Return one dependency cycle, if any, using depth-first search."""
    visiting: set[ScenarioKey] = set()
    visited: set[ScenarioKey] = set()
    path: list[ScenarioKey] = []

    def visit(node: ScenarioKey) -> tuple[ScenarioKey, ...] | None:
        if node in visiting:
            return (*path[path.index(node) :], node)
        if node in visited:
            return None
        visiting.add(node)
        path.append(node)
        for dependency in dependencies[node]:
            cycle = visit(dependency)
            if cycle is not None:
                return cycle
        path.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in dependencies:
        cycle = visit(node)
        if cycle is not None:
            return cycle
    return None


def order_scenario_items(items: Sequence[Item]) -> list[Item]:  # noqa: C901, PLR0912, PLR0914  # graph validation branches
    """
    Validate and topologically order collected BDD items by precondition.

    Non-BDD pytest items retain their original positions. Preconditions are
    ordinary scenario items, so their existing runner and message adapters
    report setup execution without a second execution mechanism.
    """
    scenario_items: dict[ScenarioKey, Item] = {}
    scenario_order: list[ScenarioKey] = []
    declarations: list[ScenarioPrecondition] = []
    bdd_item_ids: set[int] = set()

    for item in items:
        data = _item_data(item)
        if data is None:
            continue
        _gherkin_document, pickle, source = data
        name = getattr(pickle, "name", None)
        if not isinstance(name, str):
            continue
        uri = _source_uri(source, pickle)
        key = ScenarioKey(uri=uri, name=name)
        if key in scenario_items:
            continue
        scenario_items[key] = item
        scenario_order.append(key)
        bdd_item_ids.add(id(item))
        for tag_name in _tag_names(pickle):
            declaration = parse_precondition_tag(tag_name, source_uri=uri, scenario_name=name)
            if declaration is not None:
                declarations.append(declaration)

    if not declarations:
        return list(items)

    dependencies: dict[ScenarioKey, set[ScenarioKey]] = {key: set() for key in scenario_items}
    for declaration in declarations:
        if declaration.target not in scenario_items:
            message = (
                f"Scenario {declaration.key.display()} declares missing precondition {declaration.target.display()}"
            )
            raise MissingScenarioPreconditionError(message)
        dependencies[declaration.key].add(declaration.target)

    cycle = _find_cycle(dependencies)
    if cycle is not None:
        chain = " -> ".join(key.display() for key in cycle)
        message = f"Circular scenario precondition detected: {chain}"
        raise ScenarioPreconditionCycleError(message)

    remaining = {key: set(value) for key, value in dependencies.items()}
    ordered_keys: list[ScenarioKey] = []
    while remaining:
        ready = [key for key in scenario_order if key in remaining and not remaining[key]]
        if not ready:
            message = "Circular scenario precondition detected"
            raise ScenarioPreconditionCycleError(message)
        ordered_keys.extend(ready)
        for key in ready:
            del remaining[key]
        for dependency_set in remaining.values():
            dependency_set.difference_update(ready)

    ordered_items = iter(scenario_items[key] for key in ordered_keys)
    result = list(items)
    for index, item in enumerate(result):
        if id(item) in bdd_item_ids:
            result[index] = next(ordered_items)
    return result
