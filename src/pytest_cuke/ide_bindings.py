"""Payload helpers for IDE launch and step-binding diagnostics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pytest_cuke.model.feature_binding import FeatureRuntimeBinding, normalize_feature_uri
from pytest_cuke.model.message_extension import (
    IDE_DIAGNOSTIC_MEDIA_TYPE,
    IDE_LAUNCH_MEDIA_TYPE,
    IDE_STEP_BINDING_MEDIA_TYPE,
)

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, FixtureRequest
    from pytest_cuke.model import Feature, Scenario, Step
    from pytest_cuke.steps.definition import Definition


IDE_BINDING_WORKER_OUTPUT_KEY = "pytest_cuke_ide_bindings"


@dataclass
class IdeBindingCollection:
    """Collect source bindings and merge the same information from xdist workers."""

    source_identities_by_key: dict[str, dict[str, Any]] = field(default_factory=dict)
    nodeids_by_source_key: dict[str, set[str]] = field(default_factory=dict)
    test_case_ids_by_nodeid: dict[str, set[tuple[str | None, str]]] = field(default_factory=dict)

    def register_source(self, identity: dict[str, Any], nodeid: str | None = None) -> str:
        key = source_identity_key(identity)
        self.source_identities_by_key.setdefault(key, identity)
        if nodeid is not None:
            self.nodeids_by_source_key.setdefault(key, set()).add(nodeid)
        return key

    def record_test_case(self, nodeid: str, test_case_id: str, *, worker_id: str | None = None) -> None:
        self.test_case_ids_by_nodeid.setdefault(nodeid, set()).add((worker_id, test_case_id))

    def to_worker_output(self) -> dict[str, Any]:
        """Serialize only builtin values for pytest-xdist's workeroutput channel."""
        return {
            "sourceIdentities": self.source_identities_by_key.copy(),
            "nodeidsBySource": {
                key: sorted(nodeids) for key, nodeids in self.nodeids_by_source_key.items()
            },
            "testCaseIdsByNodeid": {
                nodeid: sorted(test_case_id for _, test_case_id in test_case_ids)
                for nodeid, test_case_ids in self.test_case_ids_by_nodeid.items()
            },
        }

    def merge_worker_output(self, payload: object, *, worker_id: str | None = None) -> None:
        """Merge a worker payload while ignoring malformed or unknown values."""
        if not isinstance(payload, dict):
            return

        source_identities = payload.get("sourceIdentities")
        if isinstance(source_identities, dict):
            for identity in source_identities.values():
                if isinstance(identity, dict) and all(isinstance(key, str) for key in identity):
                    self.register_source(identity)

        nodeids_by_source = payload.get("nodeidsBySource")
        if isinstance(nodeids_by_source, dict):
            for key, nodeids in nodeids_by_source.items():
                if not isinstance(key, str) or not isinstance(nodeids, list):
                    continue
                self.nodeids_by_source_key.setdefault(key, set()).update(
                    nodeid for nodeid in nodeids if isinstance(nodeid, str)
                )

        test_case_ids_by_nodeid = payload.get("testCaseIdsByNodeid")
        if isinstance(test_case_ids_by_nodeid, dict):
            for nodeid, test_case_ids in test_case_ids_by_nodeid.items():
                if not isinstance(nodeid, str) or not isinstance(test_case_ids, list):
                    continue
                for test_case_id in test_case_ids:
                    if isinstance(test_case_id, str):
                        self.record_test_case(nodeid, test_case_id, worker_id=worker_id)

    def diagnostics(self) -> list[dict[str, Any]]:
        """Return source-level diagnostics with node and case identities."""
        diagnostics: list[dict[str, Any]] = []
        for key, identity in sorted(self.source_identities_by_key.items()):
            nodeids = sorted(self.nodeids_by_source_key.get(key, ()))
            if not nodeids:
                diagnostics.append(
                    {
                        "kind": "unbound-scenario",
                        "severity": "warning",
                        "sourceIdentity": identity,
                    }
                )
                continue

            if len(nodeids) < 2:
                continue

            bindings = []
            for nodeid in nodeids:
                case_ids = sorted(
                    self.test_case_ids_by_nodeid.get(nodeid, ()),
                    key=lambda case: (case[0] or "", case[1]),
                )
                for worker_id, test_case_id in case_ids:
                    binding = {"nodeid": nodeid, "testCaseId": test_case_id}
                    if worker_id is not None:
                        binding["workerId"] = worker_id
                    bindings.append(binding)
            if len(bindings) > 1:
                diagnostics.append(
                    {
                        "kind": "duplicate-bindings",
                        "severity": "warning",
                        "sourceIdentity": identity,
                        "bindings": bindings,
                    }
                )
        return diagnostics


