"""Provide message model coverage helpers."""

from __future__ import annotations

from collections.abc import Generator, Mapping
from typing import TYPE_CHECKING, Any

import yaml  # type:ignore[import-untyped] — library has no type stubs

if TYPE_CHECKING:
    from pathlib import Path

REQUIRED = "required"
OK = "OK"
MISSING = "MISSING"


def is_populated(value: object) -> bool:
    """Return populated."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (bytes, bytearray)):
        return bool(value)
    if isinstance(value, (list, tuple, dict, set, frozenset)):
        return bool(value)
    return True


def load_oracle_payload_tree(path: Path) -> dict[str, Any]:
    """
    Load oracle payload tree.

    Raises:
        TypeError: If the operation cannot be completed.

    """
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = f"Oracle yaml must be a mapping: {path}"
        raise TypeError(msg)
    payloads = payload.get("payloads")
    if not isinstance(payloads, Mapping):
        msg = f"Oracle yaml must contain 'payloads' mapping: {path}"
        raise TypeError(msg)
    return dict(payloads)


def _walk_values(value: object, path_segments: tuple[str, ...]) -> Generator[object, None, None]:
    if not path_segments:
        yield value
        return

    segment = path_segments[0]
    tail = path_segments[1:]

    if value is None:
        return

    if isinstance(value, Mapping):
        if segment in value:
            yield from _walk_values(value[segment], tail)
        return

    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _walk_values(item, path_segments)
        return

    child = getattr(value, segment, None)
    if child is not None:
        yield from _walk_values(child, tail)


def is_path_populated(payloads: list[object], path_segments: tuple[str, ...]) -> bool:
    """Return path populated."""
    for payload in payloads:
        for value in _walk_values(payload, path_segments):
            if is_populated(value):
                return True
    return False


def build_observed_coverage_tree(
    oracle_node: object,
    payloads: list[object],
    path_prefix: tuple[str, ...] = (),
) -> object:
    """Build observed coverage tree."""
    if isinstance(oracle_node, Mapping):
        return {
            key: build_observed_coverage_tree(value, payloads, (*path_prefix, str(key)))
            for key, value in oracle_node.items()
        }

    if str(oracle_node).strip().lower() != REQUIRED:
        return str(oracle_node)

    return OK if is_path_populated(payloads, path_prefix) else MISSING


def build_expected_coverage_tree(oracle_node: object) -> object:
    """Build expected coverage tree."""
    if isinstance(oracle_node, Mapping):
        return {key: build_expected_coverage_tree(value) for key, value in oracle_node.items()}
    return OK if str(oracle_node).strip().lower() == REQUIRED else str(oracle_node)


def dump_yaml(path: Path, payload: object) -> None:
    """Serialize yaml."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
