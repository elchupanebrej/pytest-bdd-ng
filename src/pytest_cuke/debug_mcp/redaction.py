from __future__ import annotations

import os

_DEFAULT_PATTERNS = ("secret", "password", "token", "key", "credential", "api_key")


def redacted_environment(patterns: tuple[str, ...] = ()) -> dict[str, str]:
    """Capture environment only on opt-in, retaining the legacy name denylist."""
    denied = (*_DEFAULT_PATTERNS, *(pattern.casefold() for pattern in patterns))
    return {
        name: "<redacted>" if any(pattern in name.casefold() for pattern in denied) else value[:500]
        for name, value in os.environ.items()
    }
