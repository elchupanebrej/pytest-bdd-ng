from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


DEFAULT_BARRIER_TIMEOUT = 60.0


@dataclass(frozen=True)
class TestGroupPathMapping:
    """Map a relative test path glob to one configured group."""

    pattern: str
    group: str


@dataclass(frozen=True)
class TestGroupConfiguration:
    """Parsed, immutable settings for optional test-group ordering."""

    order: tuple[str, ...]
    default_group: str | None
    path_mappings: tuple[TestGroupPathMapping, ...]
    barrier_timeout: float
    warnings: tuple[str, ...]

    @property
    def enabled(self) -> bool:
        """Whether a non-empty configured order opts in to group ordering."""
        return bool(self.order)

    def ordinal(self, group: str) -> int:
        """Return the configured position for a group, raising for unknown names."""
        return self.order.index(group)


def parse_test_group_configuration(
    *,
    order: Sequence[str] | None,
    default_group: str | None = None,
    paths: Sequence[str] | None = None,
    barrier_timeout: int | float | str | None = DEFAULT_BARRIER_TIMEOUT,
) -> TestGroupConfiguration:
    """Parse public pytest settings without depending on pytest hook state.

    An absent or empty order disables this workflow. Other values are ignored in
    that case so merely carrying unrelated settings cannot produce warnings or
    activate barrier behavior.
    """
    raw_order = (
        order.split() if isinstance(order, str) else [group for line in (order or ()) for group in str(line).split()]
    )
    groups: list[str] = []
    warning_messages: list[str] = []

    for raw_group in raw_order:
        group = raw_group.strip()
        if not group:
            continue
        if group in groups:
            warning_messages.append(
                f"Duplicate test group {group!r} in cuke_test_group_order; keeping the first occurrence."
            )
            continue
        groups.append(group)

    if not groups:
        return TestGroupConfiguration(
            order=(),
            default_group=None,
            path_mappings=(),
            barrier_timeout=DEFAULT_BARRIER_TIMEOUT,
            warnings=(),
        )

    selected_default = groups[0]
    requested_default = default_group.strip() if default_group is not None else ""
    if requested_default:
        if requested_default in groups:
            selected_default = requested_default
        else:
            warning_messages.append(
                "Unknown test group default "
                f"{requested_default!r} in cuke_test_group_default; "
                f"using first configured group {selected_default!r}."
            )

    parsed_paths = _parse_path_mappings(paths, groups, warning_messages)
    timeout = _parse_barrier_timeout(barrier_timeout)

    return TestGroupConfiguration(
        order=tuple(groups),
        default_group=selected_default,
        path_mappings=tuple(parsed_paths),
        barrier_timeout=timeout,
        warnings=tuple(warning_messages),
    )


def _parse_path_mappings(
    values: Sequence[str] | None,
    groups: Sequence[str],
    warning_messages: list[str],
) -> list[TestGroupPathMapping]:
    lines = values.splitlines() if isinstance(values, str) else (values or ())
    mappings: list[TestGroupPathMapping] = []

    for raw_mapping in lines:
        mapping = raw_mapping.strip()
        if not mapping:
            continue
        pattern_text, separator, group_text = mapping.partition("=")
        pattern = _normalize_pattern(pattern_text.strip()) if separator else ""
        group = group_text.strip()
        if not pattern or not group:
            warning_messages.append(
                f"Ignoring malformed cuke_test_group_paths entry {mapping!r}; expected a relative GLOB = GROUP mapping."
            )
            continue
        if group not in groups:
            warning_messages.append(f"Ignoring cuke_test_group_paths entry {mapping!r}: unknown test group {group!r}.")
            continue
        mappings.append(TestGroupPathMapping(pattern=pattern, group=group))

    return mappings


def _normalize_pattern(pattern: str) -> str:
    normalized = pattern.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    parts = normalized.split("/")
    if not normalized or normalized.startswith("/") or "\x00" in normalized or any(part == ".." for part in parts):
        return ""
    return normalized.rstrip("/")


def _parse_barrier_timeout(value: int | float | str | None) -> float:
    if value is None:
        return DEFAULT_BARRIER_TIMEOUT
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("cuke_test_group_barrier_timeout must be a positive finite number")
    try:
        timeout = float(value)
    except ValueError as error:
        raise ValueError("cuke_test_group_barrier_timeout must be a positive finite number") from error
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("cuke_test_group_barrier_timeout must be a positive finite number")
    return timeout
