"""
Provide message validation xdist compatibility helpers.

Responsibility:
    Provide message validation xdist compatibility helpers. It directly owns the observable contract, local decisions,
    and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_validation_xdist` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - XdistReportingCompatibilityResult: owns nested behavior below this boundary
    - validate_xdist_reporting_compatibility: owns nested behavior below this boundary
    - validate_execnet_serializable_payload: owns nested behavior below this boundary
    - format_xdist_transport_compatibility_error: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/message_validation.py: imports or references `message_validation_xdist`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
      `message_validation_xdist`

State and side effects:
    mutates violations, status, reason, payload; depends on __future__.annotations, typing.Literal, attrs.frozen,
    pytest_bdd.model.message_validation_result.MessageValidationViolation.

Invariants:
    - `pytest_bdd.model.message_validation_xdist` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from typing import Literal

from attrs import frozen

from pytest_bdd.model.message_validation_result import MessageValidationViolation


@frozen
class XdistReportingCompatibilityResult:
    """
    Indicate whether the current distributed execution environment meets the requirements for xdist reporting.

    Responsibility:
        Indicate whether the current distributed execution environment meets the requirements for xdist reporting. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_validation_xdist.XdistReportingCompatibilityResult` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - is_valid: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/message_validation.py: imports or references `XdistReportingCompatibilityResult`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `XdistReportingCompatibilityResult`

    State and side effects:
        mutates status, reason.

    Invariants:
        - `pytest_bdd.model.message_validation_xdist.XdistReportingCompatibilityResult` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    status: Literal["pass", "fail"]
    reason: str | None = None

    @property
    def is_valid(self) -> bool:
        """
        Determine if the environment is fully compatible for xdist reporting.

        Returns:
            True if the status is 'pass', otherwise False.

        Responsibility:
            Determine if the environment is fully compatible for xdist reporting. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_validation_xdist.XdistReportingCompatibilityResult.is_valid` because it keeps the
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
            - src/pytest_bdd/model/message_validation.py: imports or references `is_valid`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `is_valid`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `is_valid`

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
        return self.status == "pass"


def validate_xdist_reporting_compatibility(  # noqa: PLR0913
    *,
    xdist_active: bool,
    is_worker: bool,
    is_controller: bool,
    remote_module_available: bool,
    controller_event_patch_installed: bool,
    worker_sender_available: bool,
) -> XdistReportingCompatibilityResult:
    """
    Verify that the xdist plugin configuration and node topology support remote message aggregation.

    Returns:
        An XdistReportingCompatibilityResult detailing success or the specific blocking constraint.

    Responsibility:
        Verify that the xdist plugin configuration and node topology support remote message aggregation. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_validation_xdist.validate_xdist_reporting_compatibility` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - XdistReportingCompatibilityResult: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/message_validation.py: imports or references `validate_xdist_reporting_compatibility`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `validate_xdist_reporting_compatibility`

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
    if not xdist_active:
        return XdistReportingCompatibilityResult(status="pass")
    if is_controller and not remote_module_available:
        return XdistReportingCompatibilityResult(
            status="fail",
            reason=(
                "Distributed reporting requires pytest_xdist_getremotemodule, but the hook integration is unavailable."
            ),
        )
    if is_controller and not controller_event_patch_installed:
        return XdistReportingCompatibilityResult(
            status="fail",
            reason="Distributed reporting requires controller support for reporter-specific xdist channel events.",
        )
    if is_worker and not worker_sender_available:
        return XdistReportingCompatibilityResult(
            status="fail",
            reason=(
                "Distributed reporting requires the xdist remote-module adapter to expose a worker channel sender. "
                "Falling back to a side-channel transport is not allowed."
            ),
        )
    return XdistReportingCompatibilityResult(status="pass")


def validate_execnet_serializable_payload(
    payload: object,
    *,
    path: tuple[str, ...] = (),
) -> tuple[MessageValidationViolation, ...]:
    """
    Recursively verify that a payload dictionary only contains types that can be reliably transported via execnet.

    Returns:
        A tuple of MessageValidationViolation instances for any keys or values that break serialization constraints.

    Responsibility:
        Recursively verify that a payload dictionary only contains types that can be reliably transported via execnet.
        It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_validation_xdist.validate_execnet_serializable_payload` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - violations.extend: collaborator call used by this boundary
        - validate_execnet_serializable_payload: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - MessageValidationViolation: collaborator call used by this boundary
        - join: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/message_validation.py: imports or references `validate_execnet_serializable_payload`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `validate_execnet_serializable_payload`

    State and side effects:
        mutates violations, payload.

    Invariants:
        - `pytest_bdd.model.message_validation_xdist.validate_execnet_serializable_payload` keeps its documented import
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
    if payload is None or isinstance(payload, (str, int, float, bool)):
        return ()
    if isinstance(payload, tuple):
        payload = list(payload)
    if isinstance(payload, list):
        violations: list[MessageValidationViolation] = []
        for index, item in enumerate(payload):
            violations.extend(validate_execnet_serializable_payload(item, path=(*path, str(index))))
        return tuple(violations)
    if isinstance(payload, dict):
        violations = []
        for key, value in payload.items():
            if not isinstance(key, str):
                violations.append(
                    MessageValidationViolation(
                        code="INVALID_PAYLOAD_SHAPE",
                        message=f"Execnet payload keys must be strings at {'.'.join(path) or '<root>'}.",
                        json_path=path,
                    ),
                )
                continue
            violations.extend(validate_execnet_serializable_payload(value, path=(*path, key)))
        return tuple(violations)
    return (
        MessageValidationViolation(
            code="INVALID_PAYLOAD_SHAPE",
            message=(
                f"Execnet payload contains unsupported type '{type(payload).__name__}' at {'.'.join(path) or '<root>'}."
            ),
            json_path=path,
        ),
    )


def format_xdist_transport_compatibility_error(reason: str) -> str:
    """
    Construct a standardized error message indicating a failure in the xdist reporting transport constraints.

    Returns:
        A formatted error string detailing the incompatibility.

    Responsibility:
        Construct a standardized error message indicating a failure in the xdist reporting transport constraints. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_validation_xdist.format_xdist_transport_compatibility_error` because it keeps the
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
        - src/pytest_bdd/model/message_validation.py: imports or references `format_xdist_transport_compatibility_error`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `format_xdist_transport_compatibility_error`

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
    return (
        "Distributed reporting requires the pytest-bdd xdist remote-module adapter and "
        f"compatible worker/controller channel handling. {reason}"
    )
