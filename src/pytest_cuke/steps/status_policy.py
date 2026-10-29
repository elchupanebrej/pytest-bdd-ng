from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Item
    from pytest_cuke.model.scenario import Scenario

TolerantStatus = Literal["failed", "ignored"]
WipStatus = Literal["failed", "passed", "skipped"]

_TOLERANT_STATUSES = frozenset(("failed", "ignored"))
_WIP_STATUSES = frozenset(("failed", "passed", "skipped"))


def _normalize_value(value: object) -> str:
    return str(value).strip().lower().replace("_", "-")


def _local_status(value: object, valid_statuses: frozenset[str]) -> str | None:
    normalized = _normalize_value(value)
    return normalized if normalized in valid_statuses else None


def _tag_status(tag_name: object, tag_prefix: str, valid_statuses: frozenset[str]) -> str | None:
    normalized = _normalize_value(tag_name).lstrip("@")
    if not normalized.startswith(tag_prefix):
        return None
    return _local_status(normalized[len(tag_prefix) :], valid_statuses)


def configured_status(config: Config, option_name: str, ini_name: str, valid_statuses: frozenset[str]) -> str:
    """Validate one CLI-over-ini status setting, which pytest resolves before collection."""
    cli_status = getattr(getattr(config, "option", None), option_name, None)
    value = cli_status if cli_status is not None else config.getini(ini_name)
    if value not in valid_statuses:
        choices = " or ".join(repr(status) for status in sorted(valid_statuses))
        raise ValueError(f"{ini_name} must be either {choices} (received {value!r}).")
    return cast("str", value)


def resolve_status(
    config: Config,
    item: Item,
    scenario: Scenario,
    *,
    marker_name: str,
    tag_prefix: str,
    option_name: str,
    ini_name: str,
    valid_statuses: frozenset[str],
) -> str:
    """Resolve an explicit pytest marker, Gherkin tag, then validated global setting."""
    iter_markers = getattr(item, "iter_markers", None)
    if callable(iter_markers):
        for marker in iter_markers(name=marker_name):
            if marker.args:
                status = _local_status(marker.args[0], valid_statuses)
                if status is not None:
                    return status

        for marker in iter_markers():
            status = _tag_status(getattr(marker, "name", ""), tag_prefix, valid_statuses)
            if status is not None:
                return status

    for tag_name in getattr(scenario, "tag_names", ()):
        status = _tag_status(tag_name, tag_prefix, valid_statuses)
        if status is not None:
            return status

    return configured_status(config, option_name, ini_name, valid_statuses)


def configured_tolerant_status(config: Config) -> TolerantStatus:
    return cast(
        "TolerantStatus",
        configured_status(config, "cuke_tolerant_status", "cuke_tolerant_status", _TOLERANT_STATUSES),
    )


def configured_wip_status(config: Config) -> WipStatus:
    return cast("WipStatus", configured_status(config, "cuke_wip_status", "cuke_wip_status", _WIP_STATUSES))


def resolve_tolerant_status(config: Config, item: Item, scenario: Scenario) -> TolerantStatus:
    return cast(
        "TolerantStatus",
        resolve_status(
            config,
            item,
            scenario,
            marker_name="tolerant_status",
            tag_prefix="tolerant-status-",
            option_name="cuke_tolerant_status",
            ini_name="cuke_tolerant_status",
            valid_statuses=_TOLERANT_STATUSES,
        ),
    )


def resolve_wip_status(config: Config, item: Item, scenario: Scenario) -> WipStatus:
    return cast(
        "WipStatus",
        resolve_status(
            config,
            item,
            scenario,
            marker_name="wip_status",
            tag_prefix="wip-status-",
            option_name="cuke_wip_status",
            ini_name="cuke_wip_status",
            valid_statuses=_WIP_STATUSES,
        ),
    )


__all__ = [
    "TolerantStatus",
    "WipStatus",
    "configured_status",
    "configured_tolerant_status",
    "configured_wip_status",
    "resolve_status",
    "resolve_tolerant_status",
    "resolve_wip_status",
]
