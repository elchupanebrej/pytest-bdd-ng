"""Provide test message emission points helpers."""

from __future__ import annotations

import ast
from pathlib import Path

from pytest_bdd.model.message_extension import PAYLOAD_KINDS

REPORTER_RUNTIME_DIR = (
    Path(__file__).resolve().parents[4] / "src" / "pytest_bdd" / "plugin" / "gherkin_message_reporter"
)
RUNTIME_MODULE_PATHS = (
    REPORTER_RUNTIME_DIR / "lifecycle_runtime.py",
    REPORTER_RUNTIME_DIR / "hook_catalog_runtime.py",
    REPORTER_RUNTIME_DIR / "step_catalog_runtime.py",
    REPORTER_RUNTIME_DIR / "scenario_runtime.py",
    REPORTER_RUNTIME_DIR / "attachment_runtime.py",
)

EXPECTED_EMISSIONS_BY_METHOD: dict[str, set[str]] = {
    "pytest_sessionstart": {"meta"},
    "pytest_bdd_source_read": {"source"},
    "pytest_bdd_feature_read": {"gherkin_document"},
    "pytest_bdd_pickle_read": {"pickle"},
    "pytest_runtestloop": {"test_run_started"},
    "pytest_runtest_setup": {"test_case"},
    "_report_step_definitions": {"step_definition"},
    "_register_parameter_types": {"parameter_type"},
    "pytest_fixture_setup": {"hook"},
    "pytest_bdd_before_scenario": {"test_case_started"},
    "pytest_bdd_before_step": {"test_step_started"},
    "pytest_bdd_after_step": {"test_step_finished"},
    "pytest_bdd_step_error": {"test_step_finished"},
    "pytest_bdd_after_scenario": {"test_case_finished"},
    "pytest_sessionfinish": {"test_run_finished"},
    "pytest_bdd_attach": {"attachment"},
}

# parse_error envelopes are emitted by parser layer (`BaseParser.emit_parse_error`)
# before reporter plugin hooks are entered.
EMITTED_OUTSIDE_REPORTER_PLUGIN: set[str] = {"parse_error"}


PAYLOAD_HINTS: dict[str, str] = {
    "feature_source": "source",
    "gherkin_document": "gherkin_document",
    "pickle": "pickle",
    "hook_message": "hook",
    "test_case_start": "test_case_started",
    "test_step_started": "test_step_started",
    "suggestion": "suggestion",
}


def _camel_to_snake(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if char.isupper() and index > 0 and (not value[index - 1].isupper()):
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


def _payload_kind_from_type_name(type_name: str) -> str | None:
    candidate = _camel_to_snake(type_name)
    return candidate if candidate in PAYLOAD_KINDS else None


def _infer_payload_kinds_from_expression(expression: ast.expr) -> set[str]:  # noqa: PLR0911
    if isinstance(expression, ast.Call):
        func = expression.func
        if isinstance(func, ast.Name):
            inferred = _payload_kind_from_type_name(func.id)
            return {inferred} if inferred is not None else set()
        if isinstance(func, ast.Attribute) and func.attr == "as_message":
            return {"step_definition"}
        return set()

    if isinstance(expression, ast.Name):
        if expression.id in PAYLOAD_HINTS:
            return {PAYLOAD_HINTS[expression.id]}
        inferred = _payload_kind_from_type_name(expression.id)
        return {inferred} if inferred is not None else set()

    if isinstance(expression, ast.Attribute):
        if expression.attr in PAYLOAD_HINTS:
            return {PAYLOAD_HINTS[expression.attr]}
        inferred = _payload_kind_from_type_name(expression.attr)
        return {inferred} if inferred is not None else set()

    return set()


def _payloads_from_lifecycle_call(node: ast.Call) -> set[str]:
    if not (isinstance(node.func, ast.Attribute) and node.func.attr == "_emit_lifecycle"):
        return set()
    if len(node.args) < 2:
        return set()
    payload_expression = node.args[1]
    return _infer_payload_kinds_from_expression(payload_expression)


def _payloads_from_envelope_call(node: ast.Call) -> set[str]:
    if not (isinstance(node.func, ast.Attribute) and node.func.attr == "_emit_envelope"):
        return set()
    if len(node.args) < 2:
        return set()

    message_call = node.args[1]
    if not isinstance(message_call, ast.Call):
        return set()
    if not (isinstance(message_call.func, ast.Name) and message_call.func.id == "Message"):
        return set()

    return {keyword.arg for keyword in message_call.keywords if keyword.arg is not None}


def _payloads_emitted_by_method(method: ast.FunctionDef) -> set[str]:
    emitted: set[str] = set()
    for node in ast.walk(method):
        if not isinstance(node, ast.Call):
            continue
        emitted.update(_payloads_from_lifecycle_call(node))
        emitted.update(_payloads_from_envelope_call(node))
    return emitted


def _collect_message_payload_emissions_by_method() -> dict[str, set[str]]:
    emissions_by_method: dict[str, set[str]] = {}
    for module_path in RUNTIME_MODULE_PATHS:
        module = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        class_defs = [node for node in module.body if isinstance(node, ast.ClassDef)]
        for class_def in class_defs:
            for method in class_def.body:
                if not isinstance(method, ast.FunctionDef):
                    continue
                emitted = _payloads_emitted_by_method(method)
                if emitted:
                    emissions_by_method[method.name] = emitted
    return emissions_by_method


def test_message_emission_points_cover_expected_methods_and_payloads() -> None:
    """Verify message emission points cover expected methods and payloads."""
    emissions_by_method = _collect_message_payload_emissions_by_method()

    missing_methods = sorted(set(EXPECTED_EMISSIONS_BY_METHOD).difference(set(emissions_by_method)))
    assert not missing_methods, f"Missing emission methods: {missing_methods}"

    missing_payloads_by_method: dict[str, list[str]] = {}
    for method_name, expected_payloads in EXPECTED_EMISSIONS_BY_METHOD.items():
        observed_payloads = emissions_by_method.get(method_name, set())
        missing = sorted(expected_payloads.difference(observed_payloads))
        if missing:
            missing_payloads_by_method[method_name] = missing

    assert not missing_payloads_by_method, f"Missing payload emissions by method: {missing_payloads_by_method}"


def test_message_emission_points_cover_all_supported_payload_kinds() -> None:
    """Verify message emission points cover all supported payload kinds."""
    emissions_by_method = _collect_message_payload_emissions_by_method()
    emitted_payloads = set().union(*emissions_by_method.values(), EMITTED_OUTSIDE_REPORTER_PLUGIN)
    missing_payloads = sorted(set(PAYLOAD_KINDS).difference(emitted_payloads))
    assert not missing_payloads, f"Supported payload kinds without emission point: {missing_payloads}"


def test_payload_hints_do_not_reference_current_prefixed_reporter_state() -> None:
    """Verify payload hints do not reference current prefixed reporter state."""
    current_prefixed = sorted(hint for hint in PAYLOAD_HINTS if hint.startswith("current_"))
    assert current_prefixed == []
