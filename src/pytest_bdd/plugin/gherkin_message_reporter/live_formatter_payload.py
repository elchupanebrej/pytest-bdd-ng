"""
Provide live formatter payload helpers.

Responsibility:
    Provide live formatter payload helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload`
    because it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - LiveFormatterPayloadMixin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
      `live_formatter_payload`

State and side effects:
    mutates source_reference, code_reference, reporter, type_name, normalized; depends on __future__.annotations,
    pathlib.Path, typing.TYPE_CHECKING, cucumber_messages.Envelope,
    pytest_bdd.model.cucumber_formatter_contract.CucumberFormatterRequest.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cucumber_messages import Envelope as Message

    from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
    from pytest_bdd.types.json import JSONArray, JSONObject


class LiveFormatterPayloadMixin:
    """
    Provide live formatter payload construction behavior.

    Responsibility:
        Provide live formatter payload construction behavior. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _resolve_formatter_expression_constructor_name: owns nested behavior below this boundary
        - _resolve_source_reference_uri: owns nested behavior below this boundary
        - _resolve_source_reference_line: owns nested behavior below this boundary
        - _build_cucumber_formatter_support_code_payload: owns nested behavior below this boundary
        - build_cucumber_formatter_support_code_payload: owns nested behavior below this boundary
        - _build_cucumber_formatter_payload: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
          `LiveFormatterPayloadMixin`

    State and side effects:
        mutates source_reference, code_reference, reporter, type_name, normalized.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

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

    if TYPE_CHECKING:
        reporter: GherkinMessageReporter

    @staticmethod
    def _resolve_formatter_expression_constructor_name(pattern_type: object | None) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_formatter_expression_constructor_name`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_formatter_expression_constructor_name`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - type_name.upper: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_resolve_formatter_expression_constructor_name`

        State and side effects:
            mutates type_name, normalized.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_formatter_expression_constructor_name`
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
        type_name = getattr(pattern_type, "name", None) or str(pattern_type or "")
        normalized = type_name.upper()
        if "REGULAR" in normalized:
            return "RegularExpression"
        return "CucumberExpression"

    @staticmethod
    def _resolve_source_reference_uri(source_reference: object | None) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_source_reference_uri`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_source_reference_uri`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_resolve_source_reference_uri`

        State and side effects:
            mutates uri.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_source_reference_uri`
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
        uri = getattr(source_reference, "uri", None)
        return "" if uri is None else str(uri)

    @staticmethod
    def _resolve_source_reference_line(source_reference: object | None) -> int:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_source_reference_line`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_source_reference_line`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - int: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_resolve_source_reference_line`

        State and side effects:
            mutates location, line.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._resolve_source_reference_line`
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
        location = getattr(source_reference, "location", None)
        line = getattr(location, "line", 0)
        return int(line or 0)

    def _build_cucumber_formatter_support_code_payload(self, envelopes: list[Message]) -> JSONObject:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._build_cucumber_formatter_support_code_payload`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._build_cucumber_formatter_support_code_payload`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - set: collaborator call used by this boundary
            - self._resolve_source_reference_uri: collaborator call used by this boundary
            - self._resolve_source_reference_line: collaborator call used by this boundary
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_build_cucumber_formatter_support_code_payload`

        State and side effects:
            mutates source_reference, code_reference, step_definitions, hooks, parameter_types.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._build_cucumber_formatter_support_code_payload`
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
        step_definitions: JSONArray = []
        hooks: JSONArray = []
        parameter_types: JSONArray = []
        seen_step_definition_ids: set[str] = set()
        seen_hook_ids: set[str] = set()
        seen_parameter_type_ids: set[str] = set()

        for envelope in envelopes:
            step_definition = getattr(envelope, "step_definition", None)
            if step_definition is not None and step_definition.id not in seen_step_definition_ids:
                seen_step_definition_ids.add(step_definition.id)
                source_reference = getattr(step_definition, "source_reference", None)
                java_method = getattr(source_reference, "java_method", None)
                pattern = getattr(step_definition, "pattern", None)
                code_reference = ".".join(
                    part
                    for part in (
                        getattr(java_method, "class_name", None),
                        getattr(java_method, "method_name", None),
                    )
                    if part is not None
                )
                if not code_reference:
                    code_reference = (
                        f"{self._resolve_source_reference_uri(source_reference)}:"
                        f"{self._resolve_source_reference_line(source_reference)}"
                    )
                step_definitions.append(
                    {
                        "id": str(step_definition.id),
                        "uri": self._resolve_source_reference_uri(source_reference),
                        "line": self._resolve_source_reference_line(source_reference),
                        "pattern": "" if pattern is None else str(getattr(pattern, "source", "")),
                        "expressionConstructorName": self._resolve_formatter_expression_constructor_name(
                            getattr(pattern, "type", None),
                        ),
                        "code": code_reference,
                    },
                )

            hook = getattr(envelope, "hook", None)
            if hook is not None and hook.id not in seen_hook_ids:
                seen_hook_ids.add(hook.id)
                source_reference = getattr(hook, "source_reference", None)
                hook_type = getattr(hook, "type", None)
                hook_type_name = getattr(hook_type, "name", None) or str(hook_type or "")
                hooks.append(
                    {
                        "id": str(hook.id),
                        "name": None if getattr(hook, "name", None) is None else str(hook.name),
                        "uri": self._resolve_source_reference_uri(source_reference),
                        "line": self._resolve_source_reference_line(source_reference),
                        "type": hook_type_name.split(".")[-1].lower(),
                        "tagExpression": None
                        if getattr(hook, "tag_expression", None) is None
                        else str(hook.tag_expression),
                    },
                )

            parameter_type = getattr(envelope, "parameter_type", None)
            if parameter_type is not None and parameter_type.id not in seen_parameter_type_ids:
                seen_parameter_type_ids.add(parameter_type.id)
                parameter_types.append(
                    {
                        "name": None if getattr(parameter_type, "name", None) is None else str(parameter_type.name),
                        "regularExpressions": [
                            str(regular_expression)
                            for regular_expression in getattr(parameter_type, "regular_expressions", ())
                        ],
                        "preferForRegularExpressionMatch": bool(
                            getattr(parameter_type, "prefer_for_regular_expression_match", False),
                        ),
                        "useForSnippets": bool(getattr(parameter_type, "use_for_snippets", True)),
                    },
                )

        return {
            "stepDefinitions": step_definitions,
            "hooks": hooks,
            "parameterTypes": parameter_types,
        }

    def build_cucumber_formatter_support_code_payload(self, envelopes: list[Message]) -> JSONObject:
        """
        Build cucumber formatter support code payload.

        Returns:
            Support code payload.

        Responsibility:
            Build cucumber formatter support code payload. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin.build_cucumber_formatter_support_code_payload`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._build_cucumber_formatter_support_code_payload: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `build_cucumber_formatter_support_code_payload`

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
        return self._build_cucumber_formatter_support_code_payload(envelopes)

    def _build_cucumber_formatter_payload(
        self,
        *,
        envelopes: list[Message],
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
        messages_path: Path | None = None,
    ) -> JSONObject:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._build_cucumber_formatter_payload`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_payload.LiveFormatterPayloadMixin._build_cucumber_formatter_payload`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - self._build_cucumber_formatter_support_code_payload: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_build_cucumber_formatter_payload`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_build_cucumber_formatter_payload`

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
        return {
            "cwd": str(Path(self.reporter.config.rootpath)),
            "messagesPath": str(messages_path) if messages_path is not None else None,
            "formatters": [
                {
                    "formatter": formatter_request.formatter,
                    "outputPath": None if formatter_request.output_path is None else str(formatter_request.output_path),
                    "cliFlag": formatter_request.cli_flag,
                    "runtime": {
                        "kind": formatter_request.runtime_kind.value,
                        "specifier": formatter_request.runtime_specifier,
                        "modulePath": formatter_request.runtime_module_path,
                        "exportName": formatter_request.runtime_export_name,
                    },
                }
                for formatter_request in formatter_requests
            ],
            "formatOptions": {},
            "supportCode": self._build_cucumber_formatter_support_code_payload(envelopes),
        }
