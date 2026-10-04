from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Item
    from pytest_cuke.model.scenario import Scenario

TolerantStatus = Literal["failed", "ignored"]
_VALID_STATUSES = frozenset(("failed", "ignored"))


def configured_tolerant_status(config: Config) -> TolerantStatus:
    """Return the validated session-level tolerant-step policy."""
    cli_status = getattr(getattr(config, "option", None), "cuke_tolerant_status", None)
    value = cli_status if cli_status is not None else config.getini("cuke_tolerant_status")
    if value not in _VALID_STATUSES:
        raise ValueError(
            "cuke_tolerant_status must be either 'failed' or 'ignored' "
            f"(received {value!r})."
        )
    return cast("TolerantStatus", value)


def _normalize_value(value: object) -> str:
    return str(value).strip().lower().replace("_", "-")


def _status_from_normalized(value: str) -> TolerantStatus | None:
    return cast("TolerantStatus", value) if value in _VALID_STATUSES else None


def _normalize_status(value: object) -> TolerantStatus | None:
    return _status_from_normalized(_normalize_value(value))


def _tag_status(tag_name: object) -> TolerantStatus | None:
    normalized = _normalize_value(tag_name).lstrip("@")
    prefix = "tolerant-status-"
    if not normalized.startswith(prefix):
        return None
    return _status_from_normalized(normalized[len(prefix) :])


def resolve_tolerant_status(config: Config, item: Item, scenario: Scenario) -> TolerantStatus:
    """Resolve explicit pytest marker, Gherkin tag, and then session policy."""
    iter_markers = getattr(item, "iter_markers", None)
    if callable(iter_markers):
        for marker in iter_markers(name="tolerant_status"):
            if marker.args:
                status = _normalize_status(marker.args[0])
                if status is not None:
                    return status

        for marker in iter_markers():
            status = _tag_status(getattr(marker, "name", ""))
            if status is not None:
                return status

    for tag_name in getattr(scenario, "tag_names", ()):
        status = _tag_status(tag_name)
        if status is not None:
            return status

    return configured_tolerant_status(config)


__all__ = ["TolerantStatus", "configured_tolerant_status", "resolve_tolerant_status"]
