"""Provide message validation xdist compatibility helpers."""

from __future__ import annotations

from typing import Literal

from attrs import frozen

from pytest_bdd.model.message_validation_result import MessageValidationViolation


@frozen
class XdistReportingCompatibilityResult:
    """Indicate whether the current distributed execution environment meets the requirements for xdist reporting."""

    status: Literal["pass", "fail"]
    reason: str | None = None

    @property
    def is_valid(self) -> bool:
        """
        Determine if the environment is fully compatible for xdist reporting.

        Returns:
            True if the status is 'pass', otherwise False.

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

    """
    return (
        "Distributed reporting requires the pytest-bdd xdist remote-module adapter and "
        f"compatible worker/controller channel handling. {reason}"
    )
