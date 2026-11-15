from __future__ import annotations

import os
from typing import Any

_DEFAULT_PATTERNS = ("secret", "password", "token", "key", "credential", "api_key")
_REDACTED = "<redacted>"
_MIN_SECRET_LENGTH = 6


def _denied_patterns(patterns: tuple[str, ...]) -> tuple[str, ...]:
    return (*_DEFAULT_PATTERNS, *(pattern.casefold() for pattern in patterns))


def secret_values(patterns: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Return recognizable environment values that must not appear in artifacts."""
    denied = _denied_patterns(patterns)
    return tuple(
        value
        for name, value in os.environ.items()
        if len(value) >= _MIN_SECRET_LENGTH and any(pattern in name.casefold() for pattern in denied)
    )


def redact_text(text: str, secrets: tuple[str, ...] = ()) -> str:
    """Replace recognized secret values in free text."""
    for secret in secrets:
        text = text.replace(secret, _REDACTED)
    return text


def redact_data(value: Any, secrets: tuple[str, ...] = ()) -> Any:
    """Redact strings inside JSON-like fixture and artifact data."""
    if isinstance(value, str):
        return redact_text(value, secrets)
    if isinstance(value, dict):
        return {redact_text(str(key), secrets): redact_data(item, secrets) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [redact_data(item, secrets) for item in value]
    return value


def redacted_environment(patterns: tuple[str, ...] = ()) -> dict[str, str]:
    """Capture environment only on opt-in, hiding denied names and their values everywhere."""
    denied = _denied_patterns(patterns)
    secrets = secret_values(patterns)
    return {
        name: "<redacted>"
        if any(pattern in name.casefold() for pattern in denied)
        else redact_text(value[:500], secrets)
        for name, value in os.environ.items()
    }


__all__ = ["redact_data", "redact_text", "redacted_environment", "secret_values"]
