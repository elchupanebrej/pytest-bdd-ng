"""Immutable-domain bindings used while pytest-cuke executes a feature."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from attrs import define, field, fields, has

from pytest_cuke.model import Feature, GherkinDocument, Scenario, Step


def normalize_feature_uri(feature: Feature) -> str:
    """Return a stable URI key for a parsed feature source."""
    uri = feature.uri.strip()
    if uri:
        parsed = urlsplit(uri)
        if parsed.scheme == "file":
            path = parsed.path
            is_local_file_uri = parsed.netloc.lower() in {"", "localhost"}
            has_windows_drive_root = (
                len(path) >= 4
                and path[0] == "/"
                and path[1] in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                and path[2:4] == ":/"
            )
            if is_local_file_uri and has_windows_drive_root:
                normalized_path = quote(unquote(path), safe="/:")
                return urlunsplit(("file", "", normalized_path, "", ""))

            file_path = Path(unquote(parsed.path))
            if not file_path.is_absolute() and not parsed.netloc and feature.filename:
                file_path = Path(feature.filename)
            file_path = file_path.resolve()
            return file_path.as_uri()
        if parsed.scheme:
            return urlunsplit(
                (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query, parsed.fragment)
            )
        if not feature.filename:
            return Path(uri).resolve().as_uri()
    if feature.filename:
        return Path(feature.filename).resolve().as_uri()
    return f"memory://{feature.name}"


@define(slots=True)
class FeatureRuntimeBinding:
    """Indexes parsed feature objects without attaching transient data to them."""

    uri: str
    feature: Feature
    source: str | None = None
    source_media_type: str | None = None
    document: GherkinDocument | None = None
    ast_nodes_by_id: dict[str, object] = field(factory=dict)
    pickles_by_id: dict[str, Scenario] = field(factory=dict)
    scenarios_by_source_ids: dict[tuple[str, ...], Scenario] = field(factory=dict)
    _indexed_object_ids: set[int] = field(factory=set, repr=False)

    @classmethod
    def from_feature(cls, feature: Feature) -> FeatureRuntimeBinding:
        binding = cls(
            uri=normalize_feature_uri(feature),
            feature=feature,
            source=feature.source_content,
            source_media_type=feature.source_media_type,
            document=GherkinDocument(uri=feature.uri, feature=feature),
        )
        binding._index_feature_tree()
        return binding

    def register_scenario(self, scenario: Scenario) -> None:
        """Register a parsed or expanded scenario while keeping its source model frozen."""
        if scenario.id:
            self.pickles_by_id[scenario.id] = scenario
        if scenario.source_ast_node_ids:
            self.scenarios_by_source_ids[scenario.source_ast_node_ids] = scenario
            for node_id in scenario.source_ast_node_ids:
                self.ast_nodes_by_id.setdefault(node_id, scenario)
        self._index_tree(scenario)

    def resolve_scenario(self, node_ids: tuple[str, ...]) -> Scenario | None:
        return self.scenarios_by_source_ids.get(node_ids)

    def resolve_step(self, step: Step) -> Step | None:
        if step.id is None:
            return None
        node = self.ast_nodes_by_id.get(step.id)
        return node if isinstance(node, Step) else None

    def _index_feature_tree(self) -> None:
        self._index_tree(self.feature)
        for scenario in self.feature.all_scenarios:
            self.register_scenario(scenario)

    def _index_tree(self, node: Any) -> None:
        if node is None or id(node) in self._indexed_object_ids:
            return
        self._indexed_object_ids.add(id(node))
        if isinstance(node, list | tuple):
            for child in node:
                self._index_tree(child)
            return
        node_id = getattr(node, "id", None)
        if isinstance(node_id, str) and node_id:
            self.ast_nodes_by_id.setdefault(node_id, node)
        if has(type(node)):
            for attribute in fields(type(node)):
                self._index_tree(getattr(node, attribute.name))


__all__ = ["FeatureRuntimeBinding", "normalize_feature_uri"]
