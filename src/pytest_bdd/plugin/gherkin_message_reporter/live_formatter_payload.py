"""Provide live formatter payload helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cucumber_messages import Envelope as Message

    from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRequest
    from pytest_bdd.types.json import JSONArray, JSONObject


class LiveFormatterPayloadMixin:
    """Provide live formatter payload construction behavior."""

    @staticmethod
    def _resolve_formatter_expression_constructor_name(pattern_type: object | None) -> str:
        type_name = getattr(pattern_type, "name", None) or str(pattern_type or "")
        normalized = type_name.upper()
        if "REGULAR" in normalized:
            return "RegularExpression"
        return "CucumberExpression"

    @staticmethod
    def _resolve_source_reference_uri(source_reference: object | None) -> str:
        uri = getattr(source_reference, "uri", None)
        return "" if uri is None else str(uri)

    @staticmethod
    def _resolve_source_reference_line(source_reference: object | None) -> int:
        location = getattr(source_reference, "location", None)
        line = getattr(location, "line", 0)
        return int(line or 0)

    def _build_cucumber_formatter_support_code_payload(self, envelopes: list[Message]) -> JSONObject:
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

        """
        return self._build_cucumber_formatter_support_code_payload(envelopes)

    def _build_cucumber_formatter_payload(
        self,
        *,
        envelopes: list[Message],
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
        messages_path: Path | None = None,
    ) -> JSONObject:
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