def source_identity(
    feature: Feature,
    scenario: Scenario,
    binding: FeatureRuntimeBinding | None = None,
) -> dict[str, Any]:
    """Build a stable, editor-resolvable identity for one collected source row."""
    feature_uri = normalize_feature_uri(feature)
    source_node_id = scenario.source_ast_node_ids[0] if scenario.source_ast_node_ids else scenario.id
    row_node_id = scenario.source_ast_node_ids[1] if len(scenario.source_ast_node_ids) > 1 else None
    scenario_node = binding.ast_nodes_by_id.get(source_node_id) if binding is not None and source_node_id else None
    row_node = binding.ast_nodes_by_id.get(row_node_id) if binding is not None and row_node_id else None

    scenario_line = _positive_line(getattr(scenario_node, "line", scenario.line))
    row_line = _optional_line(getattr(row_node, "line", 0))
    external_source = scenario.external_example_source

    if external_source is not None:
        launch_uri = Path(external_source.path).resolve().as_uri()
        launch_line = _positive_line(external_source.source_line)
        row_node_id = external_source.row_id or row_node_id
        row_line = launch_line
    elif row_line:
        launch_uri = feature_uri
        launch_line = row_line
    else:
        launch_uri = feature_uri
        launch_line = scenario_line

    identity: dict[str, Any] = {
        "uri": launch_uri,
        "line": launch_line,
        "scenarioUri": feature_uri,
        "scenarioLine": scenario_line,
    }
    if source_node_id:
        identity["scenarioId"] = source_node_id
    if row_node_id:
        identity["rowId"] = row_node_id
    if row_line:
        identity["rowLine"] = row_line
    if external_source is not None:
        identity["externalExamples"] = True
    return identity


def source_identity_key(identity: dict[str, Any]) -> str:
    """Return deterministic session-local grouping key for a source identity."""
    return json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def definition_reference(definition: Definition, config: Config) -> dict[str, Any]:
    """Return a Messages step definition's stable ID, pattern, and source location."""
    message = definition.as_message(config)
    source_reference = message.source_reference
    location = source_reference.location
    return {
        "stepDefinitionId": message.id,
        "pattern": message.pattern.source,
        "sourceReference": {
            "uri": source_reference.uri,
            "line": _positive_line(location.line if location is not None else None),
        },
    }


def match_arguments(definition: Definition, request: FixtureRequest, step: Step) -> list[dict[str, Any]]:
    """Extract named arguments without running the definition's converters."""
    try:
        anonymous_group_names = definition.anonymous_group_names
        if anonymous_group_names is not None:
            anonymous_group_names = tuple(anonymous_group_names)
            definition.anonymous_group_names = anonymous_group_names
        parsed = definition.parser.parse_arguments(
            request,
            step.name,
            anonymous_group_names=anonymous_group_names,
        ) or {}
        return [{"name": name, "value": _json_value(value)} for name, value in parsed.items()]
    except Exception:
        # Reporting must not change whether a scenario passes or fails.
        return []


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list | tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    try:
        json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        try:
            return str(value)
        except Exception:
            return type(value).__qualname__
    return value


def _positive_line(value: object) -> int:
    return max(1, value) if isinstance(value, int) and not isinstance(value, bool) else 1


def _optional_line(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


__all__ = [
    "IDE_BINDING_WORKER_OUTPUT_KEY",
    "IDE_DIAGNOSTIC_MEDIA_TYPE",
    "IDE_LAUNCH_MEDIA_TYPE",
    "IDE_STEP_BINDING_MEDIA_TYPE",
    "IdeBindingCollection",
    "definition_reference",
    "match_arguments",
    "source_identity",
    "source_identity_key",
]
